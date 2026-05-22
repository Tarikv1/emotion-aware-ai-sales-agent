#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.core import campaign_playbook_adapter as adapter  # noqa: E402
from runtime.core import sales_diagnostic_playbook as routesignal  # noqa: E402
from runtime.core import universal_sales_knowledge as universal  # noqa: E402
from runtime.core import vertical_sales_playbooks as verticals  # noqa: E402


CHECKPOINT_ID = "CAMPAIGN-PLAYBOOK-ADAPTER-002-cross-vertical-smoke"
GENERATED_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
RESULT_PATH = GENERATED_DIR / "result.json"
REPORT_PATH = GENERATED_DIR / "report.md"

ROUTESIGNAL_PLAYBOOK_ID = "ROUTESIGNAL-DIAGNOSTIC-PLAYBOOK-001"
FORBIDDEN_ROUTESIGNAL_TEXT = ["RouteSignal", "Northstar", "Starter", "Growth", "$29", "$59"]
REQUIRED_TOP_LEVEL_FIELDS = {
    "adapter_id",
    "campaign_id",
    "vertical_id",
    "universal_knowledge_id",
    "campaign_playbook_id",
    "campaign_context",
    "diagnostic_gaps",
    "core_diagnostic_gaps",
    "gap_order",
    "safety",
}
REQUIRED_GAP_FIELDS = {
    "campaign_gap_id",
    "label",
    "universal_pain_dimensions",
    "qualification_dimensions",
    "definition",
    "causal_story",
    "customer_language",
    "evidence_positive",
    "evidence_negative",
    "diagnostic_questions",
    "value_bridge",
    "review_focus",
    "next_gap_candidates",
}
SAFETY_KEYS = [
    "provider_calls_made",
    "local_llm_calls_made",
    "sends_email",
    "creates_calendar_event",
    "writes_crm",
    "opens_prod_102",
]


def gap(
    gap_id: str,
    label: str,
    pains: list[str],
    qualifications: list[str],
    next_gap_candidates: list[str],
) -> dict[str, Any]:
    return {
        "label": label,
        "universal_pain_dimensions": pains,
        "qualification_dimensions": qualifications,
        "definition": f"Determine whether {label} is a real current sales or support constraint.",
        "causal_story": f"If {label} is unresolved, the buyer may need a qualified human review before choosing the next step.",
        "customer_language": [label.replace("_", " "), f"question about {label.replace('_', ' ')}"],
        "evidence_positive": [f"{label.replace('_', ' ')} is a problem", f"we need help with {label.replace('_', ' ')}"],
        "evidence_negative": [f"{label.replace('_', ' ')} is handled", f"no issue with {label.replace('_', ' ')}"],
        "diagnostic_questions": [f"Is {label.replace('_', ' ')} the main thing a human should review?"],
        "value_bridge": f"The useful next step is a human review of {label.replace('_', ' ')} without making unsupported claims.",
        "review_focus": label,
        "next_gap_candidates": next_gap_candidates,
    }


def campaign(
    *,
    campaign_id: str,
    client_name: str,
    offer: str,
    vertical_id: str,
    human_owner: str,
    appointment_target: str,
    allowed_claims: list[str],
    blocked_claims: list[str],
    gaps: dict[str, dict[str, Any]],
    expected_cautions: list[str],
) -> dict[str, Any]:
    order = list(gaps)
    return {
        "campaign_id": campaign_id,
        "client_name": client_name,
        "product_or_offer_name": offer,
        "vertical_id": vertical_id,
        "objective": "appointment_setting",
        "human_followup_owner": human_owner,
        "appointment_target": appointment_target,
        "allowed_claims": allowed_claims,
        "blocked_claims": blocked_claims,
        "diagnostic_gaps": gaps,
        "core_diagnostic_gaps": order[:3],
        "gap_order": order,
        "expected_regulated_cautions": expected_cautions,
    }


def synthetic_campaigns() -> list[dict[str, Any]]:
    return [
        campaign(
            campaign_id="synthetic-b2b-saas-001",
            client_name="Synthetic SaaS Operations",
            offer="Workflow Fit Review",
            vertical_id="b2b_saas",
            human_owner="technical fit specialist",
            appointment_target="human fit and technical review",
            allowed_claims=["can discuss workflow fit at a general level"],
            blocked_claims=["integration guarantee", "security certification guarantee", "ROI guarantee"],
            expected_cautions=["legal_or_contract_sensitive", "financial_or_payment_sensitive"],
            gaps={
                "manual_work": gap("manual_work", "manual work", ["manual_work", "cost_or_time_waste"], ["need_or_pain", "current_solution_or_status_quo", "fit"], ["integration_risk"]),
                "integration_risk": gap("integration_risk", "integration risk", ["trust_or_risk_concern", "unclear_next_step"], ["fit", "compliance_or_risk_constraints"], ["visibility_gap"]),
                "visibility_gap": gap("visibility_gap", "visibility gap", ["visibility_gap", "unclear_next_step"], ["need_or_pain", "authority_or_right_person", "fit"], []),
            },
        ),
        campaign(
            campaign_id="synthetic-insurance-001",
            client_name="Synthetic Insurance Agency",
            offer="Policy Review Call",
            vertical_id="insurance",
            human_owner="licensed insurance specialist",
            appointment_target="licensed coverage review",
            allowed_claims=["can collect general review needs"],
            blocked_claims=["coverage guarantee", "premium savings guarantee", "eligibility decision", "claim outcome promise"],
            expected_cautions=["insurance"],
            gaps={
                "coverage_fit": gap("coverage_fit", "coverage fit", ["trust_or_risk_concern", "unclear_next_step"], ["need_or_pain", "fit", "compliance_or_risk_constraints"], ["premium_or_budget"]),
                "premium_or_budget": gap("premium_or_budget", "premium or budget", ["cost_or_time_waste", "trust_or_risk_concern"], ["budget_or_price_sensitivity", "fit"], ["renewal_or_timing"]),
                "renewal_or_timing": gap("renewal_or_timing", "renewal or timing", ["delay", "unclear_next_step"], ["timing", "urgency", "contact_path"], []),
            },
        ),
        campaign(
            campaign_id="synthetic-telecom-001",
            client_name="Synthetic Telecom Provider",
            offer="Plan Review Call",
            vertical_id="telecom",
            human_owner="telecom account specialist",
            appointment_target="human plan and availability review",
            allowed_claims=["can discuss plan fit generally"],
            blocked_claims=["coverage guarantee", "speed guarantee", "contract cancellation guarantee"],
            expected_cautions=["telecom_contract_or_coverage"],
            gaps={
                "coverage_or_availability": gap("coverage_or_availability", "coverage or availability", ["trust_or_risk_concern", "delay"], ["fit", "compliance_or_risk_constraints"], ["plan_fit"]),
                "plan_fit": gap("plan_fit", "plan fit", ["customer_experience_friction", "cost_or_time_waste"], ["need_or_pain", "fit", "budget_or_price_sensitivity"], ["contract_or_switching"]),
                "contract_or_switching": gap("contract_or_switching", "contract or switching", ["unclear_next_step", "trust_or_risk_concern"], ["timing", "contact_path", "compliance_or_risk_constraints"], []),
            },
        ),
        campaign(
            campaign_id="synthetic-home-services-001",
            client_name="Synthetic Home Services",
            offer="Inspection Scheduling Call",
            vertical_id="home_services",
            human_owner="qualified service coordinator",
            appointment_target="inspection or estimate review",
            allowed_claims=["can collect scheduling and property context"],
            blocked_claims=["exact quote without inspection", "safety diagnosis without inspection"],
            expected_cautions=["home_services_safety_or_estimate"],
            gaps={
                "service_need": gap("service_need", "service need", ["customer_experience_friction", "unclear_next_step"], ["need_or_pain", "fit"], ["scheduling_urgency"]),
                "scheduling_urgency": gap("scheduling_urgency", "scheduling urgency", ["delay", "trust_or_risk_concern"], ["urgency", "timing", "contact_path"], ["estimate_or_property_details"]),
                "estimate_or_property_details": gap("estimate_or_property_details", "estimate or property details", ["trust_or_risk_concern", "unclear_next_step"], ["fit", "compliance_or_risk_constraints"], []),
            },
        ),
        campaign(
            campaign_id="synthetic-healthcare-admin-001",
            client_name="Synthetic Healthcare Admin",
            offer="Specialist Review Call",
            vertical_id="healthcare_admin_or_medical_equipment",
            human_owner="qualified healthcare admin specialist",
            appointment_target="specialist human review",
            allowed_claims=["can collect admin workflow or equipment review needs"],
            blocked_claims=["diagnosis", "medical advice", "guaranteed outcome", "eligibility promise"],
            expected_cautions=["healthcare_admin_or_medical_equipment"],
            gaps={
                "admin_workflow_need": gap("admin_workflow_need", "admin workflow need", ["manual_work", "delay", "visibility_gap"], ["need_or_pain", "authority_or_right_person", "fit"], ["equipment_or_service_fit"]),
                "equipment_or_service_fit": gap("equipment_or_service_fit", "equipment or service fit", ["trust_or_risk_concern", "unclear_next_step"], ["fit", "compliance_or_risk_constraints"], ["specialist_review_needed"]),
                "specialist_review_needed": gap("specialist_review_needed", "specialist review needed", ["unclear_next_step", "trust_or_risk_concern"], ["contact_path", "authority_or_right_person"], []),
            },
        ),
        campaign(
            campaign_id="synthetic-automotive-service-001",
            client_name="Synthetic Automotive Service",
            offer="Service Advisor Review",
            vertical_id="automotive_service",
            human_owner="service advisor",
            appointment_target="service advisor inspection review",
            allowed_claims=["can collect vehicle issue and timing context"],
            blocked_claims=["exact diagnosis", "guaranteed repair cost", "warranty guarantee"],
            expected_cautions=["automotive_service_safety_or_warranty"],
            gaps={
                "vehicle_issue": gap("vehicle_issue", "vehicle issue", ["trust_or_risk_concern", "unclear_next_step"], ["need_or_pain", "fit"], ["repair_timing"]),
                "repair_timing": gap("repair_timing", "repair timing", ["delay", "cost_or_time_waste"], ["urgency", "timing", "contact_path"], ["warranty_or_estimate"]),
                "warranty_or_estimate": gap("warranty_or_estimate", "warranty or estimate", ["trust_or_risk_concern", "cost_or_time_waste"], ["budget_or_price_sensitivity", "compliance_or_risk_constraints"], []),
            },
        ),
        campaign(
            campaign_id="synthetic-membership-001",
            client_name="Synthetic Membership Program",
            offer="Plan Support Call",
            vertical_id="membership_or_subscription",
            human_owner="account support specialist",
            appointment_target="account support or plan-fit review",
            allowed_claims=["can discuss plan fit and support options generally"],
            blocked_claims=["misleading cancellation claim", "misleading renewal claim", "unverified refund claim"],
            expected_cautions=["membership_or_subscription_cancellation"],
            gaps={
                "plan_fit": gap("plan_fit", "plan fit", ["customer_experience_friction", "cost_or_time_waste"], ["need_or_pain", "fit", "budget_or_price_sensitivity"], ["renewal_or_cancellation"]),
                "renewal_or_cancellation": gap("renewal_or_cancellation", "renewal or cancellation", ["trust_or_risk_concern", "unclear_next_step"], ["timing", "contact_path", "compliance_or_risk_constraints"], ["usage_or_value"]),
                "usage_or_value": gap("usage_or_value", "usage or value", ["cost_or_time_waste", "customer_experience_friction"], ["need_or_pain", "current_solution_or_status_quo", "fit"], []),
            },
        ),
        campaign(
            campaign_id="synthetic-retail-support-001",
            client_name="Synthetic Retail Support",
            offer="Product Support Call",
            vertical_id="retail_or_ecommerce_support_sales",
            human_owner="support specialist",
            appointment_target="product or order support review",
            allowed_claims=["can collect product fit or support context"],
            blocked_claims=["false stock promise", "delivery promise", "refund promise", "warranty promise"],
            expected_cautions=["retail_or_ecommerce_refund_warranty_availability"],
            gaps={
                "product_fit": gap("product_fit", "product fit", ["customer_experience_friction", "unclear_next_step"], ["need_or_pain", "fit", "budget_or_price_sensitivity"], ["availability_or_delivery"]),
                "availability_or_delivery": gap("availability_or_delivery", "availability or delivery", ["delay", "trust_or_risk_concern"], ["timing", "contact_path", "compliance_or_risk_constraints"], ["return_or_warranty"]),
                "return_or_warranty": gap("return_or_warranty", "return or warranty", ["trust_or_risk_concern", "unclear_next_step"], ["contact_path", "compliance_or_risk_constraints"], []),
            },
        ),
    ]


def assert_condition(failures: list[str], condition: bool, message: str) -> None:
    if not condition:
        failures.append(message)


def contains_any_forbidden_routesignal_text(value: Any) -> list[str]:
    text = json.dumps(value, sort_keys=True)
    return [item for item in FORBIDDEN_ROUTESIGNAL_TEXT if item in text]


def validate_synthetic_campaign(campaign_config: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    failures: list[str] = []
    playbook = adapter.resolve_campaign_playbook(campaign_config)
    validation = adapter.validate_campaign_playbook(playbook)

    campaign_id = str(campaign_config["campaign_id"])
    vertical_id = str(campaign_config["vertical_id"])
    expected_cautions = list(campaign_config["expected_regulated_cautions"])
    expected_gap_order = list(campaign_config["gap_order"])

    assert_condition(failures, validation.get("valid") is True, f"{campaign_id}: adapter validation failed: {validation}")
    assert_condition(failures, playbook.get("campaign_id") == campaign_id, f"{campaign_id}: campaign_id mismatch")
    assert_condition(failures, playbook.get("vertical_id") == vertical_id, f"{campaign_id}: vertical_id mismatch")
    assert_condition(failures, playbook.get("campaign_playbook_id") != ROUTESIGNAL_PLAYBOOK_ID, f"{campaign_id}: returned RouteSignal playbook")
    assert_condition(failures, vertical_id in verticals.all_vertical_ids(), f"{campaign_id}: vertical missing from vertical playbooks")
    assert_condition(failures, set(REQUIRED_TOP_LEVEL_FIELDS).issubset(set(playbook)), f"{campaign_id}: missing top-level fields")
    assert_condition(failures, playbook.get("gap_order") == expected_gap_order, f"{campaign_id}: gap_order mismatch")
    assert_condition(failures, playbook.get("core_diagnostic_gaps") == expected_gap_order[:3], f"{campaign_id}: core gaps mismatch")
    assert_condition(failures, set(playbook.get("diagnostic_gaps") or {}) == set(expected_gap_order), f"{campaign_id}: diagnostic gaps mismatch")

    forbidden = contains_any_forbidden_routesignal_text(playbook)
    assert_condition(failures, not forbidden, f"{campaign_id}: RouteSignal-only text leaked into synthetic playbook: {forbidden}")

    context = playbook.get("campaign_context") or {}
    cautions = set(playbook.get("regulated_cautions") or context.get("regulated_cautions") or [])
    assert_condition(failures, set(expected_cautions).issubset(cautions), f"{campaign_id}: expected cautions missing: {expected_cautions}, got {sorted(cautions)}")
    blocked_claims = " ".join(str(item).lower() for item in context.get("blocked_claims") or [])
    for expected in campaign_config.get("blocked_claims") or []:
        assert_condition(failures, str(expected).lower() in blocked_claims, f"{campaign_id}: blocked claim missing: {expected}")

    safety = playbook.get("safety") or {}
    for key in SAFETY_KEYS:
        assert_condition(failures, safety.get(key) is False, f"{campaign_id}: safety.{key} must be false")

    pain_ids = set(universal.all_generic_pain_dimension_ids())
    qualification_ids = set(universal.all_qualification_dimension_ids())
    for gap_id, gap_record in (playbook.get("diagnostic_gaps") or {}).items():
        missing_fields = sorted(
            field
            for field in REQUIRED_GAP_FIELDS - {"next_gap_candidates"}
            if gap_record.get(field) in (None, "", [])
        )
        assert_condition(failures, not missing_fields, f"{campaign_id}.{gap_id}: missing gap fields {missing_fields}")
        assert_condition(
            failures,
            "next_gap_candidates" in gap_record and isinstance(gap_record.get("next_gap_candidates"), list),
            f"{campaign_id}.{gap_id}: next_gap_candidates must be present as a list",
        )
        assert_condition(failures, gap_record.get("campaign_gap_id") == gap_id, f"{campaign_id}.{gap_id}: campaign_gap_id mismatch")
        unknown_pains = sorted(set(gap_record.get("universal_pain_dimensions") or []) - pain_ids)
        unknown_qualifications = sorted(set(gap_record.get("qualification_dimensions") or []) - qualification_ids)
        assert_condition(failures, not unknown_pains, f"{campaign_id}.{gap_id}: unknown universal pain dimensions {unknown_pains}")
        assert_condition(failures, not unknown_qualifications, f"{campaign_id}.{gap_id}: unknown qualification dimensions {unknown_qualifications}")

    return playbook, failures


def validate_vertical_expectations(results: dict[str, dict[str, Any]], failures: list[str]) -> None:
    def blocked(campaign_id: str) -> str:
        return " ".join(str(item).lower() for item in (((results[campaign_id].get("campaign_context") or {}).get("blocked_claims")) or []))

    assert_condition(failures, "human fit and technical review" in (results["synthetic-b2b-saas-001"].get("campaign_context") or {}).get("appointment_target", ""), "b2b_saas: appointment target missing human technical review")
    for token in ["integration", "security", "roi"]:
        assert_condition(failures, token in blocked("synthetic-b2b-saas-001"), f"b2b_saas: blocked claims missing {token}")

    assert_condition(failures, "insurance" in (results["synthetic-insurance-001"].get("regulated_cautions") or []), "insurance: regulated caution missing")
    for token in ["coverage", "premium", "eligibility", "claim"]:
        assert_condition(failures, token in blocked("synthetic-insurance-001"), f"insurance: blocked claims missing {token}")
    insurance_target = (results["synthetic-insurance-001"].get("campaign_context") or {}).get("appointment_target", "").lower()
    assert_condition(failures, "licensed" in insurance_target and "review" in insurance_target, "insurance: appointment target must require licensed human review")

    expected_caution_by_campaign = {
        "synthetic-telecom-001": "telecom_contract_or_coverage",
        "synthetic-home-services-001": "home_services_safety_or_estimate",
        "synthetic-healthcare-admin-001": "healthcare_admin_or_medical_equipment",
        "synthetic-automotive-service-001": "automotive_service_safety_or_warranty",
        "synthetic-membership-001": "membership_or_subscription_cancellation",
        "synthetic-retail-support-001": "retail_or_ecommerce_refund_warranty_availability",
    }
    for campaign_id, caution_id in expected_caution_by_campaign.items():
        assert_condition(failures, caution_id in (results[campaign_id].get("regulated_cautions") or []), f"{campaign_id}: regulated caution missing {caution_id}")

    for token in ["coverage", "speed", "contract"]:
        assert_condition(failures, token in blocked("synthetic-telecom-001"), f"telecom: blocked claims missing {token}")
    for token in ["exact quote", "safety diagnosis"]:
        assert_condition(failures, token in blocked("synthetic-home-services-001"), f"home_services: blocked claims missing {token}")
    for token in ["diagnosis", "medical advice", "guaranteed outcome", "eligibility"]:
        assert_condition(failures, token in blocked("synthetic-healthcare-admin-001"), f"healthcare: blocked claims missing {token}")
    for token in ["exact diagnosis", "guaranteed repair cost", "warranty"]:
        assert_condition(failures, token in blocked("synthetic-automotive-service-001"), f"automotive: blocked claims missing {token}")
    for token in ["misleading cancellation", "misleading renewal"]:
        assert_condition(failures, token in blocked("synthetic-membership-001"), f"membership: blocked claims missing {token}")
    for token in ["false stock", "delivery", "refund", "warranty"]:
        assert_condition(failures, token in blocked("synthetic-retail-support-001"), f"retail: blocked claims missing {token}")


def validate_routesignal_preservation(failures: list[str]) -> dict[str, Any]:
    default_playbook = adapter.resolve_campaign_playbook(None)
    live_campaign_playbook = adapter.resolve_campaign_playbook({"campaign_id": adapter.DEFAULT_CAMPAIGN_ID})
    assert_condition(failures, default_playbook.get("campaign_playbook_id") == ROUTESIGNAL_PLAYBOOK_ID, "RouteSignal default campaign_playbook_id changed")
    assert_condition(failures, live_campaign_playbook.get("campaign_playbook_id") == ROUTESIGNAL_PLAYBOOK_ID, "RouteSignal live campaign id changed")
    assert_condition(failures, adapter.campaign_gap_labels(None) == routesignal.gap_labels(), "RouteSignal gap labels changed")
    assert_condition(failures, adapter.campaign_core_diagnostic_gaps(None) == routesignal.core_diagnostic_gaps(), "RouteSignal core gaps changed")
    assert_condition(failures, adapter.campaign_gap_order(None) == routesignal.gap_ids(), "RouteSignal gap order changed")
    for gap_id in routesignal.gap_ids():
        assert_condition(failures, adapter.campaign_gap_definition(gap_id).get("review_focus") == routesignal.review_focus(gap_id), f"RouteSignal review focus changed for {gap_id}")
    adapter_validation = adapter.validate_campaign_playbook_adapter()
    assert_condition(failures, adapter_validation.get("valid") is True, f"RouteSignal adapter validation failed: {adapter_validation}")
    return {
        "default_campaign_playbook_id": default_playbook.get("campaign_playbook_id"),
        "live_campaign_playbook_id": live_campaign_playbook.get("campaign_playbook_id"),
        "gap_order": adapter.campaign_gap_order(None),
        "core_diagnostic_gaps": adapter.campaign_core_diagnostic_gaps(None),
        "validator_valid": adapter_validation.get("valid") is True,
    }


def write_evidence(result: dict[str, Any], report: str) -> None:
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    REPORT_PATH.write_text(report, encoding="utf-8")


def build_report(result: dict[str, Any]) -> str:
    lines = [
        "# CAMPAIGN-PLAYBOOK-ADAPTER-002 Cross-Vertical Smoke",
        "",
        f"Status: {result['status']}",
        "",
        "## Synthetic Campaigns",
        "",
    ]
    for campaign_id, snapshot in sorted((result.get("campaigns") or {}).items()):
        lines.append(
            f"- {campaign_id}: vertical={snapshot.get('vertical_id')}, "
            f"playbook={snapshot.get('campaign_playbook_id')}, gaps={', '.join(snapshot.get('gap_order') or [])}, "
            f"cautions={', '.join(snapshot.get('regulated_cautions') or [])}"
        )
    lines.extend(["", "## RouteSignal Preservation", ""])
    route = result.get("routesignal_preservation") or {}
    lines.append(f"- Default playbook id: {route.get('default_campaign_playbook_id')}")
    lines.append(f"- Live campaign playbook id: {route.get('live_campaign_playbook_id')}")
    lines.append(f"- 4B3 behavior validator still valid: {str(route.get('validator_valid')).lower()}")
    lines.extend(["", "## Safety", ""])
    for key, value in sorted((result.get("safety") or {}).items()):
        lines.append(f"- {key}: {str(value).lower()}")
    if result.get("failures"):
        lines.extend(["", "## Failures", ""])
        for failure in result["failures"]:
            lines.append(f"- {failure}")
    return "\n".join(lines) + "\n"


def main() -> int:
    failures: list[str] = []
    campaign_results: dict[str, dict[str, Any]] = {}

    for campaign_config in synthetic_campaigns():
        playbook, campaign_failures = validate_synthetic_campaign(campaign_config)
        failures.extend(campaign_failures)
        campaign_results[str(campaign_config["campaign_id"])] = {
            "campaign_id": playbook.get("campaign_id"),
            "vertical_id": playbook.get("vertical_id"),
            "campaign_playbook_id": playbook.get("campaign_playbook_id"),
            "campaign_context": playbook.get("campaign_context"),
            "diagnostic_gaps": playbook.get("diagnostic_gaps"),
            "core_diagnostic_gaps": playbook.get("core_diagnostic_gaps"),
            "gap_order": playbook.get("gap_order"),
            "regulated_cautions": playbook.get("regulated_cautions"),
            "safety": playbook.get("safety"),
        }

    validate_vertical_expectations(campaign_results, failures)
    routesignal_preservation = validate_routesignal_preservation(failures)

    safety = {key: False for key in SAFETY_KEYS}
    result = {
        "status": "pass" if not failures else "fail",
        "checkpoint_id": CHECKPOINT_ID,
        "synthetic_campaign_count": len(campaign_results),
        "verticals_covered": sorted({str(item.get("vertical_id")) for item in campaign_results.values()}),
        "campaigns": campaign_results,
        "routesignal_preservation": routesignal_preservation,
        "phase_1_2_3_backpatch_required": False,
        "runtime_behavior_changed": False,
        "safety": safety,
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
