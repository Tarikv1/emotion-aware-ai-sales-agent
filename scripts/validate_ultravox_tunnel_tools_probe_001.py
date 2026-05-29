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
    for key in ("probe_only",):
        if result.get(key) is not True:
            fail(f"{key} must be true")
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
    if "does not open a tunnel" not in report:
        fail("report must state probe did not open a tunnel")
    print("ULTRAVOX tunnel tools probe validation passed.")


if __name__ == "__main__":
    main()
