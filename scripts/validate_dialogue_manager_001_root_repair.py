#!/usr/bin/env python3
from __future__ import annotations

import json
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
from scripts.validate_live_demo_002_conversation_stability import append_turn, normalize  # noqa: E402
from scripts.validate_live_demo_009_appointment_lead_close import is_appointment_close_ask  # noqa: E402


CHECKPOINT_ID = "DIALOGUE-MANAGER-001-root-repair"
GENERATED_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
RESULT_PATH = GENERATED_DIR / "result.json"
REPORT_PATH = GENERATED_DIR / "report.md"
TMP_DIR = ROOT / ".tmp" / CHECKPOINT_ID

FORBIDDEN_CUSTOMER_FRAGMENTS = {
    "fictional profile",
    "check fit only",
    "check scope only",
    "if not stop",
    "runtime",
    "guardrail",
}


def assert_condition(failures: list[str], condition: bool, message: str) -> None:
    if not condition:
        failures.append(message)


def build_live_turn(transcript: str, state: dict[str, Any], *, session_id: str, input_type: str = "speech-final") -> dict[str, Any]:
    return build_turn_packet(
        transcript=transcript,
        campaign_id=DEFAULT_CAMPAIGN_ID,
        stage=DEFAULT_STAGE,
        input_type=input_type,
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


def run_sequence(sequence: list[tuple[str, str]], *, session_id: str) -> list[dict[str, Any]]:
    state: dict[str, Any] = {"turns": []}
    packets: list[dict[str, Any]] = []
    for transcript, input_type in sequence:
        packet = build_live_turn(transcript, state, session_id=session_id, input_type=input_type)
        packets.append(packet)
        append_turn(state, packet)
    return packets


def customer_text(packet: dict[str, Any]) -> str:
    return str(packet["summary"]["final_response"] or "")


def manager_trace(packet: dict[str, Any]) -> dict[str, Any]:
    return dict(packet.get("dialogue_manager") or {})


def manager_action(packet: dict[str, Any]) -> dict[str, Any]:
    return dict(manager_trace(packet).get("selected_action") or {})


def assert_manager_contract(failures: list[str], packet: dict[str, Any], label: str) -> None:
    trace = manager_trace(packet)
    action = manager_action(packet)
    assert_condition(failures, trace.get("manager_id") == "DIALOGUE-MANAGER-001", f"{label}: missing manager id trace: {trace}")
    assert_condition(failures, trace.get("schema_version") == 1, f"{label}: missing manager schema version: {trace}")
    assert_condition(failures, bool(action.get("action_id")), f"{label}: missing selected action id: {trace}")
    assert_condition(failures, bool(action.get("template_id")), f"{label}: missing selected template id: {trace}")
    assert_condition(failures, trace.get("authoritative_final_action") is True, f"{label}: final response is not manager-owned: {trace}")
    assert_condition(
        failures,
        trace.get("final_response") == packet["summary"]["final_response"],
        f"{label}: manager final response mismatch: {trace.get('final_response')} != {packet['summary']['final_response']}",
    )
    assert_condition(
        failures,
        trace.get("call_control") == packet["summary"]["call_control"],
        f"{label}: manager call control mismatch: {trace.get('call_control')} != {packet['summary']['call_control']}",
    )
    assert_condition(
        failures,
        int(trace.get("candidate_response_rewrite_count") or 0) <= 1,
        f"{label}: too many independent final speech rewrites: {trace}",
    )


def validate_soft_stop_is_terminal(failures: list[str], evidence: dict[str, Any]) -> None:
    packets = run_sequence(
        [
            ("__agent_open__", "agent-open"),
            ("no I don't", "speech-final"),
            ("maybe just don't", "speech-final"),
            ("that was cool", "speech-final"),
        ],
        session_id="dialogue-manager-001-soft-stop",
    )
    stop_packet = packets[-2]
    stale_extra_packet = packets[-1]
    evidence["soft_stop_terminal"] = [
        {
            "turn": packet["session_turn_index"],
            "transcript": packet["transcript"],
            "response": customer_text(packet),
            "call_control": packet["summary"]["call_control"],
            "manager": manager_trace(packet),
            "continuity": packet["demo_session_continuity"],
        }
        for packet in packets
    ]
    assert_manager_contract(failures, stop_packet, "soft stop")
    assert_condition(
        failures,
        stop_packet["summary"]["call_control"] == "end-call",
        f"Soft callback refusal should end the call: {stop_packet['summary']['call_control']} / {customer_text(stop_packet)}",
    )
    assert_condition(
        failures,
        manager_action(stop_packet).get("action_id") == "end_call_stop_request",
        f"Soft callback refusal should be a terminal manager action: {manager_trace(stop_packet)}",
    )
    assert_manager_contract(failures, stale_extra_packet, "post-terminal extra input")
    assert_condition(
        failures,
        stale_extra_packet["summary"]["call_control"] == "end-call",
        f"Input after terminal stop should not restart sales logic: {stale_extra_packet['summary']['call_control']} / {customer_text(stale_extra_packet)}",
    )


def validate_purpose_recovery_does_not_stale_timing_loop(failures: list[str], evidence: dict[str, Any]) -> None:
    packets = run_sequence(
        [
            ("__agent_open__", "agent-open"),
            ("sure I guess", "speech-final"),
            ("what is this call about what are you trying to say", "speech-final"),
        ],
        session_id="dialogue-manager-001-purpose-recovery",
    )
    packet = packets[-1]
    response = customer_text(packet)
    lowered = normalize(response)
    evidence["purpose_recovery"] = {
        "response": response,
        "call_control": packet["summary"]["call_control"],
        "manager": manager_trace(packet),
        "continuity": packet["demo_session_continuity"],
    }
    assert_manager_contract(failures, packet, "purpose recovery")
    assert_condition(failures, "inbound demo follow" in lowered, f"Purpose recovery should answer what the call is about: {response}")
    assert_condition(failures, "no decision" not in lowered and "timing" not in lowered, f"Purpose recovery should not use stale timing advice: {response}")


def validate_crm_replacement_is_manager_owned(failures: list[str], evidence: dict[str, Any]) -> None:
    packets = run_sequence(
        [
            ("__agent_open__", "agent-open"),
            ("yeah I guess sure", "speech-final"),
            ("our system is pretty alright in general but is this going to replace our current CRM", "speech-final"),
        ],
        session_id="dialogue-manager-001-crm-replacement",
    )
    packet = packets[-1]
    response = customer_text(packet)
    lowered = normalize(response)
    evidence["crm_replacement"] = {
        "response": response,
        "call_control": packet["summary"]["call_control"],
        "manager": manager_trace(packet),
        "continuity": packet["demo_session_continuity"],
    }
    assert_manager_contract(failures, packet, "CRM replacement")
    assert_condition(
        failures,
        manager_action(packet).get("action_id") == "answer_crm_boundary_continue",
        f"CRM replacement should route through manager CRM boundary action: {manager_trace(packet)}",
    )
    assert_condition(failures, "routesignal" in lowered and "replace" in lowered, f"CRM replacement answer should be direct and public: {response}")
    assert_condition(failures, packet["summary"]["call_control"] == "continue-call", f"CRM answer should continue qualification: {packet['summary']['call_control']}")


def validate_pain_to_appointment_is_manager_owned(failures: list[str], evidence: dict[str, Any]) -> None:
    packets = run_sequence(
        [
            ("__agent_open__", "agent-open"),
            ("yes", "speech-final"),
            ("yeah leads are getting missed", "speech-final"),
        ],
        session_id="dialogue-manager-001-pain-to-appointment",
    )
    packet = packets[-1]
    response = customer_text(packet)
    evidence["pain_to_appointment"] = {
        "response": response,
        "call_control": packet["summary"]["call_control"],
        "manager": manager_trace(packet),
        "continuity": packet["demo_session_continuity"],
    }
    assert_manager_contract(failures, packet, "pain to appointment")
    assert_condition(
        failures,
        manager_action(packet).get("action_id") == "request_appointment_time",
        f"Confirmed missed-lead pain should route to the appointment manager action: {manager_trace(packet)}",
    )
    assert_condition(failures, is_appointment_close_ask(response), f"Confirmed missed-lead pain should ask for a workflow-review time: {response}")
    assert_condition(failures, packet["summary"]["call_control"] == "continue-call", f"Appointment ask should continue until time is given: {packet['summary']['call_control']}")


def validate_previous_question_clarification_is_manager_owned(failures: list[str], evidence: dict[str, Any]) -> None:
    packets = run_sequence(
        [
            ("__agent_open__", "agent-open"),
            ("I do yeah", "speech-final"),
            ("who is harder", "speech-final"),
        ],
        session_id="dialogue-manager-001-previous-question",
    )
    packet = packets[-1]
    response = customer_text(packet)
    lowered = normalize(response)
    evidence["previous_question_clarification"] = {
        "response": response,
        "call_control": packet["summary"]["call_control"],
        "manager": manager_trace(packet),
        "continuity": packet["demo_session_continuity"],
    }
    assert_manager_contract(failures, packet, "previous-question clarification")
    assert_condition(
        failures,
        manager_action(packet).get("action_id") == "clarify_previous_question",
        f"`who is harder` should be a manager-owned previous-question clarification: {manager_trace(packet)}",
    )
    assert_condition(failures, "i meant" in lowered, f"`who is harder` should explain the prior question: {response}")


def validate_customer_text_is_clean(failures: list[str], evidence: dict[str, Any]) -> None:
    for name, item in evidence.items():
        rows = item if isinstance(item, list) else [item]
        for row in rows:
            response = normalize(str(row.get("response") or ""))
            for fragment in sorted(FORBIDDEN_CUSTOMER_FRAGMENTS):
                if fragment in response:
                    failures.append(f"{name} customer speech contains internal fragment `{fragment}`: {row.get('response')}")


def render_report(payload: dict[str, Any]) -> str:
    lines = [
        "# DIALOGUE-MANAGER-001 Root Repair Validator",
        "",
        f"- Passed: `{str(payload['passed']).lower()}`",
        f"- Failure count: `{payload['failure_count']}`",
        "- Provider calls made: `false`",
        "- Local LLM calls made: `false`",
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
            "## Notes",
            "",
            "- Requires every tested final response to carry a manager action, template id, state trace, and call-control trace.",
            "- Checks observed live failures as dialogue-manager routes rather than one-off policy exceptions.",
            "- Keeps provider calls, local LLM calls, payment, contract closure, production promotion, and PROD-102 out of scope.",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    failures: list[str] = []
    evidence: dict[str, Any] = {}
    validate_soft_stop_is_terminal(failures, evidence)
    validate_purpose_recovery_does_not_stale_timing_loop(failures, evidence)
    validate_crm_replacement_is_manager_owned(failures, evidence)
    validate_pain_to_appointment_is_manager_owned(failures, evidence)
    validate_previous_question_clarification_is_manager_owned(failures, evidence)
    validate_customer_text_is_clean(failures, evidence)

    payload = {
        "checkpoint_id": CHECKPOINT_ID,
        "passed": not failures,
        "failure_count": len(failures),
        "failures": failures,
        "provider_calls_made": False,
        "local_llm_calls_made": False,
        "opens_prod_102": False,
        "evidence": evidence,
    }
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    REPORT_PATH.write_text(render_report(payload), encoding="utf-8")
    if failures:
        raise AssertionError(f"{CHECKPOINT_ID} failed with {len(failures)} issue(s). See {RESULT_PATH}.")
    print(f"{CHECKPOINT_ID} validation passed.")


if __name__ == "__main__":
    main()
