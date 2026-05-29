#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
WARM_RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-WARM-SESSION-LATENCY-001" / "result.json"
AUDIT_RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-WARM-SESSION-LATENCY-AUDIT-001" / "result.json"
AUDIT_REPORT_PATH = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-WARM-SESSION-LATENCY-AUDIT-001" / "report.md"
FEASIBILITY_RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-HOSTED-FEASIBILITY-DECISION-001" / "result.json"
FEASIBILITY_REPORT_PATH = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-HOSTED-FEASIBILITY-DECISION-001" / "report.md"
REVIEW_RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-AUDIO-SANDBOX-REVIEW-DECISION-001" / "result.json"
REVIEW_REPORT_PATH = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-AUDIO-SANDBOX-REVIEW-DECISION-001" / "report.md"
OPTIMIZATION_AUDIT_RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-LATENCY-OPTIMIZATION-AUDIT-001" / "result.json"
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


def rounded(value: float | int | None) -> float | None:
    if value is None:
        return None
    return round(float(value), 3)


def percentile_nearest(values: list[float], pct: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, math.ceil((pct / 100.0) * len(ordered)) - 1))
    return rounded(ordered[index])


def median(values: list[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    midpoint = len(ordered) // 2
    if len(ordered) % 2:
        return rounded(ordered[midpoint])
    return rounded((ordered[midpoint - 1] + ordered[midpoint]) / 2.0)


def expected_recommendation(audit: dict[str, Any]) -> str:
    if audit.get("prepared_audio_available") is not True:
        return "prepare manual audio inputs"
    if audit.get("session_created") is not True or audit.get("websocket_connected") is not True:
        return "fix session/WebSocket before more provider usage"
    if audit.get("tool_boundary_passed") is not True:
        return "do not proceed"
    p50 = audit.get("warm_p50_first_agent_audio_latency_seconds")
    if isinstance(p50, (int, float)) and p50 <= 2.0:
        return "limited synthetic voice conversation evaluation next"
    if isinstance(p50, (int, float)) and p50 <= 3.0:
        return "thesis-demo synthetic voice evaluation next"
    if isinstance(p50, (int, float)) and p50 > 5.0:
        return "keep Ultravox as architecture candidate, investigate provider settings/voice/session configuration before more usage"
    if audit.get("audio_quality_promising") is True and isinstance(p50, (int, float)):
        return "test voice/session settings and warm-run repeat once"
    return "benchmark inconclusive"


def assert_false(payload: dict[str, Any], key: str) -> None:
    if payload.get(key) is not False:
        fail(f"{key} must be false")


def main() -> None:
    warm = load_json(WARM_RESULT_PATH)
    audit = load_json(AUDIT_RESULT_PATH)
    audit_report = AUDIT_REPORT_PATH.read_text(encoding="utf-8") if AUDIT_REPORT_PATH.is_file() else ""
    feasibility = load_json(FEASIBILITY_RESULT_PATH)
    feasibility_report = FEASIBILITY_REPORT_PATH.read_text(encoding="utf-8") if FEASIBILITY_REPORT_PATH.is_file() else ""
    review = load_json(REVIEW_RESULT_PATH)
    review_report = REVIEW_REPORT_PATH.read_text(encoding="utf-8") if REVIEW_REPORT_PATH.is_file() else ""
    optimization_audit = load_json(OPTIMIZATION_AUDIT_RESULT_PATH) if OPTIMIZATION_AUDIT_RESULT_PATH.is_file() else {}
    if not audit_report:
        fail(f"missing file: {rel(AUDIT_REPORT_PATH)}")
    if not feasibility_report:
        fail(f"missing file: {rel(FEASIBILITY_REPORT_PATH)}")
    if not review_report:
        fail(f"missing file: {rel(REVIEW_REPORT_PATH)}")
    assert_no_secret(
        "warm-session audit and refreshed decisions",
        json.dumps(warm) + json.dumps(audit) + audit_report + json.dumps(feasibility) + feasibility_report + json.dumps(review) + review_report + json.dumps(optimization_audit),
    )

    if audit.get("evaluation_id") != "ULTRAVOX-WARM-SESSION-LATENCY-AUDIT-001":
        fail("unexpected warm-session latency audit evaluation_id")
    latencies = [
        float(turn["user_turn_end_to_first_agent_audio_seconds"])
        for turn in warm.get("turns", [])
        if isinstance(turn, dict)
        and turn.get("measured_turn") is True
        and isinstance(turn.get("user_turn_end_to_first_agent_audio_seconds"), (int, float))
    ]
    if audit.get("measured_warm_turn_count") != len(latencies):
        fail("audit measured_warm_turn_count must match warm result")
    if audit.get("warm_p50_first_agent_audio_latency_seconds") != median(latencies):
        fail("audit p50 latency does not match warm result")
    expected_p90 = percentile_nearest(latencies, 90.0) if len(latencies) >= 2 else None
    if audit.get("warm_p90_first_agent_audio_latency_seconds") != expected_p90:
        fail("audit p90 latency does not match warm result")
    if audit.get("minimum_latency_seconds") != (rounded(min(latencies)) if latencies else None):
        fail("audit minimum latency does not match warm result")
    if audit.get("maximum_latency_seconds") != (rounded(max(latencies)) if latencies else None):
        fail("audit maximum latency does not match warm result")
    if audit.get("recommendation") != expected_recommendation(audit):
        fail("audit recommendation does not match decision logic")
    if audit.get("latency_classification") not in {
        "live_latency_promising",
        "demo_latency_promising",
        "latency_not_ready",
        "benchmark_inconclusive",
    }:
        fail("unexpected latency classification")
    for key in (
        "live_wiring_allowed",
        "production_call_allowed",
        "real_customer_data_allowed",
        "runtime_behavior_changed",
        "response_text_changed",
        "final_elevenlabs_replacement_claimed",
    ):
        assert_false(audit, key)
        assert_false(feasibility, key)
        assert_false(review, key)
    for decision in (feasibility, review):
        if decision.get("phase") == "4J8":
            if not optimization_audit:
                fail("phase 4J8 decisions require optimization audit evidence")
            if decision.get("recommendation") != optimization_audit.get("recommendation"):
                fail("phase 4J8 decision recommendation must match optimization audit")
            if decision.get("latency_optimization_audit_id") != "ULTRAVOX-LATENCY-OPTIMIZATION-AUDIT-001":
                fail("phase 4J8 decision must point at optimization audit")
        elif decision.get("phase") == "4J7":
            if decision.get("recommendation") != audit.get("recommendation"):
                fail("refreshed decision recommendation must match warm audit")
            if decision.get("warm_session_latency_audit_id") != "ULTRAVOX-WARM-SESSION-LATENCY-AUDIT-001":
                fail("refreshed decision must point at warm latency audit")
        else:
            fail("refreshed decisions must record phase 4J7 or 4J8")
        if decision.get("no_final_elevenlabs_replacement_claim") is not True:
            fail("refreshed decision must keep no-final-ElevenLabs-replacement claim")
    for line in (
        "Warm p50 first-agent-audio latency seconds:",
        "Warm p90 first-agent-audio latency seconds:",
        "Latency classification:",
        "Decision recommendation:",
    ):
        if line not in audit_report:
            fail(f"warm audit report missing line: {line}")
    print("ULTRAVOX warm-session latency audit validation passed.")


if __name__ == "__main__":
    main()
