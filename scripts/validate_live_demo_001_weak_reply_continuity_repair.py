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

from scripts import run_live_demo_001_agent_voice_call as demo  # noqa: E402
from scripts.validate_live_demo_002_conversation_stability import append_turn  # noqa: E402


CHECKPOINT_ID = "LIVE-DEMO-001-WEAK-REPLY-CONTINUITY-REPAIR"
GENERATED_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
RESULT_PATH = GENERATED_DIR / "result.json"
REPORT_PATH = GENERATED_DIR / "report.md"
TMP_DIR = ROOT / ".tmp" / CHECKPOINT_ID

ROUTESIGNAL_PLAYBOOK_ID = "ROUTESIGNAL-DIAGNOSTIC-PLAYBOOK-001"
INSURANCE_CONFIG = ROOT / "runtime" / "campaigns" / "examples" / "synthetic-insurance-review.json"
ROUTESIGNAL_TERMS = {
    "callback",
    "callbacks",
    "handoff",
    "handoffs",
    "manual tracking",
    "missed follow-up",
    "inbound demo",
    "demo follow-up",
}
INTERNAL_TERMS = {
    "anti-loop",
    "contextual_",
    "continue_with_session_policy",
    "dialogue_focus",
    "selected_action",
    "session policy",
    "reasoner",
    "route guard",
    "fallback reason",
}
FORBIDDEN_GENERIC_OUTPUT_TERMS = {
    "RouteSignal",
    "Northstar",
    "Starter",
    "Growth",
    "$29",
    "$59",
    "inbound-demo",
    "demo-follow-up",
    "missed callbacks",
    "missed-callbacks",
    "manual tracking",
    "manual-tracking",
    "messy handoffs",
    "messy-handoffs",
}
SAFETY_KEYS = [
    "provider_calls_made",
    "local_llm_calls_made",
    "sends_email",
    "creates_calendar_event",
    "writes_crm",
    "opens_prod_102",
]
WEAK_REPLIES = [
    "okay",
    "yeah",
    "tell me more",
    "what else should I know",
    "I don't know",
    "no",
    "hmm okay that is interesting",
    "why does that matter",
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


def final_response(packet: dict[str, Any]) -> str:
    return str((packet.get("summary") or {}).get("final_response") or (packet.get("packet") or {}).get("final_response") or "")


def tts_input_text(packet: dict[str, Any]) -> str:
    return str(
        (packet.get("summary") or {}).get("tts_input_text")
        or (((packet.get("packet") or {}).get("tts_delivery") or {}).get("tts_input_text"))
        or ""
    )


def conversation_memory(packet: dict[str, Any]) -> dict[str, Any]:
    return dict(packet.get("demo_conversation_memory") or packet.get("conversation_memory") or {})


def semantic_frame(packet: dict[str, Any]) -> dict[str, Any]:
    continuity = packet.get("demo_session_continuity") or packet.get("conversation_continuity") or {}
    frame = continuity.get("contextual_buyer_semantics") or {}
    if frame:
        return frame
    manager = packet.get("dialogue_manager") or {}
    selected = manager.get("selected_action") or {}
    frame = selected.get("contextual_buyer_semantics") or selected.get("semantic_frame") or {}
    if frame:
        return frame
    if selected.get("semantic"):
        return selected
    return manager.get("contextual_buyer_semantics") or {}


def snapshot(packet: dict[str, Any]) -> dict[str, Any]:
    frame = semantic_frame(packet)
    packet_body = packet.get("packet") or {}
    tts = packet_body.get("tts_delivery") or {}
    voice = packet_body.get("voice_delivery") or {}
    manager = packet.get("dialogue_manager") or {}
    lead = (conversation_memory(packet).get("lead_followup_state") or {})
    response = final_response(packet)
    return {
        "transcript": packet.get("transcript"),
        "campaign_id": packet.get("campaign_id"),
        "campaign_config_path": packet.get("campaign_config_path"),
        "campaign_playbook_id": packet.get("campaign_playbook_id"),
        "continuity_reason": (packet.get("demo_session_continuity") or {}).get("reason"),
        "continuity_action": (packet.get("demo_session_continuity") or {}).get("action_id"),
        "semantic": frame.get("semantic"),
        "target_gap": frame.get("target_gap"),
        "confirmed_gaps": conversation_memory(packet).get("confirmed_gaps") or frame.get("confirmed_gaps") or [],
        "cleared_gaps": conversation_memory(packet).get("cleared_gaps") or frame.get("cleared_gaps") or [],
        "call_control": (packet.get("summary") or {}).get("call_control"),
        "final_response": response,
        "question_count": response.count("?"),
        "tts_input_text": tts_input_text(packet),
        "mode": packet.get("mode"),
        "audio_url": packet.get("audio_url"),
        "provider_agent_used": packet.get("provider_agent_used"),
        "durable_provider_agent_created": packet.get("durable_provider_agent_created"),
        "voice_cloning_used": packet.get("voice_cloning_used"),
        "provider_calls_made": bool(
            packet.get("provider_calls_made") or tts.get("provider_calls_made") or voice.get("provider_calls_made") or packet_body.get("api_calls_made")
        ),
        "local_llm_calls_made": bool(packet.get("local_llm_calls_made") or manager.get("local_llm_calls_made") or packet_body.get("llm_used")),
        "sends_email": bool(packet.get("sends_email") or (lead.get("safety") or {}).get("sends_email")),
        "creates_calendar_event": bool(packet.get("creates_calendar_event") or (lead.get("safety") or {}).get("creates_calendar_event")),
        "writes_crm": bool(packet.get("writes_crm") or (lead.get("safety") or {}).get("writes_crm")),
        "opens_prod_102": bool(packet.get("opens_prod_102") or manager.get("opens_prod_102")),
    }


def assert_no_side_effects(failures: list[str], packet: dict[str, Any], label: str) -> None:
    snap = snapshot(packet)
    for key in SAFETY_KEYS:
        assert_condition(failures, snap.get(key) is False, f"{label}: {key} must be false: {snap}")
    assert_condition(failures, snap.get("provider_agent_used") is False, f"{label}: provider agent must be false: {snap}")
    assert_condition(failures, snap.get("durable_provider_agent_created") is False, f"{label}: durable provider agent must be false: {snap}")
    assert_condition(failures, snap.get("voice_cloning_used") is False, f"{label}: voice cloning must be false: {snap}")
    assert_condition(failures, snap.get("audio_url") in (None, ""), f"{label}: generated audio must not be required: {snap}")


def assert_no_route_signal_leakage(failures: list[str], packet: dict[str, Any], label: str) -> None:
    combined = f"{final_response(packet)} {tts_input_text(packet)}"
    leaked = [term for term in FORBIDDEN_GENERIC_OUTPUT_TERMS if term.lower() in combined.lower()]
    assert_condition(failures, not leaked, f"{label}: generic selected campaign leaked RouteSignal copy {leaked}: {combined}")


def build_routesignal_turn(transcript: str, state: dict[str, Any], *, session_id: str, input_type: str) -> dict[str, Any]:
    return demo.build_turn_packet(
        transcript=transcript,
        campaign_id=demo.DEFAULT_CAMPAIGN_ID,
        stage=demo.DEFAULT_STAGE,
        input_type=input_type,
        silence_count=0,
        cases_path=demo.DEFAULT_CASES_PATH,
        private_out=TMP_DIR / session_id,
        live_tts=False,
        force_key_missing=False,
        timeout_seconds=8.0,
        session_id=session_id,
        session_state=state,
        asr_confidence=0.94,
        voice_turn_state="listening",
    )


def run_routesignal_weak_reply(utterance: str) -> tuple[dict[str, Any], dict[str, Any]]:
    state: dict[str, Any] = {"turns": []}
    session_id = "weak-reply-" + re.sub(r"[^a-z0-9]+", "-", utterance.lower()).strip("-")
    opening = build_routesignal_turn("__agent_open__", state, session_id=session_id, input_type="agent-open")
    append_turn(state, opening)
    reply = build_routesignal_turn(utterance, state, session_id=session_id, input_type="speech-final")
    return opening, reply


def validate_routesignal_weak_replies(failures: list[str], evidence: dict[str, Any]) -> None:
    cases: dict[str, dict[str, Any]] = {}
    for utterance in WEAK_REPLIES:
        opening, reply = run_routesignal_weak_reply(utterance)
        label = f"routesignal weak reply {utterance!r}"
        opening_response = final_response(opening)
        snap = snapshot(reply)
        response = normalize(snap["final_response"])
        cases[utterance] = {
            "opening": snapshot(opening),
            "reply": snap,
        }
        assert_no_side_effects(failures, reply, label)
        assert_condition(failures, snap["campaign_id"] == demo.DEFAULT_CAMPAIGN_ID, f"{label}: default RouteSignal campaign changed: {snap}")
        assert_condition(failures, snap["campaign_config_path"] in (None, ""), f"{label}: selected config should not be active: {snap}")
        assert_condition(failures, snap["call_control"] == "continue-call", f"{label}: call control should continue: {snap}")
        assert_condition(failures, snap["final_response"] != opening_response, f"{label}: repeated the opening response: {snap}")
        assert_condition(failures, "hi, this is maya" not in response, f"{label}: repeated agent opening identity: {snap}")
        assert_condition(failures, any(term in response for term in ROUTESIGNAL_TERMS), f"{label}: response lost RouteSignal grounding: {snap}")
        assert_condition(failures, snap["question_count"] == 1, f"{label}: response should ask one clear next question: {snap}")
        leaked_internal = [term for term in INTERNAL_TERMS if term in response]
        assert_condition(failures, not leaked_internal, f"{label}: internal continuity wording leaked {leaked_internal}: {snap}")
        assert_condition(failures, "which area should we focus" not in response, f"{label}: fell into generic focus menu: {snap}")

    okay = cases["okay"]["reply"]
    assert_condition(
        failures,
        okay["continuity_reason"] == "contextual_permission_acknowledgement",
        f"`okay` should use contextual permission continuity: {okay}",
    )
    assert_condition(
        failures,
        okay["continuity_action"] == "continue_with_session_policy",
        f"`okay` should continue through session policy: {okay}",
    )
    assert_condition(failures, okay["semantic"] == "permission_acknowledgement", f"`okay` semantic mismatch: {okay}")
    evidence["routesignal_weak_replies"] = cases


def build_selected_generic_turn(transcript: str, state: dict[str, Any], *, session_id: str) -> dict[str, Any]:
    return demo.build_browser_demo_turn_packet(
        transcript=transcript,
        campaign_id=demo.DEFAULT_CAMPAIGN_ID,
        campaign_config_path=INSURANCE_CONFIG,
        stage=demo.DEFAULT_STAGE,
        input_type="agent-open" if transcript == "__agent_open__" else "speech-final",
        silence_count=0,
        cases_path=demo.DEFAULT_CASES_PATH,
        private_out=TMP_DIR / session_id,
        live_tts=False,
        force_key_missing=True,
        timeout_seconds=8.0,
        session_id=session_id,
        session_state=state,
        asr_confidence=0.94,
        voice_turn_state="listening",
    )


def validate_generic_selector_preservation(failures: list[str], evidence: dict[str, Any]) -> None:
    state: dict[str, Any] = {"turns": []}
    packets: list[dict[str, Any]] = []
    for transcript in ["__agent_open__", "yeah sure", "premium is a problem"]:
        packet = build_selected_generic_turn(transcript, state, session_id="weak-repair-insurance")
        packets.append(packet)
        append_turn(state, packet)

    evidence["generic_selector_preservation"] = [snapshot(packet) for packet in packets]
    final = evidence["generic_selector_preservation"][-1]
    for index, packet in enumerate(packets, start=1):
        assert_no_side_effects(failures, packet, f"generic selector turn {index}")
        assert_no_route_signal_leakage(failures, packet, f"generic selector turn {index}")
        snap = snapshot(packet)
        assert_condition(failures, snap["campaign_id"] == "synthetic-insurance-review", f"generic selector campaign changed: {snap}")
        assert_condition(failures, snap["campaign_playbook_id"] != ROUTESIGNAL_PLAYBOOK_ID, f"generic selector fell back to RouteSignal: {snap}")
        assert_condition(failures, snap["mode"] == "dry-run", f"generic selector should stay dry-run: {snap}")

    assert_condition(failures, final["semantic"] == "pain_confirmed", f"insurance premium semantic mismatch: {final}")
    assert_condition(failures, final["target_gap"] == "premium_or_budget", f"insurance premium target mismatch: {final}")
    assert_condition(failures, "premium_or_budget" in set(final["confirmed_gaps"]), f"insurance premium not confirmed: {final}")


def render_report(result: dict[str, Any]) -> str:
    lines = [
        "# LIVE-DEMO-001-WEAK-REPLY-CONTINUITY-REPAIR",
        "",
        f"Status: {result['status']}",
        f"Failure count: {len(result.get('failures') or [])}",
        "",
        "## Scope",
        "",
        "- RouteSignal weak-reply continuity after the agent opening.",
        "- Generic campaign selector preservation for a selected insurance config.",
        "- Dry-run, no-provider, no-live-TTS behavior.",
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

    validate_routesignal_weak_replies(failures, evidence)
    validate_generic_selector_preservation(failures, evidence)

    result = {
        "checkpoint_id": CHECKPOINT_ID,
        "status": "pass" if not failures else "fail",
        "failures": failures,
        "evidence": evidence,
        "provider_calls_made": False,
        "local_llm_calls_made": False,
        "sends_email": False,
        "creates_calendar_event": False,
        "writes_crm": False,
        "opens_prod_102": False,
        "uses_live_tts": False,
        "uses_provider_calls": False,
        "uses_real_customer_data": False,
        "uses_private_transcripts": False,
        "uses_generated_audio": False,
        "route_signal_preserved": not any("RouteSignal campaign changed" in failure for failure in failures),
        "generic_selector_preserved": not any("generic selector" in failure for failure in failures),
        "runtime_behavior_changed": False,
    }
    write_evidence(result, render_report(result))
    if failures:
        print(json.dumps(result, indent=2, sort_keys=True))
        return 1
    print(f"{CHECKPOINT_ID}: pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
