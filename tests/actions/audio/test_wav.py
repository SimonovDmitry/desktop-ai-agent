import platform
import wave
from array import array
from types import SimpleNamespace

import pytest

from deskagent.actions.audio._wav import read_wav
from deskagent.actions.audio.analysis import (
    AnalyzeWavLevels, CompareWavFiles, DetectWavActivity, DetectWavSilence,
    FindWavClipping, GetWavChannelBalance, GetWavWaveform, GetWavZeroCrossingRate,
)
from deskagent.actions.audio.edit import (
    AdjustWavGain, ConcatenateWavFiles, ConvertWavChannels, ExtractWavChannel,
    FadeWavFile, InsertWavSilence, MixWavFiles, NormalizeWavPeak, PadWavFile,
    ReverseWavFile, SplitWavFile, TrimWavFile, TrimWavSilence,
)
from deskagent.actions.audio.generate import (
    GenerateChirpWav, GenerateClickTrackWav, GenerateNoiseWav, GenerateSilenceWav, GenerateToneWav,
)
from deskagent.actions.audio.convert import (
    ConvertAudioChannelCount, ConvertAudioFormat, ExtractAudioTrack, ResampleAudioFile,
)
from deskagent.actions.registry import create_action_registry
from deskagent.core.config import SecuritySettings, Settings


def context(tmp_path):
    settings = Settings(security=SecuritySettings(allowed_paths=[str(tmp_path)], blocked_paths=[]))
    return SimpleNamespace(settings=settings)


def wav(tmp_path, name, samples, channels=1, rate=8000):
    target = tmp_path / name
    with wave.open(str(target), "wb") as stream:
        stream.setnchannels(channels)
        stream.setsampwidth(2)
        stream.setframerate(rate)
        stream.writeframes(array("h", samples).tobytes())
    return target


def test_analysis_finds_silence_activity_and_waveform(tmp_path):
    source = wav(tmp_path, "signal.wav", [0] * 200 + [10000] * 400 + [0] * 200)
    ctx = context(tmp_path)
    levels = AnalyzeWavLevels().execute(ctx, {"path": str(source)})
    silence = DetectWavSilence().execute(ctx, {"path": str(source), "min_duration": 0.01})
    activity = DetectWavActivity().execute(ctx, {"path": str(source), "min_duration": 0.01})
    waveform = GetWavWaveform().execute(ctx, {"path": str(source), "bins": 4})
    assert levels.success and levels.data["channels_analysis"][0]["peak_dbfs"] < 0
    assert silence.data["ranges"] == [
        {"start_seconds": 0.0, "end_seconds": 0.025},
        {"start_seconds": 0.075, "end_seconds": 0.1},
    ]
    assert activity.data["ranges"] == [{"start_seconds": 0.025, "end_seconds": 0.075}]
    assert waveform.success and len(waveform.data["bins"]) == 4


def test_clipping_balance_zero_crossing_and_compare(tmp_path):
    stereo = wav(tmp_path, "stereo.wav", [1000, 2000, -1000, -2000] * 20, channels=2)
    identical = wav(tmp_path, "copy.wav", [1000, 2000, -1000, -2000] * 20, channels=2)
    clipped = wav(tmp_path, "clipped.wav", [0, -32768, 0])
    ctx = context(tmp_path)
    balance = GetWavChannelBalance().execute(ctx, {"path": str(stereo)})
    crossings = GetWavZeroCrossingRate().execute(ctx, {"path": str(stereo)})
    comparison = CompareWavFiles().execute(ctx, {"source": str(stereo), "destination": str(identical)})
    clipping = FindWavClipping().execute(ctx, {"path": str(clipped), "level": 1.0})
    assert balance.success and 6 < balance.data["right_minus_left_db"] < 6.1
    assert crossings.success and crossings.data["channels"][0]["crossings"] > 0
    assert comparison.data["identical"] is True
    assert clipping.data["ranges"] == [{"start_seconds": 0.000125, "end_seconds": 0.00025}]


def test_trim_reverse_gain_normalize_and_fade(tmp_path):
    source = wav(tmp_path, "stereo.wav", [1000, 2000, 3000, 4000] * 40, channels=2)
    ctx = context(tmp_path)
    trim = TrimWavFile().execute(ctx, {
        "path": str(source), "output_path": str(tmp_path / "trim.wav"),
        "start_seconds": 0.001, "end_seconds": 0.003,
    })
    reverse = ReverseWavFile().execute(ctx, {"path": str(source), "output_path": str(tmp_path / "reverse.wav")})
    gain = AdjustWavGain().execute(ctx, {
        "path": str(source), "output_path": str(tmp_path / "gain.wav"), "gain_db": -6,
    })
    normalize = NormalizeWavPeak().execute(ctx, {"path": str(source), "output_path": str(tmp_path / "normal.wav")})
    fade = FadeWavFile().execute(ctx, {
        "path": str(source), "output_path": str(tmp_path / "fade.wav"),
        "fade_in_seconds": 0.002, "fade_out_seconds": 0.002,
    })
    assert all(item.success for item in (trim, reverse, gain, normalize, fade))
    assert read_wav(ctx, trim.data["path"]).frames == 16
    assert list(read_wav(ctx, reverse.data["path"]).samples[:4]) == [3000, 4000, 1000, 2000]
    assert max(read_wav(ctx, gain.data["path"]).samples) < 4000
    assert max(read_wav(ctx, normalize.data["path"]).samples) > 20000
    assert list(read_wav(ctx, fade.data["path"]).samples[:2]) == [0, 0]


def test_mix_clips_only_after_adding_sources(tmp_path):
    first = wav(tmp_path, "first.wav", [30000] * 80)
    second = wav(tmp_path, "second.wav", [-30000] * 80)
    ctx = context(tmp_path)
    result = MixWavFiles().execute(ctx, {"first_path": str(first), "second_path": str(second),
                                         "output_path": str(tmp_path / "mixed.wav"),
                                         "first_gain_db": 6, "second_gain_db": 6})
    assert result.success
    assert set(read_wav(ctx, result.data["path"]).samples) == {0}


def test_channel_pad_insert_concat_split_and_silence_trim(tmp_path):
    source = wav(tmp_path, "source.wav", [0] * 80 + [1000] * 80 + [0] * 80)
    ctx = context(tmp_path)
    extract = ExtractWavChannel().execute(ctx, {
        "path": str(source), "channel": 0, "output_path": str(tmp_path / "extract.wav"),
    })
    channels = ConvertWavChannels().execute(ctx, {
        "path": str(source), "channels": 2, "output_path": str(tmp_path / "stereo.wav"),
    })
    pad = PadWavFile().execute(ctx, {
        "path": str(source), "output_path": str(tmp_path / "pad.wav"), "start_seconds": 0.01,
    })
    insert = InsertWavSilence().execute(ctx, {
        "path": str(source), "output_path": str(tmp_path / "insert.wav"),
        "at_seconds": 0.01, "duration_seconds": 0.01,
    })
    concat = ConcatenateWavFiles().execute(ctx, {
        "paths": [str(source), str(source)], "output_path": str(tmp_path / "concat.wav"),
    })
    split = SplitWavFile().execute(ctx, {
        "path": str(source), "output_directory": str(tmp_path / "parts"), "segment_seconds": 0.01,
    })
    trimmed = TrimWavSilence().execute(ctx, {
        "path": str(source), "output_path": str(tmp_path / "quiet.wav"),
    })
    assert all(item.success for item in (extract, channels, pad, insert, concat, split, trimmed))
    assert read_wav(ctx, channels.data["path"]).channels == 2
    assert read_wav(ctx, pad.data["path"]).frames == 320
    assert read_wav(ctx, insert.data["path"]).frames == 320
    assert read_wav(ctx, concat.data["path"]).frames == 480
    assert split.data["count"] == 3
    assert read_wav(ctx, trimmed.data["path"]).frames == 80


def test_generators_are_bounded_and_noise_is_reproducible(tmp_path):
    ctx = context(tmp_path)
    base = {"duration_seconds": 0.02, "sample_rate": 8000}
    actions = [
        (GenerateToneWav(), {"frequency_hz": 440}),
        (GenerateChirpWav(), {"start_hz": 200, "end_hz": 800}),
        (GenerateNoiseWav(), {"seed": 7}),
        (GenerateSilenceWav(), {}),
        (GenerateClickTrackWav(), {"bpm": 120}),
    ]
    for index, (action, extra) in enumerate(actions):
        result = action.execute(ctx, {**base, **extra, "output_path": str(tmp_path / f"generated_{index}.wav")})
        assert result.success, (action.name, result.error)
        assert read_wav(ctx, result.data["path"]).frames == 160
    second = GenerateNoiseWav().execute(ctx, {**base, "seed": 7,
                                              "output_path": str(tmp_path / "noise_again.wav")})
    assert list(read_wav(ctx, second.data["path"]).samples) == list(
        read_wav(ctx, tmp_path / "generated_2.wav").samples
    )


def test_output_is_new_and_inside_allowed_directory(tmp_path):
    ctx = context(tmp_path)
    source = wav(tmp_path, "source.wav", [1000] * 80)
    existing = tmp_path / "existing.wav"
    existing.write_bytes(b"original")
    collision = AdjustWavGain().execute(ctx, {"path": str(source), "output_path": str(existing), "gain_db": 1})
    outside = AdjustWavGain().execute(ctx, {"path": str(source),
                                            "output_path": str(tmp_path.parent / "outside.wav"), "gain_db": 1})
    assert not collision.success and existing.read_bytes() == b"original"
    assert not outside.success and not (tmp_path.parent / "outside.wav").exists()


def test_empty_wav_is_rejected(tmp_path):
    source = wav(tmp_path, "empty.wav", [])
    result = AnalyzeWavLevels().execute(context(tmp_path), {"path": str(source)})
    assert not result.success


@pytest.mark.skipif(platform.system() != "Darwin", reason="afconvert is macOS only")
def test_audio_conversion_actions(tmp_path):
    source = wav(tmp_path, "source.wav", [1000, -1000] * 800, channels=2)
    ctx = context(tmp_path)
    converted = ConvertAudioFormat().execute(ctx, {
        "path": str(source), "output_path": str(tmp_path / "converted.aiff"), "format": "aiff_pcm16",
    })
    resampled = ResampleAudioFile().execute(ctx, {
        "path": str(source), "output_path": str(tmp_path / "resampled.wav"), "sample_rate": 16000,
    })
    mono = ConvertAudioChannelCount().execute(ctx, {
        "path": str(source), "output_path": str(tmp_path / "mono.wav"), "channels": 1,
    })
    track = ExtractAudioTrack().execute(ctx, {
        "path": str(source), "output_path": str(tmp_path / "track.wav"), "track": 0,
    })
    assert all(result.success for result in (converted, resampled, mono, track))
    assert (tmp_path / "converted.aiff").stat().st_size > 0
    assert read_wav(ctx, resampled.data["path"]).rate == 16000
    assert read_wav(ctx, mono.data["path"]).channels == 1
    assert read_wav(ctx, track.data["path"]).frames > 0
    collision = ConvertAudioFormat().execute(ctx, {
        "path": str(source), "output_path": str(tmp_path / "converted.aiff"), "format": "aiff_pcm16",
    })
    assert not collision.success


def test_audio_actions_are_discoverable():
    names = create_action_registry(include_plugins=False).names()
    assert "generate_click_track_wav" in names
    assert "trim_wav_silence" in names
    assert "convert_audio_format" in names
    assert "analyze_wav_levels" in names
