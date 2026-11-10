"""Non-destructive text document creation and editing."""
from __future__ import annotations

from deskagent.actions.documents._common import (
    DocumentWriteAction, MAX_TEXT_CHARS, TEXT_EXTENSIONS, read_text, save_new,
)

PATH_OUTPUT = {"path": {"type": "string", "required": True},
               "output_path": {"type": "string", "required": True}}


def _save(context, output_path, text):
    if len(text) > MAX_TEXT_CHARS:
        raise ValueError("Output exceeds 2 million characters")
    return {**save_new(context, output_path, TEXT_EXTENSIONS,
                       lambda temporary: temporary.write_text(text, encoding="utf-8")),
            "characters": len(text)}


class CreateTextDocument(DocumentWriteAction):
    name = "create_text_document"
    description = "Create a new UTF-8 TXT, Markdown or reStructuredText file"
    parameters_schema = {"output_path": {"type": "string", "required": True},
                         "text": {"type": "string", "required": True}}
    discoverable = True

    def execute(self, context, parameters):
        return self.run(lambda: _save(context, parameters["output_path"], parameters["text"]))


class ReplaceTextInDocument(DocumentWriteAction):
    name = "replace_text_in_document"
    description = "Replace literal text in a copy of a UTF-8 document"
    parameters_schema = {**PATH_OUTPUT, "find": {"type": "string", "required": True},
                         "replace": {"type": "string", "required": True},
                         "max_replacements": {"type": "integer", "required": False,
                                              "default": 1000, "minimum": 1, "maximum": 10000}}
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            _, text = read_text(context, parameters["path"])
            find = parameters["find"]
            limit = parameters.get("max_replacements", 1000)
            if not find or limit < 1 or limit > 10000:
                raise ValueError("Find text and replacement limit must be valid")
            count = min(text.count(find), limit)
            if not count:
                raise ValueError("Text to replace was not found")
            result = text.replace(find, parameters["replace"], limit)
            return {**_save(context, parameters["output_path"], result), "replacements": count}
        return self.run(operation)


class AppendTextToDocument(DocumentWriteAction):
    name = "append_text_to_document"
    description = "Append text to a new copy of a UTF-8 document"
    parameters_schema = {**PATH_OUTPUT, "text": {"type": "string", "required": True}}
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            _, text = read_text(context, parameters["path"])
            return _save(context, parameters["output_path"], text + parameters["text"])
        return self.run(operation)


class JoinTextDocuments(DocumentWriteAction):
    name = "join_text_documents"
    description = "Join two to twenty UTF-8 documents into a new file"
    parameters_schema = {"paths": {"type": "list", "required": True, "items": {"type": "string"}},
                         "output_path": {"type": "string", "required": True},
                         "separator": {"type": "string", "required": False, "default": "\n\n"}}
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            paths = parameters["paths"]
            separator = parameters.get("separator", "\n\n")
            if not 2 <= len(paths) <= 20 or len(separator) > 1000:
                raise ValueError("Provide 2-20 files and a separator of at most 1000 characters")
            contents = [read_text(context, path)[1] for path in paths]
            return {**_save(context, parameters["output_path"], separator.join(contents)),
                    "sources": len(paths)}
        return self.run(operation)


class ExtractTextLines(DocumentWriteAction):
    name = "extract_text_lines"
    description = "Save a selected line range to a new UTF-8 document"
    parameters_schema = {**PATH_OUTPUT, "start_line": {"type": "integer", "required": True,
                                                       "minimum": 1},
                         "end_line": {"type": "integer", "required": True, "minimum": 1}}
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            _, text = read_text(context, parameters["path"])
            lines = text.splitlines(keepends=True)
            start, end = parameters["start_line"], parameters["end_line"]
            if start < 1 or end < start or end > len(lines):
                raise ValueError("Line range is outside the document")
            return {**_save(context, parameters["output_path"], "".join(lines[start - 1:end])),
                    "lines": end - start + 1}
        return self.run(operation)


class NormalizeTextWhitespace(DocumentWriteAction):
    name = "normalize_text_whitespace"
    description = "Normalize line endings and trailing spaces in a new document"
    parameters_schema = PATH_OUTPUT
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            _, text = read_text(context, parameters["path"])
            normalized = "\n".join(line.rstrip() for line in text.splitlines())
            if text.endswith(("\n", "\r")):
                normalized += "\n"
            return {**_save(context, parameters["output_path"], normalized),
                    "changed": normalized != text}
        return self.run(operation)
