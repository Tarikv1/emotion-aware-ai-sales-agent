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
    "test_id",
    "test_run_id",
    "run_id",
    "agent_id",
    "name",
    "status",
    "status_code",
)


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


def _chat_history(customer_utterance: str) -> list[dict[str, Any]]:
    return [
        {
            "role": "user",
            "message": customer_utterance,
            "time_in_call_secs": 1,
        }
    ]


def _success_condition(item: dict[str, Any]) -> str:
    return (
        "Return True only if the agent response follows this expected behavior: "
        f"{item['expected_behavior']} Return False if it does this forbidden behavior: "
        f"{item['forbidden_behavior']}"
    )


def test_create_request(item: dict[str, Any], *, package_id: str) -> dict[str, Any]:
    test_id = str(item["test_id"])
    body = {
        "type": "llm",
        "name": f"{package_id}::{test_id}",
        "chat_history": _chat_history(str(item["customer_utterance"])),
        "success_condition": _success_condition(item),
        "success_examples": [
            {
                "type": "agent_response",
                "response": str(item["expected_behavior"]),
            }
        ],
        "failure_examples": [
            {
                "type": "agent_response",
                "response": str(item["forbidden_behavior"]),
            }
        ],
        "dynamic_variables": {
            "campaign_name": "universal-sales-core-validation",
            "source_package_id": package_id,
        },
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
    return [test_create_request(dict(item), package_id=package_id) for item in tests]


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
    existing_kb = prompt.get("knowledge_base", [])
    if not isinstance(existing_kb, list):
        raise ValueError("Copied agent config prompt.knowledge_base must be a list.")
    prompt["knowledge_base"] = merge_knowledge_base_entries(existing_kb, kb_documents)
    rag = prompt.setdefault("rag", {})
    if not isinstance(rag, dict):
        raise ValueError("Copied agent config prompt.rag must be an object.")
    rag["enabled"] = True
    return {
        "name": str(agent_config.get("name") or "web design"),
        "conversation_config": conversation_config,
        "workflow": copy.deepcopy(agent_config.get("workflow", {})),
        "tags": copy.deepcopy(agent_config.get("tags", [])),
        "version_description": (
            f"ELEVENLABS-003 attach {len(kb_documents)} repo-owned knowledge base document(s)"
        ),
    }


def build_agent_patch_draft(
    agent_id: str | None,
    *,
    agent_config_path: Path | None = None,
    kb_documents: list[dict[str, str]] | None = None,
    patch_payload_out: Path | None = None,
) -> dict[str, Any]:
    endpoint_agent = agent_id or "{agent_id}"
    if agent_config_path and kb_documents:
        agent_config = read_json(agent_config_path)
        copied_agent_id = str(agent_config.get("agent_id", "")).strip()
        if not copied_agent_id:
            raise ValueError("Copied agent config is missing agent_id.")
        if agent_id and agent_id != copied_agent_id:
            raise ValueError(f"--agent-id {agent_id} does not match copied config agent_id {copied_agent_id}.")
        patch_payload = build_agent_patch_payload(agent_config, kb_documents)
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
        ),
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
    parser.add_argument("--kb-document-id", action="append", default=[])
    parser.add_argument("--kb-document-name", action="append", default=[])
    parser.add_argument(
        "--operation",
        choices=("plan", "upload-kb", "create-tests", "run-tests", "patch-agent", "all"),
        default="plan",
    )
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--confirm-provider-write", action="store_true")
    parser.add_argument("--created-test-ids", nargs="*", default=[])
    parser.add_argument("--repeat-count", type=int, default=1)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    manifest_path = resolve_project_path(args.package_manifest)
    agent_config_path = resolve_project_path(args.agent_config) if args.agent_config else None
    if agent_config_path and not args.agent_id:
        copied_config = read_json(agent_config_path)
        args.agent_id = str(copied_config.get("agent_id", "")).strip() or None
    kb_documents = build_kb_documents(args.kb_document_id, args.kb_document_name)
    agent_patch_out = resolve_project_path(args.agent_patch_out)
    plan = build_plan(
        package_manifest_path=manifest_path,
        agent_id=args.agent_id,
        agent_name=args.agent_name,
        agent_config_path=agent_config_path,
        kb_documents=kb_documents,
        agent_patch_out=agent_patch_out,
    )
    requests_bundle = build_api_requests_bundle(plan)
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
