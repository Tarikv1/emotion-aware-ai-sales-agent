#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-AUDIO-LATENCY-AUDIT-001" / "result.json"
REPORT_PATH = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-AUDIO-LATENCY-AUDIT-001" / "report.md"
AUDIT_SCRIPT = ROOT / "scripts" / "audit_ultravox_audio_latency_001.py"
SECRET_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9_-]{20,}|[A-Za-z0-9]{8}\.[A-Za-z0-9]{32}|ULTRAVOX_API_KEY\s*=\s*(?!\.\.\.|<redacted>|your-api-key)[^\s]+|PROJECT_ULTRAVOX_TOOL_TOKEN\s*=\s*(?!\.\.\.|<redacted>|your-token)[^\s]+|Authorization:\s*Bearer\s+[A-Za-z0-9]|X-API-Key:\s*(?!<redacted>|your-api-key)[A-Za-z0-9]|X-Project-Tool-Token:\s*(?!<redacted>|your-token)[A-Za-z0-9]|wss://[^\"'\s]+|https://voice\.ultravox\.ai/[^\"'\s]+)"
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


def assert_no_secret(label: str, text: str) -> None:
    match = SECRET_PATTERN.search(text)
    if match:
        fail(f"secret-like value found in {label}: {match.group(0)!r}")


def assert_false(payload: dict[str, Any], key: str) -> None:
    if payload.get(key) is not False:
        fail(f"{key} must be false")


def main() -> None:
    result = load_json(RESULT_PATH)
    report = REPORT_PATH.read_text(encoding="utf-8") if REPORT_PATH.is_file() else ""
    if not report:
        fail(f"missing file: {rel(REPORT_PATH)}")
    if not AUDIT_SCRIPT.is_file():
        fail(f"missing file: {rel(AUDIT_SCRIPT)}")
    assert_no_secret("latency audit evidence", json.dumps(result) + report)

    if result.get("evaluation_id") != "ULTRAVOX-AUDIO-LATENCY-AUDIT-001":
        fail("unexpected latency audit evaluation_id")
    if result.get("phase") != "4J6":
        fail("latency audit must record phase 4J6")
    observed = result.get("current_observed_latency_seconds")
    if observed != result.get("first_agent_audio_latency_seconds"):
        fail("current observed latency must match first agent audio latency")
    if observed != 8.599:
        fail("current observed 4J5B latency must be 8.599 seconds")
    if result.get("live_target_seconds") != {"min": 2, "max": 3}:
        fail("latency audit must record the 2-3s live target")
    if result.get("live_ready_latency") is not False:
        fail("8.599s latency must not be marked live-ready")
    if result.get("needs_warm_turn_benchmark") is not True:
        fail("latency audit must require a warm-turn benchmark")
    if result.get("another_provider_run_should_separate_cold_start_vs_warm_turn") is not True:
        fail("latency audit must recommend separating cold-start vs warm-turn latency")
    if result.get("first_agent_audio_latency_likely_includes_session_setup_startup") is not False:
        fail("first-agent-audio timing should not claim tunnel/session setup inclusion")
    for key in (
        "new_provider_call_made",
        "new_audio_generated",
        "audio_files_copied",
        "audio_files_committed",
        "outbound_phone_call_made",
        "real_customer_data_used",
        "raw_private_audio_or_transcripts_used",
        "live_wiring_allowed",
        "production_call_allowed",
        "real_customer_data_allowed",
        "runtime_behavior_changed",
        "response_text_changed",
    ):
        assert_false(result, key)

    required_report_lines = [
        "First agent audio latency seconds: `8.599`",
        "Live target seconds: `2-3`",
        "Live-ready latency: `false`",
        "Needs warm-turn benchmark: `true`",
        "Another provider run should separate cold-start vs warm-turn latency: `true`",
        "New provider call made: `false`",
        "New audio generated: `false`",
        "Live wiring allowed: `false`",
        "Production call allowed: `false`",
    ]
    for line in required_report_lines:
        if line not in report:
            fail(f"latency audit report missing line: {line}")

    print("ULTRAVOX audio latency audit validation passed.")


if __name__ == "__main__":
    main()
