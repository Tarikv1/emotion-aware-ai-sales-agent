#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "ELEVENLABS-016-cross-vertical-v2-failure-repair"
RUNNER = ROOT / "scripts" / "run_elevenlabs_agent_automation.py"
MANIFEST = ROOT / "runtime" / "providers" / "elevenlabs_agents" / "manifests" / "web_design_cross_vertical_v2_failure_repair.package.json"
FIXTURE = ROOT / "runtime" / "providers" / "elevenlabs_agents" / "fixtures" / "web_design_agent_config.sanitized.json"
UNIVERSAL_KB = ROOT / "runtime" / "providers" / "elevenlabs_agents" / "knowledge_base" / "universal_sales_core.md"
CAMPAIGN_OVERLAY = ROOT / "runtime" / "providers" / "elevenlabs_agents" / "knowledge_base" / "atlas_web_studio_web_design_campaign_overlay.md"
CAMPAIGN_PROFILE = ROOT / "runtime" / "providers" / "elevenlabs_agents" / "knowledge_base" / "atlas_web_studio_web_design_campaign_profile.md"
PROMPT = ROOT / "runtime" / "providers" / "elevenlabs_agents" / "prompts" / "web_design_atlas_sales_prompt.md"
FIRST_MESSAGE = ROOT / "runtime" / "providers" / "elevenlabs_agents" / "prompts" / "web_design_first_message.txt"
DYNAMIC_DEFAULTS = ROOT / "runtime" / "providers" / "elevenlabs_agents" / "variables" / "mikes_kitchen_dynamic_variable_defaults.json"
CROSS_VERTICAL_TESTS = ROOT / "runtime" / "providers" / "elevenlabs_agents" / "tests" / "web_design_cross_vertical_local_business_simulation_tests.json"
DOC = ROOT / "docs" / "product" / "ELEVENLABS_016_CROSS_VERTICAL_V2_FAILURE_REPAIR.md"
INDEX = ROOT / "docs" / "product" / "CHECKPOINT_INDEX.md"
COMMANDS = ROOT / "docs" / "product" / "COMMANDS.md"
METHODOLOGY_LOG = ROOT / "docs" / "thesis" / "METHODOLOGY_LOG.md"
V2_RATIONALE = ROOT / "research" / "experiments" / "generated" / "ELEVENLABS-015-cross-vertical-feedback-repair" / "live_v2_suite_rationale_sanitized.json"
V2_TRANSCRIPTS = ROOT / "research" / "experiments" / "generated" / "ELEVENLABS-015-cross-vertical-feedback-repair" / "live_v2_failed_transcripts_sanitized.json"
V3_TRANSCRIPTS = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID / "live_v3_failed_transcripts_sanitized.json"

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
        MANIFEST,
        DOC,
        V2_RATIONALE,
        V2_TRANSCRIPTS,
    ):
        assert_condition(path.is_file(), f"Missing file: {path.relative_to(ROOT)}")

    manifest = read_json(MANIFEST)
    assert_condition(manifest.get("package_id") == CHECKPOINT_ID, "manifest package_id mismatch")
    assert_condition(manifest.get("status") == "offline-repair-ready", "manifest status mismatch")
    assert_condition(manifest.get("live_provider_calls_made") is False, "manifest must stay offline by default")
    assert_condition(
        manifest.get("repair_basis", {}).get("v2_failed_suite_id") == "suite_5001kth9p7j8fjmr4eyg6ay8wyce",
        "v2 suite id mismatch",
    )
    assert_condition(
        manifest.get("repair_basis", {}).get("failure_modes")
        == [
            "verbal_email_send_path_confirmation_after_contact_capture",
            "gatekeeper_callback_window_not_email_deflection",
        ],
        "failure modes mismatch",
    )

    v2 = read_json(V2_RATIONALE)
    assert_condition(v2.get("suite_id") == "suite_5001kth9p7j8fjmr4eyg6ay8wyce", "V2 rationale suite mismatch")
    assert_condition(v2.get("failed_count") == 2, "V2 failed count mismatch")
    v2_text = V2_TRANSCRIPTS.read_text(encoding="utf-8")
    for marker in (
        "mike at northsideauto dot com",
        "When should I say to call you back?",
        "deflected to email",
    ):
        assert_condition(marker in v2_text, f"V2 evidence missing marker: {marker}")
    if V3_TRANSCRIPTS.is_file():
        v3_text = V3_TRANSCRIPTS.read_text(encoding="utf-8")
        for marker in (
            "You sending it right now?",
            "already sent or you're about to send it",
        ):
            assert_condition(marker in v3_text, f"V3 evidence missing marker: {marker}")

    prompt_text = assert_text_markers(
        PROMPT,
        (
            "## Cross-Vertical V2 Failure Repair",
            "Verbal email capture is a terminal send-path trigger.",
            "`mike at northsideauto dot com`",
            "`mike@northsideauto.com`",
            "Do not leave the call after the buyer gives an email.",
            "Gatekeeper callback-window repair",
            "do not deflect to email",
            "`I'll call back after two. Please let them know it is Emma from Atlas Web Studio about the free homepage mockup. Have a good day.`",
            "Never invent a found-online email address.",
            "Use present-action wording for send timing",
            "`Yes, I'm sending it now to luna@lunahairstudio.com. You can reply there with questions. Have a good one.`",
            "If you ask for an email and the buyer gives a clear email in the next turn",
            "Never start the email-send turn with `Great`",
        ),
    )
    assert_condition("ethical manipulation" not in prompt_text.lower(), "prompt must not frame persuasion as manipulation")

    assert_text_markers(
        UNIVERSAL_KB,
        (
            "Send Timing Confirmation",
            "I'm sending it now to [email]",
            "Do not answer a timing question with only \"I will send it\"",
        ),
    )

    assert_text_markers(
        CAMPAIGN_OVERLAY,
        (
            "## Cross-Vertical V2 Failure Repair Overlay",
            "verbal email capture",
            "Gatekeeper callback-window repair",
            "do not switch to email",
            "Never invent a found-online email address",
            "If the buyer asks whether the mockup is being sent right now",
            "Do not use only `I will send it`",
        ),
    )
    assert_text_markers(
        CAMPAIGN_PROFILE,
        (
            "## Approved Send And Callback Facts",
            "Verbal email spell-outs are valid contact details when the address is clear.",
            "No found-online email send path is approved.",
            "The agent may choose a simple outbound callback window",
            "Immediate send timing is approved for the free mockup link",
        ),
    )
    tests_text = assert_text_markers(
        CROSS_VERTICAL_TESTS,
        (
            "verbal email such as `mike at northsideauto dot com`",
            "If the gatekeeper asks when to say the owner should call back",
            "must not deflect to email",
            "If the buyer asks whether the link is being sent right now",
            "right-now send question with only future/ambiguous wording",
            "email-send path is also valid",
            "a simulated post-close repeat question should not fail the run",
        ),
    )
    assert_condition("restaurant leakage such as menu" not in tests_text, "old overbroad menu leakage wording remains")

    assert_text_markers(
        DOC,
        (
            CHECKPOINT_ID,
            "verbal email send-path confirmation",
            "gatekeeper callback-window repair",
            "python scripts\\validate_elevenlabs_016_cross_vertical_v2_failure_repair.py",
        ),
    )
    assert_text_markers(INDEX, ("Current ElevenLabs cross-vertical V2 failure repair checkpoint", CHECKPOINT_ID))
    assert_text_markers(COMMANDS, ("Validate the ElevenLabs 016 cross-vertical V2 failure repair",))
    assert_text_markers(METHODOLOGY_LOG, ("ELEVENLABS-016 cross-vertical V2 failure repair", "suite_5001kth9p7j8fjmr4eyg6ay8wyce"))

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
            "ELEVENLABS-016 cross-vertical V2 failure repair",
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

    print(
        json.dumps(
            {
                "status": "pass",
                "checkpoint_id": CHECKPOINT_ID,
                "v2_failed_count": 2,
                "live_provider_calls_made": False,
                "production_green_claimed": False,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
