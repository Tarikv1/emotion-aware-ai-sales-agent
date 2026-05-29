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
        return "fix tunnel URL parsing"
    if status == "blocked_tunnel_dns_failed":
        return "retry tunnel later, test local DNS/trycloudflare reachability, or use ngrok/cloudflared named tunnel"
    if status == "blocked_tunnel_http_failed":
        return "fix tunnel target/local server path"
    if status == "blocked_tunnel_auth_failed":
        return "fix token/header handling"
    if status == "blocked_no_tunnel_tool":
        return "install cloudflared or ngrok, rerun"
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


def main() -> None:
    mock = load_json(MOCK_RESULT)
    hosted = load_json(HOSTED_RESULT)
    local_endpoint = load_json(LOCAL_ENDPOINT_RESULT) if LOCAL_ENDPOINT_RESULT.is_file() else None
    tunnel = load_json(TUNNEL_RESULT) if TUNNEL_RESULT.is_file() else None
    decision = load_json(DECISION_RESULT)
    report_text = DECISION_REPORT.read_text(encoding="utf-8") if DECISION_REPORT.is_file() else ""
    if not report_text:
        fail(f"missing file: {rel(DECISION_REPORT)}")

    if decision.get("evaluation_id") != "ULTRAVOX-HOSTED-FEASIBILITY-DECISION-001":
        fail("unexpected feasibility decision evaluation_id")
    if decision.get("phase") not in {"4J1", "4J2", "4J3"}:
        fail("feasibility decision must record phase 4J1, 4J2, or 4J3")
    expected = expected_tunnel_recommendation(tunnel) if decision.get("phase") == "4J3" and tunnel is not None else expected_recommendation(mock, hosted, local_endpoint)
    if decision.get("recommendation") != expected:
        fail(f"recommendation must be {expected!r}, got {decision.get('recommendation')!r}")

    for key in ("live_wiring_allowed", "production_call_allowed", "real_customer_data_allowed"):
        if decision.get(key) is not False:
            fail(f"{key} must always stay false")
    active_evidence = tunnel if decision.get("phase") == "4J3" and tunnel is not None else hosted
    for key in ("sandbox_run", "provider_call_made", "tool_call_attempted", "tool_call_succeeded", "public_tool_endpoint_required", "public_tool_endpoint_available"):
        if active_evidence.get(key) is not None and decision.get(key) != active_evidence.get(key):
            fail(f"{key} must match active sandbox evidence")
    if local_endpoint is not None and decision.get("phase") != "4J3":
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
    if decision.get("phase") == "4J3":
        required_report_lines.remove("Public tool endpoint required:")
        required_report_lines.extend(
            [
                "Explicit cloudflared path present:",
                "Explicit cloudflared path exists:",
                "Cloudflared available:",
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
