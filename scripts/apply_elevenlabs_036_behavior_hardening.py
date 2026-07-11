#!/usr/bin/env python3
"""Guarded prompt and in-place KB patch for genuine ELEVENLABS-036 failures."""
from __future__ import annotations

import argparse
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
import apply_elevenlabs_038_end_call_terminal_control as live_helpers
import apply_elevenlabs_039_independent_test_hardening as guards


CHECKPOINT_ID = "ELEVENLABS-036-natural-sales-scenarios"
AGENT_ID = "agent_7801kt0g32zxf4f8x5zkykj7syty"
AGENT_NAME = "web design"
API_KEY_ENV_VAR = "ELEVENLABS_API_KEY"
CONFIRM_TOKEN = "confirm-provider-write"
OUT_DIR = ROOT / "research/experiments/generated/ELEVENLABS-036-natural-sales-scenarios"
PROMPT_PATH = ROOT / "runtime/providers/elevenlabs_agents/prompts/web_design_atlas_sales_prompt.md"
KB_DIR = ROOT / "runtime/providers/elevenlabs_agents/knowledge_base/atlas_web_studio"
KB_DOCS = (
    "atlas_offer_facts.md",
    "atlas_output_quality_rules.md",
    "atlas_price_scope_cost_drivers.md",
)
EXPECTED_LLM = {
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


def llm_config(agent: dict[str, Any]) -> dict[str, Any]:
    prompt = guards.agent_prompt(agent)
    return {field: prompt.get(field) for field in EXPECTED_LLM}


def summary(agent: dict[str, Any]) -> dict[str, Any]:
    preflight = agent_guard.preflight(agent)
    return {
        "agent_id": agent.get("agent_id"),
        "agent_name": agent.get("name"),
        "llm_config": llm_config(agent),
        "prompt_sha256": preflight["prompt_sha256"],
        "knowledge_base_count": preflight["knowledge_base_count"],
        "knowledge_base_ids_in_order": preflight["knowledge_base_ids_in_order"],
        "knowledge_base_names_in_order": preflight["knowledge_base_names_in_order"],
        "unrelated_tool_fingerprint": preflight["unrelated_tool_fingerprint"],
        "analysis_criteria_count": preflight["analysis_criteria_count"],
        "analysis_criterion_ids_in_order": preflight["analysis_criterion_ids_in_order"],
        "procedures_inactive": preflight["procedures_inactive"],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--confirm-provider-write", choices=(CONFIRM_TOKEN,), default=None)
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
        if llm_config(before) != EXPECTED_LLM:
            raise ValueError(f"unexpected live LLM configuration: {llm_config(before)!r}")

        canonical_kb, selection = live_helpers.select_canonical_kb_docs(before, api_key)
        kb_by_name = {item["name"]: item for item in canonical_kb}
        for name in KB_DOCS:
            entry = kb_by_name.get(name)
            if not entry or entry.get("type") != "file":
                raise ValueError(f"active KB document is missing or not file-backed: {name}")
            if not (KB_DIR / name).is_file():
                raise FileNotFoundError(str(KB_DIR / name))

        authorized = args.confirm_provider_write == CONFIRM_TOKEN
        write_json(
            "behavior_hardening_pre_patch_snapshot.json",
            {
                "checkpoint_id": CHECKPOINT_ID,
                "captured_at_utc": utc_now(),
                "phase": "pre_patch",
                "summary": summary(before),
                "kb_selection": selection["selection"],
                "outbound_calls_made": False,
            },
        )
        requests = [
            {
                "request_id": f"update_kb::{name}",
                "method": "PATCH",
                "endpoint": f"/v1/convai/knowledge-base/{kb_by_name[name]['id']}/update-file",
                "document_id": kb_by_name[name]["id"],
                "name": name,
                "source_path": str((KB_DIR / name).relative_to(ROOT)).replace("\\", "/"),
            }
            for name in KB_DOCS
        ]
        requests.append(
            {
                "request_id": "patch_agent_prompt_only",
                "method": "PATCH",
                "endpoint": f"/v1/convai/agents/{AGENT_ID}",
                "body": agent_guard.prompt_patch_body(PROMPT_PATH.read_text(encoding="utf-8").strip()),
            }
        )
        write_json(
            "behavior_hardening_patch_plan.json",
            {
                "checkpoint_id": CHECKPOINT_ID,
                "authorized": authorized,
                "agent_id": AGENT_ID,
                "writes": [item["request_id"] for item in requests],
                "modified_behavior": [
                    "CRM whole-project versus connection-only clarification",
                    "single-homepage visual mockup boundary",
                ],
                "tests_or_criteria_changed": False,
                "analysis_changed": False,
                "procedures_changed": False,
                "knowledge_base_attachments_changed": False,
                "outbound_calls_made": False,
            },
        )
        write_json("behavior_hardening_patch_requests.json", {"requests": requests})
        if not authorized:
            result = {
                "checkpoint_id": CHECKPOINT_ID,
                "status": "plan_only_missing_confirmation",
                "provider_writes_made": False,
                "required_confirmation": CONFIRM_TOKEN,
                "outbound_calls_made": False,
            }
            write_json("behavior_hardening_patch_result.json", result)
            print(json.dumps(result, indent=2))
            return 0

        updates: list[dict[str, Any]] = []
        for name in KB_DOCS:
            entry = kb_by_name[name]
            response = live_helpers.multipart_update_file(
                api_key=api_key,
                documentation_id=entry["id"],
                source_path=KB_DIR / name,
            )
            updates.append(
                {
                    "name": name,
                    "document_id": entry["id"],
                    "status_code": response.get("status_code"),
                }
            )

        prompt_response = guards.json_request(
            "PATCH",
            f"/v1/convai/agents/{quote(AGENT_ID, safe='')}",
            api_key=api_key,
            body=agent_guard.prompt_patch_body(PROMPT_PATH.read_text(encoding="utf-8").strip()),
        )
        after = get_agent(api_key)
        if agent_guard.prompt_text(after) != PROMPT_PATH.read_text(encoding="utf-8").strip():
            raise ValueError("live prompt does not match the repo")
        if guards.protected_agent_state(before) != guards.protected_agent_state(after):
            raise ValueError("protected agent state changed outside prompt text")
        before_summary = summary(before)
        after_summary = summary(after)
        if before_summary["unrelated_tool_fingerprint"] != after_summary["unrelated_tool_fingerprint"]:
            raise ValueError("unrelated tool fingerprint changed")
        if llm_config(after) != EXPECTED_LLM:
            raise ValueError("live LLM configuration changed during behavior patch")

        write_json(
            "behavior_hardening_post_patch_snapshot.json",
            {
                "checkpoint_id": CHECKPOINT_ID,
                "captured_at_utc": utc_now(),
                "phase": "post_patch",
                "summary": after_summary,
                "outbound_calls_made": False,
            },
        )
        result = {
            "checkpoint_id": CHECKPOINT_ID,
            "status": "passed",
            "provider_writes_made": True,
            "kb_updates": updates,
            "prompt_status_code": prompt_response.get("status_code"),
            "prompt_exact": True,
            "protected_state_preserved": True,
            "unrelated_tool_fingerprint_preserved": True,
            "llm_config_preserved": True,
            "knowledge_base_order_preserved": True,
            "analysis_criteria_preserved": True,
            "procedures_inactive": True,
            "tests_or_criteria_changed": False,
            "outbound_calls_made": False,
        }
        write_json("behavior_hardening_patch_result.json", result)
        print(json.dumps(result, indent=2))
        return 0
    except Exception as exc:
        error = guards.safe_error(exc)
        write_json(
            "behavior_hardening_patch_result.json",
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
