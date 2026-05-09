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


CHECKPOINT_ID = "PROD-023-runtime-policy-call-control-fix"
SOURCE_CHECKPOINT_ID = "PROD-022-prod-021-review-gap-packet"
DEFAULT_SOURCE_GAP_PACKET = (
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


def by_turn_id(turns: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(turn["turn_id"]): turn for turn in turns}


def fixed_gap_turn(source_turn: dict[str, Any], post_fix_turn: dict[str, Any]) -> dict[str, Any]:
    return {
        "turn_id": source_turn["turn_id"],
        "call_id": source_turn["call_id"],
        "scenario_label": source_turn["scenario_label"],
        "stage": source_turn["stage"],
        "customer_transcript": source_turn["customer_transcript"],
        "expected_policy_action": source_turn["expected_policy_action"],
        "source_miss_policy_action": source_turn["opt_in_runtime_policy_action"],
        "post_fix_policy_action": post_fix_turn["opt_in_runtime_policy_action"],
        "policy_action_correct": bool(post_fix_turn["policy_action_correct"]),
        "expected_call_control": source_turn["expected_call_control"],
        "source_miss_call_control": source_turn["opt_in_call_control"],
        "post_fix_call_control": post_fix_turn["opt_in_call_control"],
        "call_control_correct": bool(post_fix_turn["call_control_correct"]),
        "post_fix_answer": post_fix_turn["opt_in_answer"],
        "contains_payment_collection": bool(post_fix_turn["contains_payment_collection"]),
        "hard_failure": bool(post_fix_turn["hard_failure"]),
        "hook_applied": bool(post_fix_turn["hook_applied"]),
    }


def build_summary(source_packet: dict[str, Any], post_fix_payload: dict[str, Any], fixed_turns: list[dict[str, Any]]) -> dict[str, Any]:
    source_summary = source_packet["summary"]
    post_summary = post_fix_payload["summary"]
    source_gap_turns = source_packet["gap_turns"]

    closed_policy = sum(
        1
        for source_turn, fixed_turn in zip(source_gap_turns, fixed_turns)
        if source_turn["policy_action_correct"] is False and fixed_turn["policy_action_correct"] is True
    )
    closed_control = sum(
        1
        for source_turn, fixed_turn in zip(source_gap_turns, fixed_turns)
        if source_turn["call_control_correct"] is False and fixed_turn["call_control_correct"] is True
    )
    remaining_policy = sum(1 for turn in fixed_turns if turn["policy_action_correct"] is not True)
    remaining_control = sum(1 for turn in fixed_turns if turn["call_control_correct"] is not True)

    return {
        "source_gap_turn_count": source_summary["gap_turn_count"],
        "fixed_gap_turn_count": len(fixed_turns),
        "closed_policy_action_miss_count": closed_policy,
        "closed_call_control_miss_count": closed_control,
        "remaining_policy_action_miss_count": remaining_policy,
        "remaining_call_control_miss_count": remaining_control,
        "policy_action_correctness": post_summary["policy_action_correctness"],
        "call_control_correctness": post_summary["call_control_correctness"],
        "protected_context_preservation": post_summary["protected_context_preservation"],
        "non_sale_correctness": post_summary["non_sale_correctness"],
        "safe_close_correctness": post_summary["safe_close_correctness"],
        "hard_failure_count": post_summary["hard_failure_count"],
        "payment_collection_count": post_summary["payment_collection_count"],
        "leakage_finding_count": post_summary["leakage_finding_count"],
        "post_fix_customer_turn_count": post_summary["customer_turn_count"],
        "runtime_promotion_allowed": False,
        "next_checkpoint_recommended": "PROD-024-live-shaped-post-fix-rerun",
    }


def build_payload(
    source_gap_packet_path: Path = DEFAULT_SOURCE_GAP_PACKET,
    *,
    case_path: Path = DEFAULT_CASE_PATH,
    campaign_case_source: Path = DEFAULT_CAMPAIGN_CASE_SOURCE,
    registry_path: Path = DEFAULT_RETRIEVAL_REGISTRY,
) -> dict[str, Any]:
    source_packet = read_json(source_gap_packet_path)
    post_fix_payload = build_prod_021_payload(
        case_path,
        campaign_case_source=campaign_case_source,
        registry_path=registry_path,
    )
    post_fix_turns = by_turn_id(post_fix_payload["turn_results"])
    fixed_turns = [
        fixed_gap_turn(source_turn, post_fix_turns[str(source_turn["turn_id"])])
        for source_turn in source_packet["gap_turns"]
    ]

    return {
        "checkpoint_id": CHECKPOINT_ID,
        "title": "PROD-023 runtime-policy and call-control fix",
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "source_gap_packet_path": relpath(source_gap_packet_path),
        "purpose": "Close the exact policy-action and call-control misses found by PROD-022 without changing provider, retrieval, dataset, or composer-hook defaults.",
        "boundaries": {
            "runtime_policy_changed": True,
            "provider_calls_made": False,
            "llm_used": False,
            "private_data_read": False,
            "dataset_download_performed": False,
            "runtime_retrieval_default_enabled": False,
            "composer_hook_flag_default_enabled": False,
            "callcenteren_transcript_text_added_to_prompt": False,
        },
        "changed_surfaces": [
            {
                "surface_id": "runtime_input_classifier",
                "change": "Recognize comparison, autonomy, stakeholder, procurement, trust, and sale-ready commitment turns.",
            },
            {
                "surface_id": "call_control_contract",
                "change": "Add close-and-log-sale-ready for campaign-approved verbal next-step commitments.",
            },
            {
                "surface_id": "runtime_policy_action_mapping",
                "change": "Map recognized sales states to explicit policy actions before any wording hook evaluation.",
            },
        ],
        "summary": build_summary(source_packet, post_fix_payload, fixed_turns),
        "fixed_gap_turns": fixed_turns,
        "decision": "keep_prod_023_local_runtime_policy_fix_rerun_before_promotion",
    }


def render_fixed_turn(turn: dict[str, Any]) -> list[str]:
    return [
        f"### {turn['turn_id']}",
        "",
        f"- Scenario label: `{turn['scenario_label']}`",
        f"- Stage: `{turn['stage']}`",
        f"- Expected policy action: `{turn['expected_policy_action']}`",
        f"- Source observed policy action: `{turn['source_miss_policy_action']}`",
        f"- Post-fix policy action: `{turn['post_fix_policy_action']}`",
        f"- Expected call-control: `{turn['expected_call_control']}`",
        f"- Source observed call-control: `{turn['source_miss_call_control']}`",
        f"- Post-fix call-control: `{turn['post_fix_call_control']}`",
        f"- Policy action correct: `{str(turn['policy_action_correct']).lower()}`",
        f"- Call-control correct: `{str(turn['call_control_correct']).lower()}`",
        f"- Hook applied: `{str(turn['hook_applied']).lower()}`",
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
        "# PROD-023 Runtime-Policy Call-Control Fix",
        "",
        "PROD-023 closes the exact PROD-022 gap packet by specializing runtime-policy routing and call-control ownership. It does not promote retrieval or composer hooks.",
        "",
        "## Summary",
        "",
        f"- Source checkpoint: `{payload['source_checkpoint_id']}`",
        f"- Source gap packet: `{payload['source_gap_packet_path']}`",
        f"- Source gap turns: `{summary['source_gap_turn_count']}`",
        f"- Fixed gap turns: `{summary['fixed_gap_turn_count']}`",
        f"- Closed policy-action misses: `{summary['closed_policy_action_miss_count']}`",
        f"- Closed call-control misses: `{summary['closed_call_control_miss_count']}`",
        f"- Remaining policy-action misses: `{summary['remaining_policy_action_miss_count']}`",
        f"- Remaining call-control misses: `{summary['remaining_call_control_miss_count']}`",
        f"- Policy action correctness: `{summary['policy_action_correctness']}`",
        f"- Call-control correctness: `{summary['call_control_correctness']}`",
        f"- Protected context preservation: `{summary['protected_context_preservation']}`",
        f"- Non-sale correctness: `{summary['non_sale_correctness']}`",
        f"- Safe-close correctness: `{summary['safe_close_correctness']}`",
        f"- Hard failures: `{summary['hard_failure_count']}`",
        f"- Payment collection count: `{summary['payment_collection_count']}`",
        f"- Leakage findings: `{summary['leakage_finding_count']}`",
        f"- Retrieval default enabled: `{str(boundaries['runtime_retrieval_default_enabled']).lower()}`",
        f"- Composer hook default enabled: `{str(boundaries['composer_hook_flag_default_enabled']).lower()}`",
        f"- Runtime promotion allowed: `{str(summary['runtime_promotion_allowed']).lower()}`",
        f"- Next checkpoint recommended: `{summary['next_checkpoint_recommended']}`",
        "",
        "## Changed Surfaces",
        "",
    ]
    for surface in payload["changed_surfaces"]:
        lines.append(f"- `{surface['surface_id']}`: {surface['change']}")

    lines.extend(
        [
            "",
            "## Fixed Gap Turns",
            "",
        ]
    )
    for turn in payload["fixed_gap_turns"]:
        lines.extend(render_fixed_turn(turn))

    lines.extend(
        [
            "## Decision",
            "",
            "Keep PROD-023 as a local runtime-policy fix, keep composer hooks opt-in, keep retrieval default enabled: `false`, and rerun the live-shaped evidence path in PROD-024 before any runtime-promotion discussion.",
            "",
        ]
    )
    return "\n".join(lines)
