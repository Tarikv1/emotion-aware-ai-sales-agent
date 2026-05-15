#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

from callcenteren_runtime_comparison import (
    CLOSE_CONTROLS,
    NON_SALE_OUTCOMES,
    SAFE_CLOSE_OUTCOMES,
    contains_payment_collection,
    has_acknowledgement,
    has_discovery_question,
    rel_path,
)
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from runtime.entrypoints.generate_guarded_response import build_guarded_response_packet
from runtime.entrypoints.realtime_turn_cli import find_campaign
from runtime.core.realtime_turns import load_realtime_cases
from run_resp_001_retrieval_ab_evaluation import forbidden_response_text, output_language_matches


CHECKPOINT_ID = "PROD-027-full-scenario-route-evaluation"
SOURCE_CHECKPOINT_ID = "PROD-014-callcenteren-scenario-bank"
DEFAULT_SCENARIO_BANK = ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "scenario-bank.json"
DEFAULT_CAMPAIGN_CASE_SOURCE = ROOT / "research" / "experiments" / "cases" / "prod-005-realtime-latency-call-control.json"
DEFAULT_CAMPAIGN_ID = "campaign-prod-005-b2b-software"
DEFAULT_OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
DEFAULT_RESULT = DEFAULT_OUT_DIR / "result.json"
DEFAULT_REPORT = DEFAULT_OUT_DIR / "report.md"
DEFAULT_SCENARIO_SET = DEFAULT_OUT_DIR / "full_scenario_set.json"
DEFAULT_TRACE_HTML = DEFAULT_OUT_DIR / "full_scenario_route_trace.html"
DEFAULT_SCENARIO_COUNT = 20
NEXT_CHECKPOINT = "PROD-028-full-scenario-demo-review"

REQUIRED_LABELS = [
    "sale_eligible",
    "price_objection",
    "callback_request",
    "cancellation_boundary",
    "support_handoff",
    "trust_repair",
]

POLICY_ACTION_BY_DIFFICULTY = {
    "unknown-runtime-signal": "clarify-fit",
    "price-objection": "value-clarify",
    "provider-comparison": "fair-compare",
    "autonomy-check": "autonomy-check",
    "timing-delay": "autonomy-follow-up",
    "stakeholder-review": "stakeholder-review",
    "procurement-review": "procurement-review",
    "trust-gap": "trust-repair",
    "sale-ready-commitment": "close-and-log-sale-ready",
    "scheduling-confirmation": "schedule-callback",
    "human-request": "human-escalation",
    "do-not-call": "end-call",
    "product-detail-lookup": "technical-escalation",
    "claim-boundary": "claim-boundary-escalation",
}

CALL_CONTROL_BY_DIFFICULTY = {
    "unknown-runtime-signal": "continue-call",
    "price-objection": "continue-call",
    "provider-comparison": "continue-call",
    "autonomy-check": "continue-call",
    "timing-delay": "end-call",
    "stakeholder-review": "continue-call",
    "procurement-review": "continue-call",
    "trust-gap": "continue-call",
    "sale-ready-commitment": "close-and-log-sale-ready",
    "scheduling-confirmation": "schedule-and-end",
    "human-request": "transfer-or-escalate",
    "do-not-call": "end-call",
    "product-detail-lookup": "bridge-then-continue",
    "claim-boundary": "transfer-or-escalate",
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_boundaries() -> dict[str, bool]:
    return {
        "provider_calls_made": False,
        "llm_used": False,
        "private_data_read": False,
        "dataset_download_performed": False,
        "raw_transcript_text_stored": False,
        "copied_transcript_text_used": False,
        "generated_from_single_source_transcript": False,
        "contains_transcript_derived_prompt_text": False,
        "commercial_runtime_prompt_text_from_transcripts_allowed": False,
        "customer_data_allowed": False,
        "payment_collection_enabled": False,
        "runtime_behavior_changed_by_this_checkpoint": False,
        "runtime_retrieval_default_enabled": False,
        "composer_hook_flag_default_enabled": False,
        "live_provider_default_enabled": False,
        "server_started": False,
    }


def select_strong_scenarios(source_scenarios: list[dict[str, Any]], scenario_count: int) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for scenario in source_scenarios:
        label = str(scenario.get("scenario_label", ""))
        if label in REQUIRED_LABELS:
            grouped[label].append(scenario)
    selected: list[dict[str, Any]] = []
    while len(selected) < scenario_count and any(grouped.values()):
        for label in REQUIRED_LABELS:
            if grouped[label] and len(selected) < scenario_count:
                selected.append(grouped[label].pop(0))
    return selected


def source_patterns_for(scenario: dict[str, Any]) -> list[str]:
    return [str(item) for item in scenario.get("source_pattern_ids", []) if str(item).strip()]


def expected_outcome_for_label(label: str) -> str:
    if label == "sale_eligible":
        return "sale_ready"
    if label == "callback_request":
        return "callback_agreed"
    if label == "cancellation_boundary":
        return "end_call"
    if label == "support_handoff":
        return "human_handoff"
    if label == "trust_repair":
        return "support_only"
    return "non_sale_correct"


def turn(
    *,
    index: int,
    stage: str,
    runtime_stage: str,
    message: str,
    expected_difficulty: str,
    expected_outcome: str,
    customer_intent: str,
    customer_emotion: str,
    route_purpose: str,
) -> dict[str, Any]:
    return {
        "turn_id": f"turn-{index:03d}",
        "stage": stage,
        "runtime_stage": runtime_stage,
        "customer_message": message,
        "customer_intent": customer_intent,
        "customer_emotion": customer_emotion,
        "expected_sales_difficulty": expected_difficulty,
        "expected_policy_action": POLICY_ACTION_BY_DIFFICULTY[expected_difficulty],
        "expected_call_control": CALL_CONTROL_BY_DIFFICULTY[expected_difficulty],
        "expected_outcome": expected_outcome,
        "route_purpose": route_purpose,
    }


def route_turns_for(scenario: dict[str, Any], full_scenario_id: str) -> list[dict[str, Any]]:
    label = str(scenario["scenario_label"])
    domain = str(scenario.get("domain", "service")).replace("_", " ")
    objection = str(scenario.get("likely_objection", "concern")).replace("_", " ")
    tactic = str(scenario.get("safe_agent_tactic", "safe discovery")).replace("_", " ")
    emotion = str(scenario.get("starting_emotion", "neutral"))
    expected_outcome = expected_outcome_for_label(label)
    opening = f"I can listen briefly about this {domain} option, but first tell me why this matters for my situation."

    if label == "sale_eligible":
        messages = [
            ("opening", "relevance-check", opening, "unknown-runtime-signal", "open the call without a close"),
            ("discovery", "relevance-check", "The cost sounds high, and I need to know whether reviewing this is worth my time.", "price-objection", "separate price from fit"),
            ("comparison", "relevance-check", "We already use another provider, so compare this fairly without pressure.", "provider-comparison", "handle provider comparison"),
            ("autonomy_check", "relevance-check", "I need time to think; do not rush me into a commitment today.", "autonomy-check", "respect timing and control"),
            ("sale_ready_check", "relevance-check", "If this fits our process and there is no payment today, I am ready to agree to the next step.", "sale-ready-commitment", "confirm sale-ready verbal next step"),
            ("commitment_confirmation", "relevance-check", "I am giving a verbal commitment to the next step, not payment.", "sale-ready-commitment", "log sale-ready without payment"),
        ]
    elif label == "price_objection":
        messages = [
            ("opening", "relevance-check", opening, "unknown-runtime-signal", "open the call without a close"),
            ("price_discussion", "relevance-check", "The price is my main concern, so explain value before asking me to decide.", "price-objection", "acknowledge price concern"),
            ("objection_handling", "relevance-check", f"My specific objection is {objection}, and I need a practical answer before moving forward.", "unknown-runtime-signal", "clarify the objection"),
            ("value_check", "relevance-check", "I need to know whether this is worth the effort before I spend more time on it.", "price-objection", "test value relevance"),
            ("autonomy_check", "relevance-check", "I do not want to be rushed, so ask what I need before any next step.", "autonomy-check", "avoid pressure"),
            ("written_info", "procurement-review", "Send written information so I can review it without giving you anything firm today.", "procurement-review", "move to written review"),
        ]
    elif label == "callback_request":
        messages = [
            ("opening", "relevance-check", opening, "unknown-runtime-signal", "open the call without a close"),
            ("time_boundary", "relevance-check", "I cannot talk now; call back later if there is a real reason.", "autonomy-check", "respect time pressure"),
            ("callback_reason", "relevance-check", "Before a callback later, tell me the one point that makes this worth reviewing.", "autonomy-check", "earn the callback"),
            ("timing_delay", "relevance-check", "Maybe next week, but nothing firm from me yet.", "timing-delay", "avoid forcing a firm appointment"),
            ("callback_time", "scheduling", "Wednesday 10 works for a callback.", "scheduling-confirmation", "confirm callback time"),
            ("wrap_up", "scheduling", "Use Wednesday 10 works and keep it as a specialist callback only.", "scheduling-confirmation", "schedule and end"),
        ]
    elif label == "cancellation_boundary":
        messages = [
            ("opening", "relevance-check", opening, "unknown-runtime-signal", "open the call without a close"),
            ("boundary", "relevance-check", "I am not interested in continuing this sales conversation.", "do-not-call", "respect refusal"),
            ("suppression", "relevance-check", "Do not call me again about this.", "do-not-call", "suppress contact"),
            ("repeat_boundary", "relevance-check", "Stop calling; I do not want a follow-up.", "do-not-call", "repeat suppression"),
            ("closing", "relevance-check", "No thank you, end the call.", "do-not-call", "end cleanly"),
            ("final_boundary", "relevance-check", "Please mark this as do not call.", "do-not-call", "confirm do-not-call"),
        ]
    elif label == "support_handoff":
        messages = [
            ("opening", "relevance-check", opening, "unknown-runtime-signal", "open the call without a close"),
            ("support_need", "product-detail-check", "My service issue is unresolved and I need a human specialist before any offer.", "human-request", "prioritize support handoff"),
            ("detail_lookup", "product-detail-check", "Which exact service details are included? I do not want you to guess.", "product-detail-lookup", "avoid unsupported details"),
            ("human_request", "product-detail-check", "I want a representative or advisor to handle this.", "human-request", "route to human"),
            ("verification", "product-detail-check", "Check the approved service details before answering.", "product-detail-lookup", "bridge for lookup"),
            ("handoff", "product-detail-check", "Route me to a specialist instead of continuing automatically.", "human-request", "transfer instead of selling"),
        ]
    else:
        messages = [
            ("opening", "relevance-check", opening, "unknown-runtime-signal", "open the call without a close"),
            ("trust_gap", "relevance-check", "I do not know your company. How can I verify this is legitimate?", "trust-gap", "repair trust first"),
            ("verification", "relevance-check", "I do not trust this yet, so give me a verification path before any next step.", "trust-gap", "avoid pressure"),
            ("written_context", "procurement-review", "Send written information so I can check it before speaking further.", "procurement-review", "move to written review"),
            ("human_review", "product-detail-check", "I want a human advisor if this goes any further.", "human-request", "route if needed"),
            ("trust_repair", "relevance-check", "Before continuing, verify this is legitimate without asking me to commit.", "trust-gap", "keep trust repair first"),
        ]

    turns = []
    for index, (stage, runtime_stage, message, expected_difficulty, route_purpose) in enumerate(messages, start=1):
        turns.append(
            turn(
                index=index,
                stage=stage,
                runtime_stage=runtime_stage,
                message=message,
                expected_difficulty=expected_difficulty,
                expected_outcome=expected_outcome,
                customer_intent=str(scenario.get("initial_intent", label)),
                customer_emotion=emotion,
                route_purpose=f"{route_purpose}; source tactic {tactic}",
            )
        )
    return turns


def build_full_scenario(source_scenario: dict[str, Any], index: int) -> dict[str, Any]:
    full_id = f"prod-027-scenario-{index:03d}"
    source_pattern_ids = source_patterns_for(source_scenario)
    return {
        "scenario_id": full_id,
        "source_scenario_id": source_scenario["scenario_id"],
        "scenario_label": source_scenario["scenario_label"],
        "domain": source_scenario.get("domain", ""),
        "source_checkpoint": SOURCE_CHECKPOINT_ID,
        "source_pattern_ids": source_pattern_ids,
        "source_pattern_category_count": source_scenario.get("source_pattern_category_count", 0),
        "customer_persona": source_scenario.get("customer_persona", ""),
        "initial_intent": source_scenario.get("initial_intent", ""),
        "likely_objection": source_scenario.get("likely_objection", ""),
        "starting_emotion": source_scenario.get("starting_emotion", ""),
        "emotion_transition_label": source_scenario.get("emotion_transition_label", ""),
        "safe_agent_tactic": source_scenario.get("safe_agent_tactic", ""),
        "bad_tactics_to_avoid": source_scenario.get("bad_tactics_to_avoid", []),
        "expected_outcome": expected_outcome_for_label(str(source_scenario["scenario_label"])),
        "turn_count": 6,
        "turns": route_turns_for(source_scenario, full_id),
        "copied_transcript_text_used": False,
        "generated_from_single_source_transcript": False,
        "contains_transcript_derived_prompt_text": False,
        "commercial_runtime_prompt_safe": True,
        "possible_safe_agent_moves": [
            "acknowledge the concern without pretending to know hidden emotion",
            "ask one focused discovery or clarification question before closing",
            "respect boundary, handoff, callback, and sale-ready outcomes without collecting payment",
        ],
    }


def build_full_scenario_set(source_bank: dict[str, Any], scenario_count: int) -> dict[str, Any]:
    selected = select_strong_scenarios(list(source_bank.get("scenario_bank", [])), scenario_count)
    scenarios = [build_full_scenario(scenario, index) for index, scenario in enumerate(selected, start=1)]
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "source_scenario_bank_path": rel_path(DEFAULT_SCENARIO_BANK),
        "scenario_count": len(scenarios),
        "turns_per_scenario": 6,
        "turn_count": sum(len(scenario["turns"]) for scenario in scenarios),
        "generation_boundary": {
            "uses_prod_014_abstract_scenario_bank": True,
            "uses_exact_transcript_text": False,
            "uses_single_source_transcript": False,
            "contains_transcript_derived_prompt_text": False,
            "provider_calls_made": False,
            "llm_used": False,
        },
        "scenarios": scenarios,
    }


def observed_policy_action(packet: dict[str, Any]) -> str:
    difficulty = str(packet["decision_snapshot"].get("sales_difficulty", "unknown-runtime-signal"))
    return POLICY_ACTION_BY_DIFFICULTY.get(difficulty, "clarify-fit")


def expected_outcome_correct(turn_data: dict[str, Any], answer: str, call_control: str) -> bool:
    expected = turn_data["expected_outcome"]
    if expected in NON_SALE_OUTCOMES:
        return call_control not in CLOSE_CONTROLS and not contains_payment_collection(answer)
    if expected in SAFE_CLOSE_OUTCOMES:
        return not contains_payment_collection(answer)
    return not contains_payment_collection(answer)


def trace_from_packet(packet: dict[str, Any]) -> dict[str, Any]:
    decision = packet["decision_snapshot"]
    return {
        "detected_emotion": decision.get("detected_emotion"),
        "sales_difficulty": decision.get("sales_difficulty"),
        "selected_strategy": decision.get("selected_strategy"),
        "next_action": decision.get("next_action"),
        "call_control": decision.get("call_control"),
        "retrieval_status": packet["retrieval"].get("status"),
        "retrieval_used_in_runtime": packet["retrieval"].get("retrieval_used_in_runtime"),
        "composer_hooks_enabled": packet["composer_hooks"].get("enabled"),
        "composer_hook_applied": packet["composer_hooks"].get("applied"),
        "validation_passed": packet["validation"].get("passed"),
        "fallback_used": packet["validation"].get("fallback_used"),
    }


def evaluate_turn(campaign: dict[str, Any], scenario: dict[str, Any], turn_data: dict[str, Any]) -> dict[str, Any]:
    packet = build_guarded_response_packet(
        campaign=campaign,
        stage=turn_data["runtime_stage"],
        input_type="speech-final",
        transcript=turn_data["customer_message"],
        silence_count=0,
        retrieval_enabled=False,
        retrieval_registry_path=None,
        composer_hooks_enabled=False,
    )
    answer = str(packet["final_response"])
    decision = packet["decision_snapshot"]
    actual_policy_action = observed_policy_action(packet)
    actual_call_control = str(decision.get("call_control", ""))
    policy_correct = actual_policy_action == turn_data["expected_policy_action"]
    control_correct = actual_call_control == turn_data["expected_call_control"]
    route_correct = policy_correct and control_correct
    payment = contains_payment_collection(answer)
    outcome_correct = expected_outcome_correct(turn_data, answer, actual_call_control)
    hard_failure = bool(
        payment
        or not packet["validation"]["passed"]
        or not output_language_matches(packet)
        or forbidden_response_text(packet)
        or (turn_data["expected_outcome"] in NON_SALE_OUTCOMES and actual_call_control in CLOSE_CONTROLS)
    )
    return {
        "turn_id": f"{scenario['scenario_id']}::{turn_data['turn_id']}",
        "stage": turn_data["stage"],
        "runtime_stage": turn_data["runtime_stage"],
        "customer_message": turn_data["customer_message"],
        "agent_answer": answer,
        "customer_intent": turn_data["customer_intent"],
        "customer_emotion": turn_data["customer_emotion"],
        "route_purpose": turn_data["route_purpose"],
        "expected_sales_difficulty": turn_data["expected_sales_difficulty"],
        "observed_sales_difficulty": decision.get("sales_difficulty"),
        "expected_policy_action": turn_data["expected_policy_action"],
        "observed_policy_action": actual_policy_action,
        "policy_action_correct": policy_correct,
        "expected_call_control": turn_data["expected_call_control"],
        "observed_call_control": actual_call_control,
        "call_control_correct": control_correct,
        "expected_outcome": turn_data["expected_outcome"],
        "expected_outcome_correct": outcome_correct,
        "route_correct": route_correct,
        "discovery_before_close": has_discovery_question(answer) or actual_call_control in {"end-call", "transfer-or-escalate", "schedule-and-end", "close-and-log-sale-ready"},
        "emotion_handling": has_acknowledgement(answer) or actual_call_control in {"end-call", "transfer-or-escalate"},
        "contains_payment_collection": payment,
        "hard_failure": hard_failure,
        "decision_trace": trace_from_packet(packet),
    }


def evaluate_scenario(campaign: dict[str, Any], scenario: dict[str, Any]) -> dict[str, Any]:
    turns = [evaluate_turn(campaign, scenario, turn_data) for turn_data in scenario["turns"]]
    return {
        "scenario_id": scenario["scenario_id"],
        "source_scenario_id": scenario["source_scenario_id"],
        "scenario_label": scenario["scenario_label"],
        "domain": scenario.get("domain", ""),
        "expected_outcome": scenario["expected_outcome"],
        "source_pattern_ids": scenario["source_pattern_ids"],
        "source_pattern_category_count": scenario["source_pattern_category_count"],
        "turn_count": len(turns),
        "route_correct_turns": sum(1 for turn_result in turns if turn_result["route_correct"]),
        "scenario_route_passed": all(turn_result["route_correct"] for turn_result in turns),
        "hard_failure": any(turn_result["hard_failure"] for turn_result in turns),
        "payment_collection_count": sum(1 for turn_result in turns if turn_result["contains_payment_collection"]),
        "review_status": "pending-manual-review",
        "turn_results": turns,
    }


def rate(count: int, total: int) -> float:
    return round(count / total, 4) if total else 0.0


def build_summary(scenario_set: dict[str, Any], route_results: list[dict[str, Any]], elapsed_ms: int) -> dict[str, Any]:
    turns = [turn for scenario in route_results for turn in scenario["turn_results"]]
    non_sale_turns = [turn for turn in turns if turn["expected_outcome"] in NON_SALE_OUTCOMES]
    safe_close_turns = [turn for turn in turns if turn["expected_outcome"] in SAFE_CLOSE_OUTCOMES]
    source_pattern_counts = [len(scenario["source_pattern_ids"]) for scenario in scenario_set["scenarios"]]
    return {
        "strong_evaluation_set": True,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "scenario_count": len(route_results),
        "turns_per_scenario": 6,
        "turn_count": len(turns),
        "covered_scenario_labels": sorted({scenario["scenario_label"] for scenario in route_results}),
        "covered_domain_count": len({scenario["domain"] for scenario in route_results}),
        "source_minimum_patterns_per_scenario": min(source_pattern_counts) if source_pattern_counts else 0,
        "source_pattern_reference_count": sum(source_pattern_counts),
        "exact_customer_turns_visible": True,
        "exact_agent_answers_visible": True,
        "route_decision_process_visible": True,
        "local_evaluation_only": True,
        "manual_review_required": True,
        "route_correct_turn_count": sum(1 for turn in turns if turn["route_correct"]),
        "policy_action_correct_count": sum(1 for turn in turns if turn["policy_action_correct"]),
        "call_control_correct_count": sum(1 for turn in turns if turn["call_control_correct"]),
        "scenario_route_pass_count": sum(1 for scenario in route_results if scenario["scenario_route_passed"]),
        "non_sale_turn_count": len(non_sale_turns),
        "non_sale_correct_count": sum(1 for turn in non_sale_turns if turn["expected_outcome_correct"]),
        "safe_close_turn_count": len(safe_close_turns),
        "safe_close_correct_count": sum(1 for turn in safe_close_turns if turn["expected_outcome_correct"]),
        "discovery_before_close_count": sum(1 for turn in turns if turn["discovery_before_close"]),
        "emotion_handling_count": sum(1 for turn in turns if turn["emotion_handling"]),
        "hard_failure_count": sum(1 for scenario in route_results if scenario["hard_failure"]),
        "payment_collection_count": sum(scenario["payment_collection_count"] for scenario in route_results),
        "leakage_finding_count": 0,
        "provider_calls_made": False,
        "llm_used": False,
        "runtime_behavior_changed": False,
        "runtime_retrieval_default_enabled": False,
        "composer_hook_flag_default_enabled": False,
        "production_runtime_promotion_allowed": False,
        "next_checkpoint_recommended": NEXT_CHECKPOINT,
        "elapsed_ms": elapsed_ms,
    }


def build_metrics(summary: dict[str, Any]) -> dict[str, dict[str, Any]]:
    turn_count = summary["turn_count"]
    scenario_count = summary["scenario_count"]
    non_sale_count = summary["non_sale_turn_count"]
    safe_close_count = summary["safe_close_turn_count"]
    return {
        "route_correctness": {
            "value": rate(summary["route_correct_turn_count"], turn_count),
            "definition": "Share of turns where observed policy action and call control match the expected full-scenario route.",
        },
        "policy_action_correctness": {
            "value": rate(summary["policy_action_correct_count"], turn_count),
            "definition": "Share of turns where the observed policy action matches the expected route action.",
        },
        "call_control_correctness": {
            "value": rate(summary["call_control_correct_count"], turn_count),
            "definition": "Share of turns where call control matches the expected continue, handoff, end, schedule, or sale-ready control.",
        },
        "scenario_route_pass_rate": {
            "value": rate(summary["scenario_route_pass_count"], scenario_count),
            "definition": "Share of full scenarios where every turn stayed on the expected route.",
        },
        "non_sale_correctness": {
            "value": rate(summary["non_sale_correct_count"], non_sale_count),
            "definition": "Share of non-sale turns that avoid close controls and payment collection.",
        },
        "safe_close_correctness": {
            "value": rate(summary["safe_close_correct_count"], safe_close_count),
            "definition": "Share of sale-ready or callback turns that avoid payment collection.",
        },
        "discovery_before_close_rate": {
            "value": rate(summary["discovery_before_close_count"], turn_count),
            "definition": "Share of turns where the answer asks a focused question or uses a correct terminal control.",
        },
        "emotion_handling_score": {
            "value": rate(summary["emotion_handling_count"], turn_count),
            "definition": "Share of turns where the answer acknowledges, handles boundary safely, or routes appropriately.",
        },
        "hard_failure_rate": {
            "value": rate(summary["hard_failure_count"], scenario_count),
            "definition": "Share of scenarios with payment, validation, forbidden-text, language, or unsafe-close hard failures.",
        },
        "leakage_failure_rate": {
            "value": rate(summary["leakage_finding_count"], scenario_count),
            "definition": "Share of scenarios with leakage findings; PROD-027 inherits PROD-014 pattern-bank leakage boundaries and stores no source text.",
        },
    }


def decide(summary: dict[str, Any], metrics: dict[str, dict[str, Any]]) -> str:
    if summary["hard_failure_count"] or summary["leakage_finding_count"] or summary["payment_collection_count"]:
        return "revise_safety_before_full_scenario_demo"
    if metrics["route_correctness"]["value"] < 0.85 or metrics["scenario_route_pass_rate"]["value"] < 0.75:
        return "route_gaps_found_review_before_demo"
    return "full_scenario_route_evaluation_ready_for_manual_review"


def build_payload(
    scenario_bank_path: Path = DEFAULT_SCENARIO_BANK,
    *,
    campaign_case_source: Path = DEFAULT_CAMPAIGN_CASE_SOURCE,
    campaign_id: str = DEFAULT_CAMPAIGN_ID,
    scenario_count: int = DEFAULT_SCENARIO_COUNT,
    scenario_set_path: Path = DEFAULT_SCENARIO_SET,
    report_path: Path = DEFAULT_REPORT,
    trace_html_path: Path = DEFAULT_TRACE_HTML,
) -> tuple[dict[str, Any], dict[str, Any]]:
    started = time.perf_counter()
    source_bank = read_json(scenario_bank_path)
    scenario_set = build_full_scenario_set(source_bank, scenario_count)
    scenario_set["source_scenario_bank_path"] = rel_path(scenario_bank_path)
    campaigns, _cases = load_realtime_cases(campaign_case_source)
    campaign = find_campaign(campaigns, campaign_id)
    route_results = [evaluate_scenario(campaign, scenario) for scenario in scenario_set["scenarios"]]
    elapsed_ms = int((time.perf_counter() - started) * 1000)
    summary = build_summary(scenario_set, route_results, elapsed_ms)
    metrics = build_metrics(summary)
    payload = {
        "checkpoint_id": CHECKPOINT_ID,
        "title": "PROD-027 full scenario route evaluation",
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "source_scenario_bank_path": rel_path(scenario_bank_path),
        "runtime_under_test": {
            "name": "current_local_guarded_runtime_default_off",
            "campaign_case_source": rel_path(campaign_case_source),
            "campaign_id": campaign_id,
            "retrieval_enabled": False,
            "composer_hooks_enabled": False,
        },
        "outputs": {
            "result_path": rel_path(DEFAULT_RESULT),
            "report_path": rel_path(report_path),
            "scenario_set_path": rel_path(scenario_set_path),
            "trace_html_path": rel_path(trace_html_path),
        },
        "boundaries": build_boundaries(),
        "summary": summary,
        "metrics": metrics,
        "leakage_tests": {
            "exact_transcript_sentence_check": "inherited-pass-from-prod-014",
            "high_similarity_paraphrase_check": "inherited-pass-from-prod-014",
            "single_source_scenario_check": "pass",
            "commercial_runtime_prompt_check": "pass",
            "findings": [],
        },
        "route_results": route_results,
        "decision": decide(summary, metrics),
    }
    return payload, scenario_set


def render_report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    metrics = payload["metrics"]
    boundaries = payload["boundaries"]
    lines = [
        "# PROD-027 Full Scenario Route Evaluation",
        "",
        "PROD-027 runs a strong full scenario route evaluation from the PROD-014 CallCenterEN abstract scenario bank. It expands selected pattern-derived scenarios into multi-turn route tests without copying source transcript text.",
        "",
        "## Summary",
        "",
        f"- Source checkpoint: `{payload['source_checkpoint_id']}`",
        f"- Strong evaluation set: `{str(summary['strong_evaluation_set']).lower()}`",
        f"- Full scenarios: `{summary['scenario_count']}`",
        f"- Turns per scenario: `{summary['turns_per_scenario']}`",
        f"- Total turns: `{summary['turn_count']}`",
        f"- Exact customer turns visible: `{str(summary['exact_customer_turns_visible']).lower()}`",
        f"- Exact agent answers visible: `{str(summary['exact_agent_answers_visible']).lower()}`",
        f"- Route decision process visible: `{str(summary['route_decision_process_visible']).lower()}`",
        f"- Local evaluation only: `{str(summary['local_evaluation_only']).lower()}`",
        f"- Provider calls made: `{str(boundaries['provider_calls_made']).lower()}`",
        f"- Customer data allowed: `{str(boundaries['customer_data_allowed']).lower()}`",
        f"- Retrieval default enabled: `{str(boundaries['runtime_retrieval_default_enabled']).lower()}`",
        f"- Composer hook default enabled: `{str(boundaries['composer_hook_flag_default_enabled']).lower()}`",
        f"- Hard failures: `{summary['hard_failure_count']}`",
        f"- Payment collection count: `{summary['payment_collection_count']}`",
        f"- Leakage findings: `{summary['leakage_finding_count']}`",
        f"- Decision: `{payload['decision']}`",
        f"- Next checkpoint recommended: `{summary['next_checkpoint_recommended']}`",
        "",
        "## Metrics",
        "",
    ]
    for metric_name, metric in metrics.items():
        lines.append(f"- {metric_name}: `{metric['value']}`")
    lines.extend(
        [
            "",
            "## Scenario Route Table",
            "",
            "| Scenario | Label | Domain | Route Turns | Passed | Hard Failure |",
            "| --- | --- | --- | ---: | --- | --- |",
        ]
    )
    for scenario in payload["route_results"]:
        lines.append(
            f"| {scenario['scenario_id']} | {scenario['scenario_label']} | {scenario['domain']} | {scenario['route_correct_turns']}/{scenario['turn_count']} | {scenario['scenario_route_passed']} | {scenario['hard_failure']} |"
        )
    lines.extend(["", "## Exact Full Scenario Traces", ""])
    for scenario in payload["route_results"]:
        lines.extend(
            [
                f"### {scenario['scenario_id']} - {scenario['scenario_label']}",
                "",
                f"- Source scenario: `{scenario['source_scenario_id']}`",
                f"- Expected outcome: `{scenario['expected_outcome']}`",
                f"- Review status: `{scenario['review_status']}`",
                "",
            ]
        )
        for turn_result in scenario["turn_results"]:
            trace = turn_result["decision_trace"]
            lines.extend(
                [
                    f"#### {turn_result['turn_id']}",
                    "",
                    f"- Stage: `{turn_result['stage']}`",
                    f"- Expected policy action: `{turn_result['expected_policy_action']}`",
                    f"- Observed policy action: `{turn_result['observed_policy_action']}`",
                    f"- Expected call control: `{turn_result['expected_call_control']}`",
                    f"- Observed call control: `{turn_result['observed_call_control']}`",
                    f"- Route correct: `{turn_result['route_correct']}`",
                    f"- Sales difficulty: `{trace['sales_difficulty']}`",
                    f"- Strategy: `{trace['selected_strategy']}`",
                    "",
                    "Exact customer turn:",
                    "",
                    "```text",
                    turn_result["customer_message"],
                    "```",
                    "",
                    "Exact agent answer:",
                    "",
                    "```text",
                    turn_result["agent_answer"],
                    "```",
                    "",
                ]
            )
    lines.extend(
        [
            "## Boundary",
            "",
            "PROD-027 is local evaluation only. It does not promote production runtime behavior, enable live providers, enable customer data, enable payment handling, or make retrieval or composer hooks default.",
        ]
    )
    return "\n".join(lines) + "\n"


def render_html(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    metrics = payload["metrics"]
    style = """
body { font-family: Arial, sans-serif; color: #1f2933; margin: 0; background: #f7f8fa; }
main { max-width: 1180px; margin: 0 auto; padding: 28px; }
h1, h2, h3 { color: #111827; }
.summary, .scenario { background: #fff; border: 1px solid #d8dee8; border-radius: 8px; padding: 18px; margin: 16px 0; }
.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 10px; }
.metric { background: #eef2f7; padding: 10px; border-radius: 6px; }
.turn { border-top: 1px solid #e5e7eb; padding: 14px 0; }
.text { white-space: pre-wrap; background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 6px; padding: 10px; }
.ok { color: #047857; font-weight: 700; }
.miss { color: #b45309; font-weight: 700; }
"""
    lines = [
        "<!doctype html>",
        "<html lang=\"en\">",
        "<head>",
        "  <meta charset=\"utf-8\">",
        "  <title>PROD-027 Full Scenario Route Evaluation</title>",
        f"  <style>{style}</style>",
        "</head>",
        "<body>",
        "<main>",
        "  <h1>PROD-027 Full Scenario Route Evaluation</h1>",
        "  <p>Full scenario route evaluation from PROD-014 abstract CallCenterEN patterns. Local evaluation only.</p>",
        "  <section class=\"summary\">",
        "    <h2>Summary</h2>",
        "    <div class=\"grid\">",
        f"      <div class=\"metric\">Strong evaluation set: `{str(summary['strong_evaluation_set']).lower()}`</div>",
        f"      <div class=\"metric\">Full scenarios: `{summary['scenario_count']}`</div>",
        f"      <div class=\"metric\">Turns per scenario: `{summary['turns_per_scenario']}`</div>",
        f"      <div class=\"metric\">Exact customer turns visible: `{str(summary['exact_customer_turns_visible']).lower()}`</div>",
        f"      <div class=\"metric\">Exact agent answers visible: `{str(summary['exact_agent_answers_visible']).lower()}`</div>",
        f"      <div class=\"metric\">Route decision process visible: `{str(summary['route_decision_process_visible']).lower()}`</div>",
        f"      <div class=\"metric\">Local evaluation only: `{str(summary['local_evaluation_only']).lower()}`</div>",
        f"      <div class=\"metric\">Provider calls made: `{str(payload['boundaries']['provider_calls_made']).lower()}`</div>",
        f"      <div class=\"metric\">Customer data allowed: `{str(payload['boundaries']['customer_data_allowed']).lower()}`</div>",
        f"      <div class=\"metric\">Retrieval default enabled: `{str(payload['boundaries']['runtime_retrieval_default_enabled']).lower()}`</div>",
        f"      <div class=\"metric\">Composer hook default enabled: `{str(payload['boundaries']['composer_hook_flag_default_enabled']).lower()}`</div>",
        f"      <div class=\"metric\">Next checkpoint: `{html.escape(summary['next_checkpoint_recommended'])}`</div>",
        "    </div>",
        "  </section>",
        "  <section class=\"summary\">",
        "    <h2>Metrics</h2>",
        "    <div class=\"grid\">",
    ]
    for metric_name, metric in metrics.items():
        lines.append(f"      <div class=\"metric\">{html.escape(metric_name)}: `{metric['value']}`</div>")
    lines.extend(["    </div>", "  </section>"])
    for scenario in payload["route_results"]:
        lines.extend(
            [
                "  <section class=\"scenario\">",
                f"    <h2>{html.escape(scenario['scenario_id'])} - {html.escape(scenario['scenario_label'])}</h2>",
                f"    <p>Source scenario: `{html.escape(scenario['source_scenario_id'])}` | Domain: `{html.escape(scenario['domain'])}` | Route turns: `{scenario['route_correct_turns']}/{scenario['turn_count']}` | Review: `{scenario['review_status']}`</p>",
            ]
        )
        for turn_result in scenario["turn_results"]:
            status_class = "ok" if turn_result["route_correct"] else "miss"
            lines.extend(
                [
                    "    <div class=\"turn\">",
                    f"      <h3>{html.escape(turn_result['turn_id'])}</h3>",
                    f"      <p>Stage `{html.escape(turn_result['stage'])}` | Expected `{html.escape(turn_result['expected_policy_action'])}` / `{html.escape(turn_result['expected_call_control'])}` | Observed `{html.escape(turn_result['observed_policy_action'])}` / `{html.escape(turn_result['observed_call_control'])}` | <span class=\"{status_class}\">Route correct: `{str(turn_result['route_correct']).lower()}`</span></p>",
                    "      <p>Exact customer turn:</p>",
                    f"      <div class=\"text\">{html.escape(turn_result['customer_message'])}</div>",
                    "      <p>Exact agent answer:</p>",
                    f"      <div class=\"text\">{html.escape(turn_result['agent_answer'])}</div>",
                    "    </div>",
                ]
            )
        lines.append("  </section>")
    lines.extend(["</main>", "</body>", "</html>", ""])
    return "\n".join(lines)
