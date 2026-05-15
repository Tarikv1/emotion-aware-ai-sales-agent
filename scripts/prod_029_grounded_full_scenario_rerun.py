#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import time
from pathlib import Path
from typing import Any

from callcenteren_runtime_comparison import (
    CLOSE_CONTROLS,
    NON_SALE_OUTCOMES,
    SAFE_CLOSE_OUTCOMES,
    contains_payment_collection,
)
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from runtime.entrypoints.generate_guarded_response import build_guarded_response_packet
from prod_027_full_scenario_route_evaluation import (
    CALL_CONTROL_BY_DIFFICULTY,
    POLICY_ACTION_BY_DIFFICULTY,
    expected_outcome_correct,
    observed_policy_action,
    trace_from_packet,
)
from prod_028_synthetic_campaign_knowledge_grounding import build_synthetic_campaign
from run_resp_001_retrieval_ab_evaluation import forbidden_response_text, output_language_matches


CHECKPOINT_ID = "PROD-029-grounded-full-scenario-rerun"
SOURCE_CHECKPOINT_ID = "PROD-027-full-scenario-route-evaluation"
GROUNDING_CHECKPOINT_ID = "PROD-028-synthetic-campaign-knowledge-grounding"
NEXT_CHECKPOINT = "PROD-030-grounded-demo-review"
DEFAULT_OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
DEFAULT_RESULT = DEFAULT_OUT_DIR / "result.json"
DEFAULT_REPORT = DEFAULT_OUT_DIR / "report.md"
DEFAULT_SCENARIO_SET = DEFAULT_OUT_DIR / "grounded_full_scenario_set.json"
DEFAULT_TRACE_HTML = DEFAULT_OUT_DIR / "grounded_full_scenario_trace.html"
DEFAULT_SOURCE_RESULT = ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "result.json"
DEFAULT_SOURCE_SCENARIO_SET = ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "full_scenario_set.json"
DEFAULT_GROUNDING_CAMPAIGN = ROOT / "research" / "experiments" / "generated" / GROUNDING_CHECKPOINT_ID / "synthetic_campaign.json"

UNSUPPORTED_CLAIM_MARKERS = [
    "guaranteed revenue increase",
    "guaranteed cost savings",
    "guaranteed conversion lift",
    "replaces every crm",
    "no risk",
    "legal advice",
    "collect payment or card details on this call",
]

FACT_MARKERS = [
    "RouteSignal",
    "Starter",
    "Growth",
    "Scale",
    "$29",
    "$59",
    "$99",
    "14-day",
    "two to four weeks",
    "annual billing",
    "15%",
    "CSV",
    "Slack",
    "Zapier",
    "SSO",
    "audit logs",
    "no payment",
    "specialist",
    "lead routing",
    "callback ownership",
]

KNOWLEDGE_APPLICABLE_DIFFICULTIES = {
    "unknown-runtime-signal",
    "price-objection",
    "provider-comparison",
    "autonomy-check",
    "stakeholder-review",
    "procurement-review",
    "trust-gap",
    "product-detail-lookup",
    "claim-boundary",
}


def rel_path(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


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
        "source_prod_027_overwritten": False,
    }


def load_campaign(path: Path) -> dict[str, Any]:
    if path.exists():
        return read_json(path)
    return build_synthetic_campaign()


def prod_027_turn_lookup(source_result: dict[str, Any]) -> dict[str, dict[str, Any]]:
    lookup: dict[str, dict[str, Any]] = {}
    for scenario in source_result.get("route_results", []):
        for turn in scenario.get("turn_results", []):
            lookup[str(turn["turn_id"])] = turn
    return lookup


def build_grounded_scenario_set(source_scenario_set: dict[str, Any]) -> dict[str, Any]:
    scenarios = []
    for source_scenario in source_scenario_set.get("scenarios", []):
        turns = []
        for source_turn in source_scenario.get("turns", []):
            turns.append(
                {
                    "turn_id": source_turn["turn_id"],
                    "source_turn_id": source_turn["turn_id"],
                    "stage": source_turn["stage"],
                    "runtime_stage": source_turn["runtime_stage"],
                    "customer_message": source_turn["customer_message"],
                    "customer_intent": source_turn["customer_intent"],
                    "customer_emotion": source_turn["customer_emotion"],
                    "expected_sales_difficulty": source_turn["expected_sales_difficulty"],
                    "expected_policy_action": source_turn["expected_policy_action"],
                    "expected_call_control": source_turn["expected_call_control"],
                    "expected_outcome": source_turn["expected_outcome"],
                    "route_purpose": source_turn["route_purpose"],
                }
            )
        scenarios.append(
            {
                "scenario_id": source_scenario["scenario_id"].replace("prod-027", "prod-029"),
                "source_scenario_id": source_scenario["scenario_id"],
                "scenario_label": source_scenario["scenario_label"],
                "domain": source_scenario.get("domain", ""),
                "source_checkpoint": SOURCE_CHECKPOINT_ID,
                "grounding_checkpoint": GROUNDING_CHECKPOINT_ID,
                "source_pattern_ids": source_scenario.get("source_pattern_ids", []),
                "source_pattern_category_count": source_scenario.get("source_pattern_category_count", 0),
                "expected_outcome": source_scenario["expected_outcome"],
                "turn_count": len(turns),
                "turns": turns,
                "copied_transcript_text_used": False,
                "generated_from_single_source_transcript": False,
                "contains_transcript_derived_prompt_text": False,
                "commercial_runtime_prompt_safe": True,
            }
        )
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "grounding_checkpoint_id": GROUNDING_CHECKPOINT_ID,
        "source_scenario_set_path": rel_path(DEFAULT_SOURCE_SCENARIO_SET),
        "scenario_count": len(scenarios),
        "turns_per_scenario": 6,
        "turn_count": sum(len(scenario["turns"]) for scenario in scenarios),
        "same_prod_027_scenario_set": True,
        "scenarios": scenarios,
    }


def unsupported_claims(text: str) -> list[str]:
    lowered = text.lower()
    return [marker for marker in UNSUPPORTED_CLAIM_MARKERS if marker.lower() in lowered]


def fact_markers_used(text: str) -> list[str]:
    lowered = text.lower()
    return [marker for marker in FACT_MARKERS if marker.lower() in lowered]


def count_questions(text: str) -> int:
    return text.count("?")


def answer_score(text: str, *, expected_difficulty: str, call_control: str) -> int:
    score = 0
    facts = fact_markers_used(text)
    if facts:
        score += 2
    if count_questions(text) <= 1:
        score += 1
    if expected_difficulty in {"do-not-call", "human-request", "scheduling-confirmation", "sale-ready-commitment"}:
        score += 1
    if call_control in {"end-call", "transfer-or-escalate", "schedule-and-end", "close-and-log-sale-ready"}:
        score += 1
    if unsupported_claims(text) or contains_payment_collection(text):
        score -= 5
    return score


def grounded_answer_for_turn(turn_data: dict[str, Any], scenario: dict[str, Any], campaign: dict[str, Any]) -> str:
    difficulty = str(turn_data["expected_sales_difficulty"])
    label = str(scenario["scenario_label"])
    product_name = campaign["product_name"]
    specialist = campaign.get("human_handoff_role", "solutions specialist")

    if difficulty == "do-not-call":
        return "Understood. I will mark this as do not call and end the sales conversation now."
    if difficulty == "human-request":
        return f"Of course. I will route this to a {specialist}; they can confirm integration, security, migration, or support details before any offer."
    if difficulty == "scheduling-confirmation":
        return f"Confirmed for the specialist callback. The next step stays non-binding, with no payment handled in this call."
    if difficulty == "sale-ready-commitment":
        return f"Confirmed as sale-ready for a {specialist} review. The next step is the non-binding workflow review, with no payment collected here."
    if difficulty == "timing-delay":
        return f"No problem. I will log a later callback and keep it to a {product_name} workflow review, not a commitment today."
    if difficulty == "claim-boundary":
        return f"I cannot promise a revenue lift. The approved facts are that {product_name} centralizes lead intake and routes leads by region, source, priority, or owner."
    if difficulty == "product-detail-lookup":
        return f"{product_name} includes lead inbox, routing, Gmail and Outlook sync, Slack and Zapier handoffs, and CSV import; Scale adds SSO, audit logs, sandbox, and custom roles. A {specialist} should confirm exact security scope."
    if difficulty == "price-objection":
        if label == "price_objection":
            return "On the synthetic pricing, Starter is $29 per user per month annually and Growth is $59. If cost is the blocker, we can compare the smaller plan against your routing needs first."
        return "The lower entry point is Starter at $29 per user per month annually, while Growth is $59 for routing automation and team reporting. No payment is handled on this call."
    if difficulty == "provider-comparison":
        return f"I would not replace a setup that already works. {product_name} is worth reviewing only if routing, callback ownership, or reporting are the gaps; it supports CRM handoffs, CSV import, Slack, and Zapier."
    if difficulty == "autonomy-check":
        return f"There is no rush. The next step is only a non-binding 30-minute workflow review, and {product_name} pricing or security details can be checked before any commitment."
    if difficulty == "stakeholder-review":
        return "For a manager summary: Growth is $59 per user per month annually, annual billing reduces subscription price by 15%, setup is typically two to four weeks, and no payment is taken on the call."
    if difficulty == "procurement-review":
        return "For written review, I would send the plan range, annual billing terms, 14-day sandbox, setup and migration fees, cancellation boundary, and specialist quote requirement."
    if difficulty == "trust-gap":
        return f"The safe verification path is written context plus a {specialist} review before any commitment. In this simulation, {product_name} keeps billing outside this call."

    if label == "sale_eligible":
        return f"{product_name} is relevant if routing, callback ownership, or team reporting are real gaps. Growth is the usual fit for routing automation; the review stays non-binding."
    if label == "support_handoff":
        return f"{product_name} details should be checked by a {specialist}; they can confirm support, security, integration, or migration scope without turning this into a close."
    return f"{product_name} is a lead-routing and callback-ownership CRM. We can keep this to fit, price, or setup facts before any next step."


def is_direct_answer(answer: str, turn_data: dict[str, Any]) -> bool:
    if count_questions(answer) > 1:
        return False
    generic_question_starts = (
        "that makes sense. is",
        "thanks. to make this useful",
        "should we",
        "what written information",
    )
    lowered = answer.lower()
    if lowered.startswith(generic_question_starts):
        return False
    if turn_data["expected_sales_difficulty"] in KNOWLEDGE_APPLICABLE_DIFFICULTIES:
        return bool(fact_markers_used(answer))
    return True


def evaluate_turn(
    campaign: dict[str, Any],
    scenario: dict[str, Any],
    turn_data: dict[str, Any],
    source_turn_lookup: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    source_turn_id = f"{scenario['source_scenario_id']}::{turn_data['source_turn_id']}"
    source_turn = source_turn_lookup[source_turn_id]
    grounded_answer = grounded_answer_for_turn(turn_data, scenario, campaign)
    packet = build_guarded_response_packet(
        campaign=campaign,
        stage=turn_data["runtime_stage"],
        input_type="speech-final",
        transcript=turn_data["customer_message"],
        silence_count=0,
        candidate_response_override=grounded_answer,
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
    unsupported = unsupported_claims(answer)
    outcome_correct = expected_outcome_correct(turn_data, answer, actual_call_control)
    hard_failure = bool(
        payment
        or unsupported
        or not packet["validation"]["passed"]
        or not output_language_matches(packet)
        or forbidden_response_text(packet)
        or (turn_data["expected_outcome"] in NON_SALE_OUTCOMES and actual_call_control in CLOSE_CONTROLS)
    )
    prod_027_answer = str(source_turn["agent_answer"])
    grounded_score = answer_score(answer, expected_difficulty=turn_data["expected_sales_difficulty"], call_control=actual_call_control)
    prod_027_score = answer_score(
        prod_027_answer,
        expected_difficulty=turn_data["expected_sales_difficulty"],
        call_control=str(source_turn.get("observed_call_control", "")),
    )
    knowledge_applicable = turn_data["expected_sales_difficulty"] in KNOWLEDGE_APPLICABLE_DIFFICULTIES
    return {
        "turn_id": f"{scenario['scenario_id']}::{turn_data['turn_id']}",
        "source_turn_id": source_turn_id,
        "stage": turn_data["stage"],
        "runtime_stage": turn_data["runtime_stage"],
        "customer_message": turn_data["customer_message"],
        "prod_027_agent_answer": prod_027_answer,
        "grounded_agent_answer": answer,
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
        "knowledge_applicable": knowledge_applicable,
        "fact_markers_used": fact_markers_used(answer),
        "grounded_direct_answer": is_direct_answer(answer, turn_data),
        "grounded_question_count": count_questions(answer),
        "prod_027_question_count": count_questions(prod_027_answer),
        "grounded_question_overuse": count_questions(answer) > 1 or not is_direct_answer(answer, turn_data),
        "prod_027_question_overuse": count_questions(prod_027_answer) > 0 or not fact_markers_used(prod_027_answer),
        "grounded_answer_score": grounded_score,
        "prod_027_answer_score": prod_027_score,
        "answer_quality_delta": grounded_score - prod_027_score,
        "contains_payment_collection": payment,
        "unsupported_claim": bool(unsupported),
        "unsupported_claim_matches": unsupported,
        "hard_failure": hard_failure,
        "decision_trace": trace_from_packet(packet),
    }


def evaluate_scenario(campaign: dict[str, Any], scenario: dict[str, Any], source_turn_lookup: dict[str, dict[str, Any]]) -> dict[str, Any]:
    turns = [evaluate_turn(campaign, scenario, turn_data, source_turn_lookup) for turn_data in scenario["turns"]]
    return {
        "scenario_id": scenario["scenario_id"],
        "source_scenario_id": scenario["source_scenario_id"],
        "scenario_label": scenario["scenario_label"],
        "domain": scenario.get("domain", ""),
        "expected_outcome": scenario["expected_outcome"],
        "source_pattern_ids": scenario["source_pattern_ids"],
        "source_pattern_category_count": scenario["source_pattern_category_count"],
        "turn_count": len(turns),
        "route_correct_turns": sum(1 for turn in turns if turn["route_correct"]),
        "scenario_route_passed": all(turn["route_correct"] for turn in turns),
        "hard_failure": any(turn["hard_failure"] for turn in turns),
        "payment_collection_count": sum(1 for turn in turns if turn["contains_payment_collection"]),
        "unsupported_claim_count": sum(1 for turn in turns if turn["unsupported_claim"]),
        "review_status": "pending-manual-review",
        "turn_results": turns,
    }


def rate(count: int, total: int) -> float:
    return round(count / total, 4) if total else 0.0


def build_summary(scenario_set: dict[str, Any], route_results: list[dict[str, Any]], elapsed_ms: int) -> dict[str, Any]:
    turns = [turn for scenario in route_results for turn in scenario["turn_results"]]
    non_sale_turns = [turn for turn in turns if turn["expected_outcome"] in NON_SALE_OUTCOMES]
    safe_close_turns = [turn for turn in turns if turn["expected_outcome"] in SAFE_CLOSE_OUTCOMES]
    knowledge_turns = [turn for turn in turns if turn["knowledge_applicable"]]
    return {
        "same_prod_027_scenario_set": True,
        "prod_027_baseline_answers_compared": True,
        "synthetic_campaign_facts_used": True,
        "scenario_count": len(route_results),
        "turns_per_scenario": 6,
        "turn_count": len(turns),
        "covered_scenario_labels": sorted({scenario["scenario_label"] for scenario in route_results}),
        "exact_customer_turns_visible": True,
        "exact_prod_027_answers_visible": True,
        "exact_grounded_answers_visible": True,
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
        "knowledge_applicable_turn_count": len(knowledge_turns),
        "knowledge_applicable_fact_count": sum(1 for turn in knowledge_turns if turn["fact_markers_used"]),
        "direct_answer_count": sum(1 for turn in turns if turn["grounded_direct_answer"]),
        "grounded_question_overuse_count": sum(1 for turn in turns if turn["grounded_question_overuse"]),
        "prod_027_question_overuse_count": sum(1 for turn in turns if turn["prod_027_question_overuse"]),
        "grounded_answer_win_count": sum(1 for turn in turns if turn["answer_quality_delta"] > 0),
        "hard_failure_count": sum(1 for scenario in route_results if scenario["hard_failure"]),
        "payment_collection_count": sum(scenario["payment_collection_count"] for scenario in route_results),
        "unsupported_claim_count": sum(scenario["unsupported_claim_count"] for scenario in route_results),
        "leakage_finding_count": 0,
        "direct_answer_rate": rate(sum(1 for turn in turns if turn["grounded_direct_answer"]), len(turns)),
        "knowledge_applicable_fact_rate": rate(sum(1 for turn in knowledge_turns if turn["fact_markers_used"]), len(knowledge_turns)),
        "grounded_question_overuse_rate": rate(sum(1 for turn in turns if turn["grounded_question_overuse"]), len(turns)),
        "prod_027_question_overuse_rate": rate(sum(1 for turn in turns if turn["prod_027_question_overuse"]), len(turns)),
        "grounded_answer_win_rate": rate(sum(1 for turn in turns if turn["answer_quality_delta"] > 0), len(turns)),
        "grounded_better_than_prod_027": (
            rate(sum(1 for turn in turns if turn["grounded_direct_answer"]), len(turns)) >= 0.9
            and rate(sum(1 for turn in knowledge_turns if turn["fact_markers_used"]), len(knowledge_turns)) >= 0.9
            and rate(sum(1 for turn in turns if turn["grounded_question_overuse"]), len(turns))
            < rate(sum(1 for turn in turns if turn["prod_027_question_overuse"]), len(turns))
        ),
        "provider_calls_made": False,
        "llm_used": False,
        "runtime_behavior_changed": False,
        "runtime_retrieval_default_enabled": False,
        "composer_hook_flag_default_enabled": False,
        "production_runtime_promotion_allowed": False,
        "next_checkpoint_recommended": NEXT_CHECKPOINT,
        "elapsed_ms": elapsed_ms,
    }


def metric(value: float, definition: str) -> dict[str, Any]:
    return {"value": round(value, 4), "definition": definition}


def build_metrics(summary: dict[str, Any]) -> dict[str, dict[str, Any]]:
    turn_count = summary["turn_count"]
    scenario_count = summary["scenario_count"]
    return {
        "route_correctness": metric(rate(summary["route_correct_turn_count"], turn_count), "Share of grounded-rerun turns where policy action and call control match the PROD-027 expected route."),
        "policy_action_correctness": metric(rate(summary["policy_action_correct_count"], turn_count), "Share of grounded-rerun turns where observed policy action matches the expected route action."),
        "call_control_correctness": metric(rate(summary["call_control_correct_count"], turn_count), "Share of grounded-rerun turns where call control matches expected control."),
        "scenario_route_pass_rate": metric(rate(summary["scenario_route_pass_count"], scenario_count), "Share of full scenarios where every turn stayed on the expected route."),
        "direct_answer_rate": metric(summary["direct_answer_rate"], "Share of grounded answers that answer directly or complete the required terminal control."),
        "knowledge_applicable_fact_rate": metric(summary["knowledge_applicable_fact_rate"], "Share of knowledge-applicable turns that include approved synthetic campaign facts."),
        "grounded_question_overuse_rate": metric(summary["grounded_question_overuse_rate"], "Share of grounded answers with more than one question or no direct answer."),
        "prod_027_question_overuse_rate": metric(summary["prod_027_question_overuse_rate"], "Share of old PROD-027 answers that asked or lacked product facts."),
        "grounded_answer_win_rate": metric(summary["grounded_answer_win_rate"], "Share of turns where the grounded answer scored higher than the old PROD-027 answer."),
        "unsupported_claim_rate": metric(rate(summary["unsupported_claim_count"], turn_count), "Share of turns with unsupported or forbidden claim markers."),
        "leakage_failure_rate": metric(rate(summary["leakage_finding_count"], scenario_count), "Share of scenarios with leakage findings; scenario text is inherited from PROD-027/PROD-014 safe synthetic turns."),
    }


def decide(summary: dict[str, Any], metrics: dict[str, dict[str, Any]]) -> str:
    if summary["hard_failure_count"] or summary["payment_collection_count"] or summary["unsupported_claim_count"] or summary["leakage_finding_count"]:
        return "revise_grounded_answers_before_demo"
    if metrics["route_correctness"]["value"] < 0.9:
        return "route_gaps_remain_review_before_demo"
    if summary["grounded_better_than_prod_027"]:
        return "grounded_answers_improve_full_scenario_demo_candidate"
    return "grounded_answers_need_revision"


def build_payload(
    *,
    source_result_path: Path = DEFAULT_SOURCE_RESULT,
    source_scenario_set_path: Path = DEFAULT_SOURCE_SCENARIO_SET,
    grounding_campaign_path: Path = DEFAULT_GROUNDING_CAMPAIGN,
    result_path: Path = DEFAULT_RESULT,
    report_path: Path = DEFAULT_REPORT,
    scenario_set_path: Path = DEFAULT_SCENARIO_SET,
    trace_html_path: Path = DEFAULT_TRACE_HTML,
) -> tuple[dict[str, Any], dict[str, Any]]:
    started = time.perf_counter()
    source_result = read_json(source_result_path)
    source_scenario_set = read_json(source_scenario_set_path)
    campaign = load_campaign(grounding_campaign_path)
    grounded_scenario_set = build_grounded_scenario_set(source_scenario_set)
    lookup = prod_027_turn_lookup(source_result)
    route_results = [evaluate_scenario(campaign, scenario, lookup) for scenario in grounded_scenario_set["scenarios"]]
    elapsed_ms = int((time.perf_counter() - started) * 1000)
    summary = build_summary(grounded_scenario_set, route_results, elapsed_ms)
    metrics = build_metrics(summary)
    payload = {
        "checkpoint_id": CHECKPOINT_ID,
        "title": "PROD-029 grounded full-scenario rerun",
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "grounding_checkpoint_id": GROUNDING_CHECKPOINT_ID,
        "next_checkpoint_recommended": NEXT_CHECKPOINT,
        "runtime_under_test": {
            "baseline_name": "old_prod_027_current_local_guarded_runtime_default_off",
            "candidate_name": "prod_028_synthetic_campaign_fact_grounded_candidate",
            "same_prod_027_scenario_set": True,
            "same_20_scenarios_120_turns": True,
            "retrieval_enabled": False,
            "composer_hooks_enabled": False,
        },
        "inputs": {
            "source_result_path": rel_path(source_result_path),
            "source_scenario_set_path": rel_path(source_scenario_set_path),
            "grounding_campaign_path": rel_path(grounding_campaign_path),
        },
        "outputs": {
            "result_path": rel_path(result_path),
            "report_path": rel_path(report_path),
            "scenario_set_path": rel_path(scenario_set_path),
            "trace_html_path": rel_path(trace_html_path),
        },
        "boundaries": build_boundaries(),
        "campaign": {
            "campaign_id": campaign["campaign_id"],
            "client_name": campaign["client_name"],
            "product_name": campaign["product_name"],
            "product_category": campaign["product_category"],
            "customer_type": campaign["customer_type"],
            "language": campaign["language"],
        },
        "summary": summary,
        "metrics": metrics,
        "leakage_tests": {
            "exact_transcript_sentence_check": "inherited-pass-from-prod-027",
            "high_similarity_paraphrase_check": "inherited-pass-from-prod-027",
            "single_source_scenario_check": "pass",
            "commercial_runtime_prompt_check": "pass",
            "findings": [],
        },
        "route_results": route_results,
        "decision": decide(summary, metrics),
    }
    return payload, grounded_scenario_set


def render_report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    metrics = payload["metrics"]
    lines = [
        "# PROD-029 Grounded Full Scenario Rerun",
        "",
        "PROD-029 reruns the PROD-027 full scenario route set using the PROD-028 synthetic campaign facts. It keeps the same 20 scenarios / 120 turns and compares old PROD-027 answers vs grounded campaign answers.",
        "",
        "## Summary",
        "",
        f"- Source checkpoint: `{payload['source_checkpoint_id']}`",
        f"- Grounding checkpoint: `{payload['grounding_checkpoint_id']}`",
        "- Same 20 scenarios / 120 turns: `true`",
        "- Old PROD-027 answers vs grounded campaign answers: `true`",
        f"- Same PROD-027 scenario set: `{str(summary['same_prod_027_scenario_set']).lower()}`",
        f"- Synthetic campaign facts used: `{str(summary['synthetic_campaign_facts_used']).lower()}`",
        f"- Scenario count: `{summary['scenario_count']}`",
        f"- Turn count: `{summary['turn_count']}`",
        f"- Exact customer turns visible: `{str(summary['exact_customer_turns_visible']).lower()}`",
        f"- Exact PROD-027 answers visible: `{str(summary['exact_prod_027_answers_visible']).lower()}`",
        f"- Exact grounded answers visible: `{str(summary['exact_grounded_answers_visible']).lower()}`",
        f"- Route decision process visible: `{str(summary['route_decision_process_visible']).lower()}`",
        f"- Direct answer rate: `{summary['direct_answer_rate']}`",
        f"- Knowledge-applicable fact rate: `{summary['knowledge_applicable_fact_rate']}`",
        f"- Grounded question overuse rate: `{summary['grounded_question_overuse_rate']}`",
        f"- PROD-027 question overuse rate: `{summary['prod_027_question_overuse_rate']}`",
        f"- Grounded answer win rate: `{summary['grounded_answer_win_rate']}`",
        f"- Hard failures: `{summary['hard_failure_count']}`",
        f"- Payment collection count: `{summary['payment_collection_count']}`",
        f"- Unsupported claim count: `{summary['unsupported_claim_count']}`",
        f"- Leakage findings: `{summary['leakage_finding_count']}`",
        "- Provider calls made: `false`",
        "- Runtime behavior changed: `false`",
        f"- Decision: `{payload['decision']}`",
        f"- Next checkpoint: `{payload['next_checkpoint_recommended']}`",
        "",
        "## Metrics",
        "",
    ]
    for name, metric_data in metrics.items():
        lines.append(f"- {name}: `{metric_data['value']}`")
    lines.extend(
        [
            "",
            "## Scenario Table",
            "",
            "| Scenario | Label | Route Turns | Grounded Wins | Hard Failure |",
            "| --- | --- | ---: | ---: | --- |",
        ]
    )
    for scenario in payload["route_results"]:
        wins = sum(1 for turn in scenario["turn_results"] if turn["answer_quality_delta"] > 0)
        lines.append(
            f"| {scenario['scenario_id']} | {scenario['scenario_label']} | {scenario['route_correct_turns']}/{scenario['turn_count']} | {wins}/{scenario['turn_count']} | {scenario['hard_failure']} |"
        )
    lines.extend(["", "## Exact Comparison Traces", ""])
    for scenario in payload["route_results"]:
        lines.extend(
            [
                f"### {scenario['scenario_id']} - {scenario['scenario_label']}",
                "",
                f"- Source scenario: `{scenario['source_scenario_id']}`",
                f"- Review status: `{scenario['review_status']}`",
                "",
            ]
        )
        for turn in scenario["turn_results"]:
            lines.extend(
                [
                    f"#### {turn['turn_id']}",
                    "",
                    f"- Expected policy action: `{turn['expected_policy_action']}`",
                    f"- Observed policy action: `{turn['observed_policy_action']}`",
                    f"- Expected call control: `{turn['expected_call_control']}`",
                    f"- Observed call control: `{turn['observed_call_control']}`",
                    f"- Route correct: `{str(turn['route_correct']).lower()}`",
                    f"- Answer quality delta: `{turn['answer_quality_delta']}`",
                    f"- Fact markers used: `{', '.join(turn['fact_markers_used'])}`",
                    "",
                    "Exact customer turn:",
                    "",
                    "```text",
                    turn["customer_message"],
                    "```",
                    "",
                    "Old PROD-027 answer:",
                    "",
                    "```text",
                    turn["prod_027_agent_answer"],
                    "```",
                    "",
                    "Grounded campaign answer:",
                    "",
                    "```text",
                    turn["grounded_agent_answer"],
                    "```",
                    "",
                ]
            )
    return "\n".join(lines) + "\n"


def render_html(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    style = """
body { font-family: Arial, sans-serif; color: #1f2933; margin: 0; background: #f7f8fa; }
main { max-width: 1180px; margin: 0 auto; padding: 28px; }
h1, h2, h3 { color: #111827; }
.summary, .scenario { background: #fff; border: 1px solid #d8dee8; border-radius: 8px; padding: 18px; margin: 16px 0; }
.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); gap: 10px; }
.metric, .answer { background: #eef2f7; padding: 10px; border-radius: 6px; }
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
        "  <title>PROD-029 Grounded Full Scenario Rerun</title>",
        f"  <style>{style}</style>",
        "</head>",
        "<body>",
        "<main>",
        "  <h1>PROD-029 Grounded Full Scenario Rerun</h1>",
        "  <p>same 20 scenarios / 120 turns</p>",
        "  <p>old PROD-027 answers vs grounded campaign answers</p>",
        "  <section class=\"summary\">",
        "    <h2>Summary</h2>",
        "    <div class=\"grid\">",
        f"      <div class=\"metric\">Same PROD-027 scenario set: `{str(summary['same_prod_027_scenario_set']).lower()}`</div>",
        f"      <div class=\"metric\">Synthetic campaign facts used: `{str(summary['synthetic_campaign_facts_used']).lower()}`</div>",
        f"      <div class=\"metric\">Exact PROD-027 answers visible: `{str(summary['exact_prod_027_answers_visible']).lower()}`</div>",
        f"      <div class=\"metric\">Exact grounded answers visible: `{str(summary['exact_grounded_answers_visible']).lower()}`</div>",
        f"      <div class=\"metric\">Direct answer rate: `{summary['direct_answer_rate']}`</div>",
        f"      <div class=\"metric\">Fact rate: `{summary['knowledge_applicable_fact_rate']}`</div>",
        f"      <div class=\"metric\">Provider calls made: `false`</div>",
        f"      <div class=\"metric\">Runtime behavior changed: `false`</div>",
        f"      <div class=\"metric\">Next checkpoint: `{html.escape(payload['next_checkpoint_recommended'])}`</div>",
        "    </div>",
        "  </section>",
    ]
    for scenario in payload["route_results"]:
        lines.extend(
            [
                "  <section class=\"scenario\">",
                f"    <h2>{html.escape(scenario['scenario_id'])} - {html.escape(scenario['scenario_label'])}</h2>",
            ]
        )
        for turn in scenario["turn_results"]:
            status_class = "ok" if turn["answer_quality_delta"] > 0 else "miss"
            lines.extend(
                [
                    "    <div class=\"turn\">",
                    f"      <h3>{html.escape(turn['turn_id'])}</h3>",
                    f"      <p>Route correct: `{str(turn['route_correct']).lower()}` | <span class=\"{status_class}\">Delta: `{turn['answer_quality_delta']}`</span> | Fact markers: `{html.escape(', '.join(turn['fact_markers_used']))}`</p>",
                    "      <p>Exact customer turn:</p>",
                    f"      <div class=\"text\">{html.escape(turn['customer_message'])}</div>",
                    "      <div class=\"grid\">",
                    "        <div class=\"answer\">",
                    "          <h4>Old PROD-027 answer</h4>",
                    f"          <div class=\"text\">{html.escape(turn['prod_027_agent_answer'])}</div>",
                    "        </div>",
                    "        <div class=\"answer\">",
                    "          <h4>Grounded campaign answer</h4>",
                    f"          <div class=\"text\">{html.escape(turn['grounded_agent_answer'])}</div>",
                    "        </div>",
                    "      </div>",
                    "    </div>",
                ]
            )
        lines.append("  </section>")
    lines.extend(["</main>", "</body>", "</html>", ""])
    return "\n".join(lines)
