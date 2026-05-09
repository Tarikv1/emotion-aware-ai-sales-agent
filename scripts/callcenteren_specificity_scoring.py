#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PROD_017_ID = "PROD-017-callcenteren-specificity-scoring"
PROD_015_ID = "PROD-015-callcenteren-runtime-comparison"
DEFAULT_PROD_015_RESULT = ROOT / "research" / "experiments" / "generated" / "PROD-015-callcenteren-runtime-comparison" / "result.json"
DEFAULT_OUT_DIR = ROOT / "research" / "experiments" / "generated" / "PROD-017-callcenteren-specificity-scoring"
DEFAULT_RESULT = DEFAULT_OUT_DIR / "result.json"
DEFAULT_REPORT = DEFAULT_OUT_DIR / "report.md"

GENERIC_ANSWER_PATTERNS = [
    "price, fit, timing, or exact product details",
    "concrete reason for reaching out",
]
PAYMENT_TOKENS = ["credit card", "take your payment", "collect payment", "payment now", "card number"]
SALE_CLOSE_TOKENS = ["process the sale", "take your payment", "collect payment", "card number"]
STOPWORDS = {
    "about",
    "after",
    "alone",
    "also",
    "before",
    "because",
    "cannot",
    "customer",
    "decide",
    "details",
    "first",
    "from",
    "help",
    "into",
    "main",
    "need",
    "needs",
    "question",
    "raises",
    "safe",
    "should",
    "that",
    "their",
    "there",
    "this",
    "turn",
    "understand",
    "what",
    "when",
    "where",
    "which",
    "with",
    "would",
    "your",
}


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


def rate(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(numerator / denominator, 4)


def tokenize(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9]+", text.lower().replace("_", " "))
        if len(token) > 2 and token not in STOPWORDS
    }


def normalized_text(row: dict[str, Any]) -> str:
    parts = [
        str(row.get("scenario_label", "")),
        str(row.get("expected_outcome", "")),
        str(row.get("customer_question", "")),
        " ".join(str(item) for item in row.get("expected_agent_response_requirements", []) if item),
    ]
    return " ".join(parts).lower().replace("_", " ")


def contains_any(text: str, tokens: list[str]) -> bool:
    lowered = text.lower()
    return any(token in lowered for token in tokens)


def is_generic_answer(answer: str) -> bool:
    lowered = answer.lower()
    return any(pattern in lowered for pattern in GENERIC_ANSWER_PATTERNS)


def has_question(answer: str) -> bool:
    lowered = answer.lower()
    return "?" in answer or any(phrase in lowered for phrase in ["should i", "would it help", "is your", "what ", "which "])


def safety_gate(row: dict[str, Any], answer: str) -> int:
    lowered = answer.lower()
    if contains_any(lowered, PAYMENT_TOKENS):
        return 0
    expected = str(row.get("expected_outcome", ""))
    if expected in {"non_sale_correct", "support_only", "human_handoff", "end_call"} and contains_any(lowered, SALE_CLOSE_TOKENS):
        return 0
    return 1


def expected_keywords(row: dict[str, Any]) -> set[str]:
    text = normalized_text(row)
    keywords: set[str] = set()
    if any(token in text for token in ["price", "expensive", "cost", "value"]):
        keywords.update({"price", "cost", "value", "terms", "worth"})
    if any(token in text for token in ["callback", "call back", "no time", "timing", "timeline", "priority"]):
        keywords.update({"time", "timing", "callback", "priority", "schedule", "later"})
    if any(token in text for token in ["trust", "verify", "verified", "transparency"]):
        keywords.update({"trust", "verify", "verified", "company", "proof", "context", "security", "transparent"})
    if any(token in text for token in ["human", "handoff", "specialist", "issue", "resolution", "unresolved"]):
        keywords.update({"route", "human", "specialist", "issue", "resolution", "support"})
    if any(token in text for token in ["cancel", "not interested", "refusal", "boundary", "stop selling"]):
        keywords.update({"stop", "sales", "discussion", "called", "again", "choice", "no"})
    if any(token in text for token in ["decision maker", "boss", "manager", "spouse", "partner", "cannot decide"]):
        keywords.update({"summary", "boss", "manager", "partner", "decision", "concern", "share"})
    if any(token in text for token in ["confused", "clarification", "explain"]):
        keywords.update({"explain", "clarify", "useful", "part", "details"})
    if any(token in text for token in ["eligible", "eligibility", "fit", "sale ready", "verbal commitment"]):
        keywords.update({"fit", "eligible", "situation", "review", "next"})
    return keywords


def requirement_groups(row: dict[str, Any]) -> list[set[str]]:
    groups: list[set[str]] = []
    for requirement in row.get("expected_agent_response_requirements", []):
        lowered = str(requirement).lower()
        if "acknowledge" in lowered:
            groups.append({"thanks", "understand", "makes sense", "fair", "of course", "hear"})
        if "discovery" in lowered or "clarification" in lowered:
            groups.append({"?", "concern", "question", "which", "what", "should", "whether"})
        if "callback" in lowered or "time pressure" in lowered:
            groups.append({"callback", "time", "schedule", "later", "summary"})
        if "price" in lowered or "cost" in lowered or "value" in lowered:
            groups.append({"price", "cost", "value", "worth", "terms"})
        if "eligibility" in lowered or "fit" in lowered:
            groups.append({"eligible", "fit", "situation", "review"})
        if "route" in lowered or "hand off" in lowered or "handoff" in lowered:
            groups.append({"route", "human", "specialist", "handoff"})
        if "issue resolution" in lowered:
            groups.append({"issue", "resolution", "support", "specialist"})
        if "trust" in lowered or "verified" in lowered or "transparency" in lowered:
            groups.append({"trust", "verify", "verified", "company", "context", "transparent", "proof"})
        if "stop selling" in lowered or "no further sales" in lowered:
            groups.append({"stop", "sales", "discussion", "called", "again", "choice"})
    return groups


def count_matching_groups(answer: str, groups: list[set[str]]) -> int:
    lowered = answer.lower()
    count = 0
    for group in groups:
        if any(token == "?" and "?" in answer for token in group) or any(token != "?" and token in lowered for token in group):
            count += 1
    return count


def customer_specificity(row: dict[str, Any], answer: str) -> int:
    answer_tokens = tokenize(answer)
    source_tokens = tokenize(str(row.get("customer_question", "")))
    expected = expected_keywords(row)
    overlap = answer_tokens & (source_tokens | expected)
    if not overlap:
        return 0
    score = min(2, len(overlap))
    if is_generic_answer(answer):
        return min(score, 1)
    return score


def requirement_fit(row: dict[str, Any], answer: str) -> int:
    groups = requirement_groups(row)
    if not groups:
        return 0
    return min(2, count_matching_groups(answer, groups))


def objection_fit(row: dict[str, Any], answer: str) -> int:
    expected = expected_keywords(row)
    if not expected:
        return 0
    answer_tokens = tokenize(answer)
    overlap = answer_tokens & expected
    score = min(2, len(overlap))
    if is_generic_answer(answer):
        return min(score, 1)
    return score


def score_answer(row: dict[str, Any], answer: str) -> dict[str, Any]:
    safety = safety_gate(row, answer)
    question = 1 if has_question(answer) else 0
    specificity = customer_specificity(row, answer)
    fit = requirement_fit(row, answer)
    objection = objection_fit(row, answer)
    generic_penalty = -1 if is_generic_answer(answer) else 0
    total = safety + question + specificity + fit + objection + generic_penalty
    return {
        "total": total,
        "safety_gate": safety,
        "question_relevance": question,
        "customer_specificity": specificity,
        "requirement_fit": fit,
        "objection_fit": objection,
        "generic_answer_penalty": generic_penalty,
    }


def score_row(row: dict[str, Any]) -> dict[str, Any]:
    old_score = score_answer(row, str(row.get("old_runtime_answer", "")))
    retrieval_score = score_answer(row, str(row.get("retrieval_runtime_answer", "")))
    delta = retrieval_score["total"] - old_score["total"]
    if delta > 0:
        winner = "retrieval"
    elif delta < 0:
        winner = "old_runtime"
    else:
        winner = "tie"
    prod_015_winner = str(row.get("winner", ""))
    return {
        "turn_id": row.get("turn_id", ""),
        "scenario_id": row.get("scenario_id", ""),
        "scenario_label": row.get("scenario_label", ""),
        "domain": row.get("domain", ""),
        "expected_outcome": row.get("expected_outcome", ""),
        "customer_question": row.get("customer_question", ""),
        "expected_agent_response_requirements": row.get("expected_agent_response_requirements", []),
        "old_runtime_answer": row.get("old_runtime_answer", ""),
        "retrieval_runtime_answer": row.get("retrieval_runtime_answer", ""),
        "retrieval_status": row.get("retrieval_status", ""),
        "retrieval_used_in_runtime": bool(row.get("retrieval_used_in_runtime")),
        "prod_015_winner": prod_015_winner,
        "prod_015_old_score": row.get("old_runtime_score", 0),
        "prod_015_retrieval_score": row.get("retrieval_runtime_score", 0),
        "old_score": old_score,
        "retrieval_score": retrieval_score,
        "score_delta": delta,
        "winner": winner,
        "changed_from_prod_015_tie": prod_015_winner == "tie" and winner != "tie",
        "absolute_quality_gap": (
            old_score["generic_answer_penalty"] < 0
            and retrieval_score["generic_answer_penalty"] < 0
        )
        or (
            old_score["customer_specificity"] == 0
            and retrieval_score["customer_specificity"] == 0
            and old_score["requirement_fit"] < 2
            and retrieval_score["requirement_fit"] < 2
        ),
    }


def build_scoring_schema() -> dict[str, Any]:
    return {
        "schema_id": "prod-017-specificity-objection-fit-v1",
        "max_score_per_answer": 8,
        "components": {
            "safety_gate": "One point if the answer avoids payment collection and unsafe close language for the expected outcome.",
            "question_relevance": "One point if the answer asks a focused question or clarification.",
            "customer_specificity": "Zero to two points for using meaningful customer-question or expected-issue cues.",
            "requirement_fit": "Zero to two points for covering expected response requirements such as handoff, trust repair, callback, price, or fit.",
            "objection_fit": "Zero to two points for answering the scenario-specific objection or boundary type.",
            "generic_answer_penalty": "Minus one point for generic catch-all answers that can be safe but not specific.",
        },
    }


def build_summary(source: dict[str, Any], turn_scores: list[dict[str, Any]]) -> dict[str, Any]:
    source_summary = source.get("summary", {})
    analyzed_turn_count = len(turn_scores)
    old_total = sum(int(row["old_score"]["total"]) for row in turn_scores)
    retrieval_total = sum(int(row["retrieval_score"]["total"]) for row in turn_scores)
    winner_counts = Counter(row["winner"] for row in turn_scores)
    prod_015_tie_count = sum(1 for row in turn_scores if row["prod_015_winner"] == "tie")
    changed_from_tie = sum(1 for row in turn_scores if row["changed_from_prod_015_tie"])
    influenced_rows = [row for row in turn_scores if row["retrieval_used_in_runtime"]]
    influenced_retrieval_wins = sum(1 for row in influenced_rows if row["winner"] == "retrieval")
    absolute_quality_gap_count = sum(1 for row in turn_scores if row["absolute_quality_gap"])
    retrieval_changed_answers = sum(1 for row in turn_scores if str(row["old_runtime_answer"]).strip() != str(row["retrieval_runtime_answer"]).strip())
    generic_old_count = sum(1 for row in turn_scores if row["old_score"]["generic_answer_penalty"] < 0)
    generic_retrieval_count = sum(1 for row in turn_scores if row["retrieval_score"]["generic_answer_penalty"] < 0)
    return {
        "analyzed_turn_count": analyzed_turn_count,
        "hard_failure_count": int(source_summary.get("hard_failure_count", 0)),
        "leakage_finding_count": int(source_summary.get("leakage_finding_count", 0)),
        "prod_015_old_total_score": int(source_summary.get("old_runtime_total_score", 0)),
        "prod_015_retrieval_total_score": int(source_summary.get("retrieval_runtime_total_score", 0)),
        "prod_015_tie_count": prod_015_tie_count,
        "old_total_score": old_total,
        "retrieval_total_score": retrieval_total,
        "score_delta": retrieval_total - old_total,
        "prod_017_retrieval_wins": winner_counts.get("retrieval", 0),
        "prod_017_old_wins": winner_counts.get("old_runtime", 0),
        "prod_017_ties": winner_counts.get("tie", 0),
        "changed_from_prod_015_tie_count": changed_from_tie,
        "specificity_scoring_detected_delta": changed_from_tie > 0,
        "specificity_blind_spot_confirmed": changed_from_tie > 0 and int(source_summary.get("retrieval_turn_wins", 0)) == 0,
        "retrieval_changed_answer_count": retrieval_changed_answers,
        "influenced_turn_count": len(influenced_rows),
        "influenced_retrieval_win_count": influenced_retrieval_wins,
        "influenced_retrieval_win_rate": rate(influenced_retrieval_wins, len(influenced_rows)),
        "absolute_quality_gap_count": absolute_quality_gap_count,
        "absolute_quality_gap_rate": rate(absolute_quality_gap_count, analyzed_turn_count),
        "generic_old_answer_count": generic_old_count,
        "generic_retrieval_answer_count": generic_retrieval_count,
        "generic_old_answer_rate": rate(generic_old_count, analyzed_turn_count),
        "generic_retrieval_answer_rate": rate(generic_retrieval_count, analyzed_turn_count),
        "provider_calls_made": False,
        "llm_used": False,
        "runtime_behavior_changed": False,
        "runtime_retrieval_default_enabled": False,
    }


def build_label_summary(turn_scores: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in turn_scores:
        grouped[str(row["scenario_label"])].append(row)
    summaries: list[dict[str, Any]] = []
    for label in sorted(grouped):
        rows = grouped[label]
        summaries.append(
            {
                "scenario_label": label,
                "turn_count": len(rows),
                "old_total_score": sum(row["old_score"]["total"] for row in rows),
                "retrieval_total_score": sum(row["retrieval_score"]["total"] for row in rows),
                "retrieval_wins": sum(1 for row in rows if row["winner"] == "retrieval"),
                "old_wins": sum(1 for row in rows if row["winner"] == "old_runtime"),
                "ties": sum(1 for row in rows if row["winner"] == "tie"),
                "absolute_quality_gap_count": sum(1 for row in rows if row["absolute_quality_gap"]),
            }
        )
    return summaries


def build_recommendations(summary: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "recommendation_id": "use_prod_017_scoring_as_next_composer_gate",
            "priority": "P0",
            "action": "Use the PROD-017 specificity and objection-fit scorer as the gate for any PROD-018 composer-hook test.",
            "why": "It can distinguish safe-specific answers from safe-generic answers on unchanged PROD-015 cases.",
        },
        {
            "recommendation_id": "do_not_claim_retrieval_gain_until_composer_changes_more_answers",
            "priority": "P0",
            "action": "Do not claim broad retrieval improvement until a composer change improves more than the current small set of changed answers.",
            "why": f"Only {summary['retrieval_changed_answer_count']} answers changed in the fixed source result.",
        },
        {
            "recommendation_id": "add_naturalized_prompt_variant_after_scoring",
            "priority": "P1",
            "action": "After the scorer is stable, create a naturalized prompt variant for rubric-like customer turns.",
            "why": "The scorer can evaluate specificity, but the runtime classifier still needs more natural customer phrasing.",
        },
    ]


def build_payload(prod_015_result_path: Path) -> dict[str, Any]:
    source = load_json(prod_015_result_path)
    turn_scores = [score_row(row) for row in source.get("turn_results", [])]
    summary = build_summary(source, turn_scores)
    decision = "use_specificity_scoring_before_composer_hook_test"
    if summary["hard_failure_count"] or summary["leakage_finding_count"]:
        decision = "fix_safety_or_leakage_before_specificity_scoring"
    return {
        "prod_017_id": PROD_017_ID,
        "title": "PROD-017 CallCenterEN specificity scoring",
        "source_prod_015_result": {
            "prod_015_id": source.get("prod_015_id", ""),
            "path": rel_path(prod_015_result_path),
            "decision": source.get("decision", ""),
            "turn_count": len(source.get("turn_results", [])),
        },
        "hypothesis": {
            "statement": "A scorer that measures specificity and objection fit will expose quality differences hidden by the safe-only PROD-015 score.",
            "fixed_cases": "unchanged PROD-015 turn_results",
            "editable_surface_changed": "evaluation_scoring_only",
        },
        "scoring_schema": build_scoring_schema(),
        "summary": summary,
        "label_summary": build_label_summary(turn_scores),
        "turn_scores": turn_scores,
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
        "# PROD-017 CallCenterEN Specificity Scoring",
        "",
        "This checkpoint adds evaluation scoring only. It re-scores unchanged PROD-015 rows for question relevance, customer specificity, requirement fit, objection fit, and generic-answer penalty.",
        "",
        "## Summary",
        "",
        f"- Source PROD-015 decision: `{payload['source_prod_015_result']['decision']}`",
        f"- Fixed cases: `{payload['hypothesis']['fixed_cases']}`",
        f"- Editable surface changed: `{payload['hypothesis']['editable_surface_changed']}`",
        f"- Analyzed turns: `{summary['analyzed_turn_count']}`",
        f"- PROD-015 ties: `{summary['prod_015_tie_count']}`",
        f"- PROD-017 old total score: `{summary['old_total_score']}`",
        f"- PROD-017 retrieval total score: `{summary['retrieval_total_score']}`",
        f"- Score delta: `{summary['score_delta']}`",
        f"- Retrieval wins: `{summary['prod_017_retrieval_wins']}`",
        f"- Old wins: `{summary['prod_017_old_wins']}`",
        f"- Ties: `{summary['prod_017_ties']}`",
        f"- Changed from PROD-015 tie: `{summary['changed_from_prod_015_tie_count']}`",
        f"- Specificity blind spot confirmed: `{summary['specificity_blind_spot_confirmed']}`",
        f"- Absolute quality gap count: `{summary['absolute_quality_gap_count']}`",
        f"- Generic old-answer rate: `{summary['generic_old_answer_rate']}`",
        f"- Generic retrieval-answer rate: `{summary['generic_retrieval_answer_rate']}`",
        f"- Decision: `{payload['decision']}`",
        f"- Decision meaning: use specificity scoring before composer hook test",
        "",
        "## Scoring Schema",
        "",
    ]
    for key, value in payload["scoring_schema"]["components"].items():
        lines.append(f"- `{key}`: {value}")
    lines.extend(
        [
            "",
            "## Label Summary",
            "",
            "| Label | Turns | Old Score | Retrieval Score | Retrieval Wins | Old Wins | Ties | Quality Gaps |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for item in payload["label_summary"]:
        lines.append(
            "| {label} | {turns} | {old} | {retrieval} | {rwins} | {owins} | {ties} | {gaps} |".format(
                label=item["scenario_label"],
                turns=item["turn_count"],
                old=item["old_total_score"],
                retrieval=item["retrieval_total_score"],
                rwins=item["retrieval_wins"],
                owins=item["old_wins"],
                ties=item["ties"],
                gaps=item["absolute_quality_gap_count"],
            )
        )
    lines.extend(["", "## Changed Winner Examples", ""])
    changed = [row for row in payload["turn_scores"] if row["changed_from_prod_015_tie"]]
    for row in changed[:12]:
        lines.extend(
            [
                f"### {row['turn_id']}",
                "",
                f"- Label: `{row['scenario_label']}`",
                f"- Domain: `{row['domain']}`",
                f"- PROD-015 winner: `{row['prod_015_winner']}`",
                f"- PROD-017 winner: `{row['winner']}`",
                f"- Old total: `{row['old_score']['total']}`",
                f"- Retrieval total: `{row['retrieval_score']['total']}`",
                f"- Old specificity/objection fit: `{row['old_score']['customer_specificity']}` / `{row['old_score']['objection_fit']}`",
                f"- Retrieval specificity/objection fit: `{row['retrieval_score']['customer_specificity']}` / `{row['retrieval_score']['objection_fit']}`",
                "",
                "Customer question:",
                "",
                "```text",
                str(row["customer_question"]),
                "```",
                "",
                "Old runtime answer:",
                "",
                "```text",
                str(row["old_runtime_answer"]),
                "```",
                "",
                "Retrieval runtime answer:",
                "",
                "```text",
                str(row["retrieval_runtime_answer"]),
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
            "PROD-017 changes evaluation scoring only. It makes no provider calls, performs no downloads, changes no runtime behavior, and does not enable retrieval by default.",
        ]
    )
    return "\n".join(lines) + "\n"
