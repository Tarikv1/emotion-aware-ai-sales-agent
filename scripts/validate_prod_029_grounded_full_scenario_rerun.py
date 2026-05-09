#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-029-grounded-full-scenario-rerun"
SOURCE_CHECKPOINT_ID = "PROD-027-full-scenario-route-evaluation"
GROUNDING_CHECKPOINT_ID = "PROD-028-synthetic-campaign-knowledge-grounding"
EXPECTED_NEXT = "PROD-030-grounded-demo-review"

MODULE = ROOT / "scripts" / "prod_029_grounded_full_scenario_rerun.py"
RUNNER = ROOT / "scripts" / "run_prod_029_grounded_full_scenario_rerun.py"
DOC_PATH = ROOT / "docs" / "product" / "PROD_029_GROUNDED_FULL_SCENARIO_RERUN.md"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"
SCENARIO_SET_PATH = OUT_DIR / "grounded_full_scenario_set.json"
TRACE_HTML_PATH = OUT_DIR / "grounded_full_scenario_trace.html"
SOURCE_RESULT_PATH = ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "result.json"
SOURCE_SCENARIO_SET_PATH = ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "full_scenario_set.json"
GROUNDING_CAMPAIGN_PATH = ROOT / "research" / "experiments" / "generated" / GROUNDING_CHECKPOINT_ID / "synthetic_campaign.json"
COMMANDS = ROOT / "docs" / "product" / "COMMANDS.md"
CHECKPOINT_INDEX = ROOT / "docs" / "product" / "CHECKPOINT_INDEX.md"
ROADMAP = ROOT / "docs" / "thesis" / "ROADMAP.md"
METHODOLOGY_LOG = ROOT / "docs" / "thesis" / "METHODOLOGY_LOG.md"
DECISION_LOG = ROOT / "docs" / "thesis" / "DECISION_LOG.md"

REQUIRED_FILES = [
    MODULE,
    RUNNER,
    DOC_PATH,
    RESULT_PATH,
    REPORT_PATH,
    SCENARIO_SET_PATH,
    TRACE_HTML_PATH,
    SOURCE_RESULT_PATH,
    SOURCE_SCENARIO_SET_PATH,
    GROUNDING_CAMPAIGN_PATH,
]

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
    "source_prod_027_overwritten",
]

BLOCKED_OUTPUT_TEXT = [
    "data/private",
    "data/private-restricted",
    "raw private audio",
    "raw private transcript",
    "api key",
    "take your payment",
    "card number",
    "credit card number",
    '"provider_calls_made": true',
    '"private_data_read": true',
    '"runtime_retrieval_default_enabled": true',
    '"composer_hook_flag_default_enabled": true',
    '"payment_collection_enabled": true',
    '"source_prod_027_overwritten": true',
]


def assert_condition(condition: bool, message: Any) -> None:
    if not condition:
        raise AssertionError(message)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False, timeout=240)


def normalized(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def validate_payload(payload: dict[str, Any]) -> None:
    assert_condition(payload.get("checkpoint_id") == CHECKPOINT_ID, payload.get("checkpoint_id"))
    assert_condition(payload.get("source_checkpoint_id") == SOURCE_CHECKPOINT_ID, payload.get("source_checkpoint_id"))
    assert_condition(payload.get("grounding_checkpoint_id") == GROUNDING_CHECKPOINT_ID, payload.get("grounding_checkpoint_id"))
    assert_condition(payload.get("next_checkpoint_recommended") == EXPECTED_NEXT, payload.get("next_checkpoint_recommended"))

    outputs = payload.get("outputs", {})
    assert_condition(outputs.get("result_path") == normalized(RESULT_PATH), outputs)
    assert_condition(outputs.get("report_path") == normalized(REPORT_PATH), outputs)
    assert_condition(outputs.get("scenario_set_path") == normalized(SCENARIO_SET_PATH), outputs)
    assert_condition(outputs.get("trace_html_path") == normalized(TRACE_HTML_PATH), outputs)

    boundaries = payload.get("boundaries", {})
    for key in REQUIRED_BOUNDARY_FALSE_KEYS:
        assert_condition(boundaries.get(key) is False, f"boundary {key} must be false")

    summary = payload.get("summary", {})
    assert_condition(summary.get("same_prod_027_scenario_set") is True, summary)
    assert_condition(summary.get("prod_027_baseline_answers_compared") is True, summary)
    assert_condition(summary.get("synthetic_campaign_facts_used") is True, summary)
    assert_condition(summary.get("scenario_count") == 20, summary)
    assert_condition(summary.get("turn_count") == 120, summary)
    assert_condition(summary.get("exact_customer_turns_visible") is True, summary)
    assert_condition(summary.get("exact_prod_027_answers_visible") is True, summary)
    assert_condition(summary.get("exact_grounded_answers_visible") is True, summary)
    assert_condition(summary.get("route_decision_process_visible") is True, summary)
    assert_condition(summary.get("hard_failure_count") == 0, summary)
    assert_condition(summary.get("payment_collection_count") == 0, summary)
    assert_condition(summary.get("unsupported_claim_count") == 0, summary)
    assert_condition(summary.get("leakage_finding_count") == 0, summary)
    assert_condition(summary.get("direct_answer_rate") >= 0.9, summary)
    assert_condition(summary.get("grounded_question_overuse_rate") <= 0.05, summary)
    assert_condition(summary.get("prod_027_question_overuse_rate") >= 0.5, summary)
    assert_condition(summary.get("knowledge_applicable_fact_rate") >= 0.9, summary)
    assert_condition(summary.get("grounded_better_than_prod_027") is True, summary)
    assert_condition(summary.get("route_correct_turn_count") == 110, summary)
    assert_condition(summary.get("policy_action_correct_count") == 110, summary)
    assert_condition(summary.get("call_control_correct_count") == 117, summary)
    assert_condition(summary.get("scenario_route_pass_count") == 13, summary)

    metrics = payload.get("metrics", {})
    for metric in [
        "route_correctness",
        "policy_action_correctness",
        "call_control_correctness",
        "scenario_route_pass_rate",
        "direct_answer_rate",
        "knowledge_applicable_fact_rate",
        "grounded_question_overuse_rate",
        "prod_027_question_overuse_rate",
        "grounded_answer_win_rate",
        "unsupported_claim_rate",
        "leakage_failure_rate",
    ]:
        assert_condition(metric in metrics, f"missing metric {metric}")
        assert_condition(isinstance(metrics[metric].get("value"), (int, float)), metrics[metric])

    source_scenario_set = read_json(SOURCE_SCENARIO_SET_PATH)
    scenario_set = read_json(SCENARIO_SET_PATH)
    assert_condition(scenario_set.get("checkpoint_id") == CHECKPOINT_ID, scenario_set.get("checkpoint_id"))
    assert_condition(scenario_set.get("source_checkpoint_id") == SOURCE_CHECKPOINT_ID, scenario_set.get("source_checkpoint_id"))
    assert_condition(len(scenario_set.get("scenarios", [])) == len(source_scenario_set.get("scenarios", [])) == 20, "scenario count mismatch")
    for source_scenario, grounded_scenario in zip(source_scenario_set["scenarios"], scenario_set["scenarios"]):
        assert_condition(grounded_scenario["source_scenario_id"] == source_scenario["scenario_id"], grounded_scenario)
        assert_condition(len(grounded_scenario.get("turns", [])) == len(source_scenario.get("turns", [])) == 6, grounded_scenario)
        for source_turn, grounded_turn in zip(source_scenario["turns"], grounded_scenario["turns"]):
            assert_condition(grounded_turn["source_turn_id"] == source_turn["turn_id"], grounded_turn)
            assert_condition(grounded_turn["customer_message"] == source_turn["customer_message"], grounded_turn)
            assert_condition(grounded_turn["expected_policy_action"] == source_turn["expected_policy_action"], grounded_turn)
            assert_condition(grounded_turn["expected_call_control"] == source_turn["expected_call_control"], grounded_turn)

    route_results = payload.get("route_results", [])
    assert_condition(len(route_results) == 20, "route result count mismatch")
    turn_results = [turn for scenario in route_results for turn in scenario.get("turn_results", [])]
    assert_condition(len(turn_results) == 120, "turn result count mismatch")
    for turn in turn_results:
        for key in [
            "customer_message",
            "prod_027_agent_answer",
            "grounded_agent_answer",
            "expected_policy_action",
            "observed_policy_action",
            "expected_call_control",
            "observed_call_control",
            "route_correct",
            "grounded_direct_answer",
            "grounded_question_overuse",
            "answer_quality_delta",
        ]:
            assert_condition(key in turn, f"missing {key}")
        assert_condition(turn["contains_payment_collection"] is False, turn)
        assert_condition(turn["unsupported_claim"] is False, turn)
        assert_condition(turn["hard_failure"] is False, turn)
        assert_condition(len(str(turn["grounded_agent_answer"]).split()) <= 70, turn["grounded_agent_answer"])

    html = TRACE_HTML_PATH.read_text(encoding="utf-8")
    for marker in [
        "PROD-029 Grounded Full Scenario Rerun",
        "same 20 scenarios / 120 turns",
        "old PROD-027 answers vs grounded campaign answers",
    ]:
        assert_condition(marker in html, marker)

    combined = (
        json.dumps(payload, ensure_ascii=False).lower()
        + "\n"
        + REPORT_PATH.read_text(encoding="utf-8").lower()
        + "\n"
        + TRACE_HTML_PATH.read_text(encoding="utf-8").lower()
    )
    for blocked in BLOCKED_OUTPUT_TEXT:
        assert_condition(blocked.lower() not in combined, blocked)


def validate_docs() -> None:
    commands = COMMANDS.read_text(encoding="utf-8")
    assert_condition("run_prod_029_grounded_full_scenario_rerun.py" in commands, "PROD-029 runner missing from COMMANDS.md")
    assert_condition("validate_prod_029_grounded_full_scenario_rerun.py" in commands, "PROD-029 validator missing from COMMANDS.md")
    assert_condition("PROD_029_GROUNDED_FULL_SCENARIO_RERUN.md" in CHECKPOINT_INDEX.read_text(encoding="utf-8"), "PROD-029 missing from checkpoint index")
    assert_condition(CHECKPOINT_ID in ROADMAP.read_text(encoding="utf-8"), "PROD-029 missing from roadmap")
    assert_condition("PROD-029 grounded full-scenario rerun" in METHODOLOGY_LOG.read_text(encoding="utf-8"), "PROD-029 missing from methodology log")
    assert_condition("Keep PROD-029 as a grounded rerun of PROD-027" in DECISION_LOG.read_text(encoding="utf-8"), "PROD-029 decision missing from decision log")

    for path in [DOC_PATH, REPORT_PATH, TRACE_HTML_PATH]:
        text = path.read_text(encoding="utf-8")
        lowered = text.lower()
        for marker in [
            "PROD-029",
            "grounded full scenario rerun",
            "same 20 scenarios / 120 turns",
            "old PROD-027 answers vs grounded campaign answers",
            "same prod-027 scenario set: `true`",
            "synthetic campaign facts used: `true`",
            "exact prod-027 answers visible: `true`",
            "exact grounded answers visible: `true`",
            "provider calls made: `false`",
            "runtime behavior changed: `false`",
            EXPECTED_NEXT,
        ]:
            assert_condition(marker.lower() in lowered, f"{path.relative_to(ROOT)} missing marker: {marker}")
        for blocked in BLOCKED_OUTPUT_TEXT:
            assert_condition(blocked.lower() not in lowered, f"{path.relative_to(ROOT)} contains blocked text: {blocked}")


def main() -> None:
    missing = [path.relative_to(ROOT) for path in REQUIRED_FILES if not path.exists()]
    assert_condition(not missing, f"missing required PROD-029 files: {missing}")

    completed = run_command([sys.executable, str(RUNNER)])
    assert_condition(completed.returncode == 0, f"runner failed stdout={completed.stdout!r} stderr={completed.stderr!r}")

    validate_payload(read_json(RESULT_PATH))
    validate_docs()
    print("PROD-029 grounded full-scenario rerun validation passed.")


if __name__ == "__main__":
    main()
