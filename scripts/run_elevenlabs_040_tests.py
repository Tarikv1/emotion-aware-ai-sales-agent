#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol
from urllib.parse import quote


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from apply_elevenlabs_038_end_call_terminal_control import json_request
from runtime.providers.elevenlabs_agents.automation import load_baseline_tests


CHECKPOINT_ID = "ELEVENLABS-040-detailed-pricing-control"
AGENT_ID = "agent_7801kt0g32zxf4f8x5zkykj7syty"
AGENT_NAME = "web design"
CONFIRMATION = "confirm-test-creation-and-run"
API_KEY_ENV_VAR = "ELEVENLABS_API_KEY"
TESTS_PATH = ROOT / "runtime" / "providers" / "elevenlabs_agents" / "tests" / "web_design_detailed_pricing_control_tests.json"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
PENDING_RUN_STATUSES = {"", "pending", "running", "queued", "in_progress"}
PASS_RUN_STATUSES = {"passed", "pass", "completed", "succeeded", "success"}

EXPECTED_TEST_IDS = [
    "sim_040_capability_question_no_unprompted_price",
    "sim_040_free_mockup_question_no_paid_price",
    "sim_040_basic_site_direct_price",
    "sim_040_existing_site_request_form_add_on",
    "sim_040_new_site_booking_whole_project",
    "sim_040_multi_feature_no_price_stacking",
    "sim_040_direct_crm_integration_existing_site",
    "sim_040_portal_requires_scope",
    "sim_040_budget_fit_direct_answer",
    "sim_040_care_plan_only_when_asked",
]
EXPECTED_NAMES = [f"{CHECKPOINT_ID}::{test_id}" for test_id in EXPECTED_TEST_IDS]

EMAIL_RE = re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"(?<!\w)(?:\+?\d[\d\s().-]{7,}\d)(?!\w)")
SECRET_ASSIGNMENT_RE = re.compile(
    r'(?i)("?(?:xi-api-key|api[_-]?key|authorization|token|secret|password)"?\s*[:=]\s*)(?:"[^"]*"|\'[^\']*\'|[^\s,}]+)'
)
BEARER_TOKEN_RE = re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._=-]+")
OPENAI_SECRET_RE = re.compile(r"\bsk-[A-Za-z0-9_-]+\b")


class GuardError(RuntimeError):
    """Raised before provider mutation when a safety guard fails."""


class Provider(Protocol):
    def request(
        self,
        method: str,
        endpoint: str,
        *,
        body: dict[str, Any] | None = None,
        timeout_seconds: int = 20,
    ) -> dict[str, Any]:
        ...


class ElevenLabsProvider:
    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    def request(
        self,
        method: str,
        endpoint: str,
        *,
        body: dict[str, Any] | None = None,
        timeout_seconds: int = 20,
    ) -> dict[str, Any]:
        return json_request(method, endpoint, api_key=self.api_key, body=body, timeout_seconds=timeout_seconds)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def redact_text(value: str) -> str:
    value = SECRET_ASSIGNMENT_RE.sub(r"\1[REDACTED]", value)
    value = BEARER_TOKEN_RE.sub("Bearer [REDACTED]", value)
    value = OPENAI_SECRET_RE.sub("[REDACTED_SECRET]", value)
    value = EMAIL_RE.sub("[REDACTED_EMAIL]", value)
    value = PHONE_RE.sub("[REDACTED_PHONE]", value)
    return value.replace("secret", "[REDACTED]").replace("Secret", "[REDACTED]")


def sanitize(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): sanitize(item) for key, item in value.items()}
    if isinstance(value, list):
        return [sanitize(item) for item in value]
    if isinstance(value, str):
        return redact_text(value)
    return value


def safe_error(exc: BaseException) -> str:
    return redact_text(str(exc))[:1600]


def canonical_sha256(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(encoded.encode("ascii")).hexdigest()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(sanitize(payload), indent=2, ensure_ascii=True) + "\n", encoding="ascii")


def query_string(params: dict[str, Any]) -> str:
    return "&".join(f"{quote(str(key), safe='')}={quote(str(value), safe=':-_')}" for key, value in params.items())


def response_object(result: dict[str, Any], label: str) -> dict[str, Any]:
    response = result.get("response")
    if not isinstance(response, dict):
        raise GuardError(f"{label} response must be a JSON object")
    return response


def response_items(result: dict[str, Any], label: str) -> list[dict[str, Any]]:
    response = response_object(result, label)
    for key in ("tests", "items", "data"):
        raw = response.get(key)
        if isinstance(raw, list):
            return [item for item in raw if isinstance(item, dict)]
    return []


def load_expected_bodies() -> dict[str, dict[str, Any]]:
    requests = load_baseline_tests(str(TESTS_PATH), package_id=CHECKPOINT_ID)
    bodies: dict[str, dict[str, Any]] = {}
    order: list[str] = []
    for request in requests:
        source_id = str(request.get("source_test_id", ""))
        body = request.get("body")
        if source_id not in EXPECTED_TEST_IDS:
            raise GuardError(f"unexpected 040 source test ID {source_id!r}")
        if not isinstance(body, dict):
            raise GuardError(f"{source_id} expected body must be a JSON object")
        order.append(source_id)
        bodies[source_id] = body
    if order != EXPECTED_TEST_IDS:
        raise GuardError(f"040 test order mismatch: {order!r}")
    return bodies


def semantic_fields(payload: dict[str, Any]) -> dict[str, Any]:
    success_condition = payload.get("success_condition")
    if success_condition in (None, ""):
        success_conditions = payload.get("success_conditions")
        if isinstance(success_conditions, list) and len(success_conditions) == 1:
            success_condition = success_conditions[0]
    fields = {
        "type": payload.get("type"),
        "name": payload.get("name"),
        "simulation_scenario": payload.get("simulation_scenario"),
        "simulation_max_turns": payload.get("simulation_max_turns"),
        "success_condition": success_condition,
        "dynamic_variables": payload.get("dynamic_variables"),
        "simulated_user_model": payload.get("simulated_user_model"),
        "evaluation_model": payload.get("evaluation_model"),
    }
    if "chat_history" in payload:
        fields["chat_history"] = payload.get("chat_history")
    return fields


def provider_id(item: dict[str, Any]) -> str:
    value = item.get("id") or item.get("test_id") or item.get("entity_id")
    if not isinstance(value, str) or not value.strip():
        raise GuardError(f"provider item has no id: {item!r}")
    return value


def parent_folder_id(item: dict[str, Any]) -> str | None:
    for key in ("folder_parent_id", "parent_folder_id", "folder_id"):
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return None


def list_folders(provider: Provider) -> tuple[dict[str, Any] | None, int]:
    endpoint = "/v1/convai/agent-testing?" + query_string(
        {
            "types": "folder",
            "page_size": 100,
            "parent_folder_id": "root",
            "search": CHECKPOINT_ID,
        }
    )
    result = provider.request("GET", endpoint)
    exact = [
        item
        for item in response_items(result, "folder list")
        if item.get("name") == CHECKPOINT_ID and parent_folder_id(item) in (None, "root")
    ]
    if len(exact) > 1:
        raise GuardError(f"duplicate exact 040 folders found: {[provider_id(item) for item in exact]}")
    return (exact[0] if exact else None), len(exact)


def create_folder(provider: Provider) -> dict[str, Any]:
    result = provider.request("POST", "/v1/convai/agent-testing/folders", body={"name": CHECKPOINT_ID})
    folder = response_object(result, "create folder")
    folder_id = folder.get("id")
    if not isinstance(folder_id, str) or not folder_id:
        raise GuardError("created folder response has no folder id")
    return folder


def list_tests(provider: Provider, *, folder_id: str | None) -> list[dict[str, Any]]:
    params: dict[str, Any] = {
        "types": "simulation",
        "page_size": 100,
        "search": f"{CHECKPOINT_ID}::",
    }
    if folder_id is not None:
        params["parent_folder_id"] = folder_id
    endpoint = "/v1/convai/agent-testing?" + query_string(params)
    result = provider.request("GET", endpoint)
    return response_items(result, "test list")


def get_test(provider: Provider, test_id: str) -> dict[str, Any]:
    result = provider.request("GET", f"/v1/convai/agent-testing/{quote(test_id, safe='')}")
    return response_object(result, f"test {test_id}")


def ensure_folder(provider: Provider) -> dict[str, Any]:
    folder, exact_count = list_folders(provider)
    if folder is not None:
        folder_id = provider_id(folder)
        return {
            "name": CHECKPOINT_ID,
            "folder_id": folder_id,
            "reused_existing": True,
            "created_in_this_run": False,
            "parent_folder_id": "root",
            "exact_folder_match_count": exact_count,
        }
    orphaned_exact_tests = [
        {"name": item.get("name"), "provider_test_id": provider_id(item), "folder_parent_id": parent_folder_id(item)}
        for item in list_tests(provider, folder_id=None)
        if item.get("name") in EXPECTED_NAMES
    ]
    if orphaned_exact_tests:
        raise GuardError(f"exact 040 tests exist without the exact 040 folder: {orphaned_exact_tests!r}")
    created = create_folder(provider)
    return {
        "name": CHECKPOINT_ID,
        "folder_id": provider_id(created),
        "reused_existing": False,
        "created_in_this_run": True,
        "parent_folder_id": "root",
        "exact_folder_match_count": 0,
    }


def discover_tests(
    provider: Provider,
    *,
    folder_id: str,
    expected_bodies: dict[str, dict[str, Any]],
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    folder_children = [
        item for item in list_tests(provider, folder_id=folder_id)
        if item.get("name") in EXPECTED_NAMES
    ]
    all_candidates = [
        item for item in list_tests(provider, folder_id=None)
        if item.get("name") in EXPECTED_NAMES
    ]
    duplicate_names: list[str] = []
    for expected_name in EXPECTED_NAMES:
        if sum(1 for item in folder_children if item.get("name") == expected_name) > 1:
            duplicate_names.append(expected_name)
    if duplicate_names:
        raise GuardError(f"duplicate exact 040 test names inside folder: {duplicate_names!r}")

    outside_conflicts = [
        {"name": item.get("name"), "provider_test_id": provider_id(item), "folder_parent_id": parent_folder_id(item)}
        for item in all_candidates
        if parent_folder_id(item) not in (None, folder_id)
    ]
    if outside_conflicts:
        raise GuardError(f"exact 040 tests found outside chosen folder: {outside_conflicts!r}")

    existing_by_source_id: dict[str, dict[str, Any]] = {}
    semantic_mismatches: list[str] = []
    for item in folder_children:
        name = str(item.get("name"))
        source_id = name.rsplit("::", 1)[-1]
        test_id = provider_id(item)
        full = get_test(provider, test_id)
        if semantic_fields(full) != semantic_fields(expected_bodies[source_id]):
            semantic_mismatches.append(source_id)
            continue
        existing_by_source_id[source_id] = {
            "provider_test_id": provider_id(full) if any(key in full for key in ("id", "test_id", "entity_id")) else test_id,
            "provider_test_name": name,
            "body": full,
            "status_code": 200,
        }
    if semantic_mismatches:
        raise GuardError(f"same-name 040 test payload drift: {semantic_mismatches!r}")
    return existing_by_source_id, {
        "exact_test_name_conflicts": duplicate_names,
        "outside_folder_conflicts": outside_conflicts,
        "semantic_mismatches": semantic_mismatches,
    }


def create_missing_tests(
    provider: Provider,
    *,
    existing: dict[str, dict[str, Any]],
    expected_bodies: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    created: dict[str, dict[str, Any]] = {}
    for source_id in EXPECTED_TEST_IDS:
        if source_id in existing:
            continue
        body = expected_bodies[source_id]
        result = provider.request("POST", "/v1/convai/agent-testing/create", body=body)
        response = response_object(result, f"create {source_id}")
        test_id = provider_id(response)
        created[source_id] = {
            "provider_test_id": test_id,
            "provider_test_name": body["name"],
            "body": body,
            "status_code": int(result.get("status_code", 0)),
        }
    return created


def move_created_tests(provider: Provider, *, created: dict[str, dict[str, Any]], folder_id: str) -> None:
    ids = [created[source_id]["provider_test_id"] for source_id in EXPECTED_TEST_IDS if source_id in created]
    if not ids:
        return
    provider.request(
        "POST",
        "/v1/convai/agent-testing/bulk-move",
        body={"entity_ids": ids, "move_to": folder_id},
    )


def mapping_payload(
    *,
    folder: dict[str, Any],
    existing: dict[str, dict[str, Any]],
    created: dict[str, dict[str, Any]],
    expected_bodies: dict[str, dict[str, Any]],
    duplicate_prevention: dict[str, Any],
) -> dict[str, Any]:
    tests = []
    for source_id in EXPECTED_TEST_IDS:
        record = created.get(source_id) or existing[source_id]
        tests.append(
            {
                "source_test_id": source_id,
                "provider_test_name": record["provider_test_name"],
                "provider_test_id": record["provider_test_id"],
                "reused_existing": source_id in existing,
                "created_in_this_run": source_id in created,
                "body_canonical_sha256": canonical_sha256(expected_bodies[source_id]),
                "provider_status_code": record.get("status_code"),
            }
        )
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "captured_at_utc": utc_now(),
        "folder": {
            "name": folder["name"],
            "folder_id": folder["folder_id"],
            "reused_existing": folder["reused_existing"],
            "created_in_this_run": folder["created_in_this_run"],
            "parent_folder_id": folder["parent_folder_id"],
        },
        "tests": tests,
        "duplicate_prevention": {
            "exact_folder_match_count": folder["exact_folder_match_count"],
            **duplicate_prevention,
        },
    }


def terminal_run_summaries(invocation: dict[str, Any]) -> list[dict[str, Any]]:
    runs = invocation.get("test_runs")
    if not isinstance(runs, list):
        return []
    return [
        {
            "test_id": item.get("test_id"),
            "test_name": item.get("test_name"),
            "test_run_id": item.get("test_run_id") or item.get("run_id") or item.get("id"),
            "status": item.get("status"),
        }
        for item in runs
        if isinstance(item, dict)
    ]


def completed_terminal_statuses(invocation: dict[str, Any], *, expected_run_count: int) -> list[str] | None:
    summaries = terminal_run_summaries(invocation)
    statuses = [str(item.get("status", "")).strip().lower() for item in summaries]
    if len(statuses) != expected_run_count:
        return None
    if any(status in PENDING_RUN_STATUSES for status in statuses):
        return None
    return statuses


def run_tests_once(
    provider: Provider,
    *,
    provider_test_ids_by_source: dict[str, str],
    wait_timeout_seconds: int,
    poll_interval_seconds: float,
) -> dict[str, Any]:
    run_body = {
        "tests": [{"test_id": provider_test_ids_by_source[source_id]} for source_id in EXPECTED_TEST_IDS],
        "repeat_count": 1,
    }
    run_result = provider.request(
        "POST",
        f"/v1/convai/agents/{quote(AGENT_ID, safe='')}/run-tests",
        body=run_body,
        timeout_seconds=60,
    )
    run_response = response_object(run_result, "run-tests")
    invocation_id = run_response.get("id") or run_response.get("test_invocation_id") or run_response.get("invocation_id")
    if not isinstance(invocation_id, str) or not invocation_id.strip():
        raise GuardError("run-tests response did not include an invocation id")

    deadline = time.monotonic() + max(1, wait_timeout_seconds)
    completed: dict[str, Any] | None = None
    while time.monotonic() < deadline:
        invocation_result = provider.request(
            "GET",
            f"/v1/convai/test-invocations/{quote(invocation_id, safe='')}",
        )
        invocation = response_object(invocation_result, "test invocation")
        statuses = completed_terminal_statuses(invocation, expected_run_count=len(EXPECTED_TEST_IDS))
        if statuses is not None:
            completed = invocation
            break
        time.sleep(max(0, poll_interval_seconds))
    if completed is None:
        raise TimeoutError(f"test invocation {invocation_id} did not finish before timeout")

    run_summaries = terminal_run_summaries(completed)
    final_statuses = [str(item.get("status", "")).strip().lower() for item in run_summaries]
    failed_runs = [item for item in run_summaries if str(item.get("status", "")).strip().lower() not in PASS_RUN_STATUSES]
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "captured_at_utc": utc_now(),
        "status": "failed" if failed_runs else "completed",
        "invocation_id": invocation_id,
        "repeat_count": 1,
        "selected_test_count": len(EXPECTED_TEST_IDS),
        "expected_terminal_run_count": len(EXPECTED_TEST_IDS),
        "observed_terminal_run_count": len(run_summaries),
        "failed_terminal_run_count": len(failed_runs),
        "provider_status_code": int(run_result.get("status_code", 0)),
        "provider_test_ids": provider_test_ids_by_source,
        "run_statuses": run_summaries,
        "final_run_statuses": final_statuses,
        "outbound_calls_made": False,
    }


def execute_with_provider(
    provider: Provider,
    *,
    output_dir: Path = OUT_DIR,
    live: bool,
    wait_timeout_seconds: int = 420,
    poll_interval_seconds: float = 2.0,
) -> dict[str, Any]:
    if not live:
        expected_bodies = load_expected_bodies()
        plan = {
            "checkpoint_id": CHECKPOINT_ID,
            "status": "dry_run",
            "live_provider_calls_made": False,
            "provider_mutations_made": False,
            "expected_test_count": len(EXPECTED_TEST_IDS),
            "expected_test_ids": EXPECTED_TEST_IDS,
            "folder_name": CHECKPOINT_ID,
            "agent_id": AGENT_ID,
            "agent_name": AGENT_NAME,
            "would_list_existing_folders_first": True,
            "would_list_existing_tests_before_create": True,
            "would_create_only_missing_exact_tests": True,
            "would_run_exactly_once_after_confirmation": True,
            "expected_body_sha256_by_source_id": {
                source_id: canonical_sha256(expected_bodies[source_id]) for source_id in EXPECTED_TEST_IDS
            },
        }
        return plan

    try:
        expected_bodies = load_expected_bodies()
        folder = ensure_folder(provider)
        existing, duplicate_prevention = discover_tests(
            provider,
            folder_id=folder["folder_id"],
            expected_bodies=expected_bodies,
        )
        created = create_missing_tests(provider, existing=existing, expected_bodies=expected_bodies)
        move_created_tests(provider, created=created, folder_id=folder["folder_id"])
        all_records = {**existing, **created}
        if set(all_records) != set(EXPECTED_TEST_IDS):
            missing = [source_id for source_id in EXPECTED_TEST_IDS if source_id not in all_records]
            raise GuardError(f"missing provider test IDs after create/reuse: {missing!r}")
        mapping = mapping_payload(
            folder=folder,
            existing=existing,
            created=created,
            expected_bodies=expected_bodies,
            duplicate_prevention=duplicate_prevention,
        )
        write_json(output_dir / "live_test_mapping.json", mapping)
        provider_ids = {
            source_id: all_records[source_id]["provider_test_id"]
            for source_id in EXPECTED_TEST_IDS
        }
        result = run_tests_once(
            provider,
            provider_test_ids_by_source=provider_ids,
            wait_timeout_seconds=wait_timeout_seconds,
            poll_interval_seconds=poll_interval_seconds,
        )
        result["folder_id"] = folder["folder_id"]
        write_json(output_dir / "live_test_run_result.json", result)
        return {"status": result["status"], "mapping": mapping, "run_result": result}
    except Exception as exc:
        failure = {
            "checkpoint_id": CHECKPOINT_ID,
            "captured_at_utc": utc_now(),
            "status": "failed",
            "error": safe_error(exc),
            "api_failure_count": 1,
            "outbound_calls_made": False,
        }
        write_json(output_dir / "live_test_run_result.json", failure)
        raise


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Guard and run the ELEVENLABS-040 dashboard tests.")
    parser.add_argument("--dry-run", action="store_true", help="Plan only. This is the default and makes no provider calls.")
    parser.add_argument(
        "--confirm-test-creation-and-run",
        choices=(CONFIRMATION,),
        default=None,
        help="Exact token required before creating/moving/running provider tests.",
    )
    parser.add_argument("--wait-timeout-seconds", type=int, default=420)
    parser.add_argument("--poll-interval-seconds", type=float, default=2.0)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    live = args.confirm_test_creation_and_run == CONFIRMATION
    if not live:
        plan = execute_with_provider(
            provider=ElevenLabsProvider(api_key=""),
            live=False,
            wait_timeout_seconds=args.wait_timeout_seconds,
            poll_interval_seconds=args.poll_interval_seconds,
        )
        print(json.dumps(plan, indent=2, ensure_ascii=True))
        return 0

    api_key = os.environ.get(API_KEY_ENV_VAR, "").strip()
    if not api_key:
        print(f"error: {API_KEY_ENV_VAR} is required for live provider test creation/run", file=sys.stderr)
        return 2
    try:
        result = execute_with_provider(
            ElevenLabsProvider(api_key),
            live=True,
            wait_timeout_seconds=args.wait_timeout_seconds,
            poll_interval_seconds=args.poll_interval_seconds,
        )
    except Exception as exc:
        print(f"error: {safe_error(exc)}", file=sys.stderr)
        return 1
    print(json.dumps(result["run_result"], indent=2, ensure_ascii=True))
    return 0 if result["status"] == "completed" else 1


if __name__ == "__main__":
    sys.exit(main())
