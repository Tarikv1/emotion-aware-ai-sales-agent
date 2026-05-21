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


CHECKPOINT_ID = "DIALOGUE-MANAGER-002-pragmatic-dialogue-repair"
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


def response(packet: dict[str, Any]) -> str:
    return str(packet["summary"]["final_response"] or "")


def manager_action(packet: dict[str, Any]) -> str:
    return str(((packet.get("dialogue_manager") or {}).get("selected_action") or {}).get("action_id") or "")


def pragmatic_move(packet: dict[str, Any]) -> dict[str, Any]:
    return dict(packet.get("dialogue_pragmatics") or {})


def assert_pragmatic_contract(
    failures: list[str],
    packet: dict[str, Any],
    *,
    label: str,
    expected_move: str,
    expected_action: str,
) -> None:
    move = pragmatic_move(packet)
    manager = packet.get("dialogue_manager") or {}
    assert_condition(failures, move.get("pragmatics_id") == "DIALOGUE-PRAGMATICS-001", f"{label}: missing pragmatics id: {move}")
    assert_condition(failures, move.get("schema_version") == 1, f"{label}: missing pragmatics schema: {move}")
    assert_condition(failures, move.get("move_id") == expected_move, f"{label}: expected pragmatic move {expected_move}, got {move}")
    assert_condition(
        failures,
        ((manager.get("state_before") or {}).get("pragmatic_move") or {}).get("move_id") == expected_move,
        f"{label}: manager state should include pragmatic move {expected_move}: {manager}",
    )
    assert_condition(failures, manager_action(packet) == expected_action, f"{label}: expected manager action {expected_action}, got {manager_action(packet)}")


def validate_call_purpose_question(failures: list[str], evidence: dict[str, Any]) -> None:
    packets = run_sequence(
        [
            ("__agent_open__", "agent-open"),
            ("sure I guess", "speech-final"),
            ("what is this call about what are you trying to say", "speech-final"),
        ],
        session_id="dialogue-manager-002-purpose",
    )
    packet = packets[-1]
    text = response(packet)
    lowered = normalize(text)
    evidence["call_purpose_question"] = snapshot(packet)
    assert_pragmatic_contract(
        failures,
        packet,
        label="call purpose",
        expected_move="call_purpose_question",
        expected_action="recover_call_purpose",
    )
    assert_condition(failures, "inbound demo follow" in lowered, f"Purpose answer should explain the call directly: {text}")
    assert_condition(failures, "timing" not in lowered and "no decision" not in lowered, f"Purpose answer should not be stale timing advice: {text}")


def validate_previous_question_clarification(failures: list[str], evidence: dict[str, Any]) -> None:
    packets = run_sequence(
        [
            ("__agent_open__", "agent-open"),
            ("I do yeah", "speech-final"),
            ("who is harder", "speech-final"),
        ],
        session_id="dialogue-manager-002-previous-question",
    )
    packet = packets[-1]
    text = response(packet)
    lowered = normalize(text)
    evidence["previous_question_clarification"] = snapshot(packet)
    assert_pragmatic_contract(
        failures,
        packet,
        label="previous question",
        expected_move="previous_question_clarification",
        expected_action="clarify_previous_question",
    )
    assert_condition(failures, "i meant" in lowered, f"Clarification should explain the previous question: {text}")
    assert_condition(failures, "which part is more familiar" not in lowered, f"Clarification should not rotate to another qualification prompt: {text}")


def validate_unfamiliarity_simplifies_question(failures: list[str], evidence: dict[str, Any]) -> None:
    packets = run_sequence(
        [
            ("__agent_open__", "agent-open"),
            ("I do yeah", "speech-final"),
            ("who is harder", "speech-final"),
            ("they're not really familiar to me", "speech-final"),
        ],
        session_id="dialogue-manager-002-unfamiliar",
    )
    packet = packets[-1]
    text = response(packet)
    lowered = normalize(text)
    evidence["unfamiliarity_simplifies_question"] = snapshot(packet)
    assert_pragmatic_contract(
        failures,
        packet,
        label="unfamiliarity",
        expected_move="term_or_context_unfamiliarity",
        expected_action="simplify_previous_question",
    )
    assert_condition(failures, "demo" in lowered and ("owner" in lowered or "callback" in lowered or "handoff" in lowered), f"Unfamiliarity should simplify the workflow check: {text}")
    assert_condition(failures, "least clear" not in lowered and "which part is more familiar" not in lowered, f"Unfamiliarity should not reopen a generic menu: {text}")


def validate_term_meaning_question(failures: list[str], evidence: dict[str, Any]) -> None:
    packets = run_sequence(
        [
            ("__agent_open__", "agent-open"),
            ("sure", "speech-final"),
            ("what do you mean by handoff", "speech-final"),
        ],
        session_id="dialogue-manager-002-term-meaning",
    )
    packet = packets[-1]
    text = response(packet)
    lowered = normalize(text)
    evidence["term_meaning_question"] = snapshot(packet)
    assert_pragmatic_contract(
        failures,
        packet,
        label="term meaning",
        expected_move="term_meaning_question",
        expected_action="explain_term",
    )
    assert_condition(failures, "handoff" in lowered and ("owner" in lowered or "next person" in lowered), f"Term answer should explain handoff plainly: {text}")
    memory = packet.get("demo_conversation_memory") or packet.get("conversation_memory") or {}
    assert_condition(failures, not memory.get("selected_gap"), f"Term meaning question should not select a workflow pain gap: {memory}")


def validate_relevance_challenge(failures: list[str], evidence: dict[str, Any]) -> None:
    packets = run_sequence(
        [
            ("__agent_open__", "agent-open"),
            ("sure", "speech-final"),
            ("why does that matter", "speech-final"),
        ],
        session_id="dialogue-manager-002-relevance",
    )
    packet = packets[-1]
    text = response(packet)
    lowered = normalize(text)
    evidence["relevance_challenge"] = snapshot(packet)
    assert_pragmatic_contract(
        failures,
        packet,
        label="relevance challenge",
        expected_move="relevance_challenge",
        expected_action="explain_relevance",
    )
    assert_condition(failures, "missed" in lowered and ("follow" in lowered or "callback" in lowered), f"Relevance answer should connect to missed follow-up: {text}")


def validate_agent_lead_request(failures: list[str], evidence: dict[str, Any]) -> None:
    packets = run_sequence(
        [
            ("__agent_open__", "agent-open"),
            ("I don't have a question you called me", "speech-final"),
        ],
        session_id="dialogue-manager-002-agent-lead",
    )
    packet = packets[-1]
    text = response(packet)
    lowered = normalize(text)
    evidence["agent_lead_request"] = snapshot(packet)
    assert_pragmatic_contract(
        failures,
        packet,
        label="agent lead request",
        expected_move="agent_should_lead",
        expected_action="recover_seller_agenda",
    )
    assert_condition(failures, "i called to check" in lowered or "one workflow" in lowered, f"Agent should lead after buyer says caller should ask: {text}")


def validate_crm_boundary_is_pragmatic(failures: list[str], evidence: dict[str, Any]) -> None:
    packets = run_sequence(
        [
            ("__agent_open__", "agent-open"),
            ("yeah I guess sure", "speech-final"),
            ("our system is pretty alright in general but is this going to replace our current CRM", "speech-final"),
        ],
        session_id="dialogue-manager-002-crm",
    )
    packet = packets[-1]
    text = response(packet)
    lowered = normalize(text)
    evidence["crm_boundary"] = snapshot(packet)
    assert_pragmatic_contract(
        failures,
        packet,
        label="crm boundary",
        expected_move="crm_replacement_question",
        expected_action="answer_crm_boundary_continue",
    )
    assert_condition(failures, "routesignal" in lowered and "replace" in lowered, f"CRM boundary should answer directly with public wording: {text}")


def validate_pain_statement_to_appointment(failures: list[str], evidence: dict[str, Any]) -> None:
    packets = run_sequence(
        [
            ("__agent_open__", "agent-open"),
            ("yes", "speech-final"),
            ("yeah leads are getting missed", "speech-final"),
        ],
        session_id="dialogue-manager-002-pain",
    )
    packet = packets[-1]
    text = response(packet)
    evidence["pain_statement"] = snapshot(packet)
    assert_pragmatic_contract(
        failures,
        packet,
        label="pain statement",
        expected_move="pain_statement",
        expected_action="request_appointment_time",
    )
    assert_condition(failures, is_appointment_close_ask(text), f"Pain statement should move to workflow-review appointment time: {text}")


def validate_customer_text_is_clean(failures: list[str], evidence: dict[str, Any]) -> None:
    for name, item in evidence.items():
        lowered = normalize(str(item.get("response") or ""))
        for fragment in sorted(FORBIDDEN_CUSTOMER_FRAGMENTS):
            if fragment in lowered:
                failures.append(f"{name} customer speech contains internal fragment `{fragment}`: {item.get('response')}")


def snapshot(packet: dict[str, Any]) -> dict[str, Any]:
    return {
        "transcript": packet["transcript"],
        "response": response(packet),
        "call_control": packet["summary"]["call_control"],
        "dialogue_pragmatics": packet.get("dialogue_pragmatics") or {},
        "manager": packet.get("dialogue_manager") or {},
        "continuity": packet.get("demo_session_continuity") or {},
    }


def render_report(payload: dict[str, Any]) -> str:
    lines = [
        "# DIALOGUE-MANAGER-002 Pragmatic Dialogue Repair Validator",
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
            "- Checks small human dialogue moves before sales route selection.",
            "- Requires a dedicated local pragmatic move packet behind the manager.",
            "- Keeps provider calls, local LLM calls, payment, contract closure, production promotion, and PROD-102 out of scope.",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    failures: list[str] = []
    evidence: dict[str, Any] = {}
    validate_call_purpose_question(failures, evidence)
    validate_previous_question_clarification(failures, evidence)
    validate_unfamiliarity_simplifies_question(failures, evidence)
    validate_term_meaning_question(failures, evidence)
    validate_relevance_challenge(failures, evidence)
    validate_agent_lead_request(failures, evidence)
    validate_crm_boundary_is_pragmatic(failures, evidence)
    validate_pain_statement_to_appointment(failures, evidence)
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
