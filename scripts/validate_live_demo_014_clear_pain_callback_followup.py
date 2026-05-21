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


CHECKPOINT_ID = "LIVE-DEMO-014-clear-pain-callback-followup"
GENERATED_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
RESULT_PATH = GENERATED_DIR / "result.json"
REPORT_PATH = GENERATED_DIR / "report.md"
TMP_DIR = ROOT / ".tmp" / CHECKPOINT_ID

FORBIDDEN_CUSTOMER_FRAGMENTS = {
    "growth is worth reviewing",
    "if callback reminders are clean",
    "no reason to push a review",
    "we can leave it here",
    "timing only matters",
    "revisit when follow-up gaps are measurable",
    "check fit only",
    "check scope only",
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


def response(packet: dict[str, Any]) -> str:
    return str(packet["summary"]["final_response"] or "")


def snapshot(packet: dict[str, Any]) -> dict[str, Any]:
    return {
        "turn": packet["session_turn_index"],
        "transcript": packet["transcript"],
        "response": response(packet),
        "call_control": packet["summary"]["call_control"],
        "continuity": packet.get("demo_session_continuity") or {},
        "manager": packet.get("dialogue_manager") or {},
        "pragmatics": packet.get("dialogue_pragmatics") or {},
    }


def validate_all_clear_is_acknowledged(failures: list[str], evidence: dict[str, Any]) -> None:
    packets = run_sequence(
        [
            ("__agent_open__", "agent-open"),
            ("yeah sure", "speech-final"),
            ("it's all clear", "speech-final"),
        ],
        session_id="live-demo-014-all-clear",
    )
    packet = packets[-1]
    text = response(packet)
    lowered = normalize(text)
    evidence["all_clear"] = snapshot(packet)
    assert_condition(
        failures,
        any(fragment in lowered for fragment in {"got it", "understood", "that is clear", "if it is all clear"}),
        f"`it's all clear` should be acknowledged before the agent moves on: {text}",
    )
    assert_condition(
        failures,
        "which part is more familiar" not in lowered and "callback reminders for demo follow-up sit in a spreadsheet" not in lowered,
        f"`it's all clear` should not rotate to another scripted diagnostic: {text}",
    )


def validate_missed_callbacks_moves_toward_appointment(failures: list[str], evidence: dict[str, Any]) -> None:
    packets = run_sequence(
        [
            ("__agent_open__", "agent-open"),
            ("yeah sure", "speech-final"),
            ("it's all clear", "speech-final"),
            ("I would say mostly missed callbacks but we do have occasional manual tracking issues too", "speech-final"),
        ],
        session_id="live-demo-014-missed-callbacks",
    )
    packet = packets[-1]
    text = response(packet)
    lowered = normalize(text)
    evidence["missed_callbacks"] = snapshot(packet)
    assert_condition(
        failures,
        "short workflow review" in lowered and "northstar" in lowered and "missed callback" in lowered and "?" in text,
        f"Confirmed missed callbacks should move toward the Northstar workflow review: {text}",
    )
    assert_condition(failures, "growth" not in lowered, f"Appointment close should not mention unexplained plan names: {text}")
    assert_condition(failures, "if callback reminders are clean" not in lowered, f"Pain acknowledgement should not contradict the stated pain: {text}")


def validate_growth_question_gets_plain_explanation(failures: list[str], evidence: dict[str, Any]) -> None:
    packets = run_sequence(
        [
            ("__agent_open__", "agent-open"),
            ("yeah sure", "speech-final"),
            ("what do you mean growth", "speech-final"),
        ],
        session_id="live-demo-014-growth-term",
    )
    packet = packets[-1]
    text = response(packet)
    lowered = normalize(text)
    evidence["growth_term"] = snapshot(packet)
    assert_condition(failures, "sorry" in lowered or "i should have explained" in lowered, f"Growth explanation should acknowledge the unclear term: {text}")
    assert_condition(failures, "routesignal" in lowered, f"Growth explanation should name the product plainly: {text}")
    assert_condition(
        failures,
        any(fragment in lowered for fragment in {"reminder", "handoff", "follow-up", "follow up"}),
        f"Growth explanation should explain the practical product scope: {text}",
    )


def validate_think_about_it_keeps_followup_open(failures: list[str], evidence: dict[str, Any]) -> None:
    packets = run_sequence(
        [
            ("__agent_open__", "agent-open"),
            ("yeah sure", "speech-final"),
            ("I would say mostly missed callbacks but we do have occasional manual tracking issues too", "speech-final"),
            ("I didn't really accept a quick call yet I have to think about it", "speech-final"),
        ],
        session_id="live-demo-014-think-about-it",
    )
    packet = packets[-1]
    text = response(packet)
    lowered = normalize(text)
    evidence["think_about_it"] = snapshot(packet)
    assert_condition(failures, packet["summary"]["call_control"] == "continue-call", f"`think about it` should keep follow-up open: {snapshot(packet)}")
    assert_condition(failures, "leave it here" not in lowered, f"`think about it` should not be treated as a stop request: {text}")
    assert_condition(
        failures,
        ("call back" in lowered or "callback" in lowered) and "what time" in lowered,
        f"`think about it` should offer a later callback and ask for a time: {text}",
    )


def validate_callback_later_yes_requests_time(failures: list[str], evidence: dict[str, Any]) -> None:
    packets = run_sequence(
        [
            ("__agent_open__", "agent-open"),
            ("yeah sure", "speech-final"),
            ("I would say mostly missed callbacks but we do have occasional manual tracking issues too", "speech-final"),
            ("I didn't really accept a quick call yet I have to think about it", "speech-final"),
            ("yeah let's do that", "speech-final"),
        ],
        session_id="live-demo-014-callback-later-yes",
    )
    packet = packets[-1]
    text = response(packet)
    lowered = normalize(text)
    evidence["callback_later_yes"] = snapshot(packet)
    assert_condition(failures, packet["summary"]["call_control"] == "continue-call", f"`yeah let's do that` after callback offer should not end the call: {snapshot(packet)}")
    assert_condition(
        failures,
        ("call back" in lowered or "callback" in lowered) and "what time" in lowered,
        f"`yeah let's do that` after callback offer should ask for a usable callback time: {text}",
    )
    assert_condition(failures, "goodbye" not in lowered, f"`yeah let's do that` without a time should not close the call: {text}")


def validate_customer_text_is_clean(failures: list[str], evidence: dict[str, Any]) -> None:
    for name, item in evidence.items():
        lowered = normalize(str(item.get("response") or ""))
        for fragment in sorted(FORBIDDEN_CUSTOMER_FRAGMENTS):
            if fragment in lowered:
                failures.append(f"{name} customer speech contains forbidden fragment `{fragment}`: {item.get('response')}")


def render_report(payload: dict[str, Any]) -> str:
    lines = [
        "# LIVE-DEMO-014 Clear Pain Callback Follow-Up Validator",
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
            "- Replays the latest live-demo failure shape from the browser transcript.",
            "- Requires buyer statements to be acknowledged before routing forward.",
            "- Requires stated missed callbacks to move toward an appointment without internal plan names.",
            "- Requires `think about it` and callback-later agreement to keep scheduling open until a usable time is given.",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    failures: list[str] = []
    evidence: dict[str, Any] = {}
    validate_all_clear_is_acknowledged(failures, evidence)
    validate_missed_callbacks_moves_toward_appointment(failures, evidence)
    validate_growth_question_gets_plain_explanation(failures, evidence)
    validate_think_about_it_keeps_followup_open(failures, evidence)
    validate_callback_later_yes_requests_time(failures, evidence)
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
