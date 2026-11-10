"""Platform contract for notes application operations."""
from abc import ABC, abstractmethod


class NotesService(ABC):
    @abstractmethod
    def call(self, operation: str, **parameters) -> dict:
        """Perform one validated notes operation and return structured data."""
