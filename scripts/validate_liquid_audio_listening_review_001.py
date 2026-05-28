#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "LIQUID-AUDIO-LISTENING-REVIEW-001" / "result.json"
REPORT_PATH = ROOT / "research" / "experiments" / "generated" / "LIQUID-AUDIO-LISTENING-REVIEW-001" / "report.md"
MODEL_SUFFIXES = (".safetensors", ".bin", ".gguf", ".pt", ".pth", ".ckpt", ".onnx")
AUDIO_SUFFIXES = (".mp3", ".wav", ".flac", ".m4a", ".ogg")


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
    completed = subprocess.run(["git", "--no-optional-locks", *args], cwd=ROOT, capture_output=True, text=True, timeout=30, check=False)
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


def main() -> int:
    failures: list[str] = []
    result = load_json(RESULT_PATH)
    report = REPORT_PATH.read_text(encoding="utf-8") if REPORT_PATH.is_file() else ""
    if not report:
        failures.append(f"missing report: {rel(REPORT_PATH)}")
    if result.get("experiment_id") != "LIQUID-AUDIO-LISTENING-REVIEW-001":
        failures.append("listening review has wrong experiment_id")
    if result.get("status") != "pass":
        failures.append("listening review status must be pass")
    if result.get("audio_files_copied_into_public_evidence") is not False:
        failures.append("audio files must not be copied into public evidence")
    if not no_audio_bytes(result) or "data:audio/" in report or "RIFF" in report:
        failures.append("listening review must not include audio bytes or data URIs")
    entries = result.get("review_entries") if isinstance(result.get("review_entries"), list) else []
    if not entries:
        failures.append("listening review must include review entries")
    for entry in entries:
        if not isinstance(entry, dict):
            failures.append("review entries must be objects")
            continue
        path = str(entry.get("local_audio_file_path") or "").replace("\\", "/")
        if not path.startswith("local_artifacts/audio_outputs/liquid/"):
            failures.append(f"audio path must stay under local_artifacts/audio_outputs/liquid: {path}")
        if entry.get("file_exists") is not True:
            failures.append(f"audio path must exist locally for review: {path}")
        if entry.get("audio_committed") is not False:
            failures.append(f"audio_committed must be false for {entry.get('case_id')}")
        for key in ("duration_seconds", "sample_rate", "latency_seconds", "real_time_factor", "file_size_bytes"):
            if not isinstance(entry.get(key), (int, float)):
                failures.append(f"{entry.get('case_id')}.{key} must be numeric")
        if not str(entry.get("waveform_hash") or "").strip():
            failures.append(f"{entry.get('case_id')}.waveform_hash must be recorded")

    checklist = result.get("manual_listening_checklist") if isinstance(result.get("manual_listening_checklist"), list) else []
    for item in ("intelligibility", "naturalness", "voice quality", "artifacts/glitches", "emotional/prosody suitability for sales"):
        if item not in checklist:
            failures.append(f"manual checklist missing {item}")
    table = str(result.get("manual_review_table_markdown") or "")
    for heading in ("case_id", "intelligibility", "naturalness", "sales tone", "artifact severity", "notes"):
        if heading not in table:
            failures.append(f"manual review table missing {heading}")

    for key in (
        "provider_calls_made",
        "openai_api_calls_made",
        "elevenlabs_calls_made",
        "live_tts_calls_made",
        "live_wiring_allowed",
        "sales_brain_replacement_allowed",
        "runtime_behavior_changed",
        "response_text_changed",
        "model_weights_committed",
        "audio_files_committed",
    ):
        require_false(result, key, failures, "listening")
    side_effects = result.get("side_effects") if isinstance(result.get("side_effects"), dict) else {}
    for key in (
        "provider_calls_made",
        "openai_api_calls_made",
        "elevenlabs_calls_made",
        "live_tts_calls_made",
        "new_liquid_inference_run",
        "new_audio_generated",
        "model_download_attempted",
        "model_weights_committed",
        "audio_files_committed",
        "runtime_behavior_changed",
        "response_text_changed",
        "raw_private_audio_used",
        "raw_private_transcripts_included",
    ):
        require_false(side_effects, key, failures, "listening.side_effects")

    tracked = git_lines(["ls-files"])
    tracked_weights = [path for path in tracked if path.startswith("local_artifacts/") or path.lower().endswith(MODEL_SUFFIXES)]
    tracked_audio = [path for path in tracked if path.lower().endswith(AUDIO_SUFFIXES)]
    if tracked_weights:
        failures.append(f"tracked model/checkpoint/local_artifacts files are forbidden: {tracked_weights[:20]}")
    if tracked_audio:
        failures.append(f"tracked audio files are forbidden: {tracked_audio[:20]}")

    validation = {
        "status": "pass" if not failures else "fail",
        "review_entry_count": len(entries),
        "failures": failures,
        "provider_calls_made": False,
        "runtime_behavior_changed": False,
        "response_text_changed": False,
    }
    print(json.dumps(validation, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
