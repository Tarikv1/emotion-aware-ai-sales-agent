#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
FILLED_PATH = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-AUDIO-LISTENING-REVIEW-MANUAL-001" / "manual_review_filled.json"
RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-AUDIO-LISTENING-REVIEW-MANUAL-001" / "result.json"
REPORT_PATH = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-AUDIO-LISTENING-REVIEW-MANUAL-001" / "report.md"
DECISION_RESULT = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-AUDIO-SANDBOX-REVIEW-DECISION-001" / "result.json"
DECISION_REPORT = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-AUDIO-SANDBOX-REVIEW-DECISION-001" / "report.md"
IMPORT_SCRIPT = ROOT / "scripts" / "import_ultravox_audio_manual_review_001.py"
SECRET_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9_-]{20,}|[A-Za-z0-9]{8}\.[A-Za-z0-9]{32}|ULTRAVOX_API_KEY\s*=\s*(?!\.\.\.|<redacted>|your-api-key)[^\s]+|PROJECT_ULTRAVOX_TOOL_TOKEN\s*=\s*(?!\.\.\.|<redacted>|your-token)[^\s]+|Authorization:\s*Bearer\s+[A-Za-z0-9]|X-API-Key:\s*(?!<redacted>|your-api-key)[A-Za-z0-9]|X-Project-Tool-Token:\s*(?!<redacted>|your-token)[A-Za-z0-9]|wss://[^\"'\s]+|https://voice\.ultravox\.ai/[^\"'\s]+)"
)


EXPECTED_RATINGS = {
    "intelligibility": 5,
    "naturalness": 3,
    "voice_quality": 5,
    "sales_tone": 3.5,
    "pacing": 4.5,
    "artifact_severity": 1,
    "interruption_turn_taking_quality": 3,
    "thesis_demo_suitability": 4,
    "product_fallback_suitability": 5,
}


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


def assert_close(actual: Any, expected: float, label: str) -> None:
    if not isinstance(actual, (int, float)) or abs(float(actual) - expected) > 0.0001:
        fail(f"{label} must be {expected}, got {actual!r}")


def main() -> None:
    filled = load_json(FILLED_PATH)
    result = load_json(RESULT_PATH)
    decision = load_json(DECISION_RESULT)
    report = REPORT_PATH.read_text(encoding="utf-8") if REPORT_PATH.is_file() else ""
    decision_report = DECISION_REPORT.read_text(encoding="utf-8") if DECISION_REPORT.is_file() else ""
    if not report:
        fail(f"missing file: {rel(REPORT_PATH)}")
    if not decision_report:
        fail(f"missing file: {rel(DECISION_REPORT)}")
    if not IMPORT_SCRIPT.is_file():
        fail(f"missing file: {rel(IMPORT_SCRIPT)}")
    assert_no_secret("manual review import evidence", json.dumps(filled) + json.dumps(result) + json.dumps(decision) + report + decision_report)

    if filled.get("evaluation_id") != "ULTRAVOX-AUDIO-LISTENING-REVIEW-MANUAL-001":
        fail("unexpected filled review evaluation_id")
    if result.get("evaluation_id") != "ULTRAVOX-AUDIO-LISTENING-REVIEW-MANUAL-IMPORT-001":
        fail("unexpected manual import evaluation_id")
    if result.get("phase") != "4J6B":
        fail("manual import must record phase 4J6B")
    if result.get("filled_review_present") is not True:
        fail("filled manual review must be present")
    if result.get("listening_review_status") != "pass_for_product_fallback":
        fail("expected listening review status pass_for_product_fallback")
    if result.get("quality_classification") != "promising":
        fail("manual review quality must be classified as promising")
    if result.get("latency_live_ready") is not False:
        fail("manual review import must not claim live-ready latency")
    if result.get("warm_turn_benchmark_needed") is not True:
        fail("manual review import must preserve warm-turn benchmark need")
    if result.get("voice_selection_limitation_noted") is not True:
        fail("voice selection limitation must be recorded")
    if result.get("voice_id_alignment_needed") is not True:
        fail("voice ID alignment need must be recorded")

    ratings = result.get("ratings")
    if not isinstance(ratings, dict):
        fail("ratings must be an object")
    for key, expected in EXPECTED_RATINGS.items():
        assert_close(ratings.get(key), float(expected), key)
    assert_close(result.get("raw_rating_average"), 3.7778, "raw_rating_average")
    assert_close(result.get("quality_score_average"), 4.2222, "quality_score_average")
    assert_close(result.get("demo_suitability_average"), 4.4, "demo_suitability_average")
    assert_close(result.get("product_fallback_average"), 5.0, "product_fallback_average")

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

    if decision.get("phase") == "4J7":
        if decision.get("warm_session_latency_audit_id") != "ULTRAVOX-WARM-SESSION-LATENCY-AUDIT-001":
            fail("phase 4J7 decision must reference the warm-session latency audit")
    elif decision.get("recommendation") != "warm-session latency benchmark next":
        fail("decision recommendation must become warm-session latency benchmark next")
    if decision.get("secondary_recommendation") != "test Ultravox voice/voice-ID options later":
        fail("decision must include the voice/voice-ID secondary recommendation")
    if decision.get("manual_listening_review_status") != "pass_for_product_fallback":
        fail("decision must import the manual listening status")
    if decision.get("audio_quality_promising") is not True:
        fail("decision must record promising audio quality")
    for key in (
        "live_wiring_allowed",
        "production_call_allowed",
        "real_customer_data_allowed",
        "new_provider_call_made",
        "new_audio_generated",
        "audio_files_committed",
        "runtime_behavior_changed",
        "response_text_changed",
    ):
        assert_false(decision, key)

    required_report_lines = [
        "Listening review status: `pass_for_product_fallback`",
        "Quality classification: `promising`",
        "Raw rating average: `3.7778`",
        "Quality score average: `4.2222`",
        "Voice/voice-ID note:",
        "Live wiring allowed: `false`",
        "Production call allowed: `false`",
        "Runtime behavior changed: `false`",
        "Response text changed: `false`",
    ]
    for line in required_report_lines:
        if line not in report:
            fail(f"manual review import report missing line: {line}")
    if decision.get("phase") == "4J7":
        if "Warm p50 first-agent-audio latency seconds:" not in decision_report:
            fail("phase 4J7 decision report must include warm-session latency metrics")
    elif "Recommendation: `warm-session latency benchmark next`" not in decision_report:
        fail("decision report must include warm-session latency benchmark recommendation")
    if "Secondary recommendation: `test Ultravox voice/voice-ID options later`" not in decision_report:
        fail("decision report must include voice/voice-ID note")

    print("ULTRAVOX audio manual review import validation passed.")


if __name__ == "__main__":
    main()
