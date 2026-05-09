#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "scripts" / "prod_025_bounded_demo_readiness_packet.py"
RUNNER = ROOT / "scripts" / "run_prod_025_bounded_demo_readiness_packet.py"
DOC_PATH = ROOT / "docs" / "product" / "PROD_025_BOUNDED_DEMO_READINESS_PACKET.md"
SOURCE_PROD_024_RESULT = ROOT / "research" / "experiments" / "generated" / "PROD-024-live-shaped-post-fix-rerun" / "result.json"
RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "PROD-025-bounded-demo-readiness-packet" / "result.json"
REPORT_PATH = ROOT / "research" / "experiments" / "generated" / "PROD-025-bounded-demo-readiness-packet" / "report.md"
COMMANDS = ROOT / "docs" / "product" / "COMMANDS.md"
CHECKPOINT_INDEX = ROOT / "docs" / "product" / "CHECKPOINT_INDEX.md"
ROADMAP = ROOT / "docs" / "thesis" / "ROADMAP.md"
METHODOLOGY_LOG = ROOT / "docs" / "thesis" / "METHODOLOGY_LOG.md"
DECISION_LOG = ROOT / "docs" / "thesis" / "DECISION_LOG.md"

CHECKPOINT_ID = "PROD-025-bounded-demo-readiness-packet"
SOURCE_CHECKPOINT_ID = "PROD-024-live-shaped-post-fix-rerun"
EXPECTED_NEXT = "PROD-026-local-demo-trace-harness"

REQUIRED_FILES = [
    MODULE,
    RUNNER,
    DOC_PATH,
    SOURCE_PROD_024_RESULT,
    RESULT_PATH,
    REPORT_PATH,
]

REQUIRED_ALLOWED_MODES = {
    "local-trace-replay",
    "offline-scripted-call-simulation",
    "human-review-packet",
}

REQUIRED_BLOCKED_CLAIMS = {
    "production-ready autonomous calling",
    "customer-facing live runtime",
    "retrieval default enabled",
    "composer hooks default enabled",
    "payment collection or checkout",
}

REQUIRED_REVIEW_GATES = {
    "product-demo-scope-review",
    "privacy-boundary-review",
    "provider-run-boundary-review",
    "manual-trace-review",
    "human-approval-before-live",
}

REQUIRED_TRACE_FIELDS = {
    "scenario_label",
    "customer_question",
    "agent_answer",
    "policy_action",
    "call_control",
    "safety_flags",
    "source_checkpoint",
}

BLOCKED_TEXT = [
    "data/private",
    "data/private-restricted",
    "raw private audio",
    "raw private transcript",
    "api key",
    "credit card",
    "card number",
    "take your payment",
    '"provider_calls_made": true',
    '"private_data_read": true',
    '"runtime_retrieval_default_enabled": true',
    '"composer_hook_flag_default_enabled": true',
    '"customer_data_allowed": true',
    '"payment_collection_enabled": true',
]


def assert_condition(condition: bool, message: Any) -> None:
    if not condition:
        raise AssertionError(message)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False, timeout=180)


def validate_docs() -> None:
    commands = COMMANDS.read_text(encoding="utf-8")
    assert_condition("run_prod_025_bounded_demo_readiness_packet.py" in commands, "PROD-025 runner missing from COMMANDS.md")
    assert_condition("validate_prod_025_bounded_demo_readiness_packet.py" in commands, "PROD-025 validator missing from COMMANDS.md")
    assert_condition("PROD_025_BOUNDED_DEMO_READINESS_PACKET.md" in CHECKPOINT_INDEX.read_text(encoding="utf-8"), "PROD-025 missing from checkpoint index")
    assert_condition("PROD-025-bounded-demo-readiness-packet" in ROADMAP.read_text(encoding="utf-8"), "PROD-025 missing from roadmap")
    assert_condition("PROD-025 bounded demo readiness packet" in METHODOLOGY_LOG.read_text(encoding="utf-8"), "PROD-025 missing from methodology log")
    assert_condition("Keep PROD-025 as bounded demo readiness packet" in DECISION_LOG.read_text(encoding="utf-8"), "PROD-025 decision missing from decision log")

    for path in [DOC_PATH, REPORT_PATH]:
        text = path.read_text(encoding="utf-8")
        lowered = text.lower()
        for marker in [
            "PROD-025",
            "PROD-024",
            "bounded demo readiness",
            "demo readiness gate passed: `true`",
            "production runtime promotion allowed: `false`",
            "live provider demo allowed: `false`",
            "customer data allowed: `false`",
            "retrieval default enabled: `false`",
            "composer hook default enabled: `false`",
            "manual review required: `true`",
            EXPECTED_NEXT,
        ]:
            assert_condition(marker.lower() in lowered, f"{path.relative_to(ROOT)} missing marker: {marker}")
        for blocked in BLOCKED_TEXT:
            assert_condition(blocked.lower() not in lowered, f"{path.relative_to(ROOT)} contains blocked text: {blocked}")


def validate_payload(payload: dict[str, Any], source_prod_024: dict[str, Any]) -> None:
    assert_condition(payload.get("checkpoint_id") == CHECKPOINT_ID, payload.get("checkpoint_id"))
    assert_condition(payload.get("source_checkpoint_id") == SOURCE_CHECKPOINT_ID, payload.get("source_checkpoint_id"))
    assert_condition(payload.get("source_prod_024_result_path") == str(SOURCE_PROD_024_RESULT.relative_to(ROOT)).replace("\\", "/"), payload.get("source_prod_024_result_path"))
    assert_condition(source_prod_024.get("summary", {}).get("post_fix_gate_passed") is True, "source PROD-024 must pass post-fix gate")

    boundaries = payload.get("boundaries", {})
    for key in [
        "provider_calls_made",
        "llm_used",
        "private_data_read",
        "dataset_download_performed",
        "runtime_behavior_changed_by_this_checkpoint",
        "runtime_retrieval_default_enabled",
        "composer_hook_flag_default_enabled",
        "live_provider_default_enabled",
        "customer_data_allowed",
        "payment_collection_enabled",
        "customer_facing_claim_allowed",
    ]:
        assert_condition(boundaries.get(key) is False, f"boundary {key} must be false")

    readiness = payload.get("readiness_summary", {})
    assert_condition(readiness.get("source_call_count") == 7, readiness)
    assert_condition(readiness.get("source_turn_count") == 19, readiness)
    assert_condition(readiness.get("policy_action_correctness") == 1.0, readiness)
    assert_condition(readiness.get("call_control_correctness") == 1.0, readiness)
    assert_condition(readiness.get("demo_readiness_gate_passed") is True, readiness)
    assert_condition(readiness.get("bounded_demo_ready") is True, readiness)
    assert_condition(readiness.get("local_dry_run_only") is True, readiness)
    assert_condition(readiness.get("manual_review_required") is True, readiness)
    assert_condition(readiness.get("production_runtime_promotion_allowed") is False, readiness)
    assert_condition(readiness.get("live_provider_demo_allowed") is False, readiness)
    assert_condition(readiness.get("next_checkpoint_recommended") == EXPECTED_NEXT, readiness)

    allowed_modes = {item.get("mode_id") for item in payload.get("allowed_demo_modes", [])}
    assert_condition(REQUIRED_ALLOWED_MODES <= allowed_modes, allowed_modes)
    for mode in payload.get("allowed_demo_modes", []):
        assert_condition(mode.get("default_provider_calls") is False, mode)
        assert_condition(mode.get("customer_data_allowed") is False, mode)

    blocked_claims = set(payload.get("blocked_claims", []))
    assert_condition(REQUIRED_BLOCKED_CLAIMS <= blocked_claims, blocked_claims)

    review_gates = {item.get("gate_id") for item in payload.get("required_review_gates", [])}
    assert_condition(REQUIRED_REVIEW_GATES <= review_gates, review_gates)

    trace_contract = payload.get("demo_trace_contract", {})
    assert_condition(trace_contract.get("exact_question_and_answer_visible") is True, trace_contract)
    assert_condition(trace_contract.get("show_decision_process") is True, trace_contract)
    assert_condition(trace_contract.get("raw_private_data_allowed") is False, trace_contract)
    assert_condition(REQUIRED_TRACE_FIELDS <= set(trace_contract.get("required_fields", [])), trace_contract)

    trace_cards = payload.get("demo_trace_cards", [])
    assert_condition(len(trace_cards) >= 3, "expected at least three trace cards")
    required_trace_scenarios = {"software_multi_objection_sale", "software_procurement_authority_delay", "trust_price_callback"}
    assert_condition(required_trace_scenarios <= {card.get("scenario_label") for card in trace_cards}, trace_cards)
    for card in trace_cards:
        for key in ["turn_id", "scenario_label", "customer_question", "agent_answer", "policy_action", "call_control"]:
            assert_condition(card.get(key) not in (None, ""), f"trace card missing {key}")

    assert_condition(payload.get("decision") == "bounded_demo_ready_local_trace_only", payload.get("decision"))

    combined = json.dumps(payload, ensure_ascii=False).lower() + "\n" + REPORT_PATH.read_text(encoding="utf-8").lower()
    for blocked in BLOCKED_TEXT:
        assert_condition(blocked.lower() not in combined, blocked)


def main() -> None:
    missing = [path.relative_to(ROOT) for path in REQUIRED_FILES if not path.exists()]
    assert_condition(not missing, f"missing required PROD-025 files: {missing}")

    completed = run_command([sys.executable, str(RUNNER)])
    assert_condition(completed.returncode == 0, f"runner failed stdout={completed.stdout!r} stderr={completed.stderr!r}")

    payload = read_json(RESULT_PATH)
    source_prod_024 = read_json(SOURCE_PROD_024_RESULT)
    validate_payload(payload, source_prod_024)
    validate_docs()
    print("PROD-025 bounded demo readiness packet validation passed.")


if __name__ == "__main__":
    main()
