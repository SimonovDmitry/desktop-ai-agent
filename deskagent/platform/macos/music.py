"""Apple Music JXA adapter. User values travel as JSON, never script source."""
from __future__ import annotations

import json
import platform
import subprocess
from pathlib import Path

from deskagent.platform.base.music import MusicService

MUSIC_APP = "/System/Applications/Music.app"
MAX_ARGUMENT_BYTES = 60_000
MAX_RESPONSE_BYTES = 2_000_000

SCRIPT = r'''
function run(argv) {
  const p = JSON.parse(argv[0] || "{}");
  const app = Application("/System/Applications/Music.app");
  const cap = 5000;
  function safe(fn, fallback) { try { return fn(); } catch (_) { return fallback; } }
  function str(fn) { return String(safe(fn, "")); }
  function num(fn) { return Number(safe(fn, 0)) || 0; }
  function id(item) { return str(() => item.persistentID()); }
  function date(fn) {
    const v = safe(fn, null);
    return v ? (v.toISOString ? v.toISOString() : String(v)) : null;
  }
  function trackInfo(t) {
    return {id: id(t), database_id: num(() => t.databaseID()), name: str(() => t.name()),
      artist: str(() => t.artist()), album: str(() => t.album()),
      album_artist: str(() => t.albumArtist()), genre: str(() => t.genre()),
      duration: num(() => t.duration()), year: num(() => t.year()),
      track_number: num(() => t.trackNumber()), disc_number: num(() => t.discNumber()),
      rating: num(() => t.rating()), favorited: Boolean(safe(() => t.favorited(), false)),
      played_count: num(() => t.playedCount()), played_at: date(() => t.playedDate()),
      added_at: date(() => t.dateAdded()), kind: str(() => t.kind())};
  }
  function playlistInfo(x) {
    return {id: id(x), name: str(() => x.name()), description: str(() => x.description()),
      duration: num(() => x.duration()), size: num(() => x.size()),
      special_kind: str(() => x.specialKind()), visible: Boolean(safe(() => x.visible(), true))};
  }
  function library() {
    const sources = app.sources();
    for (let i = 0; i < sources.length; i++) {
      const lists = sources[i].libraryPlaylists();
      if (lists.length) return lists[0];
    }
    throw new Error("Music library playlist is unavailable");
  }
  function playlist(ident) {
    const items = app.playlists();
    for (let i = 0; i < items.length; i++) if (id(items[i]) === ident) return items[i];
    throw new Error("Playlist not found by persistent ID");
  }
  function track(ident) {
    const items = library().tracks();
    for (let i = 0; i < Math.min(items.length, cap); i++)
      if (id(items[i]) === ident) return items[i];
    throw new Error("Track not found in first 5000 library tracks");
  }
  function state() {
    const t = safe(() => app.currentTrack(), null);
    const list = safe(() => app.currentPlaylist(), null);
    return {running: app.running(), player_state: str(() => app.playerState()),
      position: num(() => app.playerPosition()), volume: num(() => app.soundVolume()),
      mute: Boolean(safe(() => app.mute(), false)),
      shuffle: Boolean(safe(() => app.shuffleEnabled(), false)),
      repeat: str(() => app.songRepeat()),
      track: t ? trackInfo(t) : null, playlist: list ? playlistInfo(list) : null};
  }
  function scan(which, query) {
    const items = (p.playlist_id ? playlist(p.playlist_id) : library()).tracks();
    const found = [], groups = {}, lower = String(query || "").toLocaleLowerCase();
    let matched = 0;
    const count = Math.min(items.length, cap);
    for (let i = 0; i < count; i++) {
      const item = items[i];
      let hit = true;
      if (which === "search") hit = [str(() => item.name()), str(() => item.artist()),
        str(() => item.album()), str(() => item.genre()), str(() => item.albumArtist())]
        .join(" ").toLocaleLowerCase().includes(lower);
      if (which === "favorites") hit = Boolean(safe(() => item.favorited(), false));
      if (which === "unplayed") hit = num(() => item.playedCount()) === 0;
      if (which === "artist") hit = str(() => item.artist()).toLocaleLowerCase() === lower;
      if (which === "album") hit = str(() => item.album()).toLocaleLowerCase() === lower;
      if (which === "genre") hit = str(() => item.genre()).toLocaleLowerCase() === lower;
      if (which === "groups") {
        const key = str(() => item[p.field]()) || "(unknown)";
        groups[key] = (groups[key] || 0) + 1;
      }
      if (hit && which !== "groups") {
        if (matched >= p.offset && found.length < p.limit) found.push(trackInfo(item));
        matched++;
      }
    }
    if (which === "groups") {
      const entries = Object.keys(groups).map(name => ({name: name, count: groups[name]}));
      entries.sort((a, b) => b.count - a.count || a.name.localeCompare(b.name));
      return {items: entries.slice(0, p.limit), total: entries.length,
        scanned: count, scan_truncated: items.length > cap};
    }
    return {tracks: found, matched: matched, scanned: count,
      scan_truncated: items.length > cap,
      truncated: items.length > cap || matched > p.offset + found.length};
  }
  switch (p.op) {
    case "ping": return JSON.stringify({available: true, running: app.running()});
    case "state": return JSON.stringify(state());
    case "current_track": {
      const t = safe(() => app.currentTrack(), null);
      return JSON.stringify({track: t ? trackInfo(t) : null});
    }
    case "current_playlist": {
      const x = safe(() => app.currentPlaylist(), null);
      return JSON.stringify({playlist: x ? playlistInfo(x) : null});
    }
    case "play": app.play(); return JSON.stringify(state());
    case "pause": app.pause(); return JSON.stringify(state());
    case "playpause": app.playpause(); return JSON.stringify(state());
    case "stop": app.stop(); return JSON.stringify(state());
    case "next": app.nextTrack(); return JSON.stringify(state());
    case "previous": app.previousTrack(); return JSON.stringify(state());
    case "back": app.backTrack(); return JSON.stringify(state());
    case "seek": app.playerPosition = p.seconds; return JSON.stringify(state());
    case "volume": app.soundVolume = p.volume; return JSON.stringify(state());
    case "mute": app.mute = p.enabled; return JSON.stringify(state());
    case "shuffle": app.shuffleEnabled = p.enabled; return JSON.stringify(state());
    case "repeat": app.songRepeat = p.mode; return JSON.stringify(state());
    case "play_track": app.play(track(p.track_id)); return JSON.stringify(state());
    case "play_playlist": app.play(playlist(p.playlist_id)); return JSON.stringify(state());
    case "track": return JSON.stringify({track: trackInfo(track(p.track_id))});
    case "lyrics": {
      const t = track(p.track_id);
      return JSON.stringify({track_id: id(t), lyrics: str(() => t.lyrics())});
    }
    case "scan": return JSON.stringify(scan(p.which, p.query));
    case "playlists": {
      const items = app.playlists();
      const found = [];
      for (let i = p.offset; i < Math.min(items.length, p.offset + p.limit); i++)
        found.push(playlistInfo(items[i]));
      return JSON.stringify({playlists: found, total: items.length,
        truncated: items.length > p.offset + found.length});
    }
    case "playlist": return JSON.stringify({playlist: playlistInfo(playlist(p.playlist_id))});
    case "playlist_stats": {
      const x = playlist(p.playlist_id), info = playlistInfo(x);
      return JSON.stringify({playlist: info, track_count: x.tracks().length});
    }
    case "library_stats": {
      const x = library();
      return JSON.stringify({track_count: x.tracks().length,
        playlist_count: app.playlists().length, duration: num(() => x.duration()),
        size: num(() => x.size())});
    }
    case "set_track": {
      const t = track(p.track_id);
      if (p.field === "favorited") t.favorited = p.value;
      else if (p.field === "rating") t.rating = p.value;
      else if (p.field === "comment") t.comment = p.value;
      else if (p.field === "genre") t.genre = p.value;
      else if (p.field === "bpm") t.bpm = p.value;
      else throw new Error("Unsupported track field");
      const info = trackInfo(t);
      if (p.field === "comment") info.comment = str(() => t.comment());
      if (p.field === "bpm") info.bpm = num(() => t.bpm());
      return JSON.stringify({track: info});
    }
    case "set_playlist": {
      const x = playlist(p.playlist_id);
      if (p.field === "name") x.name = p.value;
      else if (p.field === "description") x.description = p.value;
      else throw new Error("Unsupported playlist field");
      return JSON.stringify({playlist: playlistInfo(x)});
    }
    case "create_playlist": {
      const source = library().container();
      const before = {};
      const old = source.userPlaylists();
      for (let i = 0; i < old.length; i++) before[id(old[i])] = true;
      source.userPlaylists.push(app.UserPlaylist({name: p.name}));
      const current = source.userPlaylists();
      for (let i = 0; i < current.length; i++) {
        const x = current[i];
        if (!before[id(x)] && str(() => x.name()) === p.name)
          return JSON.stringify({playlist: playlistInfo(x), created: true});
      }
      throw new Error("Created playlist could not be verified");
    }
    case "add_to_playlist": {
      const t = track(p.track_id), x = playlist(p.playlist_id);
      const databaseID = num(() => t.databaseID());
      const before = x.tracks().length;
      app.duplicate(t, {to: x});
      const items = x.tracks();
      if (items.length <= before) throw new Error("Track was not added to playlist");
      let verified = false;
      for (let i = 0; i < items.length; i++)
        if (num(() => items[i].databaseID()) === databaseID) verified = true;
      if (!verified) throw new Error("Added track could not be verified");
      return JSON.stringify({playlist_id: p.playlist_id, track_id: p.track_id,
        track_count: items.length, added: true});
    }
    case "reveal_track": app.reveal(track(p.track_id));
      return JSON.stringify({track_id: p.track_id, revealed: true});
    case "reveal_playlist": app.reveal(playlist(p.playlist_id));
      return JSON.stringify({playlist_id: p.playlist_id, revealed: true});
    default: throw new Error("Unsupported Music operation");
  }
}
'''


class MusicBackend(MusicService):
    def __init__(self, timeout=45):
        self.timeout = timeout

    def call(self, op, **parameters):
        if platform.system() != "Darwin" or not Path(MUSIC_APP).is_dir():
            raise RuntimeError("Apple Music actions require macOS Music")
        payload = json.dumps({"op": op, **parameters}, ensure_ascii=False)
        if len(payload.encode("utf-8")) > MAX_ARGUMENT_BYTES:
            raise ValueError("Music request exceeds 60 KB")
        result = subprocess.run(
            ["/usr/bin/osascript", "-l", "JavaScript", "-e", SCRIPT, payload],
            capture_output=True, text=True, timeout=self.timeout, check=False,
        )
        if result.returncode:
            raise RuntimeError(result.stderr.strip()[:1000] or "Apple Music automation failed")
        if len(result.stdout.encode("utf-8")) > MAX_RESPONSE_BYTES:
            raise ValueError("Music response exceeds 2 MB")
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise RuntimeError("Apple Music returned an invalid response") from exc
