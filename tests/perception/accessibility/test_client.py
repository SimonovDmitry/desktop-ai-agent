from deskagent.perception.accessibility import (
    AccessibilityClient,
    ElementQuery,
    Point,
    Size,
)


class FakeBackend:
    def __init__(self):
        self.nodes = {
            "app": {
                "AXRole": "AXApplication",
                "AXTitle": "Demo",
                "AXChildren": ["window"],
            },
            "window": {
                "AXRole": "AXWindow",
                "AXTitle": "Main",
                "AXPosition": Point(0, 0),
                "AXSize": Size(800, 600),
                "AXChildren": ["run", "input", "scroll"],
            },
            "run": {
                "AXRole": "AXButton",
                "AXTitle": "Run",
                "AXPosition": Point(10, 10),
                "AXSize": Size(80, 30),
                "AXEnabled": True,
                "actions": ["AXPress"],
            },
            "input": {
                "AXRole": "AXTextField",
                "AXValue": "old",
                "AXPosition": Point(10, 50),
                "AXSize": Size(200, 30),
            },
            "scroll": {
                "AXRole": "AXScrollArea",
                "AXPosition": Point(300, 50),
                "AXSize": Size(300, 400),
                "AXVerticalScrollBar": "scrollbar",
            },
            "scrollbar": {"AXRole": "AXScrollBar", "AXValue": 0.1},
        }
        self.performed = []

    @staticmethod
    def status():
        return {"supported": True, "trusted": True, "status": "granted"}

    def application(self, name=None):
        return "app", {"name": "Demo", "pid": 42, "bundle_id": "test.demo"}

    def copy_attribute(self, ref, attribute, default=None):
        if attribute == "AXWindows":
            return ["window"]
        if attribute == "AXFocusedWindow":
            return "window"
        return self.nodes[ref].get(attribute, default)

    def actions(self, ref):
        return self.nodes[ref].get("actions", [])

    def point(self, value):
        return value

    def size(self, value):
        return value

    def perform_action(self, ref, action):
        self.performed.append((ref, action))

    def set_attribute(self, ref, attribute, value):
        self.nodes[ref][attribute] = value


def test_builds_bounded_tree_and_stable_locators():
    client = AccessibilityClient(FakeBackend())

    root = client.application_tree("Demo", max_depth=1)

    assert root.role == "AXApplication"
    assert root.children[0].role == "AXWindow"
    assert root.children[0].attributes["truncated"] is True
    assert root.locator.startswith("ax://42/root")
    assert root.id == client.application_tree("Demo", max_depth=0).id


def test_find_perform_and_set_value_reuse_native_reference():
    backend = FakeBackend()
    client = AccessibilityClient(backend)

    match = client.find(ElementQuery(application="Demo", role="button", text="Run"))
    updated = client.perform(match.element.locator, "AXPress")
    field = client.find(ElementQuery(application="Demo", role="textfield"))
    changed = client.set_value(field.element.id, "new")

    assert backend.performed == [("run", "AXPress")]
    assert updated.title == "Run"
    assert changed.value == "new"


def test_window_tree_uses_named_window():
    client = AccessibilityClient(FakeBackend())

    root = client.window_tree("Demo", "Main")

    assert root.role == "AXWindow"
    assert root.window == "Main"
    assert len(root.children) == 3


def test_expansion_and_scroll_update_settable_ax_attributes():
    backend = FakeBackend()
    client = AccessibilityClient(backend)
    button = client.find(ElementQuery(application="Demo", role="button")).element
    scroll_area = client.find(
        ElementQuery(application="Demo", role="scrollarea")
    ).element

    client.set_expanded(button.id, True)
    client.scroll(scroll_area.id, "down", 0.5)

    assert backend.nodes["run"]["AXExpanded"] is True
    assert backend.nodes["scrollbar"]["AXValue"] == 0.6
