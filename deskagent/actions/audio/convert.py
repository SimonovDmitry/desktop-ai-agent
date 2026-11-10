"""Safe macOS audio conversion using fixed afconvert arguments."""

from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path

from deskagent.actions.audio._wav import WavAction
from deskagent.actions.audio.system import _audio_file, _macos, _service
from deskagent.actions.types import RiskLevel
from deskagent.privacy.guards import FilesystemGuard

FORMATS = {
    "wav_pcm16": ("WAVE", "LEI16", ".wav"),
    "aiff_pcm16": ("AIFF", "BEI16", ".aiff"),
    "caf_pcm16": ("caff", "LEI16", ".caf"),
}
SOURCE_OUTPUT = {"path": {"type": "string", "required": True},
                 "output_path": {"type": "string", "required": True}}


class AudioConvertAction(WavAction):
    discoverable = False
    risk_level = RiskLevel.MEDIUM
    reversible = True

    @staticmethod
    def convert(context, parameters, preset, sample_rate=None, channels=None, track=None):
        _macos()
        source = _audio_file(parameters["path"])
        target = Path(parameters["output_path"]).expanduser().resolve()
        file_format, data_format, extension = FORMATS[preset]
        if target.suffix.lower() != extension:
            raise ValueError(f"Output path must end with {extension}")
        security = context.settings.security
        guard = FilesystemGuard(security.allowed_paths, security.blocked_paths)
        for action, name, path in (
            ("read_file", "path", source), ("write_file", "output_path", target),
        ):
            decision = guard.check(action, {name: str(path)})
            if not decision.allowed:
                raise PermissionError(decision.reason)
        if target.exists():
            raise FileExistsError(f"Output file already exists: {target}")
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary_dir = Path(tempfile.mkdtemp(prefix=".deskagent-convert-", dir=target.parent))
        try:
            temporary = temporary_dir / f"converted{extension}"
            descriptor = data_format if sample_rate is None else f"{data_format}@{sample_rate}"
            _service(context).convert(source, temporary, file_format, descriptor, channels, track)
            if not temporary.is_file() or temporary.stat().st_size == 0:
                raise RuntimeError("Audio converter produced no output")
            temporary.chmod(0o600)
            os.link(temporary, target)
            return {"source": str(source), "path": str(target), "format": preset,
                    "bytes": target.stat().st_size, "sample_rate": sample_rate, "channels": channels}
        finally:
            shutil.rmtree(temporary_dir)


class ConvertAudioFormat(AudioConvertAction):
    name = "convert_audio_format"
    description = "Convert a supported audio file to lossless 16-bit WAV, AIFF or CAF"
    parameters_schema = {**SOURCE_OUTPUT,
                         "format": {"type": "string", "required": True, "enum": list(FORMATS)}}
    discoverable = True

    def execute(self, context, parameters):
        return self.run(lambda: self.convert(context, parameters, parameters["format"]))


class ResampleAudioFile(AudioConvertAction):
    name = "resample_audio_file"
    description = "Resample a supported audio file into a new 16-bit PCM WAV"
    parameters_schema = {**SOURCE_OUTPUT,
                         "sample_rate": {"type": "integer", "required": True,
                                         "minimum": 8000, "maximum": 192000}}
    discoverable = True

    def execute(self, context, parameters):
        return self.run(lambda: self.convert(context, parameters, "wav_pcm16",
                                             sample_rate=parameters["sample_rate"]))


class ConvertAudioChannelCount(AudioConvertAction):
    name = "convert_audio_channel_count"
    description = "Convert a supported audio file to mono or stereo 16-bit PCM WAV"
    parameters_schema = {**SOURCE_OUTPUT,
                         "channels": {"type": "integer", "required": True, "enum": [1, 2]}}
    discoverable = True

    def execute(self, context, parameters):
        return self.run(lambda: self.convert(context, parameters, "wav_pcm16",
                                             channels=parameters["channels"]))


class ExtractAudioTrack(AudioConvertAction):
    name = "extract_audio_track"
    description = "Extract a numbered audio track to a new 16-bit PCM WAV"
    parameters_schema = {**SOURCE_OUTPUT,
                         "track": {"type": "integer", "required": True, "minimum": 0, "maximum": 32}}
    discoverable = True

    def execute(self, context, parameters):
        return self.run(lambda: self.convert(context, parameters, "wav_pcm16",
                                             track=parameters["track"]))
