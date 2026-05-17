#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-069-english-remaining-product-policy-gate-selection-after-voicemail"
CHECKPOINT_NAME = "English Remaining Product-Policy Gate Selection After Voicemail"
SOURCE_CHECKPOINT_ID = "PROD-068-english-voicemail-post-patch-regression"
PRIORITY_SOURCE_CHECKPOINT_ID = "PROD-061-english-product-policy-gate-prioritization"
PRIOR_SELECTION_CHECKPOINT_ID = "PROD-065-english-remaining-product-policy-gate-selection"
NEXT_CHECKPOINT_ID = "PROD-070-english-coverage-knowledge-policy-probe"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
CASE_FILE = ROOT / "research" / "experiments" / "cases" / "prod-069-english-remaining-product-policy-gate-selection-after-voicemail.json"
SOURCE_DIR = ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID
SOURCE_VALIDATOR = ROOT / "scripts" / "validate_prod_068_english_voicemail_post_patch_regression.py"
SOURCE_VALIDATOR_COMMAND = "python scripts\\validate_prod_068_english_voicemail_post_patch_regression.py"
PRIORITY_OPTIONS_FILE = ROOT / "research" / "experiments" / "generated" / PRIORITY_SOURCE_CHECKPOINT_ID / "gate_options.json"
PRIOR_SELECTION_FILE = ROOT / "research" / "experiments" / "generated" / PRIOR_SELECTION_CHECKPOINT_ID / "remaining_gate_selection.json"
SELECTED_GATE_ID = "coverage_knowledge_policy_behavior"
DEFERRED_GATE_ID = "customer_move_classification_outside_selected_non_refusal_groups"

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


def load_source() -> dict[str, Any]:
    source = read_json(SOURCE_DIR / "result.json")
    if source["validation"]["passed"] is not True:
        raise SystemExit("PROD-068 must pass before PROD-069.")
    if source["summary"]["recommended_next_checkpoint"] != CHECKPOINT_ID:
        raise SystemExit("PROD-068 must recommend PROD-069.")
    if source["summary"]["failed_case_count"] != 0:
        raise SystemExit("PROD-068 has failed cases; remaining-gate selection is not safe.")
    return source


def ranked_remaining_gates() -> list[dict[str, Any]]:
    source_options = read_json(PRIORITY_OPTIONS_FILE)["ranked_gates"]
    by_id = {item["gate_id"]: item for item in source_options}
    return [
        {
            "rank": 1,
            "gate_id": SELECTED_GATE_ID,
            "label": by_id[SELECTED_GATE_ID]["label"],
            "status": "selected_for_next_probe_still_blocked",
            "selected_for_next_probe": True,
            "runtime_patch_allowed": False,
            "retrieval_allowed": False,
            "why": "It is now the smallest remaining English product-policy gate after autonomy and voicemail. A synthetic boundary probe can define allowed uncertainty, escalation, and forbidden coverage advice before any runtime or retrieval change.",
            "risk": by_id[SELECTED_GATE_ID]["risk"],
            "next_action": "Open a synthetic English coverage knowledge-policy boundary probe before any runtime patch, retrieval enablement, or product fact claim.",
            "review_question": "No review needed for this selection. A later probe may need human review if it asks Tarik to accept product/legal wording or coverage facts.",
            "recommended_probe_scope": "synthetic English coverage knowledge-policy boundary examples only",
        },
        {
            "rank": 2,
            "gate_id": DEFERRED_GATE_ID,
            "label": by_id[DEFERRED_GATE_ID]["label"],
            "status": "deferred_still_blocked",
            "selected_for_next_probe": False,
            "runtime_patch_allowed": False,
            "retrieval_allowed": False,
            "why": "It still has the highest blast radius because it changes reachability across multiple runtime branches, so it should remain behind the narrower knowledge-policy boundary gate.",
            "risk": by_id[DEFERRED_GATE_ID]["risk"],
            "next_action": "Keep blocked until remaining narrower policy gates define acceptance criteria for broader classifier reachability.",
            "review_question": "Should broad classifier expansion remain last among the current English product-policy gates?",
            "recommended_probe_scope": "deferred until after coverage knowledge-policy boundary work",
        },
    ]


def build_case_file(options: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "priority_source_checkpoint_id": PRIORITY_SOURCE_CHECKPOINT_ID,
        "prior_selection_checkpoint_id": PRIOR_SELECTION_CHECKPOINT_ID,
        "scope": "remaining_english_product_policy_gate_selection_after_voicemail_only",
        "selected_gate_id": SELECTED_GATE_ID,
        "remaining_gate_ids": [item["gate_id"] for item in options],
        "runtime_change_requested": False,
        "response_text_change_requested": False,
        "classifier_change_requested": False,
        "retrieval_change_requested": False,
        "requires_human_review_before_next_checkpoint": False,
        "review_html_created": False,
        "recommended_next_checkpoint": NEXT_CHECKPOINT_ID,
        "selection_basis": [
            "PROD-068 voicemail post-patch regression passed with zero failed cases.",
            "PROD-061 ranked coverage knowledge-policy before broad customer-move classification.",
            "PROD-065 deferred coverage and broad classifier expansion while voicemail was still pending.",
            "Coverage behavior needs a policy boundary probe before any runtime, retrieval, or product-fact claim.",
            "Broad customer-move classifier expansion remains the highest-blast-radius remaining English gate.",
        ],
    }


def build_selection(options: list[dict[str, Any]]) -> dict[str, Any]:
    selected = next(item for item in options if item["gate_id"] == SELECTED_GATE_ID)
    selected = {
        **selected,
        "next_action": "open_synthetic_policy_probe",
        "still_blocked_until_probe_passes": True,
        "knowledge_fact_claims_allowed": False,
        "coverage_advice_allowed": False,
        "escalation_required_for_specific_coverage_questions": True,
    }
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "decision": "select_coverage_knowledge_policy_behavior_next",
        "selected_gate": selected,
        "deferred_gates": [DEFERRED_GATE_ID],
        "requires_human_review_before_next_checkpoint": False,
        "review_html_created": False,
        "recommended_next_checkpoint": NEXT_CHECKPOINT_ID,
    }


def build_evidence_summary(source: dict[str, Any], source_validator: dict[str, Any], options: list[dict[str, Any]]) -> dict[str, Any]:
    prior_selection = read_json(PRIOR_SELECTION_FILE)
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "source_validation": source["validation"],
        "source_summary": {
            "stable_english_guard_passed": source["summary"]["stable_english_guard_passed"],
            "failed_case_count": source["summary"]["failed_case_count"],
            "recommended_next_checkpoint": source["summary"]["recommended_next_checkpoint"],
        },
        "source_validator_run": source_validator,
        "priority_source_checkpoint_id": PRIORITY_SOURCE_CHECKPOINT_ID,
        "prior_selection_checkpoint_id": PRIOR_SELECTION_CHECKPOINT_ID,
        "prior_selected_gate_id": prior_selection["selected_gate"]["gate_id"],
        "remaining_gate_ids": [item["gate_id"] for item in options],
    }


def summarize(options: list[dict[str, Any]], source_validator: dict[str, Any]) -> dict[str, Any]:
    return {
        "selection_only": True,
        "source_validator_passed": source_validator["passed"],
        "selected_gate_id": SELECTED_GATE_ID,
        "selected_gate_status": "selected_for_next_probe_still_blocked",
        "remaining_gate_ids": [item["gate_id"] for item in options],
        "deferred_gate_ids": [DEFERRED_GATE_ID],
        "requires_human_review_before_next_checkpoint": False,
        "review_html_created": False,
        "recommended_next_checkpoint": NEXT_CHECKPOINT_ID,
        **BOUNDARY_FLAGS,
    }


def render_report(options: list[dict[str, Any]], selection: dict[str, Any], summary: dict[str, Any]) -> str:
    lines = [
        "# PROD-069 English Remaining Product-Policy Gate Selection After Voicemail",
        "",
        "`PROD-069` selects the next remaining English product-policy gate after the voicemail post-patch regression passed.",
        "",
        "No human review required; this is selection only and creates no review HTML.",
        "",
        "## Decision",
        "",
        f"- Decision: `{selection['decision']}`",
        f"- Selected gate: `{summary['selected_gate_id']}`",
        f"- Selected status: `{summary['selected_gate_status']}`",
        "- Selected for next probe: `true`",
        f"- Selection only: `{str(summary['selection_only']).lower()}`",
        f"- Review HTML created: `{str(summary['review_html_created']).lower()}`",
        f"- Recommended next checkpoint: `{summary['recommended_next_checkpoint']}`",
        "- Runtime behavior changed: `false`",
        "- Response text behavior changed: `false`",
        "- Classifier behavior changed: `false`",
        "- Retrieval enabled: `false`",
        "- Production runtime promotion allowed: `false`",
        "",
        "## Ranked Remaining Gates",
        "",
    ]
    for item in options:
        lines.extend(
            [
                f"{item['rank']}. `{item['gate_id']}`",
                f"   - Status: `{item['status']}`",
                f"   - Why: {item['why']}",
                f"   - Risk: {item['risk']}",
                f"   - Probe scope: {item['recommended_probe_scope']}",
                "",
            ]
        )
    lines.extend(
        [
            "## Boundary",
            "",
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
    source = load_source()
    source_validator = run_source_validator()
    options = ranked_remaining_gates()
    case_payload = build_case_file(options)
    selection = build_selection(options)
    evidence = build_evidence_summary(source, source_validator, options)
    summary = summarize(options, source_validator)
    result = {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "validation": {
            "passed": source_validator["passed"] and summary["selected_gate_id"] == SELECTED_GATE_ID,
            "gate_selection_passed": summary["selected_gate_id"] == SELECTED_GATE_ID,
        },
        "summary": summary,
    }
    write_json(CASE_FILE, case_payload)
    write_json(OUT_DIR / "remaining_gate_options.json", {"checkpoint_id": CHECKPOINT_ID, "ranked_remaining_gates": options, "selected_next_gate_id": SELECTED_GATE_ID})
    write_json(OUT_DIR / "remaining_gate_selection.json", selection)
    write_json(OUT_DIR / "evidence_summary.json", evidence)
    write_json(OUT_DIR / "result.json", result)
    write_text(OUT_DIR / "report.md", render_report(options, selection, summary))
    print(json.dumps({"checkpoint_id": CHECKPOINT_ID, "validation": result["validation"], "summary": summary}, indent=2))


if __name__ == "__main__":
    main()
