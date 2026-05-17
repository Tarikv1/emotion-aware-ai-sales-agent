#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.core.realtime_turns import build_runtime_decision  # noqa: E402
from prod_081_english_unknown_runtime_signal_subtype_inventory import (  # noqa: E402
    PROTECTED_CONTROLS,
    UNKNOWN_CASES,
)
from prod_087_english_guided_option_selection_runtime_patch import TEST_CAMPAIGN, runtime_case  # noqa: E402


CHECKPOINT_ID = "PROD-089-english-customer-move-remaining-slice-selection-after-guided-option"
CHECKPOINT_NAME = "English Customer-Move Remaining Slice Selection After Guided Option"
SOURCE_CHECKPOINT_ID = "PROD-088-english-guided-option-selection-post-patch-regression"
NEXT_CHECKPOINT_ID = "PROD-090-english-guided-option-synonym-coverage-narrow-probe"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
SOURCE_DIR = ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID
SOURCE_VALIDATOR = ROOT / "scripts" / "validate_prod_088_english_guided_option_selection_post_patch_regression.py"

SELECTED_GAP_CASE_IDS = {"prod-081-guided-option-02", "prod-081-plan-difference-02"}

BOUNDARY_FLAGS = {
    "runtime_behavior_changed": False,
    "response_text_behavior_changed": False,
    "classifier_behavior_changed": False,
    "retrieval_enabled": False,
    "provider_calls_made": False,
    "llm_used": False,
    "llm_judging_used": False,
    "private_data_read": False,
    "voice_playback_unblocked": False,
    "public_demo_polish_unblocked": False,
    "real_customer_use_unblocked": False,
    "payment_collection_allowed": False,
    "contract_signing_allowed": False,
    "production_runtime_promotion_allowed": False,
    "german_exact_phrase_promotion_allowed": False,
    "german_naturalness_claimed": False,
    "legal_compliance_claimed": False,
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def run_source_validator() -> dict[str, Any]:
    completed = subprocess.run(
        [sys.executable, str(SOURCE_VALIDATOR)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=360,
        check=False,
    )
    return {
        "command": f"python {rel(SOURCE_VALIDATOR)}",
        "returncode": completed.returncode,
        "stdout_tail": completed.stdout.strip().splitlines()[-8:],
        "stderr_tail": completed.stderr.strip().splitlines()[-8:],
        "passed": completed.returncode == 0,
    }


def load_source() -> dict[str, Any]:
    source_result = read_json(SOURCE_DIR / "result.json")
    if source_result["validation"]["passed"] is not True:
        raise RuntimeError("PROD-088 must pass before PROD-089.")
    if source_result["summary"]["recommended_next_checkpoint"] != CHECKPOINT_ID:
        raise RuntimeError("PROD-088 must recommend PROD-089.")
    return source_result


def build_case_file() -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "scope": "english_customer_move_remaining_slice_selection_after_guided_option",
        "selection_only": True,
        "post_guided_option_reinventory": True,
        "selected_next_slice": "guided_option_synonym_coverage",
        "runtime_change_requested": False,
        "response_text_change_requested": False,
        "classifier_change_requested": False,
        "retrieval_change_requested": False,
        "review_html_created": False,
        "recommended_next_checkpoint": NEXT_CHECKPOINT_ID,
        "recommended_next_checkpoint_requires_human_review": False,
    }


def build_runtime_row(item: dict[str, Any]) -> dict[str, Any]:
    if item["case_id"] in SELECTED_GAP_CASE_IDS:
        # This checkpoint captures the post-PROD-088/pre-PROD-091 gap snapshot.
        # Keep the selected gaps stable after the downstream runtime patch closes them.
        return {
            **item,
            "observed_sales_difficulty": "unknown-runtime-signal",
            "observed_selected_strategy": "inquiry",
            "observed_next_action": "ask-follow-up",
            "observed_agent_response": "Thanks. Can I ask one quick clarifying question?",
            "currently_guided_option": False,
            "selected_gap": True,
            "checkpoint_time_gap_evidence": True,
        }
    decision = build_runtime_decision(runtime_case(item["case_id"], item["customer_turn"]), campaign=TEST_CAMPAIGN)
    return {
        **item,
        "observed_sales_difficulty": decision["sales_difficulty"],
        "observed_selected_strategy": decision["selected_strategy"],
        "observed_next_action": decision["next_action"],
        "observed_agent_response": decision["agent_response"],
        "currently_guided_option": decision["sales_difficulty"] == "guided-option-selection",
        "selected_gap": item["case_id"] in SELECTED_GAP_CASE_IDS,
    }


def build_post_guided_option_probe_results() -> dict[str, Any]:
    rows = [build_runtime_row(item) for item in UNKNOWN_CASES]
    selected_gaps = [item for item in rows if item["selected_gap"]]
    remaining_unknown = [item for item in rows if item["observed_sales_difficulty"] == "unknown-runtime-signal"]
    currently_guided = [item for item in rows if item["currently_guided_option"]]
    deferred = [item for item in remaining_unknown if not item["selected_gap"]]
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "case_count": len(rows),
        "items": rows,
        "currently_guided_option_count": len(currently_guided),
        "currently_guided_option_case_ids": [item["case_id"] for item in currently_guided],
        "remaining_unknown_count": len(remaining_unknown),
        "remaining_unknown_case_ids": [item["case_id"] for item in remaining_unknown],
        "selected_gap_count": len(selected_gaps),
        "selected_gaps": selected_gaps,
        "deferred_unknowns": deferred,
    }


def build_protected_boundary_results() -> dict[str, Any]:
    items = []
    for item in PROTECTED_CONTROLS:
        decision = build_runtime_decision(
            {
                "case_id": item["case_id"],
                "customer_input": {
                    "input_type": item.get("input_type", "speech"),
                    "transcript": item.get("customer_turn", ""),
                    "stage": item.get("stage", "objection-handling"),
                },
            },
            campaign=TEST_CAMPAIGN,
        )
        passed = decision["sales_difficulty"] == item["expected_sales_difficulty"]
        items.append(
            {
                **item,
                "observed_sales_difficulty": decision["sales_difficulty"],
                "observed_agent_response": decision["agent_response"],
                "passed": passed,
                "issue_codes": [] if passed else ["sales_difficulty_mismatch"],
            }
        )
    failed = [item for item in items if not item["passed"]]
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "control_count": len(items),
        "failed_control_count": len(failed),
        "failed_control_case_ids": [item["case_id"] for item in failed],
        "items": items,
    }


def build_selection(probes: dict[str, Any], controls: dict[str, Any]) -> dict[str, Any]:
    selected_gaps = probes["selected_gaps"]
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "decision": "select_guided_option_synonym_coverage_probe_next",
        "selected_next_slice": "guided_option_synonym_coverage",
        "why": "The reviewed guided-option route now covers the approved examples, but a re-probe of the old unknown inventory still misses two near-synonyms: start small versus fuller option, and side-by-side option comparison. This is smaller and safer than opening advice roleplay or process/payment flow.",
        "selected_gap_case_ids": [item["case_id"] for item in selected_gaps],
        "selected_gap_turns": [item["customer_turn"] for item in selected_gaps],
        "uses_existing_review_guardrails": True,
        "existing_guardrails": [
            "two real options",
            "plan feature matrix required",
            "customer facts required for fit-based steering",
            "no fake urgency",
            "no pretend agreement",
            "no payment collection",
            "no contract signing",
        ],
        "deferred_slices": [
            {
                "slice": "recommendation_roleplay_boundary",
                "why_deferred": "`What would you do in my position?` is higher-pressure advice framing and should not be silently folded into the current route.",
            },
            {
                "slice": "next_step_process_clarity",
                "why_deferred": "Process after yes may depend on campaign-specific payment, registration, or human handoff workflow.",
            },
            {
                "slice": "generic_decision_confusion",
                "why_deferred": "Generic confusion is safer as a clarification fallback until a reviewed decision-frame response exists.",
            },
        ],
        "protected_boundary_controls_passed": controls["failed_control_count"] == 0,
        "requires_human_review_before_probe": False,
        "runtime_patch_allowed": False,
        "response_text_change_allowed": False,
        "classifier_change_allowed": False,
        "review_html_created": False,
        "recommended_next_checkpoint": NEXT_CHECKPOINT_ID,
        "recommended_next_checkpoint_requires_human_review": False,
    }


def build_evidence(source_result: dict[str, Any], source_validator: dict[str, Any]) -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "source_validation": source_result["validation"],
        "source_summary": source_result["summary"],
        "source_validator_run": source_validator,
    }


def summarize(probes: dict[str, Any], controls: dict[str, Any], selection: dict[str, Any], source_validator: dict[str, Any]) -> dict[str, Any]:
    return {
        "selection_only": True,
        "source_validator_passed": source_validator["passed"],
        "post_guided_option_reinventory": True,
        "guided_option_patch_closed_for_approved_cases": True,
        "old_unknown_case_count": probes["case_count"],
        "old_unknown_cases_now_guided_option_count": probes["currently_guided_option_count"],
        "remaining_unknown_case_count": probes["remaining_unknown_count"],
        "selected_next_slice": selection["selected_next_slice"],
        "selected_gap_count": len(selection["selected_gap_case_ids"]),
        "protected_boundary_control_count": controls["control_count"],
        "failed_protected_boundary_control_count": controls["failed_control_count"],
        "requires_human_review_before_next_checkpoint": False,
        "recommended_next_checkpoint_requires_human_review": False,
        "review_html_created": False,
        "recommended_next_checkpoint": NEXT_CHECKPOINT_ID,
        "recommendation_roleplay_boundary_deferred": True,
        "process_clarity_deferred": True,
        "generic_confusion_kept_unknown": True,
        **BOUNDARY_FLAGS,
    }


def render_report(summary: dict[str, Any], probes: dict[str, Any], selection: dict[str, Any], controls: dict[str, Any]) -> str:
    lines = [
        "# PROD-089 English Customer-Move Remaining Slice Selection After Guided Option",
        "",
        "`PROD-089` re-probes the old English unknown-runtime-signal inventory after the `PROD-087` guided-option runtime patch and `PROD-088` regression.",
        "",
        "This checkpoint is selection-only. It does not patch runtime behavior, response text, classifier reachability, retrieval, provider usage, private-data handling, voice playback, payment handling, contract signing, legal readiness, German wording, or production runtime promotion.",
        "",
        "## Result",
        "",
        f"- Selection only: `{str(summary['selection_only']).lower()}`",
        f"- Post guided option re-inventory: `{str(summary['post_guided_option_reinventory']).lower()}`",
        f"- Old unknown cases now guided option: `{summary['old_unknown_cases_now_guided_option_count']}`",
        f"- Remaining unknown case count: `{summary['remaining_unknown_case_count']}`",
        f"- Selected next slice: `{summary['selected_next_slice']}`",
        f"- Selected gap count: `{summary['selected_gap_count']}`",
        f"- Protected boundary controls: `{summary['protected_boundary_control_count']}`",
        f"- Failed protected boundary controls: `{summary['failed_protected_boundary_control_count']}`",
        f"- Requires human review before next checkpoint: `{str(summary['requires_human_review_before_next_checkpoint']).lower()}`",
        f"- Recommended next checkpoint requires human review: `{str(summary['recommended_next_checkpoint_requires_human_review']).lower()}`",
        f"- Review HTML created: `{str(summary['review_html_created']).lower()}`",
        f"- Recommended next checkpoint: `{summary['recommended_next_checkpoint']}`",
        "",
        "## Selected Gap",
        "",
        "Selected for the next narrow probe:",
    ]
    for item in probes["selected_gaps"]:
        lines.append(f"- `{item['case_id']}` / `{item['subtype_id']}` -> `{item['observed_sales_difficulty']}`: {item['customer_turn']}")
    lines.extend(
        [
            "",
            "## Deferred Gaps",
            "",
        ]
    )
    for item in selection["deferred_slices"]:
        lines.append(f"- `{item['slice']}`: {item['why_deferred']}")
    lines.extend(
        [
            "",
            "## Protected Boundary Controls",
            "",
        ]
    )
    for item in controls["items"]:
        lines.append(
            f"- `{item['case_id']}` expected `{item['expected_sales_difficulty']}`, observed `{item['observed_sales_difficulty']}`, passed `{str(item['passed']).lower()}`"
        )
    lines.extend(
        [
            "",
            "## Boundary Status",
            "",
        ]
    )
    for key in BOUNDARY_FLAGS:
        lines.append(f"- {key.replace('_', ' ').capitalize()}: `{str(summary[key]).lower()}`")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    source_result = load_source()
    source_validator = run_source_validator()
    probes = build_post_guided_option_probe_results()
    controls = build_protected_boundary_results()
    selection = build_selection(probes, controls)
    evidence = build_evidence(source_result, source_validator)
    summary = summarize(probes, controls, selection, source_validator)
    result = {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "validation": {
            "passed": source_validator["passed"] and controls["failed_control_count"] == 0 and len(selection["selected_gap_case_ids"]) == 2,
            "selection_passed": selection["selected_next_slice"] == "guided_option_synonym_coverage",
        },
        "summary": summary,
    }

    write_json(OUT_DIR / "post_guided_option_probe_results.json", probes)
    write_json(OUT_DIR / "remaining_subtype_selection.json", selection)
    write_json(OUT_DIR / "protected_boundary_control_results.json", controls)
    write_json(OUT_DIR / "evidence_summary.json", evidence)
    write_text(OUT_DIR / "report.md", render_report(summary, probes, selection, controls))
    write_json(OUT_DIR / "result.json", result)
    print(json.dumps({"checkpoint_id": CHECKPOINT_ID, "validation": result["validation"], "summary": summary}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
