#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

CHECKPOINT_ID = "UNIVERSAL-SALES-KNOWLEDGE-001"
GENERATED_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
RESULT_PATH = GENERATED_DIR / "result.json"
REPORT_PATH = GENERATED_DIR / "report.md"

REQUIRED_TOP_LEVEL_FIELDS = {
    "knowledge_id",
    "schema_version",
    "sales_stages",
    "buyer_move_families",
    "qualification_dimensions",
    "generic_pain_dimensions",
    "objection_families",
    "safe_next_action_policies",
    "call_control_policy",
    "regulated_vertical_cautions",
}

REQUIRED_SALES_STAGES = {
    "opening",
    "permission",
    "discovery",
    "qualification",
    "value_mapping",
    "objection_or_resistance",
    "send_info",
    "callback_scheduling",
    "appointment_setting",
    "right_person_handoff",
    "refusal_or_stop",
    "close_or_end",
}

REQUIRED_BUYER_MOVE_FAMILIES = {
    "permission_acknowledgement",
    "social_acknowledgement",
    "low_information_continue",
    "current_issue_clear",
    "all_clear_or_no_pain",
    "pain_confirmed",
    "possible_pain_unclear",
    "confusion_or_term_question",
    "objection",
    "timing_deferral",
    "send_info_request",
    "callback_request",
    "appointment_acceptance",
    "appointment_hesitation",
    "appointment_time_given",
    "wrong_person_or_authority_unclear",
    "refusal_not_interested",
    "stop_request",
}

REQUIRED_QUALIFICATION_DIMENSIONS = {
    "need_or_pain",
    "urgency",
    "authority_or_right_person",
    "fit",
    "current_solution_or_status_quo",
    "budget_or_price_sensitivity",
    "timing",
    "contact_path",
    "compliance_or_risk_constraints",
}

REQUIRED_GENERIC_PAIN_DIMENSIONS = {
    "missed_follow_up",
    "delay",
    "ownership_confusion",
    "manual_work",
    "duplicate_work",
    "visibility_gap",
    "customer_experience_friction",
    "trust_or_risk_concern",
    "cost_or_time_waste",
    "unclear_next_step",
}

REQUIRED_OBJECTION_FAMILIES = {
    "no_need_or_all_set",
    "not_relevant",
    "not_interested",
    "timing",
    "price",
    "authority",
    "existing_vendor_or_process",
    "trust",
    "privacy_or_security",
    "complexity",
    "send_info_first",
    "stop_or_do_not_contact",
}

REQUIRED_SAFE_NEXT_ACTION_POLICIES = {
    "ask_next_diagnostic_if_current_issue_clear",
    "clarify_if_confused",
    "do_not_push_appointment_on_confusion",
    "do_not_push_appointment_on_no_pain",
    "bridge_to_appointment_after_credible_pain_or_interest",
    "capture_send_info_contact_without_pretending_appointment",
    "capture_callback_time_before_schedule_and_end",
    "route_wrong_person_toward_right_contact_or_polite_close",
    "end_on_explicit_stop_request",
    "preserve_buyer_agency",
    "avoid_unverified_claims",
}

REQUIRED_CALL_CONTROL_IDS = {
    "continue-call",
    "schedule-and-end",
    "end-call",
    "transfer-or-escalate",
}

REQUIRED_REGULATED_CAUTIONS = {
    "insurance",
    "healthcare_admin_or_medical_equipment",
    "financial_or_payment_sensitive",
    "legal_or_contract_sensitive",
    "telecom_contract_or_coverage",
    "home_services_safety_or_estimate",
    "automotive_service_safety_or_warranty",
    "membership_or_subscription_cancellation",
    "retail_or_ecommerce_refund_warranty_availability",
}

FORBIDDEN_CAMPAIGN_TERMS = [
    "RouteSignal",
    "Northstar",
    "Starter",
    "Growth",
    "demo lead",
    "inbound demo",
    "workflow review with Northstar",
    "$29",
    "$59",
]


def assert_condition(failures: list[str], condition: bool, message: str) -> None:
    if not condition:
        failures.append(message)


def validate_record_fields(
    failures: list[str],
    records: dict[str, Any],
    required_ids: set[str],
    required_fields: set[str],
    label: str,
) -> None:
    assert_condition(failures, required_ids.issubset(records), f"{label}: missing ids {sorted(required_ids - set(records))}")
    for item_id in sorted(required_ids):
        record = records.get(item_id)
        assert_condition(failures, isinstance(record, dict), f"{label}.{item_id}: record must be a dict")
        if not isinstance(record, dict):
            continue
        for field in sorted(required_fields):
            assert_condition(failures, bool(record.get(field)), f"{label}.{item_id}.{field}: must be populated")


def module_source_text() -> str:
    return (ROOT / "runtime" / "core" / "universal_sales_knowledge.py").read_text(encoding="utf-8")


def write_evidence(result: dict[str, Any], report: str) -> None:
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    REPORT_PATH.write_text(report, encoding="utf-8")


def build_report(result: dict[str, Any]) -> str:
    status = "pass" if result["status"] == "pass" else "fail"
    lines = [
        "# UNIVERSAL-SALES-KNOWLEDGE-001",
        "",
        f"Status: {status}",
        "",
        "## Contract",
        "",
        "- Product-agnostic universal sales stages, buyer moves, qualification dimensions, pain dimensions, objections, next-action policies, call-control rules, and regulated-vertical cautions.",
        "- No runtime routing integration in this phase.",
        "- No RouteSignal migration in this phase.",
        "",
        "## Forbidden Campaign Terms",
        "",
        f"- Forbidden term check passed: {str(result['forbidden_campaign_terms_check']['passed']).lower()}",
        f"- Forbidden terms found in module: {', '.join(result['forbidden_campaign_terms_check']['found_terms']) if result['forbidden_campaign_terms_check']['found_terms'] else 'none'}",
        "",
        "## Safety",
        "",
        f"- provider_calls_made: {str(result['safety']['provider_calls_made']).lower()}",
        f"- local_llm_calls_made: {str(result['safety']['local_llm_calls_made']).lower()}",
        f"- sends_email: {str(result['safety']['sends_email']).lower()}",
        f"- creates_calendar_event: {str(result['safety']['creates_calendar_event']).lower()}",
        f"- writes_crm: {str(result['safety']['writes_crm']).lower()}",
        f"- opens_prod_102: {str(result['safety']['opens_prod_102']).lower()}",
        "",
        "## Counts",
        "",
    ]
    for key, value in result["counts"].items():
        lines.append(f"- {key}: {value}")
    if result["failures"]:
        lines.extend(["", "## Failures", ""])
        for failure in result["failures"]:
            lines.append(f"- {failure}")
    return "\n".join(lines) + "\n"


def main() -> int:
    failures: list[str] = []
    evidence: dict[str, Any] = {
        "status": "fail",
        "checkpoint_id": CHECKPOINT_ID,
        "runtime_behavior_changed": False,
        "response_text_changed": False,
        "provider_calls_made": False,
        "local_llm_calls_made": False,
        "sends_email": False,
        "creates_calendar_event": False,
        "writes_crm": False,
        "opens_prod_102": False,
    }
    try:
        from runtime.core import universal_sales_knowledge as knowledge  # noqa: WPS433
    except Exception as exc:  # pragma: no cover - exercised in red validation before module exists
        failures.append(f"module import failed: {exc!r}")
        result = {
            "status": "fail",
            "checkpoint_id": CHECKPOINT_ID,
            "failures": failures,
            "counts": {},
            "forbidden_campaign_terms_check": {"passed": False, "found_terms": []},
            "safety": {
                "provider_calls_made": False,
                "local_llm_calls_made": False,
                "sends_email": False,
                "creates_calendar_event": False,
                "writes_crm": False,
                "opens_prod_102": False,
            },
            "evidence": evidence,
        }
        write_evidence(result, build_report(result))
        print(json.dumps(result, indent=2, sort_keys=True))
        return 1

    sales_knowledge = knowledge.UNIVERSAL_SALES_KNOWLEDGE
    assert_condition(failures, isinstance(sales_knowledge, dict), "UNIVERSAL_SALES_KNOWLEDGE must be a dict")
    assert_condition(
        failures,
        REQUIRED_TOP_LEVEL_FIELDS.issubset(sales_knowledge),
        f"missing top-level fields {sorted(REQUIRED_TOP_LEVEL_FIELDS - set(sales_knowledge))}",
    )
    assert_condition(
        failures,
        knowledge.universal_knowledge_id() == "UNIVERSAL-SALES-KNOWLEDGE-001",
        "universal_knowledge_id() must return UNIVERSAL-SALES-KNOWLEDGE-001",
    )

    validate_record_fields(
        failures,
        sales_knowledge.get("sales_stages") or {},
        REQUIRED_SALES_STAGES,
        {"description", "allowed_next_actions", "blocked_actions", "call_control_defaults"},
        "sales_stages",
    )
    validate_record_fields(
        failures,
        sales_knowledge.get("buyer_move_families") or {},
        REQUIRED_BUYER_MOVE_FAMILIES,
        {
            "description",
            "typical_contexts",
            "safe_interpretation_rule",
            "unsafe_interpretation_examples",
            "recommended_next_action",
        },
        "buyer_move_families",
    )
    validate_record_fields(
        failures,
        sales_knowledge.get("qualification_dimensions") or {},
        REQUIRED_QUALIFICATION_DIMENSIONS,
        {"purpose", "positive_evidence_shape", "negative_evidence_shape", "safe_next_action"},
        "qualification_dimensions",
    )
    validate_record_fields(
        failures,
        sales_knowledge.get("generic_pain_dimensions") or {},
        REQUIRED_GENERIC_PAIN_DIMENSIONS,
        {
            "definition",
            "causal_story",
            "example_customer_language_generic",
            "what_counts_as_clear_or_no_pain",
            "possible_next_diagnostic_dimensions",
            "appointment_bridge_principle",
        },
        "generic_pain_dimensions",
    )
    validate_record_fields(
        failures,
        sales_knowledge.get("objection_families") or {},
        REQUIRED_OBJECTION_FAMILIES,
        {"interpretation", "safe_response_principle", "when_to_continue", "when_to_end", "escalation_or_handoff_rule"},
        "objection_families",
    )
    validate_record_fields(
        failures,
        sales_knowledge.get("safe_next_action_policies") or {},
        REQUIRED_SAFE_NEXT_ACTION_POLICIES,
        {"description", "allowed_when", "blocked_when", "implementation_rule"},
        "safe_next_action_policies",
    )
    validate_record_fields(
        failures,
        sales_knowledge.get("call_control_policy") or {},
        REQUIRED_CALL_CONTROL_IDS,
        {"allowed_when", "blocked_when", "examples_generic", "side_effects_allowed_false_by_default"},
        "call_control_policy",
    )
    validate_record_fields(
        failures,
        sales_knowledge.get("regulated_vertical_cautions") or {},
        REQUIRED_REGULATED_CAUTIONS,
        {"blocked_claims", "human_escalation_triggers", "safe_language_principle"},
        "regulated_vertical_cautions",
    )

    helper_checks = {
        "sales_stage": knowledge.sales_stage("opening"),
        "buyer_move_family": knowledge.buyer_move_family("pain_confirmed"),
        "qualification_dimension": knowledge.qualification_dimension("need_or_pain"),
        "generic_pain_dimension": knowledge.generic_pain_dimension("missed_follow_up"),
        "objection_family": knowledge.objection_family("not_interested"),
        "safe_next_action_policy": knowledge.safe_next_action_policy("avoid_unverified_claims"),
        "call_control_rule": knowledge.call_control_rule("continue-call"),
        "regulated_caution": knowledge.regulated_caution("insurance"),
    }
    for helper, record in helper_checks.items():
        assert_condition(failures, isinstance(record, dict) and bool(record), f"{helper} helper must return a populated record")

    id_helper_checks = {
        "all_sales_stage_ids": (set(knowledge.all_sales_stage_ids()), REQUIRED_SALES_STAGES),
        "all_buyer_move_family_ids": (set(knowledge.all_buyer_move_family_ids()), REQUIRED_BUYER_MOVE_FAMILIES),
        "all_qualification_dimension_ids": (set(knowledge.all_qualification_dimension_ids()), REQUIRED_QUALIFICATION_DIMENSIONS),
        "all_generic_pain_dimension_ids": (set(knowledge.all_generic_pain_dimension_ids()), REQUIRED_GENERIC_PAIN_DIMENSIONS),
        "all_objection_family_ids": (set(knowledge.all_objection_family_ids()), REQUIRED_OBJECTION_FAMILIES),
        "all_safe_next_action_policy_ids": (set(knowledge.all_safe_next_action_policy_ids()), REQUIRED_SAFE_NEXT_ACTION_POLICIES),
        "all_call_control_ids": (set(knowledge.all_call_control_ids()), REQUIRED_CALL_CONTROL_IDS),
        "all_regulated_caution_ids": (set(knowledge.all_regulated_caution_ids()), REQUIRED_REGULATED_CAUTIONS),
    }
    for helper, (actual, required) in id_helper_checks.items():
        assert_condition(failures, required.issubset(actual), f"{helper} missing ids {sorted(required - actual)}")

    validation_result = knowledge.validate_universal_sales_knowledge()
    assert_condition(failures, isinstance(validation_result, dict), "validate_universal_sales_knowledge() must return a dict")
    assert_condition(failures, validation_result.get("valid") is True, f"validate_universal_sales_knowledge() failed: {validation_result}")

    source_text = module_source_text()
    found_forbidden_terms = [term for term in FORBIDDEN_CAMPAIGN_TERMS if term.lower() in source_text.lower()]
    assert_condition(
        failures,
        not found_forbidden_terms,
        f"module source contains forbidden campaign/product terms: {found_forbidden_terms}",
    )

    safety = {
        "provider_calls_made": False,
        "local_llm_calls_made": False,
        "sends_email": False,
        "creates_calendar_event": False,
        "writes_crm": False,
        "opens_prod_102": False,
    }
    counts = {
        "sales_stages": len(knowledge.all_sales_stage_ids()),
        "buyer_move_families": len(knowledge.all_buyer_move_family_ids()),
        "qualification_dimensions": len(knowledge.all_qualification_dimension_ids()),
        "generic_pain_dimensions": len(knowledge.all_generic_pain_dimension_ids()),
        "objection_families": len(knowledge.all_objection_family_ids()),
        "safe_next_action_policies": len(knowledge.all_safe_next_action_policy_ids()),
        "call_control_rules": len(knowledge.all_call_control_ids()),
        "regulated_vertical_cautions": len(knowledge.all_regulated_caution_ids()),
    }
    result = {
        "status": "pass" if not failures else "fail",
        "checkpoint_id": CHECKPOINT_ID,
        "knowledge_id": knowledge.universal_knowledge_id(),
        "schema_version": sales_knowledge.get("schema_version"),
        "runtime_behavior_changed": False,
        "response_text_changed": False,
        "phase_1_2_3_backpatch_required": False,
        "top_level_fields": sorted(sales_knowledge.keys()),
        "counts": counts,
        "required_ids": {
            "sales_stages": sorted(REQUIRED_SALES_STAGES),
            "buyer_move_families": sorted(REQUIRED_BUYER_MOVE_FAMILIES),
            "qualification_dimensions": sorted(REQUIRED_QUALIFICATION_DIMENSIONS),
            "generic_pain_dimensions": sorted(REQUIRED_GENERIC_PAIN_DIMENSIONS),
            "objection_families": sorted(REQUIRED_OBJECTION_FAMILIES),
            "safe_next_action_policies": sorted(REQUIRED_SAFE_NEXT_ACTION_POLICIES),
            "call_control_policy": sorted(REQUIRED_CALL_CONTROL_IDS),
            "regulated_vertical_cautions": sorted(REQUIRED_REGULATED_CAUTIONS),
        },
        "forbidden_campaign_terms_check": {
            "passed": not found_forbidden_terms,
            "found_terms": found_forbidden_terms,
            "checked_terms": FORBIDDEN_CAMPAIGN_TERMS,
        },
        "safety": safety,
        "helper_functions_checked": sorted(helper_checks.keys()) + sorted(id_helper_checks.keys()) + ["validate_universal_sales_knowledge"],
        "generated_evidence": {
            "result_json": str(RESULT_PATH.relative_to(ROOT)),
            "report_md": str(REPORT_PATH.relative_to(ROOT)),
        },
        "failures": failures,
    }
    write_evidence(result, build_report(result))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
