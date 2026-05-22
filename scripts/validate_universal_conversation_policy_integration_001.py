"""Validate the first universal conversation policy runtime integration.

This validator intentionally exercises only the 4E2B integration slice:
policy-frame trace plus generic-campaign ASR garble repair. It does not make
provider calls, launch a browser, or require live TTS.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.core import universal_conversation_policy_runtime as policy_runtime  # noqa: E402
from scripts import run_live_demo_001_agent_voice_call as demo  # noqa: E402


CHECKPOINT_ID = "UNIVERSAL-CONVERSATION-POLICY-INTEGRATION-001"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
TMP_DIR = ROOT / ".tmp" / CHECKPOINT_ID
INSURANCE_CONFIG = ROOT / "runtime" / "campaigns" / "examples" / "synthetic-insurance-review.json"
AUTO_CONFIG = ROOT / "runtime" / "campaigns" / "examples" / "synthetic-automotive-service-review.json"


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def lower(value: Any) -> str:
    return str(value or "").lower()


def append_turn(state: dict[str, Any], packet: dict[str, Any]) -> None:
    summary = packet.get("summary") or {}
    transcript = summary.get("transcript") or packet.get("transcript") or ""
    response = summary.get("final_response") or packet.get("packet", {}).get("final_response") or ""
    state.setdefault("turns", []).append(
        {
            "transcript": transcript,
            "agent_response": response,
            "summary": summary,
            "continuity": packet.get("demo_session_continuity") or packet.get("conversation_continuity") or {},
            "conversation_memory": packet.get("demo_conversation_memory") or packet.get("conversation_memory") or {},
            "dialogue_manager": packet.get("dialogue_manager") or {},
            "dialogue_pragmatics": packet.get("dialogue_pragmatics") or {},
            "universal_policy_frame": packet.get("universal_policy_frame") or {},
        }
    )
    for key in (
        "conversation_continuity",
        "conversation_memory",
        "dialogue_manager",
        "dialogue_pragmatics",
        "universal_policy_frame",
    ):
        if key in packet:
            state[key] = packet[key]


def semantic_frame(packet: dict[str, Any]) -> dict[str, Any]:
    manager = packet.get("dialogue_manager") or {}
    selected = manager.get("selected_action") or {}
    return (
        selected.get("contextual_buyer_semantics")
        or selected.get("semantic_frame")
        or manager.get("contextual_buyer_semantics")
        or {}
    )


def universal_policy_frame(packet: dict[str, Any]) -> dict[str, Any]:
    return packet.get("universal_policy_frame") or (packet.get("dialogue_manager") or {}).get(
        "universal_policy_frame"
    ) or {}


def final_response(packet: dict[str, Any]) -> str:
    return (
        (packet.get("summary") or {}).get("final_response")
        or (packet.get("packet") or {}).get("final_response")
        or ""
    )


def call_control(packet: dict[str, Any]) -> str:
    return (packet.get("summary") or {}).get("call_control") or (packet.get("packet") or {}).get(
        "call_control"
    ) or ""


def side_effect_flags(packet: dict[str, Any]) -> dict[str, Any]:
    tts = packet.get("tts_delivery") or {}
    return {
        "provider_calls_made": bool(packet.get("provider_calls_made") or tts.get("provider_calls_made")),
        "local_llm_calls_made": bool(packet.get("local_llm_calls_made")),
        "sends_email": bool(packet.get("sends_email")),
        "creates_calendar_event": bool(packet.get("creates_calendar_event")),
        "writes_crm": bool(packet.get("writes_crm")),
        "opens_prod_102": bool(packet.get("opens_prod_102")),
        "customer_audio_uploaded_to_python_server": bool(
            packet.get("customer_audio_uploaded_to_python_server")
        ),
        "customer_audio_uploaded_to_tts_provider": bool(
            packet.get("customer_audio_uploaded_to_tts_provider")
        ),
    }


def assert_no_side_effects(packet: dict[str, Any], label: str) -> None:
    flags = side_effect_flags(packet)
    active = {key: value for key, value in flags.items() if value}
    assert_true(not active, f"{label}: unexpected side effects {active}")


def assert_no_internal_wording(response: str, label: str) -> None:
    text = lower(response)
    forbidden = [
        "i should",
        "approved qualified reviewer path",
        "for policy review call, i should stick",
        "i am asking whether",
        "if premium or budget, coverage fit, or renewal or timing are actually relevant",
    ]
    leaks = [phrase for phrase in forbidden if phrase in text]
    assert_true(not leaks, f"{label}: internal wording leaked {leaks}: {response!r}")


def assert_no_route_signal_leak(packet: dict[str, Any], label: str) -> None:
    response = lower(final_response(packet))
    forbidden = ["routesignal", "northstar", "starter", "growth", "$29", "$59", "manual tracking"]
    leaks = [phrase for phrase in forbidden if phrase in response]
    assert_true(not leaks, f"{label}: RouteSignal leakage in generic response {leaks}: {response!r}")


def assert_no_diagnostic_menu(packet: dict[str, Any], terms: list[str], label: str) -> None:
    response = lower(final_response(packet))
    hits = [term for term in terms if term in response]
    assert_true(len(hits) < 3, f"{label}: repeated full diagnostic menu {hits}: {response!r}")


def build_turn(
    transcript: str,
    state: dict[str, Any],
    *,
    session_id: str,
    campaign_config_path: Path | None,
    asr_confidence: float = 0.94,
) -> dict[str, Any]:
    private_out = TMP_DIR / session_id
    packet = demo.build_browser_demo_turn_packet(
        transcript=transcript,
        campaign_id=demo.DEFAULT_CAMPAIGN_ID,
        stage=demo.DEFAULT_STAGE,
        silence_count=0,
        cases_path=demo.DEFAULT_CASES_PATH,
        session_state=state,
        session_id=session_id,
        private_out=private_out,
        live_tts=False,
        force_key_missing=True,
        input_type="agent-open" if transcript == "__agent_open__" else "speech-final",
        timeout_seconds=8.0,
        asr_confidence=asr_confidence,
        campaign_config_path=campaign_config_path,
        generic_live_tts_allowed=False,
    )
    append_turn(state, packet)
    return packet


def run_sequence(
    transcripts: list[str],
    *,
    session_id: str,
    campaign_config_path: Path | None,
) -> list[dict[str, Any]]:
    state: dict[str, Any] = {}
    packets: list[dict[str, Any]] = []
    for transcript in transcripts:
        packets.append(
            build_turn(
                transcript,
                state,
                session_id=session_id,
                campaign_config_path=campaign_config_path,
            )
        )
    return packets


def scenario_routesignal_preservation() -> dict[str, Any]:
    packets = run_sequence(
        ["__agent_open__", "yeah sure", "callbacks are fine"],
        session_id="routesignal-preservation",
        campaign_config_path=None,
    )
    final = packets[-1]
    frame = universal_policy_frame(final)
    semantic = semantic_frame(final)
    assert_true(frame, "RouteSignal packet should include universal_policy_frame trace")
    assert_true(frame.get("enforcement_enabled") is False, "RouteSignal enforcement must remain disabled")
    assert_true(
        semantic.get("playbook_id") == "ROUTESIGNAL-DIAGNOSTIC-PLAYBOOK-001",
        f"RouteSignal playbook changed: {semantic}",
    )
    assert_true(semantic.get("target_gap") == "callbacks", f"RouteSignal target gap changed: {semantic}")
    assert_true(
        semantic.get("semantic") in {"current_gap_clear", "no_pain_for_specific_gap"},
        f"RouteSignal callbacks clear semantic changed: {semantic}",
    )
    assert_no_side_effects(final, "RouteSignal preservation")
    return snapshot(final, "routesignal_preservation")


def scenario_insurance_garble() -> dict[str, Any]:
    packets = run_sequence(
        ["__agent_open__", "yeah sure", "play a double be good"],
        session_id="insurance-garble",
        campaign_config_path=INSURANCE_CONFIG,
    )
    final = packets[-1]
    frame = universal_policy_frame(final)
    semantic = semantic_frame(final)
    response = final_response(final)
    assert_true(frame.get("buyer_move_id") == "asr_garbled_or_low_confidence", frame)
    assert_true(frame.get("response_shape_id") == "ask_repeat_for_asr_garble", frame)
    assert_true(frame.get("asr_repair_required") is True, frame)
    assert_true(frame.get("enforcement_enabled") is True, frame)
    assert_true("repeat" in lower(response) or "rephrase" in lower(response), response)
    assert_true(semantic.get("semantic") != "pain_confirmed", f"Garble inferred pain: {semantic}")
    assert_true(call_control(final) == "continue-call", f"Garble call control changed: {call_control(final)}")
    assert_true("what time" not in lower(response) and "appointment" not in lower(response), response)
    assert_no_diagnostic_menu(final, ["premium", "coverage", "renewal"], "Insurance garble")
    assert_no_route_signal_leak(final, "Insurance garble")
    assert_no_side_effects(final, "Insurance garble")
    return snapshot(final, "insurance_garble")


def scenario_automotive_near_miss() -> dict[str, Any]:
    packets = run_sequence(
        ["__agent_open__", "yes", "repeal timings are usually pretty long"],
        session_id="automotive-near-miss",
        campaign_config_path=AUTO_CONFIG,
    )
    final = packets[-1]
    frame = universal_policy_frame(final)
    semantic = semantic_frame(final)
    response = final_response(final)
    assert_true(frame.get("buyer_move_id") == "asr_garbled_or_low_confidence", frame)
    assert_true(frame.get("enforcement_enabled") is True, frame)
    assert_true(semantic.get("semantic") != "pain_confirmed", f"Near-miss inferred pain: {semantic}")
    assert_true("repeat" in lower(response) or "rephrase" in lower(response), response)
    assert_true("what time" not in lower(response) and "appointment" not in lower(response), response)
    assert_true(call_control(final) == "continue-call", f"Near-miss call control changed: {call_control(final)}")
    assert_no_diagnostic_menu(final, ["vehicle issue", "repair timing", "warranty"], "Automotive near miss")
    assert_no_route_signal_leak(final, "Automotive near miss")
    assert_no_side_effects(final, "Automotive near miss")
    return snapshot(final, "automotive_near_miss")


def scenario_automotive_clean_pain() -> dict[str, Any]:
    packets = run_sequence(
        ["__agent_open__", "yes", "repair timings are usually pretty long"],
        session_id="automotive-clean-pain",
        campaign_config_path=AUTO_CONFIG,
    )
    final = packets[-1]
    frame = universal_policy_frame(final)
    semantic = semantic_frame(final)
    assert_true(frame.get("enforcement_enabled") is False, frame)
    assert_true(semantic.get("semantic") == "pain_confirmed", f"Clean pain not confirmed: {semantic}")
    assert_true(semantic.get("target_gap") == "repair_timing", f"Clean pain target gap changed: {semantic}")
    assert_no_diagnostic_menu(final, ["vehicle issue", "repair timing", "warranty"], "Automotive clean pain")
    assert_no_route_signal_leak(final, "Automotive clean pain")
    assert_no_side_effects(final, "Automotive clean pain")
    return snapshot(final, "automotive_clean_pain")


def scenario_automotive_challenge() -> dict[str, Any]:
    packets = run_sequence(
        [
            "__agent_open__",
            "yes",
            "repair timings are usually pretty long",
            "why are you asking for this information again",
        ],
        session_id="automotive-challenge",
        campaign_config_path=AUTO_CONFIG,
    )
    final = packets[-1]
    response = lower(final_response(final))
    assert_true(
        "because" in response or "asking" in response or "reason" in response,
        f"Challenge response did not explain why: {final_response(final)!r}",
    )
    assert_no_internal_wording(final_response(final), "Automotive challenge")
    assert_no_diagnostic_menu(final, ["vehicle issue", "repair timing", "warranty"], "Automotive challenge")
    assert_no_route_signal_leak(final, "Automotive challenge")
    assert_no_side_effects(final, "Automotive challenge")
    return snapshot(final, "automotive_challenge")


def scenario_product_detail() -> dict[str, Any]:
    packets = run_sequence(
        ["__agent_open__", "yes", "what does your product do?"],
        session_id="insurance-product-detail",
        campaign_config_path=INSURANCE_CONFIG,
    )
    final = packets[-1]
    assert_true(call_control(final) != "transfer-or-escalate", f"Product detail escalated: {snapshot(final, 'x')}")
    assert_no_internal_wording(final_response(final), "Product detail")
    assert_no_route_signal_leak(final, "Product detail")
    assert_no_side_effects(final, "Product detail")
    return snapshot(final, "product_detail")


def scenario_appointment_garble() -> dict[str, Any]:
    packets = run_sequence(
        ["__agent_open__", "yeah sure", "premium is a problem", "yadav would be good"],
        session_id="appointment-garble",
        campaign_config_path=INSURANCE_CONFIG,
    )
    final = packets[-1]
    frame = universal_policy_frame(final)
    memory = final.get("conversation_memory") or {}
    assert_true(frame.get("buyer_move_id") == "asr_garbled_or_low_confidence", frame)
    assert_true(frame.get("enforcement_enabled") is True, frame)
    assert_true(call_control(final) != "schedule-and-end", f"Garble scheduled: {snapshot(final, 'x')}")
    assert_true(not memory.get("appointment_time"), f"Garble captured appointment: {memory}")
    assert_true(
        "repeat" in lower(final_response(final)) or "rephrase" in lower(final_response(final)),
        f"Appointment garble did not ask repeat/rephrase: {final_response(final)!r}",
    )
    assert_no_route_signal_leak(final, "Appointment garble")
    assert_no_side_effects(final, "Appointment garble")
    return snapshot(final, "appointment_garble")


def snapshot(packet: dict[str, Any], label: str) -> dict[str, Any]:
    semantic = semantic_frame(packet)
    return {
        "label": label,
        "campaign_selector_mode": packet.get("campaign_selector_mode"),
        "campaign_config_path": packet.get("campaign_config_path"),
        "campaign_id": packet.get("campaign_id") or semantic.get("campaign_id"),
        "campaign_playbook_id": packet.get("campaign_playbook_id") or semantic.get("playbook_id"),
        "semantic": semantic.get("semantic"),
        "target_gap": semantic.get("target_gap"),
        "confirmed_gaps": (packet.get("conversation_memory") or {}).get("confirmed_gaps"),
        "cleared_gaps": (packet.get("conversation_memory") or {}).get("cleared_gaps"),
        "call_control": call_control(packet),
        "final_response": final_response(packet),
        "universal_policy_frame": universal_policy_frame(packet),
        "side_effect_flags": side_effect_flags(packet),
    }


def write_evidence(result: dict[str, Any]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    report = [
        f"# {CHECKPOINT_ID}",
        "",
        "## Summary",
        "Validated the first universal conversation policy runtime integration: policy-frame trace plus generic-only ASR garble repair.",
        "",
        "## Scenarios",
    ]
    for scenario in result["scenarios"]:
        frame = scenario["universal_policy_frame"]
        report.extend(
            [
                f"- {scenario['label']}: semantic={scenario.get('semantic')} target_gap={scenario.get('target_gap')} "
                f"call_control={scenario.get('call_control')} enforcement={frame.get('enforcement_enabled')} "
                f"buyer_move={frame.get('buyer_move_id')}",
            ]
        )
    report.extend(
        [
            "",
            "## Safety Boundary",
            f"- provider_calls_made: {result['side_effects']['provider_calls_made']}",
            f"- local_llm_calls_made: {result['side_effects']['local_llm_calls_made']}",
            f"- sends_email: {result['side_effects']['sends_email']}",
            f"- creates_calendar_event: {result['side_effects']['creates_calendar_event']}",
            f"- writes_crm: {result['side_effects']['writes_crm']}",
            f"- opens_prod_102: {result['side_effects']['opens_prod_102']}",
            f"- customer_audio_uploaded_to_python_server: {result['side_effects']['customer_audio_uploaded_to_python_server']}",
            f"- customer_audio_uploaded_to_tts_provider: {result['side_effects']['customer_audio_uploaded_to_tts_provider']}",
        ]
    )
    (OUT_DIR / "report.md").write_text("\n".join(report) + "\n", encoding="utf-8")


def main() -> int:
    assert_true(hasattr(policy_runtime, "build_universal_conversation_policy_frame"), "missing frame builder")
    assert_true(hasattr(policy_runtime, "detect_universal_asr_garble"), "missing ASR detector")
    assert_true(hasattr(policy_runtime, "should_enforce_universal_asr_repair"), "missing enforcement helper")

    TMP_DIR.mkdir(parents=True, exist_ok=True)
    scenarios = [
        scenario_routesignal_preservation(),
        scenario_insurance_garble(),
        scenario_automotive_near_miss(),
        scenario_automotive_clean_pain(),
        scenario_automotive_challenge(),
        scenario_product_detail(),
        scenario_appointment_garble(),
    ]

    combined_flags: dict[str, bool] = {}
    for scenario in scenarios:
        for key, value in scenario["side_effect_flags"].items():
            combined_flags[key] = bool(combined_flags.get(key) or value)

    result = {
        "checkpoint_id": CHECKPOINT_ID,
        "policy_runtime_id": getattr(policy_runtime, "POLICY_RUNTIME_ID", None),
        "scenarios": scenarios,
        "side_effects": combined_flags,
        "status": "passed",
    }
    write_evidence(result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
