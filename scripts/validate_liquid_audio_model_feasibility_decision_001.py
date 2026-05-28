#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "LIQUID-AUDIO-MODEL-FEASIBILITY-DECISION-001" / "result.json"
REPORT_PATH = ROOT / "research" / "experiments" / "generated" / "LIQUID-AUDIO-MODEL-FEASIBILITY-DECISION-001" / "report.md"
DOWNLOAD_RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "LIQUID-AUDIO-MODEL-DOWNLOAD-001" / "result.json"
LOAD_RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "LIQUID-AUDIO-MODEL-LOAD-PROBE-001" / "result.json"
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
    decision = load_json(RESULT_PATH)
    download = load_json(DOWNLOAD_RESULT_PATH)
    load = load_json(LOAD_RESULT_PATH)
    if not REPORT_PATH.is_file():
        failures.append(f"missing report: {rel(REPORT_PATH)}")

    if decision.get("experiment_id") != "LIQUID-AUDIO-MODEL-FEASIBILITY-DECISION-001":
        failures.append("decision result has wrong experiment_id")
    if decision.get("status") != "pass":
        failures.append("decision status must be pass")
    for key in ("download_attempted", "download_succeeded", "model_present", "load_attempted", "load_succeeded"):
        if not isinstance(decision.get(key), bool):
            failures.append(f"decision.{key} must be boolean")
    if decision.get("download_status") != download.get("status"):
        failures.append("decision download_status must mirror download evidence")
    if decision.get("load_status") != load.get("status"):
        failures.append("decision load_status must mirror load evidence")
    if not str(decision.get("recommendation_id") or "").strip():
        failures.append("decision recommendation_id must be present")
    if not str(decision.get("next_phase_recommendation") or "").strip():
        failures.append("decision next_phase_recommendation must be present")
    if decision.get("live_wiring_allowed") is not False:
        failures.append("decision live_wiring_allowed must be false")
    if decision.get("sales_brain_replacement_allowed") is not False:
        failures.append("decision sales_brain_replacement_allowed must be false")

    side_effects = decision.get("side_effects") if isinstance(decision.get("side_effects"), dict) else {}
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
        false_side_effect(side_effects, key, failures, "decision.side_effects")

    tracked = git_lines(["ls-files"])
    tracked_weights = [path for path in tracked if path.startswith("local_artifacts/") or path.lower().endswith(MODEL_SUFFIXES)]
    tracked_audio = [path for path in tracked if path.lower().endswith(AUDIO_SUFFIXES)]
    if tracked_weights:
        failures.append(f"tracked model/checkpoint/local_artifacts files are forbidden: {tracked_weights[:20]}")
    if tracked_audio:
        failures.append(f"tracked audio files are forbidden: {tracked_audio[:20]}")

    validation = {
        "status": "pass" if not failures else "fail",
        "recommendation_id": decision.get("recommendation_id"),
        "download_status": decision.get("download_status"),
        "load_status": decision.get("load_status"),
        "failures": failures,
        "provider_calls_made": False,
        "runtime_behavior_changed": False,
        "response_text_changed": False,
    }
    print(json.dumps(validation, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
