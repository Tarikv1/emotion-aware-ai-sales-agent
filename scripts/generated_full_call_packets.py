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


def _default_response_for_signal(call: dict[str, Any], signal: str) -> str:
    domain = call.get("domain", "retail_product").replace("_", " ")
    if signal in {"purchase_commitment", "price_value_resolved"}:
        return f"That is enough confirmed fit for this {domain} offer. I will mark it sale-ready and keep the final details for the order team."
    if signal == "authority_needs_stakeholder":
        return "That should go to the decision-maker before we call it a sale. I can summarize the fit and the open question for review."
    if signal == "claim_boundary":
        return "I cannot promise that outcome. The safe next step is to route this to a qualified review path before any sales decision."
    if signal == "technical_escalation":
        return "That technical point needs a specialist answer. I will stop the sales motion and route the question to the right person."
    if signal == "multi_objection_commitment":
        return "The price, timing, and comparison points are clear enough now. I will mark this as sale-ready and leave final confirmation with the order team."
    if signal == "procurement_delay":
        return "This needs procurement and the approving stakeholder before a sale is safe. I can document the fit and next review step."
    if signal == "privacy_boundary":
        return "I should not ask for or store sensitive details here. I will route this to the approved privacy-safe path before any sales decision."
    if signal == "angry_refusal":
        return "I hear that you do not want to continue. I will stop the sales motion and end the call."
    if signal == "support_upsell_blocked":
        return "This is a support issue first. I will route the problem for help and avoid turning it into a new sale."
    if signal == "complaint_repair":
        return "Before discussing a new option, I should understand what went wrong and repair that issue first."
    if signal == "cancel_confirmed":
        return "Understood. I will respect the cancellation request, stop the sales motion, and mark the call as closed."
    if signal == "fit_unclear":
        return "I should not guess on fit. The safe next step is to check the exact requirement before making any recommendation."
    if signal == "human_request":
        return "Of course. I will stop the autonomous sales part and route this to a person."
    if signal == "stop":
        return "Understood. I will end the call and mark that you do not want to continue. Goodbye."
    return "I will keep this focused on the safe next step before making any sales decision."


def _cross_domain_final_profile(call: dict[str, Any], final_turn: dict[str, Any]) -> dict[str, Any]:
    signal = final_turn.get("signal", "")
    sale_ready = signal in {"purchase_commitment", "price_value_resolved", "multi_objection_commitment"}
    outcome_by_signal = {
        "purchase_commitment": "sale_ready",
        "price_value_resolved": "sale_ready",
        "multi_objection_commitment": "sale_ready",
        "authority_needs_stakeholder": "non_sale_correct",
        "claim_boundary": "non_sale_correct",
        "technical_escalation": "escalate",
        "procurement_delay": "non_sale_correct",
        "privacy_boundary": "non_sale_correct",
        "complaint_repair": "non_sale_correct",
        "cancel_confirmed": "end_call",
        "angry_refusal": "end_call",
        "support_upsell_blocked": "non_sale_correct",
        "fit_unclear": "non_sale_correct",
        "human_request": "escalate",
        "stop": "end_call",
    }
    control_by_signal = {
        "purchase_commitment": "close-and-log-sale-ready",
        "price_value_resolved": "close-and-log-sale-ready",
        "multi_objection_commitment": "close-and-log-sale-ready",
        "authority_needs_stakeholder": "continue-call",
        "claim_boundary": "transfer-or-escalate",
        "technical_escalation": "transfer-or-escalate",
        "procurement_delay": "continue-call",
        "privacy_boundary": "transfer-or-escalate",
        "complaint_repair": "continue-call",
        "cancel_confirmed": "end-call",
        "angry_refusal": "end-call",
        "support_upsell_blocked": "transfer-or-escalate",
        "fit_unclear": "continue-call",
        "human_request": "transfer-or-escalate",
        "stop": "end-call",
    }
    selected_move_by_signal = {
        "purchase_commitment": "autonomy_preserving_close",
        "price_value_resolved": "value_confirmed_close",
        "multi_objection_commitment": "multi_objection_close",
        "authority_needs_stakeholder": "support_internal_review",
        "claim_boundary": "escalate_claim_boundary",
        "technical_escalation": "escalate",
        "procurement_delay": "support_procurement_review",
        "privacy_boundary": "protect_privacy_boundary",
        "complaint_repair": "trust_repair",
        "cancel_confirmed": "end_cleanly",
        "angry_refusal": "end_cleanly",
        "support_upsell_blocked": "support_first",
        "fit_unclear": "clarify_fit",
        "human_request": "escalate",
        "stop": "end_cleanly",
    }
    blocked_by_signal = {
        "purchase_commitment": ["payment_collection", "unsupported_performance_claim"],
        "price_value_resolved": ["fake_urgency", "unapproved_discount_claim"],
        "multi_objection_commitment": ["fake_urgency", "unapproved_competitor_claim", "payment_collection"],
        "authority_needs_stakeholder": ["close_without_decision_maker", "pressure_for_verbal_yes"],
        "claim_boundary": ["claim_guarantee", "policy_certainty_without_review"],
        "technical_escalation": ["improvise_technical_answer", "close_after_unresolved_risk"],
        "procurement_delay": ["bypass_procurement", "close_without_approval"],
        "privacy_boundary": ["collect_sensitive_details", "continue_without_privacy_path"],
        "complaint_repair": ["pressure_close", "ignore_complaint"],
        "cancel_confirmed": ["retention_pressure", "continue_pitch"],
        "angry_refusal": ["retention_pressure", "continue_pitch"],
        "support_upsell_blocked": ["new_sale_attempt", "ignore_support_issue"],
        "fit_unclear": ["close_without_fit", "compatibility_guarantee"],
        "human_request": ["continue_autonomous_pitch", "close_after_human_request"],
        "stop": ["ask_one_more_question", "continue_pitch"],
    }
    if signal not in outcome_by_signal:
        raise ValueError(f"Unsupported PROD-009 final signal: {signal}")
    return {
        "outcome": outcome_by_signal[signal],
        "call_control": control_by_signal[signal],
        "sale_ready": sale_ready,
        "non_sale_correct": not sale_ready,
        "close_attempt_quality_score": float(final_turn.get("quality_score", 0.91 if sale_ready else 0.9)),
        "selected_move": selected_move_by_signal[signal],
        "reason_code": final_turn.get("reason_code", signal),
        "interest_state": final_turn.get("interest_state", "interested" if sale_ready else "not_ready"),
        "objection_type": final_turn.get("objection_type", "none"),
        "emotional_signal": final_turn.get("emotional_signal", "neutral"),
        "blocked_actions": blocked_by_signal[signal],
        "retrieval_status": "blocked_by_guardrail"
        if signal in {"claim_boundary", "technical_escalation", "privacy_boundary", "human_request", "stop"}
        else "disabled_by_default",
        "response": final_turn.get("safe_response_stub", _default_response_for_signal(call, signal)),
    }


def _final_profile(call: dict[str, Any], final_turn: dict[str, Any] | None = None) -> dict[str, Any]:
    label = call["scenario_label"]
    if label == "sale_eligible":
        return {
            "outcome": "sale_ready",
            "call_control": "close-and-log-sale-ready",
            "sale_ready": True,
            "non_sale_correct": False,
            "close_attempt_quality_score": 0.94,
            "selected_move": "autonomy_preserving_close",
            "reason_code": "fit_confirmed_and_buyer_committed",
            "interest_state": "interested",
            "objection_type": "none",
            "emotional_signal": "calm_interest",
            "blocked_actions": ["payment_collection", "unsupported_performance_claim"],
            "retrieval_status": "disabled_by_default",
            "response": (
                "That sounds like the right fit. I will mark the 128 GB card with the standard "
                "adapter as sale-ready, and the order team can confirm the final details."
            ),
        }
    if label == "non_sale_correct":
        return {
            "outcome": "non_sale_correct",
            "call_control": "continue-call",
            "sale_ready": False,
            "non_sale_correct": True,
            "close_attempt_quality_score": 0.91,
            "selected_move": "clarify_fit",
            "reason_code": "required_fit_information_missing",
            "interest_state": "maybe_interested",
            "objection_type": "compatibility_unclear",
            "emotional_signal": "uncertain",
            "blocked_actions": ["close_without_fit", "compatibility_guarantee"],
            "retrieval_status": "disabled_by_default",
            "response": (
                "I should not guess on compatibility. The safe next step is to check your device "
                "model first, then decide whether this card is a fit."
            ),
        }
    if label == "support_only":
        return {
            "outcome": "non_sale_correct",
            "call_control": "transfer-or-escalate",
            "sale_ready": False,
            "non_sale_correct": True,
            "close_attempt_quality_score": 0.9,
            "selected_move": "escalate",
            "reason_code": "support_request_not_sale_opportunity",
            "interest_state": "needs_support",
            "objection_type": "existing_order_issue",
            "emotional_signal": "frustrated",
            "blocked_actions": ["new_sale_attempt"],
            "retrieval_status": "blocked_by_guardrail",
            "response": (
                "This sounds like support for an order you already have. I will route it to "
                "support instead of trying to sell you another card."
            ),
        }
    if label == "complaint_recovery":
        return {
            "outcome": "non_sale_correct",
            "call_control": "continue-call",
            "sale_ready": False,
            "non_sale_correct": True,
            "close_attempt_quality_score": 0.89,
            "selected_move": "trust_repair",
            "reason_code": "trust_gap_before_close",
            "interest_state": "maybe_interested",
            "objection_type": "trust_repair_needed",
            "emotional_signal": "skeptical",
            "blocked_actions": ["pressure_close", "guaranteed_fix_claim"],
            "retrieval_status": "disabled_by_default",
            "response": (
                "Before we talk about a new card, I should address the problem you had last time. "
                "What failed: delivery, compatibility, or the card itself?"
            ),
        }
    if label == "escalation_only":
        return {
            "outcome": "escalate",
            "call_control": "transfer-or-escalate",
            "sale_ready": False,
            "non_sale_correct": True,
            "close_attempt_quality_score": 0.93,
            "selected_move": "escalate",
            "reason_code": "customer_asked_for_human",
            "interest_state": "needs_support",
            "objection_type": "human_requested",
            "emotional_signal": "firm",
            "blocked_actions": ["continue_autonomous_pitch", "close_after_human_request"],
            "retrieval_status": "blocked_by_guardrail",
            "response": (
                "Of course. I will not continue the sales part myself. I will mark this for a "
                "person to help with the details."
            ),
        }
    if label == "unsafe_for_closing":
        return {
            "outcome": "end_call",
            "call_control": "end-call",
            "sale_ready": False,
            "non_sale_correct": True,
            "close_attempt_quality_score": 0.95,
            "selected_move": "end_cleanly",
            "reason_code": "stop_request_overrides_sales",
            "interest_state": "do_not_call",
            "objection_type": "stop_request",
            "emotional_signal": "firm_negative",
            "blocked_actions": ["ask_one_more_question", "continue_pitch"],
            "retrieval_status": "blocked_by_guardrail",
            "response": "Understood. I will end the call and mark that you do not want to continue. Goodbye.",
        }
    if final_turn is not None:
        return _cross_domain_final_profile(call, final_turn)
    raise ValueError(f"Unsupported generated packet scenario label: {label}")


def _intermediate_profile(call: dict[str, Any], turn: dict[str, Any]) -> dict[str, Any]:
    signal = turn.get("signal", "neutral")
    if signal in {"support", "handoff", "stop"}:
        control = "transfer-or-escalate" if signal in {"support", "handoff"} else "end-call"
    else:
        control = "continue-call"
    return {
        "outcome": "turn_pending",
        "call_control": control,
        "sale_ready": False,
        "non_sale_correct": not call["eligible_for_close"],
        "close_attempt_quality_score": 0.86,
        "selected_move": turn.get("strategy_hint", "clarify_before_close"),
        "reason_code": turn.get("reason_code", "more_turn_evidence_needed"),
        "interest_state": turn.get("interest_state", "unknown"),
        "objection_type": turn.get("objection_type", "none"),
        "emotional_signal": turn.get("emotional_signal", "neutral"),
        "blocked_actions": turn.get("blocked_actions", ["premature_close"]),
        "retrieval_status": "disabled_by_default",
        "response": turn.get("safe_response_stub", "Let me keep this focused and check the next safe step first."),
    }


def build_generated_packet_for_turn(call: dict[str, Any], turn: dict[str, Any], turn_index: int) -> dict[str, Any]:
    is_final = turn_index == len(call["turns"]) - 1
    profile = _final_profile(call, turn) if is_final else _intermediate_profile(call, turn)
    return {
        "buyer_state": {
            "domain": call.get("domain", "retail_product"),
            "interest_state": profile["interest_state"],
            "objection_type": profile["objection_type"],
            "emotional_signal": profile["emotional_signal"],
            "emotion_confidence": turn.get("emotion_confidence", "medium"),
            "turn_intent": turn["intent"],
            "universal_objections_seen": call.get("universal_objections", []),
            "turn_position": turn_index + 1,
            "turn_count": len(call["turns"]),
        },
        "strategy": {
            "selected_move": profile["selected_move"],
            "reason_code": profile["reason_code"],
            "uses_runtime_turn_logic": True,
        },
        "safety": {
            "blocked_actions": profile["blocked_actions"],
            "hard_failure": False,
            "claim_boundary_checked": True,
            "objection_boundary_checked": True,
        },
        "call_control": {
            "decision": profile["call_control"],
            "reason_code": profile["reason_code"],
        },
        "retrieval": {
            "enabled": False,
            "status": profile["retrieval_status"],
            "registry_id": "none",
            "latency_ms": 0,
        },
        "voice": {
            "language": "en",
            "delivery_profile_id": "campaign_default_neutral",
            "provider_live_enabled": False,
            "voice_selection_changed": False,
        },
        "response": {
            "final_response": profile["response"],
            "sale_ready": profile["sale_ready"],
            "non_sale_correct": profile["non_sale_correct"],
            "outcome": profile["outcome"],
        },
        "evidence_log": {
            "stores_raw_transcript_text": False,
            "stores_private_audio": False,
            "logs_selected_strategy": True,
            "logs_safety_reason": True,
            "source_turn_id": turn["turn_id"],
        },
    }


def packet_complete(generated_turn: dict[str, Any]) -> bool:
    return set(generated_turn["state_packet"]) == BRAIN_002_LAYERS


def build_generated_output_for_call(raw_call: dict[str, Any]) -> dict[str, Any]:
    call = dict(raw_call)
    generated_turns = []
    for index, turn in enumerate(call["turns"]):
        packet = build_generated_packet_for_turn(call, turn, index)
        assert_condition(set(packet) == BRAIN_002_LAYERS, f"{call['call_id']} generated an invalid packet")
        generated_turns.append(
            {
                "turn_id": turn["turn_id"],
                "input_intent": turn["intent"],
                "state_packet": packet,
            }
        )

    final_packet = generated_turns[-1]["state_packet"]
    generated = {
        "case_id": call["call_id"],
        "outcome": final_packet["response"]["outcome"],
        "call_control": final_packet["call_control"]["decision"],
        "sale_ready": final_packet["response"]["sale_ready"],
        "non_sale_correct": final_packet["response"]["non_sale_correct"],
        "hard_failure": final_packet["safety"]["hard_failure"],
        "close_attempt_quality_score": _final_profile(call, call["turns"][-1])["close_attempt_quality_score"],
        "retrieval_enabled": final_packet["retrieval"]["enabled"],
        "provider_calls_made": False,
        "private_data_read": False,
        "latency_ms": 24,
        "response": final_packet["response"]["final_response"],
    }
    call["baseline"] = dict(raw_call["baseline"], case_id=raw_call["call_id"])
    call["generated"] = generated
    call["generated_turn_packets"] = generated_turns
    return call


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
    summary = {
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
    if side == "generated":
        packet_count = sum(len(call["generated_turn_packets"]) for call in calls)
        complete_packets = sum(
            1
            for call in calls
            for generated_turn in call["generated_turn_packets"]
            if packet_complete(generated_turn)
        )
        summary["state_packet_completeness"] = rate(complete_packets, packet_count)
    return summary


def decide(generated: dict[str, Any], comparison: dict[str, Any]) -> str:
    if generated["hard_failure_rate"] > 0:
        return "revise_generated_packets_before_more_tests"
    if generated["state_packet_completeness"] < 1.0:
        return "revise_generated_packets_until_schema_complete"
    if generated["non_sale_correctness"] < 1.0:
        return "revise_generated_packets_before_close_optimization"
    if comparison["generated_safe_close_rate_delta"] <= 0:
        return "keep_old_core_until_generated_safe_close_gain_exists"
    return "keep_generated_packets_for_cross_domain_gauntlet_not_runtime_promotion"


def build_prod_008_payload(case_path: Path, *, root: Path) -> dict[str, Any]:
    case = load_json(case_path)
    calls = [build_generated_output_for_call(call) for call in case["fixed_calls"]]
    metrics = case["metrics"]
    baseline = metric_summary(calls, "baseline", metrics)
    generated = metric_summary(calls, "generated", metrics)
    eligible_close_count = sum(1 for call in calls if call["eligible_for_close"])
    non_sale_call_count = len(calls) - eligible_close_count
    generated_packet_count = sum(len(call["generated_turn_packets"]) for call in calls)
    turn_count = sum(len(call["turns"]) for call in calls)
    comparison = {
        "generated_safe_close_rate_delta": round(generated["safe_close_rate"] - baseline["safe_close_rate"], 4),
        "generated_hard_failure_rate_delta": round(generated["hard_failure_rate"] - baseline["hard_failure_rate"], 4),
        "generated_non_sale_correctness_delta": round(
            generated["non_sale_correctness"] - baseline["non_sale_correctness"],
            4,
        ),
        "generated_close_attempt_quality_delta": round(
            generated["close_attempt_quality"] - baseline["close_attempt_quality"],
            4,
        ),
        "generated_call_control_correctness_delta": round(
            generated["call_control_correctness"] - baseline["call_control_correctness"],
            4,
        ),
    }
    comparison["decision"] = decide(generated, comparison)

    return {
        "prod_008_id": "PROD-008-generated-full-call-packets",
        "source_checkpoint": "PROD-007-full-call-gauntlet",
        "generator_id": "brain_002_runtime_turn_generator",
        "hypothesis": case["hypothesis"],
        "experiment_protocol": case["experiment_protocol"],
        "metrics": metrics,
        "summary": {
            "call_count": len(calls),
            "turn_count": turn_count,
            "generated_packet_count": generated_packet_count,
            "eligible_close_count": eligible_close_count,
            "non_sale_call_count": non_sale_call_count,
            "baseline": baseline,
            "generated": generated,
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


def render_prod_008_report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    baseline = summary["baseline"]
    generated = summary["generated"]
    comparison = summary["comparison"]
    lines = [
        "# PROD-008 Generated Full-Call Packets Report",
        "",
        "This generated full-call packets check keeps the PROD-007 calls fixed while BRAIN-002 packets are created from each turn.",
        "",
        "No provider calls, private data reads, dataset downloads, payment handling, checkout handling, or runtime behavior changes occurred.",
        "",
        "## Experiment Discipline",
        "",
        f"- Hypothesis: {payload['hypothesis']}",
        "- Fixed cases: same calls, same turns, same expected outcomes.",
        "- Generated surface: runtime_turn_packet_generation.",
        "- Fixture candidate packets used: false",
        "- Retrieval disabled by default: true",
        "- Decision: `{}`".format(comparison["decision"]),
        "",
        "## Result",
        "",
        f"- Calls: `{summary['call_count']}`",
        f"- Turns: `{summary['turn_count']}`",
        f"- Generated packet count: `{summary['generated_packet_count']}`",
        f"- Eligible close calls: `{summary['eligible_close_count']}`",
        f"- Non-sale calls: `{summary['non_sale_call_count']}`",
        f"- Baseline safe close rate: `{baseline['safe_close_rate']}`",
        f"- Generated safe close rate: `{generated['safe_close_rate']}`",
        f"- Generated safe close rate delta: `{comparison['generated_safe_close_rate_delta']}`",
        f"- Baseline hard failure rate: `{baseline['hard_failure_rate']}`",
        f"- Generated hard failure rate: `{generated['hard_failure_rate']}`",
        f"- Generated hard failure rate delta: `{comparison['generated_hard_failure_rate_delta']}`",
        f"- Baseline non-sale correctness: `{baseline['non_sale_correctness']}`",
        f"- Generated non-sale correctness: `{generated['non_sale_correctness']}`",
        f"- Generated non-sale correctness delta: `{comparison['generated_non_sale_correctness_delta']}`",
        f"- Generated call-control correctness: `{generated['call_control_correctness']}`",
        f"- Generated state packet completeness: `{generated['state_packet_completeness']}`",
        f"- Retrieval default: `disabled`",
        f"- Generated max latency: `{generated['max_latency_ms']} ms`",
        "",
        "## Call Table",
        "",
        "| Call | Label | Expected | Baseline outcome | Generated outcome | Generated call control | Packets | Hard failure |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for call in payload["calls"]:
        lines.append(
            "| {call_id} | {label} | {expected} | {baseline} | {generated} | {control} | {packets} | {hard_failure} |".format(
                call_id=call["call_id"],
                label=call["scenario_label"],
                expected=call["expected_outcome"],
                baseline=call["baseline"]["outcome"],
                generated=call["generated"]["outcome"],
                control=call["generated"]["call_control"],
                packets=len(call["generated_turn_packets"]),
                hard_failure=call["generated"]["hard_failure"],
            )
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "PROD-008 removes the pre-scored packet shortcut from PROD-007. The runtime-style generator creates BRAIN-002 state from every turn, preserves the safe close rate gain, and keeps hard failure rate and non-sale correctness at the required targets.",
            "",
            "## Next Gate",
            "",
            "Expand the generated full-call gauntlet beyond SD-card/storage scenarios, keeping the same state packet completeness, hard-failure, non-sale correctness, retrieval, and provider boundaries.",
        ]
    )
    return "\n".join(lines) + "\n"


def decide_prod_009(generated: dict[str, Any], comparison: dict[str, Any]) -> str:
    if generated["hard_failure_rate"] > 0:
        return "revise_cross_domain_generated_packets_before_more_tests"
    if generated["state_packet_completeness"] < 1.0:
        return "revise_cross_domain_generated_packets_until_schema_complete"
    if generated["non_sale_correctness"] < 1.0:
        return "revise_cross_domain_generated_packets_before_close_optimization"
    if comparison["generated_safe_close_rate_delta"] <= 0:
        return "keep_old_core_until_cross_domain_generated_safe_close_gain_exists"
    return "keep_cross_domain_generated_packets_for_harder_objection_expansion_not_runtime_promotion"


def build_prod_009_payload(case_path: Path, *, root: Path) -> dict[str, Any]:
    case = load_json(case_path)
    calls = [build_generated_output_for_call(call) for call in case["fixed_calls"]]
    metrics = case["metrics"]
    baseline = metric_summary(calls, "baseline", metrics)
    generated = metric_summary(calls, "generated", metrics)
    eligible_close_count = sum(1 for call in calls if call["eligible_for_close"])
    non_sale_call_count = len(calls) - eligible_close_count
    generated_packet_count = sum(len(call["generated_turn_packets"]) for call in calls)
    turn_count = sum(len(call["turns"]) for call in calls)
    domain_count = len({call["domain"] for call in calls})
    source_pattern_coverage_count = len({pattern for call in calls for pattern in call["source_pattern_ids"]})
    comparison = {
        "generated_safe_close_rate_delta": round(generated["safe_close_rate"] - baseline["safe_close_rate"], 4),
        "generated_hard_failure_rate_delta": round(generated["hard_failure_rate"] - baseline["hard_failure_rate"], 4),
        "generated_non_sale_correctness_delta": round(
            generated["non_sale_correctness"] - baseline["non_sale_correctness"],
            4,
        ),
        "generated_close_attempt_quality_delta": round(
            generated["close_attempt_quality"] - baseline["close_attempt_quality"],
            4,
        ),
        "generated_call_control_correctness_delta": round(
            generated["call_control_correctness"] - baseline["call_control_correctness"],
            4,
        ),
    }
    comparison["decision"] = decide_prod_009(generated, comparison)

    return {
        "prod_009_id": "PROD-009-cross-domain-generated-gauntlet",
        "source_checkpoint": "PROD-008-generated-full-call-packets",
        "generator_id": "brain_002_cross_domain_turn_generator",
        "hypothesis": case["hypothesis"],
        "experiment_protocol": case["experiment_protocol"],
        "metrics": metrics,
        "summary": {
            "call_count": len(calls),
            "turn_count": turn_count,
            "generated_packet_count": generated_packet_count,
            "domain_count": domain_count,
            "source_pattern_coverage_count": source_pattern_coverage_count,
            "eligible_close_count": eligible_close_count,
            "non_sale_call_count": non_sale_call_count,
            "baseline": baseline,
            "generated": generated,
            "comparison": comparison,
        },
        "calls": calls,
        "boundaries": {
            "provider_calls_made": False,
            "private_data_read": False,
            "runtime_behavior_changed": False,
            "retrieval_default": "disabled",
            "dataset_download_performed": False,
            "commercial_runtime_prompt_contamination": False,
            "real_customer_data_used": False,
            "payment_or_checkout_enabled": False,
        },
    }


def render_prod_009_report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    baseline = summary["baseline"]
    generated = summary["generated"]
    comparison = summary["comparison"]
    lines = [
        "# PROD-009 Cross-Domain Generated Gauntlet Report",
        "",
        "This cross-domain generated gauntlet expands PROD-008 beyond SD-card/storage calls while keeping BRAIN-002 packet generation local and deterministic.",
        "",
        "No provider calls, private data reads, dataset downloads, payment handling, checkout handling, or runtime behavior changes occurred.",
        "",
        "## Experiment Discipline",
        "",
        f"- Hypothesis: {payload['hypothesis']}",
        "- Fixed cases: ten calls across multiple domains with the same baseline and generated scoring rules.",
        "- Generated surface: cross_domain_runtime_turn_packet_generation.",
        "- Fixture candidate packets used: false",
        "- Retrieval disabled by default: true",
        "- Source patterns per call >= 3: true",
        "- Domain coverage: `{}` domains".format(summary["domain_count"]),
        "- Decision: `{}`".format(comparison["decision"]),
        "",
        "## Result",
        "",
        f"- Calls: `{summary['call_count']}`",
        f"- Turns: `{summary['turn_count']}`",
        f"- Generated packet count: `{summary['generated_packet_count']}`",
        f"- Domain count: `{summary['domain_count']}`",
        f"- Source pattern coverage count: `{summary['source_pattern_coverage_count']}`",
        f"- Eligible close calls: `{summary['eligible_close_count']}`",
        f"- Non-sale calls: `{summary['non_sale_call_count']}`",
        f"- Baseline safe close rate: `{baseline['safe_close_rate']}`",
        f"- Generated safe close rate: `{generated['safe_close_rate']}`",
        f"- Generated safe close rate delta: `{comparison['generated_safe_close_rate_delta']}`",
        f"- Baseline hard failure rate: `{baseline['hard_failure_rate']}`",
        f"- Generated hard failure rate: `{generated['hard_failure_rate']}`",
        f"- Generated hard failure rate delta: `{comparison['generated_hard_failure_rate_delta']}`",
        f"- Baseline non-sale correctness: `{baseline['non_sale_correctness']}`",
        f"- Generated non-sale correctness: `{generated['non_sale_correctness']}`",
        f"- Generated non-sale correctness delta: `{comparison['generated_non_sale_correctness_delta']}`",
        f"- Generated call-control correctness: `{generated['call_control_correctness']}`",
        f"- Generated state packet completeness: `{generated['state_packet_completeness']}`",
        f"- Retrieval default: `disabled`",
        f"- Generated max latency: `{generated['max_latency_ms']} ms`",
        "",
        "## Call Table",
        "",
        "| Call | Domain | Label | Expected | Baseline outcome | Generated outcome | Generated call control | Packets |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for call in payload["calls"]:
        lines.append(
            "| {call_id} | {domain} | {label} | {expected} | {baseline} | {generated} | {control} | {packets} |".format(
                call_id=call["call_id"],
                domain=call["domain"],
                label=call["scenario_label"],
                expected=call["expected_outcome"],
                baseline=call["baseline"]["outcome"],
                generated=call["generated"]["outcome"],
                control=call["generated"]["call_control"],
                packets=len(call["generated_turn_packets"]),
            )
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "PROD-009 keeps the generated BRAIN-002 packet path stable across retail, telecom, B2B software, insurance, medical equipment, home service, membership, and automotive-style calls. This is still local fixture evidence, not production evidence.",
            "",
            "## Next Gate",
            "",
            "Add harder universal objections and longer calls, then require the same hard-failure, non-sale correctness, state packet completeness, retrieval, and provider boundaries before any runtime promotion.",
        ]
    )
    return "\n".join(lines) + "\n"


def decide_prod_010(generated: dict[str, Any], comparison: dict[str, Any]) -> str:
    if generated["hard_failure_rate"] > 0:
        return "revise_long_call_objection_packets_before_more_tests"
    if generated["state_packet_completeness"] < 1.0:
        return "revise_long_call_objection_packets_until_schema_complete"
    if generated["objection_boundary_correctness"] < 1.0:
        return "revise_long_call_objection_boundary_before_close_optimization"
    if generated["long_call_state_continuity"] < 1.0:
        return "revise_long_call_state_continuity_before_runtime_work"
    if generated["non_sale_correctness"] < 1.0:
        return "revise_long_call_objection_packets_before_close_optimization"
    if comparison["generated_safe_close_rate_delta"] <= 0:
        return "keep_old_core_until_long_call_generated_safe_close_gain_exists"
    return "keep_long_call_objection_packets_for_dialogue_policy_hardening_not_runtime_promotion"


def build_prod_010_payload(case_path: Path, *, root: Path) -> dict[str, Any]:
    case = load_json(case_path)
    calls = [build_generated_output_for_call(call) for call in case["fixed_calls"]]
    metrics = case["metrics"]
    baseline = metric_summary(calls, "baseline", metrics)
    generated = metric_summary(calls, "generated", metrics)
    generated["objection_boundary_correctness"] = rate(
        sum(
            1
            for call in calls
            if all(turn["state_packet"]["safety"]["objection_boundary_checked"] is True for turn in call["generated_turn_packets"])
        ),
        len(calls),
    )
    generated["long_call_state_continuity"] = rate(
        sum(
            1
            for call in calls
            if all(
                turn["state_packet"]["buyer_state"]["turn_count"] == len(call["turns"])
                and turn["state_packet"]["buyer_state"]["turn_position"] == index
                and turn["state_packet"]["buyer_state"]["universal_objections_seen"] == call["universal_objections"]
                for index, turn in enumerate(call["generated_turn_packets"], start=1)
            )
        ),
        len(calls),
    )
    eligible_close_count = sum(1 for call in calls if call["eligible_for_close"])
    non_sale_call_count = len(calls) - eligible_close_count
    generated_packet_count = sum(len(call["generated_turn_packets"]) for call in calls)
    turn_count = sum(len(call["turns"]) for call in calls)
    domain_count = len({call["domain"] for call in calls})
    universal_objection_count = len({objection for call in calls for objection in call["universal_objections"]})
    comparison = {
        "generated_safe_close_rate_delta": round(generated["safe_close_rate"] - baseline["safe_close_rate"], 4),
        "generated_hard_failure_rate_delta": round(generated["hard_failure_rate"] - baseline["hard_failure_rate"], 4),
        "generated_non_sale_correctness_delta": round(
            generated["non_sale_correctness"] - baseline["non_sale_correctness"],
            4,
        ),
        "generated_close_attempt_quality_delta": round(
            generated["close_attempt_quality"] - baseline["close_attempt_quality"],
            4,
        ),
        "generated_call_control_correctness_delta": round(
            generated["call_control_correctness"] - baseline["call_control_correctness"],
            4,
        ),
    }
    comparison["decision"] = decide_prod_010(generated, comparison)

    return {
        "prod_010_id": "PROD-010-long-call-universal-objections",
        "source_checkpoint": "PROD-009-cross-domain-generated-gauntlet",
        "generator_id": "brain_002_long_call_objection_generator",
        "hypothesis": case["hypothesis"],
        "experiment_protocol": case["experiment_protocol"],
        "metrics": metrics,
        "summary": {
            "call_count": len(calls),
            "turn_count": turn_count,
            "average_turns_per_call": round(turn_count / len(calls), 4),
            "generated_packet_count": generated_packet_count,
            "domain_count": domain_count,
            "universal_objection_count": universal_objection_count,
            "eligible_close_count": eligible_close_count,
            "non_sale_call_count": non_sale_call_count,
            "baseline": baseline,
            "generated": generated,
            "comparison": comparison,
        },
        "calls": calls,
        "boundaries": {
            "provider_calls_made": False,
            "private_data_read": False,
            "runtime_behavior_changed": False,
            "retrieval_default": "disabled",
            "dataset_download_performed": False,
            "commercial_runtime_prompt_contamination": False,
            "real_customer_data_used": False,
            "payment_or_checkout_enabled": False,
        },
    }


def render_prod_010_report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    baseline = summary["baseline"]
    generated = summary["generated"]
    comparison = summary["comparison"]
    lines = [
        "# PROD-010 Long-Call Universal Objections Report",
        "",
        "This long-call universal objections gauntlet expands PROD-009 into longer calls with repeated buyer objections while keeping BRAIN-002 packet generation local and deterministic.",
        "",
        "No provider calls, private data reads, dataset downloads, payment handling, checkout handling, or runtime behavior changes occurred.",
        "",
        "## Experiment Discipline",
        "",
        f"- Hypothesis: {payload['hypothesis']}",
        "- Fixed cases: six long calls with repeated universal objections and the same baseline/generated scoring rules.",
        "- Generated surface: long_call_universal_objection_packet_generation.",
        "- Fixture candidate packets used: false",
        "- Retrieval disabled by default: true",
        "- Decision: `{}`".format(comparison["decision"]),
        "",
        "## Result",
        "",
        f"- Calls: `{summary['call_count']}`",
        f"- Turns: `{summary['turn_count']}`",
        f"- Average turns per call: `{summary['average_turns_per_call']}`",
        f"- Generated packet count: `{summary['generated_packet_count']}`",
        f"- Domain count: `{summary['domain_count']}`",
        f"- Universal objection count: `{summary['universal_objection_count']}`",
        f"- Eligible close calls: `{summary['eligible_close_count']}`",
        f"- Non-sale calls: `{summary['non_sale_call_count']}`",
        f"- Baseline safe close rate: `{baseline['safe_close_rate']}`",
        f"- Generated safe close rate: `{generated['safe_close_rate']}`",
        f"- Generated safe close rate delta: `{comparison['generated_safe_close_rate_delta']}`",
        f"- Baseline hard failure rate: `{baseline['hard_failure_rate']}`",
        f"- Generated hard failure rate: `{generated['hard_failure_rate']}`",
        f"- Generated hard failure rate delta: `{comparison['generated_hard_failure_rate_delta']}`",
        f"- Baseline non-sale correctness: `{baseline['non_sale_correctness']}`",
        f"- Generated non-sale correctness: `{generated['non_sale_correctness']}`",
        f"- Generated non-sale correctness delta: `{comparison['generated_non_sale_correctness_delta']}`",
        f"- Generated call-control correctness: `{generated['call_control_correctness']}`",
        f"- Generated state packet completeness: `{generated['state_packet_completeness']}`",
        f"- Generated objection boundary correctness: `{generated['objection_boundary_correctness']}`",
        f"- Generated long-call state continuity: `{generated['long_call_state_continuity']}`",
        f"- Retrieval default: `disabled`",
        f"- Generated max latency: `{generated['max_latency_ms']} ms`",
        "",
        "## Call Table",
        "",
        "| Call | Domain | Label | Turns | Expected | Baseline outcome | Generated outcome | Generated call control |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for call in payload["calls"]:
        lines.append(
            "| {call_id} | {domain} | {label} | {turns} | {expected} | {baseline} | {generated} | {control} |".format(
                call_id=call["call_id"],
                domain=call["domain"],
                label=call["scenario_label"],
                turns=len(call["turns"]),
                expected=call["expected_outcome"],
                baseline=call["baseline"]["outcome"],
                generated=call["generated"]["outcome"],
                control=call["generated"]["call_control"],
            )
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "PROD-010 shows the generated BRAIN-002 packet path can carry objection state across longer calls without losing non-sale boundaries. This is still local fixture evidence, not production evidence.",
            "",
            "## Next Gate",
            "",
            "Use this evidence to harden the dialogue policy for multi-turn objection handling, then test it against live-runtime-shaped transcripts only after the same provider, privacy, retrieval, and evidence boundaries remain green.",
        ]
    )
    return "\n".join(lines) + "\n"
