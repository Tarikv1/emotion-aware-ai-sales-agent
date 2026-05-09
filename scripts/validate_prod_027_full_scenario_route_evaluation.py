#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-027-full-scenario-route-evaluation"
SOURCE_CHECKPOINT_ID = "PROD-014-callcenteren-scenario-bank"
EXPECTED_NEXT = "PROD-028-full-scenario-demo-review"

MODULE = ROOT / "scripts" / "prod_027_full_scenario_route_evaluation.py"
RUNNER = ROOT / "scripts" / "run_prod_027_full_scenario_route_evaluation.py"
DOC_PATH = ROOT / "docs" / "product" / "PROD_027_FULL_SCENARIO_ROUTE_EVALUATION.md"
SOURCE_BANK = ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "scenario-bank.json"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"
SCENARIO_SET_PATH = OUT_DIR / "full_scenario_set.json"
TRACE_HTML_PATH = OUT_DIR / "full_scenario_route_trace.html"
COMMANDS = ROOT / "docs" / "product" / "COMMANDS.md"
CHECKPOINT_INDEX = ROOT / "docs" / "product" / "CHECKPOINT_INDEX.md"
ROADMAP = ROOT / "docs" / "thesis" / "ROADMAP.md"
METHODOLOGY_LOG = ROOT / "docs" / "thesis" / "METHODOLOGY_LOG.md"
DECISION_LOG = ROOT / "docs" / "thesis" / "DECISION_LOG.md"

REQUIRED_FILES = [
    MODULE,
    RUNNER,
    DOC_PATH,
    SOURCE_BANK,
    RESULT_PATH,
    REPORT_PATH,
    SCENARIO_SET_PATH,
    TRACE_HTML_PATH,
]

REQUIRED_LABELS = {
    "sale_eligible",
    "price_objection",
    "callback_request",
    "cancellation_boundary",
    "support_handoff",
    "trust_repair",
}

REQUIRED_BOUNDARY_FALSE_KEYS = [
    "provider_calls_made",
    "llm_used",
    "private_data_read",
    "dataset_download_performed",
    "raw_transcript_text_stored",
    "copied_transcript_text_used",
    "generated_from_single_source_transcript",
    "contains_transcript_derived_prompt_text",
    "commercial_runtime_prompt_text_from_transcripts_allowed",
    "customer_data_allowed",
    "payment_collection_enabled",
    "runtime_behavior_changed_by_this_checkpoint",
    "runtime_retrieval_default_enabled",
    "composer_hook_flag_default_enabled",
    "live_provider_default_enabled",
    "server_started",
]

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
    '"copied_transcript_text_used": true',
    '"generated_from_single_source_transcript": true',
    '"contains_transcript_derived_prompt_text": true',
]


def assert_condition(condition: bool, message: Any) -> None:
    if not condition:
        raise AssertionError(message)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False, timeout=240)


def validate_docs() -> None:
    commands = COMMANDS.read_text(encoding="utf-8")
    assert_condition("run_prod_027_full_scenario_route_evaluation.py" in commands, "PROD-027 runner missing from COMMANDS.md")
    assert_condition("validate_prod_027_full_scenario_route_evaluation.py" in commands, "PROD-027 validator missing from COMMANDS.md")
    assert_condition("PROD_027_FULL_SCENARIO_ROUTE_EVALUATION.md" in CHECKPOINT_INDEX.read_text(encoding="utf-8"), "PROD-027 missing from checkpoint index")
    assert_condition(CHECKPOINT_ID in ROADMAP.read_text(encoding="utf-8"), "PROD-027 missing from roadmap")
    assert_condition("PROD-027 full scenario route evaluation" in METHODOLOGY_LOG.read_text(encoding="utf-8"), "PROD-027 missing from methodology log")
    assert_condition("Keep PROD-027 as full-scenario route evaluation" in DECISION_LOG.read_text(encoding="utf-8"), "PROD-027 decision missing from decision log")

    for path in [DOC_PATH, REPORT_PATH, TRACE_HTML_PATH]:
        text = path.read_text(encoding="utf-8")
        lowered = text.lower()
        for marker in [
            "PROD-027",
            "PROD-014",
            "full scenario route evaluation",
            "strong evaluation set: `true`",
            "full scenarios: `20`",
            "turns per scenario: `6`",
            "exact customer turns visible: `true`",
            "exact agent answers visible: `true`",
            "route decision process visible: `true`",
            "local evaluation only: `true`",
            "provider calls made: `false`",
            "customer data allowed: `false`",
            "retrieval default enabled: `false`",
            "composer hook default enabled: `false`",
            EXPECTED_NEXT,
        ]:
            assert_condition(marker.lower() in lowered, f"{path.relative_to(ROOT)} missing marker: {marker}")
        for blocked in BLOCKED_TEXT:
            assert_condition(blocked.lower() not in lowered, f"{path.relative_to(ROOT)} contains blocked text: {blocked}")


def validate_payload(payload: dict[str, Any]) -> None:
    assert_condition(payload.get("checkpoint_id") == CHECKPOINT_ID, payload.get("checkpoint_id"))
    assert_condition(payload.get("source_checkpoint_id") == SOURCE_CHECKPOINT_ID, payload.get("source_checkpoint_id"))
    assert_condition(payload.get("source_scenario_bank_path") == str(SOURCE_BANK.relative_to(ROOT)).replace("\\", "/"), payload.get("source_scenario_bank_path"))

    boundaries = payload.get("boundaries", {})
    for key in REQUIRED_BOUNDARY_FALSE_KEYS:
        assert_condition(boundaries.get(key) is False, f"boundary {key} must be false")

    summary = payload.get("summary", {})
    assert_condition(summary.get("strong_evaluation_set") is True, summary)
    assert_condition(summary.get("scenario_count") == 20, summary)
    assert_condition(summary.get("turns_per_scenario") == 6, summary)
    assert_condition(summary.get("turn_count") == 120, summary)
    assert_condition(summary.get("exact_customer_turns_visible") is True, summary)
    assert_condition(summary.get("exact_agent_answers_visible") is True, summary)
    assert_condition(summary.get("route_decision_process_visible") is True, summary)
    assert_condition(summary.get("local_evaluation_only") is True, summary)
    assert_condition(summary.get("manual_review_required") is True, summary)
    assert_condition(summary.get("source_minimum_patterns_per_scenario") >= 3, summary)
    assert_condition(set(summary.get("covered_scenario_labels", [])) == REQUIRED_LABELS, summary)
    assert_condition(summary.get("leakage_finding_count") == 0, summary)
    assert_condition(summary.get("payment_collection_count") == 0, summary)
    assert_condition(summary.get("hard_failure_count") == 0, summary)
    assert_condition(summary.get("next_checkpoint_recommended") == EXPECTED_NEXT, summary)

    metrics = payload.get("metrics", {})
    for metric in [
        "route_correctness",
        "policy_action_correctness",
        "call_control_correctness",
        "non_sale_correctness",
        "safe_close_correctness",
        "discovery_before_close_rate",
        "emotion_handling_score",
        "leakage_failure_rate",
    ]:
        assert_condition(metric in metrics, f"missing metric {metric}")
        assert_condition(isinstance(metrics[metric].get("value"), (int, float)), metrics[metric])

    scenario_set = read_json(SCENARIO_SET_PATH)
    scenarios = scenario_set.get("scenarios", [])
    assert_condition(scenario_set.get("checkpoint_id") == CHECKPOINT_ID, scenario_set.get("checkpoint_id"))
    assert_condition(len(scenarios) == 20, "scenario set must contain 20 scenarios")
    assert_condition({scenario["scenario_label"] for scenario in scenarios} == REQUIRED_LABELS, "scenario set label coverage mismatch")
    for scenario in scenarios:
        assert_condition(len(scenario.get("turns", [])) == 6, scenario.get("scenario_id"))
        assert_condition(len(scenario.get("source_pattern_ids", [])) >= 3, scenario.get("scenario_id"))
        assert_condition(scenario.get("copied_transcript_text_used") is False, scenario.get("scenario_id"))
        assert_condition(scenario.get("generated_from_single_source_transcript") is False, scenario.get("scenario_id"))
        assert_condition(scenario.get("contains_transcript_derived_prompt_text") is False, scenario.get("scenario_id"))

    route_results = payload.get("route_results", [])
    assert_condition(len(route_results) == 20, "route result count mismatch")
    for scenario in route_results:
        assert_condition(len(scenario.get("turn_results", [])) == 6, scenario.get("scenario_id"))
        assert_condition(scenario.get("review_status") == "pending-manual-review", scenario.get("scenario_id"))
        for turn in scenario.get("turn_results", []):
            for key in [
                "customer_message",
                "agent_answer",
                "expected_policy_action",
                "observed_policy_action",
                "expected_call_control",
                "observed_call_control",
                "route_correct",
            ]:
                assert_condition(key in turn, f"missing {key}")
            assert_condition(turn.get("contains_payment_collection") is False, turn)
            assert_condition(turn.get("hard_failure") is False, turn)

    html = TRACE_HTML_PATH.read_text(encoding="utf-8")
    for scenario in route_results[:3]:
        assert_condition(scenario["scenario_id"] in html, f"HTML missing scenario {scenario['scenario_id']}")
        first_turn = scenario["turn_results"][0]
        assert_condition(first_turn["customer_message"] in html, f"HTML missing first customer turn for {scenario['scenario_id']}")
        assert_condition(first_turn["agent_answer"] in html, f"HTML missing first agent answer for {scenario['scenario_id']}")

    combined = (
        json.dumps(payload, ensure_ascii=False).lower()
        + "\n"
        + json.dumps(scenario_set, ensure_ascii=False).lower()
        + "\n"
        + REPORT_PATH.read_text(encoding="utf-8").lower()
        + "\n"
        + TRACE_HTML_PATH.read_text(encoding="utf-8").lower()
    )
    for blocked in BLOCKED_TEXT:
        assert_condition(blocked.lower() not in combined, blocked)


def main() -> None:
    missing = [path.relative_to(ROOT) for path in REQUIRED_FILES if not path.exists()]
    assert_condition(not missing, f"missing required PROD-027 files: {missing}")

    completed = run_command([sys.executable, str(RUNNER)])
    assert_condition(completed.returncode == 0, f"runner failed stdout={completed.stdout!r} stderr={completed.stderr!r}")

    validate_payload(read_json(RESULT_PATH))
    validate_docs()
    print("PROD-027 full scenario route evaluation validation passed.")


if __name__ == "__main__":
    main()
