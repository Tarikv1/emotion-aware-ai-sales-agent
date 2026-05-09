#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-025-bounded-demo-readiness-packet"
SOURCE_CHECKPOINT_ID = "PROD-024-live-shaped-post-fix-rerun"
DEFAULT_SOURCE_PROD_024_RESULT = (
    ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "result.json"
)
DEFAULT_OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
DEFAULT_RESULT = DEFAULT_OUT_DIR / "result.json"
DEFAULT_REPORT = DEFAULT_OUT_DIR / "report.md"
NEXT_CHECKPOINT = "PROD-026-local-demo-trace-harness"

DEMO_TRACE_SCENARIOS = {
    "software_multi_objection_sale",
    "software_procurement_authority_delay",
    "trust_price_callback",
}


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


def source_gate_clean(source_payload: dict[str, Any]) -> bool:
    summary = source_payload["summary"]
    return (
        summary["post_fix_gate_passed"] is True
        and summary["policy_action_correctness"] == 1.0
        and summary["call_control_correctness"] == 1.0
        and summary["protected_context_preservation"] == 1.0
        and summary["non_sale_correctness"] == 1.0
        and summary["safe_close_correctness"] == 1.0
        and summary["hard_failure_count"] == 0
        and summary["payment_collection_count"] == 0
        and summary["leakage_finding_count"] == 0
    )


def build_readiness_summary(source_payload: dict[str, Any]) -> dict[str, Any]:
    summary = source_payload["summary"]
    gate_clean = source_gate_clean(source_payload)
    return {
        "source_call_count": summary["call_count"],
        "source_turn_count": summary["customer_turn_count"],
        "policy_action_correctness": summary["policy_action_correctness"],
        "call_control_correctness": summary["call_control_correctness"],
        "protected_context_preservation": summary["protected_context_preservation"],
        "non_sale_correctness": summary["non_sale_correctness"],
        "safe_close_correctness": summary["safe_close_correctness"],
        "state_reference_completeness": summary["state_reference_completeness"],
        "hard_failure_count": summary["hard_failure_count"],
        "payment_collection_count": summary["payment_collection_count"],
        "leakage_finding_count": summary["leakage_finding_count"],
        "demo_readiness_gate_passed": gate_clean,
        "bounded_demo_ready": gate_clean,
        "local_dry_run_only": True,
        "manual_review_required": True,
        "production_runtime_promotion_allowed": False,
        "live_provider_demo_allowed": False,
        "next_checkpoint_recommended": NEXT_CHECKPOINT,
    }


def allowed_demo_modes() -> list[dict[str, Any]]:
    return [
        {
            "mode_id": "local-trace-replay",
            "description": "Replay selected synthetic post-fix turns with question, answer, policy action, call control, and safety flags visible.",
            "default_provider_calls": False,
            "customer_data_allowed": False,
            "allowed_before_manual_review": True,
        },
        {
            "mode_id": "offline-scripted-call-simulation",
            "description": "Run deterministic synthetic calls through the local runtime path and show structured decisions.",
            "default_provider_calls": False,
            "customer_data_allowed": False,
            "allowed_before_manual_review": True,
        },
        {
            "mode_id": "human-review-packet",
            "description": "Export a compact review packet for Tarik to inspect before any live/provider demo step.",
            "default_provider_calls": False,
            "customer_data_allowed": False,
            "allowed_before_manual_review": True,
        },
    ]


def blocked_claims() -> list[str]:
    return [
        "production-ready autonomous calling",
        "customer-facing live runtime",
        "retrieval default enabled",
        "composer hooks default enabled",
        "payment collection or checkout",
        "human replacement",
        "provider/live voice readiness",
    ]


def required_review_gates() -> list[dict[str, Any]]:
    return [
        {
            "gate_id": "product-demo-scope-review",
            "owner": "Tarik",
            "required_before": "Any demo beyond local trace replay.",
        },
        {
            "gate_id": "privacy-boundary-review",
            "owner": "Tarik",
            "required_before": "Any use of non-synthetic lead, customer, call, or audio material.",
        },
        {
            "gate_id": "provider-run-boundary-review",
            "owner": "Tarik",
            "required_before": "Any live TTS, LLM, ASR, telephony, or external provider call.",
        },
        {
            "gate_id": "manual-trace-review",
            "owner": "Tarik",
            "required_before": "Treating the demo trace as acceptable product evidence.",
        },
        {
            "gate_id": "human-approval-before-live",
            "owner": "Tarik",
            "required_before": "Any client-facing, live-call, or provider-backed demonstration.",
        },
    ]


def build_demo_trace_contract() -> dict[str, Any]:
    return {
        "exact_question_and_answer_visible": True,
        "show_decision_process": True,
        "raw_private_data_allowed": False,
        "required_fields": [
            "scenario_label",
            "customer_question",
            "agent_answer",
            "policy_action",
            "call_control",
            "safety_flags",
            "source_checkpoint",
        ],
        "decision_process_fields": [
            "policy_action",
            "call_control",
            "expected_outcome",
            "protected_context",
            "source_checkpoint",
        ],
    }


def build_trace_cards(source_payload: dict[str, Any]) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    seen: set[str] = set()
    for turn in source_payload["post_fix_turn_results"]:
        scenario = str(turn["scenario_label"])
        if scenario not in DEMO_TRACE_SCENARIOS or scenario in seen:
            continue
        seen.add(scenario)
        cards.append(
            {
                "turn_id": turn["turn_id"],
                "scenario_label": scenario,
                "customer_question": turn["customer_transcript"],
                "agent_answer": turn["post_fix_answer"],
                "policy_action": turn["post_fix_policy_action"],
                "call_control": turn["post_fix_call_control"],
                "expected_outcome": turn["expected_outcome"],
                "safety_flags": {
                    "contains_payment_collection": bool(turn["contains_payment_collection"]),
                    "hard_failure": bool(turn["hard_failure"]),
                    "protected_context_preserved": bool(turn["protected_context_preserved"]),
                },
                "source_checkpoint": SOURCE_CHECKPOINT_ID,
            }
        )
    return cards


def build_payload(source_prod_024_result_path: Path = DEFAULT_SOURCE_PROD_024_RESULT) -> dict[str, Any]:
    source_payload = read_json(source_prod_024_result_path)
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "title": "PROD-025 bounded demo readiness packet",
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "source_prod_024_result_path": relpath(source_prod_024_result_path),
        "purpose": "Convert the clean PROD-024 post-fix evidence into a bounded local-demo readiness packet without enabling live or customer-facing behavior.",
        "boundaries": {
            "provider_calls_made": False,
            "llm_used": False,
            "private_data_read": False,
            "dataset_download_performed": False,
            "runtime_behavior_changed_by_this_checkpoint": False,
            "runtime_retrieval_default_enabled": False,
            "composer_hook_flag_default_enabled": False,
            "live_provider_default_enabled": False,
            "customer_data_allowed": False,
            "payment_collection_enabled": False,
            "customer_facing_claim_allowed": False,
        },
        "source_prod_024_summary": source_payload["summary"],
        "readiness_summary": build_readiness_summary(source_payload),
        "allowed_demo_modes": allowed_demo_modes(),
        "blocked_claims": blocked_claims(),
        "required_review_gates": required_review_gates(),
        "demo_trace_contract": build_demo_trace_contract(),
        "demo_trace_cards": build_trace_cards(source_payload),
        "decision": "bounded_demo_ready_local_trace_only",
    }


def render_trace_card(card: dict[str, Any]) -> list[str]:
    return [
        f"### {card['turn_id']}",
        "",
        f"- Scenario label: `{card['scenario_label']}`",
        f"- Policy action: `{card['policy_action']}`",
        f"- Call control: `{card['call_control']}`",
        f"- Expected outcome: `{card['expected_outcome']}`",
        f"- Safety flags: `{json.dumps(card['safety_flags'], sort_keys=True)}`",
        "",
        "Customer question:",
        "",
        "```text",
        card["customer_question"],
        "```",
        "",
        "Agent answer:",
        "",
        "```text",
        card["agent_answer"],
        "```",
        "",
    ]


def render_report(payload: dict[str, Any]) -> str:
    readiness = payload["readiness_summary"]
    boundaries = payload["boundaries"]
    lines = [
        "# PROD-025 Bounded Demo Readiness Packet",
        "",
        "PROD-025 turns the clean PROD-024 evidence into a bounded demo readiness packet. It does not enable provider calls, customer data, retrieval defaults, composer-hook defaults, or production runtime promotion.",
        "",
        "## Summary",
        "",
        f"- Source checkpoint: `{payload['source_checkpoint_id']}`",
        f"- Source PROD-024 result: `{payload['source_prod_024_result_path']}`",
        f"- Source calls: `{readiness['source_call_count']}`",
        f"- Source turns: `{readiness['source_turn_count']}`",
        f"- Policy action correctness: `{readiness['policy_action_correctness']}`",
        f"- Call-control correctness: `{readiness['call_control_correctness']}`",
        f"- Demo readiness gate passed: `{str(readiness['demo_readiness_gate_passed']).lower()}`",
        f"- Bounded demo ready: `{str(readiness['bounded_demo_ready']).lower()}`",
        f"- Local dry-run only: `{str(readiness['local_dry_run_only']).lower()}`",
        f"- Manual review required: `{str(readiness['manual_review_required']).lower()}`",
        f"- Production runtime promotion allowed: `{str(readiness['production_runtime_promotion_allowed']).lower()}`",
        f"- Live provider demo allowed: `{str(readiness['live_provider_demo_allowed']).lower()}`",
        f"- Customer data allowed: `{str(boundaries['customer_data_allowed']).lower()}`",
        f"- Retrieval default enabled: `{str(boundaries['runtime_retrieval_default_enabled']).lower()}`",
        f"- Composer hook default enabled: `{str(boundaries['composer_hook_flag_default_enabled']).lower()}`",
        f"- Next checkpoint recommended: `{readiness['next_checkpoint_recommended']}`",
        "",
        "## Allowed Demo Modes",
        "",
    ]
    for mode in payload["allowed_demo_modes"]:
        lines.append(
            f"- `{mode['mode_id']}`: {mode['description']} Provider calls default: `{str(mode['default_provider_calls']).lower()}`. Customer data allowed: `{str(mode['customer_data_allowed']).lower()}`."
        )

    lines.extend(["", "## Blocked Claims", ""])
    for claim in payload["blocked_claims"]:
        lines.append(f"- `{claim}`")

    lines.extend(["", "## Required Review Gates", ""])
    for gate in payload["required_review_gates"]:
        lines.append(f"- `{gate['gate_id']}`: required before {gate['required_before']}")

    lines.extend(
        [
            "",
            "## Demo Trace Contract",
            "",
            f"- Exact question and answer visible: `{str(payload['demo_trace_contract']['exact_question_and_answer_visible']).lower()}`",
            f"- Show decision process: `{str(payload['demo_trace_contract']['show_decision_process']).lower()}`",
            f"- Private data allowed: `{str(payload['demo_trace_contract']['raw_private_data_allowed']).lower()}`",
            f"- Required fields: `{', '.join(payload['demo_trace_contract']['required_fields'])}`",
            "",
            "## Demo Trace Cards",
            "",
        ]
    )
    for card in payload["demo_trace_cards"]:
        lines.extend(render_trace_card(card))

    lines.extend(
        [
            "## Decision",
            "",
            "Bounded demo readiness is accepted for local trace-only work. Build `PROD-026-local-demo-trace-harness` next, with live providers, customer data, payment handling, retrieval defaults, and composer-hook defaults still blocked.",
            "",
        ]
    )
    return "\n".join(lines)
