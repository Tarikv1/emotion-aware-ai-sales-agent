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


CHECKPOINT_ID = "CONTEXTUAL-BUYER-SEMANTICS-004-semantic-memory-invariants"
GENERATED_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
RESULT_PATH = GENERATED_DIR / "result.json"
REPORT_PATH = GENERATED_DIR / "report.md"
TMP_DIR = ROOT / ".tmp" / CHECKPOINT_ID
LEGACY_RAW_INTENTS = {"callback_workflow_gap", "manual_tracking_objection"}


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


def gap_set(packet: dict[str, Any], key: str) -> set[str]:
    return set(str(item) for item in (memory(packet).get(key) or []))


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
        "selected_action": (manager.get("selected_action") or {}),
        "memory": memory(packet),
        "continuity": packet.get("demo_session_continuity") or {},
        "provider_calls_made": bool((packet.get("summary") or {}).get("tts_provider_calls_made")),
        "local_llm_calls_made": bool(manager.get("local_llm_calls_made")),
    }


def assert_semantic(
    failures: list[str],
    packet: dict[str, Any],
    *,
    label: str,
    expected: str,
    target_gap: str | None = None,
) -> None:
    frame = semantic_frame(packet)
    actual = str(frame.get("semantic") or "")
    assert_condition(failures, bool(frame), f"{label}: semantic frame must be exposed: {snapshot(packet)}")
    assert_condition(failures, actual == expected, f"{label}: expected semantic `{expected}`, got `{actual}`: {snapshot(packet)}")
    if target_gap is not None:
        assert_condition(failures, frame.get("target_gap") == target_gap, f"{label}: expected target_gap `{target_gap}`: {snapshot(packet)}")
    if frame.get("applied"):
        assert_condition(failures, manager_source(packet) == "contextual_buyer_semantics", f"{label}: applied semantic should own manager source: {snapshot(packet)}")


def assert_spoken_contains(failures: list[str], packet: dict[str, Any], fragments: set[str], label: str) -> None:
    final_text = normalize(response(packet))
    tts_text = normalize(tts_input_text(packet))
    assert_condition(failures, any(fragment in final_text for fragment in fragments), f"{label}: final_response should contain one of {sorted(fragments)}: {response(packet)}")
    assert_condition(failures, any(fragment in tts_text for fragment in fragments), f"{label}: tts_input_text should contain one of {sorted(fragments)}: {tts_input_text(packet)}")


def assert_contains_all(failures: list[str], values: set[str], expected: set[str], label: str, packet: dict[str, Any]) -> None:
    missing = expected - values
    assert_condition(failures, not missing, f"{label}: missing {sorted(missing)} from {sorted(values)}: {snapshot(packet)}")


def assert_semantic_owned_memory(failures: list[str], packet: dict[str, Any], label: str) -> None:
    frame = semantic_frame(packet)
    if not frame.get("applied"):
        return
    mem = memory(packet)
    semantic = str(frame.get("semantic") or "")
    target_gap = frame.get("target_gap")
    primary_gap = frame.get("primary_gap") or target_gap
    callback_semantic = mem.get("callback_semantic")
    selected_gap = mem.get("selected_gap")
    active_topic = mem.get("active_topic")

    assert_condition(failures, not bool((packet.get("summary") or {}).get("tts_provider_calls_made")), f"{label}: provider calls must stay false: {snapshot(packet)}")
    assert_condition(failures, not bool((packet.get("dialogue_manager") or {}).get("local_llm_calls_made")), f"{label}: local LLM calls must stay false: {snapshot(packet)}")
    assert_condition(failures, mem.get("last_customer_intent") not in LEGACY_RAW_INTENTS, f"{label}: last_customer_intent must not be raw legacy intent: {snapshot(packet)}")

    if semantic in {"mixed_gap_response", "pain_confirmed", "current_gap_clear", "multi_gap_clear"}:
        assert_condition(failures, mem.get("last_customer_intent") == semantic, f"{label}: last_customer_intent should equal contextual semantic `{semantic}`: {snapshot(packet)}")

    if semantic == "mixed_gap_response":
        assert_condition(failures, selected_gap == primary_gap, f"{label}: mixed selected_gap should be primary/target gap: {snapshot(packet)}")
        assert_condition(failures, active_topic in {primary_gap, "timing"}, f"{label}: active_topic should not contradict mixed target: {snapshot(packet)}")
        if primary_gap != "callbacks":
            assert_condition(failures, callback_semantic is None, f"{label}: mixed non-callback primary must clear callback_semantic: {snapshot(packet)}")
        else:
            assert_condition(failures, callback_semantic in {None, "callback_workflow_gap"}, f"{label}: callback primary may keep callback workflow semantic only: {snapshot(packet)}")

    if semantic == "pain_confirmed":
        assert_condition(failures, selected_gap == primary_gap, f"{label}: pain selected_gap should be primary/target gap: {snapshot(packet)}")
        assert_condition(failures, active_topic in {primary_gap, "timing"}, f"{label}: active_topic should not contradict pain target: {snapshot(packet)}")
        if primary_gap != "callbacks":
            assert_condition(failures, callback_semantic is None, f"{label}: non-callback pain must clear callback_semantic: {snapshot(packet)}")
        else:
            assert_condition(failures, callback_semantic in {None, "callback_workflow_gap"}, f"{label}: callback pain may keep callback workflow semantic only: {snapshot(packet)}")

    if semantic == "current_gap_clear":
        assert_condition(failures, callback_semantic is None, f"{label}: current clear must clear callback_semantic: {snapshot(packet)}")
        assert_condition(failures, target_gap in gap_set(packet, "cleared_gaps"), f"{label}: current clear should store cleared target: {snapshot(packet)}")
        assert_condition(failures, target_gap in gap_set(packet, "no_pain_topics"), f"{label}: current clear should store no-pain target: {snapshot(packet)}")

    if semantic == "multi_gap_clear":
        assert_condition(failures, callback_semantic is None, f"{label}: multi-gap clear must clear callback_semantic: {snapshot(packet)}")
        assert_condition(failures, selected_gap is None, f"{label}: multi-gap clear must not keep selected_gap: {snapshot(packet)}")
        assert_condition(failures, bool(mem.get("final_save_pending")), f"{label}: multi-gap clear should keep final_save_pending when response asks final save: {snapshot(packet)}")


def validate_semantic_memory_invariants(failures: list[str], evidence: dict[str, Any]) -> None:
    scenarios = {
        "scenario_a_mixed_callbacks_clear_handoffs_pain": ["__agent_open__", "yeah sure", "callbacks are fine but handoffs get messy"],
        "scenario_b_mixed_handoffs_clear_callbacks_pain": ["__agent_open__", "yeah sure", "handoffs are fine but callbacks get missed"],
        "scenario_c_handoffs_pain": ["__agent_open__", "yeah sure", "handoffs get messy sometimes"],
        "scenario_d_callbacks_pain": ["__agent_open__", "yeah sure", "missed callbacks happen sometimes"],
        "scenario_e_broad_no_issue": ["__agent_open__", "yeah sure", "no issue"],
        "scenario_f_callback_clear": ["__agent_open__", "yeah sure", "callbacks are fine"],
    }
    packets_by_scenario = {label: run_sequence(transcripts, session_id=label) for label, transcripts in scenarios.items()}
    for label, packets in packets_by_scenario.items():
        evidence[label] = [snapshot(packet) for packet in packets]
        for index, packet in enumerate(packets, start=1):
            assert_semantic_owned_memory(failures, packet, f"{label}_turn{index}")

    scenario_a = packets_by_scenario["scenario_a_mixed_callbacks_clear_handoffs_pain"][2]
    assert_semantic(failures, scenario_a, label="scenario_a_turn3", expected="mixed_gap_response", target_gap="handoffs")
    assert_condition(failures, semantic_frame(scenario_a).get("primary_gap") == "handoffs", f"scenario_a_turn3: primary_gap should be handoffs: {snapshot(scenario_a)}")
    assert_contains_all(failures, gap_set(scenario_a, "cleared_gaps"), {"callbacks"}, "scenario_a_turn3", scenario_a)
    assert_contains_all(failures, gap_set(scenario_a, "confirmed_gaps"), {"handoffs"}, "scenario_a_turn3", scenario_a)
    assert_spoken_contains(failures, scenario_a, {"handoffs", "workflow review", "what time works"}, "scenario_a_turn3")

    scenario_b = packets_by_scenario["scenario_b_mixed_handoffs_clear_callbacks_pain"][2]
    assert_semantic(failures, scenario_b, label="scenario_b_turn3", expected="mixed_gap_response", target_gap="callbacks")
    assert_condition(failures, semantic_frame(scenario_b).get("primary_gap") == "callbacks", f"scenario_b_turn3: primary_gap should be callbacks: {snapshot(scenario_b)}")
    assert_contains_all(failures, gap_set(scenario_b, "cleared_gaps"), {"handoffs"}, "scenario_b_turn3", scenario_b)
    assert_contains_all(failures, gap_set(scenario_b, "confirmed_gaps"), {"callbacks"}, "scenario_b_turn3", scenario_b)
    assert_spoken_contains(failures, scenario_b, {"missed callbacks", "workflow review", "what time works"}, "scenario_b_turn3")

    scenario_c = packets_by_scenario["scenario_c_handoffs_pain"][2]
    assert_semantic(failures, scenario_c, label="scenario_c_turn3", expected="pain_confirmed", target_gap="handoffs")
    assert_contains_all(failures, gap_set(scenario_c, "confirmed_gaps"), {"handoffs"}, "scenario_c_turn3", scenario_c)
    assert_spoken_contains(failures, scenario_c, {"handoffs", "workflow review", "what time works"}, "scenario_c_turn3")

    scenario_d = packets_by_scenario["scenario_d_callbacks_pain"][2]
    assert_semantic(failures, scenario_d, label="scenario_d_turn3", expected="pain_confirmed", target_gap="callbacks")
    assert_contains_all(failures, gap_set(scenario_d, "confirmed_gaps"), {"callbacks"}, "scenario_d_turn3", scenario_d)
    assert_spoken_contains(failures, scenario_d, {"missed callbacks", "workflow review", "what time works"}, "scenario_d_turn3")

    scenario_e = packets_by_scenario["scenario_e_broad_no_issue"][2]
    assert_semantic(failures, scenario_e, label="scenario_e_turn3", expected="multi_gap_clear")
    assert_contains_all(failures, gap_set(scenario_e, "cleared_gaps"), {"callbacks", "manual_tracking", "handoffs"}, "scenario_e_turn3", scenario_e)

    scenario_f = packets_by_scenario["scenario_f_callback_clear"][2]
    assert_semantic(failures, scenario_f, label="scenario_f_turn3", expected="current_gap_clear", target_gap="callbacks")
    assert_contains_all(failures, gap_set(scenario_f, "cleared_gaps"), {"callbacks"}, "scenario_f_turn3", scenario_f)
    assert_spoken_contains(failures, scenario_f, {"manual tracking", "handoffs"}, "scenario_f_turn3")


def render_report(payload: dict[str, Any]) -> str:
    lines = [
        "# CONTEXTUAL-BUYER-SEMANTICS-004 Semantic Memory Invariants",
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
            "- Replays mixed, pain, multi-gap-clear, and specific-clear turns from empty state.",
            "- Enforces that applied contextual semantics own memory intent, selected gap, callback semantic, and active topic.",
            "- Checks final_response and tts_input_text for the same semantic focus.",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    failures: list[str] = []
    evidence: dict[str, Any] = {}
    validate_semantic_memory_invariants(failures, evidence)
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
