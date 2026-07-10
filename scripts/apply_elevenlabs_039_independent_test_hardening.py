#!/usr/bin/env python3
"""Guarded live sync for the ELEVENLABS-039 independent test hardening follow-up.

This command never runs simulations or calls. Provider writes require both explicit
confirmation tokens. A full sync is limited to one KB file update, one prompt-only
PATCH, and four in-place test PUTs; --test-only limits the write to one existing test.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from apply_elevenlabs_038_end_call_terminal_control import (
        get_prompt,
        json_request,
        multipart_update_file,
        summarize_tools,
        unrelated_tool_fingerprint,
    )
    from runtime.providers.elevenlabs_agents.automation import test_create_request
except ImportError as exc:  # pragma: no cover - import paths are environment-specific
    raise SystemExit(f"error: cannot import required ElevenLabs helpers: {exc}") from exc


API_KEY_ENV_VAR = "ELEVENLABS_API_KEY"
CHECKPOINT_ID = "ELEVENLABS-039-end-call-edge-case-hardening"
AGENT_ID = "agent_7801kt0g32zxf4f8x5zkykj7syty"
AGENT_NAME = "web design"
CONFIRM_PROVIDER_WRITE = "confirm-provider-write"
CONFIRM_DASHBOARD_TEST_UPDATE = "confirm-dashboard-test-update"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
PROMPT_PATH = ROOT / "runtime" / "providers" / "elevenlabs_agents" / "prompts" / "web_design_atlas_sales_prompt.md"
KB_PATH = ROOT / "runtime" / "providers" / "elevenlabs_agents" / "knowledge_base" / "atlas_web_studio" / "atlas_output_quality_rules.md"
TESTS_PATH = ROOT / "runtime" / "providers" / "elevenlabs_agents" / "tests" / "web_design_end_call_edge_case_tests.json"

EXPECTED_TEST_IDS = (
    "sim_039_hard_stop_overrides_pending_email",
    "sim_039_delivery_timing_not_repeated",
    "sim_039_gatekeeper_callback_atomic_end_call",
    "sim_039_gatekeeper_note_atomic_end_call",
)
PROMPT_MARKERS = ("Atlas Web Studio", "Mission: earn permission")
SENSITIVE_KEY_RE = re.compile(
    r"(?:access_info|authorization|api[_-]?key|cookie|header|secret|token|creator|user|workspace|phone|customer|email)",
    re.IGNORECASE,
)
SAFE_STATUS_KEYS = {"authorization_confirmed", "provider_writes_allowed"}
EMAIL_RE = re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"(?<!\w)(?:\+?\d[\d\s().-]{7,}\d)(?!\w)")
HTTP_STATUS_RE = re.compile(r"\bfailed with (\d{3})\b")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def read_text(path: Path) -> str:
    value = path.read_text(encoding="utf-8").strip()
    if not value:
        raise ValueError(f"{path.relative_to(ROOT)} is empty")
    return value


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path.relative_to(ROOT)} must contain an object")
    return value


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def redact_text(value: str) -> str:
    value = EMAIL_RE.sub("[REDACTED_EMAIL]", value)
    return PHONE_RE.sub("[REDACTED_PHONE]", value)


def sanitize(value: Any, *, key_hint: str = "") -> Any:
    if isinstance(value, dict):
        clean: dict[str, Any] = {}
        for raw_key, raw_value in value.items():
            key = str(raw_key)
            if SENSITIVE_KEY_RE.search(key) and key not in SAFE_STATUS_KEYS:
                if isinstance(raw_value, list):
                    clean[key] = {"redacted": True, "count": len(raw_value)}
                elif raw_value in (None, "", [], {}):
                    clean[key] = raw_value
                else:
                    clean[key] = "[REDACTED]"
                continue
            clean[key] = sanitize(raw_value, key_hint=key)
        return clean
    if isinstance(value, list):
        return [sanitize(item, key_hint=key_hint) for item in value]
    if isinstance(value, str):
        return redact_text(value)
    return value


def canonical_sha256(value: Any) -> str:
    rendered = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(rendered).hexdigest()


def safe_error(exc: BaseException) -> str:
    return redact_text(str(exc))[:1600]


def request_error_status(exc: BaseException) -> int | None:
    match = HTTP_STATUS_RE.search(str(exc))
    return int(match.group(1)) if match else None


def agent_prompt(agent: dict[str, Any]) -> dict[str, Any]:
    prompt = get_prompt(agent)
    if not isinstance(prompt, dict):
        raise ValueError("agent prompt is not an object")
    return prompt


def kb_entries(agent: dict[str, Any]) -> list[dict[str, Any]]:
    entries = agent_prompt(agent).get("knowledge_base")
    if not isinstance(entries, list):
        raise ValueError("agent prompt.knowledge_base is not a list")
    if not all(isinstance(item, dict) for item in entries):
        raise ValueError("agent prompt.knowledge_base contains a non-object entry")
    return entries


def attachment_ids(entries: list[dict[str, Any]]) -> list[str]:
    ids = [str(item.get("id", "")).strip() for item in entries]
    if any(not item for item in ids):
        raise ValueError("knowledge-base attachment is missing an id")
    return ids


def active_end_call_summary(agent: dict[str, Any]) -> dict[str, Any]:
    summary = summarize_tools(agent)
    if not isinstance(summary, dict):
        raise ValueError("existing tool summary helper returned an invalid value")
    return summary


def procedures_inactive(agent: dict[str, Any]) -> bool:
    return not bool(agent.get("procedures"))


def analysis_criteria(agent: dict[str, Any]) -> list[dict[str, Any]]:
    evaluation = (agent.get("platform_settings") or {}).get("evaluation")
    criteria = evaluation.get("criteria") if isinstance(evaluation, dict) else None
    if not isinstance(criteria, list) or not all(isinstance(item, dict) for item in criteria):
        raise ValueError("agent Analysis criteria are missing or invalid")
    return criteria


def protected_agent_state(agent: dict[str, Any]) -> dict[str, Any]:
    """Return configuration state with only prompt text excluded from comparison."""
    state = {
        key: copy.deepcopy(agent.get(key))
        for key in (
            "agent_id",
            "name",
            "conversation_config",
            "platform_settings",
            "workflow",
            "tags",
            "phone_numbers",
            "whatsapp_accounts",
            "procedures",
        )
        if key in agent
    }
    prompt = state.get("conversation_config", {}).get("agent", {}).get("prompt")
    if not isinstance(prompt, dict):
        raise ValueError("agent protected-state snapshot cannot locate prompt")
    prompt.pop("prompt", None)
    return state


def protected_state_report(agent: dict[str, Any]) -> dict[str, Any]:
    protected = protected_agent_state(agent)
    prompt = agent_prompt(agent)
    criteria = analysis_criteria(agent)
    return {
        "protected_state_sha256": canonical_sha256(protected),
        "protected_state": sanitize(protected),
        "unrelated_tool_fingerprint": sanitize(unrelated_tool_fingerprint(agent)),
        "knowledge_base_ids_in_order": attachment_ids(kb_entries(agent)),
        "tool_ids": sanitize(prompt.get("tool_ids", [])),
        "mcp_server_ids": sanitize(prompt.get("mcp_server_ids", [])),
        "native_mcp_server_ids": sanitize(prompt.get("native_mcp_server_ids", [])),
        "voice": sanitize((agent.get("conversation_config") or {}).get("tts")),
        "llm": sanitize(prompt.get("llm")),
        "first_message": sanitize((agent.get("conversation_config") or {}).get("agent", {}).get("first_message")),
        "dynamic_variables": sanitize((agent.get("conversation_config") or {}).get("agent", {}).get("dynamic_variables")),
        "phone_numbers_sha256": canonical_sha256(agent.get("phone_numbers", [])),
        "analysis_criterion_ids_in_order": [str(item.get("id", "")) for item in criteria],
        "procedures_inactive": procedures_inactive(agent),
    }


def expected_test_bodies(tests_document: dict[str, Any]) -> dict[str, dict[str, Any]]:
    if tests_document.get("package_id") != CHECKPOINT_ID:
        raise ValueError("repo test package_id does not match the checkpoint")
    suite_variables = tests_document.get("dynamic_variables", {})
    if not isinstance(suite_variables, dict):
        raise ValueError("repo test suite dynamic_variables must be an object")
    tests = tests_document.get("tests")
    if not isinstance(tests, list) or len(tests) != len(EXPECTED_TEST_IDS):
        raise ValueError("repo must contain exactly four ELEVENLABS-039 tests")
    bodies: dict[str, dict[str, Any]] = {}
    for item in tests:
        if not isinstance(item, dict):
            raise ValueError("repo test entry must be an object")
        source_id = str(item.get("test_id", ""))
        request = test_create_request(
            item,
            package_id=CHECKPOINT_ID,
            suite_dynamic_variables=suite_variables,
        )
        body = request.get("body")
        if not isinstance(body, dict):
            raise ValueError(f"{source_id} create-body helper returned an invalid body")
        if source_id in bodies:
            raise ValueError(f"duplicate repo test id {source_id}")
        bodies[source_id] = body
    if tuple(bodies) != EXPECTED_TEST_IDS:
        raise ValueError(f"repo test ids must be exactly {list(EXPECTED_TEST_IDS)}")
    return bodies


def invocation_run_name(run: dict[str, Any]) -> str:
    info = run.get("test_info") if isinstance(run.get("test_info"), dict) else {}
    for key in ("test_name", "name"):
        value = run.get(key) or info.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def invocation_provider_test_id(run: dict[str, Any]) -> str:
    info = run.get("test_info") if isinstance(run.get("test_info"), dict) else {}
    for key in ("test_id", "id"):
        value = run.get(key) or info.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def resolve_provider_test_ids(invocation: dict[str, Any]) -> dict[str, str]:
    invocation_agent_id = invocation.get("agent_id")
    if invocation_agent_id not in (None, AGENT_ID):
        raise ValueError(f"test invocation targets unexpected agent {invocation_agent_id!r}")
    runs = invocation.get("test_runs")
    if not isinstance(runs, list) or len(runs) != len(EXPECTED_TEST_IDS):
        raise ValueError("test invocation must contain exactly four test runs")
    resolved: dict[str, str] = {}
    for run in runs:
        if not isinstance(run, dict):
            raise ValueError("test invocation contains an invalid test run")
        name = invocation_run_name(run)
        provider_id = invocation_provider_test_id(run)
        source_id = name.rsplit("::", 1)[-1] if name.startswith(f"{CHECKPOINT_ID}::") else ""
        if source_id not in EXPECTED_TEST_IDS:
            raise ValueError(f"test invocation contains unexpected test name {name!r}")
        if name != f"{CHECKPOINT_ID}::{source_id}":
            raise ValueError(f"test invocation name is not exact for {source_id}")
        if not provider_id:
            raise ValueError(f"test invocation does not expose provider test id for {source_id}")
        if source_id in resolved:
            raise ValueError(f"test invocation repeats {source_id}")
        resolved[source_id] = provider_id
    if set(resolved) != set(EXPECTED_TEST_IDS) or len(set(resolved.values())) != len(resolved):
        raise ValueError("test invocation does not map one unique provider id to each expected test")
    return resolved


def test_semantics(test: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(test, dict):
        raise ValueError("test payload is not an object")
    success_condition = test.get("success_condition")
    if not success_condition:
        success_conditions = test.get("success_conditions")
        if isinstance(success_conditions, list) and len(success_conditions) == 1:
            success_condition = success_conditions[0]
    chat_history = test.get("chat_history")
    normalized_history = []
    if isinstance(chat_history, list):
        normalized_history = [
            {
                "role": str(item.get("role", "")),
                "message": str(item.get("message", "")),
            }
            for item in chat_history
            if isinstance(item, dict)
        ]
    return {
        "type": test.get("type"),
        "name": test.get("name"),
        "simulated_user_model": test.get("simulated_user_model"),
        "evaluation_model": test.get("evaluation_model"),
        "simulation_scenario": test.get("simulation_scenario"),
        "simulation_max_turns": test.get("simulation_max_turns"),
        "success_condition": success_condition,
        "dynamic_variables": copy.deepcopy(test.get("dynamic_variables")),
        "chat_history": normalized_history,
    }


def verify_live_test(source_id: str, live_test: dict[str, Any], expected_body: dict[str, Any]) -> None:
    validate_live_test_identity(source_id, live_test)
    if test_semantics(live_test) != test_semantics(expected_body):
        raise ValueError(f"live test {source_id} semantics do not match the repo create-body")


def validate_live_test_identity(source_id: str, live_test: dict[str, Any]) -> None:
    expected_name = f"{CHECKPOINT_ID}::{source_id}"
    if live_test.get("type") != "simulation":
        raise ValueError(f"live test {source_id} is not a simulation")
    if live_test.get("name") != expected_name:
        raise ValueError(f"live test {source_id} name does not match {expected_name}")


def validate_preflight(agent: dict[str, Any], live_tests: dict[str, dict[str, Any]], expected_bodies: dict[str, dict[str, Any]]) -> dict[str, Any]:
    if agent.get("agent_id") != AGENT_ID or agent.get("name") != AGENT_NAME:
        raise ValueError("refusing unexpected ElevenLabs agent")
    prompt = agent_prompt(agent)
    prompt_text = str(prompt.get("prompt", ""))
    if not all(marker in prompt_text for marker in PROMPT_MARKERS):
        raise ValueError("live agent prompt is missing the required Atlas marker")
    entries = kb_entries(agent)
    ids = attachment_ids(entries)
    if len(ids) != 17 or len(set(ids)) != 17:
        raise ValueError("live agent must have 17 unique KB attachment IDs")
    output_entries = [item for item in entries if item.get("name") == KB_PATH.name]
    if len(output_entries) != 1:
        raise ValueError("live agent must have exactly one attached atlas_output_quality_rules.md")
    tools = active_end_call_summary(agent)
    if tools.get("built_in_end_call_count") != 1:
        raise ValueError("live agent must have exactly one built-in end_call")
    if tools.get("duplicate_custom_or_server_end_call_count") != 0:
        raise ValueError("live agent has a custom or server end_call duplicate")
    if not procedures_inactive(agent):
        raise ValueError("live agent Procedures must remain inactive")
    criteria = analysis_criteria(agent)
    if len(criteria) != 30:
        raise ValueError(f"live agent must have 30 Analysis criteria, found {len(criteria)}")
    for source_id in EXPECTED_TEST_IDS:
        validate_live_test_identity(source_id, live_tests[source_id])
    return {
        "kb_count": len(ids),
        "kb_ids_in_order": ids,
        "output_quality_document_id": str(output_entries[0]["id"]),
        "tool_summary": sanitize(tools),
        "procedures_inactive": True,
        "analysis_criteria_count": len(criteria),
        "prompt_markers_present": list(PROMPT_MARKERS),
        "test_names": {source_id: live_tests[source_id].get("name") for source_id in EXPECTED_TEST_IDS},
    }


def prompt_patch_body(prompt_text: str) -> dict[str, Any]:
    return {"conversation_config": {"agent": {"prompt": {"prompt": prompt_text}}}}


def patch_requests(
    provider_test_ids: dict[str, str],
    expected_bodies: dict[str, dict[str, Any]],
    output_document_id: str,
    test_only: str | None,
) -> list[dict[str, Any]]:
    requests: list[dict[str, Any]] = []
    if test_only is None:
        requests.extend(
            [
                {
                    "request_id": "update_kb::atlas_output_quality_rules.md",
                    "method": "PATCH",
                    "endpoint": f"/v1/convai/knowledge-base/{output_document_id}/update-file",
                    "content_type": "multipart/form-data",
                    "source_path": str(KB_PATH.relative_to(ROOT)).replace("\\", "/"),
                },
                {
                    "request_id": "patch_agent_prompt_only",
                    "method": "PATCH",
                    "endpoint": f"/v1/convai/agents/{AGENT_ID}",
                    "content_type": "application/json",
                    "body": sanitize(prompt_patch_body(read_text(PROMPT_PATH))),
                },
            ]
        )
    source_ids = (test_only,) if test_only is not None else EXPECTED_TEST_IDS
    for source_id in source_ids:
        requests.append(
            {
                "request_id": f"update_test::{source_id}",
                "method": "PUT",
                "endpoint": f"/v1/convai/agent-testing/{provider_test_ids[source_id]}",
                "provider_test_id": provider_test_ids[source_id],
                "content_type": "application/json",
                "body": sanitize(expected_bodies[source_id]),
            }
        )
    return requests


def snapshot_payload(
    *,
    phase: str,
    agent: dict[str, Any] | None,
    live_tests: dict[str, dict[str, Any]] | None,
    provider_test_ids: dict[str, str] | None,
    error: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "checkpoint_id": CHECKPOINT_ID,
        "phase": phase,
        "captured_at_utc": utc_now(),
        "agent_id": AGENT_ID,
        "simulations_run": False,
        "outbound_calls_made": False,
    }
    if agent is not None:
        payload["agent"] = sanitize(agent)
        payload["protected_state"] = protected_state_report(agent)
    if live_tests is not None:
        payload["tests"] = {source_id: sanitize(live_tests[source_id]) for source_id in EXPECTED_TEST_IDS}
    if provider_test_ids is not None:
        payload["provider_test_ids"] = provider_test_ids
    if error is not None:
        payload["error"] = error
    return payload


def confirm_writes(args: argparse.Namespace) -> bool:
    return (
        args.confirm_provider_write == CONFIRM_PROVIDER_WRITE
        and args.confirm_dashboard_test_update == CONFIRM_DASHBOARD_TEST_UPDATE
    )


def write_provider_changes(
    *,
    api_key: str,
    output_document_id: str,
    expected_bodies: dict[str, dict[str, Any]],
    provider_test_ids: dict[str, str],
    test_only: str | None,
    results: list[dict[str, Any]],
) -> None:
    operations: list[tuple[str, str, str]] = []
    if test_only is None:
        operations.append(("update_kb::atlas_output_quality_rules.md", "PATCH", f"/v1/convai/knowledge-base/{quote(output_document_id, safe='')}/update-file"))
        operations.append(("patch_agent_prompt_only", "PATCH", f"/v1/convai/agents/{quote(AGENT_ID, safe='')}"))
    source_ids = (test_only,) if test_only is not None else EXPECTED_TEST_IDS
    operations.extend(
        (f"update_test::{source_id}", "PUT", f"/v1/convai/agent-testing/{quote(provider_test_ids[source_id], safe='')}")
        for source_id in source_ids
    )
    for request_id, method, endpoint in operations:
        try:
            if request_id.startswith("update_kb::"):
                response = multipart_update_file(
                    api_key=api_key,
                    documentation_id=output_document_id,
                    source_path=KB_PATH,
                )
            elif request_id == "patch_agent_prompt_only":
                response = json_request(
                    method,
                    endpoint,
                    api_key=api_key,
                    body=prompt_patch_body(read_text(PROMPT_PATH)),
                )
            else:
                source_id = request_id.split("::", 1)[1]
                response = json_request(method, endpoint, api_key=api_key, body=expected_bodies[source_id])
            results.append(
                {
                    "request_id": request_id,
                    "method": method,
                    "endpoint": endpoint,
                    "status_code": response.get("status_code"),
                    "status": "success",
                    "response": sanitize(response.get("response")),
                }
            )
        except Exception as exc:
            results.append(
                {
                    "request_id": request_id,
                    "method": method,
                    "endpoint": endpoint,
                    "status_code": request_error_status(exc),
                    "status": "failed",
                    "error": safe_error(exc),
                }
            )
            raise


def compare_post_state(
    before_agent: dict[str, Any],
    after_agent: dict[str, Any],
    before_tests: dict[str, dict[str, Any]],
    after_tests: dict[str, dict[str, Any]],
    expected_bodies: dict[str, dict[str, Any]],
    before_preflight: dict[str, Any],
) -> dict[str, Any]:
    if agent_prompt(after_agent).get("prompt") != read_text(PROMPT_PATH):
        raise ValueError("post-patch prompt does not exactly match the repo prompt")
    if protected_agent_state(before_agent) != protected_agent_state(after_agent):
        raise ValueError("protected agent state changed outside prompt text")
    before_report = protected_state_report(before_agent)
    after_report = protected_state_report(after_agent)
    if before_report["protected_state_sha256"] != after_report["protected_state_sha256"]:
        raise ValueError("protected agent state SHA-256 changed")
    explicit_fields = (
        "unrelated_tool_fingerprint",
        "knowledge_base_ids_in_order",
        "tool_ids",
        "mcp_server_ids",
        "native_mcp_server_ids",
        "voice",
        "llm",
        "first_message",
        "dynamic_variables",
        "phone_numbers_sha256",
        "analysis_criterion_ids_in_order",
        "procedures_inactive",
    )
    changed = [field for field in explicit_fields if before_report[field] != after_report[field]]
    if changed:
        raise ValueError(f"protected state field(s) changed: {changed}")
    after_preflight = validate_preflight(after_agent, after_tests, expected_bodies)
    if after_preflight["kb_ids_in_order"] != before_preflight["kb_ids_in_order"]:
        raise ValueError("KB attachment ID order changed")
    for source_id in EXPECTED_TEST_IDS:
        verify_live_test(source_id, after_tests[source_id], expected_bodies[source_id])
        for field in ("folder_parent_id", "folder_path"):
            if before_tests[source_id].get(field) != after_tests[source_id].get(field):
                raise ValueError(f"live test {source_id} changed {field}")
    if set(before_tests) != set(after_tests):
        raise ValueError("provider test set changed during sync")
    return {
        "prompt_exact": True,
        "test_payload_semantics_exact": True,
        "knowledge_base_count": after_preflight["kb_count"],
        "knowledge_base_order_preserved": True,
        "end_call_counts_verified": True,
        "unrelated_tool_fingerprint_preserved": True,
        "protected_state_sha256_preserved": True,
        "protected_state_sha256": after_report["protected_state_sha256"],
        "protected_fields_preserved": list(explicit_fields),
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Guarded ELEVENLABS-039 live sync; no simulations or calls are performed.")
    parser.add_argument("--test-invocation-id", required=True, help="Existing ElevenLabs invocation containing the four named tests")
    parser.add_argument("--confirm-provider-write", default=None, help=f"Exact token required: {CONFIRM_PROVIDER_WRITE}")
    parser.add_argument("--confirm-dashboard-test-update", default=None, help=f"Exact token required: {CONFIRM_DASHBOARD_TEST_UPDATE}")
    parser.add_argument("--test-only", choices=EXPECTED_TEST_IDS, default=None, help="Update exactly one existing test and skip prompt/KB writes")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    invocation_id = str(args.test_invocation_id).strip()
    if not invocation_id:
        print("error: --test-invocation-id must not be empty", file=sys.stderr)
        return 2
    api_key = os.environ.get(API_KEY_ENV_VAR, "").strip()
    if not api_key:
        print(f"error: {API_KEY_ENV_VAR} is required for fresh live GET preflight", file=sys.stderr)
        return 2

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, Any]] = []
    before_agent: dict[str, Any] | None = None
    before_tests: dict[str, dict[str, Any]] | None = None
    provider_test_ids: dict[str, str] | None = None
    try:
        repo_prompt = read_text(PROMPT_PATH)
        read_text(KB_PATH)
        expected_bodies = expected_test_bodies(read_json(TESTS_PATH))
        before_agent = json_request("GET", f"/v1/convai/agents/{quote(AGENT_ID, safe='')}", api_key=api_key)["response"]
        invocation = json_request("GET", f"/v1/convai/test-invocations/{quote(invocation_id, safe='')}", api_key=api_key)["response"]
        if not isinstance(before_agent, dict) or not isinstance(invocation, dict):
            raise ValueError("provider GET response must be an object")
        provider_test_ids = resolve_provider_test_ids(invocation)
        before_tests = {}
        for source_id in EXPECTED_TEST_IDS:
            live_test = json_request(
                "GET",
                f"/v1/convai/agent-testing/{quote(provider_test_ids[source_id], safe='')}",
                api_key=api_key,
            )["response"]
            if not isinstance(live_test, dict):
                raise ValueError(f"live test GET returned an invalid body for {source_id}")
            before_tests[source_id] = live_test
        preflight = validate_preflight(before_agent, before_tests, expected_bodies)
        write_json(
            OUT_DIR / "independent_hardening_pre_patch.json",
            snapshot_payload(
                phase="pre_patch",
                agent=before_agent,
                live_tests=before_tests,
                provider_test_ids=provider_test_ids,
            ),
        )
        requests = patch_requests(provider_test_ids, expected_bodies, preflight["output_quality_document_id"], args.test_only)
        authorization_confirmed = confirm_writes(args)
        plan = {
            "checkpoint_id": CHECKPOINT_ID,
            "agent_id": AGENT_ID,
            "agent_name": AGENT_NAME,
            "test_invocation_id": invocation_id,
            "test_only": args.test_only,
            "authorization_confirmed": authorization_confirmed,
            "provider_writes_allowed": authorization_confirmed,
            "preflight": preflight,
            "writes": [item["request_id"] for item in requests],
            "forbidden_operations": [
                "create_tests",
                "delete_tests",
                "move_tests",
                "run_tests",
                "outbound_calls",
                "knowledge_base_broadening",
                "Analysis_updates",
                "tool_updates",
                "voice_updates",
                "LLM_updates",
                "first_message_updates",
                "dynamic_variable_updates",
                "phone_configuration_updates",
                "Procedures_updates",
            ],
            "simulations_run": False,
            "outbound_calls_made": False,
        }
        write_json(OUT_DIR / "independent_hardening_patch_plan.json", sanitize(plan))
        write_json(
            OUT_DIR / "independent_hardening_patch_requests.json",
            {"checkpoint_id": CHECKPOINT_ID, "provider_writes_allowed": authorization_confirmed, "requests": requests},
        )
        if not authorization_confirmed:
            result = {
                "checkpoint_id": CHECKPOINT_ID,
                "status": "plan_only_missing_exact_confirmations",
                "provider_writes_made": False,
                "required_confirmations": [CONFIRM_PROVIDER_WRITE, CONFIRM_DASHBOARD_TEST_UPDATE],
                "simulations_run": False,
                "outbound_calls_made": False,
            }
            write_json(OUT_DIR / "independent_hardening_patch_result.json", result)
            write_json(
                OUT_DIR / "independent_hardening_post_patch.json",
                snapshot_payload(
                    phase="not_written",
                    agent=before_agent,
                    live_tests=before_tests,
                    provider_test_ids=provider_test_ids,
                ),
            )
            print(json.dumps({"status": result["status"], "plan": str(OUT_DIR / "independent_hardening_patch_plan.json")}, indent=2))
            return 0

        write_provider_changes(
            api_key=api_key,
            output_document_id=preflight["output_quality_document_id"],
            expected_bodies=expected_bodies,
            provider_test_ids=provider_test_ids,
            test_only=args.test_only,
            results=results,
        )
        after_agent = json_request("GET", f"/v1/convai/agents/{quote(AGENT_ID, safe='')}", api_key=api_key)["response"]
        if not isinstance(after_agent, dict):
            raise ValueError("post-patch agent GET response must be an object")
        after_tests: dict[str, dict[str, Any]] = {}
        for source_id in EXPECTED_TEST_IDS:
            live_test = json_request(
                "GET",
                f"/v1/convai/agent-testing/{quote(provider_test_ids[source_id], safe='')}",
                api_key=api_key,
            )["response"]
            if not isinstance(live_test, dict):
                raise ValueError(f"post-patch test GET returned an invalid body for {source_id}")
            after_tests[source_id] = live_test
        verification = compare_post_state(
            before_agent,
            after_agent,
            before_tests,
            after_tests,
            expected_bodies,
            preflight,
        )
        write_json(
            OUT_DIR / "independent_hardening_post_patch.json",
            snapshot_payload(
                phase="post_patch",
                agent=after_agent,
                live_tests=after_tests,
                provider_test_ids=provider_test_ids,
            ),
        )
        result = {
            "checkpoint_id": CHECKPOINT_ID,
            "status": "passed",
            "provider_writes_made": True,
            "writes": results,
            "verification": verification,
            "simulations_run": False,
            "outbound_calls_made": False,
        }
        write_json(OUT_DIR / "independent_hardening_patch_result.json", result)
        print(json.dumps({"status": "passed", "verification": verification}, indent=2))
        return 0
    except Exception as exc:
        error = safe_error(exc)
        result = {
            "checkpoint_id": CHECKPOINT_ID,
            "status": "failed",
            "provider_writes_made": bool(results),
            "writes": results,
            "error": error,
            "simulations_run": False,
            "outbound_calls_made": False,
        }
        write_json(OUT_DIR / "independent_hardening_patch_result.json", result)
        write_json(
            OUT_DIR / "independent_hardening_post_patch.json",
            snapshot_payload(
                phase="failed",
                agent=before_agent,
                live_tests=before_tests,
                provider_test_ids=provider_test_ids,
                error=error,
            ),
        )
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
