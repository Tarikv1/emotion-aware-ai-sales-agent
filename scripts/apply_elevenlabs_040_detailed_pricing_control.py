#!/usr/bin/env python3
"""Guarded plan/live patcher for ELEVENLABS-040 detailed pricing control.

Default mode performs fresh live GET readback and writes sanitized plan-only
evidence. Provider writes require the exact confirm-provider-write token.
This command never runs simulations or outbound calls.
"""
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
SCRIPT_DIR = Path(__file__).resolve().parent
for path in (ROOT, SCRIPT_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

try:
    import apply_elevenlabs_039_independent_test_hardening as guards
    from apply_elevenlabs_038_end_call_terminal_control import (
        active_kb_paths,
        get_prompt,
        json_request,
        multipart_update_file,
        safe_error_message,
        summarize_tools,
        unrelated_tool_fingerprint,
    )
except ImportError as exc:  # pragma: no cover - import paths are environment-specific
    raise SystemExit(f"error: cannot import required guarded ElevenLabs helpers: {exc}") from exc


API_KEY_ENV_VAR = "ELEVENLABS_API_KEY"
CHECKPOINT_ID = "ELEVENLABS-040-detailed-pricing-control"
AGENT_ID = "agent_7801kt0g32zxf4f8x5zkykj7syty"
AGENT_NAME = "web design"
CONFIRM_TOKEN = "confirm-provider-write"
TARGET_LLM = {
    "llm": "gpt-5.5",
    "temperature": 0.1,
    "thinking_budget": None,
    "reasoning_effort": "none",
}
TARGET_PRICE_VARIABLES = {
    "website_starting_price": "$500",
    "website_basic_site_range": "$900-$1,500",
    "website_light_feature_range": "$1,800-$3,000",
    "website_workflow_content_range": "$2,800-$4,500",
    "website_integration_heavy_range": "$4,000-$6,500",
    "website_premium_price_anchor": "$6,500",
}
KB_DOCS = (
    "atlas_offer_facts.md",
    "atlas_price_scope_cost_drivers.md",
    "atlas_output_quality_rules.md",
)
KNOWN_KB_DOC_IDS = {
    "atlas_offer_facts.md": "HYTfB5s1Z8LzOw8oBADt",
    "atlas_price_scope_cost_drivers.md": "vGKk14CCzKqGW3GxgUqA",
    "atlas_output_quality_rules.md": "GS5wqgcUomoJmqWCEpP7",
}
PROMPT_PATH = ROOT / "runtime" / "providers" / "elevenlabs_agents" / "prompts" / "web_design_atlas_sales_prompt.md"
KB_ROOT = ROOT / "runtime" / "providers" / "elevenlabs_agents" / "knowledge_base" / "atlas_web_studio"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def sanitize(value: Any) -> Any:
    return guards.sanitize(value)


def canonical_sha256(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(encoded.encode("ascii")).hexdigest()


def merged_dynamic_variables(agent: dict[str, Any]) -> dict[str, Any]:
    conversation_config = agent.get("conversation_config")
    if not isinstance(conversation_config, dict):
        raise ValueError("agent conversation_config must be an object")
    agent_config = conversation_config.get("agent")
    if not isinstance(agent_config, dict):
        raise ValueError("agent conversation_config.agent must be an object")
    dynamic = copy.deepcopy(agent_config.get("dynamic_variables") or {})
    if not isinstance(dynamic, dict):
        raise ValueError("agent dynamic_variables must be an object")
    placeholders = dynamic.get("dynamic_variable_placeholders")
    if not isinstance(placeholders, dict):
        raise ValueError("agent dynamic_variable_placeholders must be an object")
    placeholders.update(TARGET_PRICE_VARIABLES)
    dynamic["dynamic_variable_placeholders"] = placeholders
    return dynamic


def patch_body(agent: dict[str, Any]) -> dict[str, Any]:
    return {
        "conversation_config": {
            "agent": {
                "prompt": {"prompt": PROMPT_PATH.read_text(encoding="utf-8").strip()},
                "dynamic_variables": merged_dynamic_variables(agent),
            }
        }
    }


def collateral_state(agent: dict[str, Any]) -> dict[str, Any]:
    state = guards.protected_agent_state(copy.deepcopy(agent))
    agent_config = state["conversation_config"]["agent"]
    prompt = agent_config["prompt"]
    prompt.pop("prompt", None)
    dynamic = agent_config.get("dynamic_variables")
    if not isinstance(dynamic, dict):
        raise ValueError("protected dynamic_variables must be an object")
    placeholders = dynamic.get("dynamic_variable_placeholders")
    if not isinstance(placeholders, dict):
        raise ValueError("protected dynamic_variable_placeholders must be an object")
    for key in TARGET_PRICE_VARIABLES:
        placeholders.pop(key, None)
    return state


def kb_entries_by_name(agent: dict[str, Any]) -> dict[str, dict[str, Any]]:
    entries = guards.kb_entries(agent)
    grouped: dict[str, list[dict[str, Any]]] = {}
    for entry in entries:
        name = str(entry.get("name", "")).strip()
        grouped.setdefault(name, []).append(entry)
    duplicates = sorted(name for name, values in grouped.items() if len(values) > 1)
    if duplicates:
        raise ValueError(f"duplicate attached KB docs: {duplicates}")
    return {name: values[0] for name, values in grouped.items()}


def validate_target_llm(agent: dict[str, Any]) -> None:
    prompt = get_prompt(agent)
    actual = {
        "llm": prompt.get("llm"),
        "temperature": prompt.get("temperature"),
        "thinking_budget": prompt.get("thinking_budget"),
        "reasoning_effort": prompt.get("reasoning_effort"),
    }
    if actual != TARGET_LLM:
        raise ValueError(f"target LLM settings mismatch: expected {TARGET_LLM!r}, got {actual!r}")


def validate_preflight(agent: dict[str, Any]) -> dict[str, Any]:
    if agent.get("agent_id") != AGENT_ID or agent.get("name") != AGENT_NAME:
        raise ValueError("refusing unexpected ElevenLabs agent")
    prompt = get_prompt(agent)
    prompt_text = str(prompt.get("prompt", ""))
    if "Atlas Web Studio" not in prompt_text or "Mission: earn permission" not in prompt_text:
        raise ValueError("target prompt is missing required Atlas markers")
    validate_target_llm(agent)

    expected_kb_order = [path.name for path in active_kb_paths()]
    entries = guards.kb_entries(agent)
    names_in_order = [str(item.get("name", "")).strip() for item in entries]
    ids_in_order = guards.attachment_ids(entries)
    if names_in_order != expected_kb_order:
        raise ValueError(f"knowledge-base name/order mismatch: expected {expected_kb_order}, got {names_in_order}")
    if len(ids_in_order) != 17 or len(set(ids_in_order)) != 17:
        raise ValueError("live agent must have 17 unique KB attachment IDs")

    by_name = kb_entries_by_name(agent)
    target_docs: dict[str, dict[str, str]] = {}
    for name in KB_DOCS:
        entry = by_name.get(name)
        if not entry:
            raise ValueError(f"live agent missing target KB doc {name}")
        live_id = str(entry.get("id", "")).strip()
        expected_id = KNOWN_KB_DOC_IDS[name]
        if live_id != expected_id:
            raise ValueError(f"target KB doc {name} ID mismatch: expected {expected_id}, got {live_id}")
        source_path = KB_ROOT / name
        if not source_path.is_file():
            raise FileNotFoundError(str(source_path))
        target_docs[name] = {
            "id": live_id,
            "source_path": str(source_path.relative_to(ROOT)).replace("\\", "/"),
        }

    tools = summarize_tools(agent)
    if tools.get("built_in_end_call_count") != 1:
        raise ValueError("live agent must have exactly one built-in end_call")
    if tools.get("duplicate_custom_or_server_end_call_count") != 0:
        raise ValueError("live agent has custom/server end_call duplicates")
    if not guards.procedures_inactive(agent):
        raise ValueError("live agent Procedures must be inactive")
    criteria = guards.analysis_criteria(agent)
    if len(criteria) != 30:
        raise ValueError(f"live agent must have 30 Analysis criteria, found {len(criteria)}")
    criteria_ids = [str(item.get("id", "")).strip() for item in criteria]
    if any(not item for item in criteria_ids) or len(set(criteria_ids)) != len(criteria_ids):
        raise ValueError("Analysis criterion IDs must be present and unique")

    dynamic = merged_dynamic_variables(agent)
    protected = {
        "knowledge_base_ids_in_order": ids_in_order,
        "unrelated_tool_fingerprint": sanitize(unrelated_tool_fingerprint(agent)),
        "analysis_criterion_ids_in_order": criteria_ids,
        "procedures_inactive": guards.procedures_inactive(agent),
        "collateral_state_sha256": canonical_sha256(collateral_state(agent)),
    }
    return {
        **protected,
        "knowledge_base_names_in_order": names_in_order,
        "target_kb_docs": target_docs,
        "tool_summary": sanitize(tools),
        "llm": TARGET_LLM,
        "dynamic_variable_placeholders_after_patch": sanitize(dynamic.get("dynamic_variable_placeholders", {})),
    }


def protected_fingerprint(agent: dict[str, Any], preflight: dict[str, Any]) -> dict[str, Any]:
    return {
        "knowledge_base_ids_in_order": preflight["knowledge_base_ids_in_order"],
        "unrelated_tool_fingerprint": preflight["unrelated_tool_fingerprint"],
        "analysis_criterion_ids_in_order": preflight["analysis_criterion_ids_in_order"],
        "procedures_inactive": preflight["procedures_inactive"],
        "collateral_state_sha256": canonical_sha256(collateral_state(agent)),
    }


def assert_fingerprint_matches(label: str, expected: dict[str, Any], actual: dict[str, Any]) -> None:
    if actual != expected:
        raise ValueError(f"{label} protected fingerprint mismatch: expected={sanitize(expected)!r}, actual={sanitize(actual)!r}")


def patch_requests(agent: dict[str, Any], preflight: dict[str, Any]) -> list[dict[str, Any]]:
    requests: list[dict[str, Any]] = []
    for name in KB_DOCS:
        doc = preflight["target_kb_docs"][name]
        requests.append(
            {
                "request_id": f"update_kb_file::{name}",
                "method": "PATCH",
                "endpoint": f"/v1/convai/knowledge-base/{doc['id']}/update-file",
                "known_document_id": doc["id"],
                "content_type": "multipart/form-data",
                "source_path": doc["source_path"],
            }
        )
    requests.append(
        {
            "request_id": "patch_agent::prompt_dynamic_variables",
            "method": "PATCH",
            "endpoint": f"/v1/convai/agents/{AGENT_ID}",
            "content_type": "application/json",
            "body": sanitize(patch_body(agent)),
        }
    )
    return requests


def snapshot_payload(*, phase: str, agent: dict[str, Any] | None, preflight: dict[str, Any] | None, error: str | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "checkpoint_id": CHECKPOINT_ID,
        "phase": phase,
        "captured_at_utc": utc_now(),
        "agent_id": AGENT_ID,
        "agent_name": AGENT_NAME,
        "simulations_run": False,
        "outbound_calls_made": False,
    }
    if agent is not None:
        payload["agent"] = sanitize(agent)
    if preflight is not None:
        payload["protected_fingerprint"] = sanitize(protected_fingerprint(agent or {}, preflight)) if agent else sanitize(preflight)
        payload["preflight"] = sanitize(preflight)
    if error is not None:
        payload["error"] = error
    return payload


def dynamic_variables_readback(agent: dict[str, Any]) -> dict[str, Any]:
    conversation_config = agent.get("conversation_config")
    if not isinstance(conversation_config, dict):
        raise ValueError("agent conversation_config must be an object")
    agent_config = conversation_config.get("agent")
    if not isinstance(agent_config, dict):
        raise ValueError("agent conversation_config.agent must be an object")
    dynamic = agent_config.get("dynamic_variables")
    if not isinstance(dynamic, dict):
        raise ValueError("agent dynamic_variables must be an object")
    placeholders = dynamic.get("dynamic_variable_placeholders")
    if not isinstance(placeholders, dict):
        raise ValueError("agent dynamic_variable_placeholders must be an object")
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "captured_at_utc": utc_now(),
        "agent_id": AGENT_ID,
        "dynamic_variables": sanitize(dynamic),
        "target_price_values_current": {key: placeholders.get(key) for key in TARGET_PRICE_VARIABLES},
        "target_price_values_planned": TARGET_PRICE_VARIABLES,
    }


def actual_dynamic_variable_placeholders(agent: dict[str, Any]) -> dict[str, Any]:
    conversation_config = agent.get("conversation_config")
    if not isinstance(conversation_config, dict):
        raise ValueError("agent conversation_config must be an object")
    agent_config = conversation_config.get("agent")
    if not isinstance(agent_config, dict):
        raise ValueError("agent conversation_config.agent must be an object")
    dynamic = agent_config.get("dynamic_variables")
    if not isinstance(dynamic, dict):
        raise ValueError("agent dynamic_variables must be an object")
    placeholders = dynamic.get("dynamic_variable_placeholders")
    if not isinstance(placeholders, dict):
        raise ValueError("agent dynamic_variable_placeholders must be an object")
    return placeholders


def write_plan_only_outputs(agent: dict[str, Any], preflight: dict[str, Any], requests: list[dict[str, Any]], status: str) -> None:
    fingerprint = protected_fingerprint(agent, preflight)
    write_json(OUT_DIR / "live_agent_pre_patch_snapshot.json", snapshot_payload(phase="pre_patch", agent=agent, preflight=preflight))
    write_json(
        OUT_DIR / "live_agent_patch_plan.json",
        {
            "checkpoint_id": CHECKPOINT_ID,
            "agent_id": AGENT_ID,
            "agent_name": AGENT_NAME,
            "status": "planned",
            "authorization_confirmed": False,
            "provider_writes_allowed": False,
            "provider_writes_made": False,
            "target_llm_preserved": TARGET_LLM,
            "target_price_variables": TARGET_PRICE_VARIABLES,
            "kb_documents_planned_for_in_place_update": list(KB_DOCS),
            "known_kb_document_ids": KNOWN_KB_DOC_IDS,
            "minimal_agent_patch_fields": ["conversation_config.agent.prompt.prompt", "conversation_config.agent.dynamic_variables"],
            "forbidden_operations": [
                "simulations",
                "outbound_calls",
                "new_knowledge_base_docs",
                "knowledge_base_reorder",
                "Analysis_updates",
                "Procedures_updates",
                "voice_updates",
                "LLM_updates",
                "first_message_updates",
                "phone_updates",
                "tool_updates",
                "MCP_updates",
                "unrelated_dynamic_variable_replacement",
            ],
            "preflight": sanitize(preflight),
        },
    )
    write_json(
        OUT_DIR / "live_agent_patch_requests.json",
        {
            "checkpoint_id": CHECKPOINT_ID,
            "provider_writes_allowed": False,
            "provider_writes_made": False,
            "requests": requests,
        },
    )
    write_json(
        OUT_DIR / "live_agent_patch_result.json",
        {
            "checkpoint_id": CHECKPOINT_ID,
            "status": status,
            "provider_writes_made": False,
            "required_confirmation": CONFIRM_TOKEN,
            "simulations_run": False,
            "outbound_calls_made": False,
        },
    )
    write_json(OUT_DIR / "live_agent_post_patch_snapshot.json", snapshot_payload(phase="not_written", agent=agent, preflight=preflight))
    write_json(OUT_DIR / "live_dynamic_variables_readback.json", dynamic_variables_readback(agent))
    write_json(OUT_DIR / "unrelated_tool_fingerprint_before.json", {"checkpoint_id": CHECKPOINT_ID, "fingerprint": fingerprint})
    write_json(OUT_DIR / "unrelated_tool_fingerprint_after.json", {"checkpoint_id": CHECKPOINT_ID, "fingerprint": fingerprint})


def write_provider_changes(*, api_key: str, agent: dict[str, Any], preflight: dict[str, Any], requests: list[dict[str, Any]]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    expected_before = protected_fingerprint(agent, preflight)
    results: list[dict[str, Any]] = []
    for request in requests:
        request_id = request["request_id"]
        if request_id.startswith("update_kb_file::"):
            name = request_id.split("::", 1)[1]
            source_path = KB_ROOT / name
            response = multipart_update_file(
                api_key=api_key,
                documentation_id=KNOWN_KB_DOC_IDS[name],
                source_path=source_path,
            )
        elif request_id == "patch_agent::prompt_dynamic_variables":
            response = json_request(
                "PATCH",
                f"/v1/convai/agents/{quote(AGENT_ID, safe='')}",
                api_key=api_key,
                body=patch_body(agent),
            )
        else:
            raise ValueError(f"unknown write request {request_id}")
        results.append(
            {
                "request_id": request_id,
                "status_code": response.get("status_code"),
                "response": sanitize(response.get("response")),
            }
        )

    post = json_request("GET", f"/v1/convai/agents/{quote(AGENT_ID, safe='')}", api_key=api_key)["response"]
    if not isinstance(post, dict):
        raise ValueError("post-patch agent GET response must be an object")
    post_preflight = validate_preflight(post)
    assert_fingerprint_matches("post-patch", expected_before, protected_fingerprint(post, post_preflight))
    if get_prompt(post).get("prompt") != PROMPT_PATH.read_text(encoding="utf-8").strip():
        raise ValueError("post-patch prompt does not exactly match repo prompt")
    placeholders = actual_dynamic_variable_placeholders(post)
    for key, expected in TARGET_PRICE_VARIABLES.items():
        if placeholders.get(key) != expected:
            raise ValueError(f"post-patch dynamic variable {key} mismatch")
    return post, results


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Guarded ELEVENLABS-040 Atlas pricing patcher; dry-run by default.")
    parser.add_argument("--confirm-provider-write", default=None, help=f"Exact token required for writes: {CONFIRM_TOKEN}")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    api_key = os.environ.get(API_KEY_ENV_VAR, "").strip()
    if not api_key:
        print(f"error: {API_KEY_ENV_VAR} is required for fresh live GET preflight", file=sys.stderr)
        return 2

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, Any]] = []
    before_agent: dict[str, Any] | None = None
    before_preflight: dict[str, Any] | None = None
    try:
        if not PROMPT_PATH.read_text(encoding="utf-8").strip():
            raise ValueError("repo prompt is empty")
        before_agent = json_request("GET", f"/v1/convai/agents/{quote(AGENT_ID, safe='')}", api_key=api_key)["response"]
        if not isinstance(before_agent, dict):
            raise ValueError("agent GET response must be an object")
        before_preflight = validate_preflight(before_agent)
        requests = patch_requests(before_agent, before_preflight)
        authorization_confirmed = args.confirm_provider_write == CONFIRM_TOKEN
        if not authorization_confirmed:
            write_plan_only_outputs(before_agent, before_preflight, requests, "plan_only_missing_confirmation")
            print(
                json.dumps(
                    {
                        "status": "plan_only_missing_confirmation",
                        "provider_writes_made": False,
                        "plan": str(OUT_DIR / "live_agent_patch_plan.json"),
                    },
                    indent=2,
                )
            )
            return 0

        post_agent, results = write_provider_changes(
            api_key=api_key,
            agent=before_agent,
            preflight=before_preflight,
            requests=requests,
        )
        post_preflight = validate_preflight(post_agent)
        write_json(OUT_DIR / "live_agent_pre_patch_snapshot.json", snapshot_payload(phase="pre_patch", agent=before_agent, preflight=before_preflight))
        write_json(OUT_DIR / "live_agent_patch_plan.json", {"checkpoint_id": CHECKPOINT_ID, "provider_writes_allowed": True, "preflight": sanitize(before_preflight)})
        write_json(OUT_DIR / "live_agent_patch_requests.json", {"checkpoint_id": CHECKPOINT_ID, "provider_writes_allowed": True, "requests": requests})
        write_json(OUT_DIR / "live_agent_post_patch_snapshot.json", snapshot_payload(phase="post_patch", agent=post_agent, preflight=post_preflight))
        write_json(OUT_DIR / "live_dynamic_variables_readback.json", dynamic_variables_readback(post_agent))
        write_json(OUT_DIR / "unrelated_tool_fingerprint_before.json", {"checkpoint_id": CHECKPOINT_ID, "fingerprint": protected_fingerprint(before_agent, before_preflight)})
        write_json(OUT_DIR / "unrelated_tool_fingerprint_after.json", {"checkpoint_id": CHECKPOINT_ID, "fingerprint": protected_fingerprint(post_agent, post_preflight)})
        write_json(
            OUT_DIR / "live_agent_patch_result.json",
            {
                "checkpoint_id": CHECKPOINT_ID,
                "status": "passed",
                "provider_writes_made": True,
                "writes": results,
                "simulations_run": False,
                "outbound_calls_made": False,
            },
        )
        print(json.dumps({"status": "passed", "provider_writes_made": True}, indent=2))
        return 0
    except Exception as exc:
        error = safe_error_message(exc)
        write_json(
            OUT_DIR / "live_agent_patch_result.json",
            {
                "checkpoint_id": CHECKPOINT_ID,
                "status": "failed",
                "provider_writes_made": bool(results),
                "writes": results,
                "error": error,
                "simulations_run": False,
                "outbound_calls_made": False,
            },
        )
        write_json(
            OUT_DIR / "live_agent_post_patch_snapshot.json",
            snapshot_payload(phase="failed", agent=before_agent, preflight=before_preflight, error=error),
        )
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
