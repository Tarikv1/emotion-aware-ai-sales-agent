#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-098-english-recommendation-roleplay-review-import"
CHECKPOINT_NAME = "English Recommendation Roleplay Review Import"
SOURCE_CHECKPOINT_ID = "PROD-097-english-customer-move-remaining-slice-selection-after-process-clarity"
NEXT_CHECKPOINT_ID = "PROD-099-english-recommendation-roleplay-narrow-policy-probe"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
SOURCE_DIR = ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID
IMPORT_FILE = ROOT / "research" / "experiments" / "imports" / SOURCE_CHECKPOINT_ID / "prod_097_recommendation_roleplay_review_from_chat.json"
SOURCE_VALIDATOR = ROOT / "scripts" / "validate_prod_097_english_customer_move_remaining_slice_selection_after_process_clarity.py"

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


def load_inputs() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    source_result = read_json(SOURCE_DIR / "result.json")
    source_packet = read_json(SOURCE_DIR / "review_packet.json")
    source_examples = read_json(SOURCE_DIR / "review_examples.json")
    review_import = read_json(IMPORT_FILE)
    if source_result["validation"]["passed"] is not True:
        raise RuntimeError("PROD-097 must pass before review import.")
    if source_result["summary"]["recommended_next_checkpoint"] != CHECKPOINT_ID:
        raise RuntimeError("PROD-097 must recommend PROD-098.")
    if source_packet["review_type"] != "recommendation_roleplay_boundary":
        raise RuntimeError("PROD-097 packet must be recommendation-roleplay review.")
    if review_import["overall_decision"] != "approve_for_policy_probe_with_two_wording_edits":
        raise RuntimeError("PROD-098 expects approval with two wording edits.")
    return source_result, source_packet, source_examples, review_import


def build_import_summary(review_import: dict[str, Any], source_examples: dict[str, Any]) -> dict[str, Any]:
    edited_ids = list(review_import["required_wording_edits"].keys())
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "review_item": review_import["review_item"],
        "review_status": review_import["review_status"],
        "reviewer": review_import["reviewer"],
        "review_date": review_import["review_date"],
        "overall_decision": review_import["overall_decision"],
        "narrow_policy_probe_approved_after_required_edits": review_import["narrow_policy_probe_approved_after_required_edits"],
        "narrow_policy_probe_approved_as_written": review_import["narrow_policy_probe_approved_as_written"],
        "approved_example_count": len(review_import["approved_example_ids"]),
        "required_edit_example_count": len(edited_ids),
        "edited_example_ids": edited_ids,
        "source_example_count": source_examples["example_count"],
        "overall_notes": review_import["overall_notes"],
        "source_artifact_preserved": True,
    }


def build_wording_edits(review_import: dict[str, Any]) -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "edits": review_import["required_wording_edits"],
        "edit_count": len(review_import["required_wording_edits"]),
        "example_3_less_pushy_option_language": True,
        "example_5_uses_but_connector": True,
    }


def build_approved_candidate_packet(source_examples: dict[str, Any], review_import: dict[str, Any]) -> dict[str, Any]:
    edits = review_import["required_wording_edits"]
    examples = []
    for source_item in source_examples["examples"]:
        example_id = source_item["example_id"]
        edited = example_id in edits
        final_response = edits[example_id]["final_candidate_response"] if edited else source_item["candidate_agent_response"]
        examples.append(
            {
                "example_id": example_id,
                "customer_turn": source_item["customer_turn"],
                "final_candidate_response": final_response,
                "review_decision": "approved_after_required_wording_edit" if edited else "approved_as_written",
                "changed_from_source": edited,
                "risk": source_item["risk"],
                "review_question": source_item["review_question"],
                "word_count": word_count(final_response),
            }
        )
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "review_item": "recommendation_roleplay_boundary",
        "narrow_policy_probe_candidate": True,
        "runtime_candidate_promoted": False,
        "examples_are_review_only_until_probe_passes": True,
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


def build_probe_readiness(review_import: dict[str, Any]) -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "narrow_policy_probe_approved_after_required_edits": True,
        "narrow_policy_probe_approved_as_written": False,
        "runtime_patch_allowed": False,
        "requires_customer_facts_for_recommendation": True,
        "requires_agency_preservation": True,
        "requires_no_agent_decides_for_customer": True,
        "requires_no_value_guarantee": True,
        "requires_no_payment_collection": True,
        "requires_no_contract_signing": True,
        "edited_examples": review_import["required_wording_edits"],
        "recommended_next_checkpoint": NEXT_CHECKPOINT_ID,
        "recommended_next_checkpoint_requires_human_review": False,
    }


def build_evidence(
    source_result: dict[str, Any],
    source_packet: dict[str, Any],
    source_examples: dict[str, Any],
    source_validator: dict[str, Any],
    review_import: dict[str, Any],
) -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "source_validation": source_result["validation"],
        "source_summary": source_result["summary"],
        "source_review_html_preserved": True,
        "source_review_type": source_packet["review_type"],
        "source_example_ids": [item["example_id"] for item in source_examples["examples"]],
        "source_validator_run": source_validator,
        "review_import_path": rel(IMPORT_FILE),
        "review_import_decision": review_import["overall_decision"],
    }


def build_summary(source_validator: dict[str, Any], review_import: dict[str, Any], candidates: dict[str, Any]) -> dict[str, Any]:
    return {
        "review_import_only": True,
        "source_validator_passed": source_validator["passed"],
        "human_review_imported": True,
        "selected_review_item": "recommendation_roleplay_boundary",
        "imported_review_decision": review_import["overall_decision"],
        "approved_example_count": len(candidates["examples"]),
        "required_edit_example_count": len(review_import["required_wording_edits"]),
        "narrow_policy_probe_approved_after_required_edits": True,
        "narrow_policy_probe_approved_as_written": False,
        "review_html_created": False,
        "runtime_candidate_promoted": False,
        "recommended_next_checkpoint": NEXT_CHECKPOINT_ID,
        "recommended_next_checkpoint_requires_human_review": False,
        **BOUNDARY_FLAGS,
    }


def render_report(
    summary: dict[str, Any],
    imported: dict[str, Any],
    edits: dict[str, Any],
    candidates: dict[str, Any],
    readiness: dict[str, Any],
) -> str:
    lines = [
        "# PROD-098 English Recommendation Roleplay Review Import",
        "",
        "`PROD-098` imports Tarik's `PROD-097` recommendation-roleplay review.",
        "",
        "This is import-only. It does not patch runtime behavior, response text, classifier reachability, retrieval, payment handling, spoken naturalness behavior, or production promotion.",
        "",
        "## Imported Decision",
        "",
        "- Decision: approve for policy probe with two wording edits",
        "- Narrow policy probe approved after required edits: `true`",
        "- Narrow policy probe approved as written: `false`",
        f"- Approved examples: `{summary['approved_example_count']}`",
        f"- Required edit examples: `{summary['required_edit_example_count']}`",
        "- Review HTML created: `false`",
        "- Runtime candidate promoted: `false`",
        f"- Recommended next checkpoint: `{summary['recommended_next_checkpoint']}`",
        "",
        "## Required Wording Edits",
        "",
        f"- `prod-097-direct-recommendation`: `{edits['edits']['prod-097-direct-recommendation']['final_candidate_response']}`",
        f"- `prod-097-decide-for-me-control`: `{edits['edits']['prod-097-decide-for-me-control']['final_candidate_response']}`",
        "",
        "## Probe Readiness",
        "",
        f"- Requires customer facts for recommendation: `{str(readiness['requires_customer_facts_for_recommendation']).lower()}`",
        f"- Requires agency preservation: `{str(readiness['requires_agency_preservation']).lower()}`",
        f"- Requires no agent decides for customer: `{str(readiness['requires_no_agent_decides_for_customer']).lower()}`",
        f"- Requires no value guarantee: `{str(readiness['requires_no_value_guarantee']).lower()}`",
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
    source_result, source_packet, source_examples, review_import = load_inputs()
    source_validator = run_source_validator()
    if not source_validator["passed"]:
        raise RuntimeError("Source validator failed; refusing to import review.")

    imported = build_import_summary(review_import, source_examples)
    edits = build_wording_edits(review_import)
    candidates = build_approved_candidate_packet(source_examples, review_import)
    readiness = build_probe_readiness(review_import)
    evidence = build_evidence(source_result, source_packet, source_examples, source_validator, review_import)
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
    write_json(OUT_DIR / "wording_edits.json", edits)
    write_json(OUT_DIR / "approved_recommendation_roleplay_candidate_packet.json", candidates)
    write_json(OUT_DIR / "narrow_policy_probe_readiness.json", readiness)
    write_json(OUT_DIR / "evidence_summary.json", evidence)
    write_json(OUT_DIR / "result.json", result)
    write_text(OUT_DIR / "report.md", render_report(summary, imported, edits, candidates, readiness))
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
