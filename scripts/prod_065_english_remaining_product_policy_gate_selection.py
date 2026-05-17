#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-065-english-remaining-product-policy-gate-selection"
CHECKPOINT_NAME = "English Remaining Product-Policy Gate Selection"
SOURCE_CHECKPOINT_ID = "PROD-064-english-autonomy-post-patch-multi-turn-regression"
PRIORITY_SOURCE_CHECKPOINT_ID = "PROD-061-english-product-policy-gate-prioritization"
NEXT_CHECKPOINT_ID = "PROD-066-english-voicemail-action-only-policy-probe"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
CASE_FILE = ROOT / "research" / "experiments" / "cases" / "prod-065-english-remaining-product-policy-gate-selection.json"
SOURCE_DIR = ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID
SOURCE_VALIDATOR = ROOT / "scripts" / "validate_prod_064_english_autonomy_post_patch_multi_turn_regression.py"
SOURCE_VALIDATOR_COMMAND = "python scripts\\validate_prod_064_english_autonomy_post_patch_multi_turn_regression.py"
PRIORITY_OPTIONS_FILE = ROOT / "research" / "experiments" / "generated" / PRIORITY_SOURCE_CHECKPOINT_ID / "gate_options.json"
VOICEMAIL_CANDIDATES_FILE = ROOT / "research" / "experiments" / "generated" / "PROD-053D-english-review-import" / "runtime_patch_candidates.json"
SELECTED_GATE_ID = "voicemail_action_only_behavior"

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


def load_source() -> dict[str, Any]:
    source = read_json(SOURCE_DIR / "result.json")
    if source["validation"]["passed"] is not True:
        raise SystemExit("PROD-064 must pass before PROD-065.")
    if source["summary"]["recommended_next_checkpoint"] != CHECKPOINT_ID:
        raise SystemExit("PROD-064 must recommend PROD-065.")
    if source["summary"]["failed_case_count"] != 0:
        raise SystemExit("PROD-064 has failed cases; remaining-gate selection is not safe.")
    return source


def load_voicemail_candidate() -> dict[str, Any]:
    candidates = read_json(VOICEMAIL_CANDIDATES_FILE)["items"]
    return next(item for item in candidates if item["case_id"] == "prod-053c-voicemail")


def ranked_remaining_gates() -> list[dict[str, Any]]:
    source_options = read_json(PRIORITY_OPTIONS_FILE)["ranked_gates"]
    by_id = {item["gate_id"]: item for item in source_options}
    return [
        {
            "rank": 1,
            "gate_id": "voicemail_action_only_behavior",
            "label": by_id["voicemail_action_only_behavior"]["label"],
            "status": "selected_for_next_probe_still_blocked",
            "selected_for_next_probe": True,
            "runtime_patch_allowed": False,
            "why": "It is the smallest remaining English product-policy gate after autonomy: one known voicemail case, explicit owner feedback, and no regulated knowledge or broad classifier expansion.",
            "risk": by_id["voicemail_action_only_behavior"]["risk"],
            "next_action": "Open a synthetic English voicemail action-only policy probe before any runtime patch.",
            "review_question": "No new review needed unless the probe finds ambiguity in action-only voicemail behavior.",
        },
        {
            "rank": 2,
            "gate_id": "coverage_knowledge_policy_behavior",
            "label": by_id["coverage_knowledge_policy_behavior"]["label"],
            "status": "deferred_still_blocked",
            "selected_for_next_probe": False,
            "runtime_patch_allowed": False,
            "why": "It involves regulated coverage or eligibility implications and needs product/legal knowledge boundaries before runtime work.",
            "risk": by_id["coverage_knowledge_policy_behavior"]["risk"],
            "next_action": "Keep blocked until a separate knowledge-policy checkpoint defines allowed facts, uncertainty handling, and escalation.",
            "review_question": "Should coverage behavior wait behind the lower-blast-radius voicemail gate?",
        },
        {
            "rank": 3,
            "gate_id": "customer_move_classification_outside_selected_non_refusal_groups",
            "label": by_id["customer_move_classification_outside_selected_non_refusal_groups"]["label"],
            "status": "deferred_still_blocked",
            "selected_for_next_probe": False,
            "runtime_patch_allowed": False,
            "why": "It has the highest blast radius because it changes reachability across multiple runtime branches.",
            "risk": by_id["customer_move_classification_outside_selected_non_refusal_groups"]["risk"],
            "next_action": "Keep blocked until smaller policy gates provide clearer acceptance criteria for broader classifier reachability.",
            "review_question": "Should broad classifier expansion remain last among the current English product-policy gates?",
        },
    ]


def build_case_file(options: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "priority_source_checkpoint_id": PRIORITY_SOURCE_CHECKPOINT_ID,
        "scope": "remaining_english_product_policy_gate_selection_only",
        "selected_gate_id": SELECTED_GATE_ID,
        "remaining_gate_ids": [item["gate_id"] for item in options],
        "runtime_change_requested": False,
        "response_text_change_requested": False,
        "requires_human_review_before_next_checkpoint": False,
        "recommended_next_checkpoint": NEXT_CHECKPOINT_ID,
        "selection_basis": [
            "PROD-064 autonomy patch regression passed with zero failed cases.",
            "PROD-061 ranked voicemail second after autonomy.",
            "PROD-053D contains explicit owner feedback that voicemail should log/retry without speaking to voicemail.",
            "Coverage behavior carries regulated knowledge risk and broad classifier expansion carries larger blast radius.",
        ],
    }


def build_selection(options: list[dict[str, Any]], voicemail_candidate: dict[str, Any]) -> dict[str, Any]:
    selected = next(item for item in options if item["gate_id"] == SELECTED_GATE_ID)
    selected = {
        **selected,
        "next_action": "open_synthetic_policy_probe",
        "still_blocked_until_probe_passes": True,
        "recommended_probe_scope": "synthetic English voicemail action-only policy examples only",
        "source_owner_feedback": voicemail_candidate["owner_notes"],
        "candidate_type": voicemail_candidate["candidate_type"],
        "candidate_action": voicemail_candidate["candidate_action"],
    }
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "decision": "select_voicemail_action_only_behavior_next",
        "selected_gate": selected,
        "deferred_gates": [
            "coverage_knowledge_policy_behavior",
            "customer_move_classification_outside_selected_non_refusal_groups",
        ],
        "requires_human_review_before_next_checkpoint": False,
        "recommended_next_checkpoint": NEXT_CHECKPOINT_ID,
    }


def build_evidence_summary(source: dict[str, Any], source_validator: dict[str, Any], voicemail_candidate: dict[str, Any]) -> dict[str, Any]:
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
        "voicemail_candidate": {
            "case_id": voicemail_candidate["case_id"],
            "candidate_type": voicemail_candidate["candidate_type"],
            "candidate_response": voicemail_candidate["candidate_response"],
            "candidate_action": voicemail_candidate["candidate_action"],
            "owner_notes": voicemail_candidate["owner_notes"],
            "requires_design_decision": voicemail_candidate["requires_design_decision"],
        },
    }


def summarize(options: list[dict[str, Any]], source_validator: dict[str, Any]) -> dict[str, Any]:
    return {
        "selection_only": True,
        "source_validator_passed": source_validator["passed"],
        "selected_gate_id": SELECTED_GATE_ID,
        "selected_gate_status": "selected_for_next_probe_still_blocked",
        "remaining_gate_ids": [item["gate_id"] for item in options],
        "deferred_gate_ids": [
            "coverage_knowledge_policy_behavior",
            "customer_move_classification_outside_selected_non_refusal_groups",
        ],
        "requires_human_review_before_next_checkpoint": False,
        "recommended_next_checkpoint": NEXT_CHECKPOINT_ID,
        **BOUNDARY_FLAGS,
    }


def render_report(options: list[dict[str, Any]], selection: dict[str, Any], summary: dict[str, Any]) -> str:
    lines = [
        "# PROD-065 English Remaining Product-Policy Gate Selection",
        "",
        "`PROD-065` selects the next remaining English product-policy gate after the autonomy patch regression passed.",
        "",
        "No human review required; this is selection only and creates no review HTML.",
        "",
        "## Decision",
        "",
        f"- Decision: `{selection['decision']}`",
        f"- Selected gate: `{summary['selected_gate_id']}`",
        f"- Selected status: `{summary['selected_gate_status']}`",
        f"- Selection only: `{str(summary['selection_only']).lower()}`",
        f"- Recommended next checkpoint: `{summary['recommended_next_checkpoint']}`",
        "- Runtime behavior changed: `false`",
        "- Response text behavior changed: `false`",
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
    voicemail_candidate = load_voicemail_candidate()
    options = ranked_remaining_gates()
    case_payload = build_case_file(options)
    selection = build_selection(options, voicemail_candidate)
    evidence = build_evidence_summary(source, source_validator, voicemail_candidate)
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
