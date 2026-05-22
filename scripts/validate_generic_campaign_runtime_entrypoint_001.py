#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import inspect
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.core import campaign_playbook_adapter as adapter  # noqa: E402


CHECKPOINT_ID = "GENERIC-CAMPAIGN-RUNTIME-ENTRYPOINT-001"
GENERATED_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
RESULT_PATH = GENERATED_DIR / "result.json"
REPORT_PATH = GENERATED_DIR / "report.md"
TMP_DIR = ROOT / ".tmp" / CHECKPOINT_ID

ROUTESIGNAL_PLAYBOOK_ID = "ROUTESIGNAL-DIAGNOSTIC-PLAYBOOK-001"
FORBIDDEN_BRAND_TERMS = ["RouteSignal", "Northstar", "Starter", "Growth", "$29", "$59"]
FORBIDDEN_ROUTE_PHRASES = ["inbound demo", "demo follow-up", "missed callbacks", "manual tracking", "messy handoffs"]
ROUTESIGNAL_GAP_IDS = {"callbacks", "manual_tracking", "handoffs"}
RAW_EMAILS = ["alex@example.com", "ops@example.com"]
EMAIL_RE = re.compile(r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b")
SAFETY_KEYS = [
    "provider_calls_made",
    "local_llm_calls_made",
    "sends_email",
    "creates_calendar_event",
    "writes_crm",
    "opens_prod_102",
]

try:
    from runtime.entrypoints import generic_campaign_turn as entrypoint  # noqa: E402
except Exception as exc:  # pragma: no cover - red-test path
    entrypoint = None
    ENTRYPOINT_IMPORT_ERROR = repr(exc)
else:
    ENTRYPOINT_IMPORT_ERROR = None


def assert_condition(failures: list[str], condition: bool, message: str) -> None:
    if not condition:
        failures.append(message)


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "").strip().lower())


def email_token(value: str) -> str:
    return "<email:sha256_12:" + hashlib.sha256(value.lower().encode("utf-8")).hexdigest()[:12] + ">"


def redact_text(text: str) -> str:
    def repl(match: re.Match[str]) -> str:
        return email_token(match.group(0))

    redacted = EMAIL_RE.sub(repl, str(text))
    for raw in RAW_EMAILS:
        redacted = redacted.replace(raw, email_token(raw))
    return redacted


def sanitize(value: Any) -> Any:
    if isinstance(value, str):
        return redact_text(value)
    if isinstance(value, list):
        return [sanitize(item) for item in value]
    if isinstance(value, dict):
        return {str(key): sanitize(item) for key, item in value.items()}
    return value


def write_evidence(result: dict[str, Any], report: str) -> None:
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    REPORT_PATH.write_text(report, encoding="utf-8")


def gap(
    gap_id: str,
    label: str,
    *,
    review_focus: str,
    customer_language: list[str],
    positive: list[str],
    negative: list[str],
    next_gap_candidates: list[str],
    universal: list[str],
    qualifications: list[str],
    value_bridge: str | None = None,
) -> dict[str, Any]:
    return {
        "campaign_gap_id": gap_id,
        "label": label,
        "universal_pain_dimensions": universal,
        "qualification_dimensions": qualifications,
        "definition": f"Determine whether {label} is a current constraint.",
        "causal_story": f"If {label} is unresolved, a qualified human should review it before a next step is promised.",
        "customer_language": customer_language,
        "evidence_positive": positive,
        "evidence_negative": negative,
        "diagnostic_questions": [f"Is {label} creating issues today?"],
        "value_bridge": value_bridge or f"A human review should verify {review_focus} before promising fit.",
        "review_focus": review_focus,
        "next_gap_candidates": next_gap_candidates,
    }


def base_campaign(
    *,
    campaign_id: str,
    client_name: str,
    offer: str,
    vertical_id: str,
    human_owner: str,
    appointment_target: str,
    diagnostic_gaps: dict[str, dict[str, Any]],
    extra: dict[str, Any],
) -> dict[str, Any]:
    order = list(diagnostic_gaps)
    campaign = {
        "campaign_id": campaign_id,
        "client_name": client_name,
        "offer_name": offer,
        "product_name": offer,
        "product_or_offer_name": offer,
        "vertical_id": vertical_id,
        "language": "en",
        "objective": "appointment_setting",
        "qualification_goals": ["identify current fit, timing, and safe human next step"],
        "human_followup_owner": human_owner,
        "human_handoff_role": human_owner,
        "appointment_target": appointment_target,
        "specialist_handoff_route": human_owner,
        "target_account_context": {"buyer_role": "the right person for this review"},
        "caller_identity": {
            "representative_name": "Maya",
            "product_relationship": f"calling about {offer}",
        },
        "diagnostic_gaps": diagnostic_gaps,
        "core_diagnostic_gaps": order[:3],
        "gap_order": order,
        "campaign_playbook_id": f"{campaign_id}-playbook",
        "allowed_claims": ["general information and scheduling only"],
        "blocked_claims": ["unsupported guarantee", "unverified outcome promise"],
        "regulated_advice_boundary_text": "Specific promises require human review of verified details.",
    }
    campaign.update(extra)
    return campaign


def synthetic_campaigns() -> dict[str, dict[str, Any]]:
    return {
        "insurance": base_campaign(
            campaign_id="synthetic-insurance-entrypoint-001",
            client_name="Synthetic Insurance Agency",
            offer="Policy Review Call",
            vertical_id="insurance",
            human_owner="licensed insurance specialist",
            appointment_target="licensed coverage review",
            extra={
                "license_boundary": "Licensed staff review coverage and policy details.",
                "allowed_policy_language": ["can schedule a licensed coverage review"],
                "human_review_owner": "licensed insurance specialist",
            },
            diagnostic_gaps={
                "coverage_fit": gap(
                    "coverage_fit",
                    "coverage fit",
                    review_focus="coverage fit against policy details",
                    customer_language=["coverage fit", "coverage", "covered"],
                    positive=["coverage fit is a problem", "coverage is the issue"],
                    negative=["coverage fit is handled", "coverage is fine"],
                    next_gap_candidates=["premium_or_budget", "renewal_or_timing"],
                    universal=["trust_or_risk_concern", "unclear_next_step"],
                    qualifications=["fit", "compliance_or_risk_constraints"],
                ),
                "premium_or_budget": gap(
                    "premium_or_budget",
                    "premium or budget",
                    review_focus="premium and budget pressure",
                    customer_language=["premium", "budget"],
                    positive=["premium is a problem", "premium is the problem", "budget is a problem"],
                    negative=["premium is handled", "premium is fine", "budget is fine"],
                    next_gap_candidates=["coverage_fit", "renewal_or_timing"],
                    universal=["cost_or_time_waste"],
                    qualifications=["budget_or_price_sensitivity"],
                ),
                "renewal_or_timing": gap(
                    "renewal_or_timing",
                    "renewal or timing",
                    review_focus="renewal timing and next-step urgency",
                    customer_language=["renewal", "timing"],
                    positive=["renewal timing is an issue", "timing is a problem"],
                    negative=["renewal timing is handled", "timing is fine"],
                    next_gap_candidates=["coverage_fit", "premium_or_budget"],
                    universal=["delay", "unclear_next_step"],
                    qualifications=["timing"],
                ),
            },
        ),
        "telecom": base_campaign(
            campaign_id="synthetic-telecom-entrypoint-001",
            client_name="Synthetic Telecom Provider",
            offer="Plan Review Call",
            vertical_id="telecom",
            human_owner="telecom plan specialist",
            appointment_target="plan and coverage review",
            extra={
                "service_area_policy": "Coverage and availability require human review against the current service map.",
                "approved_plan_facts": ["can discuss plan fit generally"],
                "account_auth_boundary": "Account-specific terms require an authorized specialist.",
            },
            diagnostic_gaps={
                "coverage_or_availability": gap(
                    "coverage_or_availability",
                    "coverage or availability",
                    review_focus="coverage and availability fit",
                    customer_language=["coverage", "availability"],
                    positive=["coverage is the issue", "coverage is a problem"],
                    negative=["coverage is fine", "coverage is handled"],
                    next_gap_candidates=["plan_fit", "contract_or_switching"],
                    universal=["trust_or_risk_concern", "delay"],
                    qualifications=["fit", "compliance_or_risk_constraints"],
                ),
                "plan_fit": gap(
                    "plan_fit",
                    "plan fit",
                    review_focus="plan fit and usage needs",
                    customer_language=["plan fit", "plan"],
                    positive=["plan fit is a problem", "plan is the problem"],
                    negative=["plan fit is fine", "plan is fine"],
                    next_gap_candidates=["coverage_or_availability", "contract_or_switching"],
                    universal=["customer_experience_friction", "cost_or_time_waste"],
                    qualifications=["fit", "budget_or_price_sensitivity"],
                ),
                "contract_or_switching": gap(
                    "contract_or_switching",
                    "contract or switching",
                    review_focus="contract timing and switching friction",
                    customer_language=["contract", "switching"],
                    positive=["contract switching is a problem", "switching is a problem"],
                    negative=["contract is handled", "switching is fine"],
                    next_gap_candidates=["coverage_or_availability", "plan_fit"],
                    universal=["trust_or_risk_concern", "unclear_next_step"],
                    qualifications=["timing", "contact_path"],
                ),
            },
        ),
        "home_services": base_campaign(
            campaign_id="synthetic-home-services-entrypoint-001",
            client_name="Synthetic Home Services",
            offer="Service Estimate Call",
            vertical_id="home_services",
            human_owner="service advisor",
            appointment_target="service estimate review",
            extra={
                "service_area": "Synthetic local service area",
                "inspection_policy": "Exact scope requires inspection or verified property details.",
                "estimate_policy": "No exact price without property review.",
            },
            diagnostic_gaps={
                "service_need": gap(
                    "service_need",
                    "service need",
                    review_focus="service need and property context",
                    customer_language=["service", "repair", "need"],
                    positive=["service is the issue", "we need service"],
                    negative=["service need is handled", "service is fine"],
                    next_gap_candidates=["scheduling_urgency", "estimate_or_property_details"],
                    universal=["unclear_next_step", "customer_experience_friction"],
                    qualifications=["need_or_pain", "fit"],
                ),
                "scheduling_urgency": gap(
                    "scheduling_urgency",
                    "scheduling urgency",
                    review_focus="schedule urgency",
                    customer_language=["scheduling", "schedule", "urgent"],
                    positive=["scheduling is a problem", "schedule is the issue"],
                    negative=["scheduling is fine", "schedule is handled"],
                    next_gap_candidates=["service_need", "estimate_or_property_details"],
                    universal=["delay"],
                    qualifications=["urgency", "timing"],
                ),
                "estimate_or_property_details": gap(
                    "estimate_or_property_details",
                    "estimate or property details",
                    review_focus="estimate details and property context",
                    customer_language=["estimate", "property details", "price"],
                    positive=["estimate is unclear", "price is unclear"],
                    negative=["estimate is fine", "property details are handled"],
                    next_gap_candidates=["service_need", "scheduling_urgency"],
                    universal=["trust_or_risk_concern", "cost_or_time_waste"],
                    qualifications=["budget_or_price_sensitivity", "compliance_or_risk_constraints"],
                ),
            },
        ),
        "b2b_saas": base_campaign(
            campaign_id="synthetic-b2b-saas-entrypoint-001",
            client_name="Synthetic SaaS Operations",
            offer="Operations Workflow Review",
            vertical_id="b2b_saas",
            human_owner="implementation specialist",
            appointment_target="operations fit review",
            extra={
                "product_category": "operations workflow software",
                "approved_feature_claims": ["can discuss workflow fit at a general level"],
                "integration_claim_policy": "Integration and security claims require technical review.",
            },
            diagnostic_gaps={
                "manual_work": gap(
                    "manual_work",
                    "manual work",
                    review_focus="manual workflow load",
                    customer_language=["manual work", "manual"],
                    positive=["manual work is the problem", "manual work is a problem"],
                    negative=["manual work is handled", "manual work is fine"],
                    next_gap_candidates=["integration_risk", "visibility_gap"],
                    universal=["manual_work", "cost_or_time_waste"],
                    qualifications=["current_solution_or_status_quo", "need_or_pain"],
                ),
                "integration_risk": gap(
                    "integration_risk",
                    "integration risk",
                    review_focus="integration and security review",
                    customer_language=["integration", "security"],
                    positive=["integration is a problem", "security is a concern"],
                    negative=["integration is fine", "security is handled"],
                    next_gap_candidates=["manual_work", "visibility_gap"],
                    universal=["trust_or_risk_concern", "unclear_next_step"],
                    qualifications=["fit", "compliance_or_risk_constraints"],
                ),
                "visibility_gap": gap(
                    "visibility_gap",
                    "visibility gap",
                    review_focus="visibility into workflow status",
                    customer_language=["visibility", "see status"],
                    positive=["visibility is the problem", "visibility is a problem"],
                    negative=["visibility is fine", "visibility is handled"],
                    next_gap_candidates=["manual_work", "integration_risk"],
                    universal=["visibility_gap", "unclear_next_step"],
                    qualifications=["need_or_pain", "authority_or_right_person"],
                ),
            },
        ),
    }


def append_turn(state: dict[str, Any], packet: dict[str, Any]) -> None:
    state.setdefault("turns", []).append(
        {
            "transcript": packet.get("transcript", ""),
            "summary": packet.get("summary", {}),
            "continuity": packet.get("demo_session_continuity") or packet.get("conversation_continuity") or {},
            "conversation_memory": packet.get("demo_conversation_memory") or packet.get("conversation_memory") or {},
            "dialogue_manager": packet.get("dialogue_manager", {}),
            "dialogue_pragmatics": packet.get("dialogue_pragmatics", {}),
        }
    )


def build_packet(transcript: str, campaign: dict[str, Any], state: dict[str, Any], session_id: str) -> dict[str, Any]:
    if entrypoint is None:
        raise RuntimeError(f"generic_campaign_turn import failed: {ENTRYPOINT_IMPORT_ERROR}")
    return entrypoint.build_generic_campaign_turn_packet(
        transcript=transcript,
        campaign=campaign,
        input_type="agent-open" if transcript == "__agent_open__" else "speech-final",
        session_id=session_id,
        session_state=state,
        private_out=TMP_DIR / session_id,
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


def memory(packet: dict[str, Any]) -> dict[str, Any]:
    return dict(packet.get("demo_conversation_memory") or packet.get("conversation_memory") or {})


def semantic_frame(packet: dict[str, Any]) -> dict[str, Any]:
    manager = packet.get("dialogue_manager") or {}
    selected = manager.get("selected_action") or {}
    frame = selected.get("contextual_buyer_semantics") or selected.get("semantic_frame") or {}
    if frame:
        return frame
    if selected.get("semantic"):
        return selected
    return manager.get("contextual_buyer_semantics") or {}


def final_response(packet: dict[str, Any]) -> str:
    return str((packet.get("summary") or {}).get("final_response") or (packet.get("packet") or {}).get("final_response") or "")


def tts_input_text(packet: dict[str, Any]) -> str:
    return str((packet.get("summary") or {}).get("tts_input_text") or (((packet.get("packet") or {}).get("tts_delivery") or {}).get("tts_input_text")) or "")


def snapshot(packet: dict[str, Any]) -> dict[str, Any]:
    frame = semantic_frame(packet)
    packet_body = packet.get("packet") or {}
    tts = packet_body.get("tts_delivery") or {}
    voice = packet_body.get("voice_delivery") or {}
    manager = packet.get("dialogue_manager") or {}
    lead = memory(packet).get("lead_followup_state") or {}
    return sanitize(
        {
            "transcript": packet.get("transcript"),
            "campaign_id": packet.get("campaign_id"),
            "campaign_playbook_id": packet.get("campaign_playbook_id"),
            "semantic": frame.get("semantic"),
            "target_gap": frame.get("target_gap"),
            "playbook_id": frame.get("playbook_id"),
            "playbook_review_focus": frame.get("playbook_review_focus"),
            "outgoing_candidate_gaps": frame.get("outgoing_candidate_gaps"),
            "call_control": (packet.get("summary") or {}).get("call_control"),
            "final_response": final_response(packet),
            "tts_input_text": tts_input_text(packet),
            "lead_followup_state": lead,
            "send_info_state": memory(packet).get("send_info_state"),
            "handoff_target_state": memory(packet).get("handoff_target_state"),
            "audio_url": packet.get("audio_url"),
            "provider_agent_used": packet.get("provider_agent_used"),
            "durable_provider_agent_created": packet.get("durable_provider_agent_created"),
            "voice_cloning_used": packet.get("voice_cloning_used"),
            "provider_calls_made": bool(tts.get("provider_calls_made") or voice.get("provider_calls_made") or packet_body.get("api_calls_made")),
            "local_llm_calls_made": bool(manager.get("local_llm_calls_made") or packet_body.get("llm_used")),
            "sends_email": bool((lead.get("safety") or {}).get("sends_email")),
            "creates_calendar_event": bool((lead.get("safety") or {}).get("creates_calendar_event")),
            "writes_crm": bool((lead.get("safety") or {}).get("writes_crm")),
            "opens_prod_102": bool(packet.get("opens_prod_102") or manager.get("opens_prod_102")),
        }
    )


def assert_no_forbidden_text(failures: list[str], packet: dict[str, Any], label: str) -> None:
    texts = {"final_response": final_response(packet), "tts_input_text": tts_input_text(packet)}
    terms = FORBIDDEN_BRAND_TERMS + FORBIDDEN_ROUTE_PHRASES
    for text_name, text in texts.items():
        found = [term for term in terms if term.lower() in text.lower()]
        assert_condition(failures, not found, f"{label}: {text_name} leaked forbidden wording {found}: {sanitize(text)}")


def assert_packet_safety(failures: list[str], packet: dict[str, Any], label: str) -> None:
    snap = snapshot(packet)
    for key in SAFETY_KEYS:
        assert_condition(failures, snap.get(key) is False, f"{label}: {key} must be false: {snap}")
    assert_condition(failures, snap.get("provider_agent_used") is False, f"{label}: provider agent must be false: {snap}")
    assert_condition(failures, snap.get("durable_provider_agent_created") is False, f"{label}: durable provider agent must be false: {snap}")
    assert_condition(failures, snap.get("voice_cloning_used") is False, f"{label}: voice cloning must be false: {snap}")
    assert_condition(failures, snap.get("audio_url") in (None, ""), f"{label}: dry-run audio_url must be null/absent: {snap}")


def assert_generic_playbook(failures: list[str], packet: dict[str, Any], campaign: dict[str, Any], label: str) -> None:
    playbook = adapter.resolve_campaign_playbook(campaign)
    frame = semantic_frame(packet)
    expected = playbook.get("campaign_playbook_id")
    assert_condition(failures, expected != ROUTESIGNAL_PLAYBOOK_ID, f"{label}: generic playbook resolved to RouteSignal")
    assert_condition(failures, packet.get("campaign_playbook_id") == expected, f"{label}: packet playbook mismatch: {snapshot(packet)}")
    if frame.get("playbook_id"):
        assert_condition(failures, frame.get("playbook_id") == expected, f"{label}: semantic playbook mismatch: {snapshot(packet)}")
    target_gap = frame.get("target_gap")
    if target_gap:
        assert_condition(failures, target_gap in set(playbook.get("diagnostic_gaps") or {}), f"{label}: target_gap not in campaign gaps: {snapshot(packet)}")
        assert_condition(failures, target_gap not in ROUTESIGNAL_GAP_IDS, f"{label}: target_gap leaked RouteSignal gap: {snapshot(packet)}")
        expected_focus = (playbook.get("diagnostic_gaps") or {}).get(target_gap, {}).get("review_focus")
        assert_condition(failures, frame.get("playbook_review_focus") == expected_focus, f"{label}: review_focus mismatch: {snapshot(packet)}")


def assert_common_packet(failures: list[str], packet: dict[str, Any], campaign: dict[str, Any], label: str) -> None:
    assert_generic_playbook(failures, packet, campaign, label)
    assert_no_forbidden_text(failures, packet, label)
    assert_packet_safety(failures, packet, label)


def assert_semantic(failures: list[str], packet: dict[str, Any], expected: str | set[str], label: str, target_gap: str | None = None) -> None:
    frame = semantic_frame(packet)
    expected_set = {expected} if isinstance(expected, str) else expected
    assert_condition(failures, frame.get("semantic") in expected_set, f"{label}: semantic mismatch: {snapshot(packet)}")
    if target_gap:
        assert_condition(failures, frame.get("target_gap") == target_gap, f"{label}: target gap mismatch: {snapshot(packet)}")


def assert_email_hash_present(failures: list[str], state: dict[str, Any], label: str) -> None:
    serialized = json.dumps(sanitize(state), sort_keys=True)
    assert_condition(failures, "<email:sha256_12:" in serialized, f"{label}: redacted email hash token missing: {serialized}")
    for raw in RAW_EMAILS:
        assert_condition(failures, raw not in serialized, f"{label}: raw email leaked into public snapshot")


def validate_import_contract(failures: list[str], evidence: dict[str, Any]) -> None:
    evidence["helper_import"] = {
        "module": "runtime.entrypoints.generic_campaign_turn",
        "imported": entrypoint is not None,
        "import_error": ENTRYPOINT_IMPORT_ERROR,
    }
    assert_condition(failures, entrypoint is not None, f"helper import failed: {ENTRYPOINT_IMPORT_ERROR}")
    if entrypoint is None:
        return
    helper = getattr(entrypoint, "build_generic_campaign_turn_packet", None)
    evidence["helper_import"]["build_generic_campaign_turn_packet_exists"] = callable(helper)
    assert_condition(failures, callable(helper), "build_generic_campaign_turn_packet missing")
    if callable(helper):
        signature = inspect.signature(helper)
        evidence["helper_import"]["signature"] = str(signature)
        assert_condition(failures, "campaign" in signature.parameters, "helper must accept campaign")
        assert_condition(failures, "cases_path" not in signature.parameters, "generic helper must not require cases_path lookup")
        assert_condition(failures, str(getattr(helper, "__module__", "")) == "runtime.entrypoints.generic_campaign_turn", "helper must be runtime entrypoint, not test-only")


def validate_insurance_happy_path(failures: list[str], evidence: dict[str, Any], campaign: dict[str, Any]) -> None:
    packets = run_sequence("insurance-happy-path", campaign, ["__agent_open__", "yeah sure", "premium is a problem", "tomorrow at 3 works"])
    evidence["insurance_happy_path"] = [snapshot(packet) for packet in packets]
    for index, packet in enumerate(packets, start=1):
        assert_common_packet(failures, packet, campaign, f"insurance_turn{index}")
    assert_condition(failures, semantic_frame(packets[1]).get("outgoing_candidate_gaps") == campaign["core_diagnostic_gaps"], f"insurance_turn2: outgoing gaps mismatch: {snapshot(packets[1])}")
    assert_semantic(failures, packets[2], "pain_confirmed", "insurance_turn3", "premium_or_budget")
    assert_condition(failures, (packets[2].get("summary") or {}).get("call_control") != "schedule-and-end", f"insurance_turn3: must not schedule before time: {snapshot(packets[2])}")
    assert_semantic(failures, packets[3], {"appointment_time_confirmed", "appointment_time_given"}, "insurance_turn4")
    lead = memory(packets[3]).get("lead_followup_state") or {}
    appointment = lead.get("appointment") or {}
    callback = lead.get("callback") or {}
    normalized = callback.get("normalized") or {}
    assert_condition(failures, (packets[3].get("summary") or {}).get("call_control") == "schedule-and-end", f"insurance_turn4: usable time should schedule-and-end: {snapshot(packets[3])}")
    assert_condition(failures, appointment.get("confirmed") is True, f"insurance_turn4: appointment must be confirmed: {snapshot(packets[3])}")
    assert_condition(failures, "3" in str(normalized.get("time_text") or ""), f"insurance_turn4: normalized time missing: {snapshot(packets[3])}")


def validate_telecom_send_info(failures: list[str], evidence: dict[str, Any], campaign: dict[str, Any]) -> None:
    packets = run_sequence("telecom-send-info", campaign, ["__agent_open__", "yeah sure", "send me details", "send it to alex@example.com"])
    evidence["telecom_send_info"] = [snapshot(packet) for packet in packets]
    for index, packet in enumerate(packets, start=1):
        assert_common_packet(failures, packet, campaign, f"telecom_turn{index}")
    assert_semantic(failures, packets[2], "send_info_request", "telecom_turn3")
    assert_condition(failures, (memory(packets[2]).get("send_info_state") or {}).get("capture_status") == "needs_email_or_callback_time", f"telecom_turn3: send_info_state did not open: {snapshot(packets[2])}")
    assert_semantic(failures, packets[3], "email_provided", "telecom_turn4")
    assert_email_hash_present(failures, evidence["telecom_send_info"][-1], "telecom_turn4")
    assert_condition(failures, (memory(packets[3]).get("lead_followup_state") or {}).get("capture_status") == "email_captured", f"telecom_turn4: email not captured: {snapshot(packets[3])}")
    assert_condition(failures, (packets[3].get("summary") or {}).get("call_control") != "schedule-and-end", f"telecom_turn4: email-only must not schedule-and-end: {snapshot(packets[3])}")


def validate_home_services_caution(failures: list[str], evidence: dict[str, Any], campaign: dict[str, Any]) -> None:
    packets = run_sequence("home-services-caution", campaign, ["__agent_open__", "yeah sure", "can you give exact price without looking?"])
    evidence["home_services_regulated_caution"] = [snapshot(packet) for packet in packets]
    for index, packet in enumerate(packets, start=1):
        assert_common_packet(failures, packet, campaign, f"home_services_turn{index}")
    response = normalize(final_response(packets[-1]))
    assert_condition(failures, any(term in response for term in ["cannot", "can't", "human review", "inspection", "property"]), f"home_services_turn3: caution wording missing: {snapshot(packets[-1])}")
    assert_condition(failures, "exact price is" not in response and "will cost" not in response, f"home_services_turn3: unsupported quote wording: {snapshot(packets[-1])}")


def validate_b2b_right_person(failures: list[str], evidence: dict[str, Any], campaign: dict[str, Any]) -> None:
    packets = run_sequence("b2b-right-person", campaign, ["__agent_open__", "yeah sure", "operations handles that", "send it to ops@example.com"])
    evidence["b2b_right_person"] = [snapshot(packet) for packet in packets]
    for index, packet in enumerate(packets, start=1):
        assert_common_packet(failures, packet, campaign, f"b2b_turn{index}")
    assert_semantic(failures, packets[2], {"department_named", "wrong_person_or_wrong_department"}, "b2b_turn3")
    handoff = memory(packets[2]).get("handoff_target_state") or {}
    assert_condition(failures, (handoff.get("target") or {}).get("role_or_department") == "operations", f"b2b_turn3: department not captured: {snapshot(packets[2])}")
    assert_condition(failures, memory(packets[2]).get("selected_gap") != "routing", f"b2b_turn3: product routing gap selected incorrectly: {snapshot(packets[2])}")
    assert_semantic(failures, packets[3], "right_person_email_provided", "b2b_turn4")
    assert_email_hash_present(failures, evidence["b2b_right_person"][-1], "b2b_turn4")
    final_handoff = memory(packets[3]).get("handoff_target_state") or {}
    assert_condition(failures, final_handoff.get("lead_status") == "open_send_info_to_right_person", f"b2b_turn4: handoff lead status mismatch: {snapshot(packets[3])}")


def validate_invalid_campaign(failures: list[str], evidence: dict[str, Any]) -> None:
    if entrypoint is None:
        evidence["invalid_campaign"] = {"handled": False, "reason": "entrypoint missing"}
        return
    invalid_campaign = {
        "campaign_id": "synthetic-invalid-001",
        "vertical_id": "insurance",
        "client_name": "Synthetic Invalid",
        "offer_name": "Invalid Review",
        "product_or_offer_name": "Invalid Review",
        "allowed_claims": ["general information only"],
        "blocked_claims": ["unsupported guarantee"],
        "human_followup_owner": "licensed insurance specialist",
        "appointment_target": "licensed coverage review",
    }
    try:
        packet = entrypoint.build_generic_campaign_turn_packet(
            transcript="__agent_open__",
            campaign=invalid_campaign,
            input_type="agent-open",
            session_id="invalid-campaign",
            session_state={"turns": []},
            private_out=TMP_DIR / "invalid-campaign",
            live_tts=False,
            force_key_missing=True,
        )
    except ValueError as exc:
        message = str(exc)
        evidence["invalid_campaign"] = sanitize({"handled": "controlled_value_error", "message": message})
        assert_condition(failures, ROUTESIGNAL_PLAYBOOK_ID not in message, f"invalid_campaign: error must not fall back to RouteSignal: {message}")
        assert_condition(failures, "routesignal" not in message.lower(), f"invalid_campaign: error leaked RouteSignal wording: {message}")
        return
    evidence["invalid_campaign"] = snapshot(packet)
    snap = snapshot(packet)
    assert_condition(failures, snap.get("playbook_id") != ROUTESIGNAL_PLAYBOOK_ID, f"invalid_campaign: returned RouteSignal playbook: {snap}")
    assert_condition(failures, "routesignal" not in normalize(snap.get("final_response")), f"invalid_campaign: produced RouteSignal opening: {snap}")
    assert_condition(failures, bool((packet.get("validation") or {}).get("valid") is False), f"invalid_campaign: must expose validation failure or raise ValueError: {snap}")


def validate_routesignal_preservation(failures: list[str], evidence: dict[str, Any]) -> None:
    from scripts.run_live_demo_001_agent_voice_call import (  # noqa: E402
        DEFAULT_CAMPAIGN_ID,
        DEFAULT_CASES_PATH,
        DEFAULT_STAGE,
        build_turn_packet,
    )

    state: dict[str, Any] = {"turns": []}
    packets: list[dict[str, Any]] = []
    for transcript in ["__agent_open__", "yeah sure", "callbacks are fine"]:
        packet = build_turn_packet(
            transcript=transcript,
            campaign_id=DEFAULT_CAMPAIGN_ID,
            stage=DEFAULT_STAGE,
            input_type="agent-open" if transcript == "__agent_open__" else "speech-final",
            silence_count=0,
            cases_path=DEFAULT_CASES_PATH,
            private_out=TMP_DIR / "routesignal",
            live_tts=False,
            force_key_missing=True,
            timeout_seconds=8.0,
            session_id="generic-runtime-entrypoint-routesignal",
            session_state=state,
            asr_confidence=0.94,
            voice_turn_state="listening",
        )
        packets.append(packet)
        append_turn(state, packet)
    evidence["routesignal_preservation"] = [snapshot(packet) for packet in packets]
    final = evidence["routesignal_preservation"][-1]
    assert_condition(failures, final.get("semantic") == "current_gap_clear", f"routesignal: callbacks clear semantic changed: {final}")
    assert_condition(failures, final.get("target_gap") == "callbacks", f"routesignal: callbacks target gap changed: {final}")
    assert_condition(failures, final.get("playbook_id") == ROUTESIGNAL_PLAYBOOK_ID, f"routesignal: playbook changed: {final}")
    assert_condition(failures, "manual tracking" in normalize(final.get("final_response")), f"routesignal: manual_tracking remaining behavior changed: {final}")
    assert_condition(failures, "handoffs" in normalize(final.get("final_response")), f"routesignal: handoffs remaining behavior changed: {final}")


def validate_runtime_entrypoint(failures: list[str], evidence: dict[str, Any]) -> None:
    validate_import_contract(failures, evidence)
    if entrypoint is None:
        return
    campaigns = synthetic_campaigns()
    evidence["synthetic_campaigns"] = {
        label: {
            "campaign_id": campaign["campaign_id"],
            "vertical_id": campaign["vertical_id"],
            "campaign_playbook_id": adapter.resolve_campaign_playbook(campaign).get("campaign_playbook_id"),
            "core_diagnostic_gaps": list(campaign.get("core_diagnostic_gaps") or []),
        }
        for label, campaign in campaigns.items()
    }
    validate_insurance_happy_path(failures, evidence, campaigns["insurance"])
    validate_telecom_send_info(failures, evidence, campaigns["telecom"])
    validate_home_services_caution(failures, evidence, campaigns["home_services"])
    validate_b2b_right_person(failures, evidence, campaigns["b2b_saas"])


def render_report(result: dict[str, Any]) -> str:
    lines = [
        "# GENERIC-CAMPAIGN-RUNTIME-ENTRYPOINT-001",
        "",
        f"Status: {result['status']}",
        f"Failure count: {len(result.get('failures') or [])}",
        "",
        "## Contract",
        "",
        f"- Helper imported: `{str((result.get('evidence') or {}).get('helper_import', {}).get('imported')).lower()}`",
        "- Helper accepts in-memory campaign configs and does not require cases_path lookup.",
        "- Live TTS/provider calls remain disabled by default.",
        "",
        "## Synthetic Scenarios",
        "",
        "- Insurance happy path: open, permission, premium pain, usable appointment time.",
        "- Telecom send-info path with redacted synthetic email evidence.",
        "- Home-services regulated caution for exact-price request.",
        "- B2B SaaS right-person path with department and redacted synthetic email evidence.",
        "- Invalid generic campaign does not fall back to RouteSignal.",
        "- RouteSignal live-demo build_turn_packet preservation.",
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
    validate_runtime_entrypoint(failures, evidence)
    validate_invalid_campaign(failures, evidence)
    validate_routesignal_preservation(failures, evidence)
    result = sanitize(
        {
            "checkpoint_id": CHECKPOINT_ID,
            "status": "pass" if not failures else "fail",
            "failures": failures,
            "evidence": evidence,
            "forbidden_terms_checked": FORBIDDEN_BRAND_TERMS + FORBIDDEN_ROUTE_PHRASES,
            "raw_synthetic_emails_in_public_evidence": any(raw in json.dumps(sanitize(evidence)).lower() for raw in RAW_EMAILS),
            "phase_1_2_3_backpatch_required": False,
            "safety_assertions": {key: False for key in SAFETY_KEYS},
            "uses_provider_calls": False,
            "uses_live_tts": False,
            "uses_real_customer_data": False,
            "uses_cases_path_lookup_for_generic_campaigns": False,
        }
    )
    serialized = json.dumps(result).lower()
    for raw in RAW_EMAILS:
        if raw in serialized:
            failures.append(f"public generated evidence leaked raw synthetic email {raw}")
    result["failures"] = failures
    result["status"] = "pass" if not failures else "fail"
    result["raw_synthetic_emails_in_public_evidence"] = any(raw in json.dumps(result).lower() for raw in RAW_EMAILS)
    write_evidence(result, render_report(result))
    if failures:
        print(json.dumps(result, indent=2, sort_keys=True))
        return 1
    print(f"{CHECKPOINT_ID}: pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
