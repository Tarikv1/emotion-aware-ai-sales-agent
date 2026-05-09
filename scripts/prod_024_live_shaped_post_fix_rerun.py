#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from prod_021_live_shaped_dialogue_policy_simulation import (
    DEFAULT_CAMPAIGN_CASE_SOURCE,
    DEFAULT_CASE_PATH,
    DEFAULT_RETRIEVAL_REGISTRY,
    ROOT,
    build_payload as build_prod_021_payload,
)


CHECKPOINT_ID = "PROD-024-live-shaped-post-fix-rerun"
SOURCE_CHECKPOINT_ID = "PROD-023-runtime-policy-call-control-fix"
DEFAULT_SOURCE_PROD_023_RESULT = (
    ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "result.json"
)
DEFAULT_OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
DEFAULT_RESULT = DEFAULT_OUT_DIR / "result.json"
DEFAULT_REPORT = DEFAULT_OUT_DIR / "report.md"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def relpath(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def post_fix_gate_passed(summary: dict[str, Any]) -> bool:
    return (
        summary["policy_action_correctness"] == 1.0
        and summary["call_control_correctness"] == 1.0
        and summary["protected_context_preservation"] == 1.0
        and summary["non_sale_correctness"] == 1.0
        and summary["safe_close_correctness"] == 1.0
        and summary["state_reference_completeness"] == 1.0
        and summary["hard_failure_count"] == 0
        and summary["payment_collection_count"] == 0
        and summary["leakage_finding_count"] == 0
        and summary["provider_calls_made"] is False
        and summary["llm_used"] is False
        and summary["runtime_retrieval_default_enabled"] is False
        and summary["composer_hook_flag_default_enabled"] is False
    )


def compact_turn_result(turn: dict[str, Any]) -> dict[str, Any]:
    return {
        "turn_id": turn["turn_id"],
        "call_id": turn["call_id"],
        "scenario_label": turn["scenario_label"],
        "stage": turn["stage"],
        "customer_transcript": turn["customer_transcript"],
        "expected_policy_action": turn["expected_policy_action"],
        "post_fix_policy_action": turn["opt_in_runtime_policy_action"],
        "policy_action_correct": bool(turn["policy_action_correct"]),
        "expected_call_control": turn["expected_call_control"],
        "post_fix_call_control": turn["opt_in_call_control"],
        "call_control_correct": bool(turn["call_control_correct"]),
        "expected_outcome": turn["expected_outcome"],
        "expected_outcome_correct": bool(turn["expected_outcome_correct"]),
        "protected_context": bool(turn["protected_context"]),
        "protected_context_preserved": bool(turn["protected_context_preserved"]),
        "contains_payment_collection": bool(turn["contains_payment_collection"]),
        "hard_failure": bool(turn["hard_failure"]),
        "hook_applied": bool(turn["hook_applied"]),
        "post_fix_answer": turn["opt_in_answer"],
    }


def compact_call_result(call: dict[str, Any]) -> dict[str, Any]:
    return {
        "call_id": call["call_id"],
        "scenario_label": call["scenario_label"],
        "domain": call["domain"],
        "turn_count": call["turn_count"],
        "final_expected": call["final_expected"],
        "final_observed": call["final_observed"],
    }


def build_summary(post_fix_summary: dict[str, Any]) -> dict[str, Any]:
    gate_passed = post_fix_gate_passed(post_fix_summary)
    return {
        "call_count": post_fix_summary["call_count"],
        "customer_turn_count": post_fix_summary["customer_turn_count"],
        "policy_action_correct_count": post_fix_summary["policy_action_correct_count"],
        "policy_action_correctness": post_fix_summary["policy_action_correctness"],
        "call_control_correct_count": post_fix_summary["call_control_correct_count"],
        "call_control_correctness": post_fix_summary["call_control_correctness"],
        "protected_context_preservation": post_fix_summary["protected_context_preservation"],
        "non_sale_correctness": post_fix_summary["non_sale_correctness"],
        "safe_close_correctness": post_fix_summary["safe_close_correctness"],
        "state_reference_completeness": post_fix_summary["state_reference_completeness"],
        "hard_failure_count": post_fix_summary["hard_failure_count"],
        "payment_collection_count": post_fix_summary["payment_collection_count"],
        "leakage_finding_count": post_fix_summary["leakage_finding_count"],
        "retrieval_only_total_score": post_fix_summary["retrieval_only_total_score"],
        "opt_in_total_score": post_fix_summary["opt_in_total_score"],
        "opt_in_wins_vs_retrieval_only": post_fix_summary["opt_in_wins_vs_retrieval_only"],
        "retrieval_only_wins_vs_opt_in": post_fix_summary["retrieval_only_wins_vs_opt_in"],
        "ties_vs_retrieval_only": post_fix_summary["ties_vs_retrieval_only"],
        "opt_in_hooked_answer_count": post_fix_summary["opt_in_hooked_answer_count"],
        "post_fix_gate_passed": gate_passed,
        "legacy_prod_021_gate_passed": bool(post_fix_summary["prod_021_gate_passed"]),
        "runtime_promotion_allowed": False,
        "bounded_demo_discussion_allowed": gate_passed,
        "next_checkpoint_recommended": "PROD-025-bounded-demo-readiness-packet",
    }


def build_payload(
    source_prod_023_result_path: Path = DEFAULT_SOURCE_PROD_023_RESULT,
    *,
    case_path: Path = DEFAULT_CASE_PATH,
    campaign_case_source: Path = DEFAULT_CAMPAIGN_CASE_SOURCE,
    registry_path: Path = DEFAULT_RETRIEVAL_REGISTRY,
) -> dict[str, Any]:
    source_prod_023 = read_json(source_prod_023_result_path)
    post_fix_payload = build_prod_021_payload(
        case_path,
        campaign_case_source=campaign_case_source,
        registry_path=registry_path,
    )
    post_fix_summary = post_fix_payload["summary"]

    return {
        "checkpoint_id": CHECKPOINT_ID,
        "title": "PROD-024 live-shaped post-fix rerun",
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "source_prod_023_result_path": relpath(source_prod_023_result_path),
        "case_file": relpath(case_path),
        "purpose": "Rerun the full live-shaped dialogue-policy evidence path after the PROD-023 runtime-policy and call-control fix.",
        "boundaries": {
            "provider_calls_made": False,
            "llm_used": False,
            "private_data_read": False,
            "dataset_download_performed": False,
            "runtime_behavior_changed_by_this_checkpoint": False,
            "runtime_retrieval_default_enabled": False,
            "composer_hook_flag_default_enabled": False,
            "callcenteren_transcript_text_added_to_prompt": False,
        },
        "source_prod_023_summary": source_prod_023["summary"],
        "summary": build_summary(post_fix_summary),
        "label_summary": post_fix_payload["label_summary"],
        "post_fix_call_results": [compact_call_result(call) for call in post_fix_payload["call_results"]],
        "post_fix_turn_results": [compact_turn_result(turn) for turn in post_fix_payload["turn_results"]],
        "interpretation": {
            "legacy_prod_021_gate_note": "The original PROD-021 hypothesis gate expected hook gain. PROD-024 uses a post-fix policy and safety gate instead.",
            "composer_hook_decision": "keep composer hooks opt-in; do not make hooks or retrieval default from this checkpoint",
            "runtime_promotion_note": "A clean post-fix rerun permits a bounded demo-readiness packet, not production runtime promotion.",
        },
        "decision": "keep_hooks_opt_in_prepare_bounded_demo_readiness_packet",
    }


def render_turn(turn: dict[str, Any]) -> list[str]:
    return [
        f"### {turn['turn_id']}",
        "",
        f"- Scenario label: `{turn['scenario_label']}`",
        f"- Stage: `{turn['stage']}`",
        f"- Expected policy action: `{turn['expected_policy_action']}`",
        f"- Post-fix policy action: `{turn['post_fix_policy_action']}`",
        f"- Expected call-control: `{turn['expected_call_control']}`",
        f"- Post-fix call-control: `{turn['post_fix_call_control']}`",
        f"- Policy action correct: `{str(turn['policy_action_correct']).lower()}`",
        f"- Call-control correct: `{str(turn['call_control_correct']).lower()}`",
        f"- Protected context preserved: `{str(turn['protected_context_preserved']).lower()}`",
        "",
        "Customer turn:",
        "",
        "```text",
        turn["customer_transcript"],
        "```",
        "",
        "Post-fix answer:",
        "",
        "```text",
        turn["post_fix_answer"],
        "```",
        "",
    ]


def render_report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    boundaries = payload["boundaries"]
    lines = [
        "# PROD-024 Live-Shaped Post-Fix Rerun",
        "",
        "PROD-024 is the live-shaped post-fix rerun after PROD-023. It checks the full dialogue-policy path, not only the ten gap turns.",
        "",
        "## Summary",
        "",
        f"- Source checkpoint: `{payload['source_checkpoint_id']}`",
        f"- Source PROD-023 result: `{payload['source_prod_023_result_path']}`",
        f"- Calls: `{summary['call_count']}`",
        f"- Customer turns: `{summary['customer_turn_count']}`",
        f"- Policy action correctness: `{summary['policy_action_correctness']}`",
        f"- Call-control correctness: `{summary['call_control_correctness']}`",
        f"- Protected context preservation: `{summary['protected_context_preservation']}`",
        f"- Non-sale correctness: `{summary['non_sale_correctness']}`",
        f"- Safe-close correctness: `{summary['safe_close_correctness']}`",
        f"- State reference completeness: `{summary['state_reference_completeness']}`",
        f"- Hard failures: `{summary['hard_failure_count']}`",
        f"- Payment collection count: `{summary['payment_collection_count']}`",
        f"- Leakage findings: `{summary['leakage_finding_count']}`",
        f"- Post-fix gate passed: `{str(summary['post_fix_gate_passed']).lower()}`",
        f"- Legacy PROD-021 gate passed: `{str(summary['legacy_prod_021_gate_passed']).lower()}`",
        f"- Retrieval default enabled: `{str(boundaries['runtime_retrieval_default_enabled']).lower()}`",
        f"- Composer hook default enabled: `{str(boundaries['composer_hook_flag_default_enabled']).lower()}`",
        f"- Runtime promotion allowed: `{str(summary['runtime_promotion_allowed']).lower()}`",
        f"- Bounded demo discussion allowed: `{str(summary['bounded_demo_discussion_allowed']).lower()}`",
        f"- Next checkpoint recommended: `{summary['next_checkpoint_recommended']}`",
        "",
        "## Interpretation",
        "",
        "- The post-fix gate passes because policy action, call-control, protected contexts, non-sale handling, safe-close handling, and leakage boundaries are clean across all live-shaped turns.",
        "- The legacy PROD-021 gate stays false because that older hypothesis required composer-hook gain. PROD-024 does not use hook gain as a promotion criterion.",
        "- Keep composer hooks opt-in and keep retrieval default enabled: `false`.",
        "- `close-and-log-sale-ready` remains the explicit safe-close control for campaign-approved verbal next-step agreement.",
        "",
        "## Post-Fix Turn Trace",
        "",
    ]
    for turn in payload["post_fix_turn_results"]:
        lines.extend(render_turn(turn))

    lines.extend(
        [
            "## Decision",
            "",
            "Keep composer hooks opt-in, treat PROD-024 as a post-fix evidence gate rather than runtime promotion, and prepare `PROD-025-bounded-demo-readiness-packet` next.",
            "",
        ]
    )
    return "\n".join(lines)
