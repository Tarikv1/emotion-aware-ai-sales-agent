#!/usr/bin/env python3
"""Audit remaining adversarial menu/reset findings after high-confidence priority."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ID = "LIVE-INSPIRED-ADVERSARIAL-DIALOGUE-MATRIX-001"
CHECKPOINT_ID = "ADVERSARIAL-REMAINING-MENU-RESET-AUDIT-001"
SOURCE_DIR = ROOT / "research" / "experiments" / "generated" / SOURCE_ID
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def norm(text: Any) -> str:
    return " ".join(str(text or "").lower().replace("'", " ").split())


def final_response(scenario: dict[str, Any]) -> str:
    turns = scenario.get("turns") or []
    if not turns:
        return ""
    return str((turns[-1] if isinstance(turns[-1], dict) else {}).get("final_response") or "")


def selected_source(scenario: dict[str, Any]) -> str:
    return str(scenario.get("selected_action_source") or "")


def _looks_like_acceptable_clarification(response: str) -> bool:
    text = norm(response)
    return (
        ("what part" in text or "which part" in text or "do you mean" in text)
        and not any(menu in text for menu in ["which part should i check first", "which part is least clear"])
    )


def classify(scenario: dict[str, Any]) -> str:
    flags = set(str(flag) for flag in scenario.get("mechanical_failure_flags") or [])
    source = selected_source(scenario)
    family = str(scenario.get("scenario_family") or "")
    response = final_response(scenario)
    response_norm = norm(response)

    if source == "terminal_call_control":
        return "terminal_preservation_artifact"
    if "internal_wording_leak" in flags:
        return "true_internal_wording_leak"
    if "explicit_stop_not_respected" in flags:
        return "needs_human_review"
    if "false_assumption_not_repaired" in flags or "repeated_false_assumption" in flags:
        return "true_false_assumption_not_repaired"
    if "campaign_contamination" in flags:
        return "true_campaign_contamination"
    if "out_of_scope_reset_after_relevant_context" in flags:
        return "true_out_of_scope_reset_after_relevant_context"
    if "appointment_too_early" in flags:
        return "true_appointment_too_early"
    if "hostile_response_not_deescalated" in flags:
        return "true_hostile_challenge_not_deescalated"
    if "repeated_response" in flags:
        if response_norm in {"understood i will stop here goodbye", "understood ill stop here goodbye"}:
            return "terminal_preservation_artifact"
        return "true_repeated_response_without_progress"
    if "asr_near_miss_not_clarified" in flags:
        if _looks_like_acceptable_clarification(response):
            return "acceptable_asr_clarification_false_positive"
        return "needs_human_review"
    if source == "pre_speech_conversation_stability_guard" and "repeated_full_menu" in flags:
        return "true_stability_menu_reset"
    if "repeated_full_menu" in flags:
        return "true_stability_menu_reset"
    if family in {
        "callback_time_too_early_or_ambiguous",
        "early_callback_premature_scheduling",
        "repeated_answer_variation_anti_loop",
    }:
        return "exploratory_expectation_too_strict"
    return "needs_human_review"


def top_examples(red_findings: list[dict[str, Any]], classification_prefix: str, limit: int) -> list[dict[str, Any]]:
    examples: list[dict[str, Any]] = []
    for item in red_findings:
        classification = str(item.get("remaining_menu_reset_classification") or "")
        if not classification.startswith(classification_prefix):
            continue
        examples.append(
            {
                "scenario_id": item.get("scenario_id"),
                "classification": classification,
                "campaign_id": item.get("campaign_id"),
                "scenario_family": item.get("scenario_family"),
                "selected_action_source": item.get("selected_action_source"),
                "mechanical_failure_flags": item.get("mechanical_failure_flags") or [],
                "buyer_script": item.get("buyer_script") or [],
                "final_response": final_response(item),
            }
        )
        if len(examples) >= limit:
            break
    return examples


def generate() -> dict[str, Any]:
    source_result = read_json(SOURCE_DIR / "result.json")
    scenarios = read_jsonl(SOURCE_DIR / "review_packet.jsonl")
    red_findings: list[dict[str, Any]] = []
    for scenario in scenarios:
        if scenario.get("tier") != "exploratory_red_findings":
            continue
        if not scenario.get("mechanical_failure_flags"):
            continue
        item = dict(scenario)
        item["remaining_menu_reset_classification"] = classify(item)
        red_findings.append(item)

    by_class = Counter(str(item["remaining_menu_reset_classification"]) for item in red_findings)
    by_source = Counter(selected_source(item) for item in red_findings)
    by_family = Counter(str(item.get("scenario_family") or "") for item in red_findings)
    by_campaign = Counter(str(item.get("campaign_id") or "") for item in red_findings)
    class_by_source: dict[str, dict[str, int]] = defaultdict(dict)
    for classification in sorted(by_class):
        class_by_source[classification] = dict(
            sorted(Counter(selected_source(item) for item in red_findings if item["remaining_menu_reset_classification"] == classification).items())
        )

    result = {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_ID,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_status": source_result.get("status"),
        "source_red_finding_count": int(source_result.get("red_finding_count") or 0),
        "audited_red_finding_count": len(red_findings),
        "classification_counts": dict(sorted(by_class.items())),
        "counts_by_selected_action_source": dict(sorted(by_source.items())),
        "counts_by_scenario_family": dict(sorted(by_family.items())),
        "counts_by_campaign": dict(sorted(by_campaign.items())),
        "classification_counts_by_source": class_by_source,
        "top_true_defects": top_examples(red_findings, "true_", 30),
        "top_false_positive_or_expectation_examples": [
            *top_examples(red_findings, "acceptable_", 10),
            *top_examples(red_findings, "exploratory_", 10),
            *top_examples(red_findings, "terminal_", 10),
        ][:10],
        "recommended_patch_scope": [
            "Patch true_stability_menu_reset after corrections, hostile challenges, mismatch, and configured-gap clarity requests.",
            "Patch true_hostile_challenge_not_deescalated with direct one-move de-escalation.",
            "Patch true_repeated_response_without_progress only where the buyer explicitly complains about repetition.",
            "Patch true_appointment_too_early separately only if callback/time requests still schedule instead of noting a preference.",
            "Do not patch acceptable ASR clarifications into pain confirmations.",
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
    return result


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
                f"- Campaign: `{item['campaign_id']}`",
                f"- Family: `{item['scenario_family']}`",
                f"- Source: `{item['selected_action_source']}`",
                f"- Flags: `{', '.join(item['mechanical_failure_flags'])}`",
                f"- Buyer script: `{item['buyer_script']}`",
                f"- Final response: {item['final_response']}",
                "",
            ]
        )
    lines.append("## False Positives / Expectation Too Strict")
    for item in result["top_false_positive_or_expectation_examples"]:
        lines.extend(
            [
                f"### {item['scenario_id']}",
                f"- Classification: `{item['classification']}`",
                f"- Campaign: `{item['campaign_id']}`",
                f"- Family: `{item['scenario_family']}`",
                f"- Flags: `{', '.join(item['mechanical_failure_flags'])}`",
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
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
