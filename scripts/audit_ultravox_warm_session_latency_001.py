#!/usr/bin/env python3
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
WARM_RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-WARM-SESSION-LATENCY-001" / "result.json"
PRIOR_REVIEW_DECISION_PATH = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-AUDIO-SANDBOX-REVIEW-DECISION-001" / "result.json"
PRIOR_FEASIBILITY_DECISION_PATH = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-HOSTED-FEASIBILITY-DECISION-001" / "result.json"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-WARM-SESSION-LATENCY-AUDIT-001"
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"
FEASIBILITY_RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-HOSTED-FEASIBILITY-DECISION-001" / "result.json"
FEASIBILITY_REPORT_PATH = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-HOSTED-FEASIBILITY-DECISION-001" / "report.md"
REVIEW_RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-AUDIO-SANDBOX-REVIEW-DECISION-001" / "result.json"
REVIEW_REPORT_PATH = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-AUDIO-SANDBOX-REVIEW-DECISION-001" / "report.md"


def load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def rounded(value: float | int | None) -> float | None:
    if value is None:
        return None
    return round(float(value), 3)


def measured_latencies(warm: dict[str, Any]) -> list[float]:
    return [
        float(turn["user_turn_end_to_first_agent_audio_seconds"])
        for turn in warm.get("turns", [])
        if isinstance(turn, dict)
        and turn.get("measured_turn") is True
        and isinstance(turn.get("user_turn_end_to_first_agent_audio_seconds"), (int, float))
    ]


def median(values: list[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    midpoint = len(ordered) // 2
    if len(ordered) % 2:
        return rounded(ordered[midpoint])
    return rounded((ordered[midpoint - 1] + ordered[midpoint]) / 2.0)


def percentile_nearest(values: list[float], pct: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, math.ceil((pct / 100.0) * len(ordered)) - 1))
    return rounded(ordered[index])


def latency_band(p50: float | None) -> str:
    if p50 is None:
        return "unknown"
    if p50 <= 2.0:
        return "strong_live_target"
    if p50 <= 3.0:
        return "early_demo_target"
    if p50 <= 5.0:
        return "borderline"
    return "not_live_ready"


def classification(p50: float | None, tool_boundary_passed: bool, session_ok: bool, measured_count: int) -> str:
    if not session_ok or measured_count == 0:
        return "benchmark_inconclusive"
    if tool_boundary_passed and p50 is not None and p50 <= 2.0:
        return "live_latency_promising"
    if tool_boundary_passed and p50 is not None and p50 <= 3.0:
        return "demo_latency_promising"
    if p50 is not None:
        return "latency_not_ready"
    return "benchmark_inconclusive"


def recommendation_for(result: dict[str, Any]) -> str:
    if result.get("prepared_audio_available") is not True:
        return "prepare manual audio inputs"
    if result.get("session_created") is not True or result.get("websocket_connected") is not True:
        return "fix session/WebSocket before more provider usage"
    if result.get("tool_boundary_passed") is not True:
        return "do not proceed"
    p50 = result.get("warm_p50_first_agent_audio_latency_seconds")
    if isinstance(p50, (int, float)) and p50 <= 2.0:
        return "limited synthetic voice conversation evaluation next"
    if isinstance(p50, (int, float)) and p50 <= 3.0:
        return "thesis-demo synthetic voice evaluation next"
    if isinstance(p50, (int, float)) and p50 > 5.0:
        return "keep Ultravox as architecture candidate, investigate provider settings/voice/session configuration before more usage"
    if result.get("audio_quality_promising") is True and isinstance(p50, (int, float)):
        return "test voice/session settings and warm-run repeat once"
    return "benchmark inconclusive"


def build_result(warm: dict[str, Any], prior_review: dict[str, Any]) -> dict[str, Any]:
    latencies = measured_latencies(warm)
    p50 = median(latencies)
    p90 = percentile_nearest(latencies, 90.0) if len(latencies) >= 2 else None
    tool_boundary_passed = (
        warm.get("tool_boundary_enforced") is True
        and int(warm.get("local_http_tool_request_count", 0) or 0) > 0
        and int(warm.get("product_truth_drift_count", 0) or 0) == 0
        and int(warm.get("fake_side_effect_count", 0) or 0) == 0
    )
    session_ok = warm.get("session_created") is True and warm.get("websocket_connected") is True
    strong = bool(tool_boundary_passed and p50 is not None and p50 <= 2.0)
    early = bool(tool_boundary_passed and p50 is not None and p50 <= 3.0)
    result = {
        "evaluation_id": "ULTRAVOX-WARM-SESSION-LATENCY-AUDIT-001",
        "phase": "4J7",
        "warm_session_latency_result_id": warm.get("evaluation_id"),
        "session_created": warm.get("session_created") is True,
        "websocket_connected": warm.get("websocket_connected") is True,
        "prepared_audio_available": warm.get("prepared_audio_available") is True,
        "provider_call_made": warm.get("provider_call_made") is True,
        "audio_turns_attempted": int(warm.get("audio_turns_attempted", 0) or 0),
        "audio_turns_completed": int(warm.get("audio_turns_completed", 0) or 0),
        "warmup_turn_latency_seconds": next(
            (
                turn.get("user_turn_end_to_first_agent_audio_seconds")
                for turn in warm.get("turns", [])
                if isinstance(turn, dict) and turn.get("warmup_turn") is True
            ),
            None,
        ),
        "measured_warm_turn_count": len(latencies),
        "warm_p50_first_agent_audio_latency_seconds": p50,
        "warm_p90_first_agent_audio_latency_seconds": p90,
        "minimum_latency_seconds": rounded(min(latencies)) if latencies else None,
        "maximum_latency_seconds": rounded(max(latencies)) if latencies else None,
        "warm_latencies_seconds": latencies,
        "tool_request_count": int(warm.get("local_http_tool_request_count", 0) or 0),
        "tool_response_followed_count": len(
            [
                turn
                for turn in warm.get("turns", [])
                if isinstance(turn, dict) and turn.get("tool_response_followed") is True
            ]
        ),
        "product_truth_drift_count": int(warm.get("product_truth_drift_count", 0) or 0),
        "fake_side_effect_count": int(warm.get("fake_side_effect_count", 0) or 0),
        "crm_email_calendar_claim_count": int(warm.get("crm_email_calendar_claim_count", 0) or 0),
        "tool_boundary_passed": tool_boundary_passed,
        "boundary_respect_result": "passed" if tool_boundary_passed else "failed" if warm.get("tool_call_attempted") else "unknown",
        "repeated_synthetic_inputs_used": warm.get("repeated_synthetic_inputs_used") is True,
        "repeated_synthetic_inputs_limit_quality_interpretation": warm.get("repeated_synthetic_inputs_used") is True,
        "repeated_synthetic_inputs_note": warm.get("repeated_synthetic_inputs_note"),
        "audio_quality_promising": prior_review.get("audio_quality_promising") is True or prior_review.get("quality_classification") == "promising",
        "strong_live_target_met": strong,
        "early_demo_target_met": early,
        "live_ready_latency": early,
        "latency_band": latency_band(p50),
        "latency_classification": classification(p50, tool_boundary_passed, session_ok, len(latencies)),
        "benchmark_inconclusive": not session_ok or len(latencies) == 0,
        "live_wiring_allowed": False,
        "production_call_allowed": False,
        "real_customer_data_allowed": False,
        "runtime_behavior_changed": False,
        "response_text_changed": False,
        "final_elevenlabs_replacement_claimed": False,
        "no_final_elevenlabs_replacement_claim": True,
        "decision_logic": [
            "If warm benchmark does not run because prepared audio is missing: prepare manual audio inputs.",
            "If WebSocket/session fails: fix session/WebSocket before more provider usage.",
            "If warm-turn p50 latency <= 2s and tool boundary passes: limited synthetic voice conversation evaluation next.",
            "If warm-turn p50 latency <= 3s and tool boundary passes: thesis-demo synthetic voice evaluation next.",
            "If latency remains > 5s: keep Ultravox as architecture candidate and investigate provider settings/voice/session configuration before more usage.",
            "If quality is promising but latency borderline: test voice/session settings and warm-run repeat once.",
            "If tool boundary fails: do not proceed.",
            "Always keep live wiring, production calls, real customer data, and final ElevenLabs replacement claims disallowed.",
        ],
    }
    result["recommendation"] = recommendation_for(result)
    return result


def build_feasibility_decision(warm: dict[str, Any], audit: dict[str, Any], prior: dict[str, Any]) -> dict[str, Any]:
    return {
        "evaluation_id": "ULTRAVOX-HOSTED-FEASIBILITY-DECISION-001",
        "phase": "4J7",
        "recommendation": audit["recommendation"],
        "blocker": warm.get("blocker"),
        "warm_session_latency_result_id": warm.get("evaluation_id"),
        "warm_session_latency_audit_id": audit.get("evaluation_id"),
        "warm_session_latency_run_status": warm.get("run_status"),
        "provider_call_made": warm.get("provider_call_made") is True,
        "provider_call_attempted": warm.get("provider_call_attempted") is True,
        "sandbox_run": warm.get("sandbox_run") is True,
        "session_created": warm.get("session_created") is True,
        "ultravox_session_created": warm.get("session_created") is True,
        "join_url_received": warm.get("join_url_received") is True,
        "websocket_connected": warm.get("websocket_connected") is True,
        "audio_turns_attempted": warm.get("audio_turns_attempted"),
        "audio_turns_completed": warm.get("audio_turns_completed"),
        "warm_measured_turn_count": audit.get("measured_warm_turn_count"),
        "warm_p50_first_agent_audio_latency_seconds": audit.get("warm_p50_first_agent_audio_latency_seconds"),
        "warm_p90_first_agent_audio_latency_seconds": audit.get("warm_p90_first_agent_audio_latency_seconds"),
        "minimum_latency_seconds": audit.get("minimum_latency_seconds"),
        "maximum_latency_seconds": audit.get("maximum_latency_seconds"),
        "tool_request_count": audit.get("tool_request_count"),
        "tool_call_attempted": warm.get("tool_call_attempted") is True,
        "tool_call_succeeded": warm.get("tool_call_succeeded") is True,
        "tool_boundary_passed": audit.get("tool_boundary_passed"),
        "tool_boundary_enforced": audit.get("tool_boundary_passed"),
        "project_tool_called": audit.get("tool_request_count", 0) > 0,
        "response_follows_project_tool": audit.get("tool_response_followed_count", 0) > 0,
        "product_truth_drift_count": audit.get("product_truth_drift_count"),
        "fake_side_effect_count": audit.get("fake_side_effect_count"),
        "crm_email_calendar_claim_count": audit.get("crm_email_calendar_claim_count"),
        "strong_live_target_met": audit.get("strong_live_target_met"),
        "early_demo_target_met": audit.get("early_demo_target_met"),
        "live_ready_latency": audit.get("live_ready_latency"),
        "latency_classification": audit.get("latency_classification"),
        "repeated_synthetic_inputs_limit_quality_interpretation": audit.get("repeated_synthetic_inputs_limit_quality_interpretation"),
        "live_wiring_allowed": False,
        "production_call_allowed": False,
        "real_customer_data_allowed": False,
        "memory_ownership_decision": "project_runtime_owns_canonical_memory",
        "sales_brain_ownership_decision": "project_runtime_owns_sales_brain_and_campaign_truth",
        "ultravox_product_truth_owner": False,
        "side_effects_allowed": False,
        "runtime_behavior_changed": False,
        "response_text_changed": False,
        "final_elevenlabs_replacement_claimed": False,
        "no_final_elevenlabs_replacement_claim": True,
        "previous_recommendation": prior.get("recommendation"),
        "decision_logic": audit["decision_logic"],
    }


def build_review_decision(warm: dict[str, Any], audit: dict[str, Any], prior: dict[str, Any]) -> dict[str, Any]:
    return {
        "evaluation_id": "ULTRAVOX-AUDIO-SANDBOX-REVIEW-DECISION-001",
        "phase": "4J7",
        "recommendation": audit["recommendation"],
        "warm_session_latency_result_id": warm.get("evaluation_id"),
        "warm_session_latency_audit_id": audit.get("evaluation_id"),
        "manual_listening_review_status": prior.get("manual_listening_review_status"),
        "audio_quality_promising": audit.get("audio_quality_promising"),
        "quality_classification": prior.get("quality_classification"),
        "current_observed_latency_seconds": prior.get("current_observed_latency_seconds"),
        "warm_p50_first_agent_audio_latency_seconds": audit.get("warm_p50_first_agent_audio_latency_seconds"),
        "warm_p90_first_agent_audio_latency_seconds": audit.get("warm_p90_first_agent_audio_latency_seconds"),
        "warm_measured_turn_count": audit.get("measured_warm_turn_count"),
        "needs_warm_turn_benchmark": audit.get("benchmark_inconclusive") is True,
        "tool_boundary_passed": audit.get("tool_boundary_passed"),
        "transcript_quality_passed": prior.get("transcript_quality_passed"),
        "product_truth_drift_count": audit.get("product_truth_drift_count"),
        "fake_side_effect_count": audit.get("fake_side_effect_count"),
        "crm_email_calendar_claim_count": audit.get("crm_email_calendar_claim_count"),
        "strong_live_target_met": audit.get("strong_live_target_met"),
        "early_demo_target_met": audit.get("early_demo_target_met"),
        "live_ready_latency": audit.get("live_ready_latency"),
        "latency_classification": audit.get("latency_classification"),
        "benchmark_provider_call_made": warm.get("provider_call_made") is True,
        "new_provider_call_made": False,
        "new_audio_generated": False,
        "audio_files_copied": False,
        "audio_files_committed": False,
        "outbound_phone_call_made": False,
        "real_customer_data_used": False,
        "raw_private_audio_or_transcripts_used": False,
        "next_provider_run_allowed_now": False,
        "live_wiring_allowed": False,
        "production_call_allowed": False,
        "real_customer_data_allowed": False,
        "runtime_behavior_changed": False,
        "response_text_changed": False,
        "final_elevenlabs_replacement_claimed": False,
        "no_final_elevenlabs_replacement_claim": True,
        "secondary_recommendation": "test Ultravox voice/voice-ID options later",
        "voice_id_alignment_needed": True,
        "voice_selection_limitation_noted": True,
        "decision_logic": audit["decision_logic"],
    }


def render_audit_report(result: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# ULTRAVOX-WARM-SESSION-LATENCY-AUDIT-001",
            "",
            f"Session created: `{str(result['session_created']).lower()}`",
            f"WebSocket connected: `{str(result['websocket_connected']).lower()}`",
            f"Warmup turn latency seconds: `{result['warmup_turn_latency_seconds']}`",
            f"Warm measured turn count: `{result['measured_warm_turn_count']}`",
            f"Warm p50 first-agent-audio latency seconds: `{result['warm_p50_first_agent_audio_latency_seconds']}`",
            f"Warm p90 first-agent-audio latency seconds: `{result['warm_p90_first_agent_audio_latency_seconds']}`",
            f"Minimum latency seconds: `{result['minimum_latency_seconds']}`",
            f"Maximum latency seconds: `{result['maximum_latency_seconds']}`",
            f"Tool request count: `{result['tool_request_count']}`",
            f"Tool response followed count: `{result['tool_response_followed_count']}`",
            f"Product truth drift count: `{result['product_truth_drift_count']}`",
            f"Fake side effect count: `{result['fake_side_effect_count']}`",
            f"CRM/email/calendar claim count: `{result['crm_email_calendar_claim_count']}`",
            f"Tool boundary passed: `{str(result['tool_boundary_passed']).lower()}`",
            f"Boundary respect result: `{result['boundary_respect_result']}`",
            f"Repeated synthetic inputs limit quality interpretation: `{str(result['repeated_synthetic_inputs_limit_quality_interpretation']).lower()}`",
            f"Strong live target met: `{str(result['strong_live_target_met']).lower()}`",
            f"Early demo target met: `{str(result['early_demo_target_met']).lower()}`",
            f"Live-ready latency: `{str(result['live_ready_latency']).lower()}`",
            f"Latency classification: `{result['latency_classification']}`",
            f"Decision recommendation: `{result['recommendation']}`",
            f"Live wiring allowed: `{str(result['live_wiring_allowed']).lower()}`",
            f"Production call allowed: `{str(result['production_call_allowed']).lower()}`",
            f"Real customer data allowed: `{str(result['real_customer_data_allowed']).lower()}`",
            f"Final ElevenLabs replacement claimed: `{str(result['final_elevenlabs_replacement_claimed']).lower()}`",
            "",
        ]
    )


def render_feasibility_report(decision: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# ULTRAVOX-HOSTED-FEASIBILITY-DECISION-001",
            "",
            f"Recommendation: `{decision['recommendation']}`",
            f"Blocker: `{decision['blocker']}`",
            f"Warm-session latency run status: `{decision['warm_session_latency_run_status']}`",
            f"Provider call made: `{str(decision['provider_call_made']).lower()}`",
            f"Ultravox session created: `{str(decision['ultravox_session_created']).lower()}`",
            f"Join URL received: `{str(decision['join_url_received']).lower()}`",
            f"WebSocket connected: `{str(decision['websocket_connected']).lower()}`",
            f"Audio turns attempted: `{decision['audio_turns_attempted']}`",
            f"Audio turns completed: `{decision['audio_turns_completed']}`",
            f"Warm measured turn count: `{decision['warm_measured_turn_count']}`",
            f"Warm p50 first-agent-audio latency seconds: `{decision['warm_p50_first_agent_audio_latency_seconds']}`",
            f"Warm p90 first-agent-audio latency seconds: `{decision['warm_p90_first_agent_audio_latency_seconds']}`",
            f"Tool request count: `{decision['tool_request_count']}`",
            f"Tool boundary passed: `{str(decision['tool_boundary_passed']).lower()}`",
            f"Project tool called: `{str(decision['project_tool_called']).lower()}`",
            f"Response follows project tool: `{str(decision['response_follows_project_tool']).lower()}`",
            f"Product truth drift count: `{decision['product_truth_drift_count']}`",
            f"Fake side effect count: `{decision['fake_side_effect_count']}`",
            f"Strong live target met: `{str(decision['strong_live_target_met']).lower()}`",
            f"Early demo target met: `{str(decision['early_demo_target_met']).lower()}`",
            f"Latency classification: `{decision['latency_classification']}`",
            f"Live wiring allowed: `{str(decision['live_wiring_allowed']).lower()}`",
            f"Production call allowed: `{str(decision['production_call_allowed']).lower()}`",
            f"Real customer data allowed: `{str(decision['real_customer_data_allowed']).lower()}`",
            f"Runtime behavior changed: `{str(decision['runtime_behavior_changed']).lower()}`",
            f"Response text changed: `{str(decision['response_text_changed']).lower()}`",
            f"Final ElevenLabs replacement claimed: `{str(decision['final_elevenlabs_replacement_claimed']).lower()}`",
            "",
            "Project runtime owns canonical memory.",
            "Project runtime owns the sales brain and campaign truth.",
            "",
        ]
    )


def render_review_report(decision: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# ULTRAVOX-AUDIO-SANDBOX-REVIEW-DECISION-001",
            "",
            f"Recommendation: `{decision['recommendation']}`",
            f"Manual listening review status: `{decision['manual_listening_review_status']}`",
            f"Warm measured turn count: `{decision['warm_measured_turn_count']}`",
            f"Warm p50 first-agent-audio latency seconds: `{decision['warm_p50_first_agent_audio_latency_seconds']}`",
            f"Warm p90 first-agent-audio latency seconds: `{decision['warm_p90_first_agent_audio_latency_seconds']}`",
            f"Tool boundary passed: `{str(decision['tool_boundary_passed']).lower()}`",
            f"Transcript quality passed: `{str(decision['transcript_quality_passed']).lower()}`",
            f"Strong live target met: `{str(decision['strong_live_target_met']).lower()}`",
            f"Early demo target met: `{str(decision['early_demo_target_met']).lower()}`",
            f"Latency classification: `{decision['latency_classification']}`",
            f"Next provider run allowed now: `{str(decision['next_provider_run_allowed_now']).lower()}`",
            f"Live wiring allowed: `{str(decision['live_wiring_allowed']).lower()}`",
            f"Production call allowed: `{str(decision['production_call_allowed']).lower()}`",
            f"Real customer data allowed: `{str(decision['real_customer_data_allowed']).lower()}`",
            f"Runtime behavior changed: `{str(decision['runtime_behavior_changed']).lower()}`",
            f"Response text changed: `{str(decision['response_text_changed']).lower()}`",
            f"Secondary recommendation: `{decision['secondary_recommendation']}`",
            f"Final ElevenLabs replacement claimed: `{str(decision['final_elevenlabs_replacement_claimed']).lower()}`",
            "",
        ]
    )


def main() -> None:
    warm = load_json(WARM_RESULT_PATH)
    prior_review = load_json(PRIOR_REVIEW_DECISION_PATH)
    prior_feasibility = load_json(PRIOR_FEASIBILITY_DECISION_PATH)
    result = build_result(warm, prior_review)
    feasibility = build_feasibility_decision(warm, result, prior_feasibility)
    review = build_review_decision(warm, result, prior_review)
    write_json(RESULT_PATH, result)
    write_text(REPORT_PATH, render_audit_report(result))
    write_json(FEASIBILITY_RESULT_PATH, feasibility)
    write_text(FEASIBILITY_REPORT_PATH, render_feasibility_report(feasibility))
    write_json(REVIEW_RESULT_PATH, review)
    write_text(REVIEW_REPORT_PATH, render_review_report(review))
    print(json.dumps({"recommendation": result["recommendation"], "latency_classification": result["latency_classification"]}, indent=2))


if __name__ == "__main__":
    main()
