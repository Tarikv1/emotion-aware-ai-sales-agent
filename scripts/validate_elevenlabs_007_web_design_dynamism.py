#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "ELEVENLABS-007-web-design-dynamism-naturalness"
PACKAGE_ID = "ELEVENLABS-007-mikes-kitchen-naturalness-tests"
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
MANIFEST = (
    ROOT
    / "runtime"
    / "providers"
    / "elevenlabs_agents"
    / "manifests"
    / "web_design_mikes_kitchen_naturalness_tests.package.json"
)
TESTS = (
    ROOT
    / "runtime"
    / "providers"
    / "elevenlabs_agents"
    / "tests"
    / "web_design_mikes_kitchen_naturalness_tests.json"
)
DOC = ROOT / "docs" / "product" / "ELEVENLABS_007_WEB_DESIGN_DYNAMISM_NATURALNESS.md"
LIVE_RESULT_SUMMARY = (
    ROOT
    / "research"
    / "experiments"
    / "generated"
    / CHECKPOINT_ID
    / "sales_intent_naturalness_results_summary.json"
)
OUT_DIR = ROOT / ".tmp" / CHECKPOINT_ID / "validation"
PLAN = OUT_DIR / "automation_plan.json"
REQUESTS = OUT_DIR / "api_requests.json"
PATCH = OUT_DIR / "agent_patch_payload.json"
TARGET_TEMPERATURE = 0.25
TARGET_TEST_FOLDER = "Atlas Web Studio - Naturalness Sales Intent Repair"


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
    assert_condition(not found, f"Output contains blocked marker(s): {found}")


def main() -> None:
    for path in (RUNNER, FIXTURE, PROMPT, FIRST_MESSAGE, DEFAULTS, MANIFEST, TESTS, DOC, LIVE_RESULT_SUMMARY):
        assert_condition(path.is_file(), f"Missing file: {path.relative_to(ROOT)}")

    prompt_text = PROMPT.read_text(encoding="utf-8")
    for marker in (
        "## Highest Priority Last-Turn Rules",
        "## Opening And Sales Intent",
        "The goal is to sell the next valid step",
        "I know this is out of the blue",
        "If the buyer already gave a callback window, confirm and stop.",
        "If the buyer says `tomorrow morning`, say you will call tomorrow morning.",
        "Preserve the time before preserving extra offer details.",
        "If the buyer asks what the mockup would show",
        "Do not list menu, hours, location, and reservation calls in every answer.",
        "Do not copy example sentences verbatim.",
        "Do not start several turns in a row with the same word",
        "Do not invent price, timeline, portfolio, SEO, ranking, reservation, revenue, or traffic claims.",
        "Callback confirmation overrides the one-question rule.",
        "A broad window such as `tomorrow morning`",
        "After a usable callback window, do not ask `What time works best?`",
        "After a usable callback window, the whole response should be a statement, not a question.",
        "Callback confirmations should include the narrow purpose: reviewing the free mockup.",
        "If your draft callback confirmation contains a question mark, remove the question.",
        "If a callback time is already known and the buyer asks for a pass-along note",
    ):
        assert_condition(marker in prompt_text, f"Prompt missing marker: {marker}")

    first_message = FIRST_MESSAGE.read_text(encoding="utf-8").strip()
    assert_condition(first_message.startswith("Hi, this is Emma from Atlas Web Studio."), "first message mismatch")
    assert_condition("I know this is out of the blue" in first_message, "first message should use the out-of-the-blue opener")
    assert_condition("I know this is a cold call" not in first_message, "first message should avoid the old cold-call opener")
    assert_condition("I could not find a full website" in first_message, "first message should state the reason early")
    assert_condition("customer action path" not in first_message, "first message should avoid abstract jargon")

    tests_payload = read_json(TESTS)
    assert_condition(tests_payload.get("package_id") == PACKAGE_ID, "test package_id mismatch")
    tests = tests_payload.get("tests")
    assert_condition(isinstance(tests, list) and len(tests) == 8, "expected exactly eight naturalness tests")
    banned_in_expected = (
        "customer action path",
        "online presence",
        "visual representation",
        "potential improvement",
        "enhance",
        "optimize",
        "digital solution",
    )
    seen_ids: set[str] = set()
    for item in tests:
        assert_condition(isinstance(item, dict), "test item must be an object")
        test_id = str(item.get("test_id", ""))
        assert_condition(test_id.startswith("natural_"), f"test_id should be natural_*: {test_id}")
        assert_condition(test_id not in seen_ids, f"duplicate test_id: {test_id}")
        seen_ids.add(test_id)
        history = item.get("chat_history")
        assert_condition(isinstance(history, list), f"{test_id} chat_history missing")
        assert_condition(8 <= len(history) <= 10, f"{test_id} should have 8-10 chat turns")
        assert_condition(history[-1].get("role") == "user", f"{test_id} must end with a user turn")
        history_text = json.dumps(history, ensure_ascii=False)
        assert_condition("I know this is a cold call" not in history_text, f"{test_id} uses stale cold-call opener")
        assert_condition("Fair question" not in history_text, f"{test_id} prior chat uses stale Fair question wording")
        assert_condition(
            "I should not make it sound hidden" not in history_text,
            f"{test_id} prior chat leaks internal pricing policy wording",
        )
        expected = str(item.get("expected_behavior", "")).lower()
        forbidden = str(item.get("forbidden_behavior", "")).lower()
        assert_condition("natural" in expected or "human" in expected, f"{test_id} expected behavior must score naturalness")
        assert_condition("do not" in forbidden, f"{test_id} forbidden behavior must include explicit rejections")
        for marker in banned_in_expected:
            assert_condition(marker not in expected, f"{test_id} expected behavior uses banned marker: {marker}")

    manifest = read_json(MANIFEST)
    assert_condition(manifest.get("package_id") == PACKAGE_ID, "manifest package_id mismatch")
    assert_condition(manifest.get("baseline_tests") == [str(TESTS.relative_to(ROOT)).replace("\\", "/")], "manifest tests mismatch")
    assert_condition(
        manifest.get("upload_intent", {}).get("target_test_folder_name") == TARGET_TEST_FOLDER,
        "target folder mismatch",
    )

    live_result = read_json(LIVE_RESULT_SUMMARY)
    assert_no_private_or_response_only_leak(live_result)
    assert_condition(live_result.get("suite_id") == "suite_3401ktc4ycc1eh0takb8tzr4ecm9", "live suite id mismatch")
    assert_condition(live_result.get("knowledge_base_document_id") == "IkaG5meLwWNWA53Z5jIM", "live KB document id mismatch")
    assert_condition(live_result.get("test_folder_id") == "tfld_1701ktc4prt0eq5szy820dh713cc", "live test folder id mismatch")
    assert_condition(live_result.get("passed_count") == 8, "live passed count mismatch")
    assert_condition(live_result.get("failed_count") == 0, "live failed count mismatch")
    assert_condition(live_result.get("pending_count") == 0, "live pending count mismatch")

    completed = subprocess.run(
        [
            sys.executable,
            str(RUNNER),
            "--package-manifest",
            str(MANIFEST),
            "--agent-id",
            "agent_7801kt0g32zxf4f8x5zkykj7syty",
            "--test-folder-name",
            TARGET_TEST_FOLDER,
            "--out",
            str(PLAN),
            "--api-requests-out",
            str(REQUESTS),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert_condition(completed.returncode == 0, completed.stderr or completed.stdout)
    plan = read_json(PLAN)
    requests = read_json(REQUESTS)
    assert_no_private_or_response_only_leak(plan)
    assert_no_private_or_response_only_leak(requests)
    assert_condition(len(plan.get("test_create_requests", [])) == 8, "plan test count mismatch")
    assert_condition(plan.get("test_folder", {}).get("folder_name") == TARGET_TEST_FOLDER, "plan folder mismatch")

    completed_patch = subprocess.run(
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
            "--agent-temperature",
            str(TARGET_TEMPERATURE),
            "--out",
            str(OUT_DIR / "patch_plan.json"),
            "--api-requests-out",
            str(OUT_DIR / "patch_api_requests.json"),
            "--agent-patch-out",
            str(PATCH),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert_condition(completed_patch.returncode == 0, completed_patch.stderr or completed_patch.stdout)
    patch = read_json(PATCH)
    assert_no_private_or_response_only_leak(patch)
    patch_prompt = patch["conversation_config"]["agent"]["prompt"]
    assert_condition(patch_prompt["temperature"] == TARGET_TEMPERATURE, "agent temperature override missing")
    assert_condition(
        patch["version_description"].startswith("ELEVENLABS-007 web design dynamism patch;"),
        "version description should identify ELEVENLABS-007",
    )
    assert_condition(patch_prompt["rag"]["enabled"] is True, "RAG should remain enabled")

    doc_text = DOC.read_text(encoding="utf-8")
    for marker in (
        CHECKPOINT_ID,
        "Passing the previous tests did not prove naturalness.",
        "temperature `0.25`",
    ):
        assert_condition(marker in doc_text, f"Doc missing marker: {marker}")

    print(
        json.dumps(
            {
                "status": "pass",
                "checkpoint_id": CHECKPOINT_ID,
                "naturalness_test_count": len(tests),
                "agent_temperature": TARGET_TEMPERATURE,
                "live_provider_calls_made": False,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
