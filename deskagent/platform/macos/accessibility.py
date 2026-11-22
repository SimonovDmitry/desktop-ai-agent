"""macOS Accessibility service with lazy AX initialization."""
from deskagent.platform.common.accessibility.client import AccessibilityClient


class MacOSAccessibilityService(AccessibilityClient):
    """Semantic Accessibility API backed by the native AX adapter."""
