# flake8: noqa: E501
import json

from deskagent.actions.browser.base import DangerousBrowserAction
from deskagent.actions.browser.page import PageAction, TARGET, TIMEOUT
from deskagent.actions.types import RiskLevel

SELECTOR = {"selector": {"type": "string", "required": True}, **TARGET}


class DOMAction(PageAction):
    discoverable = False

    @staticmethod
    def quoted(value):
        return json.dumps(value)

    def element_call(self, context, parameters, body):
        selector = self.quoted(parameters["selector"])
        expression = f"""(()=>{{const e=document.querySelector({selector});
if(!e) throw new Error('DOM element not found: '+{selector});{body}}})()"""
        return self.evaluate(context, parameters, expression)


class QueryDOMElement(DOMAction):
    name = "query_dom_element"
    description = "Query the first DOM element matching a CSS selector"
    parameters_schema = SELECTOR
    discoverable = True

    def execute(self, context, parameters):
        body = """const r=e.getBoundingClientRect();return JSON.stringify({tag:e.tagName.toLowerCase(),id:e.id||null,
classes:[...e.classList],text:(e.innerText||e.textContent||'').trim(),value:e.type==='password'?null:(e.value??null),
role:e.getAttribute('role'),name:e.getAttribute('name'),type:e.getAttribute('type'),visible:!!(r.width||r.height),
bounds:{x:r.x,y:r.y,width:r.width,height:r.height},disabled:!!e.disabled,checked:'checked'in e?!!e.checked:null});"""
        try:
            value = self.element_call(context, parameters, body)
            return self.success(json.loads(value) if isinstance(value, str) else value)
        except Exception as exc:
            return self.failure(exc)


class QueryDOMElements(DOMAction):
    name = "query_dom_elements"
    description = "Query DOM elements matching a CSS selector"
    parameters_schema = {**SELECTOR, "limit": {"type": "integer", "required": False, "default": 100, "minimum": 1, "maximum": 1000}}
    discoverable = True

    def execute(self, context, parameters):
        selector, limit = self.quoted(parameters["selector"]), parameters.get("limit", 100)
        expression = f"""[...document.querySelectorAll({selector})].slice(0,{limit}).map((e,index)=>{{const r=e.getBoundingClientRect();
return {{index,tag:e.tagName.toLowerCase(),id:e.id||null,text:(e.innerText||e.textContent||'').trim(),name:e.getAttribute('name'),
type:e.getAttribute('type'),visible:!!(r.width||r.height),bounds:{{x:r.x,y:r.y,width:r.width,height:r.height}}}}}})"""
        return self.run(context, lambda: {"elements": self.evaluate_json(context, parameters, expression)})


class ClickDOMElement(DOMAction):
    name = "click_dom_element"
    description = "Scroll to and semantically click a DOM element"
    parameters_schema = SELECTOR
    discoverable = True

    def execute(self, context, parameters):
        return self.run(context, lambda: {"clicked": bool(self.element_call(context, parameters, "e.scrollIntoView({block:'center'});e.click();return true;"))})


class FocusDOMElement(DOMAction):
    name = "focus_dom_element"
    description = "Focus a DOM element without coordinate input"
    parameters_schema = SELECTOR
    discoverable = True

    def execute(self, context, parameters):
        return self.run(context, lambda: {"focused": bool(self.element_call(context, parameters, "e.focus({preventScroll:false});return document.activeElement===e;"))})


class FillDOMInput(DOMAction):
    name = "fill_dom_input"
    description = "Set an input or textarea value and dispatch input/change events"
    parameters_schema = {**SELECTOR, "value": {"type": "string", "required": True}}
    discoverable = True

    def execute(self, context, parameters):
        value = self.quoted(parameters["value"])
        body = f"""if(!('value'in e))throw new Error('Element has no value');e.focus();
const p=Object.getPrototypeOf(e);const d=Object.getOwnPropertyDescriptor(p,'value');
if(d&&d.set)d.set.call(e,{value});else e.value={value};
e.dispatchEvent(new InputEvent('input',{{bubbles:true,inputType:'insertText',data:null}}));
e.dispatchEvent(new Event('change',{{bubbles:true}}));return true;"""
        return self.run(context, lambda: {"filled": bool(self.element_call(context, parameters, body))})


class ClearDOMInput(DOMAction):
    name = "clear_dom_input"
    description = "Clear an input or textarea and dispatch input/change events"
    parameters_schema = SELECTOR
    discoverable = True

    def execute(self, context, parameters):
        body = "if(!('value'in e))throw new Error('Element has no value');e.focus();e.value='';e.dispatchEvent(new InputEvent('input',{bubbles:true,inputType:'deleteContentBackward'}));e.dispatchEvent(new Event('change',{bubbles:true}));return true;"
        return self.run(context, lambda: {"cleared": bool(self.element_call(context, parameters, body))})


class SelectDOMOption(DOMAction):
    name = "select_dom_option"
    description = "Select an option by value in a DOM select element"
    parameters_schema = {**SELECTOR, "value": {"type": "string", "required": True}}
    discoverable = True

    def execute(self, context, parameters):
        value = self.quoted(parameters["value"])
        body = f"if(e.tagName!=='SELECT')throw new Error('Element is not a select');e.value={value};if(e.value!=={value})throw new Error('Option not found');e.dispatchEvent(new Event('input',{{bubbles:true}}));e.dispatchEvent(new Event('change',{{bubbles:true}}));return true;"
        return self.run(context, lambda: {"selected": bool(self.element_call(context, parameters, body)), "value": parameters["value"]})


class _CheckboxAction(DOMAction):
    discoverable = False
    checked = True

    def execute(self, context, parameters):
        expected = "true" if self.checked else "false"
        body = f"if(!('checked'in e))throw new Error('Element is not checkable');if(e.checked!=={expected})e.click();return e.checked==={expected};"
        return self.run(context, lambda: {"checked": bool(self.element_call(context, parameters, body))})


class CheckDOMCheckbox(_CheckboxAction):
    name = "check_dom_checkbox"
    description = "Check a DOM checkbox or radio control"
    parameters_schema = SELECTOR
    checked = True
    discoverable = True


class UncheckDOMCheckbox(_CheckboxAction):
    name = "uncheck_dom_checkbox"
    description = "Uncheck a DOM checkbox"
    parameters_schema = SELECTOR
    checked = False
    discoverable = True


class SubmitDOMForm(DOMAction):
    name = "submit_dom_form"
    description = "Submit a non-payment DOM form using requestSubmit"
    risk_level = RiskLevel.MEDIUM
    requires_confirmation = True
    parameters_schema = SELECTOR
    discoverable = True

    def execute(self, context, parameters):
        body = "const f=e.tagName==='FORM'?e:e.form;if(!f)throw new Error('No form associated with element');f.requestSubmit();return true;"
        return self.run(context, lambda: {"submitted": bool(self.element_call(context, parameters, body))})


class ScrollPage(PageAction):
    name = "scroll_page"
    description = "Scroll the page by pixels or to an absolute position"
    parameters_schema = {
        "x": {"type": "integer", "required": False, "default": 0},
        "y": {"type": "integer", "required": True},
        "absolute": {"type": "boolean", "required": False, "default": False}, **TARGET,
    }
    discoverable = True

    def execute(self, context, parameters):
        method = "scrollTo" if parameters.get("absolute", False) else "scrollBy"
        expression = f"window.{method}({parameters.get('x', 0)},{parameters['y']});JSON.stringify({{x:scrollX,y:scrollY}})"
        try:
            value = self.evaluate(context, parameters, expression)
            return self.success(json.loads(value) if isinstance(value, str) else value)
        except Exception as exc:
            return self.failure(exc)


class ScrollDOMElement(DOMAction):
    name = "scroll_dom_element"
    description = "Scroll a DOM element into view or by a pixel offset"
    parameters_schema = {
        **SELECTOR, "x": {"type": "integer", "required": False, "default": 0},
        "y": {"type": "integer", "required": False, "default": 0},
        "into_view": {"type": "boolean", "required": False, "default": True},
    }
    discoverable = True

    def execute(self, context, parameters):
        if parameters.get("into_view", True):
            body = "e.scrollIntoView({block:'center',inline:'nearest'});return true;"
        else:
            body = f"e.scrollBy({parameters.get('x', 0)},{parameters.get('y', 0)});return true;"
        return self.run(context, lambda: {"scrolled": bool(self.element_call(context, parameters, body))})


class WaitForDOMElement(DOMAction):
    name = "wait_for_dom_element"
    description = "Wait for a CSS selector to match a DOM element"
    parameters_schema = {**SELECTOR, **TIMEOUT}
    discoverable = True

    def execute(self, context, parameters):
        selector = self.quoted(parameters["selector"])
        try:
            found = self.manager(context).wait(
                lambda: self.evaluate(context, parameters, f"!!document.querySelector({selector})"), parameters.get("timeout", 15.0)
            )
            return self.success({"found": bool(found), "selector": parameters["selector"]})
        except Exception as exc:
            return self.failure(exc)


class WaitForDOMText(PageAction):
    name = "wait_for_dom_text"
    description = "Wait until visible page or element text contains a string"
    parameters_schema = {
        "text": {"type": "string", "required": True},
        "selector": {"type": "string", "required": False}, **TIMEOUT, **TARGET,
    }
    discoverable = True

    def execute(self, context, parameters):
        selector = json.dumps(parameters.get("selector")) if parameters.get("selector") else "null"
        text = json.dumps(parameters["text"])
        expression = f"(()=>{{const e={selector}?document.querySelector({selector}):document.body;return !!e&&(e.innerText||e.textContent||'').includes({text})}})()"
        try:
            found = self.manager(context).wait(lambda: self.evaluate(context, parameters, expression), parameters.get("timeout", 15.0))
            return self.success({"found": bool(found), "text": parameters["text"]})
        except Exception as exc:
            return self.failure(exc)


class ExtractDOMTable(DOMAction):
    name = "extract_dom_table"
    description = "Extract headers and cell values from an HTML table"
    parameters_schema = SELECTOR
    discoverable = True

    def execute(self, context, parameters):
        body = """if(e.tagName!=='TABLE')throw new Error('Element is not a table');
const rows=[...e.rows].map(r=>[...r.cells].map(c=>(c.innerText||'').trim()));
const headers=[...e.querySelectorAll('thead th')].map(c=>(c.innerText||'').trim());
return JSON.stringify({headers,rows,row_count:rows.length,column_count:Math.max(0,...rows.map(r=>r.length))});"""
        try:
            value = self.element_call(context, parameters, body)
            return self.success(json.loads(value) if isinstance(value, str) else value)
        except Exception as exc:
            return self.failure(exc)


class UploadFileToPage(DangerousBrowserAction):
    name = "upload_file_to_page"
    description = "Attach an allowlisted local file to a page file input"
    parameters_schema = {**SELECTOR, "path": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        manager = self.manager(context)
        try:
            path = manager.policy.validate_upload_path(parameters["path"])
            root = manager.page_command("DOM.getDocument", {"depth": 1}, parameters.get("tab_id"), parameters.get("browser"))
            node = manager.page_command(
                "DOM.querySelector", {"nodeId": root["root"]["nodeId"], "selector": parameters["selector"]},
                parameters.get("tab_id"), parameters.get("browser"),
            )
            if not node.get("nodeId"):
                raise RuntimeError(f"DOM element not found: {parameters['selector']}")
            manager.page_command(
                "DOM.setFileInputFiles", {"nodeId": node["nodeId"], "files": [str(path)]},
                parameters.get("tab_id"), parameters.get("browser"),
            )
            return self.success({"uploaded": True, "filename": path.name, "selector": parameters["selector"]})
        except Exception as exc:
            return self.failure(exc)


class SubmitPaymentForm(DangerousBrowserAction, DOMAction):
    name = "submit_payment_form"
    description = "Submit a payment form after explicit high-risk confirmation"
    parameters_schema = SELECTOR
    discoverable = True

    def execute(self, context, parameters):
        body = "const f=e.tagName==='FORM'?e:e.form;if(!f)throw new Error('No payment form found');f.requestSubmit();return true;"
        return self.run(context, lambda: {"submitted": bool(self.element_call(context, parameters, body)), "payment": True})
