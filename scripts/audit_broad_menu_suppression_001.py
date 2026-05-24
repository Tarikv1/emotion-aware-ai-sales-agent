#!/usr/bin/env python3
"""Classify broad menu and adversarial red findings before suppression patches."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ID = "LIVE-INSPIRED-ADVERSARIAL-DIALOGUE-MATRIX-001"
CHECKPOINT_ID = "BROAD-MENU-SUPPRESSION-AUDIT-001"
SOURCE_DIR = ROOT / "research" / "experiments" / "generated" / SOURCE_ID
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def norm(value: Any) -> str:
    return " ".join(str(value or "").lower().replace("'", " ").split())


def final_response(scenario: dict[str, Any]) -> str:
    turns = scenario.get("turns") or []
    if not turns:
        return ""
    return str((turns[-1] if isinstance(turns[-1], dict) else {}).get("final_response") or "")


def selected_source(scenario: dict[str, Any]) -> str:
    return str(scenario.get("selected_action_source") or "")


def last_buyer(scenario: dict[str, Any]) -> str:
    script = scenario.get("buyer_script") or []
    return norm(script[-1] if script else "")


def buyer_script_text(scenario: dict[str, Any]) -> str:
    return norm(" ".join(str(item) for item in scenario.get("buyer_script") or []))


def direct_value_answer(response_norm: str) -> bool:
    return (
        ("only if" in response_norm or "worth" in response_norm or "useful" in response_norm)
        and any(token in response_norm for token in ["costing time", "delays", "quality", "review", "relevant"])
    )


def gap_clarity_question(response_norm: str) -> bool:
    return any(token in response_norm for token in ["what part", "which part", "what it means", "do you mean"]) and not any(
        token in response_norm
        for token in [
            "which part should i check first",
            "which part is least clear",
            "premium or budget, coverage fit",
            "manual work, integration",
            "vehicle issue, repair timing",
        ]
    )


def acceptable_scope_boundary(response_norm: str) -> bool:
    return any(token in response_norm for token in ["cannot", "can't", "can not", "outside this call"]) and any(
        token in response_norm for token in ["review", "scope", "human", "specialist"]
    )


def root_cause_classification(scenario: dict[str, Any], classification: str) -> str:
    flags = set(str(flag) for flag in scenario.get("mechanical_failure_flags") or [])
    source = selected_source(scenario)
    if source == "pre_speech_conversation_stability_guard" and "repeated_full_menu" in flags:
        return "true_stability_menu_reset"
    return classification


def classify(scenario: dict[str, Any]) -> str:
    flags = set(str(flag) for flag in scenario.get("mechanical_failure_flags") or [])
    family = str(scenario.get("scenario_family") or "")
    source = selected_source(scenario)
    response = norm(final_response(scenario))
    script = buyer_script_text(scenario)
    last = last_buyer(scenario)

    if source == "terminal_call_control":
        return "terminal_preservation_artifact"
    if "campaign_contamination" in flags:
        return "true_campaign_contamination"
    if "explicit_stop_not_respected" in flags:
        return "needs_human_review"
    if "out_of_scope_reset_after_relevant_context" in flags:
        if acceptable_scope_boundary(response) and family in {"scope_boundary_regulated_detail_stress", "why_human_review_challenge"}:
            return "acceptable_scope_boundary"
        return "true_out_of_scope_reset_after_relevant_context"
    if "appointment_too_early" in flags:
        return "true_appointment_too_early"
    if "hostile_response_not_deescalated" in flags:
        return "true_hostile_challenge_not_deescalated"
    if "asr_near_miss_not_clarified" in flags:
        if "what should i care" in last and direct_value_answer(response):
            return "acceptable_direct_value_answer_false_positive"
        if "why should i care" in last and direct_value_answer(response):
            return "acceptable_direct_value_answer_false_positive"
        if gap_clarity_question(response):
            return "acceptable_gap_clarity_question_false_positive"
        return "needs_human_review"
    if "repeated_response" in flags:
        if "stop" in response and "goodbye" in response:
            return "terminal_preservation_artifact"
        if family in {"repeated_product_detail_scope_questions", "direct_product_value_challenge_loops"}:
            return "true_repeated_product_scope_loop"
        return "true_repeated_response_without_progress"
    if "repeated_full_menu" in flags:
        if family == "permission_weak_acknowledgement_variants" or any(
            phrase in script for phrase in ["okay fine", "go ahead", "fine but be fast", "maybe quickly", "maybe, quickly"]
        ):
            return "true_permission_menu_reset"
        if family in {"false_assumption_correction", "buyer_correction_contradiction_stress"}:
            return "true_correction_menu_reset"
        if family in {"hostile_challenging_buyer", "buyer_says_agent_is_wrong", "repeated_challenge_escalation"}:
            return "true_challenge_menu_reset"
        if family in {"repeated_product_detail_scope_questions", "direct_product_value_challenge_loops", "agent_looping_complaints"}:
            return "true_repeated_product_scope_loop"
        if gap_clarity_question(response):
            return "acceptable_gap_clarity_question_false_positive"
        return "exploratory_expectation_too_strict"
    if "false_assumption_not_repaired" in flags or "repeated_false_assumption" in flags:
        return "true_correction_menu_reset"
    if family in {"callback_time_too_early_or_ambiguous", "early_callback_premature_scheduling"}:
        return "exploratory_expectation_too_strict"
    if acceptable_scope_boundary(response):
        return "acceptable_scope_boundary"
    return "needs_human_review"


def examples(rows: list[dict[str, Any]], prefix: str, limit: int) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    for row in rows:
        classification = str(row.get("classification") or "")
        if not classification.startswith(prefix):
            continue
        found.append(
            {
                "scenario_id": row.get("scenario_id"),
                "classification": classification,
                "root_cause_classification": row.get("root_cause_classification"),
                "campaign_id": row.get("campaign_id"),
                "scenario_family": row.get("scenario_family"),
                "selected_action_source": row.get("selected_action_source"),
                "mechanical_failure_flags": row.get("mechanical_failure_flags") or [],
                "buyer_script": row.get("buyer_script") or [],
                "final_response": final_response(row),
            }
        )
        if len(found) >= limit:
            break
    return found


def generate() -> dict[str, Any]:
    source_result = read_json(SOURCE_DIR / "result.json")
    packet = read_jsonl(SOURCE_DIR / "review_packet.jsonl")
    red_rows: list[dict[str, Any]] = []
    for row in packet:
        if row.get("tier") != "exploratory_red_findings" or not row.get("mechanical_failure_flags"):
            continue
        item = dict(row)
        classification = classify(item)
        item["classification"] = classification
        item["root_cause_classification"] = root_cause_classification(item, classification)
        red_rows.append(item)

    by_class = Counter(str(row["classification"]) for row in red_rows)
    by_root = Counter(str(row["root_cause_classification"]) for row in red_rows)
    by_source = Counter(selected_source(row) for row in red_rows)
    by_family = Counter(str(row.get("scenario_family") or "") for row in red_rows)
    by_campaign = Counter(str(row.get("campaign_id") or "") for row in red_rows)
    class_by_source: dict[str, dict[str, int]] = defaultdict(dict)
    for classification in sorted(by_class):
        class_by_source[classification] = dict(
            sorted(Counter(selected_source(row) for row in red_rows if row["classification"] == classification).items())
        )

    true_total = sum(count for key, count in by_class.items() if key.startswith("true_"))
    false_total = sum(
        count
        for key, count in by_class.items()
        if key.startswith("acceptable_") or key in {"terminal_preservation_artifact", "exploratory_expectation_too_strict"}
    )
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_ID,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_status": source_result.get("status"),
        "source_red_finding_count": int(source_result.get("red_finding_count") or 0),
        "audited_red_finding_count": len(red_rows),
        "true_defect_count": true_total,
        "false_positive_or_expectation_count": false_total,
        "classification_counts": dict(sorted(by_class.items())),
        "root_cause_counts": dict(sorted(by_root.items())),
        "counts_by_selected_action_source": dict(sorted(by_source.items())),
        "counts_by_scenario_family": dict(sorted(by_family.items())),
        "counts_by_campaign": dict(sorted(by_campaign.items())),
        "classification_counts_by_source": class_by_source,
        "top_true_defects": examples(red_rows, "true_", 30),
        "top_false_positives": [
            *examples(red_rows, "acceptable_", 12),
            *examples(red_rows, "terminal_", 8),
            *examples(red_rows, "exploratory_", 8),
        ][:20],
        "recommended_patch_scope": [
            "Route weak permission and time-constrained permission into one primary diagnostic question before stability guard repair.",
            "Replace correction/challenge reset text with acknowledge-plus-one-neutral-reset, not diagnostic gap menus.",
            "Answer product/scope loop complaints in new wording and avoid fallback menu or wrong-contact escape.",
            "Treat early callback requests as callback preference capture plus one relevance check unless pain/readiness is already established.",
            "Calibrate ASR red-finding heuristic so 'what should I care' direct value answers are not counted as ASR near-miss failures.",
        ],
        "runtime_behavior_changed": False,
        "side_effect_boundary": {
            "provider_calls_made": False,
            "live_tts_calls_made": False,
            "local_llm_calls_made": False,
            "sends_email": False,
            "creates_calendar_event": False,
            "writes_crm": False,
            "opens_prod_102": False,
        },
    }


def write_outputs(result: dict[str, Any]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        f"# {CHECKPOINT_ID}",
        "",
        "## Summary",
        f"- Source checkpoint: `{SOURCE_ID}`",
        f"- Source red findings: `{result['source_red_finding_count']}`",
        f"- Audited red findings: `{result['audited_red_finding_count']}`",
        f"- True defects: `{result['true_defect_count']}`",
        f"- False positives / expectation artifacts: `{result['false_positive_or_expectation_count']}`",
        "",
        "## Classification Counts",
        *(f"- `{key}`: `{value}`" for key, value in result["classification_counts"].items()),
        "",
        "## Root Cause Counts",
        *(f"- `{key}`: `{value}`" for key, value in result["root_cause_counts"].items()),
        "",
        "## Counts By Selected Action Source",
        *(f"- `{key}`: `{value}`" for key, value in result["counts_by_selected_action_source"].items()),
        "",
        "## Counts By Scenario Family",
        *(f"- `{key}`: `{value}`" for key, value in result["counts_by_scenario_family"].items()),
        "",
        "## Counts By Campaign",
        *(f"- `{key}`: `{value}`" for key, value in result["counts_by_campaign"].items()),
        "",
        "## Top True Defects",
    ]
    for item in result["top_true_defects"]:
        lines.extend(
            [
                f"### {item['scenario_id']}",
                f"- Classification: `{item['classification']}`",
                f"- Root cause: `{item['root_cause_classification']}`",
                f"- Campaign: `{item['campaign_id']}`",
                f"- Family: `{item['scenario_family']}`",
                f"- Source: `{item['selected_action_source']}`",
                f"- Flags: `{', '.join(item['mechanical_failure_flags'])}`",
                f"- Buyer script: `{item['buyer_script']}`",
                f"- Final response: {item['final_response']}",
                "",
            ]
        )
    lines.append("## Top False Positives / Artifacts")
    for item in result["top_false_positives"]:
        lines.extend(
            [
                f"### {item['scenario_id']}",
                f"- Classification: `{item['classification']}`",
                f"- Campaign: `{item['campaign_id']}`",
                f"- Family: `{item['scenario_family']}`",
                f"- Source: `{item['selected_action_source']}`",
                f"- Flags: `{', '.join(item['mechanical_failure_flags'])}`",
                f"- Buyer script: `{item['buyer_script']}`",
                f"- Final response: {item['final_response']}",
                "",
            ]
        )
    lines.extend(
        [
            "## Recommended Patch Scope",
            *(f"- {item}" for item in result["recommended_patch_scope"]),
            "",
            "## Runtime Behavior Changed",
            f"- `{str(result['runtime_behavior_changed']).lower()}`",
        ]
    )
    (OUT_DIR / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    result = generate()
    write_outputs(result)
    print(
        json.dumps(
            {
                "checkpoint_id": CHECKPOINT_ID,
                "status": "pass",
                "audited_red_finding_count": result["audited_red_finding_count"],
                "classification_counts": result["classification_counts"],
                "root_cause_counts": result["root_cause_counts"],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
