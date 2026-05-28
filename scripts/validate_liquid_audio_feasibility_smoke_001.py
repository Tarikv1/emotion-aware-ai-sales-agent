#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "runtime" / "audio_backends" / "liquid_audio_feasibility_config.json"
RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "LIQUID-AUDIO-FEASIBILITY-SMOKE-001" / "result.json"
REPORT_PATH = ROOT / "research" / "experiments" / "generated" / "LIQUID-AUDIO-FEASIBILITY-SMOKE-001" / "report.md"
ALLOWED_STATUSES = {"not_run", "model_missing", "blocked", "pass"}
FORBIDDEN_WEIGHT_SUFFIXES = (".safetensors", ".bin", ".gguf", ".pt", ".pth", ".ckpt", ".onnx")
FORBIDDEN_AUDIO_SUFFIXES = (".mp3", ".wav", ".flac", ".m4a", ".ogg")


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

    if result.get("experiment_id") != "LIQUID-AUDIO-FEASIBILITY-SMOKE-001":
        failures.append("smoke result has wrong experiment_id")
    status = result.get("status")
    if status not in ALLOWED_STATUSES:
        failures.append(f"invalid smoke status: {status!r}")
    if status in {"not_run", "model_missing", "blocked"} and not str(result.get("blocker") or "").strip():
        failures.append("non-running smoke result must record a blocker")
    if result.get("live_wiring_allowed") is not False:
        failures.append("smoke live_wiring_allowed must be false")
    if result.get("sales_brain_replacement_allowed") is not False:
        failures.append("smoke sales_brain_replacement_allowed must be false")
    if result.get("model_download_attempted") is not False:
        failures.append("smoke must not attempt model download by default")
    if result.get("smoke_run") is not False and status != "pass":
        failures.append("smoke_run can only be true with pass status")

    safe_inputs = config.get("safe_test_inputs") if isinstance(config.get("safe_test_inputs"), dict) else {}
    expected_asr = safe_inputs.get("asr_phrases") or []
    expected_tts = safe_inputs.get("tts_utterances") or []
    asr = result.get("asr_smoke") if isinstance(result.get("asr_smoke"), dict) else {}
    tts = result.get("tts_smoke") if isinstance(result.get("tts_smoke"), dict) else {}
    if asr.get("synthetic_phrases") != expected_asr:
        failures.append("ASR synthetic phrase set must mirror config")
    if tts.get("synthetic_utterances") != expected_tts:
        failures.append("TTS synthetic utterance set must mirror config")
    if asr.get("raw_private_audio_used") is not False:
        failures.append("ASR smoke must not use raw private audio")
    if tts.get("audio_files_generated") is not False:
        failures.append("TTS smoke must not generate audio in default Phase 4I1 run")

    side_effects = result.get("side_effects") if isinstance(result.get("side_effects"), dict) else {}
    for key in (
        "model_download_attempted",
        "model_downloads_performed",
        "model_weights_committed",
        "audio_files_generated",
        "audio_files_committed",
        "provider_calls_made",
        "openai_api_calls_made",
        "elevenlabs_calls_made",
        "live_tts_calls_made",
        "local_model_generation_made",
        "ollama_generation_made",
        "training_performed",
        "live_runtime_wiring_changed",
        "runtime_behavior_changed",
        "response_text_changed",
        "raw_private_audio_used",
        "raw_private_transcripts_included",
        "sales_brain_replacement_allowed",
        "live_wiring_allowed",
    ):
        false_side_effect(side_effects, key, failures, "smoke.side_effects")

    tracked = git_lines(["ls-files"])
    weights = [path for path in tracked if path.lower().endswith(FORBIDDEN_WEIGHT_SUFFIXES) or path.startswith("local_artifacts/")]
    audio = [path for path in tracked if path.lower().endswith(FORBIDDEN_AUDIO_SUFFIXES)]
    if weights:
        failures.append(f"tracked model/checkpoint files are forbidden: {weights[:20]}")
    if audio:
        failures.append(f"tracked audio files are forbidden: {audio[:20]}")

    validation = {
        "status": "pass" if not failures else "fail",
        "smoke_status": status,
        "blocker": result.get("blocker"),
        "model_present": result.get("model_present"),
        "failures": failures,
        "model_download_attempted": False,
        "provider_calls_made": False,
        "runtime_behavior_changed": False,
        "response_text_changed": False,
    }
    print(json.dumps(validation, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
