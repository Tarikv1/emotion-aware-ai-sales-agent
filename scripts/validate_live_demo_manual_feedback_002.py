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


CHECKPOINT_ID = "LIVE-DEMO-MANUAL-FEEDBACK-002"
GENERATED_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
RESULT_PATH = GENERATED_DIR / "result.json"
REPORT_PATH = GENERATED_DIR / "report.md"
TMP_DIR = ROOT / ".tmp" / CHECKPOINT_ID

ROUTESIGNAL_PLAYBOOK_ID = "ROUTESIGNAL-DIAGNOSTIC-PLAYBOOK-001"
INSURANCE_CONFIG = ROOT / "runtime" / "campaigns" / "examples" / "synthetic-insurance-review.json"
AUTOMOTIVE_CONFIG = ROOT / "runtime" / "campaigns" / "examples" / "synthetic-automotive-service-review.json"
INSURANCE_REL = "runtime/campaigns/examples/synthetic-insurance-review.json"
AUTOMOTIVE_REL = "runtime/campaigns/examples/synthetic-automotive-service-review.json"

SAFETY_KEYS = [
    "provider_calls_made",
    "local_llm_calls_made",
    "sends_email",
    "creates_calendar_event",
    "writes_crm",
    "opens_prod_102",
]
GENERIC_LEAK_TERMS = [
    "routesignal",
    "northstar",
    "starter",
    "growth",
    "$29",
    "$59",
    "inbound-demo",
    "demo follow-up",
    "missed callbacks",
    "manual tracking",
    "messy handoffs",
]
INTERNAL_GENERIC_PHRASES = [
    "I should",
    "approved qualified reviewer path",
    "I am asking whether",
    "For Policy Review Call, I should stick to approved details",
    "I may not be the right contact",
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


def semantic_frame(packet: dict[str, Any]) -> dict[str, Any]:
    manager = packet.get("dialogue_manager") or {}
    selected = manager.get("selected_action") or {}
    frame = selected.get("contextual_buyer_semantics") or selected.get("semantic_frame") or {}
    if frame:
        return frame
    if selected.get("semantic"):
        return selected
    return manager.get("contextual_buyer_semantics") or {}


def memory(packet: dict[str, Any]) -> dict[str, Any]:
    return dict(packet.get("demo_conversation_memory") or packet.get("conversation_memory") or {})


def snapshot(packet: dict[str, Any]) -> dict[str, Any]:
    packet_body = packet.get("packet") or {}
    tts = packet_body.get("tts_delivery") or {}
    manager = packet.get("dialogue_manager") or {}
    summary = packet.get("summary") or {}
    frame = semantic_frame(packet)
    lead = memory(packet).get("lead_followup_state") or {}
    safety = lead.get("safety") or {}
    return {
        "campaign_selector_mode": packet.get("campaign_selector_mode"),
        "campaign_config_path": packet.get("campaign_config_path"),
        "selected_campaign_config": packet.get("selected_campaign_config"),
        "campaign_id": packet.get("campaign_id"),
        "campaign_playbook_id": packet.get("campaign_playbook_id"),
        "playbook_id": frame.get("playbook_id") or packet.get("campaign_playbook_id"),
        "vertical_id": packet.get("vertical_id") or (packet.get("selected_campaign_config") or {}).get("vertical_id"),
        "semantic": frame.get("semantic"),
        "target_gap": frame.get("target_gap"),
        "confirmed_gaps": memory(packet).get("confirmed_gaps") or frame.get("confirmed_gaps") or [],
        "cleared_gaps": memory(packet).get("cleared_gaps") or frame.get("cleared_gaps") or [],
        "call_control": summary.get("call_control"),
        "final_response": summary.get("final_response") or "",
        "audio_url": packet.get("audio_url"),
        "provider_calls_made": bool(packet.get("provider_calls_made") or tts.get("provider_calls_made") or packet_body.get("api_calls_made")),
        "local_llm_calls_made": bool(packet.get("local_llm_calls_made") or manager.get("local_llm_calls_made") or packet_body.get("llm_used")),
        "sends_email": bool(packet.get("sends_email") or safety.get("sends_email")),
        "creates_calendar_event": bool(packet.get("creates_calendar_event") or safety.get("creates_calendar_event")),
        "writes_crm": bool(packet.get("writes_crm") or safety.get("writes_crm")),
        "opens_prod_102": bool(packet.get("opens_prod_102") or manager.get("opens_prod_102")),
        "live_tts_used": bool(packet.get("live_tts_used")),
        "tts_provider_calls_made": bool(packet.get("tts_provider_calls_made") or tts.get("provider_calls_made")),
        "audio_file_created": bool(packet.get("audio_file_created") or tts.get("audio_file_created")),
        "customer_audio_uploaded_to_python_server": bool(packet.get("customer_audio_uploaded_to_python_server")),
        "customer_audio_uploaded_to_tts_provider": bool(packet.get("customer_audio_uploaded_to_tts_provider")),
    }


def assert_no_side_effects(failures: list[str], snap: dict[str, Any], label: str) -> None:
    for key in SAFETY_KEYS:
        assert_condition(failures, snap.get(key) is False, f"{label}: {key} must be false: {snap}")
    assert_condition(failures, snap.get("live_tts_used") is False, f"{label}: live_tts_used must be false: {snap}")
    assert_condition(failures, snap.get("tts_provider_calls_made") is False, f"{label}: tts provider calls must be false: {snap}")
    assert_condition(failures, snap.get("audio_file_created") is False, f"{label}: audio file must not be created: {snap}")
    assert_condition(failures, snap.get("customer_audio_uploaded_to_python_server") is False, f"{label}: customer audio uploaded to python: {snap}")
    assert_condition(failures, snap.get("customer_audio_uploaded_to_tts_provider") is False, f"{label}: customer audio uploaded to tts provider: {snap}")


def assert_clean_generic_response(failures: list[str], snap: dict[str, Any], label: str) -> None:
    response = str(snap.get("final_response") or "")
    lower = response.lower()
    for term in GENERIC_LEAK_TERMS:
        assert_condition(failures, term not in lower, f"{label}: leaked RouteSignal term {term!r}: {response!r}")
    for phrase in INTERNAL_GENERIC_PHRASES:
        assert_condition(failures, phrase not in response, f"{label}: exposed internal phrase {phrase!r}: {response!r}")
    assert_no_side_effects(failures, snap, label)


def build_turn(
    *,
    transcript: str,
    state: dict[str, Any],
    session_id: str,
    campaign_config_path: Path | None,
    input_type: str | None = None,
) -> dict[str, Any]:
    packet = demo.build_browser_demo_turn_packet(
        transcript=transcript,
        campaign_id=demo.DEFAULT_CAMPAIGN_ID,
        campaign_config_path=campaign_config_path,
        stage=demo.DEFAULT_STAGE,
        input_type=input_type or ("agent-open" if transcript == "__agent_open__" else "speech-final"),
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
        generic_live_tts_allowed=False,
    )
    append_turn(state, packet)
    return packet


def build_sequence(config_path: Path, transcripts: list[str], session_id: str) -> list[dict[str, Any]]:
    state: dict[str, Any] = {"turns": []}
    return [build_turn(transcript=transcript, state=state, session_id=session_id, campaign_config_path=config_path) for transcript in transcripts]


def make_args(campaign_config: str | None = None) -> Any:
    class Args:
        host = demo.DEFAULT_HOST
        port = 0
        campaign = demo.DEFAULT_CAMPAIGN_ID
        campaign_config = None
        stage = demo.DEFAULT_STAGE
        live_tts = False
        force_key_missing = True
        timeout_seconds = 8.0
        consent_confirmed = False
        allow_generic_live_tts = False
        live_tts_preflight = {"api_key_present": False, "voice_id_present": False, "voice_id_source": None}
        live_tts_env_file_status = {"path": None, "present": False, "loaded_keys": [], "ignored_keys": []}

    args = Args()
    args.campaign_config = campaign_config
    return args


def http_json(connection: http.client.HTTPConnection, method: str, path: str, payload: dict[str, Any] | None = None) -> tuple[int, dict[str, Any]]:
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"} if payload is not None else {}
    connection.request(method, path, body=body, headers=headers)
    response = connection.getresponse()
    raw = response.read().decode("utf-8")
    return response.status, json.loads(raw or "{}")


def write_invalid_config() -> Path:
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    config = json.loads(INSURANCE_CONFIG.read_text(encoding="utf-8"))
    config.pop("diagnostic_gaps", None)
    path = TMP_DIR / "invalid-missing-diagnostic-gaps.json"
    path.write_text(json.dumps(config, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def validate_selector_override(failures: list[str], evidence: dict[str, Any]) -> None:
    metadata = demo.build_metadata(make_args(INSURANCE_REL), demo.DEFAULT_CASES_PATH, TMP_DIR / "selector-server")
    invalid_path = write_invalid_config()
    server = ThreadingHTTPServer((demo.DEFAULT_HOST, 0), demo.make_handler(metadata, demo.DEFAULT_CASES_PATH, TMP_DIR / "selector-server"))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    connection = http.client.HTTPConnection(demo.DEFAULT_HOST, server.server_address[1], timeout=5)
    try:
        status, routesignal = http_json(
            connection,
            "POST",
            "/turn",
            {
                "transcript": "__agent_open__",
                "input_type": "agent-open",
                "session_id": "selector-routesignal",
                "campaign_selector_mode": "routesignal_live_demo",
                "campaign_id": demo.DEFAULT_CAMPAIGN_ID,
                "campaign_config_path": None,
                "asr_confidence": 0.94,
                "voice_turn_state": "listening",
            },
        )
        route_snap = snapshot(routesignal) if status == 200 else routesignal
        evidence["selector_override_routesignal"] = {"status": status, "snapshot": route_snap}
        assert_condition(failures, status == 200, f"RouteSignal explicit selector returned {status}: {routesignal}")
        if status == 200:
            assert_condition(failures, route_snap["campaign_selector_mode"] == "routesignal_live_demo", f"RouteSignal selector mode lost: {route_snap}")
            assert_condition(failures, route_snap["campaign_config_path"] is None, f"RouteSignal inherited default generic config: {route_snap}")
            assert_condition(failures, route_snap["playbook_id"] == ROUTESIGNAL_PLAYBOOK_ID, f"RouteSignal selector did not use RouteSignal playbook: {route_snap}")
            assert_condition(failures, "Synthetic Insurance" not in route_snap["final_response"], f"RouteSignal selector produced synthetic insurance text: {route_snap}")
            assert_no_side_effects(failures, route_snap, "selector routesignal")

        status, generic = http_json(
            connection,
            "POST",
            "/turn",
            {
                "transcript": "__agent_open__",
                "input_type": "agent-open",
                "session_id": "selector-generic",
                "campaign_selector_mode": "generic_config",
                "campaign_id": None,
                "campaign_config_path": INSURANCE_REL,
                "asr_confidence": 0.94,
                "voice_turn_state": "listening",
            },
        )
        generic_snap = snapshot(generic) if status == 200 else generic
        evidence["selector_override_generic"] = {"status": status, "snapshot": generic_snap}
        assert_condition(failures, status == 200, f"generic explicit selector returned {status}: {generic}")
        if status == 200:
            assert_condition(failures, generic_snap["campaign_selector_mode"] == "generic_config", f"generic selector mode lost: {generic_snap}")
            assert_condition(failures, generic_snap["campaign_id"] == "synthetic-insurance-review", f"generic selector did not use insurance config: {generic_snap}")
            assert_condition(failures, generic_snap["playbook_id"] != ROUTESIGNAL_PLAYBOOK_ID, f"generic selector fell back to RouteSignal: {generic_snap}")
            assert_clean_generic_response(failures, generic_snap, "selector generic")

        status, invalid = http_json(
            connection,
            "POST",
            "/turn",
            {
                "transcript": "__agent_open__",
                "input_type": "agent-open",
                "session_id": "selector-invalid",
                "campaign_selector_mode": "generic_config",
                "campaign_id": None,
                "campaign_config_path": str(invalid_path.relative_to(ROOT)).replace("\\", "/"),
                "asr_confidence": 0.94,
                "voice_turn_state": "listening",
            },
        )
        evidence["selector_override_invalid"] = {"status": status, "payload": invalid}
        assert_condition(failures, status == 400, f"invalid generic selector should return 400: {status}: {invalid}")
        assert_condition(failures, invalid.get("route_signal_fallback_used") is False, f"invalid selector fallback flag wrong: {invalid}")
        assert_condition(failures, invalid.get("campaign_selector_mode") == "generic_config", f"invalid selector mode wrong: {invalid}")
        assert_condition(failures, "final_response" not in invalid and "tts_input_text" not in invalid, f"invalid selector returned spoken text: {invalid}")
        assert_no_side_effects(failures, {**invalid, "live_tts_used": False, "tts_provider_calls_made": False, "audio_file_created": False}, "selector invalid")
    finally:
        connection.close()
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def validate_insurance_feedback(failures: list[str], evidence: dict[str, Any]) -> None:
    quick = build_sequence(INSURANCE_CONFIG, ["__agent_open__", "just a short minute make it quick"], "insurance-quick")
    quick_snap = snapshot(quick[-1])
    evidence["insurance_make_it_quick"] = quick_snap
    assert_condition(
        failures,
        quick_snap["semantic"] in {"permission_acknowledgement", "time_constrained_permission", "quick_permission"},
        f"insurance quick semantic wrong: {quick_snap}",
    )
    assert_condition(failures, quick_snap["call_control"] == "continue-call", f"insurance quick call_control wrong: {quick_snap}")
    assert_condition(failures, "quick" in quick_snap["final_response"].lower() or "short" in quick_snap["final_response"].lower(), f"insurance quick did not acknowledge time: {quick_snap}")
    assert_condition(failures, "premium" in quick_snap["final_response"].lower() and "coverage" in quick_snap["final_response"].lower(), f"insurance quick did not ask one concise fit question: {quick_snap}")
    assert_clean_generic_response(failures, quick_snap, "insurance quick")

    maybe = build_sequence(INSURANCE_CONFIG, ["__agent_open__", "just a short minute make it quick", "maybe coverage fit"], "insurance-maybe-coverage")
    maybe_snap = snapshot(maybe[-1])
    evidence["insurance_maybe_coverage_fit"] = maybe_snap
    assert_condition(failures, maybe_snap["semantic"] in {"possible_pain_unclear", "tentative_gap_interest", "pain_possible_but_unclear"}, f"insurance maybe semantic wrong: {maybe_snap}")
    assert_condition(failures, maybe_snap["target_gap"] == "coverage_fit", f"insurance maybe target gap wrong: {maybe_snap}")
    assert_condition(failures, maybe_snap["call_control"] == "continue-call", f"insurance maybe should continue, not escalate: {maybe_snap}")
    assert_condition(failures, "licensed" in maybe_snap["final_response"].lower() and ("callback" in maybe_snap["final_response"].lower() or "time" in maybe_snap["final_response"].lower()), f"insurance maybe response did not bridge safely: {maybe_snap}")
    assert_clean_generic_response(failures, maybe_snap, "insurance maybe coverage")

    detail = build_sequence(
        INSURANCE_CONFIG,
        [
            "__agent_open__",
            "yes sure",
            "premium is a problem",
            "what is your product do",
            "so you cannot give me any details about your product",
            "i am asking the question i am asking what your product do",
            "so you can't give me any information about the product only a licensed coverage person",
        ],
        "insurance-product-detail",
    )
    detail_snaps = [snapshot(packet) for packet in detail]
    evidence["insurance_product_detail_limitation"] = detail_snaps
    final = detail_snaps[-1]
    for index, snap in enumerate(detail_snaps[3:], start=4):
        assert_condition(failures, snap["call_control"] == "continue-call", f"insurance product detail turn {index} escalated/ended: {snap}")
        assert_clean_generic_response(failures, snap, f"insurance product detail turn {index}")
    assert_condition(failures, "premium_or_budget" in final["confirmed_gaps"], f"insurance product detail lost confirmed premium: {final}")
    response = final["final_response"].lower()
    assert_condition(failures, "purpose of this call" in response or "purpose of the call" in response, f"insurance product detail did not answer purpose: {final}")
    assert_condition(failures, "licensed" in response and ("policy" in response or "coverage" in response), f"insurance product detail missing safe limitation: {final}")
    assert_condition(failures, "premium" in response, f"insurance product detail did not preserve premium focus: {final}")


def validate_automotive_feedback(failures: list[str], evidence: dict[str, Any]) -> None:
    repair = build_sequence(AUTOMOTIVE_CONFIG, ["__agent_open__", "yes", "repair timings they're usually pretty long"], "auto-repair-timing")
    repair_snap = snapshot(repair[-1])
    evidence["automotive_repair_timing_pain"] = repair_snap
    assert_condition(failures, repair_snap["semantic"] == "pain_confirmed", f"automotive repair timing semantic wrong: {repair_snap}")
    assert_condition(failures, repair_snap["target_gap"] == "repair_timing", f"automotive repair timing target wrong: {repair_snap}")
    assert_condition(failures, "repair_timing" in repair_snap["confirmed_gaps"], f"automotive repair timing not confirmed: {repair_snap}")
    assert_condition(failures, "service advisor" in repair_snap["final_response"].lower() and "time" in repair_snap["final_response"].lower(), f"automotive repair response did not move to advisor review: {repair_snap}")
    assert_clean_generic_response(failures, repair_snap, "automotive repair timing")

    why = build_sequence(
        AUTOMOTIVE_CONFIG,
        ["__agent_open__", "yes", "repair timings they're usually pretty long", "why are you asking for this information again"],
        "auto-why",
    )
    why_snap = snapshot(why[-1])
    evidence["automotive_why_asking"] = why_snap
    assert_condition(failures, "repair_timing" in why_snap["confirmed_gaps"], f"automotive why lost repair timing: {why_snap}")
    assert_condition(failures, "because" in why_snap["final_response"].lower() and "service advisor" in why_snap["final_response"].lower(), f"automotive why did not explain purpose: {why_snap}")
    assert_condition(failures, why_snap["call_control"] == "continue-call", f"automotive why call_control wrong: {why_snap}")
    assert_clean_generic_response(failures, why_snap, "automotive why")

    acceptance = build_sequence(
        AUTOMOTIVE_CONFIG,
        [
            "__agent_open__",
            "yes",
            "repair timings they're usually pretty long",
            "why are you asking for this information again",
            "yeah that would be good",
        ],
        "auto-explanation-acceptance",
    )
    acceptance_snap = snapshot(acceptance[-1])
    evidence["automotive_explanation_acceptance"] = acceptance_snap
    assert_condition(failures, "reason" in acceptance_snap["final_response"].lower() and "service advisor" in acceptance_snap["final_response"].lower(), f"automotive acceptance did not explain reason: {acceptance_snap}")
    assert_condition(failures, "repair_timing" in acceptance_snap["confirmed_gaps"], f"automotive acceptance lost repair timing: {acceptance_snap}")
    assert_condition(failures, acceptance_snap["call_control"] == "continue-call", f"automotive acceptance call_control wrong: {acceptance_snap}")
    assert_clean_generic_response(failures, acceptance_snap, "automotive acceptance")

    contradiction = build_sequence(
        AUTOMOTIVE_CONFIG,
        [
            "__agent_open__",
            "yes",
            "repair timings they're usually pretty long",
            "why are you asking for this information again",
            "yeah that would be good",
            "yeah sure",
            "I mean if you're not the right contact for that question why did you say should I ask a question",
        ],
        "auto-contradiction",
    )
    contradiction_snaps = [snapshot(packet) for packet in contradiction]
    evidence["automotive_contradiction_repair"] = contradiction_snaps
    final = contradiction_snaps[-1]
    response = final["final_response"].lower()
    assert_condition(failures, "confusing" in response or "you re right" in response or "you're right" in response, f"automotive contradiction did not acknowledge wording problem: {final}")
    assert_condition(failures, "basic fit" in response and "service advisor" in response, f"automotive contradiction did not correct contact boundary: {final}")
    assert_condition(failures, final["call_control"] == "continue-call", f"automotive contradiction call_control wrong: {final}")
    assert_condition(failures, final["final_response"] != contradiction_snaps[-2]["final_response"], f"automotive contradiction duplicated final response: {final}")
    assert_clean_generic_response(failures, final, "automotive contradiction")


def render_report(result: dict[str, Any]) -> str:
    lines = [
        "# LIVE-DEMO-MANUAL-FEEDBACK-002",
        "",
        f"Status: {result['status']}",
        f"Failure count: {len(result.get('failures') or [])}",
        "",
        "## Coverage",
        "",
        "- Selector override regression: explicit RouteSignal browser selection must beat default generic CLI config.",
        "- Insurance quick-permission, tentative coverage-fit, and product-detail limitation flows.",
        "- Automotive repair-timing pain, why-asking, explanation acceptance, and contradiction repair flows.",
        "- Dry-run only: no provider calls, live TTS, generated audio, email, calendar, CRM, or PROD-102.",
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
    validate_selector_override(failures, evidence)
    validate_insurance_feedback(failures, evidence)
    validate_automotive_feedback(failures, evidence)

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
        "live_tts_used": False,
        "generated_audio_required": False,
    }
    write_evidence(result, render_report(result))
    if failures:
        print(json.dumps(result, indent=2, sort_keys=True))
        return 1
    print(f"{CHECKPOINT_ID}: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
