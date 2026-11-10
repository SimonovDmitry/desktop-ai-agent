"""Platform contract for native audio commands."""
from abc import ABC, abstractmethod


class AudioService(ABC):
    @abstractmethod
    def check_available(self):
        """Raise when native audio tools are unavailable."""

    @abstractmethod
    def list_voices(self):
        """Return installed text-to-speech voice output."""

    @abstractmethod
    def start_speech(self, source, voice=None, rate=None):
        """Start speech playback and return a cancellable process."""

    @abstractmethod
    def render_speech(self, source, destination, voice=None):
        """Render speech to an audio file."""

    @abstractmethod
    def start_playback(self, source):
        """Start audio playback and return a cancellable process."""

    @abstractmethod
    def file_info(self, source):
        """Return native audio metadata output."""

    @abstractmethod
    def convert(self, source, destination, file_format, data_format, channels=None, track=None):
        """Convert audio with native tools."""
