from deskagent.perception.accessibility import (
    ElementLocator,
    ElementQuery,
    Point,
    Size,
    UIElement,
)


def element(identifier, role, title=None, children=None, **kwargs):
    values = dict(
        id=identifier,
        locator=f"ax://1/{identifier}",
        role=role,
        title=title,
        position=Point(10, 10),
        size=Size(100, 30),
        children=children or [],
        application="Safari",
    )
    values.update(kwargs)
    return UIElement(**values)


def test_fuzzy_search_returns_best_match_with_confidence_and_context():
    root = element(
        "root",
        "AXApplication",
        children=[
            element("cancel", "AXButton", "Отмена"),
            element("publish", "AXButton", "Опубликовать"),
        ],
    )

    match = ElementLocator().find_one(
        root,
        ElementQuery(
            application="safari",
            role="button",
            text="Опубликоват",
            fuzzy=True,
            visible_only=True,
        ),
    )

    assert match.element.id == "publish"
    assert 0.9 < match.confidence < 1
    assert match.exact is False
    assert match.matched_field == "title"


def test_filters_invisible_and_disabled_elements():
    hidden = element("hidden", "AXButton", "Run", size=Size(0, 0))
    disabled = element("disabled", "AXButton", "Run", enabled=False)
    enabled = element("enabled", "AXButton", "Run")
    root = element("root", "AXApplication", children=[hidden, disabled, enabled])

    matches = ElementLocator().find_all(
        root,
        ElementQuery(role="AXButton", text="Run", visible_only=True, enabled_only=True),
    )

    assert [match.element.id for match in matches] == ["enabled"]


def test_exact_search_checks_value_description_and_identifier():
    field = element(
        "field", "AXTextField", value="hello", attributes={"identifier": "search-input"}
    )
    root = element("root", "AXApplication", children=[field])

    match = ElementLocator().find_one(root, ElementQuery(text="search-input"))

    assert match.element is field
    assert match.exact is True
    assert match.matched_field == "identifier"
