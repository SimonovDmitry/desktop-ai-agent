"""Service contract for portable documents operations."""
from abc import ABC, abstractmethod


class DocumentService(ABC):

    @staticmethod
    @abstractmethod
    def source_path(context, value, extensions=None):
        """Perform the operation under the caller's filesystem policy."""

    @staticmethod
    @abstractmethod
    def output_path(context, value, extensions):
        """Perform the operation under the caller's filesystem policy."""

    @staticmethod
    @abstractmethod
    def read_text(context, value):
        """Perform the operation under the caller's filesystem policy."""

    @staticmethod
    @abstractmethod
    def save_new(context, value, suffixes, writer):
        """Perform the operation under the caller's filesystem policy."""

    @staticmethod
    @abstractmethod
    def pdf_reader(context, value):
        """Perform the operation under the caller's filesystem policy."""

    @staticmethod
    @abstractmethod
    def pages(path, limit=100):
        """Execute a bounded portable operation."""

    @staticmethod
    @abstractmethod
    def pdf_writer():
        """Create a writer for a new PDF document."""
