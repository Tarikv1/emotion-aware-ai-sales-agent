#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "ELEVENLABS-011-web-design-remaining-simulation-repair"
RUNNER = ROOT / "scripts" / "run_elevenlabs_agent_automation.py"
MANIFEST = (
    ROOT
    / "runtime"
    / "providers"
    / "elevenlabs_agents"
    / "manifests"
    / "web_design_remaining_simulation_repair.package.json"
)
FIXTURE = (
    ROOT
    / "runtime"
    / "providers"
    / "elevenlabs_agents"
    / "fixtures"
    / "web_design_agent_config.sanitized.json"
)
UNIVERSAL_KB = ROOT / "runtime" / "providers" / "elevenlabs_agents" / "knowledge_base" / "universal_sales_core.md"
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
DYNAMIC_DEFAULTS = (
    ROOT
    / "runtime"
    / "providers"
    / "elevenlabs_agents"
    / "variables"
    / "mikes_kitchen_dynamic_variable_defaults.json"
)
DOC = ROOT / "docs" / "product" / "ELEVENLABS_011_WEB_DESIGN_REMAINING_SIMULATION_REPAIR.md"
INDEX = ROOT / "docs" / "product" / "CHECKPOINT_INDEX.md"
COMMANDS = ROOT / "docs" / "product" / "COMMANDS.md"
RESULT_SUMMARY_010 = (
    ROOT
    / "research"
    / "experiments"
    / "generated"
    / "ELEVENLABS-010-web-design-sales-control-repair"
    / "sales_control_repair_results_summary.json"
)
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
    )
    found = [marker for marker in blocked if marker in serialized]
    assert_condition(not found, f"Output contains blocked marker(s): {found}")


def main() -> None:
    for path in (RUNNER, FIXTURE, UNIVERSAL_KB, CAMPAIGN_KB, PROMPT, FIRST_MESSAGE, DYNAMIC_DEFAULTS, MANIFEST, DOC):
        assert_condition(path.is_file(), f"Missing file: {path.relative_to(ROOT)}")

    previous_summary = read_json(RESULT_SUMMARY_010)
    assert_condition(previous_summary.get("production_green") is False, "010 summary must remain not production-green")
    remaining_ids = {
        item.get("source_test_id")
        for item in previous_summary.get("remaining_failure_modes", [])
        if isinstance(item, dict)
    }
    assert_condition(
        remaining_ids == {"sim_plain_language_confused_buyer", "sim_social_presence_objection"},
        f"010 remaining failures changed unexpectedly: {remaining_ids}",
    )

    manifest = read_json(MANIFEST)
    assert_condition(manifest.get("package_id") == CHECKPOINT_ID, "manifest package_id mismatch")
    assert_condition(manifest.get("status") == "offline-repair-ready", "manifest status mismatch")
    assert_condition(len(manifest.get("knowledge_base_docs", [])) == 2, "manifest should upload two KB docs")
    assert_condition(manifest.get("baseline_tests") == [], "011 patch package should not create new tests")
    assert_condition(
        manifest.get("upload_intent", {}).get("replace_same_name_attached_kb_docs") is True,
        "replace intent missing",
    )
    assert_condition(
        manifest.get("live_provider_calls_made") is False,
        "011 manifest must stay offline-default",
    )

    prompt_text = assert_text_markers(
        PROMPT,
        (
            "Remaining V22 simulation repair",
            "Plain-language repair",
            "never say `potential direction`",
            "Use `free homepage mockup`",
            "Send-path acknowledgments outrank social-channel objection handling",
            "Social-channel value rotation ladder",
            "after owner control and shareable link, use proof-before-purchase",
            "do not mention menu, hours, location, reservation, practical details, key details, organized, or one place",
        ),
    )
    assert_text_markers(
        CAMPAIGN_KB,
        (
            "Package: `ELEVENLABS-011-web-design-remaining-simulation-repair`",
            "## Remaining V22 Simulation Repair",
            "Plain-language repair examples",
            "Social-channel value rotation ladder",
            "Do not rotate back into practical details",
            "If it feels like the same thing, ignore the mockup.",
        ),
    )
    assert_text_markers(
        DOC,
        (
            "does not make a live provider call",
            "V22c remains `7/9`",
            "V22d was patch-only",
            "plain-language abstract wording",
            "social-objection value rotation",
            "python scripts\\validate_elevenlabs_011_web_design_remaining_simulation_repair.py",
        ),
    )
    assert_text_markers(
        INDEX,
        (
            "Current ElevenLabs remaining-simulation repair checkpoint",
            "`ELEVENLABS-011-web-design-remaining-simulation-repair`",
        ),
    )
    assert_text_markers(
        COMMANDS,
        (
            "Validate the ElevenLabs 011 remaining simulation repair without provider calls",
            "python scripts\\validate_elevenlabs_011_web_design_remaining_simulation_repair.py",
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
            "kbdoc_validation_atlas_web_studio_web_design_campaign",
            "--kb-document-name",
            "atlas_web_studio_web_design_campaign.md",
            "--agent-prompt-file",
            str(PROMPT),
            "--first-message-file",
            str(FIRST_MESSAGE),
            "--dynamic-variable-defaults",
            str(DYNAMIC_DEFAULTS),
            "--agent-temperature",
            "0.25",
            "--agent-patch-version-scope",
            "ELEVENLABS-011 web design remaining simulation repair",
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

    assert_condition(len(plan.get("knowledge_base_upload_requests", [])) == 2, "KB upload request count mismatch")
    assert_condition(plan.get("test_create_requests") == [], "011 patch package should not create tests")
    assert_condition(plan.get("agent_config_patch", {}).get("status") == "ready_for_review", "patch status mismatch")

    patched_prompt = patch["conversation_config"]["agent"]["prompt"]["prompt"]
    for marker in (
        "Remaining V22 simulation repair",
        "Plain-language repair",
        "Social-channel value rotation ladder",
    ):
        assert_condition(marker in patched_prompt, f"patched prompt missing marker: {marker}")
    assert_condition("potential direction" not in prompt_text.replace("never say `potential direction`", ""), "prompt still leaks potential direction outside the ban")

    print(
        json.dumps(
            {
                "status": "pass",
                "checkpoint_id": CHECKPOINT_ID,
                "live_provider_calls_made": False,
                "previous_live_result": "7/9; not production-green",
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
