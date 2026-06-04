#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "ELEVENLABS-002-agent-automation"
RUNNER = ROOT / "scripts" / "run_elevenlabs_agent_automation.py"
MODULE = ROOT / "runtime" / "providers" / "elevenlabs_agents" / "automation.py"
DOC = ROOT / "docs" / "product" / "ELEVENLABS_002_AGENT_AUTOMATION.md"
OUT_DIR = ROOT / ".tmp" / CHECKPOINT_ID / "validation"
PLAN = OUT_DIR / "automation_plan.json"
API_REQUESTS = OUT_DIR / "api_requests.json"


def fail(message: str) -> None:
    raise AssertionError(message)


def assert_condition(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        fail(f"Missing JSON file: {path.relative_to(ROOT)}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        fail(f"{path.relative_to(ROOT)} must contain a JSON object.")
    return payload


def assert_no_secret_leak(payload: dict[str, Any]) -> None:
    serialized = json.dumps(payload, ensure_ascii=False).lower()
    blocked = (
        "xi-api-key:",
        "sk_",
        "api key value",
        "data/private/",
        "data/private-restricted/",
        "raw customer email",
        "private transcript",
        "creator_email",
        "creator_name",
        "access_info",
        "phone_numbers",
        "whatsapp_accounts",
        "shareable_token",
    )
    found = [item for item in blocked if item in serialized]
    assert_condition(not found, f"Automation output contains blocked marker(s): {found}")


def main() -> None:
    assert_condition(MODULE.is_file(), "Automation module is missing.")
    assert_condition(RUNNER.is_file(), "Automation runner is missing.")
    assert_condition(DOC.is_file(), "ELEVENLABS-002 doc is missing.")
    module_text = MODULE.read_text(encoding="utf-8")
    assert_condition('"response_summary": summarize_provider_response' in module_text, "live responses must be summarized")
    assert_condition('"response": result["response"]' not in module_text, "raw live provider responses must not be persisted")

    completed = subprocess.run(
        [
            sys.executable,
            str(RUNNER),
            "--agent-id",
            "agent_validation_fixture",
            "--out",
            str(PLAN),
            "--api-requests-out",
            str(API_REQUESTS),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert_condition(completed.returncode == 0, completed.stderr or completed.stdout)

    plan = read_json(PLAN)
    requests = read_json(API_REQUESTS)
    assert_no_secret_leak(plan)
    assert_no_secret_leak(requests)

    assert_condition(plan.get("checkpoint_id") == CHECKPOINT_ID, "checkpoint_id mismatch")
    assert_condition(plan.get("provider") == "elevenlabs", "provider mismatch")
    assert_condition(plan.get("mode") == "dry_run", "default mode must be dry_run")
    assert_condition(plan.get("live_provider_calls_made") is False, "dry run must not call provider")
    assert_condition(plan.get("api_key_env_var") == "ELEVENLABS_API_KEY", "API key env marker missing")
    assert_condition(plan.get("agent_id") == "agent_validation_fixture", "agent_id should carry through")

    kb_requests = plan.get("knowledge_base_upload_requests")
    assert_condition(isinstance(kb_requests, list) and kb_requests, "KB upload requests missing")
    kb_request = kb_requests[0]
    assert_condition(
        kb_request.get("method") == "POST"
        and kb_request.get("endpoint") == "/v1/convai/knowledge-base/file",
        "KB upload request endpoint mismatch",
    )
    assert_condition(kb_request.get("source_path", "").endswith("universal_sales_core.md"), "KB path missing")
    assert_condition(kb_request.get("content_bytes", 0) > 1000, "KB content size looks too small")

    test_requests = plan.get("test_create_requests")
    assert_condition(isinstance(test_requests, list) and len(test_requests) >= 10, "test create requests missing")
    first_test = test_requests[0]
    assert_condition(
        first_test.get("method") == "POST"
        and first_test.get("endpoint") == "/v1/convai/agent-testing/create",
        "test create request endpoint mismatch",
    )
    body = first_test.get("body", {})
    assert_condition(body.get("type") == "llm", "test create body must use llm type")
    assert_condition(isinstance(body.get("chat_history"), list) and body["chat_history"], "chat history missing")
    assert_condition("success_condition" in body, "success condition missing")
    assert_condition(body.get("success_examples"), "success examples missing")
    assert_condition(body.get("failure_examples"), "failure examples missing")

    run_tests = plan.get("run_tests_request", {})
    assert_condition(
        run_tests.get("endpoint") == "/v1/convai/agents/agent_validation_fixture/run-tests",
        "run-tests request endpoint mismatch",
    )
    assert_condition(run_tests.get("requires_created_test_ids") is True, "run-tests must wait for created test IDs")

    assert_condition(
        len(requests.get("requests", [])) == len(test_requests) + len(kb_requests) + 1,
        "api_requests request count mismatch",
    )

    doc_text = DOC.read_text(encoding="utf-8")
    for marker in (
        CHECKPOINT_ID,
        "Default mode is dry-run.",
        "Live provider writes require `--live` and `--confirm-provider-write`.",
        "This checkpoint does not attach KB documents to an agent automatically.",
    ):
        assert_condition(marker in doc_text, f"Doc missing marker: {marker}")

    print(
        json.dumps(
            {
                "status": "pass",
                "checkpoint_id": CHECKPOINT_ID,
                "plan": str(PLAN.relative_to(ROOT)),
                "api_requests": str(API_REQUESTS.relative_to(ROOT)),
                "live_provider_calls_made": False,
                "test_create_request_count": len(test_requests),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
