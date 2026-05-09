#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-022-prod-021-review-gap-packet"
SOURCE_CHECKPOINT_ID = "PROD-021-live-shaped-dialogue-policy-simulation"
DEFAULT_SOURCE_RESULT = ROOT / "research" / "experiments" / "generated" / "PROD-021-live-shaped-dialogue-policy-simulation" / "result.json"
DEFAULT_RESULT = ROOT / "research" / "experiments" / "generated" / "PROD-022-prod-021-review-gap-packet" / "result.json"
DEFAULT_REPORT = ROOT / "research" / "experiments" / "generated" / "PROD-022-prod-021-review-gap-packet" / "report.md"


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


def score_total(turn: dict[str, Any], key: str) -> int:
    score = turn.get(key, {})
    if not isinstance(score, dict):
        return 0
    return int(score.get("total", 0))


def find_gap_turns(source_payload: dict[str, Any]) -> list[dict[str, Any]]:
    gap_turns: list[dict[str, Any]] = []
    for turn in source_payload.get("turn_results", []):
        if turn.get("policy_action_correct") is True and turn.get("call_control_correct") is True:
            continue
        gap_turns.append(build_gap_turn(turn))
    return gap_turns


def classify_fix_target(turn: dict[str, Any]) -> str:
    if turn.get("call_control_correct") is False and turn.get("expected_call_control") == "close-and-log-sale-ready":
        return "sale_ready_call_control_detector"
    if turn.get("call_control_correct") is False and turn.get("scenario_label") == "software_procurement_authority_delay":
        return "procurement_review_continuation_guard"
    return "runtime_policy_router_specialization"


def explain_gap(turn: dict[str, Any]) -> str:
    target = classify_fix_target(turn)
    if target == "sale_ready_call_control_detector":
        return "The customer gave sale-ready language with no payment collection, but runtime call control kept asking instead of logging the sale-ready outcome."
    if target == "procurement_review_continuation_guard":
        return "The customer asked for written review or delayed approval, which should stay in a low-pressure continuation path rather than end the call."
    if turn.get("hook_applied"):
        return "The hook improved wording, but the runtime policy action still stayed generic, so hook gain should not be treated as policy correctness."
    return "The answer remained safe, but the runtime policy action missed the specific sales state needed for a reliable next move."


def build_gap_turn(turn: dict[str, Any]) -> dict[str, Any]:
    return {
        "turn_id": turn["turn_id"],
        "call_id": turn["call_id"],
        "scenario_label": turn["scenario_label"],
        "stage": turn["stage"],
        "customer_transcript": turn["customer_transcript"],
        "expected_policy_action": turn["expected_policy_action"],
        "opt_in_runtime_policy_action": turn["opt_in_runtime_policy_action"],
        "policy_action_correct": bool(turn["policy_action_correct"]),
        "expected_call_control": turn["expected_call_control"],
        "opt_in_call_control": turn["opt_in_call_control"],
        "call_control_correct": bool(turn["call_control_correct"]),
        "protected_context": bool(turn["protected_context"]),
        "contains_payment_collection": bool(turn["contains_payment_collection"]),
        "hard_failure": bool(turn["hard_failure"]),
        "hook_applied": bool(turn["hook_applied"]),
        "hook_id": turn.get("composer_hooks", {}).get("hook_id", ""),
        "opt_in_delta_vs_retrieval_only": int(turn["opt_in_delta_vs_retrieval_only"]),
        "default_off_answer": turn["baseline_answer"],
        "retrieval_only_answer": turn["retrieval_only_answer"],
        "opt_in_answer": turn["opt_in_answer"],
        "recommended_fix_target": classify_fix_target(turn),
        "why_it_matters": explain_gap(turn),
    }


def build_gap_categories(gap_turns: list[dict[str, Any]]) -> list[dict[str, Any]]:
    policy_turns = [turn for turn in gap_turns if not turn["policy_action_correct"]]
    sale_ready_turns = [
        turn
        for turn in gap_turns
        if not turn["call_control_correct"] and turn["expected_call_control"] == "close-and-log-sale-ready"
    ]
    procurement_turns = [
        turn
        for turn in gap_turns
        if not turn["call_control_correct"] and turn["scenario_label"] == "software_procurement_authority_delay"
    ]
    return [
        {
            "category_id": "policy_action_router_gap",
            "turn_count": len(policy_turns),
            "turn_ids": [turn["turn_id"] for turn in policy_turns],
            "description": "Runtime policy actions collapse specific sales states into generic clarification or autonomy moves.",
            "fix_target": "runtime_policy_router_specialization",
        },
        {
            "category_id": "call_control_sale_ready_gap",
            "turn_count": len(sale_ready_turns),
            "turn_ids": [turn["turn_id"] for turn in sale_ready_turns],
            "description": "Sale-ready language without payment collection is not converted into the sale-ready call-control outcome.",
            "fix_target": "sale_ready_call_control_detector",
        },
        {
            "category_id": "call_control_procurement_delay_gap",
            "turn_count": len(procurement_turns),
            "turn_ids": [turn["turn_id"] for turn in procurement_turns],
            "description": "Procurement and stakeholder review language is treated as an ending signal instead of a continuation signal.",
            "fix_target": "procurement_review_continuation_guard",
        },
    ]


def build_fix_targets(gap_turns: list[dict[str, Any]]) -> list[dict[str, Any]]:
    target_turns: dict[str, list[str]] = {}
    for turn in gap_turns:
        target_turns.setdefault(turn["recommended_fix_target"], []).append(turn["turn_id"])

    return [
        {
            "target_id": "runtime_policy_router_specialization",
            "status": "needed_before_runtime_promotion",
            "turn_ids": target_turns.get("runtime_policy_router_specialization", []),
            "implementation_note": "Map price, comparison, autonomy, stakeholder, trust, and callback signals to explicit policy actions before composer hooks choose wording.",
        },
        {
            "target_id": "sale_ready_call_control_detector",
            "status": "needed_before_runtime_promotion",
            "turn_ids": target_turns.get("sale_ready_call_control_detector", []),
            "implementation_note": "Recognize verbal commitment or sale-ready next-step agreement while keeping payment collection out of scope.",
        },
        {
            "target_id": "procurement_review_continuation_guard",
            "status": "needed_before_runtime_promotion",
            "turn_ids": target_turns.get("procurement_review_continuation_guard", []),
            "implementation_note": "Keep written-info, boss-review, procurement, and future-review turns in continue-call unless the customer explicitly ends the conversation.",
        },
        {
            "target_id": "keep_composer_hooks_opt_in",
            "status": "retain_but_do_not_promote",
            "turn_ids": [turn["turn_id"] for turn in gap_turns if turn["hook_applied"]],
            "implementation_note": "Hook wording gains survived, but hooks are not the owner of policy action or call-control correctness.",
        },
    ]


def build_prioritized_next_actions() -> list[dict[str, str]]:
    return [
        {
            "target_id": "runtime_policy_router_specialization",
            "action": "Fix policy-action routing for the ten gap turns before changing retrieval or voice behavior.",
            "rationale": "The failed gate is mostly policy/action routing, not hooks; hook wording gain cannot substitute for correct dialogue state.",
        },
        {
            "target_id": "procurement_review_continuation_guard",
            "action": "Stop treating written-info or delayed-approval language as an end-call signal.",
            "rationale": "Two call-control misses came from procurement review language that should remain a low-pressure continuation.",
        },
        {
            "target_id": "sale_ready_call_control_detector",
            "action": "Add sale-ready recognition for verbal next-step agreement without payment collection.",
            "rationale": "One call-control miss blocked the MVP safe-close metric even though the customer was ready for a next step.",
        },
        {
            "target_id": "keep_composer_hooks_opt_in",
            "action": "Keep PROD-020 hooks available only behind the explicit opt-in flag.",
            "rationale": "The hooks improved four turns and caused no safety regression, but runtime promotion remains blocked.",
        },
    ]


def build_summary(source_payload: dict[str, Any], gap_turns: list[dict[str, Any]]) -> dict[str, Any]:
    source_summary = source_payload["summary"]
    return {
        "source_customer_turn_count": source_summary["customer_turn_count"],
        "source_policy_action_correctness": source_summary["policy_action_correctness"],
        "source_call_control_correctness": source_summary["call_control_correctness"],
        "gap_turn_count": len(gap_turns),
        "policy_action_miss_count": sum(1 for turn in gap_turns if not turn["policy_action_correct"]),
        "call_control_miss_count": sum(1 for turn in gap_turns if not turn["call_control_correct"]),
        "protected_context_gap_count": sum(1 for turn in gap_turns if turn["protected_context"]),
        "hook_gain_turn_count": source_summary["opt_in_wins_vs_retrieval_only"],
        "hard_failure_count": source_summary["hard_failure_count"],
        "leakage_finding_count": source_summary["leakage_finding_count"],
        "payment_collection_count": source_summary["payment_collection_count"],
        "runtime_promotion_allowed": False,
        "next_checkpoint_recommended": "PROD-023-runtime-policy-call-control-fix",
    }


def build_payload(source_result_path: Path = DEFAULT_SOURCE_RESULT) -> dict[str, Any]:
    source_payload = read_json(source_result_path)
    gap_turns = find_gap_turns(source_payload)
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "title": "PROD-022 PROD-021 review gap packet",
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "source_result_path": relpath(source_result_path),
        "purpose": "Convert the failed PROD-021 gate into exact gap turns and narrow fix targets before runtime promotion.",
        "boundaries": {
            "provider_calls_made": False,
            "llm_used": False,
            "private_data_read": False,
            "dataset_download_performed": False,
            "runtime_behavior_changed": False,
            "runtime_retrieval_default_enabled": False,
            "composer_hook_flag_default_enabled": False,
            "commercial_runtime_prompt_text_changed": False,
        },
        "summary": build_summary(source_payload, gap_turns),
        "gap_categories": build_gap_categories(gap_turns),
        "fix_targets": build_fix_targets(gap_turns),
        "prioritized_next_actions": build_prioritized_next_actions(),
        "gap_turns": gap_turns,
        "decision": "keep_prod_021_hooks_opt_in_fix_policy_and_call_control_first",
    }


def render_gap_turn(turn: dict[str, Any]) -> list[str]:
    return [
        f"### {turn['turn_id']}",
        "",
        f"- Scenario label: `{turn['scenario_label']}`",
        f"- Stage: `{turn['stage']}`",
        f"- Policy action miss: expected `{turn['expected_policy_action']}`, observed `{turn['opt_in_runtime_policy_action']}`",
        f"- Call-control miss: expected `{turn['expected_call_control']}`, observed `{turn['opt_in_call_control']}`",
        f"- Hook applied: `{str(turn['hook_applied']).lower()}`",
        f"- Recommended fix target: `{turn['recommended_fix_target']}`",
        f"- Why it matters: {turn['why_it_matters']}",
        "",
        "Exact customer turn:",
        "",
        "```text",
        turn["customer_transcript"],
        "```",
        "",
        "Exact agent answers:",
        "",
        "Default-off answer:",
        "",
        "```text",
        turn["default_off_answer"],
        "```",
        "",
        "Retrieval-only answer:",
        "",
        "```text",
        turn["retrieval_only_answer"],
        "```",
        "",
        "Opt-in hook answer:",
        "",
        "```text",
        turn["opt_in_answer"],
        "```",
        "",
    ]


def render_report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# PROD-022 PROD-021 Review Gap Packet",
        "",
        "This review gap packet reads the completed PROD-021 result and extracts the exact customer turn, exact agent answer, policy action miss, and call-control miss evidence needed before any runtime promotion.",
        "",
        "No runtime behavior change is made. No provider calls were made. No private data was read. Retrieval and composer hooks remain disabled by default.",
        "",
        "## Summary",
        "",
        f"- Source checkpoint: `{payload['source_checkpoint_id']}`",
        f"- Source result: `{payload['source_result_path']}`",
        f"- Source customer turns: `{summary['source_customer_turn_count']}`",
        f"- Source policy action correctness: `{summary['source_policy_action_correctness']}`",
        f"- Source call-control correctness: `{summary['source_call_control_correctness']}`",
        f"- Gap turns: `{summary['gap_turn_count']}`",
        f"- Policy action misses: `{summary['policy_action_miss_count']}`",
        f"- Call-control misses: `{summary['call_control_miss_count']}`",
        f"- Protected context gaps: `{summary['protected_context_gap_count']}`",
        f"- Hook gain turns: `{summary['hook_gain_turn_count']}`",
        f"- Hard failures: `{summary['hard_failure_count']}`",
        f"- Leakage findings: `{summary['leakage_finding_count']}`",
        f"- Runtime promotion allowed: `{str(summary['runtime_promotion_allowed']).lower()}`",
        f"- Next checkpoint recommended: `{summary['next_checkpoint_recommended']}`",
        "",
        "## Gap Categories",
        "",
        "| Category | Turns | Fix Target |",
        "| --- | ---: | --- |",
    ]
    for category in payload["gap_categories"]:
        lines.append(f"| `{category['category_id']}` | `{category['turn_count']}` | `{category['fix_target']}` |")

    lines.extend(
        [
            "",
            "## Prioritized Next Actions",
            "",
        ]
    )
    for index, action in enumerate(payload["prioritized_next_actions"], start=1):
        lines.extend(
            [
                f"{index}. `{action['target_id']}`",
                f"   Action: {action['action']}",
                f"   Rationale: {action['rationale']}",
                "",
            ]
        )

    lines.extend(["## Gap Turns", ""])
    for turn in payload["gap_turns"]:
        lines.extend(render_gap_turn(turn))

    lines.extend(
        [
            "## Decision",
            "",
            "Keep composer hooks opt-in. Fix runtime policy routing and call-control before any demo or default-runtime discussion.",
            "",
        ]
    )
    return "\n".join(lines)
