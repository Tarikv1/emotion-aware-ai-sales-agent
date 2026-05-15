#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "scripts" / "callcenteren_scenario_evaluation.py"
RUNNER = ROOT / "scripts" / "run_prod_012_callcenteren_scenario_evaluation.py"
CASE_PATH = ROOT / "research" / "experiments" / "cases" / "prod-012-callcenteren-scenario-evaluation.json"
DOC_PATH = ROOT / "docs" / "product" / "PROD_012_CALLCENTEREN_SCENARIO_EVALUATION.md"
RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "PROD-012-callcenteren-scenario-evaluation" / "result.json"
REPORT_PATH = ROOT / "research" / "experiments" / "generated" / "PROD-012-callcenteren-scenario-evaluation" / "report.md"
REFERENCE_REGISTRY = ROOT / "docs" / "thesis" / "THESIS_REFERENCE_REGISTRY.md"
COMMANDS = ROOT / "docs" / "product" / "COMMANDS.md"

EXPECTED_ID = "PROD-012-callcenteren-scenario-evaluation"
EXPECTED_DATASET_URL = "https://huggingface.co/datasets/AIxBlock/92k-real-world-call-center-scripts-english"
EXPECTED_PAPER_URL = "https://arxiv.org/abs/2507.02958"
EXPECTED_LICENSE = "cc-by-nc-4.0"


def assert_condition(condition: bool, message: Any) -> None:
    if not condition:
        raise AssertionError(message)


def run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False, timeout=90)


def validate_payload(payload: dict[str, Any], report: str) -> None:
    source = payload["dataset_source"]
    summary = payload["summary"]
    metrics = payload["metrics"]
    leakage = payload["leakage_tests"]
    scenarios = payload["scenario_bank"]
    turns = payload["turns"]
    comparison = payload["comparison"]
    combined = (json.dumps(payload, ensure_ascii=False).lower() + "\n" + report.lower()).replace("\\", "/")

    assert_condition(payload["prod_012_id"] == EXPECTED_ID, payload)
    assert_condition(source["dataset_url"] == EXPECTED_DATASET_URL, source)
    assert_condition(source["paper_url"] == EXPECTED_PAPER_URL, source)
    assert_condition(source["license"] == EXPECTED_LICENSE, source)
    assert_condition(source["reuse_label"] == "pattern_grounding_only", source)
    assert_condition(source["commercial_runtime_use_allowed"] is False, source)
    assert_condition(source["commercial_model_training_allowed"] is False, source)

    assert_condition(summary["scenario_count"] >= 6, summary)
    assert_condition(summary["turn_count"] >= 10, summary)
    assert_condition(summary["source_pattern_count"] >= 8, summary)
    assert_condition(summary["download_performed"] is False, summary)
    assert_condition(summary["provider_calls_made"] is False, summary)
    assert_condition(summary["raw_transcript_text_stored"] is False, summary)
    assert_condition(summary["commercial_runtime_prompt_contamination"] is False, summary)
    assert_condition(summary["hard_failure_count"] == 0, summary)
    assert_condition(summary["non_sale_correct_count"] == summary["non_sale_expected_count"], summary)

    for key in [
        "hard_failure_rate",
        "non_sale_correctness",
        "leakage_failure_rate",
        "scenario_quality_score",
        "sales_emotional_handling_score",
        "retrieval_win_rate",
    ]:
        assert_condition(key in metrics, metrics)
        assert_condition("value" in metrics[key], metrics[key])

    assert_condition(metrics["hard_failure_rate"]["value"] == 0.0, metrics["hard_failure_rate"])
    assert_condition(metrics["non_sale_correctness"]["value"] == 1.0, metrics["non_sale_correctness"])
    assert_condition(metrics["leakage_failure_rate"]["value"] == 0.0, metrics["leakage_failure_rate"])
    assert_condition(metrics["scenario_quality_score"]["value"] >= 0.9, metrics["scenario_quality_score"])
    assert_condition(metrics["sales_emotional_handling_score"]["value"] > 0.0, metrics["sales_emotional_handling_score"])

    assert_condition(leakage["exact_transcript_sentence_check"]["status"] == "pass", leakage)
    assert_condition(leakage["high_similarity_paraphrase_check"]["status"] == "pass", leakage)
    assert_condition(leakage["single_source_scenario_check"]["status"] == "pass", leakage)
    assert_condition(leakage["commercial_runtime_prompt_check"]["status"] == "pass", leakage)
    assert_condition(leakage["minimum_source_patterns_per_scenario"] == 3, leakage)
    assert_condition(leakage["findings"] == [], leakage)

    labels = {scenario["scenario_label"] for scenario in scenarios}
    assert_condition({"sale_eligible", "non_sale_correct", "support_only", "trust_repair", "human_handoff"}.issubset(labels), labels)
    for scenario in scenarios:
        assert_condition(len(scenario["source_pattern_ids"]) >= 3, scenario)
        assert_condition(scenario["copied_transcript_text_used"] is False, scenario)
        assert_condition(scenario["generated_from_single_transcript"] is False, scenario)
        assert_condition(scenario["contains_transcript_derived_prompt_text"] is False, scenario)
        assert_condition(scenario["commercial_runtime_prompt_safe"] is True, scenario)

    assert_condition(turns, "PROD-012 payload must include turn-level rows.")
    for turn in turns:
        assert_condition("customer_utterance" in turn, turn)
        assert_condition("core_response" in turn and turn["core_response"], turn)
        assert_condition("retrieval_response" in turn and turn["retrieval_response"], turn)
        assert_condition("decision_trace" in turn, turn)
        trace = turn["decision_trace"]
        for section in ["policy_classification", "old_core_path", "retrieval_path", "safety_and_selection"]:
            assert_condition(section in trace, trace)
        assert_condition(trace["policy_classification"].get("sales_difficulty"), trace)
        assert_condition(trace["policy_classification"].get("next_action"), trace)
        assert_condition(trace["old_core_path"].get("local_composer_candidate"), trace)
        assert_condition(trace["retrieval_path"].get("local_composer_candidate"), trace)
        assert_condition("retrieval_used_in_runtime" in trace["retrieval_path"], trace)
        assert_condition("campaign_facts_override_rag" in trace["safety_and_selection"], trace)
        assert_condition(turn["turn_id"] in report, turn["turn_id"])
        assert_condition(turn["core_response"] in report, turn["turn_id"])
        assert_condition(turn["retrieval_response"] in report, turn["turn_id"])
        if turn["customer_utterance"]:
            assert_condition(turn["customer_utterance"] in report, turn["turn_id"])

    assert_condition(comparison["baseline_name"] == "old_core_retrieval_disabled", comparison)
    assert_condition(comparison["candidate_name"] == "rag_018_retrieval_enabled", comparison)
    assert_condition(comparison["retrieval_total_score"] > comparison["core_total_score"], comparison)
    assert_condition(comparison["retrieval_turn_wins"] >= 1, comparison)
    assert_condition(comparison["core_turn_wins"] == 0, comparison)
    assert_condition(comparison["protected_turns_preserved"] == comparison["protected_turn_count"], comparison)
    assert_condition(comparison["retrieval_over_acceptable_count"] == 0, comparison)
    assert_condition(payload["decision"] == "keep_retrieval_opt_in_for_callcenteren_grounded_scenarios", payload["decision"])

    forbidden = [
        '"source_excerpt_text":',
        '"raw_transcript_text":',
        "data/private",
        "data/private-restricted",
        "account number",
        "credit card",
        "customer phone",
        "you are anxious",
        "you are angry",
        "i can tell you feel",
        "guaranteed savings",
        "only today",
    ]
    for token in forbidden:
        assert_condition(token not in combined, token)

    for required in [
        "aixblock",
        "leakage tests",
        "hard failure rate",
        "non-sale correctness",
        "old core",
        "retrieval version",
        "do not make retrieval default",
        "exact questions and answers",
        "exact customer question/input",
        "exact old/core answer",
        "exact retrieval/rag answer",
        "decision process",
        "policy classified the turn",
        "retrieval path status",
        "retrieved advisory hints",
        "safety/selection kept campaign facts above rag",
    ]:
        assert_condition(required in report.lower(), required)


def main() -> None:
    for path, label in [
        (MODULE, "PROD-012 module"),
        (RUNNER, "PROD-012 runner"),
        (CASE_PATH, "PROD-012 case file"),
        (DOC_PATH, "PROD-012 product doc"),
    ]:
        assert_condition(path.exists(), f"{label} is missing: {path.relative_to(ROOT)}")

    registry = REFERENCE_REGISTRY.read_text(encoding="utf-8")
    assert_condition(EXPECTED_DATASET_URL in registry, "Dataset URL missing from thesis reference registry.")
    assert_condition(EXPECTED_PAPER_URL in registry, "Dataset paper URL missing from thesis reference registry.")
    assert_condition(EXPECTED_LICENSE in registry.lower(), "Dataset license missing from thesis reference registry.")

    commands = COMMANDS.read_text(encoding="utf-8")
    assert_condition("run_prod_012_callcenteren_scenario_evaluation.py" in commands, "PROD-012 runner missing from command map.")
    assert_condition("validate_prod_012_callcenteren_scenario_evaluation.py" in commands, "PROD-012 validator missing from command map.")

    completed = run_command(
        [
            sys.executable,
            str(RUNNER),
            "--cases",
            str(CASE_PATH),
            "--out",
            str(RESULT_PATH),
            "--report-out",
            str(REPORT_PATH),
        ]
    )
    assert_condition(completed.returncode == 0, f"Runner failed. stdout={completed.stdout!r} stderr={completed.stderr!r}")
    payload = json.loads(RESULT_PATH.read_text(encoding="utf-8"))
    report = REPORT_PATH.read_text(encoding="utf-8")
    validate_payload(payload, report)
    print("PROD-012 CallCenterEN scenario evaluation validation passed.")


if __name__ == "__main__":
    main()
