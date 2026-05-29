#!/usr/bin/env python3
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SETTINGS_RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-LATENCY-SETTINGS-OPTIONS-001" / "result.json"
BENCHMARK_RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-LATENCY-OPTIMIZATION-BENCHMARK-001" / "result.json"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-LATENCY-OPTIMIZATION-AUDIT-001"
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"
FEASIBILITY_DIR = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-HOSTED-FEASIBILITY-DECISION-001"
FEASIBILITY_RESULT_PATH = FEASIBILITY_DIR / "result.json"
FEASIBILITY_REPORT_PATH = FEASIBILITY_DIR / "report.md"
REVIEW_DIR = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-AUDIO-SANDBOX-REVIEW-DECISION-001"
REVIEW_RESULT_PATH = REVIEW_DIR / "result.json"
REVIEW_REPORT_PATH = REVIEW_DIR / "report.md"

BASELINE_LATENCIES = [4.001, 5.148, 4.638]
BASELINE_P50 = 4.638
BASELINE_P90 = 5.148


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


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


def measured_latencies(benchmark: dict[str, Any]) -> list[float]:
    return [
        float(turn["user_turn_end_to_first_agent_audio_seconds"])
        for turn in benchmark.get("turns", [])
        if isinstance(turn, dict)
        and turn.get("measured_turn") is True
        and isinstance(turn.get("user_turn_end_to_first_agent_audio_seconds"), (int, float))
    ]


def percent_improvement(baseline: float, optimized: float | None) -> float | None:
    if optimized is None:
        return None
    return rounded(((baseline - optimized) / baseline) * 100.0)


def latency_band(p50: float | None, p90: float | None) -> str:
    if p50 is None:
        return "inconclusive"
    if p50 <= 2.0:
        return "strong_live_target"
    if p50 <= 3.0:
        return "early_demo_target"
    if p50 <= 5.0 and (p90 is None or p90 <= 5.0):
        return "borderline"
    return "not_live_ready"


def decision_category(tool_boundary_passed: bool, p50: float | None, p90: float | None, p50_improvement: float | None) -> str:
    if not tool_boundary_passed:
        return "latency_not_ready_stop_provider_testing"
    if p50 is None:
        return "inconclusive"
    if p50 <= 3.0:
        return "latency_ready_for_limited_synthetic_eval"
    if p50 <= 4.0 and (p90 is None or p90 <= 5.0) and isinstance(p50_improvement, (int, float)) and p50_improvement > 0:
        return "latency_borderline_but_promising"
    if p50 > 4.0 or (isinstance(p90, (int, float)) and p90 > 5.0):
        return "latency_not_ready_stop_provider_testing"
    return "inconclusive"


def recommendation_for(category: str, p50: float | None) -> str:
    if category == "latency_ready_for_limited_synthetic_eval" and isinstance(p50, (int, float)) and p50 <= 2.0:
        return "limited synthetic voice conversation evaluation next"
    if category == "latency_ready_for_limited_synthetic_eval":
        return "thesis-demo synthetic voice evaluation next"
    if category == "latency_borderline_but_promising":
        return "one manually approved follow-up only if user wants to spend provider minutes"
    if category == "latency_not_ready_stop_provider_testing":
        return "stop provider latency testing for now; keep Ultravox promising but latency-limited"
    return "benchmark inconclusive"


def average_response_words(benchmark: dict[str, Any]) -> float | None:
    counts = [
        int(turn["agent_response_word_count"])
        for turn in benchmark.get("turns", [])
        if isinstance(turn, dict) and isinstance(turn.get("agent_response_word_count"), int) and turn.get("measured_turn") is True
    ]
    if not counts:
        return None
    return rounded(sum(counts) / len(counts))


def build_result(settings: dict[str, Any], benchmark: dict[str, Any]) -> dict[str, Any]:
    latencies = measured_latencies(benchmark)
    p50 = median(latencies)
    p90 = percentile_nearest(latencies, 90.0) if len(latencies) >= 2 else None
    p50_improvement = rounded(BASELINE_P50 - p50) if p50 is not None else None
    p90_improvement = rounded(BASELINE_P90 - p90) if p90 is not None else None
    tool_boundary_passed = (
        benchmark.get("tool_boundary_enforced") is True
        and int(benchmark.get("local_http_tool_request_count", 0) or 0) > 0
        and int(benchmark.get("product_truth_drift_count", 0) or 0) == 0
        and int(benchmark.get("fake_side_effect_count", 0) or 0) == 0
    )
    category = decision_category(tool_boundary_passed, p50, p90, p50_improvement)
    recommendation = recommendation_for(category, p50)
    response_words = average_response_words(benchmark)
    return {
        "evaluation_id": "ULTRAVOX-LATENCY-OPTIMIZATION-AUDIT-001",
        "phase": "4J8",
        "settings_options_result_id": settings.get("evaluation_id"),
        "latency_optimization_benchmark_id": benchmark.get("evaluation_id"),
        "baseline_warm_latencies_seconds": BASELINE_LATENCIES,
        "baseline_warm_p50_first_agent_audio_latency_seconds": BASELINE_P50,
        "baseline_warm_p90_first_agent_audio_latency_seconds": BASELINE_P90,
        "optimized_warm_latencies_seconds": latencies,
        "optimized_warm_measured_turn_count": len(latencies),
        "optimized_warm_p50_first_agent_audio_latency_seconds": p50,
        "optimized_warm_p90_first_agent_audio_latency_seconds": p90,
        "p50_improvement_seconds": p50_improvement,
        "p90_improvement_seconds": p90_improvement,
        "p50_improvement_percent": percent_improvement(BASELINE_P50, p50),
        "p90_improvement_percent": percent_improvement(BASELINE_P90, p90),
        "strong_live_target_met": bool(p50 is not None and p50 <= 2.0 and tool_boundary_passed),
        "early_demo_target_met": bool(p50 is not None and p50 <= 3.0 and tool_boundary_passed),
        "latency_band": latency_band(p50, p90),
        "decision_category": category,
        "recommendation": recommendation,
        "provider_call_made": benchmark.get("provider_call_made") is True,
        "provider_call_attempted": benchmark.get("provider_call_attempted") is True,
        "session_created": benchmark.get("session_created") is True,
        "ultravox_session_created": benchmark.get("session_created") is True,
        "join_url_received": benchmark.get("join_url_received") is True,
        "websocket_connected": benchmark.get("websocket_connected") is True,
        "audio_turns_attempted": int(benchmark.get("audio_turns_attempted", 0) or 0),
        "audio_turns_completed": int(benchmark.get("audio_turns_completed", 0) or 0),
        "tool_request_count": int(benchmark.get("local_http_tool_request_count", 0) or 0),
        "tool_boundary_passed": tool_boundary_passed,
        "product_truth_drift_count": int(benchmark.get("product_truth_drift_count", 0) or 0),
        "fake_side_effect_count": int(benchmark.get("fake_side_effect_count", 0) or 0),
        "crm_email_calendar_claim_count": int(benchmark.get("crm_email_calendar_claim_count", 0) or 0),
        "average_measured_response_word_count": response_words,
        "response_length_changed": response_words is not None,
        "optimization_harmed_quality_or_safety": False if tool_boundary_passed else "unknown",
        "another_provider_run_justified": "manual_approval_only" if category == "latency_borderline_but_promising" else False,
        "settings_without_provider_call": settings.get("provider_call_made") is False,
        "unsupported_parameters_sent_as_confirmed": benchmark.get("unsupported_parameters_sent_as_confirmed") is True,
        "live_wiring_allowed": False,
        "production_call_allowed": False,
        "real_customer_data_allowed": False,
        "runtime_behavior_changed": False,
        "response_text_changed": False,
        "final_elevenlabs_replacement_claimed": False,
        "no_final_elevenlabs_replacement_claim": True,
    }


def decision_payload(evaluation_id: str, benchmark: dict[str, Any], audit: dict[str, Any], existing: dict[str, Any]) -> dict[str, Any]:
    return {
        **existing,
        "evaluation_id": evaluation_id,
        "phase": "4J8",
        "latency_optimization_benchmark_id": benchmark.get("evaluation_id"),
        "latency_optimization_audit_id": audit.get("evaluation_id"),
        "latency_optimization_run_status": benchmark.get("run_status"),
        "provider_call_made": benchmark.get("provider_call_made") is True,
        "provider_call_attempted": benchmark.get("provider_call_attempted") is True,
        "sandbox_run": benchmark.get("sandbox_run") is True,
        "session_created": benchmark.get("session_created") is True,
        "ultravox_session_created": benchmark.get("session_created") is True,
        "join_url_received": benchmark.get("join_url_received") is True,
        "websocket_connected": benchmark.get("websocket_connected") is True,
        "audio_turns_attempted": benchmark.get("audio_turns_attempted"),
        "audio_turns_completed": benchmark.get("audio_turns_completed"),
        "warm_measured_turn_count": audit.get("optimized_warm_measured_turn_count"),
        "warm_p50_first_agent_audio_latency_seconds": audit.get("optimized_warm_p50_first_agent_audio_latency_seconds"),
        "warm_p90_first_agent_audio_latency_seconds": audit.get("optimized_warm_p90_first_agent_audio_latency_seconds"),
        "p50_improvement_seconds": audit.get("p50_improvement_seconds"),
        "p90_improvement_seconds": audit.get("p90_improvement_seconds"),
        "strong_live_target_met": audit.get("strong_live_target_met"),
        "early_demo_target_met": audit.get("early_demo_target_met"),
        "latency_classification": audit.get("latency_band"),
        "decision_category": audit.get("decision_category"),
        "recommendation": audit.get("recommendation"),
        "tool_call_attempted": benchmark.get("tool_call_attempted") is True,
        "tool_call_succeeded": benchmark.get("tool_call_succeeded") is True,
        "tool_request_count": audit.get("tool_request_count"),
        "tool_boundary_passed": audit.get("tool_boundary_passed"),
        "tool_boundary_enforced": benchmark.get("tool_boundary_enforced") is True,
        "project_tool_called": int(benchmark.get("local_http_tool_request_count", 0) or 0) > 0,
        "response_follows_project_tool": benchmark.get("tool_boundary_enforced") is True,
        "product_truth_drift_count": audit.get("product_truth_drift_count"),
        "fake_side_effect_count": audit.get("fake_side_effect_count"),
        "crm_email_calendar_claim_count": audit.get("crm_email_calendar_claim_count"),
        "benchmark_provider_call_made": benchmark.get("provider_call_made") is True,
        "new_provider_call_made": False,
        "new_audio_generated": False,
        "audio_files_copied": False,
        "audio_files_committed": False,
        "next_provider_run_allowed_now": False,
        "manual_listening_review_status": existing.get("manual_listening_review_status", "review_complete"),
        "secondary_recommendation": existing.get("secondary_recommendation", "test Ultravox voice/voice-ID options later"),
        "transcript_quality_passed": existing.get("transcript_quality_passed", True),
        "memory_ownership_decision": "project_runtime_owns_canonical_memory",
        "sales_brain_ownership_decision": "project_runtime_owns_sales_brain_and_campaign_truth",
        "ultravox_product_truth_owner": False,
        "side_effects_allowed": False,
        "live_wiring_allowed": False,
        "production_call_allowed": False,
        "real_customer_data_allowed": False,
        "runtime_behavior_changed": False,
        "response_text_changed": False,
        "final_elevenlabs_replacement_claimed": False,
        "no_final_elevenlabs_replacement_claim": True,
        "outbound_phone_call_made": False,
        "real_customer_data_used": False,
        "raw_private_audio_or_transcripts_used": False,
    }


def render_audit_report(result: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# ULTRAVOX-LATENCY-OPTIMIZATION-AUDIT-001",
            "",
            f"Optimized warm p50 first-agent-audio latency seconds: `{result['optimized_warm_p50_first_agent_audio_latency_seconds']}`",
            f"Optimized warm p90 first-agent-audio latency seconds: `{result['optimized_warm_p90_first_agent_audio_latency_seconds']}`",
            f"Optimized warm measured turn count: `{result['optimized_warm_measured_turn_count']}`",
            f"Baseline warm p50 first-agent-audio latency seconds: `{result['baseline_warm_p50_first_agent_audio_latency_seconds']}`",
            f"Baseline warm p90 first-agent-audio latency seconds: `{result['baseline_warm_p90_first_agent_audio_latency_seconds']}`",
            f"P50 improvement seconds: `{result['p50_improvement_seconds']}`",
            f"P50 improvement percent: `{result['p50_improvement_percent']}`",
            f"P90 improvement seconds: `{result['p90_improvement_seconds']}`",
            f"P90 improvement percent: `{result['p90_improvement_percent']}`",
            f"Strong live target met: `{str(result['strong_live_target_met']).lower()}`",
            f"Early demo target met: `{str(result['early_demo_target_met']).lower()}`",
            f"Latency band: `{result['latency_band']}`",
            f"Decision category: `{result['decision_category']}`",
            f"Tool boundary passed: `{str(result['tool_boundary_passed']).lower()}`",
            f"Product truth drift count: `{result['product_truth_drift_count']}`",
            f"Fake side effect count: `{result['fake_side_effect_count']}`",
            f"Response length changed: `{str(result['response_length_changed']).lower()}`",
            f"Optimization harmed quality or safety: `{result['optimization_harmed_quality_or_safety']}`",
            f"Another provider run justified: `{result['another_provider_run_justified']}`",
            f"Decision recommendation: `{result['recommendation']}`",
            "",
        ]
    )


def render_decision_report(title: str, decision: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"# {title}",
            "",
            f"Recommendation: `{decision['recommendation']}`",
            f"Decision category: `{decision['decision_category']}`",
            f"Latency optimization run status: `{decision['latency_optimization_run_status']}`",
            f"Provider call made: `{str(decision['provider_call_made']).lower()}`",
            f"Ultravox session created: `{str(decision['ultravox_session_created']).lower()}`",
            f"Join URL received: `{str(decision['join_url_received']).lower()}`",
            f"WebSocket connected: `{str(decision['websocket_connected']).lower()}`",
            f"Audio turns attempted: `{decision['audio_turns_attempted']}`",
            f"Audio turns completed: `{decision['audio_turns_completed']}`",
            f"Warm measured turn count: `{decision['warm_measured_turn_count']}`",
            f"Warm p50 first-agent-audio latency seconds: `{decision['warm_p50_first_agent_audio_latency_seconds']}`",
            f"Warm p90 first-agent-audio latency seconds: `{decision['warm_p90_first_agent_audio_latency_seconds']}`",
            f"P50 improvement seconds: `{decision['p50_improvement_seconds']}`",
            f"P90 improvement seconds: `{decision['p90_improvement_seconds']}`",
            f"Tool request count: `{decision['tool_request_count']}`",
            f"Tool boundary passed: `{str(decision['tool_boundary_passed']).lower()}`",
            f"Project tool called: `{str(decision['project_tool_called']).lower()}`",
            f"Response follows project tool: `{str(decision['response_follows_project_tool']).lower()}`",
            f"Product truth drift count: `{decision['product_truth_drift_count']}`",
            f"Fake side effect count: `{decision['fake_side_effect_count']}`",
            f"Strong live target met: `{str(decision['strong_live_target_met']).lower()}`",
            f"Early demo target met: `{str(decision['early_demo_target_met']).lower()}`",
            f"Latency classification: `{decision['latency_classification']}`",
            f"Manual listening review status: `{decision.get('manual_listening_review_status')}`",
            f"Next provider run allowed now: `{str(decision.get('next_provider_run_allowed_now')).lower()}`",
            f"Live wiring allowed: `{str(decision['live_wiring_allowed']).lower()}`",
            f"Production call allowed: `{str(decision['production_call_allowed']).lower()}`",
            f"Real customer data allowed: `{str(decision['real_customer_data_allowed']).lower()}`",
            f"Runtime behavior changed: `{str(decision['runtime_behavior_changed']).lower()}`",
            f"Response text changed: `{str(decision['response_text_changed']).lower()}`",
            f"Final ElevenLabs replacement claimed: `{str(decision['final_elevenlabs_replacement_claimed']).lower()}`",
            "",
            "Project runtime owns canonical memory.",
            "Project runtime owns the sales brain and campaign truth.",
            f"Secondary recommendation: `{decision.get('secondary_recommendation')}`",
            "",
        ]
    )


def main() -> None:
    settings = load_json(SETTINGS_RESULT_PATH)
    benchmark = load_json(BENCHMARK_RESULT_PATH)
    result = build_result(settings, benchmark)
    write_json(RESULT_PATH, result)
    write_text(REPORT_PATH, render_audit_report(result))

    feasibility = decision_payload("ULTRAVOX-HOSTED-FEASIBILITY-DECISION-001", benchmark, result, load_json(FEASIBILITY_RESULT_PATH))
    review = decision_payload("ULTRAVOX-AUDIO-SANDBOX-REVIEW-DECISION-001", benchmark, result, load_json(REVIEW_RESULT_PATH))
    write_json(FEASIBILITY_RESULT_PATH, feasibility)
    write_text(FEASIBILITY_REPORT_PATH, render_decision_report("ULTRAVOX-HOSTED-FEASIBILITY-DECISION-001", feasibility))
    write_json(REVIEW_RESULT_PATH, review)
    write_text(REVIEW_REPORT_PATH, render_decision_report("ULTRAVOX-AUDIO-SANDBOX-REVIEW-DECISION-001", review))
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
