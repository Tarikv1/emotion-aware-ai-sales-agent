#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-AUDIO-TRANSCRIPT-QUALITY-001" / "result.json"
REPORT_PATH = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-AUDIO-TRANSCRIPT-QUALITY-001" / "report.md"
AUDIT_SCRIPT = ROOT / "scripts" / "audit_ultravox_audio_transcripts_001.py"
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
    assert_no_secret("transcript quality evidence", json.dumps(result) + report)

    if result.get("evaluation_id") != "ULTRAVOX-AUDIO-TRANSCRIPT-QUALITY-001":
        fail("unexpected transcript quality evaluation_id")
    if result.get("phase") != "4J6":
        fail("transcript quality audit must record phase 4J6")
    for key in (
        "transcript_text_available",
        "user_audio_correctly_transcribed",
        "crm_preserved",
        "boundary_request_understood",
        "agent_response_respected_project_tool_output",
        "public_evidence_sanitized",
    ):
        if not isinstance(result.get(key), bool):
            fail(f"{key} must be a boolean")
    for key in (
        "new_provider_call_made",
        "new_audio_generated",
        "audio_files_copied",
        "audio_files_committed",
        "outbound_phone_call_made",
        "real_customer_data_used",
        "raw_private_audio_or_transcripts_used",
        "agent_invented_product_facts",
        "agent_claimed_fake_side_effects",
        "agent_exposed_internal_labels",
        "agent_claimed_openai_affiliation",
        "live_wiring_allowed",
        "production_call_allowed",
        "real_customer_data_allowed",
        "runtime_behavior_changed",
        "response_text_changed",
    ):
        assert_false(result, key)
    if result.get("user_transcript_count") != 2:
        fail("expected two user transcripts from 4J5B evidence")
    if int(result.get("agent_transcript_count", 0)) <= 0:
        fail("expected observed agent transcript evidence")
    expected_phrases = result.get("expected_user_phrases")
    if not isinstance(expected_phrases, list) or len(expected_phrases) != 2:
        fail("expected_user_phrases must contain two phrases")
    matches = result.get("expected_phrase_matches")
    if not isinstance(matches, list) or len(matches) != 2:
        fail("expected_phrase_matches must contain two entries")
    for match in matches:
        if match.get("exact_match") is not True and match.get("fuzzy_match") is not True:
            fail(f"expected phrase was not matched: {match.get('expected_phrase')}")
    if result.get("missing_transcript_text") is not False:
        fail("current 4J5B evidence has sanitized transcript text; missing_transcript_text must be false")
    if result.get("product_truth_drift_count") != 0 or result.get("fake_side_effect_count") != 0:
        fail("transcript audit must keep product drift and fake side effects at zero")

    required_report_lines = [
        "User transcript count:",
        "Agent transcript count:",
        "User audio correctly transcribed:",
        "CRM preserved:",
        "Boundary request understood:",
        "Agent response respected project tool output:",
        "Agent invented product facts: `false`",
        "Agent claimed fake side effects: `false`",
        "Agent exposed internal labels: `false`",
        "Agent claimed OpenAI affiliation: `false`",
        "Public evidence sanitized: `true`",
        "New provider call made: `false`",
        "New audio generated: `false`",
        "Live wiring allowed: `false`",
        "Production call allowed: `false`",
    ]
    for line in required_report_lines:
        if line not in report:
            fail(f"transcript quality report missing line: {line}")

    print("ULTRAVOX audio transcript quality validation passed.")


if __name__ == "__main__":
    main()
