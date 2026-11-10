"""Bounded inspection of UTF-8 text and Markdown documents."""
from __future__ import annotations

import collections
import re

from deskagent.actions.documents._common import DocumentAction, read_text

PATH = {"path": {"type": "string", "required": True}}
WORD = re.compile(r"\w+(?:[-']\w+)*", re.UNICODE)


def _with_text(context, parameters, operation):
    path, text = read_text(context, parameters["path"])
    return {"path": str(path), **operation(text)}


def _paragraphs(text):
    return [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]


class InspectTextDocument(DocumentAction):
    name = "inspect_text_document"
    description = "Inspect UTF-8 text size, lines, words, paragraphs and newline style"
    parameters_schema = PATH
    discoverable = True

    def execute(self, context, parameters):
        return self.run(lambda: _with_text(context, parameters, lambda text: {
            "characters": len(text), "lines": len(text.splitlines()),
            "words": len(WORD.findall(text)), "paragraphs": len(_paragraphs(text)),
            "newline": "CRLF" if "\r\n" in text else "LF",
        }))


class ReadTextLines(DocumentAction):
    name = "read_text_lines"
    description = "Read a bounded numbered range of lines from a UTF-8 document"
    parameters_schema = {**PATH, "start_line": {"type": "integer", "required": False, "default": 1, "minimum": 1},
                         "line_count": {"type": "integer", "required": False, "default": 50,
                                        "minimum": 1, "maximum": 500}}
    discoverable = True

    def execute(self, context, parameters):
        def operation(text):
            lines = text.splitlines()
            start, count = parameters.get("start_line", 1), parameters.get("line_count", 50)
            if start < 1 or count < 1 or count > 500 or start > len(lines):
                raise ValueError("Invalid line range")
            return {"total_lines": len(lines), "lines": [
                {"number": index + 1, "text": lines[index][:2000]}
                for index in range(start - 1, min(start - 1 + count, len(lines)))
            ]}
        return self.run(lambda: _with_text(context, parameters, operation))


class GetDocumentHeadings(DocumentAction):
    name = "get_document_headings"
    description = "List Markdown headings with line numbers and hierarchy levels"
    parameters_schema = PATH
    discoverable = True

    def execute(self, context, parameters):
        def operation(text):
            found = []
            for number, line in enumerate(text.splitlines(), 1):
                match = re.match(r"^(#{1,6})\s+(.+?)\s*#*\s*$", line)
                if match:
                    found.append({"line": number, "level": len(match.group(1)), "title": match.group(2)})
            return {"headings": found[:500], "total": len(found), "truncated": len(found) > 500}
        return self.run(lambda: _with_text(context, parameters, operation))


class GetDocumentParagraphs(DocumentAction):
    name = "get_document_paragraphs"
    description = "Read bounded text paragraphs with paragraph numbers"
    parameters_schema = {**PATH, "start": {"type": "integer", "required": False, "default": 1, "minimum": 1},
                         "count": {"type": "integer", "required": False, "default": 20,
                                   "minimum": 1, "maximum": 100}}
    discoverable = True

    def execute(self, context, parameters):
        def operation(text):
            entries = _paragraphs(text)
            start, count = parameters.get("start", 1), parameters.get("count", 20)
            if start < 1 or count < 1 or count > 100:
                raise ValueError("Invalid paragraph range")
            return {"total": len(entries), "paragraphs": [
                {"number": index + 1, "text": entries[index][:3000]}
                for index in range(start - 1, min(start - 1 + count, len(entries)))
            ]}
        return self.run(lambda: _with_text(context, parameters, operation))


class GetDocumentWordFrequencies(DocumentAction):
    name = "get_document_word_frequencies"
    description = "Count frequent casefolded words in a UTF-8 document"
    parameters_schema = {**PATH, "limit": {"type": "integer", "required": False, "default": 30, "minimum": 1, "maximum": 200},
                         "min_length": {"type": "integer", "required": False, "default": 3,
                                        "minimum": 1, "maximum": 30}}
    discoverable = True

    def execute(self, context, parameters):
        def operation(text):
            minimum, limit = parameters.get("min_length", 3), parameters.get("limit", 30)
            if not 1 <= minimum <= 30 or not 1 <= limit <= 200:
                raise ValueError("Invalid frequency settings")
            counter = collections.Counter(word.casefold() for word in WORD.findall(text)
                                          if len(word) >= minimum)
            return {"words": [{"word": word, "count": count}
                              for word, count in counter.most_common(limit)],
                    "unique_words": len(counter)}
        return self.run(lambda: _with_text(context, parameters, operation))


class FindDuplicateParagraphs(DocumentAction):
    name = "find_duplicate_paragraphs"
    description = "Find repeated substantial paragraphs and their positions"
    parameters_schema = {**PATH, "min_characters": {"type": "integer", "required": False,
                                                    "default": 30, "minimum": 5, "maximum": 500}}
    discoverable = True

    def execute(self, context, parameters):
        def operation(text):
            positions = collections.defaultdict(list)
            minimum = parameters.get("min_characters", 30)
            for index, paragraph in enumerate(_paragraphs(text), 1):
                key = " ".join(paragraph.casefold().split())
                if len(key) >= minimum:
                    positions[key].append(index)
            found = [{"paragraphs": indices, "excerpt": key[:200]}
                     for key, indices in positions.items() if len(indices) > 1]
            return {"duplicates": found[:100], "total": len(found), "truncated": len(found) > 100}
        return self.run(lambda: _with_text(context, parameters, operation))


class GetDocumentLinks(DocumentAction):
    name = "get_document_links"
    description = "Extract Markdown and bare HTTP links with line numbers"
    parameters_schema = PATH
    discoverable = True

    def execute(self, context, parameters):
        def operation(text):
            pattern = re.compile(r"\[([^\]\n]{1,200})\]\(([^)\n]{1,1000})\)|https?://[^\s<>)]+")
            found = [{"line": text.count("\n", 0, match.start()) + 1,
                      "label": match.group(1), "url": match.group(2) or match.group()}
                     for match in pattern.finditer(text)]
            return {"links": found[:500], "total": len(found), "truncated": len(found) > 500}
        return self.run(lambda: _with_text(context, parameters, operation))


class GetMarkdownTasks(DocumentAction):
    name = "get_markdown_tasks"
    description = "List Markdown checkboxes and completion state"
    parameters_schema = PATH
    discoverable = True

    def execute(self, context, parameters):
        def operation(text):
            found = []
            for number, line in enumerate(text.splitlines(), 1):
                match = re.match(r"^\s*[-*]\s+\[([ xX])\]\s+(.+)$", line)
                if match:
                    found.append({"line": number, "done": match.group(1).lower() == "x",
                                  "text": match.group(2)[:500]})
            return {"tasks": found[:500], "total": len(found), "truncated": len(found) > 500,
                    "completed": sum(item["done"] for item in found)}
        return self.run(lambda: _with_text(context, parameters, operation))


class EstimateDocumentReadingTime(DocumentAction):
    name = "estimate_document_reading_time"
    description = "Estimate reading time from word count and reading speed"
    parameters_schema = {**PATH, "words_per_minute": {"type": "integer", "required": False,
                                                      "default": 220, "minimum": 50, "maximum": 1000}}
    discoverable = True

    def execute(self, context, parameters):
        def operation(text):
            speed = parameters.get("words_per_minute", 220)
            if not 50 <= speed <= 1000:
                raise ValueError("Reading speed must be 50-1000 words per minute")
            count = len(WORD.findall(text))
            return {"words": count, "words_per_minute": speed,
                    "estimated_minutes": round(count / speed, 2)}
        return self.run(lambda: _with_text(context, parameters, operation))
