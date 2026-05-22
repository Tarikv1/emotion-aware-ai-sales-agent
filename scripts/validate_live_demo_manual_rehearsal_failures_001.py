#!/usr/bin/env python3
from __future__ import annotations

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

from scripts import run_live_demo_001_agent_voice_call as demo  # noqa: E402


CHECKPOINT_ID = "LIVE-DEMO-MANUAL-REHEARSAL-FAILURES-001"
GENERATED_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
RESULT_PATH = GENERATED_DIR / "result.json"
REPORT_PATH = GENERATED_DIR / "report.md"
TMP_DIR = ROOT / ".tmp" / CHECKPOINT_ID

ROUTESIGNAL_PLAYBOOK_ID = "ROUTESIGNAL-DIAGNOSTIC-PLAYBOOK-001"
INSURANCE_CONFIG = ROOT / "runtime" / "campaigns" / "examples" / "synthetic-insurance-review.json"
RAW_TURN_TRACE = ROOT / "data" / "private" / "live-demo-003" / "raw-turns" / "browser-transcript" / "LIVE-DEMO-001-6bbdc9b0-069e-4bce-a7ee-3296314cf98d-transcript.json"
SAFETY_KEYS = [
    "provider_calls_made",
    "local_llm_calls_made",
    "sends_email",
    "creates_calendar_event",
    "writes_crm",
    "opens_prod_102",
]
FORBIDDEN_GENERIC_TERMS = [
    "RouteSignal",
    "Northstar",
    "Starter",
    "Growth",
    "$29",
    "$59",
    "inbound-demo",
    "inbound demo",
    "demo-follow-up",
    "demo follow-up",
    "missed-callbacks",
    "missed callbacks",
    "manual-tracking",
    "manual tracking",
    "messy-handoffs",
    "messy handoffs",
]
FORBIDDEN_INTERNAL_TERMS = [
    "I should stick",
    "approved details",
    "I should not give",
    "approved qualified reviewer path",
    "policy wording",
]


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


def final_response(packet: dict[str, Any]) -> str:
    return str((packet.get("summary") or {}).get("final_response") or "")


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
        "final_response": final_response(packet),
        "final_response_source": (packet_body.get("final_answer") or {}).get("source") or packet.get("final_response_source"),
        "audio_url": packet.get("audio_url"),
        "live_tts_used": packet.get("live_tts_used"),
        "provider_calls_made": bool(packet.get("provider_calls_made") or tts.get("provider_calls_made") or voice.get("provider_calls_made") or packet_body.get("api_calls_made")),
        "local_llm_calls_made": bool(packet.get("local_llm_calls_made") or manager.get("local_llm_calls_made") or packet_body.get("llm_used")),
        "sends_email": bool(packet.get("sends_email") or safety.get("sends_email")),
        "creates_calendar_event": bool(packet.get("creates_calendar_event") or safety.get("creates_calendar_event")),
        "writes_crm": bool(packet.get("writes_crm") or safety.get("writes_crm")),
        "opens_prod_102": bool(packet.get("opens_prod_102") or manager.get("opens_prod_102")),
    }


def assert_no_side_effects(failures: list[str], packet_or_payload: dict[str, Any], label: str) -> None:
    snap = snapshot(packet_or_payload) if "summary" in packet_or_payload or "packet" in packet_or_payload else packet_or_payload
    for key in SAFETY_KEYS:
        assert_condition(failures, snap.get(key) is False, f"{label}: {key} must be false: {snap}")
    assert_condition(failures, snap.get("live_tts_used", False) is False, f"{label}: live_tts_used must be false: {snap}")
    assert_condition(failures, snap.get("audio_url") in (None, ""), f"{label}: generated audio should not be required: {snap}")


def assert_no_generic_leakage(failures: list[str], packet: dict[str, Any], label: str) -> None:
    response = final_response(packet)
    leaked = [term for term in FORBIDDEN_GENERIC_TERMS if term.lower() in response.lower()]
    assert_condition(failures, not leaked, f"{label}: generic selected response leaked {leaked}: {response}")


def assert_no_internal_boundary_wording(failures: list[str], packet: dict[str, Any], label: str) -> None:
    response = final_response(packet)
    leaked = [term for term in FORBIDDEN_INTERNAL_TERMS if term.lower() in response.lower()]
    assert_condition(failures, not leaked, f"{label}: internal boundary wording leaked {leaked}: {response}")


def build_sequence(
    transcripts: list[str],
    *,
    session_id: str,
    campaign_config_path: Path | None,
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


def http_json(port: int, method: str, path: str, payload: dict[str, Any] | None = None) -> tuple[int, dict[str, Any]]:
    connection = http.client.HTTPConnection(demo.DEFAULT_HOST, port, timeout=5)
    try:
        body = None if payload is None else json.dumps(payload).encode("utf-8")
        headers = {"Content-Type": "application/json"} if payload is not None else {}
        connection.request(method, path, body=body, headers=headers)
        response = connection.getresponse()
        raw = response.read().decode("utf-8")
        return response.status, json.loads(raw or "{}")
    finally:
        connection.close()


def validate_routesignal_repeated_callbacks(failures: list[str], evidence: dict[str, Any]) -> None:
    transcripts = ["__agent_open__", "yeah sure", "callbacks are fine", "callbacks are fine"]
    direct_packets = build_sequence(transcripts, session_id="manual-routesignal-direct", campaign_config_path=None)
    evidence["routesignal_repeated_callbacks_direct"] = [snapshot(packet) for packet in direct_packets]
    final = evidence["routesignal_repeated_callbacks_direct"][-1]
    assert_condition(failures, final["playbook_id"] == ROUTESIGNAL_PLAYBOOK_ID, f"RouteSignal playbook changed: {final}")
    assert_condition(failures, final["semantic"] != "pain_confirmed", f"second callbacks clear reopened pain: {final}")
    assert_condition(failures, final["call_control"] == "continue-call", f"second callbacks clear should continue unless buyer stops: {final}")
    assert_condition(failures, "campaign selection" not in final["final_response"].lower(), f"RouteSignal response should not mention campaign selection: {final}")
    for index, packet in enumerate(direct_packets, start=1):
        assert_no_side_effects(failures, packet, f"routesignal_direct_turn_{index}")

    metadata = make_metadata()
    server = ThreadingHTTPServer((demo.DEFAULT_HOST, 0), demo.make_handler(metadata, demo.DEFAULT_CASES_PATH, TMP_DIR / "server"))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    statuses: list[dict[str, Any]] = []
    try:
        for transcript in transcripts:
            try:
                status, payload = http_json(
                    server.server_address[1],
                    "POST",
                    "/turn",
                    {
                        "transcript": transcript,
                        "input_type": "agent-open" if transcript == "__agent_open__" else "speech-final",
                        "session_id": "manual-routesignal-http",
                        "asr_confidence": 0.94,
                        "voice_turn_state": "listening",
                    },
                )
                statuses.append({"status": status, "snapshot": snapshot(payload) if status == 200 else payload})
            except Exception as exc:  # pragma: no cover - captured as replay evidence.
                statuses.append({"status": 0, "snapshot": {"error_type": type(exc).__name__, "message": str(exc)}})
        evidence["routesignal_repeated_callbacks_http"] = statuses
        assert_condition(failures, all(item["status"] == 200 for item in statuses), f"RouteSignal HTTP repeated callbacks failed: {statuses}")
        if statuses and statuses[-1]["status"] == 200:
            http_final = statuses[-1]["snapshot"]
            assert_condition(failures, http_final["playbook_id"] == ROUTESIGNAL_PLAYBOOK_ID, f"RouteSignal HTTP playbook changed: {http_final}")
            assert_condition(failures, http_final["semantic"] != "pain_confirmed", f"RouteSignal HTTP reopened callbacks pain: {http_final}")
            assert_condition(failures, http_final["call_control"] == "continue-call", f"RouteSignal HTTP should continue: {http_final}")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def validate_browser_error_labeling(failures: list[str], evidence: dict[str, Any]) -> None:
    html = demo.render_html(make_metadata())
    evidence["browser_error_labeling"] = {
        "has_invalid_campaign_error_classifier": "isInvalidCampaignConfigError" in html,
        "has_generic_turn_error_message": "Turn failed. Review the error before continuing." in html,
        "has_campaign_selection_error_message": "Turn failed. Review the campaign selection error before continuing." in html,
        "has_generic_paused_status": "Turn failed. Listening is paused." in html,
        "has_campaign_selection_paused_status": "Campaign selection failed. Listening is paused." in html,
    }
    assert_condition(failures, evidence["browser_error_labeling"]["has_invalid_campaign_error_classifier"], "browser JS should distinguish invalid campaign selection errors")
    assert_condition(failures, evidence["browser_error_labeling"]["has_generic_turn_error_message"], "browser JS missing generic runtime error copy")
    assert_condition(failures, evidence["browser_error_labeling"]["has_campaign_selection_error_message"], "browser JS missing invalid config error copy")
    assert_condition(failures, evidence["browser_error_labeling"]["has_generic_paused_status"], "browser JS missing generic paused status")
    assert_condition(failures, evidence["browser_error_labeling"]["has_campaign_selection_paused_status"], "browser JS missing campaign selection paused status")


def validate_insurance_product_detail_boundaries(failures: list[str], evidence: dict[str, Any]) -> None:
    sequences = {
        "sequence_a_product_question": [
            "__agent_open__",
            "yes sure",
            "premium is a problem",
            "what is your product do",
        ],
        "sequence_b_limitation_ack": [
            "__agent_open__",
            "yes sure",
            "premium is a problem",
            "what is your product do",
            "so you cannot give me any details about your product",
        ],
        "sequence_c_repeated_limitation_ack": [
            "__agent_open__",
            "yes sure",
            "premium is a problem",
            "what is your product do",
            "so you cannot give me any details about your product",
            "i am asking the question i am asking what your product do",
            "so you can't give me any information about the product only a licensed coverage person",
        ],
        "regulated_claim_boundary_control": [
            "__agent_open__",
            "yes sure",
            "premium is a problem",
            "can you guarantee coverage?",
        ],
    }
    evidence["generic_insurance_product_detail"] = {}
    for label, transcripts in sequences.items():
        packets = build_sequence(transcripts, session_id=f"manual-insurance-{label}", campaign_config_path=INSURANCE_CONFIG)
        snaps = [snapshot(packet) for packet in packets]
        evidence["generic_insurance_product_detail"][label] = snaps
        final_packet = packets[-1]
        final = snaps[-1]
        assert_condition(failures, final["campaign_id"] == "synthetic-insurance-review", f"{label}: wrong campaign: {final}")
        assert_condition(failures, final["campaign_selector_mode"] == "generic_config", f"{label}: wrong selector mode: {final}")
        assert_condition(failures, "premium_or_budget" in set(final["confirmed_gaps"]), f"{label}: premium gap not preserved: {final}")
        assert_no_side_effects(failures, final_packet, label)
        assert_no_generic_leakage(failures, final_packet, label)

        if label == "regulated_claim_boundary_control":
            assert_condition(failures, final["semantic"] == "campaign_claim_boundary_caution", f"{label}: regulated claim boundary was bypassed: {final}")
            assert_condition(failures, "guarantee" in final["final_response"].lower() or "cannot promise" in final["final_response"].lower(), f"{label}: regulated claim boundary not explicit: {final}")
            continue

        assert_condition(failures, final["call_control"] == "continue-call", f"{label}: product-detail limitation should not escalate/end: {final}")
        assert_condition(failures, final["call_control"] != "transfer-or-escalate", f"{label}: unexpected transfer/escalate: {final}")
        assert_no_internal_boundary_wording(failures, final_packet, label)
        response = final["final_response"].lower()
        if label == "sequence_a_product_question":
            assert_condition(failures, "not a product-detail call" in response, f"{label}: should answer product scope plainly: {final}")
            assert_condition(failures, "licensed coverage review" in response, f"{label}: should mention licensed coverage review: {final}")
            assert_condition(failures, "premium" in response and "coverage" in response and "renewal" in response, f"{label}: should name safe review areas: {final}")
        elif label == "sequence_b_limitation_ack":
            assert_condition(failures, "correct" in response or "cannot give detailed" in response, f"{label}: should acknowledge limitation: {final}")
            assert_condition(failures, "licensed coverage review" in response, f"{label}: should explain safe review purpose: {final}")
            assert_condition(failures, "note a time" in response and "stop here" in response, f"{label}: should offer time or stop: {final}")
        elif label == "sequence_c_repeated_limitation_ack":
            assert_condition(failures, "yes" in response and "licensed insurance specialist" in response, f"{label}: should acknowledge licensed specialist limitation: {final}")
            assert_condition(failures, "note a time" in response and "stop here" in response, f"{label}: should offer time or stop: {final}")


def validate_private_trace_reference(evidence: dict[str, Any]) -> None:
    trace = {
        "private_raw_turn_trace_found": RAW_TURN_TRACE.exists(),
        "path": str(RAW_TURN_TRACE.relative_to(ROOT)) if RAW_TURN_TRACE.exists() else str(RAW_TURN_TRACE),
        "observed_failure_markers": {},
    }
    if RAW_TURN_TRACE.exists():
        text = RAW_TURN_TRACE.read_text(encoding="utf-8")
        markers = [
            "what is your product do",
            "I should stick to approved details",
            "so you cannot give me any details about your product",
            "approved qualified reviewer path",
            "transfer-or-escalate",
        ]
        trace["observed_failure_markers"] = {marker: marker in text for marker in markers}
    evidence["private_trace_reference"] = trace


def render_report(result: dict[str, Any]) -> str:
    evidence = result["evidence"]
    return "\n".join(
        [
            f"# {CHECKPOINT_ID}",
            "",
            f"status: {result['status']}",
            "",
            "## Replay Summary",
            f"- RouteSignal repeated callbacks direct turns: {len(evidence.get('routesignal_repeated_callbacks_direct') or [])}",
            f"- RouteSignal repeated callbacks HTTP turns: {len(evidence.get('routesignal_repeated_callbacks_http') or [])}",
            "- Generic insurance product-detail sequences: sequence A, B, C, plus regulated claim boundary control.",
            f"- Private raw-turn trace found: {(evidence.get('private_trace_reference') or {}).get('private_raw_turn_trace_found')}",
            "",
            "## Safety Boundary",
            f"- provider_calls_made: {result['provider_calls_made']}",
            f"- local_llm_calls_made: {result['local_llm_calls_made']}",
            f"- sends_email: {result['sends_email']}",
            f"- creates_calendar_event: {result['creates_calendar_event']}",
            f"- writes_crm: {result['writes_crm']}",
            f"- opens_prod_102: {result['opens_prod_102']}",
            f"- uses_live_tts: {result['uses_live_tts']}",
            "",
            "## Failures",
            json.dumps(result["failures"], indent=2),
            "",
        ]
    )


def main() -> int:
    failures: list[str] = []
    evidence: dict[str, Any] = {}

    validate_private_trace_reference(evidence)
    validate_routesignal_repeated_callbacks(failures, evidence)
    validate_browser_error_labeling(failures, evidence)
    validate_insurance_product_detail_boundaries(failures, evidence)

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
