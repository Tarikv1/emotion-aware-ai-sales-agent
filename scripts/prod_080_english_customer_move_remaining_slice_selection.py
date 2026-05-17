#!/usr/bin/env python3
from __future__ import annotations

import ast
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-080-english-customer-move-remaining-slice-selection"
CHECKPOINT_NAME = "English Customer-Move Remaining Slice Selection"
SOURCE_CHECKPOINT_ID = "PROD-079-english-provider-comparison-post-patch-regression"
NEXT_CHECKPOINT_ID = "PROD-081-english-unknown-runtime-signal-subtype-inventory"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
SOURCE_DIR = ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID
PROD_073_DIR = ROOT / "research" / "experiments" / "generated" / "PROD-073-english-customer-move-classification-gate-decision"
SOURCE_VALIDATOR = ROOT / "scripts" / "validate_prod_079_english_provider_comparison_post_patch_regression.py"
RUNTIME_PATH = ROOT / "runtime" / "core" / "realtime_turns.py"

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


def load_source() -> tuple[dict[str, Any], dict[str, Any]]:
    source_result = read_json(SOURCE_DIR / "result.json")
    slice_plan = read_json(PROD_073_DIR / "classifier_slice_plan.json")
    if source_result["validation"]["passed"] is not True:
        raise RuntimeError("PROD-079 must pass before PROD-080.")
    if source_result["summary"]["recommended_next_checkpoint"] != CHECKPOINT_ID:
        raise RuntimeError("PROD-079 must recommend PROD-080.")
    return source_result, slice_plan


def extract_constant_strings(node: ast.AST) -> set[str]:
    values: set[str] = set()
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        values.add(node.value)
    if isinstance(node, ast.IfExp):
        values.update(extract_constant_strings(node.body))
        values.update(extract_constant_strings(node.orelse))
    return values


def extract_english_response_types(localized: ast.Dict) -> set[str]:
    for key, value in zip(localized.keys, localized.values):
        if isinstance(key, ast.Constant) and key.value == "en" and isinstance(value, ast.Dict):
            return {
                item_key.value
                for item_key in value.keys
                if isinstance(item_key, ast.Constant) and isinstance(item_key.value, str)
            }
    return set()


def build_reachability_snapshot() -> dict[str, Any]:
    tree = ast.parse(RUNTIME_PATH.read_text(encoding="utf-8"))
    english_response_types: set[str] = set()
    reachable_sales_difficulties: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "LOCALIZED_RESPONSES" and isinstance(node.value, ast.Dict):
                    english_response_types.update(extract_english_response_types(node.value))
                if isinstance(target, ast.Name) and target.id == "sales_difficulty":
                    reachable_sales_difficulties.update(extract_constant_strings(node.value))
    unreachable = sorted(english_response_types - reachable_sales_difficulties)
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "runtime_path": rel(RUNTIME_PATH),
        "english_localized_response_type_count": len(english_response_types),
        "reachable_sales_difficulty_count": len(reachable_sales_difficulties),
        "unreachable_localized_response_types": unreachable,
        "reachable_sales_difficulties": sorted(reachable_sales_difficulties),
        "provider_comparison_reachable": "provider-comparison" in reachable_sales_difficulties,
    }


def build_selection(snapshot: dict[str, Any], slice_plan: dict[str, Any]) -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "decision": "select_unknown_runtime_signal_subtypes_inventory_next",
        "provider_comparison_slice_closed": snapshot["provider_comparison_reachable"],
        "unreachable_existing_response_types_remaining": bool(snapshot["unreachable_localized_response_types"]),
        "selected_next_slice": "unknown_runtime_signal_subtypes",
        "why": "After provider-comparison became reachable and post-patch regression passed, the remaining broad customer-move gate should move to inventorying unknown-runtime-signal subtypes rather than broad reachability expansion.",
        "protected_boundary_controls_required": True,
        "runtime_patch_allowed": False,
        "response_text_change_allowed": False,
        "classifier_change_allowed": False,
        "review_html_created": False,
        "recommended_next_checkpoint": NEXT_CHECKPOINT_ID,
        "available_candidate_slices": slice_plan["candidate_slices"],
    }


def build_evidence(source_result: dict[str, Any], source_validator: dict[str, Any]) -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "source_validation": source_result["validation"],
        "source_summary": {
            "failed_regression_case_count": source_result["summary"]["failed_regression_case_count"],
            "stable_english_guard_passed": source_result["summary"]["stable_english_guard_passed"],
            "recommended_next_checkpoint": source_result["summary"]["recommended_next_checkpoint"],
        },
        "source_validator_run": source_validator,
    }


def summarize(selection: dict[str, Any], snapshot: dict[str, Any], source_validator: dict[str, Any]) -> dict[str, Any]:
    return {
        "selection_only": True,
        "source_validator_passed": source_validator["passed"],
        "provider_comparison_slice_closed": selection["provider_comparison_slice_closed"],
        "unreachable_existing_response_types_remaining": selection["unreachable_existing_response_types_remaining"],
        "selected_next_slice": selection["selected_next_slice"],
        "protected_boundary_controls_required": selection["protected_boundary_controls_required"],
        "requires_human_review_before_next_checkpoint": False,
        "review_html_created": False,
        "recommended_next_checkpoint": selection["recommended_next_checkpoint"],
        "reachable_sales_difficulty_count": snapshot["reachable_sales_difficulty_count"],
        **BOUNDARY_FLAGS,
    }


def render_report(summary: dict[str, Any], selection: dict[str, Any], snapshot: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# PROD-080 English Customer-Move Remaining Slice Selection",
            "",
            "`PROD-080` selects the next remaining English customer-move classifier slice after the provider-comparison patch passed regression.",
            "",
            "This is selection-only. It changes no runtime behavior, response text, classifier reachability, or retrieval.",
            "",
            "## Decision",
            "",
            "- Decision: `select_unknown_runtime_signal_subtypes_inventory_next`",
            f"- Provider-comparison slice closed: `{str(summary['provider_comparison_slice_closed']).lower()}`",
            f"- Unreachable existing response types remaining: `{str(summary['unreachable_existing_response_types_remaining']).lower()}`",
            "- Selected next slice: `unknown_runtime_signal_subtypes`",
            "- Protected boundary controls required: `true`",
            "- Runtime patch allowed: `false`",
            f"- Review HTML created: `{str(summary['review_html_created']).lower()}`",
            f"- Recommended next checkpoint: `{summary['recommended_next_checkpoint']}`",
            "",
            "## Current Classifier Snapshot",
            "",
            f"- English localized response types: `{snapshot['english_localized_response_type_count']}`",
            f"- Reachable sales difficulties: `{snapshot['reachable_sales_difficulty_count']}`",
            f"- Unreachable localized response types: `{', '.join(snapshot['unreachable_localized_response_types']) or 'none'}`",
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


def main() -> None:
    source_result, slice_plan = load_source()
    source_validator = run_source_validator()
    snapshot = build_reachability_snapshot()
    selection = build_selection(snapshot, slice_plan)
    evidence = build_evidence(source_result, source_validator)
    summary = summarize(selection, snapshot, source_validator)
    result = {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "validation": {
            "passed": source_validator["passed"] and selection["provider_comparison_slice_closed"] and not selection["unreachable_existing_response_types_remaining"],
            "selection_passed": selection["selected_next_slice"] == "unknown_runtime_signal_subtypes",
        },
        "summary": summary,
    }
    write_json(OUT_DIR / "current_classifier_reachability_snapshot.json", snapshot)
    write_json(OUT_DIR / "remaining_slice_selection.json", selection)
    write_json(OUT_DIR / "evidence_summary.json", evidence)
    write_text(OUT_DIR / "report.md", render_report(summary, selection, snapshot))
    write_json(OUT_DIR / "result.json", result)
    print(json.dumps({"checkpoint_id": CHECKPOINT_ID, "validation": result["validation"], "summary": summary}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
