#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "scripts" / "full_sale_scenario_grounding.py"
RUNNER = ROOT / "scripts" / "run_prod_006_full_sale_scenario_grounding.py"
CASE_PATH = ROOT / "research" / "experiments" / "cases" / "prod-006-full-sale-scenario-grounding.json"
DOC_PATH = ROOT / "docs" / "product" / "FULL_SALE_MVP_STRATEGY.md"
RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "PROD-006-full-sale-scenario-grounding" / "result.json"
REPORT_PATH = ROOT / "research" / "experiments" / "generated" / "PROD-006-full-sale-scenario-grounding" / "report.md"
REFERENCE_REGISTRY = ROOT / "docs" / "thesis" / "THESIS_REFERENCE_REGISTRY.md"
COMMANDS = ROOT / "docs" / "product" / "COMMANDS.md"

EXPECTED_ID = "PROD-006-full-sale-scenario-grounding"
EXPECTED_DATASET_URL = "https://huggingface.co/datasets/AIxBlock/92k-real-world-call-center-scripts-english"
EXPECTED_PAPER_URL = "https://arxiv.org/abs/2507.02958"
EXPECTED_LICENSE = "cc-by-nc-4.0"


def assert_condition(condition: bool, message: Any) -> None:
    if not condition:
        raise AssertionError(message)


def run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False, timeout=60)


def validate_payload(payload: dict[str, Any], report: str) -> None:
    summary = payload["summary"]
    dataset = payload["dataset_source"]
    policy = payload["intake_policy"]
    metrics = payload["metrics"]
    leakage = payload["leakage_tests"]
    scenarios = payload["scenario_bank"]
    combined_text = json.dumps(payload, sort_keys=True).lower() + "\n" + report.lower()

    assert_condition(payload["prod_006_id"] == EXPECTED_ID, payload)
    assert_condition(dataset["dataset_url"] == EXPECTED_DATASET_URL, dataset)
    assert_condition(dataset["paper_url"] == EXPECTED_PAPER_URL, dataset)
    assert_condition(dataset["license"] == EXPECTED_LICENSE, dataset)
    assert_condition(dataset["reuse_label"] == "pattern_grounding_only", dataset)
    assert_condition(dataset["commercial_runtime_use_allowed"] is False, dataset)
    assert_condition(dataset["raw_audio_in_public_release"] is False, dataset)

    assert_condition(policy["download_performed"] is False, policy)
    assert_condition(policy["provider_calls_made"] is False, policy)
    assert_condition(policy["raw_transcript_text_stored"] is False, policy)
    assert_condition(policy["copied_transcript_text_allowed"] is False, policy)
    assert_condition(policy["commercial_runtime_prompt_contamination_allowed"] is False, policy)
    assert_condition(policy["raw_zip_storage"] == "ignored_local_only", policy)

    for key in [
        "safe_close_rate",
        "hard_failure_rate",
        "non_sale_correctness",
        "close_attempt_quality",
        "scenario_diversity",
        "latency_readiness",
    ]:
        assert_condition(key in metrics, metrics)
    assert_condition(metrics["hard_failure_rate"]["release_candidate_target"] == 0.0, metrics)
    assert_condition(metrics["non_sale_correctness"]["required_before_close_rate_optimization"] is True, metrics)

    assert_condition(leakage["exact_transcript_sentence_check"]["status"] == "pass", leakage)
    assert_condition(leakage["high_similarity_paraphrase_check"]["status"] == "pass", leakage)
    assert_condition(leakage["single_source_scenario_check"]["status"] == "pass", leakage)
    assert_condition(leakage["commercial_runtime_prompt_check"]["status"] == "pass", leakage)
    assert_condition(leakage["minimum_source_patterns_per_scenario"] == 3, leakage)

    assert_condition(len(scenarios) >= 6, scenarios)
    labels = {scenario["scenario_label"] for scenario in scenarios}
    assert_condition(
        {"sale_eligible", "support_only", "complaint_recovery", "escalation_only", "unsafe_for_closing"}.issubset(labels),
        labels,
    )
    for scenario in scenarios:
        assert_condition(len(scenario["source_pattern_ids"]) >= 3, scenario)
        assert_condition(scenario["copied_transcript_text_used"] is False, scenario)
        assert_condition(scenario["generated_from_single_transcript"] is False, scenario)
        assert_condition(scenario["contains_transcript_derived_prompt_text"] is False, scenario)
        assert_condition(scenario["expected_outcome"] in {"sale_ready", "non_sale_correct", "escalate", "end_call"}, scenario)

    forbidden = [
        "raw_transcript_text_stored\": true",
        "copied_transcript_text_used\": true",
        "generated_from_single_transcript\": true",
        "contains_transcript_derived_prompt_text\": true",
        "commercial_runtime_prompt_contamination_allowed\": true",
        "data/private",
        "customer phone",
        "credit card",
    ]
    normalized = combined_text.replace("\\", "/")
    for phrase in forbidden:
        assert_condition(phrase not in normalized, phrase)
    assert_condition("pattern grounding only" in combined_text, report)
    assert_condition("hard failure rate" in combined_text, report)
    assert_condition("non-sale correctness" in combined_text or "non sale correctness" in combined_text, report)


def main() -> None:
    for path, label in [
        (MODULE, "PROD-006 module"),
        (RUNNER, "PROD-006 runner"),
        (CASE_PATH, "PROD-006 case file"),
        (DOC_PATH, "Full-sale MVP strategy doc"),
    ]:
        assert_condition(path.exists(), f"{label} is missing: {path.relative_to(ROOT)}")

    registry = REFERENCE_REGISTRY.read_text(encoding="utf-8")
    assert_condition(EXPECTED_DATASET_URL in registry, "Dataset URL missing from thesis reference registry.")
    assert_condition(EXPECTED_PAPER_URL in registry, "Dataset paper URL missing from thesis reference registry.")
    assert_condition("pattern grounding" in registry.lower(), "Pattern-grounding reuse label missing from registry.")
    assert_condition(EXPECTED_LICENSE in registry.lower(), "Dataset license missing from registry.")

    commands = COMMANDS.read_text(encoding="utf-8")
    assert_condition("run_prod_006_full_sale_scenario_grounding.py" in commands, "PROD-006 runner missing from command map.")
    assert_condition("validate_prod_006_full_sale_scenario_grounding.py" in commands, "PROD-006 validator missing from command map.")

    completed = run_command([sys.executable, str(RUNNER), "--out", str(RESULT_PATH), "--report-out", str(REPORT_PATH)])
    assert_condition(completed.returncode == 0, f"Runner failed. stdout={completed.stdout!r} stderr={completed.stderr!r}")
    payload = json.loads(RESULT_PATH.read_text(encoding="utf-8"))
    report = REPORT_PATH.read_text(encoding="utf-8")
    validate_payload(payload, report)
    print("PROD-006 full-sale scenario grounding validation passed.")


if __name__ == "__main__":
    main()
