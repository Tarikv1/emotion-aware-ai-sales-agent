#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "scripts" / "callcenteren_retrieval_no_gain_diagnosis.py"
RUNNER = ROOT / "scripts" / "run_prod_016_callcenteren_retrieval_no_gain_diagnosis.py"
DOC_PATH = ROOT / "docs" / "product" / "PROD_016_CALLCENTEREN_RETRIEVAL_NO_GAIN_DIAGNOSIS.md"
COMMANDS = ROOT / "docs" / "product" / "COMMANDS.md"
CHECKPOINT_INDEX = ROOT / "docs" / "product" / "CHECKPOINT_INDEX.md"
TMP_DIR = ROOT / ".tmp" / "prod-016-callcenteren-retrieval-no-gain-diagnosis"
SOURCE_RESULT = TMP_DIR / "prod-015-result-fixture.json"
RESULT_PATH = TMP_DIR / "result.json"
REPORT_PATH = TMP_DIR / "report.md"

EXPECTED_ID = "PROD-016-callcenteren-retrieval-no-gain-diagnosis"
EXPECTED_SOURCE_ID = "PROD-015-callcenteren-runtime-comparison"


def assert_condition(condition: bool, message: Any) -> None:
    if not condition:
        raise AssertionError(message)


def row(
    index: int,
    *,
    label: str,
    status: str,
    used: bool,
    changed: bool,
    winner: str = "tie",
    difficulty: str = "unknown-runtime-signal",
    next_action: str = "ask-follow-up",
    old_score: int = 4,
    retrieval_score: int = 4,
    question: str | None = None,
    item_ids: list[str] | None = None,
) -> dict[str, Any]:
    old_answer = "Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?"
    retrieval_answer = (
        "That makes sense. Should I send a short summary you can share with your boss, or is there one concern I should address first?"
        if changed
        else old_answer
    )
    return {
        "turn_id": f"fixture-scenario-{index:03d}::turn-001",
        "scenario_id": f"fixture-scenario-{index:03d}",
        "scenario_label": label,
        "domain": "software" if index % 2 else "telecom",
        "customer_question": question or "I need time to think, so do not rush me into a decision.",
        "old_runtime_answer": old_answer,
        "retrieval_runtime_answer": retrieval_answer,
        "old_runtime_score": old_score,
        "retrieval_runtime_score": retrieval_score,
        "score_delta": retrieval_score - old_score,
        "winner": winner,
        "retrieval_status": status,
        "retrieval_used_in_runtime": used,
        "retrieved_item_ids": item_ids or ["rag007-response-yes-and-objection-framing"],
        "retrieval_elapsed_ms": 2,
        "retrieval_target_ms": 150,
        "retrieval_acceptable_ms": 300,
        "hard_failure": False,
        "contains_payment_collection": False,
        "expected_outcome": "non_sale_correct" if label != "sale_eligible" else "sale_ready",
        "decision_trace": {
            "old_runtime": {
                "sales_difficulty": difficulty,
                "detected_emotion": "neutral",
                "selected_strategy": "inquiry",
                "next_action": next_action,
                "call_control": "continue-call",
                "final_response": old_answer,
            },
            "retrieval_runtime": {
                "sales_difficulty": difficulty,
                "detected_emotion": "neutral",
                "selected_strategy": "inquiry",
                "next_action": next_action,
                "call_control": "continue-call",
                "retrieval_status": status,
                "retrieval_decision": "candidate_packet_created" if status != "blocked" else "blocked",
                "retrieved_item_ids": [] if status == "blocked" else (item_ids or ["rag007-response-yes-and-objection-framing"]),
                "advisory_hints": []
                if status in {"blocked", "no_match"}
                else [
                    {
                        "item_id": (item_ids or ["rag007-response-yes-and-objection-framing"])[0],
                        "lane": "response_wording",
                        "hint": "Acknowledge the customer concern before moving to a useful next step.",
                        "match_score": 3,
                    }
                ],
                "context_flags": ["human_escalation"] if status == "blocked" else [],
                "blocked_reason": "human_escalation_overrides_retrieval" if status == "blocked" else "",
                "retrieval_used_in_runtime": used,
                "final_response": retrieval_answer,
            },
            "scoring": {
                "old_runtime": {"score": old_score},
                "retrieval_runtime": {"score": retrieval_score},
                "winner": winner,
                "hard_failure": False,
            },
        },
    }


def write_fixture_prod_015_result() -> None:
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    rows = [
        row(1, label="callback_request", status="retrieved_not_used", used=False, changed=False),
        row(2, label="price_objection", status="retrieved_not_used", used=False, changed=False),
        row(3, label="trust_repair", status="retrieved_not_used", used=False, changed=False),
        row(
            4,
            label="sale_eligible",
            status="influenced",
            used=True,
            changed=True,
            question="I cannot decide alone, so help me understand what I would need to discuss with the other decision maker.",
            item_ids=["rag019-objection-authority-summary"],
        ),
        row(5, label="support_handoff", status="blocked", used=False, changed=False, difficulty="human-request", next_action="transfer-or-escalate"),
        row(6, label="cancellation_boundary", status="no_match", used=False, changed=False, item_ids=[]),
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
            "evaluated_scenario_count": 6,
            "evaluated_turn_count": len(rows),
            "covered_scenario_labels": sorted({item["scenario_label"] for item in rows}),
            "covered_domain_count": 2,
            "hard_failure_count": 0,
            "leakage_finding_count": 0,
            "old_runtime_total_score": sum(item["old_runtime_score"] for item in rows),
            "retrieval_runtime_total_score": sum(item["retrieval_runtime_score"] for item in rows),
            "retrieval_turn_wins": 0,
            "old_runtime_turn_wins": 0,
            "tie_turns": len(rows),
            "retrieval_influenced_count": 1,
            "retrieval_blocked_count": 1,
            "retrieval_no_match_count": 1,
            "retrieval_retrieved_not_used_count": 3,
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
    assert_condition(payload["prod_016_id"] == EXPECTED_ID, payload)
    assert_condition(payload["source_prod_015_result"]["prod_015_id"] == EXPECTED_SOURCE_ID, payload["source_prod_015_result"])
    assert_condition(payload["source_prod_015_result"]["turn_count"] == 6, payload["source_prod_015_result"])

    summary = payload["summary"]
    assert_condition(summary["no_gain_confirmed"] is True, summary)
    assert_condition(summary["runtime_behavior_changed"] is False, summary)
    assert_condition(summary["runtime_retrieval_default_enabled"] is False, summary)
    assert_condition(summary["hard_failure_count"] == 0, summary)
    assert_condition(summary["leakage_finding_count"] == 0, summary)
    assert_condition(summary["answer_changed_count"] == 1, summary)
    assert_condition(summary["unchanged_answer_count"] == 5, summary)
    assert_condition(summary["influenced_but_tied_count"] == 1, summary)
    assert_condition(summary["retrieved_not_used_rate"] == 0.5, summary)
    assert_condition(summary["matching_not_primary"] is True, summary)
    assert_condition(summary["composer_influence_gap"] is True, summary)
    assert_condition(summary["scoring_blind_spot_risk"] is True, summary)

    failure_classes = {item["class_id"] for item in payload["failure_classes"]}
    for required in [
        "composer_influence_gap",
        "scoring_blind_spot",
        "runtime_classifier_mismatch",
        "campaign_domain_mismatch",
    ]:
        assert_condition(required in failure_classes, failure_classes)

    recommendations = {item["recommendation_id"] for item in payload["recommendations"]}
    for required in [
        "add_specificity_scoring_before_claiming_gain",
        "add_composer_hooks_for_generated_objection_labels",
        "verbalize_rubric_like_scenario_turns",
        "route_scenarios_to_domain_campaigns",
    ]:
        assert_condition(required in recommendations, recommendations)

    assert_condition(payload["decision"] == "diagnose_before_retrieval_runtime_promotion", payload["decision"])
    assert_condition(payload["boundaries"]["provider_calls_made"] is False, payload["boundaries"])
    assert_condition(payload["boundaries"]["runtime_behavior_changed"] is False, payload["boundaries"])

    for required in [
        "PROD-016 CallCenterEN Retrieval No-Gain Diagnosis",
        "composer influence gap",
        "scoring blind spot",
        "runtime classifier mismatch",
        "campaign domain mismatch",
        "diagnose before retrieval runtime promotion",
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
        (MODULE, "PROD-016 module"),
        (RUNNER, "PROD-016 runner"),
        (DOC_PATH, "PROD-016 product doc"),
    ]:
        assert_condition(path.exists(), f"{label} is missing: {path.relative_to(ROOT)}")

    commands = COMMANDS.read_text(encoding="utf-8")
    assert_condition("run_prod_016_callcenteren_retrieval_no_gain_diagnosis.py" in commands, "PROD-016 runner missing from command map.")
    assert_condition("validate_prod_016_callcenteren_retrieval_no_gain_diagnosis.py" in commands, "PROD-016 validator missing from command map.")
    checkpoint_index = CHECKPOINT_INDEX.read_text(encoding="utf-8")
    assert_condition("PROD_016_CALLCENTEREN_RETRIEVAL_NO_GAIN_DIAGNOSIS.md" in checkpoint_index, "PROD-016 missing from checkpoint index.")

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
    print("PROD-016 CallCenterEN retrieval no-gain diagnosis validation passed.")


if __name__ == "__main__":
    main()
