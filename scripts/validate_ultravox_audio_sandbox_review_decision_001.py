#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PACKET_RESULT = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-AUDIO-LISTENING-REVIEW-001" / "result.json"
MANUAL_TEMPLATE_JSON = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-AUDIO-LISTENING-REVIEW-MANUAL-001" / "manual_review_template.json"
TRANSCRIPT_RESULT = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-AUDIO-TRANSCRIPT-QUALITY-001" / "result.json"
LATENCY_RESULT = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-AUDIO-LATENCY-AUDIT-001" / "result.json"
TOOL_RESULT = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-AUDIO-TOOL-BOUNDARY-AUDIT-001" / "result.json"
DECISION_RESULT = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-AUDIO-SANDBOX-REVIEW-DECISION-001" / "result.json"
DECISION_REPORT = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-AUDIO-SANDBOX-REVIEW-DECISION-001" / "report.md"
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


def expected_recommendation(packet: dict[str, Any], transcript: dict[str, Any], latency: dict[str, Any], tool: dict[str, Any], decision: dict[str, Any]) -> str:
    manual = decision.get("manual_listening_review_status")
    if manual == "pending_manual_review" or packet.get("status") == "pending_manual_review":
        return "user_listen_to_ultravox_agent_audio"
    if transcript.get("transcript_quality_passed") is not True:
        return "fix audio format / turn timing before another provider run"
    if tool.get("tool_boundary_passed") is not True:
        return "fix tool declaration/prompt before more audio testing"
    if latency.get("live_ready_latency") is not True:
        return "run warm-session latency benchmark next, still synthetic only"
    if decision.get("user_audio_review_good") is True:
        return "limited synthetic voice conversation evaluation next"
    return "user_listen_to_ultravox_agent_audio"


def main() -> None:
    packet = load_json(PACKET_RESULT)
    manual = load_json(MANUAL_TEMPLATE_JSON)
    transcript = load_json(TRANSCRIPT_RESULT)
    latency = load_json(LATENCY_RESULT)
    tool = load_json(TOOL_RESULT)
    decision = load_json(DECISION_RESULT)
    report = DECISION_REPORT.read_text(encoding="utf-8") if DECISION_REPORT.is_file() else ""
    if not report:
        fail(f"missing file: {rel(DECISION_REPORT)}")
    assert_no_secret(
        "review decision evidence",
        json.dumps(packet) + json.dumps(manual) + json.dumps(transcript) + json.dumps(latency) + json.dumps(tool) + json.dumps(decision) + report,
    )

    if decision.get("evaluation_id") != "ULTRAVOX-AUDIO-SANDBOX-REVIEW-DECISION-001":
        fail("unexpected audio sandbox review decision evaluation_id")
    if decision.get("phase") != "4J6":
        fail("review decision must record phase 4J6")
    expected = expected_recommendation(packet, transcript, latency, tool, decision)
    if decision.get("recommendation") != expected:
        fail(f"recommendation must be {expected!r}, got {decision.get('recommendation')!r}")
    if decision.get("manual_listening_review_status") != "pending_manual_review":
        fail("manual listening review should be pending until Tarik listens")
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
        assert_false(decision, key)
    if decision.get("next_provider_run_allowed_now") is not False:
        fail("next provider run must not be allowed while manual listening is pending")
    if decision.get("tool_boundary_passed") is not True:
        fail("current 4J6 decision should preserve passing tool-boundary evidence")
    if decision.get("transcript_quality_passed") is not True:
        fail("current 4J6 decision should preserve passing transcript evidence")

    required_report_lines = [
        f"Recommendation: `{expected}`",
        "Manual listening review status: `pending_manual_review`",
        "Next provider run allowed now: `false`",
        "Live wiring allowed: `false`",
        "Production call allowed: `false`",
        "Real customer data allowed: `false`",
        "Runtime behavior changed: `false`",
        "Response text changed: `false`",
    ]
    for line in required_report_lines:
        if line not in report:
            fail(f"review decision report missing line: {line}")

    print("ULTRAVOX audio sandbox review decision validation passed.")


if __name__ == "__main__":
    main()
