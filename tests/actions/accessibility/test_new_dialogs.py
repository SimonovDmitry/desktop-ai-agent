from types import SimpleNamespace
from unittest.mock import Mock

from deskagent.actions.accessibility.dialogs import GetActiveDialog
from deskagent.perception.accessibility.models import UIElement


def test_get_active_dialog_redacts_secure_field():
    secret = UIElement(id="secret", role="AXTextField", subrole="AXSecureTextField", value="private")
    dialog = UIElement(id="dialog", role="AXSheet", title="Sign in", children=[secret])
    root = UIElement(id="window", role="AXWindow", children=[dialog])
    client = Mock()
    client.window_tree.return_value = root
    context = SimpleNamespace(services=SimpleNamespace(accessibility=client))
    result = GetActiveDialog().execute(context, {})
    assert result.success
    assert result.data["dialog"]["children"][0]["value"] == "[REDACTED]"
