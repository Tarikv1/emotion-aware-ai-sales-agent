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

try:
    from runtime.core import sales_diagnostic_playbook as diagnostic_playbook  # noqa: E402
except Exception as exc:  # pragma: no cover - exercised by red validation before module exists
    diagnostic_playbook = None
    PLAYBOOK_IMPORT_ERROR = repr(exc)
else:
    PLAYBOOK_IMPORT_ERROR = ""

from scripts.run_live_demo_001_agent_voice_call import (  # noqa: E402
    DEFAULT_CAMPAIGN_ID,
    DEFAULT_CASES_PATH,
    DEFAULT_STAGE,
    build_turn_packet,
)


CHECKPOINT_ID = "CONTEXTUAL-BUYER-SEMANTICS-010-diagnostic-playbook"
GENERATED_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
RESULT_PATH = GENERATED_DIR / "result.json"
REPORT_PATH = GENERATED_DIR / "report.md"
TMP_DIR = ROOT / ".tmp" / CHECKPOINT_ID
PLAYBOOK_ID = "ROUTESIGNAL-DIAGNOSTIC-PLAYBOOK-001"
REQUIRED_GAPS = {
    "callbacks",
    "manual_tracking",
    "handoffs",
    "routing",
    "reminders",
    "duplicates",
    "visibility",
    "right_person",
}
REQUIRED_GAP_FIELDS = {
    "definition",
    "causal_story",
    "evidence_positive",
    "evidence_negative",
    "diagnostic_questions",
    "value_bridge",
    "review_focus",
}


def normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9$@.*]+", " ", str(text).lower()).strip()


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


def selected_action(packet: dict[str, Any]) -> dict[str, Any]:
    return dict(((packet.get("dialogue_manager") or {}).get("selected_action") or {}))


def memory(packet: dict[str, Any]) -> dict[str, Any]:
    return dict(packet.get("demo_conversation_memory") or packet.get("conversation_memory") or {})


def call_control(packet: dict[str, Any]) -> str:
    return str((packet.get("summary") or {}).get("call_control") or "")


def snapshot(packet: dict[str, Any]) -> dict[str, Any]:
    manager = packet.get("dialogue_manager") or {}
    return {
        "turn": packet.get("session_turn_index"),
        "transcript": packet.get("transcript"),
        "response": response(packet),
        "tts_input_text": tts_input_text(packet),
        "call_control": call_control(packet),
        "semantic_frame": semantic_frame(packet),
        "selected_action": selected_action(packet),
        "memory": memory(packet),
        "provider_calls_made": bool((packet.get("summary") or {}).get("tts_provider_calls_made")),
        "local_llm_calls_made": bool(manager.get("local_llm_calls_made")),
        "opens_prod_102": bool(manager.get("opens_prod_102")),
    }


def playbook_trace(packet: dict[str, Any]) -> dict[str, Any]:
    frame = semantic_frame(packet)
    mem = memory(packet)
    trace = dict(frame.get("playbook") or mem.get("playbook") or {})
    for key in [
        "playbook_id",
        "playbook_gap",
        "playbook_next_gap",
        "playbook_review_focus",
        "playbook_supported_gap_ids",
    ]:
        value = frame.get(key)
        if value is None:
            value = mem.get(key)
        if value is not None:
            trace[key] = value
    return trace


def assert_spoken_contains(failures: list[str], packet: dict[str, Any], fragments: set[str], label: str) -> None:
    final_text = normalize(response(packet))
    tts_text = normalize(tts_input_text(packet))
    assert_condition(failures, any(fragment in final_text for fragment in fragments), f"{label}: final_response should contain one of {sorted(fragments)}: {snapshot(packet)}")
    assert_condition(failures, any(fragment in tts_text for fragment in fragments), f"{label}: tts_input_text should contain one of {sorted(fragments)}: {snapshot(packet)}")


def assert_no_external_side_effects(failures: list[str], packet: dict[str, Any], label: str) -> None:
    manager = packet.get("dialogue_manager") or {}
    assert_condition(failures, not bool((packet.get("summary") or {}).get("tts_provider_calls_made")), f"{label}: provider calls must stay false: {snapshot(packet)}")
    assert_condition(failures, not bool(manager.get("local_llm_calls_made")), f"{label}: local LLM calls must stay false: {snapshot(packet)}")
    assert_condition(failures, not bool(manager.get("opens_prod_102")), f"{label}: PROD-102 must remain closed: {snapshot(packet)}")
    for state_key in ["send_info_state", "lead_followup_state", "handoff_target_state"]:
        safety = (memory(packet).get(state_key) or {}).get("safety") or {}
        for key in ["provider_calls_made", "local_llm_calls_made", "sends_email", "creates_calendar_event", "writes_crm", "stores_private_contact_in_public_evidence"]:
            if key in safety:
                assert_condition(failures, safety.get(key) is False, f"{label}: {state_key}.safety.{key} must be false: {snapshot(packet)}")


def assert_semantic(failures: list[str], packet: dict[str, Any], *, label: str, expected: str | set[str]) -> None:
    expected_set = {expected} if isinstance(expected, str) else set(expected)
    actual = str(semantic_frame(packet).get("semantic") or "")
    assert_condition(failures, bool(semantic_frame(packet)), f"{label}: semantic frame must be exposed: {snapshot(packet)}")
    assert_condition(failures, actual in expected_set, f"{label}: expected semantic in {sorted(expected_set)}, got `{actual}`: {snapshot(packet)}")


def assert_playbook_trace(failures: list[str], packet: dict[str, Any], label: str, *, expected_gap: str | None = None) -> None:
    trace = playbook_trace(packet)
    assert_condition(failures, trace.get("playbook_id") == PLAYBOOK_ID, f"{label}: playbook metadata must be exposed in semantic frame or memory: {snapshot(packet)}")
    supported = set(str(item) for item in trace.get("playbook_supported_gap_ids") or [])
    assert_condition(failures, REQUIRED_GAPS.issubset(supported), f"{label}: playbook trace should expose supported gap ids: {snapshot(packet)}")
    if expected_gap:
        assert_condition(failures, trace.get("playbook_gap") == expected_gap or trace.get("playbook_review_focus"), f"{label}: playbook should expose gap/review focus for {expected_gap}: {snapshot(packet)}")


def validate_playbook_contract(failures: list[str], evidence: dict[str, Any]) -> None:
    if diagnostic_playbook is None:
        failures.append(f"playbook module import failed: {PLAYBOOK_IMPORT_ERROR}")
        evidence["playbook_import_error"] = PLAYBOOK_IMPORT_ERROR
        return
    playbook = getattr(diagnostic_playbook, "PLAYBOOK", None)
    evidence["playbook_contract"] = {
        "playbook_id": (playbook or {}).get("playbook_id") if isinstance(playbook, dict) else None,
        "schema_version": (playbook or {}).get("schema_version") if isinstance(playbook, dict) else None,
        "gap_ids": sorted(((playbook or {}).get("gaps") or {}).keys()) if isinstance(playbook, dict) else [],
    }
    assert_condition(failures, isinstance(playbook, dict), "scenario_a: PLAYBOOK must be a dict")
    assert_condition(failures, (playbook or {}).get("playbook_id") == PLAYBOOK_ID, f"scenario_a: playbook_id must be {PLAYBOOK_ID}")
    assert_condition(failures, (playbook or {}).get("schema_version") == 1, "scenario_a: playbook schema_version must be 1")
    gaps = (playbook or {}).get("gaps") or {}
    assert_condition(failures, REQUIRED_GAPS.issubset(set(gaps)), f"scenario_a: missing required gaps {sorted(REQUIRED_GAPS - set(gaps))}")
    for gap_id in REQUIRED_GAPS:
        gap = gaps.get(gap_id) or {}
        for field in REQUIRED_GAP_FIELDS:
            value = gap.get(field)
            assert_condition(failures, bool(value), f"scenario_a: {gap_id}.{field} must be populated")
        assert_condition(failures, isinstance(gap.get("evidence_positive"), list), f"scenario_a: {gap_id}.evidence_positive must be a list")
        assert_condition(failures, isinstance(gap.get("evidence_negative"), list), f"scenario_a: {gap_id}.evidence_negative must be a list")
        assert_condition(failures, isinstance(gap.get("diagnostic_questions"), list), f"scenario_a: {gap_id}.diagnostic_questions must be a list")
    policy = (playbook or {}).get("conversation_policy") or {}
    for key in [
        "after_current_gap_clear",
        "after_multi_gap_clear",
        "after_pain_confirmed",
        "after_wrong_person",
        "after_send_info",
    ]:
        assert_condition(failures, bool(policy.get(key)), f"scenario_a: conversation_policy.{key} must be populated")


def validate_dialogue_playbook_behavior(failures: list[str], evidence: dict[str, Any]) -> None:
    scenarios = {
        "scenario_b_callbacks_clear": ["__agent_open__", "yeah sure", "callbacks are fine"],
        "scenario_c_manual_clear": ["__agent_open__", "yeah sure", "manual tracking is fine"],
        "scenario_d_handoffs_clear": ["__agent_open__", "yeah sure", "handoffs are fine"],
        "scenario_e_multi_gap_ranking": ["__agent_open__", "yeah sure", "mostly missed callbacks but occasional manual tracking too"],
        "scenario_f_handoff_bridge": ["__agent_open__", "yeah sure", "handoffs get messy"],
        "scenario_g_product_routing": ["__agent_open__", "yeah sure", "lead routing is unclear"],
        "scenario_h_contact_routing": ["__agent_open__", "yeah sure", "operations handles lead routing"],
        "scenario_i_duplicates": ["__agent_open__", "yeah sure", "duplicate demo requests confuse ownership"],
        "scenario_j_visibility": ["__agent_open__", "yeah sure", "managers cannot see who followed up"],
        "scenario_k_all_core_clear": ["__agent_open__", "yeah sure", "callbacks are fine", "manual tracking is fine", "handoffs are fine"],
    }
    packets_by_scenario = {label: run_sequence(transcripts, session_id=label) for label, transcripts in scenarios.items()}
    for label, packets in packets_by_scenario.items():
        evidence[label] = [snapshot(packet) for packet in packets]
        for index, packet in enumerate(packets, start=1):
            assert_no_external_side_effects(failures, packet, f"{label}_turn{index}")

    b3 = packets_by_scenario["scenario_b_callbacks_clear"][2]
    assert_semantic(failures, b3, label="scenario_b_turn3", expected="current_gap_clear")
    assert_condition(failures, semantic_frame(b3).get("target_gap") == "callbacks", f"scenario_b_turn3: target_gap should be callbacks: {snapshot(b3)}")
    assert_condition(failures, "callbacks" in set(memory(b3).get("cleared_gaps") or []), f"scenario_b_turn3: callbacks should be cleared: {snapshot(b3)}")
    assert_spoken_contains(failures, b3, {"manual tracking", "handoffs"}, "scenario_b_turn3")
    assert_condition(failures, "do callbacks" not in normalize(response(b3)), f"scenario_b_turn3: should not ask callbacks again as diagnostic: {snapshot(b3)}")
    assert_playbook_trace(failures, b3, "scenario_b_turn3", expected_gap="callbacks")
    assert_condition(failures, playbook_trace(b3).get("playbook_next_gap") in {"manual_tracking", "handoffs"}, f"scenario_b_turn3: playbook_next_gap should choose a remaining gap: {snapshot(b3)}")

    c3 = packets_by_scenario["scenario_c_manual_clear"][2]
    assert_semantic(failures, c3, label="scenario_c_turn3", expected="current_gap_clear")
    assert_condition(failures, semantic_frame(c3).get("target_gap") == "manual_tracking", f"scenario_c_turn3: target_gap should be manual_tracking: {snapshot(c3)}")
    assert_condition(failures, "manual_tracking" in set(memory(c3).get("cleared_gaps") or []), f"scenario_c_turn3: manual_tracking should be cleared: {snapshot(c3)}")
    assert_spoken_contains(failures, c3, {"callbacks", "handoffs"}, "scenario_c_turn3")
    assert_playbook_trace(failures, c3, "scenario_c_turn3", expected_gap="manual_tracking")

    d3 = packets_by_scenario["scenario_d_handoffs_clear"][2]
    assert_semantic(failures, d3, label="scenario_d_turn3", expected="current_gap_clear")
    assert_condition(failures, semantic_frame(d3).get("target_gap") == "handoffs", f"scenario_d_turn3: target_gap should be handoffs: {snapshot(d3)}")
    assert_condition(failures, "handoffs" in set(memory(d3).get("cleared_gaps") or []), f"scenario_d_turn3: handoffs should be cleared: {snapshot(d3)}")
    assert_spoken_contains(failures, d3, {"callbacks", "manual tracking"}, "scenario_d_turn3")
    assert_playbook_trace(failures, d3, "scenario_d_turn3", expected_gap="handoffs")

    e3 = packets_by_scenario["scenario_e_multi_gap_ranking"][2]
    assert_semantic(failures, e3, label="scenario_e_turn3", expected={"pain_confirmed", "mixed_gap_response"})
    assert_condition(failures, semantic_frame(e3).get("primary_gap") == "callbacks", f"scenario_e_turn3: primary gap should be callbacks: {snapshot(e3)}")
    secondary = set(semantic_frame(e3).get("secondary_confirmed_gaps") or [])
    confirmed = set(memory(e3).get("confirmed_gaps") or [])
    assert_condition(failures, "manual_tracking" in secondary or "manual_tracking" in confirmed, f"scenario_e_turn3: manual_tracking should remain secondary evidence: {snapshot(e3)}")
    assert_condition(failures, playbook_trace(e3).get("playbook_review_focus") in {"missed callback reminders", "missed callback follow-up"}, f"scenario_e_turn3: review focus should be callback-specific: {snapshot(e3)}")
    assert_spoken_contains(failures, e3, {"missed callbacks", "callback reminders", "workflow review"}, "scenario_e_turn3")

    f3 = packets_by_scenario["scenario_f_handoff_bridge"][2]
    assert_semantic(failures, f3, label="scenario_f_turn3", expected="pain_confirmed")
    assert_condition(failures, semantic_frame(f3).get("target_gap") == "handoffs", f"scenario_f_turn3: target gap should be handoffs: {snapshot(f3)}")
    assert_condition(failures, "handoff" in normalize(str(playbook_trace(f3).get("playbook_review_focus") or "")), f"scenario_f_turn3: review focus should mention handoff: {snapshot(f3)}")
    assert_spoken_contains(failures, f3, {"handoff", "ownership", "workflow review"}, "scenario_f_turn3")

    g3 = packets_by_scenario["scenario_g_product_routing"][2]
    assert_semantic(failures, g3, label="scenario_g_turn3", expected={"pain_confirmed", "playbook_gap_confirmed"})
    assert_condition(failures, semantic_frame(g3).get("target_gap") == "routing", f"scenario_g_turn3: product routing should target routing: {snapshot(g3)}")
    assert_condition(failures, memory(g3).get("selected_gap") == "routing", f"scenario_g_turn3: selected_gap should be product routing: {snapshot(g3)}")
    assert_condition(failures, not memory(g3).get("handoff_target_state"), f"scenario_g_turn3: product routing should not open right-person handoff: {snapshot(g3)}")

    h3 = packets_by_scenario["scenario_h_contact_routing"][2]
    assert_semantic(failures, h3, label="scenario_h_turn3", expected={"department_named", "wrong_person_or_wrong_department"})
    assert_condition(failures, memory(h3).get("selected_gap") != "routing", f"scenario_h_turn3: contact routing must not become product routing: {snapshot(h3)}")
    assert_condition(failures, bool(memory(h3).get("handoff_target_state")), f"scenario_h_turn3: contact route should open handoff state: {snapshot(h3)}")
    assert_spoken_contains(failures, h3, {"operations", "contact", "right person", "workflow issue"}, "scenario_h_turn3")

    i3 = packets_by_scenario["scenario_i_duplicates"][2]
    assert_semantic(failures, i3, label="scenario_i_turn3", expected={"pain_confirmed", "playbook_gap_confirmed"})
    assert_condition(failures, semantic_frame(i3).get("target_gap") == "duplicates", f"scenario_i_turn3: duplicate pain should target duplicates: {snapshot(i3)}")
    assert_spoken_contains(failures, i3, {"duplicate", "ownership", "workflow review"}, "scenario_i_turn3")

    j3 = packets_by_scenario["scenario_j_visibility"][2]
    assert_semantic(failures, j3, label="scenario_j_turn3", expected={"pain_confirmed", "playbook_gap_confirmed"})
    assert_condition(failures, semantic_frame(j3).get("target_gap") == "visibility", f"scenario_j_turn3: visibility pain should target visibility: {snapshot(j3)}")
    assert_spoken_contains(failures, j3, {"visibility", "manager", "workflow review"}, "scenario_j_turn3")

    k5 = packets_by_scenario["scenario_k_all_core_clear"][4]
    cleared = set(memory(k5).get("cleared_gaps") or [])
    assert_condition(failures, {"callbacks", "manual_tracking", "handoffs"}.issubset(cleared), f"scenario_k_turn5: all core gaps should be cleared: {snapshot(k5)}")
    final_text = normalize(response(k5))
    assert_condition(failures, "workflow review" not in final_text, f"scenario_k_turn5: should not ask workflow review without pain: {snapshot(k5)}")
    assert_condition(failures, any(fragment in final_text for fragment in ["other follow up gap", "stop here", "i will stop", "should i stop"]), f"scenario_k_turn5: should ask one final save or close politely: {snapshot(k5)}")
    assert_condition(failures, "do callbacks" not in final_text and "do manual tracking" not in final_text and "do handoffs" not in final_text, f"scenario_k_turn5: should not repeat cleared diagnostics: {snapshot(k5)}")
    assert_playbook_trace(failures, k5, "scenario_k_turn5")


def render_report(payload: dict[str, Any]) -> str:
    lines = [
        "# CONTEXTUAL-BUYER-SEMANTICS-010 Diagnostic Playbook",
        "",
        f"- Passed: `{str(payload['passed']).lower()}`",
        f"- Failure count: `{payload['failure_count']}`",
        "- Provider calls made: `false`",
        "- Local LLM calls made: `false`",
        "- Sends email: `false`",
        "- Creates calendar event: `false`",
        "- Writes CRM: `false`",
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
            "- Verifies the playbook exposes callbacks, manual tracking, handoffs, routing, reminders, duplicates, visibility, and right-person handoff definitions.",
            "- Verifies clear-gap turns choose remaining diagnostics from playbook state instead of repeating the same gap.",
            "- Verifies mixed positive evidence is ranked, review focus is customer-facing, product routing stays separate from contact routing, and duplicates/visibility map to their own review focus.",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    failures: list[str] = []
    evidence: dict[str, Any] = {}
    validate_playbook_contract(failures, evidence)
    validate_dialogue_playbook_behavior(failures, evidence)
    payload = {
        "checkpoint_id": CHECKPOINT_ID,
        "passed": not failures,
        "failure_count": len(failures),
        "failures": failures,
        "provider_calls_made": False,
        "local_llm_calls_made": False,
        "sends_email": False,
        "creates_calendar_event": False,
        "writes_crm": False,
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
