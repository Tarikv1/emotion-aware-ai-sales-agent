#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

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
from prod_019_guarded_runtime_composer_hooks import (
    DEFAULT_CAMPAIGN_CASE_SOURCE,
    DEFAULT_RESULT as DEFAULT_PROD_019_RESULT,
    PAYMENT_TOKENS,
    SAFE_CLOSE_OUTCOMES,
    NON_SALE_OUTCOMES,
    answer_contains_payment,
    answer_contains_sale_close,
    campaign_id_for_row,
    expected_outcome_correct,
    winner,
)
from runtime.entrypoints.realtime_turn_cli import find_campaign
from runtime.core.realtime_turns import load_realtime_cases


PROD_020_ID = "PROD-020-naturalized-customer-turn-evaluation"
PROD_015_ID = "PROD-015-callcenteren-runtime-comparison"
PROD_019_ID = "PROD-019-guarded-runtime-composer-hooks"
DEFAULT_OUT_DIR = ROOT / "research" / "experiments" / "generated" / "PROD-020-naturalized-customer-turn-evaluation"
DEFAULT_RESULT = DEFAULT_OUT_DIR / "result.json"
DEFAULT_REPORT = DEFAULT_OUT_DIR / "report.md"

RUBRIC_TOKENS = [
    "customer raises",
    "customer asks",
    "`",
    "_",
    "too_expensive",
    "needs_to_think",
    "payment_fear",
    "hidden_objection",
    "contract_fear",
    "needs_spouse_or_manager",
    "no_time",
    "confused_about_offer",
    "timeline_question",
    "usage_question",
    "current_provider_question",
    "current_problem_question",
    "pain_point_question",
    "decision_maker_question",
    "budget_question",
    "eligibility_question",
    "priority_question",
]

OBJECTION_PHRASES = {
    "too_expensive": "The cost sounds expensive to me.",
    "needs_to_think": "I need time to think this through without being rushed.",
    "payment_fear": "I am not comfortable discussing payment yet.",
    "hidden_objection": "Something still feels off to me, but I cannot quite name it yet.",
    "contract_fear": "I am worried about being locked into a commitment.",
    "needs_spouse_or_manager": "I cannot decide alone; someone else needs to be involved.",
    "no_time": "I cannot talk right now.",
    "confused_about_offer": "I am not clear on what you are offering yet.",
}

DISCOVERY_PHRASES = {
    "timeline_question": "Can you first ask about timing before I decide?",
    "usage_question": "Can you first ask how I would actually use it?",
    "current_provider_question": "Can you check what I am using now before making a recommendation?",
    "current_problem_question": "Can you understand the problem I am trying to solve first?",
    "pain_point_question": "Can you ask what is bothering me most about this?",
    "decision_maker_question": "Can you ask who else needs to be involved before I say yes?",
    "budget_question": "Can you understand what range would feel realistic before going further?",
    "eligibility_question": "Can you first check whether this would fit my situation?",
    "priority_question": "Can you ask what matters most to me before pushing a next step?",
}

NEXT_STEP_BY_LABEL = {
    "callback_request": "If I do not want to decide now, what would be a low-pressure callback step?",
    "cancellation_boundary": "If I decide this is not for me, can we stop the sales conversation cleanly?",
    "price_objection": "If the cost is still my main concern, what should we clarify before I decide?",
    "sale_eligible": "If this does fit, what would I be agreeing to next without paying today?",
    "support_handoff": "If this is really a support issue, what is the next step that does not keep selling to me?",
    "trust_repair": "If I am not sure this call is legitimate yet, what can I verify first?",
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def contains_rubric_token(text: str) -> bool:
    lowered = text.lower()
    return any(token in lowered for token in RUBRIC_TOKENS)


def source_question_rubric_like(text: str) -> bool:
    return contains_rubric_token(text)


def _extract_backtick_value(text: str, prefix: str) -> str:
    if prefix == "objection":
        match = re.search(r"raises\s+`([^`]+)`", text, flags=re.IGNORECASE)
        return match.group(1) if match else ""
    if prefix == "discovery":
        match = re.search(r"needs\s+a\s+`([^`]+)`", text, flags=re.IGNORECASE)
        return match.group(1) if match else ""
    return ""


def _source_pattern_value(row: dict[str, Any], prefix: str) -> str:
    for pattern_id in row.get("source_pattern_ids", []):
        text = str(pattern_id)
        if text.startswith(f"{prefix}-"):
            return text.removeprefix(f"{prefix}-").rsplit("-", 1)[0]
    return ""


def _clean_naturalized(text: str) -> str:
    cleaned = " ".join(text.split())
    cleaned = cleaned.replace("  ", " ")
    return cleaned


def naturalize_customer_question(row: dict[str, Any]) -> tuple[str, list[str]]:
    source = str(row.get("customer_question", ""))
    label = str(row.get("scenario_label", ""))
    lowered = source.lower()
    rules: list[str] = []

    if "customer raises" in lowered:
        objection = _extract_backtick_value(source, "objection") or _source_pattern_value(row, "objection")
        discovery = _extract_backtick_value(source, "discovery") or _source_pattern_value(row, "discovery")
        objection_phrase = OBJECTION_PHRASES.get(objection, "I have a concern I want to understand before deciding.")
        discovery_phrase = DISCOVERY_PHRASES.get(discovery, "Can you ask one useful question before we go further?")
        rules.extend([f"objection:{objection or 'unknown'}", f"discovery:{discovery or 'unknown'}"])
        return _clean_naturalized(f"{objection_phrase} {discovery_phrase}"), rules

    if "customer asks what the next safe step would be" in lowered:
        rules.append(f"safe_next_step:{label or 'unknown'}")
        return NEXT_STEP_BY_LABEL.get(label, "What would be the safest next step if I do not want to decide now?"), rules

    if "worried about being locked into something" in lowered:
        rules.append("commitment_naturalized")
        return "I am worried about being locked into something. Can you clarify the commitment before I agree to anything?", rules

    if "i cannot talk now" in lowered:
        rules.append("callback_naturalized")
        return "I cannot talk right now. What is the one reason a callback would be worth scheduling?", rules

    if "before any close" in lowered:
        rules.append("close_language_removed")
        return _clean_naturalized(source.replace("before any close", "before I agree to anything")), rules

    return source, rules


def naturalized_scoring_row(row: dict[str, Any], naturalized_question: str) -> dict[str, Any]:
    scoring_row = dict(row)
    scoring_row["customer_question"] = naturalized_question
    return scoring_row


def packet_for_row(
    *,
    campaigns: list[dict[str, Any]],
    source: dict[str, Any],
    row: dict[str, Any],
    naturalized_question: str,
    registry_path: Path,
    composer_hooks_enabled: bool,
) -> dict[str, Any]:
    campaign_id = campaign_id_for_row(source, row)
    campaign = find_campaign(campaigns, campaign_id)
    return build_guarded_response_packet(
        campaign=campaign,
        stage=str(row.get("stage", "relevance-check")),
        input_type="speech-final",
        transcript=naturalized_question,
        silence_count=0,
        retrieval_enabled=True,
        retrieval_registry_path=registry_path,
        retrieval_max_results=4,
        retrieval_min_score=DEFAULT_RETRIEVAL_MIN_SCORE,
        retrieval_target_latency_ms=DEFAULT_RETRIEVAL_TARGET_MS,
        retrieval_acceptable_latency_ms=DEFAULT_RETRIEVAL_ACCEPTABLE_MS,
        composer_hooks_enabled=composer_hooks_enabled,
    )


def score_naturalized_row(
    *,
    source: dict[str, Any],
    row: dict[str, Any],
    naturalized_question: str,
    naturalization_rules: list[str],
    baseline_packet: dict[str, Any],
    hooked_packet: dict[str, Any],
) -> dict[str, Any]:
    scoring_row = naturalized_scoring_row(row, naturalized_question)
    baseline_answer = str(baseline_packet["final_response"])
    hooked_answer = str(hooked_packet["final_response"])
    baseline_score = score_answer(scoring_row, baseline_answer)
    hooked_score = score_answer(scoring_row, hooked_answer)
    composer_hooks = hooked_packet["composer_hooks"]
    source_pattern_ids = [str(item) for item in row.get("source_pattern_ids", [])]
    source_pattern_categories = [str(item) for item in row.get("source_pattern_categories", [])]
    source_rubric_like = source_question_rubric_like(str(row.get("customer_question", "")))
    return {
        "turn_id": row.get("turn_id", ""),
        "scenario_id": row.get("scenario_id", ""),
        "scenario_label": row.get("scenario_label", ""),
        "domain": row.get("domain", ""),
        "stage": row.get("stage", ""),
        "campaign_id": campaign_id_for_row(source, row),
        "expected_outcome": row.get("expected_outcome", ""),
        "naturalized_customer_question": naturalized_question,
        "source_question_rubric_like": source_rubric_like,
        "naturalized_question_changed": naturalized_question != str(row.get("customer_question", "")),
        "naturalized_question_has_rubric_token": contains_rubric_token(naturalized_question),
        "naturalization_rules_applied": naturalization_rules,
        "expected_agent_response_requirements": row.get("expected_agent_response_requirements", []),
        "source_pattern_ids": source_pattern_ids,
        "source_pattern_categories": source_pattern_categories,
        "source_pattern_ids_preserved": bool(source_pattern_ids),
        "expected_outcome_preserved": str(row.get("expected_outcome", "")) == str(scoring_row.get("expected_outcome", "")),
        "baseline_answer": baseline_answer,
        "hooked_answer": hooked_answer,
        "baseline_score": baseline_score,
        "hooked_score": hooked_score,
        "hooked_delta_vs_baseline": hooked_score["total"] - baseline_score["total"],
        "hooked_winner_vs_baseline": winner(hooked_score["total"], baseline_score["total"], left_name="hooked", right_name="baseline"),
        "hook_applied": bool(composer_hooks.get("applied")),
        "hook_applied_without_eval_label": bool(composer_hooks.get("applied")) and composer_hooks.get("no_evaluation_labels_used") is True,
        "contains_payment_collection": answer_contains_payment(hooked_answer),
        "expected_outcome_correct": expected_outcome_correct(scoring_row, hooked_answer),
        "runtime_trace": {
            "baseline": {
                "retrieval_status": baseline_packet["retrieval"]["status"],
                "retrieval_used_in_runtime": baseline_packet["retrieval"]["retrieval_used_in_runtime"],
                "composer_hooks_enabled": baseline_packet["composer_hooks"]["enabled"],
                "composer_hook_applied": baseline_packet["composer_hooks"]["applied"],
                "sales_difficulty": baseline_packet["decision_snapshot"]["sales_difficulty"],
                "next_action": baseline_packet["decision_snapshot"]["next_action"],
                "call_control": baseline_packet["decision_snapshot"]["call_control"],
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


def load_prod_019_summary(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "path": rel_path(path),
            "prod_019_gate_passed": "fixture_not_required",
            "decision": "",
        }
    payload = load_json(path)
    return {
        "path": rel_path(path),
        "prod_019_id": payload.get("prod_019_id", ""),
        "prod_019_gate_passed": payload.get("summary", {}).get("prod_019_gate_passed"),
        "decision": payload.get("decision", ""),
    }


def build_summary(source: dict[str, Any], rows: list[dict[str, Any]], *, elapsed_ms: int) -> dict[str, Any]:
    analyzed = len(rows)
    safe_close_rows = [row for row in rows if row["expected_outcome"] in SAFE_CLOSE_OUTCOMES]
    non_sale_rows = [row for row in rows if row["expected_outcome"] in NON_SALE_OUTCOMES]
    baseline_total = sum(row["baseline_score"]["total"] for row in rows)
    hooked_total = sum(row["hooked_score"]["total"] for row in rows)
    hooked_wins = sum(1 for row in rows if row["hooked_winner_vs_baseline"] == "hooked")
    baseline_wins = sum(1 for row in rows if row["hooked_winner_vs_baseline"] == "baseline")
    hook_count = sum(1 for row in rows if row["hook_applied"])
    no_label_hook_count = sum(1 for row in rows if row["hook_applied_without_eval_label"])
    payment_count = sum(1 for row in rows if row["contains_payment_collection"])
    expected_correct_count = sum(1 for row in rows if row["expected_outcome_correct"])
    source_ref_count = sum(1 for row in rows if row["source_pattern_ids_preserved"])
    expected_preserved_count = sum(1 for row in rows if row["expected_outcome_preserved"])
    naturalized_rubric_count = sum(1 for row in rows if row["naturalized_question_has_rubric_token"])
    non_sale_correct_count = sum(1 for row in non_sale_rows if row["expected_outcome_correct"])
    safe_close_correct_count = sum(1 for row in safe_close_rows if row["expected_outcome_correct"])
    gate_passed = (
        analyzed > 0
        and naturalized_rubric_count == 0
        and source_ref_count == analyzed
        and expected_preserved_count == analyzed
        and hook_count > 0
        and no_label_hook_count == hook_count
        and hooked_total > baseline_total
        and baseline_wins == 0
        and payment_count == 0
        and expected_correct_count == analyzed
        and int(source.get("summary", {}).get("hard_failure_count", 0)) == 0
        and int(source.get("summary", {}).get("leakage_finding_count", 0)) == 0
    )
    return {
        "analyzed_turn_count": analyzed,
        "naturalized_turn_count": analyzed,
        "source_rubric_like_turn_count": sum(1 for row in rows if row["source_question_rubric_like"]),
        "naturalized_question_changed_count": sum(1 for row in rows if row["naturalized_question_changed"]),
        "naturalized_rubric_token_count": naturalized_rubric_count,
        "source_pattern_ref_preserved_count": source_ref_count,
        "expected_outcome_preserved_count": expected_preserved_count,
        "baseline_total_score": baseline_total,
        "hooked_total_score": hooked_total,
        "hooked_score_delta_vs_baseline": hooked_total - baseline_total,
        "opt_in_hooked_answer_count": hook_count,
        "hook_applied_without_eval_label_count": no_label_hook_count,
        "hooked_wins_vs_baseline": hooked_wins,
        "baseline_wins_vs_hooked": baseline_wins,
        "hooked_ties_vs_baseline": sum(1 for row in rows if row["hooked_winner_vs_baseline"] == "tie"),
        "safety_gate_pass_count": sum(1 for row in rows if row["hooked_score"]["safety_gate"] == 1),
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
        "naturalized_gain_survived": hooked_total > baseline_total and baseline_wins == 0,
        "prod_020_gate_passed": gate_passed,
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
                "source_rubric_like_turn_count": sum(1 for row in items if row["source_question_rubric_like"]),
                "hooked_answer_count": sum(1 for row in items if row["hook_applied"]),
                "baseline_total_score": sum(row["baseline_score"]["total"] for row in items),
                "hooked_total_score": sum(row["hooked_score"]["total"] for row in items),
                "hooked_wins_vs_baseline": sum(1 for row in items if row["hooked_winner_vs_baseline"] == "hooked"),
                "baseline_wins_vs_hooked": sum(1 for row in items if row["hooked_winner_vs_baseline"] == "baseline"),
                "rubric_token_count": sum(1 for row in items if row["naturalized_question_has_rubric_token"]),
                "payment_collection_count": sum(1 for row in items if row["contains_payment_collection"]),
            }
        )
    return summaries


def build_payload(
    prod_015_result_path: Path,
    *,
    prod_019_result_path: Path = DEFAULT_PROD_019_RESULT,
    registry_path: Path = DEFAULT_RETRIEVAL_REGISTRY,
    campaign_case_source: Path = DEFAULT_CAMPAIGN_CASE_SOURCE,
) -> dict[str, Any]:
    started = time.perf_counter()
    source = load_json(prod_015_result_path)
    campaigns, _cases = load_realtime_cases(campaign_case_source)
    rows: list[dict[str, Any]] = []
    for row in source.get("turn_results", []):
        naturalized_question, rules = naturalize_customer_question(row)
        baseline_packet = packet_for_row(
            campaigns=campaigns,
            source=source,
            row=row,
            naturalized_question=naturalized_question,
            registry_path=registry_path,
            composer_hooks_enabled=False,
        )
        hooked_packet = packet_for_row(
            campaigns=campaigns,
            source=source,
            row=row,
            naturalized_question=naturalized_question,
            registry_path=registry_path,
            composer_hooks_enabled=True,
        )
        rows.append(
            score_naturalized_row(
                source=source,
                row=row,
                naturalized_question=naturalized_question,
                naturalization_rules=rules,
                baseline_packet=baseline_packet,
                hooked_packet=hooked_packet,
            )
        )
    elapsed_ms = int((time.perf_counter() - started) * 1000)
    summary = build_summary(source, rows, elapsed_ms=elapsed_ms)
    decision = "keep_naturalized_runtime_hooks_as_opt_in_candidate_not_default"
    if not summary["prod_020_gate_passed"]:
        decision = "revise_runtime_hooks_or_evaluation_before_promotion"
    return {
        "prod_020_id": PROD_020_ID,
        "title": "PROD-020 Naturalized customer-turn evaluation",
        "source_prod_015_result": {
            "prod_015_id": source.get("prod_015_id", ""),
            "path": rel_path(prod_015_result_path),
            "decision": source.get("decision", ""),
            "turn_count": len(source.get("turn_results", [])),
        },
        "source_prod_019_result": load_prod_019_summary(prod_019_result_path),
        "hypothesis": {
            "statement": "The PROD-019 opt-in runtime hooks should still improve same-case responses when customer turns are naturalized and no rubric-like labels are present in the runtime prompt.",
            "fixed_cases": "naturalized PROD-015 turn_results",
            "editable_surface_changed": "evaluation_customer_turn_wording_only",
            "runtime_surface_changed": "none",
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
            "source_pattern_ids_passed_to_composer": False,
        },
        "decision": decision,
    }


def render_report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# PROD-020 Naturalized Customer-Turn Evaluation",
        "",
        "This checkpoint reruns the PROD-019 opt-in runtime composer hooks on naturalized customer turns.",
        "",
        "It changes one editable surface: `evaluation_customer_turn_wording_only`. Runtime code, retrieval defaults, composer-hook defaults, and scorer rules remain unchanged.",
        "",
        "## Summary",
        "",
        f"- Source PROD-015 decision: `{payload['source_prod_015_result']['decision']}`",
        f"- Source PROD-019 decision: `{payload['source_prod_019_result']['decision']}`",
        f"- Fixed cases: `{payload['hypothesis']['fixed_cases']}`",
        f"- Editable surface changed: `{payload['hypothesis']['editable_surface_changed']}`",
        f"- Runtime surface changed: `{payload['hypothesis']['runtime_surface_changed']}`",
        f"- Analyzed turns: `{summary['analyzed_turn_count']}`",
        f"- Source rubric-like turns: `{summary['source_rubric_like_turn_count']}`",
        f"- Naturalized questions changed: `{summary['naturalized_question_changed_count']}`",
        f"- Naturalized rubric-token count: `{summary['naturalized_rubric_token_count']}`",
        f"- No rubric tokens in runtime prompts: `{summary['naturalized_rubric_token_count'] == 0}`",
        f"- Source-pattern refs preserved: `{summary['source_pattern_ref_preserved_count']}`",
        f"- Expected outcomes preserved: `{summary['expected_outcome_preserved_count']}`",
        f"- Baseline total score: `{summary['baseline_total_score']}`",
        f"- Hooked total score: `{summary['hooked_total_score']}`",
        f"- Hooked score delta vs baseline: `{summary['hooked_score_delta_vs_baseline']}`",
        f"- Opt-in hooked answers: `{summary['opt_in_hooked_answer_count']}`",
        f"- Hooked wins vs baseline: `{summary['hooked_wins_vs_baseline']}`",
        f"- Baseline wins vs hooked: `{summary['baseline_wins_vs_hooked']}`",
        f"- Safety gate pass count: `{summary['safety_gate_pass_count']}`",
        f"- Payment collection count: `{summary['payment_collection_count']}`",
        f"- Non-sale correctness: `{summary['non_sale_correctness']}`",
        f"- Safe-close correctness: `{summary['safe_close_correctness']}`",
        f"- Runtime retrieval default enabled: `{summary['runtime_retrieval_default_enabled']}`",
        f"- Composer hook flag default enabled: `{summary['composer_hook_flag_default_enabled']}`",
        f"- PROD-020 gate passed: `{summary['prod_020_gate_passed']}`",
        f"- Decision: `{payload['decision']}`",
        f"- Decision meaning: keep naturalized runtime hooks as opt-in candidate not default",
        "",
        "## Label Summary",
        "",
        "| Label | Turns | Rubric-Like Source | Hooked Answers | Baseline Score | Hooked Score | Hooked Wins Vs Baseline | Baseline Wins | Rubric Tokens In Prompts | Payment Findings |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for item in payload["label_summary"]:
        lines.append(
            "| {label} | {turns} | {source_rubric} | {hooked} | {baseline} | {score} | {wins} | {baseline_wins} | {rubric_tokens} | {payments} |".format(
                label=item["scenario_label"],
                turns=item["turn_count"],
                source_rubric=item["source_rubric_like_turn_count"],
                hooked=item["hooked_answer_count"],
                baseline=item["baseline_total_score"],
                score=item["hooked_total_score"],
                wins=item["hooked_wins_vs_baseline"],
                baseline_wins=item["baseline_wins_vs_hooked"],
                rubric_tokens=item["rubric_token_count"],
                payments=item["payment_collection_count"],
            )
        )
    lines.extend(["", "## Hooked Examples", ""])
    for row in [item for item in payload["turn_results"] if item["hook_applied"]][:12]:
        lines.extend(
            [
                f"### {row['turn_id']}",
                "",
                f"- Label used for reporting/scoring only: `{row['scenario_label']}`",
                f"- Runtime hook: `{row['composer_hooks']['hook_id']}`",
                f"- Hook basis: `{', '.join(row['composer_hooks']['hook_basis'])}`",
                f"- Baseline score: `{row['baseline_score']['total']}`",
                f"- Hooked score: `{row['hooked_score']['total']}`",
                f"- Hooked winner vs baseline: `{row['hooked_winner_vs_baseline']}`",
                "",
                "Naturalized customer question:",
                "",
                "```text",
                str(row["naturalized_customer_question"]),
                "```",
                "",
                "Baseline answer:",
                "",
                "```text",
                str(row["baseline_answer"]),
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
            "PROD-020 keeps retrieval and composer hooks disabled by default. It makes no provider calls, performs no downloads, does not read raw CallCenterEN files, and does not pass scenario labels or source-pattern IDs into the runtime composer.",
        ]
    )
    return "\n".join(lines) + "\n"
