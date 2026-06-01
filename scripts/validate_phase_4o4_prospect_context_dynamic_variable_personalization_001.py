#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PHASE-4O4-PROSPECT-CONTEXT-DYNAMIC-VARIABLE-CALL-PERSONALIZATION-001"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID

REQUIRED_FILENAMES = [
    "result.json",
    "report.md",
    "00_context_layer_overview.md",
    "01_prospect_context_schema.json",
    "02_prospect_context_intake_form.md",
    "03_dynamic_variable_reference.md",
    "04_rendered_atlas_system_prompt_v4.md",
    "05_rendered_atlas_first_message_templates_v4.md",
    "06_rendered_atlas_kb_prospect_context_rules_v4.md",
    "07_example_prospect_records.jsonl",
    "08_context_aware_regression_tests_v4.md",
    "09_upload_manifest_v4_patch.json",
    "10_thesis_relevance_note.md",
]

REQUIRED_SCHEMA_FIELDS = [
    "prospect_id",
    "business_name",
    "business_type",
    "vertical",
    "city",
    "service_area",
    "known_website_url",
    "known_website_status",
    "known_social_presence",
    "known_booking_or_ordering_path",
    "known_phone_or_contact_path",
    "suspected_gap",
    "primary_offer_angle",
    "likely_decision_maker_role",
    "contact_name_if_known",
    "call_reason",
    "proof_or_observation_source",
    "data_confidence",
    "do_not_claim_as_fact_fields",
    "allowed_personalization_fields",
    "forbidden_personalization_claims",
    "followup_preference_if_known",
    "notes",
]

REQUIRED_DYNAMIC_VARIABLES = [
    "{{business_name}}",
    "{{business_type}}",
    "{{vertical}}",
    "{{city}}",
    "{{service_area}}",
    "{{known_website_status}}",
    "{{known_social_presence}}",
    "{{known_booking_or_ordering_path}}",
    "{{suspected_gap}}",
    "{{primary_offer_angle}}",
    "{{likely_decision_maker_role}}",
    "{{contact_name_if_known}}",
    "{{call_reason}}",
]

REQUIRED_TEMPLATE_MARKERS = [
    "Am I speaking with the owner or someone who helps with the website for {{business_name}}?",
    "I had {{business_name}} down as a {{business_type}} in {{city}}.",
    "Is this {{contact_name_if_known}} from {{business_name}}?",
    "I had {{business_name}} down as already having a website",
    "I had {{business_name}} down as mostly using {{known_social_presence}} rather than a full website.",
]

REQUIRED_REGRESSION_TESTS = [
    "known_business_name_opening",
    "known_vertical_opening",
    "existing_website_opening",
    "social_only_opening",
    "buyer_corrects_wrong_context",
    "decision_maker_gatekeeper",
    "already_strong_website_disqualification",
    "price_objection_with_known_business",
    "bad_prior_agency_with_known_business",
    "partner_approval_with_known_business",
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
    "autonomous_live_outbound_enabled",
    "live_readiness_claimed",
    "old_kb_reattachment_allowed",
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


def validate_schema() -> int:
    payload = read_json(OUT_DIR / "01_prospect_context_schema.json")
    require(isinstance(payload, dict), "schema must be a JSON object")
    properties = payload.get("properties")
    require(isinstance(properties, dict), "schema must define properties")
    missing = [field for field in REQUIRED_SCHEMA_FIELDS if field not in properties]
    require(not missing, f"schema missing fields: {', '.join(missing)}")
    required = payload.get("required")
    require(isinstance(required, list), "schema required must be a list")
    missing_required = [field for field in REQUIRED_SCHEMA_FIELDS if field not in required]
    require(not missing_required, f"schema required list missing fields: {', '.join(missing_required)}")
    return len(properties)


def validate_dynamic_variables() -> int:
    combined = "\n".join(
        read_text(OUT_DIR / filename)
        for filename in [
            "03_dynamic_variable_reference.md",
            "05_rendered_atlas_first_message_templates_v4.md",
        ]
    )
    missing = [variable for variable in REQUIRED_DYNAMIC_VARIABLES if variable not in combined]
    require(not missing, f"missing dynamic variables: {', '.join(missing)}")
    return len(REQUIRED_DYNAMIC_VARIABLES)


def validate_prompt() -> None:
    prompt = read_text(OUT_DIR / "04_rendered_atlas_system_prompt_v4.md")
    normalized = normalize(prompt)
    required = [
        "emma from atlas web studio",
        "cold outreach",
        "free homepage mockup",
        "use prospect context naturally",
        "confirm the business or decision-maker first",
        "do not ask for the business name if business_name is already known",
        "do not ask what kind of business it is if vertical or business_type is already known",
        "ask only for missing details needed for the mockup",
        "do not claim you inspected the website unless inspected_website is true",
        "do not invent lead data",
        "follow-up language is allowed",
        "do not say something has already been sent, booked, created, updated, or paid unless it has actually happened",
        "typical atlas ranges are: starter sites around $500-$900",
        "stop immediately",
        "no fake guarantees",
        "do not invent atlas email, phone, website, office address, or calendar link",
    ]
    missing = [marker for marker in required if marker not in normalized]
    require(not missing, f"prompt missing markers: {', '.join(missing)}")


def validate_templates() -> int:
    text = read_text(OUT_DIR / "05_rendered_atlas_first_message_templates_v4.md")
    missing = [marker for marker in REQUIRED_TEMPLATE_MARKERS if marker not in text]
    require(not missing, f"first-message templates missing markers: {', '.join(missing)}")
    template_count = len(re.findall(r"^## Template \d+", text, flags=re.MULTILINE))
    require(template_count >= 5, f"must include at least 5 first-message templates, found {template_count}")
    return template_count


def validate_examples() -> int:
    path = OUT_DIR / "07_example_prospect_records.jsonl"
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(read_text(path).splitlines(), start=1):
        if not line.strip():
            continue
        payload = json.loads(line)
        require(isinstance(payload, dict), f"example record line {line_number} must be an object")
        records.append(payload)
    require(len(records) >= 8, f"must include at least 8 example prospect records, found {len(records)}")
    missing_fields: list[str] = []
    for index, record in enumerate(records, start=1):
        for field in REQUIRED_SCHEMA_FIELDS:
            if field not in record:
                missing_fields.append(f"record {index}: {field}")
    require(not missing_fields, f"example records missing fields: {', '.join(missing_fields[:10])}")
    return len(records)


def validate_regression_tests() -> int:
    text = read_text(OUT_DIR / "08_context_aware_regression_tests_v4.md")
    normalized = normalize(text)
    test_ids = set(re.findall(r"\btest_id:\s*(4O4-CTX-\d{2})\b", text))
    require(len(test_ids) >= 10, f"must include at least 10 context-aware tests, found {len(test_ids)}")
    missing_tests = [test for test in REQUIRED_REGRESSION_TESTS if test not in normalized]
    require(not missing_tests, f"missing context-aware tests: {', '.join(missing_tests)}")
    required_failures = [
        "asks for business name when business_name was provided",
        "asks for business type when vertical was provided",
        "claims to have inspected site without context support",
        "ignores correction",
        "invents lead data",
        "guarantees outcomes",
        "ignores stop request",
    ]
    missing_failures = [marker for marker in required_failures if marker not in normalized]
    require(not missing_failures, f"regression tests missing failure markers: {', '.join(missing_failures)}")
    return len(test_ids)


def validate_kb() -> None:
    text = read_text(OUT_DIR / "06_rendered_atlas_kb_prospect_context_rules_v4.md")
    normalized = normalize(text)
    required = [
        "known context vs uncertain context",
        "confirm decision-maker",
        "handle corrections",
        "avoid sounding creepy",
        "avoid pretending deep research",
        "transition from context confirmation into the mockup offer",
        "got it, thanks for correcting me",
    ]
    missing = [marker for marker in required if marker not in normalized]
    require(not missing, f"prospect context KB missing markers: {', '.join(missing)}")


def validate_manifest() -> None:
    payload = read_json(OUT_DIR / "09_upload_manifest_v4_patch.json")
    require(isinstance(payload, dict), "upload manifest patch must be an object")
    active = payload.get("active_atlas_agent_should_use")
    require(isinstance(active, list), "manifest patch must list active attachments")
    filenames = {entry.get("filename") for entry in active if isinstance(entry, dict)}
    required = {
        "04_rendered_atlas_system_prompt_v4.md",
        "06_rendered_atlas_kb_prospect_context_rules_v4.md",
        "02_rendered_atlas_kb_sales_facts_v3.md",
        "03_rendered_atlas_kb_capability_boundaries_v3.md",
        "01_rendered_atlas_kb_trust_repair_risk_reversal_v3.md",
    }
    missing = sorted(required - filenames)
    require(not missing, f"manifest missing active attachments: {', '.join(missing)}")
    require(payload.get("do_not_attach_old_non_v3_kb_files") is True, "manifest must say not to attach old non-v3 KB files")


def validate_result_json(
    field_count: int,
    variable_count: int,
    template_count: int,
    record_count: int,
    test_count: int,
) -> None:
    result = read_json(OUT_DIR / "result.json")
    require(isinstance(result, dict), "result.json must be an object")
    require(result.get("checkpoint_id") == CHECKPOINT_ID, "checkpoint_id mismatch")
    require(result.get("status") == "pass", "status must be pass")
    require(result.get("prospect_context_schema_created") is True, "prospect_context_schema_created must be true")
    require(result.get("prospect_context_field_count") == field_count, "prospect_context_field_count mismatch")
    require(result.get("dynamic_variable_count") == variable_count, "dynamic_variable_count mismatch")
    require(result.get("rendered_prompt_v4_created") is True, "rendered_prompt_v4_created must be true")
    require(result.get("first_message_template_count") == template_count, "first_message_template_count mismatch")
    require(result.get("example_prospect_record_count") == record_count, "example_prospect_record_count mismatch")
    require(result.get("context_aware_regression_test_count") == test_count, "context_aware_regression_test_count mismatch")
    for flag in [
        "asks_business_name_when_known_forbidden",
        "asks_vertical_when_known_forbidden",
        "false_pre_call_research_claims_forbidden",
        "invented_lead_data_forbidden",
        "followup_language_allowed",
        "false_completed_action_claims_forbidden",
    ]:
        require(result.get(flag) is True, f"{flag} must be true")
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
        field_count = validate_schema()
        variable_count = validate_dynamic_variables()
        validate_prompt()
        template_count = validate_templates()
        validate_kb()
        record_count = validate_examples()
        test_count = validate_regression_tests()
        validate_manifest()
        validate_result_json(field_count, variable_count, template_count, record_count, test_count)
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
