#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MOCK_RESULT = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-TOOL-BOUNDARY-MOCK-001" / "result.json"
HOSTED_RESULT = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-HOSTED-SANDBOX-001" / "result.json"
LOCAL_ENDPOINT_RESULT = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-LOCAL-TOOL-ENDPOINT-001" / "result.json"
TUNNEL_RESULT = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-TUNNEL-SANDBOX-001" / "result.json"
WEBSOCKET_RESULT = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-WEBSOCKET-TEXT-SANDBOX-001" / "result.json"
WEBSOCKET_QUALITY_RESULT = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-WEBSOCKET-TEXT-SANDBOX-QUALITY-001" / "result.json"
AUDIO_INPUT_RESULT = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-SYNTHETIC-AUDIO-INPUTS-001" / "result.json"
MANUAL_AUDIO_INPUT_RESULT = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-MANUAL-AUDIO-INPUTS-001" / "result.json"
AUDIO_RESULT = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-WEBSOCKET-AUDIO-SANDBOX-001" / "result.json"
AUDIO_QUALITY_RESULT = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-WEBSOCKET-AUDIO-SANDBOX-QUALITY-001" / "result.json"
WARM_RESULT = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-WARM-SESSION-LATENCY-001" / "result.json"
WARM_AUDIT_RESULT = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-WARM-SESSION-LATENCY-AUDIT-001" / "result.json"
DECISION_RESULT = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-HOSTED-FEASIBILITY-DECISION-001" / "result.json"
DECISION_REPORT = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-HOSTED-FEASIBILITY-DECISION-001" / "report.md"


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def fail(message: str) -> None:
    raise AssertionError(message)


def load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        fail(f"missing file: {rel(path)}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        fail(f"{rel(path)} must be a JSON object")
    return payload


def expected_recommendation(mock: dict[str, Any], hosted: dict[str, Any], local_endpoint: dict[str, Any] | None = None) -> str:
    if local_endpoint is not None:
        if local_endpoint.get("synthetic_cases_passed") is True and local_endpoint.get("passed_count") == 8:
            return "gated temporary HTTPS tunnel sandbox next"
        return "fix endpoint before provider run"
    mock_passed = mock.get("summary", {}).get("tool_boundary_passed") is True
    provider_run = hosted.get("provider_call_made") is True and hosted.get("sandbox_run") is True
    provider_tool_calls_work = hosted.get("tool_calls_work") is True
    provider_failed_boundary = hosted.get("tool_boundary_supported") is False or hosted.get("run_status") == "failed"
    if hosted.get("run_status") in {"blocked_missing_api_key", "not_run"}:
        return "provide Ultravox key and rerun gated sandbox when ready"
    if hosted.get("run_status") == "blocked_no_public_tool_endpoint":
        return "design safe temporary HTTPS tool endpoint or client-tool strategy next"
    if not mock_passed:
        return "fix tool contract before any provider sandbox"
    if provider_run and hosted.get("tool_call_attempted") is False:
        return "do not proceed; keep Ultravox as research only until tool boundary works"
    if provider_run and provider_tool_calls_work:
        return "limited synthetic voice conversation test next, still no real customers and no phone calls"
    if provider_failed_boundary:
        return "keep Ultravox as research/reference only"
    return "keep Ultravox as research/reference only"


def expected_tunnel_recommendation(tunnel: dict[str, Any]) -> str:
    status = tunnel.get("run_status")
    if status == "blocked_explicit_cloudflared_path_missing":
        return "fix ULTRAVOX_TUNNEL_CLOUDFLARED_PATH"
    if status == "blocked_tunnel_url_not_detected":
        if tunnel.get("tunnel_tool_used") == "ngrok":
            return "fix ngrok auth/config"
        return "fix tunnel URL parsing"
    if status == "blocked_tunnel_dns_failed":
        if tunnel.get("tunnel_tool_used") == "ngrok":
            return "fix tunnel endpoint/auth before provider call"
        return "retry tunnel later, test local DNS/trycloudflare reachability, or use ngrok/cloudflared named tunnel"
    if status == "blocked_tunnel_http_failed":
        return "fix tunnel endpoint/auth before provider call" if tunnel.get("tunnel_tool_used") == "ngrok" else "fix tunnel target/local server path"
    if status == "blocked_tunnel_auth_failed":
        return "fix tunnel endpoint/auth before provider call" if tunnel.get("tunnel_tool_used") == "ngrok" else "fix token/header handling"
    if status == "blocked_no_tunnel_tool":
        return "install/configure ngrok or use Cloudflare named tunnel"
    if status == "blocked_ngrok_auth_missing":
        return "fix ngrok auth/config"
    if status == "blocked_tunnel_test_failed":
        return "fix tunnel/endpoint/auth before provider call"
    if status == "preflight_only_passed":
        return "run gated provider sandbox next"
    if status == "provider_create_failed":
        return "fix API/session payload"
    if status == "provider_session_created_no_interaction":
        return "implement WebSocket/browser client sandbox"
    if status == "provider_session_created_tool_called" and tunnel.get("tool_call_succeeded") is True:
        return "limited synthetic voice conversation test next"
    if tunnel.get("tool_call_attempted") is True and tunnel.get("tool_call_succeeded") is not True:
        return "do not proceed"
    if status == "not_run_tunnel_gates_disabled":
        return "provide tunnel gate and tool token, then rerun gated tunnel sandbox when ready"
    if status == "not_run_provider_gates_disabled":
        return "provide Ultravox key/provider gates and rerun gated tunnel sandbox when ready"
    if status == "unsafe_secret_file":
        return "fix local secret file ignore rule before any sandbox"
    return "keep Ultravox as research/reference only"


def expected_websocket_recommendation(websocket: dict[str, Any], quality: dict[str, Any] | None) -> str:
    if websocket.get("websocket_connected") is not True:
        return "fix joinUrl/WebSocket client"
    if websocket.get("synthetic_turns_attempted", 0) > 0 and websocket.get("synthetic_turns_completed", 0) == 0:
        return "audio-input WebSocket sandbox or browser WebRTC SDK next"
    if quality is not None:
        if quality.get("project_tool_called") is not True:
            return "fix tool declaration/prompt/session payload"
        if quality.get("tool_boundary_enforced") is True:
            return "limited synthetic voice/audio sandbox next"
        return "keep Ultravox as research only"
    if websocket.get("tool_boundary_enforced") is True:
        return "limited synthetic voice/audio sandbox next"
    if websocket.get("tool_call_attempted") is not True:
        return "fix tool declaration/prompt/session payload"
    return "keep Ultravox as research only"


def expected_audio_recommendation(audio_input: dict[str, Any], audio: dict[str, Any], quality: dict[str, Any] | None) -> str:
    if audio_input.get("generation_succeeded") is not True:
        return "prepare local synthetic audio inputs manually"
    if audio.get("websocket_connected") and audio.get("user_transcript_count", 0) == 0 and audio.get("synthetic_audio_turns_attempted", 0) > 0:
        return "fix audio format/chunking/sample rate"
    if audio.get("user_transcript_count", 0) > 0 and (quality is None or quality.get("project_tool_called") is not True):
        return "fix prompt/tool declaration for audio mode"
    if quality is not None:
        if quality.get("tool_boundary_enforced") is not True and quality.get("project_tool_called"):
            return "do not proceed"
        if quality.get("tool_boundary_enforced") and quality.get("agent_audio_observed") and quality.get("response_follows_project_tool"):
            return "limited synthetic voice conversation evaluation next"
        if quality.get("project_tool_called") and quality.get("agent_audio_observed"):
            return "manual listening review of agent audio next"
        if quality.get("project_tool_called") and not quality.get("agent_audio_observed"):
            return "manual listening review blocked until agent audio returns"
    return "keep Ultravox as research only"


def expected_manual_audio_recommendation(manual_input: dict[str, Any], audio: dict[str, Any], quality: dict[str, Any] | None) -> str:
    if manual_input.get("status") in {"missing_manual_inputs", "missing_manual_input_evidence"} or audio.get("manual_audio_inputs_found") is not True:
        return "add manual local test clips"
    if manual_input.get("conversion_succeeded") is not True or audio.get("manual_audio_conversion_succeeded") is not True:
        return "install/enable ffmpeg or provide 48kHz mono PCM WAV"
    if audio.get("websocket_connected") and audio.get("user_transcript_count", 0) == 0 and audio.get("synthetic_audio_turns_attempted", 0) > 0:
        return "fix audio chunking/sample rate/encoding"
    if audio.get("user_transcript_count", 0) > 0 and (quality is None or quality.get("project_tool_called") is not True):
        return "fix prompt/tool declaration for audio mode"
    if quality is not None:
        if quality.get("tool_boundary_enforced") is not True and quality.get("project_tool_called"):
            return "do not proceed"
        if quality.get("tool_boundary_enforced") and quality.get("agent_audio_observed") and quality.get("response_follows_project_tool"):
            return "limited synthetic voice conversation evaluation next"
        if quality.get("project_tool_called") and quality.get("agent_audio_observed"):
            return "manual listening review of Ultravox agent audio next"
        if quality.get("project_tool_called") and not quality.get("agent_audio_observed"):
            return "manual listening review blocked until agent audio returns"
    return "keep Ultravox as research only"


def main() -> None:
    mock = load_json(MOCK_RESULT)
    hosted = load_json(HOSTED_RESULT)
    local_endpoint = load_json(LOCAL_ENDPOINT_RESULT) if LOCAL_ENDPOINT_RESULT.is_file() else None
    tunnel = load_json(TUNNEL_RESULT) if TUNNEL_RESULT.is_file() else None
    websocket = load_json(WEBSOCKET_RESULT) if WEBSOCKET_RESULT.is_file() else None
    websocket_quality = load_json(WEBSOCKET_QUALITY_RESULT) if WEBSOCKET_QUALITY_RESULT.is_file() else None
    audio_input = load_json(AUDIO_INPUT_RESULT) if AUDIO_INPUT_RESULT.is_file() else None
    manual_audio_input = load_json(MANUAL_AUDIO_INPUT_RESULT) if MANUAL_AUDIO_INPUT_RESULT.is_file() else None
    audio = load_json(AUDIO_RESULT) if AUDIO_RESULT.is_file() else None
    audio_quality = load_json(AUDIO_QUALITY_RESULT) if AUDIO_QUALITY_RESULT.is_file() else None
    warm = load_json(WARM_RESULT) if WARM_RESULT.is_file() else None
    warm_audit = load_json(WARM_AUDIT_RESULT) if WARM_AUDIT_RESULT.is_file() else None
    decision = load_json(DECISION_RESULT)
    report_text = DECISION_REPORT.read_text(encoding="utf-8") if DECISION_REPORT.is_file() else ""
    if not report_text:
        fail(f"missing file: {rel(DECISION_REPORT)}")

    if decision.get("evaluation_id") != "ULTRAVOX-HOSTED-FEASIBILITY-DECISION-001":
        fail("unexpected feasibility decision evaluation_id")
    if decision.get("phase") not in {"4J1", "4J2", "4J3", "4J4", "4J5", "4J5B", "4J7"}:
        fail("feasibility decision must record phase 4J1, 4J2, 4J3, 4J4, 4J5, 4J5B, or 4J7")
    if decision.get("phase") == "4J7":
        if warm is None:
            fail("phase 4J7 decision requires warm-session latency evidence")
        if warm_audit is None:
            fail("phase 4J7 decision requires warm-session latency audit evidence")
        expected = warm_audit.get("recommendation")
    elif decision.get("phase") == "4J5B":
        if manual_audio_input is None:
            fail("phase 4J5B decision requires manual audio input evidence")
        if audio is None:
            fail("phase 4J5B decision requires websocket audio sandbox evidence")
        expected = expected_manual_audio_recommendation(manual_audio_input, audio, audio_quality)
    elif decision.get("phase") == "4J5":
        if audio_input is None:
            fail("phase 4J5 decision requires synthetic audio input evidence")
        if audio is None:
            fail("phase 4J5 decision requires websocket audio sandbox evidence")
        expected = expected_audio_recommendation(audio_input, audio, audio_quality)
    elif decision.get("phase") == "4J4":
        if websocket is None:
            fail("phase 4J4 decision requires websocket sandbox evidence")
        expected = expected_websocket_recommendation(websocket, websocket_quality)
    else:
        expected = expected_tunnel_recommendation(tunnel) if decision.get("phase") == "4J3" and tunnel is not None else expected_recommendation(mock, hosted, local_endpoint)
    if decision.get("recommendation") != expected:
        fail(f"recommendation must be {expected!r}, got {decision.get('recommendation')!r}")

    for key in ("live_wiring_allowed", "production_call_allowed", "real_customer_data_allowed"):
        if decision.get(key) is not False:
            fail(f"{key} must always stay false")
    if decision.get("phase") == "4J7" and warm is not None:
        active_evidence = warm
    elif decision.get("phase") in {"4J5", "4J5B"} and audio is not None:
        active_evidence = audio
    elif decision.get("phase") == "4J4" and websocket is not None:
        active_evidence = websocket
    else:
        active_evidence = tunnel if decision.get("phase") == "4J3" and tunnel is not None else hosted
    for key in ("sandbox_run", "provider_call_made", "tool_call_attempted", "tool_call_succeeded", "public_tool_endpoint_required", "public_tool_endpoint_available"):
        if active_evidence.get(key) is not None and decision.get(key) != active_evidence.get(key):
            fail(f"{key} must match active sandbox evidence")
    if decision.get("phase") == "4J7" and warm is not None and warm_audit is not None:
        for key in ("session_created", "join_url_received", "websocket_connected", "audio_turns_attempted", "audio_turns_completed"):
            if decision.get(key) != warm.get(key):
                fail(f"{key} must match warm-session evidence")
        if decision.get("ultravox_session_created") != warm.get("session_created"):
            fail("ultravox_session_created must match warm session_created evidence")
        expected_audit_fields = {
            "warm_measured_turn_count": "measured_warm_turn_count",
            "warm_p50_first_agent_audio_latency_seconds": "warm_p50_first_agent_audio_latency_seconds",
            "warm_p90_first_agent_audio_latency_seconds": "warm_p90_first_agent_audio_latency_seconds",
            "tool_request_count": "tool_request_count",
            "tool_boundary_passed": "tool_boundary_passed",
            "product_truth_drift_count": "product_truth_drift_count",
            "fake_side_effect_count": "fake_side_effect_count",
            "crm_email_calendar_claim_count": "crm_email_calendar_claim_count",
            "strong_live_target_met": "strong_live_target_met",
            "early_demo_target_met": "early_demo_target_met",
            "live_ready_latency": "live_ready_latency",
            "latency_classification": "latency_classification",
        }
        for decision_key, audit_key in expected_audit_fields.items():
            if decision.get(decision_key) != warm_audit.get(audit_key):
                fail(f"{decision_key} must match warm-session audit evidence")
    if decision.get("phase") in {"4J5", "4J5B"} and audio is not None:
        for key in ("session_created", "join_url_received", "websocket_connected", "synthetic_audio_turns_attempted", "synthetic_audio_turns_completed", "user_transcript_count", "agent_transcript_count", "agent_audio_chunks_received", "agent_audio_bytes_received", "local_http_tool_request_count"):
            if decision.get(key) != audio.get(key):
                fail(f"{key} must match websocket audio sandbox evidence")
        if decision.get("ultravox_session_created") != audio.get("session_created"):
            fail("ultravox_session_created must match audio session_created evidence")
        if decision.get("phase") == "4J5" and audio_input is not None and decision.get("synthetic_audio_generation_succeeded") != audio_input.get("generation_succeeded"):
            fail("synthetic_audio_generation_succeeded must match audio input evidence")
        if decision.get("phase") == "4J5B":
            if decision.get("manual_audio_inputs_found") != audio.get("manual_audio_inputs_found"):
                fail("manual_audio_inputs_found must match websocket audio sandbox evidence")
            if decision.get("manual_audio_conversion_succeeded") != audio.get("manual_audio_conversion_succeeded"):
                fail("manual_audio_conversion_succeeded must match websocket audio sandbox evidence")
            if decision.get("prepared_audio_inputs_count") != audio.get("prepared_audio_inputs_count"):
                fail("prepared_audio_inputs_count must match websocket audio sandbox evidence")
            if decision.get("manual_audio_converter_used") != audio.get("manual_audio_converter_used"):
                fail("manual_audio_converter_used must match websocket audio sandbox evidence")
        if audio_quality is not None:
            for key in ("tool_boundary_enforced", "project_tool_called", "response_follows_project_tool"):
                if decision.get(key) != audio_quality.get(key):
                    fail(f"{key} must match websocket audio quality evidence")
    if decision.get("phase") == "4J4" and websocket is not None:
        for key in ("ultravox_session_created", "join_url_received", "websocket_connected", "synthetic_turns_attempted", "synthetic_turns_completed", "http_tool_endpoint_request_count", "tool_result_sent_count"):
            if decision.get(key) != websocket.get(key):
                fail(f"{key} must match websocket sandbox evidence")
        if websocket_quality is not None:
            for key in ("tool_boundary_enforced", "project_tool_called", "response_follows_project_tool"):
                if decision.get(key) != websocket_quality.get(key):
                    fail(f"{key} must match websocket quality evidence")
    if local_endpoint is not None and decision.get("phase") not in {"4J3", "4J4", "4J5", "4J5B", "4J7"}:
        if decision.get("local_tool_endpoint_completed") is not True:
            fail("decision must record completed local endpoint")
        if decision.get("local_tool_endpoint_passed") is not True:
            fail("decision must record passing local endpoint")
        if decision.get("public_tunnel_opened") is not False:
            fail("decision must record no public tunnel")
    if decision.get("memory_ownership_decision") != "project_runtime_owns_canonical_memory":
        fail("canonical memory ownership must stay with project runtime")
    if decision.get("sales_brain_ownership_decision") != "project_runtime_owns_sales_brain_and_campaign_truth":
        fail("sales brain and campaign truth must stay project-owned")
    if decision.get("ultravox_product_truth_owner") is not False:
        fail("Ultravox must not own product truth")
    if decision.get("side_effects_allowed") is not False:
        fail("side effects must stay blocked")
    if decision.get("runtime_behavior_changed") is not False:
        fail("decision must record no runtime behavior change")
    if decision.get("response_text_changed") is not False:
        fail("decision must record no response text change")

    required_report_lines = [
        f"Recommendation: `{expected}`",
        "Live wiring allowed: `false`",
        "Production call allowed: `false`",
        "Project runtime owns canonical memory.",
        "Project runtime owns the sales brain and campaign truth.",
        "Public tool endpoint required:",
    ]
    if decision.get("phase") == "4J7":
        required_report_lines.remove("Public tool endpoint required:")
        required_report_lines.extend(
            [
                "Warm-session latency run status:",
                "Provider call made:",
                "Ultravox session created:",
                "Join URL received:",
                "WebSocket connected:",
                "Audio turns attempted:",
                "Audio turns completed:",
                "Warm measured turn count:",
                "Warm p50 first-agent-audio latency seconds:",
                "Warm p90 first-agent-audio latency seconds:",
                "Tool request count:",
                "Tool boundary passed:",
                "Project tool called:",
                "Response follows project tool:",
                "Product truth drift count:",
                "Fake side effect count:",
                "Strong live target met:",
                "Early demo target met:",
                "Latency classification:",
                "Real customer data allowed: `false`",
                "Final ElevenLabs replacement claimed: `false`",
            ]
        )
    elif decision.get("phase") in {"4J5", "4J5B"}:
        required_report_lines.remove("Public tool endpoint required:")
        required_report_lines.extend(
            [
                "WebSocket audio sandbox run status:",
                "WebSocket audio quality blocker classification:",
                "Provider call made:",
                "Ultravox session created:",
                "Join URL received:",
                "WebSocket connected:",
                "Manual audio inputs found:",
                "Manual audio conversion succeeded:",
                "Prepared audio input count:",
                "Manual audio converter used:",
                "Synthetic audio generation succeeded:",
                "Synthetic audio turns attempted:",
                "Synthetic audio turns completed:",
                "User transcript count:",
                "Agent transcript count:",
                "Agent audio chunks received:",
                "Agent audio bytes received:",
                "Tool call attempted:",
                "Tool call succeeded:",
                "Tool boundary enforced:",
                "Project tool called:",
                "Response follows project tool:",
                "Local HTTP tool request count:",
                "Real customer data allowed: `false`",
            ]
        )
    elif decision.get("phase") == "4J4":
        required_report_lines.remove("Public tool endpoint required:")
        required_report_lines.extend(
            [
                "WebSocket sandbox run status:",
                "WebSocket quality blocker classification:",
                "Provider call made:",
                "Ultravox session created:",
                "Join URL received:",
                "WebSocket connected:",
                "Synthetic turns attempted:",
                "Synthetic turns completed:",
                "Tool call attempted:",
                "Tool call succeeded:",
                "Tool boundary enforced:",
                "Project tool called:",
                "Response follows project tool:",
                "HTTP tool endpoint request count:",
                "Tool result sent count:",
                "Real customer data allowed: `false`",
            ]
        )
    elif decision.get("phase") == "4J3":
        required_report_lines.remove("Public tool endpoint required:")
        required_report_lines.extend(
            [
                "Explicit cloudflared path present:",
                "Explicit cloudflared path exists:",
                "Cloudflared available:",
                "Cloudflared DNS failed before:",
                "Ngrok available:",
                "Ngrok auth configured:",
                "Ngrok path source:",
                "Selected preferred tool:",
                "Tunnel preflight only:",
                "Tunnel attempted:",
                "DNS success:",
                "HTTP success:",
                "Auth preflight success:",
                "Public endpoint test passed:",
                "Provider call attempted:",
            ]
        )
    elif local_endpoint is not None:
        required_report_lines.extend(
            [
                "Local tool endpoint completed: `true`",
                "Local tool endpoint passed: `true`",
                "Public tunnel opened: `false`",
            ]
        )
    for line in required_report_lines:
        if line not in report_text:
            fail(f"decision report missing line: {line}")
    print("ULTRAVOX hosted feasibility decision validation passed.")


if __name__ == "__main__":
    main()
