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


CHECKPOINT_ID = "CONTEXTUAL-BUYER-SEMANTICS-002-sequential-dialogue"
GENERATED_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
RESULT_PATH = GENERATED_DIR / "result.json"
REPORT_PATH = GENERATED_DIR / "report.md"
TMP_DIR = ROOT / ".tmp" / CHECKPOINT_ID


def normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9$]+", " ", str(text).lower()).strip()


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


def manager_source(packet: dict[str, Any]) -> str:
    return str((((packet.get("dialogue_manager") or {}).get("selected_action") or {}).get("source")) or "")


def call_control(packet: dict[str, Any]) -> str:
    return str((packet.get("summary") or {}).get("call_control") or "")


def selected_gap(packet: dict[str, Any]) -> str:
    return str(memory(packet).get("selected_gap") or "")


def snapshot(packet: dict[str, Any]) -> dict[str, Any]:
    manager = packet.get("dialogue_manager") or {}
    return {
        "turn": packet.get("session_turn_index"),
        "transcript": packet.get("transcript"),
        "response": response(packet),
        "tts_input_text": tts_input_text(packet),
        "call_control": call_control(packet),
        "semantic_frame": semantic_frame(packet),
        "manager_source": manager_source(packet),
        "selected_action": manager.get("selected_action") or {},
        "memory": memory(packet),
        "continuity": packet.get("demo_session_continuity") or {},
        "provider_calls_made": bool((packet.get("summary") or {}).get("tts_provider_calls_made")),
        "local_llm_calls_made": bool(manager.get("local_llm_calls_made")),
    }


def assert_no_provider_or_llm(failures: list[str], packet: dict[str, Any], label: str) -> None:
    snap = snapshot(packet)
    assert_condition(failures, not snap["provider_calls_made"], f"{label}: provider calls must stay false: {snap}")
    assert_condition(failures, not snap["local_llm_calls_made"], f"{label}: local LLM calls must stay false: {snap}")


def assert_semantic(
    failures: list[str],
    packet: dict[str, Any],
    *,
    label: str,
    expected: str | set[str],
    target_gap: str | None = None,
    require_contextual_source: bool = True,
    forbidden: set[str] | None = None,
) -> None:
    frame = semantic_frame(packet)
    actual = str(frame.get("semantic") or "")
    expected_set = {expected} if isinstance(expected, str) else set(expected)
    assert_condition(failures, bool(frame), f"{label}: semantic frame must be exposed in dialogue manager trace.")
    assert_condition(failures, actual in expected_set, f"{label}: expected semantic {sorted(expected_set)}, got `{actual}`: {snapshot(packet)}")
    if target_gap is not None:
        assert_condition(failures, frame.get("target_gap") == target_gap, f"{label}: expected target_gap `{target_gap}`: {snapshot(packet)}")
    for blocked in sorted(forbidden or set()):
        assert_condition(failures, actual != blocked, f"{label}: must not classify as `{blocked}`: {snapshot(packet)}")
    if require_contextual_source and frame.get("applied"):
        assert_condition(
            failures,
            manager_source(packet) == "contextual_buyer_semantics",
            f"{label}: applied semantic should be selected from contextual_buyer_semantics: {snapshot(packet)}",
        )
    assert_no_provider_or_llm(failures, packet, label)


def assert_spoken_contains(failures: list[str], packet: dict[str, Any], fragments: set[str], label: str) -> None:
    final_text = normalize(response(packet))
    tts_text = normalize(tts_input_text(packet))
    assert_condition(
        failures,
        any(fragment in final_text for fragment in fragments),
        f"{label}: final_response should contain one of {sorted(fragments)}: {response(packet)}",
    )
    assert_condition(
        failures,
        any(fragment in tts_text for fragment in fragments),
        f"{label}: tts_input_text should contain one of {sorted(fragments)}: {tts_input_text(packet)}",
    )


def assert_spoken_excludes(failures: list[str], packet: dict[str, Any], fragments: set[str], label: str) -> None:
    final_text = normalize(response(packet))
    tts_text = normalize(tts_input_text(packet))
    for fragment in sorted(fragments):
        assert_condition(failures, fragment not in final_text, f"{label}: final_response must not contain `{fragment}`: {response(packet)}")
        assert_condition(failures, fragment not in tts_text, f"{label}: tts_input_text must not contain `{fragment}`: {tts_input_text(packet)}")


def assert_memory_contains(failures: list[str], packet: dict[str, Any], key: str, gap: str, label: str) -> None:
    values = set(memory(packet).get(key) or [])
    assert_condition(failures, gap in values, f"{label}: memory.{key} should include `{gap}`: {snapshot(packet)}")


def validate_sequential_dialogue(failures: list[str], evidence: dict[str, Any]) -> None:
    scenarios: dict[str, list[str]] = {
        "scenario_a_permission_clear_next_diagnostic": ["__agent_open__", "yeah sure", "callbacks are fine"],
        "scenario_b_clear_then_pain_then_appointment": [
            "__agent_open__",
            "yeah sure",
            "callbacks are fine",
            "manual tracking does get messy sometimes",
        ],
        "scenario_c_pain_then_different_gap_clear": [
            "__agent_open__",
            "yeah sure",
            "missed callbacks happen sometimes",
            "manual tracking is fine",
        ],
        "scenario_d_early_not_relevant": ["__agent_open__", "not relevant"],
        "scenario_e_mid_call_not_relevant": ["__agent_open__", "yeah sure", "callbacks are fine", "not relevant"],
        "scenario_f_wrong_person": ["__agent_open__", "yeah sure", "I'm not the person, operations handles this"],
        "scenario_g_send_info": ["__agent_open__", "yeah sure", "send me details"],
        "scenario_h_maybe_later": ["__agent_open__", "yeah sure", "maybe later"],
        "scenario_i_stop_calling": ["__agent_open__", "stop calling", "are you still there"],
        "scenario_j_no_problem_context_split": ["__agent_open__", "no problem", "no problem"],
    }

    packets_by_scenario = {label: run_sequence(transcripts, session_id=label) for label, transcripts in scenarios.items()}
    for label, packets in packets_by_scenario.items():
        evidence[label] = [snapshot(packet) for packet in packets]

    scenario_a = packets_by_scenario["scenario_a_permission_clear_next_diagnostic"]
    assert_semantic(failures, scenario_a[1], label="scenario_a_turn2", expected="permission_acknowledgement")
    assert_semantic(failures, scenario_a[2], label="scenario_a_turn3", expected="current_gap_clear", target_gap="callbacks")
    assert_memory_contains(failures, scenario_a[2], "cleared_gaps", "callbacks", "scenario_a_turn3")
    assert_spoken_contains(failures, scenario_a[2], {"manual tracking", "handoffs"}, "scenario_a_turn3")
    assert_spoken_excludes(failures, scenario_a[2], {"workflow review", "what time"}, "scenario_a_turn3")

    scenario_b = packets_by_scenario["scenario_b_clear_then_pain_then_appointment"]
    assert_memory_contains(failures, scenario_b[2], "cleared_gaps", "callbacks", "scenario_b_turn3")
    assert_semantic(
        failures,
        scenario_b[3],
        label="scenario_b_turn4",
        expected="pain_confirmed",
        target_gap="manual_tracking",
        require_contextual_source=False,
        forbidden={"current_gap_clear"},
    )
    assert_memory_contains(failures, scenario_b[3], "cleared_gaps", "callbacks", "scenario_b_turn4")
    assert_memory_contains(failures, scenario_b[3], "confirmed_gaps", "manual_tracking", "scenario_b_turn4")
    assert_spoken_contains(
        failures,
        scenario_b[3],
        {"workflow review", "what time works", "short workflow"},
        "scenario_b_turn4",
    )

    scenario_c = packets_by_scenario["scenario_c_pain_then_different_gap_clear"]
    assert_semantic(
        failures,
        scenario_c[2],
        label="scenario_c_turn3",
        expected="pain_confirmed",
        target_gap="callbacks",
        require_contextual_source=False,
        forbidden={"current_gap_clear"},
    )
    assert_memory_contains(failures, scenario_c[2], "confirmed_gaps", "callbacks", "scenario_c_turn3")
    assert_semantic(failures, scenario_c[3], label="scenario_c_turn4", expected="current_gap_clear", target_gap="manual_tracking")
    assert_memory_contains(failures, scenario_c[3], "cleared_gaps", "manual_tracking", "scenario_c_turn4")
    assert_memory_contains(failures, scenario_c[3], "confirmed_gaps", "callbacks", "scenario_c_turn4")
    assert_spoken_contains(failures, scenario_c[3], {"workflow review", "what time works", "real gap"}, "scenario_c_turn4")

    scenario_d = packets_by_scenario["scenario_d_early_not_relevant"]
    assert_semantic(failures, scenario_d[1], label="scenario_d_turn2", expected="not_relevant_early")
    assert_condition(failures, call_control(scenario_d[1]) == "end-call", f"scenario_d_turn2: expected end-call: {snapshot(scenario_d[1])}")
    assert_spoken_excludes(failures, scenario_d[1], {"workflow review", "what time"}, "scenario_d_turn2")

    scenario_e = packets_by_scenario["scenario_e_mid_call_not_relevant"]
    assert_semantic(
        failures,
        scenario_e[3],
        label="scenario_e_turn4",
        expected={"not_relevant_mid_call", "not_relevant_late"},
    )
    if semantic_frame(scenario_e[3]).get("semantic") == "not_relevant_mid_call":
        assert_condition(
            failures,
            response(scenario_e[3]).count("?") <= 1,
            f"scenario_e_turn4: mid-call save should use at most one question: {response(scenario_e[3])}",
        )
    assert_spoken_excludes(failures, scenario_e[3], {"workflow review", "what time works"}, "scenario_e_turn4")

    scenario_f = packets_by_scenario["scenario_f_wrong_person"]
    assert_semantic(failures, scenario_f[2], label="scenario_f_turn3", expected="wrong_person_or_wrong_department")
    assert_condition(failures, selected_gap(scenario_f[2]) != "routing", f"scenario_f_turn3: wrong person must not become product routing: {snapshot(scenario_f[2])}")
    assert_spoken_contains(failures, scenario_f[2], {"right person", "stop here"}, "scenario_f_turn3")
    assert_spoken_excludes(failures, scenario_f[2], {"workflow review", "what time works"}, "scenario_f_turn3")

    scenario_g = packets_by_scenario["scenario_g_send_info"]
    assert_semantic(failures, scenario_g[2], label="scenario_g_turn3", expected="send_info_request")
    assert_condition(failures, call_control(scenario_g[2]) == "continue-call", f"scenario_g_turn3: send-info should not auto-end: {snapshot(scenario_g[2])}")
    assert_spoken_contains(failures, scenario_g[2], {"written summary", "email", "callback time"}, "scenario_g_turn3")
    assert_spoken_excludes(failures, scenario_g[2], {"confirmed", "goodbye"}, "scenario_g_turn3")

    scenario_h = packets_by_scenario["scenario_h_maybe_later"]
    assert_semantic(
        failures,
        scenario_h[2],
        label="scenario_h_turn3",
        expected={"callback_scheduling_request", "timing_soft_deferral"},
        require_contextual_source=True,
        forbidden={"all_clear_no_pain", "current_gap_clear"},
    )
    assert_spoken_contains(failures, scenario_h[2], {"what time", "call back", "callback"}, "scenario_h_turn3")

    scenario_i = packets_by_scenario["scenario_i_stop_calling"]
    assert_semantic(failures, scenario_i[1], label="scenario_i_turn2", expected="stop_request")
    assert_condition(failures, call_control(scenario_i[1]) == "end-call", f"scenario_i_turn2: stop calling should end: {snapshot(scenario_i[1])}")
    assert_condition(failures, call_control(scenario_i[2]) == "end-call", f"scenario_i_turn3: terminal stop should remain closed: {snapshot(scenario_i[2])}")
    assert_condition(
        failures,
        ((scenario_i[2].get("dialogue_manager") or {}).get("selected_action") or {}).get("action_id") == "keep_call_closed",
        f"scenario_i_turn3: later input after stop should keep call closed: {snapshot(scenario_i[2])}",
    )

    scenario_j = packets_by_scenario["scenario_j_no_problem_context_split"]
    assert_semantic(failures, scenario_j[1], label="scenario_j_turn2", expected="permission_acknowledgement")
    assert_semantic(
        failures,
        scenario_j[2],
        label="scenario_j_turn3",
        expected={"current_gap_clear", "low_information_continue", "multi_gap_clear"},
        require_contextual_source=True,
        forbidden={"all_clear_no_pain", "pain_confirmed"},
    )


def validate_paraphrase_coverage(failures: list[str], evidence: dict[str, Any]) -> None:
    clear_phrases = [
        "we're good",
        "we are good",
        "all good",
        "we're fine",
        "we are fine",
        "we're covered",
        "we have it covered",
        "that's handled",
        "we already handle that",
        "that does not happen here",
        "we don't have that issue",
        "we do not have that issue",
        "no need there",
        "no issue there",
        "nothing falls through",
        "nothing gets lost",
        "callbacks are handled",
        "handoffs are handled",
        "routing is fine",
        "reminders are fine",
        "tracking is fine",
    ]
    clear_targets = {
        "callbacks are handled": "callbacks",
        "handoffs are handled": "handoffs",
        "routing is fine": "routing",
        "reminders are fine": "reminders",
        "tracking is fine": "manual_tracking",
    }
    refusal_phrases = [
        "not our thing",
        "not useful for us",
        "no need",
        "we don't need this",
        "we do not need this",
        "we already have a solution",
        "we already have a process",
        "we're covered, thanks",
        "no thanks",
        "I'm not interested",
        "we're not interested",
        "take us off your list",
        "remove us",
        "don't call again",
        "stop calling",
    ]
    wrong_person_phrases = [
        "I'm not the person",
        "I am not the person",
        "I don't handle that",
        "I do not handle that",
        "talk to operations",
        "sales handles that",
        "support handles that",
        "my manager handles that",
        "someone else handles that",
        "wrong department",
        "wrong team",
    ]
    send_info_phrases = [
        "send me something",
        "send over details",
        "send me details",
        "send me an email",
        "email me",
        "send information",
        "send the summary",
        "can you send info first",
        "put it in writing",
    ]
    timing_phrases = [
        "maybe later",
        "not right now",
        "not today",
        "call another time",
        "try next week",
        "now is bad",
        "bad timing",
        "I'm busy",
        "I'm in a meeting",
    ]

    paraphrase_records: dict[str, Any] = {}

    for phrase in clear_phrases:
        packet = run_sequence(["__agent_open__", "yeah sure", phrase], session_id=f"paraphrase-clear-{normalize(phrase)}")[-1]
        paraphrase_records[f"clear::{phrase}"] = snapshot(packet)
        assert_semantic(
            failures,
            packet,
            label=f"clear::{phrase}",
            expected={"current_gap_clear", "all_clear_no_pain", "multi_gap_clear"},
            target_gap=clear_targets.get(phrase),
            forbidden={"pain_confirmed", "callback_workflow_gap", "manual_tracking_objection"},
        )
        if semantic_frame(packet).get("semantic") == "current_gap_clear":
            assert_condition(
                failures,
                call_control(packet) == "continue-call",
                f"clear::{phrase}: current-gap clear should continue to a next diagnostic or bridge: {snapshot(packet)}",
            )

    for phrase in refusal_phrases:
        packet = run_sequence(["__agent_open__", phrase], session_id=f"paraphrase-refusal-{normalize(phrase)}")[-1]
        paraphrase_records[f"refusal::{phrase}"] = snapshot(packet)
        assert_semantic(
            failures,
            packet,
            label=f"refusal::{phrase}",
            expected={"not_relevant_early", "not_interested", "stop_request"},
            require_contextual_source=True,
            forbidden={"current_gap_clear", "pain_confirmed"},
        )
        assert_condition(failures, call_control(packet) == "end-call", f"refusal::{phrase}: refusal should end-call: {snapshot(packet)}")
        assert_spoken_excludes(failures, packet, {"workflow review", "what time works"}, f"refusal::{phrase}")

    for phrase in wrong_person_phrases:
        packet = run_sequence(["__agent_open__", "yeah sure", phrase], session_id=f"paraphrase-wrong-person-{normalize(phrase)}")[-1]
        paraphrase_records[f"wrong_person::{phrase}"] = snapshot(packet)
        assert_semantic(failures, packet, label=f"wrong_person::{phrase}", expected="wrong_person_or_wrong_department")
        assert_condition(
            failures,
            selected_gap(packet) != "routing",
            f"wrong_person::{phrase}: wrong person must not become product routing: {snapshot(packet)}",
        )
        assert_spoken_excludes(failures, packet, {"workflow review", "what time works"}, f"wrong_person::{phrase}")

    for phrase in send_info_phrases:
        packet = run_sequence(["__agent_open__", "yeah sure", phrase], session_id=f"paraphrase-send-info-{normalize(phrase)}")[-1]
        paraphrase_records[f"send_info::{phrase}"] = snapshot(packet)
        assert_semantic(failures, packet, label=f"send_info::{phrase}", expected="send_info_request")
        assert_condition(failures, call_control(packet) == "continue-call", f"send_info::{phrase}: send-info should not auto-end: {snapshot(packet)}")
        assert_spoken_contains(failures, packet, {"written summary", "email", "callback time"}, f"send_info::{phrase}")

    for phrase in timing_phrases:
        packet = run_sequence(["__agent_open__", "yeah sure", phrase], session_id=f"paraphrase-timing-{normalize(phrase)}")[-1]
        paraphrase_records[f"timing::{phrase}"] = snapshot(packet)
        assert_semantic(
            failures,
            packet,
            label=f"timing::{phrase}",
            expected={"callback_scheduling_request", "timing_soft_deferral"},
            forbidden={"all_clear_no_pain", "current_gap_clear"},
        )
        assert_spoken_contains(failures, packet, {"what time", "call back", "callback"}, f"timing::{phrase}")

    evidence["paraphrase_coverage"] = paraphrase_records


def render_report(payload: dict[str, Any]) -> str:
    lines = [
        "# CONTEXTUAL-BUYER-SEMANTICS-002 Sequential Dialogue Validator",
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
            "## Sequential Coverage",
            "",
            "- Replays live-demo turn packets from an empty state.",
            "- Appends each returned packet before the next buyer turn.",
            "- Checks semantic frame, manager source, memory, call control, final_response, and tts_input_text.",
            "- Keeps provider calls, live TTS, local LLMs, and PROD-102 disabled.",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    failures: list[str] = []
    evidence: dict[str, Any] = {}
    validate_sequential_dialogue(failures, evidence)
    validate_paraphrase_coverage(failures, evidence)
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
