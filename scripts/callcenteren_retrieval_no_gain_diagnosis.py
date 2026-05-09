#!/usr/bin/env python3
from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PROD_016_ID = "PROD-016-callcenteren-retrieval-no-gain-diagnosis"
PROD_015_ID = "PROD-015-callcenteren-runtime-comparison"
DEFAULT_PROD_015_RESULT = ROOT / "research" / "experiments" / "generated" / "PROD-015-callcenteren-runtime-comparison" / "result.json"
DEFAULT_OUT_DIR = ROOT / "research" / "experiments" / "generated" / "PROD-016-callcenteren-retrieval-no-gain-diagnosis"
DEFAULT_RESULT = DEFAULT_OUT_DIR / "result.json"
DEFAULT_REPORT = DEFAULT_OUT_DIR / "report.md"

NO_MATCH_PRIMARY_THRESHOLD = 0.25
COMPOSER_GAP_THRESHOLD = 0.5
CLASSIFIER_MISMATCH_THRESHOLD = 0.5


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


def nested_get(payload: dict[str, Any], path: list[str], default: Any = "") -> Any:
    current: Any = payload
    for key in path:
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    return current


def answer_changed(row: dict[str, Any]) -> bool:
    return str(row.get("old_runtime_answer", "")).strip() != str(row.get("retrieval_runtime_answer", "")).strip()


def is_rubric_like_question(question: str) -> bool:
    lowered = question.lower()
    return (
        lowered.startswith("customer ")
        or "customer raises `" in lowered
        or "customer asks " in lowered
        or "`" in question
    )


def row_sales_difficulty(row: dict[str, Any], branch: str = "retrieval_runtime") -> str:
    return str(nested_get(row, ["decision_trace", branch, "sales_difficulty"], ""))


def row_next_action(row: dict[str, Any], branch: str = "retrieval_runtime") -> str:
    return str(nested_get(row, ["decision_trace", branch, "next_action"], ""))


def row_retrieved_item_ids(row: dict[str, Any]) -> list[str]:
    ids = row.get("retrieved_item_ids")
    if isinstance(ids, list):
        return [str(item_id) for item_id in ids if str(item_id).strip()]
    ids = nested_get(row, ["decision_trace", "retrieval_runtime", "retrieved_item_ids"], [])
    if isinstance(ids, list):
        return [str(item_id) for item_id in ids if str(item_id).strip()]
    return []


def build_status_by_label(rows: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    grouped: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        grouped[str(row.get("scenario_label", "unknown"))][str(row.get("retrieval_status", "unknown"))] += 1
    return {label: dict(counter) for label, counter in sorted(grouped.items())}


def top_counts(counter: Counter[str], limit: int = 10) -> list[dict[str, Any]]:
    return [{"value": value, "count": count} for value, count in counter.most_common(limit)]


def build_summary(source: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, Any]:
    source_summary = source.get("summary", {})
    turn_count = len(rows)
    status_counts = Counter(str(row.get("retrieval_status", "unknown")) for row in rows)
    winner_counts = Counter(str(row.get("winner", "unknown")) for row in rows)
    difficulty_counts = Counter(row_sales_difficulty(row) or "unknown" for row in rows)
    next_action_counts = Counter(row_next_action(row) or "unknown" for row in rows)
    item_counts: Counter[str] = Counter()
    for row in rows:
        item_counts.update(row_retrieved_item_ids(row))

    changed_count = sum(1 for row in rows if answer_changed(row))
    unchanged_count = turn_count - changed_count
    influenced_count = sum(1 for row in rows if row.get("retrieval_used_in_runtime") is True)
    influenced_but_tied_count = sum(
        1
        for row in rows
        if row.get("retrieval_used_in_runtime") is True and row.get("winner") == "tie"
    )
    changed_but_tied_count = sum(1 for row in rows if answer_changed(row) and row.get("winner") == "tie")
    no_match_count = status_counts.get("no_match", 0)
    blocked_count = status_counts.get("blocked", 0)
    retrieved_like_count = status_counts.get("retrieved_not_used", 0) + status_counts.get("influenced", 0)
    retrievable_turn_count = max(turn_count - blocked_count, 1)
    matching_success_rate = rate(retrieved_like_count, retrievable_turn_count)
    no_match_rate = rate(no_match_count, retrievable_turn_count)
    retrieved_not_used_rate = rate(status_counts.get("retrieved_not_used", 0), turn_count)
    unchanged_answer_rate = rate(unchanged_count, turn_count)
    unknown_runtime_signal_count = difficulty_counts.get("unknown-runtime-signal", 0)
    unknown_runtime_signal_rate = rate(unknown_runtime_signal_count, turn_count)
    rubric_like_turn_count = sum(1 for row in rows if is_rubric_like_question(str(row.get("customer_question", ""))))
    rubric_like_turn_rate = rate(rubric_like_turn_count, turn_count)
    labels = sorted({str(row.get("scenario_label", "unknown")) for row in rows})
    domains = sorted({str(row.get("domain", "")) for row in rows if str(row.get("domain", "")).strip()})
    old_answer_counts = Counter(str(row.get("old_runtime_answer", "")).strip() for row in rows)
    dominant_old_answer_share = rate(old_answer_counts.most_common(1)[0][1], turn_count) if old_answer_counts else 0.0
    old_score = int(source_summary.get("old_runtime_total_score", sum(int(row.get("old_runtime_score", 0)) for row in rows)))
    retrieval_score = int(source_summary.get("retrieval_runtime_total_score", sum(int(row.get("retrieval_runtime_score", 0)) for row in rows)))
    retrieval_wins = int(source_summary.get("retrieval_turn_wins", winner_counts.get("retrieval", 0)))
    old_wins = int(source_summary.get("old_runtime_turn_wins", winner_counts.get("old_runtime", 0)))
    score_delta = retrieval_score - old_score
    no_gain_confirmed = retrieval_score <= old_score and retrieval_wins == 0
    matching_not_primary = no_match_rate <= NO_MATCH_PRIMARY_THRESHOLD and matching_success_rate >= 0.5
    composer_influence_gap = retrieved_not_used_rate >= COMPOSER_GAP_THRESHOLD or unchanged_answer_rate >= COMPOSER_GAP_THRESHOLD
    scoring_blind_spot_risk = influenced_but_tied_count > 0 or changed_but_tied_count > 0
    runtime_classifier_mismatch = unknown_runtime_signal_rate >= CLASSIFIER_MISMATCH_THRESHOLD or rubric_like_turn_rate >= CLASSIFIER_MISMATCH_THRESHOLD
    campaign_id = str(nested_get(source, ["runtime_comparison", "campaign_id"], ""))
    campaign_domain_mismatch = len(domains) > 1 and bool(campaign_id)

    return {
        "source_turn_count": int(source_summary.get("evaluated_turn_count", turn_count)),
        "analyzed_turn_count": turn_count,
        "covered_scenario_labels": labels,
        "covered_domain_count": len(domains),
        "campaign_id": campaign_id,
        "hard_failure_count": int(source_summary.get("hard_failure_count", 0)),
        "leakage_finding_count": int(source_summary.get("leakage_finding_count", 0)),
        "old_runtime_total_score": old_score,
        "retrieval_runtime_total_score": retrieval_score,
        "score_delta": score_delta,
        "retrieval_turn_wins": retrieval_wins,
        "old_runtime_turn_wins": old_wins,
        "tie_turns": int(source_summary.get("tie_turns", winner_counts.get("tie", 0))),
        "no_gain_confirmed": no_gain_confirmed,
        "retrieval_status_counts": dict(sorted(status_counts.items())),
        "winner_counts": dict(sorted(winner_counts.items())),
        "answer_changed_count": changed_count,
        "unchanged_answer_count": unchanged_count,
        "unchanged_answer_rate": unchanged_answer_rate,
        "influenced_count": influenced_count,
        "influenced_but_tied_count": influenced_but_tied_count,
        "changed_but_tied_count": changed_but_tied_count,
        "retrieved_not_used_rate": retrieved_not_used_rate,
        "matching_success_rate": matching_success_rate,
        "no_match_rate": no_match_rate,
        "matching_not_primary": matching_not_primary,
        "composer_influence_gap": composer_influence_gap,
        "scoring_blind_spot_risk": scoring_blind_spot_risk,
        "unknown_runtime_signal_count": unknown_runtime_signal_count,
        "unknown_runtime_signal_rate": unknown_runtime_signal_rate,
        "rubric_like_turn_count": rubric_like_turn_count,
        "rubric_like_turn_rate": rubric_like_turn_rate,
        "runtime_classifier_mismatch": runtime_classifier_mismatch,
        "campaign_domain_mismatch": campaign_domain_mismatch,
        "dominant_old_answer_share": dominant_old_answer_share,
        "provider_calls_made": False,
        "llm_used": False,
        "runtime_behavior_changed": False,
        "runtime_retrieval_default_enabled": False,
        "commercial_runtime_prompt_text_from_callcenteren_allowed": False,
        "top_retrieved_item_ids": top_counts(item_counts, limit=12),
        "top_sales_difficulties": top_counts(difficulty_counts, limit=10),
        "top_next_actions": top_counts(next_action_counts, limit=10),
        "status_by_label": build_status_by_label(rows),
    }


def build_failure_classes(summary: dict[str, Any]) -> list[dict[str, Any]]:
    classes: list[dict[str, Any]] = []
    if summary["composer_influence_gap"]:
        classes.append(
            {
                "class_id": "composer_influence_gap",
                "label": "Composer influence gap",
                "severity": "high",
                "evidence": (
                    f"{summary['retrieval_status_counts'].get('retrieved_not_used', 0)} turns were retrieved-not-used and "
                    f"{summary['unchanged_answer_count']} answers were unchanged."
                ),
                "interpretation": "Retrieval matching exists, but retrieved hints rarely change the deterministic response composer.",
            }
        )
    if summary["scoring_blind_spot_risk"]:
        classes.append(
            {
                "class_id": "scoring_blind_spot",
                "label": "Scoring blind spot",
                "severity": "high",
                "evidence": (
                    f"{summary['influenced_but_tied_count']} influenced turns and "
                    f"{summary['changed_but_tied_count']} changed-answer turns still tied."
                ),
                "interpretation": "The current score rewards safe generic follow-up behavior but does not measure answer specificity or objection-fit enough.",
            }
        )
    if summary["runtime_classifier_mismatch"]:
        classes.append(
            {
                "class_id": "runtime_classifier_mismatch",
                "label": "Runtime classifier mismatch",
                "severity": "medium",
                "evidence": (
                    f"{summary['unknown_runtime_signal_count']} turns were classified as unknown-runtime-signal and "
                    f"{summary['rubric_like_turn_count']} customer prompts looked rubric-like."
                ),
                "interpretation": "Generated test prompts may carry labels that the runtime classifier does not naturally parse from customer wording.",
            }
        )
    if summary["campaign_domain_mismatch"]:
        classes.append(
            {
                "class_id": "campaign_domain_mismatch",
                "label": "Campaign domain mismatch",
                "severity": "medium",
                "evidence": (
                    f"{summary['covered_domain_count']} scenario domains were evaluated through one campaign id "
                    f"`{summary['campaign_id']}`."
                ),
                "interpretation": "A single B2B software campaign can flatten domain-specific objections and make old/retrieval answers converge.",
            }
        )
    if not summary["matching_not_primary"]:
        classes.append(
            {
                "class_id": "retrieval_matching_gap",
                "label": "Retrieval matching gap",
                "severity": "medium",
                "evidence": f"No-match rate was {summary['no_match_rate']}.",
                "interpretation": "Retrieval matching itself may be too weak before composition is considered.",
            }
        )
    return classes


def build_recommendations(summary: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "recommendation_id": "add_specificity_scoring_before_claiming_gain",
            "priority": "P0",
            "target": "evaluation",
            "action": "Add specificity and objection-fit sub-scores before claiming retrieval is better.",
            "why": "A generic old answer can currently tie a more targeted retrieval answer if both are safe and ask a question.",
            "runtime_change": False,
        },
        {
            "recommendation_id": "add_composer_hooks_for_generated_objection_labels",
            "priority": "P0",
            "target": "retrieval composer",
            "action": "Add or test explicit composer hooks for generated objection labels such as needs_spouse_or_manager, callback_request, trust_repair, and price_objection.",
            "why": f"Retrieved-but-not-used rate is {summary['retrieved_not_used_rate']}, so matching is not enough.",
            "runtime_change": False,
        },
        {
            "recommendation_id": "verbalize_rubric_like_scenario_turns",
            "priority": "P1",
            "target": "scenario bank",
            "action": "Convert rubric-like customer turns into natural customer utterances before using them as runtime classifier evidence.",
            "why": f"Rubric-like turn rate is {summary['rubric_like_turn_rate']}, which can hide real classifier behavior.",
            "runtime_change": False,
        },
        {
            "recommendation_id": "route_scenarios_to_domain_campaigns",
            "priority": "P1",
            "target": "evaluation routing",
            "action": "Route multi-domain scenario slices to matching SalesCampaign profiles or mark the single-campaign result as baseline-only.",
            "why": f"{summary['covered_domain_count']} domains were evaluated through `{summary['campaign_id']}`.",
            "runtime_change": False,
        },
        {
            "recommendation_id": "run_full_bank_only_after_diagnostic_scoring",
            "priority": "P2",
            "target": "experiment sequencing",
            "action": "Run the full 240-scenario bank only after the scorer can distinguish safe-generic from safe-specific answers.",
            "why": "A bigger run with the same blind spot would mostly confirm that both versions are safe, not which one is better.",
            "runtime_change": False,
        },
    ]


def select_examples(rows: list[dict[str, Any]], limit: int = 8) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    priority_statuses = ["influenced", "retrieved_not_used", "blocked", "no_match"]
    seen_turns: set[str] = set()
    for status in priority_statuses:
        for row in rows:
            turn_id = str(row.get("turn_id", ""))
            if turn_id in seen_turns or row.get("retrieval_status") != status:
                continue
            selected.append(
                {
                    "turn_id": turn_id,
                    "scenario_label": row.get("scenario_label", ""),
                    "domain": row.get("domain", ""),
                    "retrieval_status": row.get("retrieval_status", ""),
                    "winner": row.get("winner", ""),
                    "sales_difficulty": row_sales_difficulty(row),
                    "customer_question": row.get("customer_question", ""),
                    "old_runtime_answer": row.get("old_runtime_answer", ""),
                    "retrieval_runtime_answer": row.get("retrieval_runtime_answer", ""),
                    "retrieved_item_ids": row_retrieved_item_ids(row),
                }
            )
            seen_turns.add(turn_id)
            if len(selected) >= limit:
                return selected
    return selected


def build_payload(prod_015_result_path: Path) -> dict[str, Any]:
    source = load_json(prod_015_result_path)
    rows = list(source.get("turn_results", []))
    summary = build_summary(source, rows)
    failure_classes = build_failure_classes(summary)
    recommendations = build_recommendations(summary)
    decision = "diagnose_before_retrieval_runtime_promotion"
    if summary["hard_failure_count"] or summary["leakage_finding_count"]:
        decision = "fix_safety_or_leakage_before_no_gain_diagnosis"
    elif not summary["no_gain_confirmed"]:
        decision = "no_no_gain_diagnosis_needed_review_positive_result"
    return {
        "prod_016_id": PROD_016_ID,
        "title": "PROD-016 CallCenterEN retrieval no-gain diagnosis",
        "source_prod_015_result": {
            "prod_015_id": source.get("prod_015_id", ""),
            "path": rel_path(prod_015_result_path),
            "decision": source.get("decision", ""),
            "turn_count": len(rows),
            "old_runtime_total_score": summary["old_runtime_total_score"],
            "retrieval_runtime_total_score": summary["retrieval_runtime_total_score"],
        },
        "hypothesis": {
            "statement": "PROD-015 tied because retrieval matched but did not influence the deterministic composer often enough, and the current scorer does not reward safe answer specificity.",
            "fixed_cases": "Use the already generated PROD-015 turn results without changing prompts, retrieval registry, runtime composer, or scoring inputs.",
            "editable_surface_changed": "none",
        },
        "summary": summary,
        "failure_classes": failure_classes,
        "recommendations": recommendations,
        "examples": select_examples(rows),
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
        "# PROD-016 CallCenterEN Retrieval No-Gain Diagnosis",
        "",
        "This checkpoint diagnoses why PROD-015 tied instead of promoting retrieval or changing runtime behavior.",
        "",
        "## Summary",
        "",
        f"- Source PROD-015 decision: `{payload['source_prod_015_result']['decision']}`",
        f"- Analyzed turns: `{summary['analyzed_turn_count']}`",
        f"- Old runtime score: `{summary['old_runtime_total_score']}`",
        f"- Retrieval runtime score: `{summary['retrieval_runtime_total_score']}`",
        f"- Score delta: `{summary['score_delta']}`",
        f"- No-gain confirmed: `{summary['no_gain_confirmed']}`",
        f"- Answer changed count: `{summary['answer_changed_count']}`",
        f"- Unchanged answer count: `{summary['unchanged_answer_count']}`",
        f"- Influenced but tied count: `{summary['influenced_but_tied_count']}`",
        f"- Retrieved-not-used rate: `{summary['retrieved_not_used_rate']}`",
        f"- Matching success rate: `{summary['matching_success_rate']}`",
        f"- No-match rate: `{summary['no_match_rate']}`",
        f"- Unknown-runtime-signal rate: `{summary['unknown_runtime_signal_rate']}`",
        f"- Rubric-like turn rate: `{summary['rubric_like_turn_rate']}`",
        f"- Dominant old-answer share: `{summary['dominant_old_answer_share']}`",
        f"- Decision: `{payload['decision']}`",
        f"- Decision meaning: diagnose before retrieval runtime promotion",
        "",
        "## Failure Classes",
        "",
    ]
    for item in payload["failure_classes"]:
        lines.extend(
            [
                f"### {item['label']}",
                "",
                f"- Class: `{item['class_id']}`",
                f"- Severity: `{item['severity']}`",
                f"- Evidence: {item['evidence']}",
                f"- Interpretation: {item['interpretation']}",
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
                f"- Target: `{item['target']}`",
                f"- Action: {item['action']}",
                f"- Why: {item['why']}",
                f"- Runtime change in this checkpoint: `{item['runtime_change']}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Retrieval Status By Label",
            "",
            "| Label | Status Counts |",
            "| --- | --- |",
        ]
    )
    for label, counts in summary["status_by_label"].items():
        compact = ", ".join(f"{key}: {value}" for key, value in sorted(counts.items()))
        lines.append(f"| {label} | {compact} |")
    lines.extend(["", "## Examples", ""])
    for item in payload["examples"]:
        lines.extend(
            [
                f"### {item['turn_id']}",
                "",
                f"- Label: `{item['scenario_label']}`",
                f"- Domain: `{item['domain']}`",
                f"- Retrieval status: `{item['retrieval_status']}`",
                f"- Winner: `{item['winner']}`",
                f"- Runtime difficulty: `{item['sales_difficulty']}`",
                f"- Retrieved item IDs: `{', '.join(item['retrieved_item_ids']) or 'none'}`",
                "",
                "Customer question:",
                "",
                "```text",
                str(item["customer_question"]),
                "```",
                "",
                "Old runtime answer:",
                "",
                "```text",
                str(item["old_runtime_answer"]),
                "```",
                "",
                "Retrieval runtime answer:",
                "",
                "```text",
                str(item["retrieval_runtime_answer"]),
                "```",
                "",
            ]
        )
    lines.extend(
        [
            "## Boundary",
            "",
            "PROD-016 is diagnosis only. It makes no provider calls, performs no downloads, changes no runtime behavior, and does not enable retrieval by default.",
        ]
    )
    return "\n".join(lines) + "\n"
