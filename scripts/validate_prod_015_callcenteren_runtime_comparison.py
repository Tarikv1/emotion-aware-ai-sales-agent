#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "scripts" / "callcenteren_runtime_comparison.py"
RUNNER = ROOT / "scripts" / "run_prod_015_callcenteren_runtime_comparison.py"
DOC_PATH = ROOT / "docs" / "product" / "PROD_015_CALLCENTEREN_RUNTIME_COMPARISON.md"
COMMANDS = ROOT / "docs" / "product" / "COMMANDS.md"
CHECKPOINT_INDEX = ROOT / "docs" / "product" / "CHECKPOINT_INDEX.md"
TMP_DIR = ROOT / ".tmp" / "prod-015-callcenteren-runtime-comparison"
SCENARIO_BANK = TMP_DIR / "prod-014-scenario-bank-fixture.json"
RESULT_PATH = TMP_DIR / "result.json"
REPORT_PATH = TMP_DIR / "report.md"

EXPECTED_ID = "PROD-015-callcenteren-runtime-comparison"
EXPECTED_SOURCE_ID = "PROD-014-callcenteren-scenario-bank"
EXPECTED_DATASET_URL = "https://huggingface.co/datasets/AIxBlock/92k-real-world-call-center-scripts-english"
EXPECTED_PAPER_URL = "https://arxiv.org/abs/2507.02958"
EXPECTED_LICENSE = "cc-by-nc-4.0"
EXPECTED_LABELS = {
    "sale_eligible",
    "price_objection",
    "callback_request",
    "cancellation_boundary",
    "support_handoff",
    "trust_repair",
}


def assert_condition(condition: bool, message: Any) -> None:
    if not condition:
        raise AssertionError(message)


def scenario(
    index: int,
    label: str,
    *,
    prompt: str,
    outcome: str,
    emotion: str,
    objection: str,
    tactic: str,
) -> dict[str, Any]:
    domain = ["software", "telecom", "insurance", "home_service", "medical_equipment", "energy"][index % 6]
    return {
        "scenario_id": f"prod-014-fixture-{label}-{index:03d}",
        "scenario_label": label,
        "domain": domain,
        "source_recipe": {
            "source_pattern_bank": "PROD-013-callcenteren-pattern-extraction",
            "minimum_source_patterns": 5,
            "source_pattern_categories": [
                "scenario_template",
                "domain_pattern",
                "customer_intent",
                "objection",
                "persuasion_strategy",
                "discovery_question",
            ],
            "variant_index": index,
            "variant_source_pattern_ids": [
                f"objection-{objection}-{index:03d}",
                f"persuasion-{tactic}-{index:03d}",
                f"emotion-{emotion}-{index:03d}",
                f"close-trial_close-{index:03d}",
            ],
            "uses_exact_transcript_text": False,
            "uses_single_source_transcript": False,
        },
        "source_pattern_ids": [
            f"scenario-template-{index:03d}",
            f"domain-{domain}",
            f"intent-{label}-{index:03d}",
            f"objection-{objection}-{index:03d}",
            f"persuasion-{tactic}-{index:03d}",
            f"discovery-question-{index:03d}",
        ],
        "source_pattern_category_count": 6,
        "customer_persona": "fixture_customer",
        "initial_intent": label,
        "likely_objection": objection,
        "starting_emotion": emotion,
        "safe_agent_tactic": tactic,
        "bad_tactics_to_avoid": ["pushy", "unsupported_claim", "premature_close"],
        "expected_outcome": outcome,
        "safe_close_definition": "verbal commitment or sale-ready outcome without payment collection",
        "support_or_boundary_first": outcome in {"support_only", "human_handoff", "end_call", "non_sale_correct"},
        "commercial_runtime_prompt_safe": True,
        "copied_transcript_text_used": False,
        "generated_from_single_source_transcript": False,
        "contains_transcript_derived_prompt_text": False,
        "turns": [
            {
                "turn_id": "turn-001",
                "stage": "relevance-check",
                "customer_prompt": prompt,
                "customer_intent": label,
                "customer_emotion": emotion,
                "expected_agent_response_requirements": [
                    "acknowledge the customer's stated state without labeling their emotion as fact",
                    "ask one focused discovery or clarification question before any close attempt",
                    "avoid payment collection",
                ],
                "avoid": ["pushy", "unsupported_claim", "premature_close"],
            },
            {
                "turn_id": "turn-002",
                "stage": "clarification",
                "customer_prompt": f"Customer raises `{objection}` and asks for a safe next step.",
                "customer_intent": label,
                "customer_emotion": emotion,
                "expected_agent_response_requirements": [
                    "answer the objection without unsupported claims",
                    "ask one focused discovery question",
                    "avoid payment collection",
                ],
                "avoid": ["pushy", "unsupported_claim", "premature_close"],
            },
            {
                "turn_id": "turn-003",
                "stage": "trial_close",
                "customer_prompt": "Customer asks what the next safe step would be.",
                "customer_intent": label,
                "customer_emotion": "neutral",
                "expected_agent_response_requirements": [
                    "confirm the next step without collecting payment",
                    "avoid unsupported claims",
                ],
                "avoid": ["pushy", "unsupported_claim", "premature_close"],
            },
        ],
    }


def write_fixture_scenario_bank() -> None:
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    prompts = [
        ("sale_eligible", "I am interested, but I need to know if this is worth the effort for my situation.", "sale_ready", "interested", "contract_fear", "benefit_framing"),
        ("price_objection", "This sounds too expensive, and I am not sure the review is worth the effort.", "non_sale_correct", "skeptical", "too_expensive", "pain_point_discovery"),
        ("callback_request", "I cannot talk now; send information or give me one reason to schedule a callback.", "callback_agreed", "neutral", "no_time", "callback_close"),
        ("cancellation_boundary", "No thanks, I am not interested and I do not want a sales push.", "end_call", "annoyed", "not_interested", "empathy_first"),
        ("support_handoff", "I need a human specialist because my service issue is unresolved.", "human_handoff", "angry", "bad_previous_experience", "handoff_close"),
        ("trust_repair", "I do not trust this call, so explain what can be verified without pressuring me.", "support_only", "skeptical", "does_not_trust_agent", "empathy_first"),
    ]
    scenarios = []
    for round_index in range(3):
        for offset, item in enumerate(prompts):
            scenarios.append(scenario(round_index * len(prompts) + offset + 1, item[0], prompt=item[1], outcome=item[2], emotion=item[3], objection=item[4], tactic=item[5]))
    payload = {
        "prod_014_id": EXPECTED_SOURCE_ID,
        "dataset_source": {
            "dataset_name": "AIxBlock/92k-real-world-call-center-scripts-english",
            "dataset_url": EXPECTED_DATASET_URL,
            "paper_url": EXPECTED_PAPER_URL,
            "license": EXPECTED_LICENSE,
        },
        "scenario_generation": {
            "mode": "expanded_multi_pattern_combinatorial",
            "default_scenario_count": 240,
        },
        "reuse_boundary": {
            "reuse_label": "abstract_scenario_bank_only",
            "raw_transcript_text_stored": False,
            "commercial_runtime_prompt_text_from_transcripts_allowed": False,
        },
        "summary": {
            "scenario_count": len(scenarios),
            "turn_count": sum(len(item["turns"]) for item in scenarios),
            "leakage_finding_count": 0,
            "provider_calls_made": False,
            "llm_used": False,
            "runtime_behavior_changed": False,
        },
        "scenario_bank": scenarios,
        "leakage_tests": {"findings": []},
    }
    SCENARIO_BANK.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False, timeout=180)


def validate_payload(payload: dict[str, Any], report: str) -> None:
    assert_condition(payload["prod_015_id"] == EXPECTED_ID, payload)
    assert_condition(payload["source_scenario_bank"]["prod_014_id"] == EXPECTED_SOURCE_ID, payload["source_scenario_bank"])
    assert_condition(payload["dataset_source"]["dataset_url"] == EXPECTED_DATASET_URL, payload["dataset_source"])
    assert_condition(payload["dataset_source"]["paper_url"] == EXPECTED_PAPER_URL, payload["dataset_source"])
    assert_condition(payload["dataset_source"]["license"] == EXPECTED_LICENSE, payload["dataset_source"])

    summary = payload["summary"]
    assert_condition(summary["evaluated_scenario_count"] == 12, summary)
    assert_condition(summary["evaluated_turn_count"] == 36, summary)
    assert_condition(summary["stratified_slice"] is True, summary)
    assert_condition(summary["source_bank_scenario_count"] == 18, summary)
    assert_condition(summary["provider_calls_made"] is False, summary)
    assert_condition(summary["llm_used"] is False, summary)
    assert_condition(summary["runtime_behavior_changed"] is False, summary)
    assert_condition(summary["runtime_retrieval_default_enabled"] is False, summary)
    assert_condition(summary["leakage_finding_count"] == 0, summary)

    labels = set(summary["covered_scenario_labels"])
    assert_condition(EXPECTED_LABELS <= labels, labels)

    metrics = payload["metrics"]
    for key in [
        "hard_failure_rate",
        "non_sale_correctness",
        "safe_close_correctness",
        "discovery_before_close_rate",
        "emotional_handling_score",
        "leakage_failure_rate",
        "retrieval_win_rate",
    ]:
        assert_condition(key in metrics and "value" in metrics[key], metrics)
    assert_condition(metrics["hard_failure_rate"]["value"] == 0.0, metrics["hard_failure_rate"])
    assert_condition(metrics["leakage_failure_rate"]["value"] == 0.0, metrics["leakage_failure_rate"])
    assert_condition(metrics["non_sale_correctness"]["value"] >= 0.9, metrics["non_sale_correctness"])
    assert_condition(metrics["safe_close_correctness"]["value"] >= 0.9, metrics["safe_close_correctness"])

    comparison = payload["comparison"]
    for key in ["old_runtime_total_score", "retrieval_runtime_total_score", "retrieval_turn_wins", "old_runtime_turn_wins", "tie_turns"]:
        assert_condition(key in comparison, comparison)
    assert_condition(comparison["baseline_name"] == "old_runtime_retrieval_disabled", comparison)
    assert_condition(comparison["candidate_name"] == "retrieval_runtime_rag_018_enabled", comparison)
    assert_condition(comparison["retrieval_runtime_total_score"] >= comparison["old_runtime_total_score"], comparison)

    leakage = payload["leakage_tests"]
    assert_condition(leakage["exact_transcript_sentence_check"]["status"] == "pass", leakage)
    assert_condition(leakage["high_similarity_paraphrase_check"]["status"] == "pass", leakage)
    assert_condition(leakage["single_source_scenario_check"]["status"] == "pass", leakage)
    assert_condition(leakage["commercial_runtime_prompt_check"]["status"] == "pass", leakage)
    assert_condition(leakage["findings"] == [], leakage)

    rows = payload["turn_results"]
    assert_condition(len(rows) == 36, len(rows))
    for row in rows:
        assert_condition(row["customer_question"], row)
        assert_condition(row["old_runtime_answer"], row)
        assert_condition(row["retrieval_runtime_answer"], row)
        assert_condition("decision_trace" in row, row)
        trace = row["decision_trace"]
        assert_condition("old_runtime" in trace and "retrieval_runtime" in trace and "scoring" in trace, trace)
        assert_condition(row["scenario_label"] in EXPECTED_LABELS, row)
        assert_condition(row["expected_outcome"] in {"sale_ready", "callback_agreed", "non_sale_correct", "support_only", "human_handoff", "end_call"}, row)
        assert_condition(row["hard_failure"] is False, row)
        assert_condition(row["contains_payment_collection"] is False, row)

    combined = (json.dumps(payload, ensure_ascii=False).lower() + "\n" + report.lower()).replace("\\", "/")
    forbidden = [
        '"raw_transcript_text":',
        '"source_excerpt_text":',
        '"transcript":',
        "data/private",
        "data/private-restricted",
        "credit card",
        "take your payment",
        "commercial runtime prompt source",
    ]
    for token in forbidden:
        assert_condition(token not in combined, token)

    for required in [
        "PROD-015 CallCenterEN Runtime Comparison",
        "exact customer question",
        "exact old runtime answer",
        "exact retrieval runtime answer",
        "decision trace",
        "hard failure rate",
        "non-sale correctness",
        "ready for review",
    ]:
        assert_condition(required.lower() in report.lower(), required)


def main() -> None:
    for path, label in [
        (MODULE, "PROD-015 module"),
        (RUNNER, "PROD-015 runner"),
        (DOC_PATH, "PROD-015 product doc"),
    ]:
        assert_condition(path.exists(), f"{label} is missing: {path.relative_to(ROOT)}")

    commands = COMMANDS.read_text(encoding="utf-8")
    assert_condition("run_prod_015_callcenteren_runtime_comparison.py" in commands, "PROD-015 runner missing from command map.")
    assert_condition("validate_prod_015_callcenteren_runtime_comparison.py" in commands, "PROD-015 validator missing from command map.")
    checkpoint_index = CHECKPOINT_INDEX.read_text(encoding="utf-8")
    assert_condition("PROD_015_CALLCENTEREN_RUNTIME_COMPARISON.md" in checkpoint_index, "PROD-015 missing from checkpoint index.")

    write_fixture_scenario_bank()
    completed = run_command(
        [
            sys.executable,
            str(RUNNER),
            "--scenario-bank",
            str(SCENARIO_BANK),
            "--out",
            str(RESULT_PATH),
            "--report-out",
            str(REPORT_PATH),
            "--limit-scenarios",
            "12",
            "--leakage-sentence-limit",
            "0",
        ]
    )
    assert_condition(completed.returncode == 0, f"Runner failed. stdout={completed.stdout!r} stderr={completed.stderr!r}")
    payload = json.loads(RESULT_PATH.read_text(encoding="utf-8"))
    report = REPORT_PATH.read_text(encoding="utf-8")
    validate_payload(payload, report)
    print("PROD-015 CallCenterEN runtime comparison validation passed.")


if __name__ == "__main__":
    main()
