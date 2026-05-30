#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.core import campaign_playbook_adapter as adapter  # noqa: E402
from runtime.core import contextual_buyer_semantics as semantics  # noqa: E402
from runtime.core import dialogue_manager  # noqa: E402
from scripts.run_live_demo_001_agent_voice_call import (  # noqa: E402
    DEFAULT_CAMPAIGN_ID,
    DEFAULT_CASES_PATH,
    DEFAULT_STAGE,
    build_turn_packet,
)


CHECKPOINT_ID = "CONTEXTUAL-BUYER-SEMANTICS-011-campaign-adapter-runtime"
GENERATED_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
RESULT_PATH = GENERATED_DIR / "result.json"
REPORT_PATH = GENERATED_DIR / "report.md"
TMP_DIR = ROOT / ".tmp" / CHECKPOINT_ID

ROUTESIGNAL_PLAYBOOK_ID = "ROUTESIGNAL-DIAGNOSTIC-PLAYBOOK-001"
FORBIDDEN_ROUTESIGNAL_TEXT = ["RouteSignal", "Northstar", "Starter", "Growth", "$29", "$59"]
SAFETY_KEYS = [
    "provider_calls_made",
    "local_llm_calls_made",
    "sends_email",
    "creates_calendar_event",
    "writes_crm",
    "opens_prod_102",
]


def normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9$@.]+", " ", str(text).lower()).strip()


def assert_condition(failures: list[str], condition: bool, message: str) -> None:
    if not condition:
        failures.append(message)


def write_evidence(result: dict[str, Any], report: str) -> None:
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    REPORT_PATH.write_text(report, encoding="utf-8")


def gap(
    gap_id: str,
    label: str,
    pains: list[str],
    qualifications: list[str],
    next_gap_candidates: list[str],
    *,
    review_focus: str | None = None,
    customer_language: list[str] | None = None,
    positive: list[str] | None = None,
    negative: list[str] | None = None,
) -> dict[str, Any]:
    readable = label.replace("_", " ")
    return {
        "label": label,
        "universal_pain_dimensions": pains,
        "qualification_dimensions": qualifications,
        "definition": f"Determine whether {readable} is a real current campaign constraint.",
        "causal_story": f"If {readable} is unresolved, a qualified human should review it before a next step is promised.",
        "customer_language": customer_language or [readable],
        "evidence_positive": positive or [f"{readable} is a problem", f"{readable} is the issue"],
        "evidence_negative": negative or [f"{readable} is handled", f"{readable} is fine"],
        "diagnostic_questions": [f"Is {readable} creating issues today?"],
        "value_bridge": f"The useful next step is a cautious human review of {readable}, without unsupported claims.",
        "review_focus": review_focus or readable,
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
    blocked_claims: list[str],
    gaps: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    order = list(gaps)
    return {
        "campaign_id": campaign_id,
        "client_name": client_name,
        "product_or_offer_name": offer,
        "vertical_id": vertical_id,
        "language": "en",
        "objective": "appointment_setting",
        "human_followup_owner": human_owner,
        "appointment_target": appointment_target,
        "allowed_claims": ["can collect general fit and review needs"],
        "blocked_claims": blocked_claims,
        "diagnostic_gaps": gaps,
        "core_diagnostic_gaps": order[:3],
        "gap_order": order,
        "campaign_playbook_id": f"{campaign_id}-playbook",
    }


def synthetic_campaigns() -> dict[str, dict[str, Any]]:
    return {
        "insurance": campaign(
            campaign_id="synthetic-insurance-contextual-011",
            client_name="Synthetic Insurance Agency",
            offer="Policy Review Call",
            vertical_id="insurance",
            human_owner="licensed insurance specialist",
            appointment_target="licensed coverage review",
            blocked_claims=["coverage guarantee", "premium savings guarantee", "eligibility decision", "claim outcome promise"],
            gaps={
                "coverage_fit": gap(
                    "coverage_fit",
                    "coverage fit",
                    ["trust_or_risk_concern", "unclear_next_step"],
                    ["need_or_pain", "fit", "compliance_or_risk_constraints"],
                    ["premium_or_budget"],
                    review_focus="licensed coverage fit review",
                    customer_language=["coverage fit", "coverage"],
                    positive=["coverage fit is a problem", "coverage is the issue"],
                    negative=["coverage fit is handled", "coverage is handled"],
                ),
                "premium_or_budget": gap(
                    "premium_or_budget",
                    "premium or budget",
                    ["cost_or_time_waste", "trust_or_risk_concern"],
                    ["budget_or_price_sensitivity", "fit"],
                    ["renewal_or_timing"],
                    review_focus="premium and budget review",
                    customer_language=["premium", "budget", "premium or budget"],
                    positive=["premium is a problem", "budget is a problem"],
                    negative=["premium is fine", "budget is handled"],
                ),
                "renewal_or_timing": gap(
                    "renewal_or_timing",
                    "renewal or timing",
                    ["delay", "unclear_next_step"],
                    ["timing", "urgency", "contact_path"],
                    [],
                    review_focus="renewal timing review",
                    customer_language=["renewal", "timing"],
                ),
            },
        ),
        "telecom": campaign(
            campaign_id="synthetic-telecom-contextual-011",
            client_name="Synthetic Telecom Provider",
            offer="Plan Review Call",
            vertical_id="telecom",
            human_owner="telecom account specialist",
            appointment_target="human plan and availability review",
            blocked_claims=["coverage guarantee", "speed guarantee", "contract cancellation guarantee"],
            gaps={
                "coverage_or_availability": gap(
                    "coverage_or_availability",
                    "coverage or availability",
                    ["trust_or_risk_concern", "delay"],
                    ["fit", "compliance_or_risk_constraints"],
                    ["plan_fit"],
                    review_focus="coverage and availability review",
                    customer_language=["coverage", "availability"],
                    positive=["coverage is the issue", "availability is the issue"],
                    negative=["coverage is fine", "availability is handled"],
                ),
                "plan_fit": gap(
                    "plan_fit",
                    "plan fit",
                    ["customer_experience_friction", "cost_or_time_waste"],
                    ["need_or_pain", "fit", "budget_or_price_sensitivity"],
                    ["contract_or_switching"],
                    review_focus="plan-fit review",
                    customer_language=["plan fit", "plan"],
                    positive=["plan fit is the problem", "plan is a problem"],
                    negative=["plan fit is fine", "plan is fine"],
                ),
                "contract_or_switching": gap(
                    "contract_or_switching",
                    "contract or switching",
                    ["unclear_next_step", "trust_or_risk_concern"],
                    ["timing", "contact_path", "compliance_or_risk_constraints"],
                    [],
                    review_focus="contract and switching review",
                    customer_language=["contract", "switching"],
                ),
            },
        ),
        "home_services": campaign(
            campaign_id="synthetic-home-services-contextual-011",
            client_name="Synthetic Home Services",
            offer="Inspection Scheduling Call",
            vertical_id="home_services",
            human_owner="qualified service coordinator",
            appointment_target="inspection or estimate review",
            blocked_claims=["exact quote without inspection", "remote safety diagnosis"],
            gaps={
                "service_need": gap(
                    "service_need",
                    "service need",
                    ["customer_experience_friction", "unclear_next_step"],
                    ["need_or_pain", "fit"],
                    ["scheduling_urgency"],
                    review_focus="service-need review",
                    customer_language=["service need", "service"],
                ),
                "scheduling_urgency": gap(
                    "scheduling_urgency",
                    "scheduling urgency",
                    ["delay", "trust_or_risk_concern"],
                    ["urgency", "timing", "contact_path"],
                    ["estimate_or_property_details"],
                    review_focus="scheduling urgency review",
                    customer_language=["scheduling", "schedule", "urgency"],
                    positive=["scheduling is a problem", "schedule is the issue"],
                    negative=["scheduling is fine", "schedule is fine"],
                ),
                "estimate_or_property_details": gap(
                    "estimate_or_property_details",
                    "estimate or property details",
                    ["trust_or_risk_concern", "unclear_next_step"],
                    ["fit", "compliance_or_risk_constraints"],
                    [],
                    review_focus="estimate and property detail review",
                    customer_language=["estimate", "property details"],
                    positive=["the estimate is unclear", "property details are unclear"],
                    negative=["the estimate is handled", "property details are fine"],
                ),
            },
        ),
        "b2b_saas": campaign(
            campaign_id="synthetic-b2b-saas-contextual-011",
            client_name="Synthetic SaaS Operations",
            offer="Workflow Fit Review",
            vertical_id="b2b_saas",
            human_owner="technical fit specialist",
            appointment_target="human fit and technical review",
            blocked_claims=["unverified integration claim", "unverified security claim", "ROI guarantee"],
            gaps={
                "manual_work": gap(
                    "manual_work",
                    "manual work",
                    ["manual_work", "cost_or_time_waste"],
                    ["need_or_pain", "current_solution_or_status_quo", "fit"],
                    ["integration_risk"],
                    review_focus="manual-work review",
                    customer_language=["manual work", "manual"],
                    positive=["manual work is a problem", "manual is the problem"],
                    negative=["manual work is handled", "manual is handled"],
                ),
                "integration_risk": gap(
                    "integration_risk",
                    "integration risk",
                    ["trust_or_risk_concern", "unclear_next_step"],
                    ["fit", "compliance_or_risk_constraints"],
                    ["visibility_gap"],
                    review_focus="integration-risk review",
                    customer_language=["integration", "integration risk"],
                    positive=["integration risk is a problem", "integration is the issue"],
                    negative=["integration risk is handled", "integration is fine"],
                ),
                "visibility_gap": gap(
                    "visibility_gap",
                    "visibility gap",
                    ["visibility_gap", "unclear_next_step"],
                    ["need_or_pain", "authority_or_right_person", "fit"],
                    [],
                    review_focus="visibility-gap review",
                    customer_language=["visibility", "visibility gap"],
                    positive=["visibility is the problem", "visibility gap is a problem"],
                    negative=["visibility is handled", "visibility gap is handled"],
                ),
            },
        ),
    }


def seed_permission_state() -> dict[str, Any]:
    return {
        "turns": [
            {
                "transcript": "__agent_open__",
                "summary": {"final_response": "Do you have a minute for one quick question?", "call_control": "continue-call"},
                "continuity": {"applied": True, "reason": "seed_permission_check", "dialogue_focus": "qualification"},
                "conversation_memory": {},
                "dialogue_manager": {},
                "dialogue_pragmatics": {},
            }
        ]
    }


def append_semantic_turn(state: dict[str, Any], transcript: str, frame: dict[str, Any]) -> None:
    memory = {
        "last_customer_intent": frame.get("semantic"),
        "selected_gap": frame.get("target_gap"),
        "active_gap_scope": frame.get("active_gap_scope"),
        "candidate_gaps": list(frame.get("candidate_gaps") or []),
        "outgoing_question_type": frame.get("outgoing_question_type"),
        "outgoing_candidate_gaps": list(frame.get("outgoing_candidate_gaps") or []),
        "outgoing_active_gap_scope": frame.get("outgoing_active_gap_scope"),
        "playbook_id": frame.get("playbook_id"),
        "playbook_review_focus": frame.get("playbook_review_focus"),
        "playbook_supported_gap_ids": list(frame.get("playbook_supported_gap_ids") or []),
    }
    if frame.get("cleared_gaps"):
        memory["cleared_gaps"] = list(frame.get("cleared_gaps") or [])
    if frame.get("confirmed_gaps"):
        memory["confirmed_gaps"] = list(frame.get("confirmed_gaps") or [])
    state.setdefault("turns", []).append(
        {
            "transcript": transcript,
            "summary": {"final_response": str(frame.get("candidate_response") or ""), "call_control": "continue-call"},
            "continuity": {"applied": bool(frame.get("applied")), "reason": str(frame.get("semantic") or ""), "dialogue_focus": frame.get("dialogue_focus")},
            "conversation_memory": memory,
            "dialogue_manager": {"contextual_buyer_semantics": frame},
            "dialogue_pragmatics": {},
        }
    )


def direct_frame(transcript: str, state: dict[str, Any], campaign_config: dict[str, Any]) -> dict[str, Any]:
    return semantics.classify_contextual_buyer_semantics(
        transcript,
        state,
        campaign_config,
        dialogue_reasoning={"validator": CHECKPOINT_ID, "provider_calls_made": False, "local_llm_calls_made": False},
    )


def planned_action(transcript: str, state: dict[str, Any], campaign_config: dict[str, Any]) -> dict[str, Any]:
    return dialogue_manager.plan_dialogue_action(
        transcript=transcript,
        session_state=state,
        campaign=campaign_config,
        quality_gate={"accepted": True, "reason": "validator_synthetic"},
        dialogue_reasoning={"validator": CHECKPOINT_ID, "provider_calls_made": False, "local_llm_calls_made": False},
    )


def action_frame(action: dict[str, Any]) -> dict[str, Any]:
    return dict((action.get("state_before") or {}).get("contextual_buyer_semantics") or {})


def response_text(value: dict[str, Any]) -> str:
    if "summary" in value:
        return str((value.get("summary") or {}).get("final_response") or "")
    return str(value.get("candidate_response") or value.get("final_response") or "")


def contains_forbidden(value: Any) -> list[str]:
    text = json.dumps(value, sort_keys=True)
    return [item for item in FORBIDDEN_ROUTESIGNAL_TEXT if item in text]


def assert_no_forbidden_response(failures: list[str], value: dict[str, Any], label: str) -> None:
    response = response_text(value)
    forbidden = [item for item in FORBIDDEN_ROUTESIGNAL_TEXT if item.lower() in response.lower()]
    assert_condition(failures, not forbidden, f"{label}: response must not contain RouteSignal-specific wording {forbidden}: {response}")


def assert_frame_safety(failures: list[str], frame: dict[str, Any], label: str) -> None:
    assert_condition(failures, frame.get("provider_calls_made") is False, f"{label}: provider_calls_made must be false: {frame}")
    assert_condition(failures, frame.get("local_llm_calls_made") is False, f"{label}: local_llm_calls_made must be false: {frame}")
    assert_condition(failures, frame.get("opens_prod_102") is False, f"{label}: opens_prod_102 must be false: {frame}")
    safety = (frame.get("playbook") or {}).get("safety") or {}
    for key in SAFETY_KEYS:
        if key in safety:
            assert_condition(failures, safety.get(key) is False, f"{label}: playbook safety {key} must be false: {frame}")


def assert_synthetic_frame(
    failures: list[str],
    frame: dict[str, Any],
    campaign_config: dict[str, Any],
    label: str,
    *,
    expected_semantic: str | None = None,
    expected_gap: str | None = None,
) -> None:
    playbook = adapter.resolve_campaign_playbook(campaign_config)
    expected_playbook_id = playbook.get("campaign_playbook_id")
    campaign_gaps = set(playbook.get("diagnostic_gaps") or {})
    assert_condition(failures, frame.get("playbook_id") == expected_playbook_id, f"{label}: semantic frame playbook_id must match synthetic campaign playbook id: {frame}")
    assert_condition(failures, frame.get("playbook_id") != ROUTESIGNAL_PLAYBOOK_ID, f"{label}: synthetic frame must not use RouteSignal playbook: {frame}")
    if expected_semantic:
        assert_condition(failures, frame.get("semantic") == expected_semantic, f"{label}: expected semantic {expected_semantic}, got {frame.get('semantic')}: {frame}")
    if expected_gap:
        assert_condition(failures, frame.get("target_gap") == expected_gap, f"{label}: expected target_gap {expected_gap}, got {frame.get('target_gap')}: {frame}")
        assert_condition(failures, expected_gap in campaign_gaps, f"{label}: expected gap must be in campaign gaps: {frame}")
        assert_condition(failures, frame.get("playbook_review_focus") == (playbook.get("diagnostic_gaps") or {}).get(expected_gap, {}).get("review_focus"), f"{label}: review_focus must come from synthetic gap: {frame}")
    target_gap = frame.get("target_gap")
    if target_gap:
        assert_condition(failures, target_gap in campaign_gaps, f"{label}: target_gap must be a synthetic campaign gap: {frame}")
        assert_condition(failures, target_gap not in {"callbacks", "manual_tracking", "handoffs"}, f"{label}: target_gap leaked RouteSignal core gap: {frame}")
    assert_no_forbidden_response(failures, frame, label)
    assert_frame_safety(failures, frame, label)


def validate_synthetic_campaigns(failures: list[str], evidence: dict[str, Any]) -> None:
    tests = {
        "insurance": [
            ("coverage fit is handled", "current_gap_clear", "coverage_fit"),
            ("premium is a problem", "pain_confirmed", "premium_or_budget"),
        ],
        "telecom": [
            ("coverage is the issue", "pain_confirmed", "coverage_or_availability"),
            ("plan fit is fine", "current_gap_clear", "plan_fit"),
        ],
        "home_services": [
            ("the estimate is unclear", "pain_confirmed", "estimate_or_property_details"),
            ("scheduling is fine", "current_gap_clear", "scheduling_urgency"),
        ],
        "b2b_saas": [
            ("manual work is handled", "current_gap_clear", "manual_work"),
            ("visibility is the problem", "pain_confirmed", "visibility_gap"),
        ],
    }
    for label, campaign_config in synthetic_campaigns().items():
        playbook = adapter.resolve_campaign_playbook(campaign_config)
        core = list(playbook.get("core_diagnostic_gaps") or [])
        evidence[label] = {
            "campaign_playbook_id": playbook.get("campaign_playbook_id"),
            "vertical_id": playbook.get("vertical_id"),
            "core_diagnostic_gaps": core,
            "regulated_cautions": playbook.get("regulated_cautions") or (playbook.get("campaign_context") or {}).get("regulated_cautions") or [],
            "turns": {},
        }
        assert_condition(failures, playbook.get("campaign_playbook_id") != ROUTESIGNAL_PLAYBOOK_ID, f"{label}: resolved playbook must not be RouteSignal")
        assert_condition(failures, set(core) == set((campaign_config.get("core_diagnostic_gaps") or [])), f"{label}: core gaps must come from campaign config")

        state = seed_permission_state()
        permission_frame = direct_frame("yeah sure", state, campaign_config)
        evidence[label]["turns"]["permission_acknowledgement"] = permission_frame
        assert_synthetic_frame(failures, permission_frame, campaign_config, f"{label}:permission", expected_semantic="permission_acknowledgement")
        assert_condition(failures, permission_frame.get("outgoing_candidate_gaps") == core, f"{label}: permission outgoing candidate gaps must be campaign core gaps: {permission_frame}")
        assert_condition(failures, permission_frame.get("outgoing_active_gap_scope") == "campaign_relevance", f"{label}: permission outgoing active gap scope must be campaign_relevance: {permission_frame}")
        append_semantic_turn(state, "yeah sure", permission_frame)

        manager_action = planned_action("yeah sure", seed_permission_state(), campaign_config)
        manager_frame = action_frame(manager_action)
        manager_memory = dialogue_manager.build_conversation_memory(
            action=manager_action,
            session_state=seed_permission_state(),
            transcript="yeah sure",
            final_response=response_text(manager_action),
            campaign=campaign_config,
        )
        evidence[label]["turns"]["manager_permission_acknowledgement"] = {
            "selected_action": manager_action.get("selected_action"),
            "candidate_response": manager_action.get("candidate_response"),
            "contextual_buyer_semantics": manager_frame,
            "conversation_memory": manager_memory,
        }
        assert_synthetic_frame(failures, manager_frame, campaign_config, f"{label}:manager_permission", expected_semantic="permission_acknowledgement")
        assert_condition(failures, manager_frame.get("outgoing_candidate_gaps") == core, f"{label}: manager outgoing candidate gaps must be campaign core gaps: {manager_frame}")
        assert_condition(failures, manager_frame.get("outgoing_active_gap_scope") == "campaign_relevance", f"{label}: manager outgoing active gap scope must be campaign_relevance: {manager_frame}")
        assert_condition(failures, manager_memory.get("outgoing_candidate_gaps") == core, f"{label}: manager memory outgoing candidate gaps must be campaign core gaps: {manager_memory}")
        assert_condition(failures, manager_memory.get("outgoing_active_gap_scope") == "campaign_relevance", f"{label}: manager memory outgoing active gap scope must be campaign_relevance: {manager_memory}")
        assert_no_forbidden_response(failures, manager_action, f"{label}:manager_permission")

        for utterance, expected_semantic, expected_gap in tests[label]:
            frame = direct_frame(utterance, state, campaign_config)
            evidence[label]["turns"][utterance] = frame
            assert_synthetic_frame(
                failures,
                frame,
                campaign_config,
                f"{label}:{utterance}",
                expected_semantic=expected_semantic,
                expected_gap=expected_gap,
            )

        if label == "telecom":
            trace = evidence[label]["turns"]["coverage is the issue"].get("playbook") or {}
            cautions = set(trace.get("regulated_cautions") or evidence[label].get("regulated_cautions") or [])
            assert_condition(failures, "telecom_contract_or_coverage" in cautions, f"{label}: regulated caution must remain exposed in playbook trace: {trace}")
        if label == "b2b_saas":
            caution_action = planned_action("does it integrate securely with Salesforce?", {"turns": []}, campaign_config)
            evidence[label]["turns"]["integration_security_caution"] = {
                "selected_action": caution_action.get("selected_action"),
                "candidate_response": caution_action.get("candidate_response"),
                "contextual_buyer_semantics": action_frame(caution_action),
            }
            caution_text = normalize(response_text(caution_action))
            assert_condition(
                failures,
                any(fragment in caution_text for fragment in ["verify", "verified", "cannot claim", "before i claim", "exact setup"]),
                f"{label}: integration/security answer must stay cautious: {caution_action}",
            )
            assert_no_forbidden_response(failures, caution_action, f"{label}:integration_security_caution")


def append_live_turn(state: dict[str, Any], packet: dict[str, Any]) -> None:
    state.setdefault("turns", []).append(
        {
            "transcript": packet.get("transcript", ""),
            "summary": packet.get("summary", {}),
            "continuity": packet.get("demo_session_continuity", {}),
            "conversation_memory": packet.get("demo_conversation_memory") or packet.get("conversation_memory") or {},
            "dialogue_manager": packet.get("dialogue_manager", {}),
            "dialogue_pragmatics": packet.get("dialogue_pragmatics", {}),
        }
    )


def build_demo_turn(transcript: str, state: dict[str, Any], *, session_id: str) -> dict[str, Any]:
    return build_turn_packet(
        transcript=transcript,
        campaign_id=DEFAULT_CAMPAIGN_ID,
        stage=DEFAULT_STAGE,
        input_type="agent-open" if transcript == "__agent_open__" else "speech-final",
        silence_count=0,
        cases_path=DEFAULT_CASES_PATH,
        private_out=TMP_DIR,
        live_tts=False,
        force_key_missing=False,
        timeout_seconds=8.0,
        session_id=session_id,
        session_state=state,
        asr_confidence=0.94,
        voice_turn_state="listening",
    )


def packet_frame(packet: dict[str, Any]) -> dict[str, Any]:
    manager = packet.get("dialogue_manager") or {}
    return dict(manager.get("contextual_buyer_semantics") or (manager.get("state_before") or {}).get("contextual_buyer_semantics") or {})


def packet_snapshot(packet: dict[str, Any]) -> dict[str, Any]:
    manager = packet.get("dialogue_manager") or {}
    return {
        "turn": packet.get("session_turn_index"),
        "transcript": packet.get("transcript"),
        "response": response_text(packet),
        "semantic_frame": packet_frame(packet),
        "memory": packet.get("demo_conversation_memory") or packet.get("conversation_memory") or {},
        "provider_calls_made": bool((packet.get("summary") or {}).get("tts_provider_calls_made")),
        "local_llm_calls_made": bool(manager.get("local_llm_calls_made")),
        "opens_prod_102": bool(manager.get("opens_prod_102")),
    }


def validate_routesignal_preservation(failures: list[str], evidence: dict[str, Any]) -> None:
    state: dict[str, Any] = {"turns": []}
    packets: list[dict[str, Any]] = []
    for transcript in ["__agent_open__", "yeah sure", "callbacks are fine"]:
        packet = build_demo_turn(transcript, state, session_id="contextual-011-routesignal")
        packets.append(packet)
        append_live_turn(state, packet)
    snapshots = [packet_snapshot(packet) for packet in packets]
    evidence["routesignal_preservation"] = snapshots
    final = snapshots[-1]
    frame = final["semantic_frame"]
    response = normalize(final["response"])
    assert_condition(failures, frame.get("semantic") == "current_gap_clear", f"routesignal: callbacks clear semantic changed: {final}")
    assert_condition(failures, frame.get("target_gap") == "callbacks", f"routesignal: callbacks target gap changed: {final}")
    assert_condition(failures, frame.get("playbook_id") == ROUTESIGNAL_PLAYBOOK_ID, f"routesignal: playbook id changed: {final}")
    assert_condition(failures, "manual tracking" in response and "handoffs" in response, f"routesignal: remaining diagnostic behavior changed: {final}")
    assert_condition(failures, final["provider_calls_made"] is False, f"routesignal: provider calls must be false: {final}")
    assert_condition(failures, final["local_llm_calls_made"] is False, f"routesignal: local LLM calls must be false: {final}")
    assert_condition(failures, final["opens_prod_102"] is False, f"routesignal: PROD-102 must remain closed: {final}")


def validate_dependency_boundary(failures: list[str], evidence: dict[str, Any]) -> None:
    source = (ROOT / "runtime" / "core" / "contextual_buyer_semantics.py").read_text(encoding="utf-8")
    evidence["dependency_boundary"] = {
        "imports_sales_diagnostic_playbook": "sales_diagnostic_playbook" in source,
        "imports_campaign_playbook_adapter": "campaign_playbook_adapter" in source,
        "module_gap_labels_assignment": bool(re.search(r"^GAP_LABELS\s*=", source, flags=re.MULTILINE)),
        "module_core_gaps_assignment": bool(re.search(r"^CORE_DIAGNOSTIC_GAPS\s*=", source, flags=re.MULTILINE)),
    }
    assert_condition(failures, not evidence["dependency_boundary"]["imports_sales_diagnostic_playbook"], "contextual_buyer_semantics.py must not import sales_diagnostic_playbook")
    assert_condition(failures, evidence["dependency_boundary"]["imports_campaign_playbook_adapter"], "contextual_buyer_semantics.py should import campaign_playbook_adapter")
    assert_condition(failures, not evidence["dependency_boundary"]["module_gap_labels_assignment"], "contextual_buyer_semantics.py must not use module-level GAP_LABELS")
    assert_condition(failures, not evidence["dependency_boundary"]["module_core_gaps_assignment"], "contextual_buyer_semantics.py must not use module-level CORE_DIAGNOSTIC_GAPS")
    for helper in [
        "_resolved_playbook",
        "_gap_labels",
        "_core_diagnostic_gaps",
        "_gap_order",
        "_supported_gap_ids",
        "_gap_definition",
        "_review_focus",
        "_next_gap_candidates",
    ]:
        assert_condition(failures, f"def {helper}" in source, f"contextual_buyer_semantics.py missing campaign-aware helper {helper}")


def build_report(result: dict[str, Any]) -> str:
    lines = [
        "# CONTEXTUAL-BUYER-SEMANTICS-011 Campaign Adapter Runtime",
        "",
        f"Status: {result['status']}",
        "",
        "## Synthetic Campaigns",
        "",
    ]
    for label, snapshot in sorted((result.get("synthetic_campaigns") or {}).items()):
        lines.append(
            f"- {label}: playbook={snapshot.get('campaign_playbook_id')}, "
            f"vertical={snapshot.get('vertical_id')}, core_gaps={snapshot.get('core_diagnostic_gaps')}"
        )
    lines.extend(
        [
            "",
            "## RouteSignal Preservation",
            "",
        ]
    )
    route = (result.get("routesignal_preservation") or [{}])[-1]
    route_frame = route.get("semantic_frame") or {}
    lines.append(
        f"- callbacks clear: semantic={route_frame.get('semantic')}, "
        f"target_gap={route_frame.get('target_gap')}, playbook_id={route_frame.get('playbook_id')}"
    )
    lines.extend(["", "## Dependency Boundary", ""])
    for key, value in sorted((result.get("dependency_boundary") or {}).items()):
        lines.append(f"- {key}: {str(value).lower()}")
    if result.get("failures"):
        lines.extend(["", "## Failures", ""])
        for failure in result["failures"]:
            lines.append(f"- {failure}")
    return "\n".join(lines) + "\n"


def main() -> int:
    failures: list[str] = []
    evidence: dict[str, Any] = {"synthetic_campaigns": {}}
    validate_dependency_boundary(failures, evidence)
    validate_synthetic_campaigns(failures, evidence["synthetic_campaigns"])
    validate_routesignal_preservation(failures, evidence)
    result = {
        "checkpoint_id": CHECKPOINT_ID,
        "status": "pass" if not failures else "fail",
        "failures": failures,
        **evidence,
    }
    write_evidence(result, build_report(result))
    if failures:
        print(json.dumps(result, indent=2, sort_keys=True))
        return 1
    print(f"{CHECKPOINT_ID}: pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
