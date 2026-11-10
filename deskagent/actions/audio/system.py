from __future__ import annotations

import os
import re
import subprocess
import tempfile
import threading
from pathlib import Path

from deskagent.actions.base import Action
from deskagent.actions.types import ActionCategory, ActionResult, RiskLevel
from deskagent.platform.macos.audio import MacOSAudioService
from deskagent.privacy.guards import FilesystemGuard


def _macos():
    MacOSAudioService().check_available()


def _audio_file(path):
    source = Path(path).expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError(source)
    if source.suffix.lower() not in {".aiff", ".aif", ".wav", ".m4a", ".mp3", ".caf"}:
        raise ValueError("Unsupported audio file extension")
    return source


def _service(context):
    return getattr(getattr(context, "services", None), "media_audio", None) or MacOSAudioService()


class ListSystemVoices(Action):
    name = "list_system_voices"
    description = "List locally installed macOS text-to-speech voices"
    category = ActionCategory.MEDIA
    parameters_schema = {}

    def execute(self, context, parameters):
        try:
            _macos()
            output = _service(context).list_voices()
            voices = []
            for line in output.splitlines()[:300]:
                match = re.match(r"^(.*?)\s+([a-z]{2}_[A-Z]{2})\s+#", line)
                if match:
                    voices.append({"name": match.group(1).strip(), "locale": match.group(2)})
            return ActionResult(True, {"voices": voices})
        except Exception as exc:
            return ActionResult(False, error=str(exc), error_code="AUDIO_ERROR")


class SpeakText(Action):
    name = "speak_text"
    description = "Speak bounded text aloud using a local macOS system voice"
    category = ActionCategory.MEDIA
    risk_level = RiskLevel.MEDIUM
    parameters_schema = {
        "text": {"type": "string", "required": True},
        "voice": {"type": "string", "required": False},
        "rate": {"type": "integer", "required": False, "minimum": 80, "maximum": 400},
    }

    def __init__(self):
        self.process = None
        self._cancelled = threading.Event()

    def cancel(self):
        self._cancelled.set()
        if self.process and self.process.poll() is None:
            self.process.terminate()

    def execute(self, context, parameters):
        temporary = None
        try:
            _macos()
            text = parameters["text"]
            if not text.strip() or len(text) > 5000:
                raise ValueError("Speech text must contain 1 to 5000 characters")
            fd, temporary = tempfile.mkstemp(prefix="deskagent-speech-", suffix=".txt")
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                stream.write(text)
            self.process = _service(context).start_speech(
                temporary, parameters.get("voice"), parameters.get("rate"))
            _, stderr = self.process.communicate(timeout=120)
            if self._cancelled.is_set():
                return ActionResult(False, error="Speech was cancelled", error_code="ACTION_CANCELLED")
            if self.process.returncode:
                raise RuntimeError(stderr.decode(errors="replace")[:1000] or "System speech failed")
            return ActionResult(True, {"spoken": True, "characters": len(text)})
        except subprocess.TimeoutExpired:
            self.cancel()
            return ActionResult(False, error="Speech timed out", error_code="TIMEOUT")
        except Exception as exc:
            return ActionResult(False, error=str(exc), error_code="AUDIO_ERROR")
        finally:
            if temporary:
                Path(temporary).unlink(missing_ok=True)
            self.process = None


class RenderSpeechToFile(Action):
    name = "render_speech_to_file"
    description = "Render bounded text to a new AIFF audio file using a local macOS voice"
    category = ActionCategory.MEDIA
    risk_level = RiskLevel.MEDIUM
    parameters_schema = {
        "text": {"type": "string", "required": True},
        "output_path": {"type": "string", "required": True},
        "voice": {"type": "string", "required": False},
    }

    def execute(self, context, parameters):
        temporary = None
        target = None
        reserved = False
        try:
            _macos()
            text = parameters["text"]
            if not text.strip() or len(text) > 5000:
                raise ValueError("Speech text must contain 1 to 5000 characters")
            target = Path(parameters["output_path"]).expanduser().resolve()
            if target.suffix.lower() != ".aiff" or target.exists():
                raise ValueError("Output must be a new .aiff file")
            security = context.settings.security
            decision = FilesystemGuard(security.allowed_paths, security.blocked_paths).check(
                "write_file", {"output_path": str(target)}
            )
            if not decision.allowed:
                raise PermissionError(decision.reason)
            target.parent.mkdir(parents=True, exist_ok=True)
            descriptor = os.open(target, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            os.close(descriptor)
            reserved = True
            fd, temporary = tempfile.mkstemp(prefix="deskagent-speech-", suffix=".txt")
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                stream.write(text)
            _service(context).render_speech(temporary, target, parameters.get("voice"))
            if not target.is_file() or target.stat().st_size == 0:
                raise RuntimeError("Speech renderer produced no audio")
            target.chmod(0o600)
            return ActionResult(True, {"path": str(target), "bytes": target.stat().st_size})
        except Exception as exc:
            if reserved and target and target.exists():
                target.unlink(missing_ok=True)
            return ActionResult(False, error=str(exc), error_code="AUDIO_ERROR")
        finally:
            if temporary:
                Path(temporary).unlink(missing_ok=True)


class PlayAudioFile(Action):
    name = "play_audio_file"
    description = "Play a local audio file through macOS audio output"
    category = ActionCategory.MEDIA
    risk_level = RiskLevel.MEDIUM
    parameters_schema = {"path": {"type": "string", "required": True}}

    def __init__(self):
        self.process = None
        self._cancelled = threading.Event()

    def cancel(self):
        self._cancelled.set()
        if self.process and self.process.poll() is None:
            self.process.terminate()

    def execute(self, context, parameters):
        try:
            _macos()
            source = _audio_file(parameters["path"])
            self.process = _service(context).start_playback(source)
            _, stderr = self.process.communicate(timeout=600)
            if self._cancelled.is_set():
                return ActionResult(False, error="Playback was cancelled", error_code="ACTION_CANCELLED")
            if self.process.returncode:
                raise RuntimeError(stderr.decode(errors="replace")[:1000] or "Audio playback failed")
            return ActionResult(True, {"path": str(source), "played": True})
        except subprocess.TimeoutExpired:
            self.cancel()
            return ActionResult(False, error="Audio playback timed out", error_code="TIMEOUT")
        except Exception as exc:
            return ActionResult(False, error=str(exc), error_code="AUDIO_ERROR")
        finally:
            self.process = None


class GetAudioFileInfo(Action):
    name = "get_audio_file_info"
    description = "Read format and duration information for a local audio file"
    category = ActionCategory.MEDIA
    parameters_schema = {"path": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        try:
            _macos()
            source = _audio_file(parameters["path"])
            output = _service(context).file_info(source)
            duration = re.search(r"estimated duration:\s*([\d.]+)\s*sec", output)
            return ActionResult(True, {
                "path": str(source), "bytes": source.stat().st_size,
                "duration_seconds": float(duration.group(1)) if duration else None,
                "info": output[:5000],
            })
        except Exception as exc:
            return ActionResult(False, error=str(exc), error_code="AUDIO_ERROR")
