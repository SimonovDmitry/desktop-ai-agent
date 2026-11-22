"""Browser automation backend contract."""
from abc import ABC, abstractmethod
from typing import Protocol


class BrowserBackend(ABC):
    @abstractmethod
    def available(self) -> bool:
        pass

    @abstractmethod
    def list_tabs(self):
        pass

    @abstractmethod
    def command(self, method: str, params: dict | None = None, tab_id: str | None = None):
        pass


class BrowserService(Protocol):
    def configure(self, settings):
        ...

    def list_browsers(self):
        ...

    def default_browser(self):
        ...

    def launch(self, browser=None, url=None, incognito=False, headless=False):
        ...

    def status(self, browser=None):
        ...

    def active_browser(self):
        ...

    def list_tabs(self, browser=None):
        ...

    def active_tab(self, browser=None):
        ...

    def open_tab(self, url='about:blank', browser=None, activate=True):
        ...

    def close_tab(self, tab_id=None, browser=None):
        ...

    def activate_tab(self, tab_id, browser=None):
        ...

    def duplicate_tab(self, tab_id=None, browser=None):
        ...

    def pin_tab(self, tab_id, pinned=True, browser=None):
        ...

    def move_tab(self, tab_id, index, browser=None):
        ...

    def reopen_closed_tab(self, browser=None):
        ...

    def navigate(self, url, tab_id=None, browser=None):
        ...

    def page_command(self, method, params=None, tab_id=None, browser=None):
        ...

    def evaluate(self, expression, tab_id=None, browser=None, *, user_script=False):
        ...

    def wait(self, predicate, timeout=None, interval=0.2):
        ...

    def download(self, url, directory=None, filename=None, headers=None):
        ...

    def list_downloads(self):
        ...

    def download_status(self, download_id):
        ...

    def wait_download(self, download_id, timeout=None):
        ...

    def cancel_download(self, download_id):
        ...

    def reveal_download(self, download_id):
        ...

    def list_browsers_shallow(self):
        ...
