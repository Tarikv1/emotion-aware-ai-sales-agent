from __future__ import annotations

from copy import deepcopy
from typing import Any


SCHEMA_VERSION = 1
SUGGESTED_UNIVERSAL_ADDITIONS: list[dict[str, str]] = []

_COMMON_REQUIRED_CAMPAIGN_FIELDS = [
    "campaign_id",
    "client_name",
    "offer_name",
    "allowed_claims",
    "blocked_claims",
    "qualification_goals",
    "appointment_target",
    "human_followup_owner",
]


VERTICAL_SALES_PLAYBOOKS: dict[str, dict[str, Any]] = {
    "b2b_saas": {
        "vertical_id": "b2b_saas",
        "schema_version": SCHEMA_VERSION,
        "description": "Business software outreach where the useful sales logic is workflow fit, buyer authority, current tool/process friction, and a human review of the buyer's actual operating context.",
        "typical_call_center_contexts": ["outbound qualification", "trial or inquiry follow-up", "renewal expansion", "implementation interest"],
        "common_buyer_roles": ["operations owner", "department manager", "systems administrator", "finance or procurement contact"],
        "common_sales_stages": ["opening", "permission", "discovery", "qualification", "value_mapping", "appointment_setting", "right_person_handoff"],
        "likely_qualification_dimensions": ["need_or_pain", "authority_or_right_person", "fit", "current_solution_or_status_quo", "budget_or_price_sensitivity", "compliance_or_risk_constraints"],
        "common_pain_dimensions": ["manual_work", "visibility_gap", "ownership_confusion", "delay", "duplicate_work"],
        "common_objection_families": ["existing_vendor_or_process", "price", "authority", "privacy_or_security", "complexity"],
        "safe_discovery_questions": [
            "Where does the current process still depend on manual work?",
            "Who owns the decision if the team wants to review a better process?",
            "What part of the current tool or process creates the most delay?",
        ],
        "safe_value_bridge_principles": [
            "Tie value only to the buyer's named workflow issue.",
            "Route technical, security, and contract details to a human.",
            "Avoid product performance claims unless the campaign config allows them.",
        ],
        "appointment_or_followup_patterns": ["human fit review", "technical discovery call", "implementation-readiness callback"],
        "right_person_or_authority_patterns": ["decision owner", "technical owner", "procurement owner", "department lead"],
        "send_info_patterns": ["product summary", "fit notes", "human follow-up packet"],
        "regulated_cautions": ["legal_or_contract_sensitive", "financial_or_payment_sensitive"],
        "blocked_claim_types": ["unverified integration claim", "unverified security claim", "guaranteed business outcome"],
        "human_escalation_triggers": ["security review question", "contract term question", "technical implementation scope"],
        "campaign_config_required_fields": _COMMON_REQUIRED_CAMPAIGN_FIELDS + ["product_category", "approved_feature_claims", "integration_claim_policy"],
    },
    "insurance": {
        "vertical_id": "insurance",
        "schema_version": SCHEMA_VERSION,
        "description": "Insurance-related outreach where qualification must stay cautious around eligibility, coverage, policy terms, claims, price, and licensed human review.",
        "typical_call_center_contexts": ["policy inquiry", "renewal outreach", "quote follow-up", "claims-adjacent support"],
        "common_buyer_roles": ["policy holder", "benefits administrator", "small business owner", "family decision maker"],
        "common_sales_stages": ["opening", "permission", "discovery", "qualification", "objection_or_resistance", "appointment_setting", "close_or_end"],
        "likely_qualification_dimensions": ["need_or_pain", "urgency", "fit", "budget_or_price_sensitivity", "compliance_or_risk_constraints"],
        "common_pain_dimensions": ["trust_or_risk_concern", "cost_or_time_waste", "unclear_next_step", "delay"],
        "common_objection_families": ["price", "trust", "privacy_or_security", "existing_vendor_or_process", "complexity"],
        "safe_discovery_questions": [
            "What made you want to review options now?",
            "Is the main concern cost, fit, timing, or understanding the next step?",
            "Would a licensed human need to review the details with you?",
        ],
        "safe_value_bridge_principles": [
            "Keep the conversation to information gathering and human review.",
            "Do not decide eligibility, coverage, or claim outcomes.",
            "Use only campaign-approved policy language.",
        ],
        "appointment_or_followup_patterns": ["licensed human review", "quote review callback", "policy information callback"],
        "right_person_or_authority_patterns": ["policy owner", "benefits owner", "authorized family contact", "business owner"],
        "send_info_patterns": ["approved information summary", "licensed review callback", "document-request handoff"],
        "regulated_cautions": ["insurance", "financial_or_payment_sensitive", "legal_or_contract_sensitive"],
        "blocked_claim_types": ["coverage decision", "claim outcome promise", "legal or financial advice"],
        "human_escalation_triggers": ["coverage question", "claim question", "eligibility question", "policy term dispute"],
        "campaign_config_required_fields": _COMMON_REQUIRED_CAMPAIGN_FIELDS + ["license_boundary", "allowed_policy_language", "human_review_owner"],
    },
    "telecom": {
        "vertical_id": "telecom",
        "schema_version": SCHEMA_VERSION,
        "description": "Telecom outreach where qualification often involves plan fit, service availability, contract timing, switching friction, device or service needs, and careful handling of coverage claims.",
        "typical_call_center_contexts": ["plan upgrade", "service inquiry", "retention callback", "switching follow-up"],
        "common_buyer_roles": ["account owner", "household decision maker", "business account manager", "technical contact"],
        "common_sales_stages": ["opening", "permission", "discovery", "qualification", "objection_or_resistance", "send_info", "appointment_setting"],
        "likely_qualification_dimensions": ["need_or_pain", "fit", "timing", "budget_or_price_sensitivity", "contact_path"],
        "common_pain_dimensions": ["delay", "customer_experience_friction", "cost_or_time_waste", "trust_or_risk_concern"],
        "common_objection_families": ["price", "existing_vendor_or_process", "timing", "trust", "complexity"],
        "safe_discovery_questions": [
            "Is the main issue plan fit, service availability, price, or switching timing?",
            "Who owns the account decision?",
            "What would need to be clear before you consider a change?",
        ],
        "safe_value_bridge_principles": [
            "Separate general plan discussion from verified availability or contract details.",
            "Do not promise coverage, speed, fee, or cancellation outcomes without approved facts.",
            "Escalate account-specific terms to a human.",
        ],
        "appointment_or_followup_patterns": ["plan-fit callback", "account review", "availability review by human"],
        "right_person_or_authority_patterns": ["account owner", "authorized account contact", "business telecom owner"],
        "send_info_patterns": ["plan information", "switching checklist", "human callback details"],
        "regulated_cautions": ["telecom_contract_or_coverage", "legal_or_contract_sensitive", "financial_or_payment_sensitive"],
        "blocked_claim_types": ["unverified coverage claim", "unverified fee claim", "contract cancellation outcome"],
        "human_escalation_triggers": ["coverage dispute", "contract term question", "billing concern", "account authorization issue"],
        "campaign_config_required_fields": _COMMON_REQUIRED_CAMPAIGN_FIELDS + ["service_area_policy", "approved_plan_facts", "account_auth_boundary"],
    },
    "home_services": {
        "vertical_id": "home_services",
        "schema_version": SCHEMA_VERSION,
        "description": "Home-service outreach where qualification usually involves urgency, service area, property context, scheduling, estimates, and safety-sensitive boundaries.",
        "typical_call_center_contexts": ["service request follow-up", "inspection scheduling", "maintenance reminder", "quote callback"],
        "common_buyer_roles": ["homeowner", "property manager", "tenant coordinator", "facilities contact"],
        "common_sales_stages": ["opening", "permission", "discovery", "qualification", "callback_scheduling", "appointment_setting", "close_or_end"],
        "likely_qualification_dimensions": ["need_or_pain", "urgency", "fit", "timing", "contact_path"],
        "common_pain_dimensions": ["delay", "trust_or_risk_concern", "customer_experience_friction", "unclear_next_step"],
        "common_objection_families": ["price", "timing", "trust", "complexity", "not_relevant"],
        "safe_discovery_questions": [
            "Is this urgent, routine, or just something you want reviewed?",
            "What type of property or service area should a human confirm?",
            "Would you prefer a callback or an appointment window?",
        ],
        "safe_value_bridge_principles": [
            "Offer scheduling or inspection review rather than remote diagnosis.",
            "Keep estimates conditional on human review where required.",
            "Escalate safety concerns to qualified staff.",
        ],
        "appointment_or_followup_patterns": ["inspection appointment", "service callback", "estimate review"],
        "right_person_or_authority_patterns": ["property owner", "property manager", "facilities owner", "authorized resident"],
        "send_info_patterns": ["service overview", "appointment preparation notes", "callback options"],
        "regulated_cautions": ["home_services_safety_or_estimate", "legal_or_contract_sensitive", "financial_or_payment_sensitive"],
        "blocked_claim_types": ["exact quote without inspection", "remote safety diagnosis", "permit or code interpretation"],
        "human_escalation_triggers": ["safety concern", "urgent property issue", "estimate request", "permit or code question"],
        "campaign_config_required_fields": _COMMON_REQUIRED_CAMPAIGN_FIELDS + ["service_area", "inspection_policy", "estimate_policy"],
    },
    "healthcare_admin_or_medical_equipment": {
        "vertical_id": "healthcare_admin_or_medical_equipment",
        "schema_version": SCHEMA_VERSION,
        "description": "Healthcare admin or medical equipment outreach where qualification must avoid clinical advice while routing operational, scheduling, equipment, or specialist questions to humans.",
        "typical_call_center_contexts": ["equipment inquiry", "admin workflow follow-up", "specialist callback", "procurement support"],
        "common_buyer_roles": ["clinic administrator", "care coordinator", "procurement contact", "patient support contact"],
        "common_sales_stages": ["opening", "permission", "discovery", "qualification", "right_person_handoff", "appointment_setting", "close_or_end"],
        "likely_qualification_dimensions": ["need_or_pain", "authority_or_right_person", "fit", "contact_path", "compliance_or_risk_constraints"],
        "common_pain_dimensions": ["manual_work", "delay", "visibility_gap", "trust_or_risk_concern", "unclear_next_step"],
        "common_objection_families": ["privacy_or_security", "authority", "complexity", "existing_vendor_or_process", "trust"],
        "safe_discovery_questions": [
            "Is this about administrative workflow, equipment logistics, or a specialist question?",
            "Who should review the operational or equipment details?",
            "Would a qualified human callback be the safer next step?",
        ],
        "safe_value_bridge_principles": [
            "Stay with operations, scheduling, or handoff support unless campaign-approved details exist.",
            "Do not provide clinical judgment or patient-specific recommendations.",
            "Escalate medical, equipment suitability, and sensitive data questions.",
        ],
        "appointment_or_followup_patterns": ["specialist callback", "admin review", "equipment support follow-up"],
        "right_person_or_authority_patterns": ["clinic administrator", "procurement owner", "care team contact", "authorized support contact"],
        "send_info_patterns": ["approved overview", "specialist follow-up request", "admin summary"],
        "regulated_cautions": ["healthcare_admin_or_medical_equipment", "financial_or_payment_sensitive", "legal_or_contract_sensitive"],
        "blocked_claim_types": ["medical advice", "diagnosis", "approval or outcome promise"],
        "human_escalation_triggers": ["clinical question", "patient-specific question", "equipment suitability question", "sensitive data concern"],
        "campaign_config_required_fields": _COMMON_REQUIRED_CAMPAIGN_FIELDS + ["clinical_boundary", "approved_admin_language", "specialist_handoff_owner"],
    },
    "automotive_service": {
        "vertical_id": "automotive_service",
        "schema_version": SCHEMA_VERSION,
        "description": "Automotive service outreach where qualification involves vehicle issue, urgency, scheduling, inspection need, estimate caution, warranty caution, and service advisor handoff.",
        "typical_call_center_contexts": ["service inquiry", "repair callback", "maintenance reminder", "inspection scheduling"],
        "common_buyer_roles": ["vehicle owner", "fleet manager", "service advisor contact", "authorized driver"],
        "common_sales_stages": ["opening", "permission", "discovery", "qualification", "callback_scheduling", "appointment_setting", "close_or_end"],
        "likely_qualification_dimensions": ["need_or_pain", "urgency", "timing", "fit", "contact_path"],
        "common_pain_dimensions": ["trust_or_risk_concern", "delay", "unclear_next_step", "cost_or_time_waste"],
        "common_objection_families": ["price", "timing", "trust", "existing_vendor_or_process", "complexity"],
        "safe_discovery_questions": [
            "Is the main need inspection, maintenance, repair scheduling, or advisor review?",
            "Is there any safety concern that should go to a service advisor?",
            "What time would work for a qualified human to review the next step?",
        ],
        "safe_value_bridge_principles": [
            "Route diagnosis, safety, estimate, and warranty details to service staff.",
            "Use the call to capture the issue and schedule the right review.",
            "Avoid remote repair conclusions.",
        ],
        "appointment_or_followup_patterns": ["service advisor callback", "inspection appointment", "maintenance scheduling"],
        "right_person_or_authority_patterns": ["vehicle owner", "fleet decision owner", "authorized driver", "service advisor"],
        "send_info_patterns": ["service preparation notes", "inspection options", "advisor callback path"],
        "regulated_cautions": ["automotive_service_safety_or_warranty", "legal_or_contract_sensitive", "financial_or_payment_sensitive"],
        "blocked_claim_types": ["exact diagnosis without inspection", "warranty outcome promise", "repair cost certainty"],
        "human_escalation_triggers": ["safety issue", "warranty dispute", "repair estimate request", "drivability concern"],
        "campaign_config_required_fields": _COMMON_REQUIRED_CAMPAIGN_FIELDS + ["service_scope", "inspection_policy", "advisor_handoff_owner"],
    },
    "membership_or_subscription": {
        "vertical_id": "membership_or_subscription",
        "schema_version": SCHEMA_VERSION,
        "description": "Membership or subscription outreach where qualification involves plan fit, value concern, renewal or cancellation intent, onboarding support, and account-specific human routing.",
        "typical_call_center_contexts": ["renewal follow-up", "save offer", "onboarding help", "plan-fit callback"],
        "common_buyer_roles": ["account holder", "household decision maker", "team administrator", "billing contact"],
        "common_sales_stages": ["opening", "permission", "discovery", "qualification", "objection_or_resistance", "send_info", "close_or_end"],
        "likely_qualification_dimensions": ["need_or_pain", "budget_or_price_sensitivity", "timing", "contact_path", "fit"],
        "common_pain_dimensions": ["cost_or_time_waste", "customer_experience_friction", "unclear_next_step", "trust_or_risk_concern"],
        "common_objection_families": ["price", "not_interested", "timing", "complexity", "stop_or_do_not_contact"],
        "safe_discovery_questions": [
            "Is the concern plan fit, renewal timing, cancellation, or help using the service?",
            "What would need to be clearer before you decide?",
            "Would you prefer account help, written information, or no further contact?",
        ],
        "safe_value_bridge_principles": [
            "Respect cancellation or refusal language immediately.",
            "Do not obscure renewal, billing, or cancellation boundaries.",
            "Route account-specific actions to authorized support.",
        ],
        "appointment_or_followup_patterns": ["account support callback", "plan-fit review", "renewal help"],
        "right_person_or_authority_patterns": ["account holder", "billing owner", "team administrator", "authorized support contact"],
        "send_info_patterns": ["plan summary", "account help options", "callback path"],
        "regulated_cautions": ["membership_or_subscription_cancellation", "financial_or_payment_sensitive", "legal_or_contract_sensitive"],
        "blocked_claim_types": ["hidden cancellation terms", "unverified refund claim", "unapproved account change"],
        "human_escalation_triggers": ["cancellation request", "billing dispute", "refund request", "account access issue"],
        "campaign_config_required_fields": _COMMON_REQUIRED_CAMPAIGN_FIELDS + ["cancellation_boundary", "billing_escalation_owner", "approved_plan_language"],
    },
    "retail_or_ecommerce_support_sales": {
        "vertical_id": "retail_or_ecommerce_support_sales",
        "schema_version": SCHEMA_VERSION,
        "description": "Retail or ecommerce support-sales outreach where qualification involves product fit, availability, delivery timing, return or warranty concern, and support escalation.",
        "typical_call_center_contexts": ["cart or inquiry follow-up", "support-to-sales callback", "availability question", "return or warranty support"],
        "common_buyer_roles": ["shopper", "account holder", "gift purchaser", "business purchaser"],
        "common_sales_stages": ["opening", "permission", "discovery", "qualification", "send_info", "callback_scheduling", "close_or_end"],
        "likely_qualification_dimensions": ["need_or_pain", "fit", "timing", "budget_or_price_sensitivity", "contact_path"],
        "common_pain_dimensions": ["customer_experience_friction", "delay", "trust_or_risk_concern", "unclear_next_step", "cost_or_time_waste"],
        "common_objection_families": ["price", "timing", "trust", "privacy_or_security", "existing_vendor_or_process"],
        "safe_discovery_questions": [
            "Is this about product fit, availability, delivery timing, or support?",
            "What would need to be clear before you decide?",
            "Would a support callback or written product information help?",
        ],
        "safe_value_bridge_principles": [
            "Use only verified policy and product facts from the campaign.",
            "Route refund, warranty, stock, and shipping exceptions to support.",
            "Do not promise availability or delivery unless the campaign config allows it.",
        ],
        "appointment_or_followup_patterns": ["support callback", "product-fit callback", "order support handoff"],
        "right_person_or_authority_patterns": ["account holder", "purchasing contact", "support owner", "gift recipient contact"],
        "send_info_patterns": ["product information", "support summary", "callback options"],
        "regulated_cautions": ["retail_or_ecommerce_refund_warranty_availability", "financial_or_payment_sensitive", "legal_or_contract_sensitive"],
        "blocked_claim_types": ["false stock claim", "delivery promise without approved facts", "refund or warranty promise"],
        "human_escalation_triggers": ["refund dispute", "availability question", "warranty claim", "shipping dispute"],
        "campaign_config_required_fields": _COMMON_REQUIRED_CAMPAIGN_FIELDS + ["policy_fact_source", "stock_claim_boundary", "support_escalation_owner"],
    },
}


def vertical_playbook(vertical_id: str | None) -> dict[str, Any]:
    if not vertical_id:
        return {}
    return deepcopy(VERTICAL_SALES_PLAYBOOKS.get(vertical_id) or {})


def all_vertical_ids() -> list[str]:
    return sorted(VERTICAL_SALES_PLAYBOOKS)


def vertical_ids_for_regulated_caution(caution_id: str | None) -> list[str]:
    if not caution_id:
        return []
    return sorted(
        vertical_id
        for vertical_id, playbook in VERTICAL_SALES_PLAYBOOKS.items()
        if caution_id in (playbook.get("regulated_cautions") or [])
    )


def vertical_required_campaign_fields(vertical_id: str | None) -> list[str]:
    return list((vertical_playbook(vertical_id)).get("campaign_config_required_fields") or [])


def vertical_regulated_cautions(vertical_id: str | None) -> list[str]:
    return list((vertical_playbook(vertical_id)).get("regulated_cautions") or [])


def vertical_safe_discovery_questions(vertical_id: str | None) -> list[str]:
    return list((vertical_playbook(vertical_id)).get("safe_discovery_questions") or [])


def vertical_blocked_claim_types(vertical_id: str | None) -> list[str]:
    return list((vertical_playbook(vertical_id)).get("blocked_claim_types") or [])


def _universal_module(universal_knowledge: Any | None = None) -> Any:
    if universal_knowledge is not None:
        return universal_knowledge
    from runtime.core import universal_sales_knowledge

    return universal_sales_knowledge


def validate_vertical_sales_playbooks(universal_knowledge: Any | None = None) -> dict[str, Any]:
    universal = _universal_module(universal_knowledge)
    failures: list[str] = []
    required_fields = {
        "vertical_id",
        "schema_version",
        "description",
        "typical_call_center_contexts",
        "common_buyer_roles",
        "common_sales_stages",
        "likely_qualification_dimensions",
        "common_pain_dimensions",
        "common_objection_families",
        "safe_discovery_questions",
        "safe_value_bridge_principles",
        "appointment_or_followup_patterns",
        "right_person_or_authority_patterns",
        "send_info_patterns",
        "regulated_cautions",
        "blocked_claim_types",
        "human_escalation_triggers",
        "campaign_config_required_fields",
    }
    stage_ids = set(universal.all_sales_stage_ids())
    qualification_ids = set(universal.all_qualification_dimension_ids())
    pain_ids = set(universal.all_generic_pain_dimension_ids())
    objection_ids = set(universal.all_objection_family_ids())
    caution_ids = set(universal.all_regulated_caution_ids())

    for vertical_id, playbook in VERTICAL_SALES_PLAYBOOKS.items():
        if playbook.get("vertical_id") != vertical_id:
            failures.append(f"{vertical_id}: vertical_id mismatch")
        if playbook.get("schema_version") != SCHEMA_VERSION:
            failures.append(f"{vertical_id}: schema_version mismatch")
        for field in sorted(required_fields):
            if not playbook.get(field):
                failures.append(f"{vertical_id}.{field}: missing")
        unknown_stages = sorted(set(playbook.get("common_sales_stages") or []) - stage_ids)
        unknown_qualifications = sorted(set(playbook.get("likely_qualification_dimensions") or []) - qualification_ids)
        unknown_pains = sorted(set(playbook.get("common_pain_dimensions") or []) - pain_ids)
        unknown_objections = sorted(set(playbook.get("common_objection_families") or []) - objection_ids)
        unknown_cautions = sorted(set(playbook.get("regulated_cautions") or []) - caution_ids)
        if unknown_stages:
            failures.append(f"{vertical_id}: unknown sales stages {unknown_stages}")
        if unknown_qualifications:
            failures.append(f"{vertical_id}: unknown qualification dimensions {unknown_qualifications}")
        if unknown_pains:
            failures.append(f"{vertical_id}: unknown pain dimensions {unknown_pains}")
        if unknown_objections:
            failures.append(f"{vertical_id}: unknown objection families {unknown_objections}")
        if unknown_cautions:
            failures.append(f"{vertical_id}: unknown regulated cautions {unknown_cautions}")

    return {
        "valid": not failures,
        "schema_version": SCHEMA_VERSION,
        "vertical_ids": all_vertical_ids(),
        "suggested_universal_additions": deepcopy(SUGGESTED_UNIVERSAL_ADDITIONS),
        "failures": failures,
        "provider_calls_made": False,
        "local_llm_calls_made": False,
        "sends_email": False,
        "creates_calendar_event": False,
        "writes_crm": False,
        "opens_prod_102": False,
    }
