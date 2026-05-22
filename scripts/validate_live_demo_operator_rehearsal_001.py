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


CHECKPOINT_ID = "LIVE-DEMO-OPERATOR-REHEARSAL-001"
GENERATED_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
RESULT_PATH = GENERATED_DIR / "result.json"
REPORT_PATH = GENERATED_DIR / "report.md"
TMP_DIR = ROOT / ".tmp" / CHECKPOINT_ID
CHECKLIST_PATH = ROOT / "docs" / "demo" / "LIVE_DEMO_OPERATOR_REHEARSAL.md"

ROUTESIGNAL_PLAYBOOK_ID = "ROUTESIGNAL-DIAGNOSTIC-PLAYBOOK-001"
INSURANCE_CONFIG = ROOT / "runtime" / "campaigns" / "examples" / "synthetic-insurance-review.json"
B2B_CONFIG = ROOT / "runtime" / "campaigns" / "examples" / "synthetic-b2b-saas-operations.json"
EXPECTED_EXAMPLE_COUNT = 8
DRY_RUN_START_COMMAND = "python scripts\\run_live_demo_001_agent_voice_call.py --force-key-missing"
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


def server_json(port: int, method: str, path: str, payload: dict[str, Any] | None = None) -> tuple[int, dict[str, Any]]:
    connection = http.client.HTTPConnection(demo.DEFAULT_HOST, port, timeout=5)
    try:
        return http_json(connection, method, path, payload)
    finally:
        connection.close()


def memory(packet: dict[str, Any]) -> dict[str, Any]:
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
    lead = memory(packet).get("lead_followup_state") or {}
    safety = lead.get("safety") or {}
    summary = packet.get("summary") or {}
    return {
        "transcript": packet.get("transcript"),
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
        "call_control": summary.get("call_control"),
        "final_response": summary.get("final_response"),
        "tts_input_text": summary.get("tts_input_text"),
        "lead_followup_state": lead,
        "audio_url": packet.get("audio_url"),
        "live_tts_used": packet.get("live_tts_used"),
        "provider_calls_made": bool(packet.get("provider_calls_made") or tts.get("provider_calls_made") or voice.get("provider_calls_made") or packet_body.get("api_calls_made")),
        "local_llm_calls_made": bool(packet.get("local_llm_calls_made") or manager.get("local_llm_calls_made") or packet_body.get("llm_used")),
        "sends_email": bool(packet.get("sends_email") or safety.get("sends_email")),
        "creates_calendar_event": bool(packet.get("creates_calendar_event") or safety.get("creates_calendar_event")),
        "writes_crm": bool(packet.get("writes_crm") or safety.get("writes_crm")),
        "opens_prod_102": bool(packet.get("opens_prod_102") or manager.get("opens_prod_102")),
    }


def provider_boundary(packet: dict[str, Any]) -> dict[str, Any]:
    snap = snapshot(packet)
    return {
        "provider_calls_made": snap["provider_calls_made"],
        "local_llm_calls_made": snap["local_llm_calls_made"],
        "sends_email": snap["sends_email"],
        "creates_calendar_event": snap["creates_calendar_event"],
        "writes_crm": snap["writes_crm"],
        "opens_prod_102": snap["opens_prod_102"],
        "live_tts_used": snap["live_tts_used"] is True,
        "audio_url": snap["audio_url"],
    }


def campaign_selector_trace(packet: dict[str, Any]) -> dict[str, Any]:
    snap = snapshot(packet)
    return {
        "campaign_selector_mode": snap["campaign_selector_mode"],
        "campaign_config_path": snap["campaign_config_path"],
        "selected_campaign_config": snap["selected_campaign_config"],
        "campaign_id": snap["campaign_id"],
        "campaign_playbook_id": snap["campaign_playbook_id"],
        "vertical_id": snap["vertical_id"],
        "provider_calls_made": snap["provider_calls_made"],
        "local_llm_calls_made": snap["local_llm_calls_made"],
        "live_tts_used": snap["live_tts_used"] is True,
    }


def transcript_download_payload(session_id: str, packets: list[dict[str, Any]], *, campaign_id: str | None, campaign_config_path: str | None) -> dict[str, Any]:
    return {
        "live_demo_id": demo.LIVE_DEMO_ID,
        "session_id": session_id,
        "campaign_id": campaign_id,
        "campaign_config_path": campaign_config_path,
        "audio_stored": False,
        "customer_audio_uploaded_to_python_server": False,
        "turns": [
            {
                "turn_index": packet.get("session_turn_index"),
                "input_type": "agent-open" if packet.get("transcript") == "__agent_open__" else "speech-final",
                "customer_transcript": "(agent opening)" if packet.get("transcript") == "__agent_open__" else packet.get("transcript"),
                "agent_response": (packet.get("summary") or {}).get("final_response"),
                "call_control": (packet.get("summary") or {}).get("call_control"),
                "campaign_selector": campaign_selector_trace(packet),
                "provider_boundary": provider_boundary(packet),
            }
            for packet in packets
        ],
    }


def assert_no_side_effects(failures: list[str], packet_or_error: dict[str, Any], label: str) -> None:
    snap = snapshot(packet_or_error) if "summary" in packet_or_error or "packet" in packet_or_error else packet_or_error
    for key in SAFETY_KEYS:
        assert_condition(failures, snap.get(key) is False, f"{label}: {key} must be false: {snap}")
    assert_condition(failures, snap.get("live_tts_used", False) is False, f"{label}: live_tts_used must be false: {snap}")
    assert_condition(failures, snap.get("audio_url") in (None, ""), f"{label}: generated audio should not be required: {snap}")


def validate_operator_checklist(failures: list[str], evidence: dict[str, Any]) -> None:
    evidence["operator_checklist"] = {
        "path": str(CHECKLIST_PATH.relative_to(ROOT)),
        "exists": CHECKLIST_PATH.exists(),
    }
    assert_condition(failures, CHECKLIST_PATH.exists(), f"operator checklist missing: {CHECKLIST_PATH}")
    if not CHECKLIST_PATH.exists():
        return
    text = CHECKLIST_PATH.read_text(encoding="utf-8")
    required_fragments = [
        DRY_RUN_START_COMMAND,
        "RouteSignal",
        "generic campaign config",
        "selected campaign metadata",
        "typed-turn",
        "Browser Fallback Voice",
        "provider_calls_made",
        "Download JSON",
        "Download TXT",
        "do not enable live TTS",
        "do not use real customer data",
        "do not paste private transcripts",
        "do not use PROD-102",
        "email",
        "calendar",
        "CRM",
    ]
    missing = [fragment for fragment in required_fragments if fragment not in text]
    evidence["operator_checklist"]["missing_fragments"] = missing
    assert_condition(failures, not missing, f"operator checklist missing required fragments: {missing}")


def validate_exported_html_and_metadata(failures: list[str], evidence: dict[str, Any], metadata: dict[str, Any]) -> None:
    html = demo.render_html(metadata)
    evidence["html_metadata"] = {
        "html_length": len(html),
        "metadata_generic_campaign_count": len(metadata.get("generic_campaign_options") or []),
        "has_selector_metadata_panel": "selectedCampaignMetadata" in html and "selectedCampaignMode" in html,
        "has_download_payload": "function transcriptDownloadPayload" in html and "campaign_selector" in html and "provider_boundary" in html,
        "has_browser_fallback_voice": "Browser Fallback Voice" in html,
        "has_generic_dry_run_warning": "Generic campaign configs run dry-run TTS by default. No provider calls are made." in html,
    }
    assert_condition(failures, evidence["html_metadata"]["has_selector_metadata_panel"], "exported HTML missing selector metadata panel")
    assert_condition(failures, evidence["html_metadata"]["has_download_payload"], "exported HTML missing transcript download trace fields")
    assert_condition(failures, evidence["html_metadata"]["has_browser_fallback_voice"], "exported HTML missing browser fallback voice control")
    assert_condition(failures, evidence["html_metadata"]["has_generic_dry_run_warning"], "exported HTML missing generic dry-run warning")
    assert_condition(failures, len(metadata.get("generic_campaign_options") or []) == EXPECTED_EXAMPLE_COUNT, "metadata generic_campaign_options count mismatch")


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


def build_turn_sequence(
    *,
    session_id: str,
    transcripts: list[str],
    campaign_config_path: Path | None = None,
) -> list[dict[str, Any]]:
    state: dict[str, Any] = {"turns": []}
    packets: list[dict[str, Any]] = []
    for transcript in transcripts:
        packet = demo.build_browser_demo_turn_packet(
            transcript=transcript,
            campaign_id=demo.DEFAULT_CAMPAIGN_ID,
            campaign_config_path=campaign_config_path,
            stage=demo.DEFAULT_STAGE,
            input_type="agent-open" if transcript == "__agent_open__" else "speech-final",
            silence_count=0,
            cases_path=demo.DEFAULT_CASES_PATH,
            private_out=TMP_DIR / "direct-turns",
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


def write_invalid_config() -> Path:
    base = campaign_registry.load_campaign_config(INSURANCE_CONFIG)
    invalid = copy.deepcopy(base)
    invalid.pop("diagnostic_gaps", None)
    path = TMP_DIR / "invalid-configs" / "missing-diagnostic-gaps.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(invalid, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def validate_transcript_payload(failures: list[str], payload: dict[str, Any], label: str) -> None:
    assert_condition(failures, payload.get("live_demo_id") == demo.LIVE_DEMO_ID, f"{label}: live_demo_id missing: {payload}")
    assert_condition(failures, payload.get("session_id"), f"{label}: session_id missing: {payload}")
    assert_condition(failures, bool(payload.get("campaign_id")) != bool(payload.get("campaign_config_path")), f"{label}: expected campaign_id or campaign_config_path: {payload}")
    turns = payload.get("turns") or []
    assert_condition(failures, bool(turns), f"{label}: turns missing: {payload}")
    for index, turn in enumerate(turns, start=1):
        assert_condition(failures, isinstance(turn.get("campaign_selector"), dict), f"{label} turn {index}: campaign selector trace missing: {turn}")
        assert_condition(failures, isinstance(turn.get("provider_boundary"), dict), f"{label} turn {index}: provider boundary missing: {turn}")
        boundary = turn.get("provider_boundary") or {}
        for key in SAFETY_KEYS:
            assert_condition(failures, boundary.get(key) is False, f"{label} turn {index}: {key} should be false: {turn}")
        assert_condition(failures, boundary.get("live_tts_used") is False, f"{label} turn {index}: live_tts_used should be false: {turn}")


def validate_http_rehearsals(failures: list[str], evidence: dict[str, Any], metadata: dict[str, Any]) -> None:
    invalid_path = write_invalid_config()
    server = ThreadingHTTPServer((demo.DEFAULT_HOST, 0), demo.make_handler(metadata, demo.DEFAULT_CASES_PATH, TMP_DIR / "server"))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = int(server.server_address[1])
    try:
        status, campaigns = server_json(port, "GET", "/campaigns")
        evidence["campaigns_endpoint"] = {"status": status, "count": len(campaigns.get("campaigns") or [])}
        assert_condition(failures, status == 200, f"/campaigns returned {status}: {campaigns}")
        assert_condition(failures, len(campaigns.get("campaigns") or []) == EXPECTED_EXAMPLE_COUNT, f"/campaigns count mismatch: {campaigns}")

        route_packets = build_turn_sequence(
            session_id="operator-routesignal",
            transcripts=["__agent_open__", "yeah sure", "callbacks are fine"],
        )
        insurance_packets = build_turn_sequence(
            session_id="operator-insurance",
            transcripts=["__agent_open__", "yeah sure", "premium is a problem", "tomorrow at 3 works"],
            campaign_config_path=INSURANCE_CONFIG,
        )
        b2b_packets = build_turn_sequence(
            session_id="operator-b2b",
            transcripts=["__agent_open__", "yeah sure", "manual work is a problem", "tomorrow at 3 works"],
            campaign_config_path=B2B_CONFIG,
        )

        evidence["routesignal_rehearsal"] = [snapshot(packet) for packet in route_packets]
        evidence["insurance_rehearsal"] = [snapshot(packet) for packet in insurance_packets]
        evidence["b2b_rehearsal"] = [snapshot(packet) for packet in b2b_packets]

        route_final = evidence["routesignal_rehearsal"][-1]
        assert_condition(failures, route_final["campaign_selector_mode"] == "routesignal_live_demo", f"RouteSignal mode mismatch: {route_final}")
        assert_condition(failures, route_final["playbook_id"] == ROUTESIGNAL_PLAYBOOK_ID, f"RouteSignal playbook mismatch: {route_final}")
        assert_condition(failures, route_final["semantic"] == "current_gap_clear", f"RouteSignal final semantic mismatch: {route_final}")
        assert_condition(failures, route_final["target_gap"] == "callbacks", f"RouteSignal target gap mismatch: {route_final}")

        insurance_pain = evidence["insurance_rehearsal"][2]
        insurance_final = evidence["insurance_rehearsal"][-1]
        assert_condition(failures, insurance_pain["campaign_selector_mode"] == "generic_config", f"insurance mode mismatch: {insurance_pain}")
        assert_condition(failures, insurance_pain["campaign_id"] == "synthetic-insurance-review", f"insurance campaign mismatch: {insurance_pain}")
        assert_condition(failures, insurance_pain["target_gap"] == "premium_or_budget", f"insurance premium target mismatch: {insurance_pain}")
        assert_condition(failures, "premium_or_budget" in set(insurance_pain["confirmed_gaps"]), f"insurance premium not confirmed: {insurance_pain}")
        assert_condition(failures, bool(insurance_final["lead_followup_state"].get("appointment") or insurance_final["lead_followup_state"].get("callback")), f"insurance time not captured: {insurance_final}")

        b2b_pain = evidence["b2b_rehearsal"][2]
        b2b_final = evidence["b2b_rehearsal"][-1]
        assert_condition(failures, b2b_pain["campaign_selector_mode"] == "generic_config", f"b2b mode mismatch: {b2b_pain}")
        assert_condition(failures, b2b_pain["campaign_id"] == "synthetic-b2b-saas-operations", f"b2b campaign mismatch: {b2b_pain}")
        assert_condition(failures, b2b_pain["target_gap"] == "manual_work", f"b2b manual_work target mismatch: {b2b_pain}")
        assert_condition(failures, "manual_work" in set(b2b_pain["confirmed_gaps"]), f"b2b manual_work not confirmed: {b2b_pain}")
        assert_condition(failures, bool(b2b_final["lead_followup_state"].get("appointment") or b2b_final["lead_followup_state"].get("callback")), f"b2b time not captured: {b2b_final}")

        for label, packets in {
            "routesignal": route_packets,
            "insurance": insurance_packets,
            "b2b": b2b_packets,
        }.items():
            for index, packet in enumerate(packets, start=1):
                assert_no_side_effects(failures, packet, f"{label} turn {index}")

        route_transcript = transcript_download_payload(
            "operator-routesignal",
            route_packets,
            campaign_id=demo.DEFAULT_CAMPAIGN_ID,
            campaign_config_path=None,
        )
        insurance_transcript = transcript_download_payload(
            "operator-insurance",
            insurance_packets,
            campaign_id=None,
            campaign_config_path="runtime/campaigns/examples/synthetic-insurance-review.json",
        )
        b2b_transcript = transcript_download_payload(
            "operator-b2b",
            b2b_packets,
            campaign_id=None,
            campaign_config_path="runtime/campaigns/examples/synthetic-b2b-saas-operations.json",
        )
        evidence["transcript_download_payloads"] = {
            "routesignal": route_transcript,
            "insurance": insurance_transcript,
            "b2b": b2b_transcript,
        }
        validate_transcript_payload(failures, route_transcript, "routesignal transcript")
        validate_transcript_payload(failures, insurance_transcript, "insurance transcript")
        validate_transcript_payload(failures, b2b_transcript, "b2b transcript")

        status, invalid = server_json(
            port,
            "POST",
            "/turn",
            {
                "transcript": "__agent_open__",
                "input_type": "agent-open",
                "session_id": "operator-invalid",
                "campaign_config_path": str(invalid_path.relative_to(ROOT)).replace("\\", "/"),
                "asr_confidence": 0.94,
                "voice_turn_state": "listening",
            },
        )
        evidence["invalid_config_rehearsal"] = {"status": status, "payload": invalid}
        assert_condition(failures, status == 400, f"invalid config should return HTTP 400: {status}: {invalid}")
        assert_condition(failures, invalid.get("route_signal_fallback_used") is False, f"invalid config fallback flag wrong: {invalid}")
        assert_condition(failures, "final_response" not in invalid, f"invalid config should not include final_response: {invalid}")
        assert_condition(failures, "tts_input_text" not in invalid, f"invalid config should not include tts_input_text: {invalid}")
        assert_no_side_effects(failures, invalid, "invalid config")
        leaked = [term for term in FORBIDDEN_INVALID_ERROR_TERMS if term in json.dumps(invalid)]
        assert_condition(failures, not leaked, f"invalid config leaked RouteSignal/Northstar wording {leaked}: {invalid}")
    except AssertionError as exc:
        failures.append(str(exc))
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def render_report(result: dict[str, Any]) -> str:
    lines = [
        "# LIVE-DEMO-OPERATOR-REHEARSAL-001",
        "",
        f"Status: {result['status']}",
        f"Failure count: {len(result.get('failures') or [])}",
        "",
        "## Dry-Run Start",
        "",
        f"- `{DRY_RUN_START_COMMAND}`",
        "",
        "## Rehearsal Sequences",
        "",
        "- RouteSignal: `__agent_open__`, `yeah sure`, `callbacks are fine`.",
        "- Insurance generic: `__agent_open__`, `yeah sure`, `premium is a problem`, `tomorrow at 3 works`.",
        "- B2B generic: `__agent_open__`, `yeah sure`, `manual work is a problem`, `tomorrow at 3 works`.",
        "",
        "## Invalid Config",
        "",
        f"- Result: HTTP {((result.get('evidence') or {}).get('invalid_config_rehearsal') or {}).get('status')}",
        "",
        "## Transcript Capture",
        "",
        "- Required fields: `live_demo_id`, `session_id`, `campaign_id` or `campaign_config_path`, `turns`, per-turn `campaign_selector`, per-turn `provider_boundary`.",
        "",
        "## Safety Boundary",
        "",
        f"- Provider calls made: `{str(result.get('provider_calls_made')).lower()}`",
        f"- Local LLM calls made: `{str(result.get('local_llm_calls_made')).lower()}`",
        f"- Live TTS used: `{str(result.get('uses_live_tts')).lower()}`",
        f"- Email/calendar/CRM writes: `{str(result.get('sends_email') or result.get('creates_calendar_event') or result.get('writes_crm')).lower()}`",
        f"- PROD-102 opened: `{str(result.get('opens_prod_102')).lower()}`",
        "",
        "## Manual Checklist",
        "",
        f"- `{CHECKLIST_PATH.relative_to(ROOT)}`",
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

    validate_operator_checklist(failures, evidence)
    validate_exported_html_and_metadata(failures, evidence, metadata)
    validate_http_rehearsals(failures, evidence, metadata)

    result = {
        "checkpoint_id": CHECKPOINT_ID,
        "status": "pass" if not failures else "fail",
        "failures": failures,
        "evidence": evidence,
        "dry_run_start_command": DRY_RUN_START_COMMAND,
        "operator_checklist_path": str(CHECKLIST_PATH.relative_to(ROOT)),
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
