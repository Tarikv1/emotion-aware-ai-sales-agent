#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "scripts" / "callcenteren_specificity_scoring.py"
RUNNER = ROOT / "scripts" / "run_prod_017_callcenteren_specificity_scoring.py"
DOC_PATH = ROOT / "docs" / "product" / "PROD_017_CALLCENTEREN_SPECIFICITY_SCORING.md"
COMMANDS = ROOT / "docs" / "product" / "COMMANDS.md"
CHECKPOINT_INDEX = ROOT / "docs" / "product" / "CHECKPOINT_INDEX.md"
TMP_DIR = ROOT / ".tmp" / "prod-017-callcenteren-specificity-scoring"
SOURCE_RESULT = TMP_DIR / "prod-015-result-fixture.json"
RESULT_PATH = TMP_DIR / "result.json"
REPORT_PATH = TMP_DIR / "report.md"

EXPECTED_ID = "PROD-017-callcenteren-specificity-scoring"
EXPECTED_SOURCE_ID = "PROD-015-callcenteren-runtime-comparison"


def assert_condition(condition: bool, message: Any) -> None:
    if not condition:
        raise AssertionError(message)


def make_row(
    index: int,
    *,
    scenario_label: str,
    expected_outcome: str,
    customer_question: str,
    requirements: list[str],
    old_answer: str,
    retrieval_answer: str,
    retrieval_status: str = "influenced",
    retrieval_used: bool = True,
    old_score: int = 4,
    retrieval_score: int = 4,
) -> dict[str, Any]:
    return {
        "turn_id": f"fixture-specificity-{index:03d}::turn-001",
        "scenario_id": f"fixture-specificity-{index:03d}",
        "scenario_label": scenario_label,
        "domain": "software" if index % 2 else "telecom",
        "expected_outcome": expected_outcome,
        "customer_question": customer_question,
        "expected_agent_response_requirements": requirements,
        "avoid": ["vague_claim", "talks_too_much", "premature_close"],
        "old_runtime_answer": old_answer,
        "retrieval_runtime_answer": retrieval_answer,
        "old_runtime_score": old_score,
        "retrieval_runtime_score": retrieval_score,
        "score_delta": retrieval_score - old_score,
        "winner": "tie",
        "retrieval_status": retrieval_status,
        "retrieval_used_in_runtime": retrieval_used,
        "retrieved_item_ids": ["rag019-objection-authority-summary"] if retrieval_status != "blocked" else [],
        "retrieval_elapsed_ms": 2,
        "retrieval_target_ms": 150,
        "retrieval_acceptable_ms": 300,
        "hard_failure": False,
        "contains_payment_collection": False,
        "decision_trace": {
            "old_runtime": {
                "sales_difficulty": "unknown-runtime-signal",
                "detected_emotion": "neutral",
                "selected_strategy": "inquiry",
                "next_action": "ask-follow-up",
                "call_control": "continue-call",
                "final_response": old_answer,
            },
            "retrieval_runtime": {
                "sales_difficulty": "unknown-runtime-signal",
                "detected_emotion": "neutral",
                "selected_strategy": "inquiry",
                "next_action": "ask-follow-up",
                "call_control": "continue-call",
                "retrieval_status": retrieval_status,
                "retrieval_decision": "candidate_packet_created",
                "retrieved_item_ids": ["rag019-objection-authority-summary"],
                "advisory_hints": [
                    {
                        "item_id": "rag019-objection-authority-summary",
                        "lane": "response_wording",
                        "hint": "When another decision maker is involved, offer a short summary and ask which concern to address first.",
                        "match_score": 3,
                    }
                ],
                "context_flags": [],
                "blocked_reason": "",
                "retrieval_used_in_runtime": retrieval_used,
                "final_response": retrieval_answer,
            },
        },
    }


def write_fixture_prod_015_result() -> None:
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    generic = "Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?"
    rows = [
        make_row(
            1,
            scenario_label="sale_eligible",
            expected_outcome="sale_ready",
            customer_question="I cannot decide alone, so help me understand what I would need to discuss with the other decision maker.",
            requirements=[
                "acknowledge the customer's stated state without labeling their emotion as fact",
                "ask one focused discovery or clarification question before any close attempt",
                "avoid vague_claim, talks_too_much, premature_close",
            ],
            old_answer=generic,
            retrieval_answer="That makes sense. Should I send a short summary you can share with your boss, or is there one concern I should address first?",
        ),
        make_row(
            2,
            scenario_label="price_objection",
            expected_outcome="non_sale_correct",
            customer_question="Customer raises `too_expensive` and needs a `timeline_question` before any close.",
            requirements=[
                "separate price concern from value, timing, and contract concerns",
                "use cost or value framing only if campaign facts support it",
            ],
            old_answer=generic,
            retrieval_answer=generic,
            retrieval_status="retrieved_not_used",
            retrieval_used=False,
        ),
        make_row(
            3,
            scenario_label="support_handoff",
            expected_outcome="human_handoff",
            customer_question="I need a human specialist because my service issue is unresolved.",
            requirements=[
                "prioritize issue resolution before sales",
                "route or hand off instead of guessing",
                "avoid unsupported troubleshooting or product claims",
            ],
            old_answer=generic,
            retrieval_answer="Of course. I will route this to a specialist instead of continuing automatically.",
        ),
    ]
    payload = {
        "prod_015_id": EXPECTED_SOURCE_ID,
        "title": "PROD-015 CallCenterEN runtime comparison",
        "runtime_comparison": {
            "baseline_name": "old_runtime_retrieval_disabled",
            "candidate_name": "retrieval_runtime_rag_018_enabled",
            "campaign_id": "campaign-prod-005-b2b-software",
            "stratified_slice": True,
        },
        "summary": {
            "evaluated_scenario_count": 3,
            "evaluated_turn_count": len(rows),
            "hard_failure_count": 0,
            "leakage_finding_count": 0,
            "old_runtime_total_score": sum(item["old_runtime_score"] for item in rows),
            "retrieval_runtime_total_score": sum(item["retrieval_runtime_score"] for item in rows),
            "retrieval_turn_wins": 0,
            "old_runtime_turn_wins": 0,
            "tie_turns": len(rows),
            "provider_calls_made": False,
            "llm_used": False,
            "runtime_behavior_changed": False,
            "runtime_retrieval_default_enabled": False,
        },
        "metrics": {
            "hard_failure_rate": {"value": 0.0},
            "leakage_failure_rate": {"value": 0.0},
            "retrieval_win_rate": {"value": 0.0},
        },
        "turn_results": rows,
        "decision": "ready_for_review_no_retrieval_gain_on_slice",
    }
    SOURCE_RESULT.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False, timeout=180)


def validate_payload(payload: dict[str, Any], report: str) -> None:
    assert_condition(payload["prod_017_id"] == EXPECTED_ID, payload)
    assert_condition(payload["source_prod_015_result"]["prod_015_id"] == EXPECTED_SOURCE_ID, payload["source_prod_015_result"])
    assert_condition(payload["hypothesis"]["fixed_cases"] == "unchanged PROD-015 turn_results", payload["hypothesis"])
    assert_condition(payload["hypothesis"]["editable_surface_changed"] == "evaluation_scoring_only", payload["hypothesis"])

    schema = payload["scoring_schema"]
    for key in [
        "safety_gate",
        "question_relevance",
        "customer_specificity",
        "requirement_fit",
        "objection_fit",
        "generic_answer_penalty",
    ]:
        assert_condition(key in schema["components"], schema)

    summary = payload["summary"]
    assert_condition(summary["analyzed_turn_count"] == 3, summary)
    assert_condition(summary["runtime_behavior_changed"] is False, summary)
    assert_condition(summary["runtime_retrieval_default_enabled"] is False, summary)
    assert_condition(summary["provider_calls_made"] is False, summary)
    assert_condition(summary["hard_failure_count"] == 0, summary)
    assert_condition(summary["leakage_finding_count"] == 0, summary)
    assert_condition(summary["prod_015_tie_count"] == 3, summary)
    assert_condition(summary["prod_017_retrieval_wins"] == 2, summary)
    assert_condition(summary["prod_017_old_wins"] == 0, summary)
    assert_condition(summary["prod_017_ties"] == 1, summary)
    assert_condition(summary["specificity_scoring_detected_delta"] is True, summary)
    assert_condition(summary["specificity_blind_spot_confirmed"] is True, summary)
    assert_condition(summary["retrieval_total_score"] > summary["old_total_score"], summary)
    assert_condition(summary["absolute_quality_gap_count"] >= 1, summary)

    rows = payload["turn_scores"]
    assert_condition(len(rows) == 3, rows)
    changed = [row for row in rows if row["turn_id"] == "fixture-specificity-001::turn-001"][0]
    assert_condition(changed["winner"] == "retrieval", changed)
    assert_condition(changed["retrieval_score"]["customer_specificity"] > changed["old_score"]["customer_specificity"], changed)
    assert_condition(changed["retrieval_score"]["objection_fit"] > changed["old_score"]["objection_fit"], changed)

    support = [row for row in rows if row["turn_id"] == "fixture-specificity-003::turn-001"][0]
    assert_condition(support["winner"] == "retrieval", support)
    assert_condition(support["retrieval_score"]["requirement_fit"] > support["old_score"]["requirement_fit"], support)

    price = [row for row in rows if row["turn_id"] == "fixture-specificity-002::turn-001"][0]
    assert_condition(price["winner"] == "tie", price)
    assert_condition(price["old_score"]["generic_answer_penalty"] < 0, price)
    assert_condition(price["retrieval_score"]["generic_answer_penalty"] < 0, price)

    recommendations = {item["recommendation_id"] for item in payload["recommendations"]}
    for required in [
        "use_prod_017_scoring_as_next_composer_gate",
        "do_not_claim_retrieval_gain_until_composer_changes_more_answers",
        "add_naturalized_prompt_variant_after_scoring",
    ]:
        assert_condition(required in recommendations, recommendations)

    assert_condition(payload["decision"] == "use_specificity_scoring_before_composer_hook_test", payload["decision"])
    assert_condition(payload["boundaries"]["runtime_behavior_changed"] is False, payload["boundaries"])
    assert_condition(payload["boundaries"]["provider_calls_made"] is False, payload["boundaries"])

    for required in [
        "PROD-017 CallCenterEN Specificity Scoring",
        "specificity blind spot confirmed",
        "evaluation scoring only",
        "question relevance",
        "customer specificity",
        "objection fit",
        "use specificity scoring before composer hook test",
    ]:
        assert_condition(required.lower() in report.lower(), required)

    combined = (json.dumps(payload, ensure_ascii=False).lower() + "\n" + report.lower()).replace("\\", "/")
    for forbidden in [
        '"raw_transcript_text":',
        '"source_excerpt_text":',
        '"transcript":',
        "data/private",
        "data/private-restricted",
        "provider call made",
    ]:
        assert_condition(forbidden not in combined, forbidden)


def main() -> None:
    for path, label in [
        (MODULE, "PROD-017 module"),
        (RUNNER, "PROD-017 runner"),
        (DOC_PATH, "PROD-017 product doc"),
    ]:
        assert_condition(path.exists(), f"{label} is missing: {path.relative_to(ROOT)}")

    commands = COMMANDS.read_text(encoding="utf-8")
    assert_condition("run_prod_017_callcenteren_specificity_scoring.py" in commands, "PROD-017 runner missing from command map.")
    assert_condition("validate_prod_017_callcenteren_specificity_scoring.py" in commands, "PROD-017 validator missing from command map.")
    checkpoint_index = CHECKPOINT_INDEX.read_text(encoding="utf-8")
    assert_condition("PROD_017_CALLCENTEREN_SPECIFICITY_SCORING.md" in checkpoint_index, "PROD-017 missing from checkpoint index.")

    write_fixture_prod_015_result()
    completed = run_command(
        [
            sys.executable,
            str(RUNNER),
            "--prod-015-result",
            str(SOURCE_RESULT),
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
    print("PROD-017 CallCenterEN specificity scoring validation passed.")


if __name__ == "__main__":
    main()
