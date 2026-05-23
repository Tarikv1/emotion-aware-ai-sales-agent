#!/usr/bin/env python3
"""Audit live-inspired adversarial matrix red findings by root cause."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ID = "LIVE-INSPIRED-ADVERSARIAL-DIALOGUE-MATRIX-001"
CHECKPOINT_ID = "ADVERSARIAL-MATRIX-RED-FINDINGS-AUDIT-001"
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


def selected_source(scenario: dict[str, Any]) -> str:
    return str(scenario.get("selected_action_source") or "")


def final_response(scenario: dict[str, Any]) -> str:
    turns = scenario.get("turns") or []
    return str((turns[-1] if turns else {}).get("final_response") or "")


def classify(scenario: dict[str, Any]) -> str:
    flags = set(str(flag) for flag in scenario.get("mechanical_failure_flags") or [])
    source = selected_source(scenario)
    response = norm(final_response(scenario))
    family = str(scenario.get("scenario_family") or "")

    if "stability_guard_overrode_high_confidence_move" in flags:
        return "stability_guard_overrode_high_confidence_move"
    if source == "pre_speech_conversation_stability_guard" and "repeated_full_menu" in flags:
        return "stability_guard_menu_reset"
    if "asr_near_miss_not_clarified" in flags:
        return "asr_near_miss_gap_not_recognized"
    if "did_not_answer_direct_question" in flags:
        return "direct_question_not_satisfied"
    if "false_assumption_not_repaired" in flags or "repeated_false_assumption" in flags:
        return "false_assumption_correction_missing"
    if "internal_wording_leak" in flags:
        if source == "live_voice_session_policy" or "i should not" in response or "approved qualified reviewer path" in response:
            return "internal_wording_source_live_policy"
        return "internal_wording_source_universal"
    if "campaign_contamination" in flags:
        return "campaign_contamination"
    if "out_of_scope_reset_after_relevant_context" in flags:
        return "out_of_campaign_relevance_bad_fallback"
    if "appointment_too_early" in flags:
        return "appointment_too_early"
    if "hostile_response_not_deescalated" in flags:
        return "hostile_challenge_not_deescalated"
    if "repeated_response" in flags:
        return "repeated_response_without_progress"
    if family in {
        "callback_time_too_early_or_ambiguous",
        "early_callback_premature_scheduling",
        "repeated_answer_variation_anti_loop",
    }:
        return "exploratory_expectation_too_strict"
    return "needs_human_review"


def top_examples(red_findings: list[dict[str, Any]], limit: int = 20) -> list[dict[str, Any]]:
    priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    ranked = sorted(
        red_findings,
        key=lambda item: (
            priority_order.get(str(item.get("human_reviewer_priority") or ""), 4),
            -len(item.get("mechanical_failure_flags") or []),
            str(item.get("scenario_id") or ""),
        ),
    )
    examples: list[dict[str, Any]] = []
    for item in ranked[:limit]:
        examples.append(
            {
                "scenario_id": item.get("scenario_id"),
                "root_cause": item.get("root_cause"),
                "campaign_id": item.get("campaign_id"),
                "scenario_family": item.get("scenario_family"),
                "selected_action_source": item.get("selected_action_source"),
                "mechanical_failure_flags": item.get("mechanical_failure_flags") or [],
                "buyer_script": item.get("buyer_script") or [],
                "final_response": final_response(item),
            }
        )
    return examples


def generate() -> dict[str, Any]:
    source_result = read_json(SOURCE_DIR / "result.json")
    records = read_jsonl(SOURCE_DIR / "review_packet.jsonl")
    red_findings: list[dict[str, Any]] = []
    for scenario in records:
        if scenario.get("tier") == "exploratory_red_findings" and scenario.get("mechanical_failure_flags"):
            item = dict(scenario)
            item["root_cause"] = classify(item)
            red_findings.append(item)

    by_root = Counter(str(item["root_cause"]) for item in red_findings)
    by_source = Counter(selected_source(item) for item in red_findings)
    by_family = Counter(str(item.get("scenario_family") or "") for item in red_findings)
    by_campaign = Counter(str(item.get("campaign_id") or "") for item in red_findings)
    root_by_source: dict[str, dict[str, int]] = defaultdict(dict)
    for root in sorted(by_root):
        source_counts = Counter(selected_source(item) for item in red_findings if item["root_cause"] == root)
        root_by_source[root] = dict(sorted(source_counts.items()))

    recommendation = [
        "Patch stability_guard_menu_reset for near configured gaps before broad exploratory work.",
        "Patch internal_wording_source_live_policy where customer-facing boundary text leaks implementation wording.",
        "Patch direct question / why-human-review only after the menu reset slice is green.",
        "Leave callback ambiguity, repeated-response style, and broad hostile-challenge polish as follow-up unless focused validators reproduce a low-risk fix.",
    ]

    result = {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_ID,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_status": source_result.get("status"),
        "source_red_finding_count": int(source_result.get("red_finding_count") or 0),
        "audited_red_finding_count": len(red_findings),
        "classification_counts": dict(sorted(by_root.items())),
        "counts_by_source": dict(sorted(by_source.items())),
        "counts_by_scenario_family": dict(sorted(by_family.items())),
        "counts_by_campaign": dict(sorted(by_campaign.items())),
        "root_cause_counts_by_source": root_by_source,
        "top_examples": top_examples(red_findings),
        "recommended_patch_slice": recommendation,
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
        "## Count By Root Cause",
        *(f"- `{key}`: `{value}`" for key, value in result["classification_counts"].items()),
        "",
        "## Count By Source",
        *(f"- `{key}`: `{value}`" for key, value in result["counts_by_source"].items()),
        "",
        "## Count By Scenario Family",
        *(f"- `{key}`: `{value}`" for key, value in result["counts_by_scenario_family"].items()),
        "",
        "## Count By Campaign",
        *(f"- `{key}`: `{value}`" for key, value in result["counts_by_campaign"].items()),
        "",
        "## Top Examples",
    ]
    for item in result["top_examples"]:
        lines.extend(
            [
                f"### {item['scenario_id']}",
                f"- Root cause: `{item['root_cause']}`",
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
            *(f"- {item}" for item in result["recommended_patch_slice"]),
            "",
            "## Runtime Behavior Changed",
            f"- `{str(result['runtime_behavior_changed']).lower()}`",
        ]
    )
    (OUT_DIR / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    result = generate()
    write_outputs(result)
    print(json.dumps({
        "checkpoint_id": CHECKPOINT_ID,
        "audited_red_finding_count": result["audited_red_finding_count"],
        "classification_counts": result["classification_counts"],
        "status": "pass",
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
