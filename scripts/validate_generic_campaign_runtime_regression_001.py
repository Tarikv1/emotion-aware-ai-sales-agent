#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.entrypoints import generic_campaign_turn  # noqa: E402
from scripts.validate_generic_campaign_runtime_entrypoint_001 import (  # noqa: E402
    FORBIDDEN_BRAND_TERMS,
    FORBIDDEN_ROUTE_PHRASES,
    RAW_EMAILS,
    append_turn,
    assert_common_packet,
    assert_condition,
    assert_semantic,
    base_campaign,
    final_response,
    gap,
    memory,
    normalize,
    sanitize,
    semantic_frame,
    snapshot,
    validate_invalid_campaign,
    validate_routesignal_preservation,
)


CHECKPOINT_ID = "GENERIC-CAMPAIGN-RUNTIME-REGRESSION-001"
GENERATED_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
RESULT_PATH = GENERATED_DIR / "result.json"
REPORT_PATH = GENERATED_DIR / "report.md"
TMP_DIR = ROOT / ".tmp" / CHECKPOINT_ID

ROUTESIGNAL_PLAYBOOK_ID = "ROUTESIGNAL-DIAGNOSTIC-PLAYBOOK-001"
SAFETY_KEYS = [
    "provider_calls_made",
    "local_llm_calls_made",
    "sends_email",
    "creates_calendar_event",
    "writes_crm",
    "opens_prod_102",
]


def write_evidence(result: dict[str, Any], report: str) -> None:
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    REPORT_PATH.write_text(report, encoding="utf-8")


def g(
    gap_id: str,
    label: str,
    *,
    review_focus: str,
    language: list[str],
    positive: list[str],
    negative: list[str],
    next_gaps: list[str],
    pain: list[str],
    qual: list[str],
) -> dict[str, Any]:
    return gap(
        gap_id,
        label,
        review_focus=review_focus,
        customer_language=language,
        positive=positive,
        negative=negative,
        next_gap_candidates=next_gaps,
        universal=pain,
        qualifications=qual,
    )


def synthetic_campaigns() -> dict[str, dict[str, Any]]:
    common_claims = ["can collect sales qualification context and schedule a human review"]
    return {
        "b2b_saas": base_campaign(
            campaign_id="synthetic-b2b-saas-regression-001",
            client_name="Synthetic SaaS Operations",
            offer="Operations Workflow Review",
            vertical_id="b2b_saas",
            human_owner="implementation specialist",
            appointment_target="operations fit review",
            extra={
                "allowed_claims": common_claims,
                "blocked_claims": ["integration guarantee", "security guarantee", "ROI guarantee"],
                "product_category": "operations workflow software",
                "approved_feature_claims": ["can discuss workflow fit at a general level"],
                "integration_claim_policy": "Integration and security claims require technical review.",
            },
            diagnostic_gaps={
                "manual_work": g(
                    "manual_work",
                    "manual work",
                    review_focus="manual workflow load",
                    language=["manual work", "manual"],
                    positive=["manual work is the problem", "manual work is a problem"],
                    negative=["manual work is handled", "manual work is fine"],
                    next_gaps=["integration_risk", "visibility_gap"],
                    pain=["manual_work", "cost_or_time_waste"],
                    qual=["current_solution_or_status_quo", "need_or_pain"],
                ),
                "integration_risk": g(
                    "integration_risk",
                    "integration risk",
                    review_focus="integration and security review",
                    language=["integration", "security"],
                    positive=["integration is a problem", "security is a concern"],
                    negative=["integration is fine", "security is handled"],
                    next_gaps=["manual_work", "visibility_gap"],
                    pain=["trust_or_risk_concern", "unclear_next_step"],
                    qual=["fit", "compliance_or_risk_constraints"],
                ),
                "visibility_gap": g(
                    "visibility_gap",
                    "visibility gap",
                    review_focus="visibility into workflow status",
                    language=["visibility", "see status"],
                    positive=["visibility is the problem", "visibility is a problem"],
                    negative=["visibility is handled", "visibility is fine"],
                    next_gaps=["manual_work", "integration_risk"],
                    pain=["visibility_gap", "unclear_next_step"],
                    qual=["need_or_pain", "authority_or_right_person"],
                ),
            },
        ),
        "insurance": base_campaign(
            campaign_id="synthetic-insurance-regression-001",
            client_name="Synthetic Insurance Agency",
            offer="Policy Review Call",
            vertical_id="insurance",
            human_owner="licensed insurance specialist",
            appointment_target="licensed coverage review",
            extra={
                "allowed_claims": common_claims,
                "blocked_claims": ["coverage guarantee", "claim approval promise", "premium guarantee"],
                "license_boundary": "Licensed staff review coverage and policy details.",
                "allowed_policy_language": ["can schedule a licensed coverage review"],
                "human_review_owner": "licensed insurance specialist",
            },
            diagnostic_gaps={
                "coverage_fit": g(
                    "coverage_fit",
                    "coverage fit",
                    review_focus="coverage fit against policy details",
                    language=["coverage fit", "coverage", "covered"],
                    positive=["coverage fit is a problem", "coverage is the issue"],
                    negative=["coverage fit is handled", "coverage is fine"],
                    next_gaps=["premium_or_budget", "renewal_or_timing"],
                    pain=["trust_or_risk_concern", "unclear_next_step"],
                    qual=["fit", "compliance_or_risk_constraints"],
                ),
                "premium_or_budget": g(
                    "premium_or_budget",
                    "premium or budget",
                    review_focus="premium and budget pressure",
                    language=["premium", "budget"],
                    positive=["premium is a problem", "premium is the problem"],
                    negative=["premium is handled", "premium is fine"],
                    next_gaps=["coverage_fit", "renewal_or_timing"],
                    pain=["cost_or_time_waste"],
                    qual=["budget_or_price_sensitivity"],
                ),
                "renewal_or_timing": g(
                    "renewal_or_timing",
                    "renewal or timing",
                    review_focus="renewal timing and next-step urgency",
                    language=["renewal", "timing"],
                    positive=["renewal timing is an issue", "timing is a problem"],
                    negative=["renewal timing is handled", "timing is fine"],
                    next_gaps=["coverage_fit", "premium_or_budget"],
                    pain=["delay", "unclear_next_step"],
                    qual=["timing"],
                ),
            },
        ),
        "telecom": base_campaign(
            campaign_id="synthetic-telecom-regression-001",
            client_name="Synthetic Telecom Provider",
            offer="Plan Review Call",
            vertical_id="telecom",
            human_owner="telecom plan specialist",
            appointment_target="plan and coverage review",
            extra={
                "allowed_claims": common_claims,
                "blocked_claims": ["coverage guarantee", "speed guarantee", "contract cancellation promise"],
                "service_area_policy": "Coverage and availability require human review against the current service map.",
                "approved_plan_facts": ["can discuss plan fit generally"],
                "account_auth_boundary": "Account-specific terms require an authorized specialist.",
            },
            diagnostic_gaps={
                "coverage_or_availability": g(
                    "coverage_or_availability",
                    "coverage or availability",
                    review_focus="coverage and availability fit",
                    language=["coverage", "availability"],
                    positive=["coverage is the issue", "coverage is a problem"],
                    negative=["coverage is fine", "coverage is handled"],
                    next_gaps=["plan_fit", "contract_or_switching"],
                    pain=["trust_or_risk_concern", "delay"],
                    qual=["fit", "compliance_or_risk_constraints"],
                ),
                "plan_fit": g(
                    "plan_fit",
                    "plan fit",
                    review_focus="plan fit and usage needs",
                    language=["plan fit", "plan"],
                    positive=["plan fit is a problem", "plan is the problem"],
                    negative=["plan fit is fine", "plan is fine"],
                    next_gaps=["coverage_or_availability", "contract_or_switching"],
                    pain=["customer_experience_friction", "cost_or_time_waste"],
                    qual=["fit", "budget_or_price_sensitivity"],
                ),
                "contract_or_switching": g(
                    "contract_or_switching",
                    "contract or switching",
                    review_focus="contract timing and switching friction",
                    language=["contract", "switching"],
                    positive=["contract switching is a problem", "switching is a problem"],
                    negative=["contract is handled", "switching is fine"],
                    next_gaps=["coverage_or_availability", "plan_fit"],
                    pain=["trust_or_risk_concern", "unclear_next_step"],
                    qual=["timing", "contact_path"],
                ),
            },
        ),
        "home_services": base_campaign(
            campaign_id="synthetic-home-services-regression-001",
            client_name="Synthetic Home Services",
            offer="Service Estimate Call",
            vertical_id="home_services",
            human_owner="service advisor",
            appointment_target="service estimate review",
            extra={
                "allowed_claims": common_claims,
                "blocked_claims": ["exact price without inspection", "repair outcome promise"],
                "service_area": "Synthetic local service area",
                "inspection_policy": "Exact scope requires inspection or verified property details.",
                "estimate_policy": "No exact price without property review.",
            },
            diagnostic_gaps={
                "service_need": g(
                    "service_need",
                    "service need",
                    review_focus="service need and property context",
                    language=["service", "repair", "need"],
                    positive=["service is the issue", "we need service"],
                    negative=["service need is handled", "service is fine"],
                    next_gaps=["scheduling_urgency", "estimate_or_property_details"],
                    pain=["unclear_next_step", "customer_experience_friction"],
                    qual=["need_or_pain", "fit"],
                ),
                "scheduling_urgency": g(
                    "scheduling_urgency",
                    "scheduling urgency",
                    review_focus="schedule urgency",
                    language=["scheduling", "schedule", "urgent"],
                    positive=["scheduling is a problem", "schedule is the issue"],
                    negative=["scheduling is fine", "schedule is handled"],
                    next_gaps=["service_need", "estimate_or_property_details"],
                    pain=["delay"],
                    qual=["urgency", "timing"],
                ),
                "estimate_or_property_details": g(
                    "estimate_or_property_details",
                    "estimate or property details",
                    review_focus="estimate details and property context",
                    language=["estimate", "property details", "price"],
                    positive=["estimate is unclear", "price is unclear"],
                    negative=["estimate is fine", "property details are handled"],
                    next_gaps=["service_need", "scheduling_urgency"],
                    pain=["trust_or_risk_concern", "cost_or_time_waste"],
                    qual=["budget_or_price_sensitivity", "compliance_or_risk_constraints"],
                ),
            },
        ),
        "healthcare_admin_or_medical_equipment": base_campaign(
            campaign_id="synthetic-healthcare-admin-regression-001",
            client_name="Synthetic Healthcare Admin",
            offer="Admin Equipment Review",
            vertical_id="healthcare_admin_or_medical_equipment",
            human_owner="specialist review coordinator",
            appointment_target="specialist admin review",
            extra={
                "allowed_claims": common_claims,
                "blocked_claims": ["clinical advice", "equipment outcome guarantee", "diagnosis"],
                "clinical_boundary": "Clinical or patient-specific questions require qualified human review.",
                "approved_admin_language": ["can discuss administrative fit and route specialist review"],
                "specialist_handoff_owner": "specialist review coordinator",
            },
            diagnostic_gaps={
                "admin_workflow_need": g(
                    "admin_workflow_need",
                    "admin workflow need",
                    review_focus="admin workflow need",
                    language=["admin workflow", "workflow need", "admin work"],
                    positive=["admin workflow is a problem", "admin workflow need is the issue"],
                    negative=["admin workflow need is handled", "admin work is fine"],
                    next_gaps=["equipment_or_service_fit", "specialist_review_needed"],
                    pain=["manual_work", "delay"],
                    qual=["need_or_pain", "current_solution_or_status_quo"],
                ),
                "equipment_or_service_fit": g(
                    "equipment_or_service_fit",
                    "equipment or service fit",
                    review_focus="equipment or service fit",
                    language=["equipment fit", "equipment", "service fit"],
                    positive=["equipment fit is a problem", "service fit is the issue"],
                    negative=["equipment fit is handled", "equipment fit is fine"],
                    next_gaps=["admin_workflow_need", "specialist_review_needed"],
                    pain=["trust_or_risk_concern", "unclear_next_step"],
                    qual=["fit", "compliance_or_risk_constraints"],
                ),
                "specialist_review_needed": g(
                    "specialist_review_needed",
                    "specialist review needed",
                    review_focus="specialist review need",
                    language=["specialist review", "specialist", "review needed"],
                    positive=["specialist review is needed", "specialist review is a problem"],
                    negative=["specialist review is handled", "specialist is not needed"],
                    next_gaps=["admin_workflow_need", "equipment_or_service_fit"],
                    pain=["trust_or_risk_concern", "unclear_next_step"],
                    qual=["contact_path", "compliance_or_risk_constraints"],
                ),
            },
        ),
        "automotive_service": base_campaign(
            campaign_id="synthetic-automotive-service-regression-001",
            client_name="Synthetic Automotive Service",
            offer="Service Advisor Review",
            vertical_id="automotive_service",
            human_owner="service advisor",
            appointment_target="service advisor inspection review",
            extra={
                "allowed_claims": common_claims,
                "blocked_claims": ["exact diagnosis", "guaranteed repair cost", "warranty guarantee"],
                "service_scope": "Vehicle details require service advisor review.",
                "inspection_policy": "Exact repair scope requires inspection.",
                "advisor_handoff_owner": "service advisor",
            },
            diagnostic_gaps={
                "vehicle_issue": g(
                    "vehicle_issue",
                    "vehicle issue",
                    review_focus="vehicle issue",
                    language=["vehicle issue", "car issue", "vehicle"],
                    positive=["vehicle issue is a problem", "car issue is the problem"],
                    negative=["vehicle issue is handled", "vehicle is fine"],
                    next_gaps=["repair_timing", "warranty_or_estimate"],
                    pain=["trust_or_risk_concern", "unclear_next_step"],
                    qual=["need_or_pain", "fit"],
                ),
                "repair_timing": g(
                    "repair_timing",
                    "repair timing",
                    review_focus="repair timing",
                    language=["repair timing", "timing"],
                    positive=["repair timing is a problem", "timing is the problem"],
                    negative=["repair timing is handled", "repair timing is fine"],
                    next_gaps=["vehicle_issue", "warranty_or_estimate"],
                    pain=["delay", "cost_or_time_waste"],
                    qual=["urgency", "timing"],
                ),
                "warranty_or_estimate": g(
                    "warranty_or_estimate",
                    "warranty or estimate",
                    review_focus="warranty or estimate",
                    language=["warranty", "estimate", "repair cost"],
                    positive=["warranty estimate is the problem", "estimate is a problem"],
                    negative=["warranty estimate is handled", "estimate is fine"],
                    next_gaps=["vehicle_issue", "repair_timing"],
                    pain=["trust_or_risk_concern", "cost_or_time_waste"],
                    qual=["budget_or_price_sensitivity", "compliance_or_risk_constraints"],
                ),
            },
        ),
        "membership_or_subscription": base_campaign(
            campaign_id="synthetic-membership-regression-001",
            client_name="Synthetic Membership Services",
            offer="Membership Plan Review",
            vertical_id="membership_or_subscription",
            human_owner="membership specialist",
            appointment_target="membership account review",
            extra={
                "allowed_claims": common_claims,
                "blocked_claims": ["hidden cancellation terms", "billing outcome promise", "guaranteed savings"],
                "cancellation_boundary": "Cancellation and billing terms must stay transparent and account-specific.",
                "billing_escalation_owner": "membership specialist",
                "approved_plan_language": ["can discuss plan fit and route account review"],
            },
            diagnostic_gaps={
                "plan_fit": g(
                    "plan_fit",
                    "plan fit",
                    review_focus="plan fit",
                    language=["plan fit", "plan"],
                    positive=["plan fit is a problem", "plan is the issue"],
                    negative=["plan fit is fine", "plan is fine"],
                    next_gaps=["renewal_or_cancellation", "usage_or_value"],
                    pain=["customer_experience_friction", "cost_or_time_waste"],
                    qual=["fit", "budget_or_price_sensitivity"],
                ),
                "renewal_or_cancellation": g(
                    "renewal_or_cancellation",
                    "renewal or cancellation",
                    review_focus="renewal or cancellation terms",
                    language=["renewal", "cancellation", "cancel"],
                    positive=["renewal is the issue", "cancellation is a problem"],
                    negative=["renewal is handled", "cancellation is fine"],
                    next_gaps=["plan_fit", "usage_or_value"],
                    pain=["trust_or_risk_concern", "unclear_next_step"],
                    qual=["timing", "contact_path"],
                ),
                "usage_or_value": g(
                    "usage_or_value",
                    "usage or value",
                    review_focus="usage and value fit",
                    language=["usage", "value"],
                    positive=["usage value is a problem", "value is the issue"],
                    negative=["usage is fine", "value is handled"],
                    next_gaps=["plan_fit", "renewal_or_cancellation"],
                    pain=["cost_or_time_waste", "customer_experience_friction"],
                    qual=["need_or_pain", "budget_or_price_sensitivity"],
                ),
            },
        ),
        "retail_or_ecommerce_support_sales": base_campaign(
            campaign_id="synthetic-retail-ecommerce-regression-001",
            client_name="Synthetic Retail Support",
            offer="Product Support Review",
            vertical_id="retail_or_ecommerce_support_sales",
            human_owner="support sales specialist",
            appointment_target="product support review",
            extra={
                "allowed_claims": common_claims,
                "blocked_claims": ["refund guarantee", "stock guarantee", "warranty outcome promise"],
                "policy_fact_source": "Policy-specific claims require support specialist review.",
                "stock_claim_boundary": "Availability must be checked against current stock.",
                "support_escalation_owner": "support sales specialist",
            },
            diagnostic_gaps={
                "product_fit": g(
                    "product_fit",
                    "product fit",
                    review_focus="product fit",
                    language=["product fit", "product"],
                    positive=["product fit is a problem", "product is the issue"],
                    negative=["product fit is fine", "product fit is handled"],
                    next_gaps=["availability_or_delivery", "return_or_warranty"],
                    pain=["customer_experience_friction", "unclear_next_step"],
                    qual=["need_or_pain", "fit"],
                ),
                "availability_or_delivery": g(
                    "availability_or_delivery",
                    "availability or delivery",
                    review_focus="availability or delivery timing",
                    language=["availability", "delivery"],
                    positive=["delivery is a problem", "availability is the issue"],
                    negative=["delivery is fine", "availability is handled"],
                    next_gaps=["product_fit", "return_or_warranty"],
                    pain=["delay", "customer_experience_friction"],
                    qual=["timing", "contact_path"],
                ),
                "return_or_warranty": g(
                    "return_or_warranty",
                    "return or warranty",
                    review_focus="return or warranty policy",
                    language=["return", "warranty", "refund policy"],
                    positive=["return policy is the concern", "warranty is a problem"],
                    negative=["return policy is fine", "warranty is handled"],
                    next_gaps=["product_fit", "availability_or_delivery"],
                    pain=["trust_or_risk_concern", "unclear_next_step"],
                    qual=["contact_path", "compliance_or_risk_constraints"],
                ),
            },
        ),
    }


def build_packet(transcript: str, campaign: dict[str, Any], state: dict[str, Any], label: str) -> dict[str, Any]:
    return generic_campaign_turn.build_generic_campaign_turn_packet(
        transcript=transcript,
        campaign=campaign,
        input_type="agent-open" if transcript == "__agent_open__" else "speech-final",
        session_id=label,
        session_state=state,
        private_out=TMP_DIR / label,
        live_tts=False,
        force_key_missing=True,
        timeout_seconds=8.0,
    )


def run_sequence(label: str, campaign: dict[str, Any], transcripts: list[str]) -> list[dict[str, Any]]:
    state: dict[str, Any] = {"turns": []}
    packets: list[dict[str, Any]] = []
    for transcript in transcripts:
        packet = build_packet(transcript, campaign, state, label)
        packets.append(packet)
        append_turn(state, packet)
    return packets


def assert_all_common(failures: list[str], packets: list[dict[str, Any]], campaign: dict[str, Any], label: str) -> None:
    for index, packet in enumerate(packets, start=1):
        assert_common_packet(failures, packet, campaign, f"{label}_turn{index}")


def assert_no_full_sale_close(failures: list[str], packet: dict[str, Any], label: str) -> None:
    response = normalize(final_response(packet))
    forbidden = ["you are signed up", "purchase confirmed", "payment confirmed", "contract is done", "sale is closed"]
    found = [phrase for phrase in forbidden if phrase in response]
    assert_condition(failures, not found, f"{label}: full sale close wording found {found}: {snapshot(packet)}")


def assert_remaining_gap_question(failures: list[str], packet: dict[str, Any], campaign: dict[str, Any], cleared_gap: str, label: str) -> None:
    response = normalize(final_response(packet))
    remaining = [gap_id for gap_id in campaign["core_diagnostic_gaps"] if gap_id != cleared_gap]
    labels = [normalize(campaign["diagnostic_gaps"][gap_id]["label"]) for gap_id in remaining]
    missing = [text for text in labels if text and text not in response]
    assert_condition(failures, not missing, f"{label}: response did not ask remaining gaps {missing}: {snapshot(packet)}")


def assert_review_bridge(failures: list[str], packet: dict[str, Any], campaign: dict[str, Any], label: str) -> None:
    response = normalize(final_response(packet))
    owner = normalize(campaign.get("human_followup_owner"))
    target = normalize(campaign.get("appointment_target"))
    assert_condition(failures, owner in response or target in response, f"{label}: response did not bridge to campaign human follow-up: {snapshot(packet)}")
    assert_condition(failures, (packet.get("summary") or {}).get("call_control") != "schedule-and-end", f"{label}: pain turn must not schedule-and-end: {snapshot(packet)}")
    assert_no_full_sale_close(failures, packet, label)


def validate_opening_permission(failures: list[str], evidence: dict[str, Any], campaigns: dict[str, dict[str, Any]]) -> None:
    evidence["opening_permission"] = {}
    for label, campaign in campaigns.items():
        packets = run_sequence(f"opening-{label}", campaign, ["__agent_open__", "yeah sure"])
        evidence["opening_permission"][label] = [snapshot(packet) for packet in packets]
        assert_all_common(failures, packets, campaign, f"opening_{label}")
        assert_semantic(failures, packets[1], "permission_acknowledgement", f"opening_{label}_turn2")
        outgoing = semantic_frame(packets[1]).get("outgoing_candidate_gaps")
        assert_condition(failures, outgoing == campaign["core_diagnostic_gaps"], f"opening_{label}: outgoing gaps mismatch: {snapshot(packets[1])}")


def validate_current_gap_clear(failures: list[str], evidence: dict[str, Any], campaigns: dict[str, dict[str, Any]]) -> None:
    cases = {
        "b2b_saas": ("manual work is handled", "manual_work"),
        "insurance": ("coverage fit is handled", "coverage_fit"),
        "telecom": ("coverage is fine", "coverage_or_availability"),
        "home_services": ("scheduling is fine", "scheduling_urgency"),
        "healthcare_admin_or_medical_equipment": ("equipment fit is handled", "equipment_or_service_fit"),
        "automotive_service": ("repair timing is handled", "repair_timing"),
        "membership_or_subscription": ("plan fit is fine", "plan_fit"),
        "retail_or_ecommerce_support_sales": ("product fit is fine", "product_fit"),
    }
    evidence["current_gap_clear"] = {}
    for label, (utterance, target_gap) in cases.items():
        campaign = campaigns[label]
        packets = run_sequence(f"clear-{label}", campaign, ["__agent_open__", "yeah sure", utterance])
        evidence["current_gap_clear"][label] = [snapshot(packet) for packet in packets]
        assert_all_common(failures, packets, campaign, f"clear_{label}")
        assert_semantic(failures, packets[-1], "current_gap_clear", f"clear_{label}_turn3", target_gap)
        cleared = memory(packets[-1]).get("cleared_gaps") or []
        assert_condition(failures, target_gap in cleared, f"clear_{label}: cleared gap not persisted: {snapshot(packets[-1])}")
        assert_remaining_gap_question(failures, packets[-1], campaign, target_gap, f"clear_{label}_turn3")


def validate_pain_confirmed(failures: list[str], evidence: dict[str, Any], campaigns: dict[str, dict[str, Any]]) -> None:
    cases = {
        "b2b_saas": ("visibility is the problem", "visibility_gap"),
        "insurance": ("premium is a problem", "premium_or_budget"),
        "telecom": ("coverage is the issue", "coverage_or_availability"),
        "home_services": ("estimate is unclear", "estimate_or_property_details"),
        "healthcare_admin_or_medical_equipment": ("specialist review is needed", "specialist_review_needed"),
        "automotive_service": ("warranty estimate is the problem", "warranty_or_estimate"),
        "membership_or_subscription": ("renewal is the issue", "renewal_or_cancellation"),
        "retail_or_ecommerce_support_sales": ("return policy is the concern", "return_or_warranty"),
    }
    evidence["pain_confirmed"] = {}
    for label, (utterance, target_gap) in cases.items():
        campaign = campaigns[label]
        packets = run_sequence(f"pain-{label}", campaign, ["__agent_open__", "yeah sure", utterance])
        evidence["pain_confirmed"][label] = [snapshot(packet) for packet in packets]
        assert_all_common(failures, packets, campaign, f"pain_{label}")
        assert_semantic(failures, packets[-1], "pain_confirmed", f"pain_{label}_turn3", target_gap)
        confirmed = memory(packets[-1]).get("confirmed_gaps") or []
        assert_condition(failures, target_gap in confirmed, f"pain_{label}: confirmed gap not persisted: {snapshot(packets[-1])}")
        assert_review_bridge(failures, packets[-1], campaign, f"pain_{label}_turn3")


def validate_send_info(failures: list[str], evidence: dict[str, Any], campaigns: dict[str, dict[str, Any]]) -> None:
    labels = ["insurance", "telecom", "healthcare_admin_or_medical_equipment", "retail_or_ecommerce_support_sales"]
    evidence["send_info"] = {}
    for label in labels:
        campaign = campaigns[label]
        packets = run_sequence(f"send-info-{label}", campaign, ["__agent_open__", "yeah sure", "send me details", "send it to alex@example.com"])
        evidence["send_info"][label] = [snapshot(packet) for packet in packets]
        assert_all_common(failures, packets, campaign, f"send_info_{label}")
        assert_semantic(failures, packets[2], "send_info_request", f"send_info_{label}_turn3")
        assert_condition(failures, (memory(packets[2]).get("send_info_state") or {}).get("capture_status") == "needs_email_or_callback_time", f"send_info_{label}: state did not open: {snapshot(packets[2])}")
        assert_semantic(failures, packets[3], "email_provided", f"send_info_{label}_turn4")
        lead = memory(packets[3]).get("lead_followup_state") or {}
        assert_condition(failures, (lead.get("contact") or {}).get("email_hash"), f"send_info_{label}: email hash missing: {snapshot(packets[3])}")
        assert_condition(failures, (lead.get("contact") or {}).get("raw_email_stored_in_public_evidence") is False, f"send_info_{label}: raw email flag wrong: {snapshot(packets[3])}")
        assert_condition(failures, (packets[3].get("summary") or {}).get("call_control") != "schedule-and-end", f"send_info_{label}: email-only must not schedule: {snapshot(packets[3])}")


def validate_callback_time(failures: list[str], evidence: dict[str, Any], campaigns: dict[str, dict[str, Any]]) -> None:
    labels = ["b2b_saas", "home_services", "automotive_service", "membership_or_subscription"]
    evidence["callback_time"] = {}
    for label in labels:
        campaign = campaigns[label]
        packets = run_sequence(f"callback-{label}", campaign, ["__agent_open__", "yeah sure", "send me details", "tomorrow at 3 works"])
        evidence["callback_time"][label] = [snapshot(packet) for packet in packets]
        assert_all_common(failures, packets, campaign, f"callback_{label}")
        lead = memory(packets[3]).get("lead_followup_state") or {}
        callback = lead.get("callback") or {}
        normalized = callback.get("normalized") or {}
        assert_condition(failures, bool(callback.get("raw_text_redacted")), f"callback_{label}: callback raw text missing: {snapshot(packets[3])}")
        assert_condition(failures, "3" in str(normalized.get("time_text") or ""), f"callback_{label}: normalized time missing: {snapshot(packets[3])}")
        assert_condition(failures, (packets[3].get("summary") or {}).get("call_control") == "schedule-and-end", f"callback_{label}: usable callback should schedule-and-end: {snapshot(packets[3])}")
        assert_condition(failures, not (lead.get("contact") or {}).get("email_hash"), f"callback_{label}: email invented: {snapshot(packets[3])}")


def validate_right_person(failures: list[str], evidence: dict[str, Any], campaigns: dict[str, dict[str, Any]]) -> None:
    labels = ["b2b_saas", "insurance", "telecom", "healthcare_admin_or_medical_equipment"]
    evidence["right_person"] = {}
    for label in labels:
        campaign = campaigns[label]
        packets = run_sequence(f"right-person-{label}", campaign, ["__agent_open__", "yeah sure", "I'm not the person", "operations handles that"])
        evidence["right_person"][label] = [snapshot(packet) for packet in packets]
        assert_all_common(failures, packets, campaign, f"right_person_{label}")
        assert_semantic(failures, packets[2], "wrong_person_or_wrong_department", f"right_person_{label}_turn3")
        assert_condition(failures, (memory(packets[2]).get("handoff_target_state") or {}).get("capture_status") == "needs_right_person", f"right_person_{label}: handoff did not open: {snapshot(packets[2])}")
        assert_semantic(failures, packets[3], {"department_named", "wrong_person_or_wrong_department"}, f"right_person_{label}_turn4")
        handoff = memory(packets[3]).get("handoff_target_state") or {}
        assert_condition(failures, (handoff.get("target") or {}).get("role_or_department") == "operations", f"right_person_{label}: department missing: {snapshot(packets[3])}")
        assert_condition(failures, memory(packets[3]).get("selected_gap") not in campaign["core_diagnostic_gaps"], f"right_person_{label}: product gap selected on handoff: {snapshot(packets[3])}")
        response = normalize(final_response(packets[3]))
        assert_condition(failures, any(term in response for term in ["contact", "email", "callback", "right person", "path"]), f"right_person_{label}: response did not ask contact/path: {snapshot(packets[3])}")


def validate_stop_refusal(failures: list[str], evidence: dict[str, Any], campaigns: dict[str, dict[str, Any]]) -> None:
    evidence["stop_refusal"] = {}
    for label, campaign in campaigns.items():
        packets = run_sequence(f"stop-{label}", campaign, ["__agent_open__", "stop calling", "actually one more thing"])
        evidence["stop_refusal"][label] = [snapshot(packet) for packet in packets]
        assert_all_common(failures, packets, campaign, f"stop_{label}")
        assert_semantic(failures, packets[1], "stop_request", f"stop_{label}_turn2")
        assert_condition(failures, (packets[1].get("summary") or {}).get("call_control") == "end-call", f"stop_{label}: stop must end call: {snapshot(packets[1])}")
        assert_condition(failures, (packets[2].get("summary") or {}).get("call_control") == "end-call", f"stop_{label}: terminal state must persist: {snapshot(packets[2])}")
        response = normalize(final_response(packets[2]))
        assert_condition(failures, not any(term in response for term in ["quick fit check", "what time works", "creating issues today"]), f"stop_{label}: continued selling after stop: {snapshot(packets[2])}")


def validate_regulated_caution(failures: list[str], evidence: dict[str, Any], campaigns: dict[str, dict[str, Any]]) -> None:
    cases = {
        "insurance": "can you guarantee I'm covered?",
        "telecom": "can you guarantee coverage here?",
        "home_services": "can you give exact price without looking?",
        "healthcare_admin_or_medical_equipment": "can you guarantee this equipment solves the issue?",
        "automotive_service": "can you guarantee the repair cost?",
        "membership_or_subscription": "can you hide cancellation terms?",
        "retail_or_ecommerce_support_sales": "can you guarantee the refund?",
    }
    evidence["regulated_caution"] = {}
    for label, utterance in cases.items():
        campaign = campaigns[label]
        packets = run_sequence(f"caution-{label}", campaign, ["__agent_open__", "yeah sure", utterance])
        evidence["regulated_caution"][label] = [snapshot(packet) for packet in packets]
        assert_all_common(failures, packets, campaign, f"caution_{label}")
        response = normalize(final_response(packets[-1]))
        assert_condition(
            failures,
            any(term in response for term in ["cannot", "can't", "not", "human", "specialist", "review", "policy", "inspection", "advisor", "licensed"]),
            f"caution_{label}: regulated caution wording missing: {snapshot(packets[-1])}",
        )
        unsupported = [
            "i can guarantee",
            "we can guarantee",
            "guaranteed refund",
            "guaranteed coverage",
            "exact price is",
            "i can hide cancellation",
            "we can hide cancellation",
            "will hide cancellation",
            "hide them for you",
        ]
        found = [term for term in unsupported if term in response]
        assert_condition(failures, not found, f"caution_{label}: unsupported claim found {found}: {snapshot(packets[-1])}")


def validate_matrix(failures: list[str], evidence: dict[str, Any]) -> None:
    campaigns = synthetic_campaigns()
    evidence["verticals_tested"] = sorted(campaigns)
    evidence["campaigns"] = {
        label: {
            "campaign_id": campaign["campaign_id"],
            "vertical_id": campaign["vertical_id"],
            "campaign_playbook_id": campaign["campaign_playbook_id"],
            "core_diagnostic_gaps": campaign["core_diagnostic_gaps"],
        }
        for label, campaign in campaigns.items()
    }
    for label, campaign in campaigns.items():
        validation = generic_campaign_turn.validate_generic_campaign_config(campaign)
        assert_condition(failures, validation.get("valid") is True, f"{label}: campaign config invalid: {validation}")
        assert_condition(failures, validation.get("campaign_playbook_id") != ROUTESIGNAL_PLAYBOOK_ID, f"{label}: synthetic campaign resolved to RouteSignal: {validation}")

    validate_opening_permission(failures, evidence, campaigns)
    validate_current_gap_clear(failures, evidence, campaigns)
    validate_pain_confirmed(failures, evidence, campaigns)
    validate_send_info(failures, evidence, campaigns)
    validate_callback_time(failures, evidence, campaigns)
    validate_right_person(failures, evidence, campaigns)
    validate_stop_refusal(failures, evidence, campaigns)
    validate_regulated_caution(failures, evidence, campaigns)
    validate_invalid_campaign(failures, evidence)
    validate_routesignal_preservation(failures, evidence)


def render_report(result: dict[str, Any]) -> str:
    lines = [
        "# GENERIC-CAMPAIGN-RUNTIME-REGRESSION-001",
        "",
        f"Status: {result['status']}",
        f"Failure count: {len(result.get('failures') or [])}",
        f"Vertical count: {len((result.get('evidence') or {}).get('verticals_tested') or [])}",
        "",
        "## Scenarios",
        "",
        "- Opening and permission across all eight verticals.",
        "- Current gap clear across all eight verticals.",
        "- Pain confirmed across all eight verticals.",
        "- Send-info with redacted email across insurance, telecom, healthcare admin, and retail/ecommerce.",
        "- Callback time capture across B2B SaaS, home services, automotive service, and membership/subscription.",
        "- Right-person handoff across B2B SaaS, insurance, telecom, and healthcare admin.",
        "- Stop/refusal terminal behavior across all eight verticals.",
        "- Regulated caution across seven regulated verticals.",
        "- Invalid campaign failure and RouteSignal live-demo preservation.",
        "",
        "## Safety",
        "",
        f"- Raw synthetic emails in public evidence: `{str(result.get('raw_synthetic_emails_in_public_evidence')).lower()}`",
        "- Provider calls made: `false`",
        "- Local LLM calls made: `false`",
        "- Sends email: `false`",
        "- Creates calendar event: `false`",
        "- Writes CRM: `false`",
        "- Opens PROD-102: `false`",
        "",
        "## Failures",
        "",
    ]
    failures = result.get("failures") or []
    if failures:
        lines.extend(f"- {failure}" for failure in failures)
    else:
        lines.append("- None")
    return "\n".join(lines) + "\n"


def main() -> int:
    failures: list[str] = []
    evidence: dict[str, Any] = {}
    validate_matrix(failures, evidence)
    result = sanitize(
        {
            "checkpoint_id": CHECKPOINT_ID,
            "status": "pass" if not failures else "fail",
            "failures": failures,
            "evidence": evidence,
            "forbidden_terms_checked": FORBIDDEN_BRAND_TERMS + FORBIDDEN_ROUTE_PHRASES,
            "phase_1_2_3_backpatch_required": False,
            "safety_assertions": {key: False for key in SAFETY_KEYS},
            "uses_provider_calls": False,
            "uses_live_tts": False,
            "uses_real_customer_data": False,
        }
    )
    serialized = json.dumps(result).lower()
    leaked_emails = [raw for raw in RAW_EMAILS if raw in serialized]
    if leaked_emails:
        failures.extend(f"public generated evidence leaked raw synthetic email {raw}" for raw in leaked_emails)
        result["failures"] = failures
        result["status"] = "fail"
    result["raw_synthetic_emails_in_public_evidence"] = any(raw in json.dumps(result).lower() for raw in RAW_EMAILS)
    write_evidence(result, render_report(result))
    if failures:
        print(json.dumps(result, indent=2, sort_keys=True))
        return 1
    print(f"{CHECKPOINT_ID}: pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
