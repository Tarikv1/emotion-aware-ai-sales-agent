#!/usr/bin/env python3
"""Guarded prompt-only live patch for ELEVENLABS-036 natural-sales failures."""
from __future__ import annotations

import argparse
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

import apply_elevenlabs_039_independent_test_hardening as guards


CHECKPOINT_ID = "ELEVENLABS-036-natural-sales-scenarios"
AGENT_ID = "agent_7801kt0g32zxf4f8x5zkykj7syty"
AGENT_NAME = "web design"
CONFIRM_TOKEN = "confirm-provider-write"
API_KEY_ENV_VAR = "ELEVENLABS_API_KEY"
PROMPT_PATH = ROOT / "runtime/providers/elevenlabs_agents/prompts/web_design_atlas_sales_prompt.md"
MANIFEST_PATH = ROOT / "runtime/providers/elevenlabs_agents/manifests/web_design_sales_spine_compression.package.json"
OUT_DIR = ROOT / "research/experiments/generated/ELEVENLABS-036-natural-sales-scenarios"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def write_json(name: str, payload: dict[str, Any]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / name).write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def expected_kb_names() -> list[str]:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    paths = manifest["active_kb_recommendation"]["recommended_upload_docs"]
    return [Path(path).name for path in paths]


def prompt_text(agent: dict[str, Any]) -> str:
    value = guards.agent_prompt(agent).get("prompt")
    if not isinstance(value, str) or not value.strip():
        raise ValueError("live agent prompt text is missing")
    return value.strip()


def preflight(agent: dict[str, Any]) -> dict[str, Any]:
    if agent.get("agent_id") != AGENT_ID or agent.get("name") != AGENT_NAME:
        raise ValueError("refusing unexpected ElevenLabs agent")
    entries = guards.kb_entries(agent)
    ids = guards.attachment_ids(entries)
    names = [str(item.get("name", "")) for item in entries]
    if len(ids) != 17 or len(set(ids)) != 17:
        raise ValueError("live agent must have 17 unique KB attachments")
    if names != expected_kb_names():
        raise ValueError("live KB order does not match the active manifest")
    tool_summary = guards.active_end_call_summary(agent)
    if tool_summary.get("built_in_end_call_count") != 1:
        raise ValueError("live agent must have exactly one built-in end_call")
    if tool_summary.get("duplicate_custom_or_server_end_call_count") != 0:
        raise ValueError("live agent has a custom/server end_call duplicate")
    criteria = guards.analysis_criteria(agent)
    if len(criteria) != 30:
        raise ValueError(f"live agent must have 30 Analysis criteria, found {len(criteria)}")
    if not guards.procedures_inactive(agent):
        raise ValueError("live agent Procedures must remain inactive")
    protected = guards.protected_state_report(agent)
    return {
        "agent_id": AGENT_ID,
        "agent_name": AGENT_NAME,
        "prompt_sha256": sha256_text(prompt_text(agent)),
        "knowledge_base_count": len(ids),
        "knowledge_base_ids_in_order": ids,
        "knowledge_base_names_in_order": names,
        "tool_summary": guards.sanitize(tool_summary),
        "analysis_criteria_count": len(criteria),
        "analysis_criterion_ids_in_order": protected["analysis_criterion_ids_in_order"],
        "procedures_inactive": True,
        "unrelated_tool_fingerprint": protected["unrelated_tool_fingerprint"],
        "protected_state_sha256": protected["protected_state_sha256"],
    }


def prompt_patch_body(value: str) -> dict[str, Any]:
    return {"conversation_config": {"agent": {"prompt": {"prompt": value}}}}


def snapshot(phase: str, agent: dict[str, Any], summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "captured_at_utc": utc_now(),
        "phase": phase,
        "summary": summary,
        "protected_state": guards.protected_state_report(agent),
        "simulations_run": False,
        "outbound_calls_made": False,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Guarded ELEVENLABS-036 prompt-only live patch.")
    parser.add_argument("--confirm-provider-write", default=None, help=f"Exact token required: {CONFIRM_TOKEN}")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    api_key = os.environ.get(API_KEY_ENV_VAR, "").strip()
    if not api_key:
        print(f"error: {API_KEY_ENV_VAR} is required", file=sys.stderr)
        return 2
    repo_prompt = PROMPT_PATH.read_text(encoding="utf-8").strip()
    if not repo_prompt:
        print("error: repo prompt is empty", file=sys.stderr)
        return 2

    try:
        before = guards.json_request(
            "GET",
            f"/v1/convai/agents/{quote(AGENT_ID, safe='')}",
            api_key=api_key,
        )["response"]
        if not isinstance(before, dict):
            raise ValueError("pre-patch agent response is invalid")
        before_summary = preflight(before)
        write_json("live_prompt_hardening_pre_patch.json", snapshot("pre_patch", before, before_summary))

        request = {
            "request_id": "patch_agent_prompt_only",
            "method": "PATCH",
            "endpoint": f"/v1/convai/agents/{AGENT_ID}",
            "body": guards.sanitize(prompt_patch_body(repo_prompt)),
        }
        authorized = args.confirm_provider_write == CONFIRM_TOKEN
        write_json(
            "live_prompt_hardening_plan.json",
            {
                "checkpoint_id": CHECKPOINT_ID,
                "agent_id": AGENT_ID,
                "authorized": authorized,
                "writes": ["patch_agent_prompt_only"],
                "repo_prompt_sha256": sha256_text(repo_prompt),
                "preflight": before_summary,
                "forbidden_operations": [
                    "knowledge_base_updates",
                    "test_updates",
                    "Analysis_updates",
                    "tool_updates",
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
        write_json("live_prompt_hardening_request.json", request)
        if not authorized:
            write_json(
                "live_prompt_hardening_result.json",
                {
                    "checkpoint_id": CHECKPOINT_ID,
                    "status": "plan_only_missing_confirmation",
                    "provider_writes_made": False,
                    "required_confirmation": CONFIRM_TOKEN,
                    "simulations_run": False,
                    "outbound_calls_made": False,
                },
            )
            print(json.dumps({"status": "plan_only_missing_confirmation", "writes": ["patch_agent_prompt_only"]}, indent=2))
            return 0

        response = guards.json_request(
            "PATCH",
            f"/v1/convai/agents/{quote(AGENT_ID, safe='')}",
            api_key=api_key,
            body=prompt_patch_body(repo_prompt),
        )
        after = guards.json_request(
            "GET",
            f"/v1/convai/agents/{quote(AGENT_ID, safe='')}",
            api_key=api_key,
        )["response"]
        if not isinstance(after, dict):
            raise ValueError("post-patch agent response is invalid")
        after_summary = preflight(after)
        if prompt_text(after) != repo_prompt:
            raise ValueError("live prompt does not exactly match the repo after PATCH")
        if guards.protected_agent_state(before) != guards.protected_agent_state(after):
            raise ValueError("protected agent state changed outside prompt text")
        if before_summary["unrelated_tool_fingerprint"] != after_summary["unrelated_tool_fingerprint"]:
            raise ValueError("unrelated tool fingerprint changed")
        write_json("live_prompt_hardening_post_patch.json", snapshot("post_patch", after, after_summary))
        result = {
            "checkpoint_id": CHECKPOINT_ID,
            "status": "passed",
            "provider_writes_made": True,
            "write": {
                "request_id": "patch_agent_prompt_only",
                "status_code": response.get("status_code"),
            },
            "prompt_exact": True,
            "protected_state_preserved": True,
            "unrelated_tool_fingerprint_preserved": True,
            "knowledge_base_order_preserved": True,
            "procedures_inactive": True,
            "simulations_run": False,
            "outbound_calls_made": False,
        }
        write_json("live_prompt_hardening_result.json", result)
        print(json.dumps(result, indent=2))
        return 0
    except Exception as exc:
        error = guards.safe_error(exc)
        write_json(
            "live_prompt_hardening_result.json",
            {
                "checkpoint_id": CHECKPOINT_ID,
                "status": "failed",
                "error": error,
                "simulations_run": False,
                "outbound_calls_made": False,
            },
        )
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
