"""Lazy local inference and OpenAI-compatible audio APIs. No implicit cloud fallback."""
import io
import re
from pathlib import Path

from .types import AudioClip, AudioError


def split_text(text, limit=800):
    """Bound synthesis requests without dropping long words or sentence tails."""
    remaining = text.strip()
    while remaining:
        if len(remaining) <= limit:
            yield remaining
            return
        boundary = max(remaining.rfind(mark, 0, limit) for mark in (". ", "! ", "? ", "\n", " "))
        end = boundary + 1 if boundary > 0 else limit
        yield remaining[:end].strip()
        remaining = remaining[end:].strip()


class TOneSTT:
    """T-one ONNX inference. Supply a pre-provisioned directory for offline use."""

    def __init__(self, model_path):
        self.model_path = Path(model_path).expanduser()
        self._model = None

    def transcribe(self, clip):
        try:
            import numpy as np
            import onnx_asr
            if not self.model_path.is_dir():
                raise AudioError(f"T-one model directory missing: {self.model_path}. See docs/audio.md")
            if self._model is None:
                self._model = onnx_asr.load_model("t-tech/t-one", str(self.model_path))
            # Keep inference windows short; T-one's ONNX adapter is not streaming.
            size = clip.sample_rate * 20 * 2
            texts = []
            for offset in range(0, len(clip.pcm), size):
                samples = np.frombuffer(clip.pcm[offset:offset + size], dtype="<i2").astype(np.float32) / 32768
                texts.append(self._model.recognize(samples, sample_rate=clip.sample_rate))
            return " ".join(texts).strip()
        except ImportError as exc:
            raise AudioError("Install requirements-audio.txt for local T-one recognition") from exc
        except AudioError:
            raise
        except Exception as exc:
            raise AudioError("T-one inference failed; check model files and audio format") from exc


class SileroTTS:
    """Load the requested v5_ru package directly from disk, without torch.hub code downloads."""

    def __init__(self, model_path, speaker="xenia", sample_rate=48000, device="cpu"):
        self.model_path = Path(model_path).expanduser()
        self.speaker = speaker
        self.sample_rate = sample_rate
        self.device = device
        self._model = None

    def synthesize(self, text):
        try:
            import numpy as np
            import torch
            if not self.model_path.is_file():
                raise AudioError(f"Silero v5_ru model missing: {self.model_path}. See docs/audio.md")
            if self._model is None:
                self._model = torch.package.PackageImporter(str(self.model_path)).load_pickle("tts_models", "model")
                self._model.to(torch.device(self.device))
            chunks = []
            with torch.inference_mode():
                for part in split_text(text):
                    samples = self._model.apply_tts(text=part, speaker=self.speaker, sample_rate=self.sample_rate)
                    samples = samples.detach().cpu().numpy()
                    chunks.append((np.clip(samples, -1, 1) * 32767).astype("<i2").tobytes())
            return AudioClip(b"".join(chunks), self.sample_rate)
        except ImportError as exc:
            raise AudioError("Install requirements-audio.txt for Silero synthesis") from exc
        except AudioError:
            raise
        except Exception as exc:
            raise AudioError("Silero synthesis failed; check v5_ru package, speaker and device") from exc


class OpenAIAudio:
    """Independent endpoint/model/key per direction, including self-hosted servers."""

    def __init__(self, base_url, api_key, model, *, language="ru", voice="alloy", timeout=60):
        self.base_url, self.api_key, self.model = base_url, api_key, model
        self.language, self.voice, self.timeout = language, voice, timeout
        self._client = None

    def _get_client(self):
        if self._client is None:
            from openai import OpenAI
            self._client = OpenAI(base_url=self.base_url, api_key=self.api_key or "local", timeout=self.timeout,
                                  max_retries=0)
        return self._client

    def transcribe(self, clip):
        try:
            result = self._get_client().audio.transcriptions.create(
                model=self.model, file=("speech.wav", io.BytesIO(clip.to_wav()), "audio/wav"),
                language=self.language, response_format="json",
            )
            return result.text.strip()
        except Exception as exc:
            # SDK exceptions may contain request bodies, endpoint credentials or headers.
            raise AudioError("STT API request failed; check endpoint, model, credentials and timeout") from exc

    def synthesize(self, text):
        clips = []
        try:
            for part in split_text(text):
                response = self._get_client().audio.speech.create(
                    model=self.model, voice=self.voice, input=part, response_format="pcm",
                )
                # OpenAI PCM contract: mono signed PCM16 at 24 kHz.
                clips.append(response.content)
            return AudioClip(b"".join(clips), 24000)
        except Exception as exc:
            raise AudioError("TTS API request failed; server must support PCM16/24kHz output") from exc


def spoken_text(text):
    text = re.sub(r"```.*?```", " Код приведён в текстовом ответе. ", text, flags=re.S)
    text = re.sub(r"\[([^]]+)\]\([^)]+\)", r"\1", text)
    return re.sub(r"[*#`_]", "", text).strip()
