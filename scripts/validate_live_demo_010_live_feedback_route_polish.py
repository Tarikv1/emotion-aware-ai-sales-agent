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


CHECKPOINT_ID = "LIVE-DEMO-010-live-feedback-route-polish"
GENERATED_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
RESULT_PATH = GENERATED_DIR / "result.json"
REPORT_PATH = GENERATED_DIR / "report.md"
TMP_DIR = ROOT / ".tmp" / CHECKPOINT_ID

FORBIDDEN_CUSTOMER_FRAGMENTS = {
    "check fit only",
    "check effort only",
    "if not, stop here",
    "the effort test is simple",
    "verified workflow review may be useful",
    "the yes-or-no is whether",
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


def is_callback_time_request(response: str) -> bool:
    lowered = normalize(response)
    return "callback" in lowered and any(fragment in lowered for fragment in {"what time", "when should", "when can"})


def is_appointment_close_ask(response: str) -> bool:
    lowered = normalize(response)
    return (
        any(fragment in lowered for fragment in {"short workflow review", "quick call", "short call"})
        and any(fragment in lowered for fragment in {"someone from northstar", "person from northstar", "northstar"})
        and any(fragment in lowered for fragment in {"what time works", "when works", "what time would work"})
    )


def validate_permission_refusal_is_heard(failures: list[str], evidence: dict[str, Any]) -> None:
    packets = run_sequence(
        [
            ("__agent_open__", "agent-open"),
            ("no I don't", "speech-final"),
        ],
        session_id="live-demo-010-permission-refusal",
    )
    refusal_packet = packets[-1]
    response = refusal_packet["summary"]["final_response"]
    continuity = refusal_packet["demo_session_continuity"]
    evidence["permission_refusal"] = {
        "response": response,
        "continuity": continuity,
        "stability_guard": refusal_packet["demo_conversation_stability_guard"],
    }
    assert_condition(
        failures,
        continuity.get("reason") == "callback_request_time_needed",
        f"Permission refusal should route to callback timing, not qualification: {continuity}",
    )
    assert_condition(failures, is_callback_time_request(response), f"Permission refusal should ask for a callback time: {response}")
    assert_condition(failures, "which part" not in normalize(response), f"Permission refusal should not continue qualification: {response}")


def validate_observed_pain_moves_forward(failures: list[str], evidence: dict[str, Any]) -> None:
    sequence = [
        ("__agent_open__", "agent-open"),
        ("yes", "speech-final"),
        ("I'm sorry what is this about", "speech-final"),
        ("I said what is this about like what are you trying to sell me here", "speech-final"),
        ("what do you mean by owners", "speech-final"),
        ("yeah you can contact me about that if we decide to continue of course", "speech-final"),
        ("I didn't say I am a manager but yeah I guess it would be worth", "speech-final"),
        ("I mean it's completely clear So Gone", "speech-final"),
        ("manual tracking", "speech-final"),
        (
            "so sometimes the leads get lost in the mail because there is a lot of mails and it is kind of overwhelming "
            "to assign each lead to a different person and yes sometimes we just miss it and it falls through the cracks",
            "speech-final",
        ),
        ("we could say that I guess they are getting missed", "speech-final"),
    ]
    packets = run_sequence(sequence, session_id="live-demo-010-observed-pain")
    evidence["observed_pain_sequence"] = [
        {
            "turn": packet["session_turn_index"],
            "transcript": packet["transcript"],
            "response": packet["summary"]["final_response"],
            "tts_input_text": packet["summary"]["tts_input_text"],
            "continuity": packet["demo_session_continuity"],
        }
        for packet in packets
    ]
    responses_to_check = [packet["summary"]["final_response"] for packet in packets] + [
        packet["summary"]["tts_input_text"] for packet in packets
    ]
    for response in responses_to_check:
        fragment = forbidden_fragment(response)
        assert_condition(failures, fragment is None, f"Internal runtime phrase leaked into customer speech ({fragment}): {response}")
        assert_condition(
            failures,
            "live in a spreadsheet" not in normalize(response),
            f"Ambiguous TTS pronunciation phrase should be avoided: {response}",
        )
    pain_response = packets[-2]["summary"]["final_response"]
    final_response = packets[-1]["summary"]["final_response"]
    assert_condition(
        failures,
        is_appointment_close_ask(pain_response) or is_appointment_close_ask(final_response),
        f"Confirmed missed-lead pain should move toward appointment-setting, not another fit check: {pain_response} / {final_response}",
    )
    assert_condition(
        failures,
        is_appointment_close_ask(final_response),
        f"Non-time confirmation after appointment context should keep asking for a usable time: {final_response}",
    )


def render_report(payload: dict[str, Any]) -> str:
    lines = [
        "# LIVE-DEMO-010 Live Feedback Route Polish Validator",
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
            "- Checks that `no I don't` after the opener is heard as a time refusal.",
            "- Checks that observed missed-lead pain moves toward the appointment-setting close.",
            "- Blocks internal runtime phrases from customer speech.",
            "- Avoids the ambiguous spreadsheet-verb TTS phrase.",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    failures: list[str] = []
    evidence: dict[str, Any] = {}
    validate_permission_refusal_is_heard(failures, evidence)
    validate_observed_pain_moves_forward(failures, evidence)

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
