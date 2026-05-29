#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PACKET_RESULT = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-AUDIO-LISTENING-REVIEW-001" / "result.json"
MANUAL_TEMPLATE_JSON = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-AUDIO-LISTENING-REVIEW-MANUAL-001" / "manual_review_template.json"
MANUAL_IMPORT_RESULT = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-AUDIO-LISTENING-REVIEW-MANUAL-001" / "result.json"
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


def load_optional_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    return load_json(path)


def assert_no_secret(label: str, text: str) -> None:
    match = SECRET_PATTERN.search(text)
    if match:
        fail(f"secret-like value found in {label}: {match.group(0)!r}")


def assert_false(payload: dict[str, Any], key: str) -> None:
    if payload.get(key) is not False:
        fail(f"{key} must be false")


def expected_recommendation(manual_import: dict[str, Any], transcript: dict[str, Any], latency: dict[str, Any], tool: dict[str, Any], decision: dict[str, Any]) -> str:
    manual = manual_import.get("listening_review_status") or decision.get("manual_listening_review_status")
    if manual in {None, "pending_manual_review"}:
        return "user_listen_to_ultravox_agent_audio"
    if transcript.get("transcript_quality_passed") is not True:
        return "fix audio format / turn timing before another provider run"
    if tool.get("tool_boundary_passed") is not True:
        return "fix tool declaration/prompt before more audio testing"
    if manual_import.get("quality_promising") is True and latency.get("live_ready_latency") is not True:
        return "warm-session latency benchmark next"
    if manual_import.get("quality_promising") is True:
        return "limited synthetic voice conversation evaluation next"
    return "user_listen_to_ultravox_agent_audio"


def main() -> None:
    packet = load_json(PACKET_RESULT)
    manual = load_json(MANUAL_TEMPLATE_JSON)
    manual_import = load_optional_json(MANUAL_IMPORT_RESULT)
    transcript = load_json(TRANSCRIPT_RESULT)
    latency = load_json(LATENCY_RESULT)
    tool = load_json(TOOL_RESULT)
    decision = load_json(DECISION_RESULT)
    report = DECISION_REPORT.read_text(encoding="utf-8") if DECISION_REPORT.is_file() else ""
    if not report:
        fail(f"missing file: {rel(DECISION_REPORT)}")
    assert_no_secret(
        "review decision evidence",
        json.dumps(packet) + json.dumps(manual) + json.dumps(manual_import) + json.dumps(transcript) + json.dumps(latency) + json.dumps(tool) + json.dumps(decision) + report,
    )

    if decision.get("evaluation_id") != "ULTRAVOX-AUDIO-SANDBOX-REVIEW-DECISION-001":
        fail("unexpected audio sandbox review decision evaluation_id")
    if decision.get("phase") not in {"4J6", "4J6B"}:
        fail("review decision must record phase 4J6 or 4J6B")
    expected = expected_recommendation(manual_import, transcript, latency, tool, decision)
    if decision.get("recommendation") != expected:
        fail(f"recommendation must be {expected!r}, got {decision.get('recommendation')!r}")
    expected_manual_status = manual_import.get("listening_review_status") or "pending_manual_review"
    if decision.get("manual_listening_review_status") != expected_manual_status:
        fail("manual listening review status must match manual import result")
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
        fail("next provider run must not be allowed by this review decision")
    if decision.get("tool_boundary_passed") is not True:
        fail("current 4J6 decision should preserve passing tool-boundary evidence")
    if decision.get("transcript_quality_passed") is not True:
        fail("current 4J6 decision should preserve passing transcript evidence")

    required_report_lines = [
        f"Recommendation: `{expected}`",
        f"Manual listening review status: `{expected_manual_status}`",
        "Next provider run allowed now: `false`",
        "Live wiring allowed: `false`",
        "Production call allowed: `false`",
        "Real customer data allowed: `false`",
        "Runtime behavior changed: `false`",
        "Response text changed: `false`",
    ]
    if manual_import.get("quality_promising") is True:
        required_report_lines.extend(
            [
                "Secondary recommendation: `test Ultravox voice/voice-ID options later`",
                "Final ElevenLabs replacement claimed: `false`",
            ]
        )
    for line in required_report_lines:
        if line not in report:
            fail(f"review decision report missing line: {line}")

    print("ULTRAVOX audio sandbox review decision validation passed.")


if __name__ == "__main__":
    main()
