"""Compatibility alias; implementation lives in deskagent.platform.common.browser.cdp."""
import sys
from importlib import import_module

sys.modules[__name__] = import_module("deskagent.platform.common.browser.cdp")
