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


CHECKPOINT_ID = "DIALOGUE-MANAGER-003-plain-sales-clarity-and-vague-appointment-time"
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
    "owner lookup",
    "value point",
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


def manager_action(packet: dict[str, Any]) -> str:
    return str(((packet.get("dialogue_manager") or {}).get("selected_action") or {}).get("action_id") or "")


def manager_source(packet: dict[str, Any]) -> str:
    return str(((packet.get("dialogue_manager") or {}).get("selected_action") or {}).get("source") or "")


def continuity_reason(packet: dict[str, Any]) -> str:
    return str((packet.get("demo_session_continuity") or {}).get("reason") or "")


def memory(packet: dict[str, Any]) -> dict[str, Any]:
    return dict(packet.get("demo_conversation_memory") or {})


def snapshot(packet: dict[str, Any]) -> dict[str, Any]:
    return {
        "turn": packet["session_turn_index"],
        "transcript": packet["transcript"],
        "response": response(packet),
        "call_control": packet["summary"]["call_control"],
        "continuity": packet.get("demo_session_continuity") or {},
        "memory": packet.get("demo_conversation_memory") or {},
        "manager": packet.get("dialogue_manager") or {},
        "dialogue_pragmatics": packet.get("dialogue_pragmatics") or {},
    }


def assert_plain_sales_explanation(failures: list[str], text: str, label: str) -> None:
    lowered = normalize(text)
    assert_condition(failures, "routesignal" in lowered, f"{label}: should name RouteSignal plainly: {text}")
    assert_condition(failures, "demo lead" in lowered or "demo request" in lowered, f"{label}: should talk about demo leads, not internal labels: {text}")
    assert_condition(
        failures,
        any(fragment in lowered for fragment in {"assigned", "who follows up", "followed up", "reminder", "reminded"}),
        f"{label}: should explain the actual thing being sold: {text}",
    )
    assert_condition(failures, "handoff status" not in lowered and "owner lookup" not in lowered, f"{label}: should avoid internal workflow jargon: {text}")


def validate_call_purpose_is_plain_sales(failures: list[str], evidence: dict[str, Any]) -> None:
    packets = run_sequence(
        [
            ("__agent_open__", "agent-open"),
            ("yes", "speech-final"),
            ("what is this call about", "speech-final"),
        ],
        session_id="dialogue-manager-003-purpose",
    )
    packet = packets[-1]
    text = response(packet)
    evidence["plain_call_purpose"] = snapshot(packet)
    assert_condition(failures, manager_action(packet) == "recover_call_purpose", f"Purpose question should route through purpose recovery: {snapshot(packet)}")
    assert_plain_sales_explanation(failures, text, "purpose")
    assert_condition(failures, "which of those" not in normalize(text), f"Purpose response should not immediately ask a label menu: {text}")


def validate_live_failure_sequence_progresses_to_time_ask(failures: list[str], evidence: dict[str, Any]) -> None:
    sequence = [
        ("__agent_open__", "agent-open"),
        ("yes", "speech-final"),
        ("what do you mean by handoff", "speech-final"),
        ("ok I can see that", "speech-final"),
        ("what is this call about", "speech-final"),
        ("I'm not really sure but we do get some leads missing time to time", "speech-final"),
        ("I don't know you tell me", "speech-final"),
        ("I told you we what we have the problem we have I already told you", "speech-final"),
        ("I said manual tracking", "speech-final"),
        ("I guess in the let me see let me see um it's probably the reminders", "speech-final"),
        ("yeah sure", "speech-final"),
    ]
    packets = run_sequence(sequence, session_id="dialogue-manager-003-live-failure-progress")
    pain_packet = packets[5]
    already_packet = packets[7]
    agreement_packet = packets[-1]
    evidence["live_failure_progression"] = [snapshot(packet) for packet in packets]

    pain_text = response(pain_packet)
    assert_condition(
        failures,
        memory(pain_packet).get("selected_gap") in {"handoffs", "callbacks", "reminders"},
        f"`leads missing time to time` should select a real pain gap: {snapshot(pain_packet)}",
    )
    assert_condition(
        failures,
        "would a short workflow review be worth checking" not in normalize(pain_text),
        f"Pain should be acknowledged before asking review worthiness: {pain_text}",
    )
    assert_plain_sales_explanation(failures, pain_text, "pain acknowledgement")

    already_text = normalize(response(already_packet))
    assert_condition(
        failures,
        "already" in already_text or "that is the problem" in already_text or "the missed lead problem" in already_text,
        f"Buyer saying they already stated the problem should be acknowledged: {response(already_packet)}",
    )

    agreement_text = response(agreement_packet)
    assert_condition(failures, manager_action(agreement_packet) == "request_appointment_time", f"`yeah sure` should request appointment time: {snapshot(agreement_packet)}")
    assert_condition(failures, is_appointment_close_ask(agreement_text), f"`yeah sure` after review usefulness should ask for appointment time: {agreement_text}")
    assert_condition(failures, "selling point" not in normalize(agreement_text), f"`yeah sure` should not drift back into explanation: {agreement_text}")


def validate_vague_next_week_keeps_appointment_open(failures: list[str], evidence: dict[str, Any]) -> None:
    sequence = [
        ("__agent_open__", "agent-open"),
        ("yes", "speech-final"),
        ("what is this call about", "speech-final"),
        ("we get some leads missing time to time", "speech-final"),
        ("yeah sure", "speech-final"),
        ("sometime in the next week", "speech-final"),
    ]
    packets = run_sequence(sequence, session_id="dialogue-manager-003-vague-next-week")
    appointment_packet = packets[-2]
    vague_time_packet = packets[-1]
    text = response(vague_time_packet)
    lowered = normalize(text)
    evidence["vague_next_week"] = {
        "appointment_turn": snapshot(appointment_packet),
        "vague_time_turn": snapshot(vague_time_packet),
    }
    assert_condition(failures, is_appointment_close_ask(response(appointment_packet)), f"Preceding turn should ask for appointment time: {response(appointment_packet)}")
    assert_condition(
        failures,
        vague_time_packet["summary"]["call_control"] == "continue-call",
        f"Vague next-week availability should keep the appointment conversation open: {snapshot(vague_time_packet)}",
    )
    assert_condition(
        failures,
        continuity_reason(vague_time_packet) == "appointment_time_clarification_needed",
        f"Vague next-week availability should use an appointment clarification reason: {snapshot(vague_time_packet)}",
    )
    assert_condition(
        failures,
        "which day" in lowered or "what day" in lowered or "what time" in lowered,
        f"Vague next-week availability should ask for a concrete day/time: {text}",
    )
    assert_condition(failures, "do not need to decide" not in lowered, f"Vague appointment time should not close as no-decision timing: {text}")
    assert_condition(failures, "goodbye" not in lowered, f"Vague appointment time should not end the call: {text}")


def validate_customer_text_is_clean(failures: list[str], evidence: dict[str, Any]) -> None:
    def rows(value: Any) -> list[dict[str, Any]]:
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
        if isinstance(value, dict) and "response" in value:
            return [value]
        if isinstance(value, dict):
            return [item for item in value.values() if isinstance(item, dict) and "response" in item]
        return []

    for name, item in evidence.items():
        for row in rows(item):
            lowered = normalize(str(row.get("response") or ""))
            for fragment in sorted(FORBIDDEN_CUSTOMER_FRAGMENTS):
                if fragment in lowered:
                    failures.append(f"{name} customer speech contains internal fragment `{fragment}`: {row.get('response')}")


def render_report(payload: dict[str, Any]) -> str:
    lines = [
        "# DIALOGUE-MANAGER-003 Plain Sales Clarity And Vague Appointment Time Validator",
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
            "- Replays the observed live failure shape from the browser transcript.",
            "- Requires plain sales-call language before further diagnosis.",
            "- Requires vague appointment availability to stay in appointment scheduling, not generic timing closure.",
            "- Keeps provider calls, local LLM calls, payment, contract closure, production promotion, and PROD-102 out of scope.",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    failures: list[str] = []
    evidence: dict[str, Any] = {}
    validate_call_purpose_is_plain_sales(failures, evidence)
    validate_live_failure_sequence_progresses_to_time_ask(failures, evidence)
    validate_vague_next_week_keeps_appointment_open(failures, evidence)
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
