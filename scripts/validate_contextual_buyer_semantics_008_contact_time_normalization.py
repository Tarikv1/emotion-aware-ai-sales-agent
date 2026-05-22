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

from scripts.run_live_demo_001_agent_voice_call import (  # noqa: E402
    DEFAULT_CAMPAIGN_ID,
    DEFAULT_CASES_PATH,
    DEFAULT_STAGE,
    build_turn_packet,
)


CHECKPOINT_ID = "CONTEXTUAL-BUYER-SEMANTICS-008-contact-time-normalization"
GENERATED_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
RESULT_PATH = GENERATED_DIR / "result.json"
REPORT_PATH = GENERATED_DIR / "report.md"
TMP_DIR = ROOT / ".tmp" / CHECKPOINT_ID
RAW_SYNTHETIC_EMAIL = "alex@example.com"
REDACTED_EMAIL = "a***@example.com"
RAW_SYNTHETIC_ASR_EMAIL = "alex at example dot com"
EMAIL_RE = re.compile(r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b")


def normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9$@.*]+", " ", str(text).lower()).strip()


def redact_emails(text: str) -> str:
    redacted = EMAIL_RE.sub(lambda match: REDACTED_EMAIL if match.group(0).lower() == RAW_SYNTHETIC_EMAIL else "[redacted-email]", str(text))
    return redacted.replace(RAW_SYNTHETIC_ASR_EMAIL, "[redacted-spoken-email]")


def sanitize(value: Any) -> Any:
    if isinstance(value, str):
        return redact_emails(value)
    if isinstance(value, list):
        return [sanitize(item) for item in value]
    if isinstance(value, dict):
        return {str(key): sanitize(item) for key, item in value.items()}
    return value


def assert_condition(failures: list[str], condition: bool, message: str) -> None:
    if not condition:
        failures.append(message)


def append_turn(state: dict[str, Any], packet: dict[str, Any]) -> None:
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


def run_sequence(transcripts: list[str], *, session_id: str) -> list[dict[str, Any]]:
    state: dict[str, Any] = {"turns": []}
    packets: list[dict[str, Any]] = []
    for transcript in transcripts:
        packet = build_demo_turn(transcript, state, session_id=session_id)
        packets.append(packet)
        append_turn(state, packet)
    return packets


def response(packet: dict[str, Any]) -> str:
    return str((packet.get("summary") or {}).get("final_response") or "")


def tts_input_text(packet: dict[str, Any]) -> str:
    summary = packet.get("summary") or {}
    packet_tts = ((packet.get("packet") or {}).get("tts_delivery") or {})
    return str(summary.get("tts_input_text") or packet_tts.get("tts_input_text") or response(packet))


def semantic_frame(packet: dict[str, Any]) -> dict[str, Any]:
    manager = packet.get("dialogue_manager") or {}
    return dict(manager.get("contextual_buyer_semantics") or (manager.get("state_before") or {}).get("contextual_buyer_semantics") or {})


def memory(packet: dict[str, Any]) -> dict[str, Any]:
    return dict(packet.get("demo_conversation_memory") or packet.get("conversation_memory") or {})


def lead_followup_state(packet: dict[str, Any]) -> dict[str, Any]:
    return dict(memory(packet).get("lead_followup_state") or {})


def send_info_state(packet: dict[str, Any]) -> dict[str, Any]:
    return dict(memory(packet).get("send_info_state") or {})


def selected_action(packet: dict[str, Any]) -> dict[str, Any]:
    return dict(((packet.get("dialogue_manager") or {}).get("selected_action") or {}))


def call_control(packet: dict[str, Any]) -> str:
    return str((packet.get("summary") or {}).get("call_control") or "")


def snapshot(packet: dict[str, Any]) -> dict[str, Any]:
    manager = packet.get("dialogue_manager") or {}
    return sanitize(
        {
            "turn": packet.get("session_turn_index"),
            "transcript": packet.get("transcript"),
            "response": response(packet),
            "tts_input_text": tts_input_text(packet),
            "call_control": call_control(packet),
            "semantic_frame": semantic_frame(packet),
            "selected_action": selected_action(packet),
            "memory": memory(packet),
            "provider_calls_made": bool((packet.get("summary") or {}).get("tts_provider_calls_made")),
            "local_llm_calls_made": bool(manager.get("local_llm_calls_made")),
            "opens_prod_102": bool(manager.get("opens_prod_102")),
        }
    )


def assert_semantic(failures: list[str], packet: dict[str, Any], *, label: str, expected: str | set[str]) -> None:
    frame = semantic_frame(packet)
    actual = str(frame.get("semantic") or "")
    expected_set = {expected} if isinstance(expected, str) else set(expected)
    assert_condition(failures, bool(frame), f"{label}: semantic frame must be exposed: {snapshot(packet)}")
    assert_condition(failures, actual in expected_set, f"{label}: expected semantic in {sorted(expected_set)}, got `{actual}`: {snapshot(packet)}")


def assert_action(failures: list[str], packet: dict[str, Any], *, label: str, expected: str | set[str]) -> None:
    expected_set = {expected} if isinstance(expected, str) else set(expected)
    assert_condition(failures, selected_action(packet).get("action_id") in expected_set, f"{label}: expected action in {sorted(expected_set)}: {snapshot(packet)}")


def assert_spoken_contains(failures: list[str], packet: dict[str, Any], fragments: set[str], label: str) -> None:
    final_text = normalize(response(packet))
    tts_text = normalize(tts_input_text(packet))
    assert_condition(failures, any(fragment in final_text for fragment in fragments), f"{label}: final_response should contain one of {sorted(fragments)}: {snapshot(packet)}")
    assert_condition(failures, any(fragment in tts_text for fragment in fragments), f"{label}: tts_input_text should contain one of {sorted(fragments)}: {snapshot(packet)}")


def assert_no_external_side_effects(failures: list[str], packet: dict[str, Any], label: str) -> None:
    manager = packet.get("dialogue_manager") or {}
    safety = ((lead_followup_state(packet).get("safety") or {}) if lead_followup_state(packet) else {})
    assert_condition(failures, not bool((packet.get("summary") or {}).get("tts_provider_calls_made")), f"{label}: provider calls must stay false: {snapshot(packet)}")
    assert_condition(failures, not bool(manager.get("local_llm_calls_made")), f"{label}: local LLM calls must stay false: {snapshot(packet)}")
    assert_condition(failures, not bool(manager.get("opens_prod_102")), f"{label}: PROD-102 must remain closed: {snapshot(packet)}")
    for key in ["provider_calls_made", "local_llm_calls_made", "sends_email", "creates_calendar_event", "writes_crm", "stores_private_contact_in_public_evidence"]:
        if safety:
            assert_condition(failures, safety.get(key) is False, f"{label}: safety.{key} must be false: {snapshot(packet)}")


def assert_email_state(failures: list[str], packet: dict[str, Any], label: str, *, source: str = "explicit_email") -> None:
    lead = lead_followup_state(packet)
    contact = lead.get("contact") or {}
    assert_condition(failures, lead.get("schema_version") == 1, f"{label}: lead_followup_state schema missing: {snapshot(packet)}")
    assert_condition(failures, contact.get("email_redacted") == REDACTED_EMAIL, f"{label}: redacted email missing: {snapshot(packet)}")
    assert_condition(failures, bool(contact.get("email_hash")), f"{label}: email_hash missing: {snapshot(packet)}")
    assert_condition(failures, contact.get("email_source") == source, f"{label}: email_source mismatch: {snapshot(packet)}")
    assert_condition(failures, contact.get("email_valid") is True, f"{label}: email should be valid: {snapshot(packet)}")
    assert_condition(failures, contact.get("raw_email_stored_in_public_evidence") is False, f"{label}: raw email flag must be false: {snapshot(packet)}")


def assert_no_email_state(failures: list[str], packet: dict[str, Any], label: str) -> None:
    contact = (lead_followup_state(packet).get("contact") or {})
    assert_condition(failures, not contact.get("email_redacted"), f"{label}: no email should be captured: {snapshot(packet)}")
    assert_condition(failures, not contact.get("email_hash"), f"{label}: no email hash should be captured: {snapshot(packet)}")


def assert_callback_normalized(
    failures: list[str],
    packet: dict[str, Any],
    label: str,
    *,
    expected_relative: str | None = None,
    expected_time_fragment: str | None = None,
    needs_clarification: bool | None = None,
) -> None:
    lead = lead_followup_state(packet)
    callback = lead.get("callback") or {}
    normalized = callback.get("normalized") or {}
    assert_condition(failures, bool(callback.get("raw_text_redacted")), f"{label}: callback raw_text_redacted missing: {snapshot(packet)}")
    if expected_relative is not None:
        assert_condition(
            failures,
            normalized.get("relative_date") == expected_relative or normalized.get("date_text") == expected_relative or normalized.get("day_text") == expected_relative,
            f"{label}: expected relative/date `{expected_relative}`: {snapshot(packet)}",
        )
    if expected_time_fragment is not None:
        assert_condition(failures, expected_time_fragment in str(normalized.get("time_text") or ""), f"{label}: expected time fragment `{expected_time_fragment}`: {snapshot(packet)}")
    if needs_clarification is not None:
        assert_condition(failures, callback.get("needs_clarification") is needs_clarification, f"{label}: needs_clarification mismatch: {snapshot(packet)}")


def assert_appointment(failures: list[str], packet: dict[str, Any], label: str, *, appointment_type: str | set[str], confirmed: bool) -> None:
    appointment = lead_followup_state(packet).get("appointment") or {}
    expected_set = {appointment_type} if isinstance(appointment_type, str) else set(appointment_type)
    assert_condition(failures, appointment.get("type") in expected_set, f"{label}: appointment.type mismatch: {snapshot(packet)}")
    assert_condition(failures, appointment.get("confirmed") is confirmed, f"{label}: appointment.confirmed mismatch: {snapshot(packet)}")


def validate_contact_time_normalization(failures: list[str], evidence: dict[str, Any]) -> None:
    scenarios = {
        "scenario_a_email_only": ["__agent_open__", "yeah sure", "send me details", f"send it to {RAW_SYNTHETIC_EMAIL}"],
        "scenario_b_callback_only": ["__agent_open__", "yeah sure", "send me details", "tomorrow at 3 works"],
        "scenario_c_email_and_callback": ["__agent_open__", "yeah sure", "send me details", f"email {RAW_SYNTHETIC_EMAIL} and call tomorrow at 3"],
        "scenario_d_vague_callback": ["__agent_open__", "yeah sure", "send me details", "next week"],
        "scenario_e_asr_spelled_email": ["__agent_open__", "yeah sure", "send me details", "alex at example dot com"],
        "scenario_f_invalid_email_like": ["__agent_open__", "yeah sure", "send me details", "send it to alex at example"],
        "scenario_g_workflow_review_time": ["__agent_open__", "yeah sure", "missed callbacks happen sometimes", "yeah that would be useful", "tomorrow at 3 works"],
        "scenario_h_ordinary_callback": ["__agent_open__", "call me tomorrow at 3"],
    }
    packets_by_scenario = {label: run_sequence(transcripts, session_id=label) for label, transcripts in scenarios.items()}
    for label, packets in packets_by_scenario.items():
        evidence[label] = [snapshot(packet) for packet in packets]
        for index, packet in enumerate(packets, start=1):
            assert_no_external_side_effects(failures, packet, f"{label}_turn{index}")

    a4 = packets_by_scenario["scenario_a_email_only"][3]
    assert_semantic(failures, a4, label="scenario_a_turn4", expected="email_provided")
    assert_action(failures, a4, label="scenario_a_turn4", expected="capture_send_info_email")
    assert_email_state(failures, a4, "scenario_a_turn4")
    assert_condition(failures, lead_followup_state(a4).get("lead_status") == "open_send_info", f"scenario_a_turn4: lead_status mismatch: {snapshot(a4)}")
    assert_condition(failures, lead_followup_state(a4).get("capture_status") == "email_captured", f"scenario_a_turn4: capture_status mismatch: {snapshot(a4)}")
    assert_condition(failures, not (lead_followup_state(a4).get("callback") or {}).get("raw_text_redacted"), f"scenario_a_turn4: callback should be empty: {snapshot(a4)}")
    assert_condition(failures, call_control(a4) != "schedule-and-end", f"scenario_a_turn4: email-only should not schedule-and-end: {snapshot(a4)}")

    b4 = packets_by_scenario["scenario_b_callback_only"][3]
    assert_semantic(failures, b4, label="scenario_b_turn4", expected="callback_time_provided")
    assert_action(failures, b4, label="scenario_b_turn4", expected="capture_send_info_callback_time")
    assert_callback_normalized(failures, b4, "scenario_b_turn4", expected_relative="tomorrow", expected_time_fragment="3", needs_clarification=False)
    assert_condition(failures, lead_followup_state(b4).get("lead_status") == "open_callback", f"scenario_b_turn4: lead_status mismatch: {snapshot(b4)}")
    assert_appointment(failures, b4, "scenario_b_turn4", appointment_type={"send_info_followup", "callback"}, confirmed=True)
    assert_no_email_state(failures, b4, "scenario_b_turn4")
    assert_condition(failures, call_control(b4) == "schedule-and-end", f"scenario_b_turn4: usable callback should schedule-and-end: {snapshot(b4)}")

    c4 = packets_by_scenario["scenario_c_email_and_callback"][3]
    assert_action(failures, c4, label="scenario_c_turn4", expected="capture_send_info_email_and_callback")
    assert_condition(failures, lead_followup_state(c4).get("capture_status") == "email_and_callback_time_captured", f"scenario_c_turn4: capture_status mismatch: {snapshot(c4)}")
    assert_email_state(failures, c4, "scenario_c_turn4")
    assert_callback_normalized(failures, c4, "scenario_c_turn4", expected_relative="tomorrow", expected_time_fragment="3", needs_clarification=False)
    assert_condition(failures, RAW_SYNTHETIC_EMAIL not in json.dumps(snapshot(c4)), "scenario_c_turn4: snapshot must redact raw synthetic email")

    d4 = packets_by_scenario["scenario_d_vague_callback"][3]
    assert_semantic(failures, d4, label="scenario_d_turn4", expected={"callback_time_unclear", "contact_detail_unclear"})
    assert_callback_normalized(failures, d4, "scenario_d_turn4", expected_relative="next_week", needs_clarification=True)
    assert_condition(failures, call_control(d4) != "schedule-and-end", f"scenario_d_turn4: vague time must not schedule-and-end: {snapshot(d4)}")
    assert_spoken_contains(failures, d4, {"day and time", "what day", "what time"}, "scenario_d_turn4")

    e4 = packets_by_scenario["scenario_e_asr_spelled_email"][3]
    assert_semantic(failures, e4, label="scenario_e_turn4", expected={"email_provided", "contact_detail_unclear"})
    if semantic_frame(e4).get("semantic") == "email_provided":
        assert_email_state(failures, e4, "scenario_e_turn4", source="asr_spelled_email")
    else:
        assert_condition(failures, lead_followup_state(e4).get("capture_status") == "contact_unclear", f"scenario_e_turn4: explicit unclear contact required: {snapshot(e4)}")
    assert_condition(failures, RAW_SYNTHETIC_ASR_EMAIL not in json.dumps(snapshot(e4)).lower(), "scenario_e_turn4: raw spoken email should not appear in public snapshot")

    f4 = packets_by_scenario["scenario_f_invalid_email_like"][3]
    assert_semantic(failures, f4, label="scenario_f_turn4", expected="contact_detail_unclear")
    assert_no_email_state(failures, f4, "scenario_f_turn4")
    assert_condition(failures, lead_followup_state(f4).get("capture_status") == "contact_unclear", f"scenario_f_turn4: capture_status mismatch: {snapshot(f4)}")
    assert_condition(failures, call_control(f4) != "schedule-and-end", f"scenario_f_turn4: invalid email must not schedule-and-end: {snapshot(f4)}")
    assert_spoken_contains(failures, f4, {"repeat the email", "callback time"}, "scenario_f_turn4")

    g5 = packets_by_scenario["scenario_g_workflow_review_time"][4]
    assert_semantic(failures, g5, label="scenario_g_turn5", expected="appointment_time_given")
    assert_callback_normalized(failures, g5, "scenario_g_turn5", expected_relative="tomorrow", expected_time_fragment="3", needs_clarification=False)
    assert_appointment(failures, g5, "scenario_g_turn5", appointment_type="workflow_review", confirmed=True)
    assert_condition(failures, call_control(g5) == "schedule-and-end", f"scenario_g_turn5: workflow-review time should schedule-and-end: {snapshot(g5)}")
    assert_no_email_state(failures, g5, "scenario_g_turn5")

    h2 = packets_by_scenario["scenario_h_ordinary_callback"][1]
    assert_condition(failures, not send_info_state(h2), f"scenario_h_turn2: ordinary callback must not create send_info_state: {snapshot(h2)}")
    if call_control(h2) == "schedule-and-end":
        assert_callback_normalized(failures, h2, "scenario_h_turn2", expected_relative="tomorrow", expected_time_fragment="3", needs_clarification=False)
        assert_appointment(failures, h2, "scenario_h_turn2", appointment_type="callback", confirmed=True)

    serialized_evidence = json.dumps(evidence)
    assert_condition(failures, RAW_SYNTHETIC_EMAIL not in serialized_evidence, "public generated evidence must redact raw synthetic email")


def render_report(payload: dict[str, Any]) -> str:
    lines = [
        "# CONTEXTUAL-BUYER-SEMANTICS-008 Contact Time Normalization",
        "",
        f"- Passed: `{str(payload['passed']).lower()}`",
        f"- Failure count: `{payload['failure_count']}`",
        "- Provider calls made: `false`",
        "- Local LLM calls made: `false`",
        "- Sends email: `false`",
        "- Creates calendar event: `false`",
        "- Writes CRM: `false`",
        "- Raw synthetic email stored in public evidence: `false`",
        "",
        "## Failures",
        "",
    ]
    if payload["failures"]:
        lines.extend(f"- {failure}" for failure in payload["failures"])
    else:
        lines.append("- None")
    lines.extend(
        [
            "",
            "## Coverage",
            "",
            "- Verifies email-only, callback-only, email+callback, vague callback, ASR-spelled email, invalid email-like text, workflow-review appointment time, and ordinary callback outside send-info.",
            "- Enforces lead_followup_state with contact, callback normalization, appointment, and safety sections.",
            "- Keeps synthetic email redacted from generated public evidence.",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    failures: list[str] = []
    evidence: dict[str, Any] = {}
    validate_contact_time_normalization(failures, evidence)
    payload = sanitize(
        {
            "checkpoint_id": CHECKPOINT_ID,
            "passed": not failures,
            "failure_count": len(failures),
            "failures": failures,
            "provider_calls_made": False,
            "local_llm_calls_made": False,
            "sends_email": False,
            "creates_calendar_event": False,
            "writes_crm": False,
            "opens_prod_102": False,
            "raw_synthetic_email_in_public_evidence": RAW_SYNTHETIC_EMAIL in json.dumps(evidence),
            "evidence": evidence,
        }
    )
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    REPORT_PATH.write_text(render_report(payload), encoding="utf-8")
    if failures:
        raise AssertionError(f"{CHECKPOINT_ID} failed with {len(failures)} issue(s). See {RESULT_PATH}.")
    print(f"{CHECKPOINT_ID} validation passed.")


if __name__ == "__main__":
    main()
