"""Bounded synthetic audio generation."""

from __future__ import annotations

import math
import random
from array import array

from deskagent.actions.audio._wav import MAX_SAMPLES, WavAction, clamp, write_wav
from deskagent.actions.types import RiskLevel

BASE = {
    "output_path": {"type": "string", "required": True},
    "duration_seconds": {"type": "float", "required": True, "minimum": 0.001, "maximum": 120},
    "sample_rate": {"type": "integer", "required": False, "default": 44100, "minimum": 8000, "maximum": 192000},
    "channels": {"type": "integer", "required": False, "default": 1, "enum": [1, 2]},
}
AMPLITUDE = {"amplitude": {"type": "float", "required": False, "default": 0.5, "minimum": 0, "maximum": 1}}


class GenerateWavAction(WavAction):
    discoverable = False
    risk_level = RiskLevel.MEDIUM
    reversible = True

    @staticmethod
    def layout(parameters):
        rate = parameters.get("sample_rate", 44100)
        channels = parameters.get("channels", 1)
        frames = round(parameters["duration_seconds"] * rate)
        if frames < 1 or frames * channels > MAX_SAMPLES:
            raise ValueError("Generated output exceeds the processing limit")
        return rate, channels, frames

    @staticmethod
    def save(context, parameters, mono_samples, rate, channels):
        if channels == 1:
            values = array("h", mono_samples)
        else:
            values = array("h", (sample for value in mono_samples for sample in (value, value)))
        return write_wav(context, parameters["output_path"], values, channels, rate)


class GenerateToneWav(GenerateWavAction):
    name = "generate_tone_wav"
    description = "Create a bounded sine-wave tone in a new WAV"
    parameters_schema = {**BASE, **AMPLITUDE,
                         "frequency_hz": {"type": "float", "required": True, "minimum": 20, "maximum": 20000}}
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            rate, channels, frames = self.layout(parameters)
            frequency = parameters["frequency_hz"]
            if frequency >= rate / 2:
                raise ValueError("Tone frequency must be below Nyquist")
            level = parameters.get("amplitude", 0.5) * 32767
            samples = (clamp(level * math.sin(2 * math.pi * frequency * frame / rate))
                       for frame in range(frames))
            return self.save(context, parameters, samples, rate, channels)
        return self.run(operation)


class GenerateChirpWav(GenerateWavAction):
    name = "generate_chirp_wav"
    description = "Create a linear frequency sweep in a new WAV"
    parameters_schema = {**BASE, **AMPLITUDE,
                         "start_hz": {"type": "float", "required": True, "minimum": 20, "maximum": 20000},
                         "end_hz": {"type": "float", "required": True, "minimum": 20, "maximum": 20000}}
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            rate, channels, frames = self.layout(parameters)
            start, end = parameters["start_hz"], parameters["end_hz"]
            if max(start, end) >= rate / 2:
                raise ValueError("Sweep frequencies must be below Nyquist")
            duration = frames / rate
            level = parameters.get("amplitude", 0.5) * 32767
            samples = (
                clamp(level * math.sin(2 * math.pi * (
                    start * frame / rate + (end - start) * (frame / rate) ** 2 / (2 * duration)
                ))) for frame in range(frames)
            )
            return self.save(context, parameters, samples, rate, channels)
        return self.run(operation)


class GenerateNoiseWav(GenerateWavAction):
    name = "generate_noise_wav"
    description = "Create reproducible white noise in a new WAV"
    parameters_schema = {**BASE, **AMPLITUDE,
                         "seed": {"type": "integer", "required": False, "default": 0}}
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            rate, channels, frames = self.layout(parameters)
            randomizer = random.Random(parameters.get("seed", 0))
            level = parameters.get("amplitude", 0.5) * 32767
            samples = (clamp(randomizer.uniform(-level, level)) for _ in range(frames))
            return self.save(context, parameters, samples, rate, channels)
        return self.run(operation)


class GenerateSilenceWav(GenerateWavAction):
    name = "generate_silence_wav"
    description = "Create a silent PCM WAV of a specified duration"
    parameters_schema = BASE
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            rate, channels, frames = self.layout(parameters)
            return write_wav(context, parameters["output_path"], array("h", [0]) * (frames * channels), channels, rate)
        return self.run(operation)


class GenerateClickTrackWav(GenerateWavAction):
    name = "generate_click_track_wav"
    description = "Create a metronome click track with accented bar starts"
    parameters_schema = {**BASE,
                         "bpm": {"type": "integer", "required": True, "minimum": 20, "maximum": 300},
                         "beats_per_bar": {"type": "integer", "required": False, "default": 4,
                                           "minimum": 1, "maximum": 16}}
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            rate, channels, frames = self.layout(parameters)
            bpm = parameters["bpm"]
            beat_frames = rate * 60 / bpm
            pulse_frames = max(1, round(0.025 * rate))
            output = array("h", [0]) * frames
            beat = 0
            while True:
                start = round(beat * beat_frames)
                if start >= frames:
                    break
                frequency = 1500 if beat % parameters.get("beats_per_bar", 4) == 0 else 1000
                for offset in range(min(pulse_frames, frames - start)):
                    envelope = 1 - offset / pulse_frames
                    output[start + offset] = clamp(
                        22000 * envelope * math.sin(2 * math.pi * frequency * offset / rate)
                    )
                beat += 1
            return self.save(context, parameters, output, rate, channels)
        return self.run(operation)
