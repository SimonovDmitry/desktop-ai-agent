"""Voice orchestration around the existing agent and its confirmation boundary."""
from dataclasses import dataclass
from threading import Event, Lock

from .devices import SoundDeviceIO
from .providers import OpenAIAudio, SileroTTS, TOneSTT, spoken_text
from .types import AudioError


@dataclass
class VoiceTurn:
    transcript: str = ""
    response: object = None
    speech_error: str = ""


class VoiceAssistant:
    def __init__(self, settings, *, stt=None, tts=None, devices=None):
        settings.validate()
        self.settings = settings
        self.stt = stt or self._provider("stt")
        self.tts = tts or self._provider("tts")
        self.devices = devices or SoundDeviceIO(settings)
        self.stop_event = Event()
        self._lock = Lock()

    def _provider(self, direction):
        s = self.settings
        name = getattr(s, f"{direction}_provider")
        if name in {"openai", "openai_compatible"}:
            return OpenAIAudio(getattr(s, f"{direction}_base_url"), getattr(s, f"{direction}_api_key"),
                               getattr(s, f"{direction}_model"), language=s.language,
                               voice=s.api_voice, timeout=s.api_timeout)
        if direction == "stt":
            return TOneSTT(s.stt_model_path)
        return SileroTTS(s.tts_model_path, s.speaker, s.tts_sample_rate, s.device)

    def stop(self):
        self.stop_event.set()

    def speak(self, text):
        text = spoken_text(text)
        if text and not self.stop_event.is_set():
            clip = self.tts.synthesize(text)
            self.devices.play(clip, self.stop_event)

    def turn(self, agent, session, *, clip=None):
        if not self.settings.enabled:
            raise AudioError("Audio is disabled; enable audio.enabled or pass --voice")
        if not self._lock.acquire(blocking=False):
            raise AudioError("A voice turn is already running")
        try:
            if self.stop_event.is_set():
                return VoiceTurn()
            clip = clip if clip is not None else self.devices.record(self.stop_event)
            if clip is None or not clip.pcm or self.stop_event.is_set():
                return VoiceTurn()
            text = self.stt.transcribe(clip).strip()
            if self.settings.wake_word:
                word = self.settings.wake_word
                if not text.casefold().startswith(word.casefold()):
                    return VoiceTurn()
                text = text[len(word):].lstrip(" ,:!.-")
            if not text or self.stop_event.is_set():
                return VoiceTurn()
            response = agent.ask(text, session)
            result = VoiceTurn(text, response)
            if self.settings.speak_responses and not self.stop_event.is_set():
                try:
                    self.speak(response.content)
                except Exception:
                    # Keep the completed agent response usable even if speech fails.
                    result.speech_error = "Could not speak the response; text response is available"
            return result
        finally:
            self._lock.release()
