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


CHECKPOINT_ID = "CONTEXTUAL-BUYER-SEMANTICS-009-right-person-handoff"
GENERATED_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
RESULT_PATH = GENERATED_DIR / "result.json"
REPORT_PATH = GENERATED_DIR / "report.md"
TMP_DIR = ROOT / ".tmp" / CHECKPOINT_ID
RAW_EMAILS = {"sarah@example.com", "ops@example.com"}
EMAIL_RE = re.compile(r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b")
HANDOFF_ACTION_IDS = {
    "request_right_person_or_close",
    "request_right_person_contact",
    "capture_right_person_name",
    "capture_right_person_contact",
    "capture_right_person_callback_time",
    "clarify_right_person_contact",
    "close_wrong_person",
    "send_info_to_right_person_contact",
}


def normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9$@.*]+", " ", str(text).lower()).strip()


def redact_email_value(email: str) -> str:
    local, domain = email.lower().split("@", 1)
    return f"{local[:1]}***@{domain}"


def redact_emails(text: str) -> str:
    def replace(match: re.Match[str]) -> str:
        email = match.group(0).lower()
        if email in RAW_EMAILS:
            return redact_email_value(email)
        return "[redacted-email]"

    return EMAIL_RE.sub(replace, str(text))


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


def handoff_target_state(packet: dict[str, Any]) -> dict[str, Any]:
    return dict(memory(packet).get("handoff_target_state") or {})


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
    assert_condition(failures, selected_action(packet).get("source") == "contextual_buyer_semantics", f"{label}: expected contextual source: {snapshot(packet)}")
    assert_condition(failures, selected_action(packet).get("action_id") in expected_set, f"{label}: expected action in {sorted(expected_set)}: {snapshot(packet)}")


def assert_spoken_contains(failures: list[str], packet: dict[str, Any], fragments: set[str], label: str) -> None:
    final_text = normalize(response(packet))
    tts_text = normalize(tts_input_text(packet))
    assert_condition(failures, any(fragment in final_text for fragment in fragments), f"{label}: final_response should contain one of {sorted(fragments)}: {snapshot(packet)}")
    assert_condition(failures, any(fragment in tts_text for fragment in fragments), f"{label}: tts_input_text should contain one of {sorted(fragments)}: {snapshot(packet)}")


def assert_no_external_side_effects(failures: list[str], packet: dict[str, Any], label: str) -> None:
    manager = packet.get("dialogue_manager") or {}
    safety_states = []
    if handoff_target_state(packet):
        safety_states.append(handoff_target_state(packet).get("safety") or {})
    if lead_followup_state(packet):
        safety_states.append(lead_followup_state(packet).get("safety") or {})
    assert_condition(failures, not bool((packet.get("summary") or {}).get("tts_provider_calls_made")), f"{label}: provider calls must stay false: {snapshot(packet)}")
    assert_condition(failures, not bool(manager.get("local_llm_calls_made")), f"{label}: local LLM calls must stay false: {snapshot(packet)}")
    assert_condition(failures, not bool(manager.get("opens_prod_102")), f"{label}: PROD-102 must remain closed: {snapshot(packet)}")
    for safety in safety_states:
        for key in ["provider_calls_made", "local_llm_calls_made", "sends_email", "creates_calendar_event", "writes_crm", "stores_private_contact_in_public_evidence"]:
            assert_condition(failures, safety.get(key) is False, f"{label}: safety.{key} must be false: {snapshot(packet)}")


def assert_handoff_schema(failures: list[str], packet: dict[str, Any], label: str) -> None:
    state = handoff_target_state(packet)
    assert_condition(failures, state.get("schema_version") == 1, f"{label}: handoff_target_state schema missing: {snapshot(packet)}")
    assert_condition(failures, state.get("requested") is True, f"{label}: handoff target should be requested/open: {snapshot(packet)}")
    assert_condition(failures, (state.get("target") or {}).get("raw_contact_stored_in_public_evidence") is False, f"{label}: raw contact flag must be false: {snapshot(packet)}")
    safety = state.get("safety") or {}
    for key in ["provider_calls_made", "local_llm_calls_made", "sends_email", "creates_calendar_event", "writes_crm", "stores_private_contact_in_public_evidence"]:
        assert_condition(failures, safety.get(key) is False, f"{label}: handoff safety.{key} must be false: {snapshot(packet)}")


def assert_handoff_email(failures: list[str], packet: dict[str, Any], label: str, raw_email: str) -> None:
    target = handoff_target_state(packet).get("target") or {}
    assert_condition(failures, target.get("email_redacted") == redact_email_value(raw_email), f"{label}: redacted email mismatch: {snapshot(packet)}")
    assert_condition(failures, bool(target.get("email_hash")), f"{label}: email_hash missing: {snapshot(packet)}")
    assert_condition(failures, raw_email not in json.dumps(snapshot(packet)).lower(), f"{label}: raw email must be redacted from public snapshot")


def assert_callback_normalized(failures: list[str], packet: dict[str, Any], label: str) -> None:
    callback = (lead_followup_state(packet).get("callback") or {})
    normalized = callback.get("normalized") or {}
    assert_condition(failures, bool(callback.get("raw_text_redacted")), f"{label}: callback raw_text_redacted missing: {snapshot(packet)}")
    assert_condition(failures, normalized.get("relative_date") == "tomorrow" or normalized.get("date_text") == "tomorrow", f"{label}: expected tomorrow normalization: {snapshot(packet)}")
    assert_condition(failures, "3" in str(normalized.get("time_text") or ""), f"{label}: expected time fragment 3: {snapshot(packet)}")
    assert_condition(failures, callback.get("needs_clarification") is False, f"{label}: callback should not need clarification: {snapshot(packet)}")


def validate_right_person_handoff(failures: list[str], evidence: dict[str, Any]) -> None:
    scenarios = {
        "scenario_a_wrong_person": ["__agent_open__", "yeah sure", "I'm not the person"],
        "scenario_b_department_named": ["__agent_open__", "yeah sure", "operations handles that"],
        "scenario_c_person_named": ["__agent_open__", "yeah sure", "Sarah handles that"],
        "scenario_d_right_person_email": ["__agent_open__", "yeah sure", "Sarah handles that", "send it to sarah@example.com"],
        "scenario_e_department_plus_email": ["__agent_open__", "yeah sure", "operations handles it, send it to ops@example.com"],
        "scenario_f_right_person_callback_time": ["__agent_open__", "yeah sure", "call Sarah tomorrow at 3"],
        "scenario_g_refusal_to_provide": ["__agent_open__", "yeah sure", "I'm not the person", "I don't know who handles it"],
        "scenario_h_stop_after_wrong_person": ["__agent_open__", "yeah sure", "I'm not the person", "stop calling", "hello?"],
        "scenario_i_send_info_to_manager": ["__agent_open__", "yeah sure", "send it to my manager"],
        "scenario_j_contact_vs_product_routing": ["__agent_open__", "yeah sure", "operations handles lead routing"],
        "scenario_k_trace_audit_alignment": ["__agent_open__", "yeah sure"],
    }
    packets_by_scenario = {label: run_sequence(transcripts, session_id=label) for label, transcripts in scenarios.items()}
    for label, packets in packets_by_scenario.items():
        evidence[label] = [snapshot(packet) for packet in packets]
        for index, packet in enumerate(packets, start=1):
            assert_no_external_side_effects(failures, packet, f"{label}_turn{index}")

    a3 = packets_by_scenario["scenario_a_wrong_person"][2]
    assert_semantic(failures, a3, label="scenario_a_turn3", expected="wrong_person_or_wrong_department")
    assert_action(failures, a3, label="scenario_a_turn3", expected="request_right_person_or_close")
    assert_handoff_schema(failures, a3, "scenario_a_turn3")
    assert_condition(failures, handoff_target_state(a3).get("capture_status") == "needs_right_person", f"scenario_a_turn3: expected needs_right_person: {snapshot(a3)}")
    assert_condition(failures, memory(a3).get("selected_gap") != "routing", f"scenario_a_turn3: wrong person must not become product routing: {snapshot(a3)}")
    assert_condition(failures, call_control(a3) == "continue-call", f"scenario_a_turn3: should continue for right-person capture: {snapshot(a3)}")
    assert_condition(failures, "workflow review" not in normalize(response(a3)), f"scenario_a_turn3: should not ask workflow review: {snapshot(a3)}")
    assert_spoken_contains(failures, a3, {"right person", "right team", "who handles"}, "scenario_a_turn3")

    b3 = packets_by_scenario["scenario_b_department_named"][2]
    assert_semantic(failures, b3, label="scenario_b_turn3", expected={"department_named", "manager_required", "wrong_person_or_wrong_department"})
    assert_action(failures, b3, label="scenario_b_turn3", expected="request_right_person_contact")
    assert_handoff_schema(failures, b3, "scenario_b_turn3")
    assert_condition(failures, (handoff_target_state(b3).get("target") or {}).get("role_or_department") == "operations", f"scenario_b_turn3: operations should be captured: {snapshot(b3)}")
    assert_condition(failures, not bool(memory(b3).get("appointment_close_ready")), f"scenario_b_turn3: appointment must not be confirmed: {snapshot(b3)}")
    assert_spoken_contains(failures, b3, {"contact", "email", "callback"}, "scenario_b_turn3")

    c3 = packets_by_scenario["scenario_c_person_named"][2]
    assert_semantic(failures, c3, label="scenario_c_turn3", expected="right_person_named")
    assert_action(failures, c3, label="scenario_c_turn3", expected={"capture_right_person_name", "request_right_person_contact"})
    assert_handoff_schema(failures, c3, "scenario_c_turn3")
    assert_condition(failures, handoff_target_state(c3).get("capture_status") == "person_name_captured", f"scenario_c_turn3: expected person_name_captured: {snapshot(c3)}")
    assert_spoken_contains(failures, c3, {"email", "callback", "contact"}, "scenario_c_turn3")

    d4 = packets_by_scenario["scenario_d_right_person_email"][3]
    assert_semantic(failures, d4, label="scenario_d_turn4", expected="right_person_email_provided")
    assert_action(failures, d4, label="scenario_d_turn4", expected="capture_right_person_contact")
    assert_handoff_schema(failures, d4, "scenario_d_turn4")
    assert_handoff_email(failures, d4, "scenario_d_turn4", "sarah@example.com")
    assert_condition(failures, handoff_target_state(d4).get("lead_status") == "open_send_info_to_right_person", f"scenario_d_turn4: expected send-info handoff lead: {snapshot(d4)}")

    e3 = packets_by_scenario["scenario_e_department_plus_email"][2]
    assert_semantic(failures, e3, label="scenario_e_turn3", expected={"right_person_email_provided", "department_named"})
    assert_action(failures, e3, label="scenario_e_turn3", expected="capture_right_person_contact")
    assert_handoff_schema(failures, e3, "scenario_e_turn3")
    assert_condition(failures, (handoff_target_state(e3).get("target") or {}).get("role_or_department") == "operations", f"scenario_e_turn3: operations should be captured: {snapshot(e3)}")
    assert_handoff_email(failures, e3, "scenario_e_turn3", "ops@example.com")
    assert_condition(failures, handoff_target_state(e3).get("lead_status") == "open_send_info_to_right_person", f"scenario_e_turn3: expected send-info handoff lead: {snapshot(e3)}")

    f3 = packets_by_scenario["scenario_f_right_person_callback_time"][2]
    assert_semantic(failures, f3, label="scenario_f_turn3", expected="right_person_callback_time_provided")
    assert_action(failures, f3, label="scenario_f_turn3", expected="capture_right_person_callback_time")
    assert_handoff_schema(failures, f3, "scenario_f_turn3")
    assert_callback_normalized(failures, f3, "scenario_f_turn3")
    appointment = lead_followup_state(f3).get("appointment") or {}
    assert_condition(failures, appointment.get("type") in {"right_person_callback", "handoff_callback"}, f"scenario_f_turn3: appointment type mismatch: {snapshot(f3)}")
    assert_condition(failures, call_control(f3) == "schedule-and-end", f"scenario_f_turn3: usable callback should schedule-and-end: {snapshot(f3)}")

    g4 = packets_by_scenario["scenario_g_refusal_to_provide"][3]
    assert_semantic(failures, g4, label="scenario_g_turn4", expected={"refused_right_person_contact", "right_person_contact_unclear"})
    assert_action(failures, g4, label="scenario_g_turn4", expected={"clarify_right_person_contact", "close_wrong_person"})
    assert_condition(failures, "workflow review" not in normalize(response(g4)), f"scenario_g_turn4: should not push workflow review: {snapshot(g4)}")
    assert_spoken_contains(failures, g4, {"stop", "right person", "no problem"}, "scenario_g_turn4")

    h4 = packets_by_scenario["scenario_h_stop_after_wrong_person"][3]
    h5 = packets_by_scenario["scenario_h_stop_after_wrong_person"][4]
    assert_semantic(failures, h4, label="scenario_h_turn4", expected="stop_request")
    assert_condition(failures, call_control(h4) == "end-call", f"scenario_h_turn4: explicit stop must end call: {snapshot(h4)}")
    assert_condition(failures, call_control(h5) == "end-call", f"scenario_h_turn5: terminal stop must persist: {snapshot(h5)}")

    i3 = packets_by_scenario["scenario_i_send_info_to_manager"][2]
    assert_semantic(failures, i3, label="scenario_i_turn3", expected="send_info_to_right_person")
    assert_action(failures, i3, label="scenario_i_turn3", expected="send_info_to_right_person_contact")
    assert_handoff_schema(failures, i3, "scenario_i_turn3")
    assert_condition(failures, not (handoff_target_state(i3).get("target") or {}).get("email_redacted"), f"scenario_i_turn3: no contact should be captured: {snapshot(i3)}")
    assert_spoken_contains(failures, i3, {"email", "callback", "manager"}, "scenario_i_turn3")

    j3 = packets_by_scenario["scenario_j_contact_vs_product_routing"][2]
    assert_semantic(failures, j3, label="scenario_j_turn3", expected={"department_named", "wrong_person_or_wrong_department"})
    assert_condition(failures, memory(j3).get("selected_gap") != "routing", f"scenario_j_turn3: contact routing must not become product routing: {snapshot(j3)}")
    assert_spoken_contains(failures, j3, {"operations", "contact", "right person", "workflow issue"}, "scenario_j_turn3")

    k2 = packets_by_scenario["scenario_k_trace_audit_alignment"][1]
    final_text = normalize(response(k2))
    asked_standard_multi_gap = all(fragment in final_text for fragment in ["callbacks", "manual tracking", "handoffs"])
    if asked_standard_multi_gap:
        expected_gaps = {"callbacks", "manual_tracking", "handoffs"}
        trace_outgoing = set(str(item) for item in (semantic_frame(k2).get("outgoing_candidate_gaps") or []))
        evidence_outgoing = set(str(item) for item in ((semantic_frame(k2).get("evidence") or {}).get("outgoing_candidate_gaps") or []))
        memory_outgoing = set(str(item) for item in (memory(k2).get("outgoing_candidate_gaps") or []))
        assert_condition(
            failures,
            expected_gaps.issubset(trace_outgoing) or expected_gaps.issubset(evidence_outgoing) or expected_gaps.issubset(memory_outgoing),
            f"scenario_k_turn2: outgoing diagnostic scope must expose callbacks/manual_tracking/handoffs: {snapshot(k2)}",
        )
        if not expected_gaps.issubset(set(str(item) for item in (semantic_frame(k2).get("candidate_gaps") or []))):
            assert_condition(
                failures,
                bool(trace_outgoing or evidence_outgoing),
                f"scenario_k_turn2: trace must separate buyer-context candidate_gaps from outgoing_response_candidate_gaps: {snapshot(k2)}",
            )

    serialized_evidence = json.dumps(evidence).lower()
    for raw_email in RAW_EMAILS:
        assert_condition(failures, raw_email not in serialized_evidence, f"public generated evidence must redact raw synthetic email {raw_email}")


def render_report(payload: dict[str, Any]) -> str:
    lines = [
        "# CONTEXTUAL-BUYER-SEMANTICS-009 Right Person Handoff",
        "",
        f"- Passed: `{str(payload['passed']).lower()}`",
        f"- Failure count: `{payload['failure_count']}`",
        "- Provider calls made: `false`",
        "- Local LLM calls made: `false`",
        "- Sends email: `false`",
        "- Creates calendar event: `false`",
        "- Writes CRM: `false`",
        "- Raw synthetic emails stored in public evidence: `false`",
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
            "- Verifies wrong-person, department, named person, right-person email, department plus email, right-person callback time, refusal, explicit stop, send-info to manager, and contact-vs-product-routing separation.",
            "- Verifies the outgoing diagnostic trace exposes callbacks, manual tracking, and handoffs when the spoken response asks all three.",
            "- Keeps synthetic right-person contact details redacted from generated public evidence.",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    failures: list[str] = []
    evidence: dict[str, Any] = {}
    validate_right_person_handoff(failures, evidence)
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
            "raw_synthetic_emails_in_public_evidence": any(raw in json.dumps(evidence).lower() for raw in RAW_EMAILS),
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
