#!/usr/bin/env python3
"""Classify remaining universal response progression defects after broad-menu suppression."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ID = "LIVE-INSPIRED-ADVERSARIAL-DIALOGUE-MATRIX-001"
PREVIOUS_AUDIT_ID = "BROAD-MENU-SUPPRESSION-AUDIT-001"
CHECKPOINT_ID = "UNIVERSAL-RESPONSE-PROGRESSION-AUDIT-001"
SOURCE_DIR = ROOT / "research" / "experiments" / "generated" / SOURCE_ID
PREVIOUS_AUDIT_DIR = ROOT / "research" / "experiments" / "generated" / PREVIOUS_AUDIT_ID
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def norm(value: Any) -> str:
    return " ".join(str(value or "").lower().replace("'", " ").split())


def final_response(scenario: dict[str, Any]) -> str:
    turns = scenario.get("turns") or []
    return str((turns[-1] if turns and isinstance(turns[-1], dict) else {}).get("final_response") or "")


def selected_source(scenario: dict[str, Any]) -> str:
    return str(scenario.get("selected_action_source") or "")


def buyer_script(scenario: dict[str, Any]) -> list[str]:
    return [str(item) for item in scenario.get("buyer_script") or []]


def buyer_script_text(scenario: dict[str, Any]) -> str:
    return norm(" ".join(buyer_script(scenario)))


def last_buyer(scenario: dict[str, Any]) -> str:
    script = buyer_script(scenario)
    return norm(script[-1] if script else "")


def acceptable_scope_boundary(response_norm: str, family: str) -> bool:
    return (
        family == "scope_boundary_regulated_detail_stress"
        and ("cannot" in response_norm or "can t" in response_norm or "can't" in response_norm)
        and ("coverage" in response_norm or "specialist" in response_norm or "scope" in response_norm)
    )


def classify(scenario: dict[str, Any]) -> str:
    flags = set(str(flag) for flag in scenario.get("mechanical_failure_flags") or [])
    family = str(scenario.get("scenario_family") or "")
    response = norm(final_response(scenario))
    script = buyer_script_text(scenario)
    last = last_buyer(scenario)
    source = selected_source(scenario)

    if source == "terminal_call_control":
        return "terminal_preservation_artifact"
    if "too_long_for_live_voice" in flags and "said inbound demo follow-up, not callbacks" in script:
        return "repeated_direct_answer_without_progress"
    if "campaign_contamination" in flags:
        return "campaign_contamination_true"
    if "appointment_too_early" in flags:
        return "early_callback_before_purpose_or_pain"
    if "hostile_response_not_deescalated" in flags:
        if any(token in last for token in ["wrong", "make sense", "assumption"]):
            return "hostile_challenge_needs_specific_clarification"
        return "generic_reset_instead_of_deescalation"
    if "out_of_scope_reset_after_relevant_context" in flags:
        if acceptable_scope_boundary(response, family):
            return "acceptable_scope_boundary_false_positive"
        return "out_of_campaign_mismatch_needs_clean_boundary"
    if "repeated_response" in flags:
        if "that would be useful" in script or "okay what now" in script:
            return "repeated_pain_question_after_confirmed_pain"
        return "repeated_direct_answer_without_progress"
    if "repeated_full_menu" in flags:
        return "generic_reset_instead_of_deescalation"
    if acceptable_scope_boundary(response, family):
        return "acceptable_scope_boundary_false_positive"
    return "needs_human_review"


def example(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "scenario_id": row.get("scenario_id"),
        "classification": row.get("classification"),
        "campaign_id": row.get("campaign_id"),
        "scenario_family": row.get("scenario_family"),
        "selected_action_source": row.get("selected_action_source"),
        "mechanical_failure_flags": row.get("mechanical_failure_flags") or [],
        "buyer_script": buyer_script(row),
        "final_response": final_response(row),
    }


def top_examples(rows: list[dict[str, Any]], limit_per_class: int = 4) -> list[dict[str, Any]]:
    counts: Counter[str] = Counter()
    selected: list[dict[str, Any]] = []
    for row in rows:
        classification = str(row.get("classification") or "")
        if counts[classification] >= limit_per_class:
            continue
        selected.append(example(row))
        counts[classification] += 1
    return selected


def recommended_patch_scope(class_counts: Counter[str]) -> list[str]:
    recommendations: list[str] = []
    if class_counts["repeated_pain_question_after_confirmed_pain"]:
        recommendations.append(
            "Progress after confirmed pain: treat useful/what-now moves as impact or callback progression, not a fresh pain diagnostic."
        )
    if class_counts["repeated_direct_answer_without_progress"]:
        recommendations.append(
            "Vary repeated direct answers and advance to one relevance, correction, or stop choice without reopening a menu."
        )
    if class_counts["hostile_challenge_needs_specific_clarification"] or class_counts["generic_reset_instead_of_deescalation"]:
        recommendations.append(
            "Replace challenge resets with acknowledge-plus-specific-correction questions; do not pitch review usefulness."
        )
    if class_counts["early_callback_before_purpose_or_pain"]:
        recommendations.append(
            "Demote early callback times to callback preference capture plus one relevance check until pain and impact exist."
        )
    if class_counts["out_of_campaign_mismatch_needs_clean_boundary"] or class_counts["campaign_contamination_true"]:
        recommendations.append(
            "Acknowledge out-of-campaign pain as a mismatch, state current campaign scope, and offer to stop."
        )
    return recommendations


def generate() -> dict[str, Any]:
    matrix_result = read_json(SOURCE_DIR / "result.json")
    previous_audit = read_json(PREVIOUS_AUDIT_DIR / "result.json")
    packet = read_jsonl(SOURCE_DIR / "review_packet.jsonl")
    red_rows: list[dict[str, Any]] = []
    for row in packet:
        if row.get("tier") != "exploratory_red_findings" or not row.get("mechanical_failure_flags"):
            continue
        item = dict(row)
        item["classification"] = classify(item)
        red_rows.append(item)

    class_counts = Counter(str(row["classification"]) for row in red_rows)
    by_source = Counter(selected_source(row) for row in red_rows)
    by_campaign = Counter(str(row.get("campaign_id") or "") for row in red_rows)
    by_family = Counter(str(row.get("scenario_family") or "") for row in red_rows)
    class_by_source: dict[str, dict[str, int]] = defaultdict(dict)
    for classification in sorted(class_counts):
        class_by_source[classification] = dict(
            sorted(Counter(selected_source(row) for row in red_rows if row["classification"] == classification).items())
        )
    class_by_campaign: dict[str, dict[str, int]] = defaultdict(dict)
    for classification in sorted(class_counts):
        class_by_campaign[classification] = dict(
            sorted(Counter(str(row.get("campaign_id") or "") for row in red_rows if row["classification"] == classification).items())
        )

    return {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_ID,
        "previous_audit_checkpoint_id": PREVIOUS_AUDIT_ID,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_status": matrix_result.get("status"),
        "source_red_finding_count": int(matrix_result.get("red_finding_count") or 0),
        "previous_audit_classification_counts": previous_audit.get("classification_counts") or {},
        "audited_red_finding_count": len(red_rows),
        "classification_counts": dict(sorted(class_counts.items())),
        "counts_by_source": dict(sorted(by_source.items())),
        "counts_by_campaign": dict(sorted(by_campaign.items())),
        "counts_by_scenario_family": dict(sorted(by_family.items())),
        "classification_counts_by_source": dict(sorted(class_by_source.items())),
        "classification_counts_by_campaign": dict(sorted(class_by_campaign.items())),
        "top_examples": top_examples(red_rows),
        "recommended_patch_scope": recommended_patch_scope(class_counts),
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
        "",
        "## Classification Counts",
        *(f"- `{key}`: `{value}`" for key, value in result["classification_counts"].items()),
        "",
        "## Counts By Source",
        *(f"- `{key}`: `{value}`" for key, value in result["counts_by_source"].items()),
        "",
        "## Counts By Campaign",
        *(f"- `{key}`: `{value}`" for key, value in result["counts_by_campaign"].items()),
        "",
        "## Recommended Patch Scope",
        *(f"- {item}" for item in result["recommended_patch_scope"]),
        "",
        "## Top Examples",
    ]
    for item in result["top_examples"]:
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
    (OUT_DIR / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    result = generate()
    write_outputs(result)
    print(
        json.dumps(
            {
                "checkpoint_id": CHECKPOINT_ID,
                "audited_red_finding_count": result["audited_red_finding_count"],
                "classification_counts": result["classification_counts"],
                "counts_by_source": result["counts_by_source"],
                "counts_by_campaign": result["counts_by_campaign"],
                "recommended_patch_scope": result["recommended_patch_scope"],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
