#!/usr/bin/env python3
from __future__ import annotations

import datetime as dt
import json
import re
import wave
from pathlib import Path
from typing import Any

from raw_audio_speech_features import analyze_wav_file


ROOT = Path(__file__).resolve().parents[1]
PRIVATE_DATA_ROOT = ROOT / "data" / "private"
CASE_PATH = ROOT / "research" / "experiments" / "cases" / "voice-030c-private-learning-queue.json"
SUPPORTED_ANALYSIS_EXTENSIONS = {".wav"}

DEFAULT_SPEAKER_CONTEXT = {
    "native_language": "tr",
    "spoken_languages": ["en", "de", "tr"],
    "english_proficiency": "high",
    "pronunciation_learning": "use_selectively_for_natural_delivery_not_identity_clone",
    "learn_from": [
        "timing",
        "filler_placement",
        "repair_style",
        "thinking_pauses",
        "sentence_rhythm",
        "clear_english_delivery_patterns",
    ],
    "guardrails": [
        "do_not_clone_or_overfit_to_one_speaker_identity",
        "do_not_force_every_campaign_to_match_tarik_exactly",
    ],
}

DIAGNOSTIC_ONLY_FEATURES = [
    "pause_ratio",
    "average_pause_ms",
    "longest_pause_ms",
    "silence_seconds",
]

RUNTIME_CANDIDATE_FEATURES = [
    "speech_burst_count",
    "energy_variation",
    "mean_speech_rms",
]


def learning_signal_policy() -> dict[str, Any]:
    return {
        "long_formulation_pauses": "expected_in_owner_samples_not_agent_target",
        "pause_duration_reasoning": (
            "Owner samples may include long pauses while formulating complex instructions; "
            "these pauses should not slow down the sales agent."
        ),
        "diagnostic_only_features": DIAGNOSTIC_ONLY_FEATURES,
        "runtime_candidate_features": RUNTIME_CANDIDATE_FEATURES,
        "runtime_use_requires_human_review": True,
    }


def runtime_learning_candidates(features: dict[str, Any]) -> dict[str, Any]:
    return {
        key: features[key]
        for key in RUNTIME_CANDIDATE_FEATURES
        if key in features
    }


def utc_now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def project_relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def is_under(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def safe_sample_id(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9._-]+", "-", value).strip(".-_").lower()
    return cleaned[:80] or "speech-sample"


def load_case() -> dict[str, Any]:
    if not CASE_PATH.exists():
        return {}
    return json.loads(CASE_PATH.read_text(encoding="utf-8"))


def speaker_context_from_case() -> dict[str, Any]:
    return load_case().get("speaker_context", DEFAULT_SPEAKER_CONTEXT)


def ensure_private_queue_paths(private_root: Path) -> tuple[Path, Path]:
    if not is_under(private_root, PRIVATE_DATA_ROOT):
        raise ValueError("VOICE-030C private root must stay under data/private.")
    queue_manifest = private_root / "derived" / "local-speech-learning-queue.jsonl"
    features_dir = private_root / "derived" / "audio-features"
    queue_manifest.parent.mkdir(parents=True, exist_ok=True)
    features_dir.mkdir(parents=True, exist_ok=True)
    return queue_manifest, features_dir


def privacy_boundary() -> dict[str, Any]:
    return {
        "outputs_stay_under_data_private": True,
        "provider_calls_made": False,
        "transcription_created": False,
        "voice_cloning_used": False,
        "runtime_profile_applied": False,
        "public_artifact_created": False,
        "human_review_required_before_runtime_use": True,
    }


def append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def resolve_stored_audio(record: dict[str, Any], private_root: Path) -> Path:
    relative_path = str(record.get("stored_relative_path", ""))
    audio_path = ROOT / relative_path
    if not is_under(audio_path, private_root):
        raise ValueError("VOICE-030C refuses to process audio outside the selected private root.")
    return audio_path


def build_feature_payload(
    *,
    record: dict[str, Any],
    features: dict[str, Any],
    private_root: Path,
) -> dict[str, Any]:
    return {
        "voice_milestone": "VOICE-030C",
        "sample_id": record["sample_id"],
        "language": record.get("language", "unknown"),
        "source_kind": record.get("source_kind", "unknown"),
        "source_file_extension": record.get("file_extension"),
        "source_content_sha256": record.get("content_sha256"),
        "features": features,
        "learning_signal_policy": learning_signal_policy(),
        "runtime_learning_candidates": runtime_learning_candidates(features),
        "speaker_context": speaker_context_from_case(),
        "privacy_boundary": {
            **privacy_boundary(),
            "stored_under_private_root": is_under(private_root, PRIVATE_DATA_ROOT),
        },
    }


def process_capture_record(
    record: dict[str, Any],
    *,
    private_root: Path,
) -> dict[str, Any]:
    queue_manifest, features_dir = ensure_private_queue_paths(private_root)
    extension = str(record.get("file_extension", "")).lower()
    sample_id = safe_sample_id(str(record.get("sample_id", "speech-sample")))
    feature_path: Path | None = None
    error: str | None = None

    if extension in SUPPORTED_ANALYSIS_EXTENSIONS:
        try:
            audio_path = resolve_stored_audio(record, private_root)
            features = analyze_wav_file(audio_path)
            feature_path = features_dir / f"{sample_id}.json"
            write_json(
                feature_path,
                build_feature_payload(record=record, features=features, private_root=private_root),
            )
            processing_status = "analyzed_needs_review"
        except (OSError, ValueError, wave.Error) as exc:
            processing_status = "analysis_failed_needs_review"
            error = str(exc)
    else:
        processing_status = "needs_local_conversion"

    queue_record = {
        "voice_milestone": "VOICE-030C",
        "queued_at_utc": utc_now(),
        "sample_id": sample_id,
        "language": record.get("language", "unknown"),
        "source_kind": record.get("source_kind", "unknown"),
        "source_file_extension": extension,
        "source_content_sha256": record.get("content_sha256"),
        "processing_status": processing_status,
        "derived_feature_relative_path": project_relative(feature_path) if feature_path else None,
        "speaker_context": speaker_context_from_case(),
        "privacy_boundary": {
            **privacy_boundary(),
            "stored_under_private_root": is_under(private_root, PRIVATE_DATA_ROOT),
        },
    }
    if error:
        queue_record["error"] = error

    append_jsonl(queue_manifest, queue_record)
    return {
        "voice_milestone": "VOICE-030C",
        "sample_id": queue_record["sample_id"],
        "processing_status": processing_status,
        "derived_feature_relative_path": queue_record["derived_feature_relative_path"],
        "speaker_context": queue_record["speaker_context"],
        "privacy_boundary": queue_record["privacy_boundary"],
    }
