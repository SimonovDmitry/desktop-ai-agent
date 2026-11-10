"""Platform contract for music player and library operations."""
from abc import ABC, abstractmethod


class MusicService(ABC):
    @abstractmethod
    def call(self, operation: str, **parameters) -> dict:
        """Perform one validated music operation and return structured data."""
