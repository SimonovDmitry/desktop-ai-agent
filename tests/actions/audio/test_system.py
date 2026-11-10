from types import SimpleNamespace
from unittest.mock import Mock

from deskagent.actions.audio import system
from deskagent.core.config import SecuritySettings, Settings


def test_list_system_voices_parses_installed_voices(monkeypatch):
    monkeypatch.setattr(system, "_macos", lambda: None)
    monkeypatch.setattr(system.subprocess, "run", lambda *args, **kwargs:
                        SimpleNamespace(stdout="Anna                 ru_RU    # example\n"))
    result = system.ListSystemVoices().execute(None, {})
    assert result.success
    assert result.data["voices"] == [{"name": "Anna", "locale": "ru_RU"}]


def test_render_speech_never_deletes_preexisting_file(tmp_path, monkeypatch):
    monkeypatch.setattr(system, "_macos", lambda: None)
    run = Mock()
    monkeypatch.setattr(system.subprocess, "run", run)
    target = tmp_path / "existing.aiff"
    target.write_bytes(b"original")
    context = SimpleNamespace(settings=Settings(security=SecuritySettings(allowed_paths=[str(tmp_path)])))
    result = system.RenderSpeechToFile().execute(context, {"text": "hello", "output_path": str(target)})
    assert not result.success
    assert target.read_bytes() == b"original"
    run.assert_not_called()


def test_render_speech_creates_new_private_file(tmp_path, monkeypatch):
    monkeypatch.setattr(system, "_macos", lambda: None)

    def fake_run(command, **kwargs):
        target = command[command.index("-o") + 1]
        with open(target, "wb") as output:
            output.write(b"audio")

    monkeypatch.setattr(system.subprocess, "run", fake_run)
    target = tmp_path / "new.aiff"
    context = SimpleNamespace(settings=Settings(security=SecuritySettings(allowed_paths=[str(tmp_path)])))
    result = system.RenderSpeechToFile().execute(context, {"text": "hello", "output_path": str(target)})
    assert result.success
    assert target.read_bytes() == b"audio"
    assert target.stat().st_mode & 0o777 == 0o600
