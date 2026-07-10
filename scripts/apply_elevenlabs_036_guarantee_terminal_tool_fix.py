#!/usr/bin/env python3
"""Guarded built-in end_call description patch for the 036 guarantee flow."""
from __future__ import annotations

import argparse
import copy
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
import apply_elevenlabs_038_end_call_terminal_control as tool_contract
import apply_elevenlabs_039_independent_test_hardening as guards


CHECKPOINT_ID = "ELEVENLABS-036-natural-sales-scenarios"
AGENT_ID = "agent_7801kt0g32zxf4f8x5zkykj7syty"
CONFIRM_TOKEN = "confirm-provider-write"
API_KEY_ENV_VAR = "ELEVENLABS_API_KEY"
OUT_DIR = ROOT / "research/experiments/generated/ELEVENLABS-036-natural-sales-scenarios"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def write_json(name: str, payload: dict[str, Any]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / name).write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def live_end_call(agent: dict[str, Any]) -> dict[str, Any]:
    built_ins = guards.agent_prompt(agent).get("built_in_tools")
    if not isinstance(built_ins, dict):
        raise ValueError("live built_in_tools is not an object")
    end_call = built_ins.get("end_call")
    if not isinstance(end_call, dict):
        raise ValueError("live built-in end_call is missing")
    return end_call


def schema_without_description(tool: dict[str, Any]) -> dict[str, Any]:
    value = copy.deepcopy(tool)
    value.pop("description", None)
    return value


def patch_body(agent: dict[str, Any]) -> dict[str, Any]:
    built_ins = copy.deepcopy(guards.agent_prompt(agent).get("built_in_tools"))
    if not isinstance(built_ins, dict) or not isinstance(built_ins.get("end_call"), dict):
        raise ValueError("cannot build tool patch from invalid live built_in_tools")
    built_ins["end_call"]["description"] = tool_contract.END_CALL_DESCRIPTION
    return {"conversation_config": {"agent": {"prompt": {"built_in_tools": built_ins}}}}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Patch only the live built-in end_call description for ELEVENLABS-036.")
    parser.add_argument("--confirm-provider-write", default=None, help=f"Exact token required: {CONFIRM_TOKEN}")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    api_key = os.environ.get(API_KEY_ENV_VAR, "").strip()
    if not api_key:
        print(f"error: {API_KEY_ENV_VAR} is required", file=sys.stderr)
        return 2
    try:
        before = guards.json_request(
            "GET",
            f"/v1/convai/agents/{quote(AGENT_ID, safe='')}",
            api_key=api_key,
        )["response"]
        if not isinstance(before, dict):
            raise ValueError("pre-patch agent response is invalid")
        before_summary = agent_guard.preflight(before)
        before_tool = copy.deepcopy(live_end_call(before))
        request_body = patch_body(before)
        authorized = args.confirm_provider_write == CONFIRM_TOKEN
        write_json(
            "live_guarantee_tool_pre_patch.json",
            {
                "checkpoint_id": CHECKPOINT_ID,
                "captured_at_utc": utc_now(),
                "summary": before_summary,
                "built_in_end_call": guards.sanitize(before_tool),
                "simulations_run": False,
                "outbound_calls_made": False,
            },
        )
        write_json(
            "live_guarantee_tool_plan.json",
            {
                "checkpoint_id": CHECKPOINT_ID,
                "authorized": authorized,
                "writes": ["patch_builtin_end_call_description_only"],
                "target_description": tool_contract.END_CALL_DESCRIPTION,
                "preserved_end_call_schema": guards.sanitize(schema_without_description(before_tool)),
                "preflight": before_summary,
                "forbidden_operations": [
                    "prompt_text_updates",
                    "knowledge_base_updates",
                    "test_updates",
                    "Analysis_updates",
                    "unrelated_tool_updates",
                    "voice_updates",
                    "LLM_updates",
                    "first_message_updates",
                    "dynamic_variable_updates",
                    "phone_updates",
                    "Procedures_updates",
                    "outbound_calls",
                ],
            },
        )
        write_json(
            "live_guarantee_tool_request.json",
            {
                "request_id": "patch_builtin_end_call_description_only",
                "method": "PATCH",
                "endpoint": f"/v1/convai/agents/{AGENT_ID}",
                "body": guards.sanitize(request_body),
            },
        )
        if not authorized:
            result = {
                "checkpoint_id": CHECKPOINT_ID,
                "status": "plan_only_missing_confirmation",
                "provider_writes_made": False,
                "required_confirmation": CONFIRM_TOKEN,
                "simulations_run": False,
                "outbound_calls_made": False,
            }
            write_json("live_guarantee_tool_result.json", result)
            print(json.dumps(result, indent=2))
            return 0

        response = guards.json_request(
            "PATCH",
            f"/v1/convai/agents/{quote(AGENT_ID, safe='')}",
            api_key=api_key,
            body=request_body,
        )
        after = guards.json_request(
            "GET",
            f"/v1/convai/agents/{quote(AGENT_ID, safe='')}",
            api_key=api_key,
        )["response"]
        if not isinstance(after, dict):
            raise ValueError("post-patch agent response is invalid")
        after_summary = agent_guard.preflight(after)
        after_tool = live_end_call(after)
        if after_tool.get("description") != tool_contract.END_CALL_DESCRIPTION:
            raise ValueError("live end_call description does not match the repo")
        if schema_without_description(before_tool) != schema_without_description(after_tool):
            raise ValueError("end_call schema changed outside description")
        if before_summary["unrelated_tool_fingerprint"] != after_summary["unrelated_tool_fingerprint"]:
            raise ValueError("unrelated tool fingerprint changed")
        for field in (
            "knowledge_base_ids_in_order",
            "analysis_criterion_ids_in_order",
            "procedures_inactive",
        ):
            if before_summary[field] != after_summary[field]:
                raise ValueError(f"protected field changed: {field}")
        if guards.agent_prompt(before).get("prompt") != guards.agent_prompt(after).get("prompt"):
            raise ValueError("prompt text changed during tool-only patch")
        write_json(
            "live_guarantee_tool_post_patch.json",
            {
                "checkpoint_id": CHECKPOINT_ID,
                "captured_at_utc": utc_now(),
                "summary": after_summary,
                "built_in_end_call": guards.sanitize(after_tool),
                "simulations_run": False,
                "outbound_calls_made": False,
            },
        )
        result = {
            "checkpoint_id": CHECKPOINT_ID,
            "status": "passed",
            "provider_writes_made": True,
            "write": {"request_id": "patch_builtin_end_call_description_only", "status_code": response.get("status_code")},
            "description_exact": True,
            "end_call_schema_preserved": True,
            "unrelated_tool_fingerprint_preserved": True,
            "prompt_text_preserved": True,
            "knowledge_base_order_preserved": True,
            "analysis_order_preserved": True,
            "procedures_inactive": True,
            "simulations_run": False,
            "outbound_calls_made": False,
        }
        write_json("live_guarantee_tool_result.json", result)
        print(json.dumps(result, indent=2))
        return 0
    except Exception as exc:
        error = guards.safe_error(exc)
        result = {
            "checkpoint_id": CHECKPOINT_ID,
            "status": "failed",
            "error": error,
            "simulations_run": False,
            "outbound_calls_made": False,
        }
        write_json("live_guarantee_tool_result.json", result)
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
