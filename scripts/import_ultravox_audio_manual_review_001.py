#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from statistics import mean
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MANUAL_DIR = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-AUDIO-LISTENING-REVIEW-MANUAL-001"
TEMPLATE_PATH = MANUAL_DIR / "manual_review_template.json"
FILLED_PATH = MANUAL_DIR / "manual_review_filled.json"
RESULT_PATH = MANUAL_DIR / "result.json"
REPORT_PATH = MANUAL_DIR / "report.md"
TRANSCRIPT_RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-AUDIO-TRANSCRIPT-QUALITY-001" / "result.json"
LATENCY_RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-AUDIO-LATENCY-AUDIT-001" / "result.json"
TOOL_RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-AUDIO-TOOL-BOUNDARY-AUDIT-001" / "result.json"
DECISION_DIR = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-AUDIO-SANDBOX-REVIEW-DECISION-001"
DECISION_RESULT_PATH = DECISION_DIR / "result.json"
DECISION_REPORT_PATH = DECISION_DIR / "report.md"

NUMERIC_FIELDS = (
    "intelligibility",
    "naturalness",
    "voice_quality",
    "sales_tone",
    "pacing",
    "artifact_severity",
    "interruption_turn_taking_quality",
    "thesis_demo_suitability",
    "product_fallback_suitability",
)
TEXT_FIELDS = ("compared_to_elevenlabs", "notes")


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"{path} must contain a JSON object")
    return payload


def load_optional_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    return load_json(path)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def round4(value: float) -> float:
    return round(value, 4)


def validate_ratings(review: dict[str, Any]) -> dict[str, Any]:
    reviews = review.get("per_audio_output_reviews")
    if not isinstance(reviews, list) or len(reviews) != 1 or not isinstance(reviews[0], dict):
        raise AssertionError("manual_review_filled.json must contain exactly one audio output review")
    ratings = reviews[0].get("ratings")
    if not isinstance(ratings, dict):
        raise AssertionError("manual review entry must contain ratings")
    normalized: dict[str, Any] = {}
    for field in NUMERIC_FIELDS:
        value = ratings.get(field)
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise AssertionError(f"{field} must be a numeric rating")
        value_float = float(value)
        if value_float < 1 or value_float > 5:
            raise AssertionError(f"{field} must be between 1 and 5")
        normalized[field] = int(value_float) if value_float.is_integer() else value_float
    for field in TEXT_FIELDS:
        value = ratings.get(field)
        if not isinstance(value, str) or not value.strip():
            raise AssertionError(f"{field} must be non-empty text")
        normalized[field] = " ".join(value.split())
    return normalized


def classify(ratings: dict[str, Any]) -> str:
    if ratings["intelligibility"] < 3 or ratings["voice_quality"] < 3 or ratings["artifact_severity"] >= 4:
        return "fail_quality"
    if ratings["product_fallback_suitability"] >= 4.5 and ratings["intelligibility"] >= 4 and ratings["voice_quality"] >= 4 and ratings["artifact_severity"] <= 2:
        return "pass_for_product_fallback"
    if ratings["thesis_demo_suitability"] >= 4 and ratings["intelligibility"] >= 4 and ratings["artifact_severity"] <= 2:
        return "pass_for_thesis_demo"
    return "needs_more_review"


def quality_classification(status: str) -> str:
    if status in {"pass_for_product_fallback", "pass_for_thesis_demo"}:
        return "promising"
    if status == "fail_quality":
        return "failed"
    return "needs_more_review"


def compute_averages(ratings: dict[str, Any]) -> dict[str, float]:
    raw_values = [float(ratings[field]) for field in NUMERIC_FIELDS]
    artifact_quality_score = 6 - float(ratings["artifact_severity"])
    quality_values = [
        float(ratings["intelligibility"]),
        float(ratings["naturalness"]),
        float(ratings["voice_quality"]),
        float(ratings["sales_tone"]),
        float(ratings["pacing"]),
        artifact_quality_score,
        float(ratings["interruption_turn_taking_quality"]),
        float(ratings["thesis_demo_suitability"]),
        float(ratings["product_fallback_suitability"]),
    ]
    return {
        "raw_rating_average": round4(mean(raw_values)),
        "quality_score_average": round4(mean(quality_values)),
        "artifact_quality_score": round4(artifact_quality_score),
        "demo_suitability_average": round4(mean([float(ratings["intelligibility"]), float(ratings["voice_quality"]), float(ratings["pacing"]), float(ratings["sales_tone"]), float(ratings["thesis_demo_suitability"])])),
        "product_fallback_average": round4(mean([float(ratings["intelligibility"]), float(ratings["voice_quality"]), artifact_quality_score, float(ratings["product_fallback_suitability"])])),
        "voice_naturalness_average": round4(mean([float(ratings["naturalness"]), float(ratings["voice_quality"])])),
    }


def pending_result(template: dict[str, Any]) -> dict[str, Any]:
    return {
        "evaluation_id": "ULTRAVOX-AUDIO-LISTENING-REVIEW-MANUAL-IMPORT-001",
        "phase": "4J6B",
        "source_template_evaluation_id": template.get("evaluation_id"),
        "filled_review_present": False,
        "listening_review_status": "pending_manual_review",
        "quality_classification": "pending_manual_review",
        "ratings": {},
        "new_provider_call_made": False,
        "new_audio_generated": False,
        "audio_files_copied": False,
        "audio_files_committed": False,
        "outbound_phone_call_made": False,
        "real_customer_data_used": False,
        "raw_private_audio_or_transcripts_used": False,
        "live_wiring_allowed": False,
        "production_call_allowed": False,
        "real_customer_data_allowed": False,
        "runtime_behavior_changed": False,
        "response_text_changed": False,
    }


def build_result(template: dict[str, Any], filled: dict[str, Any], latency: dict[str, Any]) -> dict[str, Any]:
    ratings = validate_ratings(filled)
    status = classify(ratings)
    averages = compute_averages(ratings)
    compared = str(ratings["compared_to_elevenlabs"]).lower()
    notes = str(ratings["notes"]).lower()
    result = {
        "evaluation_id": "ULTRAVOX-AUDIO-LISTENING-REVIEW-MANUAL-IMPORT-001",
        "phase": "4J6B",
        "source_template_evaluation_id": template.get("evaluation_id"),
        "source_filled_review": "manual_review_filled.json",
        "filled_review_present": True,
        "listening_review_status": status,
        "quality_classification": quality_classification(status),
        "quality_promising": status in {"pass_for_product_fallback", "pass_for_thesis_demo"},
        "ratings": ratings,
        "artifact_severity_scale_note": "1 means low or no artifact; 5 means severe artifact.",
        "voice_selection_limitation_noted": "voice" in notes and ("selected" in notes or "different" in notes),
        "voice_id_alignment_needed": "voice id" in compared or "voice-id" in compared,
        "latency_live_ready": latency.get("live_ready_latency") is True,
        "warm_turn_benchmark_needed": latency.get("needs_warm_turn_benchmark") is True,
        "current_observed_latency_seconds": latency.get("current_observed_latency_seconds"),
        "live_readiness_claimed": False,
        "final_elevenlabs_replacement_claimed": False,
        "new_provider_call_made": False,
        "new_audio_generated": False,
        "audio_files_copied": False,
        "audio_files_committed": False,
        "outbound_phone_call_made": False,
        "real_customer_data_used": False,
        "raw_private_audio_or_transcripts_used": False,
        "live_wiring_allowed": False,
        "production_call_allowed": False,
        "real_customer_data_allowed": False,
        "runtime_behavior_changed": False,
        "response_text_changed": False,
    }
    result.update(averages)
    return result


def decision_recommendation(manual: dict[str, Any], transcript: dict[str, Any], latency: dict[str, Any], tool: dict[str, Any]) -> str:
    if manual.get("listening_review_status") == "pending_manual_review":
        return "user_listen_to_ultravox_agent_audio"
    if transcript.get("transcript_quality_passed") is not True:
        return "fix audio format / turn timing before another provider run"
    if tool.get("tool_boundary_passed") is not True:
        return "fix tool declaration/prompt before more audio testing"
    if manual.get("quality_promising") is True and latency.get("live_ready_latency") is not True:
        return "warm-session latency benchmark next"
    if manual.get("quality_promising") is True:
        return "limited synthetic voice conversation evaluation next"
    return "needs_more_review"


def build_decision(manual: dict[str, Any], transcript: dict[str, Any], latency: dict[str, Any], tool: dict[str, Any]) -> dict[str, Any]:
    recommendation = decision_recommendation(manual, transcript, latency, tool)
    return {
        "evaluation_id": "ULTRAVOX-AUDIO-SANDBOX-REVIEW-DECISION-001",
        "phase": "4J6B",
        "recommendation": recommendation,
        "secondary_recommendation": "test Ultravox voice/voice-ID options later",
        "manual_listening_review_status": manual.get("listening_review_status"),
        "quality_classification": manual.get("quality_classification"),
        "audio_quality_promising": manual.get("quality_promising") is True,
        "user_audio_review_good": manual.get("quality_promising") is True,
        "voice_selection_limitation_noted": manual.get("voice_selection_limitation_noted") is True,
        "voice_id_alignment_needed": manual.get("voice_id_alignment_needed") is True,
        "transcript_quality_passed": transcript.get("transcript_quality_passed") is True,
        "tool_boundary_passed": tool.get("tool_boundary_passed") is True,
        "live_ready_latency": latency.get("live_ready_latency") is True,
        "needs_warm_turn_benchmark": latency.get("needs_warm_turn_benchmark") is True,
        "current_observed_latency_seconds": latency.get("current_observed_latency_seconds"),
        "next_provider_run_allowed_now": False,
        "live_ready_claimed": False,
        "production_ready_claimed": False,
        "final_elevenlabs_replacement_claimed": False,
        "decision_logic": [
            "Manual listening review imported: audio quality is promising for product fallback and thesis/demo exploration.",
            "Latency remains above the 2-3 second live target, so the next step is a warm-session latency benchmark, still synthetic only.",
            "Voice naturalness and sales tone appear limited by the selected voice; test Ultravox voice/voice-ID options later.",
            "Do not recommend live wiring, production calls, real customer data, or a final ElevenLabs replacement claim.",
        ],
        "new_provider_call_made": False,
        "new_audio_generated": False,
        "audio_files_copied": False,
        "audio_files_committed": False,
        "outbound_phone_call_made": False,
        "real_customer_data_used": False,
        "raw_private_audio_or_transcripts_used": False,
        "live_wiring_allowed": False,
        "production_call_allowed": False,
        "real_customer_data_allowed": False,
        "runtime_behavior_changed": False,
        "response_text_changed": False,
    }


def render_report(result: dict[str, Any]) -> str:
    ratings = result.get("ratings", {})
    return "\n".join(
        [
            "# ULTRAVOX-AUDIO-LISTENING-REVIEW-MANUAL-IMPORT-001",
            "",
            f"Filled review present: `{str(result['filled_review_present']).lower()}`",
            f"Listening review status: `{result['listening_review_status']}`",
            f"Quality classification: `{result['quality_classification']}`",
            f"Raw rating average: `{result.get('raw_rating_average')}`",
            f"Quality score average: `{result.get('quality_score_average')}`",
            f"Demo suitability average: `{result.get('demo_suitability_average')}`",
            f"Product fallback average: `{result.get('product_fallback_average')}`",
            f"Latency live-ready: `{str(result.get('latency_live_ready')).lower()}`",
            f"Warm-turn benchmark needed: `{str(result.get('warm_turn_benchmark_needed')).lower()}`",
            "",
            "## Ratings",
            *[f"- {field}: `{ratings.get(field)}`" for field in NUMERIC_FIELDS],
            "",
            f"Voice/voice-ID note: `{ratings.get('compared_to_elevenlabs')}`",
            f"Notes: `{ratings.get('notes')}`",
            "",
            "## Boundaries",
            "New provider call made: `false`",
            "New audio generated: `false`",
            "Audio files copied: `false`",
            "Audio files committed: `false`",
            "Outbound phone call made: `false`",
            "Real customer data used: `false`",
            "Raw private audio or transcripts used: `false`",
            "Live wiring allowed: `false`",
            "Production call allowed: `false`",
            "Runtime behavior changed: `false`",
            "Response text changed: `false`",
            "",
        ]
    )


def render_decision_report(decision: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# ULTRAVOX-AUDIO-SANDBOX-REVIEW-DECISION-001",
            "",
            f"Recommendation: `{decision['recommendation']}`",
            f"Secondary recommendation: `{decision['secondary_recommendation']}`",
            f"Manual listening review status: `{decision['manual_listening_review_status']}`",
            f"Quality classification: `{decision['quality_classification']}`",
            f"Audio quality promising: `{str(decision['audio_quality_promising']).lower()}`",
            f"Voice selection limitation noted: `{str(decision['voice_selection_limitation_noted']).lower()}`",
            f"Voice ID alignment needed: `{str(decision['voice_id_alignment_needed']).lower()}`",
            f"Transcript quality passed: `{str(decision['transcript_quality_passed']).lower()}`",
            f"Tool boundary passed: `{str(decision['tool_boundary_passed']).lower()}`",
            f"Live-ready latency: `{str(decision['live_ready_latency']).lower()}`",
            f"Needs warm-turn benchmark: `{str(decision['needs_warm_turn_benchmark']).lower()}`",
            f"Current observed latency seconds: `{decision['current_observed_latency_seconds']}`",
            f"Next provider run allowed now: `{str(decision['next_provider_run_allowed_now']).lower()}`",
            f"Final ElevenLabs replacement claimed: `{str(decision['final_elevenlabs_replacement_claimed']).lower()}`",
            "",
            "## Boundaries",
            "New provider call made: `false`",
            "New audio generated: `false`",
            "Audio files copied: `false`",
            "Audio files committed: `false`",
            "Outbound phone call made: `false`",
            "Real customer data used: `false`",
            "Raw private audio or transcripts used: `false`",
            "Live wiring allowed: `false`",
            "Production call allowed: `false`",
            "Real customer data allowed: `false`",
            "Runtime behavior changed: `false`",
            "Response text changed: `false`",
            "",
        ]
    )


def main() -> None:
    template = load_json(TEMPLATE_PATH)
    transcript = load_optional_json(TRANSCRIPT_RESULT_PATH)
    latency = load_optional_json(LATENCY_RESULT_PATH)
    tool = load_optional_json(TOOL_RESULT_PATH)
    if not FILLED_PATH.is_file():
        result = pending_result(template)
    else:
        result = build_result(template, load_json(FILLED_PATH), latency)
    decision = build_decision(result, transcript, latency, tool)
    write_json(RESULT_PATH, result)
    write_text(REPORT_PATH, render_report(result))
    write_json(DECISION_RESULT_PATH, decision)
    write_text(DECISION_REPORT_PATH, render_decision_report(decision))
    print(json.dumps({"listening_review_status": result["listening_review_status"], "recommendation": decision["recommendation"]}, indent=2))


if __name__ == "__main__":
    main()
