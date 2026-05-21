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


CHECKPOINT_ID = "LIVE-DEMO-012-soft-stop-and-context-recovery"
GENERATED_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
RESULT_PATH = GENERATED_DIR / "result.json"
REPORT_PATH = GENERATED_DIR / "report.md"
TMP_DIR = ROOT / ".tmp" / CHECKPOINT_ID

FORBIDDEN_CONTEXT_FRAGMENTS = {
    "no problem we do not need to decide anything now",
    "timing is already the blocker",
    "safe next step is either a later callback",
    "a useful timing test",
    "if not wait",
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


def validate_soft_stop_ends_call(failures: list[str], evidence: dict[str, Any]) -> None:
    packets = run_sequence(
        [
            ("__agent_open__", "agent-open"),
            ("no I don't", "speech-final"),
            ("maybe just don't", "speech-final"),
        ],
        session_id="live-demo-012-soft-stop",
    )
    packet = packets[-1]
    response = customer_text(packet)
    evidence["soft_stop"] = {
        "response": response,
        "call_control": packet["summary"]["call_control"],
        "continuity": packet["demo_session_continuity"],
        "stability_guard": packet["demo_conversation_stability_guard"],
    }
    assert_condition(failures, packet["summary"]["call_control"] == "end-call", f"Soft callback stop should end the call: {response}")
    assert_condition(failures, "goodbye" in normalize(response), f"Soft callback stop should use terminal stop wording: {response}")


def validate_call_purpose_overrides_timing(failures: list[str], evidence: dict[str, Any]) -> None:
    packets = run_sequence(
        [
            ("__agent_open__", "agent-open"),
            ("no I don't", "speech-final"),
            ("so what is this called about what are you trying to say", "speech-final"),
        ],
        session_id="live-demo-012-purpose-after-timing",
    )
    packet = packets[-1]
    response = customer_text(packet)
    lowered = normalize(response)
    evidence["purpose_after_timing"] = {
        "response": response,
        "call_control": packet["summary"]["call_control"],
        "continuity": packet["demo_session_continuity"],
        "memory": packet["demo_conversation_memory"],
    }
    assert_condition(
        failures,
        "inbound demo follow up" in lowered or "inbound demo" in lowered,
        f"Purpose question after timing context should answer call purpose: {response}",
    )
    assert_condition(
        failures,
        packet["demo_conversation_memory"].get("active_topic") == "qualification",
        f"Purpose answer should move focus back to qualification, not stay timing: {packet['demo_conversation_memory']}",
    )


def validate_owner_answer_after_purpose_stays_on_sales_track(failures: list[str], evidence: dict[str, Any]) -> None:
    packets = run_sequence(
        [
            ("__agent_open__", "agent-open"),
            ("no I don't", "speech-final"),
            ("what is this call about", "speech-final"),
            ("I guess the owners", "speech-final"),
        ],
        session_id="live-demo-012-owner-after-purpose",
    )
    packet = packets[-1]
    response = customer_text(packet)
    lowered = normalize(response)
    evidence["owner_after_purpose"] = {
        "response": response,
        "call_control": packet["summary"]["call_control"],
        "continuity": packet["demo_session_continuity"],
        "memory": packet["demo_conversation_memory"],
    }
    assert_condition(
        failures,
        ("owner" in lowered or "routing" in lowered) and "workflow review" in lowered,
        f"Owner answer after purpose should stay on the sales workflow track: {response}",
    )


def validate_no_timing_leaks(failures: list[str], evidence: dict[str, Any]) -> None:
    for name, item in evidence.items():
        response = normalize(str(item.get("response") or ""))
        for fragment in sorted(FORBIDDEN_CONTEXT_FRAGMENTS):
            if fragment in response:
                failures.append(f"{name} leaked timing-context fallback `{fragment}`: {item.get('response')}")


def render_report(payload: dict[str, Any]) -> str:
    lines = [
        "# LIVE-DEMO-012 Soft Stop And Context Recovery Validator",
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
            "- Checks that a soft callback refusal such as `maybe just don't` ends the call.",
            "- Checks that call-purpose questions override stale timing context.",
            "- Checks that owner/routing answers after call-purpose recovery stay on the sales workflow track.",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    failures: list[str] = []
    evidence: dict[str, Any] = {}
    validate_soft_stop_ends_call(failures, evidence)
    validate_call_purpose_overrides_timing(failures, evidence)
    validate_owner_answer_after_purpose_stays_on_sales_track(failures, evidence)
    validate_no_timing_leaks(failures, evidence)

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
