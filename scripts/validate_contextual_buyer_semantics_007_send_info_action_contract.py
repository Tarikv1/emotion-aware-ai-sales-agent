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


CHECKPOINT_ID = "CONTEXTUAL-BUYER-SEMANTICS-007-send-info-action-contract"
GENERATED_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
RESULT_PATH = GENERATED_DIR / "result.json"
REPORT_PATH = GENERATED_DIR / "report.md"
TMP_DIR = ROOT / ".tmp" / CHECKPOINT_ID
RAW_SYNTHETIC_EMAIL = "alex@example.com"
REDACTED_EMAIL = "a***@example.com"
EMAIL_RE = re.compile(r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b")
SEND_INFO_ACTION_IDS = {
    "request_send_info_contact",
    "capture_send_info_email",
    "capture_send_info_callback_time",
    "capture_send_info_email_and_callback",
    "clarify_send_info_contact",
    "close_send_info_refused",
}


def normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9$@.*]+", " ", str(text).lower()).strip()


def redact_emails(text: str) -> str:
    return EMAIL_RE.sub(lambda match: REDACTED_EMAIL if match.group(0).lower() == RAW_SYNTHETIC_EMAIL else "[redacted-email]", str(text))


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


def send_info_state(packet: dict[str, Any]) -> dict[str, Any]:
    return dict(memory(packet).get("send_info_state") or {})


def selected_action(packet: dict[str, Any]) -> dict[str, Any]:
    return dict(((packet.get("dialogue_manager") or {}).get("selected_action") or {}))


def decision_snapshot(packet: dict[str, Any]) -> dict[str, Any]:
    return dict(packet.get("decision_snapshot") or ((packet.get("packet") or {}).get("decision_snapshot") or {}))


def call_control(packet: dict[str, Any]) -> str:
    return str((packet.get("summary") or {}).get("call_control") or "")


def gap_set(packet: dict[str, Any], key: str) -> set[str]:
    return set(str(item) for item in (memory(packet).get(key) or []))


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
            "decision_snapshot": decision_snapshot(packet),
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


def assert_action(
    failures: list[str],
    packet: dict[str, Any],
    *,
    label: str,
    action_id: str,
    template_id: str,
    call_control_value: str,
) -> None:
    action = selected_action(packet)
    assert_condition(failures, action.get("source") == "contextual_buyer_semantics", f"{label}: expected contextual source: {snapshot(packet)}")
    assert_condition(failures, action.get("action_id") == action_id, f"{label}: expected action_id `{action_id}`: {snapshot(packet)}")
    assert_condition(failures, action.get("template_id") == template_id, f"{label}: expected template_id `{template_id}`: {snapshot(packet)}")
    assert_condition(failures, action.get("call_control") == call_control_value, f"{label}: selected action call_control mismatch: {snapshot(packet)}")
    assert_condition(failures, call_control(packet) == call_control_value, f"{label}: summary call_control mismatch: {snapshot(packet)}")


def assert_decision_next_action(failures: list[str], packet: dict[str, Any], expected: str, label: str) -> None:
    assert_condition(failures, decision_snapshot(packet).get("next_action") == expected, f"{label}: expected decision next_action `{expected}`: {snapshot(packet)}")


def assert_spoken_contains(failures: list[str], packet: dict[str, Any], fragments: set[str], label: str) -> None:
    final_text = normalize(response(packet))
    tts_text = normalize(tts_input_text(packet))
    assert_condition(failures, any(fragment in final_text for fragment in fragments), f"{label}: final_response should contain one of {sorted(fragments)}: {snapshot(packet)}")
    assert_condition(failures, any(fragment in tts_text for fragment in fragments), f"{label}: tts_input_text should contain one of {sorted(fragments)}: {snapshot(packet)}")


def assert_no_provider_or_llm(failures: list[str], packet: dict[str, Any], label: str) -> None:
    manager = packet.get("dialogue_manager") or {}
    assert_condition(failures, not bool((packet.get("summary") or {}).get("tts_provider_calls_made")), f"{label}: provider calls must stay false: {snapshot(packet)}")
    assert_condition(failures, not bool(manager.get("local_llm_calls_made")), f"{label}: local LLM calls must stay false: {snapshot(packet)}")
    assert_condition(failures, not bool(manager.get("opens_prod_102")), f"{label}: PROD-102 must remain closed: {snapshot(packet)}")


def assert_no_fake_appointment_or_callback(failures: list[str], packet: dict[str, Any], label: str) -> None:
    mem = memory(packet)
    text = normalize(response(packet))
    assert_condition(failures, not bool(mem.get("appointment_close_ready")), f"{label}: appointment must not be marked ready: {snapshot(packet)}")
    assert_condition(failures, mem.get("appointment_close_gap") is None, f"{label}: appointment gap must not be confirmed: {snapshot(packet)}")
    assert_condition(failures, "confirmed" not in text or selected_action(packet).get("action_id") not in {"capture_send_info_email", "request_send_info_contact"}, f"{label}: should not confirm callback/appointment: {snapshot(packet)}")


def assert_send_info_not_callback_action(failures: list[str], packet: dict[str, Any], label: str) -> None:
    assert_condition(failures, selected_action(packet).get("action_id") != "request_callback_time", f"{label}: send-info route must not use request_callback_time: {snapshot(packet)}")
    assert_condition(failures, selected_action(packet).get("template_id") != "callback_time_request", f"{label}: send-info route must not use callback_time_request template: {snapshot(packet)}")


def validate_send_info_action_contract(failures: list[str], evidence: dict[str, Any]) -> None:
    scenarios = {
        "scenario_a_send_details_before_pain": ["__agent_open__", "yeah sure", "send me details"],
        "scenario_b_send_details_then_email": ["__agent_open__", "yeah sure", "send me details", f"send it to {RAW_SYNTHETIC_EMAIL}"],
        "scenario_c_send_details_then_callback_time": ["__agent_open__", "yeah sure", "send me details", "tomorrow at 3 works"],
        "scenario_d_send_details_then_vague_yes": ["__agent_open__", "yeah sure", "send me details", "yes send it"],
        "scenario_e_send_details_then_refusal": ["__agent_open__", "yeah sure", "send me details", "never mind"],
        "scenario_f_confirmed_pain_then_send_details": ["__agent_open__", "yeah sure", "missed callbacks happen sometimes", "send me details first"],
        "scenario_g_email_plus_callback_time": ["__agent_open__", "yeah sure", "send me details", f"email {RAW_SYNTHETIC_EMAIL} and call tomorrow at 3"],
        "scenario_h_invalid_email_like_text": ["__agent_open__", "yeah sure", "send me details", "send it to alex at example"],
        "scenario_i_plain_callback_outside_send_info": ["__agent_open__", "call me tomorrow at 3"],
    }
    packets_by_scenario = {label: run_sequence(transcripts, session_id=label) for label, transcripts in scenarios.items()}
    for label, packets in packets_by_scenario.items():
        evidence[label] = [snapshot(packet) for packet in packets]
        for index, packet in enumerate(packets, start=1):
            assert_no_provider_or_llm(failures, packet, f"{label}_turn{index}")

    a3 = packets_by_scenario["scenario_a_send_details_before_pain"][2]
    assert_semantic(failures, a3, label="scenario_a_turn3", expected="send_info_request")
    assert_action(failures, a3, label="scenario_a_turn3", action_id="request_send_info_contact", template_id="send_info_contact_request", call_control_value="continue-call")
    assert_decision_next_action(failures, a3, "collect-email-or-callback-time", "scenario_a_turn3")
    assert_send_info_not_callback_action(failures, a3, "scenario_a_turn3")
    assert_condition(failures, send_info_state(a3).get("capture_status") == "needs_email_or_callback_time", f"scenario_a_turn3: expected missing contact state: {snapshot(a3)}")
    assert_spoken_contains(failures, a3, {"email", "callback time"}, "scenario_a_turn3")

    b4 = packets_by_scenario["scenario_b_send_details_then_email"][3]
    assert_semantic(failures, b4, label="scenario_b_turn4", expected="email_provided")
    assert_action(failures, b4, label="scenario_b_turn4", action_id="capture_send_info_email", template_id="send_info_email_capture", call_control_value="continue-call")
    assert_decision_next_action(failures, b4, "confirm-summary-note-or-offer-callback", "scenario_b_turn4")
    assert_send_info_not_callback_action(failures, b4, "scenario_b_turn4")
    assert_condition(failures, send_info_state(b4).get("captured_email_redacted") == REDACTED_EMAIL, f"scenario_b_turn4: expected redacted email: {snapshot(b4)}")
    assert_no_fake_appointment_or_callback(failures, b4, "scenario_b_turn4")

    c4 = packets_by_scenario["scenario_c_send_details_then_callback_time"][3]
    assert_semantic(failures, c4, label="scenario_c_turn4", expected="callback_time_provided")
    assert_action(failures, c4, label="scenario_c_turn4", action_id="capture_send_info_callback_time", template_id="send_info_callback_time_capture", call_control_value="schedule-and-end")
    assert_decision_next_action(failures, c4, "confirm-callback", "scenario_c_turn4")
    assert_condition(failures, send_info_state(c4).get("capture_status") == "callback_time_captured", f"scenario_c_turn4: expected callback capture: {snapshot(c4)}")
    assert_condition(failures, send_info_state(c4).get("lead_status") == "open_callback", f"scenario_c_turn4: expected callback lead: {snapshot(c4)}")

    d4 = packets_by_scenario["scenario_d_send_details_then_vague_yes"][3]
    assert_semantic(failures, d4, label="scenario_d_turn4", expected="send_info_affirmed_without_contact")
    assert_action(failures, d4, label="scenario_d_turn4", action_id="request_send_info_contact", template_id="send_info_contact_request", call_control_value="continue-call")
    assert_send_info_not_callback_action(failures, d4, "scenario_d_turn4")
    assert_condition(failures, not send_info_state(d4).get("captured_email_redacted"), f"scenario_d_turn4: should not capture email: {snapshot(d4)}")
    assert_condition(failures, not send_info_state(d4).get("captured_callback_time"), f"scenario_d_turn4: should not capture callback time: {snapshot(d4)}")
    assert_spoken_contains(failures, d4, {"email", "callback time"}, "scenario_d_turn4")

    e4 = packets_by_scenario["scenario_e_send_details_then_refusal"][3]
    assert_semantic(failures, e4, label="scenario_e_turn4", expected="send_info_refused_contact")
    assert_action(failures, e4, label="scenario_e_turn4", action_id="close_send_info_refused", template_id="send_info_refused_close", call_control_value="end-call")
    assert_condition(failures, send_info_state(e4).get("lead_status") == "closed_refused", f"scenario_e_turn4: expected closed refusal: {snapshot(e4)}")
    assert_spoken_contains(failures, e4, {"stop here", "not send anything"}, "scenario_e_turn4")

    f4 = packets_by_scenario["scenario_f_confirmed_pain_then_send_details"][3]
    assert_semantic(failures, f4, label="scenario_f_turn4", expected={"send_info_with_confirmed_pain", "send_info_request"})
    assert_action(failures, f4, label="scenario_f_turn4", action_id="request_send_info_contact", template_id="send_info_contact_request", call_control_value="continue-call")
    assert_condition(failures, "callbacks" in gap_set(f4, "confirmed_gaps"), f"scenario_f_turn4: confirmed callbacks should persist: {snapshot(f4)}")
    assert_no_fake_appointment_or_callback(failures, f4, "scenario_f_turn4")
    assert_spoken_contains(failures, f4, {"missed callbacks", "email", "callback time"}, "scenario_f_turn4")

    g4 = packets_by_scenario["scenario_g_email_plus_callback_time"][3]
    assert_semantic(failures, g4, label="scenario_g_turn4", expected={"contact_detail_provided", "email_and_callback_time_captured"})
    assert_action(failures, g4, label="scenario_g_turn4", action_id="capture_send_info_email_and_callback", template_id="send_info_email_and_callback_capture", call_control_value="schedule-and-end")
    assert_condition(failures, send_info_state(g4).get("capture_status") == "email_and_callback_time_captured", f"scenario_g_turn4: expected full contact capture: {snapshot(g4)}")
    assert_condition(failures, RAW_SYNTHETIC_EMAIL not in json.dumps(snapshot(g4)), "scenario_g_turn4: snapshot must redact raw synthetic email")

    h4 = packets_by_scenario["scenario_h_invalid_email_like_text"][3]
    assert_semantic(failures, h4, label="scenario_h_turn4", expected="contact_detail_unclear")
    assert_action(failures, h4, label="scenario_h_turn4", action_id="clarify_send_info_contact", template_id="send_info_contact_clarification", call_control_value="continue-call")
    assert_send_info_not_callback_action(failures, h4, "scenario_h_turn4")
    assert_condition(failures, not send_info_state(h4).get("captured_email_redacted"), f"scenario_h_turn4: invalid email must not be captured: {snapshot(h4)}")
    assert_spoken_contains(failures, h4, {"repeat the email", "callback time"}, "scenario_h_turn4")

    i2 = packets_by_scenario["scenario_i_plain_callback_outside_send_info"][1]
    assert_condition(failures, selected_action(i2).get("action_id") not in SEND_INFO_ACTION_IDS, f"scenario_i_turn2: ordinary callback should not use send-info action IDs: {snapshot(i2)}")
    assert_condition(failures, not send_info_state(i2), f"scenario_i_turn2: ordinary callback should not create send_info_state: {snapshot(i2)}")

    serialized_evidence = json.dumps(evidence)
    assert_condition(failures, RAW_SYNTHETIC_EMAIL not in serialized_evidence, "public generated evidence must redact raw synthetic email")


def render_report(payload: dict[str, Any]) -> str:
    lines = [
        "# CONTEXTUAL-BUYER-SEMANTICS-007 Send Info Action Contract",
        "",
        f"- Passed: `{str(payload['passed']).lower()}`",
        f"- Failure count: `{payload['failure_count']}`",
        "- Provider calls made: `false`",
        "- Local LLM calls made: `false`",
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
            "- Verifies send-info request, email capture, callback-time capture, vague acknowledgement, refusal, confirmed-pain send-info, combined contact capture, and unclear contact all use explicit send-info action/template IDs.",
            "- Verifies ordinary callback outside send-info does not get forced into send-info action IDs.",
            "- Keeps synthetic email redacted from generated public evidence.",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    failures: list[str] = []
    evidence: dict[str, Any] = {}
    validate_send_info_action_contract(failures, evidence)
    payload = sanitize(
        {
            "checkpoint_id": CHECKPOINT_ID,
            "passed": not failures,
            "failure_count": len(failures),
            "failures": failures,
            "provider_calls_made": False,
            "local_llm_calls_made": False,
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
