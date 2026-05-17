#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-083-english-guided-option-selection-review-import"
CHECKPOINT_NAME = "English Guided Option Selection Review Import"
SOURCE_CHECKPOINT_ID = "PROD-082-english-guided-option-selection-review"
NEXT_CHECKPOINT_ID = "PROD-084-english-guided-option-selection-rewrite-design"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
SOURCE_DIR = ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID
IMPORT_FILE = ROOT / "research" / "experiments" / "imports" / SOURCE_CHECKPOINT_ID / "prod_082_guided_option_selection_review_from_chat.json"
SOURCE_VALIDATOR = ROOT / "scripts" / "validate_prod_082_english_guided_option_selection_review.py"

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
        timeout=300,
        check=False,
    )
    return {
        "command": f"python {rel(SOURCE_VALIDATOR)}",
        "returncode": completed.returncode,
        "stdout_tail": completed.stdout.strip().splitlines()[-8:],
        "stderr_tail": completed.stderr.strip().splitlines()[-8:],
        "passed": completed.returncode == 0,
    }


def load_inputs() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    source_result = read_json(SOURCE_DIR / "result.json")
    source_packet = read_json(SOURCE_DIR / "guided_option_selection_review_packet.json")
    review_import = read_json(IMPORT_FILE)
    if source_result["validation"]["passed"] is not True:
        raise RuntimeError("PROD-082 must pass before review import.")
    if source_result["summary"]["recommended_next_checkpoint"] != CHECKPOINT_ID:
        raise RuntimeError("PROD-082 must recommend PROD-083.")
    if source_packet["review_item"] != "guided_option_selection_candidate":
        raise RuntimeError("PROD-082 packet must be guided option selection.")
    if review_import["overall_decision"] != "needs_rewrite_before_probe":
        raise RuntimeError("PROD-083 expects needs_rewrite_before_probe.")
    return source_result, source_packet, review_import


def build_import_summary(review_import: dict[str, Any], source_packet: dict[str, Any]) -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "review_item": review_import["review_item"],
        "review_status": review_import["review_status"],
        "reviewer": review_import["reviewer"],
        "review_date": review_import["review_date"],
        "overall_decision": review_import["overall_decision"],
        "narrow_policy_probe_approved": False,
        "review_interpretation": {
            "existing_examples_approved": False,
            "rewrite_required": True,
            "why": "The review rejected the defensive opt-out framing and requires fit-based plan explanation, approved feature facts, shorter wording, and campaign-specific payment-path handling before any probe.",
        },
        "source_review_options": source_packet["review_options"],
        "overall_notes": review_import["overall_notes"],
        "example_decisions": review_import["example_decisions"],
    }


def build_rewrite_requirements(review_import: dict[str, Any]) -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "review_item": "guided_option_selection_candidate",
        "rewrite_required": True,
        "narrow_policy_probe_allowed_now": False,
        "rules": review_import["required_rewrite_rules"],
        "candidate_response_direction": [
            "Explain which plan fits which need.",
            "Use approved plan facts such as plan feature lists or upgrade paths.",
            "Steer toward the better fit when customer facts support it.",
            "Use acknowledgement plus light persuasion for uncertainty instead of dropping the opportunity.",
            "Keep deferral answers short.",
            "Leave obvious facts out.",
            "Do not repeat price math or customer wording unless the customer explicitly asks.",
        ],
    }


def build_plan_fact_requirements(review_import: dict[str, Any]) -> dict[str, Any]:
    payload = review_import["plan_fact_requirements"]
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "review_item": "guided_option_selection_candidate",
        "plan_feature_matrix_required": payload["plan_feature_matrix_required"],
        "invent_plan_features_allowed": payload["invent_plan_features_allowed"],
        "example_plan_placeholders": payload["example_plan_placeholders"],
        "runtime_requirement": "Do not generate guided option selection copy unless approved campaign data provides the plan feature matrix or the response uses explicit placeholders in a review-only artifact.",
    }


def build_payment_requirements(review_import: dict[str, Any]) -> dict[str, Any]:
    payload = review_import["payment_workflow_requirements"]
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "review_item": "guided_option_selection_candidate",
        "no_payment_on_call_default": payload["no_payment_on_call_default"],
        "approved_campaign_payment_path_can_be_explained": payload["approved_campaign_payment_path_can_be_explained"],
        "example_campaign_payment_paths": payload["example_campaign_payment_paths"],
        "future_agent_payment_handling_deferred": payload["future_agent_payment_handling_deferred"],
        "runtime_requirement": "For now, option selection must not collect payment on the call. The agent may explain the approved campaign payment path if the campaign profile defines it.",
    }


def build_naturalness_constraints(review_import: dict[str, Any]) -> dict[str, Any]:
    payload = review_import["spoken_naturalness_feedback"]
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "review_item": "spoken_naturalness_discourse_markers",
        "sparse_contextual_discourse_markers_candidate": payload["sparse_contextual_discourse_markers_candidate"],
        "random_fillers_allowed": payload["random_fillers_allowed"],
        "example_markers": payload["example_markers"],
        "constraints": payload["constraints"],
        "runtime_requirement": "Do not add random fillers. Treat discourse markers as a future spoken-naturalness rule that must be sparse, context-aware, and blocked in sensitive boundary statements.",
    }


def build_evidence(source_result: dict[str, Any], source_validator: dict[str, Any], review_import: dict[str, Any]) -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "source_validation": source_result["validation"],
        "source_summary": {
            "review_html_created": source_result["summary"]["review_html_created"],
            "requires_human_review_before_next_checkpoint": source_result["summary"]["requires_human_review_before_next_checkpoint"],
            "selected_review_item": source_result["summary"]["selected_review_item"],
        },
        "source_validator_run": source_validator,
        "review_import_path": rel(IMPORT_FILE),
        "review_import_decision": review_import["overall_decision"],
    }


def build_summary(source_validator: dict[str, Any], review_import: dict[str, Any]) -> dict[str, Any]:
    return {
        "review_import_only": True,
        "source_validator_passed": source_validator["passed"],
        "human_review_imported": True,
        "selected_review_item": "guided_option_selection_candidate",
        "imported_review_decision": review_import["overall_decision"],
        "narrow_policy_probe_approved": False,
        "rewrite_required": True,
        "plan_feature_matrix_required": True,
        "campaign_payment_path_required_before_payment_explanation": True,
        "sparse_contextual_discourse_markers_candidate": True,
        "random_fillers_allowed": False,
        "review_html_created": False,
        "recommended_next_checkpoint": NEXT_CHECKPOINT_ID,
        "recommended_next_checkpoint_requires_human_review": False,
        **BOUNDARY_FLAGS,
    }


def render_report(
    summary: dict[str, Any],
    imported: dict[str, Any],
    rewrite: dict[str, Any],
    plan_facts: dict[str, Any],
    payment: dict[str, Any],
    naturalness: dict[str, Any],
) -> str:
    lines = [
        "# PROD-083 English Guided Option Selection Review Import",
        "",
        "`PROD-083` imports Tarik's `PROD-082` guided option selection review feedback.",
        "",
        "This is import-only. It does not patch runtime behavior, response text, classifier reachability, retrieval, payment handling, or spoken naturalness behavior.",
        "",
        "## Imported Decision",
        "",
        "- Decision: needs rewrite before probe",
        "- Narrow policy probe approved: `false`",
        "- Existing examples approved: `false`",
        "- Rewrite required: `true`",
        "- Review HTML created: `false`",
        f"- Recommended next checkpoint: `{summary['recommended_next_checkpoint']}`",
        "",
        "## Rewrite Rules",
        "",
    ]
    for rule in rewrite["rules"]:
        lines.append(f"- {rule}")
    lines.extend(
        [
            "",
            "## Plan Facts",
            "",
            f"- Plan feature matrix required: `{str(plan_facts['plan_feature_matrix_required']).lower()}`",
            f"- Invent plan features allowed: `{str(plan_facts['invent_plan_features_allowed']).lower()}`",
            "- Example placeholders: `$29` -> `feature_x/feature_y/feature_z`; `$59` -> `$29` features plus additional approved features",
            "",
            "## Payment Workflow",
            "",
            f"- No payment on the call by default: `{str(payment['no_payment_on_call_default']).lower()}`",
            f"- Approved campaign payment path can be explained: `{str(payment['approved_campaign_payment_path_can_be_explained']).lower()}`",
            f"- Future agent payment handling deferred: `{str(payment['future_agent_payment_handling_deferred']).lower()}`",
            "- Campaign payment path examples: human callback, approved company-domain email link, approved registration link/form, or paperwork outside the call.",
            "",
            "## Spoken Naturalness",
            "",
            f"- Sparse contextual discourse markers candidate: `{str(naturalness['sparse_contextual_discourse_markers_candidate']).lower()}`",
            f"- Random fillers allowed: `{str(naturalness['random_fillers_allowed']).lower()}`",
            f"- Example markers: `{', '.join(naturalness['example_markers'])}`",
            "",
            "## Imported Notes",
            "",
        ]
    )
    for note in imported["overall_notes"]:
        lines.append(f"- {note}")
    lines.extend(
        [
            "",
            "## Boundary Status",
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
    source_result, source_packet, review_import = load_inputs()
    source_validator = run_source_validator()
    imported = build_import_summary(review_import, source_packet)
    rewrite = build_rewrite_requirements(review_import)
    plan_facts = build_plan_fact_requirements(review_import)
    payment = build_payment_requirements(review_import)
    naturalness = build_naturalness_constraints(review_import)
    evidence = build_evidence(source_result, source_validator, review_import)
    summary = build_summary(source_validator, review_import)
    result = {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "validation": {
            "passed": source_validator["passed"],
            "review_imported": True,
        },
        "summary": summary,
        "outputs": {
            "result": rel(OUT_DIR / "result.json"),
            "report": rel(OUT_DIR / "report.md"),
            "imported_review_summary": rel(OUT_DIR / "imported_review_summary.json"),
            "rewrite_requirements": rel(OUT_DIR / "rewrite_requirements.json"),
            "plan_fact_requirements": rel(OUT_DIR / "plan_fact_requirements.json"),
            "payment_workflow_requirements": rel(OUT_DIR / "payment_workflow_requirements.json"),
            "spoken_naturalness_constraints": rel(OUT_DIR / "spoken_naturalness_constraints.json"),
            "evidence_summary": rel(OUT_DIR / "evidence_summary.json"),
        },
    }
    write_json(OUT_DIR / "imported_review_summary.json", imported)
    write_json(OUT_DIR / "rewrite_requirements.json", rewrite)
    write_json(OUT_DIR / "plan_fact_requirements.json", plan_facts)
    write_json(OUT_DIR / "payment_workflow_requirements.json", payment)
    write_json(OUT_DIR / "spoken_naturalness_constraints.json", naturalness)
    write_json(OUT_DIR / "evidence_summary.json", evidence)
    write_text(OUT_DIR / "report.md", render_report(summary, imported, rewrite, plan_facts, payment, naturalness))
    write_json(OUT_DIR / "result.json", result)
    print(json.dumps({"checkpoint_id": CHECKPOINT_ID, "validation": result["validation"], "summary": summary}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
