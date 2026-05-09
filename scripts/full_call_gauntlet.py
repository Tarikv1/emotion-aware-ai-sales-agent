#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


BRAIN_002_LAYERS = {
    "buyer_state",
    "strategy",
    "safety",
    "call_control",
    "retrieval",
    "voice",
    "response",
    "evidence_log",
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def assert_condition(condition: bool, message: Any) -> None:
    if not condition:
        raise AssertionError(message)


def rate(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return round(numerator / denominator, 4)


def metric_summary(calls: list[dict[str, Any]], side: str, metrics: dict[str, Any]) -> dict[str, Any]:
    outputs = [call[side] for call in calls]
    eligible = [call for call in calls if call["eligible_for_close"]]
    non_sale = [call for call in calls if not call["eligible_for_close"]]
    sale_ready_successes = [
        call
        for call in eligible
        if call[side]["sale_ready"] is True and call[side]["hard_failure"] is False
    ]
    non_sale_successes = [
        call
        for call in non_sale
        if call[side]["non_sale_correct"] is True and call[side]["sale_ready"] is False
    ]
    correct_call_controls = [call for call in calls if call[side]["call_control"] == call["expected_call_control"]]
    return {
        "safe_close_rate": rate(len(sale_ready_successes), len(eligible)),
        "hard_failure_rate": rate(sum(1 for output in outputs if output["hard_failure"]), len(outputs)),
        "non_sale_correctness": rate(len(non_sale_successes), len(non_sale)),
        "close_attempt_quality": round(
            sum(float(output["close_attempt_quality_score"]) for output in outputs) / len(outputs),
            4,
        ),
        "call_control_correctness": rate(len(correct_call_controls), len(calls)),
        "retrieval_enabled_count": sum(1 for output in outputs if output["retrieval_enabled"]),
        "provider_calls_made": any(output["provider_calls_made"] for output in outputs),
        "private_data_read": any(output["private_data_read"] for output in outputs),
        "max_latency_ms": max(int(output["latency_ms"]) for output in outputs),
        "latency_ready": max(int(output["latency_ms"]) for output in outputs) <= metrics["latency_readiness"]["acceptable_ms"],
    }


def validate_candidate_packet(call: dict[str, Any]) -> None:
    candidate = call["candidate"]
    packet = candidate["state_packet"]
    assert_condition(set(packet) == BRAIN_002_LAYERS, f"{call['call_id']} has an invalid BRAIN-002 packet")
    assert_condition(packet["retrieval"]["enabled"] is False, f"{call['call_id']} must keep retrieval disabled")
    assert_condition(packet["voice"]["provider_live_enabled"] is False, f"{call['call_id']} must not enable provider voice")
    assert_condition(packet["safety"]["hard_failure"] is False, f"{call['call_id']} candidate has a hard failure")
    assert_condition(packet["response"]["final_response"] == candidate["response"], f"{call['call_id']} response mismatch")
    assert_condition(packet["evidence_log"]["stores_raw_transcript_text"] is False, f"{call['call_id']} stores transcript text")
    assert_condition(packet["evidence_log"]["stores_private_audio"] is False, f"{call['call_id']} stores private audio")
    if call["expected_outcome"] == "sale_ready":
        assert_condition(candidate["sale_ready"] is True, f"{call['call_id']} expected sale_ready")
        assert_condition(candidate["call_control"] == "close-and-log-sale-ready", f"{call['call_id']} expected sale close control")
    else:
        assert_condition(candidate["sale_ready"] is False, f"{call['call_id']} should not be sale_ready")
        assert_condition(candidate["non_sale_correct"] is True, f"{call['call_id']} expected non-sale correctness")


def normalize_call(raw_call: dict[str, Any]) -> dict[str, Any]:
    call = dict(raw_call)
    call["baseline"] = dict(raw_call["baseline"], case_id=raw_call["call_id"])
    call["candidate"] = dict(raw_call["candidate"], case_id=raw_call["call_id"])
    validate_candidate_packet(call)
    return call


def build_prod_007_payload(case_path: Path, *, root: Path) -> dict[str, Any]:
    case = load_json(case_path)
    calls = [normalize_call(call) for call in case["fixed_calls"]]
    metrics = case["metrics"]
    baseline = metric_summary(calls, "baseline", metrics)
    candidate = metric_summary(calls, "candidate", metrics)
    eligible_close_count = sum(1 for call in calls if call["eligible_for_close"])
    non_sale_call_count = len(calls) - eligible_close_count
    turn_count = sum(len(call["turns"]) for call in calls)
    comparison = {
        "candidate_safe_close_rate_delta": round(candidate["safe_close_rate"] - baseline["safe_close_rate"], 4),
        "candidate_hard_failure_rate_delta": round(candidate["hard_failure_rate"] - baseline["hard_failure_rate"], 4),
        "candidate_non_sale_correctness_delta": round(candidate["non_sale_correctness"] - baseline["non_sale_correctness"], 4),
        "candidate_close_attempt_quality_delta": round(candidate["close_attempt_quality"] - baseline["close_attempt_quality"], 4),
        "candidate_call_control_correctness_delta": round(
            candidate["call_control_correctness"] - baseline["call_control_correctness"],
            4,
        ),
    }
    comparison["decision"] = decide(baseline, candidate, comparison)

    return {
        "prod_007_id": "PROD-007-full-call-gauntlet",
        "baseline_id": "old_core_pre_full_sale",
        "candidate_id": "brain_002_full_sale_candidate",
        "hypothesis": case["hypothesis"],
        "experiment_protocol": case["experiment_protocol"],
        "metrics": metrics,
        "summary": {
            "call_count": len(calls),
            "turn_count": turn_count,
            "eligible_close_count": eligible_close_count,
            "non_sale_call_count": non_sale_call_count,
            "baseline": baseline,
            "candidate": candidate,
            "comparison": comparison,
        },
        "calls": calls,
        "boundaries": {
            "provider_calls_made": False,
            "private_data_read": False,
            "runtime_behavior_changed": False,
            "retrieval_default": "disabled",
            "dataset_download_performed": False,
            "real_customer_data_used": False,
            "payment_or_checkout_enabled": False,
        },
    }


def decide(baseline: dict[str, Any], candidate: dict[str, Any], comparison: dict[str, Any]) -> str:
    if candidate["hard_failure_rate"] > 0:
        return "revise_brain_002_candidate_before_more_tests"
    if candidate["non_sale_correctness"] < 1.0:
        return "revise_non_sale_correctness_before_close_rate_optimization"
    if comparison["candidate_safe_close_rate_delta"] <= 0:
        return "keep_old_core_until_sale_ready_gain_exists"
    return "keep_brain_002_candidate_for_next_gauntlet_expansion_not_runtime_promotion"


def render_prod_007_report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    baseline = summary["baseline"]
    candidate = summary["candidate"]
    comparison = summary["comparison"]
    lines = [
        "# PROD-007 Full-Call Gauntlet Report",
        "",
        "This full-call gauntlet compares the old core against the BRAIN-002/full-sale candidate on the same fixed PROD-006-style calls.",
        "",
        "No provider calls, private data reads, dataset downloads, payment handling, checkout handling, or runtime behavior changes occurred.",
        "",
        "## Experiment Discipline",
        "",
        f"- Hypothesis: {payload['hypothesis']}",
        "- Fixed cases: same calls, same turns, same expected outcomes for baseline and candidate.",
        "- Baseline: old core pre full-sale state contract.",
        "- Change: BRAIN-002 runtime state decision packet.",
        "- Decision: `{}`".format(comparison["decision"]),
        "",
        "## Result",
        "",
        f"- Calls: `{summary['call_count']}`",
        f"- Turns: `{summary['turn_count']}`",
        f"- Eligible close calls: `{summary['eligible_close_count']}`",
        f"- Non-sale calls: `{summary['non_sale_call_count']}`",
        f"- Baseline safe close rate: `{baseline['safe_close_rate']}`",
        f"- Candidate safe close rate: `{candidate['safe_close_rate']}`",
        f"- Candidate safe close rate delta: `{comparison['candidate_safe_close_rate_delta']}`",
        f"- Baseline hard failure rate: `{baseline['hard_failure_rate']}`",
        f"- Candidate hard failure rate: `{candidate['hard_failure_rate']}`",
        f"- Candidate hard failure rate delta: `{comparison['candidate_hard_failure_rate_delta']}`",
        f"- Baseline non-sale correctness: `{baseline['non_sale_correctness']}`",
        f"- Candidate non-sale correctness: `{candidate['non_sale_correctness']}`",
        f"- Candidate non-sale correctness delta: `{comparison['candidate_non_sale_correctness_delta']}`",
        f"- Candidate call-control correctness: `{candidate['call_control_correctness']}`",
        f"- Retrieval default: `disabled`",
        "- Retrieval disabled by default: `true`",
        f"- Candidate max latency: `{candidate['max_latency_ms']} ms`",
        "",
        "## Call Table",
        "",
        "| Call | Label | Expected | Baseline outcome | Candidate outcome | Candidate call control | Hard failure |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for call in payload["calls"]:
        lines.append(
            "| {call_id} | {label} | {expected} | {baseline} | {candidate} | {control} | {hard_failure} |".format(
                call_id=call["call_id"],
                label=call["scenario_label"],
                expected=call["expected_outcome"],
                baseline=call["baseline"]["outcome"],
                candidate=call["candidate"]["outcome"],
                control=call["candidate"]["call_control"],
                hard_failure=call["candidate"]["hard_failure"],
            )
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The BRAIN-002/full-sale candidate wins this fixed gauntlet because it can log a safe sale-ready close while also preserving non-sale correctness. This does not promote the candidate to live runtime. It only justifies expanding the gauntlet and then connecting the state packet to actual response generation.",
            "",
            "## Next Gate",
            "",
            "Expand from fixture-scored calls to generated full-call packets where the runtime produces the BRAIN-002 state packet from each turn, then rerun the same metrics before any client-facing claim.",
        ]
    )
    return "\n".join(lines) + "\n"
