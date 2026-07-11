#!/usr/bin/env python3
"""Guarded live LLM-only experiment for the Atlas ELEVENLABS-036 suite."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import apply_elevenlabs_036_natural_sales_prompt_hardening as agent_guard
import apply_elevenlabs_039_independent_test_hardening as guards


CHECKPOINT_ID = "ELEVENLABS-036-natural-sales-scenarios"
AGENT_ID = "agent_7801kt0g32zxf4f8x5zkykj7syty"
AGENT_NAME = "web design"
API_KEY_ENV_VAR = "ELEVENLABS_API_KEY"
CONFIRM_TOKEN = "confirm-provider-write"
OUT_DIR = ROOT / "research/experiments/generated/ELEVENLABS-036-natural-sales-scenarios"
LLM_FIELDS = ("llm", "temperature", "thinking_budget", "reasoning_effort")
TARGET_CONFIG = {
    "llm": "gpt-5.5",
    "temperature": 0.1,
    "thinking_budget": 0,
    "reasoning_effort": "none",
}
EXPECTED_READBACK_CONFIG = {
    "llm": "gpt-5.5",
    "temperature": 0.1,
    "thinking_budget": None,
    "reasoning_effort": "none",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def write_json(name: str, payload: dict[str, Any]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / name).write_text(
        json.dumps(guards.sanitize(payload), indent=2, ensure_ascii=True) + "\n",
        encoding="ascii",
    )


def canonical_sha256(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(encoded.encode("ascii")).hexdigest()


def prompt(agent: dict[str, Any]) -> dict[str, Any]:
    return guards.agent_prompt(agent)


def llm_config(agent: dict[str, Any]) -> dict[str, Any]:
    current = prompt(agent)
    return {field: copy.deepcopy(current.get(field)) for field in LLM_FIELDS}


def protected_except_llm(agent: dict[str, Any]) -> dict[str, Any]:
    state = guards.protected_agent_state(agent)
    current_prompt = state["conversation_config"]["agent"]["prompt"]
    for field in LLM_FIELDS:
        current_prompt.pop(field, None)
    return state


def snapshot(phase: str, agent: dict[str, Any]) -> dict[str, Any]:
    summary = agent_guard.preflight(agent)
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "captured_at_utc": utc_now(),
        "phase": phase,
        "agent_id": agent.get("agent_id"),
        "agent_name": agent.get("name"),
        "llm_config": llm_config(agent),
        "llm_independent_protected_state_sha256": canonical_sha256(protected_except_llm(agent)),
        "preflight": summary,
        "agent": guards.sanitize(agent),
        "outbound_calls_made": False,
    }


def patch_body(config: dict[str, Any]) -> dict[str, Any]:
    return {"conversation_config": {"agent": {"prompt": copy.deepcopy(config)}}}


def get_agent(api_key: str) -> dict[str, Any]:
    response = guards.json_request(
        "GET",
        f"/v1/convai/agents/{quote(AGENT_ID, safe='')}",
        api_key=api_key,
    )["response"]
    if not isinstance(response, dict):
        raise ValueError("live agent response is invalid")
    agent_guard.preflight(response)
    return response


def validate_target_model(api_key: str) -> dict[str, Any]:
    response = guards.json_request("GET", "/v1/convai/llm/list", api_key=api_key)["response"]
    models = response.get("llms") if isinstance(response, dict) else None
    if not isinstance(models, list):
        raise ValueError("ElevenLabs LLM list response is invalid")
    model = next(
        (item for item in models if isinstance(item, dict) and item.get("llm") == TARGET_CONFIG["llm"]),
        None,
    )
    if model is None:
        raise ValueError(f"target model {TARGET_CONFIG['llm']} is not available to this workspace")
    efforts = model.get("available_reasoning_efforts")
    if not isinstance(efforts, list) or TARGET_CONFIG["reasoning_effort"] not in efforts:
        raise ValueError("target model does not support reasoning_effort=none")
    deprecation = model.get("deprecation_info")
    if isinstance(deprecation, dict) and deprecation.get("is_deprecated"):
        raise ValueError("target model is deprecated")
    return model


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--confirm-provider-write", choices=(CONFIRM_TOKEN,), default=None)
    parser.add_argument("--verify-only", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    api_key = os.environ.get(API_KEY_ENV_VAR, "").strip()
    if not api_key:
        print(f"error: {API_KEY_ENV_VAR} is required", file=sys.stderr)
        return 2

    try:
        before = get_agent(api_key)
        if before.get("agent_id") != AGENT_ID or before.get("name") != AGENT_NAME:
            raise ValueError("refusing unexpected ElevenLabs agent")
        target_model = validate_target_model(api_key)
        before_config = llm_config(before)

        if args.verify_only:
            pre_path = OUT_DIR / "llm_experiment_gpt55_pre_patch_snapshot.json"
            if not pre_path.is_file():
                raise FileNotFoundError("pre-patch LLM experiment snapshot is missing")
            pre_snapshot = json.loads(pre_path.read_text(encoding="ascii"))
            before_hash = pre_snapshot.get("llm_independent_protected_state_sha256")
            after_hash = canonical_sha256(protected_except_llm(before))
            if before_config != EXPECTED_READBACK_CONFIG:
                raise ValueError(
                    f"live LLM readback mismatch: expected {EXPECTED_READBACK_CONFIG!r}, got {before_config!r}"
                )
            if before_hash != after_hash:
                raise ValueError("protected live agent state changed outside the approved LLM fields")
            write_json("llm_experiment_gpt55_post_patch_snapshot.json", snapshot("post_patch", before))
            result = {
                "checkpoint_id": CHECKPOINT_ID,
                "status": "passed",
                "verification_only": True,
                "provider_writes_made_by_verification": False,
                "after_llm_config": before_config,
                "target_exact_after_provider_normalization": True,
                "provider_normalization": {"thinking_budget": {"requested": 0, "readback": None}},
                "protected_state_preserved": True,
                "unrelated_tool_fingerprint_preserved": True,
                "knowledge_base_order_preserved": True,
                "analysis_criteria_preserved": True,
                "procedures_inactive": True,
                "outbound_calls_made": False,
            }
            write_json("llm_experiment_gpt55_patch_result.json", result)
            print(json.dumps(result, indent=2))
            return 0

        request_body = patch_body(TARGET_CONFIG)
        authorized = args.confirm_provider_write == CONFIRM_TOKEN

        write_json("llm_experiment_gpt55_pre_patch_snapshot.json", snapshot("pre_patch", before))
        write_json(
            "llm_experiment_gpt55_patch_plan.json",
            {
                "checkpoint_id": CHECKPOINT_ID,
                "agent_id": AGENT_ID,
                "agent_name": AGENT_NAME,
                "authorized": authorized,
                "hypothesis": "GPT-5.5 at low temperature follows unresolved-question and no-CTA state locks more reliably than GPT-5.4.",
                "fixed_cases": "existing live ELEVENLABS-036 tests and criteria",
                "baseline_llm_config": before_config,
                "target_llm_config": TARGET_CONFIG,
                "target_model_capabilities": target_model,
                "editable_surface": "conversation_config.agent.prompt LLM fields only",
                "forbidden_changes": [
                    "test definitions or criteria",
                    "prompt text",
                    "knowledge base attachments or order",
                    "tools or tool ids",
                    "voice or first message",
                    "dynamic variables or phone configuration",
                    "Analysis criteria",
                    "Procedures",
                    "outbound calls",
                ],
            },
        )
        write_json(
            "llm_experiment_gpt55_patch_request.json",
            {
                "method": "PATCH",
                "endpoint": f"/v1/convai/agents/{AGENT_ID}",
                "body": request_body,
            },
        )

        if not authorized:
            result = {
                "checkpoint_id": CHECKPOINT_ID,
                "status": "plan_only_missing_confirmation",
                "provider_writes_made": False,
                "required_confirmation": CONFIRM_TOKEN,
                "outbound_calls_made": False,
            }
            write_json("llm_experiment_gpt55_patch_result.json", result)
            print(json.dumps(result, indent=2))
            return 0

        response = guards.json_request(
            "PATCH",
            f"/v1/convai/agents/{quote(AGENT_ID, safe='')}",
            api_key=api_key,
            body=request_body,
        )
        after = get_agent(api_key)
        after_config = llm_config(after)
        collateral_preserved = protected_except_llm(before) == protected_except_llm(after)
        if after_config != EXPECTED_READBACK_CONFIG:
            raise ValueError(
                f"live LLM readback mismatch: expected {EXPECTED_READBACK_CONFIG!r}, got {after_config!r}"
            )
        if not collateral_preserved:
            raise ValueError("protected live agent state changed outside the approved LLM fields")

        write_json("llm_experiment_gpt55_post_patch_snapshot.json", snapshot("post_patch", after))
        result = {
            "checkpoint_id": CHECKPOINT_ID,
            "status": "passed",
            "provider_writes_made": True,
            "status_code": response.get("status_code"),
            "before_llm_config": before_config,
            "after_llm_config": after_config,
            "target_exact": True,
            "protected_state_preserved": True,
            "unrelated_tool_fingerprint_preserved": (
                agent_guard.preflight(before)["unrelated_tool_fingerprint"]
                == agent_guard.preflight(after)["unrelated_tool_fingerprint"]
            ),
            "knowledge_base_order_preserved": True,
            "analysis_criteria_preserved": True,
            "procedures_inactive": True,
            "outbound_calls_made": False,
        }
        write_json("llm_experiment_gpt55_patch_result.json", result)
        print(json.dumps(result, indent=2))
        return 0
    except Exception as exc:
        error = guards.safe_error(exc)
        write_json(
            "llm_experiment_gpt55_patch_result.json",
            {
                "checkpoint_id": CHECKPOINT_ID,
                "status": "failed",
                "error": error,
                "outbound_calls_made": False,
            },
        )
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
