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


CHECKPOINT_ID = "CONTEXTUAL-BUYER-SEMANTICS-003-memory-alignment"
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


def selected_action(packet: dict[str, Any]) -> dict[str, Any]:
    return dict(((packet.get("dialogue_manager") or {}).get("selected_action")) or {})


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
        "selected_action": selected_action(packet),
        "memory": memory(packet),
        "continuity": packet.get("demo_session_continuity") or {},
        "provider_calls_made": bool((packet.get("summary") or {}).get("tts_provider_calls_made")),
        "local_llm_calls_made": bool(manager.get("local_llm_calls_made")),
    }


def gaps(packet: dict[str, Any], key: str) -> set[str]:
    return set(str(item) for item in (memory(packet).get(key) or []))


def frame_gaps(packet: dict[str, Any], key: str) -> set[str]:
    frame = semantic_frame(packet)
    values = frame.get(key) or (frame.get("evidence") or {}).get(key) or []
    return set(str(item) for item in values)


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
) -> None:
    frame = semantic_frame(packet)
    actual = str(frame.get("semantic") or "")
    expected_set = {expected} if isinstance(expected, str) else set(expected)
    assert_condition(failures, bool(frame), f"{label}: semantic frame must be exposed: {snapshot(packet)}")
    assert_condition(failures, actual in expected_set, f"{label}: expected semantic {sorted(expected_set)}, got `{actual}`: {snapshot(packet)}")
    if target_gap is not None:
        assert_condition(failures, frame.get("target_gap") == target_gap, f"{label}: expected target_gap `{target_gap}`: {snapshot(packet)}")
    if frame.get("applied"):
        assert_condition(
            failures,
            manager_source(packet) == "contextual_buyer_semantics",
            f"{label}: applied semantic should be manager source contextual_buyer_semantics: {snapshot(packet)}",
        )
    assert_no_provider_or_llm(failures, packet, label)


def assert_contains_all(failures: list[str], values: set[str], expected: set[str], label: str, packet: dict[str, Any]) -> None:
    missing = expected - values
    assert_condition(failures, not missing, f"{label}: missing {sorted(missing)} from {sorted(values)}: {snapshot(packet)}")


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


def assert_memory_alignment(failures: list[str], packet: dict[str, Any], label: str) -> None:
    frame = semantic_frame(packet)
    semantic = str(frame.get("semantic") or "")
    mem = memory(packet)
    if semantic in {"current_gap_clear", "no_pain_for_specific_gap", "multi_gap_clear", "all_clear_no_pain"}:
        target_gap = frame.get("target_gap")
        if target_gap:
            assert_condition(failures, target_gap in gaps(packet, "cleared_gaps"), f"{label}: clear semantic should store cleared gap: {snapshot(packet)}")
            assert_condition(failures, target_gap in gaps(packet, "no_pain_topics"), f"{label}: clear semantic should store no-pain topic: {snapshot(packet)}")
        assert_condition(
            failures,
            mem.get("callback_semantic") != "callback_workflow_gap",
            f"{label}: clear semantic must not leave callback_workflow_gap memory: {snapshot(packet)}",
        )
        assert_condition(
            failures,
            mem.get("last_customer_intent") != "callback_workflow_gap",
            f"{label}: clear semantic must not leave callback_workflow_gap intent: {snapshot(packet)}",
        )
    if semantic == "pain_confirmed":
        target_gap = str(frame.get("target_gap") or "")
        assert_condition(failures, target_gap in gaps(packet, "confirmed_gaps"), f"{label}: pain semantic should store confirmed gap: {snapshot(packet)}")
    if semantic == "send_info_request":
        assert_condition(failures, not mem.get("appointment_close_ready"), f"{label}: send-info must not fake appointment readiness: {snapshot(packet)}")
        assert_condition(failures, call_control(packet) != "schedule-and-end", f"{label}: send-info must not schedule-and-end without a time: {snapshot(packet)}")


def validate_memory_alignment(failures: list[str], evidence: dict[str, Any]) -> None:
    scenarios = {
        "scenario_a_clear_callbacks_no_memory_pollution": ["__agent_open__", "yeah sure", "callbacks are fine"],
        "scenario_b_all_good_multi_gap_clear": ["__agent_open__", "yeah sure", "all good"],
        "scenario_c_no_issue_multi_gap_clear": ["__agent_open__", "yeah sure", "no issue"],
        "scenario_d_clear_callbacks_confirm_handoffs": ["__agent_open__", "yeah sure", "callbacks are fine but handoffs get messy"],
        "scenario_e_multi_gap_pain_ranking": ["__agent_open__", "yeah sure", "mostly missed callbacks but occasional manual tracking too"],
        "scenario_f_early_not_relevant_no_callback_gap": ["__agent_open__", "not relevant"],
        "scenario_g_mid_not_relevant_all_of_it": ["__agent_open__", "yeah sure", "callbacks are fine", "not relevant", "all of it"],
        "scenario_h_mid_not_relevant_just_callbacks": ["__agent_open__", "yeah sure", "callbacks are fine", "not relevant", "just callbacks"],
        "scenario_i_final_save_uncovers_handoffs": ["__agent_open__", "yeah sure", "callbacks are fine", "not relevant", "handoffs are the actual issue"],
        "scenario_j_send_info_stays_open": ["__agent_open__", "yeah sure", "send me details", "yes send it"],
    }
    packets_by_scenario = {label: run_sequence(transcripts, session_id=label) for label, transcripts in scenarios.items()}
    for label, packets in packets_by_scenario.items():
        evidence[label] = [snapshot(packet) for packet in packets]

    scenario_a = packets_by_scenario["scenario_a_clear_callbacks_no_memory_pollution"]
    assert_semantic(failures, scenario_a[2], label="scenario_a_turn3", expected="current_gap_clear", target_gap="callbacks")
    assert_memory_alignment(failures, scenario_a[2], "scenario_a_turn3")
    assert_spoken_contains(failures, scenario_a[2], {"manual tracking", "handoffs"}, "scenario_a_turn3")

    for scenario_name in ["scenario_b_all_good_multi_gap_clear", "scenario_c_no_issue_multi_gap_clear"]:
        packet = packets_by_scenario[scenario_name][2]
        label = f"{scenario_name}_turn3"
        assert_semantic(failures, packet, label=label, expected={"all_clear_no_pain", "multi_gap_clear"})
        frame = semantic_frame(packet)
        assert_condition(failures, frame.get("active_gap_scope") == "multi_gap", f"{label}: should expose active_gap_scope=multi_gap: {snapshot(packet)}")
        assert_contains_all(failures, set(frame.get("candidate_gaps") or []), {"callbacks", "manual_tracking", "handoffs"}, label, packet)
        assert_contains_all(failures, gaps(packet, "cleared_gaps"), {"callbacks", "manual_tracking", "handoffs"}, label, packet)
        assert_memory_alignment(failures, packet, label)
        assert_spoken_excludes(failures, packet, {"workflow review", "what time works"}, label)
        assert_spoken_excludes(failures, packet, {"missed callbacks manual tracking or handoffs creating issues"}, label)

    scenario_d = packets_by_scenario["scenario_d_clear_callbacks_confirm_handoffs"]
    assert_semantic(failures, scenario_d[2], label="scenario_d_turn3", expected={"pain_confirmed", "mixed_gap_response"}, target_gap="handoffs")
    assert_contains_all(failures, gaps(scenario_d[2], "cleared_gaps"), {"callbacks"}, "scenario_d_turn3", scenario_d[2])
    assert_contains_all(failures, gaps(scenario_d[2], "confirmed_gaps"), {"handoffs"}, "scenario_d_turn3", scenario_d[2])
    assert_spoken_contains(failures, scenario_d[2], {"workflow review", "handoffs", "what time works"}, "scenario_d_turn3")

    scenario_e = packets_by_scenario["scenario_e_multi_gap_pain_ranking"]
    assert_semantic(failures, scenario_e[2], label="scenario_e_turn3", expected="pain_confirmed", target_gap="callbacks")
    frame_e = semantic_frame(scenario_e[2])
    assert_condition(failures, frame_e.get("primary_gap") == "callbacks", f"scenario_e_turn3: primary_gap should be callbacks: {snapshot(scenario_e[2])}")
    confirmed_or_secondary = gaps(scenario_e[2], "confirmed_gaps") | set(frame_e.get("secondary_confirmed_gaps") or [])
    assert_contains_all(failures, confirmed_or_secondary, {"callbacks", "manual_tracking"}, "scenario_e_turn3", scenario_e[2])
    assert_spoken_contains(failures, scenario_e[2], {"missed callbacks"}, "scenario_e_turn3")

    scenario_f = packets_by_scenario["scenario_f_early_not_relevant_no_callback_gap"]
    assert_semantic(failures, scenario_f[1], label="scenario_f_turn2", expected="not_relevant_early")
    frame_f = semantic_frame(scenario_f[1])
    assert_condition(
        failures,
        frame_f.get("target_topic") in {None, "campaign_relevance"},
        f"scenario_f_turn2: early not relevant should target campaign relevance/null: {snapshot(scenario_f[1])}",
    )
    assert_condition(failures, memory(scenario_f[1]).get("selected_gap") not in {"callbacks"}, f"scenario_f_turn2: opener callbacks must not become selected gap: {snapshot(scenario_f[1])}")
    assert_condition(failures, call_control(scenario_f[1]) == "end-call", f"scenario_f_turn2: expected end-call: {snapshot(scenario_f[1])}")
    assert_spoken_excludes(failures, scenario_f[1], {"workflow review", "what time works"}, "scenario_f_turn2")

    scenario_g = packets_by_scenario["scenario_g_mid_not_relevant_all_of_it"]
    assert_semantic(failures, scenario_g[3], label="scenario_g_turn4", expected="not_relevant_mid_call")
    assert_condition(failures, bool(memory(scenario_g[3]).get("final_save_pending")), f"scenario_g_turn4: final_save_pending should be true: {snapshot(scenario_g[3])}")
    assert_condition(failures, response(scenario_g[3]).count("?") <= 1, f"scenario_g_turn4: final save should be one question: {response(scenario_g[3])}")
    assert_semantic(failures, scenario_g[4], label="scenario_g_turn5", expected={"not_relevant_late", "stop_request"})
    assert_condition(failures, call_control(scenario_g[4]) == "end-call", f"scenario_g_turn5: final save all-of-it should end: {snapshot(scenario_g[4])}")
    assert_spoken_excludes(failures, scenario_g[4], {"manual tracking or handoffs ever create", "workflow review"}, "scenario_g_turn5")

    scenario_h = packets_by_scenario["scenario_h_mid_not_relevant_just_callbacks"]
    assert_semantic(failures, scenario_h[4], label="scenario_h_turn5", expected={"current_gap_clear", "not_relevant_late", "multi_gap_clear"})
    assert_contains_all(failures, gaps(scenario_h[4], "cleared_gaps"), {"callbacks"}, "scenario_h_turn5", scenario_h[4])
    assert_condition(failures, memory(scenario_h[4]).get("callback_semantic") != "callback_workflow_gap", f"scenario_h_turn5: just callbacks must not reopen callback pain: {snapshot(scenario_h[4])}")

    scenario_i = packets_by_scenario["scenario_i_final_save_uncovers_handoffs"]
    assert_semantic(failures, scenario_i[4], label="scenario_i_turn5", expected="pain_confirmed", target_gap="handoffs")
    assert_contains_all(failures, gaps(scenario_i[4], "cleared_gaps"), {"callbacks"}, "scenario_i_turn5", scenario_i[4])
    assert_contains_all(failures, gaps(scenario_i[4], "confirmed_gaps"), {"handoffs"}, "scenario_i_turn5", scenario_i[4])
    assert_spoken_contains(failures, scenario_i[4], {"workflow review", "handoffs", "what time works"}, "scenario_i_turn5")

    scenario_j = packets_by_scenario["scenario_j_send_info_stays_open"]
    assert_semantic(failures, scenario_j[2], label="scenario_j_turn3", expected="send_info_request")
    assert_memory_alignment(failures, scenario_j[2], "scenario_j_turn3")
    assert_condition(failures, call_control(scenario_j[3]) != "schedule-and-end", f"scenario_j_turn4: no fake schedule end: {snapshot(scenario_j[3])}")
    assert_condition(failures, not memory(scenario_j[3]).get("appointment_close_ready"), f"scenario_j_turn4: no fake appointment ready: {snapshot(scenario_j[3])}")
    assert_spoken_contains(failures, scenario_j[3], {"callback", "email", "human", "what time"}, "scenario_j_turn4")


def render_report(payload: dict[str, Any]) -> str:
    lines = [
        "# CONTEXTUAL-BUYER-SEMANTICS-003 Memory Alignment Validator",
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
            "## Coverage",
            "",
            "- Replays real live-demo turn packets from empty state.",
            "- Checks semantic frame, manager source, memory, call control, final_response, and tts_input_text.",
            "- Guards contextual semantics against older callback/workflow memory pollution.",
            "- Adds multi-gap diagnostic scope expectations for the broad fit-check question.",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    failures: list[str] = []
    evidence: dict[str, Any] = {}
    validate_memory_alignment(failures, evidence)
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
