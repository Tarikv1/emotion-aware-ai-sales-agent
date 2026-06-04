#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "ELEVENLABS-003-agent-config-patcher"
RUNNER = ROOT / "scripts" / "run_elevenlabs_agent_automation.py"
FIXTURE = (
    ROOT
    / "runtime"
    / "providers"
    / "elevenlabs_agents"
    / "fixtures"
    / "web_design_agent_config.sanitized.json"
)
OUT_DIR = ROOT / ".tmp" / CHECKPOINT_ID / "validation"
PLAN = OUT_DIR / "automation_plan.json"
REQUESTS = OUT_DIR / "api_requests.json"
PATCH = OUT_DIR / "agent_patch_payload.json"


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


def assert_no_private_or_response_only_leak(payload: dict[str, Any]) -> None:
    serialized = json.dumps(payload, ensure_ascii=False).lower()
    blocked = (
        "kizilderetarik5@gmail.com",
        "creator_email",
        "creator_name",
        "access_info",
        "phone_numbers",
        "whatsapp_accounts",
        "shareable_token",
        "xi-api-key",
        "api key value",
        "data/private/",
        "data/private-restricted/"
    )
    found = [marker for marker in blocked if marker in serialized]
    assert_condition(not found, f"Patch output contains blocked marker(s): {found}")


def main() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            str(RUNNER),
            "--agent-config",
            str(FIXTURE),
            "--kb-document-id",
            "kbdoc_validation_universal_sales_core",
            "--kb-document-name",
            "universal_sales_core.md",
            "--out",
            str(PLAN),
            "--api-requests-out",
            str(REQUESTS),
            "--agent-patch-out",
            str(PATCH),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert_condition(completed.returncode == 0, completed.stderr or completed.stdout)
    plan = read_json(PLAN)
    requests = read_json(REQUESTS)
    patch = read_json(PATCH)
    assert_no_private_or_response_only_leak(plan)
    assert_no_private_or_response_only_leak(requests)
    assert_no_private_or_response_only_leak(patch)

    assert_condition(plan.get("agent_config_patch", {}).get("status") == "ready_for_review", "patch status mismatch")
    assert_condition(plan["agent_config_patch"].get("source_config_path", "").endswith("web_design_agent_config.sanitized.json"), "source config path missing")
    assert_condition(plan["agent_config_patch"].get("patch_payload_path", "").endswith("agent_patch_payload.json"), "patch payload path missing")

    prompt = patch["conversation_config"]["agent"]["prompt"]
    kb_entries = prompt["knowledge_base"]
    assert_condition(
        kb_entries == [
            {
                "type": "file",
                "name": "universal_sales_core.md",
                "id": "kbdoc_validation_universal_sales_core",
            }
        ],
        f"knowledge_base entry mismatch: {kb_entries}",
    )
    assert_condition(prompt["rag"]["enabled"] is True, "RAG should be enabled after KB attach")
    assert_condition(prompt["rag"]["embedding_model"] == "e5_mistral_7b_instruct", "embedding model changed unexpectedly")
    assert_condition(
        patch["conversation_config"]["agent"]["first_message"] == "Hello! How can I help you today?",
        "first message should be preserved by KB-only patch",
    )
    assert_condition(
        prompt["prompt"] == "You are a helpful assistant.",
        "system prompt should be preserved by KB-only patch",
    )
    assert_condition(patch["name"] == "web design", "agent name should be preserved")
    assert_condition(
        patch["version_description"].startswith("ELEVENLABS-003"),
        "version description should identify patch checkpoint",
    )

    patch_requests = [item for item in requests["requests"] if item["request_id"] == "patch_agent::{agent_id}"]
    assert_condition(len(patch_requests) == 1, "api_requests should include one patch_agent request")
    assert_condition(
        patch_requests[0]["url"].endswith("/v1/convai/agents/agent_7801kt0g32zxf4f8x5zkykj7syty"),
        "patch request URL should target copied agent ID",
    )

    print(
        json.dumps(
            {
                "status": "pass",
                "checkpoint_id": CHECKPOINT_ID,
                "patch_payload": str(PATCH.relative_to(ROOT)),
                "kb_document_id": "kbdoc_validation_universal_sales_core",
                "rag_enabled": True,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
