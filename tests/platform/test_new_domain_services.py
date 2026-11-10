"""New platform adapters are wired into actions without touching real apps."""
from types import SimpleNamespace

from deskagent.actions.audio import system as audio_actions
from deskagent.actions.music import actions as music_actions
from deskagent.actions.notes.reading import CheckNotesAvailability
from deskagent.actions.vision.screen import CaptureWindow, ReadScreenText
from deskagent.actions.system import capabilities
from deskagent.core.services import ServicesFactory
from deskagent.platform.base.audio import AudioService
from deskagent.platform.base.image import ImageService
from deskagent.platform.base.music import MusicService
from deskagent.platform.base.notes import NotesService
from deskagent.platform.base.vision import VisionService


def test_factory_wires_new_platform_contracts():
    services = ServicesFactory.create()
    assert isinstance(services.media_audio, AudioService)
    assert isinstance(services.music, MusicService)
    assert isinstance(services.notes, NotesService)
    assert isinstance(services.vision, VisionService)
    assert isinstance(services.image, ImageService)


def test_music_and_notes_actions_use_context_services():
    calls = []
    music = SimpleNamespace(call=lambda op, **params: calls.append(("music", op, params)) or {"available": True})
    notes = SimpleNamespace(call=lambda op, **params: calls.append(("notes", op, params)) or {"available": True})
    context = SimpleNamespace(services=SimpleNamespace(music=music, notes=notes))
    assert music_actions.CheckMusicAvailability().execute(context, {}).success
    assert CheckNotesAvailability().execute(context, {}).success
    assert calls == [("music", "ping", {}), ("notes", "ping", {})]


def test_vision_actions_use_context_service(tmp_path):
    calls = []
    image = tmp_path / "capture.png"
    image.write_bytes(b"png")
    vision = SimpleNamespace(
        capture=lambda window_id=None: calls.append(("capture", window_id)) or {"path": str(image)},
        read_text=lambda path: calls.append(("read_text", path)) or [{"text": "Save"}],
    )
    context = SimpleNamespace(services=SimpleNamespace(vision=vision))
    assert CaptureWindow().execute(context, {"window_id": 42}).success
    result = ReadScreenText().execute(context, {})
    assert result.success and result.data["lines"] == [{"text": "Save"}]
    assert calls == [("capture", 42), ("capture", None), ("read_text", str(image))]
    assert not image.exists()


def test_audio_action_uses_context_service(monkeypatch):
    monkeypatch.setattr(audio_actions, "_macos", lambda: None)
    audio = SimpleNamespace(list_voices=lambda: "Anna ru_RU # test\n")
    context = SimpleNamespace(services=SimpleNamespace(media_audio=audio))
    result = audio_actions.ListSystemVoices().execute(context, {})
    assert result.success
    assert result.data["voices"] == [{"name": "Anna", "locale": "ru_RU"}]


def test_platform_only_actions_report_unavailable_off_macos(monkeypatch):
    monkeypatch.setattr(capabilities.platform, "system", lambda: "Linux")
    for name in ("play_music", "capture_screen", "convert_audio_format", "list_system_voices"):
        result = capabilities._availability(None, name)
        assert result["available"] is False
        assert "macOS" in result["reason"]
