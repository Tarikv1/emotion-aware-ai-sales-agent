#!/usr/bin/env python3
from __future__ import annotations

import json
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

from callcenteren_composer_hook_test import DEFAULT_RESULT as DEFAULT_PROD_018_RESULT
from callcenteren_specificity_scoring import (
    DEFAULT_PROD_015_RESULT,
    ROOT,
    contains_any,
    rate,
    rel_path,
    score_answer,
    write_json,
    write_text,
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


PROD_019_ID = "PROD-019-guarded-runtime-composer-hooks"
PROD_015_ID = "PROD-015-callcenteren-runtime-comparison"
DEFAULT_CAMPAIGN_CASE_SOURCE = ROOT / "research" / "experiments" / "cases" / "prod-005-realtime-latency-call-control.json"
DEFAULT_OUT_DIR = ROOT / "research" / "experiments" / "generated" / "PROD-019-guarded-runtime-composer-hooks"
DEFAULT_RESULT = DEFAULT_OUT_DIR / "result.json"
DEFAULT_REPORT = DEFAULT_OUT_DIR / "report.md"

PAYMENT_TOKENS = ["credit card", "take your payment", "collect payment", "payment now", "card number"]
SALE_CLOSE_TOKENS = ["process the sale", "take your payment", "collect payment", "card number"]
NON_SALE_OUTCOMES = {"non_sale_correct", "support_only", "human_handoff", "end_call"}
SAFE_CLOSE_OUTCOMES = {"sale_ready", "callback_agreed"}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def answer_contains_payment(answer: str) -> bool:
    return contains_any(answer, PAYMENT_TOKENS)


def answer_contains_sale_close(answer: str) -> bool:
    return contains_any(answer, SALE_CLOSE_TOKENS)


def expected_outcome_correct(row: dict[str, Any], answer: str) -> bool:
    expected = str(row.get("expected_outcome", ""))
    if answer_contains_payment(answer):
        return False
    if expected in NON_SALE_OUTCOMES:
        return not answer_contains_sale_close(answer)
    if expected in SAFE_CLOSE_OUTCOMES:
        return not answer_contains_payment(answer)
    return not answer_contains_payment(answer)


def winner(left_score: int, right_score: int, *, left_name: str, right_name: str) -> str:
    if left_score > right_score:
        return left_name
    if right_score > left_score:
        return right_name
    return "tie"


def campaign_id_for_row(source: dict[str, Any], row: dict[str, Any]) -> str:
    return str(
        row.get("campaign_id")
        or source.get("runtime_comparison", {}).get("campaign_id")
        or "campaign-prod-005-b2b-software"
    )


def packet_for_row(
    *,
    campaigns: list[dict[str, Any]],
    source: dict[str, Any],
    row: dict[str, Any],
    registry_path: Path,
    composer_hooks_enabled: bool,
) -> dict[str, Any]:
    campaign_id = campaign_id_for_row(source, row)
    campaign = find_campaign(campaigns, campaign_id)
    return build_guarded_response_packet(
        campaign=campaign,
        stage=str(row.get("stage", "relevance-check")),
        input_type="speech-final",
        transcript=str(row.get("customer_question", "")),
        silence_count=0,
        retrieval_enabled=True,
        retrieval_registry_path=registry_path,
        retrieval_max_results=4,
        retrieval_min_score=DEFAULT_RETRIEVAL_MIN_SCORE,
        retrieval_target_latency_ms=DEFAULT_RETRIEVAL_TARGET_MS,
        retrieval_acceptable_latency_ms=DEFAULT_RETRIEVAL_ACCEPTABLE_MS,
        composer_hooks_enabled=composer_hooks_enabled,
    )


def score_runtime_row(
    *,
    source: dict[str, Any],
    row: dict[str, Any],
    default_packet: dict[str, Any],
    hooked_packet: dict[str, Any],
) -> dict[str, Any]:
    current_answer = str(row.get("retrieval_runtime_answer", ""))
    default_off_answer = str(default_packet["final_response"])
    hooked_answer = str(hooked_packet["final_response"])
    old_answer = str(row.get("old_runtime_answer", ""))
    old_score = score_answer(row, old_answer)
    current_score = score_answer(row, current_answer)
    default_off_score = score_answer(row, default_off_answer)
    hooked_score = score_answer(row, hooked_answer)
    composer_hooks = hooked_packet["composer_hooks"]
    hook_applied = bool(composer_hooks.get("applied"))
    preserved_existing_influenced = row.get("retrieval_status") == "influenced" and not hook_applied
    payment = answer_contains_payment(hooked_answer)
    return {
        "turn_id": row.get("turn_id", ""),
        "scenario_id": row.get("scenario_id", ""),
        "scenario_label": row.get("scenario_label", ""),
        "domain": row.get("domain", ""),
        "stage": row.get("stage", ""),
        "campaign_id": campaign_id_for_row(source, row),
        "expected_outcome": row.get("expected_outcome", ""),
        "customer_question": row.get("customer_question", ""),
        "expected_agent_response_requirements": row.get("expected_agent_response_requirements", []),
        "source_retrieval_status": row.get("retrieval_status", ""),
        "source_retrieval_used_in_runtime": bool(row.get("retrieval_used_in_runtime")),
        "default_off_answer_drift": default_off_answer != current_answer,
        "hook_applied": hook_applied,
        "hook_applied_without_eval_label": hook_applied and composer_hooks.get("no_evaluation_labels_used") is True,
        "preserved_existing_influenced": preserved_existing_influenced,
        "old_runtime_answer": old_answer,
        "current_retrieval_answer": current_answer,
        "default_off_answer": default_off_answer,
        "hooked_answer": hooked_answer,
        "old_score": old_score,
        "current_retrieval_score": current_score,
        "default_off_score": default_off_score,
        "hooked_score": hooked_score,
        "hooked_delta_vs_current": hooked_score["total"] - current_score["total"],
        "hooked_delta_vs_default_off": hooked_score["total"] - default_off_score["total"],
        "hooked_winner_vs_current": winner(hooked_score["total"], current_score["total"], left_name="hooked", right_name="current"),
        "hooked_winner_vs_default_off": winner(hooked_score["total"], default_off_score["total"], left_name="hooked", right_name="default_off"),
        "contains_payment_collection": payment,
        "expected_outcome_correct": expected_outcome_correct(row, hooked_answer),
        "runtime_trace": {
            "default_off": {
                "retrieval_status": default_packet["retrieval"]["status"],
                "retrieval_used_in_runtime": default_packet["retrieval"]["retrieval_used_in_runtime"],
                "composer_hooks_enabled": default_packet["composer_hooks"]["enabled"],
                "composer_hook_applied": default_packet["composer_hooks"]["applied"],
                "sales_difficulty": default_packet["decision_snapshot"]["sales_difficulty"],
                "next_action": default_packet["decision_snapshot"]["next_action"],
                "call_control": default_packet["decision_snapshot"]["call_control"],
            },
            "opt_in": {
                "retrieval_status": hooked_packet["retrieval"]["status"],
                "retrieval_used_in_runtime": hooked_packet["retrieval"]["retrieval_used_in_runtime"],
                "composer_hooks_enabled": composer_hooks["enabled"],
                "composer_hook_applied": composer_hooks["applied"],
                "hook_id": composer_hooks["hook_id"],
                "hook_basis": composer_hooks["hook_basis"],
                "protected_context_preserved": composer_hooks["protected_context_preserved"],
                "sales_difficulty": hooked_packet["decision_snapshot"]["sales_difficulty"],
                "next_action": hooked_packet["decision_snapshot"]["next_action"],
                "call_control": hooked_packet["decision_snapshot"]["call_control"],
            },
        },
        "composer_hooks": composer_hooks,
    }


def load_prod_018_summary(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "path": rel_path(path),
            "prod_018_gate_passed": "fixture_not_required",
            "decision": "",
        }
    payload = load_json(path)
    return {
        "path": rel_path(path),
        "prod_018_id": payload.get("prod_018_id", ""),
        "prod_018_gate_passed": payload.get("summary", {}).get("prod_018_gate_passed"),
        "decision": payload.get("decision", ""),
    }


def build_summary(source: dict[str, Any], rows: list[dict[str, Any]], *, elapsed_ms: int) -> dict[str, Any]:
    analyzed = len(rows)
    safe_close_rows = [row for row in rows if row["expected_outcome"] in SAFE_CLOSE_OUTCOMES]
    non_sale_rows = [row for row in rows if row["expected_outcome"] in NON_SALE_OUTCOMES]
    current_total = sum(row["current_retrieval_score"]["total"] for row in rows)
    default_total = sum(row["default_off_score"]["total"] for row in rows)
    hooked_total = sum(row["hooked_score"]["total"] for row in rows)
    hooked_wins = sum(1 for row in rows if row["hooked_winner_vs_current"] == "hooked")
    current_wins = sum(1 for row in rows if row["hooked_winner_vs_current"] == "current")
    hook_count = sum(1 for row in rows if row["hook_applied"])
    no_label_hook_count = sum(1 for row in rows if row["hook_applied_without_eval_label"])
    payment_count = sum(1 for row in rows if row["contains_payment_collection"])
    expected_correct_count = sum(1 for row in rows if row["expected_outcome_correct"])
    safety_gate_pass_count = sum(1 for row in rows if row["hooked_score"]["safety_gate"] == 1)
    drift_count = sum(1 for row in rows if row["default_off_answer_drift"])
    non_sale_correct_count = sum(1 for row in non_sale_rows if row["expected_outcome_correct"])
    safe_close_correct_count = sum(1 for row in safe_close_rows if row["expected_outcome_correct"])
    gate_passed = (
        drift_count == 0
        and hook_count > 0
        and no_label_hook_count == hook_count
        and hooked_total > current_total
        and current_wins == 0
        and payment_count == 0
        and expected_correct_count == analyzed
        and int(source.get("summary", {}).get("hard_failure_count", 0)) == 0
        and int(source.get("summary", {}).get("leakage_finding_count", 0)) == 0
    )
    return {
        "analyzed_turn_count": analyzed,
        "default_off_answer_drift_count": drift_count,
        "opt_in_hooked_answer_count": hook_count,
        "hook_applied_without_eval_label_count": no_label_hook_count,
        "preserved_existing_influenced_count": sum(1 for row in rows if row["preserved_existing_influenced"]),
        "current_retrieval_total_score": current_total,
        "default_off_total_score": default_total,
        "hooked_total_score": hooked_total,
        "hooked_score_delta_vs_current": hooked_total - current_total,
        "hooked_score_delta_vs_default_off": hooked_total - default_total,
        "hooked_wins_vs_current": hooked_wins,
        "hooked_current_wins": current_wins,
        "hooked_ties_vs_current": sum(1 for row in rows if row["hooked_winner_vs_current"] == "tie"),
        "safety_gate_pass_count": safety_gate_pass_count,
        "payment_collection_count": payment_count,
        "expected_outcome_correct_count": expected_correct_count,
        "non_sale_turn_count": len(non_sale_rows),
        "non_sale_correct_count": non_sale_correct_count,
        "non_sale_correctness": rate(non_sale_correct_count, len(non_sale_rows)),
        "safe_close_turn_count": len(safe_close_rows),
        "safe_close_correct_count": safe_close_correct_count,
        "safe_close_correctness": rate(safe_close_correct_count, len(safe_close_rows)),
        "hard_failure_count": int(source.get("summary", {}).get("hard_failure_count", 0)),
        "leakage_finding_count": int(source.get("summary", {}).get("leakage_finding_count", 0)),
        "provider_calls_made": False,
        "llm_used": False,
        "default_runtime_behavior_changed": False,
        "runtime_retrieval_default_enabled": False,
        "composer_hook_flag_default_enabled": False,
        "prod_019_gate_passed": gate_passed,
        "elapsed_ms": elapsed_ms,
    }


def build_label_summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["scenario_label"])].append(row)
    summaries: list[dict[str, Any]] = []
    for label in sorted(grouped):
        items = grouped[label]
        summaries.append(
            {
                "scenario_label": label,
                "turn_count": len(items),
                "hooked_answer_count": sum(1 for row in items if row["hook_applied"]),
                "current_retrieval_total_score": sum(row["current_retrieval_score"]["total"] for row in items),
                "hooked_total_score": sum(row["hooked_score"]["total"] for row in items),
                "hooked_wins_vs_current": sum(1 for row in items if row["hooked_winner_vs_current"] == "hooked"),
                "default_off_answer_drift_count": sum(1 for row in items if row["default_off_answer_drift"]),
                "payment_collection_count": sum(1 for row in items if row["contains_payment_collection"]),
            }
        )
    return summaries


def build_payload(
    prod_015_result_path: Path,
    *,
    prod_018_result_path: Path = DEFAULT_PROD_018_RESULT,
    registry_path: Path = DEFAULT_RETRIEVAL_REGISTRY,
    campaign_case_source: Path = DEFAULT_CAMPAIGN_CASE_SOURCE,
) -> dict[str, Any]:
    started = time.perf_counter()
    source = load_json(prod_015_result_path)
    campaigns, _cases = load_realtime_cases(campaign_case_source)
    rows: list[dict[str, Any]] = []
    for row in source.get("turn_results", []):
        default_packet = packet_for_row(
            campaigns=campaigns,
            source=source,
            row=row,
            registry_path=registry_path,
            composer_hooks_enabled=False,
        )
        hooked_packet = packet_for_row(
            campaigns=campaigns,
            source=source,
            row=row,
            registry_path=registry_path,
            composer_hooks_enabled=True,
        )
        rows.append(score_runtime_row(source=source, row=row, default_packet=default_packet, hooked_packet=hooked_packet))
    elapsed_ms = int((time.perf_counter() - started) * 1000)
    summary = build_summary(source, rows, elapsed_ms=elapsed_ms)
    decision = "keep_runtime_composer_hooks_opt_in_candidate_not_default"
    if not summary["prod_019_gate_passed"]:
        decision = "revise_runtime_composer_hooks_before_promotion"
    return {
        "prod_019_id": PROD_019_ID,
        "title": "PROD-019 Guarded runtime composer hooks",
        "source_prod_015_result": {
            "prod_015_id": source.get("prod_015_id", ""),
            "path": rel_path(prod_015_result_path),
            "decision": source.get("decision", ""),
            "turn_count": len(source.get("turn_results", [])),
        },
        "source_prod_018_result": load_prod_018_summary(prod_018_result_path),
        "hypothesis": {
            "statement": "The actual guarded response composer can use opt-in, default-off hooks to improve signal-detectable generic retrieved-not-used turns without changing default behavior.",
            "fixed_cases": "unchanged PROD-015 turn_results",
            "editable_surface_changed": "guarded_runtime_composer_hook_flag_only",
            "runtime_surface_changed": "generate_guarded_response local deterministic composer",
            "scoring_gate": "PROD-017 specificity and objection-fit scoring",
        },
        "summary": summary,
        "label_summary": build_label_summary(rows),
        "turn_results": rows,
        "boundaries": {
            "provider_calls_made": False,
            "llm_used": False,
            "dataset_download_performed": False,
            "default_runtime_behavior_changed": False,
            "runtime_retrieval_default_enabled": False,
            "composer_hook_flag_default_enabled": False,
            "commercial_runtime_prompt_text_from_callcenteren_allowed": False,
            "raw_dataset_text_stored": False,
            "scenario_label_passed_to_composer": False,
        },
        "decision": decision,
    }


def render_report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# PROD-019 Guarded Runtime Composer Hooks",
        "",
        "This checkpoint tests opt-in runtime composer hooks through the actual guarded response composer.",
        "",
        "It changes one editable surface: guarded runtime composer hook flag only. Default-off behavior unchanged remains a hard gate.",
        "",
        "## Summary",
        "",
        f"- Source PROD-015 decision: `{payload['source_prod_015_result']['decision']}`",
        f"- Fixed cases: `{payload['hypothesis']['fixed_cases']}`",
        f"- Editable surface changed: `{payload['hypothesis']['editable_surface_changed']}`",
        f"- Analyzed turns: `{summary['analyzed_turn_count']}`",
        f"- Default-off answer drift count: `{summary['default_off_answer_drift_count']}`",
        f"- Opt-in hooked answers: `{summary['opt_in_hooked_answer_count']}`",
        f"- Hooked without evaluation labels: `{summary['hook_applied_without_eval_label_count']}`",
        f"- Current retrieval total score: `{summary['current_retrieval_total_score']}`",
        f"- Hooked total score: `{summary['hooked_total_score']}`",
        f"- Hooked score delta vs current: `{summary['hooked_score_delta_vs_current']}`",
        f"- Hooked wins vs current: `{summary['hooked_wins_vs_current']}`",
        f"- Current wins against hooked: `{summary['hooked_current_wins']}`",
        f"- Safety gate pass count: `{summary['safety_gate_pass_count']}`",
        f"- Payment collection count: `{summary['payment_collection_count']}`",
        f"- Non-sale correctness: `{summary['non_sale_correctness']}`",
        f"- Safe-close correctness: `{summary['safe_close_correctness']}`",
        f"- Runtime retrieval default enabled: `{summary['runtime_retrieval_default_enabled']}`",
        f"- Composer hook flag default enabled: `{summary['composer_hook_flag_default_enabled']}`",
        f"- PROD-019 gate passed: `{summary['prod_019_gate_passed']}`",
        f"- Decision: `{payload['decision']}`",
        f"- Decision meaning: keep runtime composer hooks opt-in candidate not default",
        "",
        "## Label Summary",
        "",
        "| Label | Turns | Hooked Answers | Current Score | Hooked Score | Hooked Wins Vs Current | Default Drift | Payment Findings |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for item in payload["label_summary"]:
        lines.append(
            "| {label} | {turns} | {hooked} | {current} | {score} | {wins_current} | {drift} | {payments} |".format(
                label=item["scenario_label"],
                turns=item["turn_count"],
                hooked=item["hooked_answer_count"],
                current=item["current_retrieval_total_score"],
                score=item["hooked_total_score"],
                wins_current=item["hooked_wins_vs_current"],
                drift=item["default_off_answer_drift_count"],
                payments=item["payment_collection_count"],
            )
        )
    lines.extend(["", "## Hooked Examples", ""])
    for row in [item for item in payload["turn_results"] if item["hook_applied"]][:12]:
        lines.extend(
            [
                f"### {row['turn_id']}",
                "",
                f"- Label used for reporting only: `{row['scenario_label']}`",
                f"- Runtime hook: `{row['composer_hooks']['hook_id']}`",
                f"- Hook basis: `{', '.join(row['composer_hooks']['hook_basis'])}`",
                f"- Current retrieval score: `{row['current_retrieval_score']['total']}`",
                f"- Hooked score: `{row['hooked_score']['total']}`",
                f"- Hooked winner vs current: `{row['hooked_winner_vs_current']}`",
                "",
                "Customer question:",
                "",
                "```text",
                str(row["customer_question"]),
                "```",
                "",
                "Default-off answer:",
                "",
                "```text",
                str(row["default_off_answer"]),
                "```",
                "",
                "Opt-in hooked answer:",
                "",
                "```text",
                str(row["hooked_answer"]),
                "```",
                "",
            ]
        )
    lines.extend(
        [
            "## Boundary",
            "",
            "PROD-019 keeps retrieval and composer hooks disabled by default. It makes no provider calls, performs no downloads, and does not use CallCenterEN-derived text in commercial runtime prompts.",
        ]
    )
    return "\n".join(lines) + "\n"
