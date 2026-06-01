#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PHASE-4O2-TOOL-READY-FULFILLMENT-MODE-ARCHITECTURE-001"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID

REQUIRED_FILENAMES = [
    "result.json",
    "report.md",
    "00_fulfillment_architecture_overview.md",
    "01_universal_fulfillment_mode_policy.md",
    "02_fulfillment_mode_schema.json",
    "03_tool_state_machine.md",
    "04_campaign_intake_fulfillment_fields.md",
    "05_atlas_manual_followup_adapter.md",
    "06_rendered_atlas_system_prompt_v2.md",
    "07_rendered_atlas_kb_sales_facts_v2.md",
    "08_rendered_atlas_kb_capability_and_tools_v2.md",
    "09_atlas_regression_tests_v2.md",
    "10_upload_manifest_v2.json",
    "11_thesis_relevance_note.md",
]

FULFILLMENT_MODES = [
    "no_fulfillment",
    "interest_capture_only",
    "manual_human_followup_allowed",
    "simulated_manual_followup_for_internal_tests",
    "tool_enabled_email",
    "tool_enabled_calendar",
    "tool_enabled_crm",
    "tool_enabled_payment",
    "live_autonomous_followup",
]

TOOL_STATES = [
    "not_available",
    "planned_future",
    "manual_human_process",
    "configured_disabled",
    "configured_enabled",
    "tool_called_pending",
    "tool_success",
    "tool_failure",
]

TOOL_STATE_FLAGS = [
    "email_tool_state",
    "calendar_tool_state",
    "crm_tool_state",
    "payment_tool_state",
]

DISABLED_FLAGS = [
    "email_tool_enabled",
    "calendar_tool_enabled",
    "crm_tool_enabled",
    "payment_tool_enabled",
]

FALSE_RESULT_FLAGS = [
    "provider_calls_made",
    "elevenlabs_calls_made",
    "openai_api_calls_made",
    "model_calls_made",
    "tts_calls_made",
    "crm_calls_made",
    "email_calls_made",
    "calendar_calls_made",
    "payment_calls_made",
    "account_side_effects_made",
    "live_readiness_claimed",
    "autonomous_live_outbound_enabled",
]

REQUIRED_REGRESSION_CASES = [
    "partner_approval_path",
    "mechanic_outdated_website_trust_path",
    "busy_cafe_owner_micro_close",
    "plumber_emergency_call_value",
    "beauty_salon_instagram_objection",
    "restaurant_no_website",
    "already_strong_website",
    "wrong_person_receptionist",
    "too_expensive_repeated_price_question",
    "guarantee_leads",
    "spam_suspicion",
    "stop_request",
]

ALLOWED_FOLLOWUP_PHRASES = [
    "we can send the mockup over",
    "what email should we use",
    "we'll be in touch",
    "i can call back",
]

FORBIDDEN_COMPLETED_ACTION_CLAIMS = [
    "i just sent it",
    "the email has been sent",
    "the meeting is booked",
    "i updated our crm",
    "payment is processed",
    "the mockup is already created",
]

PRICING_MARKERS = [
    "starter sites around $500-$900",
    "growth sites around $1,000-$2,000",
    "premium or custom work usually $2,000+",
    "$50-$150/month",
]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def read_json(path: Path) -> Any:
    return json.loads(read_text(path))


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def validate_required_files() -> None:
    missing = [filename for filename in REQUIRED_FILENAMES if not (OUT_DIR / filename).is_file()]
    require(not missing, f"missing required files: {', '.join(missing)}")


def validate_fulfillment_modes() -> None:
    combined = normalize(
        "\n".join(
            read_text(OUT_DIR / filename)
            for filename in [
                "00_fulfillment_architecture_overview.md",
                "01_universal_fulfillment_mode_policy.md",
                "02_fulfillment_mode_schema.json",
            ]
        )
    )
    missing = [mode for mode in FULFILLMENT_MODES if mode not in combined]
    require(not missing, f"fulfillment modes missing: {', '.join(missing)}")
    require("manual_human_followup_allowed" in normalize(read_text(OUT_DIR / "05_atlas_manual_followup_adapter.md")), "Atlas adapter must set manual_human_followup_allowed")


def validate_tool_state_machine() -> None:
    text = normalize(read_text(OUT_DIR / "03_tool_state_machine.md"))
    missing = [state for state in TOOL_STATES if state not in text]
    require(not missing, f"tool state machine missing states: {', '.join(missing)}")
    require("completed-action claims require tool_success or confirmed human process" in text, "state machine must bind completed-action claims to tool_success or confirmed human process")
    require("future commitments are allowed in manual_human_process" in text, "state machine must allow future commitments in manual_human_process")


def validate_schema() -> None:
    payload = read_json(OUT_DIR / "02_fulfillment_mode_schema.json")
    require(isinstance(payload, dict), "schema must be a JSON object")
    properties = payload.get("properties")
    require(isinstance(properties, dict), "schema must define properties")
    require(properties.get("fulfillment_mode", {}).get("enum") == FULFILLMENT_MODES, "schema fulfillment_mode enum mismatch")
    tool_states = properties.get("tool_states", {}).get("properties", {})
    require(isinstance(tool_states, dict), "schema must define tool_states properties")
    for tool_name in ["email", "calendar", "crm", "payment"]:
        enum = tool_states.get(tool_name, {}).get("enum")
        require(enum == TOOL_STATES, f"schema tool state enum mismatch: {tool_name}")


def validate_rendered_prompt() -> None:
    prompt = read_text(OUT_DIR / "06_rendered_atlas_system_prompt_v2.md")
    prompt_norm = normalize(prompt)
    require("Atlas Web Studio" in prompt, "rendered prompt must contain Atlas Web Studio")
    require("Emma" in prompt, "rendered prompt must contain Emma")
    require("fulfillment_mode: manual_human_followup_allowed" in prompt, "rendered prompt must name Atlas fulfillment mode")
    require("follow-up language is allowed" in prompt_norm, "prompt must allow follow-up language")
    missing_allowed = [phrase for phrase in ALLOWED_FOLLOWUP_PHRASES if phrase not in prompt_norm]
    require(not missing_allowed, f"prompt missing allowed follow-up phrases: {', '.join(missing_allowed)}")
    missing_forbidden = [phrase for phrase in FORBIDDEN_COMPLETED_ACTION_CLAIMS if phrase not in prompt_norm]
    require(not missing_forbidden, f"prompt missing forbidden completed-action examples: {', '.join(missing_forbidden)}")
    require("completed-action claims require tool_success" in prompt_norm, "prompt must require tool_success before completed-action claims")
    require("do not invent atlas email, phone, url, or address" in prompt_norm, "prompt must forbid invented Atlas contact paths")
    missing_pricing = [marker for marker in PRICING_MARKERS if marker not in prompt_norm]
    require(not missing_pricing, f"prompt missing pricing ranges: {', '.join(missing_pricing)}")
    forbidden_patterns = [r"\bOpenAI\b", r"\bRouteSignal\b", r"\[[^\]\n]+\]"]
    hits = [pattern for pattern in forbidden_patterns if re.search(pattern, prompt, flags=re.IGNORECASE)]
    require(not hits, f"rendered prompt contains forbidden pattern(s): {', '.join(hits)}")


def validate_kb_and_manifest() -> None:
    sales_facts = normalize(read_text(OUT_DIR / "07_rendered_atlas_kb_sales_facts_v2.md"))
    capability = normalize(read_text(OUT_DIR / "08_rendered_atlas_kb_capability_and_tools_v2.md"))
    combined = f"{sales_facts}\n{capability}"
    required = [
        "sales facts",
        "pricing",
        "fulfillment mode",
        "tool readiness",
        "capability boundaries",
        "follow-up language rules",
    ]
    missing = [marker for marker in required if marker not in combined]
    require(not missing, f"rendered KB files missing sections: {', '.join(missing)}")
    manifest = read_json(OUT_DIR / "10_upload_manifest_v2.json")
    require(isinstance(manifest, list), "upload manifest must be a list")
    filenames = {entry.get("filename") for entry in manifest if isinstance(entry, dict)}
    expected = {
        "06_rendered_atlas_system_prompt_v2.md",
        "07_rendered_atlas_kb_sales_facts_v2.md",
        "08_rendered_atlas_kb_capability_and_tools_v2.md",
    }
    require(expected.issubset(filenames), "upload manifest missing prompt or KB files")
    for entry in manifest:
        if isinstance(entry, dict) and entry.get("filename") in expected:
            require(entry.get("side_effects_enabled") is False, f"manifest side effects must be false for {entry.get('filename')}")


def validate_regression_tests() -> int:
    text = read_text(OUT_DIR / "09_atlas_regression_tests_v2.md")
    normalized = normalize(text)
    test_ids = set(re.findall(r"\btest_id:\s*(4O2-ATLAS-\d{2})\b", text))
    require(len(test_ids) >= 12, f"regression tests must include at least 12 tests, found {len(test_ids)}")
    missing_cases = [case for case in REQUIRED_REGRESSION_CASES if case not in normalized]
    require(not missing_cases, f"regression tests missing cases: {', '.join(missing_cases)}")
    require("do not fail merely for future follow-up language when fulfillment_mode is manual_human_followup_allowed" in normalized, "regression tests must not treat allowed future follow-up language as failure")
    for phrase in ALLOWED_FOLLOWUP_PHRASES:
        require(phrase in normalized, f"regression tests missing allowed follow-up phrase: {phrase}")
    failure_markers = [
        "claims an action already happened",
        "invents atlas contact details",
        "guarantees leads",
        "unapproved exact delivery date",
        "ignores stop request",
        "claims tool usage without an enabled tool",
        "processes payment",
    ]
    missing_failures = [marker for marker in failure_markers if marker not in normalized]
    require(not missing_failures, f"regression tests missing failure markers: {', '.join(missing_failures)}")
    return len(test_ids)


def validate_result_json(regression_test_count: int) -> None:
    result = read_json(OUT_DIR / "result.json")
    require(isinstance(result, dict), "result.json must be an object")
    require(result.get("checkpoint_id") == CHECKPOINT_ID, "checkpoint_id mismatch")
    require(result.get("status") == "pass", "status must be pass")
    require(result.get("fulfillment_modes_defined") == FULFILLMENT_MODES, "fulfillment_modes_defined mismatch")
    require(result.get("atlas_fulfillment_mode") == "manual_human_followup_allowed", "atlas fulfillment mode mismatch")
    require(result.get("rendered_prompt_v2_created") is True, "rendered_prompt_v2_created must be true")
    require(result.get("rendered_kb_v2_file_count") == 2, "rendered_kb_v2_file_count must be 2")
    require(result.get("regression_test_count") == regression_test_count, "regression_test_count mismatch")
    for flag in [
        "followup_language_allowed",
        "completed_action_claims_require_tool_success",
        "false_completed_action_claims_forbidden",
        "invented_contact_path_forbidden",
        "pricing_in_system_prompt",
    ]:
        require(result.get(flag) is True, f"{flag} must be true")
    for flag in TOOL_STATE_FLAGS:
        require(result.get(flag) == "planned_future", f"{flag} must be planned_future")
    for flag in DISABLED_FLAGS:
        require(result.get(flag) is False, f"{flag} must be false")
    unsafe = [flag for flag in FALSE_RESULT_FLAGS if result.get(flag) is not False]
    require(not unsafe, f"unsafe result flags must be false: {', '.join(unsafe)}")


def validate_git_diff_check() -> None:
    result = subprocess.run(["git", "diff", "--check"], cwd=ROOT, capture_output=True, text=True, check=False)
    details = "\n".join(part for part in [result.stdout.strip(), result.stderr.strip()] if part)
    require(result.returncode == 0, f"git diff --check failed: {details}")


def main() -> int:
    failures: list[str] = []
    try:
        validate_required_files()
        validate_fulfillment_modes()
        validate_schema()
        validate_tool_state_machine()
        validate_rendered_prompt()
        validate_kb_and_manifest()
        regression_test_count = validate_regression_tests()
        validate_result_json(regression_test_count)
        validate_git_diff_check()
    except Exception as exc:
        failures.append(str(exc))

    if failures:
        print(json.dumps({"status": "fail", "failures": failures}, indent=2, sort_keys=True))
        return 1

    print(json.dumps({"status": "pass", "checkpoint_id": CHECKPOINT_ID}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
