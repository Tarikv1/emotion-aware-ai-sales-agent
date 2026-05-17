#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-076-english-provider-comparison-review-import"
CHECKPOINT_NAME = "English Provider-Comparison Review Import"
SOURCE_CHECKPOINT_ID = "PROD-075-english-provider-comparison-reachability-review"
NEXT_CHECKPOINT_ID = "PROD-077-english-provider-comparison-narrow-probe-design"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
SOURCE_DIR = ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID
IMPORT_FILE = ROOT / "research" / "experiments" / "imports" / SOURCE_CHECKPOINT_ID / "prod_075_provider_comparison_review_export_from_chat.json"
SOURCE_VALIDATOR = ROOT / "scripts" / "validate_prod_075_english_provider_comparison_reachability_review.py"
SOURCE_VALIDATOR_COMMAND = "python scripts\\validate_prod_075_english_provider_comparison_reachability_review.py"
CURRENT_RESPONSE = "That is fair. We can compare fit and terms without pressure before you decide whether this is worth reviewing."

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
        "command": SOURCE_VALIDATOR_COMMAND,
        "returncode": completed.returncode,
        "stdout_tail": completed.stdout.strip().splitlines()[-5:],
        "stderr_tail": completed.stderr.strip().splitlines()[-5:],
        "passed": completed.returncode == 0 and SOURCE_CHECKPOINT_ID in completed.stdout,
    }


def load_inputs() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    source_result = read_json(SOURCE_DIR / "result.json")
    source_packet = read_json(SOURCE_DIR / "provider_comparison_review_packet.json")
    review_import = read_json(IMPORT_FILE)
    if source_result["validation"]["passed"] is not True:
        raise RuntimeError("PROD-075 must pass before review import.")
    if source_packet["review_item"] != "provider-comparison":
        raise RuntimeError("PROD-075 packet must be for provider-comparison.")
    if review_import["overall_decision"] != "approve_for_narrow_probe_with_brevity_constraint":
        raise RuntimeError("PROD-076 expects Tarik's constrained narrow-probe approval.")
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
        "decision_interpretation": (
            "Approved for a future narrow classifier probe, but not approved as exact wording. "
            "Provider and terms comparison must be grounded in a known comparison target, and future wording should be shorter."
        ),
        "source_current_response": source_packet["current_response"],
        "approved_for_narrow_probe": True,
        "approved_as_exact_response_text": False,
        "notes": review_import["notes"],
        "example_decisions": review_import["example_decisions"],
    }


def build_approved_with_constraints(imported: dict[str, Any]) -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "review_item": "provider-comparison",
        "source_response": CURRENT_RESPONSE,
        "approved_for_narrow_probe": True,
        "approved_as_exact_response_text": False,
        "constraints": [
            "Use only a narrow probe; do not promote broad customer-move classification.",
            "Do not claim provider or terms comparison unless the comparison target is known from the customer turn or approved campaign data.",
            "Keep future response wording shorter than the PROD-075 review text.",
            "Keep no-replacement discipline.",
            "Keep payment collection, contract signing, and production promotion blocked.",
        ],
    }


def build_probe_requirements() -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "review_item": "provider-comparison",
        "requirements": {
            "comparison_target_required": True,
            "generic_provider_or_terms_comparison_allowed": False,
            "narrow_classifier_probe_allowed": True,
            "broad_customer_move_classifier_patch_allowed": False,
            "payment_details_request_allowed": False,
            "contract_signing_allowed": False,
            "known_current_provider_or_terms_signal_required": True,
            "unknown_comparison_target_should_not_route_to_provider_comparison": True,
        },
        "positive_probe_signal_examples": [
            "How is this different from our current provider?",
            "Can you compare this with what we already use?",
            "What would be different versus our current setup?",
        ],
        "negative_probe_signal_examples": [
            "What do you offer?",
            "Is it better?",
            "Can you sign me up?",
            "What does it cost?",
        ],
    }


def build_candidate_constraints() -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "review_item": "provider-comparison",
        "source_response": CURRENT_RESPONSE,
        "brevity_required": True,
        "comparison_grounding_required": True,
        "example_brevity_edit": "No payment details needed.",
        "allowed_candidate_direction": "Shorten the response and keep it as a fit-check bridge, not a factual provider or terms comparison.",
        "candidate_response_not_promoted": True,
        "runtime_response_changed": False,
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
        "selected_review_item": "provider-comparison",
        "imported_review_decision": review_import["overall_decision"],
        "narrow_probe_approved": True,
        "exact_as_written_approval": False,
        "brevity_constraint_required": True,
        "comparison_grounding_required": True,
        "review_html_created": False,
        "recommended_next_checkpoint": NEXT_CHECKPOINT_ID,
        "recommended_next_checkpoint_requires_human_review": False,
        **BOUNDARY_FLAGS,
    }


def render_report(summary: dict[str, Any], imported: dict[str, Any], requirements: dict[str, Any], constraints: dict[str, Any]) -> str:
    lines = [
        "# PROD-076 English Provider-Comparison Review Import",
        "",
        "`PROD-076` imports Tarik's `PROD-075` review feedback for the unreachable English `provider-comparison` response.",
        "",
        "This is an import-only checkpoint. It does not patch runtime behavior, response text, classifier reachability, or retrieval.",
        "",
        "## Imported Decision",
        "",
        "- Decision: approve for narrow probe with brevity constraint",
        "- Interpretation: not approved as exact wording",
        "- Comparison target required: `true`",
        "- Narrow probe approved: `true`",
        "- Exact as-written approval: `false`",
        "- Review HTML created: `false`",
        f"- Recommended next checkpoint: `{summary['recommended_next_checkpoint']}`",
        "",
        "## Review Notes",
        "",
    ]
    for note in imported["notes"]:
        lines.append(f"- {note}")
    lines.extend(
        [
            "",
            "## Probe Requirements",
            "",
            f"- Comparison target required: `{str(requirements['requirements']['comparison_target_required']).lower()}`",
            f"- Generic provider or terms comparison allowed: `{str(requirements['requirements']['generic_provider_or_terms_comparison_allowed']).lower()}`",
            f"- Broad customer-move classifier patch allowed: `{str(requirements['requirements']['broad_customer_move_classifier_patch_allowed']).lower()}`",
            f"- Payment details request allowed: `{str(requirements['requirements']['payment_details_request_allowed']).lower()}`",
            "",
            "## Candidate Response Constraints",
            "",
            f"- Brevity required: `{str(constraints['brevity_required']).lower()}`",
            f"- Example brevity edit: {constraints['example_brevity_edit']}",
            f"- Candidate response promoted: `{str(not constraints['candidate_response_not_promoted']).lower()}`",
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
    approved = build_approved_with_constraints(imported)
    requirements = build_probe_requirements()
    constraints = build_candidate_constraints()
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
            "approved_with_constraints": rel(OUT_DIR / "approved_with_constraints.json"),
            "narrow_probe_requirements": rel(OUT_DIR / "narrow_probe_requirements.json"),
            "candidate_response_constraints": rel(OUT_DIR / "candidate_response_constraints.json"),
            "evidence_summary": rel(OUT_DIR / "evidence_summary.json"),
        },
    }
    write_json(OUT_DIR / "imported_review_summary.json", imported)
    write_json(OUT_DIR / "approved_with_constraints.json", approved)
    write_json(OUT_DIR / "narrow_probe_requirements.json", requirements)
    write_json(OUT_DIR / "candidate_response_constraints.json", constraints)
    write_json(OUT_DIR / "evidence_summary.json", evidence)
    write_text(OUT_DIR / "report.md", render_report(summary, imported, requirements, constraints))
    write_json(OUT_DIR / "result.json", result)
    print(json.dumps({"checkpoint_id": CHECKPOINT_ID, "validation": result["validation"], "summary": summary}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
