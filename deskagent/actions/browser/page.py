# flake8: noqa: E501
import json

from deskagent.actions.browser.base import BrowserAction, DangerousBrowserAction

TARGET = {
    "tab_id": {"type": "string", "required": False},
    "browser": {"type": "string", "required": False},
}
TIMEOUT = {"timeout": {"type": "float", "required": False, "default": 15.0, "minimum": 0.1, "maximum": 300}}


class PageAction(BrowserAction):
    discoverable = False

    def evaluate(self, context, parameters, expression):
        p = parameters or {}
        return self.manager(context).evaluate(expression, p.get("tab_id"), p.get("browser"))

    def evaluate_json(self, context, parameters, expression):
        value = self.evaluate(context, parameters, f"JSON.stringify({expression})")
        return json.loads(value) if isinstance(value, str) else value


class NavigateToURL(BrowserAction):
    name = "navigate_to_url"
    description = "Navigate a browser tab to a security-validated URL"
    parameters_schema = {"url": {"type": "string", "required": True}, **TARGET}

    def execute(self, context, parameters):
        return self.run(context, self.manager(context).navigate, parameters["url"], parameters.get("tab_id"), parameters.get("browser"))


class ReloadPage(BrowserAction):
    name = "reload_page"
    description = "Reload a browser page, optionally bypassing cache"
    parameters_schema = {"ignore_cache": {"type": "boolean", "required": False, "default": False}, **TARGET}

    def execute(self, context, parameters):
        p = parameters or {}
        return self.run(context, self.manager(context).page_command, "Page.reload", {"ignoreCache": p.get("ignore_cache", False)}, p.get("tab_id"), p.get("browser"))


class StopPageLoading(BrowserAction):
    name = "stop_page_loading"
    description = "Stop loading resources in a browser tab"
    parameters_schema = TARGET

    def execute(self, context, parameters):
        p = parameters or {}
        return self.run(context, self.manager(context).page_command, "Page.stopLoading", {}, p.get("tab_id"), p.get("browser"))


class _HistoryAction(PageAction):
    discoverable = False
    delta = 0

    def execute(self, context, parameters):
        return self.run(context, self.evaluate, context, parameters, f"history.go({self.delta}); true")


class BrowserBack(_HistoryAction):
    name = "browser_back"
    description = "Navigate the active tab backward in session history"
    parameters_schema = TARGET
    delta = -1
    discoverable = True


class BrowserForward(_HistoryAction):
    name = "browser_forward"
    description = "Navigate the active tab forward in session history"
    parameters_schema = TARGET
    delta = 1
    discoverable = True


class WaitForNavigation(PageAction):
    name = "wait_for_navigation"
    description = "Wait until the page URL changes or matches an expected URL"
    parameters_schema = {"url": {"type": "string", "required": False}, **TIMEOUT, **TARGET}
    discoverable = True

    def execute(self, context, parameters):
        p = parameters or {}
        manager = self.manager(context)
        try:
            initial = self.evaluate(context, p, "location.href")
            expected = p.get("url")
            def navigated():
                current = self.evaluate(context, p, "location.href")
                return current if (current == expected if expected else current != initial) else None

            result = manager.wait(navigated, p.get("timeout", 15.0))
            return self.success({"url": result, "navigated": True})
        except Exception as exc:
            return self.failure(exc)


class WaitForPageReady(PageAction):
    name = "wait_for_page_ready"
    description = "Wait until document.readyState reaches interactive or complete"
    parameters_schema = {
        "state": {"type": "string", "required": False, "default": "complete", "enum": ["interactive", "complete"]},
        **TIMEOUT, **TARGET,
    }
    discoverable = True

    def execute(self, context, parameters):
        p = parameters or {}
        state = p.get("state", "complete")
        accepted = ["interactive", "complete"] if state == "interactive" else ["complete"]
        try:
            def ready():
                value = self.evaluate(context, p, "document.readyState")
                return value if value in accepted else None

            result = self.manager(context).wait(ready, p.get("timeout", 15.0))
            return self.success({"ready": True, "state": result})
        except Exception as exc:
            return self.failure(exc)


class GetPageURL(PageAction):
    name = "get_page_url"
    description = "Get the current page URL"
    parameters_schema = TARGET
    discoverable = True

    def execute(self, context, parameters):
        return self.run(context, lambda: {"url": self.evaluate(context, parameters, "location.href")})


class GetPageTitle(PageAction):
    name = "get_page_title"
    description = "Get the current page title"
    parameters_schema = TARGET
    discoverable = True

    def execute(self, context, parameters):
        return self.run(context, lambda: {"title": self.evaluate(context, parameters, "document.title")})


class GetPageMetadata(PageAction):
    name = "get_page_metadata"
    description = "Get URL, title, description, canonical URL, language, charset and viewport"
    parameters_schema = TARGET
    discoverable = True

    def execute(self, context, parameters):
        expression = """({
url:location.href,title:document.title,
description:document.querySelector('meta[name="description"]')?.content||null,
canonical_url:document.querySelector('link[rel="canonical"]')?.href||null,
language:document.documentElement.lang||null,charset:document.characterSet||null,
content_type:document.contentType||null,
viewport:{width:innerWidth,height:innerHeight,device_pixel_ratio:devicePixelRatio}
})"""
        return self.run(context, self.evaluate_json, context, parameters, expression)


class GetPageText(PageAction):
    name = "get_page_text"
    description = "Get visible text from the page body with an optional character limit"
    parameters_schema = {"max_characters": {"type": "integer", "required": False, "default": 50000, "minimum": 1, "maximum": 1000000}, **TARGET}
    discoverable = True

    def execute(self, context, parameters):
        limit = (parameters or {}).get("max_characters", 50000)
        return self.run(context, lambda: {"text": self.evaluate(context, parameters, f"(document.body?.innerText||'').slice(0,{limit})")})


class GetReadablePageContent(PageAction):
    name = "get_readable_page_content"
    description = "Extract readable main content and basic document metadata"
    parameters_schema = {"max_characters": {"type": "integer", "required": False, "default": 50000, "minimum": 1, "maximum": 1000000}, **TARGET}
    discoverable = True

    def execute(self, context, parameters):
        limit = (parameters or {}).get("max_characters", 50000)
        expression = f"""(()=>{{const root=document.querySelector('article,main,[role="main"]')||document.body;
return {{title:document.title,url:location.href,text:(root?.innerText||'').slice(0,{limit})}}}})()"""
        return self.run(context, self.evaluate_json, context, parameters, expression)


class GetSelectedPageText(PageAction):
    name = "get_selected_page_text"
    description = "Get text selected in the current web page"
    parameters_schema = TARGET
    discoverable = True

    def execute(self, context, parameters):
        return self.run(context, lambda: {"text": self.evaluate(context, parameters, "String(getSelection()||'')")})


class _PageCollection(PageAction):
    discoverable = False
    expression = "[]"
    key = "items"

    def execute(self, context, parameters):
        return self.run(context, lambda: {self.key: self.evaluate_json(context, parameters, self.expression)})


class GetPageLinks(_PageCollection):
    name = "get_page_links"
    description = "List page links with text, URL, target and relationship"
    parameters_schema = TARGET
    key = "links"
    expression = "[...document.querySelectorAll('a[href]')].map((e,i)=>({index:i,text:(e.innerText||e.ariaLabel||'').trim(),url:e.href,target:e.target||null,rel:e.rel||null}))"
    discoverable = True


class GetPageImages(_PageCollection):
    name = "get_page_images"
    description = "List page images with source, alt text and rendered dimensions"
    parameters_schema = TARGET
    key = "images"
    expression = "[...document.images].map((e,i)=>({index:i,src:e.currentSrc||e.src,alt:e.alt||'',width:e.naturalWidth,height:e.naturalHeight,rendered_width:e.clientWidth,rendered_height:e.clientHeight}))"
    discoverable = True


class GetPageForms(_PageCollection):
    name = "get_page_forms"
    description = "List forms and their non-secret controls"
    parameters_schema = TARGET
    key = "forms"
    expression = "[...document.forms].map((f,i)=>({index:i,id:f.id||null,name:f.name||null,action:f.action,method:f.method,controls:[...f.elements].map(e=>({tag:e.tagName.toLowerCase(),type:e.type||null,name:e.name||null,id:e.id||null,required:!!e.required,disabled:!!e.disabled,value:e.type==='password'?null:e.value}))}))"
    discoverable = True


class ExecutePageJavaScript(DangerousBrowserAction, PageAction):
    name = "execute_page_javascript"
    description = "Execute allowlisted JavaScript in a page; disabled by default"
    parameters_schema = {"javascript": {"type": "string", "required": True}, **TARGET}
    discoverable = True

    def execute(self, context, parameters):
        p = parameters or {}
        return self.run(
            context, self.manager(context).evaluate, p["javascript"], p.get("tab_id"), p.get("browser"),
            user_script=True,
        )
