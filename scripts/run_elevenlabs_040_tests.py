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
REPAIR_CONFIRMATION = "confirm-owned-context-repair"
CANARY_CONFIRMATION = "confirm-canary-run"
MAX_LIST_PAGES = 20
API_KEY_ENV_VAR = "ELEVENLABS_API_KEY"
TESTS_PATH = ROOT / "runtime" / "providers" / "elevenlabs_agents" / "tests" / "web_design_detailed_pricing_control_tests.json"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
DEFAULT_MAPPING_PATH = OUT_DIR / "live_test_mapping.json"
PENDING_RUN_STATUSES = {"", "pending", "running", "queued", "in_progress"}
PASS_RUN_STATUSES = {"passed", "pass", "completed", "succeeded", "success"}
REPAIR_CONTEXT_VALUES = {
    "business_name": "Acme Dental",
    "business_type": "dental clinic",
    "city": "Phoenix",
}
REPAIR_CONTEXT_KEYS = tuple(REPAIR_CONTEXT_VALUES)
TEST_UPDATE_SEMANTICS = {
    "method": "PUT",
    "endpoint_template": "/v1/convai/agent-testing/:test_id",
    "body": "full exact simulation test definition",
}

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


class OperationLedger:
    def __init__(self) -> None:
        self.attempts: list[dict[str, Any]] = []

    def start(
        self,
        *,
        request_id: str,
        operation: str,
        method: str,
        endpoint: str,
        body: dict[str, Any] | None,
    ) -> dict[str, Any]:
        attempt = {
            "request_id": request_id,
            "operation": operation,
            "method": method,
            "endpoint": endpoint,
            "body": body,
            "attempted_at_utc": utc_now(),
            "status": "attempted",
        }
        self.attempts.append(attempt)
        return attempt

    def success(self, attempt: dict[str, Any], result: dict[str, Any]) -> None:
        attempt["status"] = "succeeded"
        attempt["status_code"] = int(result.get("status_code", 0))
        attempt["completed_at_utc"] = utc_now()

    def failure(self, attempt: dict[str, Any], exc: BaseException) -> None:
        attempt["status"] = "failed"
        attempt["error"] = safe_error(exc)
        attempt["completed_at_utc"] = utc_now()

    def payload(self) -> dict[str, Any]:
        successes = [attempt for attempt in self.attempts if attempt.get("status") == "succeeded"]
        failures = [attempt for attempt in self.attempts if attempt.get("status") == "failed"]
        failed = failures[-1] if failures else None
        return {
            "attempt_count": len(self.attempts),
            "success_count": len(successes),
            "failure_count": len(failures),
            "failed_request_id": failed.get("request_id") if failed else None,
            "failed_error": failed.get("error") if failed else None,
            "attempts": self.attempts,
        }


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


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise GuardError(f"{path} must contain a JSON object")
    return payload


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


def response_has_more(response: dict[str, Any]) -> bool:
    for key in ("has_more", "has_more_results", "has_next_page"):
        if key in response:
            return bool(response[key])
    return False


def response_next_cursor(response: dict[str, Any]) -> str | None:
    for key in ("next_cursor", "cursor", "next_page_cursor", "next_page_token"):
        value = response.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return None


def list_entities(
    provider: Provider,
    *,
    entity_type: str,
    search: str,
    label: str,
    parent_folder_id: str | None = None,
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    cursor: str | None = None
    seen_cursors: set[str] = set()
    for page_index in range(MAX_LIST_PAGES):
        params: dict[str, Any] = {
            "types": entity_type,
            "page_size": 100,
            "search": search,
        }
        if parent_folder_id is not None:
            params["parent_folder_id"] = parent_folder_id
        if cursor is not None:
            params["cursor"] = cursor
        endpoint = "/v1/convai/agent-testing?" + query_string(params)
        result = provider.request("GET", endpoint)
        response = response_object(result, f"{label} page {page_index + 1}")
        items.extend(response_items(result, f"{label} page {page_index + 1}"))
        if not response_has_more(response):
            return items
        next_cursor = response_next_cursor(response)
        if next_cursor is None:
            raise GuardError(f"{label} pagination has_more without a next cursor")
        if next_cursor in seen_cursors:
            raise GuardError(f"{label} pagination cursor cycle detected at {next_cursor!r}")
        seen_cursors.add(next_cursor)
        cursor = next_cursor
    raise GuardError(f"{label} pagination exceeded page cap {MAX_LIST_PAGES}")


def mutating_request(
    provider: Provider,
    ledger: OperationLedger,
    *,
    request_id: str,
    operation: str,
    method: str,
    endpoint: str,
    body: dict[str, Any] | None,
    timeout_seconds: int = 20,
) -> dict[str, Any]:
    attempt = ledger.start(
        request_id=request_id,
        operation=operation,
        method=method,
        endpoint=endpoint,
        body=body,
    )
    try:
        result = provider.request(method, endpoint, body=body, timeout_seconds=timeout_seconds)
    except Exception as exc:
        ledger.failure(attempt, exc)
        raise
    ledger.success(attempt, result)
    return result


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
    items = list_entities(
        provider,
        entity_type="folder",
        parent_folder_id="root",
        search=CHECKPOINT_ID,
        label="folder list",
    )
    exact = [
        item
        for item in items
        if item.get("name") == CHECKPOINT_ID and parent_folder_id(item) in (None, "root")
    ]
    if len(exact) > 1:
        raise GuardError(f"duplicate exact 040 folders found: {[provider_id(item) for item in exact]}")
    return (exact[0] if exact else None), len(exact)


def create_folder(provider: Provider, ledger: OperationLedger) -> dict[str, Any]:
    result = mutating_request(
        provider,
        ledger,
        request_id=f"create_folder::{CHECKPOINT_ID}",
        operation="create-folder",
        method="POST",
        endpoint="/v1/convai/agent-testing/folders",
        body={"name": CHECKPOINT_ID},
    )
    folder = response_object(result, "create folder")
    folder_id = folder.get("id")
    if not isinstance(folder_id, str) or not folder_id:
        raise GuardError("created folder response has no folder id")
    return folder


def list_tests(provider: Provider, *, folder_id: str | None) -> list[dict[str, Any]]:
    return list_entities(
        provider,
        entity_type="simulation",
        parent_folder_id=folder_id,
        search=f"{CHECKPOINT_ID}::",
        label="test list",
    )


def get_test(provider: Provider, test_id: str) -> dict[str, Any]:
    result = provider.request("GET", f"/v1/convai/agent-testing/{quote(test_id, safe='')}")
    return response_object(result, f"test {test_id}")


def ensure_folder(provider: Provider, ledger: OperationLedger) -> dict[str, Any]:
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
    created = create_folder(provider, ledger)
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
    ledger: OperationLedger,
    existing: dict[str, dict[str, Any]],
    expected_bodies: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    created: dict[str, dict[str, Any]] = {}
    for source_id in EXPECTED_TEST_IDS:
        if source_id in existing:
            continue
        body = expected_bodies[source_id]
        result = mutating_request(
            provider,
            ledger,
            request_id=f"create_test::{source_id}",
            operation="create-test",
            method="POST",
            endpoint="/v1/convai/agent-testing/create",
            body=body,
        )
        response = response_object(result, f"create {source_id}")
        test_id = provider_id(response)
        created[source_id] = {
            "provider_test_id": test_id,
            "provider_test_name": body["name"],
            "body": body,
            "status_code": int(result.get("status_code", 0)),
        }
    return created


def move_created_tests(
    provider: Provider,
    *,
    ledger: OperationLedger,
    created: dict[str, dict[str, Any]],
    folder_id: str,
) -> None:
    ids = [created[source_id]["provider_test_id"] for source_id in EXPECTED_TEST_IDS if source_id in created]
    if not ids:
        return
    mutating_request(
        provider,
        ledger,
        request_id=f"move_created_tests::{folder_id}",
        operation="move-created-tests",
        method="POST",
        endpoint="/v1/convai/agent-testing/bulk-move",
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


def validate_owned_mapping(mapping: dict[str, Any]) -> tuple[str, dict[str, str]]:
    if mapping.get("checkpoint_id") != CHECKPOINT_ID:
        raise GuardError("live_test_mapping checkpoint_id mismatch")
    folder = mapping.get("folder")
    if not isinstance(folder, dict):
        raise GuardError("live_test_mapping folder must be an object")
    if folder.get("name") != CHECKPOINT_ID:
        raise GuardError("live_test_mapping folder name mismatch")
    folder_id = folder.get("folder_id")
    if not isinstance(folder_id, str) or not folder_id.strip():
        raise GuardError("live_test_mapping folder_id missing")
    tests = mapping.get("tests")
    if not isinstance(tests, list) or len(tests) != len(EXPECTED_TEST_IDS):
        raise GuardError("live_test_mapping tests must contain exactly ten entries")

    provider_ids: dict[str, str] = {}
    names: list[str] = []
    seen_provider_ids: set[str] = set()
    for index, (expected_source_id, item) in enumerate(zip(EXPECTED_TEST_IDS, tests, strict=True), start=1):
        if not isinstance(item, dict):
            raise GuardError(f"live_test_mapping test entry {index} must be an object")
        source_id = item.get("source_test_id")
        expected_name = f"{CHECKPOINT_ID}::{expected_source_id}"
        if source_id != expected_source_id:
            raise GuardError(f"live_test_mapping source order mismatch at {index}: {source_id!r}")
        if item.get("provider_test_name") != expected_name:
            raise GuardError(f"live_test_mapping provider test name mismatch for {expected_source_id}")
        if item.get("created_in_this_run") is not True:
            raise GuardError(f"live_test_mapping test was not created by this Task 9 runner: {expected_source_id}")
        provider_test_id = item.get("provider_test_id")
        if not isinstance(provider_test_id, str) or not provider_test_id.startswith("test_"):
            raise GuardError(f"live_test_mapping provider test ID missing or invalid for {expected_source_id}")
        if provider_test_id in seen_provider_ids:
            raise GuardError(f"duplicate provider test ID in live_test_mapping: {provider_test_id}")
        names.append(str(item.get("provider_test_name")))
        seen_provider_ids.add(provider_test_id)
        provider_ids[expected_source_id] = provider_test_id

    if len(set(names)) != len(names):
        raise GuardError("duplicate provider test names in live_test_mapping")
    return folder_id, provider_ids


def expected_without_repair_context(expected_body: dict[str, Any]) -> dict[str, Any]:
    body = json.loads(json.dumps(expected_body))
    dynamic_variables = body.get("dynamic_variables")
    if not isinstance(dynamic_variables, dict):
        raise GuardError("expected 040 body dynamic_variables must be an object")
    missing: list[str] = []
    for key, expected in REPAIR_CONTEXT_VALUES.items():
        if dynamic_variables.get(key) != expected:
            missing.append(key)
        dynamic_variables.pop(key, None)
    if missing:
        raise GuardError(f"frozen 040 body missing repair context values: {missing!r}")
    return body


def assert_only_repair_context_absent(
    *,
    source_id: str,
    live_test: dict[str, Any],
    expected_body: dict[str, Any],
    folder_id: str,
    provider_test_id: str,
) -> None:
    if provider_id(live_test) != provider_test_id:
        raise GuardError(f"provider ID readback mismatch for {source_id}")
    expected_name = f"{CHECKPOINT_ID}::{source_id}"
    if live_test.get("name") != expected_name:
        raise GuardError(f"provider test name mismatch for {source_id}")
    if parent_folder_id(live_test) not in (None, folder_id):
        raise GuardError(f"provider test folder mismatch for {source_id}")
    dynamic_variables = live_test.get("dynamic_variables")
    if not isinstance(dynamic_variables, dict):
        raise GuardError(f"provider test dynamic_variables must be an object for {source_id}")
    present_context_keys = [key for key in REPAIR_CONTEXT_KEYS if key in dynamic_variables]
    if present_context_keys:
        raise GuardError(f"provider test already contains repair context keys for {source_id}: {present_context_keys!r}")
    expected_minus_context = expected_without_repair_context(expected_body)
    if semantic_fields(live_test) != semantic_fields(expected_minus_context):
        raise GuardError(f"provider test payload drift beyond missing context for {source_id}")


def execute_repair_owned_context(
    provider: Provider | None,
    *,
    mapping_path: Path = DEFAULT_MAPPING_PATH,
    output_dir: Path = OUT_DIR,
    live: bool,
) -> dict[str, Any]:
    expected_bodies = load_expected_bodies()
    if not live:
        return {
            "checkpoint_id": CHECKPOINT_ID,
            "status": "dry_run",
            "mode": "repair_owned_context",
            "live_provider_calls_made": False,
            "provider_mutations_made": False,
            "mapping_path": str(mapping_path),
            "expected_test_count": len(EXPECTED_TEST_IDS),
            "repair_context_values": REPAIR_CONTEXT_VALUES,
            "put_semantics": TEST_UPDATE_SEMANTICS,
        }
    if provider is None:
        raise GuardError("repair-owned-context live mode requires a provider")

    ledger = OperationLedger()
    try:
        mapping = read_json(mapping_path)
        folder_id, provider_ids = validate_owned_mapping(mapping)
        live_tests: dict[str, dict[str, Any]] = {}
        for source_id in EXPECTED_TEST_IDS:
            live_test = get_test(provider, provider_ids[source_id])
            assert_only_repair_context_absent(
                source_id=source_id,
                live_test=live_test,
                expected_body=expected_bodies[source_id],
                folder_id=folder_id,
                provider_test_id=provider_ids[source_id],
            )
            live_tests[source_id] = live_test

        repaired: list[dict[str, Any]] = []
        for source_id in EXPECTED_TEST_IDS:
            provider_test_id = provider_ids[source_id]
            endpoint = f"/v1/convai/agent-testing/{quote(provider_test_id, safe='')}"
            result = mutating_request(
                provider,
                ledger,
                request_id=f"repair_test::{source_id}",
                operation="repair-owned-context",
                method="PUT",
                endpoint=endpoint,
                body=expected_bodies[source_id],
            )
            readback = get_test(provider, provider_test_id)
            if semantic_fields(readback) != semantic_fields(expected_bodies[source_id]):
                raise GuardError(f"provider repair readback mismatch for {source_id}")
            repaired.append(
                {
                    "source_test_id": source_id,
                    "provider_test_id": provider_test_id,
                    "provider_test_name": expected_bodies[source_id]["name"],
                    "provider_status_code": int(result.get("status_code", 0)),
                }
            )

        payload = {
            "checkpoint_id": CHECKPOINT_ID,
            "captured_at_utc": utc_now(),
            "status": "completed",
            "mode": "repair_owned_context",
            "folder_id": folder_id,
            "repaired_test_count": len(repaired),
            "repaired_tests": repaired,
            "repair_context_values": REPAIR_CONTEXT_VALUES,
            "put_semantics": TEST_UPDATE_SEMANTICS,
            "operation_ledger": ledger.payload(),
            "outbound_calls_made": False,
        }
        write_json(output_dir / "live_test_context_repair_result.json", payload)
        return payload
    except Exception as exc:
        failure = {
            "checkpoint_id": CHECKPOINT_ID,
            "captured_at_utc": utc_now(),
            "status": "failed",
            "mode": "repair_owned_context",
            "error": safe_error(exc),
            "put_semantics": TEST_UPDATE_SEMANTICS,
            "operation_ledger": ledger.payload(),
            "outbound_calls_made": False,
        }
        write_json(output_dir / "live_test_context_repair_result.json", failure)
        raise


def execute_canary_run(
    provider: Provider | None,
    *,
    source_test_id: str,
    mapping_path: Path = DEFAULT_MAPPING_PATH,
    output_dir: Path = OUT_DIR,
    live: bool,
    wait_timeout_seconds: int = 420,
    poll_interval_seconds: float = 2.0,
) -> dict[str, Any]:
    if source_test_id not in EXPECTED_TEST_IDS:
        raise GuardError(f"canary test ID is not part of 040 suite: {source_test_id!r}")
    if not live:
        return {
            "checkpoint_id": CHECKPOINT_ID,
            "status": "dry_run",
            "mode": "canary_run",
            "live_provider_calls_made": False,
            "provider_mutations_made": False,
            "mapping_path": str(mapping_path),
            "selected_test_ids": [source_test_id],
            "would_run_provider_test_count": 1,
        }
    if provider is None:
        raise GuardError("canary live mode requires a provider")

    ledger = OperationLedger()
    try:
        mapping = read_json(mapping_path)
        folder_id, provider_ids = validate_owned_mapping(mapping)
        result = run_tests_once(
            provider,
            ledger=ledger,
            provider_test_ids_by_source=provider_ids,
            selected_source_ids=[source_test_id],
            wait_timeout_seconds=wait_timeout_seconds,
            poll_interval_seconds=poll_interval_seconds,
        )
        result["mode"] = "canary_run"
        result["folder_id"] = folder_id
        result["operation_ledger"] = ledger.payload()
        write_json(output_dir / "live_test_canary_result.json", result)
        return result
    except Exception as exc:
        failure = {
            "checkpoint_id": CHECKPOINT_ID,
            "captured_at_utc": utc_now(),
            "status": "failed",
            "mode": "canary_run",
            "selected_test_ids": [source_test_id],
            "error": safe_error(exc),
            "operation_ledger": ledger.payload(),
            "outbound_calls_made": False,
        }
        write_json(output_dir / "live_test_canary_result.json", failure)
        raise


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
    ledger: OperationLedger,
    provider_test_ids_by_source: dict[str, str],
    selected_source_ids: list[str] | None = None,
    wait_timeout_seconds: int,
    poll_interval_seconds: float,
) -> dict[str, Any]:
    selected = selected_source_ids or EXPECTED_TEST_IDS
    if not selected or any(source_id not in EXPECTED_TEST_IDS for source_id in selected):
        raise GuardError(f"invalid selected 040 tests: {selected!r}")
    run_body = {
        "tests": [{"test_id": provider_test_ids_by_source[source_id]} for source_id in selected],
        "repeat_count": 1,
    }
    run_result = mutating_request(
        provider,
        ledger,
        request_id=f"run_tests::{AGENT_ID}",
        operation="run-tests",
        method="POST",
        endpoint=f"/v1/convai/agents/{quote(AGENT_ID, safe='')}/run-tests",
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
        statuses = completed_terminal_statuses(invocation, expected_run_count=len(selected))
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
        "selected_test_count": len(selected),
        "selected_test_ids": selected,
        "expected_terminal_run_count": len(selected),
        "observed_terminal_run_count": len(run_summaries),
        "failed_terminal_run_count": len(failed_runs),
        "provider_status_code": int(run_result.get("status_code", 0)),
        "provider_test_ids": provider_test_ids_by_source,
        "run_statuses": run_summaries,
        "final_run_statuses": final_statuses,
        "outbound_calls_made": False,
    }


def execute_with_provider(
    provider: Provider | None,
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

    if provider is None:
        raise GuardError("live execution requires a provider")
    ledger = OperationLedger()
    try:
        expected_bodies = load_expected_bodies()
        folder = ensure_folder(provider, ledger)
        existing, duplicate_prevention = discover_tests(
            provider,
            folder_id=folder["folder_id"],
            expected_bodies=expected_bodies,
        )
        created = create_missing_tests(
            provider,
            ledger=ledger,
            existing=existing,
            expected_bodies=expected_bodies,
        )
        move_created_tests(provider, ledger=ledger, created=created, folder_id=folder["folder_id"])
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
            ledger=ledger,
            provider_test_ids_by_source=provider_ids,
            wait_timeout_seconds=wait_timeout_seconds,
            poll_interval_seconds=poll_interval_seconds,
        )
        result["folder_id"] = folder["folder_id"]
        result["operation_ledger"] = ledger.payload()
        write_json(output_dir / "live_test_run_result.json", result)
        return {"status": result["status"], "mapping": mapping, "run_result": result}
    except Exception as exc:
        failure = {
            "checkpoint_id": CHECKPOINT_ID,
            "captured_at_utc": utc_now(),
            "status": "failed",
            "error": safe_error(exc),
            "operation_ledger": ledger.payload(),
            "outbound_calls_made": False,
        }
        write_json(output_dir / "live_test_run_result.json", failure)
        raise


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Guard and run the ELEVENLABS-040 dashboard tests.")
    parser.add_argument("--dry-run", action="store_true", help="Plan only. This is the default and makes no provider calls.")
    parser.add_argument(
        "--confirm-test-creation-and-run",
        choices=(CONFIRMATION,),
        default=None,
        help="Exact token required before creating/moving/running provider tests.",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--repair-owned-context",
        action="store_true",
        help="Repair only the owned 040 tests whose sole drift is missing shared business context variables.",
    )
    mode.add_argument(
        "--canary-test-id",
        choices=tuple(EXPECTED_TEST_IDS),
        default=None,
        help="Run one mapped 040 provider test once and write separate canary evidence.",
    )
    parser.add_argument(
        "--confirm-owned-context-repair",
        choices=(REPAIR_CONFIRMATION,),
        default=None,
        help="Exact token required before PUT repair of owned 040 test context.",
    )
    parser.add_argument(
        "--confirm-canary-run",
        choices=(CANARY_CONFIRMATION,),
        default=None,
        help="Exact token required before a one-test canary run.",
    )
    parser.add_argument("--mapping-path", type=Path, default=DEFAULT_MAPPING_PATH)
    parser.add_argument("--wait-timeout-seconds", type=int, default=420)
    parser.add_argument("--poll-interval-seconds", type=float, default=2.0)
    args = parser.parse_args(argv)
    selected_modes = [
        args.confirm_test_creation_and_run == CONFIRMATION,
        args.repair_owned_context,
        args.canary_test_id is not None,
    ]
    if sum(1 for selected in selected_modes if selected) > 1:
        parser.error("select exactly one live-capable mode")
    if args.confirm_owned_context_repair and not args.repair_owned_context:
        parser.error("--confirm-owned-context-repair requires --repair-owned-context")
    if args.confirm_canary_run and args.canary_test_id is None:
        parser.error("--confirm-canary-run requires --canary-test-id")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.repair_owned_context:
        repair_live = args.confirm_owned_context_repair == REPAIR_CONFIRMATION and not args.dry_run
        if not repair_live:
            plan = execute_repair_owned_context(
                provider=None,
                mapping_path=args.mapping_path,
                live=False,
            )
            print(json.dumps(plan, indent=2, ensure_ascii=True))
            return 0
        api_key = os.environ.get(API_KEY_ENV_VAR, "").strip()
        if not api_key:
            print(f"error: {API_KEY_ENV_VAR} is required for live owned-context repair", file=sys.stderr)
            return 2
        try:
            result = execute_repair_owned_context(
                ElevenLabsProvider(api_key),
                mapping_path=args.mapping_path,
                live=True,
            )
        except Exception as exc:
            print(f"error: {safe_error(exc)}", file=sys.stderr)
            return 1
        print(json.dumps(result, indent=2, ensure_ascii=True))
        return 0 if result["status"] == "completed" else 1

    if args.canary_test_id is not None:
        canary_live = args.confirm_canary_run == CANARY_CONFIRMATION and not args.dry_run
        if not canary_live:
            plan = execute_canary_run(
                provider=None,
                source_test_id=args.canary_test_id,
                mapping_path=args.mapping_path,
                live=False,
                wait_timeout_seconds=args.wait_timeout_seconds,
                poll_interval_seconds=args.poll_interval_seconds,
            )
            print(json.dumps(plan, indent=2, ensure_ascii=True))
            return 0
        api_key = os.environ.get(API_KEY_ENV_VAR, "").strip()
        if not api_key:
            print(f"error: {API_KEY_ENV_VAR} is required for live canary run", file=sys.stderr)
            return 2
        try:
            result = execute_canary_run(
                ElevenLabsProvider(api_key),
                source_test_id=args.canary_test_id,
                mapping_path=args.mapping_path,
                live=True,
                wait_timeout_seconds=args.wait_timeout_seconds,
                poll_interval_seconds=args.poll_interval_seconds,
            )
        except Exception as exc:
            print(f"error: {safe_error(exc)}", file=sys.stderr)
            return 1
        print(json.dumps(result, indent=2, ensure_ascii=True))
        return 0 if result["status"] == "completed" else 1

    full_live = args.confirm_test_creation_and_run == CONFIRMATION and not args.dry_run
    if not full_live:
        plan = execute_with_provider(
            provider=None,
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
