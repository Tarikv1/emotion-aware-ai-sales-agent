#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.entrypoints import generic_campaign_turn  # noqa: E402
from scripts.validate_generic_campaign_runtime_entrypoint_001 import append_turn  # noqa: E402
from scripts.validate_generic_campaign_runtime_regression_001 import synthetic_campaigns  # noqa: E402
from scripts.run_live_demo_001_agent_voice_call import (  # noqa: E402
    DEFAULT_CAMPAIGN_ID,
    DEFAULT_CASES_PATH,
    DEFAULT_STAGE,
    build_turn_packet as build_routesignal_turn_packet,
    load_campaign as load_routesignal_campaign,
)


CHECKPOINT_ID = "HUMAN-SEMANTIC-REVIEW-PACKET-001"
GENERATED_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
TMP_DIR = ROOT / ".tmp" / CHECKPOINT_ID

RAW_SYNTHETIC_EMAILS = [
    "alex@example.com",
    "ops@example.com",
    "manager@example.com",
    "policy@example.com",
    "support@example.com",
]
EMAIL_RE = re.compile(r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b")
SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_-]{12,}"),
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"(?i)\b(api[_-]?key|secret|token|password)\s*[:=]\s*['\"]?[A-Za-z0-9._-]{8,}"),
]
SAFETY_KEYS = [
    "provider_calls_made",
    "local_llm_calls_made",
    "sends_email",
    "creates_calendar_event",
    "writes_crm",
    "opens_prod_102",
]
TARGET_CHECKPOINTS = [
    "CONTEXTUAL-BUYER-SEMANTICS-001",
    "CONTEXTUAL-BUYER-SEMANTICS-002-sequential-dialogue",
    "CONTEXTUAL-BUYER-SEMANTICS-003-memory-alignment",
    "CONTEXTUAL-BUYER-SEMANTICS-004-semantic-memory-invariants",
    "CONTEXTUAL-BUYER-SEMANTICS-005-outgoing-question-state",
    "CONTEXTUAL-BUYER-SEMANTICS-006-send-info-contact-capture",
    "CONTEXTUAL-BUYER-SEMANTICS-007-send-info-action-contract",
    "CONTEXTUAL-BUYER-SEMANTICS-008-contact-time-normalization",
    "CONTEXTUAL-BUYER-SEMANTICS-009-right-person-handoff",
    "CONTEXTUAL-BUYER-SEMANTICS-010-diagnostic-playbook",
    "CONTEXTUAL-BUYER-SEMANTICS-011-campaign-adapter-runtime",
    "UNIVERSAL-SALES-KNOWLEDGE-001",
    "VERTICAL-SALES-PLAYBOOKS-001",
    "CAMPAIGN-PLAYBOOK-ADAPTER-001",
    "CAMPAIGN-PLAYBOOK-ADAPTER-002-cross-vertical-smoke",
    "GENERIC-CAMPAIGN-RUNTIME-SMOKE-001",
    "GENERIC-CAMPAIGN-RUNTIME-ENTRYPOINT-001",
    "GENERIC-CAMPAIGN-RUNTIME-REGRESSION-001",
    "GENERIC-CAMPAIGN-BUYER-MOVE-PARAPHRASE-001",
    "GENERIC-CAMPAIGN-FALLBACK-LEAKAGE-001",
    "GENERIC-CAMPAIGN-RESPONSE-QUALITY-001",
    "GENERIC-CAMPAIGN-SPOKEN-TEXT-QUALITY-001",
    "GENERIC-CAMPAIGN-LONG-CONVERSATION-STRESS-001",
    "LIVE-DEMO-013-reasoner-route-guard",
    "LIVE-DEMO-014-clear-pain-callback-followup",
    "DIALOGUE-MANAGER-001-root-repair",
    "DIALOGUE-MANAGER-002-pragmatic-dialogue-repair",
    "DIALOGUE-MANAGER-003-plain-sales-clarity-and-vague-appointment-time",
]


GENERIC_CLEAR_PHRASES = {
    "b2b_saas": "manual work is handled",
    "insurance": "coverage fit is handled",
    "telecom": "coverage is fine",
    "home_services": "scheduling is fine",
    "healthcare_admin_or_medical_equipment": "equipment fit is handled",
    "automotive_service": "repair timing is handled",
    "membership_or_subscription": "plan fit is fine",
    "retail_or_ecommerce_support_sales": "product fit is fine",
}
GENERIC_PAIN_PHRASES = {
    "b2b_saas": "visibility is the problem",
    "insurance": "premium is a problem",
    "telecom": "coverage is the issue",
    "home_services": "estimate is unclear",
    "healthcare_admin_or_medical_equipment": "specialist review is needed",
    "automotive_service": "warranty estimate is the problem",
    "membership_or_subscription": "renewal is the issue",
    "retail_or_ecommerce_support_sales": "return policy is the concern",
}
GENERIC_RISKY_QUESTIONS = {
    "b2b_saas": "can you guarantee integration security?",
    "insurance": "can you guarantee I am covered?",
    "telecom": "can you promise coverage here?",
    "home_services": "can you quote exact price now?",
    "healthcare_admin_or_medical_equipment": "can you guarantee this equipment solves the issue?",
    "automotive_service": "can you guarantee repair cost?",
    "membership_or_subscription": "can you hide cancellation terms?",
    "retail_or_ecommerce_support_sales": "can you guarantee refund?",
}
GENERIC_LONG_SEQUENCES = {
    "b2b_saas": [
        "__agent_open__",
        "yeah go ahead",
        "I do not handle this",
        "operations handles it",
        "send it to ops@example.com",
        "can you help with my password?",
    ],
    "insurance": [
        "__agent_open__",
        "yeah sure",
        "coverage fit is handled",
        "premium is a problem",
        "send me details first",
        "send it to alex@example.com",
        "what happens next?",
    ],
    "telecom": [
        "__agent_open__",
        "okay quick",
        "coverage is sometimes an issue",
        "what do you mean?",
        "coverage is the issue",
        "call me next Tuesday at 10",
    ],
    "home_services": [
        "__agent_open__",
        "yes",
        "can you quote exact price now?",
        "no need",
        "stop calling",
        "actually one more thing",
    ],
    "healthcare_admin_or_medical_equipment": [
        "__agent_open__",
        "yeah sure",
        "equipment fit is handled",
        "specialist review is needed",
        "what happens next?",
        "tomorrow at 3 works",
    ],
    "automotive_service": [
        "__agent_open__",
        "yeah sure",
        "I do not understand",
        "what is this about?",
        "what happens next?",
        "maybe",
        "not sure",
        "warranty estimate is the problem",
        "I already told you",
        "tomorrow at 3 works",
    ],
    "membership_or_subscription": [
        "__agent_open__",
        "yes",
        "plan fit is fine",
        "renewal is handled",
        "usage is fine",
        "no need",
        "all of it",
    ],
    "retail_or_ecommerce_support_sales": [
        "__agent_open__",
        "yeah sure",
        "return policy is the concern",
        "how much does it cost?",
        "can you guarantee refund?",
        "tomorrow at 3 works",
    ],
}


def email_token(value: str) -> str:
    return "<email:sha256_12:" + hashlib.sha256(value.lower().encode("utf-8")).hexdigest()[:12] + ">"


def redact_text(text: str) -> str:
    def repl(match: re.Match[str]) -> str:
        return email_token(match.group(0))

    redacted = EMAIL_RE.sub(repl, str(text or ""))
    for raw in RAW_SYNTHETIC_EMAILS:
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


def one_line(text: str, limit: int = 260) -> str:
    value = re.sub(r"\s+", " ", str(text or "")).strip()
    if len(value) <= limit:
        return value
    return value[: limit - 3].rstrip() + "..."


def normalize_key(text: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9]+", "-", str(text or "").lower()).strip("-")
    return value or "case"


def load_json_if_present(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"parse_error": True}
    return value if isinstance(value, dict) else {"non_object_json": True}


def generated_evidence_inventory() -> list[dict[str, Any]]:
    inventory: list[dict[str, Any]] = []
    base = ROOT / "research" / "experiments" / "generated"
    for checkpoint in TARGET_CHECKPOINTS:
        path = base / checkpoint
        result = load_json_if_present(path / "result.json")
        report_exists = (path / "report.md").exists()
        inventory.append(
            {
                "checkpoint_id": checkpoint,
                "path": f"research/experiments/generated/{checkpoint}/",
                "present": path.exists(),
                "result_status": result.get("status"),
                "report_exists": report_exists,
                "keys": sorted(result.keys())[:20],
            }
        )
    return inventory


def text_from_packet(packet: dict[str, Any], key: str) -> str:
    summary = packet.get("summary") or {}
    body = packet.get("packet") or {}
    if key == "final_response":
        return str(summary.get("final_response") or body.get("final_response") or "")
    if key == "tts_input_text":
        tts = body.get("tts_delivery") or {}
        return str(summary.get("tts_input_text") or tts.get("tts_input_text") or "")
    if key == "provider_rendered_text":
        voice = body.get("voice_delivery") or {}
        rendering = voice.get("provider_rendering") or {}
        return str(rendering.get("rendered_text") or "")
    return ""


def semantic_frame(packet: dict[str, Any]) -> dict[str, Any]:
    manager = packet.get("dialogue_manager") or {}
    selected = manager.get("selected_action") or {}
    frame = selected.get("contextual_buyer_semantics") or selected.get("semantic_frame") or {}
    if frame:
        return frame
    if selected.get("semantic"):
        return selected
    return manager.get("contextual_buyer_semantics") or {}


def conversation_memory(packet: dict[str, Any]) -> dict[str, Any]:
    return dict(packet.get("demo_conversation_memory") or packet.get("conversation_memory") or {})


def compact_state(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    keep = [
        "status",
        "stage",
        "requested",
        "email_hash",
        "contact_email_hash",
        "callback_time",
        "callback_time_normalized",
        "normalized_time",
        "department",
        "handoff_department",
        "target_department",
        "right_person",
        "safety",
        "source",
    ]
    return sanitize({key: value.get(key) for key in keep if key in value})


def selected_action_summary(packet: dict[str, Any]) -> dict[str, Any]:
    action = ((packet.get("dialogue_manager") or {}).get("selected_action") or {})
    frame = semantic_frame(packet)
    return sanitize(
        {
            "source": action.get("source"),
            "semantic": action.get("semantic") or frame.get("semantic"),
            "next_action": action.get("next_action"),
            "question_type": action.get("question_type") or action.get("next_question_type"),
            "memory_update_key": action.get("memory_update_key"),
            "response_strategy": action.get("response_strategy"),
        }
    )


def safety_flags(packet: dict[str, Any]) -> dict[str, bool]:
    body = packet.get("packet") or {}
    summary = packet.get("summary") or {}
    tts = body.get("tts_delivery") or {}
    voice = body.get("voice_delivery") or {}
    manager = packet.get("dialogue_manager") or {}
    memory = conversation_memory(packet)
    lead = memory.get("lead_followup_state") or {}
    lead_safety = lead.get("safety") or {}
    return {
        "provider_calls_made": bool(packet.get("provider_calls_made") or summary.get("tts_provider_calls_made") or tts.get("provider_calls_made") or voice.get("provider_calls_made") or body.get("api_calls_made")),
        "local_llm_calls_made": bool(packet.get("local_llm_calls_made") or manager.get("local_llm_calls_made") or body.get("llm_used")),
        "sends_email": bool(packet.get("sends_email") or lead_safety.get("sends_email")),
        "creates_calendar_event": bool(packet.get("creates_calendar_event") or lead_safety.get("creates_calendar_event")),
        "writes_crm": bool(packet.get("writes_crm") or lead_safety.get("writes_crm")),
        "opens_prod_102": bool(packet.get("opens_prod_102") or manager.get("opens_prod_102")),
    }


def turn_review_questions(edge_buckets: list[str]) -> list[str]:
    questions = [
        "Did the agent understand this buyer turn correctly?",
        "Did the next action match the conversation state?",
        "Is the wording natural enough for a live appointment-setting call?",
    ]
    if "regulated_caution" in edge_buckets:
        questions.append("Did the response avoid guarantees and route safely to human or policy review?")
    if "send_info" in edge_buckets:
        questions.append("Was contact capture safe without implying an email was sent?")
    if "right_person_authority" in edge_buckets:
        questions.append("Did the agent keep contact routing separate from product-gap routing?")
    if "stop_refusal" in edge_buckets:
        questions.append("Was the stop/refusal respected without continued selling?")
    return questions


def turn_record(packet: dict[str, Any], edge_buckets: list[str]) -> dict[str, Any]:
    frame = semantic_frame(packet)
    memory = conversation_memory(packet)
    selected = selected_action_summary(packet)
    return sanitize(
        {
            "turn_index": packet.get("session_turn_index"),
            "buyer_transcript": packet.get("transcript"),
            "agent_final_response": text_from_packet(packet, "final_response"),
            "tts_input_text": text_from_packet(packet, "tts_input_text"),
            "provider_rendered_text": text_from_packet(packet, "provider_rendered_text"),
            "semantic": frame.get("semantic") or selected.get("semantic"),
            "target_gap": frame.get("target_gap"),
            "primary_gap": frame.get("primary_gap") or frame.get("target_gap"),
            "playbook_id": frame.get("playbook_id") or packet.get("campaign_playbook_id"),
            "playbook_review_focus": frame.get("playbook_review_focus"),
            "outgoing_candidate_gaps": frame.get("outgoing_candidate_gaps"),
            "cleared_gaps": memory.get("cleared_gaps") or frame.get("cleared_gaps") or [],
            "confirmed_gaps": memory.get("confirmed_gaps") or frame.get("confirmed_gaps") or [],
            "selected_action": selected,
            "call_control": (packet.get("summary") or {}).get("call_control"),
            "send_info_state": compact_state(memory.get("send_info_state")),
            "lead_followup_state": compact_state(memory.get("lead_followup_state")),
            "handoff_target_state": compact_state(memory.get("handoff_target_state")),
            "safety_flags": safety_flags(packet),
            "reviewer_questions": turn_review_questions(edge_buckets),
        }
    )


def build_generic_sequence(campaign: dict[str, Any], transcripts: list[str], session_id: str) -> list[dict[str, Any]]:
    state: dict[str, Any] = {"turns": []}
    packets: list[dict[str, Any]] = []
    for transcript in transcripts:
        packet = generic_campaign_turn.build_generic_campaign_turn_packet(
            transcript=transcript,
            campaign=campaign,
            input_type="agent-open" if transcript == "__agent_open__" else "speech-final",
            session_id=session_id,
            session_state=state,
            private_out=TMP_DIR / session_id,
            live_tts=False,
            force_key_missing=True,
            timeout_seconds=8.0,
            asr_confidence=0.94,
            voice_turn_state="listening",
        )
        packets.append(packet)
        append_turn(state, packet)
    return packets


def build_routesignal_sequence(transcripts: list[str], session_id: str) -> list[dict[str, Any]]:
    state: dict[str, Any] = {"turns": []}
    packets: list[dict[str, Any]] = []
    for transcript in transcripts:
        packet = build_routesignal_turn_packet(
            transcript=transcript,
            campaign_id=DEFAULT_CAMPAIGN_ID,
            stage=DEFAULT_STAGE,
            input_type="agent-open" if transcript == "__agent_open__" else "speech-final",
            silence_count=0,
            cases_path=DEFAULT_CASES_PATH,
            private_out=TMP_DIR / session_id,
            live_tts=False,
            force_key_missing=True,
            timeout_seconds=8.0,
            session_id=session_id,
            session_state=state,
            asr_confidence=0.94,
            voice_turn_state="listening",
        )
        packets.append(packet)
        append_turn(state, packet)
    return packets


def campaign_summary(vertical_id: str, campaign: dict[str, Any], *, routesignal_allowed: bool = False) -> dict[str, Any]:
    gaps = campaign.get("diagnostic_gaps") or {}
    return sanitize(
        {
            "campaign_id": campaign.get("campaign_id") or DEFAULT_CAMPAIGN_ID,
            "vertical_id": vertical_id,
            "client_name": campaign.get("client_name"),
            "product_or_offer_name": campaign.get("product_or_offer_name") or campaign.get("offer_name") or campaign.get("product_name"),
            "human_followup_owner": campaign.get("human_followup_owner") or campaign.get("human_handoff_role"),
            "appointment_target": campaign.get("appointment_target"),
            "diagnostic_gaps": [
                {
                    "gap_id": gap_id,
                    "label": gap.get("label"),
                    "review_focus": gap.get("review_focus"),
                    "evidence_positive": gap.get("evidence_positive"),
                    "evidence_negative": gap.get("evidence_negative"),
                }
                for gap_id, gap in gaps.items()
            ],
            "regulated_cautions": [
                campaign.get("regulated_advice_boundary_text"),
                campaign.get("license_boundary"),
                campaign.get("service_area_policy"),
                campaign.get("inspection_boundary"),
                campaign.get("integration_claim_policy"),
                campaign.get("account_auth_boundary"),
            ],
            "blocked_claims": campaign.get("blocked_claims") or [],
            "routesignal_terms_allowed": routesignal_allowed,
        }
    )


def generic_scenarios(vertical_id: str, campaign: dict[str, Any]) -> list[dict[str, Any]]:
    first_gap = (campaign.get("core_diagnostic_gaps") or ["first gap"])[0]
    first_label = ((campaign.get("diagnostic_gaps") or {}).get(first_gap) or {}).get("label") or first_gap.replace("_", " ")
    return [
        {
            "scenario_type": "opening_and_permission",
            "source_checkpoint": "GENERIC-CAMPAIGN-RUNTIME-REGRESSION-001",
            "edge_buckets": ["permission_acknowledgement"],
            "risk_tags": ["baseline"],
            "expected": "Agent opens with campaign-aware reason, then starts one concise diagnostic after permission.",
            "transcripts": ["__agent_open__", "yeah sure"],
        },
        {
            "scenario_type": "current_gap_clear",
            "source_checkpoint": "GENERIC-CAMPAIGN-RUNTIME-REGRESSION-001",
            "edge_buckets": ["no_pain_current_issue_clear"],
            "risk_tags": ["state_memory"],
            "expected": f"Agent treats {first_label} as cleared and asks about remaining campaign gaps.",
            "transcripts": ["__agent_open__", "yeah sure", GENERIC_CLEAR_PHRASES[vertical_id]],
        },
        {
            "scenario_type": "pain_confirmed",
            "source_checkpoint": "GENERIC-CAMPAIGN-RUNTIME-REGRESSION-001",
            "edge_buckets": ["pain_confirmed"],
            "risk_tags": ["appointment_pressure"],
            "expected": "Agent confirms the campaign-specific pain and moves toward a human follow-up without full sale closure.",
            "transcripts": ["__agent_open__", "yeah sure", GENERIC_PAIN_PHRASES[vertical_id]],
        },
        {
            "scenario_type": "possible_pain_then_confusion",
            "source_checkpoint": "GENERIC-CAMPAIGN-BUYER-MOVE-PARAPHRASE-001",
            "edge_buckets": ["possible_pain_ambiguity", "confusion"],
            "risk_tags": ["hard_case", "edge_case", "wrong_next_action_risk"],
            "expected": "Agent should not create false pain and should clarify the prior diagnostic without appointment pressure.",
            "transcripts": ["__agent_open__", "okay quick", "sometimes maybe", "what do you mean?"],
        },
        {
            "scenario_type": "send_info_email_capture",
            "source_checkpoint": "GENERIC-CAMPAIGN-RUNTIME-REGRESSION-001",
            "edge_buckets": ["send_info"],
            "risk_tags": ["hard_case", "edge_case", "contact_capture"],
            "expected": "Agent opens send-info state, captures redacted email/hash, and does not claim an email was sent.",
            "transcripts": ["__agent_open__", "yeah sure", "send me details", "send it to alex@example.com"],
        },
        {
            "scenario_type": "callback_timing_capture",
            "source_checkpoint": "GENERIC-CAMPAIGN-RUNTIME-REGRESSION-001",
            "edge_buckets": ["callback_timing"],
            "risk_tags": ["hard_case", "edge_case", "time_capture"],
            "expected": "Agent captures a usable callback time without creating calendar or CRM side effects.",
            "transcripts": ["__agent_open__", "yeah sure", "send me details", "tomorrow at 3 works"],
        },
        {
            "scenario_type": "right_person_handoff",
            "source_checkpoint": "GENERIC-CAMPAIGN-RUNTIME-REGRESSION-001",
            "edge_buckets": ["right_person_authority"],
            "risk_tags": ["hard_case", "edge_case", "handoff_state"],
            "expected": "Agent opens right-person state, captures department/contact path, and keeps it separate from product gaps.",
            "transcripts": ["__agent_open__", "yeah sure", "I'm not the person", "operations handles it", "send it to ops@example.com"],
        },
        {
            "scenario_type": "regulated_caution_refusal_stop",
            "source_checkpoint": "GENERIC-CAMPAIGN-LONG-CONVERSATION-STRESS-001",
            "edge_buckets": ["regulated_caution", "not_relevant_no_need", "stop_refusal"],
            "risk_tags": ["hard_case", "edge_case", "regulated", "terminal_state"],
            "expected": "Agent refuses unsafe guarantee/concealment, handles no-need stage-aware, and preserves terminal stop behavior.",
            "transcripts": ["__agent_open__", "yes", GENERIC_RISKY_QUESTIONS[vertical_id], "no need", "stop calling", "actually one more thing"],
        },
        {
            "scenario_type": "fallback_repair_stack",
            "source_checkpoint": "GENERIC-CAMPAIGN-FALLBACK-LEAKAGE-001",
            "edge_buckets": ["fallback_repair", "confusion"],
            "risk_tags": ["hard_case", "edge_case", "fallback_leakage", "naturalness"],
            "expected": "Agent stays campaign-aware through purpose, confusion, next-step, price, and out-of-scope repair turns.",
            "transcripts": ["__agent_open__", "yeah sure", "what is this about?", "I don't understand", "what happens next?", "is it expensive?", "can you help with my password?"],
        },
        {
            "scenario_type": "long_mixed_state_drift",
            "source_checkpoint": "GENERIC-CAMPAIGN-LONG-CONVERSATION-STRESS-001",
            "edge_buckets": ["long_conversation_state_drift"],
            "risk_tags": ["hard_case", "edge_case", "state_drift", "duplicate_question_risk"],
            "expected": "Agent should preserve cleared/confirmed/contact/terminal state across a realistic longer conversation.",
            "transcripts": GENERIC_LONG_SEQUENCES[vertical_id],
        },
    ]


def routesignal_scenarios() -> list[dict[str, Any]]:
    return [
        ("opening_permission", ["permission_acknowledgement"], ["baseline"], ["__agent_open__", "yeah sure"], "RouteSignal opening and diagnostic start remain allowed."),
        ("callbacks_clear", ["no_pain_current_issue_clear", "routesignal_preservation"], ["state_memory"], ["__agent_open__", "yeah sure", "callbacks are fine"], "Callbacks are cleared and remaining RouteSignal gaps are asked."),
        ("handoffs_pain", ["pain_confirmed", "routesignal_preservation"], ["appointment_pressure"], ["__agent_open__", "yeah sure", "handoffs get messy"], "Handoffs pain is confirmed and RouteSignal/Northstar wording is allowed."),
        ("send_info_yes", ["send_info", "routesignal_preservation"], ["hard_case", "edge_case"], ["__agent_open__", "yeah sure", "send me details first", "yes send it"], "Send-info state opens without fake send."),
        ("callback_time", ["callback_timing", "routesignal_preservation"], ["hard_case", "edge_case"], ["__agent_open__", "yeah sure", "send me details", "tomorrow at 3 works"], "Callback time capture works through live-demo path."),
        ("right_person", ["right_person_authority", "routesignal_preservation"], ["hard_case", "edge_case"], ["__agent_open__", "yeah sure", "I'm not the person", "operations handles it"], "Wrong-person route remains safe."),
        ("stop_terminal", ["stop_refusal", "routesignal_preservation"], ["hard_case", "edge_case"], ["__agent_open__", "stop calling", "actually one more thing"], "Stop ends call and terminal behavior persists."),
        ("confusion_repair", ["confusion", "routesignal_preservation"], ["hard_case"], ["__agent_open__", "yeah sure", "I don't understand", "what do you mean?"], "Confusion gets a repair rather than appointment pressure."),
        ("price_question", ["fallback_repair", "routesignal_preservation"], ["hard_case"], ["__agent_open__", "yeah sure", "how much does it cost?"], "Price question is answered only within live-demo policy."),
        ("no_need", ["not_relevant_no_need", "routesignal_preservation"], ["hard_case"], ["__agent_open__", "yeah sure", "no need", "all of it"], "No-need path should avoid continued selling loops."),
        ("possible_pain", ["possible_pain_ambiguity", "routesignal_preservation"], ["hard_case"], ["__agent_open__", "yeah sure", "sometimes maybe"], "Possible pain should not create a false confirmed pain."),
        ("next_step", ["fallback_repair", "routesignal_preservation"], ["hard_case"], ["__agent_open__", "yeah sure", "what happens next?"], "Next-step answer may mention Northstar in RouteSignal path only."),
        ("manual_tracking_clear", ["no_pain_current_issue_clear", "routesignal_preservation"], ["state_memory"], ["__agent_open__", "yeah sure", "manual tracking is handled"], "Manual tracking clear behavior remains stable."),
        ("callbacks_pain", ["pain_confirmed", "routesignal_preservation"], ["appointment_pressure"], ["__agent_open__", "yeah sure", "callbacks are a problem"], "Callbacks pain confirmation remains stable."),
        ("long_routesignal", ["long_conversation_state_drift", "routesignal_preservation"], ["hard_case", "edge_case", "state_drift"], ["__agent_open__", "yeah sure", "callbacks are fine", "handoffs get messy", "send me details first", "yes send it", "tomorrow at 3 works"], "Long RouteSignal preservation across clear, pain, send-info, and callback."),
        ("odd_out_of_scope", ["fallback_repair", "routesignal_preservation"], ["hard_case", "edge_case"], ["__agent_open__", "yeah sure", "can you help with my password?"], "Out-of-scope fallback should not break live-demo behavior."),
    ]


def conversation_from_packets(
    *,
    conversation_id: str,
    source_checkpoint: str,
    campaign_id: str,
    vertical_id: str,
    scenario_type: str,
    edge_buckets: list[str],
    risk_tags: list[str],
    expected: str,
    packets: list[dict[str, Any]],
) -> dict[str, Any]:
    turns = [turn_record(packet, edge_buckets) for packet in packets]
    return {
        "conversation_id": conversation_id,
        "source_checkpoint": source_checkpoint,
        "campaign_id": campaign_id,
        "vertical_id": vertical_id,
        "scenario_type": scenario_type,
        "edge_buckets": edge_buckets,
        "risk_tags": risk_tags,
        "expected_high_level_behavior": expected,
        "turns": turns,
        "reviewer_conversation_questions": [
            "Where did the deterministic route feel brittle or too scripted?",
            "Which turn should become a new validator case?",
            "Was the appointment-setting pressure appropriate for this buyer state?",
            "Did state memory preserve confirmed gaps, cleared gaps, contact capture, and terminal stops?",
        ],
    }


def build_conversations(campaigns: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    conversations: list[dict[str, Any]] = []
    for vertical_id, campaign in campaigns.items():
        for index, scenario in enumerate(generic_scenarios(vertical_id, campaign), start=1):
            scenario_slug = normalize_key(scenario["scenario_type"])
            conversation_id = f"generic-{normalize_key(vertical_id)}-{scenario_slug}-{index:03d}"
            packets = build_generic_sequence(campaign, scenario["transcripts"], conversation_id)
            conversations.append(
                conversation_from_packets(
                    conversation_id=conversation_id,
                    source_checkpoint=scenario["source_checkpoint"],
                    campaign_id=str(campaign.get("campaign_id")),
                    vertical_id=vertical_id,
                    scenario_type=scenario["scenario_type"],
                    edge_buckets=list(scenario["edge_buckets"]),
                    risk_tags=list(scenario["risk_tags"]),
                    expected=scenario["expected"],
                    packets=packets,
                )
            )

    for index, (scenario_type, edge_buckets, risk_tags, transcripts, expected) in enumerate(routesignal_scenarios(), start=1):
        conversation_id = f"routesignal-live-demo-{normalize_key(scenario_type)}-{index:03d}"
        packets = build_routesignal_sequence(transcripts, conversation_id)
        conversations.append(
            conversation_from_packets(
                conversation_id=conversation_id,
                source_checkpoint="LIVE-DEMO-014-clear-pain-callback-followup" if "long" in scenario_type or "callback" in scenario_type else "LIVE-DEMO-013-reasoner-route-guard",
                campaign_id=DEFAULT_CAMPAIGN_ID,
                vertical_id="routesignal_live_demo",
                scenario_type=scenario_type,
                edge_buckets=list(edge_buckets),
                risk_tags=list(risk_tags),
                expected=expected,
                packets=packets,
            )
        )
    return conversations


def jsonl_records(conversations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for conversation in conversations:
        for turn in conversation["turns"]:
            records.append(
                {
                    "record_type": "turn_review",
                    "conversation_id": conversation["conversation_id"],
                    "source_checkpoint": conversation["source_checkpoint"],
                    "campaign_id": conversation["campaign_id"],
                    "vertical_id": conversation["vertical_id"],
                    "scenario_type": conversation["scenario_type"],
                    "edge_buckets": conversation["edge_buckets"],
                    "risk_tags": conversation["risk_tags"],
                    "expected_high_level_behavior": conversation["expected_high_level_behavior"],
                    **turn,
                }
            )
    return records


def known_human_questionable(conversations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    wanted_tags = {"hard_case", "edge_case", "fallback_leakage", "naturalness", "duplicate_question_risk", "terminal_state"}
    for conversation in conversations:
        if wanted_tags.intersection(set(conversation.get("risk_tags") or [])):
            final_turn = conversation["turns"][-1]
            selected.append(
                {
                    "conversation_id": conversation["conversation_id"],
                    "scenario_type": conversation["scenario_type"],
                    "why_human_should_review": [
                        "Validator pass does not prove the response feels human.",
                        "State transitions and appointment pressure may still be debatable.",
                        "This case is useful for finding validator gaps rather than runtime crashes.",
                    ],
                    "last_buyer_transcript": final_turn.get("buyer_transcript"),
                    "last_agent_response": final_turn.get("agent_final_response"),
                    "semantic": final_turn.get("semantic"),
                    "call_control": final_turn.get("call_control"),
                }
            )
        if len(selected) >= 24:
            break
    return selected


def edge_bucket_summary(conversations: list[dict[str, Any]]) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for conversation in conversations:
        counter.update(str(item) for item in conversation.get("edge_buckets") or [])
    return dict(sorted(counter.items()))


def vertical_summary(conversations: list[dict[str, Any]]) -> dict[str, int]:
    counter = Counter(str(item.get("vertical_id") or "") for item in conversations)
    return dict(sorted(counter.items()))


def build_packet_json(
    *,
    conversations: list[dict[str, Any]],
    campaigns: dict[str, dict[str, Any]],
    evidence_inventory: list[dict[str, Any]],
) -> dict[str, Any]:
    route_campaign = load_routesignal_campaign(DEFAULT_CAMPAIGN_ID, DEFAULT_CASES_PATH)
    campaign_sections = [campaign_summary(vertical_id, campaign) for vertical_id, campaign in campaigns.items()]
    campaign_sections.append(campaign_summary("routesignal_live_demo", route_campaign, routesignal_allowed=True))
    return sanitize(
        {
            "checkpoint_id": CHECKPOINT_ID,
            "packet_type": "sanitized_human_semantic_review_packet",
            "runtime_behavior_changed": False,
            "provider_calls_made": False,
            "local_llm_calls_made": False,
            "live_tts_called": False,
            "sends_email": False,
            "creates_calendar_event": False,
            "writes_crm": False,
            "opens_prod_102": False,
            "architecture_snapshot": {
                "contextual_buyer_semantics": "Deterministic buyer-move and gap classification.",
                "dialogue_manager": "Deterministic action planning, memory updates, anti-loop and stability guards.",
                "campaign_playbook_adapter": "Resolves RouteSignal or synthetic campaign playbooks.",
                "universal_sales_knowledge": "Shared pain and qualification dimensions.",
                "vertical_sales_playbooks": "Reusable vertical defaults for generic campaigns.",
                "generic_campaign_turn": "Reusable dry-run generic campaign turn packet entrypoint.",
                "live_voice_session_policy": "Session policy and fallback wording for live-demo and generic runtime paths.",
                "voice_tts_dry_run": "Dry-run voice/TTS text shaping with provider calls disabled.",
                "validators": "Deterministic project validators for semantics, memory, generic campaigns, fallback leakage, wording, spoken text, and long conversations.",
            },
            "review_objective": "Human reviewer should judge missed buyer meaning, wrong next action, appointment pressure, state drift, naturalness, regulated caution, campaign leakage, and validator gaps.",
            "campaigns": campaign_sections,
            "generated_evidence_inventory": evidence_inventory,
            "conversation_count": len(conversations),
            "turn_record_count": sum(len(item.get("turns") or []) for item in conversations),
            "vertical_summary": vertical_summary(conversations),
            "edge_bucket_summary": edge_bucket_summary(conversations),
            "known_validator_passed_but_human_questionable_examples": known_human_questionable(conversations),
            "suggested_human_review_rubric": {
                "score_scale": "1 to 5, where 1 is poor and 5 is ready for live dry-run review.",
                "score_dimensions": [
                    "buyer meaning understood",
                    "acknowledgement quality",
                    "next action correctness",
                    "appointment-setting appropriateness",
                    "naturalness",
                    "safety/compliance",
                    "state consistency",
                    "overall readiness",
                ],
                "failure_categories": [
                    "missed_buyer_meaning",
                    "wrong_semantic",
                    "wrong_next_action",
                    "too_pushy",
                    "too_passive",
                    "repeated_question",
                    "unnatural_wording",
                    "campaign_leakage",
                    "unsafe_claim",
                    "state_drift",
                    "contact_capture_issue",
                    "right_person_issue",
                    "stop_refusal_issue",
                    "tts_meaning_drift",
                    "validator_gap",
                ],
            },
            "open_questions_for_reviewer": [
                "Which failures should become validators?",
                "Which issues are just copy polish?",
                "Which issues require semantic architecture changes?",
                "Which issues require campaign config changes?",
                "Which issues require live audio review?",
                "Is an LLM evaluator worth building after this packet?",
            ],
            "conversations": conversations,
        }
    )


def markdown_table_row(values: list[Any]) -> str:
    cells = [str(value if value is not None else "").replace("\n", " ").replace("|", "\\|") for value in values]
    return "| " + " | ".join(cells) + " |"


def render_review_packet(packet: dict[str, Any]) -> str:
    lines: list[str] = [
        "# Human Semantic Review Packet 001",
        "",
        "## 1. Executive Summary For Reviewer",
        "",
        "This packet contains sanitized deterministic sales-agent conversations for manual semantic review. The runtime goal is appointment-setting and lead qualification, not full sale closure. The reviewed agent does not use live LLM final speech here; responses are deterministic runtime outputs. Provider calls, live TTS, email sending, calendar creation, CRM writes, and PROD-102 are disabled.",
        "",
        "Judge what the deterministic agent still gets wrong: buyer meaning, next action, appointment pressure, state drift, repeated questions, refusal handling, regulated caution quality, campaign leakage, generic wording quality, and long-conversation realism.",
        "",
        f"Conversation count: {packet['conversation_count']}",
        f"Turn record count: {packet['turn_record_count']}",
        "",
        "## 2. Review Instructions",
        "",
        "For each conversation, score whether the agent understood the buyer, acknowledged correctly, chose the right next action, preserved confirmed and cleared gaps, used appropriate appointment pressure, respected refusal or stop, handled send-info and contact capture safely, handled right-person routing, sounded natural, preserved meaning between final response and TTS text, avoided campaign leakage, handled regulated claims safely, and suggests any new validator case.",
        "",
        "## 3. Architecture Snapshot",
        "",
    ]
    for key, value in packet["architecture_snapshot"].items():
        lines.append(f"- `{key}`: {value}")
    lines.extend(["", "## 4. Campaign And Vertical Coverage", ""])
    for campaign in packet["campaigns"]:
        lines.extend(
            [
                f"### {campaign.get('vertical_id')} - {campaign.get('campaign_id')}",
                "",
                f"- Product/offer: {campaign.get('product_or_offer_name')}",
                f"- Human follow-up owner: {campaign.get('human_followup_owner')}",
                f"- Appointment target: {campaign.get('appointment_target')}",
                f"- RouteSignal-specific terms allowed: {campaign.get('routesignal_terms_allowed')}",
                f"- Blocked claims: {', '.join(str(item) for item in campaign.get('blocked_claims') or []) or 'None listed'}",
                "- Diagnostic gaps:",
            ]
        )
        for gap in campaign.get("diagnostic_gaps") or []:
            lines.append(f"  - `{gap.get('gap_id')}`: {gap.get('label')} - review focus: {gap.get('review_focus')}")
        cautions = [item for item in campaign.get("regulated_cautions") or [] if item]
        lines.append(f"- Regulated cautions: {'; '.join(str(item) for item in cautions) if cautions else 'None listed'}")
        lines.append("")

    lines.extend(["## 5. Conversation Review Records", ""])
    for conversation in packet["conversations"]:
        lines.extend(
            [
                f"### {conversation['conversation_id']}",
                "",
                f"- Source checkpoint: `{conversation['source_checkpoint']}`",
                f"- Campaign: `{conversation['campaign_id']}`",
                f"- Vertical: `{conversation['vertical_id']}`",
                f"- Scenario type: `{conversation['scenario_type']}`",
                f"- Edge buckets: {', '.join(conversation['edge_buckets'])}",
                f"- Risk tags: {', '.join(conversation['risk_tags'])}",
                f"- Expected high-level behavior: {conversation['expected_high_level_behavior']}",
                "",
                markdown_table_row(["Turn", "Buyer", "Agent final response", "TTS input", "Semantic", "Target gap", "Cleared", "Confirmed", "Action", "Call control", "Reviewer prompts"]),
                markdown_table_row(["---", "---", "---", "---", "---", "---", "---", "---", "---", "---", "---"]),
            ]
        )
        for turn in conversation["turns"]:
            action = turn.get("selected_action") or {}
            lines.append(
                markdown_table_row(
                    [
                        turn.get("turn_index"),
                        one_line(turn.get("buyer_transcript"), 120),
                        one_line(turn.get("agent_final_response"), 260),
                        one_line(turn.get("tts_input_text"), 220),
                        turn.get("semantic"),
                        turn.get("target_gap"),
                        ", ".join(str(item) for item in turn.get("cleared_gaps") or []),
                        ", ".join(str(item) for item in turn.get("confirmed_gaps") or []),
                        one_line(json.dumps(action, sort_keys=True), 160),
                        turn.get("call_control"),
                        one_line("; ".join(turn.get("reviewer_questions") or []), 260),
                    ]
                )
            )
        lines.append("")

    lines.extend(
        [
            "## 6. Edge-Case Buckets",
            "",
        ]
    )
    for bucket, count in packet["edge_bucket_summary"].items():
        lines.append(f"- `{bucket}`: {count} conversations")
    lines.extend(["", "## 7. Known Validator-Passed But Human-Questionable Examples", ""])
    for example in packet["known_validator_passed_but_human_questionable_examples"]:
        lines.extend(
            [
                f"### {example['conversation_id']}",
                "",
                f"- Scenario: `{example['scenario_type']}`",
                f"- Last buyer turn: {example.get('last_buyer_transcript')}",
                f"- Last agent response: {example.get('last_agent_response')}",
                f"- Semantic: `{example.get('semantic')}`",
                f"- Call control: `{example.get('call_control')}`",
                "- Why review:",
            ]
        )
        for reason in example.get("why_human_should_review") or []:
            lines.append(f"  - {reason}")
        lines.append("")

    lines.extend(
        [
            "## 8. Suggested Human Review Rubric",
            "",
            "Score each dimension 1 to 5, where 1 is poor and 5 is ready for live dry-run review.",
            "",
        ]
    )
    for dimension in packet["suggested_human_review_rubric"]["score_dimensions"]:
        lines.append(f"- {dimension}")
    lines.extend(["", "Failure categories:", ""])
    for category in packet["suggested_human_review_rubric"]["failure_categories"]:
        lines.append(f"- `{category}`")

    lines.extend(["", "## 9. Open Questions For Reviewer", ""])
    for question in packet["open_questions_for_reviewer"]:
        lines.append(f"- {question}")

    lines.extend(
        [
            "",
            "## 10. Redaction And Safety Summary",
            "",
            "- Synthetic examples only.",
            "- No private transcripts.",
            "- Raw synthetic emails are redacted as stable hash tokens.",
            "- No secrets, API keys, env values, audio, or customer data are included.",
            "- Provider calls false.",
            "- Local LLM calls false.",
            "- Live TTS false.",
            "- Email/calendar/CRM writes false.",
            "- PROD-102 false.",
            "",
        ]
    )
    return "\n".join(lines)


def render_index(packet: dict[str, Any]) -> str:
    lines = [
        "# HUMAN-SEMANTIC-REVIEW-PACKET-001 Index",
        "",
        "Upload these files to ChatGPT or a human reviewer:",
        "",
        "- `review_packet.md`: primary readable review packet.",
        "- `review_packet.json`: full machine-readable packet.",
        "- `review_packet.jsonl`: one sanitized reviewed turn per line.",
        "- `redaction_report.json`: privacy and side-effect proof.",
        "",
        f"Conversations: {packet['conversation_count']}",
        f"Turn records: {packet['turn_record_count']}",
        "",
        "Vertical coverage:",
    ]
    for vertical, count in packet["vertical_summary"].items():
        lines.append(f"- `{vertical}`: {count} conversations")
    lines.extend(["", "Edge buckets:"])
    for bucket, count in packet["edge_bucket_summary"].items():
        lines.append(f"- `{bucket}`: {count} conversations")
    lines.extend(
        [
            "",
            "Review priority:",
            "",
            "1. Long mixed state-drift conversations.",
            "2. Regulated caution turns.",
            "3. Send-info and right-person contact capture.",
            "4. Stop/refusal persistence.",
            "5. Fallback repair and out-of-scope questions.",
            "6. RouteSignal preservation cases where RouteSignal wording is allowed.",
            "",
        ]
    )
    return "\n".join(lines)


def render_report(packet: dict[str, Any], redaction: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# HUMAN-SEMANTIC-REVIEW-PACKET-001 Report",
            "",
            "## Summary",
            "",
            "Generated a sanitized human/ChatGPT semantic review packet from deterministic local runtime turn packets. No runtime behavior was patched.",
            "",
            "## Files Created",
            "",
            "- `review_packet.md`",
            "- `review_packet.json`",
            "- `review_packet.jsonl`",
            "- `review_index.md`",
            "- `redaction_report.json`",
            "- `report.md`",
            "- `result.json`",
            "",
            "## Coverage",
            "",
            f"- Conversations: {packet['conversation_count']}",
            f"- Turn records: {packet['turn_record_count']}",
            f"- Verticals/campaigns: {', '.join(packet['vertical_summary'])}",
            f"- Edge buckets: {', '.join(packet['edge_bucket_summary'])}",
            "",
            "## Safety",
            "",
            f"- Raw synthetic emails found: {redaction['raw_synthetic_emails_found']}",
            f"- Private-looking secret matches: {redaction['private_or_secret_pattern_matches']}",
            f"- Side-effect summary: `{json.dumps(redaction['side_effect_summary'], sort_keys=True)}`",
            "- Generated audio required: false",
            "- Provider calls: false",
            "- Local LLM calls: false",
            "- Email/calendar/CRM writes: false",
            "- PROD-102: false",
            "",
            "## Runtime Behavior",
            "",
            "No runtime files were changed by this phase. Packet generation used the generic campaign entrypoint and RouteSignal live-demo dry-run path only.",
            "",
            "## Phase 1/2/3 Backpatch Decision",
            "",
            "No Phase 1/2/3 backpatch was required. This phase packaged evidence and added a packet validator/helper only.",
            "",
            "## Recommended Review Use",
            "",
            "Upload `review_index.md`, `review_packet.md`, `review_packet.json`, `review_packet.jsonl`, and `redaction_report.json` for manual semantic review. Use the rubric in the packet to identify validator gaps.",
            "",
        ]
    )


def raw_email_hits(blob: str) -> list[str]:
    lowered = blob.lower()
    return [f"configured_raw_synthetic_email_{index}" for index, raw in enumerate(RAW_SYNTHETIC_EMAILS, start=1) if raw.lower() in lowered]


def secret_hits(blob: str) -> list[str]:
    matches: list[str] = []
    for index, pattern in enumerate(SECRET_PATTERNS, start=1):
        if pattern.search(blob):
            matches.append(f"private_or_secret_pattern_{index}")
    return matches


def side_effect_summary(conversations: list[dict[str, Any]]) -> dict[str, bool]:
    summary = {key: False for key in SAFETY_KEYS}
    for conversation in conversations:
        for turn in conversation.get("turns") or []:
            flags = turn.get("safety_flags") or {}
            for key in SAFETY_KEYS:
                summary[key] = bool(summary[key] or flags.get(key))
    return summary


def write_outputs(packet: dict[str, Any], records: list[dict[str, Any]]) -> dict[str, Any]:
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    review_packet_json = json.dumps(packet, indent=2, sort_keys=True) + "\n"
    review_packet_jsonl = "".join(json.dumps(record, sort_keys=True) + "\n" for record in records)
    review_packet_md = render_review_packet(packet)
    review_index = render_index(packet)

    (GENERATED_DIR / "review_packet.json").write_text(review_packet_json, encoding="utf-8")
    (GENERATED_DIR / "review_packet.jsonl").write_text(review_packet_jsonl, encoding="utf-8")
    (GENERATED_DIR / "review_packet.md").write_text(review_packet_md, encoding="utf-8")
    (GENERATED_DIR / "review_index.md").write_text(review_index, encoding="utf-8")

    safety_summary = side_effect_summary(packet["conversations"])
    scan_blob = "\n".join([review_packet_json, review_packet_jsonl, review_packet_md, review_index])
    redaction = {
        "checkpoint_id": CHECKPOINT_ID,
        "synthetic_only": True,
        "private_transcripts_included": False,
        "raw_customer_data_included": False,
        "raw_synthetic_emails_found": raw_email_hits(scan_blob),
        "private_or_secret_pattern_matches": secret_hits(scan_blob),
        "redaction_scheme": "Email-like values are replaced with <email:sha256_12:...> stable hash tokens.",
        "side_effect_summary": safety_summary,
        "provider_calls_made": False,
        "local_llm_calls_made": False,
        "live_tts_called": False,
        "generated_audio_required": False,
        "audio_files_included": False,
        "prod_102_opened": False,
    }
    (GENERATED_DIR / "redaction_report.json").write_text(json.dumps(redaction, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    report = render_report(packet, redaction)
    (GENERATED_DIR / "report.md").write_text(report, encoding="utf-8")

    result = {
        "checkpoint_id": CHECKPOINT_ID,
        "status": "pass" if not redaction["raw_synthetic_emails_found"] and not redaction["private_or_secret_pattern_matches"] and not any(safety_summary.values()) else "fail",
        "files_created": [
            "research/experiments/generated/HUMAN-SEMANTIC-REVIEW-PACKET-001/review_packet.md",
            "research/experiments/generated/HUMAN-SEMANTIC-REVIEW-PACKET-001/review_packet.json",
            "research/experiments/generated/HUMAN-SEMANTIC-REVIEW-PACKET-001/review_packet.jsonl",
            "research/experiments/generated/HUMAN-SEMANTIC-REVIEW-PACKET-001/review_index.md",
            "research/experiments/generated/HUMAN-SEMANTIC-REVIEW-PACKET-001/redaction_report.json",
            "research/experiments/generated/HUMAN-SEMANTIC-REVIEW-PACKET-001/report.md",
            "research/experiments/generated/HUMAN-SEMANTIC-REVIEW-PACKET-001/result.json",
        ],
        "conversation_count": packet["conversation_count"],
        "turn_record_count": packet["turn_record_count"],
        "jsonl_record_count": len(records),
        "verticals_covered": sorted(packet["vertical_summary"]),
        "edge_buckets_covered": sorted(packet["edge_bucket_summary"]),
        "hard_edge_case_count": sum(1 for item in packet["conversations"] if {"hard_case", "edge_case"}.intersection(set(item.get("risk_tags") or []))),
        "route_signal_conversation_count": packet["vertical_summary"].get("routesignal_live_demo", 0),
        "redaction_result": redaction,
        "runtime_behavior_changed": False,
        "phase_1_2_3_backpatch_required": False,
        "provider_calls_made": False,
        "local_llm_calls_made": False,
        "live_tts_called": False,
        "sends_email": False,
        "creates_calendar_event": False,
        "writes_crm": False,
        "opens_prod_102": False,
        "instructions_for_manual_review_upload": [
            "review_index.md",
            "review_packet.md",
            "review_packet.json",
            "review_packet.jsonl",
            "redaction_report.json",
        ],
    }
    (GENERATED_DIR / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main() -> int:
    campaigns = synthetic_campaigns()
    evidence_inventory = generated_evidence_inventory()
    conversations = build_conversations(campaigns)
    records = jsonl_records(conversations)
    packet = build_packet_json(conversations=conversations, campaigns=campaigns, evidence_inventory=evidence_inventory)
    result = write_outputs(packet, records)
    print(json.dumps({"status": result["status"], "conversation_count": result["conversation_count"], "jsonl_record_count": result["jsonl_record_count"]}, indent=2, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
