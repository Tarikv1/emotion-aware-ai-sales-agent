#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-TUNNEL-DIAGNOSTICS-001" / "result.json"
REPORT_PATH = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-TUNNEL-DIAGNOSTICS-001" / "report.md"
TUNNEL_RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-TUNNEL-SANDBOX-001" / "result.json"
ENV_PATH = ROOT / "runtime" / "config" / "local" / "ultravox.env"
SECRET_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9_-]{20,}|[A-Za-z0-9]{8}\.[A-Za-z0-9]{32}|ULTRAVOX_API_KEY\s*=\s*(?!\.\.\.|<redacted>|your-api-key)[^\s]+|PROJECT_ULTRAVOX_TOOL_TOKEN\s*=\s*(?!\.\.\.|<redacted>|your-token)[^\s]+|Authorization:\s*Bearer\s+[A-Za-z0-9]|X-API-Key:\s*(?!<redacted>|your-api-key)[A-Za-z0-9]|X-Project-Tool-Token:\s*(?!<redacted>|your-token)[A-Za-z0-9])"
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


def git_ignored(path: Path) -> bool:
    completed = subprocess.run(
        ["git", "check-ignore", "-v", rel(path)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    return completed.returncode == 0


def assert_no_secret(text: str) -> None:
    match = SECRET_PATTERN.search(text)
    if match:
        fail(f"secret-like token found: {match.group(0)!r}")


def main() -> None:
    result = load_json(RESULT_PATH)
    tunnel = load_json(TUNNEL_RESULT_PATH)
    report = REPORT_PATH.read_text(encoding="utf-8") if REPORT_PATH.is_file() else ""
    if not report:
        fail(f"missing file: {rel(REPORT_PATH)}")
    assert_no_secret(json.dumps(result) + json.dumps(tunnel) + report)
    if ENV_PATH.exists() and not git_ignored(ENV_PATH):
        fail("runtime/config/local/ultravox.env exists but is not ignored by Git")

    if result.get("evaluation_id") != "ULTRAVOX-TUNNEL-DIAGNOSTICS-001":
        fail("unexpected tunnel diagnostics evaluation_id")
    if result.get("phase") != "4J3E":
        fail("diagnostics must record phase 4J3E")
    for key in (
        "cloudflared_available",
        "explicit_cloudflared_path_used",
        "explicit_cloudflared_path_present",
        "explicit_cloudflared_path_exists",
        "tunnel_preflight_only",
        "tunnel_attempted",
        "tunnel_url_created",
        "tunnel_url_full_recorded",
        "dns_success",
        "http_success",
        "auth_preflight_success",
        "valid_request_success",
        "missing_token_401",
        "invalid_token_401",
        "provider_call_attempted",
        "provider_call_made",
        "secrets_logged",
        "raw_audio_committed",
        "audio_committed",
        "raw_private_audio_or_transcripts_used",
        "outbound_phone_call_made",
        "real_customer_data_used",
        "live_wiring_allowed",
        "production_call_allowed",
        "runtime_behavior_changed",
        "response_text_changed",
    ):
        if not isinstance(result.get(key), bool):
            fail(f"{key} must be a boolean")
    for key in ("dns_attempt_count", "http_attempt_count"):
        if not isinstance(result.get(key), int):
            fail(f"{key} must be an integer")
    for key in ("dns_first_success_seconds", "dns_last_error", "http_first_success_seconds", "http_last_status", "http_last_error", "blocker"):
        if key not in result:
            fail(f"{key} must exist")
    if result.get("tunnel_url_full_recorded") is not False:
        fail("diagnostics must not record the full tunnel URL")
    if result.get("provider_call_made") and not result.get("provider_call_attempted"):
        fail("provider_call_made cannot be true unless provider_call_attempted is true")
    if result.get("provider_call_attempted") and not (
        result.get("dns_success") and result.get("http_success") and result.get("auth_preflight_success")
    ):
        fail("provider call must not be attempted unless DNS, HTTP, and auth preflight passed")
    if result.get("tunnel_preflight_only") and result.get("provider_call_attempted") is not False:
        fail("provider call must not be attempted in tunnel-preflight-only mode")
    for key in ("secrets_logged", "raw_audio_committed", "audio_committed", "live_wiring_allowed", "production_call_allowed"):
        if result.get(key) is not False:
            fail(f"{key} must be false")

    for key in (
        "tunnel_preflight_only",
        "tunnel_attempted",
        "tunnel_url_created",
        "dns_success",
        "http_success",
        "auth_preflight_success",
        "provider_call_attempted",
        "provider_call_made",
    ):
        if result.get(key) != tunnel.get(key):
            fail(f"{key} must match tunnel sandbox evidence")
    if "DNS success:" not in report or "HTTP success:" not in report or "Auth preflight success:" not in report:
        fail("diagnostics report must include DNS, HTTP, and auth readiness")
    print("ULTRAVOX tunnel diagnostics validation passed.")


if __name__ == "__main__":
    main()
