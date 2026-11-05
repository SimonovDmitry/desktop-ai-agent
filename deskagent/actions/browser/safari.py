from __future__ import annotations

import json
import shutil
import subprocess

from deskagent.actions.browser.base import BrowserBackend
from deskagent.actions.browser.models import (
    BackendKind,
    BrowserConnectionError,
    BrowserNotSupportedError,
    BrowserTab,
)


class SafariBackend(BrowserBackend):
    """Safari adapter using JXA/AppleScript without coordinate-based interaction."""

    def __init__(self, timeout=10.0):
        self.timeout = timeout

    def available(self) -> bool:
        if not shutil.which("osascript"):
            return False
        try:
            return bool(self._jxa("const s=Application('Safari'); return s.running();"))
        except BrowserConnectionError:
            return False

    def list_tabs(self):
        script = """
const s = Application('Safari');
if (!s.running()) return [];
const result = [];
const windows = s.windows();
for (let wi = 0; wi < windows.length; wi++) {
  const tabs = windows[wi].tabs();
  const current = windows[wi].currentTab();
  for (let ti = 0; ti < tabs.length; ti++) {
    result.push({
      id: `safari:${wi + 1}:${ti + 1}`,
      title: tabs[ti].name() || '',
      url: tabs[ti].url() || '',
      active: current && current.id() === tabs[ti].id()
    });
  }
}
return result;
"""
        return [
            BrowserTab(
                id=item["id"], title=item["title"], url=item["url"], active=item["active"],
                browser="safari", backend=BackendKind.SAFARI,
            )
            for item in self._jxa(script)
        ]

    def command(self, method: str, params=None, tab_id=None):
        params = params or {}
        if method == "Runtime.evaluate":
            return {"result": {"value": self.evaluate(params.get("expression", ""), tab_id)}}
        if method == "Page.navigate":
            self.navigate(params["url"], tab_id)
            return {}
        if method == "Page.reload":
            self.evaluate("location.reload()", tab_id)
            return {}
        if method == "Page.stopLoading":
            self.evaluate("window.stop()", tab_id)
            return {}
        raise BrowserNotSupportedError(f"Safari backend does not support command: {method}")

    def open_tab(self, url="about:blank"):
        script = """
const s=Application('Safari'); s.activate();
if (s.windows.length === 0) s.Document().make();
const tab=s.Tab({url: argv[0]}); s.windows[0].tabs.push(tab); s.windows[0].currentTab=tab;
return true;
"""
        return self._jxa(script, url)

    def close_tab(self, tab_id):
        window, tab = self._indices(tab_id)
        return self._jxa(
            "const s=Application('Safari'); "
            "s.windows[argv[0]-1].tabs[argv[1]-1].close(); return true;",
            window,
            tab,
        )

    def activate_tab(self, tab_id):
        window, tab = self._indices(tab_id)
        script = """
const s=Application('Safari'); const w=s.windows[argv[0]-1]; w.currentTab=w.tabs[argv[1]-1];
w.index=1; s.activate(); return true;
"""
        return self._jxa(script, window, tab)

    def navigate(self, url, tab_id=None):
        window, tab = self._indices(tab_id or self._active_tab_id())
        return self._jxa(
            "const s=Application('Safari'); s.windows[argv[0]-1].tabs[argv[1]-1].url=argv[2]; return true;",
            window, tab, url,
        )

    def evaluate(self, expression, tab_id=None):
        window, tab = self._indices(tab_id or self._active_tab_id())
        script = """
const s=Application('Safari'); const app=Application.currentApplication(); app.includeStandardAdditions=true;
const escaped=argv[2].replace(/\\/g,'\\\\').replace(/"/g,'\\"');
const source='tell application "Safari" to do JavaScript "' + escaped + '" in tab ' + argv[1] + ' of window ' + argv[0];
return app.runScript(source, {language: 'AppleScript'});
"""
        return self._jxa(script, window, tab, expression)

    def _active_tab_id(self):
        tabs = self.list_tabs()
        if not tabs:
            raise BrowserConnectionError("Safari has no open tabs")
        return next((tab.id for tab in tabs if tab.active), tabs[0].id)

    @staticmethod
    def _indices(tab_id):
        try:
            prefix, window, tab = str(tab_id).split(":")
            if prefix != "safari":
                raise ValueError
            return int(window), int(tab)
        except (TypeError, ValueError) as exc:
            raise BrowserConnectionError(f"Invalid Safari tab id: {tab_id}") from exc

    def _jxa(self, body, *args):
        source = (
            "function run(argv) { const value = (function() {\n"
            + body
            + "\n})(); return JSON.stringify(value); }"
        )
        try:
            result = subprocess.run(
                ["osascript", "-l", "JavaScript", "-e", source, *map(str, args)],
                capture_output=True, text=True, timeout=self.timeout, check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise BrowserConnectionError(f"Safari automation failed: {exc}") from exc
        if result.returncode:
            message = result.stderr.strip() or "unknown osascript error"
            if "JavaScript from Apple Events" in message:
                message += "; enable Safari Develop > Allow JavaScript from Apple Events"
            raise BrowserConnectionError(message)
        value = result.stdout.strip()
        if not value:
            return None
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            if value in {"true", "false"}:
                return value == "true"
            return value
