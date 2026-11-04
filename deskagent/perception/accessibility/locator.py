from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher

from deskagent.perception.accessibility.models import (
    ElementQuery,
    UIElement,
    UIElementMatch,
)
from deskagent.perception.accessibility.tree import flatten_tree

ROLE_ALIASES = {
    "button": "AXButton",
    "checkbox": "AXCheckBox",
    "dialog": "AXDialog",
    "image": "AXImage",
    "link": "AXLink",
    "menu": "AXMenu",
    "menuitem": "AXMenuItem",
    "radiobutton": "AXRadioButton",
    "scrollarea": "AXScrollArea",
    "slider": "AXSlider",
    "statictext": "AXStaticText",
    "tab": "AXRadioButton",
    "table": "AXTable",
    "textarea": "AXTextArea",
    "textfield": "AXTextField",
    "toolbar": "AXToolbar",
    "window": "AXWindow",
}


def normalize_text(value: object) -> str:
    text = unicodedata.normalize("NFKC", str(value or "")).casefold().strip()
    return re.sub(r"\s+", " ", text)


def normalize_role(role: str | None) -> str | None:
    if not role:
        return None
    compact = re.sub(r"[\s_-]", "", role).casefold()
    if compact.startswith("ax"):
        return "AX" + role[2:]
    return ROLE_ALIASES.get(compact, role)


def element_text_fields(element: UIElement):
    return (
        ("title", element.title),
        (
            "value",
            element.value if isinstance(element.value, (str, int, float)) else None,
        ),
        ("description", element.description),
        ("identifier", element.attributes.get("identifier")),
        ("help", element.attributes.get("help")),
    )


def text_score(expected: str, actual: object, fuzzy: bool) -> tuple[float, bool]:
    expected_normalized, actual_normalized = (
        normalize_text(expected),
        normalize_text(actual),
    )
    if not expected_normalized or not actual_normalized:
        return 0.0, False
    if expected_normalized == actual_normalized:
        return 1.0, True
    if not fuzzy:
        return 0.0, False
    ratio = SequenceMatcher(None, expected_normalized, actual_normalized).ratio()
    if (
        expected_normalized in actual_normalized
        or actual_normalized in expected_normalized
    ):
        ratio = max(
            ratio,
            min(len(expected_normalized), len(actual_normalized))
            / max(len(expected_normalized), len(actual_normalized)),
        )
    return ratio, False


class ElementLocator:
    def find_all(
        self, roots, query: ElementQuery, limit: int | None = None
    ) -> list[UIElementMatch]:
        matches = []
        expected_role = normalize_role(query.role)
        for element in flatten_tree(roots):
            if query.locator and element.locator != query.locator:
                continue
            if query.application and normalize_text(
                element.application
            ) != normalize_text(query.application):
                continue
            if query.window and normalize_text(element.window) != normalize_text(
                query.window
            ):
                continue
            if expected_role and normalize_role(element.role) != expected_role:
                continue
            if query.visible_only and not element.visible:
                continue
            if query.enabled_only and not element.enabled:
                continue

            confidence, exact, field = 1.0, True, None
            if query.text is not None:
                scored = [
                    (text_score(query.text, value, query.fuzzy), name)
                    for name, value in element_text_fields(element)
                ]
                (confidence, exact), field = max(scored, key=lambda item: item[0][0])
                if confidence < query.minimum_confidence:
                    continue
            matches.append(UIElementMatch(element, confidence, exact, field))

        matches.sort(
            key=lambda item: (item.exact, item.confidence, item.element.visible),
            reverse=True,
        )
        return matches[:limit] if limit is not None else matches

    def find_one(self, roots, query: ElementQuery) -> UIElementMatch | None:
        matches = self.find_all(roots, query, limit=1)
        return matches[0] if matches else None
