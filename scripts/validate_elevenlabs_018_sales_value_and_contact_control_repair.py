#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "ELEVENLABS-018-sales-value-and-contact-control-repair"
RUNNER = ROOT / "scripts" / "run_elevenlabs_agent_automation.py"
MANIFEST = (
    ROOT
    / "runtime"
    / "providers"
    / "elevenlabs_agents"
    / "manifests"
    / "web_design_sales_value_and_contact_control_repair.package.json"
)
TEST_MANIFEST = (
    ROOT
    / "runtime"
    / "providers"
    / "elevenlabs_agents"
    / "manifests"
    / "web_design_cross_vertical_local_business_simulation_tests.package.json"
)
FIXTURE = ROOT / "runtime" / "providers" / "elevenlabs_agents" / "fixtures" / "web_design_agent_config.sanitized.json"
PROMPT = ROOT / "runtime" / "providers" / "elevenlabs_agents" / "prompts" / "web_design_atlas_sales_prompt.md"
FIRST_MESSAGE = ROOT / "runtime" / "providers" / "elevenlabs_agents" / "prompts" / "web_design_first_message.txt"
DYNAMIC_DEFAULTS = ROOT / "runtime" / "providers" / "elevenlabs_agents" / "variables" / "mikes_kitchen_dynamic_variable_defaults.json"
UNIVERSAL_KB = ROOT / "runtime" / "providers" / "elevenlabs_agents" / "knowledge_base" / "universal_sales_core.md"
COMPILED = ROOT / "runtime" / "sales_knowledge" / "universal_sales_rag" / "compiled" / "universal_sales_core.md"
CAMPAIGN_OVERLAY = (
    ROOT / "runtime" / "providers" / "elevenlabs_agents" / "knowledge_base" / "atlas_web_studio_web_design_campaign_overlay.md"
)
CAMPAIGN_PROFILE = (
    ROOT / "runtime" / "providers" / "elevenlabs_agents" / "knowledge_base" / "atlas_web_studio_web_design_campaign_profile.md"
)
CROSS_VERTICAL_TESTS = (
    ROOT / "runtime" / "providers" / "elevenlabs_agents" / "tests" / "web_design_cross_vertical_local_business_simulation_tests.json"
)
CATEGORY_JOURNEY = ROOT / "runtime" / "sales_knowledge" / "universal_sales_rag" / "categories" / "02_buyer_journey_jobs.md"
CATEGORY_ENABLEMENT = ROOT / "runtime" / "sales_knowledge" / "universal_sales_rag" / "categories" / "03_buyer_enablement_and_sensemaking.md"
CATEGORY_STAKEHOLDER = ROOT / "runtime" / "sales_knowledge" / "universal_sales_rag" / "categories" / "04_stakeholder_mapping.md"
CATEGORY_VALUE = ROOT / "runtime" / "sales_knowledge" / "universal_sales_rag" / "categories" / "07_value_and_roi_framing.md"
CATEGORY_NEXT_STEP = ROOT / "runtime" / "sales_knowledge" / "universal_sales_rag" / "categories" / "12_next_step_policy.md"
CATEGORY_ETHICS = ROOT / "runtime" / "sales_knowledge" / "universal_sales_rag" / "categories" / "16_ethical_persuasion_boundaries.md"
DOC = ROOT / "docs" / "product" / "ELEVENLABS_018_SALES_VALUE_AND_CONTACT_CONTROL_REPAIR.md"
INDEX = ROOT / "docs" / "product" / "CHECKPOINT_INDEX.md"
COMMANDS = ROOT / "docs" / "product" / "COMMANDS.md"
METHODOLOGY_LOG = ROOT / "docs" / "thesis" / "METHODOLOGY_LOG.md"

OUT_DIR = ROOT / ".tmp" / CHECKPOINT_ID / "validation"
PLAN = OUT_DIR / "agent_patch_plan.json"
REQUESTS = OUT_DIR / "agent_patch_requests.json"
PATCH = OUT_DIR / "agent_patch_payload.json"
TEST_PLAN = OUT_DIR / "revised_tests_plan.json"
TEST_REQUESTS = OUT_DIR / "revised_tests_requests.json"


def fail(message: str) -> None:
    raise AssertionError(message)


def assert_condition(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def read_json(path: Path) -> dict[str, Any]:
    assert_condition(path.is_file(), f"Missing JSON file: {path.relative_to(ROOT)}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert_condition(isinstance(payload, dict), f"{path.relative_to(ROOT)} must contain a JSON object")
    return payload


def assert_markers(path: Path, markers: tuple[str, ...]) -> str:
    assert_condition(path.is_file(), f"Missing file: {path.relative_to(ROOT)}")
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
        MANIFEST,
        TEST_MANIFEST,
        FIXTURE,
        PROMPT,
        FIRST_MESSAGE,
        DYNAMIC_DEFAULTS,
        UNIVERSAL_KB,
        COMPILED,
        CAMPAIGN_OVERLAY,
        CAMPAIGN_PROFILE,
        CROSS_VERTICAL_TESTS,
        CATEGORY_JOURNEY,
        CATEGORY_ENABLEMENT,
        CATEGORY_STAKEHOLDER,
        CATEGORY_VALUE,
        CATEGORY_NEXT_STEP,
        CATEGORY_ETHICS,
        DOC,
        INDEX,
        COMMANDS,
        METHODOLOGY_LOG,
    ):
        assert_condition(path.is_file(), f"Missing file: {path.relative_to(ROOT)}")

    manifest = read_json(MANIFEST)
    assert_condition(manifest.get("package_id") == CHECKPOINT_ID, "manifest package_id mismatch")
    assert_condition(manifest.get("status") == "offline-repair-ready", "manifest status mismatch")
    assert_condition(manifest.get("live_provider_calls_made") is False, "manifest must stay offline by default")
    assert_condition(
        manifest.get("repair_basis", {}).get("human_feedback_categories")
        == [
            "weak_website_value_mechanism_after_non_guarantee",
            "missing_owner_manager_name_capture",
            "premature_send_path_ending_without_contact_capture",
            "unanswered_terminal_buyer_clarification",
            "public_profile_contact_lookup_handoff",
            "stricter_simulation_criteria_for_contact_completion",
        ],
        "human feedback categories mismatch",
    )
    assert_condition(
        manifest.get("upload_intent", {}).get("target_test_folder_name")
        == "Atlas Web Studio - Cross-Vertical Local Business Simulation V3",
        "target test folder mismatch",
    )
    planned = manifest.get("planned_live_application", {})
    assert_condition(planned.get("previous_live_agent_version_id") == "agtvrsn_6701kthngpabe6etedq4rr4a3dpa", "prior version mismatch")

    if "live_application" in manifest:
        live = manifest["live_application"]
        assert_condition(live.get("live_provider_calls_made") is True, "live_application provider flag mismatch")
        assert_condition(len(live.get("current_attached_knowledge_base_document_ids", [])) == 3, "live KB id count mismatch")
        assert_condition(live.get("simulation_run_made") is False, "simulation run must remain unclaimed")
        assert_condition(live.get("production_green_claimed") is False, "production green must remain unclaimed")

    test_manifest = read_json(TEST_MANIFEST)
    revision = test_manifest.get("source_revision_after_live_creation", {})
    assert_condition(revision.get("checkpoint") == CHECKPOINT_ID, "test manifest checkpoint mismatch")
    assert_condition(revision.get("revised_live_folder_name") == "Atlas Web Studio - Cross-Vertical Local Business Simulation V3", "V3 folder name missing")
    if revision.get("live_test_recreation_required") is False:
        assert_condition(bool(revision.get("revised_live_folder_id")), "live V3 folder id missing")
        assert_condition(bool(revision.get("revised_live_creation_evidence")), "live V3 evidence missing")

    prompt_text = assert_markers(
        PROMPT,
        (
            "Update marker: `ELEVENLABS-018-sales-value-and-contact-control-repair`",
            "owned, indexable page could support local visibility",
            "No, I can't promise that.",
            "support from an owned, indexable page",
            "Do not say `key details`, `customer decision path`, `focused inquiries`, `clearer page`, `something to judge`, or `initial judgments`",
            "ask for the name in the same turn",
            "If you missed it in the first owner/manager answer, ask before the next value explanation",
            "Public-profile lookup handoff",
            "buyer-instructed public-source lookup",
            "That's it: you'll get the link there",
            "mike@northsideauto.com",
        ),
    )
    overlay_text = assert_markers(
        CAMPAIGN_OVERLAY,
        (
            "Update marker: `ELEVENLABS-018-sales-value-and-contact-control-repair`",
            "Exact email capture is not complete until",
            "Buyer-instructed public-profile contact lookup is allowed for this campaign",
            "Do not hard-refuse with \"I can't send it to an email I find",
            "Name capture should happen in the first non-terminal owner/manager answer",
            "owned, indexable page",
            "Do not use\n`clearer page`, `something to judge`, or `initial judgments` as the main value",
        ),
    )
    profile_text = assert_markers(
        CAMPAIGN_PROFILE,
        (
            "Update marker: `ELEVENLABS-018-sales-value-and-contact-control-repair`",
            "required completion facts are: normalized",
            "Buyer-instructed public-profile contact lookup is approved for this campaign",
            "The `ELEVENLABS-018` public-profile rule",
            "owned, indexable page people can check",
            "No more-customers,",
        ),
    )
    assert_condition(UNIVERSAL_KB.read_text(encoding="utf-8") == COMPILED.read_text(encoding="utf-8"), "provider universal KB must match compiled output")
    assert_condition("ethical manipulation" not in "\n".join((prompt_text, overlay_text, profile_text, UNIVERSAL_KB.read_text(encoding="utf-8"))).lower(), "runtime text must not use ethical manipulation")

    assert_markers(CATEGORY_JOURNEY, ("The problem must be concrete enough to create demand", "local visibility support"))
    assert_markers(CATEGORY_ENABLEMENT, ("how a buyer checks a local service from Google",))
    assert_markers(CATEGORY_STAKEHOLDER, ("ask once in the same non-terminal turn", "ask before the next value explanation"))
    assert_markers(CATEGORY_VALUE, ("Strong mechanism after a \"no\"", "owned indexed page", "Avoid weak filler"))
    assert_markers(CATEGORY_NEXT_STEP, ("Final send-path clarification", "Public-source handoff policy"))
    assert_markers(CATEGORY_ETHICS, ("make the supported value mechanism clear",))

    tests = read_json(CROSS_VERTICAL_TESTS)
    serialized_tests = json.dumps(tests, ensure_ascii=False)
    for marker in (
        CHECKPOINT_ID,
        "stronger_value_mechanism",
        "public_profile_lookup_handoff",
        "send_path_completion",
        "local visibility support from an owned indexable page",
        "No, I can't promise that.",
        "weak filler such as clearer page",
        "Facebook page, same name",
        "hard-refuses a buyer-instructed public business-source lookup",
        "must ask before the next value explanation",
        "final buyer contact turn with no agent confirmation must fail",
    ):
        assert_condition(marker in serialized_tests, f"cross-vertical tests missing marker: {marker}")

    assert_markers(DOC, (CHECKPOINT_ID, "local visibility", "name capture", "Public-profile", "V3"))
    assert_markers(INDEX, (CHECKPOINT_ID, "sales-value and contact-control repair"))
    assert_markers(COMMANDS, ("Validate the ElevenLabs 018 sales-value and contact-control repair", "validate_elevenlabs_018_sales_value_and_contact_control_repair.py"))
    assert_markers(METHODOLOGY_LOG, ("ELEVENLABS-018 sales-value and contact-control repair", "owned indexable page", "public-profile lookup"))

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
            "ELEVENLABS-018 sales value and contact control repair",
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
    for payload_path in (PLAN, REQUESTS, PATCH):
        assert_no_secret_leak(read_json(payload_path))
    plan = read_json(PLAN)
    assert_condition(plan.get("live_provider_calls_made") is False, "validator must not call provider")
    assert_condition(len(plan.get("knowledge_base_upload_requests", [])) == 3, "plan must include three KB uploads")
    assert_condition(plan.get("agent_config_patch", {}).get("status") == "ready_for_review", "agent patch must be ready")

    tests_completed = subprocess.run(
        [
            sys.executable,
            str(RUNNER),
            "--package-manifest",
            str(TEST_MANIFEST),
            "--test-folder-name",
            "Atlas Web Studio - Cross-Vertical Local Business Simulation V3",
            "--out",
            str(TEST_PLAN),
            "--api-requests-out",
            str(TEST_REQUESTS),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert_condition(tests_completed.returncode == 0, tests_completed.stderr or tests_completed.stdout)
    for payload_path in (TEST_PLAN, TEST_REQUESTS):
        assert_no_secret_leak(read_json(payload_path))
    test_plan = read_json(TEST_PLAN)
    assert_condition(test_plan.get("live_provider_calls_made") is False, "test-plan validator must not call provider")
    assert_condition(len(test_plan.get("test_create_requests", [])) == 6, "test plan must include six tests")
    assert_condition(
        test_plan.get("test_folder", {}).get("folder_name")
        == "Atlas Web Studio - Cross-Vertical Local Business Simulation V3",
        "test folder name mismatch",
    )

    print(
        json.dumps(
            {
                "status": "pass",
                "checkpoint_id": CHECKPOINT_ID,
                "knowledge_base_upload_count": 3,
                "test_create_request_count": 6,
                "live_provider_calls_made": False,
                "production_green_claimed": False,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
