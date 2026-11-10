"""Music actions are tested without changing the user's library."""

import json
from types import SimpleNamespace

import pytest

from deskagent.actions.music import actions, backend
from deskagent.actions.registry import create_action_registry


class FakeBackend:
    def __init__(self):
        self.calls = []

    def call(self, op, **kwargs):
        self.calls.append((op, kwargs))
        if op == "set_track":
            return {"track": {kwargs["field"]: kwargs["value"]}}
        if op == "set_playlist":
            return {"playlist": {kwargs["field"]: kwargs["value"]}}
        if op in {"volume", "mute", "shuffle", "repeat"}:
            key = {"volume": "volume", "mute": "mute", "shuffle": "shuffle", "repeat": "repeat"}[op]
            return {key: kwargs.get("volume", kwargs.get("enabled", kwargs.get("mode")))}
        return {"operation": op, **kwargs}


def test_all_music_actions_registered():
    registry = create_action_registry(include_plugins=False)
    names = {a.name for a in registry.all() if a.__module__ == actions.__name__}
    assert len(names) == 47
    assert {
        "play_music_track",
        "search_music_tracks",
        "create_music_playlist",
        "get_music_track_lyrics",
        "set_music_track_rating",
    } <= names


def test_read_and_write_dispatch(monkeypatch):
    fake = FakeBackend()
    monkeypatch.setattr(actions, "MusicBackend", lambda: fake)
    cases = [
        ("get_music_player_state", {}, "state"),
        ("list_music_tracks", {}, "scan"),
        ("search_music_tracks", {"query": "Björk"}, "scan"),
        ("list_music_playlist_tracks", {"playlist_id": "ABC"}, "scan"),
        ("play_music_track", {"track_id": "TRACK"}, "play_track"),
        ("set_music_volume", {"volume": 35}, "volume"),
        ("set_music_track_rating", {"track_id": "TRACK", "value": 80}, "set_track"),
        ("rename_music_playlist", {"playlist_id": "ABC", "value": "New"}, "set_playlist"),
        ("create_music_playlist", {"name": "Travel"}, "create_playlist"),
        ("add_music_track_to_playlist", {"playlist_id": "ABC", "track_id": "TRACK"}, "add_to_playlist"),
    ]
    registry = create_action_registry(include_plugins=False)
    for name, params, operation in cases:
        result = registry.create(name).execute(None, params)
        assert result.success, (name, result.error)
        assert fake.calls[-1][0] == operation
    assert fake.calls[1][1]["limit"] == 50
    assert fake.calls[2][1]["query"] == "Björk"


@pytest.mark.parametrize(
    "name,params",
    [
        ("search_music_tracks", {"query": ""}),
        ("list_music_tracks", {"limit": 201}),
        ("list_music_tracks", {"offset": -1}),
        ("set_music_volume", {"volume": True}),
        ("set_music_volume", {"volume": 101}),
        ("set_music_repeat", {"mode": "forever"}),
        ("get_music_track", {"track_id": " "}),
    ],
)
def test_invalid_parameters_fail_before_backend(monkeypatch, name, params):
    fake = FakeBackend()
    monkeypatch.setattr(actions, "MusicBackend", lambda: fake)
    result = create_action_registry(include_plugins=False).create(name).execute(None, params)
    assert not result.success
    assert fake.calls == []


def test_music_backend_passes_untrusted_text_as_json_argument(monkeypatch):
    monkeypatch.setattr(backend.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(backend.Path, "is_dir", lambda self: True)
    captured = {}

    def run(argv, **kwargs):
        captured["argv"] = argv
        return SimpleNamespace(returncode=0, stdout='{"tracks":[]}', stderr="")

    monkeypatch.setattr(backend.subprocess, "run", run)
    malicious = '"; app.stop(); //'
    result = backend.MusicBackend().call("scan", query=malicious)
    assert result == {"tracks": []}
    assert malicious not in captured["argv"][4]
    assert json.loads(captured["argv"][5])["query"] == malicious
    assert captured["argv"][:4] == ["/usr/bin/osascript", "-l", "JavaScript", "-e"]


def test_music_backend_rejects_non_macos(monkeypatch):
    monkeypatch.setattr(backend.platform, "system", lambda: "Linux")
    with pytest.raises(RuntimeError, match="macOS"):
        backend.MusicBackend().call("ping")
