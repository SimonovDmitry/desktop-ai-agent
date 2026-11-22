"""Service contract for portable audio operations."""
from abc import ABC, abstractmethod


class WavService(ABC):

    @staticmethod
    @abstractmethod
    def read_wav(context, path):
        """Perform the operation under the caller's filesystem policy."""

    @staticmethod
    @abstractmethod
    def write_wav(context, output_path, samples, channels, rate):
        """Perform the operation under the caller's filesystem policy."""
