"""Platform contract for screen capture and text recognition."""
from abc import ABC, abstractmethod


class VisionService(ABC):
    @abstractmethod
    def capture(self, window_id=None) -> dict:
        """Capture a screen or window and return private image metadata."""

    @abstractmethod
    def read_text(self, path: str) -> list[dict]:
        """Recognize text and bounds in a captured image."""
