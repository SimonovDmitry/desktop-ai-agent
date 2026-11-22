"""Service contract for portable code operations."""
from abc import ABC, abstractmethod


class CodeService(ABC):

    @staticmethod
    @abstractmethod
    def project_dir(context, value):
        """Perform the operation under the caller's filesystem policy."""

    @staticmethod
    @abstractmethod
    def safe_file(context, project, value, *, required=True):
        """Perform the operation under the caller's filesystem policy."""

    @staticmethod
    @abstractmethod
    def read_source(context, project, value):
        """Perform the operation under the caller's filesystem policy."""

    @staticmethod
    @abstractmethod
    def walk_sources(context, project):
        """Perform the operation under the caller's filesystem policy."""

    @staticmethod
    @abstractmethod
    def git_names(context, project, *args):
        """Perform the operation under the caller's filesystem policy."""

    @staticmethod
    @abstractmethod
    def git_output(project, *args):
        """Execute a bounded portable operation."""

    @staticmethod
    @abstractmethod
    def run_project_tests(context, parameters):
        """Execute a bounded portable operation."""

    @staticmethod
    @abstractmethod
    def read_test_failures(context, parameters):
        """Execute a bounded portable operation."""

    @staticmethod
    @abstractmethod
    def check_ignored(context, project, path):
        """Execute a bounded portable operation."""

    @staticmethod
    @abstractmethod
    def git(project, *args, max_output=200_000):
        """Run Git with bounded text output."""
