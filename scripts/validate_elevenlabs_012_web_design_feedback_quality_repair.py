#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "ELEVENLABS-012-web-design-feedback-quality-repair"
RUNNER = ROOT / "scripts" / "run_elevenlabs_agent_automation.py"
MANIFEST = (
    ROOT
    / "runtime"
    / "providers"
    / "elevenlabs_agents"
    / "manifests"
    / "web_design_feedback_quality_repair.package.json"
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
DYNAMIC_DEFAULTS = (
    ROOT
    / "runtime"
    / "providers"
    / "elevenlabs_agents"
    / "variables"
    / "mikes_kitchen_dynamic_variable_defaults.json"
)
DOC = ROOT / "docs" / "product" / "ELEVENLABS_012_WEB_DESIGN_FEEDBACK_QUALITY_REPAIR.md"
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
    assert_condition(manifest.get("provider") == "elevenlabs", "manifest provider mismatch")
    assert_condition(manifest.get("source_of_truth") == "repo", "manifest source_of_truth mismatch")
    assert_condition(manifest.get("live_provider_calls_made") is False, "012 manifest must stay offline-default")
    assert_condition(
        manifest.get("knowledge_base_docs")
        == [
            "runtime/providers/elevenlabs_agents/knowledge_base/universal_sales_core.md",
            "runtime/providers/elevenlabs_agents/knowledge_base/atlas_web_studio_web_design_campaign_overlay.md",
            "runtime/providers/elevenlabs_agents/knowledge_base/atlas_web_studio_web_design_campaign_profile.md",
        ],
        "manifest KB docs must preserve universal, overlay, profile order",
    )
    basis = manifest.get("repair_basis", {})
    assert_condition(basis.get("live_rerun_required_for_green") is True, "live rerun gate missing")
    assert_condition(
        basis.get("human_feedback_categories")
        == [
            "repetition_failure_from_same_value_angle",
            "assurance_first_for_free_no_strings",
            "send_path_sign_up_assurance",
            "busy_pressure_brevity",
            "direct_catch_answering",
        ],
        "human feedback categories mismatch",
    )

    prompt_text = assert_text_markers(
        PROMPT,
        (
            "## Feedback Quality Repair",
            "First-sentence pressure matching",
            "Do not lead with `That's fair` when the buyer asks `what's the catch`",
            "There isn't a catch, really.",
            "It is completely free to review.",
            "No, you are not being signed up for anything.",
            "Do not write fake `haha`, `[laughing]`, or scripted chuckle",
            "Busy-pressure brevity",
            "Yes, I can call back. Would tomorrow morning work?",
            "Value-angle exclusivity",
            "Do not treat `organized details`, `clear path`, `key information`, `faster first impression`, and `one place` as distinct value angles.",
            "If two value angles do not soften the buyer, switch to proof-before-purchase or stop.",
            "one shareable link across Instagram bio, Google profile, texts, emails, QR codes, and print",
        ),
    )
    assert_condition("[laughing]" not in prompt_text.replace("`[laughing]`", ""), "prompt uses unsafe laughing tag outside the ban")

    assert_text_markers(
        CAMPAIGN_OVERLAY,
        (
            "`ELEVENLABS-012-web-design-feedback-quality-repair`",
            "## Feedback Quality Repair Overlay",
            "assurance-first wording",
            "There isn't a catch, really.",
            "It is completely free to review.",
            "No, you are not being signed up for anything.",
            "Busy-pressure brevity",
            "Named value-angle rotation",
            "one shareable link across Instagram bio, Google profile, texts, emails, QR codes, and print",
        ),
    )
    assert_text_markers(
        CAMPAIGN_PROFILE,
        (
            "`ELEVENLABS-012-web-design-feedback-quality-repair`",
            "## Approved Assurance Facts",
            "The mockup is completely free to review.",
            "There is no obligation and no sign-up when the buyer receives the mockup link.",
            "The buyer is not being signed up for a paid project by receiving the mockup link.",
            "The buyer can ignore the mockup if it is not useful.",
        ),
    )
    assert_text_markers(
        DOC,
        (
            "does not make a live provider call",
            "human feedback from the latest simulation screenshots",
            "first-sentence pressure matching",
            "value-angle exclusivity",
            "no literal fake laughter",
            "python scripts\\validate_elevenlabs_012_web_design_feedback_quality_repair.py",
        ),
    )
    assert_text_markers(
        INDEX,
        (
            "Current ElevenLabs feedback-quality repair checkpoint",
            "`ELEVENLABS-012-web-design-feedback-quality-repair`",
        ),
    )
    assert_text_markers(
        COMMANDS,
        (
            "Validate the ElevenLabs 012 feedback-quality repair without provider calls",
            "python scripts\\validate_elevenlabs_012_web_design_feedback_quality_repair.py",
        ),
    )
    assert_text_markers(
        METHODOLOGY_LOG,
        (
            "ELEVENLABS-012 feedback-quality repair package",
            "first-sentence pressure matching",
            "value-angle exclusivity",
            "no literal fake laughter",
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
            "ELEVENLABS-012 web design feedback quality repair",
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
    assert_condition(plan.get("test_create_requests") == [], "012 patch package should not create tests")
    assert_condition(plan.get("agent_config_patch", {}).get("status") == "ready_for_review", "patch status mismatch")

    patched_prompt = patch["conversation_config"]["agent"]["prompt"]["prompt"]
    for marker in (
        "## Feedback Quality Repair",
        "First-sentence pressure matching",
        "Value-angle exclusivity",
    ):
        assert_condition(marker in patched_prompt, f"patched prompt missing marker: {marker}")
    patched_kb_names = [item.get("name") for item in patch["conversation_config"]["agent"]["prompt"]["knowledge_base"]]
    assert_condition(
        patched_kb_names
        == [
            "universal_sales_core.md",
            "atlas_web_studio_web_design_campaign_overlay.md",
            "atlas_web_studio_web_design_campaign_profile.md",
        ],
        "patched KB order mismatch",
    )

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
