#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-073-english-customer-move-classification-gate-decision"
CHECKPOINT_NAME = "English Customer-Move Classification Gate Decision"
SOURCE_CHECKPOINT_ID = "PROD-072-english-coverage-knowledge-post-patch-regression"
PRIORITY_SOURCE_CHECKPOINT_ID = "PROD-061-english-product-policy-gate-prioritization"
NEXT_CHECKPOINT_ID = "PROD-074-english-customer-move-classification-slice-inventory"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
CASE_FILE = ROOT / "research" / "experiments" / "cases" / "prod-073-english-customer-move-classification-gate-decision.json"
SOURCE_DIR = ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID
SOURCE_VALIDATOR = ROOT / "scripts" / "validate_prod_072_english_coverage_knowledge_post_patch_regression.py"
SOURCE_VALIDATOR_COMMAND = "python scripts\\validate_prod_072_english_coverage_knowledge_post_patch_regression.py"
PRIORITY_OPTIONS_FILE = ROOT / "research" / "experiments" / "generated" / PRIORITY_SOURCE_CHECKPOINT_ID / "gate_options.json"
PRIOR_SELECTION_FILE = ROOT / "research" / "experiments" / "generated" / "PROD-069-english-remaining-product-policy-gate-selection-after-voicemail" / "remaining_gate_selection.json"
GATE_ID = "customer_move_classification_outside_selected_non_refusal_groups"

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

CANDIDATE_SLICES = [
    {
        "slice_id": "specific_known_safe_non_refusal_turns",
        "status": "candidate_for_inventory_only",
        "why": "Some already-reviewed non-refusal groups have strong evidence, but expanding beyond those groups needs exact branch inventory first.",
        "risk": "Could duplicate already-promoted safe-call-control behavior or accidentally widen approved branches.",
        "runtime_patch_allowed": False,
    },
    {
        "slice_id": "unreachable_existing_response_types",
        "status": "candidate_for_inventory_only",
        "why": "Some localized responses may exist without classifier reachability; inventory can separate dead responses from intentionally blocked routes.",
        "risk": "Making dormant responses reachable without review can surface unapproved wording.",
        "runtime_patch_allowed": False,
    },
    {
        "slice_id": "unknown_runtime_signal_subtypes",
        "status": "candidate_for_inventory_only",
        "why": "Unknown turns are currently safest as clarification. Splitting unknowns requires evidence that a subtype has a safer deterministic route.",
        "risk": "Over-classification could reduce clarification and force wrong branches.",
        "runtime_patch_allowed": False,
    },
    {
        "slice_id": "protected_boundary_false_positive_checks",
        "status": "candidate_for_inventory_only",
        "why": "Any classifier expansion must prove it does not swallow support, do-not-call, payment, healthcare, coverage, voicemail, human-request, or email-only boundaries.",
        "risk": "False positives in protected boundaries are higher severity than missed sales opportunities.",
        "runtime_patch_allowed": False,
    },
]

SPLIT_CRITERIA = [
    "No broad customer-move classifier patch without a branch inventory.",
    "Each slice must define expected sales_difficulty, next_action, and call_control before runtime patching.",
    "Protected-boundary controls must be included for every classifier slice.",
    "Response text changes must stay out of classifier-reachability checkpoints unless separately reviewed.",
    "Human review is required only when the checkpoint asks Tarik to approve concrete behavior, wording, or product-policy tradeoffs.",
]


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
        timeout=300,
        check=False,
    )
    return {
        "command": SOURCE_VALIDATOR_COMMAND,
        "returncode": completed.returncode,
        "stdout_tail": completed.stdout.strip().splitlines()[-5:],
        "stderr_tail": completed.stderr.strip().splitlines()[-5:],
        "passed": completed.returncode == 0 and SOURCE_CHECKPOINT_ID in completed.stdout,
    }


def load_source() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    source_result = read_json(SOURCE_DIR / "result.json")
    source_decision = read_json(SOURCE_DIR / "post_patch_regression_decision.json")
    priority_options = read_json(PRIORITY_OPTIONS_FILE)
    prior_selection = read_json(PRIOR_SELECTION_FILE)
    summary = source_result["summary"]
    if source_result["validation"]["passed"] is not True:
        raise SystemExit("PROD-072 must pass before PROD-073.")
    if summary["failed_case_count"] != 0:
        raise SystemExit("PROD-072 failed cases block customer-move gate decision.")
    if summary["recommended_next_checkpoint"] != CHECKPOINT_ID:
        raise SystemExit("PROD-072 must recommend PROD-073.")
    if source_decision["recommended_next_checkpoint"] != CHECKPOINT_ID:
        raise SystemExit("PROD-072 decision must recommend PROD-073.")
    if prior_selection["deferred_gates"] != [GATE_ID]:
        raise SystemExit("PROD-069 must leave only the broad customer-move gate deferred.")
    if GATE_ID not in {item["gate_id"] for item in priority_options["ranked_gates"]}:
        raise SystemExit("PROD-061 gate options must include the broad customer-move classifier gate.")
    return source_result, source_decision, priority_options


def build_case_file() -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "priority_source_checkpoint_id": PRIORITY_SOURCE_CHECKPOINT_ID,
        "scope": "english_customer_move_classification_gate_decision_only",
        "remaining_gate_id": GATE_ID,
        "decision_type": "split_before_probe",
        "broad_classifier_patch_allowed": False,
        "runtime_change_requested": False,
        "response_text_change_requested": False,
        "classifier_change_requested": False,
        "retrieval_change_requested": False,
        "requires_human_review_before_next_checkpoint": False,
        "review_html_created": False,
        "recommended_next_checkpoint": NEXT_CHECKPOINT_ID,
        "split_criteria": SPLIT_CRITERIA,
    }


def build_decision() -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "decision": "split_broad_customer_move_gate_before_probe",
        "remaining_gate_id": GATE_ID,
        "broad_classifier_patch_allowed": False,
        "reason": "The remaining gate has the highest blast radius because it changes reachability across multiple runtime branches. The safe next step is an inventory of candidate slices, not a patch.",
        "requires_human_review_before_next_checkpoint": False,
        "review_html_created": False,
        "recommended_next_checkpoint": NEXT_CHECKPOINT_ID,
        "production_runtime_promotion_allowed": False,
    }


def build_slice_plan() -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "remaining_gate_id": GATE_ID,
        "selected_next_action": "inventory_classifier_slices",
        "runtime_patch_allowed": False,
        "response_text_change_allowed": False,
        "retrieval_allowed": False,
        "requires_human_review_before_next_checkpoint": False,
        "recommended_next_checkpoint": NEXT_CHECKPOINT_ID,
        "candidate_slices": CANDIDATE_SLICES,
        "inventory_requirements": [
            "enumerate current deterministic classifier branches",
            "identify unreachable localized response types",
            "separate already-approved selected non-refusal groups from unreviewed branches",
            "attach protected-boundary controls to every candidate slice",
            "recommend at most one narrow probe as the next runtime-adjacent step",
        ],
    }


def build_evidence_summary(source_result: dict[str, Any], source_validator: dict[str, Any], priority_options: dict[str, Any]) -> dict[str, Any]:
    gate = next(item for item in priority_options["ranked_gates"] if item["gate_id"] == GATE_ID)
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "source_validation": source_result["validation"],
        "source_summary": {
            "failed_case_count": source_result["summary"]["failed_case_count"],
            "stable_english_guard_passed": source_result["summary"]["stable_english_guard_passed"],
            "voicemail_guard_passed": source_result["summary"]["voicemail_guard_passed"],
            "recommended_next_checkpoint": source_result["summary"]["recommended_next_checkpoint"],
        },
        "source_validator_run": source_validator,
        "priority_source_checkpoint_id": PRIORITY_SOURCE_CHECKPOINT_ID,
        "priority_gate_rank": gate["rank"],
        "priority_gate_risk": gate["risk"],
    }


def summarize(source_validator: dict[str, Any]) -> dict[str, Any]:
    return {
        "decision_only": True,
        "source_validator_passed": source_validator["passed"],
        "remaining_gate_id": GATE_ID,
        "decision": "split_broad_customer_move_gate_before_probe",
        "broad_classifier_patch_allowed": False,
        "narrow_slice_inventory_required_next": True,
        "candidate_slice_count": len(CANDIDATE_SLICES),
        "requires_human_review_before_next_checkpoint": False,
        "review_html_created": False,
        "recommended_next_checkpoint": NEXT_CHECKPOINT_ID,
        **BOUNDARY_FLAGS,
    }


def render_report(decision: dict[str, Any], slice_plan: dict[str, Any], summary: dict[str, Any]) -> str:
    lines = [
        "# PROD-073 English Customer-Move Classification Gate Decision",
        "",
        "`PROD-073` decides what to do with the remaining broad `customer_move_classification_outside_selected_non_refusal_groups` gate.",
        "",
        "No human review required. This is decision only, creates no review HTML, and does not approve classifier expansion.",
        "",
        "## Decision",
        "",
        f"- Decision: `{decision['decision']}`",
        f"- Remaining gate: `{summary['remaining_gate_id']}`",
        f"- Broad classifier patch allowed: `{str(summary['broad_classifier_patch_allowed']).lower()}`",
        f"- Narrow slice inventory required next: `{str(summary['narrow_slice_inventory_required_next']).lower()}`",
        f"- Candidate slice count: `{summary['candidate_slice_count']}`",
        f"- Decision only: `{str(summary['decision_only']).lower()}`",
        f"- Review HTML created: `{str(summary['review_html_created']).lower()}`",
        f"- Recommended next checkpoint: `{summary['recommended_next_checkpoint']}`",
        "- Runtime behavior changed: `false`",
        "- Response text behavior changed: `false`",
        "- Classifier behavior changed: `false`",
        "- Retrieval enabled: `false`",
        "- Production runtime promotion allowed: `false`",
        "",
        "## Candidate Slices For Inventory",
        "",
    ]
    for item in slice_plan["candidate_slices"]:
        lines.extend(
            [
                f"### {item['slice_id']}",
                "",
                f"- Status: `{item['status']}`",
                f"- Runtime patch allowed: `{str(item['runtime_patch_allowed']).lower()}`",
                f"- Why: {item['why']}",
                f"- Risk: {item['risk']}",
                "",
            ]
        )
    lines.extend(
        [
            "## Boundary",
            "",
            "- Runtime behavior changed: `false`",
            "- Response text behavior changed: `false`",
            "- Classifier behavior changed: `false`",
            "- Retrieval enabled: `false`",
            "- Provider calls made: `false`",
            "- LLM used: `false`",
            "- LLM judging used: `false`",
            "- Private data read: `false`",
            "- Voice playback unblocked: `false`",
            "- Public demo polish unblocked: `false`",
            "- Real customer use unblocked: `false`",
            "- Payment collection allowed: `false`",
            "- Contract signing allowed: `false`",
            "- Production runtime promotion allowed: `false`",
            "- German exact-phrase promotion allowed: `false`",
            "- German naturalness claimed: `false`",
            "- Legal compliance claimed: `false`",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    source_result, _source_decision, priority_options = load_source()
    source_validator = run_source_validator()
    case_payload = build_case_file()
    decision = build_decision()
    slice_plan = build_slice_plan()
    evidence = build_evidence_summary(source_result, source_validator, priority_options)
    summary = summarize(source_validator)
    result = {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "validation": {
            "passed": source_validator["passed"] and summary["broad_classifier_patch_allowed"] is False,
            "gate_decision_passed": summary["decision"] == "split_broad_customer_move_gate_before_probe",
        },
        "summary": summary,
    }
    write_json(CASE_FILE, case_payload)
    write_json(OUT_DIR / "customer_move_gate_decision.json", decision)
    write_json(OUT_DIR / "classifier_slice_plan.json", slice_plan)
    write_json(OUT_DIR / "evidence_summary.json", evidence)
    write_json(OUT_DIR / "result.json", result)
    write_text(OUT_DIR / "report.md", render_report(decision, slice_plan, summary))
    print(json.dumps({"checkpoint_id": CHECKPOINT_ID, "validation": result["validation"], "summary": summary}, indent=2))


if __name__ == "__main__":
    main()
