"""Higher-level actions built on local Apple Vision OCR."""
from __future__ import annotations

import math
import struct
from pathlib import Path

from deskagent.actions.vision._image import ImageAction, _guard
from deskagent.actions.vision.screen import _capture, _ocr

PATH = {"path": {"type": "string", "required": False}}


def _recognize(context, value=None):
    temporary = None
    try:
        if value:
            path = Path(value).expanduser().resolve()
            decision = _guard(context).check("read_file", {"path": str(path)})
            if not decision.allowed:
                raise PermissionError(decision.reason)
            if path.suffix.lower() != ".png" or not path.is_file() or path.stat().st_size > 50_000_000:
                raise ValueError("OCR requires a PNG file under 50 MB")
        else:
            temporary = _capture()
            path = Path(temporary["path"])
        with path.open("rb") as stream:
            header = stream.read(24)
        if len(header) != 24 or header[:8] != b"\x89PNG\r\n\x1a\n":
            raise ValueError("OCR requires a valid PNG header")
        width, height = struct.unpack(">II", header[16:24])
        if width < 1 or height < 1 or width * height > 100_000_000:
            raise ValueError("Image dimensions exceed the OCR limit")
        lines = _ocr(str(path))
        if len(lines) > 5000:
            raise ValueError("OCR returned more than 5000 lines")
        return {"path": None if temporary else str(path), "width": width,
                "height": height, "lines": lines}
    finally:
        if temporary:
            Path(temporary["path"]).unlink(missing_ok=True)


def _box(line):
    return line["bounds"]


def _center(line):
    box = _box(line)
    return (box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)


class FindTextInImage(ImageAction):
    name = "find_text_in_image"
    description = "Find OCR lines containing a phrase and return image coordinates"
    parameters_schema = {**PATH, "query": {"type": "string", "required": True},
                         "case_sensitive": {"type": "boolean", "required": False, "default": False}}
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            query = parameters["query"].strip()
            if not query or len(query) > 200:
                raise ValueError("Query must contain 1-200 characters")
            image = _recognize(context, parameters.get("path"))
            needle = query if parameters.get("case_sensitive", False) else query.casefold()
            matches = [line for line in image["lines"] if needle in (
                line["text"] if parameters.get("case_sensitive", False) else line["text"].casefold()
            )]
            return {**{key: image[key] for key in ("path", "width", "height")},
                    "query": query, "matches": matches[:100], "total": len(matches),
                    "truncated": len(matches) > 100}
        return self.run(operation)


class GetTextInImageRegion(ImageAction):
    name = "get_text_in_image_region"
    description = "Read OCR lines whose centers fall within an image rectangle"
    parameters_schema = {**PATH, "x": {"type": "integer", "required": True, "minimum": 0},
                         "y": {"type": "integer", "required": True, "minimum": 0},
                         "width": {"type": "integer", "required": True, "minimum": 1},
                         "height": {"type": "integer", "required": True, "minimum": 1}}
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            image = _recognize(context, parameters.get("path"))
            x, y = parameters["x"], parameters["y"]
            width, height = parameters["width"], parameters["height"]
            if x < 0 or y < 0 or width < 1 or height < 1 or x + width > image["width"] or y + height > image["height"]:
                raise ValueError("Region must fit inside the image")
            lines = [line for line in image["lines"]
                     if x <= _center(line)[0] < x + width and y <= _center(line)[1] < y + height]
            return {"path": image["path"], "region": {"x": x, "y": y, "width": width, "height": height},
                    "lines": lines[:500], "total": len(lines), "truncated": len(lines) > 500}
        return self.run(operation)


class GetImageTextSummary(ImageAction):
    name = "get_image_text_summary"
    description = "Summarize OCR line count, word count and covered image area"
    parameters_schema = PATH
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            image = _recognize(context, parameters.get("path"))
            lines = image["lines"]
            area = sum(_box(line)["width"] * _box(line)["height"] for line in lines)
            return {"path": image["path"], "line_count": len(lines),
                    "word_count": sum(len(line["text"].split()) for line in lines),
                    "mean_confidence": round(sum(line["confidence"] for line in lines) / len(lines), 4)
                    if lines else None,
                    "approximate_coverage": round(min(1, area / (image["width"] * image["height"])), 4)}
        return self.run(operation)


class GetOcrConfidenceReport(ImageAction):
    name = "get_ocr_confidence_report"
    description = "Identify low-confidence OCR lines for review"
    parameters_schema = {**PATH, "threshold": {"type": "float", "required": False,
                                               "default": 0.75, "minimum": 0, "maximum": 1}}
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            threshold = parameters.get("threshold", 0.75)
            if not 0 <= threshold <= 1:
                raise ValueError("Confidence threshold must be 0-1")
            image = _recognize(context, parameters.get("path"))
            low = [line for line in image["lines"] if line["confidence"] < threshold]
            return {"path": image["path"], "threshold": threshold,
                    "low_confidence": low[:100], "total": len(low), "truncated": len(low) > 100}
        return self.run(operation)


class GetImageTextReadingOrder(ImageAction):
    name = "get_image_text_reading_order"
    description = "Sort OCR lines by top-to-bottom, then left-to-right coordinates"
    parameters_schema = PATH
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            image = _recognize(context, parameters.get("path"))
            ordered = sorted(image["lines"], key=lambda line: (_box(line)["y"], _box(line)["x"]))
            return {"path": image["path"], "lines": ordered[:500],
                    "total": len(ordered), "truncated": len(ordered) > 500}
        return self.run(operation)


class FindTextNearText(ImageAction):
    name = "find_text_near_text"
    description = "Find OCR lines nearest to a text anchor"
    parameters_schema = {**PATH, "anchor": {"type": "string", "required": True},
                         "limit": {"type": "integer", "required": False,
                                   "default": 5, "minimum": 1, "maximum": 20}}
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            anchor = parameters["anchor"].strip().casefold()
            limit = parameters.get("limit", 5)
            if not anchor or len(anchor) > 200 or not 1 <= limit <= 20:
                raise ValueError("Invalid anchor or limit")
            image = _recognize(context, parameters.get("path"))
            anchors = [line for line in image["lines"] if anchor in line["text"].casefold()]
            if not anchors:
                return {"path": image["path"], "anchors": [], "nearby": []}
            if len(anchors) > 1:
                raise ValueError("Anchor text is ambiguous")
            center = _center(anchors[0])
            nearby = sorted((line for line in image["lines"] if line is not anchors[0]),
                            key=lambda line: math.dist(center, _center(line)))
            return {"path": image["path"], "anchors": anchors,
                    "nearby": nearby[:limit]}
        return self.run(operation)


class CompareImageText(ImageAction):
    name = "compare_image_text"
    description = "Compare recognized text from two PNG images"
    parameters_schema = {"first_path": {"type": "string", "required": True},
                         "second_path": {"type": "string", "required": True}}
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            first = _recognize(context, parameters["first_path"])
            second = _recognize(context, parameters["second_path"])
            left = [line["text"] for line in first["lines"]]
            right = [line["text"] for line in second["lines"]]
            removed = sorted(set(left) - set(right))[:100]
            added = sorted(set(right) - set(left))[:100]
            return {"first_path": first["path"], "second_path": second["path"],
                    "identical_text": left == right, "removed_lines": removed,
                    "added_lines": added, "first_lines": len(left), "second_lines": len(right)}
        return self.run(operation)


class CountTextInImage(ImageAction):
    name = "count_text_in_image"
    description = "Count OCR lines containing a phrase without returning all text"
    parameters_schema = {**PATH, "query": {"type": "string", "required": True}}
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            query = parameters["query"].strip().casefold()
            if not query or len(query) > 200:
                raise ValueError("Query must contain 1-200 characters")
            image = _recognize(context, parameters.get("path"))
            matches = [line for line in image["lines"] if query in line["text"].casefold()]
            return {"path": image["path"], "query": parameters["query"],
                    "matching_lines": len(matches), "total_lines": len(image["lines"])}
        return self.run(operation)
