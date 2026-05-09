#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REQUIRED_LAYERS = [
    "buyer_state",
    "strategy",
    "safety",
    "call_control",
    "retrieval",
    "voice",
    "response",
    "evidence_log",
]

REQUIRED_CALL_CONTROLS = {
    "continue-call",
    "bridge-then-continue",
    "transfer-or-escalate",
    "end-call",
    "schedule-and-end",
    "close-and-log-sale-ready",
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def assert_condition(condition: bool, message: Any) -> None:
    if not condition:
        raise AssertionError(message)


def _required_field_set(schema_layer: dict[str, Any]) -> set[str]:
    return set(schema_layer.get("required_fields", []))


def _validate_turn(turn: dict[str, Any], state_schema: dict[str, Any]) -> dict[str, Any]:
    packet = turn["state_packet"]
    assert_condition(set(packet) == set(REQUIRED_LAYERS), f"Unexpected state packet layers for {turn['turn_id']}")
    for layer in REQUIRED_LAYERS:
        required_fields = _required_field_set(state_schema[layer])
        assert_condition(required_fields.issubset(set(packet[layer])), f"{turn['turn_id']} missing {layer} field(s)")

    decision = packet["call_control"]["decision"]
    assert_condition(decision in REQUIRED_CALL_CONTROLS, f"{turn['turn_id']} has invalid call_control decision: {decision}")
    assert_condition(packet["retrieval"]["enabled"] is False, f"{turn['turn_id']} must keep retrieval disabled by default")
    assert_condition(packet["voice"]["provider_live_enabled"] is False, f"{turn['turn_id']} must not enable live provider voice")
    assert_condition(packet["response"]["final_response"] == turn["response_preview"], f"{turn['turn_id']} response preview mismatch")

    expected_sale = turn["expected_outcome"] == "sale_ready"
    assert_condition(packet["response"]["sale_ready"] is expected_sale, f"{turn['turn_id']} sale_ready mismatch")
    if not expected_sale:
        assert_condition(packet["response"]["non_sale_correct"] is True, f"{turn['turn_id']} must count as non-sale correctness")
    assert_condition(packet["safety"]["hard_failure"] is False, f"{turn['turn_id']} has a hard failure")
    assert_condition(packet["evidence_log"]["stores_raw_transcript_text"] is False, f"{turn['turn_id']} stores transcript text")
    assert_condition(packet["evidence_log"]["stores_private_audio"] is False, f"{turn['turn_id']} stores private audio")
    return turn


def build_brain_002_payload(case_path: Path, *, root: Path) -> dict[str, Any]:
    case = load_json(case_path)
    state_schema = case["state_schema"]
    assert_condition(set(REQUIRED_LAYERS).issubset(set(state_schema)), "Case file is missing required schema layers")
    call_controls = set(state_schema["call_control"]["allowed_values"])
    assert_condition(REQUIRED_CALL_CONTROLS.issubset(call_controls), "Case file is missing required call-control values")

    turns = [_validate_turn(turn, state_schema) for turn in case["example_turns"]]
    sale_ready_count = sum(1 for turn in turns if turn["state_packet"]["response"]["sale_ready"] is True)
    non_sale_correct_count = sum(
        1
        for turn in turns
        if turn["expected_outcome"] != "sale_ready" and turn["state_packet"]["response"]["non_sale_correct"] is True
    )
    hard_failure_count = sum(1 for turn in turns if turn["state_packet"]["safety"]["hard_failure"] is True)

    return {
        "brain_002_id": "BRAIN-002-runtime-state-schema",
        "schema_version": "brain-runtime-state-v1",
        "status": "schema_checkpoint_only",
        "summary": {
            "turn_count": len(turns),
            "sale_ready_count": sale_ready_count,
            "non_sale_correct_count": non_sale_correct_count,
            "hard_failure_count": hard_failure_count,
            "provider_calls_made": False,
            "private_data_read": False,
            "runtime_behavior_changed": False,
            "retrieval_default": "disabled",
            "schema_layer_count": len(REQUIRED_LAYERS),
            "call_control_value_count": len(call_controls),
        },
        "state_schema": state_schema,
        "example_turns": turns,
        "architecture_boundary": {
            "core_loop": "SalesCampaign plus short-term state plus strategy plus safety plus call control plus response contract",
            "retrieval": "retrieval disabled by default; RAG hints need separate RAG-017/RAG-018 promotion",
            "voice": "voice profile is delivery metadata only and makes no live provider call",
            "learning": "post-call learning stays outside the live path",
            "runtime_effect": "no runtime behavior changed by this checkpoint",
        },
        "data_boundary": {
            "real_customer_data_used": False,
            "private_data_read": False,
            "transcript_bodies_persisted": False,
            "provider_calls_made": False,
            "payment_or_checkout_enabled": False,
            "commercial_runtime_prompt_changed": False,
        },
    }


def render_brain_002_report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    state_schema = payload["state_schema"]
    call_controls = ", ".join(state_schema["call_control"]["allowed_values"])
    lines = [
        "# BRAIN-002 Runtime State Schema Report",
        "",
        "BRAIN-002 defines the runtime state schema for the sales-agent brain.",
        "This is a schema checkpoint only: no runtime behavior changed, no provider calls were made, and retrieval disabled by default remains the rule.",
        "",
        "## Summary",
        "",
        f"- Turn examples: `{summary['turn_count']}`",
        f"- Sale-ready examples: `{summary['sale_ready_count']}`",
        f"- Non-sale correctness examples: `{summary['non_sale_correct_count']}`",
        f"- Hard failures: `{summary['hard_failure_count']}`",
        f"- Retrieval default: `{summary['retrieval_default']}`",
        "",
        "## State Layers",
        "",
    ]
    for layer_name, layer in state_schema.items():
        fields = ", ".join(layer["required_fields"])
        lines.append(f"- `{layer_name}`: {fields}")
    lines.extend(
        [
            "",
            "## Call Control",
            "",
            f"Allowed values: `{call_controls}`",
            "",
            "`close-and-log-sale-ready` is the full-sale close value. It can only appear when the response packet has `sale_ready=true`, no hard failure, and the campaign close criteria are satisfied.",
            "",
            "## Boundaries",
            "",
            "- Retrieval disabled by default.",
            "- RAG-020/RAG-021 remain advisory until a separate registry rebuild and guarded evaluation.",
            "- Voice profile is delivery metadata, not a sales-reasoning layer.",
            "- Non-sale correctness remains a required gate before optimizing close rate.",
        ]
    )
    return "\n".join(lines) + "\n"
