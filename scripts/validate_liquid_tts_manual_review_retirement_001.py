#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

MANUAL_DIR = ROOT / "research" / "experiments" / "generated" / "LIQUID-AUDIO-LISTENING-REVIEW-MANUAL-001"
FILLED_JSON_PATH = MANUAL_DIR / "manual_review_filled.json"
MANUAL_RESULT_PATH = MANUAL_DIR / "result.json"
DECISION_RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "LIQUID-AUDIO-LISTENING-REVIEW-DECISION-001" / "result.json"
SMOKE_DECISION_RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "LIQUID-AUDIO-SMOKE-DIAGNOSTIC-DECISION-001" / "result.json"
REGISTRY_PATH = ROOT / "runtime" / "audio_backends" / "audio_backend_candidates.json"
MODEL_SUFFIXES = (".safetensors", ".bin", ".gguf", ".pt", ".pth", ".ckpt", ".onnx")
AUDIO_SUFFIXES = (".mp3", ".wav", ".flac", ".m4a", ".ogg")
RATING_FIELDS = (
    "intelligibility_1_to_5",
    "naturalness_1_to_5",
    "voice_quality_1_to_5",
    "sales_tone_1_to_5",
    "pacing_1_to_5",
    "artifact_severity_1_to_5",
    "robotic_sound_1_to_5",
    "thesis_demo_suitability_1_to_5",
    "product_fallback_suitability_1_to_5",
)


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


def require_true(payload: dict[str, Any], key: str, failures: list[str], prefix: str) -> None:
    if payload.get(key) is not True:
        failures.append(f"{prefix}.{key} must be true")


def validate_no_side_effects(payload: dict[str, Any], failures: list[str], prefix: str) -> None:
    for key in (
        "provider_calls_made",
        "openai_api_calls_made",
        "elevenlabs_calls_made",
        "live_tts_calls_made",
        "liquid_inference_run",
        "new_liquid_inference_run",
        "new_audio_generated",
        "audio_files_copied",
        "model_download_attempted",
        "model_weights_committed",
        "audio_files_committed",
        "generated_audio_committed",
        "runtime_behavior_changed",
        "response_text_changed",
        "raw_private_audio_used",
        "raw_private_transcripts_included",
    ):
        if key in payload:
            require_false(payload, key, failures, prefix)
    side_effects = payload.get("side_effects") if isinstance(payload.get("side_effects"), dict) else {}
    for key in (
        "provider_calls_made",
        "openai_api_calls_made",
        "elevenlabs_calls_made",
        "live_tts_calls_made",
        "liquid_inference_run",
        "new_liquid_inference_run",
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
        if key in side_effects:
            require_false(side_effects, key, failures, f"{prefix}.side_effects")


def main() -> int:
    failures: list[str] = []
    filled = load_json(FILLED_JSON_PATH)
    manual = load_json(MANUAL_RESULT_PATH)
    decision = load_json(DECISION_RESULT_PATH)
    smoke = load_json(SMOKE_DECISION_RESULT_PATH)
    registry = load_json(REGISTRY_PATH)

    entries = filled.get("entries") if isinstance(filled.get("entries"), list) else []
    if len(entries) != 5:
        failures.append(f"manual_review_filled.json must contain 5 entries, got {len(entries)}")
    for entry in entries:
        if not isinstance(entry, dict):
            failures.append("manual_review_filled.json entries must be objects")
            continue
        for field in RATING_FIELDS:
            expected = 5 if field in {"artifact_severity_1_to_5", "robotic_sound_1_to_5"} else 1
            if entry.get(field) != expected:
                failures.append(f"{entry.get('case_id')}.{field} must be {expected}")
        if entry.get("compared_to_elevenlabs") != "Liquid is unusable here; ElevenLabs remains far better and should remain the current voice path.":
            failures.append(f"{entry.get('case_id')}.compared_to_elevenlabs has unexpected text")
        if entry.get("notes") != "Human review: no recognizable words or sentences; output sounded like unintelligible gibberish/noise.":
            failures.append(f"{entry.get('case_id')}.notes has unexpected text")

    if manual.get("listening_review_status") != "fail_quality":
        failures.append("manual listening_review_status must be fail_quality")
    if manual.get("validated_review_entries") != 5:
        failures.append("manual result must validate all five entries")
    require_true(manual, "quality_based_on_manual_review", failures, "manual")
    require_true(manual, "elevenlabs_remains_current_voice_path", failures, "manual")
    require_true(manual, "liquid_architecture_inspiration_only", failures, "manual")
    require_false(manual, "thesis_demo_tts_allowed", failures, "manual")
    require_false(manual, "product_fallback_tts_allowed", failures, "manual")

    if decision.get("recommendation") != "liquid_architecture_inspiration_only":
        failures.append("decision must recommend liquid_architecture_inspiration_only")
    require_true(decision, "quality_based_on_manual_review", failures, "decision")
    require_true(decision, "liquid_architecture_inspiration_only", failures, "decision")
    require_false(decision, "liquid_thesis_or_offline_only", failures, "decision")
    require_false(decision, "compare_liquid_against_kokoro_and_elevenlabs", failures, "decision")
    require_false(decision, "thesis_demo_tts_allowed", failures, "decision")
    require_false(decision, "product_fallback_tts_allowed", failures, "decision")
    if decision.get("liquid_tts_backend_candidate_status") != "rejected_by_manual_listening_review":
        failures.append("decision must mark Liquid TTS rejected by manual listening review")

    if smoke.get("primary_recommendation") != "liquid_architecture_inspiration_only":
        failures.append("smoke decision must retire Liquid to architecture inspiration only")
    if smoke.get("liquid_tts_quality_status") != "failed_manual_review":
        failures.append("smoke decision must record failed manual review")
    if smoke.get("liquid_asr_prompt_mode_fix_next") != "not recommended now":
        failures.append("smoke decision must not recommend Liquid ASR prompt/mode work now")
    require_false(smoke, "independent_asr_benchmark_recommended", failures, "smoke")
    require_false(smoke, "interleaved_s2s_probe_recommended", failures, "smoke")
    require_true(smoke, "kokoro_tts_benchmark_recommended_next", failures, "smoke")
    require_true(smoke, "elevenlabs_remains_current_voice_path", failures, "smoke")

    candidates = registry.get("candidates") if isinstance(registry.get("candidates"), list) else []
    liquid = next((item for item in candidates if isinstance(item, dict) and item.get("backend_id") == "liquid_audio_lfm25"), {})
    if not liquid:
        failures.append("Liquid registry entry missing")
    if liquid.get("integration_classification") != "architecture_inspiration_only":
        failures.append("Liquid registry must mark architecture_inspiration_only")
    if liquid.get("tts_backend_candidate_status") != "rejected_by_manual_listening_review":
        failures.append("Liquid registry must reject TTS backend candidate status")
    for key in (
        "near_term_voice_backend_allowed",
        "thesis_demo_tts_allowed",
        "product_fallback_tts_allowed",
        "live_runtime_allowed",
        "sales_brain_replacement_allowed",
    ):
        require_false(liquid, key, failures, "liquid_registry")
    role = str(liquid.get("role_in_project") or "").lower()
    note = str(liquid.get("phase_4i1g_manual_review_note") or "").lower()
    if "architecture inspiration" not in role or "tts/voice backend" not in role:
        failures.append("Liquid role must keep it as architecture inspiration, not a TTS/voice backend")
    if "unintelligible" not in note or "no recognizable words" not in note:
        failures.append("Liquid registry note must capture the manual listening failure")

    for name, payload in (
        ("filled", filled),
        ("manual", manual),
        ("decision", decision),
        ("smoke", smoke),
    ):
        validate_no_side_effects(payload, failures, name)
        require_false(payload, "runtime_behavior_changed", failures, name)
        require_false(payload, "response_text_changed", failures, name)
        if "live_wiring_allowed" in payload:
            require_false(payload, "live_wiring_allowed", failures, name)
        if "sales_brain_replacement_allowed" in payload:
            require_false(payload, "sales_brain_replacement_allowed", failures, name)

    evidence_audio = [
        rel(path)
        for base in (
            MANUAL_DIR,
            DECISION_RESULT_PATH.parent,
            SMOKE_DECISION_RESULT_PATH.parent,
        )
        for path in base.rglob("*")
        if path.is_file() and path.suffix.lower() in AUDIO_SUFFIXES
    ]
    if evidence_audio:
        failures.append(f"audio files copied into public evidence are forbidden: {evidence_audio[:20]}")

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
        "validated_review_entries": manual.get("validated_review_entries"),
        "liquid_tts_backend_candidate_status": liquid.get("tts_backend_candidate_status") if isinstance(liquid, dict) else None,
        "elevenlabs_remains_current_voice_path": smoke.get("elevenlabs_remains_current_voice_path"),
        "kokoro_tts_benchmark_recommended_next": smoke.get("kokoro_tts_benchmark_recommended_next"),
        "audio_files_copied": False,
        "audio_files_committed": bool(tracked_audio),
        "model_weights_committed": bool(tracked_weights),
        "new_inference_or_audio_generation": False,
        "provider_calls_made": False,
        "runtime_behavior_changed": False,
        "response_text_changed": False,
        "failures": failures,
    }
    print(json.dumps(validation, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
