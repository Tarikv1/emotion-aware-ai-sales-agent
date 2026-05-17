#!/usr/bin/env python3
from __future__ import annotations

import ast
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-074-english-customer-move-classification-slice-inventory"
CHECKPOINT_NAME = "English Customer-Move Classification Slice Inventory"
SOURCE_CHECKPOINT_ID = "PROD-073-english-customer-move-classification-gate-decision"
NEXT_CHECKPOINT_ID = "PROD-075-english-provider-comparison-reachability-review"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
CASE_FILE = ROOT / "research" / "experiments" / "cases" / "prod-074-english-customer-move-classification-slice-inventory.json"
SOURCE_DIR = ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID
SOURCE_VALIDATOR = ROOT / "scripts" / "validate_prod_073_english_customer_move_classification_gate_decision.py"
SOURCE_VALIDATOR_COMMAND = "python scripts\\validate_prod_073_english_customer_move_classification_gate_decision.py"
RUNTIME_PATH = ROOT / "runtime" / "core" / "realtime_turns.py"
PROD_051_PROTECTED = ROOT / "research" / "experiments" / "generated" / "PROD-051-safe-call-control-runtime-update" / "protected_boundary_results.json"

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

SELECTED_NON_REFUSAL_GROUPS = [
    "price-first-direct",
    "written-info-request",
    "stakeholder-review",
    "partner-review",
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
    result = read_json(SOURCE_DIR / "result.json")
    decision = read_json(SOURCE_DIR / "customer_move_gate_decision.json")
    slice_plan = read_json(SOURCE_DIR / "classifier_slice_plan.json")
    if result["validation"]["passed"] is not True:
        raise SystemExit("PROD-073 must pass before PROD-074.")
    if result["summary"]["recommended_next_checkpoint"] != CHECKPOINT_ID:
        raise SystemExit("PROD-073 must recommend PROD-074.")
    if decision["broad_classifier_patch_allowed"] is not False:
        raise SystemExit("PROD-073 must block broad classifier patching.")
    if slice_plan["selected_next_action"] != "inventory_classifier_slices":
        raise SystemExit("PROD-073 must select classifier slice inventory.")
    return result, decision, slice_plan


def extract_runtime_inventory() -> dict[str, Any]:
    tree = ast.parse(RUNTIME_PATH.read_text(encoding="utf-8"))
    localized_response_types: set[str] = set()
    assigned_sales_difficulties: set[str] = set()
    runtime_classification_sales_difficulties: set[str] = set()
    response_branch_types: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "LOCALIZED_RESPONSES" and isinstance(node.value, ast.Dict):
                    localized_response_types.update(extract_localized_response_types(node.value))
                if isinstance(target, ast.Name) and target.id == "sales_difficulty":
                    assigned_sales_difficulties.update(extract_sales_difficulty_assignment(node.value))

        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "runtime_classification":
            if len(node.args) >= 3 and isinstance(node.args[2], ast.Constant) and isinstance(node.args[2].value, str):
                runtime_classification_sales_difficulties.add(node.args[2].value)

        if isinstance(node, ast.Compare) and isinstance(node.left, ast.Name) and node.left.id == "sales_difficulty":
            response_branch_types.update(extract_sales_difficulty_comparison(node))

    reachable = assigned_sales_difficulties | runtime_classification_sales_difficulties
    response_supported = localized_response_types | response_branch_types
    unreachable_localized = sorted(localized_response_types - reachable)
    reachable_without_response = sorted(reachable - response_supported)
    response_only_unreachable = sorted(response_supported - reachable)
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "runtime_path": rel(RUNTIME_PATH),
        "localized_response_types": sorted(localized_response_types),
        "localized_response_type_count": len(localized_response_types),
        "assigned_sales_difficulties": sorted(assigned_sales_difficulties),
        "runtime_classification_sales_difficulties": sorted(runtime_classification_sales_difficulties),
        "reachable_sales_difficulties": sorted(reachable),
        "reachable_sales_difficulty_count": len(reachable),
        "response_branch_types": sorted(response_branch_types),
        "response_supported_sales_difficulties": sorted(response_supported),
        "unreachable_localized_response_types": unreachable_localized,
        "reachable_without_response_support": reachable_without_response,
        "response_only_unreachable_types": response_only_unreachable,
        "selected_non_refusal_groups": SELECTED_NON_REFUSAL_GROUPS,
    }


def extract_localized_response_types(node: ast.Dict) -> set[str]:
    for key, value in zip(node.keys, node.values):
        if isinstance(key, ast.Constant) and key.value == "en" and isinstance(value, ast.Dict):
            return {item.value for item in value.keys if isinstance(item, ast.Constant) and isinstance(item.value, str)}
    return set()


def extract_sales_difficulty_assignment(node: ast.AST) -> set[str]:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return {node.value}
    if isinstance(node, ast.IfExp):
        values: set[str] = set()
        for part in [node.body, node.orelse]:
            if isinstance(part, ast.Constant) and isinstance(part.value, str):
                values.add(part.value)
        return values
    return set()


def extract_sales_difficulty_comparison(node: ast.Compare) -> set[str]:
    values: set[str] = set()
    for operator, comparator in zip(node.ops, node.comparators):
        if isinstance(operator, ast.Eq) and isinstance(comparator, ast.Constant) and isinstance(comparator.value, str):
            values.add(comparator.value)
        if isinstance(operator, ast.In) and isinstance(comparator, (ast.Set, ast.Tuple, ast.List)):
            for item in comparator.elts:
                if isinstance(item, ast.Constant) and isinstance(item.value, str):
                    values.add(item.value)
    return values


def protected_boundary_inventory() -> dict[str, Any]:
    payload = read_json(PROD_051_PROTECTED)
    items = [
        {
            "case_id": item["case_id"],
            "customer_move_id": item["customer_move_id"],
            "sales_difficulty": item["live_runtime_decision"]["sales_difficulty"],
            "next_action": item["live_runtime_decision"]["next_action"],
            "call_control": item["live_runtime_decision"]["call_control"],
            "passed": item["passed"],
        }
        for item in payload["items"]
    ]
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": payload["checkpoint_id"],
        "protected_boundary_count": len(items),
        "items": items,
    }


def unreachable_response_inventory(branch_inventory: dict[str, Any]) -> dict[str, Any]:
    items = []
    for sales_difficulty in branch_inventory["unreachable_localized_response_types"]:
        items.append(
            {
                "sales_difficulty": sales_difficulty,
                "slice_id": "unreachable_existing_response_types",
                "status": "requires_human_review_before_reachability",
                "why": "The English response text exists but was excluded from prior exact-phrase review because classifier reachability was not defined.",
                "requires_human_review_before_reachability": True,
                "runtime_patch_allowed": False,
                "review_checkpoint": NEXT_CHECKPOINT_ID,
            }
        )
    return {"checkpoint_id": CHECKPOINT_ID, "items": items}


def build_case_file() -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "scope": "english_customer_move_classification_slice_inventory_only",
        "runtime_change_requested": False,
        "response_text_change_requested": False,
        "classifier_change_requested": False,
        "retrieval_change_requested": False,
        "requires_human_review_before_next_checkpoint": False,
        "review_html_created": False,
        "recommended_next_checkpoint": NEXT_CHECKPOINT_ID,
        "recommended_next_checkpoint_requires_human_review": True,
        "inventory_targets": [
            "current deterministic classifier branches",
            "unreachable localized English response types",
            "already-approved selected non-refusal groups",
            "protected-boundary controls",
        ],
    }


def build_decision(branch_inventory: dict[str, Any]) -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "decision": "select_provider_comparison_reachability_review_next",
        "selected_next_slice": "unreachable_existing_response_types",
        "selected_next_review_item": "provider-comparison",
        "unreachable_localized_response_types": branch_inventory["unreachable_localized_response_types"],
        "runtime_patch_allowed": False,
        "response_text_change_allowed": False,
        "classifier_change_allowed": False,
        "recommended_next_checkpoint": NEXT_CHECKPOINT_ID,
        "recommended_next_checkpoint_requires_human_review": True,
        "production_runtime_promotion_allowed": False,
    }


def build_evidence_summary(source_result: dict[str, Any], source_validator: dict[str, Any]) -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "source_validation": source_result["validation"],
        "source_summary": {
            "decision": source_result["summary"]["decision"],
            "broad_classifier_patch_allowed": source_result["summary"]["broad_classifier_patch_allowed"],
            "recommended_next_checkpoint": source_result["summary"]["recommended_next_checkpoint"],
        },
        "source_validator_run": source_validator,
    }


def summarize(
    branch_inventory: dict[str, Any],
    unreachable_inventory: dict[str, Any],
    protected_inventory: dict[str, Any],
    source_validator: dict[str, Any],
) -> dict[str, Any]:
    return {
        "inventory_only": True,
        "source_validator_passed": source_validator["passed"],
        "localized_response_type_count": branch_inventory["localized_response_type_count"],
        "reachable_sales_difficulty_count": branch_inventory["reachable_sales_difficulty_count"],
        "unreachable_localized_response_types": branch_inventory["unreachable_localized_response_types"],
        "unreachable_response_item_count": len(unreachable_inventory["items"]),
        "protected_boundary_count": protected_inventory["protected_boundary_count"],
        "selected_non_refusal_group_count": len(SELECTED_NON_REFUSAL_GROUPS),
        "selected_next_slice": "unreachable_existing_response_types",
        "selected_next_review_item": "provider-comparison",
        "requires_human_review_before_next_checkpoint": False,
        "recommended_next_checkpoint_requires_human_review": True,
        "review_html_created": False,
        "recommended_next_checkpoint": NEXT_CHECKPOINT_ID,
        **BOUNDARY_FLAGS,
    }


def render_report(
    summary: dict[str, Any],
    branch_inventory: dict[str, Any],
    unreachable_inventory: dict[str, Any],
    protected_inventory: dict[str, Any],
    decision: dict[str, Any],
) -> str:
    unreachable_text = ", ".join(summary["unreachable_localized_response_types"]) or "none"
    lines = [
        "# PROD-074 English Customer-Move Classification Slice Inventory",
        "",
        "`PROD-074` inventories the current deterministic classifier surface before any customer-move classifier expansion.",
        "",
        "No human review required for this checkpoint. It creates no review HTML because it is inventory only.",
        "",
        "## Summary",
        "",
        f"- Inventory only: `{str(summary['inventory_only']).lower()}`",
        f"- Localized response type count: `{summary['localized_response_type_count']}`",
        f"- Reachable sales difficulty count: `{summary['reachable_sales_difficulty_count']}`",
        f"- Unreachable localized response types: `{unreachable_text}`",
        f"- Protected boundary count: `{summary['protected_boundary_count']}`",
        f"- Selected next slice: `{summary['selected_next_slice']}`",
        f"- Selected next review item: `{summary['selected_next_review_item']}`",
        f"- Recommended next checkpoint requires human review: `{str(summary['recommended_next_checkpoint_requires_human_review']).lower()}`",
        f"- Review HTML created: `{str(summary['review_html_created']).lower()}`",
        f"- Recommended next checkpoint: `{summary['recommended_next_checkpoint']}`",
        "- Runtime behavior changed: `false`",
        "- Response text behavior changed: `false`",
        "- Classifier behavior changed: `false`",
        "- Retrieval enabled: `false`",
        "- Production runtime promotion allowed: `false`",
        "",
        "## Decision",
        "",
        f"- Decision: `{decision['decision']}`",
        f"- Runtime patch allowed: `{str(decision['runtime_patch_allowed']).lower()}`",
        f"- Classifier change allowed: `{str(decision['classifier_change_allowed']).lower()}`",
        "",
        "## Unreachable Response Inventory",
        "",
    ]
    for item in unreachable_inventory["items"]:
        lines.extend(
            [
                f"### {item['sales_difficulty']}",
                "",
                f"- Status: `{item['status']}`",
                f"- Requires human review before reachability: `{str(item['requires_human_review_before_reachability']).lower()}`",
                f"- Review checkpoint: `{item['review_checkpoint']}`",
                f"- Why: {item['why']}",
                "",
            ]
        )
    lines.extend(
        [
            "## Selected Non-Refusal Groups Already Promoted",
            "",
            *[f"- `{item}`" for item in branch_inventory["selected_non_refusal_groups"]],
            "",
            "## Protected Boundary Controls",
            "",
        ]
    )
    for item in protected_inventory["items"]:
        lines.append(f"- `{item['customer_move_id']}` -> `{item['sales_difficulty']}` / `{item['call_control']}`")
    lines.extend(
        [
            "",
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
    source_result, _source_decision, _source_slice_plan = load_source()
    source_validator = run_source_validator()
    branch_inventory = extract_runtime_inventory()
    protected_inventory = protected_boundary_inventory()
    unreachable_inventory = unreachable_response_inventory(branch_inventory)
    decision = build_decision(branch_inventory)
    evidence = build_evidence_summary(source_result, source_validator)
    summary = summarize(branch_inventory, unreachable_inventory, protected_inventory, source_validator)
    result = {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "validation": {
            "passed": source_validator["passed"] and branch_inventory["unreachable_localized_response_types"] == ["provider-comparison"],
            "slice_inventory_passed": branch_inventory["unreachable_localized_response_types"] == ["provider-comparison"],
        },
        "summary": summary,
    }
    write_json(CASE_FILE, build_case_file())
    write_json(OUT_DIR / "classifier_branch_inventory.json", branch_inventory)
    write_json(OUT_DIR / "unreachable_response_inventory.json", unreachable_inventory)
    write_json(OUT_DIR / "protected_boundary_inventory.json", protected_inventory)
    write_json(OUT_DIR / "slice_inventory_decision.json", decision)
    write_json(OUT_DIR / "evidence_summary.json", evidence)
    write_json(OUT_DIR / "result.json", result)
    write_text(OUT_DIR / "report.md", render_report(summary, branch_inventory, unreachable_inventory, protected_inventory, decision))
    print(json.dumps({"checkpoint_id": CHECKPOINT_ID, "validation": result["validation"], "summary": summary}, indent=2))


if __name__ == "__main__":
    main()
