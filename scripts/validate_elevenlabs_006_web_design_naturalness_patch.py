#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "ELEVENLABS-006-web-design-naturalness-patch"
RUNNER = ROOT / "scripts" / "run_elevenlabs_agent_automation.py"
FIXTURE = (
    ROOT
    / "runtime"
    / "providers"
    / "elevenlabs_agents"
    / "fixtures"
    / "web_design_agent_config.sanitized.json"
)
PROMPT = ROOT / "runtime" / "providers" / "elevenlabs_agents" / "prompts" / "web_design_atlas_sales_prompt.md"
FIRST_MESSAGE = ROOT / "runtime" / "providers" / "elevenlabs_agents" / "prompts" / "web_design_first_message.txt"
DEFAULTS = (
    ROOT
    / "runtime"
    / "providers"
    / "elevenlabs_agents"
    / "variables"
    / "mikes_kitchen_dynamic_variable_defaults.json"
)
DOC = ROOT / "docs" / "product" / "ELEVENLABS_006_WEB_DESIGN_NATURALNESS_PATCH.md"
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
        "data/private-restricted/",
        "private transcript",
    )
    found = [marker for marker in blocked if marker in serialized]
    assert_condition(not found, f"Patch output contains blocked marker(s): {found}")


def main() -> None:
    for path in (RUNNER, FIXTURE, PROMPT, FIRST_MESSAGE, DEFAULTS, DOC):
        assert_condition(path.is_file(), f"Missing file: {path.relative_to(ROOT)}")

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
            "--agent-prompt-file",
            str(PROMPT),
            "--first-message-file",
            str(FIRST_MESSAGE),
            "--dynamic-variable-defaults",
            str(DEFAULTS),
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
    assert_condition(plan["agent_config_patch"].get("prompt_override_applied") is True, "prompt override missing")
    assert_condition(plan["agent_config_patch"].get("first_message_override_applied") is True, "first message override missing")
    assert_condition(plan["agent_config_patch"].get("dynamic_variable_placeholders_applied") is True, "dynamic defaults override missing")

    prompt = patch["conversation_config"]["agent"]["prompt"]["prompt"]
    first_message = patch["conversation_config"]["agent"]["first_message"]
    placeholders = patch["conversation_config"]["agent"]["dynamic_variables"]["dynamic_variable_placeholders"]

    for required in (
        "You are Emma from Atlas Web Studio.",
        "visual representation",
        "Do not say `customer action path` to the buyer.",
        "Do not say `reservation-call path`",
        "Normal-words ask: ask the buyer to take a quick look",
        "Usable callback window: confirm the callback and the narrow purpose.",
        "Do not promise more calls, bookings, ranking, revenue, or customer behavior.",
    ):
        assert_condition(required in prompt, f"prompt missing required marker: {required}")
    assert_condition("You are a helpful assistant." not in prompt, "old generic prompt survived")
    assert_condition(first_message.startswith("Hi, this is Emma from Atlas Web Studio."), "first message mismatch")
    assert_condition("customer action path" not in first_message, "first message should avoid abstract jargon")
    assert_condition(placeholders.get("business_name") == "Mike's Kitchen", "business_name placeholder mismatch")
    assert_condition(placeholders.get("known_social_presence") == "Instagram and Google Maps", "social placeholder mismatch")
    assert_condition("customer action path" not in placeholders.get("call_reason", ""), "call_reason should be concrete")
    assert_condition(patch["conversation_config"]["agent"]["prompt"]["rag"]["enabled"] is True, "RAG should remain enabled")
    assert_condition(
        patch["version_description"].startswith("ELEVENLABS-006 web design prompt naturalness patch;"),
        "version description should identify the naturalness patch",
    )
    assert_condition(
        patch["conversation_config"]["agent"]["prompt"]["knowledge_base"][0]["id"] == "kbdoc_validation_universal_sales_core",
        "KB document ID mismatch",
    )

    doc_text = DOC.read_text(encoding="utf-8")
    for marker in (
        CHECKPOINT_ID,
        "The live ElevenLabs agent prompt had drifted to `You are a helpful assistant.`",
        "No new KB document is uploaded.",
    ):
        assert_condition(marker in doc_text, f"Doc missing marker: {marker}")

    print(
        json.dumps(
            {
                "status": "pass",
                "checkpoint_id": CHECKPOINT_ID,
                "prompt_chars": len(prompt),
                "first_message_chars": len(first_message),
                "rag_enabled": True,
                "live_provider_calls_made": False,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
