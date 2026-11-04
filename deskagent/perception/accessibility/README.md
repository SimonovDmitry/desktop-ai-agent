# Accessibility perception

The accessibility subsystem turns macOS `AXUIElement` objects into bounded,
serializable `UIElement` trees. It is intentionally split into small layers:

- `client.py` owns native references, tree snapshots and AX mutations;
- `models.py` defines stable public data contracts;
- `tree.py` provides traversal helpers;
- `locator.py` implements exact and fuzzy semantic search;
- `observer.py` implements cancellable polling for asynchronous interfaces;
- `permissions.py` handles the macOS trust check and system prompt;
- `serializer.py` prevents native PyObjC values from leaking into tool results.

Locators have the form `ax://<pid>/<index-path>?role=<role>&title=<hint>`. They
are stable while an application's accessibility hierarchy remains structurally
stable. The shorter element `id` is a hash of that locator. Native references
are cached only inside `AccessibilityClient`; callers receive JSON-safe values.

Tree reads default to a depth of 12 and 2,000 nodes. Actions allow callers to
lower those limits and enforce hard maxima in their schemas. Search supports AX
roles and friendly aliases such as `button`, `textfield` and `scrollarea`; text
is matched across title, value, description, identifier and help.

Example action call:

```json
{
  "action": "find_ui_element",
  "parameters": {
    "application": "PyCharm",
    "role": "button",
    "text": "Run",
    "fuzzy": true,
    "visible_only": true
  }
}
```

The returned match includes `exact`, `confidence`, bounds, application/window
context, supported AX actions, an element id and its locator. Pass either the id
or locator as `element` to interaction and wait actions.

The native backend is imported lazily, so models, locators and action contracts
remain testable on non-macOS CI. Actual tree access requires the process to be
enabled in **System Settings → Privacy & Security → Accessibility**.
