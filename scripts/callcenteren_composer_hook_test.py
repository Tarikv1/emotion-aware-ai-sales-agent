#!/usr/bin/env python3
from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from callcenteren_specificity_scoring import (
    DEFAULT_PROD_015_RESULT,
    ROOT,
    contains_any,
    is_generic_answer,
    rate,
    rel_path,
    score_answer,
    write_json,
    write_text,
)


PROD_018_ID = "PROD-018-callcenteren-composer-hook-test"
PROD_015_ID = "PROD-015-callcenteren-runtime-comparison"
DEFAULT_OUT_DIR = ROOT / "research" / "experiments" / "generated" / "PROD-018-callcenteren-composer-hook-test"
DEFAULT_RESULT = DEFAULT_OUT_DIR / "result.json"
DEFAULT_REPORT = DEFAULT_OUT_DIR / "report.md"

PAYMENT_TOKENS = ["credit card", "take your payment", "collect payment", "payment now", "card number"]
SALE_CLOSE_TOKENS = ["process the sale", "take your payment", "collect payment", "card number"]
NON_SALE_OUTCOMES = {"non_sale_correct", "support_only", "human_handoff", "end_call"}
SAFE_CLOSE_OUTCOMES = {"sale_ready", "callback_agreed"}


HOOK_SET = [
    {
        "hook_id": "price_objection_clarifier",
        "label": "Price objection clarifier",
        "scenario_labels": ["price_objection"],
        "purpose": "Separate cost, value, terms, and timing before any close.",
    },
    {
        "hook_id": "support_handoff_router",
        "label": "Support handoff router",
        "scenario_labels": ["support_handoff"],
        "purpose": "Route unresolved service issues to a specialist instead of guessing.",
    },
    {
        "hook_id": "cancellation_boundary_stop",
        "label": "Cancellation boundary stop",
        "scenario_labels": ["cancellation_boundary"],
        "purpose": "Stop the sales discussion and confirm whether the customer wants no further calls.",
    },
    {
        "hook_id": "callback_request_low_commitment",
        "label": "Callback request low commitment",
        "scenario_labels": ["callback_request"],
        "purpose": "Offer a low-commitment callback or relevant summary without forcing a decision.",
    },
    {
        "hook_id": "trust_repair_verification",
        "label": "Trust repair verification",
        "scenario_labels": ["trust_repair"],
        "purpose": "Offer verifiable company or specialist context without pressure.",
    },
    {
        "hook_id": "sale_eligible_fit_check",
        "label": "Sale eligible fit check",
        "scenario_labels": ["sale_eligible"],
        "purpose": "Check fit, timing, or eligibility before any verbal commitment.",
    },
]

HOOK_IDS_BY_LABEL = {
    label: hook["hook_id"]
    for hook in HOOK_SET
    for label in hook["scenario_labels"]
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def answer_contains_payment(answer: str) -> bool:
    return contains_any(answer, PAYMENT_TOKENS)


def answer_contains_sale_close(answer: str) -> bool:
    return contains_any(answer, SALE_CLOSE_TOKENS)


def is_hook_eligible(row: dict[str, Any]) -> bool:
    return (
        row.get("hard_failure") is not True
        and row.get("retrieval_status") == "retrieved_not_used"
        and is_generic_answer(str(row.get("retrieval_runtime_answer", "")))
        and str(row.get("scenario_label", "")) in HOOK_IDS_BY_LABEL
    )


def compose_hooked_answer(row: dict[str, Any]) -> tuple[str, str]:
    label = str(row.get("scenario_label", ""))
    question = str(row.get("customer_question", "")).lower()
    if label == "price_objection":
        if "timeline" in question or "timing" in question:
            return (
                "That makes sense. Is the bigger concern the cost, the value you would get back, or the timing for reviewing it?",
                "price_objection_clarifier",
            )
        return (
            "That makes sense. Is the bigger concern the price, the terms, or whether the value is worth reviewing now?",
            "price_objection_clarifier",
        )
    if label == "support_handoff":
        return (
            "Of course. Since this is an unresolved service issue, I should route you to a specialist rather than guess. What is the main issue they should review first?",
            "support_handoff_router",
        )
    if label == "cancellation_boundary":
        return (
            "Understood. I can stop the sales discussion here. Do you want me to mark that you do not want further calls?",
            "cancellation_boundary_stop",
        )
    if label == "callback_request":
        return (
            "That makes sense. Would a brief callback later help, or should I send the one detail that would make this worth reviewing first?",
            "callback_request_low_commitment",
        )
    if label == "trust_repair":
        return (
            "Fair. I can keep this low-pressure: should I share what can be verified about the company, or would you prefer a specialist follow-up?",
            "trust_repair_verification",
        )
    if label == "sale_eligible":
        return (
            "That makes sense. Before any commitment, should we confirm fit, timing, or eligibility for your situation?",
            "sale_eligible_fit_check",
        )
    return str(row.get("retrieval_runtime_answer", "")), "no_hook"


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


def score_hook_row(row: dict[str, Any]) -> dict[str, Any]:
    old_answer = str(row.get("old_runtime_answer", ""))
    current_answer = str(row.get("retrieval_runtime_answer", ""))
    hook_applied = is_hook_eligible(row)
    preserved_existing_influenced = row.get("retrieval_status") == "influenced"
    if hook_applied:
        hooked_answer, hook_id = compose_hooked_answer(row)
    else:
        hooked_answer = current_answer
        hook_id = "preserve_existing_influenced" if preserved_existing_influenced else "no_hook"

    old_score = score_answer(row, old_answer)
    current_score = score_answer(row, current_answer)
    hooked_score = score_answer(row, hooked_answer)
    payment = answer_contains_payment(hooked_answer)
    return {
        "turn_id": row.get("turn_id", ""),
        "scenario_id": row.get("scenario_id", ""),
        "scenario_label": row.get("scenario_label", ""),
        "domain": row.get("domain", ""),
        "expected_outcome": row.get("expected_outcome", ""),
        "customer_question": row.get("customer_question", ""),
        "expected_agent_response_requirements": row.get("expected_agent_response_requirements", []),
        "retrieval_status": row.get("retrieval_status", ""),
        "retrieval_used_in_runtime": bool(row.get("retrieval_used_in_runtime")),
        "hook_applied": hook_applied,
        "hook_id": hook_id,
        "preserved_existing_influenced": preserved_existing_influenced,
        "old_runtime_answer": old_answer,
        "current_retrieval_answer": current_answer,
        "hooked_answer": hooked_answer,
        "old_score": old_score,
        "current_retrieval_score": current_score,
        "hooked_score": hooked_score,
        "hooked_delta_vs_current": hooked_score["total"] - current_score["total"],
        "hooked_delta_vs_old": hooked_score["total"] - old_score["total"],
        "hooked_winner_vs_current": winner(hooked_score["total"], current_score["total"], left_name="hooked", right_name="current"),
        "hooked_winner_vs_old": winner(hooked_score["total"], old_score["total"], left_name="hooked", right_name="old_runtime"),
        "contains_payment_collection": payment,
        "expected_outcome_correct": expected_outcome_correct(row, hooked_answer),
    }


def build_summary(source: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, Any]:
    source_summary = source.get("summary", {})
    analyzed = len(rows)
    safe_close_rows = [row for row in rows if row["expected_outcome"] in SAFE_CLOSE_OUTCOMES]
    non_sale_rows = [row for row in rows if row["expected_outcome"] in NON_SALE_OUTCOMES]
    hooked_total = sum(row["hooked_score"]["total"] for row in rows)
    current_total = sum(row["current_retrieval_score"]["total"] for row in rows)
    old_total = sum(row["old_score"]["total"] for row in rows)
    hooked_wins_vs_current = sum(1 for row in rows if row["hooked_winner_vs_current"] == "hooked")
    hooked_wins_vs_old = sum(1 for row in rows if row["hooked_winner_vs_old"] == "hooked")
    hooked_old_wins = sum(1 for row in rows if row["hooked_winner_vs_old"] == "old_runtime")
    hooked_ties_vs_old = sum(1 for row in rows if row["hooked_winner_vs_old"] == "tie")
    payment_count = sum(1 for row in rows if row["contains_payment_collection"])
    safety_gate_pass_count = sum(1 for row in rows if row["hooked_score"]["safety_gate"] == 1)
    expected_correct_count = sum(1 for row in rows if row["expected_outcome_correct"])
    non_sale_correct_count = sum(1 for row in non_sale_rows if row["expected_outcome_correct"])
    safe_close_correct_count = sum(1 for row in safe_close_rows if row["expected_outcome_correct"])
    hooked_answer_count = sum(1 for row in rows if row["hook_applied"])
    preserved_existing_influenced_count = sum(1 for row in rows if row["preserved_existing_influenced"])
    gate_passed = (
        hooked_total > current_total
        and hooked_wins_vs_current > 0
        and hooked_old_wins == 0
        and payment_count == 0
        and expected_correct_count == analyzed
        and int(source_summary.get("hard_failure_count", 0)) == 0
        and int(source_summary.get("leakage_finding_count", 0)) == 0
    )
    return {
        "analyzed_turn_count": analyzed,
        "eligible_hook_turn_count": sum(1 for row in rows if row["hook_applied"] or (row["retrieval_status"] == "retrieved_not_used" and row["hook_id"] != "no_hook")),
        "hooked_answer_count": hooked_answer_count,
        "preserved_existing_influenced_count": preserved_existing_influenced_count,
        "old_total_score": old_total,
        "current_retrieval_total_score": current_total,
        "hooked_total_score": hooked_total,
        "hooked_score_delta_vs_current": hooked_total - current_total,
        "hooked_score_delta_vs_old": hooked_total - old_total,
        "hooked_wins_vs_current": hooked_wins_vs_current,
        "hooked_wins_vs_old": hooked_wins_vs_old,
        "hooked_old_wins": hooked_old_wins,
        "hooked_ties_vs_old": hooked_ties_vs_old,
        "safety_gate_pass_count": safety_gate_pass_count,
        "payment_collection_count": payment_count,
        "expected_outcome_correct_count": expected_correct_count,
        "non_sale_turn_count": len(non_sale_rows),
        "non_sale_correct_count": non_sale_correct_count,
        "non_sale_correctness": rate(non_sale_correct_count, len(non_sale_rows)),
        "safe_close_turn_count": len(safe_close_rows),
        "safe_close_correct_count": safe_close_correct_count,
        "safe_close_correctness": rate(safe_close_correct_count, len(safe_close_rows)),
        "hard_failure_count": int(source_summary.get("hard_failure_count", 0)),
        "leakage_finding_count": int(source_summary.get("leakage_finding_count", 0)),
        "provider_calls_made": False,
        "llm_used": False,
        "runtime_behavior_changed": False,
        "runtime_retrieval_default_enabled": False,
        "prod_018_gate_passed": gate_passed,
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
                "hooked_wins_vs_old": sum(1 for row in items if row["hooked_winner_vs_old"] == "hooked"),
                "payment_collection_count": sum(1 for row in items if row["contains_payment_collection"]),
            }
        )
    return summaries


def build_recommendations(summary: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "recommendation_id": "keep_hooks_as_runtime_candidate_only",
            "priority": "P0",
            "action": "Keep the composer hooks as a candidate for a later guarded runtime implementation, not as default retrieval behavior.",
            "why": "This checkpoint is offline and fixed-case only.",
        },
        {
            "recommendation_id": "convert_hooks_into_runtime_composer_tests_next",
            "priority": "P0",
            "action": "If accepted, add red-first tests around the real guarded response composer before moving any hook into runtime code.",
            "why": f"The offline hook improved {summary['hooked_wins_vs_current']} fixed rows versus current retrieval.",
        },
        {
            "recommendation_id": "keep_prod_017_as_promotion_gate",
            "priority": "P1",
            "action": "Keep PROD-017 scoring as the gate for any later runtime composer change.",
            "why": "Safe generic answers should not pass as equivalent to safe specific answers.",
        },
    ]


def build_payload(prod_015_result_path: Path) -> dict[str, Any]:
    source = load_json(prod_015_result_path)
    rows = [score_hook_row(row) for row in source.get("turn_results", [])]
    summary = build_summary(source, rows)
    decision = "keep_composer_hooks_for_runtime_candidate_not_default"
    if not summary["prod_018_gate_passed"]:
        decision = "revise_composer_hooks_before_runtime_candidate"
    return {
        "prod_018_id": PROD_018_ID,
        "title": "PROD-018 CallCenterEN composer hook test",
        "source_prod_015_result": {
            "prod_015_id": source.get("prod_015_id", ""),
            "path": rel_path(prod_015_result_path),
            "decision": source.get("decision", ""),
            "turn_count": len(source.get("turn_results", [])),
        },
        "hypothesis": {
            "statement": "Narrow offline composer hooks can turn retrieved-but-not-used hints into safer, more specific answers on fixed no-gain rows.",
            "fixed_cases": "unchanged PROD-015 turn_results",
            "editable_surface_changed": "offline_composer_hook_only",
            "scoring_gate": "PROD-017 specificity and objection-fit scoring",
        },
        "hook_set": HOOK_SET,
        "summary": summary,
        "label_summary": build_label_summary(rows),
        "turn_results": rows,
        "recommendations": build_recommendations(summary),
        "boundaries": {
            "provider_calls_made": False,
            "llm_used": False,
            "dataset_download_performed": False,
            "runtime_behavior_changed": False,
            "runtime_retrieval_default_enabled": False,
            "commercial_runtime_prompt_text_from_callcenteren_allowed": False,
            "raw_dataset_text_stored": False,
        },
        "decision": decision,
    }


def render_report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# PROD-018 CallCenterEN Composer Hook Test",
        "",
        "This checkpoint tests an offline composer hook only surface on unchanged PROD-015 rows and scores it with the PROD-017 specificity scorer.",
        "",
        "## Summary",
        "",
        f"- Source PROD-015 decision: `{payload['source_prod_015_result']['decision']}`",
        f"- Fixed cases: `{payload['hypothesis']['fixed_cases']}`",
        f"- Editable surface changed: `{payload['hypothesis']['editable_surface_changed']}`",
        f"- Analyzed turns: `{summary['analyzed_turn_count']}`",
        f"- Eligible hook turns: `{summary['eligible_hook_turn_count']}`",
        f"- Hooked answers: `{summary['hooked_answer_count']}`",
        f"- Preserved existing influenced answers: `{summary['preserved_existing_influenced_count']}`",
        f"- Current retrieval total score: `{summary['current_retrieval_total_score']}`",
        f"- Hooked total score: `{summary['hooked_total_score']}`",
        f"- Hooked score delta vs current: `{summary['hooked_score_delta_vs_current']}`",
        f"- Hooked wins vs current: `{summary['hooked_wins_vs_current']}`",
        f"- Hooked wins vs old: `{summary['hooked_wins_vs_old']}`",
        f"- Old wins against hooked: `{summary['hooked_old_wins']}`",
        f"- Safety gate pass count: `{summary['safety_gate_pass_count']}`",
        f"- Payment collection count: `{summary['payment_collection_count']}`",
        f"- Non-sale correctness: `{summary['non_sale_correctness']}`",
        f"- Safe-close correctness: `{summary['safe_close_correctness']}`",
        f"- PROD-018 gate passed: `{summary['prod_018_gate_passed']}`",
        f"- Decision: `{payload['decision']}`",
        f"- Decision meaning: keep composer hooks for runtime candidate not default",
        "",
        "## Hook Set",
        "",
    ]
    for hook in payload["hook_set"]:
        lines.extend(
            [
                f"### {hook['label']}",
                "",
                f"- Hook ID: `{hook['hook_id']}`",
                f"- Scenario labels: `{', '.join(hook['scenario_labels'])}`",
                f"- Purpose: {hook['purpose']}",
                "",
            ]
        )
    lines.extend(
        [
            "## Label Summary",
            "",
            "| Label | Turns | Hooked Answers | Current Score | Hooked Score | Hooked Wins Vs Current | Hooked Wins Vs Old | Payment Findings |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for item in payload["label_summary"]:
        lines.append(
            "| {label} | {turns} | {hooked} | {current} | {score} | {wins_current} | {wins_old} | {payments} |".format(
                label=item["scenario_label"],
                turns=item["turn_count"],
                hooked=item["hooked_answer_count"],
                current=item["current_retrieval_total_score"],
                score=item["hooked_total_score"],
                wins_current=item["hooked_wins_vs_current"],
                wins_old=item["hooked_wins_vs_old"],
                payments=item["payment_collection_count"],
            )
        )
    lines.extend(["", "## Hooked Examples", ""])
    for row in [item for item in payload["turn_results"] if item["hook_applied"]][:12]:
        lines.extend(
            [
                f"### {row['turn_id']}",
                "",
                f"- Label: `{row['scenario_label']}`",
                f"- Hook: `{row['hook_id']}`",
                f"- Current retrieval score: `{row['current_retrieval_score']['total']}`",
                f"- Hooked score: `{row['hooked_score']['total']}`",
                f"- Hooked winner vs current: `{row['hooked_winner_vs_current']}`",
                f"- Hooked winner vs old: `{row['hooked_winner_vs_old']}`",
                "",
                "Customer question:",
                "",
                "```text",
                str(row["customer_question"]),
                "```",
                "",
                "Current retrieval answer:",
                "",
                "```text",
                str(row["current_retrieval_answer"]),
                "```",
                "",
                "Hooked answer:",
                "",
                "```text",
                str(row["hooked_answer"]),
                "```",
                "",
            ]
        )
    lines.extend(["## Recommendations", ""])
    for item in payload["recommendations"]:
        lines.extend(
            [
                f"### {item['recommendation_id']}",
                "",
                f"- Priority: `{item['priority']}`",
                f"- Action: {item['action']}",
                f"- Why: {item['why']}",
                "",
            ]
        )
    lines.extend(
        [
            "## Boundary",
            "",
            "PROD-018 changes no runtime code. It makes no provider calls, performs no downloads, and does not enable retrieval by default.",
        ]
    )
    return "\n".join(lines) + "\n"
