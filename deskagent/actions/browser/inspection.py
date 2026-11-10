"""Bounded page observations and assertions for semantic browser automation."""

from __future__ import annotations

import hashlib
import json
import threading
import time

from deskagent.actions.browser.page import PageAction, TARGET
from deskagent.actions.types import ActionResult


SELECTOR = {"selector": {"type": "string", "required": True}, **TARGET}


def _page_state(action, context, parameters):
    state = action.evaluate_json(context, parameters, """({
        url:location.href,title:document.title,
        text:(document.body?.innerText||'').slice(0,200000)
    })""")
    text = state.pop("text", "")
    state["text_digest"] = hashlib.sha256(text.encode("utf-8")).hexdigest()
    state["text_length_sampled"] = len(text)
    return state


def _element_state(action, context, parameters):
    selector = json.dumps(parameters["selector"])
    return action.evaluate_json(context, parameters, f"""(()=>{{
        const e=document.querySelector({selector});
        if(!e)return {{exists:false}};
        const r=e.getBoundingClientRect();
        return {{exists:true,visible:!!(r.width&&r.height),enabled:!e.disabled,
            checked:'checked' in e?!!e.checked:null,
            text:(e.innerText||e.textContent||'').trim().slice(0,2000)}};
    }})()""")


def _matches_state(actual, parameters):
    expected = {key.removeprefix("expected_"): value for key, value in parameters.items()
                if key.startswith("expected_")}
    if not expected:
        raise ValueError("At least one expected state is required")
    mismatches = {key: {"expected": value, "actual": actual.get(key)}
                  for key, value in expected.items() if actual.get(key) != value}
    return mismatches


class GetPageSnapshot(PageAction):
    name = "get_page_snapshot"
    description = "Read the current page URL, title and bounded text digest for change detection"
    parameters_schema = TARGET
    discoverable = True

    def execute(self, context, parameters):
        return self.run(context, _page_state, self, context, parameters)


class WaitForPageChange(PageAction):
    name = "wait_for_page_change"
    description = "Wait until page URL, title or sampled text differs from a prior snapshot"
    parameters_schema = {
        "baseline": {"type": "dict", "required": True},
        "timeout": {"type": "float", "required": False, "default": 15, "minimum": 0.1, "maximum": 120},
        **TARGET,
    }
    discoverable = True

    def __init__(self):
        self._cancelled = threading.Event()

    def cancel(self):
        self._cancelled.set()

    def execute(self, context, parameters):
        try:
            baseline = parameters["baseline"]
            if not any(key in baseline for key in ("url", "title", "text_digest")):
                raise ValueError("Baseline must include a URL, title or text_digest")
            deadline = time.monotonic() + parameters.get("timeout", 15)
            while True:
                if self._cancelled.is_set():
                    return ActionResult(False, error="Wait was cancelled", error_code="ACTION_CANCELLED")
                current = _page_state(self, context, parameters)
                changed = [key for key in ("url", "title", "text_digest")
                           if key in baseline and baseline[key] != current[key]]
                if changed:
                    return ActionResult(True, {"changed": changed, "snapshot": current})
                if time.monotonic() >= deadline:
                    return ActionResult(False, {"snapshot": current}, "Page did not change", "TIMEOUT")
                self._cancelled.wait(0.2)
        except Exception as exc:
            return self.failure(exc)


class VerifyPageText(PageAction):
    name = "verify_page_text"
    description = "Assert that visible page or element text contains or excludes a phrase"
    parameters_schema = {
        "text": {"type": "string", "required": True},
        "selector": {"type": "string", "required": False},
        "absent": {"type": "boolean", "required": False, "default": False},
        **TARGET,
    }
    discoverable = True

    def execute(self, context, parameters):
        try:
            phrase = parameters["text"].strip()
            if not phrase:
                raise ValueError("Text must be non-empty")
            selector = json.dumps(parameters.get("selector"))
            expected = json.dumps(phrase.casefold())
            observed = self.evaluate(context, parameters, f"""(()=>{{
                const e={selector}?document.querySelector({selector}):document.body;
                if(!e)throw Error('Element not found');
                return (e.innerText||e.textContent||'').toLocaleLowerCase().includes({expected});
            }})()""")
            found = observed is True or observed == "true"
            verified = not found if parameters.get("absent") else found
            return ActionResult(verified, {"verified": verified, "found": found, "text": phrase},
                                None if verified else "Page text did not meet the assertion",
                                None if verified else "VERIFICATION_FAILED")
        except Exception as exc:
            return self.failure(exc)


class GetPageOutline(PageAction):
    name = "get_page_outline"
    description = "List visible page headings with levels and bounded text"
    parameters_schema = TARGET
    discoverable = True

    def execute(self, context, parameters):
        expression = """[...document.querySelectorAll('h1,h2,h3,h4,h5,h6')]
            .filter(e=>{const r=e.getBoundingClientRect();return r.width&&r.height})
            .slice(0,100).map(e=>({level:Number(e.tagName[1]),text:(e.innerText||'').trim().slice(0,300)}))"""
        return self.run(context, lambda: {"headings": self.evaluate_json(context, parameters, expression)})


class FindPageElementByRole(PageAction):
    name = "find_page_element_by_role"
    description = "Find a unique visible page control by ARIA role and optional accessible name"
    parameters_schema = {
        "role": {"type": "string", "required": True},
        "name": {"type": "string", "required": False},
        **TARGET,
    }
    discoverable = True

    def execute(self, context, parameters):
        try:
            role = json.dumps(parameters["role"].casefold())
            name = json.dumps((parameters.get("name") or "").casefold())
            expression = f"""(()=>{{const role={role},name={name};const matches=[];
            for(const e of document.querySelectorAll('[role],button,a,input,select,textarea')){{
              if(e.type==='password')continue;
              const r=e.getBoundingClientRect();if(!r.width||!r.height)continue;
              const inputRole=e.tagName==='INPUT'?
                ({{checkbox:'checkbox',radio:'radio',button:'button',submit:'button',search:'searchbox'}}[e.type]
                ||'textbox'):'';
              const current=(e.getAttribute('role')||inputRole||
                ({{BUTTON:'button',A:'link',SELECT:'combobox',TEXTAREA:'textbox'}}[e.tagName]||''))
                .toLocaleLowerCase();
              const label=(e.getAttribute('aria-label')||e.labels?.[0]?.innerText||
                e.innerText||e.getAttribute('placeholder')||e.title||'')
                .trim().toLocaleLowerCase();
              if(current!==role||(name&&label!==name))continue;
              const path=[];let n=e;
              while(n&&n.nodeType===1&&n!==document.documentElement){{
                const i=[...n.parentElement.children].indexOf(n)+1;
                path.unshift(n.tagName.toLowerCase()+':nth-child('+i+')');n=n.parentElement;
              }}
              matches.push({{selector:path.join(' > '),role:current,name:label,
                bounds:{{x:r.x,y:r.y,width:r.width,height:r.height}}}});
              if(matches.length>1)break;
            }}return matches;}})()"""
            matches = self.evaluate_json(context, parameters, expression)
            if len(matches) != 1:
                return ActionResult(False, {"matches": matches},
                                    f"Expected one matching page control; found {len(matches)}",
                                    "ELEMENT_NOT_FOUND" if not matches else "TARGET_AMBIGUOUS")
            return ActionResult(True, {"element": matches[0]})
        except Exception as exc:
            return self.failure(exc)


class CountDOMElements(PageAction):
    name = "count_dom_elements"
    description = "Count page elements matching a CSS selector, optionally visible only"
    parameters_schema = {
        **SELECTOR,
        "visible_only": {"type": "boolean", "required": False, "default": False},
    }
    discoverable = True

    def execute(self, context, parameters):
        try:
            selector = json.dumps(parameters["selector"])
            visible = "true" if parameters.get("visible_only") else "false"
            expression = f"""[...document.querySelectorAll({selector})]
                .filter(e=>!{visible}||(()=>{{const r=e.getBoundingClientRect();return r.width&&r.height}})()).length"""
            return ActionResult(True, {"selector": parameters["selector"],
                                       "count": self.evaluate_json(context, parameters, expression)})
        except Exception as exc:
            return self.failure(exc)


class VerifyDOMElementState(PageAction):
    name = "verify_dom_element_state"
    description = "Assert the existence, visibility, enabled state, checked state or text of a DOM element"
    parameters_schema = {
        **SELECTOR,
        "expected_exists": {"type": "boolean", "required": False},
        "expected_visible": {"type": "boolean", "required": False},
        "expected_enabled": {"type": "boolean", "required": False},
        "expected_checked": {"type": "boolean", "required": False},
        "expected_text": {"type": "string", "required": False},
    }
    discoverable = True

    def execute(self, context, parameters):
        try:
            actual = _element_state(self, context, parameters)
            mismatches = _matches_state(actual, parameters)
            verified = not mismatches
            return ActionResult(
                verified, {"verified": verified, "actual": actual, "mismatches": mismatches},
                None if verified else "DOM state did not match",
                None if verified else "VERIFICATION_FAILED",
            )
        except Exception as exc:
            return self.failure(exc)


class WaitForDOMElementState(VerifyDOMElementState):
    name = "wait_for_dom_element_state"
    description = "Wait until a DOM element matches the expected observable state"
    parameters_schema = {
        **VerifyDOMElementState.parameters_schema,
        "timeout": {"type": "float", "required": False, "default": 15, "minimum": 0.1, "maximum": 120},
    }

    def __init__(self):
        self._cancelled = threading.Event()

    def cancel(self):
        self._cancelled.set()

    def execute(self, context, parameters):
        try:
            deadline = time.monotonic() + parameters.get("timeout", 15)
            while True:
                if self._cancelled.is_set():
                    return ActionResult(False, error="Wait was cancelled", error_code="ACTION_CANCELLED")
                actual = _element_state(self, context, parameters)
                mismatches = _matches_state(actual, parameters)
                if not mismatches:
                    return ActionResult(True, {"verified": True, "actual": actual})
                if time.monotonic() >= deadline:
                    return ActionResult(False, {"actual": actual, "mismatches": mismatches},
                                        "DOM state did not match before timeout", "TIMEOUT")
                self._cancelled.wait(0.2)
        except Exception as exc:
            return self.failure(exc)
