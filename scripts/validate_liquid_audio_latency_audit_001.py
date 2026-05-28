#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "LIQUID-AUDIO-LATENCY-AUDIT-001" / "result.json"
REPORT_PATH = ROOT / "research" / "experiments" / "generated" / "LIQUID-AUDIO-LATENCY-AUDIT-001" / "report.md"
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


def main() -> int:
    failures: list[str] = []
    result = load_json(RESULT_PATH)
    report = REPORT_PATH.read_text(encoding="utf-8") if REPORT_PATH.is_file() else ""
    if not report:
        failures.append(f"missing report: {rel(REPORT_PATH)}")
    if result.get("experiment_id") != "LIQUID-AUDIO-LATENCY-AUDIT-001":
        failures.append("latency audit has wrong experiment_id")
    if result.get("status") != "pass":
        failures.append("latency audit status must be pass")
    if result.get("current_smoke_live_usable") is not False:
        failures.append("latency audit must not claim current smoke is live usable")
    if result.get("streaming_requires_verifier_gating_before_playback") is not True:
        failures.append("latency audit must require verifier gating for streaming")
    for key in ("generation_latency_seconds", "first_audio_latency_seconds", "real_time_factor", "first_audio_vs_full_generation"):
        value = result.get(key)
        if not isinstance(value, dict) or not value:
            failures.append(f"latency audit must record {key}")
    first_vs_full = result.get("first_audio_vs_full_generation") if isinstance(result.get("first_audio_vs_full_generation"), dict) else {}
    for key in ("p50_first_audio_seconds", "p50_full_generation_seconds", "p90_first_audio_seconds", "p90_full_generation_seconds"):
        if not isinstance(first_vs_full.get(key), (int, float)):
            failures.append(f"first_audio_vs_full_generation.{key} must be numeric")
    targets = result.get("latency_targets") if isinstance(result.get("latency_targets"), dict) else {}
    for key in ("live_voice", "offline_demo", "batch_generation", "architecture_inspiration"):
        if key not in targets:
            failures.append(f"latency target missing {key}")
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
        require_false(result, key, failures, "latency")
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
        require_false(side_effects, key, failures, "latency.side_effects")

    tracked = git_lines(["ls-files"])
    tracked_weights = [path for path in tracked if path.startswith("local_artifacts/") or path.lower().endswith(MODEL_SUFFIXES)]
    tracked_audio = [path for path in tracked if path.lower().endswith(AUDIO_SUFFIXES)]
    if tracked_weights:
        failures.append(f"tracked model/checkpoint/local_artifacts files are forbidden: {tracked_weights[:20]}")
    if tracked_audio:
        failures.append(f"tracked audio files are forbidden: {tracked_audio[:20]}")

    validation = {
        "status": "pass" if not failures else "fail",
        "current_smoke_live_usable": result.get("current_smoke_live_usable"),
        "failures": failures,
        "provider_calls_made": False,
        "runtime_behavior_changed": False,
        "response_text_changed": False,
    }
    print(json.dumps(validation, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
