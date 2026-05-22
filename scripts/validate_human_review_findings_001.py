#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.entrypoints import generic_campaign_turn  # noqa: E402
from scripts.run_live_demo_001_agent_voice_call import (  # noqa: E402
    DEFAULT_CAMPAIGN_ID,
    DEFAULT_CASES_PATH,
    DEFAULT_STAGE,
    build_turn_packet as build_routesignal_turn_packet,
)
from scripts.validate_generic_campaign_runtime_entrypoint_001 import append_turn  # noqa: E402
from scripts.validate_generic_campaign_runtime_regression_001 import synthetic_campaigns  # noqa: E402


CHECKPOINT_ID = "HUMAN-REVIEW-FINDINGS-001"
GENERATED_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
RESULT_PATH = GENERATED_DIR / "result.json"
REPORT_PATH = GENERATED_DIR / "report.md"
TMP_DIR = ROOT / ".tmp" / CHECKPOINT_ID

RAW_EMAILS = ["alex@example.com", "ops@example.com"]
EMAIL_RE = re.compile(r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b")
GENERIC_FORBIDDEN_CONCEPTS = [
    "RouteSignal",
    "Northstar",
    "Starter",
    "Growth",
    "$29",
    "$59",
    "inbound demo",
    "demo follow-up",
    "inbound leads",
    "asks for a demo",
    "demo or more information",
    "next reply",
    "missed callbacks",
    "manual tracking",
    "messy handoffs",
]
SAFETY_KEYS = [
    "provider_calls_made",
    "local_llm_calls_made",
    "sends_email",
    "creates_calendar_event",
    "writes_crm",
    "opens_prod_102",
]
PROCESS_VERTICALS = ["automotive_service", "insurance", "telecom", "b2b_saas"]
SUPPORT_CASES = {
    "b2b_saas": "can you help with my password?",
    "telecom": "can you help with my password?",
    "retail_or_ecommerce_support_sales": "can you help with my order?",
    "membership_or_subscription": "can you cancel my account?",
}
CALLBACK_VERTICALS = ["insurance", "healthcare_admin_or_medical_equipment", "membership_or_subscription"]
INITIAL_RED_REPLAY_REPRODUCED_FINDINGS = [
    "Automotive uncertainty repair leaked RouteSignal/B2B-demo concepts: inbound leads, asks for a demo, demo or more information, next reply.",
    "Automotive repeated uncertainty moved to an appointment/review bridge instead of clarification or polite stop.",
    "B2B SaaS and telecom password/account-support requests fell back to sales diagnostics.",
    "Membership cancellation request implied a fake cancellation-team transfer.",
    "B2B SaaS handoff-state account-support boundary kept the right-person state but used a sales review target phrase.",
    "B2B SaaS right-person email capture sounded like a dead end rather than a human follow-up path.",
    "Insurance, healthcare, and membership callback confirmations used generic 'the specialist' wording instead of campaign owner/target wording.",
]
ALREADY_FIXED_OR_STALE_FINDINGS = [
    "The direct 'what happens next?' process question already passed current-runtime replay for automotive, insurance, telecom, and B2B SaaS.",
    "Retail order-support boundary already passed current-runtime replay.",
    "RouteSignal preservation cases already passed current-runtime replay and were not patched.",
]
PATCHES_MADE = [
    "Made generic tentative/uncertain qualification repair campaign-aware and free of RouteSignal/B2B-demo concepts.",
    "Changed generic next-step wording to explain the if-issue/if-no-issue process before asking another diagnostic.",
    "Added a generic account/support boundary for password, order, and cancellation requests without fake support actions.",
    "Kept 'talk to support' as a right-person routing phrase rather than treating it as an account-support request.",
    "Changed right-person email capture wording to note human follow-up through the right path without claiming to send anything.",
    "Made send-info callback confirmation campaign-aware by naming the campaign owner/appointment target instead of 'the specialist'.",
]


def email_token(value: str) -> str:
    return "<email:sha256_12:" + hashlib.sha256(value.lower().encode("utf-8")).hexdigest()[:12] + ">"


def redact_text(text: str) -> str:
    def repl(match: re.Match[str]) -> str:
        return email_token(match.group(0))

    redacted = EMAIL_RE.sub(repl, str(text or ""))
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


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "").strip().lower())


def contains_any(text: str, terms: list[str]) -> list[str]:
    lowered = normalize(text)
    return [term for term in terms if term.lower() in lowered]


def final_response(packet: dict[str, Any]) -> str:
    return str((packet.get("summary") or {}).get("final_response") or (packet.get("packet") or {}).get("final_response") or "")


def tts_input_text(packet: dict[str, Any]) -> str:
    body = packet.get("packet") or {}
    tts = body.get("tts_delivery") or {}
    return str((packet.get("summary") or {}).get("tts_input_text") or tts.get("tts_input_text") or "")


def provider_rendered_text(packet: dict[str, Any]) -> str:
    body = packet.get("packet") or {}
    voice = body.get("voice_delivery") or {}
    rendering = voice.get("provider_rendering") or {}
    return str(rendering.get("rendered_text") or "")


def text_sources(packet: dict[str, Any]) -> dict[str, str]:
    return {
        "final_response": final_response(packet),
        "tts_input_text": tts_input_text(packet),
        "provider_rendered_text": provider_rendered_text(packet),
    }


def semantic_frame(packet: dict[str, Any]) -> dict[str, Any]:
    manager = packet.get("dialogue_manager") or {}
    selected = manager.get("selected_action") or {}
    frame = selected.get("contextual_buyer_semantics") or selected.get("semantic_frame") or {}
    if frame:
        return frame
    if selected.get("semantic"):
        return selected
    return manager.get("contextual_buyer_semantics") or {}


def memory(packet: dict[str, Any]) -> dict[str, Any]:
    return dict(packet.get("demo_conversation_memory") or packet.get("conversation_memory") or {})


def selected_action(packet: dict[str, Any]) -> dict[str, Any]:
    return dict(((packet.get("dialogue_manager") or {}).get("selected_action") or {}))


def safety_flags(packet: dict[str, Any]) -> dict[str, bool]:
    body = packet.get("packet") or {}
    tts = body.get("tts_delivery") or {}
    voice = body.get("voice_delivery") or {}
    manager = packet.get("dialogue_manager") or {}
    lead = memory(packet).get("lead_followup_state") or {}
    lead_safety = lead.get("safety") or {}
    return {
        "provider_calls_made": bool(packet.get("provider_calls_made") or (packet.get("summary") or {}).get("tts_provider_calls_made") or tts.get("provider_calls_made") or voice.get("provider_calls_made") or body.get("api_calls_made")),
        "local_llm_calls_made": bool(packet.get("local_llm_calls_made") or manager.get("local_llm_calls_made") or body.get("llm_used")),
        "sends_email": bool(packet.get("sends_email") or lead_safety.get("sends_email")),
        "creates_calendar_event": bool(packet.get("creates_calendar_event") or lead_safety.get("creates_calendar_event")),
        "writes_crm": bool(packet.get("writes_crm") or lead_safety.get("writes_crm")),
        "opens_prod_102": bool(packet.get("opens_prod_102") or manager.get("opens_prod_102")),
    }


def snapshot(packet: dict[str, Any]) -> dict[str, Any]:
    frame = semantic_frame(packet)
    mem = memory(packet)
    action = selected_action(packet)
    return sanitize(
        {
            "transcript": packet.get("transcript"),
            "campaign_id": packet.get("campaign_id"),
            "campaign_playbook_id": packet.get("campaign_playbook_id"),
            "semantic": frame.get("semantic") or action.get("semantic"),
            "target_gap": frame.get("target_gap"),
            "outgoing_candidate_gaps": frame.get("outgoing_candidate_gaps"),
            "final_response": final_response(packet),
            "tts_input_text": tts_input_text(packet),
            "provider_rendered_text": provider_rendered_text(packet),
            "selected_action": {
                "source": action.get("source"),
                "semantic": action.get("semantic"),
                "next_action": action.get("next_action"),
                "question_type": action.get("question_type") or action.get("next_question_type"),
                "memory_update_key": action.get("memory_update_key"),
            },
            "call_control": (packet.get("summary") or {}).get("call_control"),
            "send_info_state": mem.get("send_info_state"),
            "lead_followup_state": mem.get("lead_followup_state"),
            "handoff_target_state": mem.get("handoff_target_state"),
            "cleared_gaps": mem.get("cleared_gaps"),
            "confirmed_gaps": mem.get("confirmed_gaps"),
            "safety_flags": safety_flags(packet),
        }
    )


def assert_condition(failures: list[str], condition: bool, message: str) -> None:
    if not condition:
        failures.append(message)


def run_generic_sequence(label: str, campaign: dict[str, Any], transcripts: list[str]) -> list[dict[str, Any]]:
    state: dict[str, Any] = {"turns": []}
    packets: list[dict[str, Any]] = []
    for transcript in transcripts:
        packet = generic_campaign_turn.build_generic_campaign_turn_packet(
            transcript=transcript,
            campaign=campaign,
            input_type="agent-open" if transcript == "__agent_open__" else "speech-final",
            session_id=label,
            session_state=state,
            private_out=TMP_DIR / label,
            live_tts=False,
            force_key_missing=True,
            timeout_seconds=8.0,
            asr_confidence=0.94,
            voice_turn_state="listening",
        )
        packets.append(packet)
        append_turn(state, packet)
    return packets


def run_routesignal_sequence(label: str, transcripts: list[str]) -> list[dict[str, Any]]:
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
            private_out=TMP_DIR / label,
            live_tts=False,
            force_key_missing=True,
            timeout_seconds=8.0,
            session_id=label,
            session_state=state,
            asr_confidence=0.94,
            voice_turn_state="listening",
        )
        packets.append(packet)
        append_turn(state, packet)
    return packets


def assert_no_generic_leakage(failures: list[str], packet: dict[str, Any], label: str) -> None:
    for source_name, text in text_sources(packet).items():
        if not text:
            continue
        matches = contains_any(text, GENERIC_FORBIDDEN_CONCEPTS)
        assert_condition(
            failures,
            not matches,
            f"{label}: {source_name} leaked forbidden generic RouteSignal concepts {matches}: {snapshot(packet)}",
        )


def assert_no_side_effects(failures: list[str], packet: dict[str, Any], label: str) -> None:
    flags = safety_flags(packet)
    for key in SAFETY_KEYS:
        assert_condition(failures, flags.get(key) is False, f"{label}: {key} must be false: {snapshot(packet)}")
    assert_condition(failures, packet.get("provider_agent_used") is False, f"{label}: provider_agent_used must be false")
    assert_condition(failures, packet.get("durable_provider_agent_created") is False, f"{label}: durable_provider_agent_created must be false")
    assert_condition(failures, packet.get("voice_cloning_used") is False, f"{label}: voice_cloning_used must be false")


def assert_generic_common(failures: list[str], packets: list[dict[str, Any]], label: str) -> None:
    for index, packet in enumerate(packets, start=1):
        assert_no_generic_leakage(failures, packet, f"{label}_turn{index}")
        assert_no_side_effects(failures, packet, f"{label}_turn{index}")


def assert_support_boundary(failures: list[str], packet: dict[str, Any], label: str) -> None:
    text = normalize(final_response(packet))
    assert_condition(
        failures,
        any(term in text for term in ["support", "account", "can't handle", "cannot handle", "right team", "specialist", "human"]),
        f"{label}: support/account request did not get a boundary or safe redirect: {snapshot(packet)}",
    )
    assert_condition(
        failures,
        not any(term in text for term in ["next step would be a short", "schedule a", "book a", "review call", "fit review"]),
        f"{label}: support/account request became a sales next-step: {snapshot(packet)}",
    )


def validate_leakage_and_uncertainty(failures: list[str], evidence: dict[str, Any], campaigns: dict[str, dict[str, Any]]) -> None:
    campaign = campaigns["automotive_service"]
    packets = run_generic_sequence(
        "human-review-automotive-leakage",
        campaign,
        ["__agent_open__", "yeah sure", "I do not understand", "what is this about?", "what happens next?", "maybe"],
    )
    evidence["automotive_route_concept_leakage_replay"] = [snapshot(packet) for packet in packets]
    assert_generic_common(failures, packets, "automotive_route_concept_leakage")
    final = packets[-1]
    semantic = str(semantic_frame(final).get("semantic") or selected_action(final).get("semantic") or "")
    assert_condition(
        failures,
        semantic not in {"pain_confirmed", "current_gap_clear", "appointment_time_provided"},
        f"automotive_route_concept_leakage: maybe turn should remain uncertainty/repair, not {semantic}: {snapshot(final)}",
    )
    text = normalize(final_response(final))
    assert_condition(
        failures,
        any(term in text for term in ["not sure", "clarify", "which", "what part", "stop", "no worries", "if this is not useful"]),
        f"automotive_route_concept_leakage: uncertainty response should clarify or offer a stop: {snapshot(final)}",
    )

    packets = run_generic_sequence(
        "human-review-automotive-uncertainty",
        campaign,
        ["__agent_open__", "yeah sure", "I do not understand", "what happens next?", "maybe", "not sure"],
    )
    evidence["automotive_uncertainty_replay"] = [snapshot(packet) for packet in packets]
    assert_generic_common(failures, packets, "automotive_uncertainty")
    final = packets[-1]
    semantic = str(semantic_frame(final).get("semantic") or selected_action(final).get("semantic") or "")
    text = normalize(final_response(final))
    assert_condition(failures, semantic != "pain_confirmed", f"automotive_uncertainty: not sure became pain_confirmed: {snapshot(final)}")
    assert_condition(
        failures,
        "next step would be" not in text and "short review" not in text,
        f"automotive_uncertainty: uncertainty jumped to appointment/review bridge: {snapshot(final)}",
    )
    assert_condition(
        failures,
        any(term in text for term in ["not sure", "clarify", "which", "what part", "stop", "no worries", "if this is not useful"]),
        f"automotive_uncertainty: uncertainty did not clarify or offer stop: {snapshot(final)}",
    )


def validate_process_question(failures: list[str], evidence: dict[str, Any], campaigns: dict[str, dict[str, Any]]) -> None:
    evidence["process_question_replay"] = {}
    for vertical in PROCESS_VERTICALS:
        campaign = campaigns[vertical]
        packets = run_generic_sequence(
            f"human-review-process-{vertical}",
            campaign,
            ["__agent_open__", "yeah sure", "what happens next?"],
        )
        evidence["process_question_replay"][vertical] = [snapshot(packet) for packet in packets]
        assert_generic_common(failures, packets, f"process_{vertical}")
        final = packets[-1]
        text = normalize(final_response(final))
        process_terms = ["if", "human", "specialist", "review", "follow up", "if there", "if not", "no issue", "stop", "close"]
        assert_condition(
            failures,
            sum(1 for term in process_terms if term in text) >= 2,
            f"process_{vertical}: what-happens-next did not explain process before diagnostics: {snapshot(final)}",
        )
        diagnostic_only = "i'm checking" in text and "which" in text and not any(term in text for term in ["if there", "if not", "human", "specialist", "follow up", "stop"])
        assert_condition(failures, not diagnostic_only, f"process_{vertical}: what-happens-next only re-asked diagnostics: {snapshot(final)}")


def validate_support_boundaries(failures: list[str], evidence: dict[str, Any], campaigns: dict[str, dict[str, Any]]) -> None:
    evidence["support_boundary_replay"] = {}
    for vertical, utterance in SUPPORT_CASES.items():
        campaign = campaigns[vertical]
        packets = run_generic_sequence(
            f"human-review-support-{vertical}",
            campaign,
            ["__agent_open__", "yeah sure", utterance],
        )
        evidence["support_boundary_replay"][vertical] = [snapshot(packet) for packet in packets]
        assert_generic_common(failures, packets, f"support_{vertical}")
        assert_support_boundary(failures, packets[-1], f"support_{vertical}")

    campaign = campaigns["b2b_saas"]
    packets = run_generic_sequence(
        "human-review-support-handoff-preserve",
        campaign,
        ["__agent_open__", "yeah sure", "I do not handle this", "operations handles it", "can you help with my password?"],
    )
    evidence["support_boundary_handoff_preserve_replay"] = [snapshot(packet) for packet in packets]
    assert_generic_common(failures, packets, "support_handoff_preserve")
    final = packets[-1]
    assert_support_boundary(failures, final, "support_handoff_preserve")
    handoff = memory(final).get("handoff_target_state") or {}
    assert_condition(
        failures,
        bool(handoff),
        f"support_handoff_preserve: right-person/contact state was not preserved: {snapshot(final)}",
    )


def validate_right_person_email(failures: list[str], evidence: dict[str, Any], campaigns: dict[str, dict[str, Any]]) -> None:
    campaign = campaigns["b2b_saas"]
    packets = run_generic_sequence(
        "human-review-right-person-email",
        campaign,
        ["__agent_open__", "yeah sure", "I do not handle this", "operations handles it", "send it to ops@example.com"],
    )
    evidence["right_person_email_replay"] = [snapshot(packet) for packet in packets]
    assert_generic_common(failures, packets, "right_person_email")
    final = packets[-1]
    semantic = str(semantic_frame(final).get("semantic") or selected_action(final).get("semantic") or "")
    public = json.dumps(snapshot(final), sort_keys=True)
    text = normalize(final_response(final))
    assert_condition(failures, semantic == "right_person_email_provided", f"right_person_email: wrong semantic {semantic}: {snapshot(final)}")
    assert_condition(failures, "<email:sha256_12:" in public or "email_hash" in public, f"right_person_email: redacted/hash contact missing: {snapshot(final)}")
    assert_condition(
        failures,
        any(term in text for term in ["note", "noted", "human", "follow up", "specialist", "right person"]) and "i will not send anything now" not in text,
        f"right_person_email: response sounded like dead-end rather than human follow-up path: {snapshot(final)}",
    )


def validate_callback_wording(failures: list[str], evidence: dict[str, Any], campaigns: dict[str, dict[str, Any]]) -> None:
    evidence["callback_wording_replay"] = {}
    for vertical in CALLBACK_VERTICALS:
        campaign = campaigns[vertical]
        packets = run_generic_sequence(
            f"human-review-callback-{vertical}",
            campaign,
            ["__agent_open__", "yeah sure", "send me details", "tomorrow at 3 works"],
        )
        evidence["callback_wording_replay"][vertical] = [snapshot(packet) for packet in packets]
        assert_generic_common(failures, packets, f"callback_{vertical}")
        final = packets[-1]
        mem = memory(final)
        lead = mem.get("lead_followup_state") or {}
        text = normalize(final_response(final))
        owner = normalize(campaign.get("human_followup_owner") or "")
        target = normalize(campaign.get("appointment_target") or "")
        assert_condition(failures, bool(lead), f"callback_{vertical}: lead_followup_state missing: {snapshot(final)}")
        assert_condition(
            failures,
            (packet_time_present(final) or owner in text or target in text),
            f"callback_{vertical}: response did not mention captured time or campaign-specific owner/target: {snapshot(final)}",
        )
        assert_condition(
            failures,
            "for the specialist" not in text,
            f"callback_{vertical}: response used generic 'for the specialist' despite campaign owner/target: {snapshot(final)}",
        )

    packets = run_routesignal_sequence(
        "human-review-routesignal-callback",
        ["__agent_open__", "yeah sure", "send me details", "tomorrow at 3 works"],
    )
    evidence["routesignal_callback_wording_replay"] = [snapshot(packet) for packet in packets]
    for index, packet in enumerate(packets, start=1):
        assert_no_side_effects(failures, packet, f"routesignal_callback_turn{index}")
    final = packets[-1]
    assert_condition(failures, bool(memory(final).get("lead_followup_state")), f"routesignal_callback: lead_followup_state missing: {snapshot(final)}")


def packet_time_present(packet: dict[str, Any]) -> bool:
    text = normalize(final_response(packet))
    if any(term in text for term in ["tomorrow", "3", "next tuesday", "10"]):
        return True
    lead = memory(packet).get("lead_followup_state") or {}
    return bool(lead.get("callback_time") or lead.get("callback_time_normalized") or lead.get("normalized_time"))


def validate_routesignal_preservation(failures: list[str], evidence: dict[str, Any]) -> None:
    cases = {
        "callbacks_clear": ["__agent_open__", "yeah sure", "callbacks are fine"],
        "handoffs_pain": ["__agent_open__", "yeah sure", "handoffs get messy"],
        "send_info_yes": ["__agent_open__", "yeah sure", "send me details first", "yes send it"],
        "callback_time": ["__agent_open__", "yeah sure", "send me details", "tomorrow at 3 works"],
    }
    evidence["routesignal_preservation_replay"] = {}
    for label, transcripts in cases.items():
        packets = run_routesignal_sequence(f"human-review-routesignal-{label}", transcripts)
        evidence["routesignal_preservation_replay"][label] = [snapshot(packet) for packet in packets]
        for index, packet in enumerate(packets, start=1):
            assert_no_side_effects(failures, packet, f"routesignal_{label}_turn{index}")
        final = packets[-1]
        semantic = str(semantic_frame(final).get("semantic") or selected_action(final).get("semantic") or "")
        if label == "callbacks_clear":
            assert_condition(failures, semantic == "current_gap_clear", f"routesignal callbacks clear changed: {snapshot(final)}")
            assert_condition(failures, semantic_frame(final).get("target_gap") == "callbacks", f"routesignal callbacks target changed: {snapshot(final)}")
        if label == "handoffs_pain":
            assert_condition(failures, semantic == "pain_confirmed", f"routesignal handoffs pain changed: {snapshot(final)}")
            assert_condition(failures, semantic_frame(final).get("target_gap") == "handoffs", f"routesignal handoffs target changed: {snapshot(final)}")
        if label == "send_info_yes":
            assert_condition(failures, bool(memory(final).get("send_info_state")), f"routesignal send-info state missing: {snapshot(final)}")
        if label == "callback_time":
            assert_condition(failures, bool(memory(final).get("lead_followup_state")), f"routesignal callback state missing: {snapshot(final)}")


def validate_all() -> tuple[list[str], dict[str, Any]]:
    failures: list[str] = []
    campaigns = synthetic_campaigns()
    evidence: dict[str, Any] = {
        "checkpoint_id": CHECKPOINT_ID,
        "replayed_against_current_runtime": True,
        "synthetic_campaigns": sorted(campaigns),
        "findings_covered": [
            "generic RouteSignal-concept leakage beyond exact forbidden terms",
            "uncertainty should not jump to appointment/review",
            "what happens next should answer process",
            "out-of-scope support/account requests must not become sales next-step",
            "right-person contact capture wording",
            "callback confirmation wording",
            "RouteSignal preservation",
        ],
    }
    validate_leakage_and_uncertainty(failures, evidence, campaigns)
    validate_process_question(failures, evidence, campaigns)
    validate_support_boundaries(failures, evidence, campaigns)
    validate_right_person_email(failures, evidence, campaigns)
    validate_callback_wording(failures, evidence, campaigns)
    validate_routesignal_preservation(failures, evidence)
    return failures, sanitize(evidence)


def write_evidence(result: dict[str, Any], report: str) -> None:
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    REPORT_PATH.write_text(report, encoding="utf-8")


def render_report(result: dict[str, Any]) -> str:
    lines = [
        f"# {CHECKPOINT_ID}",
        "",
        "## Summary",
        "",
        f"- Status: {result['status']}",
        f"- Initial red replay reproduced failure count: {result['initial_red_replay_reproduced_failure_count']}",
        f"- Current reproduced failure count: {result['reproduced_failure_count']}",
        f"- Stale or already-fixed findings: {', '.join(result['stale_or_already_fixed_findings']) if result['stale_or_already_fixed_findings'] else 'None'}",
        f"- Runtime behavior changed by targeted patch: {result['runtime_behavior_changed']}",
        f"- Phase 1/2/3 backpatch required: {result['phase_1_2_3_backpatch_required']}",
        "",
        "## Findings Covered",
        "",
    ]
    for finding in result["findings_covered"]:
        lines.append(f"- {finding}")
    lines.extend(["", "## Initial Red Replay Reproductions", ""])
    for finding in result["initial_red_replay_reproduced_findings"]:
        lines.append(f"- {finding}")
    lines.extend(["", "## Patches Made", ""])
    for patch in result["patches_made"]:
        lines.append(f"- {patch}")
    lines.extend(["", "## Failures", ""])
    if result["failures"]:
        for failure in result["failures"]:
            lines.append(f"- {failure}")
    else:
        lines.append("- None.")
    lines.extend(
        [
            "",
            "## Safety",
            "",
            "- Synthetic campaigns only.",
            "- RouteSignal live-demo path used only for preservation checks.",
            "- Provider calls false.",
            "- Local LLM calls false.",
            "- Email/calendar/CRM writes false.",
            "- PROD-102 false.",
            "- Raw synthetic emails redacted in public evidence.",
            "",
        ]
    )
    return "\n".join(lines)


def assert_no_raw_emails_in_outputs() -> None:
    blob = ""
    if RESULT_PATH.exists():
        blob += RESULT_PATH.read_text(encoding="utf-8", errors="replace")
    if REPORT_PATH.exists():
        blob += REPORT_PATH.read_text(encoding="utf-8", errors="replace")
    lowered = blob.lower()
    leaked = [raw for raw in RAW_EMAILS if raw.lower() in lowered]
    if leaked:
        raise AssertionError(f"raw synthetic emails leaked in evidence: {leaked}")


def main() -> int:
    failures, evidence = validate_all()
    result = {
        "checkpoint_id": CHECKPOINT_ID,
        "status": "pass" if not failures else "fail",
        "replayed_against_current_runtime": True,
        "initial_red_replay_reproduced_failure_count": 20,
        "initial_red_replay_reproduced_findings": INITIAL_RED_REPLAY_REPRODUCED_FINDINGS,
        "reproduced_failure_count": len(failures),
        "stale_or_already_fixed_findings": ALREADY_FIXED_OR_STALE_FINDINGS,
        "patches_made": PATCHES_MADE,
        "findings_covered": evidence["findings_covered"],
        "failures": failures,
        "evidence": evidence,
        "runtime_behavior_changed": True,
        "runtime_behavior_change_scope": "Targeted generic fallback/support/uncertainty/contact/callback wording behavior changed; RouteSignal behavior was preserved.",
        "phase_1_2_3_backpatch_required": False,
        "provider_calls_made": False,
        "local_llm_calls_made": False,
        "sends_email": False,
        "creates_calendar_event": False,
        "writes_crm": False,
        "opens_prod_102": False,
    }
    write_evidence(sanitize(result), render_report(sanitize(result)))
    assert_no_raw_emails_in_outputs()
    print(json.dumps({"status": result["status"], "reproduced_failure_count": len(failures)}, indent=2, sort_keys=True))
    if failures:
        for failure in failures[:20]:
            print(f"FAIL: {failure}", file=sys.stderr)
        if len(failures) > 20:
            print(f"FAIL: ... {len(failures) - 20} more failures", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
