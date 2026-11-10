"""Read-only PDF structure inspection."""
from __future__ import annotations

from deskagent.actions.documents._common import DocumentAction, pdf_reader, page_range

PATH = {"path": {"type": "string", "required": True}}
RANGE = {**PATH, "start_page": {"type": "integer", "required": False, "default": 1, "minimum": 1},
         "page_count": {"type": "integer", "required": False, "default": 10,
                        "minimum": 1, "maximum": 100}}


def _safe(value):
    return None if value is None else str(value)[:1000]


class GetPdfMetadata(DocumentAction):
    name = "get_pdf_metadata"
    description = "Read PDF title, author, dates, page count and encryption status"
    parameters_schema = PATH
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            path, reader = pdf_reader(context, parameters["path"])
            metadata = reader.metadata or {}
            return {"path": str(path), "page_count": len(reader.pages),
                    "metadata": {str(key): _safe(value) for key, value in metadata.items()}}
        return self.run(operation)


class GetPdfPageDimensions(DocumentAction):
    name = "get_pdf_page_dimensions"
    description = "Read dimensions and rotation of a bounded PDF page range"
    parameters_schema = RANGE
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            path, reader = pdf_reader(context, parameters["path"])
            pages = []
            for index in page_range(parameters, len(reader.pages)):
                page = reader.pages[index]
                box = page.mediabox
                pages.append({"page": index + 1, "width_points": float(box.width),
                              "height_points": float(box.height), "rotation": int(page.get("/Rotate", 0))})
            return {"path": str(path), "pages": pages}
        return self.run(operation)


class GetPdfOutline(DocumentAction):
    name = "get_pdf_outline"
    description = "Read a bounded flat list of PDF bookmarks with hierarchy depth"
    parameters_schema = PATH
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            path, reader = pdf_reader(context, parameters["path"])
            found = []

            def walk(items, depth):
                for item in items:
                    if len(found) >= 500:
                        return
                    if isinstance(item, list):
                        walk(item, depth + 1)
                    else:
                        try:
                            number = reader.get_destination_page_number(item) + 1
                        except Exception:
                            number = None
                        found.append({"title": _safe(getattr(item, "title", item)),
                                      "page": number, "depth": depth})
            walk(reader.outline, 0)
            return {"path": str(path), "bookmarks": found, "truncated": len(found) >= 500}
        return self.run(operation)


class GetPdfPageTextStatistics(DocumentAction):
    name = "get_pdf_page_text_statistics"
    description = "Measure extracted character, word and line counts per PDF page"
    parameters_schema = RANGE
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            path, reader = pdf_reader(context, parameters["path"])
            pages = []
            for index in page_range(parameters, len(reader.pages)):
                text = reader.pages[index].extract_text() or ""
                pages.append({"page": index + 1, "characters": len(text),
                              "words": len(text.split()), "lines": len(text.splitlines()),
                              "has_extractable_text": bool(text.strip())})
            return {"path": str(path), "pages": pages}
        return self.run(operation)


class GetPdfLinks(DocumentAction):
    name = "get_pdf_links"
    description = "List PDF link annotations and their URI targets"
    parameters_schema = RANGE
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            path, reader = pdf_reader(context, parameters["path"])
            links = []
            for index in page_range(parameters, len(reader.pages)):
                for annotation in reader.pages[index].get("/Annots", []) or []:
                    value = annotation.get_object()
                    if value.get("/Subtype") != "/Link":
                        continue
                    action = value.get("/A") or {}
                    uri = action.get("/URI") if hasattr(action, "get") else None
                    links.append({"page": index + 1, "uri": _safe(uri),
                                  "rectangle": [float(x) for x in value.get("/Rect", [])[:4]]})
                    if len(links) >= 500:
                        return {"path": str(path), "links": links, "truncated": True}
            return {"path": str(path), "links": links, "truncated": False}
        return self.run(operation)


class GetPdfAnnotations(DocumentAction):
    name = "get_pdf_annotations"
    description = "List bounded PDF annotation types, authors and text"
    parameters_schema = RANGE
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            path, reader = pdf_reader(context, parameters["path"])
            found = []
            for index in page_range(parameters, len(reader.pages)):
                for annotation in reader.pages[index].get("/Annots", []) or []:
                    value = annotation.get_object()
                    found.append({"page": index + 1, "type": _safe(value.get("/Subtype")),
                                  "author": _safe(value.get("/T")),
                                  "contents": _safe(value.get("/Contents"))})
                    if len(found) >= 500:
                        return {"path": str(path), "annotations": found, "truncated": True}
            return {"path": str(path), "annotations": found, "truncated": False}
        return self.run(operation)


class GetPdfFormFields(DocumentAction):
    name = "get_pdf_form_fields"
    description = "Inspect PDF AcroForm fields and current values"
    parameters_schema = PATH
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            path, reader = pdf_reader(context, parameters["path"])
            fields = reader.get_fields() or {}
            found = [{"name": str(name)[:300], "type": _safe(value.get("/FT")),
                      "value": _safe(value.get("/V"))}
                     for name, value in list(fields.items())[:500]]
            return {"path": str(path), "fields": found, "total": len(fields),
                    "truncated": len(fields) > 500}
        return self.run(operation)


class GetPdfImageInventory(DocumentAction):
    name = "get_pdf_image_inventory"
    description = "List image names and byte sizes without returning image bytes"
    parameters_schema = RANGE
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            path, reader = pdf_reader(context, parameters["path"])
            found = []
            for index in page_range(parameters, len(reader.pages)):
                for image in reader.pages[index].images:
                    found.append({"page": index + 1, "name": _safe(image.name),
                                  "bytes": len(image.data)})
                    if len(found) >= 500:
                        return {"path": str(path), "images": found, "truncated": True}
            return {"path": str(path), "images": found, "truncated": False}
        return self.run(operation)


class CheckPdfAccessibilityBasics(DocumentAction):
    name = "check_pdf_accessibility_basics"
    description = "Check basic PDF tagging, language and extractable text signals"
    parameters_schema = PATH
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            path, reader = pdf_reader(context, parameters["path"])
            root = reader.trailer["/Root"]
            tagged = bool(root.get("/MarkInfo", {}).get("/Marked", False))
            language = _safe(root.get("/Lang"))
            empty = [index + 1 for index, page in enumerate(reader.pages)
                     if not (page.extract_text() or "").strip()]
            return {"path": str(path), "tagged": tagged, "language": language,
                    "pages_without_extractable_text": empty[:100],
                    "pages_without_extractable_text_count": len(empty),
                    "note": "Basic signals only; not a full accessibility audit"}
        return self.run(operation)
