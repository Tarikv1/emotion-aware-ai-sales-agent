#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "ELEVENLABS-010-web-design-sales-control-repair"
RUNNER = ROOT / "scripts" / "run_elevenlabs_agent_automation.py"
MANIFEST = (
    ROOT
    / "runtime"
    / "providers"
    / "elevenlabs_agents"
    / "manifests"
    / "web_design_sales_control_repair.package.json"
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
SIMULATION_TESTS = (
    ROOT
    / "runtime"
    / "providers"
    / "elevenlabs_agents"
    / "tests"
    / "web_design_mikes_kitchen_simulation_tests.json"
)
DOC = ROOT / "docs" / "product" / "ELEVENLABS_010_WEB_DESIGN_SALES_CONTROL_REPAIR.md"
RESULT_SUMMARY = (
    ROOT
    / "research"
    / "experiments"
    / "generated"
    / CHECKPOINT_ID
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
    for path in (RUNNER, MANIFEST, FIXTURE, UNIVERSAL_KB, CAMPAIGN_KB, PROMPT, FIRST_MESSAGE, DYNAMIC_DEFAULTS, SIMULATION_TESTS, DOC):
        assert_condition(path.is_file(), f"Missing file: {path.relative_to(ROOT)}")

    sys.path.insert(0, str(ROOT))
    from runtime.providers.elevenlabs_agents.automation import merge_knowledge_base_entries

    merged = merge_knowledge_base_entries(
        [
            {"type": "file", "name": "universal_sales_core.md", "id": "old_universal"},
            {"type": "file", "name": "keep_campaign.md", "id": "keep_campaign"},
        ],
        [
            {"type": "file", "name": "universal_sales_core.md", "id": "new_universal"},
        ],
    )
    assert_condition(
        merged == [
            {"type": "file", "name": "keep_campaign.md", "id": "keep_campaign"},
            {"type": "file", "name": "universal_sales_core.md", "id": "new_universal"},
        ],
        f"same-name KB replacement failed: {merged}",
    )

    manifest = read_json(MANIFEST)
    assert_condition(manifest.get("package_id") == CHECKPOINT_ID, "manifest package_id mismatch")
    assert_condition(len(manifest.get("knowledge_base_docs", [])) == 2, "manifest should upload two KB docs")
    assert_condition(manifest.get("baseline_tests") == [], "010 patch package should not own the 009 simulation test IDs")
    assert_condition(manifest.get("upload_intent", {}).get("replace_same_name_attached_kb_docs") is True, "replace intent missing")
    simulation_pack = read_json(SIMULATION_TESTS)
    simulation_tests = simulation_pack.get("tests")
    assert_condition(isinstance(simulation_tests, list) and len(simulation_tests) == 9, "simulation pack should contain nine tests")
    serialized_tests = json.dumps(simulation_pack, ensure_ascii=False)
    for marker in (
        "optional_booking_future_scope",
        "unapproved or nonsensical bracketed delivery tags",
        "repeats the same review/send/quick-look ask",
        "reachable turn to respond",
        "asks the gatekeeper what the call is regarding",
        "$10-$30/month",
    ):
        assert_condition(marker in serialized_tests, f"simulation pack missing marker: {marker}")

    universal_text = UNIVERSAL_KB.read_text(encoding="utf-8")
    campaign_text = CAMPAIGN_KB.read_text(encoding="utf-8")
    prompt_text = PROMPT.read_text(encoding="utf-8")
    defaults = read_json(DYNAMIC_DEFAULTS)

    for marker in (
        "do not repeat the same review or demo ask",
        "Campaign Value Handling",
        "Sales Rhythm",
        "Upsell Discipline",
        "Ethical persuasion means truthful relevance",
    ):
        assert_condition(marker in universal_text, f"universal KB missing marker: {marker}")
    for marker in (
        "Local Restaurant Website Value",
        "Google Maps And Instagram Boundary",
        "Online Booking And Upsell Boundary",
        "Simple website projects generally start around `$1,000`",
        "Basic hosting for a small business website is usually around `$10-$30/month`",
    ):
        assert_condition(marker in campaign_text, f"campaign KB missing marker: {marker}")
    for marker in (
        "Do not output bracketed delivery tags as normal customer-visible text",
        "Do not keep asking the same close.",
        "If the buyer says they are not interested",
        "so you will pitch me later",
        "website_hosting_monthly_ballpark",
        "Website-need question",
        "Optional booking upsell",
        "Gatekeeper role boundary",
        "Google or Instagram defense forbidden wording",
        "Plain-language ban",
    ):
        assert_condition(marker in prompt_text, f"prompt missing marker: {marker}")
    for key in ("website_campaign_value_points", "optional_upsell_boundary", "website_hosting_monthly_ballpark"):
        assert_condition(isinstance(defaults.get(key), str) and defaults[key].strip(), f"dynamic default missing {key}")

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
            "ELEVENLABS-010 web design sales control repair",
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
    assert_condition(plan.get("test_create_requests") == [], "010 patch package should not create tests")
    assert_condition(plan.get("agent_config_patch", {}).get("status") == "ready_for_review", "patch status mismatch")

    prompt = patch["conversation_config"]["agent"]["prompt"]
    kb_entries = prompt.get("knowledge_base", [])
    assert_condition(
        kb_entries == [
            {
                "type": "file",
                "name": "universal_sales_core.md",
                "id": "kbdoc_validation_universal_sales_core",
            },
            {
                "type": "file",
                "name": "atlas_web_studio_web_design_campaign.md",
                "id": "kbdoc_validation_atlas_web_studio_web_design_campaign",
            },
        ],
        f"patch KB entries mismatch: {kb_entries}",
    )
    assert_condition(prompt["rag"]["enabled"] is True, "RAG should be enabled")
    assert_condition(prompt["temperature"] == 0.25, "temperature mismatch")
    assert_condition("Do not keep asking the same close." in prompt["prompt"], "patched prompt missing sales rhythm")
    assert_condition("Basic hosting is usually around" in prompt["prompt"], "patched prompt missing hosting disclosure")

    result_summary = read_json(RESULT_SUMMARY)
    assert_no_secret_leak(result_summary)
    assert_condition(result_summary.get("checkpoint_id") == CHECKPOINT_ID, "result summary checkpoint mismatch")
    assert_condition(str(result_summary.get("repaired_simulation_folder_id", "")).startswith("tfld_"), "folder id mismatch")
    assert_condition(str(result_summary.get("repaired_simulation_suite", "")).startswith("suite_"), "suite id mismatch")
    passed_count = int(result_summary.get("passed_count", -1))
    failed_count = int(result_summary.get("failed_count", -1))
    pending_count = int(result_summary.get("pending_count", -1))
    assert_condition(passed_count + failed_count + pending_count == 9, "result counts do not add up")
    if failed_count:
        assert_condition(result_summary.get("production_green") is False, "failed result must not be production-green")
        remaining = result_summary.get("remaining_failure_modes")
        assert_condition(
            isinstance(remaining, list) and len(remaining) == failed_count,
            "remaining failure modes mismatch",
        )

    doc_text = DOC.read_text(encoding="utf-8")
    for marker in (
        CHECKPOINT_ID,
        "human-reviewed simulation repair",
        "atlas_web_studio_web_design_campaign.md",
        "same-name KB replacement",
        "unapproved bracketed delivery tags",
    ):
        assert_condition(marker in doc_text, f"Doc missing marker: {marker}")

    print(
        json.dumps(
            {
                "status": "pass",
                "checkpoint_id": CHECKPOINT_ID,
                "kb_docs": len(plan.get("knowledge_base_upload_requests", [])),
                "owned_test_create_requests": len(plan.get("test_create_requests", [])),
                "simulation_pack_tests": len(simulation_tests),
                "live_provider_calls_made": False,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
