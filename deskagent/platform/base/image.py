"""Platform contract for native image inspection and transforms."""
from abc import ABC, abstractmethod


class ImageService(ABC):
    @abstractmethod
    def source(self, context, path):
        """Validate and resolve an input image."""

    @abstractmethod
    def properties(self, context, path):
        """Read image dimensions and metadata."""

    @abstractmethod
    def transform(self, context, source, target, options, *, extensions=None):
        """Transform an image into a new guarded file."""

    @abstractmethod
    def hash(self, context, path):
        """Hash a validated image."""
