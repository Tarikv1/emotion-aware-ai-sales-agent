from __future__ import annotations

import io
import math
import wave
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import numpy as np
from scipy.signal.windows import hann

FEATURE_NAMES = (
    "duration_seconds",
    "silence_ratio",
    "voiced_fraction",
    "f0_median_hz",
    "f0_iqr_hz",
    "f0_range_hz",
    "rms_dbfs_mean",
    "rms_dbfs_std",
    "rms_dbfs_p90_minus_p10",
    "zero_crossing_rate_mean",
    "zero_crossing_rate_std",
    "spectral_centroid_hz_mean",
    "spectral_centroid_hz_std",
    "spectral_bandwidth_hz_mean",
    "spectral_bandwidth_hz_std",
    "spectral_rolloff_85_hz_mean",
    "spectral_rolloff_85_hz_std",
)
ZERO_FRAME_RMS_FLOOR = 1.0 / (32768.0 * math.sqrt(400.0))


class FeatureExtractionError(ValueError):
    pass


def _read_pcm16_mono_16khz_bytes(wav_bytes: bytes) -> np.ndarray:
    if type(wav_bytes) is not bytes:
        raise TypeError("WAV content must be bytes")
    try:
        with wave.open(io.BytesIO(wav_bytes), "rb") as source:
            if source.getnchannels() != 1:
                raise FeatureExtractionError("WAV must be mono")
            if source.getsampwidth() != 2:
                raise FeatureExtractionError("WAV must use 16-bit PCM")
            if source.getframerate() != 16000:
                raise FeatureExtractionError("WAV sample rate must be 16000 Hz")
            if source.getcomptype() != "NONE":
                raise FeatureExtractionError("WAV must be uncompressed PCM")
            frame_count = source.getnframes()
            if frame_count <= 0:
                raise FeatureExtractionError("WAV contains no samples")
            payload = source.readframes(frame_count)
    except FeatureExtractionError:
        raise
    except (EOFError, OSError, wave.Error) as error:
        raise FeatureExtractionError("WAV is malformed or unsupported") from error

    if len(payload) != frame_count * 2:
        raise FeatureExtractionError("WAV sample stream is truncated")
    pcm = np.frombuffer(payload, dtype="<i2")
    if pcm.size != frame_count:
        raise FeatureExtractionError("WAV sample count does not match")
    samples = pcm.astype(np.float64) / 32768.0
    if not np.all(np.isfinite(samples)):
        raise FeatureExtractionError("WAV contains non-finite samples")
    return samples


def _read_pcm16_mono_16khz(path: Path) -> np.ndarray:
    try:
        wav_bytes = Path(path).read_bytes()
    except OSError as error:
        raise FeatureExtractionError("WAV is malformed or unsupported") from error
    return _read_pcm16_mono_16khz_bytes(wav_bytes)


def _frames(
    samples: np.ndarray,
    frame_size: int,
    hop_size: int,
) -> np.ndarray:
    values = np.asarray(samples, dtype=np.float64)
    if values.ndim != 1:
        raise FeatureExtractionError("samples must be one-dimensional")
    if not np.all(np.isfinite(values)):
        raise FeatureExtractionError("samples contain a non-finite value")
    if frame_size <= 0 or hop_size <= 0:
        raise FeatureExtractionError("frame and hop sizes must be positive")
    if values.size < frame_size:
        return np.empty((0, frame_size), dtype=np.float64)
    frame_count = 1 + (values.size - frame_size) // hop_size
    starts = np.arange(frame_count, dtype=np.int64) * hop_size
    offsets = np.arange(frame_size, dtype=np.int64)
    return values[starts[:, np.newaxis] + offsets]


def _linear_percentile(values: np.ndarray, percentile: float) -> float:
    return float(np.percentile(values, percentile, method="linear"))


def _normalized_autocorrelation_f0(
    frame: np.ndarray,
    *,
    sample_rate: int,
    minimum_hz: float,
    maximum_hz: float,
) -> tuple[float, float]:
    centered = np.asarray(frame, dtype=np.float64) - float(np.mean(frame))
    residual_energy = float(np.dot(centered, centered))
    if residual_energy == 0.0:
        return 0.0, 0.0
    minimum_lag = math.ceil(sample_rate / maximum_hz)
    maximum_lag = math.floor(sample_rate / minimum_hz)
    lags = np.arange(minimum_lag, maximum_lag + 1, dtype=np.int64)
    correlations = np.empty(lags.size, dtype=np.float64)
    for index, lag in enumerate(lags):
        left = centered[:-lag]
        right = centered[lag:]
        denominator = math.sqrt(
            float(np.dot(left, left)) * float(np.dot(right, right))
        )
        correlations[index] = (
            float(np.dot(left, right)) / denominator
            if denominator > 0.0
            else 0.0
        )
    peak = float(np.max(correlations))
    peak_index = int(np.flatnonzero(correlations == peak)[0])
    lag = int(lags[peak_index])
    return float(sample_rate / lag), peak


def _summarize(
    frames: np.ndarray,
    sample_count: int,
    sample_rate: int,
) -> dict[str, float]:
    values = np.asarray(frames, dtype=np.float64)
    if (
        values.ndim != 2
        or values.shape[0] == 0
        or values.shape[1] != 400
    ):
        raise FeatureExtractionError("analysis frames do not match")
    if not np.all(np.isfinite(values)):
        raise FeatureExtractionError("analysis frames contain a non-finite value")
    if sample_count <= 0 or sample_rate != 16000:
        raise FeatureExtractionError("sample metadata does not match")

    frame_rms = np.sqrt(np.mean(np.square(values), axis=1))
    frame_dbfs = 20.0 * np.log10(
        np.maximum(frame_rms, ZERO_FRAME_RMS_FLOOR)
    )
    peak_frame_dbfs = float(np.max(frame_dbfs))
    nonsilent_threshold = max(-50.0, peak_frame_dbfs - 40.0)
    nonsilent_mask = frame_dbfs >= nonsilent_threshold
    nonsilent = values[nonsilent_mask]
    if nonsilent.shape[0] == 0:
        raise FeatureExtractionError("WAV has no nonsilent analysis frame")

    periodic_hann = hann(400, sym=False)
    windowed = nonsilent * periodic_hann[np.newaxis, :]

    zero_crossing_rates = np.mean(
        np.signbit(nonsilent[:, :-1]) != np.signbit(nonsilent[:, 1:]),
        axis=1,
    )

    power_spectra = np.square(np.abs(np.fft.rfft(windowed, axis=1)))
    frequencies = np.fft.rfftfreq(400, d=1.0 / sample_rate)
    power_totals = np.sum(power_spectra, axis=1)
    if np.any(power_totals <= 0.0):
        raise FeatureExtractionError("nonsilent frame has no spectral power")
    spectral_centroids = (
        np.sum(power_spectra * frequencies[np.newaxis, :], axis=1)
        / power_totals
    )
    spectral_bandwidths = np.sqrt(
        np.sum(
            power_spectra
            * np.square(
                frequencies[np.newaxis, :]
                - spectral_centroids[:, np.newaxis]
            ),
            axis=1,
        )
        / power_totals
    )
    cumulative_power = np.cumsum(power_spectra, axis=1)
    rolloff_indexes = np.asarray(
        [
            np.searchsorted(row, 0.85 * total, side="left")
            for row, total in zip(cumulative_power, power_totals)
        ],
        dtype=np.int64,
    )
    spectral_rolloffs = frequencies[rolloff_indexes]

    f0_values: list[float] = []
    for frame in nonsilent:
        f0_hz, peak = _normalized_autocorrelation_f0(
            frame,
            sample_rate=sample_rate,
            minimum_hz=75.0,
            maximum_hz=400.0,
        )
        if peak >= 0.30:
            f0_values.append(f0_hz)
    if len(f0_values) < 3:
        raise FeatureExtractionError("WAV has fewer than three voiced frames")
    f0 = np.asarray(f0_values, dtype=np.float64)

    f0_q25 = _linear_percentile(f0, 25.0)
    f0_q75 = _linear_percentile(f0, 75.0)
    rms_p10 = _linear_percentile(frame_dbfs, 10.0)
    rms_p90 = _linear_percentile(frame_dbfs, 90.0)
    result = {
        "duration_seconds": float(sample_count / sample_rate),
        "silence_ratio": float(1.0 - np.mean(nonsilent_mask)),
        "voiced_fraction": float(len(f0_values) / values.shape[0]),
        "f0_median_hz": _linear_percentile(f0, 50.0),
        "f0_iqr_hz": float(f0_q75 - f0_q25),
        "f0_range_hz": float(np.max(f0) - np.min(f0)),
        "rms_dbfs_mean": float(np.mean(frame_dbfs)),
        "rms_dbfs_std": float(np.std(frame_dbfs, ddof=0)),
        "rms_dbfs_p90_minus_p10": float(rms_p90 - rms_p10),
        "zero_crossing_rate_mean": float(np.mean(zero_crossing_rates)),
        "zero_crossing_rate_std": float(
            np.std(zero_crossing_rates, ddof=0)
        ),
        "spectral_centroid_hz_mean": float(np.mean(spectral_centroids)),
        "spectral_centroid_hz_std": float(
            np.std(spectral_centroids, ddof=0)
        ),
        "spectral_bandwidth_hz_mean": float(np.mean(spectral_bandwidths)),
        "spectral_bandwidth_hz_std": float(
            np.std(spectral_bandwidths, ddof=0)
        ),
        "spectral_rolloff_85_hz_mean": float(np.mean(spectral_rolloffs)),
        "spectral_rolloff_85_hz_std": float(
            np.std(spectral_rolloffs, ddof=0)
        ),
    }
    if tuple(result) != FEATURE_NAMES:
        raise FeatureExtractionError("feature output order does not match")
    if any(not math.isfinite(value) for value in result.values()):
        raise FeatureExtractionError("feature output contains a non-finite value")
    return result


def extract_acoustic_features(path: Path) -> dict[str, float]:
    try:
        wav_bytes = Path(path).read_bytes()
    except OSError as error:
        raise FeatureExtractionError("WAV is malformed or unsupported") from error
    return extract_acoustic_features_bytes(wav_bytes)


def extract_acoustic_features_bytes(wav_bytes: bytes) -> dict[str, float]:
    samples = _read_pcm16_mono_16khz_bytes(wav_bytes)
    frames = _frames(samples, frame_size=400, hop_size=160)
    if frames.shape[0] == 0:
        raise FeatureExtractionError("WAV has no complete analysis frame")
    return _summarize(frames, sample_count=samples.size, sample_rate=16000)


def feature_vector(row: Mapping[str, Any]) -> tuple[float, ...]:
    if set(row) != set(FEATURE_NAMES):
        raise FeatureExtractionError("feature row fields do not match")
    values = tuple(float(row[name]) for name in FEATURE_NAMES)
    if any(not math.isfinite(value) for value in values):
        raise FeatureExtractionError("feature row contains a non-finite value")
    return values
