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
    DEFAULT_CASES_PATH,
    DEFAULT_CAMPAIGN_ID,
    DEFAULT_STAGE,
    build_turn_packet,
)
from scripts.validate_live_demo_002_conversation_stability import append_turn, normalize  # noqa: E402


CHECKPOINT_ID = "LIVE-DEMO-009-appointment-lead-close"
GENERATED_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
RESULT_PATH = GENERATED_DIR / "result.json"
REPORT_PATH = GENERATED_DIR / "report.md"
TMP_DIR = ROOT / ".tmp" / CHECKPOINT_ID


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


def question_count(response: str) -> int:
    return response.count("?")


def has_second_opening_question(response: str) -> bool:
    lowered = normalize(response)
    return any(
        fragment in lowered
        for fragment in {
            "is that worth a quick check",
            "which part is harder",
            "which gap costs",
            "where does it break",
            "which part is least clear",
        }
    )


def is_appointment_close_ask(response: str) -> bool:
    lowered = normalize(response)
    return (
        any(fragment in lowered for fragment in {"short workflow review", "quick call", "short call"})
        and any(fragment in lowered for fragment in {"person from northstar", "someone from northstar", "northstar"})
        and any(fragment in lowered for fragment in {"what time works", "when works", "what time would work"})
    )


def asks_review_usefulness_again(response: str) -> bool:
    lowered = normalize(response)
    return any(
        fragment in lowered
        for fragment in {
            "would a short workflow review be useful",
            "would a short check be useful",
            "would a short workflow review be worth checking",
            "are missed follow ups frequent enough to check",
            "would a short written summary help",
            "would a short workflow review be worth",
        }
    )


def contains_payment_or_contract_close(response: str) -> bool:
    lowered = normalize(response)
    return any(fragment in lowered for fragment in {"payment", "credit card", "contract", "sign today", "buy now"})


def validate_single_permission_opening(failures: list[str], evidence: dict[str, Any]) -> None:
    packets = run_sequence([("__agent_open__", "agent-open")], session_id="live-demo-009-opening")
    response = packets[0]["summary"]["final_response"]
    evidence["single_permission_opening"] = {
        "response": response,
        "question_count": question_count(response),
        "provider_calls_made": packets[0]["summary"]["tts_provider_calls_made"],
    }
    assert_condition(failures, "do you have a minute" in normalize(response), f"Opening should ask for time permission: {response}")
    assert_condition(failures, question_count(response) == 1, f"Opening should ask one question, then wait: {response}")
    assert_condition(failures, not has_second_opening_question(response), f"Opening asked a second qualification question before buyer permission: {response}")
    assert_condition(failures, "northstar workflow labs" in normalize(response), f"Opening should name Northstar: {response}")
    assert_condition(failures, "routesignal" in normalize(response), f"Opening should name RouteSignal: {response}")
    assert_condition(failures, packets[0]["summary"]["tts_provider_calls_made"] is False, "Validator must not make provider calls.")


def validate_no_early_appointment_push(failures: list[str], evidence: dict[str, Any]) -> None:
    packets = run_sequence(
        [
            ("__agent_open__", "agent-open"),
            ("yes", "speech-final"),
        ],
        session_id="live-demo-009-no-early-close",
    )
    response = packets[-1]["summary"]["final_response"]
    evidence["no_early_appointment_push"] = {
        "response": response,
        "continuity": packets[-1]["demo_session_continuity"],
    }
    assert_condition(failures, not is_appointment_close_ask(response), f"Early permission yes should not trigger appointment close: {response}")
    assert_condition(failures, "which part" in normalize(response) or "inbound demo" in normalize(response), f"Early permission yes should start qualification: {response}")


def validate_appointment_close_after_confirmed_gap(failures: list[str], evidence: dict[str, Any]) -> None:
    sequence = [
        ("__agent_open__", "agent-open"),
        ("sure I guess", "speech-final"),
        ("I guess assigning is one of the hard parts", "speech-final"),
        ("I'm not really sure about that", "speech-final"),
        (
            "our inbound follow-ups usually land in one inbox and one person tracks it before it goes to other people",
            "speech-final",
        ),
        ("growth what do you mean by that", "speech-final"),
        ("they can but they should not", "speech-final"),
        ("yeah it would help", "speech-final"),
    ]
    packets = run_sequence(sequence, session_id="live-demo-009-confirmed-gap-close")
    close_packet = packets[-1]
    response = close_packet["summary"]["final_response"]
    evidence["confirmed_gap_close"] = [
        {
            "turn": packet["session_turn_index"],
            "transcript": packet["transcript"],
            "response": packet["summary"]["final_response"],
            "continuity": packet["demo_session_continuity"],
            "memory": packet["demo_conversation_memory"],
        }
        for packet in packets
    ]
    assert_condition(failures, is_appointment_close_ask(response), f"Confirmed useful gap should move to appointment close: {response}")
    assert_condition(failures, not asks_review_usefulness_again(response), f"Confirmed useful gap should not ask another review-usefulness question: {response}")
    assert_condition(failures, not contains_payment_or_contract_close(response), f"Appointment MVP must not close payment or contract: {response}")
    assert_condition(
        failures,
        close_packet["summary"]["call_control"] == "continue-call",
        f"Appointment ask should continue until buyer gives a time/contact: {close_packet['summary']['call_control']}",
    )


def validate_repeated_yes_does_not_reopen_review_loop(failures: list[str], evidence: dict[str, Any]) -> None:
    sequence = [
        ("__agent_open__", "agent-open"),
        ("sure I guess", "speech-final"),
        ("I guess assigning is one of the hard parts", "speech-final"),
        ("they can but they should not", "speech-final"),
        ("yes it would help", "speech-final"),
        ("yes", "speech-final"),
    ]
    packets = run_sequence(sequence, session_id="live-demo-009-repeated-yes")
    responses = [packet["summary"]["final_response"] for packet in packets]
    evidence["repeated_yes_close"] = [
        {
            "turn": packet["session_turn_index"],
            "transcript": packet["transcript"],
            "response": packet["summary"]["final_response"],
            "continuity": packet["demo_session_continuity"],
        }
        for packet in packets
    ]
    final_response = responses[-1]
    assert_condition(failures, is_appointment_close_ask(final_response), f"Repeated yes after value confirmation should stay on appointment next step: {final_response}")
    assert_condition(
        failures,
        sum(1 for response in responses if asks_review_usefulness_again(response)) <= 1,
        f"Sequence reopened review-usefulness loop too often: {responses}",
    )


def validate_scheduling_controls_preserved(failures: list[str], evidence: dict[str, Any]) -> None:
    packets = run_sequence(
        [
            ("__agent_open__", "agent-open"),
            ("sure I guess", "speech-final"),
            ("call me back later", "speech-final"),
            ("tomorrow at 3 works", "speech-final"),
        ],
        session_id="live-demo-009-scheduling-controls",
    )
    schedule_request = packets[-2]
    time_confirm = packets[-1]
    evidence["scheduling_controls"] = {
        "request_response": schedule_request["summary"]["final_response"],
        "request_continuity": schedule_request["demo_session_continuity"],
        "time_response": time_confirm["summary"]["final_response"],
        "time_call_control": time_confirm["summary"]["call_control"],
        "time_continuity": time_confirm["demo_session_continuity"],
    }
    assert_condition(
        failures,
        schedule_request["demo_session_continuity"].get("reason") == "callback_request_time_needed",
        f"Explicit call-back-later request should still ask for time: {schedule_request['demo_session_continuity']}",
    )
    assert_condition(
        failures,
        time_confirm["summary"]["call_control"] == "schedule-and-end",
        f"Time after scheduling context should still schedule and end: {time_confirm['summary']['call_control']}",
    )


def validate_appointment_time_confirmation(failures: list[str], evidence: dict[str, Any]) -> None:
    sequence = [
        ("__agent_open__", "agent-open"),
        ("sure I guess", "speech-final"),
        ("I guess assigning is one of the hard parts", "speech-final"),
        ("I'm not really sure about that", "speech-final"),
        (
            "our inbound follow-ups usually land in one inbox and one person tracks it before it goes to other people",
            "speech-final",
        ),
        ("growth what do you mean by that", "speech-final"),
        ("they can but they should not", "speech-final"),
        ("yeah it would help", "speech-final"),
        ("tomorrow at 3 works", "speech-final"),
    ]
    packets = run_sequence(sequence, session_id="live-demo-009-appointment-time")
    close_packet = packets[-2]
    time_packet = packets[-1]
    evidence["appointment_time_confirmation"] = {
        "appointment_response": close_packet["summary"]["final_response"],
        "time_response": time_packet["summary"]["final_response"],
        "time_call_control": time_packet["summary"]["call_control"],
        "time_continuity": time_packet["demo_session_continuity"],
    }
    assert_condition(failures, is_appointment_close_ask(close_packet["summary"]["final_response"]), "Preceding turn should request appointment time.")
    assert_condition(
        failures,
        time_packet["demo_session_continuity"].get("reason") == "appointment_time_confirmed",
        f"Time after appointment ask should confirm appointment context: {time_packet['demo_session_continuity']}",
    )
    assert_condition(
        failures,
        time_packet["summary"]["call_control"] == "schedule-and-end",
        f"Appointment time confirmation should schedule and end: {time_packet['summary']['call_control']}",
    )


def render_report(payload: dict[str, Any]) -> str:
    lines = [
        "# LIVE-DEMO-009 Appointment Lead Close Validator",
        "",
        f"- Passed: `{str(payload['passed']).lower()}`",
        f"- Failure count: `{payload['failure_count']}`",
        "- Provider calls made: `false`",
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
            "- Checks that the opening asks one permission question and waits.",
            "- Checks that confirmed workflow pain moves to an appointment-setting next step.",
            "- Keeps payment, contract close, provider calls, and production promotion out of scope.",
            "- Preserves explicit callback scheduling controls.",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    failures: list[str] = []
    evidence: dict[str, Any] = {}
    validate_single_permission_opening(failures, evidence)
    validate_no_early_appointment_push(failures, evidence)
    validate_appointment_close_after_confirmed_gap(failures, evidence)
    validate_repeated_yes_does_not_reopen_review_loop(failures, evidence)
    validate_scheduling_controls_preserved(failures, evidence)
    validate_appointment_time_confirmation(failures, evidence)

    payload = {
        "checkpoint_id": CHECKPOINT_ID,
        "passed": not failures,
        "failure_count": len(failures),
        "failures": failures,
        "provider_calls_made": False,
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
