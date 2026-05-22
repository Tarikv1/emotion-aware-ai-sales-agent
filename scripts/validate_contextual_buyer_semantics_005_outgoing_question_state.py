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


CHECKPOINT_ID = "CONTEXTUAL-BUYER-SEMANTICS-005-outgoing-question-state"
GENERATED_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
RESULT_PATH = GENERATED_DIR / "result.json"
REPORT_PATH = GENERATED_DIR / "report.md"
TMP_DIR = ROOT / ".tmp" / CHECKPOINT_ID
CORE_GAPS = {"callbacks", "manual_tracking", "handoffs"}


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


def assert_text_mentions_core_fit_check(failures: list[str], packet: dict[str, Any], label: str) -> None:
    final_text = normalize(response(packet))
    tts_text = normalize(tts_input_text(packet))
    for text_label, text in [("final_response", final_text), ("tts_input_text", tts_text)]:
        assert_condition(failures, "callbacks" in text, f"{label}: {text_label} should mention callbacks: {snapshot(packet)}")
        assert_condition(failures, "manual tracking" in text, f"{label}: {text_label} should mention manual tracking: {snapshot(packet)}")
        assert_condition(failures, "handoffs" in text, f"{label}: {text_label} should mention handoffs: {snapshot(packet)}")


def assert_spoken_contains(failures: list[str], packet: dict[str, Any], fragments: set[str], label: str) -> None:
    final_text = normalize(response(packet))
    tts_text = normalize(tts_input_text(packet))
    assert_condition(failures, any(fragment in final_text for fragment in fragments), f"{label}: final_response should contain one of {sorted(fragments)}: {response(packet)}")
    assert_condition(failures, any(fragment in tts_text for fragment in fragments), f"{label}: tts_input_text should contain one of {sorted(fragments)}: {tts_input_text(packet)}")


def assert_contains_all(failures: list[str], values: set[str], expected: set[str], label: str, packet: dict[str, Any]) -> None:
    missing = expected - values
    assert_condition(failures, not missing, f"{label}: missing {sorted(missing)} from {sorted(values)}: {snapshot(packet)}")


def assert_no_provider_or_llm(failures: list[str], packet: dict[str, Any], label: str) -> None:
    assert_condition(failures, not bool((packet.get("summary") or {}).get("tts_provider_calls_made")), f"{label}: provider calls must stay false: {snapshot(packet)}")
    assert_condition(failures, not bool((packet.get("dialogue_manager") or {}).get("local_llm_calls_made")), f"{label}: local LLM calls must stay false: {snapshot(packet)}")


def assert_outgoing_scope(failures: list[str], packet: dict[str, Any], label: str) -> None:
    mem = memory(packet)
    assert_condition(failures, mem.get("outgoing_question_type") == "multi_gap_diagnostic", f"{label}: outgoing_question_type should be multi_gap_diagnostic: {snapshot(packet)}")
    assert_condition(failures, mem.get("outgoing_active_gap_scope") == "multi_gap", f"{label}: outgoing_active_gap_scope should be multi_gap: {snapshot(packet)}")
    assert_contains_all(failures, set(str(item) for item in (mem.get("outgoing_candidate_gaps") or [])), CORE_GAPS, f"{label} outgoing_candidate_gaps", packet)
    assert_contains_all(failures, set(str(item) for item in (mem.get("candidate_gaps") or [])), CORE_GAPS, f"{label} candidate_gaps", packet)


def assert_memory_matches_semantic(failures: list[str], packet: dict[str, Any], label: str) -> None:
    frame = semantic_frame(packet)
    mem = memory(packet)
    semantic = str(frame.get("semantic") or "")
    if frame.get("applied"):
        assert_condition(failures, mem.get("last_customer_intent") == semantic, f"{label}: memory intent should match semantic: {snapshot(packet)}")
        assert_condition(failures, manager_source(packet) == "contextual_buyer_semantics", f"{label}: applied semantic should own manager source: {snapshot(packet)}")
    if semantic == "current_gap_clear":
        assert_condition(failures, mem.get("callback_semantic") is None, f"{label}: current clear should not keep callback workflow memory: {snapshot(packet)}")
    if semantic == "mixed_gap_response" and (frame.get("primary_gap") or frame.get("target_gap")) == "callbacks":
        assert_condition(failures, mem.get("selected_gap") == "callbacks", f"{label}: mixed callback primary should own selected_gap: {snapshot(packet)}")


def validate_outgoing_question_state(failures: list[str], evidence: dict[str, Any]) -> None:
    scenarios = {
        "scenario_a_permission_outgoing_scope": ["__agent_open__", "yeah sure"],
        "scenario_b_outgoing_drives_all_clear": ["__agent_open__", "yeah sure", "all good"],
        "scenario_c_outgoing_drives_specific_clear": ["__agent_open__", "yeah sure", "manual tracking is fine"],
        "scenario_d_outgoing_drives_mixed_response": ["__agent_open__", "yeah sure", "manual tracking is fine but callbacks get missed"],
    }
    packets_by_scenario = {label: run_sequence(transcripts, session_id=label) for label, transcripts in scenarios.items()}
    for label, packets in packets_by_scenario.items():
        evidence[label] = [snapshot(packet) for packet in packets]
        for index, packet in enumerate(packets, start=1):
            assert_no_provider_or_llm(failures, packet, f"{label}_turn{index}")
            assert_memory_matches_semantic(failures, packet, f"{label}_turn{index}")

    scenario_a_turn2 = packets_by_scenario["scenario_a_permission_outgoing_scope"][1]
    assert_semantic(failures, scenario_a_turn2, label="scenario_a_turn2", expected="permission_acknowledgement")
    assert_condition(failures, memory(scenario_a_turn2).get("last_customer_intent") == "permission_acknowledgement", f"scenario_a_turn2: expected permission memory intent: {snapshot(scenario_a_turn2)}")
    assert_text_mentions_core_fit_check(failures, scenario_a_turn2, "scenario_a_turn2")
    assert_outgoing_scope(failures, scenario_a_turn2, "scenario_a_turn2")

    scenario_b_turn3 = packets_by_scenario["scenario_b_outgoing_drives_all_clear"][2]
    assert_semantic(failures, scenario_b_turn3, label="scenario_b_turn3", expected="multi_gap_clear")
    assert_contains_all(failures, set(str(item) for item in (semantic_frame(scenario_b_turn3).get("candidate_gaps") or [])), CORE_GAPS, "scenario_b_turn3 semantic candidate_gaps", scenario_b_turn3)
    assert_contains_all(failures, gap_set(scenario_b_turn3, "cleared_gaps"), CORE_GAPS, "scenario_b_turn3 cleared_gaps", scenario_b_turn3)
    assert_condition(failures, bool(memory(scenario_b_turn3).get("final_save_pending")), f"scenario_b_turn3: expected final_save_pending after broad no-pain: {snapshot(scenario_b_turn3)}")

    scenario_c_turn3 = packets_by_scenario["scenario_c_outgoing_drives_specific_clear"][2]
    assert_semantic(failures, scenario_c_turn3, label="scenario_c_turn3", expected="current_gap_clear", target_gap="manual_tracking")
    assert_contains_all(failures, gap_set(scenario_c_turn3, "cleared_gaps"), {"manual_tracking"}, "scenario_c_turn3 cleared_gaps", scenario_c_turn3)
    assert_spoken_contains(failures, scenario_c_turn3, {"callbacks", "handoffs"}, "scenario_c_turn3")

    scenario_d_turn3 = packets_by_scenario["scenario_d_outgoing_drives_mixed_response"][2]
    assert_semantic(failures, scenario_d_turn3, label="scenario_d_turn3", expected="mixed_gap_response", target_gap="callbacks")
    assert_contains_all(failures, gap_set(scenario_d_turn3, "cleared_gaps"), {"manual_tracking"}, "scenario_d_turn3 cleared_gaps", scenario_d_turn3)
    assert_contains_all(failures, gap_set(scenario_d_turn3, "confirmed_gaps"), {"callbacks"}, "scenario_d_turn3 confirmed_gaps", scenario_d_turn3)
    assert_condition(failures, semantic_frame(scenario_d_turn3).get("primary_gap") == "callbacks", f"scenario_d_turn3: primary_gap should be callbacks: {snapshot(scenario_d_turn3)}")
    assert_spoken_contains(failures, scenario_d_turn3, {"missed callbacks", "workflow review", "what time works"}, "scenario_d_turn3")


def render_report(payload: dict[str, Any]) -> str:
    lines = [
        "# CONTEXTUAL-BUYER-SEMANTICS-005 Outgoing Question State",
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
            "- Replays permission acknowledgement into the standard three-gap diagnostic from empty state.",
            "- Enforces outgoing_question_type, outgoing_active_gap_scope, and outgoing_candidate_gaps in memory.",
            "- Verifies the next buyer turn uses the outgoing diagnostic scope for all-clear, specific-clear, and mixed responses.",
            "- Checks final_response and tts_input_text for matching diagnostic or appointment focus.",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    failures: list[str] = []
    evidence: dict[str, Any] = {}
    validate_outgoing_question_state(failures, evidence)
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
