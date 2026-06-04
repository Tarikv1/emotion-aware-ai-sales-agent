#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import json
import mimetypes
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
CHECKPOINT_ID = "ELEVENLABS-002-agent-automation"
PROVIDER = "elevenlabs"
API_BASE_URL = "https://api.elevenlabs.io"
API_KEY_ENV_VAR = "ELEVENLABS_API_KEY"
DEFAULT_PACKAGE_MANIFEST = (
    ROOT
    / "runtime"
    / "providers"
    / "elevenlabs_agents"
    / "manifests"
    / "universal_sales_core.package.json"
)
DEFAULT_OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
DEFAULT_PLAN = DEFAULT_OUT_DIR / "automation_plan.json"
DEFAULT_API_REQUESTS = DEFAULT_OUT_DIR / "api_requests.json"
DEFAULT_AGENT_PATCH = DEFAULT_OUT_DIR / "agent_patch_payload.json"

PRIVATE_PATH_PARTS = (("data", "private"), ("data", "private-restricted"))
SAFE_LIVE_RESPONSE_KEYS = (
    "id",
    "document_id",
    "folder_id",
    "test_id",
    "test_run_id",
    "run_id",
    "agent_id",
    "name",
    "status",
    "status_code",
)


def validate_chat_history_entries(payload: Any, *, source_label: str) -> list[dict[str, Any]]:
    if not isinstance(payload, list) or not payload:
        raise ValueError(f"{source_label} chat_history must be a non-empty list.")
    entries: list[dict[str, Any]] = []
    for index, item in enumerate(payload):
        if not isinstance(item, dict):
            raise ValueError(f"{source_label} chat_history item {index} must be an object.")
        role = str(item.get("role", "")).strip()
        if role not in {"user", "agent"}:
            raise ValueError(f"{source_label} chat_history item {index} role must be user or agent.")
        message = str(item.get("message", "")).strip()
        if not message:
            raise ValueError(f"{source_label} chat_history item {index} message is required.")
        time_in_call_secs = item.get("time_in_call_secs", index + 1)
        if not isinstance(time_in_call_secs, (int, float)) or time_in_call_secs < 0:
            raise ValueError(f"{source_label} chat_history item {index} time_in_call_secs must be non-negative.")
        entries.append(
            {
                "role": role,
                "message": message,
                "time_in_call_secs": time_in_call_secs,
            }
        )
    if entries[-1]["role"] != "user":
        raise ValueError(f"{source_label} chat_history must end with a user turn.")
    return entries


def rel_path(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def resolve_project_path(path_value: str | Path) -> Path:
    path = Path(path_value)
    candidate = path if path.is_absolute() else ROOT / path
    resolved = candidate.resolve(strict=False)
    root_resolved = ROOT.resolve(strict=False)
    try:
        resolved.relative_to(root_resolved)
    except ValueError as exc:
        raise ValueError(f"Path must stay inside project root: {path_value}") from exc
    parts = tuple(part.lower() for part in resolved.parts)
    for private_parts in PRIVATE_PATH_PARTS:
        for index in range(0, len(parts) - len(private_parts) + 1):
            if parts[index : index + len(private_parts)] == private_parts:
                raise ValueError(f"Path is restricted for ElevenLabs automation: {path_value}")
    return resolved


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{rel_path(path)} must contain a JSON object.")
    return payload


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def read_text(path: Path) -> str:
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        raise ValueError(f"{rel_path(path)} must not be empty.")
    return text


def load_package(manifest_path: Path) -> dict[str, Any]:
    manifest = read_json(manifest_path)
    if manifest.get("provider") != PROVIDER:
        raise ValueError("Package manifest provider must be elevenlabs.")
    if manifest.get("source_of_truth") != "repo":
        raise ValueError("Package manifest must keep repo as source_of_truth.")
    return manifest


def kb_upload_request(source_path_text: str) -> dict[str, Any]:
    source_path = resolve_project_path(source_path_text)
    if not source_path.is_file():
        raise FileNotFoundError(rel_path(source_path))
    content_bytes = source_path.read_bytes()
    return {
        "request_id": f"upload_knowledge_base::{source_path.stem}",
        "method": "POST",
        "endpoint": "/v1/convai/knowledge-base/file",
        "source_path": rel_path(source_path),
        "name": source_path.name,
        "content_bytes": len(content_bytes),
        "content_type": mimetypes.guess_type(source_path.name)[0] or "text/markdown",
        "requires_api_key_env_var": API_KEY_ENV_VAR,
        "docs_url": "https://elevenlabs.io/docs/eleven-agents/api-reference/knowledge-base/create-from-file",
    }


def _single_turn_chat_history(customer_utterance: str) -> list[dict[str, Any]]:
    return [
        {
            "role": "user",
            "message": customer_utterance,
            "time_in_call_secs": 1,
        }
    ]


def build_chat_history(item: dict[str, Any], *, test_id: str) -> list[dict[str, Any]]:
    if "chat_history" in item:
        return validate_chat_history_entries(item["chat_history"], source_label=test_id)
    return _single_turn_chat_history(str(item["customer_utterance"]))


def _success_condition(item: dict[str, Any]) -> str:
    return (
        "Return True only if the agent response follows this expected behavior: "
        f"{item['expected_behavior']} Return False if it does this forbidden behavior: "
        f"{item['forbidden_behavior']}"
    )


def _validate_dynamic_variables(payload: Any, *, source_label: str) -> dict[str, Any]:
    if payload is None:
        return {}
    if not isinstance(payload, dict):
        raise ValueError(f"{source_label} dynamic_variables must be an object.")
    variables: dict[str, Any] = {}
    for key, value in payload.items():
        key_text = str(key).strip()
        if not key_text:
            raise ValueError(f"{source_label} dynamic_variables contains an empty key.")
        if value is not None and not isinstance(value, (str, int, float, bool)):
            raise ValueError(f"{source_label} dynamic variable {key_text} must be a scalar value.")
        variables[key_text] = value
    return variables


def build_dynamic_variables(
    item: dict[str, Any],
    *,
    package_id: str,
    suite_dynamic_variables: dict[str, Any] | None = None,
) -> dict[str, Any]:
    variables: dict[str, Any] = {
        "campaign_name": "universal-sales-core-validation",
        "source_package_id": package_id,
    }
    variables.update(
        _validate_dynamic_variables(
            suite_dynamic_variables,
            source_label=f"{package_id} suite",
        )
    )
    variables.update(
        _validate_dynamic_variables(
            item.get("dynamic_variables", {}),
            source_label=str(item.get("test_id", "test")),
        )
    )
    variables["source_package_id"] = package_id
    return variables


def test_create_request(
    item: dict[str, Any],
    *,
    package_id: str,
    suite_dynamic_variables: dict[str, Any] | None = None,
) -> dict[str, Any]:
    test_id = str(item["test_id"])
    body = {
        "type": "llm",
        "name": f"{package_id}::{test_id}",
        "chat_history": build_chat_history(item, test_id=test_id),
        "success_condition": _success_condition(item),
        "success_examples": [
            {
                "type": "success",
                "response": str(item["expected_behavior"]),
            }
        ],
        "failure_examples": [
            {
                "type": "failure",
                "response": str(item["forbidden_behavior"]),
            }
        ],
        "dynamic_variables": build_dynamic_variables(
            item,
            package_id=package_id,
            suite_dynamic_variables=suite_dynamic_variables,
        ),
    }
    return {
        "request_id": f"create_test::{test_id}",
        "method": "POST",
        "endpoint": "/v1/convai/agent-testing/create",
        "source_test_id": test_id,
        "body": body,
        "requires_api_key_env_var": API_KEY_ENV_VAR,
        "docs_url": "https://elevenlabs.io/docs/eleven-agents/api-reference/tests/create",
    }


def load_baseline_tests(path_text: str, *, package_id: str) -> list[dict[str, Any]]:
    path = resolve_project_path(path_text)
    payload = read_json(path)
    if payload.get("package_id") != package_id:
        raise ValueError(f"{rel_path(path)} package_id does not match {package_id}.")
    tests = payload.get("tests")
    if not isinstance(tests, list) or not tests:
        raise ValueError(f"{rel_path(path)} has no tests.")
    suite_dynamic_variables = _validate_dynamic_variables(
        payload.get("dynamic_variables", {}),
        source_label=f"{rel_path(path)} suite",
    )
    return [
        test_create_request(
            dict(item),
            package_id=package_id,
            suite_dynamic_variables=suite_dynamic_variables,
        )
        for item in tests
    ]


def build_run_tests_request(agent_id: str | None) -> dict[str, Any]:
    endpoint_agent = agent_id or "{agent_id}"
    return {
        "request_id": "run_tests::{agent_id}",
        "method": "POST",
        "endpoint": f"/v1/convai/agents/{endpoint_agent}/run-tests",
        "agent_id": agent_id,
        "requires_created_test_ids": True,
        "body_template": {
            "tests": [
                {
                    "test_id": "{created_test_id}"
                }
            ],
            "repeat_count": 1,
        },
        "docs_url": "https://elevenlabs.io/docs/eleven-agents/api-reference/tests/run-tests",
    }


def build_kb_documents(ids: list[str], names: list[str]) -> list[dict[str, str]]:
    if not ids:
        return []
    if not names:
        names = ["universal_sales_core.md"]
    if len(names) == 1 and len(ids) > 1:
        names = names * len(ids)
    if len(names) != len(ids):
        raise ValueError("--kb-document-name count must be 1 or match --kb-document-id count.")
    return [
        {
            "type": "file",
            "name": name,
            "id": document_id,
        }
        for document_id, name in zip(ids, names)
    ]


def merge_knowledge_base_entries(
    existing_entries: list[dict[str, Any]],
    new_entries: list[dict[str, str]],
) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for item in [*existing_entries, *new_entries]:
        if not isinstance(item, dict):
            continue
        item_id = str(item.get("id", "")).strip()
        if not item_id or item_id in seen_ids:
            continue
        merged.append(dict(item))
        seen_ids.add(item_id)
    return merged


def build_agent_patch_payload(
    agent_config: dict[str, Any],
    kb_documents: list[dict[str, str]],
    *,
    prompt_override: str | None = None,
    first_message_override: str | None = None,
    dynamic_variable_placeholders: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not kb_documents:
        raise ValueError("At least one KB document ID is required for an agent patch payload.")
    agent_id = str(agent_config.get("agent_id", "")).strip()
    if not agent_id:
        raise ValueError("Copied agent config is missing agent_id.")
    conversation_config = copy.deepcopy(agent_config.get("conversation_config"))
    if not isinstance(conversation_config, dict):
        raise ValueError("Copied agent config is missing conversation_config.")
    prompt = conversation_config.setdefault("agent", {}).setdefault("prompt", {})
    if not isinstance(prompt, dict):
        raise ValueError("Copied agent config prompt must be an object.")
    if prompt_override:
        prompt["prompt"] = prompt_override
    if first_message_override:
        agent_section = conversation_config.setdefault("agent", {})
        if not isinstance(agent_section, dict):
            raise ValueError("Copied agent config agent section must be an object.")
        agent_section["first_message"] = first_message_override
    if dynamic_variable_placeholders is not None:
        agent_section = conversation_config.setdefault("agent", {})
        if not isinstance(agent_section, dict):
            raise ValueError("Copied agent config agent section must be an object.")
        dynamic_variables = agent_section.setdefault("dynamic_variables", {})
        if not isinstance(dynamic_variables, dict):
            raise ValueError("Copied agent config dynamic_variables must be an object.")
        dynamic_variables["dynamic_variable_placeholders"] = _validate_dynamic_variables(
            dynamic_variable_placeholders,
            source_label="agent dynamic_variable_placeholders",
        )
    existing_kb = prompt.get("knowledge_base", [])
    if not isinstance(existing_kb, list):
        raise ValueError("Copied agent config prompt.knowledge_base must be a list.")
    prompt["knowledge_base"] = merge_knowledge_base_entries(existing_kb, kb_documents)
    rag = prompt.setdefault("rag", {})
    if not isinstance(rag, dict):
        raise ValueError("Copied agent config prompt.rag must be an object.")
    rag["enabled"] = True
    version_scope = (
        "ELEVENLABS-006 web design prompt naturalness patch"
        if prompt_override or first_message_override or dynamic_variable_placeholders is not None
        else "ELEVENLABS-003 knowledge base attachment"
    )
    return {
        "name": str(agent_config.get("name") or "web design"),
        "conversation_config": conversation_config,
        "workflow": copy.deepcopy(agent_config.get("workflow", {})),
        "tags": copy.deepcopy(agent_config.get("tags", [])),
        "version_description": f"{version_scope}; attach {len(kb_documents)} repo-owned knowledge base document(s)",
    }


def build_agent_patch_draft(
    agent_id: str | None,
    *,
    agent_config_path: Path | None = None,
    kb_documents: list[dict[str, str]] | None = None,
    patch_payload_out: Path | None = None,
    prompt_override: str | None = None,
    first_message_override: str | None = None,
    dynamic_variable_placeholders: dict[str, Any] | None = None,
) -> dict[str, Any]:
    endpoint_agent = agent_id or "{agent_id}"
    if agent_config_path and kb_documents:
        agent_config = read_json(agent_config_path)
        copied_agent_id = str(agent_config.get("agent_id", "")).strip()
        if not copied_agent_id:
            raise ValueError("Copied agent config is missing agent_id.")
        if agent_id and agent_id != copied_agent_id:
            raise ValueError(f"--agent-id {agent_id} does not match copied config agent_id {copied_agent_id}.")
        patch_payload = build_agent_patch_payload(
            agent_config,
            kb_documents,
            prompt_override=prompt_override,
            first_message_override=first_message_override,
            dynamic_variable_placeholders=dynamic_variable_placeholders,
        )
        patch_out = patch_payload_out or DEFAULT_AGENT_PATCH
        write_json(patch_out, patch_payload)
        return {
            "request_id": "patch_agent::{agent_id}",
            "method": "PATCH",
            "endpoint": f"/v1/convai/agents/{copied_agent_id}",
            "agent_id": copied_agent_id,
            "status": "ready_for_review",
            "source_config_path": rel_path(agent_config_path),
            "patch_payload_path": rel_path(patch_out),
            "knowledge_base_documents": kb_documents,
            "prompt_override_applied": prompt_override is not None,
            "first_message_override_applied": first_message_override is not None,
            "dynamic_variable_placeholders_applied": dynamic_variable_placeholders is not None,
            "docs_url": "https://elevenlabs.io/docs/eleven-agents/api-reference/agents/update",
        }
    return {
        "request_id": "patch_agent::{agent_id}",
        "method": "PATCH",
        "endpoint": f"/v1/convai/agents/{endpoint_agent}",
        "agent_id": agent_id,
        "status": "draft_only",
        "reason": (
            "Attaching knowledge base documents requires the current dashboard "
            "agent JSON shape. Use Copy agent JSON config before enabling this write."
        ),
        "docs_url": "https://elevenlabs.io/docs/eleven-agents/api-reference/agents/update",
    }


def build_plan(
    *,
    package_manifest_path: Path,
    agent_id: str | None,
    agent_name: str,
    agent_config_path: Path | None = None,
    kb_documents: list[dict[str, str]] | None = None,
    agent_patch_out: Path | None = None,
    prompt_override: str | None = None,
    first_message_override: str | None = None,
    dynamic_variable_placeholders: dict[str, Any] | None = None,
) -> dict[str, Any]:
    manifest = load_package(package_manifest_path)
    package_id = str(manifest["package_id"])
    kb_requests = [
        kb_upload_request(path_text)
        for path_text in manifest.get("knowledge_base_docs", [])
    ]
    test_requests: list[dict[str, Any]] = []
    for test_path in manifest.get("baseline_tests", []):
        test_requests.extend(load_baseline_tests(str(test_path), package_id=package_id))
    run_tests = build_run_tests_request(agent_id)
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "package_id": package_id,
        "provider": PROVIDER,
        "mode": "dry_run",
        "source_of_truth": "repo",
        "dashboard_role": "managed runtime and manual upload surface",
        "agent_id": agent_id,
        "agent_name": agent_name,
        "api_base_url": API_BASE_URL,
        "api_key_env_var": API_KEY_ENV_VAR,
        "live_provider_calls_made": False,
        "private_customer_data_used": False,
        "provider_writes_require": ["--live", "--confirm-provider-write"],
        "knowledge_base_upload_requests": kb_requests,
        "test_create_requests": test_requests,
        "run_tests_request": run_tests,
        "agent_config_patch": build_agent_patch_draft(
            agent_id,
            agent_config_path=agent_config_path,
            kb_documents=kb_documents,
            patch_payload_out=agent_patch_out,
            prompt_override=prompt_override,
            first_message_override=first_message_override,
            dynamic_variable_placeholders=dynamic_variable_placeholders,
        ),
        "test_folder": {
            "folder_name": None,
            "folder_id": None,
            "parent_folder_id": None,
            "applies_to_live_created_tests": False,
        },
        "dashboard_upload_order": [
            "Upload knowledge base documents",
            "Create baseline tests",
            "Attach returned knowledge base document IDs to the agent",
            "Run tests against the selected agent or branch",
            "Copy agent JSON config back into the repo for drift review",
        ],
    }


def build_api_requests_bundle(plan: dict[str, Any]) -> dict[str, Any]:
    requests: list[dict[str, Any]] = []
    for request in plan["knowledge_base_upload_requests"]:
        requests.append(
            {
                "request_id": request["request_id"],
                "method": request["method"],
                "url": API_BASE_URL + request["endpoint"],
                "content_type": "multipart/form-data",
                "fields": {
                    "file": request["source_path"],
                    "name": request["name"],
                },
                "docs_url": request["docs_url"],
            }
        )
    for request in plan["test_create_requests"]:
        requests.append(
            {
                "request_id": request["request_id"],
                "method": request["method"],
                "url": API_BASE_URL + request["endpoint"],
                "content_type": "application/json",
                "body": request["body"],
                "docs_url": request["docs_url"],
            }
        )
    requests.append(
        {
            "request_id": plan["run_tests_request"]["request_id"],
            "method": plan["run_tests_request"]["method"],
            "url": API_BASE_URL + plan["run_tests_request"]["endpoint"],
            "content_type": "application/json",
            "body_template": plan["run_tests_request"]["body_template"],
            "requires_created_test_ids": True,
            "docs_url": plan["run_tests_request"]["docs_url"],
        }
    )
    patch = plan.get("agent_config_patch", {})
    if patch.get("status") == "ready_for_review":
        payload_path = resolve_project_path(patch["patch_payload_path"])
        requests.append(
            {
                "request_id": patch["request_id"],
                "method": patch["method"],
                "url": API_BASE_URL + patch["endpoint"],
                "content_type": "application/json",
                "body": read_json(payload_path),
                "docs_url": patch["docs_url"],
            }
        )
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "provider": PROVIDER,
        "mode": plan["mode"],
        "api_key_env_var": API_KEY_ENV_VAR,
        "live_provider_calls_made": False,
        "requests": requests,
    }


def _json_request(
    method: str,
    endpoint: str,
    *,
    api_key: str,
    body: dict[str, Any] | None = None,
    timeout_seconds: int = 20,
) -> dict[str, Any]:
    data = None if body is None else json.dumps(body).encode("utf-8")
    request = urllib.request.Request(
        API_BASE_URL + endpoint,
        data=data,
        method=method,
        headers={
            "Content-Type": "application/json",
            "xi-api-key": api_key,
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            response_text = response.read().decode("utf-8")
            return {
                "status_code": response.status,
                "response": json.loads(response_text) if response_text else {},
            }
    except urllib.error.HTTPError as exc:
        body_text = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"ElevenLabs API error {exc.code}: {body_text[:800]}") from exc


def find_or_create_test_folder(
    *,
    api_key: str,
    folder_name: str,
    folder_id: str | None = None,
    parent_folder_id: str | None = None,
) -> dict[str, Any]:
    if folder_id:
        result = _json_request("GET", f"/v1/convai/agent-testing/folders/{urllib.parse.quote(folder_id)}", api_key=api_key)
        response = result["response"]
        return {
            "folder_id": response.get("id") or folder_id,
            "name": response.get("name"),
            "created": False,
        }
    query = urllib.parse.urlencode(
        {
            "types": "folder",
            "page_size": 100,
            "search": folder_name,
        }
    )
    result = _json_request("GET", f"/v1/convai/agent-testing?{query}", api_key=api_key)
    for item in result["response"].get("tests", []):
        if not isinstance(item, dict):
            continue
        if item.get("entity_type") != "folder" and item.get("type") != "folder":
            continue
        if item.get("name") != folder_name:
            continue
        if parent_folder_id and item.get("folder_parent_id") != parent_folder_id:
            continue
        return {
            "folder_id": item["id"],
            "name": item.get("name"),
            "created": False,
        }
    body: dict[str, Any] = {"name": folder_name}
    if parent_folder_id:
        body["parent_folder_id"] = parent_folder_id
    created = _json_request("POST", "/v1/convai/agent-testing/folders", api_key=api_key, body=body)
    response = created["response"]
    return {
        "folder_id": response.get("id"),
        "name": response.get("name"),
        "created": True,
    }


def move_tests_to_folder(*, api_key: str, test_ids: list[str], folder_id: str) -> dict[str, Any]:
    if not test_ids:
        return {"moved_count": 0, "folder_id": folder_id}
    _json_request(
        "POST",
        "/v1/convai/agent-testing/bulk-move",
        api_key=api_key,
        body={
            "entity_ids": test_ids,
            "move_to": folder_id,
        },
    )
    return {
        "moved_count": len(test_ids),
        "folder_id": folder_id,
        "test_ids": test_ids,
    }


def _multipart_upload(
    source_path: Path,
    *,
    api_key: str,
    name: str,
    timeout_seconds: int = 30,
) -> dict[str, Any]:
    boundary = f"----codex-elevenlabs-{int(time.time() * 1000)}"
    file_bytes = source_path.read_bytes()
    content_type = mimetypes.guess_type(source_path.name)[0] or "text/markdown"
    parts = [
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="name"\r\n\r\n{name}\r\n'.encode("utf-8"),
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{source_path.name}"\r\n'
        f"Content-Type: {content_type}\r\n\r\n".encode("utf-8"),
        file_bytes,
        f"\r\n--{boundary}--\r\n".encode("utf-8"),
    ]
    body = b"".join(parts)
    request = urllib.request.Request(
        API_BASE_URL + "/v1/convai/knowledge-base/file",
        data=body,
        method="POST",
        headers={
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "xi-api-key": api_key,
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            response_text = response.read().decode("utf-8")
            return {
                "status_code": response.status,
                "response": json.loads(response_text) if response_text else {},
            }
    except urllib.error.HTTPError as exc:
        body_text = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"ElevenLabs KB upload error {exc.code}: {body_text[:800]}") from exc


def require_live_write(args: argparse.Namespace) -> str:
    if not args.live or not args.confirm_provider_write:
        raise SystemExit("Provider writes require --live and --confirm-provider-write.")
    api_key = os.getenv(API_KEY_ENV_VAR, "").strip()
    if not api_key:
        raise SystemExit(f"Set {API_KEY_ENV_VAR} in the environment before live provider writes.")
    return api_key


def _safe_live_response_values(response: dict[str, Any], keys: tuple[str, ...]) -> dict[str, Any]:
    safe: dict[str, Any] = {}
    for key in keys:
        if key not in response:
            continue
        value = response[key]
        if value is None or isinstance(value, (str, int, float, bool)):
            safe[key] = value
    return safe


def summarize_provider_response(response: Any, operation: str) -> dict[str, Any]:
    if not isinstance(response, dict):
        return {"summary": "non_object_response"}
    if operation == "patch-agent":
        conversation_config = response.get("conversation_config")
        prompt: dict[str, Any] = {}
        if isinstance(conversation_config, dict):
            agent = conversation_config.get("agent")
            if isinstance(agent, dict) and isinstance(agent.get("prompt"), dict):
                prompt = agent["prompt"]
        knowledge_base = prompt.get("knowledge_base", [])
        kb_ids = [
            str(item.get("id"))
            for item in knowledge_base
            if isinstance(item, dict) and item.get("id")
        ]
        rag = prompt.get("rag", {})
        return {
            "agent_id": response.get("agent_id"),
            "name": response.get("name"),
            "version_id": response.get("version_id"),
            "branch_id": response.get("branch_id"),
            "knowledge_base_document_ids": kb_ids,
            "rag_enabled": rag.get("enabled") if isinstance(rag, dict) else None,
        }
    safe = _safe_live_response_values(response, SAFE_LIVE_RESPONSE_KEYS)
    if safe:
        return safe
    return {"summary": "response_received"}


def perform_live_operation(args: argparse.Namespace, plan: dict[str, Any]) -> dict[str, Any]:
    if args.operation == "plan":
        return {"operation": "plan", "live_provider_calls_made": False, "results": []}
    api_key = require_live_write(args)
    results: list[dict[str, Any]] = []
    created_test_ids: list[str] = []
    if args.operation in {"upload-kb", "all"}:
        for request in plan["knowledge_base_upload_requests"]:
            source_path = resolve_project_path(request["source_path"])
            result = _multipart_upload(source_path, api_key=api_key, name=request["name"])
            results.append(
                {
                    "request_id": request["request_id"],
                    "operation": "upload-kb",
                    "status_code": result["status_code"],
                    "response_summary": summarize_provider_response(result["response"], "upload-kb"),
                }
            )
    if args.operation in {"create-tests", "all"}:
        for request in plan["test_create_requests"]:
            result = _json_request("POST", request["endpoint"], api_key=api_key, body=request["body"])
            results.append(
                {
                    "request_id": request["request_id"],
                    "operation": "create-tests",
                    "status_code": result["status_code"],
                    "response_summary": summarize_provider_response(result["response"], "create-tests"),
                }
            )
            response_id = result["response"].get("id")
            if isinstance(response_id, str) and response_id:
                created_test_ids.append(response_id)
        if created_test_ids and (args.test_folder_name or args.test_folder_id):
            folder = find_or_create_test_folder(
                api_key=api_key,
                folder_name=args.test_folder_name or args.test_folder_id,
                folder_id=args.test_folder_id,
                parent_folder_id=args.test_folder_parent_id,
            )
            folder_id = str(folder["folder_id"])
            moved = move_tests_to_folder(api_key=api_key, test_ids=created_test_ids, folder_id=folder_id)
            results.append(
                {
                    "request_id": "move_created_tests::{test_folder}",
                    "operation": "move-tests-to-folder",
                    "status_code": 200,
                    "response_summary": {
                        "folder_id": folder_id,
                        "folder_name": folder.get("name"),
                        "folder_created": folder.get("created"),
                        "moved_count": moved["moved_count"],
                    },
                }
            )
    if args.operation == "run-tests":
        if not args.agent_id:
            raise SystemExit("--agent-id is required for run-tests.")
        if not args.created_test_ids:
            raise SystemExit("--created-test-ids is required for run-tests.")
        body = {
            "tests": [{"test_id": test_id} for test_id in args.created_test_ids],
            "repeat_count": args.repeat_count,
        }
        result = _json_request(
            "POST",
            f"/v1/convai/agents/{urllib.parse.quote(args.agent_id)}/run-tests",
            api_key=api_key,
            body=body,
        )
        results.append(
            {
                "request_id": "run_tests::{agent_id}",
                "operation": "run-tests",
                "status_code": result["status_code"],
                "response_summary": summarize_provider_response(result["response"], "run-tests"),
            }
        )
    if args.operation == "patch-agent":
        patch = plan.get("agent_config_patch", {})
        if patch.get("status") != "ready_for_review":
            raise SystemExit("--agent-config and --kb-document-id are required for patch-agent.")
        patch_payload = read_json(resolve_project_path(patch["patch_payload_path"]))
        result = _json_request("PATCH", patch["endpoint"], api_key=api_key, body=patch_payload)
        results.append(
            {
                "request_id": "patch_agent::{agent_id}",
                "operation": "patch-agent",
                "status_code": result["status_code"],
                "response_summary": summarize_provider_response(result["response"], "patch-agent"),
            }
        )
    if args.operation == "move-tests":
        if not args.created_test_ids:
            raise SystemExit("--created-test-ids is required for move-tests.")
        if not args.test_folder_name and not args.test_folder_id:
            raise SystemExit("--test-folder-name or --test-folder-id is required for move-tests.")
        folder = find_or_create_test_folder(
            api_key=api_key,
            folder_name=args.test_folder_name or args.test_folder_id,
            folder_id=args.test_folder_id,
            parent_folder_id=args.test_folder_parent_id,
        )
        folder_id = str(folder["folder_id"])
        moved = move_tests_to_folder(api_key=api_key, test_ids=args.created_test_ids, folder_id=folder_id)
        results.append(
            {
                "request_id": "move_tests::{test_folder}",
                "operation": "move-tests",
                "status_code": 200,
                "response_summary": {
                    "folder_id": folder_id,
                    "folder_name": folder.get("name"),
                    "folder_created": folder.get("created"),
                    "moved_count": moved["moved_count"],
                },
            }
        )
    return {
        "operation": args.operation,
        "live_provider_calls_made": bool(results),
        "api_key_env_var": API_KEY_ENV_VAR,
        "results": results,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build or execute ElevenLabs Agent package automation.")
    parser.add_argument("--package-manifest", default=str(DEFAULT_PACKAGE_MANIFEST))
    parser.add_argument("--agent-id", default=None)
    parser.add_argument("--agent-name", default="Atlas Universal Sales Core")
    parser.add_argument("--out", default=str(DEFAULT_PLAN))
    parser.add_argument("--api-requests-out", default=str(DEFAULT_API_REQUESTS))
    parser.add_argument("--agent-config", default=None)
    parser.add_argument("--agent-patch-out", default=str(DEFAULT_AGENT_PATCH))
    parser.add_argument("--agent-prompt-file", default=None)
    parser.add_argument("--first-message-file", default=None)
    parser.add_argument("--dynamic-variable-defaults", default=None)
    parser.add_argument("--kb-document-id", action="append", default=[])
    parser.add_argument("--kb-document-name", action="append", default=[])
    parser.add_argument(
        "--operation",
        choices=("plan", "upload-kb", "create-tests", "run-tests", "patch-agent", "move-tests", "all"),
        default="plan",
    )
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--confirm-provider-write", action="store_true")
    parser.add_argument("--created-test-ids", nargs="*", default=[])
    parser.add_argument("--repeat-count", type=int, default=1)
    parser.add_argument("--test-folder-name", default=None)
    parser.add_argument("--test-folder-id", default=None)
    parser.add_argument("--test-folder-parent-id", default=None)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    manifest_path = resolve_project_path(args.package_manifest)
    agent_config_path = resolve_project_path(args.agent_config) if args.agent_config else None
    agent_prompt_path = resolve_project_path(args.agent_prompt_file) if args.agent_prompt_file else None
    first_message_path = resolve_project_path(args.first_message_file) if args.first_message_file else None
    dynamic_defaults_path = resolve_project_path(args.dynamic_variable_defaults) if args.dynamic_variable_defaults else None
    if agent_config_path and not args.agent_id:
        copied_config = read_json(agent_config_path)
        args.agent_id = str(copied_config.get("agent_id", "")).strip() or None
    kb_documents = build_kb_documents(args.kb_document_id, args.kb_document_name)
    prompt_override = read_text(agent_prompt_path) if agent_prompt_path else None
    first_message_override = read_text(first_message_path) if first_message_path else None
    dynamic_variable_placeholders = read_json(dynamic_defaults_path) if dynamic_defaults_path else None
    agent_patch_out = resolve_project_path(args.agent_patch_out)
    plan = build_plan(
        package_manifest_path=manifest_path,
        agent_id=args.agent_id,
        agent_name=args.agent_name,
        agent_config_path=agent_config_path,
        kb_documents=kb_documents,
        agent_patch_out=agent_patch_out,
        prompt_override=prompt_override,
        first_message_override=first_message_override,
        dynamic_variable_placeholders=dynamic_variable_placeholders,
    )
    requests_bundle = build_api_requests_bundle(plan)
    plan["test_folder"] = {
        "folder_name": args.test_folder_name,
        "folder_id": args.test_folder_id,
        "parent_folder_id": args.test_folder_parent_id,
        "applies_to_live_created_tests": bool(args.test_folder_name or args.test_folder_id),
    }
    live_result = perform_live_operation(args, plan)
    if live_result["live_provider_calls_made"]:
        plan["mode"] = "live"
        requests_bundle["mode"] = "live"
        requests_bundle["live_provider_calls_made"] = True
    plan["live_result"] = live_result
    out = resolve_project_path(args.out)
    api_requests_out = resolve_project_path(args.api_requests_out)
    write_json(out, plan)
    write_json(api_requests_out, requests_bundle)
    print(
        json.dumps(
            {
                "checkpoint_id": CHECKPOINT_ID,
                "mode": plan["mode"],
                "plan": rel_path(out),
                "api_requests": rel_path(api_requests_out),
                "live_provider_calls_made": live_result["live_provider_calls_made"],
                "knowledge_base_upload_count": len(plan["knowledge_base_upload_requests"]),
                "test_create_request_count": len(plan["test_create_requests"]),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main(sys.argv[1:])
