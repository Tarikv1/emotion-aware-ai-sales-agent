#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-TUNNEL-SANDBOX-QUALITY-001" / "result.json"
REPORT_PATH = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-TUNNEL-SANDBOX-QUALITY-001" / "report.md"
TUNNEL_RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-TUNNEL-SANDBOX-001" / "result.json"
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
    tunnel = load_json(TUNNEL_RESULT_PATH)
    report = REPORT_PATH.read_text(encoding="utf-8") if REPORT_PATH.is_file() else ""
    if not report:
        fail(f"missing file: {rel(REPORT_PATH)}")
    assert_no_secret(json.dumps(result) + json.dumps(tunnel) + report)

    if result.get("evaluation_id") != "ULTRAVOX-TUNNEL-SANDBOX-QUALITY-001":
        fail("unexpected tunnel sandbox quality evaluation_id")
    if result.get("phase") != "4J3":
        fail("quality evidence must record phase 4J3")
    for key in ("sandbox_run", "provider_call_made", "ultravox_session_created", "tool_call_attempted", "tool_call_succeeded", "hosted_turns_attempted"):
        if result.get(key) != tunnel.get(key):
            fail(f"{key} must match tunnel sandbox evidence")
    for key in ("dns_success", "http_success", "auth_preflight_success", "provider_call_gate_passed"):
        if result.get(key) != tunnel.get(key):
            fail(f"{key} must match tunnel sandbox evidence")
    for key in ("cloudflared_available", "cloudflared_dns_failed_before", "ngrok_available", "ngrok_auth_configured", "tunnel_tool_used"):
        if result.get(key) != tunnel.get(key):
            fail(f"{key} must match tunnel sandbox evidence")
    if result.get("hosted_turns_attempted") == 0 and not result.get("hosted_turns_not_run_reason"):
        fail("quality evidence must explain why hosted turns were not run")
    for field in (
        "product_truth_drift_count",
        "unsupported_claim_count",
        "fake_side_effect_count",
        "crm_email_calendar_claim_count",
        "internal_label_leak_count",
        "source_boundary_violation_count",
        "memory_conflict_count",
    ):
        if result.get(field) != 0:
            fail(f"{field} must be 0")
    for key in (
        "outbound_phone_call_made",
        "real_customer_data_used",
        "raw_private_audio_or_transcripts_used",
        "raw_audio_stored",
        "audio_committed",
        "secrets_logged",
        "side_effects_allowed",
        "live_wiring_allowed",
        "production_call_allowed",
        "runtime_behavior_changed",
        "response_text_changed",
    ):
        if result.get(key) is not False:
            fail(f"{key} must be false")
    if "Hosted turns not run reason" not in report:
        fail("quality report must record hosted-turn reason")
    print("ULTRAVOX tunnel sandbox quality validation passed.")


if __name__ == "__main__":
    main()
