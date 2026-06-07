#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "ELEVENLABS-017-natural-control-feedback-repair"
RUNNER = ROOT / "scripts" / "run_elevenlabs_agent_automation.py"
MANIFEST = (
    ROOT
    / "runtime"
    / "providers"
    / "elevenlabs_agents"
    / "manifests"
    / "web_design_natural_control_feedback_repair.package.json"
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
CATEGORY_JOURNEY = ROOT / "runtime" / "sales_knowledge" / "universal_sales_rag" / "categories" / "02_buyer_journey_jobs.md"
CATEGORY_ENABLEMENT = ROOT / "runtime" / "sales_knowledge" / "universal_sales_rag" / "categories" / "03_buyer_enablement_and_sensemaking.md"
CATEGORY_STAKEHOLDER = ROOT / "runtime" / "sales_knowledge" / "universal_sales_rag" / "categories" / "04_stakeholder_mapping.md"
CATEGORY_VALUE = ROOT / "runtime" / "sales_knowledge" / "universal_sales_rag" / "categories" / "07_value_and_roi_framing.md"
CATEGORY_NEXT_STEP = ROOT / "runtime" / "sales_knowledge" / "universal_sales_rag" / "categories" / "12_next_step_policy.md"
CATEGORY_ETHICS = ROOT / "runtime" / "sales_knowledge" / "universal_sales_rag" / "categories" / "16_ethical_persuasion_boundaries.md"
COMPILED = ROOT / "runtime" / "sales_knowledge" / "universal_sales_rag" / "compiled" / "universal_sales_core.md"
DOC = ROOT / "docs" / "product" / "ELEVENLABS_017_NATURAL_CONTROL_FEEDBACK_REPAIR.md"
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
    if not path.is_file():
        fail(f"Missing JSON file: {path.relative_to(ROOT)}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        fail(f"{path.relative_to(ROOT)} must contain a JSON object")
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


def assert_no_runtime_manipulation_phrase(*texts: str) -> None:
    combined = "\n".join(texts).lower()
    assert_condition("ethical manipulation" not in combined, "runtime text must not use the phrase ethical manipulation")


def main() -> None:
    for path in (
        RUNNER,
        MANIFEST,
        TEST_MANIFEST,
        FIXTURE,
        UNIVERSAL_KB,
        CAMPAIGN_OVERLAY,
        CAMPAIGN_PROFILE,
        PROMPT,
        FIRST_MESSAGE,
        DYNAMIC_DEFAULTS,
        CROSS_VERTICAL_TESTS,
        CATEGORY_JOURNEY,
        CATEGORY_ENABLEMENT,
        CATEGORY_STAKEHOLDER,
        CATEGORY_VALUE,
        CATEGORY_NEXT_STEP,
        CATEGORY_ETHICS,
        COMPILED,
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
    live_application = manifest.get("live_application", {})
    assert_condition(
        live_application.get("current_live_agent_version_id") == "agtvrsn_6701kthngpabe6etedq4rr4a3dpa",
        "live agent version mismatch",
    )
    assert_condition(
        live_application.get("current_attached_knowledge_base_document_ids")
        == ["7pyke4f9n9casIzeA25x", "K6xBUXcBoo8cPDvrmCzL", "9pv9mi6v2EdWIOUsAzoH"],
        "live KB document ids mismatch",
    )
    assert_condition(
        live_application.get("revised_test_folder_id") == "tfld_6201kth9njh3f18rxe63zqd34cgm",
        "live revised test folder mismatch",
    )
    assert_condition(len(live_application.get("revised_tests_created", [])) == 6, "live revised test count mismatch")
    assert_condition(live_application.get("simulation_run_made") is False, "simulation run must remain unclaimed")
    assert_condition(live_application.get("production_green_claimed") is False, "production green must remain unclaimed")
    assert_condition(
        manifest.get("repair_basis", {}).get("human_feedback_categories")
        == [
            "premature_send_path_ending_without_contact_capture",
            "unanswered_terminal_buyer_clarification",
            "delivery_timing_repeat_loop_repair",
            "busy_callback_email_option_compression",
            "stronger_name_capture_when_natural",
            "plain_analogy_and_perspective_sensemaking",
            "short_non_guarantee_claim_boundary",
            "problem_solution_gain_curiosity_sequence",
        ],
        "human feedback categories mismatch",
    )
    assert_condition(manifest.get("baseline_tests") == [], "017 repair manifest must not mix package ids in baseline_tests")
    assert_condition(
        manifest.get("upload_intent", {}).get("revised_test_manifest")
        == "runtime/providers/elevenlabs_agents/manifests/web_design_cross_vertical_local_business_simulation_tests.package.json",
        "017 manifest must point to revised cross-vertical test manifest",
    )

    test_manifest = read_json(TEST_MANIFEST)
    revision = test_manifest.get("source_revision_after_live_creation", {})
    if revision.get("checkpoint") == CHECKPOINT_ID:
        assert_condition(revision.get("live_test_recreation_required") is False, "test manifest should record completed V2 creation")
        assert_condition(
            revision.get("revised_live_folder_id") == "tfld_6201kth9njh3f18rxe63zqd34cgm",
            "test manifest revised V2 folder mismatch",
        )
    else:
        assert_condition(
            revision.get("previous_revised_live_folder_id") == "tfld_6201kth9njh3f18rxe63zqd34cgm",
            "later test manifest revision must preserve the 017 V2 folder id",
        )

    prompt_text = assert_text_markers(
        PROMPT,
        (
            "## Natural Control Feedback Repair",
            "Update marker: `ELEVENLABS-017-natural-control-feedback-repair`",
            "Accepted send without contact is not terminal",
            "`Sure. What email should I use?`",
            "Repeated delivery-timing repair",
            "`Sorry, I meant right now. It should arrive shortly.`",
            "Busy two-option compression",
            "`I can do both. Which would you prefer?`",
            "by the second non-terminal agent turn",
            "Short non-guarantee and perspective framing",
            "For regulated or medical-adjacent contexts",
            "Use plain analogies and perspective checks",
            "Demand-creation sequence",
            "Problem-solution-gain-curiosity sequence",
            "Do not assert the buyer definitely has the problem",
            "Do not describe the approved control style as manipulation",
        ),
    )

    overlay_text = assert_text_markers(
        CAMPAIGN_OVERLAY,
        (
            "## Natural Control Feedback Repair Overlay",
            "Update marker: `ELEVENLABS-017-natural-control-feedback-repair`",
            "Accepted send without contact is not terminal.",
            "Delivery timing repair",
            "Busy two-option compression",
            "Name capture should happen by the second non-terminal agent turn",
            "Plain analogies and perspective checks are allowed",
            "Problem-solution-gain-curiosity sequence for this campaign",
            "Possible problem: first-time prospects may not have",
            "Do not describe the approved control style as manipulation",
        ),
    )
    profile_text = assert_text_markers(
        CAMPAIGN_PROFILE,
        (
            "## Approved Natural-Control Facts",
            "Update marker: `ELEVENLABS-017-natural-control-feedback-repair`",
            "If the buyer accepts the free mockup but has not provided an email",
            "should arrive shortly or today",
            "Asking the speaker's name is allowed for rapport",
            "No more-customers, more-patients,",
            "Plain analogies may compare a homepage",
            "The campaign-approved problem hypothesis",
            "approved curiosity/proof step",
        ),
    )
    universal_text = UNIVERSAL_KB.read_text(encoding="utf-8")
    compiled_text = COMPILED.read_text(encoding="utf-8")
    assert_condition(universal_text == compiled_text, "provider universal KB must match compiled universal KB")
    assert_no_runtime_manipulation_phrase(prompt_text, overlay_text, profile_text, universal_text)

    assert_text_markers(
        CATEGORY_JOURNEY,
        (
            "Demand-creation sequence",
            "likely problem, the offered solution, the buyer gain, and the curiosity/proof step",
        ),
    )
    assert_text_markers(
        CATEGORY_ENABLEMENT,
        (
            "Plain analogies and perspective checks",
            "one short analogy or perspective question",
        ),
    )
    assert_text_markers(CATEGORY_STAKEHOLDER, ("Name capture should identify the human speaker",))
    assert_text_markers(
        CATEGORY_VALUE,
        (
            "Short non-guarantee framing",
            "I can't promise that. What it can do is",
            "Problem-solution-gain-curiosity framing",
            "make demand visible",
        ),
    )
    assert_text_markers(
        CATEGORY_NEXT_STEP,
        (
            "Accepted send without contact is not terminal",
            "Repeated delivery-timing repair",
            "Busy two-option compression",
        ),
    )
    assert_text_markers(
        CATEGORY_ETHICS,
        (
            "Do not hide intent or imply a guarantee through vague wording",
            "short non-guarantee boundary",
        ),
    )

    tests = read_json(CROSS_VERTICAL_TESTS)
    serialized_tests = json.dumps(tests, ensure_ascii=False)
    for marker in (
        "accepted_send_without_contact",
        "unanswered_terminal_question",
        "delivery_timing_repair",
        "busy_two_option_compression",
        "analogy_and_perspective",
        "short_non_guarantee",
        "name_capture",
        "If the buyer accepts the send path before giving contact details",
        "final buyer turn that asks a new clear question",
        "I can do both. Which would you prefer?",
        "plain analogy or perspective check",
        "must not use long wording such as `I can't promise that a website will automatically",
        "ask who it is speaking with by the second non-terminal turn",
        "leaves a terminal buyer clarification unanswered",
    ):
        assert_condition(marker in serialized_tests, f"cross-vertical tests missing marker: {marker}")
    assert_condition("restaurant leakage such as menu" not in serialized_tests, "old overbroad menu leakage wording remains")

    assert_text_markers(
        DOC,
        (
            CHECKPOINT_ID,
            "premature send-path endings",
            "delivery-timing questions",
            "problem-solution-gain-curiosity",
            "agtvrsn_6701kthngpabe6etedq4rr4a3dpa",
            "tfld_6201kth9njh3f18rxe63zqd34cgm",
            "ethical manipulation",
            "python scripts\\validate_elevenlabs_017_natural_control_feedback_repair.py",
        ),
    )
    assert_text_markers(INDEX, ("Current ElevenLabs natural-control feedback repair checkpoint", CHECKPOINT_ID))
    assert_text_markers(
        COMMANDS,
        (
            "Validate the ElevenLabs 017 natural-control feedback repair without provider calls",
            "python scripts\\validate_elevenlabs_017_natural_control_feedback_repair.py",
        ),
    )
    assert_text_markers(
        METHODOLOGY_LOG,
        (
            "ELEVENLABS-017 natural-control feedback repair",
            "accepted-send-without-contact",
            "delivery-timing repeat repair",
            "problem-solution-gain-curiosity",
            "agtvrsn_6701kthngpabe6etedq4rr4a3dpa",
            "tfld_6201kth9njh3f18rxe63zqd34cgm",
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
            "ELEVENLABS-017 natural control feedback repair",
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
    assert_condition(len(plan.get("knowledge_base_upload_requests", [])) == 3, "plan must include three KB uploads")
    assert_condition(len(plan.get("test_create_requests", [])) == 0, "017 patch plan must not mix package-id test creates")
    assert_condition(
        plan.get("agent_config_patch", {}).get("status") == "ready_for_review",
        "agent patch must be ready for review",
    )

    tests_completed = subprocess.run(
        [
            sys.executable,
            str(RUNNER),
            "--package-manifest",
            str(TEST_MANIFEST),
            "--test-folder-name",
            "Atlas Web Studio - Cross-Vertical Local Business Simulation V2",
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
    test_plan = read_json(TEST_PLAN)
    test_requests = read_json(TEST_REQUESTS)
    assert_no_secret_leak(test_plan)
    assert_no_secret_leak(test_requests)
    assert_condition(test_plan.get("live_provider_calls_made") is False, "test-plan validator must not call provider")
    assert_condition(len(test_plan.get("test_create_requests", [])) == 6, "test plan must include six revised test creates")
    assert_condition(
        test_plan.get("test_folder", {}).get("folder_name") == "Atlas Web Studio - Cross-Vertical Local Business Simulation V2",
        "test plan folder mismatch",
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
