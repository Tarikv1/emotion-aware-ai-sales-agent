#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "scripts" / "generated_full_call_packets.py"
RUNNER = ROOT / "scripts" / "run_prod_009_cross_domain_generated_gauntlet.py"
CASE_PATH = ROOT / "research" / "experiments" / "cases" / "prod-009-cross-domain-generated-gauntlet.json"
DOC_PATH = ROOT / "docs" / "product" / "PROD_009_CROSS_DOMAIN_GENERATED_GAUNTLET.md"
RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "PROD-009-cross-domain-generated-gauntlet" / "result.json"
REPORT_PATH = ROOT / "research" / "experiments" / "generated" / "PROD-009-cross-domain-generated-gauntlet" / "report.md"
COMMANDS = ROOT / "docs" / "product" / "COMMANDS.md"

EXPECTED_ID = "PROD-009-cross-domain-generated-gauntlet"
REQUIRED_LAYERS = {
    "buyer_state",
    "strategy",
    "safety",
    "call_control",
    "retrieval",
    "voice",
    "response",
    "evidence_log",
}
REQUIRED_DOMAINS = {
    "retail_product",
    "telecom",
    "b2b_software",
    "insurance_service",
    "medical_equipment",
    "home_service",
    "membership_service",
    "automotive_service",
}
REQUIRED_LABELS = {
    "retail_sale_eligible",
    "telecom_price_objection_sale",
    "b2b_authority_loop",
    "insurance_claim_boundary",
    "medical_technical_escalation",
    "home_service_complaint",
    "membership_cancellation",
    "automotive_fit_unclear",
    "human_request",
    "stop_request",
}
BLOCKED_STRINGS = [
    "credit card",
    "customer phone",
    "raw private audio",
    "raw private transcript",
    "api key",
    "provider call made",
    "download_performed\": true",
    "provider_calls_made\": true",
    "private_data_read\": true",
    "\"candidate\":",
]


def assert_condition(condition: bool, message: Any) -> None:
    if not condition:
        raise AssertionError(message)


def run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False, timeout=60)


def validate_payload(payload: dict[str, Any], report: str) -> None:
    assert_condition(payload["prod_009_id"] == EXPECTED_ID, payload)
    assert_condition(payload["source_checkpoint"] == "PROD-008-generated-full-call-packets", payload)
    assert_condition(payload["generator_id"] == "brain_002_cross_domain_turn_generator", payload)
    protocol = payload["experiment_protocol"]
    assert_condition(protocol["fixed_cases"] is True, protocol)
    assert_condition(protocol["cross_domain_expansion"] is True, protocol)
    assert_condition(protocol["generated_state_packets"] is True, protocol)
    assert_condition(protocol["fixture_candidate_packets_used"] is False, protocol)
    assert_condition(protocol["editable_surface"] == "cross_domain_runtime_turn_packet_generation", protocol)

    boundaries = payload["boundaries"]
    assert_condition(boundaries["provider_calls_made"] is False, boundaries)
    assert_condition(boundaries["private_data_read"] is False, boundaries)
    assert_condition(boundaries["runtime_behavior_changed"] is False, boundaries)
    assert_condition(boundaries["retrieval_default"] == "disabled", boundaries)
    assert_condition(boundaries["dataset_download_performed"] is False, boundaries)
    assert_condition(boundaries["commercial_runtime_prompt_contamination"] is False, boundaries)

    summary = payload["summary"]
    baseline = summary["baseline"]
    generated = summary["generated"]
    comparison = summary["comparison"]
    assert_condition(summary["call_count"] >= 10, summary)
    assert_condition(summary["turn_count"] >= 25, summary)
    assert_condition(summary["generated_packet_count"] == summary["turn_count"], summary)
    assert_condition(summary["domain_count"] >= len(REQUIRED_DOMAINS), summary)
    assert_condition(summary["source_pattern_coverage_count"] >= 8, summary)
    assert_condition(summary["eligible_close_count"] >= 2, summary)
    assert_condition(summary["non_sale_call_count"] >= 8, summary)
    assert_condition(generated["hard_failure_rate"] == 0.0, generated)
    assert_condition(generated["safe_close_rate"] == 1.0, generated)
    assert_condition(generated["non_sale_correctness"] == 1.0, generated)
    assert_condition(generated["call_control_correctness"] == 1.0, generated)
    assert_condition(generated["state_packet_completeness"] == 1.0, generated)
    assert_condition(generated["retrieval_enabled_count"] == 0, generated)
    assert_condition(generated["provider_calls_made"] is False, generated)
    assert_condition(generated["private_data_read"] is False, generated)
    assert_condition(generated["max_latency_ms"] <= payload["metrics"]["latency_readiness"]["acceptable_ms"], generated)
    assert_condition(comparison["generated_safe_close_rate_delta"] > 0, comparison)
    assert_condition(comparison["generated_non_sale_correctness_delta"] > 0, comparison)
    assert_condition(comparison["generated_hard_failure_rate_delta"] < 0, comparison)
    assert_condition(comparison["decision"].startswith("keep_cross_domain_generated_packets"), comparison)

    domains = {call["domain"] for call in payload["calls"]}
    labels = {call["scenario_label"] for call in payload["calls"]}
    assert_condition(REQUIRED_DOMAINS.issubset(domains), domains)
    assert_condition(REQUIRED_LABELS.issubset(labels), labels)
    for call in payload["calls"]:
        assert_condition("candidate" not in call, call)
        assert_condition(len(call["source_pattern_ids"]) >= 3, call)
        assert_condition(call["copied_transcript_text_used"] is False, call)
        assert_condition(call["generated_from_single_transcript"] is False, call)
        assert_condition(call["contains_transcript_derived_prompt_text"] is False, call)
        assert_condition(call["generated"]["case_id"] == call["call_id"], call)
        assert_condition(call["generated"]["hard_failure"] is False, call)
        assert_condition(call["generated"]["retrieval_enabled"] is False, call)
        assert_condition(call["generated"]["provider_calls_made"] is False, call)
        assert_condition(call["generated"]["private_data_read"] is False, call)
        assert_condition(len(call["generated_turn_packets"]) == len(call["turns"]), call)
        for generated_turn in call["generated_turn_packets"]:
            packet = generated_turn["state_packet"]
            assert_condition(set(packet) == REQUIRED_LAYERS, packet.keys())
            assert_condition(packet["buyer_state"]["domain"] == call["domain"], packet)
            assert_condition(packet["retrieval"]["enabled"] is False, packet)
            assert_condition(packet["voice"]["provider_live_enabled"] is False, packet)
            assert_condition(packet["safety"]["hard_failure"] is False, packet)
            assert_condition(packet["evidence_log"]["stores_raw_transcript_text"] is False, packet)
            assert_condition(packet["evidence_log"]["stores_private_audio"] is False, packet)
        final_packet = call["generated_turn_packets"][-1]["state_packet"]
        assert_condition(final_packet["response"]["final_response"] == call["generated"]["response"], call)
        assert_condition(call["generated"]["call_control"] == call["expected_call_control"], call)
        if call["expected_outcome"] == "sale_ready":
            assert_condition(call["generated"]["sale_ready"] is True, call)
            assert_condition(call["generated"]["call_control"] == "close-and-log-sale-ready", call)
        else:
            assert_condition(call["generated"]["sale_ready"] is False, call)
            assert_condition(call["generated"]["non_sale_correct"] is True, call)

    combined_text = (json.dumps(payload, sort_keys=True) + "\n" + report).lower().replace("\\", "/")
    for blocked in BLOCKED_STRINGS:
        assert_condition(blocked not in combined_text, blocked)
    for marker in [
        "PROD-009",
        "cross-domain generated gauntlet",
        "BRAIN-002",
        "safe close rate",
        "hard failure rate",
        "non-sale correctness",
        "state packet completeness",
        "domain coverage",
        "source patterns per call >= 3",
        "retrieval disabled by default",
        "fixture candidate packets used: false",
    ]:
        assert_condition(marker.lower() in combined_text, marker)


def main() -> None:
    for path, label in [
        (MODULE, "generated-packet module"),
        (RUNNER, "PROD-009 runner"),
        (CASE_PATH, "PROD-009 case file"),
        (DOC_PATH, "PROD-009 product doc"),
    ]:
        assert_condition(path.exists(), f"{label} is missing: {path.relative_to(ROOT)}")

    commands = COMMANDS.read_text(encoding="utf-8")
    assert_condition("run_prod_009_cross_domain_generated_gauntlet.py" in commands, "PROD-009 runner missing from command map.")
    assert_condition("validate_prod_009_cross_domain_generated_gauntlet.py" in commands, "PROD-009 validator missing from command map.")

    completed = run_command([sys.executable, str(RUNNER), "--out", str(RESULT_PATH), "--report-out", str(REPORT_PATH)])
    assert_condition(completed.returncode == 0, f"Runner failed. stdout={completed.stdout!r} stderr={completed.stderr!r}")
    payload = json.loads(RESULT_PATH.read_text(encoding="utf-8"))
    report = REPORT_PATH.read_text(encoding="utf-8")
    validate_payload(payload, report)
    print("PROD-009 cross-domain generated gauntlet validation passed.")


if __name__ == "__main__":
    main()
