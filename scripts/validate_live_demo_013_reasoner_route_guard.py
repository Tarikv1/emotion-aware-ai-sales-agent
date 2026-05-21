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


CHECKPOINT_ID = "LIVE-DEMO-013-reasoner-route-guard"
GENERATED_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
RESULT_PATH = GENERATED_DIR / "result.json"
REPORT_PATH = GENERATED_DIR / "report.md"
TMP_DIR = ROOT / ".tmp" / CHECKPOINT_ID

FORBIDDEN_CUSTOMER_FRAGMENTS = {
    "fictional profile",
    "check fit only",
    "check scope only",
    "runtime",
    "guardrail",
    "if not stop",
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


def locked_route(packet: dict[str, Any]) -> dict[str, Any]:
    return dict((packet.get("dialogue_reasoner_async_enrichment") or {}).get("locked_deterministic_route") or {})


def validate_crm_replacement_question(failures: list[str], evidence: dict[str, Any]) -> None:
    packets = run_sequence(
        [
            ("__agent_open__", "agent-open"),
            ("yeah I guess sure", "speech-final"),
            ("I'm not really sure but our system is pretty alright in general but is this going to replace our current CRM", "speech-final"),
        ],
        session_id="live-demo-013-crm-replacement",
    )
    packet = packets[-1]
    response = customer_text(packet)
    lowered = normalize(response)
    route = locked_route(packet)
    evidence["crm_replacement"] = {
        "response": response,
        "call_control": packet["summary"]["call_control"],
        "continuity": packet["demo_session_continuity"],
        "reasoner_route": route,
    }
    assert_condition(failures, route.get("dialogue_act") == "integration_question", f"CRM replacement should be reasoned as an integration/CRM boundary: {route}")
    assert_condition(failures, "fictional profile" not in lowered, f"CRM answer must not expose fixture wording: {response}")
    assert_condition(failures, "routesignal" in lowered, f"CRM answer should use the public product name: {response}")
    assert_condition(failures, "replace" in lowered, f"CRM replacement question should be answered directly: {response}")
    assert_condition(failures, packet["summary"]["call_control"] == "continue-call", f"CRM replacement answer should keep the call open for qualification: {packet['summary']['call_control']}")


def validate_asr_question_clarification(failures: list[str], evidence: dict[str, Any]) -> None:
    packets = run_sequence(
        [
            ("__agent_open__", "agent-open"),
            ("I do yeah", "speech-final"),
            ("who is harder", "speech-final"),
        ],
        session_id="live-demo-013-who-is-harder",
    )
    packet = packets[-1]
    response = customer_text(packet)
    lowered = normalize(response)
    route = locked_route(packet)
    evidence["who_is_harder"] = {
        "response": response,
        "call_control": packet["summary"]["call_control"],
        "continuity": packet["demo_session_continuity"],
        "reasoner_route": route,
    }
    assert_condition(
        failures,
        route.get("dialogue_act") == "previous_question_clarification",
        f"`who is harder` should be reasoned as clarification of the previous question: {route}",
    )
    assert_condition(
        failures,
        packet["demo_session_continuity"].get("reason") == "previous_question_clarified",
        f"`who is harder` should use the previous-question clarification route: {packet['demo_session_continuity']}",
    )
    assert_condition(
        failures,
        "i meant" in lowered and ("owner" in lowered or "callback" in lowered or "handoff" in lowered),
        f"`who is harder` should explain the prior question in plain terms: {response}",
    )
    assert_condition(
        failures,
        "spreadsheet" not in lowered and "which part is more familiar" not in lowered,
        f"`who is harder` should not rotate to a different scripted qualification line: {response}",
    )


def validate_unfamiliar_after_clarification_stays_simple(failures: list[str], evidence: dict[str, Any]) -> None:
    packets = run_sequence(
        [
            ("__agent_open__", "agent-open"),
            ("I do yeah", "speech-final"),
            ("who is harder", "speech-final"),
            ("they're not really familiar to me", "speech-final"),
        ],
        session_id="live-demo-013-not-familiar",
    )
    packet = packets[-1]
    response = customer_text(packet)
    lowered = normalize(response)
    evidence["not_familiar_after_clarification"] = {
        "response": response,
        "call_control": packet["summary"]["call_control"],
        "continuity": packet["demo_session_continuity"],
        "reasoner_route": locked_route(packet),
    }
    assert_condition(
        failures,
        "demo" in lowered and ("owner" in lowered or "callback" in lowered or "handoff" in lowered),
        f"`not familiar` after clarification should simplify the workflow check: {response}",
    )
    assert_condition(
        failures,
        "least clear" not in lowered and "which part is more familiar" not in lowered,
        f"`not familiar` after clarification should not rotate another scripted menu: {response}",
    )


def validate_customer_text_is_clean(failures: list[str], evidence: dict[str, Any]) -> None:
    for name, item in evidence.items():
        response = normalize(str(item.get("response") or ""))
        for fragment in sorted(FORBIDDEN_CUSTOMER_FRAGMENTS):
            if fragment in response:
                failures.append(f"{name} customer speech contains internal fragment `{fragment}`: {item.get('response')}")


def render_report(payload: dict[str, Any]) -> str:
    lines = [
        "# LIVE-DEMO-013 Reasoner Route Guard Validator",
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
            "- Checks that CRM replacement questions use public product wording, not internal fixture labels.",
            "- Checks that ASR-shaped clarification such as `who is harder` explains the previous question.",
            "- Checks that deterministic reasoner labels are present before async enrichment and match the spoken route.",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    failures: list[str] = []
    evidence: dict[str, Any] = {}
    validate_crm_replacement_question(failures, evidence)
    validate_asr_question_clarification(failures, evidence)
    validate_unfamiliar_after_clarification_stays_simple(failures, evidence)
    validate_customer_text_is_clean(failures, evidence)

    payload = {
        "checkpoint_id": CHECKPOINT_ID,
        "passed": not failures,
        "failure_count": len(failures),
        "failures": failures,
        "provider_calls_made": False,
        "local_llm_calls_made": False,
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
