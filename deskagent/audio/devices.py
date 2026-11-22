"""Bounded, synchronous half-duplex audio: microphone is closed before playback."""
from collections import deque
import math
import struct

from .types import AudioClip, AudioError


class UtteranceDetector:
    """Energy endpoint detector with pre-roll, trailing silence and hard time bounds."""

    def __init__(self, settings):
        self.settings = settings
        self.pre_roll = deque(maxlen=10)  # 300 ms for 30 ms blocks
        self.frames = []
        self.elapsed = self.silence = self.voiced = 0.0
        self.started = False

    def feed(self, pcm):
        samples = struct.unpack(f"<{len(pcm) // 2}h", pcm)
        duration = len(samples) / self.settings.sample_rate
        rms = math.sqrt(sum(x * x for x in samples) / max(1, len(samples))) / 32768
        self.elapsed += duration
        speech = rms >= self.settings.energy_threshold
        if not self.started:
            self.pre_roll.append(pcm)
            if speech:
                self.started = True
                self.frames.extend(self.pre_roll)
        else:
            self.frames.append(pcm)
        if self.started:
            self.voiced += duration if speech else 0
            self.silence = 0 if speech else self.silence + duration
        return (self.elapsed >= self.settings.max_record_seconds
                or (not self.started and self.elapsed >= self.settings.listen_timeout)
                or (self.started and self.silence >= self.settings.silence_seconds))

    def result(self):
        if self.voiced < self.settings.min_speech_seconds:
            return None
        return AudioClip(b"".join(self.frames), self.settings.sample_rate)


class SoundDeviceIO:
    def __init__(self, settings):
        self.settings = settings

    @staticmethod
    def _backend():
        try:
            import sounddevice
            return sounddevice
        except (ImportError, OSError) as exc:
            raise AudioError("Install sounddevice and PortAudio for microphone/playback support") from exc

    def record(self, stop=None):
        detector = UtteranceDetector(self.settings)
        backend = self._backend()
        try:
            with backend.RawInputStream(samplerate=self.settings.sample_rate, channels=1, dtype="int16",
                                        blocksize=int(self.settings.sample_rate * 0.03),
                                        device=self.settings.input_device or None) as stream:
                while stop is None or not stop.is_set():
                    pcm, overflow = stream.read(int(self.settings.sample_rate * 0.03))
                    if overflow:
                        raise AudioError("Microphone overflow; lower device load and retry")
                    if detector.feed(bytes(pcm)):
                        return detector.result()
            return None
        except AudioError:
            raise
        except Exception as exc:
            raise AudioError("Microphone unavailable; check device and microphone permission") from exc

    def play(self, clip, stop=None):
        backend = self._backend()
        try:
            with backend.RawOutputStream(samplerate=clip.sample_rate, channels=1, dtype="int16",
                                         device=self.settings.output_device or None) as stream:
                size = max(2, int(clip.sample_rate * 0.03) * 2)
                for offset in range(0, len(clip.pcm), size):
                    if stop is not None and stop.is_set():
                        stream.abort()
                        break
                    stream.write(clip.pcm[offset:offset + size])
        except Exception as exc:
            raise AudioError("Audio playback failed; check output device") from exc
