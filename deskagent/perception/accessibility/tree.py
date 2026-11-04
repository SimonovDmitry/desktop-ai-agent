from __future__ import annotations

from collections.abc import Iterable, Iterator

from deskagent.perception.accessibility.models import UIElement


def walk_tree(root: UIElement) -> Iterator[UIElement]:
    stack = [root]
    while stack:
        element = stack.pop()
        yield element
        stack.extend(reversed(element.children))


def flatten_tree(roots: UIElement | Iterable[UIElement]) -> list[UIElement]:
    if isinstance(roots, UIElement):
        roots = (roots,)
    return [element for root in roots for element in walk_tree(root)]


def find_by_id(
    roots: UIElement | Iterable[UIElement], element_id: str
) -> UIElement | None:
    return next(
        (element for element in flatten_tree(roots) if element.id == element_id), None
    )


def prune_tree(root: UIElement, max_depth: int) -> UIElement:
    if max_depth < 0:
        root.children = []
        return root
    root.children = [prune_tree(child, max_depth - 1) for child in root.children]
    return root
