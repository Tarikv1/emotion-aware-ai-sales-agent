#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SETTINGS_RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-LATENCY-SETTINGS-OPTIONS-001" / "result.json"
BENCHMARK_RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-LATENCY-OPTIMIZATION-BENCHMARK-001" / "result.json"
AUDIT_RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-LATENCY-OPTIMIZATION-AUDIT-001" / "result.json"
AUDIT_REPORT_PATH = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-LATENCY-OPTIMIZATION-AUDIT-001" / "report.md"
FEASIBILITY_RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-HOSTED-FEASIBILITY-DECISION-001" / "result.json"
FEASIBILITY_REPORT_PATH = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-HOSTED-FEASIBILITY-DECISION-001" / "report.md"
REVIEW_RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-AUDIO-SANDBOX-REVIEW-DECISION-001" / "result.json"
REVIEW_REPORT_PATH = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-AUDIO-SANDBOX-REVIEW-DECISION-001" / "report.md"

BASELINE_P50 = 4.638
BASELINE_P90 = 5.148
BASELINE_LATENCIES = [4.001, 5.148, 4.638]
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


def median(values: list[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    midpoint = len(ordered) // 2
    if len(ordered) % 2:
        return rounded(ordered[midpoint])
    return rounded((ordered[midpoint - 1] + ordered[midpoint]) / 2.0)


def percentile_nearest(values: list[float], pct: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, math.ceil((pct / 100.0) * len(ordered)) - 1))
    return rounded(ordered[index])


def expected_category(audit: dict[str, Any]) -> str:
    if audit.get("tool_boundary_passed") is not True:
        return "latency_not_ready_stop_provider_testing"
    p50 = audit.get("optimized_warm_p50_first_agent_audio_latency_seconds")
    p90 = audit.get("optimized_warm_p90_first_agent_audio_latency_seconds")
    if isinstance(p50, (int, float)) and p50 <= 2.0:
        return "latency_ready_for_limited_synthetic_eval"
    if isinstance(p50, (int, float)) and p50 <= 3.0:
        return "latency_ready_for_limited_synthetic_eval"
    if (
        isinstance(p50, (int, float))
        and p50 <= 4.0
        and (p90 is None or (isinstance(p90, (int, float)) and p90 <= 5.0))
        and isinstance(audit.get("p50_improvement_seconds"), (int, float))
        and audit["p50_improvement_seconds"] > 0
    ):
        return "latency_borderline_but_promising"
    if isinstance(p50, (int, float)) and (p50 > 4.0 or (isinstance(p90, (int, float)) and p90 > 5.0)):
        return "latency_not_ready_stop_provider_testing"
    return "inconclusive"


def assert_false(payload: dict[str, Any], key: str) -> None:
    if payload.get(key) is not False:
        fail(f"{key} must be false")


def main() -> None:
    settings = load_json(SETTINGS_RESULT_PATH)
    benchmark = load_json(BENCHMARK_RESULT_PATH)
    audit = load_json(AUDIT_RESULT_PATH)
    feasibility = load_json(FEASIBILITY_RESULT_PATH)
    review = load_json(REVIEW_RESULT_PATH)
    audit_report = AUDIT_REPORT_PATH.read_text(encoding="utf-8") if AUDIT_REPORT_PATH.is_file() else ""
    feasibility_report = FEASIBILITY_REPORT_PATH.read_text(encoding="utf-8") if FEASIBILITY_REPORT_PATH.is_file() else ""
    review_report = REVIEW_REPORT_PATH.read_text(encoding="utf-8") if REVIEW_REPORT_PATH.is_file() else ""
    if not audit_report:
        fail(f"missing file: {rel(AUDIT_REPORT_PATH)}")
    if not feasibility_report:
        fail(f"missing file: {rel(FEASIBILITY_REPORT_PATH)}")
    if not review_report:
        fail(f"missing file: {rel(REVIEW_REPORT_PATH)}")
    assert_no_secret(
        "latency optimization audit and refreshed decisions",
        json.dumps(settings) + json.dumps(benchmark) + json.dumps(audit) + audit_report + json.dumps(feasibility) + feasibility_report + json.dumps(review) + review_report,
    )

    if audit.get("evaluation_id") != "ULTRAVOX-LATENCY-OPTIMIZATION-AUDIT-001":
        fail("unexpected latency optimization audit evaluation_id")
    if audit.get("phase") != "4J8":
        fail("latency optimization audit must record phase 4J8")
    if audit.get("baseline_warm_latencies_seconds") != BASELINE_LATENCIES:
        fail("baseline latencies changed")
    if audit.get("baseline_warm_p50_first_agent_audio_latency_seconds") != BASELINE_P50:
        fail("baseline p50 changed")
    if audit.get("baseline_warm_p90_first_agent_audio_latency_seconds") != BASELINE_P90:
        fail("baseline p90 changed")

    latencies = [
        float(turn["user_turn_end_to_first_agent_audio_seconds"])
        for turn in benchmark.get("turns", [])
        if isinstance(turn, dict)
        and turn.get("measured_turn") is True
        and isinstance(turn.get("user_turn_end_to_first_agent_audio_seconds"), (int, float))
    ]
    p50 = median(latencies)
    p90 = percentile_nearest(latencies, 90.0) if len(latencies) >= 2 else None
    if audit.get("optimized_warm_measured_turn_count") != len(latencies):
        fail("audit measured turn count must match benchmark")
    if audit.get("optimized_warm_p50_first_agent_audio_latency_seconds") != p50:
        fail("audit p50 latency does not match benchmark")
    if audit.get("optimized_warm_p90_first_agent_audio_latency_seconds") != p90:
        fail("audit p90 latency does not match benchmark")
    if p50 is not None and audit.get("p50_improvement_seconds") != rounded(BASELINE_P50 - p50):
        fail("p50 improvement seconds does not match baseline comparison")
    if p90 is not None and audit.get("p90_improvement_seconds") != rounded(BASELINE_P90 - p90):
        fail("p90 improvement seconds does not match baseline comparison")
    if audit.get("decision_category") != expected_category(audit):
        fail("decision category does not match latency/tool-boundary logic")
    if settings.get("unsupported_parameters_sent_as_confirmed") is not False:
        fail("settings audit must not confirm unsupported sent parameters")
    if benchmark.get("unsupported_parameters_sent_as_confirmed") is not False:
        fail("benchmark must not send unsupported confirmed parameters")
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
        if decision.get("phase") != "4J8":
            fail("refreshed decisions must record phase 4J8")
        if decision.get("latency_optimization_audit_id") != "ULTRAVOX-LATENCY-OPTIMIZATION-AUDIT-001":
            fail("refreshed decision must point at optimization audit")
        if decision.get("decision_category") != audit.get("decision_category"):
            fail("refreshed decision category must match optimization audit")
        if decision.get("recommendation") != audit.get("recommendation"):
            fail("refreshed decision recommendation must match optimization audit")
        if decision.get("no_final_elevenlabs_replacement_claim") is not True:
            fail("refreshed decision must keep no-final-ElevenLabs-replacement claim")
    for line in (
        "Optimized warm p50 first-agent-audio latency seconds:",
        "Optimized warm p90 first-agent-audio latency seconds:",
        "P50 improvement seconds:",
        "Decision category:",
        "Decision recommendation:",
    ):
        if line not in audit_report:
            fail(f"optimization audit report missing line: {line}")
    print("ULTRAVOX latency optimization audit validation passed.")


if __name__ == "__main__":
    main()
