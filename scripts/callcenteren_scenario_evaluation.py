#!/usr/bin/env python3
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from full_sale_scenario_grounding import (
    collect_transient_sentences_from_zip_dir,
    detect_leakage,
    leakage_status,
    normalize_text,
)
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from runtime.entrypoints.generate_guarded_response import (
    DEFAULT_RETRIEVAL_ACCEPTABLE_MS,
    DEFAULT_RETRIEVAL_MIN_SCORE,
    DEFAULT_RETRIEVAL_REGISTRY,
    DEFAULT_RETRIEVAL_TARGET_MS,
    build_guarded_response_packet,
)
from runtime.entrypoints.realtime_turn_cli import find_campaign
from runtime.core.realtime_turns import load_realtime_cases
from run_resp_001_retrieval_ab_evaluation import forbidden_response_text, output_language_matches


DEFAULT_CAMPAIGN_CASE_SOURCE = ROOT / "research" / "experiments" / "cases" / "prod-005-realtime-latency-call-control.json"
NON_SALE_OUTCOMES = {"non_sale_correct", "support_only", "escalate", "end_call", "human_handoff"}
CLOSE_CONTROLS = {"close-and-log-sale-ready", "log-sale-ready"}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def rel_path(path: Path, *, root: Path = ROOT) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def marker_group_score(text: str, marker_groups: list[dict[str, Any]]) -> int:
    lowered = text.lower()
    score = 0
    for group in marker_groups:
        markers = [str(marker).lower() for marker in group.get("markers", [])]
        if markers and all(marker in lowered for marker in markers):
            score += 1
    return score


def max_marker_score(turns: list[dict[str, Any]]) -> int:
    return sum(len(turn.get("quality_marker_groups", [])) for turn in turns if turn.get("quality_scored"))


def run_packet(
    *,
    campaign: dict[str, Any],
    turn: dict[str, Any],
    retrieval_enabled: bool,
    registry_path: Path,
    max_results: int,
    min_score: int,
    target_latency_ms: int,
    acceptable_latency_ms: int,
) -> dict[str, Any]:
    return build_guarded_response_packet(
        campaign=campaign,
        stage=turn["stage"],
        input_type=turn.get("input_type", "speech-final"),
        transcript=turn.get("customer_utterance", turn.get("transcript", "")),
        silence_count=int(turn.get("silence_count", 0)),
        retrieval_enabled=retrieval_enabled,
        retrieval_registry_path=registry_path if retrieval_enabled else None,
        retrieval_max_results=max_results,
        retrieval_min_score=min_score,
        retrieval_target_latency_ms=target_latency_ms,
        retrieval_acceptable_latency_ms=acceptable_latency_ms,
    )


def response_has_sale_close_language(text: str) -> bool:
    lowered = text.lower()
    return "sale_ready" in lowered or "process the sale" in lowered or "take your payment" in lowered


def summarize_turn(
    *,
    scenario: dict[str, Any],
    turn: dict[str, Any],
    no_retrieval: dict[str, Any],
    with_retrieval: dict[str, Any],
) -> dict[str, Any]:
    retrieval = with_retrieval["retrieval"]
    core_response = no_retrieval["final_response"]
    retrieval_response = with_retrieval["final_response"]
    protected_context = bool(turn.get("protected_context"))
    protected_text_preserved = (core_response == retrieval_response) if protected_context else True
    marker_groups = [dict(group) for group in turn.get("quality_marker_groups", [])]
    core_score = marker_group_score(core_response, marker_groups) if turn.get("quality_scored") else 0
    retrieval_score = marker_group_score(retrieval_response, marker_groups) if turn.get("quality_scored") else 0
    score_delta = retrieval_score - core_score
    if score_delta > 0:
        winner = "retrieval"
    elif score_delta < 0:
        winner = "core"
    else:
        winner = "tie"

    safe = (
        no_retrieval["validation"]["passed"]
        and with_retrieval["validation"]["passed"]
        and output_language_matches(no_retrieval)
        and output_language_matches(with_retrieval)
        and not forbidden_response_text(no_retrieval)
        and not forbidden_response_text(with_retrieval)
        and with_retrieval["core_pack"]["campaign_facts_override_rag"] is True
        and (not protected_context or (protected_text_preserved and retrieval["retrieval_used_in_runtime"] is False))
        and not response_has_sale_close_language(retrieval_response)
    )

    return {
        "scenario_id": scenario["scenario_id"],
        "scenario_label": scenario["scenario_label"],
        "turn_id": turn["turn_id"],
        "turn_title": turn.get("turn_title", ""),
        "campaign_id": turn.get("campaign_id", scenario["campaign_id"]),
        "stage": turn["stage"],
        "input_type": turn.get("input_type", "customer_utterance"),
        "customer_utterance": turn.get("customer_utterance", ""),
        "silence_count": turn.get("silence_count", 0),
        "expected_winner": turn.get("expected_winner", ""),
        "quality_scored": bool(turn.get("quality_scored")),
        "protected_context": protected_context,
        "protected_text_preserved": protected_text_preserved,
        "sales_difficulty": no_retrieval["decision_snapshot"]["sales_difficulty"],
        "call_control": with_retrieval["decision_snapshot"]["call_control"],
        "core_response": core_response,
        "retrieval_response": retrieval_response,
        "decision_trace": {
            "policy_classification": {
                "response_mode": with_retrieval["decision_snapshot"].get("response_mode"),
                "campaign_language": with_retrieval["decision_snapshot"].get("campaign_language"),
                "response_language": with_retrieval["decision_snapshot"].get("response_language"),
                "detected_emotion": with_retrieval["decision_snapshot"].get("detected_emotion"),
                "sales_difficulty": with_retrieval["decision_snapshot"].get("sales_difficulty"),
                "interest_state": with_retrieval["decision_snapshot"].get("interest_state"),
                "selected_strategy": with_retrieval["decision_snapshot"].get("selected_strategy"),
                "next_action": with_retrieval["decision_snapshot"].get("next_action"),
                "call_control": with_retrieval["decision_snapshot"].get("call_control"),
                "background_modules": with_retrieval["decision_snapshot"].get("background_modules", []),
            },
            "old_core_path": {
                "retrieval_enabled": False,
                "policy_response": no_retrieval["policy_response"],
                "local_composer_candidate": no_retrieval["candidate_response"],
                "validation_passed": no_retrieval["validation"]["passed"],
                "fallback_used": no_retrieval["validation"]["fallback_used"],
                "forbidden_claim_matches": no_retrieval["validation"]["forbidden_claim_matches"],
                "final_response": core_response,
            },
            "retrieval_path": {
                "retrieval_enabled": True,
                "retrieval_status": retrieval["status"],
                "retrieval_decision": retrieval["retrieval_decision"],
                "retrieval_position": retrieval["retrieval_position"],
                "context_flags": retrieval.get("context_flags", []),
                "blocked_reason": retrieval.get("blocked_reason", ""),
                "retrieved_item_ids": retrieval["retrieved_item_ids"],
                "advisory_hints": retrieval.get("advisory_hints", []),
                "rejected_items": retrieval.get("rejected_items", []),
                "policy_response": with_retrieval["policy_response"],
                "local_composer_candidate": with_retrieval["candidate_response"],
                "validation_passed": with_retrieval["validation"]["passed"],
                "fallback_used": with_retrieval["validation"]["fallback_used"],
                "forbidden_claim_matches": with_retrieval["validation"]["forbidden_claim_matches"],
                "retrieval_used_in_runtime": retrieval["retrieval_used_in_runtime"],
                "influence_basis": retrieval.get("influence_basis", ""),
                "final_response": retrieval_response,
            },
            "safety_and_selection": {
                "campaign_facts_override_rag": with_retrieval["core_pack"]["campaign_facts_override_rag"],
                "protected_context": protected_context,
                "protected_text_preserved": protected_text_preserved,
                "language_match": output_language_matches(with_retrieval),
                "safe": safe,
                "core_score": core_score,
                "retrieval_score": retrieval_score,
                "score_delta": score_delta,
                "winner": winner,
                "quality_marker_groups": marker_groups,
            },
        },
        "core_score": core_score,
        "retrieval_score": retrieval_score,
        "score_delta": score_delta,
        "winner": winner,
        "retrieval_status": retrieval["status"],
        "retrieval_used_in_runtime": retrieval["retrieval_used_in_runtime"],
        "retrieved_item_ids": retrieval["retrieved_item_ids"],
        "retrieval_elapsed_ms": retrieval["latency"]["elapsed_ms"],
        "retrieval_target_ms": retrieval["latency"]["target_ms"],
        "retrieval_acceptable_ms": retrieval["latency"]["acceptable_ms"],
        "language_match": output_language_matches(with_retrieval),
        "campaign_facts_override_rag": with_retrieval["core_pack"]["campaign_facts_override_rag"],
        "validation_passed": with_retrieval["validation"]["passed"],
        "safe": safe,
    }


def scenario_quality_score(scenarios: list[dict[str, Any]]) -> float:
    scores = []
    for scenario in scenarios:
        checks = [
            len(scenario.get("source_pattern_ids", [])) >= 3,
            scenario.get("copied_transcript_text_used") is False,
            scenario.get("generated_from_single_transcript") is False,
            scenario.get("contains_transcript_derived_prompt_text") is False,
            scenario.get("commercial_runtime_prompt_safe") is True,
            bool(scenario.get("turns")),
            scenario.get("expected_outcome") in {"sale_ready", "non_sale_correct", "support_only", "escalate", "end_call", "human_handoff"},
        ]
        scores.append(sum(1 for check in checks if check) / len(checks))
    return round(sum(scores) / len(scores), 4) if scores else 0.0


def summarize_scenarios(scenarios: list[dict[str, Any]], rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows_by_scenario: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        rows_by_scenario.setdefault(row["scenario_id"], []).append(row)

    summaries: list[dict[str, Any]] = []
    for scenario in scenarios:
        scenario_rows = rows_by_scenario.get(scenario["scenario_id"], [])
        expected_outcome = scenario["expected_outcome"]
        non_sale_expected = expected_outcome in NON_SALE_OUTCOMES
        non_sale_correct = None
        if non_sale_expected:
            non_sale_correct = all(
                row["safe"]
                and row["call_control"] not in CLOSE_CONTROLS
                and not response_has_sale_close_language(row["retrieval_response"])
                for row in scenario_rows
            )
        summaries.append(
            {
                "scenario_id": scenario["scenario_id"],
                "scenario_label": scenario["scenario_label"],
                "expected_outcome": expected_outcome,
                "source_pattern_count": len(scenario.get("source_pattern_ids", [])),
                "turn_count": len(scenario_rows),
                "quality_scored_turn_count": sum(1 for row in scenario_rows if row["quality_scored"]),
                "safe_turn_count": sum(1 for row in scenario_rows if row["safe"]),
                "retrieval_wins": sum(1 for row in scenario_rows if row["winner"] == "retrieval"),
                "core_wins": sum(1 for row in scenario_rows if row["winner"] == "core"),
                "non_sale_expected": non_sale_expected,
                "non_sale_correct": non_sale_correct,
            }
        )
    return summaries


def build_summary(
    *,
    case: dict[str, Any],
    scenarios: list[dict[str, Any]],
    rows: list[dict[str, Any]],
    findings: list[Any],
    transient_sentence_count: int,
    started_at: float,
    completed_at: float,
) -> dict[str, Any]:
    quality_scored = [row for row in rows if row["quality_scored"]]
    protected = [row for row in rows if row["protected_context"]]
    latencies = [row["retrieval_elapsed_ms"] for row in rows]
    scenario_summaries = summarize_scenarios(scenarios, rows)
    non_sale_expected = [item for item in scenario_summaries if item["non_sale_expected"]]
    non_sale_correct = [item for item in non_sale_expected if item["non_sale_correct"] is True]
    expected_mismatch = [
        row["turn_id"]
        for row in rows
        if row["expected_winner"] and row["expected_winner"] != row["winner"]
    ]
    hard_failure_ids = sorted(
        {
            row["scenario_id"]
            for row in rows
            if not row["safe"] or row["turn_id"] in expected_mismatch
        }
        | {item["scenario_id"] for item in non_sale_expected if item["non_sale_correct"] is not True}
        | {finding.scenario_id for finding in findings}
    )
    return {
        "scenario_count": len(scenarios),
        "turn_count": len(rows),
        "source_pattern_count": len(case.get("source_patterns", [])),
        "quality_scored_turn_count": len(quality_scored),
        "download_performed": False,
        "provider_calls_made": False,
        "raw_transcript_text_stored": False,
        "runtime_retrieval_default_enabled": False,
        "commercial_runtime_prompt_contamination": leakage_status(findings, "commercial_runtime_prompt_contamination") == "fail",
        "transient_source_sentence_count": transient_sentence_count,
        "leakage_finding_count": len(findings),
        "safe_turn_count": sum(1 for row in rows if row["safe"]),
        "unsafe_turn_count": sum(1 for row in rows if not row["safe"]),
        "hard_failure_count": len(hard_failure_ids),
        "hard_failure_scenario_ids": hard_failure_ids,
        "non_sale_expected_count": len(non_sale_expected),
        "non_sale_correct_count": len(non_sale_correct),
        "protected_turn_count": len(protected),
        "protected_turns_preserved": sum(1 for row in protected if row["protected_text_preserved"] and not row["retrieval_used_in_runtime"]),
        "retrieval_turn_wins": sum(1 for row in quality_scored if row["winner"] == "retrieval"),
        "core_turn_wins": sum(1 for row in quality_scored if row["winner"] == "core"),
        "tie_turns": sum(1 for row in rows if row["winner"] == "tie"),
        "expected_winner_mismatch_ids": expected_mismatch,
        "core_total_score": sum(row["core_score"] for row in quality_scored),
        "retrieval_total_score": sum(row["retrieval_score"] for row in quality_scored),
        "max_possible_quality_score": max_marker_score([turn for scenario in scenarios for turn in scenario.get("turns", [])]),
        "retrieval_influenced_count": sum(1 for row in rows if row["retrieval_used_in_runtime"]),
        "retrieval_blocked_count": sum(1 for row in rows if row["retrieval_status"] == "blocked"),
        "retrieval_retrieved_not_used_count": sum(1 for row in rows if row["retrieval_status"] == "retrieved_not_used"),
        "retrieval_no_match_count": sum(1 for row in rows if row["retrieval_status"] == "no_match"),
        "retrieval_over_target_count": sum(1 for row in rows if row["retrieval_elapsed_ms"] > row["retrieval_target_ms"]),
        "retrieval_over_acceptable_count": sum(1 for row in rows if row["retrieval_elapsed_ms"] > row["retrieval_acceptable_ms"]),
        "max_retrieval_elapsed_ms": max(latencies) if latencies else 0,
        "avg_retrieval_elapsed_ms": round(sum(latencies) / len(latencies), 2) if latencies else 0,
        "scenario_quality_score": scenario_quality_score(scenarios),
        "total_elapsed_ms": int((completed_at - started_at) * 1000),
    }


def build_metrics(summary: dict[str, Any], findings: list[Any]) -> dict[str, dict[str, Any]]:
    scenario_count = max(summary["scenario_count"], 1)
    quality_turns = max(summary["quality_scored_turn_count"], 1)
    max_score = max(summary["max_possible_quality_score"], 1)
    non_sale_expected = max(summary["non_sale_expected_count"], 1)
    return {
        "hard_failure_rate": {
            "value": round(summary["hard_failure_count"] / scenario_count, 4),
            "definition": "Share of scenarios with any safety, leakage, non-sale, protected-text, expected-winner, or latency hard failure.",
            "release_candidate_target": 0.0,
        },
        "non_sale_correctness": {
            "value": round(summary["non_sale_correct_count"] / non_sale_expected, 4),
            "definition": "Share of non-sale expected scenarios where retrieval-enabled output avoids sale close and preserves the right outcome.",
            "required_before_close_rate_optimization": True,
        },
        "leakage_failure_rate": {
            "value": round(len(findings) / scenario_count, 4),
            "definition": "Share of scenarios with transcript sentence, high-similarity, single-source, copied-text, or commercial prompt contamination findings.",
            "release_candidate_target": 0.0,
        },
        "scenario_quality_score": {
            "value": summary["scenario_quality_score"],
            "definition": "Average structural quality score for scenario diversity, source-pattern count, synthetic rewrite status, and expected-outcome coverage.",
        },
        "sales_emotional_handling_score": {
            "value": round(summary["retrieval_total_score"] / max_score, 4),
            "definition": "Retrieval-enabled marker score across objection handling, autonomy support, trust repair, escalation, and next-step quality markers.",
        },
        "retrieval_win_rate": {
            "value": round(summary["retrieval_turn_wins"] / quality_turns, 4),
            "definition": "Share of quality-scored turns where RAG-018 retrieval beats the old retrieval-disabled core response.",
        },
    }


def decide(summary: dict[str, Any]) -> str:
    if summary["hard_failure_count"]:
        return "revise_scenarios_or_runtime_before_reuse"
    if summary["retrieval_over_acceptable_count"]:
        return "revise_retrieval_latency_before_runtime_use"
    if summary["retrieval_total_score"] > summary["core_total_score"] and summary["core_turn_wins"] == 0:
        return "keep_retrieval_opt_in_for_callcenteren_grounded_scenarios"
    return "keep_old_core_until_retrieval_beats_fixed_scenarios"


def build_payload(
    case_path: Path,
    *,
    registry_path: Path = DEFAULT_RETRIEVAL_REGISTRY,
    raw_zip_dir: Path | None = None,
    root: Path = ROOT,
) -> dict[str, Any]:
    case = load_json(case_path)
    scenarios = list(case.get("scenario_bank", []))
    runtime_prompts = list(case.get("commercial_runtime_prompts", []))
    source_probe_sentences = [normalize_text(text) for text in case.get("synthetic_leakage_probe_sentences", [])]
    transient_sentence_count = 0
    if raw_zip_dir is not None and raw_zip_dir.exists():
        transient_sentences = collect_transient_sentences_from_zip_dir(raw_zip_dir)
        transient_sentence_count = len(transient_sentences)
        source_probe_sentences.extend(transient_sentences)
    findings = detect_leakage(scenarios, source_probe_sentences, runtime_prompts)

    campaign_source = root / case.get("campaign_case_source", rel_path(DEFAULT_CAMPAIGN_CASE_SOURCE, root=root))
    campaigns, _runtime_cases = load_realtime_cases(campaign_source)
    retrieval_config = case.get("retrieval", {})
    max_results = int(retrieval_config.get("max_results", 4))
    min_score = int(retrieval_config.get("min_score", DEFAULT_RETRIEVAL_MIN_SCORE))
    target_latency_ms = int(retrieval_config.get("target_latency_ms", DEFAULT_RETRIEVAL_TARGET_MS))
    acceptable_latency_ms = int(retrieval_config.get("acceptable_latency_ms", DEFAULT_RETRIEVAL_ACCEPTABLE_MS))

    started_at = time.perf_counter()
    rows: list[dict[str, Any]] = []
    for scenario in scenarios:
        for turn in scenario.get("turns", []):
            campaign_id = turn.get("campaign_id", scenario["campaign_id"])
            campaign = find_campaign(campaigns, campaign_id)
            if campaign is None:
                raise ValueError(f"Unknown campaign_id: {campaign_id}")
            no_retrieval = run_packet(
                campaign=campaign,
                turn=turn,
                retrieval_enabled=False,
                registry_path=registry_path,
                max_results=max_results,
                min_score=min_score,
                target_latency_ms=target_latency_ms,
                acceptable_latency_ms=acceptable_latency_ms,
            )
            with_retrieval = run_packet(
                campaign=campaign,
                turn=turn,
                retrieval_enabled=True,
                registry_path=registry_path,
                max_results=max_results,
                min_score=min_score,
                target_latency_ms=target_latency_ms,
                acceptable_latency_ms=acceptable_latency_ms,
            )
            rows.append(summarize_turn(scenario=scenario, turn=turn, no_retrieval=no_retrieval, with_retrieval=with_retrieval))
    completed_at = time.perf_counter()

    summary = build_summary(
        case=case,
        scenarios=scenarios,
        rows=rows,
        findings=findings,
        transient_sentence_count=transient_sentence_count,
        started_at=started_at,
        completed_at=completed_at,
    )
    metrics = build_metrics(summary, findings)
    payload = {
        "prod_012_id": "PROD-012-callcenteren-scenario-evaluation",
        "title": case.get("title", ""),
        "cases_path": rel_path(case_path, root=root),
        "campaign_case_source": rel_path(campaign_source, root=root),
        "registry_path": rel_path(registry_path, root=root),
        "dataset_source": case["dataset_source"],
        "intake_policy": case["intake_policy"],
        "summary": summary,
        "metrics": metrics,
        "comparison": {
            "baseline_name": "old_core_retrieval_disabled",
            "candidate_name": "rag_018_retrieval_enabled",
            "core_total_score": summary["core_total_score"],
            "retrieval_total_score": summary["retrieval_total_score"],
            "score_delta": summary["retrieval_total_score"] - summary["core_total_score"],
            "retrieval_turn_wins": summary["retrieval_turn_wins"],
            "core_turn_wins": summary["core_turn_wins"],
            "tie_turns": summary["tie_turns"],
            "protected_turn_count": summary["protected_turn_count"],
            "protected_turns_preserved": summary["protected_turns_preserved"],
            "retrieval_over_acceptable_count": summary["retrieval_over_acceptable_count"],
        },
        "leakage_tests": {
            "minimum_source_patterns_per_scenario": 3,
            "exact_transcript_sentence_check": {
                "status": leakage_status(findings, "exact_transcript_sentence"),
                "method": "normalized exact sentence scan against transient source sentences and synthetic leak probes",
            },
            "high_similarity_paraphrase_check": {
                "status": leakage_status(findings, "high_similarity_paraphrase"),
                "threshold": 0.86,
            },
            "single_source_scenario_check": {
                "status": leakage_status(findings, "single_source_scenario"),
                "method": "each scenario must use at least three source pattern IDs",
            },
            "commercial_runtime_prompt_check": {
                "status": leakage_status(findings, "commercial_runtime_prompt_contamination"),
                "method": "source-derived sentences are blocked from commercial runtime prompts",
            },
            "findings": [finding.to_dict() for finding in findings],
        },
        "source_patterns": case["source_patterns"],
        "scenario_bank": scenarios,
        "scenario_results": summarize_scenarios(scenarios, rows),
        "turns": rows,
        "boundaries": {
            "pattern_grounding_only": True,
            "download_required_for_default_run": False,
            "raw_dataset_storage": "data/external/callcenteren/raw/ ignored local-only",
            "tracked_artifacts_may_store_raw_transcripts": False,
            "commercial_runtime_may_use_transcript_text": False,
            "provider_calls_made": False,
            "external_vector_db_used": False,
            "embedding_provider_used": False,
            "llm_used": False,
        },
        "decision": "",
    }
    payload["decision"] = decide(summary)
    return payload


def render_report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    metrics = payload["metrics"]
    comparison = payload["comparison"]
    lines = [
        "# PROD-012 CallCenterEN Scenario Evaluation",
        "",
        "This local checkpoint uses AIxBlock / CallCenterEN only as pattern grounding for project-owned synthetic scenarios.",
        "It compares the old core retrieval-disabled runtime against the RAG-018 retrieval version on the same fixed scenario turns.",
        "",
        "No dataset download, provider call, private customer data read, transcript body storage, vector database, embedding provider, or LLM reranker was used.",
        "",
        "## Source Boundary",
        "",
        f"- Dataset: {payload['dataset_source']['dataset_url']}",
        f"- Paper: {payload['dataset_source']['paper_url']}",
        f"- License observed: `{payload['dataset_source']['license']}`",
        f"- Reuse label: `{payload['dataset_source']['reuse_label']}`",
        "- Commercial runtime use: `false`",
        "",
        "## Metrics",
        "",
        f"- Hard failure rate: `{metrics['hard_failure_rate']['value']}`",
        f"- Non-sale correctness: `{metrics['non_sale_correctness']['value']}`",
        f"- Leakage failure rate: `{metrics['leakage_failure_rate']['value']}`",
        f"- Scenario quality score: `{metrics['scenario_quality_score']['value']}`",
        f"- Sales/emotional handling score: `{metrics['sales_emotional_handling_score']['value']}`",
        f"- Retrieval win rate: `{metrics['retrieval_win_rate']['value']}`",
        "",
        "## Retrieval Version vs Old Core",
        "",
        f"- Old core total score: `{comparison['core_total_score']}`",
        f"- Retrieval version total score: `{comparison['retrieval_total_score']}`",
        f"- Retrieval version wins: `{comparison['retrieval_turn_wins']}`",
        f"- Old core wins: `{comparison['core_turn_wins']}`",
        f"- Protected turns preserved: `{comparison['protected_turns_preserved']}/{comparison['protected_turn_count']}`",
        f"- Decision: `{payload['decision']}`",
        "",
        "Interpretation: retrieval is better on these fixed CallCenterEN-grounded synthetic objection turns, but the result is still opt-in evidence. Do not make retrieval default from this checkpoint alone.",
        "",
        "## Leakage Tests",
        "",
    ]
    for name, check in payload["leakage_tests"].items():
        if isinstance(check, dict) and "status" in check:
            lines.append(f"- {name}: `{check['status']}`")
    lines.extend(["", "## Scenario Table", "", "| Scenario | Label | Expected | Turns | Retrieval Wins | Non-Sale Correct |", "| --- | --- | --- | ---: | ---: | --- |"])
    for item in payload["scenario_results"]:
        non_sale_display = "n/a" if item["non_sale_correct"] is None else str(item["non_sale_correct"])
        lines.append(
            "| {scenario_id} | {label} | {expected} | {turns} | {wins} | {non_sale} |".format(
                scenario_id=item["scenario_id"],
                label=item["scenario_label"],
                expected=item["expected_outcome"],
                turns=item["turn_count"],
                wins=item["retrieval_wins"],
                non_sale=non_sale_display,
            )
        )
    lines.extend(["", "## Exact Questions And Answers", ""])
    for row in payload["turns"]:
        input_note = ""
        if row.get("input_type") != "customer_utterance":
            input_note = f" (`input_type`: `{row.get('input_type')}`, `silence_count`: `{row.get('silence_count', 0)}`)"
        lines.extend(
            [
                f"### {row['turn_id']} - {row['turn_title']}",
                "",
                f"- Scenario: `{row['scenario_id']}` / `{row['scenario_label']}`",
                f"- Stage: `{row['stage']}`",
                f"- Winner: `{row['winner']}`",
                f"- Retrieval status: `{row['retrieval_status']}`",
                f"- Exact customer question/input{input_note}:",
                "",
                "```text",
                row.get("customer_utterance", ""),
                "```",
                "",
                "- Exact old/core answer:",
                "",
                "```text",
                row["core_response"],
                "```",
                "",
                "- Exact retrieval/RAG answer:",
                "",
                "```text",
                row["retrieval_response"],
                "```",
                "",
                "- Decision process:",
                "",
                f"  1. Policy classified the turn as sales difficulty `{row['decision_trace']['policy_classification']['sales_difficulty']}`, emotion `{row['decision_trace']['policy_classification']['detected_emotion']}`, strategy `{row['decision_trace']['policy_classification']['selected_strategy']}`, next action `{row['decision_trace']['policy_classification']['next_action']}`, call control `{row['decision_trace']['policy_classification']['call_control']}`.",
                f"  2. Old/core path used policy response `{row['decision_trace']['old_core_path']['policy_response']}` and local composer candidate `{row['decision_trace']['old_core_path']['local_composer_candidate']}`. Validation passed: `{row['decision_trace']['old_core_path']['validation_passed']}`. Fallback used: `{row['decision_trace']['old_core_path']['fallback_used']}`.",
                f"  3. Retrieval path status `{row['decision_trace']['retrieval_path']['retrieval_status']}` with context flags `{', '.join(row['decision_trace']['retrieval_path']['context_flags']) or 'none'}` and retrieved item IDs `{', '.join(row['decision_trace']['retrieval_path']['retrieved_item_ids']) or 'none'}`.",
            ]
        )
        hints = row["decision_trace"]["retrieval_path"]["advisory_hints"]
        if hints:
            lines.append("  4. Retrieved advisory hints:")
            for hint in hints:
                lines.append(
                    "     - `{item_id}` score `{score}`: {hint_text}".format(
                        item_id=hint["item_id"],
                        score=hint["match_score"],
                        hint_text=hint["hint"],
                    )
                )
            next_step_number = 5
        else:
            lines.append("  4. Retrieved advisory hints: none")
            next_step_number = 5
        lines.extend(
            [
                f"  {next_step_number}. Retrieval composer candidate was `{row['decision_trace']['retrieval_path']['local_composer_candidate']}`. Validation passed: `{row['decision_trace']['retrieval_path']['validation_passed']}`. Fallback used: `{row['decision_trace']['retrieval_path']['fallback_used']}`. Retrieval used in runtime: `{row['decision_trace']['retrieval_path']['retrieval_used_in_runtime']}`.",
                f"  {next_step_number + 1}. Safety/selection kept campaign facts above RAG: `{row['decision_trace']['safety_and_selection']['campaign_facts_override_rag']}`; protected text preserved: `{row['decision_trace']['safety_and_selection']['protected_text_preserved']}`; final winner: `{row['decision_trace']['safety_and_selection']['winner']}` with score delta `{row['decision_trace']['safety_and_selection']['score_delta']}`.",
                "",
            ]
        )
    lines.extend(
        [
            "",
            "## Runtime Boundary",
            "",
            "The generated scenarios are synthetic rewrites combined from at least three source patterns. Raw transcript text, high-similarity paraphrases, single-source scenario generation, and transcript-derived commercial runtime prompts are hard failures.",
        ]
    )
    return "\n".join(lines) + "\n"
