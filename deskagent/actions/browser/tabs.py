from deskagent.actions.browser.base import BrowserAction

BROWSER = {"browser": {"type": "string", "required": False}}
TAB = {"tab_id": {"type": "string", "required": False}, **BROWSER}
REQUIRED_TAB = {"tab_id": {"type": "string", "required": True}, **BROWSER}


class ListBrowserTabs(BrowserAction):
    name = "list_browser_tabs"
    description = "List browser tabs with stable semantic target identifiers"
    parameters_schema = BROWSER

    def execute(self, context, parameters):
        return self.run(context, lambda: {
            "tabs": [tab.to_dict() for tab in self.manager(context).list_tabs((parameters or {}).get("browser"))]
        })


class GetActiveTab(BrowserAction):
    name = "get_active_tab"
    description = "Get the active browser tab"
    parameters_schema = BROWSER

    def execute(self, context, parameters):
        return self.run(context, lambda: self.manager(context).active_tab((parameters or {}).get("browser")).to_dict())


class OpenBrowserTab(BrowserAction):
    name = "open_browser_tab"
    description = "Open a validated URL in a new browser tab"
    parameters_schema = {
        "url": {"type": "string", "required": False, "default": "about:blank"},
        "activate": {"type": "boolean", "required": False, "default": True}, **BROWSER,
    }

    def execute(self, context, parameters):
        p = parameters or {}
        return self.run(
            context,
            self.manager(context).open_tab,
            p.get("url", "about:blank"),
            p.get("browser"),
            p.get("activate", True),
        )


class CloseBrowserTab(BrowserAction):
    name = "close_browser_tab"
    description = "Close a browser tab by target id, or the active tab"
    parameters_schema = TAB

    def execute(self, context, parameters):
        p = parameters or {}
        return self.run(context, self.manager(context).close_tab, p.get("tab_id"), p.get("browser"))


class ActivateBrowserTab(BrowserAction):
    name = "activate_browser_tab"
    description = "Activate a browser tab by target id"
    parameters_schema = REQUIRED_TAB

    def execute(self, context, parameters):
        return self.run(context, self.manager(context).activate_tab, parameters["tab_id"], parameters.get("browser"))


class DuplicateBrowserTab(BrowserAction):
    name = "duplicate_browser_tab"
    description = "Duplicate a browser tab and activate the copy"
    parameters_schema = TAB

    def execute(self, context, parameters):
        p = parameters or {}
        return self.run(context, self.manager(context).duplicate_tab, p.get("tab_id"), p.get("browser"))


class PinBrowserTab(BrowserAction):
    name = "pin_browser_tab"
    description = "Pin a browser tab when the semantic backend supports it"
    parameters_schema = REQUIRED_TAB

    def execute(self, context, parameters):
        return self.run(context, self.manager(context).pin_tab, parameters["tab_id"], True, parameters.get("browser"))


class UnpinBrowserTab(BrowserAction):
    name = "unpin_browser_tab"
    description = "Unpin a browser tab when the semantic backend supports it"
    parameters_schema = REQUIRED_TAB

    def execute(self, context, parameters):
        return self.run(
            context,
            self.manager(context).pin_tab,
            parameters["tab_id"],
            False,
            parameters.get("browser"),
        )


class MoveBrowserTab(BrowserAction):
    name = "move_browser_tab"
    description = "Move a tab to a browser-strip index when supported"
    parameters_schema = {**REQUIRED_TAB, "index": {"type": "integer", "required": True, "minimum": 0}}

    def execute(self, context, parameters):
        return self.run(
            context,
            self.manager(context).move_tab,
            parameters["tab_id"],
            parameters["index"],
            parameters.get("browser"),
        )


class ReopenClosedTab(BrowserAction):
    name = "reopen_closed_tab"
    description = "Reopen the most recently closed browser tab when supported"
    parameters_schema = BROWSER

    def execute(self, context, parameters):
        return self.run(context, self.manager(context).reopen_closed_tab, (parameters or {}).get("browser"))
