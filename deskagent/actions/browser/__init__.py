"""Semantic browser automation actions backed by CDP and Safari automation."""

from deskagent.actions.browser.manager import BrowserManager
from deskagent.actions.browser.models import BrowserInfo, BrowserTab, DownloadItem

__all__ = ["BrowserManager", "BrowserInfo", "BrowserTab", "DownloadItem"]
