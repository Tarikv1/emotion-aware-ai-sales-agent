#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any
from urllib.parse import quote


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

try:
    from apply_elevenlabs_038_end_call_terminal_control import json_request
    from runtime.providers.elevenlabs_agents.automation import load_baseline_tests
except ImportError as exc:  # pragma: no cover - import failures are environment errors
    raise SystemExit(f"error: could not import required local helpers: {exc}") from exc


API_KEY_ENV_VAR = "ELEVENLABS_API_KEY"
CHECKPOINT_ID = "ELEVENLABS-039-end-call-edge-case-hardening"
EXPECTED_AGENT_ID = "agent_7801kt0g32zxf4f8x5zkykj7syty"
EXPECTED_AGENT_NAME = "web design"
BASELINE_PATH = ROOT / "runtime" / "providers" / "elevenlabs_agents" / "tests" / "web_design_end_call_edge_case_tests.json"
EVIDENCE_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
REQUEST_EVIDENCE_PATH = EVIDENCE_DIR / "independent_hardening_test_run_request.json"
RESULT_EVIDENCE_PATH = EVIDENCE_DIR / "independent_hardening_test_run_start_result.json"


class GuardError(RuntimeError):
    """Raised when a live guard fails before the run-tests POST."""


def require_object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise GuardError(f"{label} must be a JSON object")
    return value


def response_body(result: dict[str, Any], label: str) -> dict[str, Any]:
    return require_object(result.get("response"), f"{label} response")


def load_expected_bodies() -> tuple[list[str], dict[str, dict[str, Any]]]:
    requests = load_baseline_tests(str(BASELINE_PATH), package_id=CHECKPOINT_ID)
    bodies: dict[str, dict[str, Any]] = {}
    ordered_names: list[str] = []
    for request in requests:
        body = require_object(request.get("body"), "baseline test body")
        name = body.get("name")
        if not isinstance(name, str) or not name:
            raise GuardError("baseline test body has no exact provider name")
        if name in bodies:
            raise GuardError(f"baseline contains duplicate provider test name {name!r}")
        ordered_names.append(name)
        bodies[name] = body
    expected_names = [
        f"{CHECKPOINT_ID}::sim_039_hard_stop_overrides_pending_email",
        f"{CHECKPOINT_ID}::sim_039_delivery_timing_not_repeated",
        f"{CHECKPOINT_ID}::sim_039_gatekeeper_callback_atomic_end_call",
        f"{CHECKPOINT_ID}::sim_039_gatekeeper_note_atomic_end_call",
    ]
    if ordered_names != expected_names:
        raise GuardError(f"baseline names/order mismatch: expected {expected_names!r}, got {ordered_names!r}")
    if len(bodies) != 4:
        raise GuardError(f"expected exactly four baseline simulations, got {len(bodies)}")
    return expected_names, bodies


def normalized_chat_history(value: Any, label: str) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise GuardError(f"{label}.chat_history must be a list")
    normalized: list[dict[str, Any]] = []
    for index, entry in enumerate(value):
        item = require_object(entry, f"{label}.chat_history[{index}]")
        required = ("role", "message")
        missing = [key for key in required if key not in item]
        if missing:
            raise GuardError(f"{label}.chat_history[{index}] missing {missing!r}")
        normalized.append({key: item[key] for key in required})
    return normalized


def semantic_fields(payload: dict[str, Any], label: str) -> dict[str, Any]:
    success_condition = payload.get("success_condition")
    if not success_condition:
        success_conditions = payload.get("success_conditions")
        if isinstance(success_conditions, list) and len(success_conditions) == 1:
            success_condition = success_conditions[0]
    fields = {
        "type": payload.get("type"),
        "name": payload.get("name"),
        "chat_history": normalized_chat_history(payload.get("chat_history"), label),
        "simulation_scenario": payload.get("simulation_scenario"),
        "simulation_max_turns": payload.get("simulation_max_turns"),
        "success_condition": success_condition,
        "dynamic_variables": payload.get("dynamic_variables"),
        "simulated_user_model": payload.get("simulated_user_model"),
        "evaluation_model": payload.get("evaluation_model"),
    }
    if not isinstance(fields["dynamic_variables"], dict):
        raise GuardError(f"{label}.dynamic_variables must be an object")
    return fields


def find_provider_test_ids(
    invocation: dict[str, Any], expected_names: list[str]
) -> tuple[dict[str, str], dict[str, str]]:
    runs = invocation.get("test_runs")
    if not isinstance(runs, list):
        raise GuardError("reference invocation is missing test_runs")
    expected_set = set(expected_names)
    ids_by_name: dict[str, str] = {}
    run_ids_by_name: dict[str, str] = {}
    for raw_run in runs:
        run = require_object(raw_run, "reference invocation test run")
        name = run.get("test_name")
        if name not in expected_set:
            continue
        test_id = run.get("test_id")
        if not isinstance(test_id, str) or not test_id.strip():
            raise GuardError(f"reference run {name!r} has no provider test ID")
        if name in ids_by_name and ids_by_name[name] != test_id:
            raise GuardError(f"reference invocation has conflicting provider IDs for {name!r}")
        ids_by_name[name] = test_id
        run_id = run.get("test_run_id") or run.get("run_id") or run.get("id")
        if isinstance(run_id, str) and run_id.strip():
            run_ids_by_name[name] = run_id
    missing = [name for name in expected_names if name not in ids_by_name]
    if missing:
        raise GuardError(f"reference invocation is missing exact test names: {missing!r}")
    if len(set(ids_by_name.values())) != 4:
        raise GuardError("reference invocation did not resolve four unique provider test IDs")
    return ids_by_name, run_ids_by_name


def get_prompt(agent: dict[str, Any]) -> dict[str, Any]:
    conversation_config = require_object(agent.get("conversation_config"), "agent.conversation_config")
    agent_config = require_object(conversation_config.get("agent"), "agent.conversation_config.agent")
    return require_object(agent_config.get("prompt"), "agent prompt")


def validate_agent(agent: dict[str, Any]) -> dict[str, Any]:
    if agent.get("agent_id") != EXPECTED_AGENT_ID:
        raise GuardError(f"unexpected target agent ID {agent.get('agent_id')!r}")
    if agent.get("name") != EXPECTED_AGENT_NAME:
        raise GuardError(f"unexpected target agent name {agent.get('name')!r}")
    if agent.get("procedures"):
        raise GuardError("target agent has active Procedures")

    prompt = get_prompt(agent)
    knowledge_base = prompt.get("knowledge_base")
    if not isinstance(knowledge_base, list) or len(knowledge_base) != 17:
        raise GuardError("target agent must have exactly 17 KB attachments")
    attachment_ids: list[str] = []
    for index, item in enumerate(knowledge_base):
        entry = require_object(item, f"agent prompt.knowledge_base[{index}]")
        document_id = entry.get("id")
        if not isinstance(document_id, str) or not document_id.strip():
            raise GuardError(f"KB attachment {index} has no document ID")
        attachment_ids.append(document_id)
    if len(set(attachment_ids)) != 17:
        raise GuardError("target agent KB attachments are not 17 unique documents")

    built_in_tools = prompt.get("built_in_tools")
    if not isinstance(built_in_tools, dict) or not isinstance(built_in_tools.get("end_call"), dict):
        raise GuardError("target agent must have exactly one built-in end_call")
    legacy_tools = prompt.get("tools", [])
    if legacy_tools is not None and not isinstance(legacy_tools, list):
        raise GuardError("target agent prompt.tools is not a list")
    end_call_entries = [
        item for item in (legacy_tools or [])
        if isinstance(item, dict) and item.get("name") == "end_call"
    ]
    custom_or_server_duplicates = [
        item
        for item in end_call_entries
        if not (
            item.get("type") == "system"
            and isinstance(item.get("params"), dict)
            and item["params"].get("system_tool_type") == "end_call"
        )
    ]
    if custom_or_server_duplicates:
        raise GuardError("target agent has a custom/server end_call duplicate")
    return {
        "agent_id": EXPECTED_AGENT_ID,
        "agent_name": EXPECTED_AGENT_NAME,
        "procedures_inactive": True,
        "knowledge_base_attachment_count": 17,
        "knowledge_base_unique_attachment_count": 17,
        "built_in_end_call_count": 1,
        "custom_or_server_end_call_duplicate_count": 0,
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="ascii")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Guard and optionally run exactly the four ELEVENLABS-039 dashboard simulations."
    )
    parser.add_argument("--reference-invocation-id", required=True, help="Existing test invocation used to resolve provider test IDs")
    parser.add_argument(
        "--confirm-simulations",
        choices=("confirm-simulations",),
        default=None,
        help="Required exact confirmation before the run-tests POST; omit for a dry-run plan",
    )
    parser.add_argument("--wait-timeout-seconds", type=int, default=300, help="Maximum wait for the four runs to finish")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    api_key = os.environ.get(API_KEY_ENV_VAR, "").strip()
    if not api_key:
        print(f"error: {API_KEY_ENV_VAR} is required", file=sys.stderr)
        return 2
    reference_invocation_id = str(args.reference_invocation_id).strip()
    if not reference_invocation_id:
        print("error: --reference-invocation-id must not be empty", file=sys.stderr)
        return 2

    try:
        expected_names, expected_bodies = load_expected_bodies()
        reference_result = json_request(
            "GET",
            f"/v1/convai/test-invocations/{quote(reference_invocation_id, safe='')}",
            api_key=api_key,
        )
        reference = response_body(reference_result, "reference invocation")
        if reference.get("agent_id") not in (None, EXPECTED_AGENT_ID):
            raise GuardError(f"reference invocation belongs to unexpected agent {reference.get('agent_id')!r}")
        provider_ids, reference_run_ids = find_provider_test_ids(reference, expected_names)

        live_test_status_codes: dict[str, int] = {}
        for name in expected_names:
            test_id = provider_ids[name]
            live_test_result = json_request(
                "GET",
                f"/v1/convai/agent-testing/{quote(test_id, safe='')}",
                api_key=api_key,
            )
            live_test_status_codes[test_id] = int(live_test_result.get("status_code", 0))
            live_test = response_body(live_test_result, f"live test {test_id}")
            expected_semantics = semantic_fields(expected_bodies[name], f"baseline {name}")
            actual_semantics = semantic_fields(live_test, f"live test {test_id}")
            if actual_semantics != expected_semantics:
                raise GuardError(f"live test semantic mismatch for {name}")

        agent_result = json_request(
            "GET",
            f"/v1/convai/agents/{quote(EXPECTED_AGENT_ID, safe='')}",
            api_key=api_key,
        )
        agent = response_body(agent_result, "target agent")
        agent_guards = validate_agent(agent)

        run_body = {
            "tests": [{"test_id": provider_ids[name]} for name in expected_names],
            "repeat_count": 1,
        }
        request_evidence = {
            "checkpoint_id": CHECKPOINT_ID,
            "agent_id": EXPECTED_AGENT_ID,
            "agent_name": EXPECTED_AGENT_NAME,
            "reference_invocation_id": reference_invocation_id,
            "reference_test_run_ids": {
                name: reference_run_ids.get(name) for name in expected_names
            },
            "provider_test_ids": {
                name: provider_ids[name] for name in expected_names
            },
            "status_codes": {
                "reference_invocation_get": int(reference_result.get("status_code", 0)),
                "live_test_gets": live_test_status_codes,
                "agent_get": int(agent_result.get("status_code", 0)),
            },
            "guards": agent_guards,
            "request": {
                "method": "POST",
                "endpoint": f"/v1/convai/agents/{EXPECTED_AGENT_ID}/run-tests",
                "body": run_body,
            },
        }

        if args.confirm_simulations is None:
            print(json.dumps({"status": "dry_run", "post_performed": False, **request_evidence}, indent=2))
            return 0

        write_json(REQUEST_EVIDENCE_PATH, request_evidence)
        run_result = json_request(
            "POST",
            f"/v1/convai/agents/{quote(EXPECTED_AGENT_ID, safe='')}/run-tests",
            api_key=api_key,
            body=run_body,
            timeout_seconds=60,
        )
        run_response = response_body(run_result, "run-tests")
        run_invocation_id = run_response.get("id") or run_response.get("test_invocation_id") or run_response.get("invocation_id")
        test_run_ids: list[str] = []
        raw_test_runs = run_response.get("test_runs")
        if isinstance(raw_test_runs, list):
            for raw_run in raw_test_runs:
                if not isinstance(raw_run, dict):
                    continue
                run_id = raw_run.get("test_run_id") or raw_run.get("run_id") or raw_run.get("id")
                if isinstance(run_id, str) and run_id.strip():
                    test_run_ids.append(run_id)
        result_evidence = {
            "checkpoint_id": CHECKPOINT_ID,
            "agent_id": EXPECTED_AGENT_ID,
            "reference_invocation_id": reference_invocation_id,
            "run_invocation_id": run_invocation_id,
            "test_run_ids": test_run_ids,
            "provider_test_ids": [provider_ids[name] for name in expected_names],
            "repeat_count": 1,
            "status": run_response.get("status") or "submitted",
            "status_code": int(run_result.get("status_code", 0)),
        }
        deadline = time.monotonic() + max(1, args.wait_timeout_seconds)
        completed_invocation: dict[str, Any] | None = None
        while isinstance(run_invocation_id, str) and run_invocation_id and time.monotonic() < deadline:
            invocation_result = json_request(
                "GET",
                f"/v1/convai/test-invocations/{quote(run_invocation_id, safe='')}",
                api_key=api_key,
            )
            invocation = response_body(invocation_result, "submitted test invocation")
            runs = invocation.get("test_runs")
            statuses = [str(item.get("status", "")) for item in runs if isinstance(item, dict)] if isinstance(runs, list) else []
            if len(statuses) == 4 and all(status not in {"", "pending"} for status in statuses):
                completed_invocation = invocation
                result_evidence["final_run_statuses"] = statuses
                result_evidence["completed"] = True
                break
            time.sleep(2)
        if completed_invocation is None:
            result_evidence["completed"] = False
            write_json(RESULT_EVIDENCE_PATH, result_evidence)
            raise GuardError("test invocation did not complete before the wait timeout")
        write_json(RESULT_EVIDENCE_PATH, result_evidence)
        print(json.dumps(result_evidence, indent=2))
        return 0
    except GuardError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
