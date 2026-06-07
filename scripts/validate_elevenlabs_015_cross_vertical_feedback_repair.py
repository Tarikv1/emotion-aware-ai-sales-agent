#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "ELEVENLABS-015-cross-vertical-feedback-repair"
RUNNER = ROOT / "scripts" / "run_elevenlabs_agent_automation.py"
MANIFEST = (
    ROOT
    / "runtime"
    / "providers"
    / "elevenlabs_agents"
    / "manifests"
    / "web_design_cross_vertical_feedback_repair.package.json"
)
FIXTURE = ROOT / "runtime" / "providers" / "elevenlabs_agents" / "fixtures" / "web_design_agent_config.sanitized.json"
UNIVERSAL_KB = ROOT / "runtime" / "providers" / "elevenlabs_agents" / "knowledge_base" / "universal_sales_core.md"
CAMPAIGN_OVERLAY = (
    ROOT / "runtime" / "providers" / "elevenlabs_agents" / "knowledge_base" / "atlas_web_studio_web_design_campaign_overlay.md"
)
CAMPAIGN_PROFILE = (
    ROOT / "runtime" / "providers" / "elevenlabs_agents" / "knowledge_base" / "atlas_web_studio_web_design_campaign_profile.md"
)
PROMPT = ROOT / "runtime" / "providers" / "elevenlabs_agents" / "prompts" / "web_design_atlas_sales_prompt.md"
FIRST_MESSAGE = ROOT / "runtime" / "providers" / "elevenlabs_agents" / "prompts" / "web_design_first_message.txt"
DYNAMIC_DEFAULTS = ROOT / "runtime" / "providers" / "elevenlabs_agents" / "variables" / "mikes_kitchen_dynamic_variable_defaults.json"
CROSS_VERTICAL_TESTS = (
    ROOT / "runtime" / "providers" / "elevenlabs_agents" / "tests" / "web_design_cross_vertical_local_business_simulation_tests.json"
)
CATEGORY_VALUE = ROOT / "runtime" / "sales_knowledge" / "universal_sales_rag" / "categories" / "07_value_and_roi_framing.md"
CATEGORY_NEXT_STEP = ROOT / "runtime" / "sales_knowledge" / "universal_sales_rag" / "categories" / "12_next_step_policy.md"
CATEGORY_ETHICS = ROOT / "runtime" / "sales_knowledge" / "universal_sales_rag" / "categories" / "16_ethical_persuasion_boundaries.md"
COMPILED = ROOT / "runtime" / "sales_knowledge" / "universal_sales_rag" / "compiled" / "universal_sales_core.md"
DOC = ROOT / "docs" / "product" / "ELEVENLABS_015_CROSS_VERTICAL_FEEDBACK_REPAIR.md"
INDEX = ROOT / "docs" / "product" / "CHECKPOINT_INDEX.md"
COMMANDS = ROOT / "docs" / "product" / "COMMANDS.md"
METHODOLOGY_LOG = ROOT / "docs" / "thesis" / "METHODOLOGY_LOG.md"

OUT_DIR = ROOT / ".tmp" / CHECKPOINT_ID / "validation"
PLAN = OUT_DIR / "agent_patch_plan.json"
REQUESTS = OUT_DIR / "agent_patch_requests.json"
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


def assert_text_markers(path: Path, markers: tuple[str, ...]) -> str:
    if not path.is_file():
        fail(f"Missing file: {path.relative_to(ROOT)}")
    text = path.read_text(encoding="utf-8")
    for marker in markers:
        assert_condition(marker in text, f"{path.relative_to(ROOT)} missing marker: {marker}")
    return text


def assert_no_secret_leak(payload: dict[str, Any]) -> None:
    serialized = json.dumps(payload, ensure_ascii=False).lower()
    blocked = (
        "xi-api-key",
        "api key value",
        "creator_email",
        "creator_name",
        "access_info",
        "phone_numbers",
        "whatsapp_accounts",
        "shareable_token",
        "data/private/",
        "data/private-restricted/",
        "private transcript",
        "sk-",
    )
    found = [marker for marker in blocked if marker in serialized]
    assert_condition(not found, f"Output contains blocked marker(s): {found}")


def main() -> None:
    for path in (
        RUNNER,
        FIXTURE,
        UNIVERSAL_KB,
        CAMPAIGN_OVERLAY,
        CAMPAIGN_PROFILE,
        PROMPT,
        FIRST_MESSAGE,
        DYNAMIC_DEFAULTS,
        CROSS_VERTICAL_TESTS,
        CATEGORY_VALUE,
        CATEGORY_NEXT_STEP,
        CATEGORY_ETHICS,
        COMPILED,
        MANIFEST,
        DOC,
    ):
        assert_condition(path.is_file(), f"Missing file: {path.relative_to(ROOT)}")

    manifest = read_json(MANIFEST)
    assert_condition(manifest.get("package_id") == CHECKPOINT_ID, "manifest package_id mismatch")
    assert_condition(manifest.get("status") == "offline-repair-ready", "manifest status mismatch")
    assert_condition(manifest.get("live_provider_calls_made") is False, "manifest must stay offline by default")
    assert_condition(
        manifest.get("repair_basis", {}).get("human_feedback_categories")
        == [
            "cross_vertical_service_menu_evaluator_repair",
            "local_business_website_value_library",
            "safe_local_visibility_language",
            "name_capture_when_natural",
            "contractions_and_short_guarantee_language",
            "callback_number_gap_boundary",
            "ethical_persuasion_conversation_control",
        ],
        "human feedback categories mismatch",
    )

    prompt_text = assert_text_markers(
        PROMPT,
        (
            "## Cross-Vertical Local-Business Feedback Repair",
            "service menu or pricing menu is allowed",
            "food menu, reservations, tables, or food ordering",
            "local visibility can be a valid value angle",
            "Do not promise first-page ranking, SEO results, traffic, bookings, or more customers.",
            "ask `Who am I speaking with?` once when it is natural",
            "Use common contractions in spoken replies",
            "`I can't promise that.`",
            "Do not repeat `ignore it` as the default risk reversal.",
            "If asked for a callback number and no approved callback number is configured",
            "ethical persuasion, not manipulation",
            "answer, bridge, and guide",
        ),
    )
    assert_condition("ethical manipulation" not in prompt_text.lower(), "prompt must not frame persuasion as manipulation")

    assert_text_markers(
        CAMPAIGN_OVERLAY,
        (
            "## Cross-Vertical Local-Business Feedback Repair Overlay",
            "local visibility can be a value angle",
            "owned, indexable page",
            "service menu or pricing menu is allowed outside restaurant context",
            "ask for the buyer's name when it is natural",
            "Do not invent a callback number.",
            "conversation control means answer, bridge, and guide",
        ),
    )
    assert_text_markers(
        CAMPAIGN_PROFILE,
        (
            "## Approved Local-Business Website Value Facts",
            "A website can support local visibility",
            "No ranking, traffic, lead, booking, revenue, or customer-growth guarantee is approved.",
            "Service menus and pricing menus are allowed for non-restaurant verticals when the business context supports them.",
            "No approved callback phone number is configured in this package.",
        ),
    )
    assert_text_markers(
        CATEGORY_VALUE,
        (
            "steer from the buyer's concern to a different supported value angle",
            "Value is not only a feature list",
        ),
    )
    assert_text_markers(
        CATEGORY_NEXT_STEP,
        (
            "Conversation control means answer, bridge, and guide",
            "name capture",
        ),
    )
    assert_text_markers(
        CATEGORY_ETHICS,
        (
            "Ethical persuasion is not manipulation",
            "steer the conversation by relevance",
        ),
    )
    compiled_text = assert_text_markers(
        COMPILED,
        (
            "Ethical persuasion is not manipulation",
            "Conversation control means answer, bridge, and guide",
            "steer from the buyer's concern to a different supported value angle",
        ),
    )
    assert_condition(UNIVERSAL_KB.read_text(encoding="utf-8") == compiled_text, "provider universal KB must match compiled universal KB")

    tests = read_json(CROSS_VERTICAL_TESTS)
    serialized_tests = json.dumps(tests, ensure_ascii=False)
    assert_condition("service menu or pricing menu is acceptable" in serialized_tests, "test pack must allow salon service menu context")
    assert_condition("food menu, reservations, tables, food ordering" in serialized_tests, "test pack must narrow restaurant leakage wording")
    assert_condition("Mike-related language unless Mike appears in buyer-provided contact details" in serialized_tests, "test pack must not falsely fail buyer-provided Mike email")
    assert_condition("restaurant leakage such as menu" not in serialized_tests, "old overbroad menu leakage wording remains")

    assert_text_markers(
        DOC,
        (
            CHECKPOINT_ID,
            "safe local visibility",
            "service menu evaluator repair",
            "name capture",
            "contractions",
            "callback number gap",
            "ethical persuasion, not manipulation",
            "python scripts\\validate_elevenlabs_015_cross_vertical_feedback_repair.py",
        ),
    )
    assert_text_markers(
        INDEX,
        (
            "Current ElevenLabs cross-vertical feedback repair checkpoint",
            "`ELEVENLABS-015-cross-vertical-feedback-repair`",
        ),
    )
    assert_text_markers(
        COMMANDS,
        (
            "Validate the ElevenLabs 015 cross-vertical feedback repair without provider calls",
            "python scripts\\validate_elevenlabs_015_cross_vertical_feedback_repair.py",
        ),
    )
    assert_text_markers(
        METHODOLOGY_LOG,
        (
            "ELEVENLABS-015 cross-vertical feedback repair",
            "safe local visibility",
            "service menu evaluator repair",
            "ethical persuasion, not manipulation",
        ),
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(RUNNER),
            "--package-manifest",
            str(MANIFEST),
            "--agent-config",
            str(FIXTURE),
            "--kb-document-id",
            "kbdoc_validation_universal_sales_core",
            "--kb-document-name",
            "universal_sales_core.md",
            "--kb-document-id",
            "kbdoc_validation_atlas_web_studio_web_design_campaign_overlay",
            "--kb-document-name",
            "atlas_web_studio_web_design_campaign_overlay.md",
            "--kb-document-id",
            "kbdoc_validation_atlas_web_studio_web_design_campaign_profile",
            "--kb-document-name",
            "atlas_web_studio_web_design_campaign_profile.md",
            "--agent-prompt-file",
            str(PROMPT),
            "--first-message-file",
            str(FIRST_MESSAGE),
            "--dynamic-variable-defaults",
            str(DYNAMIC_DEFAULTS),
            "--agent-temperature",
            "0.25",
            "--agent-patch-version-scope",
            "ELEVENLABS-015 cross-vertical feedback repair",
            "--agent-patch-out",
            str(PATCH),
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
    patch = read_json(PATCH)
    assert_no_secret_leak(plan)
    assert_no_secret_leak(requests)
    assert_no_secret_leak(patch)
    assert_condition(plan.get("live_provider_calls_made") is False, "validator must not call provider")
    assert_condition(len(plan.get("knowledge_base_upload_requests", [])) == 3, "KB upload request count mismatch")
    assert_condition(plan.get("test_create_requests") == [], "015 patch package should not create tests")
    assert_condition(plan.get("agent_config_patch", {}).get("status") == "ready_for_review", "patch status mismatch")

    patched_prompt = patch["conversation_config"]["agent"]["prompt"]["prompt"]
    assert_condition("## Cross-Vertical Local-Business Feedback Repair" in patched_prompt, "patched prompt missing 015 section")

    print(
        json.dumps(
            {
                "status": "pass",
                "checkpoint_id": CHECKPOINT_ID,
                "knowledge_base_upload_requests": 3,
                "live_provider_calls_made": False,
                "production_green_claimed": False,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
