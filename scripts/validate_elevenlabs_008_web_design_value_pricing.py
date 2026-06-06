#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "ELEVENLABS-008-web-design-value-pricing-repair"
PACKAGE_ID = "ELEVENLABS-008-mikes-kitchen-value-pricing-tests"
RUNNER = ROOT / "scripts" / "run_elevenlabs_agent_automation.py"
FIXTURE = (
    ROOT
    / "runtime"
    / "providers"
    / "elevenlabs_agents"
    / "fixtures"
    / "web_design_agent_config.sanitized.json"
)
KB = ROOT / "runtime" / "providers" / "elevenlabs_agents" / "knowledge_base" / "universal_sales_core.md"
CAMPAIGN_KB = (
    ROOT
    / "runtime"
    / "providers"
    / "elevenlabs_agents"
    / "knowledge_base"
    / "atlas_web_studio_web_design_campaign.md"
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
    / "web_design_mikes_kitchen_value_pricing_tests.package.json"
)
TESTS = (
    ROOT
    / "runtime"
    / "providers"
    / "elevenlabs_agents"
    / "tests"
    / "web_design_mikes_kitchen_value_pricing_tests.json"
)
DOC = ROOT / "docs" / "product" / "ELEVENLABS_008_WEB_DESIGN_VALUE_PRICING_REPAIR.md"
LIVE_RESULT_SUMMARY = (
    ROOT
    / "research"
    / "experiments"
    / "generated"
    / CHECKPOINT_ID
    / "value_pricing_results_summary.json"
)
OUT_DIR = ROOT / ".tmp" / CHECKPOINT_ID / "validation"
PLAN = OUT_DIR / "automation_plan.json"
REQUESTS = OUT_DIR / "api_requests.json"
PATCH = OUT_DIR / "agent_patch_payload.json"
TARGET_TEMPERATURE = 0.25
PATCH_SCOPE = "ELEVENLABS-008 web design value pricing repair"


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
    for path in (RUNNER, FIXTURE, KB, CAMPAIGN_KB, PROMPT, FIRST_MESSAGE, DEFAULTS, MANIFEST, TESTS, DOC, LIVE_RESULT_SUMMARY):
        assert_condition(path.is_file(), f"Missing file: {path.relative_to(ROOT)}")

    kb_text = KB.read_text(encoding="utf-8")
    for marker in (
        "disclose the approved anchor instead of dodging",
        "translate features into the buyer's practical outcome",
        "use the campaign knowledge base for the actual selling points",
        "Universal sales advice must stay subordinate to campaign facts.",
    ):
        assert_condition(marker in kb_text, f"Universal sales core missing marker: {marker}")

    campaign_kb_text = CAMPAIGN_KB.read_text(encoding="utf-8")
    for marker in (
        "website-specific facts and",
        "selling points for local restaurant outreach",
        "for practical customer decisions",
        "Simple website projects generally start around `$1,000`.",
    ):
        assert_condition(marker in campaign_kb_text, f"Campaign KB missing marker: {marker}")

    prompt_text = PROMPT.read_text(encoding="utf-8")
    for marker in (
        "Never speak your private reasoning",
        "If the buyer says they do not want surprise pricing",
        "Simple website projects generally start around `{{website_starting_price}}`.",
        "A more custom premium or 3D immersive site can go up to around `{{website_premium_price_anchor}}`",
        "Apps/order systems concern",
        "Skepticism about free: if it is a statement",
        "Do not leak internal self-correction.",
    ):
        assert_condition(marker in prompt_text, f"Prompt missing marker: {marker}")

    defaults = read_json(DEFAULTS)
    assert_condition(defaults.get("website_starting_price") == "$1,000", "starting price default mismatch")
    assert_condition(defaults.get("website_premium_price_anchor") == "$5,000", "premium anchor default mismatch")
    assert_condition("phone-only reservations" in defaults.get("approved_value_points", ""), "value point missing")

    tests_payload = read_json(TESTS)
    assert_condition(tests_payload.get("package_id") == PACKAGE_ID, "test package_id mismatch")
    tests = tests_payload.get("tests")
    assert_condition(isinstance(tests, list) and len(tests) == 6, "expected six value/pricing tests")
    expected_ids = {
        "value_pricing_direct_starting_price",
        "value_pricing_higher_scope_range",
        "value_statement_not_fair_question",
        "value_staff_after_three_callback_only",
        "value_phone_reservation_single_value_point",
        "value_why_look_customer_confusion",
    }
    seen_ids: set[str] = set()
    blocked_prior_turn_markers = ("Fair question", "I should not make it sound hidden")
    for item in tests:
        assert_condition(isinstance(item, dict), "test item must be an object")
        test_id = str(item.get("test_id", ""))
        seen_ids.add(test_id)
        history = item.get("chat_history")
        assert_condition(isinstance(history, list), f"{test_id} chat_history missing")
        assert_condition(8 <= len(history) <= 10, f"{test_id} should have 8-10 chat turns")
        assert_condition(history[-1].get("role") == "user", f"{test_id} must end with a user turn")
        history_text = json.dumps(history)
        for marker in blocked_prior_turn_markers:
            assert_condition(marker not in history_text, f"{test_id} prior chat leaks blocked marker: {marker}")
        expected = str(item.get("expected_behavior", ""))
        forbidden = str(item.get("forbidden_behavior", ""))
        expected_lower = expected.lower()
        assert_condition(
            "$1,000" in expected
            or "$5,000" in expected
            or "value" in expected_lower
            or "callback" in expected_lower
            or "statement" in expected_lower
            or "phone number" in expected_lower,
            f"{test_id} expected behavior too generic",
        )
        assert_condition("Do not" in forbidden, f"{test_id} forbidden behavior must include explicit rejections")
    assert_condition(expected_ids == seen_ids, f"test ids mismatch: {sorted(seen_ids)}")

    manifest = read_json(MANIFEST)
    assert_condition(manifest.get("package_id") == PACKAGE_ID, "manifest package_id mismatch")
    assert_condition(manifest.get("baseline_tests") == [str(TESTS.relative_to(ROOT)).replace("\\", "/")], "manifest tests mismatch")
    assert_condition(
        manifest.get("upload_intent", {}).get("target_test_folder_name") == "Atlas Web Studio - Value Pricing Stress",
        "target folder mismatch",
    )

    live_result = read_json(LIVE_RESULT_SUMMARY)
    assert_no_private_or_response_only_leak(live_result)
    assert_condition(live_result.get("suite_id") == "suite_8301ktc5025rfd2v42k5frtdp269", "live suite id mismatch")
    assert_condition(live_result.get("knowledge_base_document_id") == "IkaG5meLwWNWA53Z5jIM", "live KB document id mismatch")
    assert_condition(live_result.get("test_folder_id") == "tfld_2301kta29zg4edxb33ja2bbqq1p6", "live test folder id mismatch")
    assert_condition(live_result.get("passed_count") == 6, "live passed count mismatch")
    assert_condition(live_result.get("failed_count") == 0, "live failed count mismatch")
    assert_condition(live_result.get("pending_count") == 0, "live pending count mismatch")
    assert_condition(live_result.get("secret_values_logged") is False, "live summary secret flag mismatch")
    assert_condition(live_result.get("raw_provider_response_committed") is False, "live summary raw response flag mismatch")

    completed = subprocess.run(
        [
            sys.executable,
            str(RUNNER),
            "--package-manifest",
            str(MANIFEST),
            "--agent-id",
            "agent_7801kt0g32zxf4f8x5zkykj7syty",
            "--test-folder-name",
            "Atlas Web Studio - Value Pricing Stress",
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
    assert_condition(len(plan.get("test_create_requests", [])) == 6, "plan test count mismatch")

    completed_patch = subprocess.run(
        [
            sys.executable,
            str(RUNNER),
            "--agent-config",
            str(FIXTURE),
            "--kb-document-id",
            "kbdoc_validation_universal_sales_core_v2",
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
            "--agent-patch-version-scope",
            PATCH_SCOPE,
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
    assert_condition(patch["version_description"].startswith(PATCH_SCOPE), "version scope override missing")
    assert_condition(patch_prompt["rag"]["enabled"] is True, "RAG should remain enabled")

    doc_text = DOC.read_text(encoding="utf-8")
    for marker in (
        CHECKPOINT_ID,
        "internal reasoning leak",
        "starting price",
        "Salesforce",
        "HubSpot",
        "Bain",
    ):
        assert_condition(marker in doc_text, f"Doc missing marker: {marker}")

    print(
        json.dumps(
            {
                "status": "pass",
                "checkpoint_id": CHECKPOINT_ID,
                "value_pricing_test_count": len(tests),
                "agent_temperature": TARGET_TEMPERATURE,
                "live_provider_calls_made": False,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
