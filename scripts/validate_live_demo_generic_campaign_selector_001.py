#!/usr/bin/env python3
from __future__ import annotations

import copy
import http.client
import json
import sys
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.core import campaign_registry  # noqa: E402
from scripts import run_live_demo_001_agent_voice_call as demo  # noqa: E402


CHECKPOINT_ID = "LIVE-DEMO-GENERIC-CAMPAIGN-SELECTOR-001"
GENERATED_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
RESULT_PATH = GENERATED_DIR / "result.json"
REPORT_PATH = GENERATED_DIR / "report.md"
TMP_DIR = ROOT / ".tmp" / CHECKPOINT_ID

ROUTESIGNAL_PLAYBOOK_ID = "ROUTESIGNAL-DIAGNOSTIC-PLAYBOOK-001"
INSURANCE_CONFIG = ROOT / "runtime" / "campaigns" / "examples" / "synthetic-insurance-review.json"
B2B_CONFIG = ROOT / "runtime" / "campaigns" / "examples" / "synthetic-b2b-saas-operations.json"
EXPECTED_EXAMPLE_COUNT = 8
SAFETY_KEYS = [
    "provider_calls_made",
    "local_llm_calls_made",
    "sends_email",
    "creates_calendar_event",
    "writes_crm",
    "opens_prod_102",
]
FORBIDDEN_GENERIC_OUTPUT_TERMS = [
    "RouteSignal",
    "Northstar",
    "Starter",
    "Growth",
    "$29",
    "$59",
    "inbound demo",
    "inbound-demo",
    "demo follow-up",
    "demo-follow-up",
    "missed callbacks",
    "missed-callbacks",
    "manual tracking",
    "manual-tracking",
    "messy handoffs",
    "messy-handoffs",
]


def assert_condition(failures: list[str], condition: bool, message: str) -> None:
    if not condition:
        failures.append(message)


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
        "campaign_config_path": packet.get("campaign_config_path"),
        "campaign_playbook_id": packet.get("campaign_playbook_id"),
        "semantic": frame.get("semantic"),
        "target_gap": frame.get("target_gap"),
        "confirmed_gaps": memory(packet).get("confirmed_gaps") or frame.get("confirmed_gaps") or [],
        "cleared_gaps": memory(packet).get("cleared_gaps") or frame.get("cleared_gaps") or [],
        "playbook_id": frame.get("playbook_id"),
        "call_control": (packet.get("summary") or {}).get("call_control"),
        "final_response": final_response(packet),
        "tts_input_text": tts_input_text(packet),
        "lead_followup_state": lead,
        "mode": packet.get("mode"),
        "audio_url": packet.get("audio_url"),
        "provider_agent_used": packet.get("provider_agent_used"),
        "durable_provider_agent_created": packet.get("durable_provider_agent_created"),
        "voice_cloning_used": packet.get("voice_cloning_used"),
        "provider_calls_made": bool(packet.get("provider_calls_made") or tts.get("provider_calls_made") or voice.get("provider_calls_made") or packet_body.get("api_calls_made")),
        "local_llm_calls_made": bool(packet.get("local_llm_calls_made") or manager.get("local_llm_calls_made") or packet_body.get("llm_used")),
        "sends_email": bool(packet.get("sends_email") or (lead.get("safety") or {}).get("sends_email")),
        "creates_calendar_event": bool(packet.get("creates_calendar_event") or (lead.get("safety") or {}).get("creates_calendar_event")),
        "writes_crm": bool(packet.get("writes_crm") or (lead.get("safety") or {}).get("writes_crm")),
        "opens_prod_102": bool(packet.get("opens_prod_102") or manager.get("opens_prod_102")),
    }


def assert_no_side_effects(failures: list[str], packet_or_error: dict[str, Any], label: str) -> None:
    snap = snapshot(packet_or_error) if "summary" in packet_or_error or "packet" in packet_or_error else packet_or_error
    for key in SAFETY_KEYS:
        assert_condition(failures, snap.get(key) is False, f"{label}: {key} must be false: {snap}")
    assert_condition(failures, snap.get("provider_agent_used", False) is False, f"{label}: provider agent must be false: {snap}")
    assert_condition(failures, snap.get("durable_provider_agent_created", False) is False, f"{label}: durable provider agent must be false: {snap}")
    assert_condition(failures, snap.get("voice_cloning_used", False) is False, f"{label}: voice cloning must be false: {snap}")
    assert_condition(failures, snap.get("audio_url") in (None, ""), f"{label}: generated audio not required: {snap}")


def assert_no_generic_leakage(failures: list[str], packet: dict[str, Any], label: str) -> None:
    combined = f"{final_response(packet)} {tts_input_text(packet)}"
    leaked = [term for term in FORBIDDEN_GENERIC_OUTPUT_TERMS if term.lower() in combined.lower()]
    assert_condition(failures, not leaked, f"{label}: generic output leaked {leaked}: {combined}")


def build_selected_sequence(config_path: Path, transcripts: list[str], session_id: str) -> list[dict[str, Any]]:
    state: dict[str, Any] = {"turns": []}
    packets: list[dict[str, Any]] = []
    for transcript in transcripts:
        packet = demo.build_browser_demo_turn_packet(
            transcript=transcript,
            campaign_id=demo.DEFAULT_CAMPAIGN_ID,
            campaign_config_path=config_path,
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
        packets.append(packet)
        append_turn(state, packet)
    return packets


def validate_routesignal_default(failures: list[str], evidence: dict[str, Any]) -> None:
    state: dict[str, Any] = {"turns": []}
    packets: list[dict[str, Any]] = []
    for transcript in ["__agent_open__", "yeah sure", "callbacks are fine"]:
        packet = demo.build_browser_demo_turn_packet(
            transcript=transcript,
            campaign_id=demo.DEFAULT_CAMPAIGN_ID,
            campaign_config_path=None,
            stage=demo.DEFAULT_STAGE,
            input_type="agent-open" if transcript == "__agent_open__" else "speech-final",
            silence_count=0,
            cases_path=demo.DEFAULT_CASES_PATH,
            private_out=TMP_DIR / "routesignal",
            live_tts=False,
            force_key_missing=True,
            timeout_seconds=8.0,
            session_id="selector-routesignal",
            session_state=state,
            asr_confidence=0.94,
            voice_turn_state="listening",
        )
        packets.append(packet)
        append_turn(state, packet)
    evidence["routesignal_default"] = [snapshot(packet) for packet in packets]
    final = evidence["routesignal_default"][-1]
    assert_condition(failures, final.get("playbook_id") == ROUTESIGNAL_PLAYBOOK_ID, f"RouteSignal playbook changed: {final}")
    assert_condition(failures, final.get("semantic") == "current_gap_clear", f"RouteSignal semantic changed: {final}")
    assert_condition(failures, final.get("target_gap") == "callbacks", f"RouteSignal callbacks target changed: {final}")
    for index, packet in enumerate(packets, start=1):
        assert_no_side_effects(failures, packet, f"routesignal_turn{index}")


def validate_campaign_listing(failures: list[str], evidence: dict[str, Any]) -> None:
    entries = demo.generic_campaign_options()
    evidence["generic_campaign_options"] = entries
    assert_condition(failures, len(entries) == EXPECTED_EXAMPLE_COUNT, f"expected {EXPECTED_EXAMPLE_COUNT} generic examples, got {len(entries)}")
    for entry in entries:
        for key in ["campaign_id", "vertical_id", "product_or_offer_name", "appointment_target", "human_followup_owner", "config_path"]:
            assert_condition(failures, entry.get(key) not in (None, ""), f"campaign option missing {key}: {entry}")
        loaded = campaign_registry.load_campaign_config(ROOT / str(entry.get("config_path")))
        validation = campaign_registry.validate_campaign_config(loaded)
        assert_condition(failures, validation.get("valid") is True, f"campaign option did not validate: {entry}: {validation}")


def validate_generic_insurance(failures: list[str], evidence: dict[str, Any]) -> None:
    packets = build_selected_sequence(
        INSURANCE_CONFIG,
        ["__agent_open__", "yeah sure", "premium is a problem", "tomorrow at 3 works"],
        "selector-insurance",
    )
    evidence["generic_insurance"] = [snapshot(packet) for packet in packets]
    pain = evidence["generic_insurance"][2]
    final = evidence["generic_insurance"][3]
    for index, packet in enumerate(packets, start=1):
        assert_no_side_effects(failures, packet, f"insurance_turn{index}")
        assert_no_generic_leakage(failures, packet, f"insurance_turn{index}")
        assert_condition(failures, snapshot(packet).get("mode") == "dry-run", f"insurance_turn{index}: generic path must be dry-run: {snapshot(packet)}")
        assert_condition(failures, packet.get("campaign_playbook_id") != ROUTESIGNAL_PLAYBOOK_ID, f"insurance_turn{index}: resolved to RouteSignal: {snapshot(packet)}")
    assert_condition(failures, pain.get("target_gap") == "premium_or_budget", f"insurance pain target mismatch: {pain}")
    assert_condition(failures, "premium_or_budget" in set(pain.get("confirmed_gaps") or []), f"insurance premium gap not confirmed: {pain}")
    lead = final.get("lead_followup_state") or {}
    appointment = lead.get("appointment") or {}
    callback = lead.get("callback") or {}
    assert_condition(
        failures,
        appointment.get("confirmed") is True or "3" in str((callback.get("normalized") or {}).get("time_text") or ""),
        f"insurance appointment/callback time not captured: {final}",
    )


def validate_generic_b2b_manual_work(failures: list[str], evidence: dict[str, Any]) -> None:
    packets = build_selected_sequence(
        B2B_CONFIG,
        ["__agent_open__", "yeah sure", "manual work is a problem"],
        "selector-b2b-manual-work",
    )
    evidence["generic_b2b_manual_work"] = [snapshot(packet) for packet in packets]
    final = evidence["generic_b2b_manual_work"][-1]
    for index, packet in enumerate(packets, start=1):
        assert_no_side_effects(failures, packet, f"b2b_turn{index}")
        assert_no_generic_leakage(failures, packet, f"b2b_turn{index}")
        assert_condition(failures, packet.get("campaign_playbook_id") != ROUTESIGNAL_PLAYBOOK_ID, f"b2b_turn{index}: resolved to RouteSignal: {snapshot(packet)}")
    assert_condition(failures, final.get("semantic") == "pain_confirmed", f"b2b manual_work semantic mismatch: {final}")
    assert_condition(failures, final.get("target_gap") == "manual_work", f"b2b manual_work target mismatch: {final}")
    assert_condition(failures, "manual_work" in set(final.get("confirmed_gaps") or []), f"b2b manual_work not confirmed: {final}")


def write_invalid_config() -> Path:
    base = campaign_registry.load_campaign_config(INSURANCE_CONFIG)
    invalid = copy.deepcopy(base)
    invalid.pop("diagnostic_gaps", None)
    path = TMP_DIR / "invalid-configs" / "missing-diagnostic-gaps.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(invalid, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def validate_invalid_selection(failures: list[str], evidence: dict[str, Any]) -> Path:
    path = write_invalid_config()
    try:
        demo.build_browser_demo_turn_packet(
            transcript="__agent_open__",
            campaign_id=demo.DEFAULT_CAMPAIGN_ID,
            campaign_config_path=path,
            stage=demo.DEFAULT_STAGE,
            input_type="agent-open",
            silence_count=0,
            cases_path=demo.DEFAULT_CASES_PATH,
            private_out=TMP_DIR / "invalid-direct",
            live_tts=False,
            force_key_missing=True,
            timeout_seconds=8.0,
            session_id="invalid-direct",
            session_state={"turns": []},
            asr_confidence=0.94,
            voice_turn_state="listening",
        )
    except Exception as exc:
        record = {"path": str(path.relative_to(ROOT)), "error_type": type(exc).__name__, "message": str(exc)}
        evidence["invalid_direct_selection"] = record
        assert_condition(failures, isinstance(exc, campaign_registry.CampaignRegistryError), f"invalid selection should fail with registry error: {record}")
        serialized = json.dumps(record)
        assert_condition(failures, "RouteSignal" not in serialized and "Northstar" not in serialized, f"invalid error leaked RouteSignal/Northstar: {record}")
    else:
        failures.append("invalid config selection generated a turn packet")
    return path


def make_metadata() -> dict[str, Any]:
    class Args:
        host = demo.DEFAULT_HOST
        port = 0
        campaign = demo.DEFAULT_CAMPAIGN_ID
        stage = demo.DEFAULT_STAGE
        live_tts = False
        force_key_missing = True
        timeout_seconds = 8.0
        consent_confirmed = False
        live_tts_preflight = {"api_key_present": False, "voice_id_present": False, "voice_id_source": None}
        live_tts_env_file_status = {"path": None, "present": False, "loaded_keys": [], "ignored_keys": []}

    return demo.build_metadata(Args(), demo.DEFAULT_CASES_PATH, TMP_DIR / "server")


def http_json(connection: http.client.HTTPConnection, method: str, path: str, payload: dict[str, Any] | None = None) -> tuple[int, dict[str, Any]]:
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"} if payload is not None else {}
    connection.request(method, path, body=body, headers=headers)
    response = connection.getresponse()
    raw = response.read().decode("utf-8")
    return response.status, json.loads(raw or "{}")


def validate_http_surface(failures: list[str], evidence: dict[str, Any], invalid_path: Path) -> None:
    metadata = make_metadata()
    server = ThreadingHTTPServer((demo.DEFAULT_HOST, 0), demo.make_handler(metadata, demo.DEFAULT_CASES_PATH, TMP_DIR / "server"))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    connection = http.client.HTTPConnection(demo.DEFAULT_HOST, server.server_address[1], timeout=5)
    try:
        status, listing = http_json(connection, "GET", "/campaigns")
        evidence["http_campaigns"] = {"status": status, "payload": listing}
        assert_condition(failures, status == 200, f"/campaigns returned {status}: {listing}")
        assert_condition(failures, len(listing.get("campaigns") or []) == EXPECTED_EXAMPLE_COUNT, f"/campaigns did not list examples: {listing}")

        status, selected = http_json(
            connection,
            "POST",
            "/turn",
            {
                "transcript": "__agent_open__",
                "input_type": "agent-open",
                "session_id": "http-insurance",
                "campaign_config_path": str(INSURANCE_CONFIG.relative_to(ROOT)).replace("\\", "/"),
                "asr_confidence": 0.94,
                "voice_turn_state": "listening",
            },
        )
        evidence["http_selected_turn"] = {"status": status, "snapshot": snapshot(selected) if status == 200 else selected}
        assert_condition(failures, status == 200, f"selected config /turn returned {status}: {selected}")
        if status == 200:
            assert_condition(failures, selected.get("campaign_id") == "synthetic-insurance-review", f"selected config did not reach generic builder: {snapshot(selected)}")
            assert_condition(failures, selected.get("campaign_playbook_id") != ROUTESIGNAL_PLAYBOOK_ID, f"selected config fell back to RouteSignal: {snapshot(selected)}")
            assert_no_side_effects(failures, selected, "http_selected_turn")
            assert_no_generic_leakage(failures, selected, "http_selected_turn")

        status, invalid = http_json(
            connection,
            "POST",
            "/turn",
            {
                "transcript": "__agent_open__",
                "input_type": "agent-open",
                "session_id": "http-invalid",
                "campaign_config_path": str(invalid_path.relative_to(ROOT)).replace("\\", "/"),
                "asr_confidence": 0.94,
                "voice_turn_state": "listening",
            },
        )
        evidence["http_invalid_turn"] = {"status": status, "payload": invalid}
        assert_condition(failures, status == 400, f"invalid config /turn should return 400: {status}: {invalid}")
        assert_condition(failures, invalid.get("route_signal_fallback_used") is False, f"invalid config fallback flag wrong: {invalid}")
        assert_condition(failures, "final_response" not in invalid and "tts_input_text" not in invalid, f"invalid config returned spoken text: {invalid}")
        assert_no_side_effects(failures, invalid, "http_invalid_turn")
        serialized = json.dumps(invalid)
        assert_condition(failures, "RouteSignal" not in serialized and "Northstar" not in serialized, f"invalid HTTP error leaked RouteSignal/Northstar: {invalid}")
    finally:
        connection.close()
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def render_report(result: dict[str, Any]) -> str:
    lines = [
        "# LIVE-DEMO-GENERIC-CAMPAIGN-SELECTOR-001",
        "",
        f"Status: {result['status']}",
        f"Failure count: {len(result.get('failures') or [])}",
        "",
        "## Scope",
        "",
        "- RouteSignal default live-demo path preservation.",
        "- Browser/server generic campaign selector backed by `runtime/campaigns/examples` JSON configs.",
        "- Invalid config selection fails closed without RouteSignal fallback or provider side effects.",
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

    required_helpers = ["build_browser_demo_turn_packet", "generic_campaign_options"]
    missing_helpers = [name for name in required_helpers if not callable(getattr(demo, name, None))]
    if missing_helpers:
        failures.append(f"live demo generic campaign selector helpers missing: {missing_helpers}")
        result = {
            "checkpoint_id": CHECKPOINT_ID,
            "status": "fail",
            "failures": failures,
            "evidence": {"missing_helpers": missing_helpers},
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
            "route_signal_default_preserved": False,
            "runtime_behavior_changed": False,
        }
        write_evidence(result, render_report(result))
        print(json.dumps(result, indent=2, sort_keys=True))
        return 1

    validate_routesignal_default(failures, evidence)
    validate_campaign_listing(failures, evidence)
    validate_generic_insurance(failures, evidence)
    validate_generic_b2b_manual_work(failures, evidence)
    invalid_path = validate_invalid_selection(failures, evidence)
    validate_http_surface(failures, evidence, invalid_path)

    result = {
        "checkpoint_id": CHECKPOINT_ID,
        "status": "pass" if not failures else "fail",
        "failures": failures,
        "evidence": evidence,
        "forbidden_generic_output_terms": FORBIDDEN_GENERIC_OUTPUT_TERMS,
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
        "route_signal_default_preserved": not any("RouteSignal" in failure for failure in failures),
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
