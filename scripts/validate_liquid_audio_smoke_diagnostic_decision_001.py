#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "LIQUID-AUDIO-SMOKE-DIAGNOSTIC-DECISION-001" / "result.json"
REPORT_PATH = ROOT / "research" / "experiments" / "generated" / "LIQUID-AUDIO-SMOKE-DIAGNOSTIC-DECISION-001" / "report.md"
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
    if result.get("experiment_id") != "LIQUID-AUDIO-SMOKE-DIAGNOSTIC-DECISION-001":
        failures.append("diagnostic decision has wrong experiment_id")
    if result.get("status") != "pass":
        failures.append("diagnostic decision status must be pass")
    if result.get("live_wiring_allowed") is not False:
        failures.append("decision must keep live_wiring_allowed false")
    if result.get("sales_brain_replacement_allowed") is not False:
        failures.append("decision must keep sales_brain_replacement_allowed false")
    if result.get("runtime_behavior_changed") is not False:
        failures.append("decision runtime_behavior_changed must be false")
    if result.get("response_text_changed") is not False:
        failures.append("decision response_text_changed must be false")
    if result.get("independent_asr_benchmark_recommended") is not False:
        failures.append("independent ASR benchmark must not be recommended before prompt/mode fix")
    if result.get("interleaved_s2s_probe_recommended") is not False:
        failures.append("interleaved S2S probe must not be recommended as immediate next step")
    if result.get("liquid_remains_offline_candidate_or_inspiration") is not True:
        failures.append("decision must keep Liquid as offline candidate/inspiration")
    if not str(result.get("primary_recommendation") or "").strip():
        failures.append("primary_recommendation must be recorded")
    ranked = result.get("ranked_recommendations") if isinstance(result.get("ranked_recommendations"), list) else []
    if len(ranked) < 3:
        failures.append("ranked_recommendations must include multiple options")
    options = {item.get("option") for item in ranked if isinstance(item, dict)}
    for expected in (
        "liquid_tts_listening_review_next",
        "liquid_asr_prompt_mode_fix_next",
        "liquid_architecture_inspiration_only",
        "liquid_independent_asr_benchmark_next",
        "liquid_interleaved_s2s_probe_next",
    ):
        if expected not in options:
            failures.append(f"missing decision option {expected}")
    report_lower = report.lower()
    if "live ready" in report_lower or "live_wiring_allowed: true" in report_lower:
        failures.append("decision report must not claim live readiness")

    for key in (
        "provider_calls_made",
        "generated_audio_committed",
        "model_weights_committed",
        "runtime_behavior_changed",
        "response_text_changed",
    ):
        require_false(result, key, failures, "decision")
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
        require_false(side_effects, key, failures, "decision.side_effects")

    tracked = git_lines(["ls-files"])
    tracked_weights = [path for path in tracked if path.startswith("local_artifacts/") or path.lower().endswith(MODEL_SUFFIXES)]
    tracked_audio = [path for path in tracked if path.lower().endswith(AUDIO_SUFFIXES)]
    if tracked_weights:
        failures.append(f"tracked model/checkpoint/local_artifacts files are forbidden: {tracked_weights[:20]}")
    if tracked_audio:
        failures.append(f"tracked audio files are forbidden: {tracked_audio[:20]}")

    validation = {
        "status": "pass" if not failures else "fail",
        "primary_recommendation": result.get("primary_recommendation"),
        "failures": failures,
        "provider_calls_made": False,
        "runtime_behavior_changed": False,
        "response_text_changed": False,
    }
    print(json.dumps(validation, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
