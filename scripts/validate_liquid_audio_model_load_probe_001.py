#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "LIQUID-AUDIO-MODEL-LOAD-PROBE-001" / "result.json"
REPORT_PATH = ROOT / "research" / "experiments" / "generated" / "LIQUID-AUDIO-MODEL-LOAD-PROBE-001" / "report.md"
ALLOWED_STATUSES = {"not_run", "model_missing", "load_succeeded", "load_failed", "oom", "blocked"}
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
    result = load_json(RESULT_PATH)
    if not REPORT_PATH.is_file():
        failures.append(f"missing report: {rel(REPORT_PATH)}")

    if result.get("experiment_id") != "LIQUID-AUDIO-MODEL-LOAD-PROBE-001":
        failures.append("load result has wrong experiment_id")
    if result.get("status") not in ALLOWED_STATUSES:
        failures.append(f"invalid load status: {result.get('status')!r}")
    if result.get("status") in {"not_run", "model_missing", "load_failed", "oom", "blocked"} and not str(result.get("blocker") or result.get("exact_blocker") or "").strip():
        failures.append("non-success load result must record blocker")
    if result.get("status") in {"load_failed", "oom"} and not str(result.get("exact_blocker") or "").strip():
        failures.append("failed load must record exact_blocker")
    if result.get("load_succeeded") is True:
        if result.get("processor_load_succeeded") is not True:
            failures.append("successful load must include successful processor load")
        if result.get("full_model_load_succeeded") is not True:
            failures.append("successful load must include successful full model load")
        if not isinstance(result.get("full_model_load_time_seconds"), (int, float)):
            failures.append("successful load must record full model load time")
        gpu = result.get("gpu_memory") if isinstance(result.get("gpu_memory"), dict) else {}
        for key in ("cuda_available", "device_name", "max_memory_reserved_bytes", "mem_get_info_total_bytes"):
            if key not in gpu:
                failures.append(f"successful load must record gpu_memory.{key}")
    if result.get("inference_run") is not False:
        failures.append("load probe must not run inference")
    if result.get("audio_files_generated") is not False:
        failures.append("load probe must not generate audio")
    if result.get("live_wiring_allowed") is not False:
        failures.append("load live_wiring_allowed must be false")
    if result.get("sales_brain_replacement_allowed") is not False:
        failures.append("load sales_brain_replacement_allowed must be false")

    side_effects = result.get("side_effects") if isinstance(result.get("side_effects"), dict) else {}
    for key in (
        "audio_files_committed",
        "audio_files_generated",
        "elevenlabs_calls_made",
        "inference_run",
        "live_runtime_wiring_changed",
        "live_tts_calls_made",
        "local_model_generation_made",
        "model_download_attempted",
        "model_downloads_performed",
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
        false_side_effect(side_effects, key, failures, "load.side_effects")

    tracked = git_lines(["ls-files"])
    tracked_weights = [path for path in tracked if path.startswith("local_artifacts/") or path.lower().endswith(MODEL_SUFFIXES)]
    tracked_audio = [path for path in tracked if path.lower().endswith(AUDIO_SUFFIXES)]
    if tracked_weights:
        failures.append(f"tracked model/checkpoint/local_artifacts files are forbidden: {tracked_weights[:20]}")
    if tracked_audio:
        failures.append(f"tracked audio files are forbidden: {tracked_audio[:20]}")

    validation = {
        "status": "pass" if not failures else "fail",
        "load_status": result.get("status"),
        "load_attempted": result.get("load_attempted"),
        "load_succeeded": result.get("load_succeeded"),
        "failures": failures,
        "provider_calls_made": False,
        "runtime_behavior_changed": False,
        "response_text_changed": False,
    }
    print(json.dumps(validation, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
