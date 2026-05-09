#!/usr/bin/env python3
from __future__ import annotations

import json
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from callcenteren_scenario_bank import (
    DEFAULT_RAW_ZIP_DIR,
    detect_prod_014_leakage,
    leakage_status,
)
from generate_guarded_response import (
    DEFAULT_RETRIEVAL_ACCEPTABLE_MS,
    DEFAULT_RETRIEVAL_MIN_SCORE,
    DEFAULT_RETRIEVAL_REGISTRY,
    DEFAULT_RETRIEVAL_TARGET_MS,
    build_guarded_response_packet,
)
from realtime_turn_cli import find_campaign
from run_realtime_turn_simulation import load_realtime_cases
from run_resp_001_retrieval_ab_evaluation import forbidden_response_text, output_language_matches


ROOT = Path(__file__).resolve().parents[1]
PROD_015_ID = "PROD-015-callcenteren-runtime-comparison"
PROD_014_ID = "PROD-014-callcenteren-scenario-bank"
DEFAULT_SCENARIO_BANK = ROOT / "research" / "experiments" / "generated" / "PROD-014-callcenteren-scenario-bank" / "scenario-bank.json"
DEFAULT_CAMPAIGN_CASE_SOURCE = ROOT / "research" / "experiments" / "cases" / "prod-005-realtime-latency-call-control.json"
DEFAULT_CAMPAIGN_ID = "campaign-prod-005-b2b-software"
DEFAULT_LIMIT_SCENARIOS = 60
NON_SALE_OUTCOMES = {"non_sale_correct", "support_only", "human_handoff", "end_call"}
SAFE_CLOSE_OUTCOMES = {"sale_ready", "callback_agreed"}
CLOSE_CONTROLS = {"close-and-log-sale-ready", "log-sale-ready"}
PAYMENT_TOKENS = ["credit card", "take your payment", "collect payment", "payment now", "card number"]
SALE_CLOSE_TOKENS = ["sale_ready", "process the sale", "take your payment", "collect payment"]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def rel_path(path: Path, *, root: Path = ROOT) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def normalize_stage(stage: str) -> str:
    if stage in {"callback_scheduling", "commitment_confirmation"}:
        return "scheduling"
    if stage in {"price_discussion", "objection_handling", "clarification", "trial_close", "close_attempt"}:
        return "relevance-check"
    if stage in {"handoff", "escalation", "support"}:
        return "product-detail-check"
    return "relevance-check"


def select_stratified_scenarios(scenarios: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    if limit <= 0 or limit >= len(scenarios):
        return list(scenarios)
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for scenario in scenarios:
        grouped[str(scenario.get("scenario_label", "unknown"))].append(scenario)
    selected: list[dict[str, Any]] = []
    label_order = sorted(grouped)
    while len(selected) < limit and any(grouped.values()):
        for label in label_order:
            if grouped[label] and len(selected) < limit:
                selected.append(grouped[label].pop(0))
    return selected


def contains_any(text: str, tokens: list[str]) -> bool:
    lowered = text.lower()
    return any(token in lowered for token in tokens)


def contains_payment_collection(text: str) -> bool:
    return contains_any(text, PAYMENT_TOKENS)


def contains_sale_close_language(text: str) -> bool:
    return contains_any(text, SALE_CLOSE_TOKENS)


def has_discovery_question(text: str) -> bool:
    lowered = text.lower()
    return "?" in text or any(
        token in lowered
        for token in [
            "is your main",
            "should i",
            "would it help",
            "may i ask",
            "what is",
            "what would",
            "which",
            "whether",
        ]
    )


def has_acknowledgement(text: str) -> bool:
    lowered = text.lower()
    return any(
        token in lowered
        for token in [
            "that makes sense",
            "i understand",
            "i hear",
            "fair",
            "of course",
            "understood",
            "thanks",
            "good question",
            "i do not want",
        ]
    )


def has_support_boundary(text: str) -> bool:
    lowered = text.lower()
    return any(token in lowered for token in ["route", "specialist", "human", "check the approved", "do not guess", "not called again"])


def expected_outcome_correct(row: dict[str, Any], response: str, call_control: str) -> bool:
    expected = row["expected_outcome"]
    if expected in NON_SALE_OUTCOMES:
        return not contains_sale_close_language(response) and not contains_payment_collection(response) and call_control not in CLOSE_CONTROLS
    if expected in SAFE_CLOSE_OUTCOMES:
        return not contains_payment_collection(response)
    return not contains_payment_collection(response)


def score_response(row: dict[str, Any], response: str, packet: dict[str, Any]) -> dict[str, Any]:
    expected_ok = expected_outcome_correct(row, response, packet["decision_snapshot"]["call_control"])
    discovery_ok = has_discovery_question(response)
    emotion_ok = has_acknowledgement(response)
    boundary_ok = True
    if row["expected_outcome"] in {"support_only", "human_handoff", "end_call"}:
        boundary_ok = has_support_boundary(response) or packet["decision_snapshot"]["call_control"] in {"end-call", "bridge-then-continue"}
    no_payment = not contains_payment_collection(response)
    score = sum(1 for check in [expected_ok, discovery_ok, emotion_ok, boundary_ok, no_payment] if check)
    return {
        "score": score,
        "expected_outcome_correct": expected_ok,
        "discovery_before_close": discovery_ok,
        "emotional_handling": emotion_ok,
        "boundary_correct": boundary_ok,
        "contains_payment_collection": not no_payment,
    }


def run_packet(
    *,
    campaign: dict[str, Any],
    stage: str,
    customer_question: str,
    retrieval_enabled: bool,
    registry_path: Path,
    max_results: int,
    min_score: int,
    target_latency_ms: int,
    acceptable_latency_ms: int,
) -> dict[str, Any]:
    return build_guarded_response_packet(
        campaign=campaign,
        stage=stage,
        input_type="speech-final",
        transcript=customer_question,
        silence_count=0,
        retrieval_enabled=retrieval_enabled,
        retrieval_registry_path=registry_path if retrieval_enabled else None,
        retrieval_max_results=max_results,
        retrieval_min_score=min_score,
        retrieval_target_latency_ms=target_latency_ms,
        retrieval_acceptable_latency_ms=acceptable_latency_ms,
    )


def row_from_turn(
    *,
    scenario: dict[str, Any],
    turn: dict[str, Any],
    turn_index: int,
    campaign_id: str,
    old_packet: dict[str, Any],
    retrieval_packet: dict[str, Any],
) -> dict[str, Any]:
    customer_question = str(turn.get("customer_prompt", ""))
    base = {
        "scenario_id": scenario["scenario_id"],
        "scenario_label": scenario["scenario_label"],
        "domain": scenario.get("domain", ""),
        "turn_id": f"{scenario['scenario_id']}::{turn.get('turn_id', f'turn-{turn_index:03d}')}",
        "turn_index": turn_index,
        "stage": normalize_stage(str(turn.get("stage", ""))),
        "campaign_id": campaign_id,
        "customer_question": customer_question,
        "customer_intent": turn.get("customer_intent", scenario.get("initial_intent", "")),
        "customer_emotion": turn.get("customer_emotion", scenario.get("starting_emotion", "")),
        "expected_outcome": scenario["expected_outcome"],
        "expected_agent_response_requirements": turn.get("expected_agent_response_requirements", []),
        "avoid": turn.get("avoid", scenario.get("bad_tactics_to_avoid", [])),
        "source_pattern_ids": scenario.get("source_pattern_ids", []),
        "source_pattern_categories": scenario.get("source_recipe", {}).get("source_pattern_categories", []),
    }
    old_answer = old_packet["final_response"]
    retrieval_answer = retrieval_packet["final_response"]
    old_score = score_response(base, old_answer, old_packet)
    retrieval_score = score_response(base, retrieval_answer, retrieval_packet)
    delta = retrieval_score["score"] - old_score["score"]
    winner = "retrieval" if delta > 0 else "old_runtime" if delta < 0 else "tie"
    retrieval = retrieval_packet["retrieval"]
    hard_failure = not (
        old_packet["validation"]["passed"]
        and retrieval_packet["validation"]["passed"]
        and output_language_matches(old_packet)
        and output_language_matches(retrieval_packet)
        and not forbidden_response_text(old_packet)
        and not forbidden_response_text(retrieval_packet)
        and retrieval_packet["core_pack"]["campaign_facts_override_rag"] is True
        and retrieval_score["expected_outcome_correct"]
        and not retrieval_score["contains_payment_collection"]
    )
    base.update(
        {
            "old_runtime_answer": old_answer,
            "retrieval_runtime_answer": retrieval_answer,
            "old_runtime_score": old_score["score"],
            "retrieval_runtime_score": retrieval_score["score"],
            "score_delta": delta,
            "winner": winner,
            "retrieval_status": retrieval["status"],
            "retrieval_used_in_runtime": retrieval["retrieval_used_in_runtime"],
            "retrieved_item_ids": retrieval["retrieved_item_ids"],
            "retrieval_elapsed_ms": retrieval["latency"]["elapsed_ms"],
            "retrieval_target_ms": retrieval["latency"]["target_ms"],
            "retrieval_acceptable_ms": retrieval["latency"]["acceptable_ms"],
            "hard_failure": hard_failure,
            "contains_payment_collection": retrieval_score["contains_payment_collection"],
            "non_sale_correct": retrieval_score["expected_outcome_correct"] if base["expected_outcome"] in NON_SALE_OUTCOMES else None,
            "safe_close_correct": retrieval_score["expected_outcome_correct"] if base["expected_outcome"] in SAFE_CLOSE_OUTCOMES else None,
            "discovery_before_close": retrieval_score["discovery_before_close"],
            "emotional_handling": retrieval_score["emotional_handling"],
            "decision_trace": {
                "old_runtime": {
                    "retrieval_enabled": False,
                    "sales_difficulty": old_packet["decision_snapshot"]["sales_difficulty"],
                    "detected_emotion": old_packet["decision_snapshot"]["detected_emotion"],
                    "selected_strategy": old_packet["decision_snapshot"]["selected_strategy"],
                    "next_action": old_packet["decision_snapshot"]["next_action"],
                    "call_control": old_packet["decision_snapshot"]["call_control"],
                    "policy_response": old_packet["policy_response"],
                    "candidate_response": old_packet["candidate_response"],
                    "validation_passed": old_packet["validation"]["passed"],
                    "fallback_used": old_packet["validation"]["fallback_used"],
                    "final_response": old_answer,
                },
                "retrieval_runtime": {
                    "retrieval_enabled": True,
                    "sales_difficulty": retrieval_packet["decision_snapshot"]["sales_difficulty"],
                    "detected_emotion": retrieval_packet["decision_snapshot"]["detected_emotion"],
                    "selected_strategy": retrieval_packet["decision_snapshot"]["selected_strategy"],
                    "next_action": retrieval_packet["decision_snapshot"]["next_action"],
                    "call_control": retrieval_packet["decision_snapshot"]["call_control"],
                    "retrieval_status": retrieval["status"],
                    "retrieval_decision": retrieval["retrieval_decision"],
                    "retrieved_item_ids": retrieval["retrieved_item_ids"],
                    "advisory_hints": retrieval.get("advisory_hints", []),
                    "context_flags": retrieval.get("context_flags", []),
                    "blocked_reason": retrieval.get("blocked_reason", ""),
                    "retrieval_used_in_runtime": retrieval["retrieval_used_in_runtime"],
                    "policy_response": retrieval_packet["policy_response"],
                    "candidate_response": retrieval_packet["candidate_response"],
                    "validation_passed": retrieval_packet["validation"]["passed"],
                    "fallback_used": retrieval_packet["validation"]["fallback_used"],
                    "final_response": retrieval_answer,
                },
                "scoring": {
                    "old_runtime": old_score,
                    "retrieval_runtime": retrieval_score,
                    "winner": winner,
                    "hard_failure": hard_failure,
                },
            },
        }
    )
    return base


def summarize_scenarios(scenarios: list[dict[str, Any]], rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows_by_scenario: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        rows_by_scenario[row["scenario_id"]].append(row)
    summaries: list[dict[str, Any]] = []
    for scenario in scenarios:
        scenario_rows = rows_by_scenario.get(scenario["scenario_id"], [])
        summaries.append(
            {
                "scenario_id": scenario["scenario_id"],
                "scenario_label": scenario["scenario_label"],
                "domain": scenario.get("domain", ""),
                "expected_outcome": scenario["expected_outcome"],
                "turn_count": len(scenario_rows),
                "hard_failure": any(row["hard_failure"] for row in scenario_rows),
                "retrieval_wins": sum(1 for row in scenario_rows if row["winner"] == "retrieval"),
                "old_runtime_wins": sum(1 for row in scenario_rows if row["winner"] == "old_runtime"),
                "ties": sum(1 for row in scenario_rows if row["winner"] == "tie"),
                "non_sale_correct": all(row["non_sale_correct"] is not False for row in scenario_rows)
                if scenario["expected_outcome"] in NON_SALE_OUTCOMES
                else None,
                "safe_close_correct": all(row["safe_close_correct"] is not False for row in scenario_rows)
                if scenario["expected_outcome"] in SAFE_CLOSE_OUTCOMES
                else None,
            }
        )
    return summaries


def average_bool(rows: list[dict[str, Any]], field: str) -> float:
    if not rows:
        return 0.0
    return round(sum(1 for row in rows if row.get(field) is True) / len(rows), 4)


def build_summary(
    *,
    source_bank: dict[str, Any],
    selected_scenarios: list[dict[str, Any]],
    rows: list[dict[str, Any]],
    findings: list[Any],
    transient_sentence_count: int,
    limit_scenarios: int,
    started_at: float,
    completed_at: float,
) -> dict[str, Any]:
    non_sale_rows = [row for row in rows if row["expected_outcome"] in NON_SALE_OUTCOMES]
    safe_close_rows = [row for row in rows if row["expected_outcome"] in SAFE_CLOSE_OUTCOMES]
    labels = sorted({scenario["scenario_label"] for scenario in selected_scenarios})
    latencies = [row["retrieval_elapsed_ms"] for row in rows]
    hard_failure_scenario_ids = sorted({row["scenario_id"] for row in rows if row["hard_failure"]} | {finding.scenario_id for finding in findings})
    return {
        "source_bank_scenario_count": int(source_bank.get("summary", {}).get("scenario_count", len(source_bank.get("scenario_bank", [])))),
        "limit_scenarios": limit_scenarios,
        "stratified_slice": 0 < limit_scenarios < len(source_bank.get("scenario_bank", [])),
        "evaluated_scenario_count": len(selected_scenarios),
        "evaluated_turn_count": len(rows),
        "covered_scenario_labels": labels,
        "covered_domain_count": len({scenario.get("domain", "") for scenario in selected_scenarios}),
        "hard_failure_count": len(hard_failure_scenario_ids),
        "hard_failure_scenario_ids": hard_failure_scenario_ids,
        "non_sale_turn_count": len(non_sale_rows),
        "non_sale_correct_count": sum(1 for row in non_sale_rows if row["non_sale_correct"] is True),
        "safe_close_turn_count": len(safe_close_rows),
        "safe_close_correct_count": sum(1 for row in safe_close_rows if row["safe_close_correct"] is True),
        "discovery_before_close_count": sum(1 for row in rows if row["discovery_before_close"]),
        "emotional_handling_count": sum(1 for row in rows if row["emotional_handling"]),
        "old_runtime_total_score": sum(row["old_runtime_score"] for row in rows),
        "retrieval_runtime_total_score": sum(row["retrieval_runtime_score"] for row in rows),
        "retrieval_turn_wins": sum(1 for row in rows if row["winner"] == "retrieval"),
        "old_runtime_turn_wins": sum(1 for row in rows if row["winner"] == "old_runtime"),
        "tie_turns": sum(1 for row in rows if row["winner"] == "tie"),
        "retrieval_influenced_count": sum(1 for row in rows if row["retrieval_used_in_runtime"]),
        "retrieval_blocked_count": sum(1 for row in rows if row["retrieval_status"] == "blocked"),
        "retrieval_no_match_count": sum(1 for row in rows if row["retrieval_status"] == "no_match"),
        "retrieval_retrieved_not_used_count": sum(1 for row in rows if row["retrieval_status"] == "retrieved_not_used"),
        "retrieval_over_acceptable_count": sum(1 for row in rows if row["retrieval_elapsed_ms"] > row["retrieval_acceptable_ms"]),
        "max_retrieval_elapsed_ms": max(latencies) if latencies else 0,
        "avg_retrieval_elapsed_ms": round(sum(latencies) / len(latencies), 2) if latencies else 0,
        "transient_source_sentence_count": transient_sentence_count,
        "leakage_finding_count": len(findings),
        "provider_calls_made": False,
        "llm_used": False,
        "download_performed": False,
        "runtime_behavior_changed": False,
        "runtime_retrieval_default_enabled": False,
        "raw_dataset_text_stored": False,
        "ready_for_review": not hard_failure_scenario_ids and not findings,
        "elapsed_ms": int((completed_at - started_at) * 1000),
    }


def build_metrics(summary: dict[str, Any], findings: list[Any]) -> dict[str, dict[str, Any]]:
    scenario_count = max(summary["evaluated_scenario_count"], 1)
    turn_count = max(summary["evaluated_turn_count"], 1)
    non_sale_count = max(summary["non_sale_turn_count"], 1)
    safe_close_count = max(summary["safe_close_turn_count"], 1)
    return {
        "hard_failure_rate": {
            "value": round(summary["hard_failure_count"] / scenario_count, 4),
            "definition": "Share of evaluated scenarios with safety, leakage, non-sale, validation, or payment-collection hard failures.",
        },
        "non_sale_correctness": {
            "value": round(summary["non_sale_correct_count"] / non_sale_count, 4),
            "definition": "Share of non-sale expected turns where the retrieval runtime avoids sale close and payment collection.",
        },
        "safe_close_correctness": {
            "value": round(summary["safe_close_correct_count"] / safe_close_count, 4),
            "definition": "Share of sale-ready/callback turns where the retrieval runtime avoids payment collection and remains within safe-close rules.",
        },
        "discovery_before_close_rate": {
            "value": round(summary["discovery_before_close_count"] / turn_count, 4),
            "definition": "Share of turns where the retrieval runtime asks a focused question or clarification before any close.",
        },
        "emotional_handling_score": {
            "value": round(summary["emotional_handling_count"] / turn_count, 4),
            "definition": "Share of turns where the retrieval runtime acknowledges or responds constructively without claiming hidden emotion certainty.",
        },
        "leakage_failure_rate": {
            "value": round(len(findings) / scenario_count, 4),
            "definition": "Share of evaluated scenarios with exact sentence, high-similarity, single-source, copied-text, or commercial prompt contamination findings.",
        },
        "retrieval_win_rate": {
            "value": round(summary["retrieval_turn_wins"] / turn_count, 4),
            "definition": "Share of evaluated turns where the retrieval runtime outscored the old retrieval-disabled runtime.",
        },
    }


def decide(summary: dict[str, Any]) -> str:
    if summary["hard_failure_count"]:
        return "revise_before_prod_015_reuse"
    if summary["retrieval_over_acceptable_count"]:
        return "revise_retrieval_latency_before_runtime_use"
    if summary["retrieval_runtime_total_score"] > summary["old_runtime_total_score"]:
        return "ready_for_review_retrieval_runtime_beats_old_runtime_on_slice"
    return "ready_for_review_no_retrieval_gain_on_slice"


def build_payload(
    scenario_bank_path: Path,
    *,
    registry_path: Path = DEFAULT_RETRIEVAL_REGISTRY,
    campaign_case_source: Path = DEFAULT_CAMPAIGN_CASE_SOURCE,
    campaign_id: str = DEFAULT_CAMPAIGN_ID,
    limit_scenarios: int = DEFAULT_LIMIT_SCENARIOS,
    raw_zip_dir: Path | None = None,
    leakage_sentence_limit: int = 5000,
) -> dict[str, Any]:
    started_at = time.perf_counter()
    source_bank = load_json(scenario_bank_path)
    all_scenarios = list(source_bank.get("scenario_bank", []))
    selected_scenarios = select_stratified_scenarios(all_scenarios, limit_scenarios)
    source_sentences: list[str] = []
    if raw_zip_dir is not None and raw_zip_dir.exists() and leakage_sentence_limit > 0:
        from full_sale_scenario_grounding import collect_transient_sentences_from_zip_dir

        source_sentences = collect_transient_sentences_from_zip_dir(raw_zip_dir, limit=leakage_sentence_limit)
    findings = detect_prod_014_leakage(selected_scenarios, source_sentences, [])

    campaigns, _cases = load_realtime_cases(campaign_case_source)
    campaign = find_campaign(campaigns, campaign_id)
    rows: list[dict[str, Any]] = []
    for scenario in selected_scenarios:
        for index, turn in enumerate(scenario.get("turns", []), start=1):
            question = str(turn.get("customer_prompt", ""))
            stage = normalize_stage(str(turn.get("stage", "")))
            old_packet = run_packet(
                campaign=campaign,
                stage=stage,
                customer_question=question,
                retrieval_enabled=False,
                registry_path=registry_path,
                max_results=4,
                min_score=DEFAULT_RETRIEVAL_MIN_SCORE,
                target_latency_ms=DEFAULT_RETRIEVAL_TARGET_MS,
                acceptable_latency_ms=DEFAULT_RETRIEVAL_ACCEPTABLE_MS,
            )
            retrieval_packet = run_packet(
                campaign=campaign,
                stage=stage,
                customer_question=question,
                retrieval_enabled=True,
                registry_path=registry_path,
                max_results=4,
                min_score=DEFAULT_RETRIEVAL_MIN_SCORE,
                target_latency_ms=DEFAULT_RETRIEVAL_TARGET_MS,
                acceptable_latency_ms=DEFAULT_RETRIEVAL_ACCEPTABLE_MS,
            )
            rows.append(
                row_from_turn(
                    scenario=scenario,
                    turn=turn,
                    turn_index=index,
                    campaign_id=campaign_id,
                    old_packet=old_packet,
                    retrieval_packet=retrieval_packet,
                )
            )
    completed_at = time.perf_counter()
    summary = build_summary(
        source_bank=source_bank,
        selected_scenarios=selected_scenarios,
        rows=rows,
        findings=findings,
        transient_sentence_count=len(source_sentences),
        limit_scenarios=limit_scenarios,
        started_at=started_at,
        completed_at=completed_at,
    )
    return {
        "prod_015_id": PROD_015_ID,
        "title": "PROD-015 CallCenterEN runtime comparison",
        "source_scenario_bank": {
            "prod_014_id": source_bank.get("prod_014_id", ""),
            "path": rel_path(scenario_bank_path),
            "scenario_count": source_bank.get("summary", {}).get("scenario_count", len(all_scenarios)),
            "turn_count": source_bank.get("summary", {}).get("turn_count", 0),
            "scenario_generation_mode": source_bank.get("scenario_generation", {}).get("mode", ""),
        },
        "dataset_source": source_bank["dataset_source"],
        "runtime_comparison": {
            "baseline_name": "old_runtime_retrieval_disabled",
            "candidate_name": "retrieval_runtime_rag_018_enabled",
            "campaign_case_source": rel_path(campaign_case_source),
            "campaign_id": campaign_id,
            "retrieval_registry_path": rel_path(registry_path),
            "limit_scenarios": limit_scenarios,
            "stratified_slice": summary["stratified_slice"],
        },
        "summary": summary,
        "metrics": build_metrics(summary, findings),
        "comparison": {
            "baseline_name": "old_runtime_retrieval_disabled",
            "candidate_name": "retrieval_runtime_rag_018_enabled",
            "old_runtime_total_score": summary["old_runtime_total_score"],
            "retrieval_runtime_total_score": summary["retrieval_runtime_total_score"],
            "score_delta": summary["retrieval_runtime_total_score"] - summary["old_runtime_total_score"],
            "retrieval_turn_wins": summary["retrieval_turn_wins"],
            "old_runtime_turn_wins": summary["old_runtime_turn_wins"],
            "tie_turns": summary["tie_turns"],
            "retrieval_influenced_count": summary["retrieval_influenced_count"],
        },
        "leakage_tests": {
            "exact_transcript_sentence_check": {"status": leakage_status(findings, "exact_transcript_sentence")},
            "high_similarity_paraphrase_check": {"status": leakage_status(findings, "high_similarity_paraphrase")},
            "single_source_scenario_check": {"status": leakage_status(findings, "single_source_scenario")},
            "commercial_runtime_prompt_check": {"status": leakage_status(findings, "commercial_runtime_prompt_contamination")},
            "findings": [finding.to_dict() for finding in findings],
        },
        "scenario_results": summarize_scenarios(selected_scenarios, rows),
        "turn_results": rows,
        "boundaries": {
            "scenario_bank_from_prod_014": True,
            "provider_calls_made": False,
            "llm_used": False,
            "external_vector_db_used": False,
            "embedding_provider_used": False,
            "runtime_behavior_changed": False,
            "runtime_retrieval_default_enabled": False,
            "commercial_runtime_prompt_text_from_transcripts_allowed": False,
        },
        "decision": decide(summary),
    }


def render_report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    metrics = payload["metrics"]
    comparison = payload["comparison"]
    lines = [
        "# PROD-015 CallCenterEN Runtime Comparison",
        "",
        "This checkpoint runs the old retrieval-disabled runtime and the retrieval-enabled runtime on the same PROD-014 generated customer prompts.",
        "",
        "It records the exact customer question, exact old runtime answer, exact retrieval runtime answer, and a decision trace for each evaluated turn.",
        "",
        "## Summary",
        "",
        f"- Source bank scenarios: `{summary['source_bank_scenario_count']}`",
        f"- Evaluated scenarios: `{summary['evaluated_scenario_count']}`",
        f"- Evaluated turns: `{summary['evaluated_turn_count']}`",
        f"- Stratified slice: `{summary['stratified_slice']}`",
        f"- Covered labels: `{', '.join(summary['covered_scenario_labels'])}`",
        f"- Hard failure count: `{summary['hard_failure_count']}`",
        f"- Leakage findings: `{summary['leakage_finding_count']}`",
        f"- Decision: `{payload['decision']}`",
        "",
        "## Metrics",
        "",
        f"- Hard failure rate: `{metrics['hard_failure_rate']['value']}`",
        f"- Non-sale correctness: `{metrics['non_sale_correctness']['value']}`",
        f"- Safe close correctness: `{metrics['safe_close_correctness']['value']}`",
        f"- Discovery-before-close rate: `{metrics['discovery_before_close_rate']['value']}`",
        f"- Emotional handling score: `{metrics['emotional_handling_score']['value']}`",
        f"- Leakage failure rate: `{metrics['leakage_failure_rate']['value']}`",
        f"- Retrieval win rate: `{metrics['retrieval_win_rate']['value']}`",
        "",
        "## Runtime Comparison",
        "",
        f"- Old runtime total score: `{comparison['old_runtime_total_score']}`",
        f"- Retrieval runtime total score: `{comparison['retrieval_runtime_total_score']}`",
        f"- Score delta: `{comparison['score_delta']}`",
        f"- Retrieval wins: `{comparison['retrieval_turn_wins']}`",
        f"- Old runtime wins: `{comparison['old_runtime_turn_wins']}`",
        f"- Ties: `{comparison['tie_turns']}`",
        f"- Retrieval influenced responses: `{comparison['retrieval_influenced_count']}`",
        "",
        "## Leakage Tests",
        "",
    ]
    for name, check in payload["leakage_tests"].items():
        if isinstance(check, dict) and "status" in check:
            lines.append(f"- {name}: `{check['status']}`")
    lines.extend(
        [
            "",
            "## Scenario Table",
            "",
            "| Scenario | Label | Expected | Turns | Retrieval Wins | Old Wins | Ties | Hard Failure |",
            "| --- | --- | --- | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for item in payload["scenario_results"]:
        lines.append(
            "| {scenario_id} | {label} | {expected} | {turns} | {rwins} | {owins} | {ties} | {hard} |".format(
                scenario_id=item["scenario_id"],
                label=item["scenario_label"],
                expected=item["expected_outcome"],
                turns=item["turn_count"],
                rwins=item["retrieval_wins"],
                owins=item["old_runtime_wins"],
                ties=item["ties"],
                hard=item["hard_failure"],
            )
        )
    lines.extend(["", "## Exact Questions And Answers", ""])
    for row in payload["turn_results"]:
        trace = row["decision_trace"]
        lines.extend(
            [
                f"### {row['turn_id']}",
                "",
                f"- Scenario: `{row['scenario_id']}` / `{row['scenario_label']}` / `{row['domain']}`",
                f"- Expected outcome: `{row['expected_outcome']}`",
                f"- Winner: `{row['winner']}`",
                f"- Retrieval status: `{row['retrieval_status']}`",
                f"- Hard failure: `{row['hard_failure']}`",
                "",
                "Exact customer question:",
                "",
                "```text",
                row["customer_question"],
                "```",
                "",
                "Exact old runtime answer:",
                "",
                "```text",
                row["old_runtime_answer"],
                "```",
                "",
                "Exact retrieval runtime answer:",
                "",
                "```text",
                row["retrieval_runtime_answer"],
                "```",
                "",
                "Decision trace:",
                "",
                f"1. Old runtime classified sales difficulty `{trace['old_runtime']['sales_difficulty']}`, emotion `{trace['old_runtime']['detected_emotion']}`, strategy `{trace['old_runtime']['selected_strategy']}`, next action `{trace['old_runtime']['next_action']}`, call control `{trace['old_runtime']['call_control']}`.",
                f"2. Retrieval runtime classified sales difficulty `{trace['retrieval_runtime']['sales_difficulty']}`, emotion `{trace['retrieval_runtime']['detected_emotion']}`, strategy `{trace['retrieval_runtime']['selected_strategy']}`, next action `{trace['retrieval_runtime']['next_action']}`, call control `{trace['retrieval_runtime']['call_control']}`.",
                f"3. Retrieval decision `{trace['retrieval_runtime']['retrieval_decision']}` with status `{trace['retrieval_runtime']['retrieval_status']}` and item IDs `{', '.join(trace['retrieval_runtime']['retrieved_item_ids']) or 'none'}`.",
                f"4. Scoring: old `{trace['scoring']['old_runtime']['score']}`, retrieval `{trace['scoring']['retrieval_runtime']['score']}`, winner `{trace['scoring']['winner']}`.",
                "",
            ]
        )
    lines.extend(
        [
            "## Runtime Boundary",
            "",
            "PROD-015 changes no runtime behavior. Retrieval remains disabled by default. The result is ready for review, not a runtime promotion.",
        ]
    )
    return "\n".join(lines) + "\n"
