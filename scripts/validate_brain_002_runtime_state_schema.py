#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "scripts" / "brain_runtime_state_schema.py"
RUNNER = ROOT / "scripts" / "run_brain_002_runtime_state_schema.py"
CASE_PATH = ROOT / "research" / "experiments" / "cases" / "brain-002-runtime-state-schema.json"
DOC_PATH = ROOT / "docs" / "brain" / "BRAIN_002_RUNTIME_STATE_SCHEMA.md"
RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "BRAIN-002-runtime-state-schema" / "result.json"
REPORT_PATH = ROOT / "research" / "experiments" / "generated" / "BRAIN-002-runtime-state-schema" / "report.md"
COMMANDS = ROOT / "docs" / "product" / "COMMANDS.md"

EXPECTED_ID = "BRAIN-002-runtime-state-schema"
REQUIRED_LAYERS = [
    "buyer_state",
    "strategy",
    "safety",
    "call_control",
    "retrieval",
    "voice",
    "response",
    "evidence_log",
]
REQUIRED_CALL_CONTROLS = {
    "continue-call",
    "bridge-then-continue",
    "transfer-or-escalate",
    "end-call",
    "schedule-and-end",
    "close-and-log-sale-ready",
}
BLOCKED_STRINGS = [
    "credit card",
    "customer phone",
    "raw private audio",
    "raw private transcript",
    "api key",
    "provider call made",
]


def assert_condition(condition: bool, message: Any) -> None:
    if not condition:
        raise AssertionError(message)


def run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False, timeout=60)


def validate_payload(payload: dict[str, Any], report: str) -> None:
    assert_condition(payload["brain_002_id"] == EXPECTED_ID, payload)
    assert_condition(payload["schema_version"] == "brain-runtime-state-v1", payload)

    summary = payload["summary"]
    assert_condition(summary["provider_calls_made"] is False, summary)
    assert_condition(summary["private_data_read"] is False, summary)
    assert_condition(summary["runtime_behavior_changed"] is False, summary)
    assert_condition(summary["retrieval_default"] == "disabled", summary)
    assert_condition(summary["hard_failure_count"] == 0, summary)
    assert_condition(summary["turn_count"] >= 6, summary)
    assert_condition(summary["non_sale_correct_count"] >= 3, summary)
    assert_condition(summary["sale_ready_count"] >= 1, summary)

    state_schema = payload["state_schema"]
    for layer in REQUIRED_LAYERS:
        assert_condition(layer in state_schema, f"Missing schema layer: {layer}")
        assert_condition(state_schema[layer]["required_fields"], f"Schema layer {layer} has no required fields.")

    call_control_values = set(state_schema["call_control"]["allowed_values"])
    assert_condition(REQUIRED_CALL_CONTROLS.issubset(call_control_values), call_control_values)

    for turn in payload["example_turns"]:
        packet = turn["state_packet"]
        assert_condition(set(packet) == set(REQUIRED_LAYERS), packet.keys())
        assert_condition(packet["call_control"]["decision"] in REQUIRED_CALL_CONTROLS, packet)
        assert_condition(packet["retrieval"]["enabled"] is False, packet)
        assert_condition(packet["retrieval"]["status"] in {"disabled_by_default", "blocked_by_guardrail"}, packet)
        assert_condition(packet["voice"]["provider_live_enabled"] is False, packet)
        assert_condition(packet["response"]["final_response"] == turn["response_preview"], turn)
        assert_condition(packet["response"]["sale_ready"] == (turn["expected_outcome"] == "sale_ready"), turn)
        if turn["expected_outcome"] != "sale_ready":
            assert_condition(packet["response"]["non_sale_correct"] is True, turn)
        assert_condition(packet["safety"]["hard_failure"] is False, turn)
        assert_condition(packet["evidence_log"]["stores_raw_transcript_text"] is False, turn)
        assert_condition(packet["evidence_log"]["stores_private_audio"] is False, turn)

    combined_text = (json.dumps(payload, sort_keys=True) + "\n" + report).lower()
    for blocked in BLOCKED_STRINGS:
        assert_condition(blocked not in combined_text, blocked)
    for marker in [
        "BRAIN-002",
        "runtime state schema",
        "retrieval disabled by default",
        "non-sale correctness",
        "close-and-log-sale-ready",
    ]:
        assert_condition(marker.lower() in combined_text, marker)


def main() -> None:
    for path, label in [
        (MODULE, "BRAIN-002 schema module"),
        (RUNNER, "BRAIN-002 runner"),
        (CASE_PATH, "BRAIN-002 case file"),
        (DOC_PATH, "BRAIN-002 product doc"),
    ]:
        assert_condition(path.exists(), f"{label} is missing: {path.relative_to(ROOT)}")

    commands = COMMANDS.read_text(encoding="utf-8")
    assert_condition("run_brain_002_runtime_state_schema.py" in commands, "BRAIN-002 runner missing from command map.")
    assert_condition("validate_brain_002_runtime_state_schema.py" in commands, "BRAIN-002 validator missing from command map.")

    completed = run_command([sys.executable, str(RUNNER), "--out", str(RESULT_PATH), "--report-out", str(REPORT_PATH)])
    assert_condition(completed.returncode == 0, f"Runner failed. stdout={completed.stdout!r} stderr={completed.stderr!r}")

    payload = json.loads(RESULT_PATH.read_text(encoding="utf-8"))
    report = REPORT_PATH.read_text(encoding="utf-8")
    validate_payload(payload, report)
    print("BRAIN-002 runtime state schema validation passed.")


if __name__ == "__main__":
    main()
