#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "ELEVENLABS-013-send-path-final-confirmation"
RUNNER = ROOT / "scripts" / "run_elevenlabs_agent_automation.py"
MANIFEST = (
    ROOT
    / "runtime"
    / "providers"
    / "elevenlabs_agents"
    / "manifests"
    / "web_design_send_path_final_confirmation.package.json"
)
FIXTURE = ROOT / "runtime" / "providers" / "elevenlabs_agents" / "fixtures" / "web_design_agent_config.sanitized.json"
UNIVERSAL_KB = ROOT / "runtime" / "providers" / "elevenlabs_agents" / "knowledge_base" / "universal_sales_core.md"
CAMPAIGN_OVERLAY = (
    ROOT
    / "runtime"
    / "providers"
    / "elevenlabs_agents"
    / "knowledge_base"
    / "atlas_web_studio_web_design_campaign_overlay.md"
)
CAMPAIGN_PROFILE = (
    ROOT
    / "runtime"
    / "providers"
    / "elevenlabs_agents"
    / "knowledge_base"
    / "atlas_web_studio_web_design_campaign_profile.md"
)
PROMPT = ROOT / "runtime" / "providers" / "elevenlabs_agents" / "prompts" / "web_design_atlas_sales_prompt.md"
FIRST_MESSAGE = ROOT / "runtime" / "providers" / "elevenlabs_agents" / "prompts" / "web_design_first_message.txt"
DYNAMIC_DEFAULTS = ROOT / "runtime" / "providers" / "elevenlabs_agents" / "variables" / "mikes_kitchen_dynamic_variable_defaults.json"
DOC = ROOT / "docs" / "product" / "ELEVENLABS_013_SEND_PATH_FINAL_CONFIRMATION.md"
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
        MANIFEST,
        DOC,
    ):
        assert_condition(path.is_file(), f"Missing file: {path.relative_to(ROOT)}")

    manifest = read_json(MANIFEST)
    assert_condition(manifest.get("package_id") == CHECKPOINT_ID, "manifest package_id mismatch")
    assert_condition(manifest.get("status") == "offline-repair-ready", "manifest status mismatch")
    assert_condition(manifest.get("live_provider_calls_made") is False, "manifest must stay offline by default")
    assert_condition(
        manifest.get("knowledge_base_docs")
        == [
            "runtime/providers/elevenlabs_agents/knowledge_base/universal_sales_core.md",
            "runtime/providers/elevenlabs_agents/knowledge_base/atlas_web_studio_web_design_campaign_overlay.md",
            "runtime/providers/elevenlabs_agents/knowledge_base/atlas_web_studio_web_design_campaign_profile.md",
        ],
        "manifest KB docs must preserve universal, overlay, profile order",
    )

    assert_text_markers(
        PROMPT,
        (
            "## Send-Path Final Confirmation Repair",
            "If the send path is already clear and the buyer asks a final yes/no confirmation",
            "`so I'll get an email with a link`",
            "`so you are emailing the sample page`",
            "answer yes, confirm the link, add one short closing, and stop.",
            "Good final shape: `Yes, I'll send the email with the mockup link. Have a good one.`",
            "Do not reopen the pitch, ask another question, mention website value, or repeat the full send-path explanation.",
        ),
    )
    assert_text_markers(
        DOC,
        (
            "final send-path clarification",
            "one-line terminal answer",
            "Yes, I'll send the email with the mockup link. Have a good one.",
            "python scripts\\validate_elevenlabs_013_send_path_final_confirmation.py",
        ),
    )
    assert_text_markers(
        INDEX,
        (
            "Current ElevenLabs send-path final-confirmation repair checkpoint",
            "`ELEVENLABS-013-send-path-final-confirmation`",
        ),
    )
    assert_text_markers(
        COMMANDS,
        (
            "Validate the ElevenLabs 013 send-path final-confirmation repair without provider calls",
            "python scripts\\validate_elevenlabs_013_send_path_final_confirmation.py",
        ),
    )
    assert_text_markers(
        METHODOLOGY_LOG,
        (
            "ELEVENLABS-013 send-path final-confirmation repair",
            "final send-path clarification",
            "one-line terminal answer",
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
            "ELEVENLABS-013 send-path final confirmation",
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
    assert_condition(len(plan.get("knowledge_base_upload_requests", [])) == 3, "KB upload request count mismatch")
    assert_condition(plan.get("agent_config_patch", {}).get("status") == "ready_for_review", "patch status mismatch")
    patched_prompt = patch["conversation_config"]["agent"]["prompt"]["prompt"]
    assert_condition("## Send-Path Final Confirmation Repair" in patched_prompt, "patched prompt missing repair section")

    print(
        json.dumps(
            {
                "status": "pass",
                "checkpoint_id": CHECKPOINT_ID,
                "live_provider_calls_made": False,
                "production_green_claimed": False,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
