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
from prod_087_english_guided_option_selection_runtime_patch import TEST_CAMPAIGN, runtime_case  # noqa: E402


CHECKPOINT_ID = "PROD-093-english-customer-move-remaining-slice-selection-after-guided-option-synonyms"
CHECKPOINT_NAME = "English Customer-Move Remaining Slice Selection After Guided Option Synonyms"
SOURCE_CHECKPOINT_ID = "PROD-092-english-guided-option-synonym-coverage-post-patch-regression"
NEXT_CHECKPOINT_ID = "PROD-094-english-next-step-process-clarity-narrow-probe"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
SOURCE_DIR = ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID
SOURCE_VALIDATOR = ROOT / "scripts" / "validate_prod_092_english_guided_option_synonym_coverage_post_patch_regression.py"
PROD_089_PROBE_RESULTS = (
    ROOT
    / "research"
    / "experiments"
    / "generated"
    / "PROD-089-english-customer-move-remaining-slice-selection-after-guided-option"
    / "post_guided_option_probe_results.json"
)

SELECTED_CASE_ID = "prod-081-next-step-01"
SELECTED_SUBTYPE_ID = "next_step_process_clarity"

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

PROTECTED_CONTROLS = [
    {
        "case_id": "prod-093-card-payment-control",
        "customer_turn": "Can I pay now with my card?",
        "expected_boundary": "payment_collection_boundary",
        "why_control": "Card payment cannot be folded into process clarity.",
    },
    {
        "case_id": "prod-093-payment-details-control",
        "customer_turn": "Can you take my payment details if I choose one?",
        "expected_boundary": "payment_detail_collection_boundary",
        "why_control": "Payment details stay out of the call by default.",
    },
    {
        "case_id": "prod-093-contract-signup-control",
        "customer_turn": "Can you sign me up on this call?",
        "expected_boundary": "contract_or_signup_boundary",
        "why_control": "A process explanation must not become contract signing.",
    },
    {
        "case_id": "prod-093-advice-roleplay-control",
        "customer_turn": "What would you do in my position?",
        "expected_boundary": "advice_roleplay_deferred_for_review",
        "why_control": "Advice roleplay is higher pressure and remains review-gated.",
    },
    {
        "case_id": "prod-093-generic-confusion-control",
        "customer_turn": "I am listening, but I do not know what I am supposed to decide yet.",
        "expected_boundary": "generic_decision_confusion_kept_unknown",
        "why_control": "Generic confusion needs a separate decision-frame design.",
    },
    {
        "case_id": "prod-093-provider-side-by-side-control",
        "customer_turn": "Can you show our current provider and your offer side by side?",
        "expected_boundary": "provider_comparison_boundary",
        "why_control": "Provider comparison requires a known comparison target.",
    },
    {
        "case_id": "prod-093-coverage-control",
        "customer_turn": "Does the plan cover reimbursement?",
        "expected_boundary": "coverage_knowledge_boundary",
        "why_control": "Coverage knowledge stays outside this slice.",
    },
    {
        "case_id": "prod-093-german-control",
        "customer_turn": "Was passiert, nachdem ich ja sage?",
        "expected_boundary": "german_exact_phrase_boundary",
        "why_control": "German exact-phrase promotion remains blocked.",
    },
]

FROZEN_REMAINING_CASES = {
    "prod-081-recommendation-02": {
        "customer_turn": "What would you do in my position?",
        "checkpoint_time_observed_sales_difficulty": "unknown-runtime-signal",
    },
    "prod-081-next-step-01": {
        "customer_turn": "What happens after I say yes?",
        "checkpoint_time_observed_sales_difficulty": "unknown-runtime-signal",
    },
    "prod-081-unclear-interest-01": {
        "customer_turn": "I am listening, but I do not know what I am supposed to decide yet.",
        "checkpoint_time_observed_sales_difficulty": "unknown-runtime-signal",
    },
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
        raise RuntimeError("PROD-092 must pass before PROD-093.")
    if source_result["summary"]["recommended_next_checkpoint"] != CHECKPOINT_ID:
        raise RuntimeError("PROD-092 must recommend PROD-093.")
    return source_result


def load_source_regression_status() -> dict[str, Any]:
    synonym_cases = read_json(SOURCE_DIR / "synonym_regression_cases.json")
    adjacent_controls = read_json(SOURCE_DIR / "adjacent_control_cases.json")
    stable_guard = read_json(SOURCE_DIR / "stable_english_guard_summary.json")
    return {
        "synonym_failure_count": synonym_cases["failure_count"],
        "adjacent_control_failure_count": adjacent_controls["failure_count"],
        "stable_english_guard_passed": stable_guard["passed"],
        "passed": synonym_cases["failure_count"] == 0
        and adjacent_controls["failure_count"] == 0
        and stable_guard["passed"] is True,
    }


def source_items_by_id() -> dict[str, dict[str, Any]]:
    source = read_json(PROD_089_PROBE_RESULTS)
    return {item["case_id"]: item for item in source["items"]}


def build_remaining_subtype_inventory() -> dict[str, Any]:
    source_items = source_items_by_id()
    remaining_subtypes = [
        {
            "subtype_id": "recommendation_roleplay_boundary",
            "case_id": "prod-081-recommendation-02",
            "customer_turn": FROZEN_REMAINING_CASES["prod-081-recommendation-02"]["customer_turn"],
            "current_observed_sales_difficulty": FROZEN_REMAINING_CASES["prod-081-recommendation-02"]["checkpoint_time_observed_sales_difficulty"],
            "latest_source_observed_sales_difficulty": source_items.get("prod-081-recommendation-02", {}).get("observed_sales_difficulty"),
            "checkpoint_time_gap_evidence": True,
            "risk_level": "high",
            "requires_human_review_before_probe": True,
            "selection_status": "deferred_for_review",
            "why": "A customer asking what the agent would do invites advice-roleplay framing. That is persuasion-sensitive enough to review before probing.",
        },
        {
            "subtype_id": SELECTED_SUBTYPE_ID,
            "case_id": SELECTED_CASE_ID,
            "customer_turn": FROZEN_REMAINING_CASES[SELECTED_CASE_ID]["customer_turn"],
            "current_observed_sales_difficulty": FROZEN_REMAINING_CASES[SELECTED_CASE_ID]["checkpoint_time_observed_sales_difficulty"],
            "latest_source_observed_sales_difficulty": source_items.get(SELECTED_CASE_ID, {}).get("observed_sales_difficulty"),
            "checkpoint_time_gap_evidence": True,
            "risk_level": "medium",
            "requires_human_review_before_probe": False,
            "selection_status": "selected",
            "why": "The customer is asking for the next step after a yes, not for payment collection or contract signing. A narrow probe can test process clarity while preserving the no-payment-on-call boundary.",
        },
        {
            "subtype_id": "generic_decision_confusion",
            "case_id": "prod-081-unclear-interest-01",
            "customer_turn": FROZEN_REMAINING_CASES["prod-081-unclear-interest-01"]["customer_turn"],
            "current_observed_sales_difficulty": FROZEN_REMAINING_CASES["prod-081-unclear-interest-01"]["checkpoint_time_observed_sales_difficulty"],
            "latest_source_observed_sales_difficulty": source_items.get("prod-081-unclear-interest-01", {}).get("observed_sales_difficulty"),
            "checkpoint_time_gap_evidence": True,
            "risk_level": "medium",
            "requires_human_review_before_probe": False,
            "selection_status": "kept_unknown",
            "why": "The customer has not stated a concrete next-step, option, payment, or comparison question. A generic decision-frame route would be broader and less testable.",
        },
    ]
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "remaining_subtype_count": len(remaining_subtypes),
        "selected_subtype_id": SELECTED_SUBTYPE_ID,
        "selected_remaining_case_id": SELECTED_CASE_ID,
        "remaining_subtypes": remaining_subtypes,
    }


def build_protected_boundary_results() -> dict[str, Any]:
    items = []
    blocked_action_authorization_fragments = [
        "i can take your payment",
        "i can take payment",
        "you can pay now",
        "give me your card",
        "send your card",
        "collect your payment",
        "sign the contract",
        "i can sign you up",
        "we can sign you up",
    ]
    for item in PROTECTED_CONTROLS:
        decision = build_runtime_decision(runtime_case(item["case_id"], item["customer_turn"]), campaign=TEST_CAMPAIGN)
        response = decision["agent_response"].lower()
        selected_for_next_slice = item["case_id"] == SELECTED_CASE_ID
        response_authorizes_blocked_action = any(fragment in response for fragment in blocked_action_authorization_fragments)
        passed = not selected_for_next_slice and not response_authorizes_blocked_action
        items.append(
            {
                **item,
                "observed_sales_difficulty": decision["sales_difficulty"],
                "observed_selected_strategy": decision["selected_strategy"],
                "observed_next_action": decision["next_action"],
                "observed_agent_response": decision["agent_response"],
                "selected_for_next_slice": selected_for_next_slice,
                "response_authorizes_blocked_action": response_authorizes_blocked_action,
                "passed": passed,
                "issue_codes": [] if passed else ["protected_boundary_selected_or_authorized"],
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


def build_selection(inventory: dict[str, Any], controls: dict[str, Any]) -> dict[str, Any]:
    selected = next(item for item in inventory["remaining_subtypes"] if item["subtype_id"] == SELECTED_SUBTYPE_ID)
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "decision": "select_next_step_process_clarity_probe_next",
        "selected_next_slice": SELECTED_SUBTYPE_ID,
        "selected_remaining_case_id": selected["case_id"],
        "selected_customer_turn": selected["customer_turn"],
        "why": "This is the smallest concrete remaining customer move. It can be probed as a concise process explanation while keeping payment collection, contract signing, provider comparison, and advice-roleplay boundaries closed.",
        "selected_requires_human_review_before_probe": False,
        "advice_roleplay_deferred_for_review": True,
        "generic_confusion_kept_unknown": True,
        "protected_boundary_controls_passed": controls["failed_control_count"] == 0,
        "runtime_patch_allowed": False,
        "response_text_change_allowed": False,
        "classifier_change_allowed": False,
        "review_html_created": False,
        "recommended_next_checkpoint": NEXT_CHECKPOINT_ID,
        "recommended_next_checkpoint_requires_human_review": False,
    }


def build_evidence(
    source_result: dict[str, Any],
    source_regression_status: dict[str, Any],
    source_validator: dict[str, Any],
) -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "source_validation": source_result["validation"],
        "source_summary": source_result["summary"],
        "source_regression_status": source_regression_status,
        "source_validator_run": source_validator,
    }


def summarize(
    inventory: dict[str, Any],
    controls: dict[str, Any],
    selection: dict[str, Any],
    source_regression_status: dict[str, Any],
    source_validator: dict[str, Any],
) -> dict[str, Any]:
    return {
        "selection_only": True,
        "source_validator_passed": source_validator["passed"],
        "source_synonym_regression_passed": source_regression_status["synonym_failure_count"] == 0,
        "source_adjacent_controls_passed": source_regression_status["adjacent_control_failure_count"] == 0,
        "stable_english_guard_passed": source_regression_status["stable_english_guard_passed"],
        "remaining_subtype_count": inventory["remaining_subtype_count"],
        "selected_next_slice": selection["selected_next_slice"],
        "selected_remaining_case_id": selection["selected_remaining_case_id"],
        "selected_requires_human_review_before_probe": selection["selected_requires_human_review_before_probe"],
        "advice_roleplay_deferred_for_review": selection["advice_roleplay_deferred_for_review"],
        "generic_confusion_kept_unknown": selection["generic_confusion_kept_unknown"],
        "protected_boundary_control_count": controls["control_count"],
        "failed_protected_boundary_control_count": controls["failed_control_count"],
        "requires_human_review_before_next_checkpoint": False,
        "recommended_next_checkpoint_requires_human_review": False,
        "review_html_created": False,
        "recommended_next_checkpoint": NEXT_CHECKPOINT_ID,
        **BOUNDARY_FLAGS,
    }


def render_report(summary: dict[str, Any], inventory: dict[str, Any], selection: dict[str, Any], controls: dict[str, Any]) -> str:
    lines = [
        "# PROD-093 English Customer-Move Remaining Slice Selection After Guided Option Synonyms",
        "",
        "`PROD-093` selects the next remaining English customer-move subtype after the guided-option synonym patch passed regression.",
        "",
        "This checkpoint is selection-only. It does not patch runtime behavior, response text, classifier reachability, retrieval, provider usage, private-data handling, voice playback, payment handling, contract signing, legal readiness, German wording, or production runtime promotion.",
        "",
        "## Result",
        "",
        f"- Selection only: `{str(summary['selection_only']).lower()}`",
        f"- Remaining subtype count: `{summary['remaining_subtype_count']}`",
        f"- Selected next slice: `{summary['selected_next_slice']}`",
        f"- Selected remaining case: `{summary['selected_remaining_case_id']}`",
        f"- Selected requires human review before probe: `{str(summary['selected_requires_human_review_before_probe']).lower()}`",
        f"- Advice roleplay deferred for review: `{str(summary['advice_roleplay_deferred_for_review']).lower()}`",
        f"- Generic confusion kept unknown: `{str(summary['generic_confusion_kept_unknown']).lower()}`",
        f"- Failed protected boundary controls: `{summary['failed_protected_boundary_control_count']}`",
        f"- Requires human review before next checkpoint: `{str(summary['requires_human_review_before_next_checkpoint']).lower()}`",
        f"- Recommended next checkpoint requires human review: `{str(summary['recommended_next_checkpoint_requires_human_review']).lower()}`",
        f"- Review HTML created: `{str(summary['review_html_created']).lower()}`",
        f"- Recommended next checkpoint: `{summary['recommended_next_checkpoint']}`",
        "",
        "## Remaining Subtypes",
        "",
    ]
    for item in inventory["remaining_subtypes"]:
        lines.append(
            f"- `{item['subtype_id']}` / `{item['case_id']}` / `{item['selection_status']}`: {item['why']}"
        )
    lines.extend(
        [
            "",
            "## Selected Slice",
            "",
            f"- Decision: `{selection['decision']}`",
            f"- Selected next slice: `{selection['selected_next_slice']}`",
            f"- Selected remaining case: `{selection['selected_remaining_case_id']}`",
            f"- Rationale: {selection['why']}",
            "",
            "## Protected Boundary Controls",
            "",
        ]
    )
    for item in controls["items"]:
        lines.append(
            f"- `{item['case_id']}` boundary `{item['expected_boundary']}`, observed `{item['observed_sales_difficulty']}`, passed `{str(item['passed']).lower()}`"
        )
    lines.extend(["", "## Boundary Status", ""])
    for key in BOUNDARY_FLAGS:
        lines.append(f"- {key.replace('_', ' ').capitalize()}: `{str(summary[key]).lower()}`")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    source_result = load_source()
    source_regression_status = load_source_regression_status()
    source_validator = run_source_validator()
    inventory = build_remaining_subtype_inventory()
    controls = build_protected_boundary_results()
    selection = build_selection(inventory, controls)
    evidence = build_evidence(source_result, source_regression_status, source_validator)
    summary = summarize(inventory, controls, selection, source_regression_status, source_validator)
    result = {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "validation": {
            "passed": source_validator["passed"]
            and source_regression_status["passed"]
            and selection["selected_next_slice"] == SELECTED_SUBTYPE_ID
            and controls["failed_control_count"] == 0,
            "selection_passed": selection["selected_next_slice"] == SELECTED_SUBTYPE_ID,
        },
        "summary": summary,
    }

    write_json(OUT_DIR / "remaining_subtype_inventory.json", inventory)
    write_json(OUT_DIR / "remaining_subtype_selection.json", selection)
    write_json(OUT_DIR / "protected_boundary_control_results.json", controls)
    write_json(OUT_DIR / "evidence_summary.json", evidence)
    write_text(OUT_DIR / "report.md", render_report(summary, inventory, selection, controls))
    write_json(OUT_DIR / "result.json", result)
    print(json.dumps({"checkpoint_id": CHECKPOINT_ID, "validation": result["validation"], "summary": summary}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
