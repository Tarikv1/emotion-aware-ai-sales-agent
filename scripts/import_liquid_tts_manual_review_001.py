#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MANUAL_DIR = ROOT / "research" / "experiments" / "generated" / "LIQUID-AUDIO-LISTENING-REVIEW-MANUAL-001"
TEMPLATE_JSON_PATH = MANUAL_DIR / "manual_review_template.json"
FILLED_JSON_PATH = MANUAL_DIR / "manual_review_filled.json"
RESULT_PATH = MANUAL_DIR / "result.json"
REPORT_PATH = MANUAL_DIR / "report.md"
DECISION_DIR = ROOT / "research" / "experiments" / "generated" / "LIQUID-AUDIO-LISTENING-REVIEW-DECISION-001"
DECISION_RESULT_PATH = DECISION_DIR / "result.json"
DECISION_REPORT_PATH = DECISION_DIR / "report.md"
MODEL_SUFFIXES = (".safetensors", ".bin", ".gguf", ".pt", ".pth", ".ckpt", ".onnx")
AUDIO_SUFFIXES = (".mp3", ".wav", ".flac", ".m4a", ".ogg")
RATING_FIELDS = [
    "intelligibility_1_to_5",
    "naturalness_1_to_5",
    "voice_quality_1_to_5",
    "sales_tone_1_to_5",
    "pacing_1_to_5",
    "artifact_severity_1_to_5",
    "robotic_sound_1_to_5",
    "thesis_demo_suitability_1_to_5",
    "product_fallback_suitability_1_to_5",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


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


def tracked_model_files() -> list[str]:
    return [
        path
        for path in git_lines(["ls-files"])
        if path.startswith("local_artifacts/") or path.lower().endswith(MODEL_SUFFIXES)
    ]


def tracked_audio_files() -> list[str]:
    return [path for path in git_lines(["ls-files"]) if path.lower().endswith(AUDIO_SUFFIXES)]


def side_effects() -> dict[str, bool]:
    return {
        "provider_calls_made": False,
        "openai_api_calls_made": False,
        "elevenlabs_calls_made": False,
        "live_tts_calls_made": False,
        "liquid_inference_run": False,
        "new_audio_generated": False,
        "audio_files_copied": False,
        "model_download_attempted": False,
        "model_weights_committed": bool(tracked_model_files()),
        "audio_files_committed": bool(tracked_audio_files()),
        "runtime_behavior_changed": False,
        "response_text_changed": False,
        "raw_private_audio_used": False,
        "raw_private_transcripts_included": False,
    }


def average(values: list[float]) -> float | None:
    if not values:
        return None
    return round(sum(values) / len(values), 4)


def validate_rating(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    if value < 1 or value > 5:
        return None
    return float(value)


def compute_averages(entries: list[dict[str, Any]]) -> dict[str, float | None]:
    averages: dict[str, float | None] = {}
    for field in RATING_FIELDS:
        values = [float(entry[field]) for entry in entries if isinstance(entry.get(field), (int, float))]
        averages[field.replace("_1_to_5", "")] = average(values)
    return averages


def classify(averages: dict[str, float | None], valid_entries: int, expected_entries: int) -> str:
    if valid_entries == 0:
        return "pending_manual_review"
    if valid_entries < expected_entries:
        return "needs_more_review"
    intelligibility = averages.get("intelligibility") or 0
    naturalness = averages.get("naturalness") or 0
    voice_quality = averages.get("voice_quality") or 0
    sales_tone = averages.get("sales_tone") or 0
    artifact = averages.get("artifact_severity") or 5
    robotic = averages.get("robotic_sound") or 5
    thesis = averages.get("thesis_demo_suitability") or 0
    fallback = averages.get("product_fallback_suitability") or 0
    if intelligibility < 3 or voice_quality < 3 or artifact > 3.5 or robotic > 3.5:
        return "fail_quality"
    if fallback >= 4 and intelligibility >= 4 and naturalness >= 3.5 and sales_tone >= 3.5 and artifact <= 2.5:
        return "pass_for_offline_fallback"
    if thesis >= 4 and intelligibility >= 4 and fallback < 4:
        return "pass_for_thesis_demo"
    return "needs_more_review"


def decision_for_status(status: str, averages: dict[str, float | None]) -> tuple[str, str]:
    if status == "pending_manual_review":
        return "user_listen_and_fill_review", "Manual ratings are missing. Listen to the five local files and fill manual_review_filled.json."
    if status == "pass_for_thesis_demo":
        return "keep_liquid_as_thesis_offline_demo_candidate_only", "Manual review supports thesis/offline demo use, but not product fallback."
    if status == "pass_for_offline_fallback":
        return "compare_liquid_tts_against_kokoro_and_elevenlabs_latency_quality", "Manual review supports fallback exploration; compare against Kokoro and ElevenLabs before any product decision."
    if status == "fail_quality":
        return (
            "liquid_architecture_inspiration_only",
            "Human listening review found all generated Liquid TTS files unintelligible/gibberish. Liquid should not be used as TTS/voice backend. Keep it as architecture inspiration only.",
        )
    return "continue_manual_review_or_collect_second_listener", "Manual review is incomplete or inconclusive; collect the missing ratings or a second listener review."


def template_entries() -> list[dict[str, Any]]:
    template = read_json(TEMPLATE_JSON_PATH)
    return [entry for entry in template.get("entries", []) if isinstance(entry, dict)]


def pending_result(reason: str) -> dict[str, Any]:
    entries = template_entries()
    result = {
        "experiment_id": "LIQUID-AUDIO-LISTENING-REVIEW-MANUAL-001",
        "generated_at": utc_now(),
        "status": "pending_manual_review",
        "listening_review_status": "pending_manual_review",
        "reason": reason,
        "manual_review_template": rel(TEMPLATE_JSON_PATH) if TEMPLATE_JSON_PATH.is_file() else "",
        "manual_review_filled": rel(FILLED_JSON_PATH),
        "filled_review_present": FILLED_JSON_PATH.is_file(),
        "expected_review_entries": len(entries),
        "validated_review_entries": 0,
        "averages": {
            "intelligibility": None,
            "naturalness": None,
            "voice_quality": None,
            "sales_tone": None,
            "pacing": None,
            "artifact_severity": None,
            "robotic_sound": None,
            "thesis_demo_suitability": None,
            "product_fallback_suitability": None,
        },
        "quality_inferred_from_latency": False,
        "live_readiness_claimed": False,
        "provider_calls_made": False,
        "openai_api_calls_made": False,
        "elevenlabs_calls_made": False,
        "live_tts_calls_made": False,
        "liquid_inference_run": False,
        "new_audio_generated": False,
        "audio_files_copied": False,
        "audio_files_committed": bool(tracked_audio_files()),
        "model_weights_committed": bool(tracked_model_files()),
        "runtime_behavior_changed": False,
        "response_text_changed": False,
        "live_wiring_allowed": False,
        "sales_brain_replacement_allowed": False,
        "side_effects": side_effects(),
    }
    return result


def write_result_report(result: dict[str, Any]) -> None:
    outcome_lines = []
    if result.get("listening_review_status") == "fail_quality":
        outcome_lines = [
            "",
            "## Outcome",
            "",
            "- Liquid TTS failed manual listening review.",
            "- Failure type: quality/intelligibility, not latency.",
            "- Liquid is not suitable for thesis demo audio.",
            "- Liquid is not suitable as a product fallback voice.",
            "- Liquid should not replace ElevenLabs.",
            "- Liquid remains architecture inspiration only.",
        ]
    write_json(RESULT_PATH, result)
    write_text(
        REPORT_PATH,
        "\n".join(
            [
                "# LIQUID-AUDIO-LISTENING-REVIEW-MANUAL-001",
                "",
                f"- status: {result['status']}",
                f"- listening_review_status: {result['listening_review_status']}",
                f"- filled_review_present: {str(result['filled_review_present']).lower()}",
                f"- validated_review_entries: {result['validated_review_entries']}",
                "- quality_inferred_from_latency: false",
                "- live_readiness_claimed: false",
                "- provider_calls_made: false",
                "- live_wiring_allowed: false",
                "- sales_brain_replacement_allowed: false",
                "",
                "## Averages",
                "",
                json.dumps(result.get("averages", {}), indent=2),
                *outcome_lines,
            ]
        ),
    )


def write_decision(result: dict[str, Any]) -> dict[str, Any]:
    recommendation, rationale = decision_for_status(str(result.get("listening_review_status")), result.get("averages") or {})
    decision = {
        "experiment_id": "LIQUID-AUDIO-LISTENING-REVIEW-DECISION-001",
        "generated_at": utc_now(),
        "status": "pass",
        "manual_review_result": rel(RESULT_PATH),
        "listening_review_status": result.get("listening_review_status"),
        "recommendation": recommendation,
        "rationale": rationale,
        "quality_inferred_from_latency": False,
        "live_readiness_claimed": False,
        "compare_liquid_against_kokoro_and_elevenlabs": recommendation == "compare_liquid_tts_against_kokoro_and_elevenlabs_latency_quality",
        "liquid_thesis_or_offline_only": recommendation == "keep_liquid_as_thesis_offline_demo_candidate_only",
        "liquid_architecture_inspiration_only": recommendation == "liquid_architecture_inspiration_only",
        "quality_based_on_manual_review": result.get("quality_based_on_manual_review") is True,
        "thesis_demo_tts_allowed": result.get("thesis_demo_tts_allowed") is True,
        "product_fallback_tts_allowed": result.get("product_fallback_tts_allowed") is True,
        "elevenlabs_remains_current_voice_path": result.get("elevenlabs_remains_current_voice_path") is True,
        "liquid_tts_backend_candidate_status": result.get("liquid_tts_backend_candidate_status"),
        "liquid_should_replace_elevenlabs": False,
        "provider_calls_made": False,
        "openai_api_calls_made": False,
        "elevenlabs_calls_made": False,
        "live_tts_calls_made": False,
        "liquid_inference_run": False,
        "new_audio_generated": False,
        "audio_files_copied": False,
        "audio_files_committed": bool(tracked_audio_files()),
        "model_weights_committed": bool(tracked_model_files()),
        "runtime_behavior_changed": False,
        "response_text_changed": False,
        "live_wiring_allowed": False,
        "sales_brain_replacement_allowed": False,
        "side_effects": side_effects(),
    }
    write_json(DECISION_RESULT_PATH, decision)
    write_text(
        DECISION_REPORT_PATH,
        "\n".join(
            [
                "# LIQUID-AUDIO-LISTENING-REVIEW-DECISION-001",
                "",
                f"- status: {decision['status']}",
                f"- listening_review_status: {decision['listening_review_status']}",
                f"- recommendation: `{decision['recommendation']}`",
                "- quality_inferred_from_latency: false",
                f"- quality_based_on_manual_review: {str(decision['quality_based_on_manual_review']).lower()}",
                f"- thesis_demo_tts_allowed: {str(decision['thesis_demo_tts_allowed']).lower()}",
                f"- product_fallback_tts_allowed: {str(decision['product_fallback_tts_allowed']).lower()}",
                f"- liquid_architecture_inspiration_only: {str(decision['liquid_architecture_inspiration_only']).lower()}",
                f"- elevenlabs_remains_current_voice_path: {str(decision['elevenlabs_remains_current_voice_path']).lower()}",
                "- live_readiness_claimed: false",
                "- live_wiring_allowed: false",
                "- sales_brain_replacement_allowed: false",
                "",
                "## Rationale",
                "",
                rationale,
            ]
        ),
    )
    return decision


def main() -> int:
    template = read_json(TEMPLATE_JSON_PATH)
    expected_entries = [entry for entry in template.get("entries", []) if isinstance(entry, dict)]
    if not FILLED_JSON_PATH.is_file():
        result = pending_result("manual_review_filled.json is missing")
        write_result_report(result)
        decision = write_decision(result)
        print(json.dumps({"status": result["status"], "recommendation": decision["recommendation"]}, indent=2))
        return 0

    filled = read_json(FILLED_JSON_PATH)
    filled_entries = [entry for entry in filled.get("entries", []) if isinstance(entry, dict)]
    expected_by_id = {entry.get("case_id"): entry for entry in expected_entries}
    validation_errors: list[str] = []
    validated_entries: list[dict[str, Any]] = []
    for entry in filled_entries:
        case_id = entry.get("case_id")
        if case_id not in expected_by_id:
            validation_errors.append(f"unknown case_id: {case_id}")
            continue
        merged = dict(expected_by_id[case_id])
        merged.update(entry)
        for field in RATING_FIELDS:
            rating = validate_rating(merged.get(field))
            if rating is None:
                validation_errors.append(f"{case_id}.{field} must be a number from 1 to 5")
            else:
                merged[field] = rating
        if not isinstance(merged.get("compared_to_elevenlabs"), str):
            validation_errors.append(f"{case_id}.compared_to_elevenlabs must be a string")
        if not isinstance(merged.get("notes"), str):
            validation_errors.append(f"{case_id}.notes must be a string")
        validated_entries.append(merged)

    averages = compute_averages(validated_entries)
    status = "needs_more_review" if validation_errors else classify(averages, len(validated_entries), len(expected_entries))
    fail_quality = status == "fail_quality"
    result = {
        "experiment_id": "LIQUID-AUDIO-LISTENING-REVIEW-MANUAL-001",
        "generated_at": utc_now(),
        "status": "pass" if not validation_errors else "needs_more_review",
        "listening_review_status": status,
        "validation_errors": validation_errors,
        "manual_review_template": rel(TEMPLATE_JSON_PATH),
        "manual_review_filled": rel(FILLED_JSON_PATH),
        "filled_review_present": True,
        "expected_review_entries": len(expected_entries),
        "validated_review_entries": len(validated_entries),
        "entries": validated_entries,
        "averages": averages,
        "manual_review_source": filled.get("manual_review_source") or "manual_review_filled_json",
        "review_summary": filled.get("review_summary") or "",
        "quality_based_on_manual_review": len(validated_entries) == len(expected_entries) and not validation_errors,
        "liquid_tts_backend_candidate_status": "rejected_by_manual_listening_review" if fail_quality else status,
        "failure_type": "quality_intelligibility" if fail_quality else "",
        "thesis_demo_tts_allowed": status == "pass_for_thesis_demo",
        "product_fallback_tts_allowed": status == "pass_for_offline_fallback",
        "elevenlabs_remains_current_voice_path": True,
        "liquid_should_replace_elevenlabs": False,
        "liquid_architecture_inspiration_only": fail_quality,
        "quality_inferred_from_latency": False,
        "live_readiness_claimed": False,
        "provider_calls_made": False,
        "openai_api_calls_made": False,
        "elevenlabs_calls_made": False,
        "live_tts_calls_made": False,
        "liquid_inference_run": False,
        "new_audio_generated": False,
        "audio_files_copied": False,
        "audio_files_committed": bool(tracked_audio_files()),
        "model_weights_committed": bool(tracked_model_files()),
        "runtime_behavior_changed": False,
        "response_text_changed": False,
        "live_wiring_allowed": False,
        "sales_brain_replacement_allowed": False,
        "side_effects": side_effects(),
    }
    write_result_report(result)
    decision = write_decision(result)
    print(json.dumps({"status": result["status"], "listening_review_status": status, "recommendation": decision["recommendation"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
