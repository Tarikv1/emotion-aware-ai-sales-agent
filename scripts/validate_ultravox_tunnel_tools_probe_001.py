#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-TUNNEL-TOOLS-PROBE-001" / "result.json"
REPORT_PATH = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-TUNNEL-TOOLS-PROBE-001" / "report.md"
SECRET_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9_-]{20,}|[A-Za-z0-9]{8}\.[A-Za-z0-9]{32}|ULTRAVOX_API_KEY\s*=\s*(?!\.\.\.|<redacted>|your-api-key)[^\s]+|PROJECT_ULTRAVOX_TOOL_TOKEN\s*=\s*(?!\.\.\.|<redacted>|your-token)[^\s]+|Authorization:\s*Bearer\s+[A-Za-z0-9]|X-Project-Tool-Token:\s*(?!<redacted>|your-token)[A-Za-z0-9])"
)


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


def assert_no_secret(text: str) -> None:
    match = SECRET_PATTERN.search(text)
    if match:
        fail(f"secret-like token found: {match.group(0)!r}")


def main() -> None:
    result = load_json(RESULT_PATH)
    report = REPORT_PATH.read_text(encoding="utf-8") if REPORT_PATH.is_file() else ""
    if not report:
        fail(f"missing file: {rel(REPORT_PATH)}")
    assert_no_secret(json.dumps(result) + report)
    if result.get("evaluation_id") != "ULTRAVOX-TUNNEL-TOOLS-PROBE-001":
        fail("unexpected tunnel tools probe evaluation_id")
    if result.get("phase") != "4J3":
        fail("tunnel tools probe must record phase 4J3")
    for key in ("env_file_exists", "env_file_ignored_by_git", "env_file_loaded", "unsafe_secret_file"):
        if key not in result or not isinstance(result.get(key), bool):
            fail(f"{key} must be a boolean")
    for key in ("probe_only",):
        if result.get(key) is not True:
            fail(f"{key} must be true")
    for key in (
        "explicit_cloudflared_path_present",
        "explicit_cloudflared_path_exists",
        "explicit_cloudflared_version_ok",
        "cloudflared_available",
        "cloudflared_dns_failed_before",
        "cloudflared_passed_before",
        "ngrok_available",
        "ngrok_version_ok",
        "ngrok_config_check_attempted",
        "ngrok_config_check_succeeded",
        "explicit_ngrok_path_present",
        "explicit_ngrok_path_exists",
        "explicit_ngrok_version_ok",
    ):
        if not isinstance(result.get(key), bool):
            fail(f"{key} must be a boolean")
    if result.get("explicit_cloudflared_path_present") and result.get("explicit_cloudflared_executable") in {"", None}:
        fail("explicit cloudflared path evidence must include a safe executable path or redacted marker")
    if result.get("cloudflared_dns_failed_before") and result.get("ngrok_available"):
        if result.get("selected_tunnel_tool") != "ngrok":
            fail("ngrok must be selected when cloudflared DNS failed before and ngrok is available")
    elif result.get("cloudflared_available") and result.get("cloudflared_passed_before"):
        if result.get("selected_tunnel_tool") != "cloudflared":
            fail("cloudflared must be selected when it is available and previously passed readiness")
    if result.get("selected_preferred_tool") != result.get("selected_tunnel_tool"):
        fail("selected_preferred_tool must match selected_tunnel_tool")
    if result.get("ngrok_available") and not result.get("ngrok_config_check_attempted"):
        fail("ngrok config check must be attempted when ngrok is available")
    if result.get("ngrok_auth_configured") not in {True, False, "unknown"}:
        fail("ngrok_auth_configured must be true, false, or unknown")
    if result.get("ngrok_auth_configured") is True and result.get("ngrok_config_check_succeeded") is not True:
        fail("ngrok auth configured true requires successful config check")
    if result.get("selected_tunnel_tool") and not result.get("selected_tunnel_executable"):
        fail("selected tunnel executable must be recorded when a tool is selected")
    for key in (
        "tunnel_opened",
        "provider_calls_made",
        "ultravox_hosted_call_made",
        "outbound_phone_call_made",
        "real_customer_data_used",
        "raw_private_audio_or_transcripts_used",
        "secrets_logged",
        "live_wiring_allowed",
        "production_call_allowed",
        "runtime_behavior_changed",
        "response_text_changed",
    ):
        if result.get(key) is not False:
            fail(f"{key} must be false")
    tools = result.get("candidate_tunnel_tools", {})
    for name in ("cloudflared", "ngrok", "localtunnel", "npx"):
        if name not in tools:
            fail(f"missing probe details for {name}")
    if tools.get("ngrok", {}).get("available") != result.get("ngrok_available"):
        fail("top-level ngrok_available must match candidate tool details")
    if any("_executable_for_run" in json.dumps(tool) for tool in tools.values()):
        fail("internal executable-for-run fields must not be written to probe evidence")
    if "does not open a tunnel" not in report:
        fail("report must state probe did not open a tunnel")
    print("ULTRAVOX tunnel tools probe validation passed.")


if __name__ == "__main__":
    main()
