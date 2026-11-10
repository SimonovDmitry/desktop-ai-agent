"""Non-destructive PCM WAV editing actions."""

from __future__ import annotations

import math
import re
from array import array
from pathlib import Path

from deskagent.actions.audio._wav import (
    MAX_OUTPUTS, MAX_SAMPLES, WavAction, clamp, frame_at, gain_factor, read_wav, write_wav,
)
from deskagent.actions.types import RiskLevel
from deskagent.privacy.guards import FilesystemGuard

INPUT_OUTPUT = {"path": {"type": "string", "required": True},
                "output_path": {"type": "string", "required": True}}


class WavEditAction(WavAction):
    discoverable = False
    risk_level = RiskLevel.MEDIUM
    reversible = True


class TrimWavFile(WavEditAction):
    name = "trim_wav_file"
    description = "Save a time interval of a WAV as a new file"
    parameters_schema = {**INPUT_OUTPUT,
                         "start_seconds": {"type": "float", "required": True, "minimum": 0},
                         "end_seconds": {"type": "float", "required": True, "minimum": 0}}
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            data = read_wav(context, parameters["path"])
            start = frame_at(parameters["start_seconds"], data.rate, data.frames)
            end = frame_at(parameters["end_seconds"], data.rate, data.frames, allow_end=True)
            if end <= start:
                raise ValueError("End time must follow start time")
            return write_wav(context, parameters["output_path"],
                             data.samples[start * data.channels:end * data.channels], data.channels, data.rate)
        return self.run(operation)


class ConcatenateWavFiles(WavEditAction):
    name = "concatenate_wav_files"
    description = "Join 2-20 WAV files with matching format into a new file"
    parameters_schema = {"paths": {"type": "list", "required": True, "items": {"type": "string"}},
                         "output_path": {"type": "string", "required": True}}
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            paths = parameters["paths"]
            if not 2 <= len(paths) <= 20:
                raise ValueError("Provide 2 to 20 WAV files")
            sources = [read_wav(context, path) for path in paths]
            channels, rate = sources[0].channels, sources[0].rate
            if any((item.channels, item.rate) != (channels, rate) for item in sources):
                raise ValueError("All WAV files must have the same channels and sample rate")
            if sum(len(item.samples) for item in sources) > MAX_SAMPLES:
                raise ValueError("Combined output exceeds the processing limit")
            combined = array("h")
            for item in sources:
                combined.extend(item.samples)
            return {**write_wav(context, parameters["output_path"], combined, channels, rate),
                    "source_count": len(sources)}
        return self.run(operation)


class MixWavFiles(WavEditAction):
    name = "mix_wav_files"
    description = "Mix two matching WAV files with independent gain and a start offset"
    parameters_schema = {
        "first_path": {"type": "string", "required": True},
        "second_path": {"type": "string", "required": True},
        "output_path": {"type": "string", "required": True},
        "second_start_seconds": {"type": "float", "required": False, "default": 0, "minimum": 0, "maximum": 600},
        "first_gain_db": {"type": "float", "required": False, "default": 0, "minimum": -60, "maximum": 60},
        "second_gain_db": {"type": "float", "required": False, "default": 0, "minimum": -60, "maximum": 60},
    }
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            first = read_wav(context, parameters["first_path"])
            second = read_wav(context, parameters["second_path"])
            if (first.channels, first.rate) != (second.channels, second.rate):
                raise ValueError("WAV channel counts and sample rates must match")
            offset = round(parameters.get("second_start_seconds", 0) * first.rate) * first.channels
            length = max(len(first.samples), offset + len(second.samples))
            if length > MAX_SAMPLES:
                raise ValueError("Mixed output exceeds the processing limit")
            output = array("h", [0]) * length
            first_gain = gain_factor(parameters.get("first_gain_db", 0))
            second_gain = gain_factor(parameters.get("second_gain_db", 0))
            for index in range(length):
                first_value = first.samples[index] * first_gain if index < len(first.samples) else 0
                second_index = index - offset
                second_value = (second.samples[second_index] * second_gain
                                if 0 <= second_index < len(second.samples) else 0)
                output[index] = clamp(first_value + second_value)
            return write_wav(context, parameters["output_path"], output, first.channels, first.rate)
        return self.run(operation)


class AdjustWavGain(WavEditAction):
    name = "adjust_wav_gain"
    description = "Apply a bounded gain in decibels and save a new WAV"
    parameters_schema = {**INPUT_OUTPUT,
                         "gain_db": {"type": "float", "required": True, "minimum": -60, "maximum": 60}}
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            data = read_wav(context, parameters["path"])
            factor = gain_factor(parameters["gain_db"])
            output = array("h", (clamp(value * factor) for value in data.samples))
            return {**write_wav(context, parameters["output_path"], output, data.channels, data.rate),
                    "gain_db": parameters["gain_db"]}
        return self.run(operation)


class NormalizeWavPeak(WavEditAction):
    name = "normalize_wav_peak"
    description = "Normalize peak amplitude to a requested dBFS level without overwriting source"
    parameters_schema = {**INPUT_OUTPUT,
                         "target_peak_db": {"type": "float", "required": False, "default": -1,
                                            "minimum": -30, "maximum": 0}}
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            data = read_wav(context, parameters["path"])
            peak = max(abs(value) for value in data.samples)
            target = 32767 * 10 ** (parameters.get("target_peak_db", -1) / 20)
            factor = target / peak if peak else 1
            output = array("h", (clamp(value * factor) for value in data.samples))
            return {**write_wav(context, parameters["output_path"], output, data.channels, data.rate),
                    "source_peak": peak, "target_peak_db": parameters.get("target_peak_db", -1)}
        return self.run(operation)


class FadeWavFile(WavEditAction):
    name = "fade_wav_file"
    description = "Apply linear fade-in and fade-out to a new WAV"
    parameters_schema = {**INPUT_OUTPUT,
                         "fade_in_seconds": {"type": "float", "required": False, "default": 0, "minimum": 0},
                         "fade_out_seconds": {"type": "float", "required": False, "default": 0, "minimum": 0}}
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            data = read_wav(context, parameters["path"])
            fade_in = round(parameters.get("fade_in_seconds", 0) * data.rate)
            fade_out = round(parameters.get("fade_out_seconds", 0) * data.rate)
            if fade_in > data.frames or fade_out > data.frames or not (fade_in or fade_out):
                raise ValueError("Fade durations must fit the file and at least one must be positive")
            output = array("h", data.samples)
            for frame in range(data.frames):
                factor = 1.0
                if fade_in and frame < fade_in:
                    factor *= frame / max(1, fade_in - 1)
                if fade_out and frame >= data.frames - fade_out:
                    factor *= (data.frames - 1 - frame) / max(1, fade_out - 1)
                if factor != 1:
                    start = frame * data.channels
                    for channel in range(data.channels):
                        output[start + channel] = clamp(output[start + channel] * factor)
            return write_wav(context, parameters["output_path"], output, data.channels, data.rate)
        return self.run(operation)


class ReverseWavFile(WavEditAction):
    name = "reverse_wav_file"
    description = "Reverse PCM frames while preserving channel order"
    parameters_schema = INPUT_OUTPUT
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            data = read_wav(context, parameters["path"])
            output = array("h")
            for frame in range(data.frames - 1, -1, -1):
                start = frame * data.channels
                output.extend(data.samples[start:start + data.channels])
            return write_wav(context, parameters["output_path"], output, data.channels, data.rate)
        return self.run(operation)


class ExtractWavChannel(WavEditAction):
    name = "extract_wav_channel"
    description = "Extract one numbered channel into a mono WAV"
    parameters_schema = {**INPUT_OUTPUT,
                         "channel": {"type": "integer", "required": True, "minimum": 0, "maximum": 7}}
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            data = read_wav(context, parameters["path"])
            channel = parameters["channel"]
            if channel >= data.channels:
                raise ValueError("Channel index is outside the file")
            output = data.samples[channel::data.channels]
            return {**write_wav(context, parameters["output_path"], output, 1, data.rate), "channel": channel}
        return self.run(operation)


class ConvertWavChannels(WavEditAction):
    name = "convert_wav_channels"
    description = "Convert mono to stereo or average stereo to mono"
    parameters_schema = {**INPUT_OUTPUT,
                         "channels": {"type": "integer", "required": True, "enum": [1, 2]}}
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            data = read_wav(context, parameters["path"])
            target = parameters["channels"]
            if data.channels not in {1, 2}:
                raise ValueError("Only mono and stereo sources are supported")
            if data.channels == target:
                output = data.samples
            elif target == 1:
                output = array("h", (clamp((data.samples[i] + data.samples[i + 1]) / 2)
                                     for i in range(0, len(data.samples), 2)))
            else:
                output = array("h", (value for sample in data.samples for value in (sample, sample)))
            return write_wav(context, parameters["output_path"], output, target, data.rate)
        return self.run(operation)


class PadWavFile(WavEditAction):
    name = "pad_wav_file"
    description = "Add bounded silence before and after a WAV"
    parameters_schema = {**INPUT_OUTPUT,
                         "start_seconds": {"type": "float", "required": False, "default": 0, "minimum": 0,
                                           "maximum": 120},
                         "end_seconds": {"type": "float", "required": False, "default": 0, "minimum": 0,
                                         "maximum": 120}}
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            data = read_wav(context, parameters["path"])
            start = round(parameters.get("start_seconds", 0) * data.rate) * data.channels
            end = round(parameters.get("end_seconds", 0) * data.rate) * data.channels
            if start + len(data.samples) + end > MAX_SAMPLES:
                raise ValueError("Padded output exceeds the processing limit")
            output = array("h", [0]) * start + data.samples + array("h", [0]) * end
            return write_wav(context, parameters["output_path"], output, data.channels, data.rate)
        return self.run(operation)


class InsertWavSilence(WavEditAction):
    name = "insert_wav_silence"
    description = "Insert a bounded silence interval at a specified time"
    parameters_schema = {**INPUT_OUTPUT,
                         "at_seconds": {"type": "float", "required": True, "minimum": 0},
                         "duration_seconds": {"type": "float", "required": True, "minimum": 0.001,
                                              "maximum": 120}}
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            data = read_wav(context, parameters["path"])
            at = frame_at(parameters["at_seconds"], data.rate, data.frames, allow_end=True) * data.channels
            silence = round(parameters["duration_seconds"] * data.rate) * data.channels
            if len(data.samples) + silence > MAX_SAMPLES:
                raise ValueError("Output exceeds the processing limit")
            output = data.samples[:at] + array("h", [0]) * silence + data.samples[at:]
            return write_wav(context, parameters["output_path"], output, data.channels, data.rate)
        return self.run(operation)


class TrimWavSilence(WavEditAction):
    name = "trim_wav_silence"
    description = "Remove leading and trailing quiet frames while preserving interior pauses"
    parameters_schema = {**INPUT_OUTPUT,
                         "threshold_db": {"type": "float", "required": False, "default": -40,
                                          "minimum": -90, "maximum": 0}}
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            data = read_wav(context, parameters["path"])
            threshold = 32768 * 10 ** (parameters.get("threshold_db", -40) / 20)
            first = last = None
            for frame in range(data.frames):
                start = frame * data.channels
                if max(abs(value) for value in data.samples[start:start + data.channels]) > threshold:
                    if first is None:
                        first = frame
                    last = frame + 1
            if first is None:
                raise ValueError("No non-silent frames found")
            output = data.samples[first * data.channels:last * data.channels]
            return {**write_wav(context, parameters["output_path"], output, data.channels, data.rate),
                    "removed_start_seconds": round(first / data.rate, 6),
                    "removed_end_seconds": round((data.frames - last) / data.rate, 6)}
        return self.run(operation)


class SplitWavFile(WavEditAction):
    name = "split_wav_file"
    description = "Split a WAV into bounded equal-duration segments in an allowed output directory"
    parameters_schema = {"path": {"type": "string", "required": True},
                         "output_directory": {"type": "string", "required": True},
                         "segment_seconds": {"type": "float", "required": True, "minimum": 0.01},
                         "prefix": {"type": "string", "required": False, "default": "part"}}
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            data = read_wav(context, parameters["path"])
            segment = round(parameters["segment_seconds"] * data.rate)
            if segment < 1:
                raise ValueError("Segment duration is too short")
            count = math.ceil(data.frames / segment)
            if count > MAX_OUTPUTS:
                raise ValueError("Split would create more than 100 files")
            prefix = parameters.get("prefix", "part")
            if not re.fullmatch(r"[A-Za-z0-9_-]{1,40}", prefix):
                raise ValueError("Prefix must contain 1-40 safe letters, digits, dashes or underscores")
            directory = Path(parameters["output_directory"]).expanduser().resolve()
            decision = FilesystemGuard(context.settings.security.allowed_paths,
                                       context.settings.security.blocked_paths).check(
                "write_file", {"output_directory": str(directory)}
            )
            if not decision.allowed:
                raise PermissionError(decision.reason)
            targets = [directory / f"{prefix}_{index + 1:03d}.wav" for index in range(count)]
            if any(path.exists() for path in targets):
                raise FileExistsError("At least one split output already exists")
            created = []
            try:
                for index, target in enumerate(targets):
                    start = index * segment * data.channels
                    end = min((index + 1) * segment, data.frames) * data.channels
                    created.append(write_wav(context, target, data.samples[start:end], data.channels, data.rate))
            except Exception:
                for item in created:
                    Path(item["path"]).unlink(missing_ok=True)
                raise
            return {"source": str(data.path), "parts": created, "count": len(created)}
        return self.run(operation)
