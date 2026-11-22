"""Resolve a user-visible target through AX, the active web page, or screen text."""

from __future__ import annotations

import json
from pathlib import Path

from deskagent.actions.vision.screen import _capture, _ocr
from deskagent.perception.accessibility.locator import normalize_text


def _dom_match(context, parameters):
    if parameters.get("locator") or parameters.get("application") or parameters.get("window"):
        raise LookupError("DOM lookup cannot use an AX locator or app/window filter")
    manager = context.services.browser
    if manager is None:
        raise LookupError("Browser backend is unavailable")
    manager.configure(context.settings)
    text = json.dumps(normalize_text(parameters.get("text")))
    role = json.dumps(normalize_text(parameters.get("role")))
    expression = f"""(()=>{{
const expectedText={text}, expectedRole={role};
const nodes=[...document.querySelectorAll('button,a,input,textarea,select,[role],[contenteditable]')];
const hits=[];
for(const e of nodes){{
 if(e.type==='password')continue;
 const r=e.getBoundingClientRect(); if(!r.width||!r.height||e.disabled)continue;
 const label=(e.getAttribute('aria-label')||e.labels?.[0]?.innerText||e.innerText||e.value||
  e.getAttribute('placeholder')||e.title||'').trim().toLocaleLowerCase();
 const inputRole=e.tagName==='INPUT'?
  ({{checkbox:'checkbox',radio:'radio',button:'button',submit:'button',search:'searchbox'}}[e.type]
  ||'textbox'):'';
 const role=(e.getAttribute('role')||inputRole||
  ({{BUTTON:'button',A:'link',TEXTAREA:'textbox',SELECT:'combobox'}}[e.tagName]||'')).toLocaleLowerCase();
 if(expectedText&&label!==expectedText)continue;
 if(expectedRole&&role!==expectedRole)continue;
 const path=[];let n=e;while(n&&n.nodeType===1&&n!==document.documentElement){{
  const index=[...n.parentElement.children].indexOf(n)+1;
  path.unshift(n.tagName.toLowerCase()+':nth-child('+index+')');n=n.parentElement;
 }}
 hits.push({{selector:path.join(' > '),text:label,role,bounds:{{x:r.x,y:r.y,width:r.width,height:r.height}}}});
 if(hits.length>1)break;
}}
return hits;
}})()"""
    matches = manager.evaluate(expression)
    if isinstance(matches, str):
        matches = json.loads(matches)
    if len(matches or []) != 1:
        raise LookupError(f"Expected one matching DOM target; found {len(matches or [])}")
    return {"source": "dom", **matches[0]}


def _ocr_match(parameters):
    if parameters.get("role") or parameters.get("locator") or parameters.get("application") or parameters.get("window"):
        raise LookupError("Screen text lookup only supports exact text")
    expected = normalize_text(parameters.get("text"))
    if not expected:
        raise ValueError("Text is required for screen lookup")
    capture = _capture()
    try:
        matches = [line for line in _ocr(capture["path"]) if normalize_text(line["text"]) == expected
                   and line["confidence"] >= parameters.get("minimum_confidence", 0.9)]
    finally:
        Path(capture["path"]).unlink(missing_ok=True)
    if len(matches) != 1:
        raise LookupError(f"Expected one matching screen text target; found {len(matches)}")
    return {"source": "ocr", **matches[0], "captured_at": capture["captured_at"]}


def resolve(context, parameters, client, ax_find):
    backend = parameters.get("backend", "auto")
    errors = []
    if backend in {"auto", "accessibility"}:
        try:
            match = ax_find(client, parameters)
            return {"source": "accessibility", "match": match}
        except Exception as exc:
            errors.append(f"Accessibility: {exc}")
    if backend in {"auto", "dom"}:
        try:
            return _dom_match(context, parameters)
        except Exception as exc:
            errors.append(f"DOM: {exc}")
    if backend in {"auto", "ocr"}:
        try:
            return _ocr_match(parameters)
        except Exception as exc:
            errors.append(f"OCR: {exc}")
    raise LookupError("; ".join(errors) or "Target was not found")
