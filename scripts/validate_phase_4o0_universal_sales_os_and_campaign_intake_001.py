#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PHASE-4O0-UNIVERSAL-SALES-OS-AND-CAMPAIGN-INTAKE-001"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID

REQUIRED_FILENAMES = [
    "result.json",
    "report.md",
    "00_architecture_overview.md",
    "01_universal_sales_operating_system.md",
    "02_universal_sales_system_prompt.md",
    "03_universal_sales_principles_kb.md",
    "04_universal_buyer_state_and_emotion_kb.md",
    "05_universal_objection_handling_kb.md",
    "06_universal_persuasion_strategy_kb.md",
    "07_universal_capability_and_side_effect_policy.md",
    "08_campaign_intake_form.md",
    "09_campaign_intake_schema.json",
    "10_campaign_adapter_schema.json",
    "11_campaign_intake_validation_rules.md",
    "12_campaign_adapter_rendering_spec.md",
    "13_minimal_atlas_example_intake.json",
    "14_universal_test_matrix.md",
    "15_thesis_relevance_note.md",
]

UNIVERSAL_FILENAMES = [
    "00_architecture_overview.md",
    "01_universal_sales_operating_system.md",
    "02_universal_sales_system_prompt.md",
    "03_universal_sales_principles_kb.md",
    "04_universal_buyer_state_and_emotion_kb.md",
    "05_universal_objection_handling_kb.md",
    "06_universal_persuasion_strategy_kb.md",
    "07_universal_capability_and_side_effect_policy.md",
    "08_campaign_intake_form.md",
    "09_campaign_intake_schema.json",
    "10_campaign_adapter_schema.json",
    "11_campaign_intake_validation_rules.md",
    "12_campaign_adapter_rendering_spec.md",
    "14_universal_test_matrix.md",
    "15_thesis_relevance_note.md",
]

REQUIRED_INTAKE_FIELDS = [
    "campaign_id",
    "company_name",
    "agent_name",
    "company_description",
    "product_or_service_name",
    "product_category",
    "short_offer_summary",
    "target_customer_segments",
    "buyer_personas",
    "business_pains_solved",
    "business_outcomes_promised_safely",
    "what_product_does",
    "what_product_does_not_do",
    "included_features_or_services",
    "excluded_features_or_services",
    "pricing_model",
    "approved_price_ranges",
    "free_trial_or_demo_policy",
    "guarantees_or_refund_policy",
    "proof_points",
    "case_studies_or_examples",
    "differentiators",
    "competitors_or_alternatives",
    "comparison_rules",
    "qualification_questions",
    "disqualification_rules",
    "common_objections",
    "objection_responses",
    "close_paths",
    "primary_conversion_goal",
    "secondary_conversion_goals",
    "allowed_commitments",
    "forbidden_claims",
    "compliance_constraints",
    "data_privacy_constraints",
    "tool_permissions",
    "unavailable_actions",
    "tone_and_style",
    "escalation_or_handoff_policy",
    "stop_request_policy",
]

REQUIRED_ADAPTER_FIELDS = [
    "normalized_product_facts",
    "approved_claims",
    "forbidden_claims",
    "buyer_personas",
    "pain_to_value_mappings",
    "objection_playbooks",
    "qualification_logic",
    "disqualification_logic",
    "pricing_behavior",
    "close_paths",
    "tool_capability_boundaries",
    "campaign_specific_test_cases",
    "uploadable_kb_files",
    "rendered_system_prompt_fields",
]

REQUIRED_VALIDATION_RULE_IDS = [
    "missing_pricing_policy",
    "missing_target_customer",
    "missing_conversion_goal",
    "missing_disqualification_rules",
    "missing_forbidden_claims",
    "unsupported_guarantees",
    "vague_product_description",
    "unclear_next_step",
    "fake_side_effect_risk",
    "third_party_impersonation_risk",
    "no_compliance_boundary",
    "weak_objection_responses",
    "no_proof_points",
    "no_competitor_alternative_positioning",
    "no_stop_request_policy",
]

FALSE_RESULT_FLAGS = [
    "rendered_runtime_enabled",
    "real_outbound_calls_enabled",
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
]

UNIVERSAL_REQUIRED_PHRASES = [
    "truthful identity",
    "cold-call opening",
    "qualification",
    "discovery",
    "buyer-state detection",
    "emotion-aware adaptation",
    "pain-to-value bridge",
    "consultative persuasion",
    "objection handling",
    "disqualification",
    "micro-close",
    "pricing behavior",
    "capability boundaries",
    "side-effect boundaries",
    "stop-request handling",
    "repeated-question repair",
    "trust repair",
    "call control",
    "no fake guarantees",
    "no fake authority",
    "no pressure after refusal",
    "no bracketed/internal labels",
]

FORBIDDEN_UNIVERSAL_CAMPAIGN_CONTENT = [
    "atlas web studio",
    "local business websites",
    "free homepage mockup",
    "homepage mockup",
    "emma",
]

UNSAFE_LIVE_CLAIM_PATTERNS = [
    r"\bready for live\b",
    r"\blive ready\b",
    r"\blive-ready\b",
    r"\bproduction ready\b",
    r"\breal outbound calls enabled\b",
    r"\bprovider calls made\b",
    r"\belevenlabs calls made\b",
]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def read_json(path: Path) -> Any:
    return json.loads(read_text(path))


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def fail(message: str) -> None:
    raise AssertionError(message)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def schema_properties(filename: str) -> dict[str, Any]:
    payload = read_json(OUT_DIR / filename)
    require(isinstance(payload, dict), f"{filename} must be a JSON object")
    properties = payload.get("properties")
    require(isinstance(properties, dict), f"{filename} must define properties")
    return properties


def validate_required_files() -> None:
    missing = [filename for filename in REQUIRED_FILENAMES if not (OUT_DIR / filename).is_file()]
    require(not missing, f"missing required files: {', '.join(missing)}")


def validate_universal_sales_layer() -> None:
    text = "\n".join(read_text(OUT_DIR / filename) for filename in UNIVERSAL_FILENAMES)
    normalized = normalize(text)
    missing = [phrase for phrase in UNIVERSAL_REQUIRED_PHRASES if phrase not in normalized]
    require(not missing, f"universal sales layer missing phrases: {', '.join(missing)}")


def validate_no_atlas_content_in_universal_files() -> None:
    failures: list[str] = []
    for filename in UNIVERSAL_FILENAMES:
        normalized = normalize(read_text(OUT_DIR / filename))
        for needle in FORBIDDEN_UNIVERSAL_CAMPAIGN_CONTENT:
            if needle in normalized:
                failures.append(f"{filename} contains campaign-specific content: {needle}")
    require(not failures, "; ".join(failures))


def validate_intake_schema() -> int:
    properties = schema_properties("09_campaign_intake_schema.json")
    missing = [field for field in REQUIRED_INTAKE_FIELDS if field not in properties]
    require(not missing, f"intake schema missing fields: {', '.join(missing)}")

    required = read_json(OUT_DIR / "09_campaign_intake_schema.json").get("required")
    require(isinstance(required, list), "intake schema required must be a list")
    missing_required = [field for field in REQUIRED_INTAKE_FIELDS if field not in required]
    require(not missing_required, f"intake schema required list missing fields: {', '.join(missing_required)}")
    return len(properties)


def validate_adapter_schema() -> int:
    properties = schema_properties("10_campaign_adapter_schema.json")
    missing = [field for field in REQUIRED_ADAPTER_FIELDS if field not in properties]
    require(not missing, f"adapter schema missing fields: {', '.join(missing)}")

    required = read_json(OUT_DIR / "10_campaign_adapter_schema.json").get("required")
    require(isinstance(required, list), "adapter schema required must be a list")
    missing_required = [field for field in REQUIRED_ADAPTER_FIELDS if field not in required]
    require(not missing_required, f"adapter schema required list missing fields: {', '.join(missing_required)}")
    return len(properties)


def validate_intake_validation_rules() -> int:
    text = read_text(OUT_DIR / "11_campaign_intake_validation_rules.md")
    missing = [rule_id for rule_id in REQUIRED_VALIDATION_RULE_IDS if rule_id not in text]
    require(not missing, f"validation rules missing ids: {', '.join(missing)}")
    severities = set(re.findall(r"severity:\s*(blocker|warning|optional)", text))
    require({"blocker", "warning", "optional"}.issubset(severities), "rules must include blocker, warning, and optional severities")
    return len(REQUIRED_VALIDATION_RULE_IDS)


def validate_atlas_example() -> None:
    payload = read_json(OUT_DIR / "13_minimal_atlas_example_intake.json")
    require(isinstance(payload, dict), "Atlas example must be an object")
    require(payload.get("company_name") == "Atlas Web Studio", "Atlas company_name mismatch")
    require(payload.get("agent_name") == "Emma", "Atlas agent_name mismatch")
    require(payload.get("product_category") == "local business websites", "Atlas product_category mismatch")
    require(payload.get("primary_conversion_goal") == "free homepage mockup/demo permission", "Atlas primary_conversion_goal mismatch")
    missing = [field for field in REQUIRED_INTAKE_FIELDS if field not in payload]
    require(not missing, f"Atlas example missing intake fields: {', '.join(missing)}")
    require(payload.get("real_outbound_calls_enabled") is False, "Atlas example must keep real_outbound_calls_enabled false")
    require(payload.get("tools_enabled") == [], "Atlas example must not enable tools")


def validate_universal_tests() -> int:
    text = read_text(OUT_DIR / "14_universal_test_matrix.md")
    test_ids = set(re.findall(r"\btest_id:\s*(4O0-UT-\d{2})\b", text))
    require(len(test_ids) >= 15, f"universal test matrix must include at least 15 tests, found {len(test_ids)}")

    required_markers = [
        "universal_failure_type:",
        "scenario:",
        "expected behavior:",
        "pass/fail criteria:",
        "relevant EASID fields:",
    ]
    missing = [marker for marker in required_markers if marker not in text]
    require(not missing, f"universal tests missing markers: {', '.join(missing)}")
    return len(test_ids)


def validate_result_json(intake_field_count: int, adapter_field_count: int, rule_count: int, test_count: int) -> None:
    result = read_json(OUT_DIR / "result.json")
    require(isinstance(result, dict), "result.json must be an object")
    require(result.get("checkpoint_id") == CHECKPOINT_ID, "checkpoint_id mismatch")
    require(result.get("status") == "pass", "status must be pass")
    require(result.get("universal_sales_layer_defined") is True, "universal_sales_layer_defined must be true")
    require(result.get("campaign_intake_schema_defined") is True, "campaign_intake_schema_defined must be true")
    require(result.get("campaign_adapter_schema_defined") is True, "campaign_adapter_schema_defined must be true")
    require(result.get("intake_validation_rule_count") == rule_count, "intake_validation_rule_count mismatch")
    require(result.get("universal_test_count") == test_count, "universal_test_count mismatch")
    require(result.get("intake_field_count") == intake_field_count, "intake_field_count mismatch")
    require(result.get("adapter_schema_field_count") == adapter_field_count, "adapter_schema_field_count mismatch")
    require(result.get("atlas_example_created") is True, "atlas_example_created must be true")

    unsafe = [flag for flag in FALSE_RESULT_FLAGS if result.get(flag) is not False]
    require(not unsafe, f"unsafe result flags must be false: {', '.join(unsafe)}")


def validate_no_live_readiness_claim() -> None:
    combined = "\n".join(read_text(OUT_DIR / filename) for filename in REQUIRED_FILENAMES)
    normalized = normalize(combined)
    hits = [pattern for pattern in UNSAFE_LIVE_CLAIM_PATTERNS if re.search(pattern, normalized)]
    require(not hits, f"unsafe live/provider claim pattern found: {', '.join(hits)}")


def validate_git_diff_check() -> None:
    result = subprocess.run(["git", "diff", "--check"], cwd=ROOT, capture_output=True, text=True, check=False)
    details = "\n".join(part for part in [result.stdout.strip(), result.stderr.strip()] if part)
    require(result.returncode == 0, f"git diff --check failed: {details}")


def main() -> int:
    failures: list[str] = []
    try:
        validate_required_files()
        validate_universal_sales_layer()
        validate_no_atlas_content_in_universal_files()
        intake_field_count = validate_intake_schema()
        adapter_field_count = validate_adapter_schema()
        rule_count = validate_intake_validation_rules()
        validate_atlas_example()
        test_count = validate_universal_tests()
        validate_result_json(intake_field_count, adapter_field_count, rule_count, test_count)
        validate_no_live_readiness_claim()
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
