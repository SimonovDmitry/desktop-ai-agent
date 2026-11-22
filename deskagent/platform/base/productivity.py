"""Service contract for portable productivity operations."""
from abc import ABC, abstractmethod


class ProductivityService(ABC):

    @staticmethod
    @abstractmethod
    def store_path(context):
        """Perform the operation under the caller's filesystem policy."""

    @staticmethod
    @abstractmethod
    def with_store(context, operation):
        """Perform the operation under the caller's filesystem policy."""

    @staticmethod
    @abstractmethod
    def with_session(context, session_id, operation):
        """Perform the operation under the caller's filesystem policy."""

    @staticmethod
    @abstractmethod
    def rows(context, session_id, query, params=()):
        """Perform the operation under the caller's filesystem policy."""

    @staticmethod
    @abstractmethod
    def query_rows(context, query, params=()):
        """Perform the operation under the caller's filesystem policy."""
