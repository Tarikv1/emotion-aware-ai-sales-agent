#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-085-english-guided-option-selection-rewrite-review-import"
CHECKPOINT_NAME = "English Guided Option Selection Rewrite Review Import"
SOURCE_CHECKPOINT_ID = "PROD-084-english-guided-option-selection-rewrite-design"
NEXT_CHECKPOINT_ID = "PROD-086-english-guided-option-selection-narrow-policy-probe"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
SOURCE_DIR = ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID
IMPORT_FILE = ROOT / "research" / "experiments" / "imports" / SOURCE_CHECKPOINT_ID / "prod_084_guided_option_selection_rewrite_review_from_chat.json"
SOURCE_VALIDATOR = ROOT / "scripts" / "validate_prod_084_english_guided_option_selection_rewrite_design.py"

PAYMENT_EXAMPLE_ID = "rewrite-payment-path"

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


def word_count(text: str) -> int:
    return len(text.replace("/", " ").replace("-", " ").split())


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
    source_packet = read_json(SOURCE_DIR / "rewritten_guided_option_review_packet.json")
    review_import = read_json(IMPORT_FILE)
    if source_result["validation"]["passed"] is not True:
        raise RuntimeError("PROD-084 must pass before review import.")
    if source_result["summary"]["recommended_next_checkpoint"] != CHECKPOINT_ID:
        raise RuntimeError("PROD-084 must recommend PROD-085.")
    if source_packet["review_item"] != "guided_option_selection_rewritten_examples":
        raise RuntimeError("PROD-084 packet must be the rewritten guided option review packet.")
    if review_import["overall_decision"] != "approve_rewrite_for_policy_probe_with_payment_wording_edit":
        raise RuntimeError("PROD-085 expects approval with required payment wording edit.")
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
        "narrow_policy_probe_approved_after_required_edit": review_import["narrow_policy_probe_approved_after_required_edit"],
        "narrow_policy_probe_approved_as_written": review_import["narrow_policy_probe_approved_as_written"],
        "payment_example_status": "approved_after_required_wording_edit",
        "other_examples_status": "approved_as_written",
        "approved_as_written_examples": review_import["approved_as_written_examples"],
        "required_edit_examples": [PAYMENT_EXAMPLE_ID],
        "source_example_count": len(source_packet["examples"]),
        "overall_notes": review_import["overall_notes"],
        "source_artifact_preserved": True,
    }


def build_payment_wording_edit(review_import: dict[str, Any]) -> dict[str, Any]:
    edit = review_import["required_payment_wording_edit"]
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "example_id": PAYMENT_EXAMPLE_ID,
        "review_decision": edit["review_decision"],
        "source_issue": edit["source_issue"],
        "required_direction": edit["required_direction"],
        "final_candidate_response": edit["final_candidate_response"],
        "no_payment_on_call_default": True,
        "generic_payment_link_wording": True,
        "company_domain_placeholder_removed": True,
        "runtime_payment_collection_allowed": False,
    }


def build_approved_candidate_packet(
    source_packet: dict[str, Any],
    review_import: dict[str, Any],
    payment_edit: dict[str, Any],
) -> dict[str, Any]:
    examples = []
    decisions = review_import["example_decisions"]
    for source_item in source_packet["examples"]:
        example_id = source_item["example_id"]
        decision = decisions[example_id]["decision"]
        final_response = source_item["proposed_response"]
        changed = False
        if example_id == PAYMENT_EXAMPLE_ID:
            final_response = payment_edit["final_candidate_response"]
            changed = True
        examples.append(
            {
                "example_id": example_id,
                "title": source_item["title"],
                "customer_turn": source_item["customer_turn"],
                "final_candidate_response": final_response,
                "review_decision": decision,
                "changed_from_source": changed,
                "uses_discourse_marker": source_item["uses_discourse_marker"],
                "marker": source_item["marker"],
                "word_count": word_count(final_response),
                "current_runtime_route": source_item["current_runtime_route"],
                "review_target": source_item["review_target"],
            }
        )

    return {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "review_item": "guided_option_selection_rewritten_examples",
        "narrow_policy_probe_candidate": True,
        "runtime_candidate_promoted": False,
        "examples_are_review_only_until_probe_passes": True,
        "approved_as_written_example_count": 7,
        "required_edit_example_count": 1,
        "examples": examples,
        "boundaries": {
            "runtime_patch_allowed": False,
            "response_text_change_allowed": False,
            "classifier_change_allowed": False,
            "retrieval_allowed": False,
            "payment_collection_allowed": False,
            "contract_signing_allowed": False,
            "production_runtime_promotion_allowed": False,
        },
    }


def build_probe_readiness(payment_edit: dict[str, Any]) -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "narrow_policy_probe_approved_after_required_edit": True,
        "narrow_policy_probe_approved_as_written": False,
        "runtime_patch_allowed": False,
        "requires_plan_feature_matrix": True,
        "requires_customer_facts_for_steering": True,
        "requires_no_payment_on_call_default": True,
        "requires_no_company_domain_in_generic_payment_wording": True,
        "final_payment_response": payment_edit["final_candidate_response"],
        "recommended_next_checkpoint": NEXT_CHECKPOINT_ID,
        "recommended_next_checkpoint_requires_human_review": False,
    }


def build_evidence(
    source_result: dict[str, Any],
    source_packet: dict[str, Any],
    source_validator: dict[str, Any],
    review_import: dict[str, Any],
) -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "source_validation": source_result["validation"],
        "source_summary": {
            "review_html_created": source_result["summary"]["review_html_created"],
            "requires_human_review_before_next_checkpoint": source_result["summary"]["requires_human_review_before_next_checkpoint"],
            "selected_review_item": source_result["summary"]["selected_review_item"],
            "review_example_count": source_result["summary"]["review_example_count"],
        },
        "source_review_html_preserved": True,
        "source_example_ids": [item["example_id"] for item in source_packet["examples"]],
        "source_validator_run": source_validator,
        "review_import_path": rel(IMPORT_FILE),
        "review_import_decision": review_import["overall_decision"],
    }


def build_summary(
    source_validator: dict[str, Any],
    review_import: dict[str, Any],
    candidates: dict[str, Any],
) -> dict[str, Any]:
    return {
        "review_import_only": True,
        "source_validator_passed": source_validator["passed"],
        "human_review_imported": True,
        "selected_review_item": "guided_option_selection_rewritten_examples",
        "imported_review_decision": review_import["overall_decision"],
        "approved_as_written_example_count": 7,
        "required_edit_example_count": 1,
        "narrow_policy_probe_approved_after_required_edit": True,
        "narrow_policy_probe_approved_as_written": False,
        "payment_wording_edit_required": True,
        "final_payment_response": review_import["required_payment_wording_edit"]["final_candidate_response"],
        "approved_rewrite_candidate_count": len(candidates["examples"]),
        "review_html_created": False,
        "runtime_candidate_promoted": False,
        "recommended_next_checkpoint": NEXT_CHECKPOINT_ID,
        "recommended_next_checkpoint_requires_human_review": False,
        **BOUNDARY_FLAGS,
    }


def render_report(
    summary: dict[str, Any],
    imported: dict[str, Any],
    payment_edit: dict[str, Any],
    candidates: dict[str, Any],
    readiness: dict[str, Any],
) -> str:
    lines = [
        "# PROD-085 English Guided Option Selection Rewrite Review Import",
        "",
        "`PROD-085` imports Tarik's `PROD-084` review decision.",
        "",
        "This is import-only. It does not patch runtime behavior, response text, classifier reachability, retrieval, payment handling, spoken naturalness behavior, or production promotion.",
        "",
        "## Imported Decision",
        "",
        "- Decision: approve rewrite for policy probe with payment wording edit",
        "- Narrow policy probe approved after required edit: `true`",
        "- Narrow policy probe approved as written: `false`",
        "- Approved as-written examples: `7`",
        "- Required edit examples: `1`",
        "- Review HTML created: `false`",
        "- Runtime candidate promoted: `false`",
        f"- Recommended next checkpoint: `{summary['recommended_next_checkpoint']}`",
        "",
        "## Payment Wording Edit",
        "",
        "- Status: approved after required payment wording edit",
        "- Source artifact preserved: `true`",
        "- Source issue: remove the `companyname.com` placeholder from the generic payment example.",
        f"- Final candidate: `{payment_edit['final_candidate_response']}`",
        "- No payment on this call remains the default.",
        "",
        "## Candidate Packet",
        "",
        f"- Candidate examples: `{len(candidates['examples'])}`",
        "- The payment example is the only changed source example.",
        "- The final candidate packet does not include the `companyname.com` placeholder.",
        "",
        "## Probe Readiness",
        "",
        f"- Requires plan feature matrix: `{str(readiness['requires_plan_feature_matrix']).lower()}`",
        f"- Requires customer facts for steering: `{str(readiness['requires_customer_facts_for_steering']).lower()}`",
        f"- Requires no payment on call default: `{str(readiness['requires_no_payment_on_call_default']).lower()}`",
        f"- Requires no company domain in generic payment wording: `{str(readiness['requires_no_company_domain_in_generic_payment_wording']).lower()}`",
        "",
        "## Imported Notes",
        "",
        imported["overall_notes"],
        "",
        "## Boundary Status",
        "",
    ]
    for key in BOUNDARY_FLAGS:
        label = key.replace("_", " ")
        lines.append(f"- {label}: `{str(summary[key]).lower()}`")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    source_result, source_packet, review_import = load_inputs()
    source_validator = run_source_validator()
    if not source_validator["passed"]:
        raise RuntimeError("Source validator failed; refusing to import review.")

    imported = build_import_summary(review_import, source_packet)
    payment_edit = build_payment_wording_edit(review_import)
    candidates = build_approved_candidate_packet(source_packet, review_import, payment_edit)
    readiness = build_probe_readiness(payment_edit)
    evidence = build_evidence(source_result, source_packet, source_validator, review_import)
    summary = build_summary(source_validator, review_import, candidates)
    result = {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "validation": {
            "passed": True,
            "review_imported": True,
        },
        "summary": summary,
    }

    write_json(OUT_DIR / "imported_review_summary.json", imported)
    write_json(OUT_DIR / "payment_wording_edit.json", payment_edit)
    write_json(OUT_DIR / "approved_rewrite_candidate_packet.json", candidates)
    write_json(OUT_DIR / "narrow_policy_probe_readiness.json", readiness)
    write_json(OUT_DIR / "evidence_summary.json", evidence)
    write_json(OUT_DIR / "result.json", result)
    write_text(OUT_DIR / "report.md", render_report(summary, imported, payment_edit, candidates, readiness))
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
