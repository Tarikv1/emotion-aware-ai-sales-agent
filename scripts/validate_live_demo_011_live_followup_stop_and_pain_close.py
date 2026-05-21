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


CHECKPOINT_ID = "LIVE-DEMO-011-live-followup-stop-and-pain-close"
GENERATED_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
RESULT_PATH = GENERATED_DIR / "result.json"
REPORT_PATH = GENERATED_DIR / "report.md"
TMP_DIR = ROOT / ".tmp" / CHECKPOINT_ID

FORBIDDEN_CUSTOMER_FRAGMENTS = {
    "check fit only",
    "check effort only",
    "if not, stop here",
    "if it is not happening",
    "there is no reason to schedule one",
    "use a later callback or written summary",
    "timing is the blocker",
    "mark that you do not want another call",
    "the practical question is whether",
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


def forbidden_fragment(response: str) -> str | None:
    lowered = normalize(response)
    for fragment in sorted(FORBIDDEN_CUSTOMER_FRAGMENTS):
        if fragment in lowered:
            return fragment
    return None


def is_simple_stop_response(response: str) -> bool:
    lowered = normalize(response)
    return "understood" in lowered and "goodbye" in lowered and "mark that" not in lowered


def is_appointment_close_ask(response: str) -> bool:
    lowered = normalize(response)
    return (
        any(fragment in lowered for fragment in {"short workflow review", "quick call", "short call"})
        and "northstar" in lowered
        and any(fragment in lowered for fragment in {"what time works", "when works", "what time would work"})
    )


def validate_callback_never_stops(failures: list[str], evidence: dict[str, Any]) -> None:
    packets = run_sequence(
        [
            ("__agent_open__", "agent-open"),
            ("no I don't", "speech-final"),
            ("never", "speech-final"),
        ],
        session_id="live-demo-011-callback-never",
    )
    never_packet = packets[-1]
    response = never_packet["summary"]["final_response"]
    evidence["callback_never"] = {
        "response": response,
        "call_control": never_packet["summary"]["call_control"],
        "continuity": never_packet["demo_session_continuity"],
    }
    assert_condition(failures, never_packet["summary"]["call_control"] == "end-call", f"`never` after callback timing should end the call: {response}")
    assert_condition(failures, is_simple_stop_response(response), f"`never` after callback timing should get a simple stop response: {response}")


def validate_explicit_do_not_call_is_plain(failures: list[str], evidence: dict[str, Any]) -> None:
    packets = run_sequence(
        [
            ("__agent_open__", "agent-open"),
            ("no I don't", "speech-final"),
            ("don't call me again", "speech-final"),
        ],
        session_id="live-demo-011-do-not-call",
    )
    stop_packet = packets[-1]
    response = stop_packet["summary"]["final_response"]
    evidence["explicit_do_not_call"] = {
        "response": response,
        "call_control": stop_packet["summary"]["call_control"],
        "continuity": stop_packet["demo_session_continuity"],
    }
    assert_condition(failures, stop_packet["summary"]["call_control"] == "end-call", f"Explicit do-not-call should end the call: {response}")
    assert_condition(failures, is_simple_stop_response(response), f"Explicit do-not-call response should be plain: {response}")


def validate_confirmed_missed_leads_closes(failures: list[str], evidence: dict[str, Any]) -> None:
    packets = run_sequence(
        [
            ("__agent_open__", "agent-open"),
            ("yeah you find your person I have a minute", "speech-final"),
            ("I guess manual tracking is a bit of an issue", "speech-final"),
            ("Leeds are getting missed for us because it's hard to organize everything", "speech-final"),
        ],
        session_id="live-demo-011-confirmed-missed-leads",
    )
    pain_packet = packets[-1]
    response = pain_packet["summary"]["final_response"]
    evidence["confirmed_missed_leads"] = {
        "response": response,
        "tts_input_text": pain_packet["summary"]["tts_input_text"],
        "continuity": pain_packet["demo_session_continuity"],
    }
    assert_condition(failures, is_appointment_close_ask(response), f"Confirmed missed leads should move directly to appointment-setting: {response}")


def validate_fit_check_confirmation_closes(failures: list[str], evidence: dict[str, Any]) -> None:
    state: dict[str, Any] = {
        "turns": [
            {
                "transcript": "manual tracking",
                "summary": {
                    "final_response": "The practical fit check is whether inbound leads, callbacks, or handoffs get missed today.",
                    "call_control": "continue-call",
                },
                "continuity": {"dialogue_focus": "fit"},
                "conversation_memory": {"active_topic": "fit", "selected_gap": None},
            }
        ]
    }
    packet = build_live_turn(
        "Leeds are getting missed so yeah",
        state,
        session_id="live-demo-011-fit-check-confirmation",
    )
    response = packet["summary"]["final_response"]
    evidence["fit_check_confirmation"] = {
        "response": response,
        "tts_input_text": packet["summary"]["tts_input_text"],
        "continuity": packet["demo_session_continuity"],
    }
    assert_condition(failures, is_appointment_close_ask(response), f"Pain confirmation after fit check should move to appointment-setting: {response}")


def validate_customer_text_is_clean(failures: list[str], evidence: dict[str, Any]) -> None:
    responses: list[str] = []
    for item in evidence.values():
        if isinstance(item, dict):
            for key in ("response", "tts_input_text"):
                value = item.get(key)
                if isinstance(value, str):
                    responses.append(value)
    for response in responses:
        fragment = forbidden_fragment(response)
        assert_condition(failures, fragment is None, f"Customer speech contains runtime-sounding fragment `{fragment}`: {response}")


def render_report(payload: dict[str, Any]) -> str:
    lines = [
        "# LIVE-DEMO-011 Live Follow-Up Stop And Pain Close Validator",
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
            "- Checks that `never` after a callback-time request stops the call.",
            "- Checks that explicit do-not-call wording stays plain.",
            "- Checks that ASR-style `Leeds` pain still maps to missed leads.",
            "- Checks that confirmed missed leads move directly to the appointment ask.",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    failures: list[str] = []
    evidence: dict[str, Any] = {}
    validate_callback_never_stops(failures, evidence)
    validate_explicit_do_not_call_is_plain(failures, evidence)
    validate_confirmed_missed_leads_closes(failures, evidence)
    validate_fit_check_confirmation_closes(failures, evidence)
    validate_customer_text_is_clean(failures, evidence)

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
