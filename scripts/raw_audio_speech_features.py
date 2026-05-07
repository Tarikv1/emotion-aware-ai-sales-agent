#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import math
import struct
import wave
from pathlib import Path
from typing import Any


RAW_AUDIO_FEATURES_ID = "VOICE-030A-raw-audio-local-reader"
SUPPORTED_AUDIO_EXTENSIONS = {".wav"}
KNOWN_UNSUPPORTED_AUDIO_EXTENSIONS = {".mp3", ".m4a", ".aac", ".ogg", ".flac", ".webm"}


def stable_audio_id(text: str) -> str:
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return f"audio-{digest[:12]}"


def write_synthetic_wav(path: Path, recipe: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    sample_rate = int(recipe.get("sample_rate_hz", 16000))
    samples: list[int] = []
    for segment in recipe.get("segments", []):
        duration_ms = int(segment.get("duration_ms", 0))
        frame_count = max(0, int(round(sample_rate * (duration_ms / 1000))))
        if segment.get("kind") == "silence":
            samples.extend([0] * frame_count)
            continue
        amplitude = float(segment.get("amplitude", 0.3))
        frequency = float(segment.get("frequency_hz", 220))
        start_index = len(samples)
        for offset in range(frame_count):
            time_seconds = (start_index + offset) / sample_rate
            value = amplitude * math.sin(2 * math.pi * frequency * time_seconds)
            samples.append(int(max(-1.0, min(1.0, value)) * 32767))

    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(struct.pack(f"<{len(samples)}h", *samples))


def decode_pcm_samples(raw_frames: bytes, sample_width: int, channels: int) -> list[float]:
    if sample_width == 1:
        values = [(byte - 128) / 128 for byte in raw_frames]
    elif sample_width == 2:
        count = len(raw_frames) // 2
        values = [value / 32768 for (value,) in struct.iter_unpack("<h", raw_frames[: count * 2])]
    elif sample_width == 3:
        values = []
        for index in range(0, len(raw_frames) - 2, 3):
            raw_value = int.from_bytes(raw_frames[index : index + 3], "little", signed=False)
            if raw_value >= 1 << 23:
                raw_value -= 1 << 24
            values.append(raw_value / 8388608)
    elif sample_width == 4:
        count = len(raw_frames) // 4
        values = [value / 2147483648 for (value,) in struct.iter_unpack("<i", raw_frames[: count * 4])]
    else:
        raise ValueError(f"Unsupported WAV sample width: {sample_width} bytes")

    if channels <= 1:
        return values

    mono: list[float] = []
    for index in range(0, len(values) - channels + 1, channels):
        frame_values = values[index : index + channels]
        mono.append(sum(frame_values) / channels)
    return mono


def read_wav_samples(path: Path) -> tuple[list[float], dict[str, Any]]:
    with wave.open(str(path), "rb") as wav_file:
        if wav_file.getcomptype() != "NONE":
            raise ValueError(f"Unsupported WAV compression: {wav_file.getcomptype()}")
        channels = wav_file.getnchannels()
        sample_rate = wav_file.getframerate()
        sample_width = wav_file.getsampwidth()
        frame_count = wav_file.getnframes()
        raw_frames = wav_file.readframes(frame_count)
    samples = decode_pcm_samples(raw_frames, sample_width, channels)
    metadata = {
        "sample_rate_hz": sample_rate,
        "channels": channels,
        "sample_width_bytes": sample_width,
        "frame_count": frame_count,
    }
    return samples, metadata


def rms(values: list[float]) -> float:
    if not values:
        return 0.0
    return math.sqrt(sum(value * value for value in values) / len(values))


def frame_rms_values(samples: list[float], sample_rate: int, frame_ms: int) -> list[float]:
    frame_size = max(1, int(round(sample_rate * (frame_ms / 1000))))
    frames = []
    for index in range(0, len(samples), frame_size):
        frame = samples[index : index + frame_size]
        if frame:
            frames.append(rms(frame))
    return frames


def count_regions(flags: list[bool], target: bool) -> int:
    count = 0
    in_region = False
    for flag in flags:
        if flag is target and not in_region:
            count += 1
            in_region = True
        elif flag is not target:
            in_region = False
    return count


def silence_regions_ms(speech_flags: list[bool], frame_ms: int, min_pause_ms: int) -> list[int]:
    regions = []
    current_frames = 0
    for is_speech in speech_flags:
        if not is_speech:
            current_frames += 1
            continue
        duration = current_frames * frame_ms
        if duration >= min_pause_ms:
            regions.append(duration)
        current_frames = 0
    duration = current_frames * frame_ms
    if duration >= min_pause_ms:
        regions.append(duration)
    return regions


def analyze_wav_file(
    path: Path,
    *,
    frame_ms: int = 20,
    silence_threshold: float = 0.025,
    min_pause_ms: int = 180,
) -> dict[str, Any]:
    samples, metadata = read_wav_samples(path)
    sample_rate = int(metadata["sample_rate_hz"])
    frame_values = frame_rms_values(samples, sample_rate, frame_ms)
    speech_flags = [value >= silence_threshold for value in frame_values]
    speech_frame_count = sum(1 for flag in speech_flags if flag)
    silence_frame_count = len(speech_flags) - speech_frame_count
    speech_values = [value for value, flag in zip(frame_values, speech_flags) if flag]
    pause_regions = silence_regions_ms(speech_flags, frame_ms, min_pause_ms)
    duration_seconds = len(samples) / sample_rate if sample_rate else 0.0
    speech_seconds = speech_frame_count * (frame_ms / 1000)
    silence_seconds = silence_frame_count * (frame_ms / 1000)
    mean_speech_energy = sum(speech_values) / max(1, len(speech_values))
    energy_variation = 0.0
    if len(speech_values) > 1 and mean_speech_energy:
        variance = sum((value - mean_speech_energy) ** 2 for value in speech_values) / len(speech_values)
        energy_variation = math.sqrt(variance) / mean_speech_energy

    return {
        **metadata,
        "duration_seconds": round(duration_seconds, 3),
        "frame_ms": frame_ms,
        "silence_threshold": silence_threshold,
        "min_pause_ms": min_pause_ms,
        "speech_seconds": round(speech_seconds, 3),
        "silence_seconds": round(silence_seconds, 3),
        "pause_ratio": round(silence_seconds / duration_seconds, 3) if duration_seconds else 0.0,
        "pause_count": len(pause_regions),
        "longest_pause_ms": max(pause_regions) if pause_regions else 0,
        "average_pause_ms": round(sum(pause_regions) / len(pause_regions), 1) if pause_regions else 0.0,
        "speech_burst_count": count_regions(speech_flags, True),
        "mean_rms": round(sum(frame_values) / max(1, len(frame_values)), 5),
        "mean_speech_rms": round(mean_speech_energy, 5),
        "energy_variation": round(energy_variation, 3),
    }


def discover_audio_files(input_dir: Path) -> list[Path]:
    extensions = SUPPORTED_AUDIO_EXTENSIONS | KNOWN_UNSUPPORTED_AUDIO_EXTENSIONS
    return sorted(path for path in input_dir.rglob("*") if path.is_file() and path.suffix.lower() in extensions)
