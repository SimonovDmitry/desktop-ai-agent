"""Dependency-free contracts for replaceable speech and device backends."""
from dataclasses import dataclass
from typing import Protocol
import io
import wave


class AudioError(RuntimeError):
    """Actionable audio failure, safe for presentation by the CLI."""


@dataclass(frozen=True)
class AudioClip:
    pcm: bytes
    sample_rate: int

    def __post_init__(self):
        if self.sample_rate <= 0 or len(self.pcm) % 2:
            raise ValueError("Expected mono signed 16-bit PCM and a positive sample rate")

    @property
    def duration(self):
        return len(self.pcm) / (2 * self.sample_rate)

    def to_wav(self):
        output = io.BytesIO()
        with wave.open(output, "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(self.sample_rate)
            wav.writeframes(self.pcm)
        return output.getvalue()

    @classmethod
    def from_wav(cls, data):
        try:
            with wave.open(io.BytesIO(data), "rb") as wav:
                if wav.getnchannels() != 1 or wav.getsampwidth() != 2 or wav.getcomptype() != "NONE":
                    raise AudioError("Expected uncompressed mono PCM16 WAV")
                return cls(wav.readframes(wav.getnframes()), wav.getframerate())
        except (wave.Error, EOFError) as exc:
            raise AudioError("Invalid WAV response") from exc


class SpeechToText(Protocol):
    def transcribe(self, clip: AudioClip) -> str:
        ...


class TextToSpeech(Protocol):
    def synthesize(self, text: str) -> AudioClip:
        ...
