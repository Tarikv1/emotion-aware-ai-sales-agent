#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "runtime" / "audio_backends" / "liquid_audio_model_probe_config.json"
RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "LIQUID-AUDIO-MODEL-DOWNLOAD-001" / "result.json"
REPORT_PATH = ROOT / "research" / "experiments" / "generated" / "LIQUID-AUDIO-MODEL-DOWNLOAD-001" / "report.md"
ALLOWED_STATUSES = {"not_run", "download_succeeded", "download_failed", "blocked"}
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


def false_side_effect(payload: dict[str, Any], key: str, failures: list[str], prefix: str) -> None:
    if payload.get(key) is not False:
        failures.append(f"{prefix}.{key} must be false")


def main() -> int:
    failures: list[str] = []
    config = load_json(CONFIG_PATH)
    result = load_json(RESULT_PATH)
    if not REPORT_PATH.is_file():
        failures.append(f"missing report: {rel(REPORT_PATH)}")

    if config.get("backend_id") != "liquid_audio_lfm25":
        failures.append("config backend_id must be liquid_audio_lfm25")
    for key in (
        "default_download_allowed",
        "default_load_allowed",
        "default_inference_allowed",
        "live_wiring_allowed",
        "sales_brain_replacement_allowed",
        "model_weights_commit_allowed",
        "generated_audio_commit_allowed",
    ):
        if config.get(key) is not False:
            failures.append(f"config.{key} must be false")
    if result.get("experiment_id") != "LIQUID-AUDIO-MODEL-DOWNLOAD-001":
        failures.append("download result has wrong experiment_id")
    if result.get("status") not in ALLOWED_STATUSES:
        failures.append(f"invalid download status: {result.get('status')!r}")
    if result.get("status") == "not_run" and not str(result.get("blocker") or "").strip():
        failures.append("not_run download must record blocker/gates")
    if result.get("status") == "download_failed" and not str(result.get("exact_blocker") or "").strip():
        failures.append("failed download must record exact_blocker")
    if result.get("model_download_attempted") is True:
        path_status = result.get("path_status") if isinstance(result.get("path_status"), dict) else {}
        if not str(path_status.get("local_model_path") or "").startswith("local_artifacts/"):
            failures.append("download model path must be under local_artifacts")
    if result.get("model_download_succeeded") is True:
        inventory = result.get("model_inventory") if isinstance(result.get("model_inventory"), dict) else {}
        if int(inventory.get("model_file_count") or 0) <= 0:
            failures.append("successful download must record model files")
        if int(inventory.get("total_approx_bytes") or 0) <= 0:
            failures.append("successful download must record approximate bytes")
    if result.get("live_wiring_allowed") is not False:
        failures.append("download live_wiring_allowed must be false")
    if result.get("sales_brain_replacement_allowed") is not False:
        failures.append("download sales_brain_replacement_allowed must be false")

    side_effects = result.get("side_effects") if isinstance(result.get("side_effects"), dict) else {}
    for key in (
        "audio_files_committed",
        "audio_files_generated",
        "elevenlabs_calls_made",
        "inference_run",
        "live_runtime_wiring_changed",
        "live_tts_calls_made",
        "local_model_generation_made",
        "model_weights_committed",
        "ollama_generation_made",
        "openai_api_calls_made",
        "provider_calls_made",
        "raw_private_audio_used",
        "raw_private_transcripts_included",
        "response_text_changed",
        "runtime_behavior_changed",
        "sales_brain_replacement_allowed",
        "training_performed",
        "live_wiring_allowed",
    ):
        false_side_effect(side_effects, key, failures, "download.side_effects")

    tracked = git_lines(["ls-files"])
    tracked_weights = [path for path in tracked if path.startswith("local_artifacts/") or path.lower().endswith(MODEL_SUFFIXES)]
    tracked_audio = [path for path in tracked if path.lower().endswith(AUDIO_SUFFIXES)]
    if tracked_weights:
        failures.append(f"tracked model/checkpoint/local_artifacts files are forbidden: {tracked_weights[:20]}")
    if tracked_audio:
        failures.append(f"tracked audio files are forbidden: {tracked_audio[:20]}")

    validation = {
        "status": "pass" if not failures else "fail",
        "download_status": result.get("status"),
        "download_attempted": result.get("model_download_attempted"),
        "download_succeeded": result.get("model_download_succeeded"),
        "failures": failures,
        "provider_calls_made": False,
        "runtime_behavior_changed": False,
        "response_text_changed": False,
    }
    print(json.dumps(validation, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
