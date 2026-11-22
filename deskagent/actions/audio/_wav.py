"""Action wrappers for portable platform operations."""
from __future__ import annotations

import wave
from array import array

from deskagent.actions.base import Action
from deskagent.actions.types import ActionCategory, ActionResult
from deskagent.platform.common import audio as portable
from deskagent.platform.common.audio import (  # noqa: F401
    MAX_SAMPLES,
    MAX_OUTPUTS,
    WavData,
    _guard,
    frame_at,
    clamp,
    dbfs,
    gain_factor,
)


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


def read_wav(context, path):
    service = getattr(getattr(context, "services", None), "wav", None)
    return (service or portable.WavService()).read_wav(context, path)


def write_wav(context, output_path, samples: array, channels: int, rate: int):
    service = getattr(getattr(context, "services", None), "wav", None)
    return (service or portable.WavService()).write_wav(context, output_path, samples, channels, rate)
