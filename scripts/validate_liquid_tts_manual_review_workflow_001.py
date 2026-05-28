#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import subprocess
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MANUAL_DIR = ROOT / "research" / "experiments" / "generated" / "LIQUID-AUDIO-LISTENING-REVIEW-MANUAL-001"
TEMPLATE_JSON_PATH = MANUAL_DIR / "manual_review_template.json"
TEMPLATE_MD_PATH = MANUAL_DIR / "manual_review_template.md"
FILLED_JSON_PATH = MANUAL_DIR / "manual_review_filled.json"
PLAYBACK_RESULT_PATH = MANUAL_DIR / "playback_helper_result.json"
RESULT_PATH = MANUAL_DIR / "result.json"
MODEL_SUFFIXES = (".safetensors", ".bin", ".gguf", ".pt", ".pth", ".ckpt", ".onnx")
AUDIO_SUFFIXES = (".mp3", ".wav", ".flac", ".m4a", ".ogg")
RATING_FIELDS = [
    "intelligibility_1_to_5",
    "naturalness_1_to_5",
    "voice_quality_1_to_5",
    "sales_tone_1_to_5",
    "pacing_1_to_5",
    "artifact_severity_1_to_5",
    "robotic_sound_1_to_5",
    "thesis_demo_suitability_1_to_5",
    "product_fallback_suitability_1_to_5",
]


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise AssertionError(f"missing file: {rel(path)}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise AssertionError(f"{rel(path)} must be a JSON object")
    return payload


def git_lines(args: list[str]) -> list[str]:
    completed = subprocess.run(
        ["git", "--no-optional-locks", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    if completed.returncode != 0:
        return []
    return [line.strip().replace("\\", "/") for line in completed.stdout.splitlines() if line.strip()]


def require_false(payload: dict[str, Any], key: str, failures: list[str], prefix: str) -> None:
    if payload.get(key) is not False:
        failures.append(f"{prefix}.{key} must be false")


def no_audio_bytes(value: Any) -> bool:
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key).lower() in {"audio_bytes", "audio_base64", "data_uri", "wav_bytes"}:
                return False
            if not no_audio_bytes(child):
                return False
    if isinstance(value, list):
        return all(no_audio_bytes(item) for item in value)
    if isinstance(value, str) and (value.startswith("data:audio/") or value.startswith("RIFF")):
        return False
    return True


def validate_side_effects(payload: dict[str, Any], failures: list[str], prefix: str) -> None:
    side_effects = payload.get("side_effects") if isinstance(payload.get("side_effects"), dict) else {}
    for key in (
        "provider_calls_made",
        "openai_api_calls_made",
        "elevenlabs_calls_made",
        "live_tts_calls_made",
        "liquid_inference_run",
        "new_audio_generated",
        "audio_files_copied",
        "model_download_attempted",
        "model_weights_committed",
        "audio_files_committed",
        "runtime_behavior_changed",
        "response_text_changed",
        "raw_private_audio_used",
        "raw_private_transcripts_included",
    ):
        require_false(side_effects, key, failures, f"{prefix}.side_effects")


def main() -> int:
    failures: list[str] = []
    template = load_json(TEMPLATE_JSON_PATH)
    playback = load_json(PLAYBACK_RESULT_PATH)
    result = load_json(RESULT_PATH)
    if not TEMPLATE_MD_PATH.is_file():
        failures.append(f"missing template markdown: {rel(TEMPLATE_MD_PATH)}")
    if not no_audio_bytes(template) or not no_audio_bytes(playback) or not no_audio_bytes(result):
        failures.append("manual review workflow evidence must not include audio bytes")

    entries = template.get("entries") if isinstance(template.get("entries"), list) else []
    if len(entries) != 5:
        failures.append(f"manual template must include 5 review entries, got {len(entries)}")
    for entry in entries:
        if not isinstance(entry, dict):
            failures.append("template entries must be objects")
            continue
        path = str(entry.get("local_audio_path") or "").replace("\\", "/")
        if not path.startswith("local_artifacts/audio_outputs/liquid/"):
            failures.append(f"local_audio_path must stay under local_artifacts/audio_outputs/liquid: {path}")
        if not (ROOT / path).is_file():
            failures.append(f"local audio path must exist: {path}")
        for key in ("case_id", "input_text", "duration_seconds", "sample_rate", "waveform_hash", "latency_seconds", "real_time_factor"):
            if key not in entry:
                failures.append(f"template entry missing {key}")
        for field in RATING_FIELDS:
            if field not in entry:
                failures.append(f"template entry missing rating field {field}")
        if "compared_to_elevenlabs" not in entry or "notes" not in entry:
            failures.append("template entry must include compared_to_elevenlabs and notes")

    if playback.get("review_entries_count") != 5:
        failures.append("playback helper must report 5 review entries")
    if playback.get("open_requested") is not False:
        failures.append("required playback helper run must not open files or folders")
    printed = playback.get("printed_paths") if isinstance(playback.get("printed_paths"), list) else []
    if len(printed) != 5:
        failures.append("playback helper must print 5 paths")
    for path in printed:
        normalized = str(path).replace("\\", "/")
        if not normalized.startswith("local_artifacts/audio_outputs/liquid/"):
            failures.append(f"printed path must stay under local_artifacts/audio_outputs/liquid: {normalized}")

    filled_missing = not FILLED_JSON_PATH.is_file()
    if filled_missing and result.get("status") != "pending_manual_review":
        failures.append("missing filled review must produce pending_manual_review status, not failure")
    if result.get("filled_review_present") is not (not filled_missing):
        failures.append("filled_review_present must reflect manual_review_filled.json existence")
    if result.get("quality_inferred_from_latency") is not False:
        failures.append("manual workflow must not infer quality from latency")
    if result.get("live_readiness_claimed") is not False:
        failures.append("manual workflow must never claim live readiness")

    for payload_name, payload in (("template", template), ("playback", playback), ("result", result)):
        for key in (
            "provider_calls_made",
            "live_wiring_allowed",
            "sales_brain_replacement_allowed",
            "runtime_behavior_changed",
            "response_text_changed",
        ):
            if key in payload:
                require_false(payload, key, failures, payload_name)
        validate_side_effects(payload, failures, payload_name)

    tracked = git_lines(["ls-files"])
    tracked_weights = [path for path in tracked if path.startswith("local_artifacts/") or path.lower().endswith(MODEL_SUFFIXES)]
    tracked_audio = [path for path in tracked if path.lower().endswith(AUDIO_SUFFIXES)]
    evidence_audio = [
        str(path.relative_to(ROOT)).replace("\\", "/")
        for path in MANUAL_DIR.rglob("*")
        if path.is_file() and path.suffix.lower() in AUDIO_SUFFIXES
    ]
    if tracked_weights:
        failures.append(f"tracked model/checkpoint/local_artifacts files are forbidden: {tracked_weights[:20]}")
    if tracked_audio:
        failures.append(f"tracked audio files are forbidden: {tracked_audio[:20]}")
    if evidence_audio:
        failures.append(f"audio files copied into manual evidence are forbidden: {evidence_audio[:20]}")

    validation = {
        "status": "pass" if not failures else "fail",
        "review_entries_count": len(entries),
        "manual_review_status": result.get("listening_review_status"),
        "filled_review_present": not filled_missing,
        "failures": failures,
        "provider_calls_made": False,
        "runtime_behavior_changed": False,
        "response_text_changed": False,
    }
    print(json.dumps(validation, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
