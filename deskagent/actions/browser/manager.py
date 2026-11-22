"""Compatibility alias; implementation lives in deskagent.platform.macos.browser.manager."""
import sys
from importlib import import_module

sys.modules[__name__] = import_module("deskagent.platform.macos.browser.manager")
