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

from runtime.entrypoints.generic_campaign_turn import build_generic_campaign_turn_packet_from_config_path  # noqa: E402


CHECKPOINT_ID = "GENERIC-CAMPAIGN-MANUAL-WORK-SEMANTICS-001"
GENERATED_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
RESULT_PATH = GENERATED_DIR / "result.json"
REPORT_PATH = GENERATED_DIR / "report.md"
TMP_DIR = ROOT / ".tmp" / CHECKPOINT_ID
CONFIG_PATH = ROOT / "runtime" / "campaigns" / "examples" / "synthetic-b2b-saas-operations.json"

ROUTESIGNAL_PLAYBOOK_ID = "ROUTESIGNAL-DIAGNOSTIC-PLAYBOOK-001"
B2B_CAMPAIGN_ID = "synthetic-b2b-saas-operations"
FORBIDDEN_GENERIC_TERMS = ["RouteSignal", "Northstar", "Starter", "Growth", "$29", "$59"]
SAFETY_KEYS = [
    "provider_calls_made",
    "local_llm_calls_made",
    "sends_email",
    "creates_calendar_event",
    "writes_crm",
    "opens_prod_102",
]


def assert_condition(failures: list[str], condition: bool, message: str) -> None:
    if not condition:
        failures.append(message)


def normalize(text: Any) -> str:
    return re.sub(r"\s+", " ", str(text or "").strip().lower())


def write_evidence(result: dict[str, Any], report: str) -> None:
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    REPORT_PATH.write_text(report, encoding="utf-8")


def append_turn(state: dict[str, Any], packet: dict[str, Any]) -> None:
    state.setdefault("turns", []).append(
        {
            "transcript": packet.get("transcript", ""),
            "summary": packet.get("summary", {}),
            "continuity": packet.get("demo_session_continuity") or packet.get("conversation_continuity") or {},
            "conversation_memory": packet.get("demo_conversation_memory") or packet.get("conversation_memory") or {},
            "dialogue_manager": packet.get("dialogue_manager", {}),
            "dialogue_pragmatics": packet.get("dialogue_pragmatics", {}),
        }
    )


def memory(packet: dict[str, Any]) -> dict[str, Any]:
    return dict(packet.get("demo_conversation_memory") or packet.get("conversation_memory") or {})


def semantic_frame(packet: dict[str, Any]) -> dict[str, Any]:
    manager = packet.get("dialogue_manager") or {}
    selected = manager.get("selected_action") or {}
    frame = selected.get("contextual_buyer_semantics") or selected.get("semantic_frame") or {}
    if frame:
        return frame
    if selected.get("semantic"):
        return selected
    return manager.get("contextual_buyer_semantics") or {}


def final_response(packet: dict[str, Any]) -> str:
    return str((packet.get("summary") or {}).get("final_response") or (packet.get("packet") or {}).get("final_response") or "")


def tts_input_text(packet: dict[str, Any]) -> str:
    return str((packet.get("summary") or {}).get("tts_input_text") or (((packet.get("packet") or {}).get("tts_delivery") or {}).get("tts_input_text")) or "")


def snapshot(packet: dict[str, Any]) -> dict[str, Any]:
    frame = semantic_frame(packet)
    packet_body = packet.get("packet") or {}
    tts = packet_body.get("tts_delivery") or {}
    voice = packet_body.get("voice_delivery") or {}
    manager = packet.get("dialogue_manager") or {}
    lead = memory(packet).get("lead_followup_state") or {}
    return {
        "transcript": packet.get("transcript"),
        "campaign_id": packet.get("campaign_id"),
        "campaign_playbook_id": packet.get("campaign_playbook_id"),
        "semantic": frame.get("semantic"),
        "target_gap": frame.get("target_gap"),
        "playbook_id": frame.get("playbook_id"),
        "playbook_review_focus": frame.get("playbook_review_focus"),
        "confirmed_gaps": memory(packet).get("confirmed_gaps") or frame.get("confirmed_gaps") or [],
        "cleared_gaps": memory(packet).get("cleared_gaps") or frame.get("cleared_gaps") or [],
        "call_control": (packet.get("summary") or {}).get("call_control"),
        "final_response": final_response(packet),
        "tts_input_text": tts_input_text(packet),
        "lead_followup_state": lead,
        "audio_url": packet.get("audio_url"),
        "provider_agent_used": packet.get("provider_agent_used"),
        "durable_provider_agent_created": packet.get("durable_provider_agent_created"),
        "voice_cloning_used": packet.get("voice_cloning_used"),
        "provider_calls_made": bool(tts.get("provider_calls_made") or voice.get("provider_calls_made") or packet_body.get("api_calls_made")),
        "local_llm_calls_made": bool(manager.get("local_llm_calls_made") or packet_body.get("llm_used")),
        "sends_email": bool((lead.get("safety") or {}).get("sends_email")),
        "creates_calendar_event": bool((lead.get("safety") or {}).get("creates_calendar_event")),
        "writes_crm": bool((lead.get("safety") or {}).get("writes_crm")),
        "opens_prod_102": bool(packet.get("opens_prod_102") or manager.get("opens_prod_102")),
    }


def build_packet(transcript: str, state: dict[str, Any], session_id: str) -> dict[str, Any]:
    return build_generic_campaign_turn_packet_from_config_path(
        transcript=transcript,
        campaign_config_path=CONFIG_PATH,
        input_type="agent-open" if transcript == "__agent_open__" else "speech-final",
        session_id=session_id,
        session_state=state,
        private_out=TMP_DIR / session_id,
        live_tts=False,
        force_key_missing=True,
        timeout_seconds=8.0,
    )


def run_sequence(session_id: str, utterance: str) -> list[dict[str, Any]]:
    state: dict[str, Any] = {"turns": []}
    packets: list[dict[str, Any]] = []
    for transcript in ["__agent_open__", "yeah sure", utterance]:
        packet = build_packet(transcript, state, session_id)
        packets.append(packet)
        append_turn(state, packet)
    return packets


def assert_generic_packet(failures: list[str], packet: dict[str, Any], label: str) -> None:
    snap = snapshot(packet)
    assert_condition(failures, snap["campaign_id"] == B2B_CAMPAIGN_ID, f"{label}: campaign_id mismatch: {snap}")
    assert_condition(failures, snap["campaign_playbook_id"] != ROUTESIGNAL_PLAYBOOK_ID, f"{label}: generic packet resolved to RouteSignal: {snap}")
    assert_condition(failures, snap["playbook_id"] != ROUTESIGNAL_PLAYBOOK_ID, f"{label}: semantic playbook resolved to RouteSignal: {snap}")
    for key in SAFETY_KEYS:
        assert_condition(failures, snap.get(key) is False, f"{label}: {key} must be false: {snap}")
    assert_condition(failures, snap["provider_agent_used"] is False, f"{label}: provider agent must be false: {snap}")
    assert_condition(failures, snap["durable_provider_agent_created"] is False, f"{label}: durable provider agent must be false: {snap}")
    assert_condition(failures, snap["voice_cloning_used"] is False, f"{label}: voice cloning must be false: {snap}")
    assert_condition(failures, snap["audio_url"] in (None, ""), f"{label}: dry-run audio_url must be null/absent: {snap}")
    combined_text = f"{snap['final_response']} {snap['tts_input_text']}"
    leaked = [term for term in FORBIDDEN_GENERIC_TERMS if term.lower() in combined_text.lower()]
    assert_condition(failures, not leaked, f"{label}: forbidden generic text leaked {leaked}: {snap}")


def assert_manual_pain(failures: list[str], packet: dict[str, Any], label: str) -> None:
    snap = snapshot(packet)
    assert_condition(failures, snap["semantic"] == "pain_confirmed", f"{label}: expected pain_confirmed: {snap}")
    assert_condition(failures, snap["target_gap"] == "manual_work", f"{label}: expected manual_work target: {snap}")
    assert_condition(failures, "manual_work" in set(snap["confirmed_gaps"]), f"{label}: manual_work not confirmed: {snap}")
    assert_condition(failures, "manual_work" not in set(snap["cleared_gaps"]), f"{label}: manual_work was incorrectly cleared: {snap}")
    response = normalize(snap["final_response"])
    assert_condition(failures, "operations fit review" in response, f"{label}: response did not move toward operations fit review: {snap}")


def assert_manual_clear(failures: list[str], packet: dict[str, Any], label: str) -> None:
    snap = snapshot(packet)
    assert_condition(failures, snap["semantic"] in {"current_gap_clear", "no_pain_for_specific_gap"}, f"{label}: expected manual_work clear/no-pain: {snap}")
    assert_condition(failures, snap["target_gap"] == "manual_work", f"{label}: expected manual_work target: {snap}")
    assert_condition(failures, "manual_work" in set(snap["cleared_gaps"]), f"{label}: manual_work not cleared: {snap}")
    assert_condition(failures, "manual_work" not in set(snap["confirmed_gaps"]), f"{label}: manual_work was incorrectly confirmed: {snap}")
    response = normalize(snap["final_response"])
    assert_condition(failures, "integration risk" in response or "visibility gap" in response, f"{label}: remaining gap question missing: {snap}")


def validate_manual_work_cases(failures: list[str], evidence: dict[str, Any]) -> None:
    cases = {
        "manual_work_problem": ("manual work is a problem", assert_manual_pain),
        "manual_work_the_problem": ("manual work is the problem", assert_manual_pain),
        "manual_workflow_problem": ("manual workflow is a problem", assert_manual_pain),
        "manual_work_handled": ("manual work is handled", assert_manual_clear),
        "manual_work_fine": ("manual work is fine", assert_manual_clear),
        "manual_work_not_problem": ("manual work is not a problem", assert_manual_clear),
        "manual_process_handled": ("manual process is handled", assert_manual_clear),
    }
    evidence["manual_work_cases"] = {}
    for label, (utterance, assertion) in cases.items():
        packets = run_sequence(label, utterance)
        evidence["manual_work_cases"][label] = [snapshot(packet) for packet in packets]
        for index, packet in enumerate(packets, start=1):
            assert_generic_packet(failures, packet, f"{label}_turn{index}")
        assertion(failures, packets[-1], label)


def validate_non_manual_controls(failures: list[str], evidence: dict[str, Any]) -> None:
    cases = {
        "integration_problem": ("integration is a problem", "integration_risk"),
        "visibility_problem": ("visibility is a problem", "visibility_gap"),
    }
    evidence["non_manual_controls"] = {}
    for label, (utterance, expected_gap) in cases.items():
        packets = run_sequence(label, utterance)
        evidence["non_manual_controls"][label] = [snapshot(packet) for packet in packets]
        for index, packet in enumerate(packets, start=1):
            assert_generic_packet(failures, packet, f"{label}_turn{index}")
        snap = snapshot(packets[-1])
        assert_condition(failures, snap["semantic"] == "pain_confirmed", f"{label}: expected pain_confirmed: {snap}")
        assert_condition(failures, snap["target_gap"] == expected_gap, f"{label}: expected {expected_gap}: {snap}")
        assert_condition(failures, snap["target_gap"] != "manual_work", f"{label}: incorrectly selected manual_work: {snap}")


def validate_routesignal_preservation(failures: list[str], evidence: dict[str, Any]) -> None:
    from scripts.run_live_demo_001_agent_voice_call import (  # noqa: E402
        DEFAULT_CAMPAIGN_ID,
        DEFAULT_CASES_PATH,
        DEFAULT_STAGE,
        build_turn_packet,
    )

    state: dict[str, Any] = {"turns": []}
    packets: list[dict[str, Any]] = []
    for transcript in ["__agent_open__", "yeah sure", "manual tracking is fine"]:
        packet = build_turn_packet(
            transcript=transcript,
            campaign_id=DEFAULT_CAMPAIGN_ID,
            stage=DEFAULT_STAGE,
            input_type="agent-open" if transcript == "__agent_open__" else "speech-final",
            silence_count=0,
            cases_path=DEFAULT_CASES_PATH,
            private_out=TMP_DIR / "routesignal",
            live_tts=False,
            force_key_missing=True,
            timeout_seconds=8.0,
            session_id="manual-work-routesignal-preservation",
            session_state=state,
            asr_confidence=0.94,
            voice_turn_state="listening",
        )
        packets.append(packet)
        append_turn(state, packet)

    evidence["routesignal_preservation"] = [snapshot(packet) for packet in packets]
    final = evidence["routesignal_preservation"][-1]
    assert_condition(failures, final["playbook_id"] == ROUTESIGNAL_PLAYBOOK_ID, f"RouteSignal playbook changed: {final}")
    assert_condition(failures, final["semantic"] == "current_gap_clear", f"RouteSignal manual tracking semantic changed: {final}")
    assert_condition(failures, final["target_gap"] == "manual_tracking", f"RouteSignal manual_tracking target changed: {final}")


def render_report(result: dict[str, Any]) -> str:
    lines = [
        "# GENERIC-CAMPAIGN-MANUAL-WORK-SEMANTICS-001",
        "",
        f"Status: {result['status']}",
        f"Failure count: {len(result.get('failures') or [])}",
        "",
        "## Scope",
        "",
        "- Generic B2B SaaS `manual_work` positive and negative semantics through config-path runtime.",
        "- Non-manual B2B controls for integration and visibility.",
        "- RouteSignal manual_tracking preservation.",
        "",
        "## Failures",
        "",
    ]
    failures = result.get("failures") or []
    if failures:
        lines.extend(f"- {failure}" for failure in failures)
    else:
        lines.append("- None")
    return "\n".join(lines) + "\n"


def main() -> int:
    failures: list[str] = []
    evidence: dict[str, Any] = {}
    validate_manual_work_cases(failures, evidence)
    validate_non_manual_controls(failures, evidence)
    validate_routesignal_preservation(failures, evidence)

    result = {
        "checkpoint_id": CHECKPOINT_ID,
        "status": "pass" if not failures else "fail",
        "failures": failures,
        "evidence": evidence,
        "safety_assertions": {key: False for key in SAFETY_KEYS},
        "provider_calls_made": False,
        "local_llm_calls_made": False,
        "sends_email": False,
        "creates_calendar_event": False,
        "writes_crm": False,
        "opens_prod_102": False,
        "uses_provider_calls": False,
        "uses_live_tts": False,
        "uses_real_customer_data": False,
        "uses_private_transcripts": False,
        "uses_generated_audio": False,
        "runtime_behavior_changed": True,
    }
    write_evidence(result, render_report(result))
    if failures:
        print(json.dumps(result, indent=2, sort_keys=True))
        return 1
    print(f"{CHECKPOINT_ID}: pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
