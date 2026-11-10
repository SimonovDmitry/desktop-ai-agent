from __future__ import annotations

import mimetypes
import os
import re
import shutil
import subprocess
import threading
import time
import uuid
from pathlib import Path
from urllib.parse import unquote, urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

from deskagent.actions.browser.cdp import CDPBackend
from deskagent.actions.browser.models import (
    BackendKind,
    BrowserInfo,
    BrowserKind,
    BrowserNotSupportedError,
    BrowserTargetError,
    DownloadItem,
)
from deskagent.actions.browser.safari import SafariBackend
from deskagent.actions.browser.security import BrowserSecurityPolicy


class _ValidatingRedirectHandler(HTTPRedirectHandler):
    def __init__(self, policy):
        self.policy = policy

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        self.policy.validate_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


class BrowserManager:
    BROWSERS = (
        ("chrome", "Google Chrome", BrowserKind.CHROME, "/Applications/Google Chrome.app", 9222),
        ("edge", "Microsoft Edge", BrowserKind.EDGE, "/Applications/Microsoft Edge.app", 9223),
        ("chromium", "Chromium", BrowserKind.CHROMIUM, "/Applications/Chromium.app", 9224),
        ("safari", "Safari", BrowserKind.SAFARI, "/Applications/Safari.app", None),
    )

    def __init__(self):
        self.policy = BrowserSecurityPolicy()
        self.timeout = 15.0
        self._settings_identity = None
        self._preferred_browser = None
        self.profile_root = Path("~/.deskagent/browser-profiles").expanduser()
        self._active_tabs = {}
        self._downloads = {}
        self._download_cancel = {}
        self._download_lock = threading.RLock()

    def configure(self, settings):
        if settings is None or id(settings) == self._settings_identity:
            return self
        self._settings_identity = id(settings)
        browser = getattr(settings, "browser", None)
        self.timeout = float(getattr(browser, "command_timeout", 15.0))
        self._preferred_browser = getattr(browser, "preferred_browser", None) or None
        self.profile_root = Path(getattr(browser, "profile_root", "~/.deskagent/browser-profiles")).expanduser()
        self.policy = BrowserSecurityPolicy.from_settings(settings)
        return self

    def list_browsers(self):
        running = self._running_applications()
        result = []
        for browser_id, name, kind, path, port in self.BROWSERS:
            installed = Path(path).exists() or bool(shutil.which(browser_id))
            is_running = name in running or (browser_id == "safari" and "Safari" in running)
            backend = None
            if browser_id == "safari" and SafariBackend(self.timeout).available():
                backend = BackendKind.SAFARI
                is_running = True
            elif port and CDPBackend(port, timeout=self.timeout, browser_id=browser_id).available():
                backend = BackendKind.CDP
                is_running = True
            result.append(BrowserInfo(browser_id, name, kind, path, installed, is_running, backend, port))
        return result

    def default_browser(self):
        if self._preferred_browser:
            return self._browser_info(self._preferred_browser)
        if shutil.which("osascript"):
            script = 'id of app (path to default application for URL "https://example.com")'
            result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, check=False)
            bundle_id = result.stdout.strip().lower()
            mapping = {
                "com.google.chrome": "chrome", "com.microsoft.edgemac": "edge",
                "org.chromium.chromium": "chromium", "com.apple.safari": "safari",
            }
            if bundle_id in mapping:
                return self._browser_info(mapping[bundle_id])
        return next((item for item in self.list_browsers() if item.installed), self.list_browsers()[-1])

    def launch(self, browser=None, url=None, incognito=False, headless=False):
        info = self._browser_info(browser or self.default_browser().id)
        if not info.installed:
            raise BrowserTargetError(f"Browser is not installed: {info.name}")
        args = ["open", "-a", info.name]
        if info.kind != BrowserKind.SAFARI:
            profile = (self.profile_root / info.id).resolve()
            profile.mkdir(parents=True, exist_ok=True)
            args.insert(1, "-n")
            flags = [
                f"--remote-debugging-port={info.debug_port}",
                "--remote-allow-origins=http://127.0.0.1",
                f"--user-data-dir={profile}",
            ]
            if incognito:
                flags.append("--incognito")
            if headless:
                flags.extend(["--headless=new", "--disable-gpu"])
            if url:
                flags.append(self.policy.validate_url(url, allow_internal=True))
            args.extend(["--args", *flags])
        elif url:
            args.append(self.policy.validate_url(url, allow_internal=True))
        process = subprocess.run(args, capture_output=True, text=True, check=False)
        if process.returncode:
            raise RuntimeError(process.stderr.strip() or f"Failed to launch {info.name}")
        deadline = time.monotonic() + self.timeout
        while time.monotonic() < deadline:
            if self._backend(info.id, require=False):
                break
            time.sleep(0.15)
        return {"browser": info.id, "launched": True, "backend": self._backend_name(info.id)}

    def status(self, browser=None):
        browser_id = browser or self.default_browser().id
        info = next((item for item in self.list_browsers() if item.id == browser_id), self._browser_info(browser_id))
        tabs = []
        backend = self._backend(info.id, require=False)
        if backend:
            tabs = backend.list_tabs()
        return {**info.to_dict(), "connected": backend is not None, "tab_count": len(tabs)}

    def active_browser(self):
        candidates = [item for item in self.list_browsers() if item.running and item.backend]
        if not candidates:
            return None
        if self._preferred_browser:
            preferred = next((item for item in candidates if item.id == self._preferred_browser), None)
            if preferred:
                return preferred
        return candidates[0]

    def list_tabs(self, browser=None):
        browser_id, backend = self._resolve(browser)
        tabs = backend.list_tabs()
        active_id = self._active_tabs.get(browser_id)
        for index, tab in enumerate(tabs):
            tab.active = tab.active or tab.id == active_id or (active_id is None and index == 0)
        return tabs

    def active_tab(self, browser=None):
        tabs = self.list_tabs(browser)
        if not tabs:
            raise BrowserTargetError("Browser has no open tabs")
        return next((tab for tab in tabs if tab.active), tabs[0])

    def open_tab(self, url="about:blank", browser=None, activate=True):
        safe_url = self.policy.validate_url(url, allow_internal=True)
        browser_id, backend = self._resolve(browser)
        created = backend.open_tab(safe_url)
        tab_id = created.get("id") if isinstance(created, dict) else None
        if not tab_id:
            tabs = backend.list_tabs()
            tab_id = tabs[-1].id if tabs else None
        if activate and tab_id:
            backend.activate_tab(tab_id)
            self._active_tabs[browser_id] = tab_id
        return self._tab_dict(browser_id, tab_id)

    def close_tab(self, tab_id=None, browser=None):
        browser_id, backend, tab = self._target(browser, tab_id)
        result = backend.close_tab(tab.id)
        self._active_tabs.pop(browser_id, None)
        return {"tab_id": tab.id, "closed": bool(result is not False)}

    def activate_tab(self, tab_id, browser=None):
        browser_id, backend, tab = self._target(browser, tab_id)
        backend.activate_tab(tab.id)
        self._active_tabs[browser_id] = tab.id
        return {"tab_id": tab.id, "active": True}

    def duplicate_tab(self, tab_id=None, browser=None):
        _, _, tab = self._target(browser, tab_id)
        return self.open_tab(tab.url, browser, activate=True)

    def pin_tab(self, tab_id, pinned=True, browser=None):
        browser_id, backend, tab = self._target(browser, tab_id)
        if not isinstance(backend, CDPBackend):
            raise BrowserNotSupportedError("Pinning tabs is only available through a Chromium CDP backend")
        result = backend.browser_command("Target.getTargets")
        info = next((item for item in result.get("targetInfos", []) if item.get("targetId") == tab.id), None)
        if info is None:
            raise BrowserTargetError(f"Browser tab not found: {tab.id}")
        # Stable CDP exposes no cross-version command for browser-strip pinning.
        raise BrowserNotSupportedError("The connected browser/CDP version does not expose tab pinning")

    def move_tab(self, tab_id, index, browser=None):
        _, backend, tab = self._target(browser, tab_id)
        if isinstance(backend, SafariBackend):
            raise BrowserNotSupportedError("Safari AppleScript does not expose tab reordering")
        raise BrowserNotSupportedError("CDP does not expose browser-strip tab reordering")

    def reopen_closed_tab(self, browser=None):
        browser_id, backend = self._resolve(browser)
        if isinstance(backend, SafariBackend):
            raise BrowserNotSupportedError("Safari AppleScript does not expose recently closed tabs")
        # Chromium's stable CDP API has no session-restore primitive.
        raise BrowserNotSupportedError(
            f"Reopening closed tabs is not exposed by {browser_id}'s CDP endpoint"
        )

    def navigate(self, url, tab_id=None, browser=None):
        safe_url = self.policy.validate_url(url, allow_internal=True)
        _, backend, tab = self._target(browser, tab_id)
        result = backend.command("Page.navigate", {"url": safe_url}, tab.id)
        return {"tab_id": tab.id, "url": safe_url, **result}

    def page_command(self, method, params=None, tab_id=None, browser=None):
        _, backend, tab = self._target(browser, tab_id)
        return backend.command(method, params or {}, tab.id)

    def evaluate(self, expression, tab_id=None, browser=None, *, user_script=False):
        _, backend, tab = self._target(browser, tab_id)
        if user_script:
            expression = self.policy.validate_javascript(expression, tab.url)
        result = backend.command(
            "Runtime.evaluate",
            {"expression": expression, "returnByValue": True, "awaitPromise": True, "userGesture": False},
            tab.id,
        )
        remote = result.get("result", result)
        if remote.get("subtype") == "error" or result.get("exceptionDetails"):
            details = result.get("exceptionDetails", {})
            raise RuntimeError(details.get("text") or remote.get("description") or "Page JavaScript failed")
        return remote.get("value")

    def wait(self, predicate, timeout=None, interval=0.2):
        deadline = time.monotonic() + (timeout or self.timeout)
        last_error = None
        while time.monotonic() < deadline:
            try:
                value = predicate()
                if value:
                    return value
            except Exception as exc:
                last_error = exc
            time.sleep(interval)
        if last_error:
            raise TimeoutError(f"Browser wait timed out; last error: {last_error}")
        raise TimeoutError("Browser wait timed out")

    def download(self, url, directory=None, filename=None, headers=None):
        safe_url = self.policy.validate_url(url)
        target_dir = self.policy.validate_download_path(directory)
        download_id = uuid.uuid4().hex
        parsed_name = Path(unquote(urlparse(safe_url).path)).name or "download"
        safe_name = self._safe_filename(filename or parsed_name)
        item = DownloadItem(download_id, safe_url, safe_name, str(target_dir / safe_name), started_at=time.time())
        cancel = threading.Event()
        with self._download_lock:
            self._downloads[download_id] = item
            self._download_cancel[download_id] = cancel
        thread = threading.Thread(
            target=self._download_worker, args=(item, cancel, headers or {}), daemon=True,
            name=f"deskagent-download-{download_id[:8]}",
        )
        thread.start()
        return item

    def list_downloads(self):
        with self._download_lock:
            return list(self._downloads.values())

    def download_status(self, download_id):
        with self._download_lock:
            try:
                return self._downloads[download_id]
            except KeyError as exc:
                raise BrowserTargetError(f"Download not found: {download_id}") from exc

    def wait_download(self, download_id, timeout=None):
        item = self.wait(lambda: self._finished_download(download_id), timeout)
        return item

    def cancel_download(self, download_id):
        self.download_status(download_id)
        self._download_cancel[download_id].set()
        return {"download_id": download_id, "cancel_requested": True}

    def reveal_download(self, download_id):
        item = self.download_status(download_id)
        if item.state != "completed" or not item.path or not Path(item.path).exists():
            raise BrowserTargetError("Downloaded file is not available")
        process = subprocess.run(["open", "-R", item.path], capture_output=True, text=True, check=False)
        if process.returncode:
            raise RuntimeError(process.stderr.strip() or "Failed to reveal downloaded file")
        return {"download_id": download_id, "path": item.path, "revealed": True}

    def _download_worker(self, item, cancel, headers):
        partial = Path(item.path + ".part")
        try:
            request = Request(item.url, headers={"User-Agent": "DeskAgent/1.0", **headers})
            opener = build_opener(_ValidatingRedirectHandler(self.policy))
            with opener.open(request, timeout=self.timeout) as response, partial.open("wb") as output:
                item.total_bytes = self._content_length(response.headers.get("Content-Length"))
                content_type = response.headers.get_content_type()
                if item.filename == "download":
                    extension = mimetypes.guess_extension(content_type) or ""
                    item.filename += extension
                    item.path += extension
                while not cancel.is_set():
                    chunk = response.read(65536)
                    if not chunk:
                        break
                    output.write(chunk)
                    item.received_bytes += len(chunk)
            if cancel.is_set():
                item.state = "cancelled"
                partial.unlink(missing_ok=True)
            else:
                os.replace(partial, item.path)
                item.state = "completed"
        except Exception as exc:
            item.state = "failed"
            item.error = str(exc)
            partial.unlink(missing_ok=True)

    def _finished_download(self, download_id):
        item = self.download_status(download_id)
        return item if item.state in {"completed", "failed", "cancelled"} else None

    def _resolve(self, browser=None):
        active = self.active_browser()
        browser_id = browser or (active.id if active else self.default_browser().id)
        return browser_id, self._backend(browser_id)

    def _target(self, browser=None, tab_id=None):
        browser_id, backend = self._resolve(browser)
        tabs = backend.list_tabs()
        wanted = tab_id or self._active_tabs.get(browser_id)
        tab = next((item for item in tabs if item.id == wanted), None) if wanted else None
        tab = tab or next((item for item in tabs if item.active), None) or (tabs[0] if tabs else None)
        if tab is None:
            raise BrowserTargetError("Browser has no open page tabs")
        return browser_id, backend, tab

    def _backend(self, browser_id, require=True):
        info = self._browser_info(browser_id)
        if info.kind == BrowserKind.SAFARI:
            backend = SafariBackend(self.timeout)
        else:
            backend = CDPBackend(info.debug_port, timeout=self.timeout, browser_id=info.id)
        if backend.available():
            return backend
        if require:
            hint = (
                f"Launch {info.name} through launch_browser so remote debugging is enabled"
                if info.kind != BrowserKind.SAFARI else "Launch Safari and grant Automation permission"
            )
            raise BrowserTargetError(f"Semantic browser backend is unavailable. {hint}")
        return None

    def _backend_name(self, browser_id):
        backend = self._backend(browser_id, require=False)
        if isinstance(backend, CDPBackend):
            return BackendKind.CDP.value
        if isinstance(backend, SafariBackend):
            return BackendKind.SAFARI.value
        return None

    def _browser_info(self, browser_id):
        normalized = str(browser_id).lower().replace("google ", "").replace("microsoft ", "")
        for item in self.list_browsers_shallow():
            if normalized in {item.id, item.name.lower()}:
                return item
        raise BrowserTargetError(f"Unsupported browser: {browser_id}")

    def list_browsers_shallow(self):
        return [
            BrowserInfo(identifier, name, kind, path, Path(path).exists(), False, None, port)
            for identifier, name, kind, path, port in self.BROWSERS
        ]

    def _tab_dict(self, browser_id, tab_id):
        tab = next((tab for tab in self.list_tabs(browser_id) if tab.id == tab_id), None)
        return tab.to_dict() if tab else {"id": tab_id, "browser": browser_id}

    @staticmethod
    def _running_applications():
        if not shutil.which("osascript"):
            return set()
        script = (
            'tell application "System Events" to get name of every application process '
            "whose background only is false"
        )
        result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, check=False)
        return {name.strip() for name in result.stdout.split(",") if name.strip()}

    @staticmethod
    def _safe_filename(value):
        name = re.sub(r"[\\/:*?\"<>|\x00-\x1f]", "_", Path(value).name).strip(". ")
        if not name:
            raise ValueError("Download filename is empty after sanitization")
        return name[:240]

    @staticmethod
    def _content_length(value):
        try:
            return int(value) if value is not None else None
        except ValueError:
            return None
