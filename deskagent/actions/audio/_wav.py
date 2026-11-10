"""Bounded PCM WAV primitives shared by audio actions."""

from __future__ import annotations

import math
import os
import sys
import tempfile
import wave
from array import array
from dataclasses import dataclass
from pathlib import Path

from deskagent.actions.base import Action
from deskagent.actions.types import ActionCategory, ActionResult
from deskagent.privacy.guards import FilesystemGuard

MAX_SAMPLES = 20_000_000
MAX_OUTPUTS = 100


@dataclass
class WavData:
    path: Path
    samples: array
    channels: int
    rate: int

    @property
    def frames(self):
        return len(self.samples) // self.channels

    @property
    def duration(self):
        return self.frames / self.rate

    def info(self):
        return {
            "path": str(self.path), "channels": self.channels, "sample_rate": self.rate,
            "sample_width_bits": 16, "frames": self.frames, "duration_seconds": round(self.duration, 6),
        }


class WavAction(Action):
    discoverable = False
    category = ActionCategory.MEDIA

    @staticmethod
    def run(operation):
        try:
            return ActionResult(True, operation())
        except (ValueError, FileNotFoundError, FileExistsError, PermissionError, wave.Error) as exc:
            return ActionResult(False, error=str(exc), error_code="INVALID_AUDIO")
        except Exception as exc:
            return ActionResult(False, error=str(exc), error_code="AUDIO_ERROR")


def _guard(context):
    security = context.settings.security
    return FilesystemGuard(security.allowed_paths, security.blocked_paths)


def read_wav(context, path) -> WavData:
    source = Path(path).expanduser().resolve()
    decision = _guard(context).check("read_file", {"path": str(source)})
    if not decision.allowed:
        raise PermissionError(decision.reason)
    if source.suffix.lower() != ".wav" or not source.is_file():
        raise FileNotFoundError("A readable .wav file is required")
    with wave.open(str(source), "rb") as stream:
        channels, width, rate, frames = (
            stream.getnchannels(), stream.getsampwidth(), stream.getframerate(), stream.getnframes()
        )
        if width != 2 or channels < 1 or channels > 8 or rate < 8000 or rate > 192000:
            raise ValueError("Only uncompressed 16-bit PCM WAV with 1-8 channels is supported")
        if frames * channels > MAX_SAMPLES:
            raise ValueError("WAV exceeds the processing limit of 20 million samples")
        if frames < 1:
            raise ValueError("WAV file contains no audio frames")
        samples = array("h")
        samples.frombytes(stream.readframes(frames))
    if sys.byteorder != "little":
        samples.byteswap()
    if len(samples) != frames * channels:
        raise ValueError("WAV contains fewer samples than its header declares")
    return WavData(source, samples, channels, rate)


def write_wav(context, output_path, samples: array, channels: int, rate: int):
    target = Path(output_path).expanduser().resolve()
    if target.suffix.lower() != ".wav":
        raise ValueError("Output path must end with .wav")
    if channels < 1 or channels > 8 or rate < 8000 or rate > 192000:
        raise ValueError("Invalid channel count or sample rate")
    if not samples or len(samples) % channels or len(samples) > MAX_SAMPLES:
        raise ValueError("Output must contain complete frames within the processing limit")
    decision = _guard(context).check("write_file", {"output_path": str(target)})
    if not decision.allowed:
        raise PermissionError(decision.reason)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        raise FileExistsError(f"Output file already exists: {target}")
    descriptor, temporary = tempfile.mkstemp(prefix=".deskagent-audio-", suffix=".wav", dir=target.parent)
    os.close(descriptor)
    try:
        raw = array("h", samples)
        if sys.byteorder != "little":
            raw.byteswap()
        with wave.open(temporary, "wb") as stream:
            stream.setnchannels(channels)
            stream.setsampwidth(2)
            stream.setframerate(rate)
            stream.writeframes(raw.tobytes())
        os.link(temporary, target)
        return {"path": str(target), "frames": len(samples) // channels,
                "duration_seconds": round(len(samples) / channels / rate, 6), "bytes": target.stat().st_size}
    finally:
        Path(temporary).unlink(missing_ok=True)


def frame_at(seconds, rate, total, *, allow_end=False):
    if not isinstance(seconds, (int, float)) or not math.isfinite(seconds) or seconds < 0:
        raise ValueError("Time must be a finite non-negative number")
    frame = round(seconds * rate)
    if frame > total or (frame == total and not allow_end):
        raise ValueError("Time is outside the audio file")
    return frame


def clamp(sample):
    return max(-32768, min(32767, round(sample)))


def dbfs(amplitude):
    return None if amplitude <= 0 else round(20 * math.log10(amplitude / 32768), 3)


def gain_factor(db):
    if not isinstance(db, (int, float)) or not math.isfinite(db) or db < -60 or db > 60:
        raise ValueError("Gain must be between -60 and +60 dB")
    return 10 ** (db / 20)
