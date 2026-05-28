#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import subprocess
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MANUAL_RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "LIQUID-AUDIO-LISTENING-REVIEW-MANUAL-001" / "result.json"
DECISION_RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "LIQUID-AUDIO-LISTENING-REVIEW-DECISION-001" / "result.json"
DECISION_REPORT_PATH = ROOT / "research" / "experiments" / "generated" / "LIQUID-AUDIO-LISTENING-REVIEW-DECISION-001" / "report.md"
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


def require_false(payload: dict[str, Any], key: str, failures: list[str], prefix: str) -> None:
    if payload.get(key) is not False:
        failures.append(f"{prefix}.{key} must be false")


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
    manual = load_json(MANUAL_RESULT_PATH)
    decision = load_json(DECISION_RESULT_PATH)
    report = DECISION_REPORT_PATH.read_text(encoding="utf-8") if DECISION_REPORT_PATH.is_file() else ""
    if not report:
        failures.append(f"missing decision report: {rel(DECISION_REPORT_PATH)}")
    if decision.get("experiment_id") != "LIQUID-AUDIO-LISTENING-REVIEW-DECISION-001":
        failures.append("decision has wrong experiment_id")
    if decision.get("status") != "pass":
        failures.append("decision status must be pass")
    if decision.get("listening_review_status") != manual.get("listening_review_status"):
        failures.append("decision must mirror manual listening_review_status")
    recommendation = str(decision.get("recommendation") or "")
    if not recommendation:
        failures.append("decision recommendation must be present")
    if manual.get("listening_review_status") == "pending_manual_review" and recommendation != "user_listen_and_fill_review":
        failures.append("pending manual review must recommend user_listen_and_fill_review")
    if manual.get("listening_review_status") == "fail_quality":
        if recommendation != "liquid_architecture_inspiration_only":
            failures.append("failed manual quality review must recommend liquid_architecture_inspiration_only")
        if decision.get("liquid_architecture_inspiration_only") is not True:
            failures.append("failed review decision must mark liquid_architecture_inspiration_only true")
        if decision.get("liquid_thesis_or_offline_only") is not False:
            failures.append("failed review decision must not keep Liquid as thesis/offline TTS")
        if decision.get("compare_liquid_against_kokoro_and_elevenlabs") is not False:
            failures.append("failed review decision must not recommend comparing Liquid as a near-term voice backend")
        if decision.get("quality_based_on_manual_review") is not True:
            failures.append("failed review decision must record quality_based_on_manual_review true")
        if decision.get("thesis_demo_tts_allowed") is not False:
            failures.append("failed review decision must reject thesis demo TTS suitability")
        if decision.get("product_fallback_tts_allowed") is not False:
            failures.append("failed review decision must reject product fallback TTS suitability")
        if decision.get("elevenlabs_remains_current_voice_path") is not True:
            failures.append("failed review decision must keep ElevenLabs as current voice path")
        if decision.get("liquid_tts_backend_candidate_status") != "rejected_by_manual_listening_review":
            failures.append("failed review decision must mark Liquid TTS rejected by manual listening review")
        rationale = str(decision.get("rationale") or "").lower()
        if "unintelligible" not in rationale or "architecture inspiration" not in rationale:
            failures.append("failed review rationale must cite unintelligible audio and architecture-inspiration-only status")
    if decision.get("quality_inferred_from_latency") is not False:
        failures.append("decision must not infer quality from latency")
    if decision.get("live_readiness_claimed") is not False:
        failures.append("decision must not claim live readiness")
    if decision.get("live_wiring_allowed") is not False:
        failures.append("decision live_wiring_allowed must be false")
    if decision.get("sales_brain_replacement_allowed") is not False:
        failures.append("decision sales_brain_replacement_allowed must be false")
    if "live ready" in report.lower() or "live_wiring_allowed: true" in report.lower():
        failures.append("decision report must not claim live readiness")

    for key in (
        "provider_calls_made",
        "openai_api_calls_made",
        "elevenlabs_calls_made",
        "live_tts_calls_made",
        "liquid_inference_run",
        "new_audio_generated",
        "audio_files_copied",
        "audio_files_committed",
        "model_weights_committed",
        "runtime_behavior_changed",
        "response_text_changed",
    ):
        require_false(decision, key, failures, "decision")
    validate_side_effects(decision, failures, "decision")

    tracked = git_lines(["ls-files"])
    tracked_weights = [path for path in tracked if path.startswith("local_artifacts/") or path.lower().endswith(MODEL_SUFFIXES)]
    tracked_audio = [path for path in tracked if path.lower().endswith(AUDIO_SUFFIXES)]
    if tracked_weights:
        failures.append(f"tracked model/checkpoint/local_artifacts files are forbidden: {tracked_weights[:20]}")
    if tracked_audio:
        failures.append(f"tracked audio files are forbidden: {tracked_audio[:20]}")

    validation = {
        "status": "pass" if not failures else "fail",
        "manual_review_status": manual.get("listening_review_status"),
        "recommendation": recommendation,
        "failures": failures,
        "provider_calls_made": False,
        "runtime_behavior_changed": False,
        "response_text_changed": False,
    }
    print(json.dumps(validation, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
