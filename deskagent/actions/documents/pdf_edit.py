"""PDF transformations that create new files and preserve their sources."""
from __future__ import annotations

from deskagent.actions.documents._common import (
    DocumentWriteAction, pdf_reader, pdf_writer, save_new,
)

PATH_OUTPUT = {"path": {"type": "string", "required": True},
               "output_path": {"type": "string", "required": True}}
RANGE = {**PATH_OUTPUT, "start_page": {"type": "integer", "required": True, "minimum": 1},
         "page_count": {"type": "integer", "required": True, "minimum": 1, "maximum": 500}}


def _save_pdf(context, path, writer):
    return save_new(context, path, {".pdf"}, lambda temporary: writer.write(str(temporary)))


class MergePdfFiles(DocumentWriteAction):
    name = "merge_pdf_files"
    description = "Merge two to twenty PDFs into a new PDF"
    parameters_schema = {"paths": {"type": "list", "required": True, "items": {"type": "string"}},
                         "output_path": {"type": "string", "required": True}}
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            paths = parameters["paths"]
            if not 2 <= len(paths) <= 20:
                raise ValueError("Provide 2 to 20 PDF files")
            writer = pdf_writer()
            total = 0
            for path in paths:
                _, reader = pdf_reader(context, path)
                total += len(reader.pages)
                if total > 500:
                    raise ValueError("Merged PDF exceeds 500 pages")
                for page in reader.pages:
                    writer.add_page(page)
            return {**_save_pdf(context, parameters["output_path"], writer),
                    "pages": total, "sources": len(paths)}
        return self.run(operation)


class ExtractPdfPages(DocumentWriteAction):
    name = "extract_pdf_pages"
    description = "Save a bounded contiguous page range to a new PDF"
    parameters_schema = RANGE
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            _, reader = pdf_reader(context, parameters["path"])
            start, count = parameters["start_page"], parameters["page_count"]
            if start < 1 or count < 1 or start + count - 1 > len(reader.pages):
                raise ValueError("Page range is outside the PDF")
            writer = pdf_writer()
            for index in range(start - 1, start - 1 + count):
                writer.add_page(reader.pages[index])
            return {**_save_pdf(context, parameters["output_path"], writer), "pages": count}
        return self.run(operation)


class RemovePdfPages(DocumentWriteAction):
    name = "remove_pdf_pages"
    description = "Save a new PDF excluding selected pages; source stays intact"
    requires_confirmation = True
    parameters_schema = {**PATH_OUTPUT, "pages": {"type": "list", "required": True,
                                                  "items": {"type": "integer"}}}
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            _, reader = pdf_reader(context, parameters["path"])
            removed = parameters["pages"]
            if not removed or any(type(page) is not int or page < 1 or page > len(reader.pages)
                                  for page in removed):
                raise ValueError("Invalid page list")
            selected = set(removed)
            if len(selected) == len(reader.pages):
                raise ValueError("At least one page must remain")
            writer = pdf_writer()
            for number, page in enumerate(reader.pages, 1):
                if number not in selected:
                    writer.add_page(page)
            return {**_save_pdf(context, parameters["output_path"], writer),
                    "pages": len(writer.pages), "removed_pages": sorted(selected)}
        return self.run(operation)


class ReorderPdfPages(DocumentWriteAction):
    name = "reorder_pdf_pages"
    description = "Save a PDF with pages in an explicit order"
    parameters_schema = {**PATH_OUTPUT, "page_order": {"type": "list", "required": True,
                                                       "items": {"type": "integer"}}}
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            _, reader = pdf_reader(context, parameters["path"])
            order = parameters["page_order"]
            if len(order) != len(reader.pages) or sorted(order) != list(range(1, len(reader.pages) + 1)):
                raise ValueError("Page order must contain every page exactly once")
            writer = pdf_writer()
            for number in order:
                writer.add_page(reader.pages[number - 1])
            return {**_save_pdf(context, parameters["output_path"], writer), "pages": len(order)}
        return self.run(operation)


class RotatePdfPages(DocumentWriteAction):
    name = "rotate_pdf_pages"
    description = "Rotate selected pages by 90, 180 or 270 degrees in a new PDF"
    parameters_schema = {**PATH_OUTPUT, "pages": {"type": "list", "required": True,
                                                  "items": {"type": "integer"}},
                         "degrees": {"type": "integer", "required": True, "enum": [90, 180, 270]}}
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            _, reader = pdf_reader(context, parameters["path"])
            selected = parameters["pages"]
            degrees = parameters["degrees"]
            if degrees not in {90, 180, 270} or not selected or any(
                type(number) is not int or number < 1 or number > len(reader.pages) for number in selected
            ):
                raise ValueError("Invalid rotation or page list")
            writer = pdf_writer()
            for number, page in enumerate(reader.pages, 1):
                writer.add_page(page)
                if number in selected:
                    writer.pages[-1].rotate(degrees)
            return {**_save_pdf(context, parameters["output_path"], writer),
                    "pages": len(reader.pages), "rotated_pages": sorted(set(selected))}
        return self.run(operation)


class SetPdfMetadata(DocumentWriteAction):
    name = "set_pdf_metadata"
    description = "Save a PDF copy with title, author, subject or keywords"
    parameters_schema = {**PATH_OUTPUT,
                         "title": {"type": "string", "required": False},
                         "author": {"type": "string", "required": False},
                         "subject": {"type": "string", "required": False},
                         "keywords": {"type": "string", "required": False}}
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            _, reader = pdf_reader(context, parameters["path"])
            fields = {"/" + key.capitalize(): parameters[key] for key in
                      ("title", "author", "subject", "keywords") if key in parameters}
            if not fields or any(len(value) > 1000 for value in fields.values()):
                raise ValueError("Provide metadata fields of at most 1000 characters")
            writer = pdf_writer()
            for page in reader.pages:
                writer.add_page(page)
            writer.add_metadata(fields)
            return {**_save_pdf(context, parameters["output_path"], writer),
                    "pages": len(reader.pages), "updated_fields": list(fields)}
        return self.run(operation)


class ExportPdfText(DocumentWriteAction):
    name = "export_pdf_text"
    description = "Extract PDF text with page markers into a new UTF-8 text file"
    parameters_schema = PATH_OUTPUT
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            _, reader = pdf_reader(context, parameters["path"])
            text = "\n\n".join(f"--- Page {number} ---\n{page.extract_text() or ''}"
                               for number, page in enumerate(reader.pages, 1))
            if len(text) > 2_000_000:
                raise ValueError("Extracted text exceeds 2 million characters")
            return {**save_new(context, parameters["output_path"], {".txt"},
                               lambda temporary: temporary.write_text(text, encoding="utf-8")),
                    "pages": len(reader.pages), "characters": len(text)}
        return self.run(operation)
