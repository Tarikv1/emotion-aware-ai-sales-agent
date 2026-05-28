#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "LIQUID-AUDIO-SMOKE-IMPLEMENTATION-AUDIT-001" / "result.json"
REPORT_PATH = ROOT / "research" / "experiments" / "generated" / "LIQUID-AUDIO-SMOKE-IMPLEMENTATION-AUDIT-001" / "report.md"
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
    if result.get("experiment_id") != "LIQUID-AUDIO-SMOKE-IMPLEMENTATION-AUDIT-001":
        failures.append("implementation audit has wrong experiment_id")
    if result.get("status") != "pass":
        failures.append("implementation audit status must be pass")
    if result.get("live_wiring_allowed") is not False:
        failures.append("live_wiring_allowed must be false")
    if result.get("sales_brain_replacement_allowed") is not False:
        failures.append("sales_brain_replacement_allowed must be false")
    if result.get("runtime_behavior_changed") is not False:
        failures.append("runtime_behavior_changed must be false")
    if result.get("response_text_changed") is not False:
        failures.append("response_text_changed must be false")

    mode = result.get("mode_audit") if isinstance(result.get("mode_audit"), dict) else {}
    output = result.get("output_audit") if isinstance(result.get("output_audit"), dict) else {}
    causes = result.get("likely_failure_causes") if isinstance(result.get("likely_failure_causes"), list) else []
    if not str(result.get("primary_asr_failure_cause") or "").strip():
        failures.append("primary_asr_failure_cause must be recorded")
    if result.get("primary_asr_failure_cause") == "actual_model_limitation":
        failures.append("audit must not overclaim final model limitation from loopback evidence")
    if "assistant_response" not in str(output.get("asr_output_classification") or ""):
        failures.append("ASR output classification must identify assistant-response-like output")
    if not causes:
        failures.append("likely_failure_causes must be populated")
    if not mode.get("asked_to_transcribe"):
        failures.append("audit must record whether model was asked to transcribe")
    if not mode.get("chat_state_roles_used"):
        failures.append("audit must record chat-state role usage")

    audio_audit = result.get("audio_input_audit") if isinstance(result.get("audio_input_audit"), dict) else {}
    if audio_audit.get("generated_tts_loopback_is_valid_asr_quality_source") is not False:
        failures.append("loopback audio must not be treated as independent ASR quality source")
    for item in audio_audit.get("loopback_audio_metadata") or []:
        if not isinstance(item, dict):
            failures.append("loopback metadata entries must be objects")
            continue
        if item.get("under_local_artifacts") is not True:
            failures.append(f"loopback audio path must stay under local_artifacts: {item.get('path')}")

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
        require_false(side_effects, key, failures, "implementation.side_effects")

    tracked = git_lines(["ls-files"])
    tracked_weights = [path for path in tracked if path.startswith("local_artifacts/") or path.lower().endswith(MODEL_SUFFIXES)]
    tracked_audio = [path for path in tracked if path.lower().endswith(AUDIO_SUFFIXES)]
    if tracked_weights:
        failures.append(f"tracked model/checkpoint/local_artifacts files are forbidden: {tracked_weights[:20]}")
    if tracked_audio:
        failures.append(f"tracked audio files are forbidden: {tracked_audio[:20]}")

    validation = {
        "status": "pass" if not failures else "fail",
        "primary_asr_failure_cause": result.get("primary_asr_failure_cause"),
        "failures": failures,
        "provider_calls_made": False,
        "runtime_behavior_changed": False,
        "response_text_changed": False,
    }
    print(json.dumps(validation, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
