"""Registered Apple Music actions. All identifiers are persistent Music IDs."""

from __future__ import annotations

from deskagent.actions.base import Action
from deskagent.actions.music.backend import MusicBackend
from deskagent.actions.types import ActionCategory, ActionResult, RiskLevel


def field(kind="string", required=True, **options):
    return {"type": kind, "required": required, **options}


TRACK = {"track_id": field()}
PLAYLIST = {"playlist_id": field()}
PAGE = {
    "limit": field("integer", False, default=50, minimum=1, maximum=200),
    "offset": field("integer", False, default=0, minimum=0),
}
FILTER = {**PAGE, "query": field()}


class _MusicAction(Action):
    discoverable = False
    category = ActionCategory.MEDIA
    operation = ""
    fixed: dict = {}

    def execute(self, context, parameters):
        try:
            if not isinstance(parameters, dict):
                raise ValueError("parameters must be an object")
            args = dict(self.fixed)
            for key, spec in self.parameters_schema.items():
                value = parameters.get(key, spec.get("default"))
                if value is None:
                    if spec.get("required"):
                        raise ValueError(f"{key} is required")
                    continue
                kind = spec["type"]
                valid = (
                    (kind == "string" and isinstance(value, str))
                    or (kind == "integer" and type(value) is int)
                    or (kind == "boolean" and type(value) is bool)
                )
                if not valid:
                    raise ValueError(f"{key} must be {kind}")
                if kind == "string" and (not value.strip() or len(value) > spec.get("max_length", 512)):
                    raise ValueError(f"{key} must contain 1-{spec.get('max_length', 512)} characters")
                if "minimum" in spec and value < spec["minimum"]:
                    raise ValueError(f"{key} must be at least {spec['minimum']}")
                if "maximum" in spec and value > spec["maximum"]:
                    raise ValueError(f"{key} must be at most {spec['maximum']}")
                if "enum" in spec and value not in spec["enum"]:
                    raise ValueError(f"{key} must be one of {spec['enum']}")
                args[key] = value
            service = getattr(getattr(context, "services", None), "music", None) or MusicBackend()
            result = service.call(self.operation, **args)
            if self.operation == "set_track":
                actual = result["track"].get(args["field"])
                if actual != args["value"]:
                    raise RuntimeError("Music did not retain the track change")
            if self.operation == "set_playlist":
                if result["playlist"].get(args["field"]) != args["value"]:
                    raise RuntimeError("Music did not retain the playlist change")
            if self.operation in {"volume", "mute", "shuffle", "repeat"}:
                key = {"volume": "volume", "mute": "mute", "shuffle": "shuffle", "repeat": "repeat"}[self.operation]
                requested = args.get("volume", args.get("enabled", args.get("mode")))
                if result.get(key) != requested:
                    raise RuntimeError("Music did not retain the playback setting")
            return ActionResult(True, result)
        except Exception as exc:
            return ActionResult(False, error=str(exc), error_code="MUSIC_ERROR")


def register(class_name, name, description, operation, schema=None, *, fixed=None, write=False):
    globals()[class_name] = type(
        class_name,
        (_MusicAction,),
        {
            "__module__": __name__,
            "discoverable": True,
            "name": name,
            "description": description,
            "operation": operation,
            "parameters_schema": schema or {},
            "fixed": fixed or {},
            "risk_level": RiskLevel.MEDIUM if write else RiskLevel.LOW,
        },
    )


# Availability and player state.
register(
    "CheckMusicAvailability", "check_music_availability", "Check whether Apple Music is installed and running", "ping"
)
register(
    "GetMusicPlayerState",
    "get_music_player_state",
    "Read player state, position, volume, mode and current song",
    "state",
)
register("GetCurrentMusicTrack", "get_current_music_track", "Read the current Apple Music track", "current_track")
register(
    "GetCurrentMusicPlaylist",
    "get_current_music_playlist",
    "Read the current Apple Music playlist",
    "current_playlist",
)

# Playback controls. Each result includes the player state read after the command.
for cls, name, description, op in [
    ("PlayMusic", "play_music", "Start or resume Apple Music playback", "play"),
    ("PauseMusic", "pause_music", "Pause Apple Music playback", "pause"),
    ("ToggleMusicPlayback", "toggle_music_playback", "Toggle playing and paused state", "playpause"),
    ("StopMusic", "stop_music", "Stop Apple Music playback", "stop"),
    ("NextMusicTrack", "next_music_track", "Skip to the next track", "next"),
    ("PreviousMusicTrack", "previous_music_track", "Go to the previous track", "previous"),
    ("RestartMusicTrack", "restart_music_track", "Restart the current track", "back"),
]:
    register(cls, name, description, op, write=True)
register(
    "SeekMusic",
    "seek_music",
    "Seek to a position in the current track",
    "seek",
    {"seconds": field("integer", minimum=0, maximum=86400)},
    write=True,
)
register(
    "SetMusicVolume",
    "set_music_volume",
    "Set Music player volume from 0 to 100",
    "volume",
    {"volume": field("integer", minimum=0, maximum=100)},
    write=True,
)
register(
    "SetMusicMute", "set_music_mute", "Set Music player mute state", "mute", {"enabled": field("boolean")}, write=True
)
register(
    "SetMusicShuffle",
    "set_music_shuffle",
    "Enable or disable Music shuffle",
    "shuffle",
    {"enabled": field("boolean")},
    write=True,
)
register(
    "SetMusicRepeat",
    "set_music_repeat",
    "Set Music repeat mode",
    "repeat",
    {"mode": field(enum=["off", "one", "all"])},
    write=True,
)
register(
    "PlayMusicTrack", "play_music_track", "Play a library track by persistent ID", "play_track", TRACK, write=True
)
register(
    "PlayMusicPlaylist",
    "play_music_playlist",
    "Play a playlist by persistent ID",
    "play_playlist",
    PLAYLIST,
    write=True,
)

# Library discovery and track detail.
register(
    "GetMusicLibraryStats",
    "get_music_library_stats",
    "Read track count, playlist count, duration and size",
    "library_stats",
)
register(
    "ListMusicTracks",
    "list_music_tracks",
    "Page through tracks in the Music library",
    "scan",
    PAGE,
    fixed={"which": "all", "query": ""},
)
register(
    "SearchMusicTracks",
    "search_music_tracks",
    "Search track title, artist, album and genre",
    "scan",
    FILTER,
    fixed={"which": "search"},
)
for cls, name, desc, which in [
    ("FindMusicTracksByArtist", "find_music_tracks_by_artist", "Find tracks by exact artist", "artist"),
    ("FindMusicTracksByAlbum", "find_music_tracks_by_album", "Find tracks by exact album", "album"),
    ("FindMusicTracksByGenre", "find_music_tracks_by_genre", "Find tracks by exact genre", "genre"),
]:
    register(cls, name, desc, "scan", FILTER, fixed={"which": which})
register(
    "ListFavoriteMusicTracks",
    "list_favorite_music_tracks",
    "List favorited library tracks",
    "scan",
    PAGE,
    fixed={"which": "favorites", "query": ""},
)
register(
    "ListUnplayedMusicTracks",
    "list_unplayed_music_tracks",
    "List never played library tracks",
    "scan",
    PAGE,
    fixed={"which": "unplayed", "query": ""},
)
for cls, name, desc, field_name in [
    ("ListMusicArtists", "list_music_artists", "Count library tracks by artist", "artist"),
    ("ListMusicAlbums", "list_music_albums", "Count library tracks by album", "album"),
    ("ListMusicGenres", "list_music_genres", "Count library tracks by genre", "genre"),
]:
    register(
        cls,
        name,
        desc,
        "scan",
        {"limit": PAGE["limit"]},
        fixed={"which": "groups", "field": field_name, "query": "", "offset": 0},
    )
register("GetMusicTrack", "get_music_track", "Read metadata for a library track", "track", TRACK)
register("GetMusicTrackLyrics", "get_music_track_lyrics", "Read stored lyrics for a library track", "lyrics", TRACK)
register(
    "RevealMusicTrack", "reveal_music_track", "Reveal a track in the Music window", "reveal_track", TRACK, write=True
)

# Playlist discovery and management.
register("ListMusicPlaylists", "list_music_playlists", "Page through Apple Music playlists", "playlists", PAGE)
register("GetMusicPlaylist", "get_music_playlist", "Read playlist metadata by persistent ID", "playlist", PLAYLIST)
register(
    "GetMusicPlaylistStats",
    "get_music_playlist_stats",
    "Read playlist duration, size and track count",
    "playlist_stats",
    PLAYLIST,
)
register(
    "ListMusicPlaylistTracks",
    "list_music_playlist_tracks",
    "Page through tracks in a playlist",
    "scan",
    {**PLAYLIST, **PAGE},
    fixed={"which": "all", "query": ""},
)
register(
    "SearchMusicPlaylistTracks",
    "search_music_playlist_tracks",
    "Search tracks within a playlist",
    "scan",
    {**PLAYLIST, **FILTER},
    fixed={"which": "search"},
)
register(
    "RevealMusicPlaylist",
    "reveal_music_playlist",
    "Reveal a playlist in the Music window",
    "reveal_playlist",
    PLAYLIST,
    write=True,
)
register(
    "CreateMusicPlaylist",
    "create_music_playlist",
    "Create a user playlist in the Music library",
    "create_playlist",
    {"name": field(max_length=200)},
    write=True,
)
register(
    "AddMusicTrackToPlaylist",
    "add_music_track_to_playlist",
    "Add a library track to a user playlist",
    "add_to_playlist",
    {**TRACK, **PLAYLIST},
    write=True,
)

# Reversible library metadata changes.
for cls, name, desc, field_name, value_spec in [
    (
        "SetMusicTrackFavorite",
        "set_music_track_favorite",
        "Set a track's favorite flag",
        "favorited",
        field("boolean"),
    ),
    (
        "SetMusicTrackRating",
        "set_music_track_rating",
        "Set a track rating from 0 to 100",
        "rating",
        field("integer", minimum=0, maximum=100),
    ),
    ("SetMusicTrackComment", "set_music_track_comment", "Set a track comment", "comment", field(max_length=4000)),
    ("SetMusicTrackGenre", "set_music_track_genre", "Set a track genre", "genre", field(max_length=200)),
    (
        "SetMusicTrackBpm",
        "set_music_track_bpm",
        "Set a track tempo in BPM",
        "bpm",
        field("integer", minimum=0, maximum=999),
    ),
]:
    register(cls, name, desc, "set_track", {**TRACK, "value": value_spec}, fixed={"field": field_name}, write=True)
register(
    "RenameMusicPlaylist",
    "rename_music_playlist",
    "Rename a playlist",
    "set_playlist",
    {**PLAYLIST, "value": field(max_length=200)},
    fixed={"field": "name"},
    write=True,
)
register(
    "SetMusicPlaylistDescription",
    "set_music_playlist_description",
    "Set a playlist description",
    "set_playlist",
    {**PLAYLIST, "value": field(max_length=4000)},
    fixed={"field": "description"},
    write=True,
)
