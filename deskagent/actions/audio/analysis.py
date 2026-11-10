"""Signal analysis for bounded 16-bit PCM WAV files."""

from __future__ import annotations

import math

from deskagent.actions.audio._wav import WavAction, dbfs, read_wav

PATH = {"path": {"type": "string", "required": True}}
THRESHOLD = {"threshold_db": {"type": "float", "required": False, "default": -40, "minimum": -90, "maximum": 0}}
MIN_DURATION = {"min_duration": {"type": "float", "required": False, "default": 0.2, "minimum": 0, "maximum": 60}}


def _ranges(data, threshold_db, min_duration, active, inclusive=False):
    threshold = 32768 * 10 ** (threshold_db / 20)
    minimum = max(1, round(min_duration * data.rate))
    results, start = [], None
    for frame in range(data.frames + 1):
        condition = False
        if frame < data.frames:
            first = frame * data.channels
            level = max(abs(value) for value in data.samples[first:first + data.channels])
            condition = (level >= threshold if inclusive else level > threshold) if active else level <= threshold
        if condition and start is None:
            start = frame
        elif not condition and start is not None:
            if frame - start >= minimum:
                results.append({"start_seconds": round(start / data.rate, 6),
                                "end_seconds": round(frame / data.rate, 6)})
            start = None
    return {"ranges": results[:1000], "truncated": len(results) > 1000,
            "threshold_db": threshold_db, "min_duration": min_duration}


class InspectWavFile(WavAction):
    name = "inspect_wav_file"
    description = "Read verified PCM WAV format, channel count, sample rate, frames and duration"
    parameters_schema = PATH
    discoverable = True

    def execute(self, context, parameters):
        return self.run(lambda: read_wav(context, parameters["path"]).info())


class AnalyzeWavLevels(WavAction):
    name = "analyze_wav_levels"
    description = "Measure peak, RMS, DC offset, clipping and crest factor per WAV channel"
    parameters_schema = PATH
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            data = read_wav(context, parameters["path"])
            channels = []
            for channel in range(data.channels):
                values = data.samples[channel::data.channels]
                peak = max(abs(value) for value in values)
                rms = math.sqrt(sum(value * value for value in values) / len(values))
                dc = sum(values) / len(values)
                channels.append({
                    "channel": channel, "peak_dbfs": dbfs(peak), "rms_dbfs": dbfs(rms),
                    "dc_offset": round(dc / 32768, 6),
                    "clipped_samples": sum(abs(value) >= 32767 for value in values),
                    "crest_factor_db": round(20 * math.log10(peak / rms), 3) if rms else None,
                })
            return {**data.info(), "channels_analysis": channels}
        return self.run(operation)


class DetectWavSilence(WavAction):
    name = "detect_wav_silence"
    description = "Find quiet time ranges below an amplitude threshold"
    parameters_schema = {**PATH, **THRESHOLD, **MIN_DURATION}
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            data = read_wav(context, parameters["path"])
            return {"path": str(data.path), **_ranges(
                data, parameters.get("threshold_db", -40), parameters.get("min_duration", 0.2), False
            )}
        return self.run(operation)


class DetectWavActivity(WavAction):
    name = "detect_wav_activity"
    description = "Find active time ranges above an amplitude threshold"
    parameters_schema = {**PATH, **THRESHOLD, **MIN_DURATION}
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            data = read_wav(context, parameters["path"])
            return {"path": str(data.path), **_ranges(
                data, parameters.get("threshold_db", -40), parameters.get("min_duration", 0.2), True
            )}
        return self.run(operation)


class GetWavWaveform(WavAction):
    name = "get_wav_waveform"
    description = "Return bounded min, max and RMS waveform bins for visual inspection"
    parameters_schema = {**PATH, "bins": {"type": "integer", "required": False, "default": 100,
                                          "minimum": 1, "maximum": 1000}}
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            data = read_wav(context, parameters["path"])
            count = min(parameters.get("bins", 100), data.frames)
            waveform = []
            for index in range(count):
                start = index * data.frames // count
                end = (index + 1) * data.frames // count
                values = data.samples[start * data.channels:end * data.channels]
                rms = math.sqrt(sum(value * value for value in values) / len(values))
                waveform.append({"start_seconds": round(start / data.rate, 6),
                                 "min": min(values) / 32768, "max": max(values) / 32768,
                                 "rms": round(rms / 32768, 6)})
            return {"path": str(data.path), "bins": waveform, "channels": data.channels}
        return self.run(operation)


class FindWavClipping(WavAction):
    name = "find_wav_clipping"
    description = "Find time ranges whose samples approach or reach the PCM ceiling"
    parameters_schema = {**PATH,
                         "level": {"type": "float", "required": False, "default": 0.99,
                                   "minimum": 0.5, "maximum": 1.0}}
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            data = read_wav(context, parameters["path"])
            level = parameters.get("level", 0.99)
            threshold_db = 20 * math.log10(level)
            return {"path": str(data.path), "level": level, **_ranges(data, threshold_db, 0, True, True)}
        return self.run(operation)


class GetWavChannelBalance(WavAction):
    name = "get_wav_channel_balance"
    description = "Measure the left/right RMS difference of a stereo WAV"
    parameters_schema = PATH
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            data = read_wav(context, parameters["path"])
            if data.channels != 2:
                raise ValueError("Stereo WAV is required")
            values = [data.samples[channel::2] for channel in range(2)]
            rms = [math.sqrt(sum(value * value for value in part) / len(part)) for part in values]
            return {"path": str(data.path), "left_rms_dbfs": dbfs(rms[0]),
                    "right_rms_dbfs": dbfs(rms[1]),
                    "right_minus_left_db": round(20 * math.log10(rms[1] / rms[0]), 3)
                    if all(rms) else None}
        return self.run(operation)


class CompareWavFiles(WavAction):
    name = "compare_wav_files"
    description = "Compare WAV sample formats and count sample-level differences"
    parameters_schema = {"source": {"type": "string", "required": True},
                         "destination": {"type": "string", "required": True}}
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            left = read_wav(context, parameters["source"])
            right = read_wav(context, parameters["destination"])
            compatible = (left.channels, left.rate, left.frames) == (right.channels, right.rate, right.frames)
            differences = sum(a != b for a, b in zip(left.samples, right.samples)) if compatible else None
            return {"compatible": compatible, "identical": compatible and differences == 0,
                    "different_samples": differences, "source": left.info(), "destination": right.info()}
        return self.run(operation)


class GetWavZeroCrossingRate(WavAction):
    name = "get_wav_zero_crossing_rate"
    description = "Measure sign-change rate per channel as a rough signal texture indicator"
    parameters_schema = PATH
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            data = read_wav(context, parameters["path"])
            rates = []
            for channel in range(data.channels):
                values = data.samples[channel::data.channels]
                crossings = sum((a < 0) != (b < 0) for a, b in zip(values, values[1:]))
                rates.append({"channel": channel, "crossings": crossings,
                              "crossings_per_second": round(crossings / data.duration, 3)})
            return {"path": str(data.path), "channels": rates}
        return self.run(operation)
