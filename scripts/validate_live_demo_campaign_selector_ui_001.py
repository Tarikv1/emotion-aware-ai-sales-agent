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


CHECKPOINT_ID = "LIVE-DEMO-CAMPAIGN-SELECTOR-UI-001"
GENERATED_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
RESULT_PATH = GENERATED_DIR / "result.json"
REPORT_PATH = GENERATED_DIR / "report.md"
TMP_DIR = ROOT / ".tmp" / CHECKPOINT_ID

ROUTESIGNAL_PLAYBOOK_ID = "ROUTESIGNAL-DIAGNOSTIC-PLAYBOOK-001"
INSURANCE_CONFIG = ROOT / "runtime" / "campaigns" / "examples" / "synthetic-insurance-review.json"
EXPECTED_EXAMPLE_COUNT = 8
SAFETY_KEYS = [
    "provider_calls_made",
    "local_llm_calls_made",
    "sends_email",
    "creates_calendar_event",
    "writes_crm",
    "opens_prod_102",
]
FORBIDDEN_INVALID_ERROR_TERMS = ["RouteSignal", "Northstar"]


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


def snapshot(packet: dict[str, Any]) -> dict[str, Any]:
    frame = semantic_frame(packet)
    packet_body = packet.get("packet") or {}
    tts = packet_body.get("tts_delivery") or {}
    voice = packet_body.get("voice_delivery") or {}
    manager = packet.get("dialogue_manager") or {}
    lead = memory(packet).get("lead_followup_state") or {}
    summary = packet.get("summary") or {}
    return {
        "campaign_selector_mode": packet.get("campaign_selector_mode"),
        "campaign_config_path": packet.get("campaign_config_path"),
        "selected_campaign_config": packet.get("selected_campaign_config"),
        "campaign_id": packet.get("campaign_id"),
        "campaign_playbook_id": packet.get("campaign_playbook_id"),
        "vertical_id": packet.get("vertical_id") or (packet.get("selected_campaign_config") or {}).get("vertical_id"),
        "mode": packet.get("mode"),
        "semantic": frame.get("semantic"),
        "target_gap": frame.get("target_gap"),
        "playbook_id": frame.get("playbook_id"),
        "confirmed_gaps": memory(packet).get("confirmed_gaps") or frame.get("confirmed_gaps") or [],
        "cleared_gaps": memory(packet).get("cleared_gaps") or frame.get("cleared_gaps") or [],
        "final_response": summary.get("final_response"),
        "tts_input_text": summary.get("tts_input_text"),
        "audio_url": packet.get("audio_url"),
        "live_tts_used": packet.get("live_tts_used"),
        "provider_calls_made": bool(packet.get("provider_calls_made") or tts.get("provider_calls_made") or voice.get("provider_calls_made") or packet_body.get("api_calls_made")),
        "local_llm_calls_made": bool(packet.get("local_llm_calls_made") or manager.get("local_llm_calls_made") or packet_body.get("llm_used")),
        "sends_email": bool(packet.get("sends_email") or (lead.get("safety") or {}).get("sends_email")),
        "creates_calendar_event": bool(packet.get("creates_calendar_event") or (lead.get("safety") or {}).get("creates_calendar_event")),
        "writes_crm": bool(packet.get("writes_crm") or (lead.get("safety") or {}).get("writes_crm")),
        "opens_prod_102": bool(packet.get("opens_prod_102") or manager.get("opens_prod_102")),
    }


def assert_no_side_effects(failures: list[str], payload: dict[str, Any], label: str) -> None:
    snap = snapshot(payload) if "summary" in payload or "packet" in payload else payload
    for key in SAFETY_KEYS:
        assert_condition(failures, snap.get(key) is False, f"{label}: {key} must be false: {snap}")
    assert_condition(failures, snap.get("audio_url") in (None, ""), f"{label}: audio_url should be absent/null: {snap}")


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
        campaign_config = None
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


def validate_exported_html(failures: list[str], evidence: dict[str, Any], metadata: dict[str, Any]) -> None:
    html = demo.render_html(metadata)
    evidence["html_checks"] = {
        "html_length": len(html),
        "has_generic_campaign_options": "generic_campaign_options" in html,
        "has_selector_grouping": "document.createElement(\"optgroup\")" in html and "RouteSignal live demo" in html and "Generic config dry-run campaigns" in html,
        "has_metadata_display": "selectedCampaignMetadata" in html and "campaign_id" in html and "appointment_target" in html,
        "has_config_payload": "campaign_config_path" in html,
        "has_mode_display": "campaign_selector_mode" in html and "selectedCampaignMode" in html,
        "has_dry_run_warning": "Generic campaign configs run dry-run TTS by default. No provider calls are made." in html,
        "has_invalid_error_path": "campaignError" in html and "handleTurnError" in html and "route_signal_fallback_used" in html,
    }
    for key, value in evidence["html_checks"].items():
        if key != "html_length":
            assert_condition(failures, value is True, f"HTML check failed: {key}")


def validate_metadata(failures: list[str], evidence: dict[str, Any], metadata: dict[str, Any]) -> None:
    selector = metadata.get("campaign_selector") or {}
    evidence["metadata_selector"] = selector
    assert_condition(failures, isinstance(selector, dict), "metadata campaign_selector missing")
    assert_condition(failures, len(metadata.get("generic_campaign_options") or []) == EXPECTED_EXAMPLE_COUNT, "metadata generic_campaign_options count mismatch")
    assert_condition(failures, metadata.get("generic_campaign_count") == EXPECTED_EXAMPLE_COUNT, f"metadata generic_campaign_count mismatch: {metadata.get('generic_campaign_count')}")
    assert_condition(failures, metadata.get("generic_campaigns_use_registry") is True, "metadata generic_campaigns_use_registry missing/false")
    assert_condition(failures, metadata.get("generic_campaigns_use_config_path_runtime") is True, "metadata generic_campaigns_use_config_path_runtime missing/false")
    assert_condition(failures, metadata.get("generic_campaigns_live_tts_enabled_by_default") is False, "metadata generic_campaigns_live_tts_enabled_by_default should be false")
    assert_condition(failures, selector.get("default_mode") == "routesignal_live_demo", f"RouteSignal should be default: {selector}")


def write_invalid_config() -> Path:
    base = campaign_registry.load_campaign_config(INSURANCE_CONFIG)
    invalid = copy.deepcopy(base)
    invalid.pop("diagnostic_gaps", None)
    path = TMP_DIR / "invalid-configs" / "missing-diagnostic-gaps.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(invalid, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def validate_http_surface(failures: list[str], evidence: dict[str, Any], metadata: dict[str, Any]) -> None:
    invalid_path = write_invalid_config()
    server = ThreadingHTTPServer((demo.DEFAULT_HOST, 0), demo.make_handler(metadata, demo.DEFAULT_CASES_PATH, TMP_DIR / "server"))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    connection = http.client.HTTPConnection(demo.DEFAULT_HOST, server.server_address[1], timeout=5)
    try:
        status, selected = http_json(
            connection,
            "POST",
            "/turn",
            {
                "transcript": "__agent_open__",
                "input_type": "agent-open",
                "session_id": "ui-insurance",
                "campaign_config_path": str(INSURANCE_CONFIG.relative_to(ROOT)).replace("\\", "/"),
                "asr_confidence": 0.94,
                "voice_turn_state": "listening",
            },
        )
        selected_snap = snapshot(selected) if status == 200 else selected
        evidence["selected_generic_turn"] = {"status": status, "snapshot": selected_snap}
        assert_condition(failures, status == 200, f"selected generic turn returned {status}: {selected}")
        if status == 200:
            assert_condition(failures, selected_snap["campaign_selector_mode"] == "generic_config", f"selected mode mismatch: {selected_snap}")
            assert_condition(failures, selected_snap["campaign_config_path"] == "runtime/campaigns/examples/synthetic-insurance-review.json", f"selected config path mismatch: {selected_snap}")
            assert_condition(failures, isinstance(selected_snap["selected_campaign_config"], dict), f"selected campaign config metadata missing: {selected_snap}")
            assert_condition(failures, selected_snap["campaign_id"] == "synthetic-insurance-review", f"selected campaign id mismatch: {selected_snap}")
            assert_condition(failures, selected_snap["campaign_playbook_id"] == "synthetic-insurance-review-playbook", f"selected playbook id mismatch: {selected_snap}")
            assert_condition(failures, selected_snap["vertical_id"] == "insurance", f"selected vertical mismatch: {selected_snap}")
            assert_condition(failures, selected_snap["mode"] == "dry-run", f"selected generic mode should be dry-run: {selected_snap}")
            assert_condition(failures, selected_snap["live_tts_used"] is False, f"selected generic live_tts_used should be false: {selected_snap}")
            assert_no_side_effects(failures, selected, "selected generic turn")

        status, invalid = http_json(
            connection,
            "POST",
            "/turn",
            {
                "transcript": "__agent_open__",
                "input_type": "agent-open",
                "session_id": "ui-invalid",
                "campaign_config_path": str(invalid_path.relative_to(ROOT)).replace("\\", "/"),
                "asr_confidence": 0.94,
                "voice_turn_state": "listening",
            },
        )
        evidence["invalid_turn"] = {"status": status, "payload": invalid}
        assert_condition(failures, status == 400, f"invalid config should return HTTP 400: {status}: {invalid}")
        assert_condition(failures, invalid.get("route_signal_fallback_used") is False, f"invalid fallback flag wrong: {invalid}")
        assert_condition(failures, invalid.get("error") and invalid.get("error_type"), f"invalid payload should have clear error and error_type: {invalid}")
        assert_condition(failures, "final_response" not in invalid, f"invalid payload should not contain final_response: {invalid}")
        assert_condition(failures, "tts_input_text" not in invalid, f"invalid payload should not contain tts_input_text: {invalid}")
        assert_condition(failures, invalid.get("audio_url") in (None, ""), f"invalid payload should not contain audio_url: {invalid}")
        assert_no_side_effects(failures, invalid, "invalid config")
        serialized = json.dumps(invalid)
        leaked = [term for term in FORBIDDEN_INVALID_ERROR_TERMS if term in serialized]
        assert_condition(failures, not leaked, f"invalid config error leaked RouteSignal/Northstar wording {leaked}: {invalid}")
    finally:
        connection.close()
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


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
            session_id="ui-routesignal",
            session_state=state,
            asr_confidence=0.94,
            voice_turn_state="listening",
        )
        packets.append(packet)
        append_turn(state, packet)
    evidence["routesignal_default"] = [snapshot(packet) for packet in packets]
    final = evidence["routesignal_default"][-1]
    assert_condition(failures, final["campaign_selector_mode"] == "routesignal_live_demo", f"RouteSignal mode changed: {final}")
    assert_condition(failures, final["playbook_id"] == ROUTESIGNAL_PLAYBOOK_ID, f"RouteSignal playbook changed: {final}")
    assert_condition(failures, final["semantic"] == "current_gap_clear", f"RouteSignal semantic changed: {final}")
    assert_condition(failures, final["target_gap"] == "callbacks", f"RouteSignal callbacks target changed: {final}")
    for index, packet in enumerate(packets, start=1):
        snap = snapshot(packet)
        assert_condition(failures, snap["campaign_config_path"] in (None, ""), f"RouteSignal should not have config path on turn {index}: {snap}")
        for key in SAFETY_KEYS:
            assert_condition(failures, snap.get(key) is False, f"RouteSignal turn {index}: {key} must be false: {snap}")


def render_report(result: dict[str, Any]) -> str:
    lines = [
        "# LIVE-DEMO-CAMPAIGN-SELECTOR-UI-001",
        "",
        f"Status: {result['status']}",
        f"Failure count: {len(result.get('failures') or [])}",
        "",
        "## Scope",
        "",
        "- Browser campaign selector operator UX.",
        "- Turn packet traceability for selected generic configs.",
        "- Invalid selected-config error handling without fallback speech.",
        "- RouteSignal default preservation.",
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
    metadata = make_metadata()

    validate_exported_html(failures, evidence, metadata)
    validate_metadata(failures, evidence, metadata)
    validate_http_surface(failures, evidence, metadata)
    validate_routesignal_default(failures, evidence)

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
