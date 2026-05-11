#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-045-core-sales-policy-regression-rerun"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID

REQUIRED_FILES = {
    "module": ROOT / "scripts" / "prod_045_core_sales_policy_regression_rerun.py",
    "runner": ROOT / "scripts" / "run_prod_045_core_sales_policy_regression_rerun.py",
    "validator": ROOT / "scripts" / "validate_prod_045_core_sales_policy_regression_rerun.py",
    "doc": ROOT / "docs" / "product" / "PROD_045_CORE_SALES_POLICY_REGRESSION_RERUN.md",
    "result": OUT_DIR / "result.json",
    "report": OUT_DIR / "report.md",
    "cases": OUT_DIR / "regression_cases.json",
    "results": OUT_DIR / "regression_results.json",
    "hardening": OUT_DIR / "evaluator_hardening_results.json",
    "change_summary": OUT_DIR / "runtime_policy_change_summary.json",
    "review_data": OUT_DIR / "prod_045_review_data.json",
    "review_html": OUT_DIR / "prod_045_review.html",
}

SOURCE_FILES = [
    ROOT / "research" / "experiments" / "generated" / "PROD-043-sales-playbook-runtime-adapter" / "result.json",
    ROOT / "research" / "experiments" / "generated" / "PROD-044-core-sales-policy-update" / "result.json",
    ROOT / "research" / "experiments" / "generated" / "PROD-044-core-sales-policy-update" / "core_sales_policy_review_packet.json",
]

BOUNDARY_FALSE_FIELDS = [
    "retrieval_enabled",
    "provider_calls_made",
    "llm_used",
    "private_data_read",
    "dataset_download_performed",
    "production_runtime_promotion_allowed",
    "voice_playback_unblocked",
    "public_demo_polish_unblocked",
    "payment_collection_allowed",
    "contract_signing_allowed",
    "uses_exact_transcript_text",
    "uses_source_transcript_sequence",
    "uses_dataset_specific_phrasing",
]

REQUIRED_MOVES = {
    "price_first",
    "who_are_you",
    "send_info",
    "email_only",
    "scam_or_card_fear",
    "payment_safety_fear",
    "support_issue",
    "cancellation_request",
    "technical_question",
    "security_review",
    "coverage_confusion",
    "sensitive_healthcare_concern",
    "existing_provider",
    "needs_manager_approval",
    "needs_spouse_or_partner_input",
    "sale_ready_interest",
}

PHONE_PATTERN = re.compile(r"\b(?:\+?\d[\d\-\(\) ]{7,}\d)\b")
EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")


def assert_condition(condition: bool, message: Any) -> None:
    if not condition:
        raise AssertionError(message)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def run_runner() -> None:
    completed = subprocess.run(
        [sys.executable, str(REQUIRED_FILES["runner"])],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=240,
        check=False,
    )
    assert_condition(completed.returncode == 0, f"runner failed stdout={completed.stdout!r} stderr={completed.stderr!r}")


def validate_existence() -> None:
    missing = [rel(path) for path in [*REQUIRED_FILES.values(), *SOURCE_FILES] if not path.exists()]
    assert_condition(not missing, f"missing required files: {missing}")


def validate_sources() -> None:
    for source in SOURCE_FILES[:2]:
        result = read_json(source)
        assert_condition(result.get("validation", {}).get("passed") is True, f"source validation did not pass: {rel(source)}")


def validate_result() -> dict[str, Any]:
    result = read_json(REQUIRED_FILES["result"])
    summary = result.get("summary", {})
    assert_condition(result.get("checkpoint_id") == CHECKPOINT_ID, result)
    assert_condition(result.get("validation", {}).get("passed") is True, result)
    assert_condition(summary.get("runtime_behavior_changed") is True, summary)
    assert_condition(summary.get("runtime_agent_modified") is True, summary)
    for field in BOUNDARY_FALSE_FIELDS:
        assert_condition(summary.get(field) is False, f"{field} must remain false")
    assert_condition(summary.get("generic_clarification_unexpected_pass_count") == 0, summary)
    assert_condition(summary.get("generic_runtime_response_count") == 0, summary)
    assert_condition(summary.get("regression_fail_count") == 0, summary)
    assert_condition(summary.get("payment_collection_violation_count") == 0, summary)
    assert_condition(summary.get("contract_signing_violation_count") == 0, summary)
    assert_condition(summary.get("unsupported_claim_violation_count") == 0, summary)
    return result


def validate_hardening() -> None:
    hardening = read_json(REQUIRED_FILES["hardening"])
    rows = hardening.get("generic_clarification_results", [])
    moves = {row["customer_move_id"] for row in rows}
    assert_condition(REQUIRED_MOVES.issubset(moves), f"missing hardening moves: {REQUIRED_MOVES - moves}")
    assert_condition(hardening.get("generic_clarification_unexpected_pass_count") == 0, hardening)
    for row in rows:
        assert_condition(row.get("passed") is False, row)
        assert_condition(row.get("failed_check_ids"), row)


def validate_regressions() -> None:
    payload = read_json(REQUIRED_FILES["results"])
    results = payload.get("results", [])
    assert_condition(results, "regression results missing")
    moves = {item["customer_move_id"] for item in results}
    assert_condition(REQUIRED_MOVES.issubset(moves), f"missing regression moves: {REQUIRED_MOVES - moves}")
    for item in results:
        decision = item["runtime_decision"]
        assert_condition(item.get("passed") is True, item)
        assert_condition(item.get("generic_response_used") is False, item)
        assert_condition(decision.get("sales_difficulty") != "unknown-runtime-signal", item)
        assert_condition(item.get("required_action_evaluation", {}).get("passed") is True, item)
        response = decision.get("agent_response", "").lower()
        assert_condition("may i ask one quick clarifying question" not in response, item)
        assert_condition("collect payment" not in response, item)
        assert_condition("sign a contract" not in response, item)

    by_id = {item["case_id"]: item for item in results}
    assert_condition(by_id["prod-045-support"]["runtime_decision"]["call_control"] == "transfer-or-escalate", by_id["prod-045-support"])
    assert_condition(by_id["prod-045-cancellation"]["runtime_decision"]["call_control"] == "transfer-or-escalate", by_id["prod-045-cancellation"])
    assert_condition(by_id["prod-045-hostile"]["runtime_decision"]["call_control"] == "end-call", by_id["prod-045-hostile"])
    assert_condition(by_id["prod-045-callback"]["runtime_decision"]["call_control"] == "end-call", by_id["prod-045-callback"])
    assert_condition(by_id["prod-045-sale-ready-ok"]["runtime_decision"]["call_control"] == "close-and-log-sale-ready", by_id["prod-045-sale-ready-ok"])
    assert_condition(by_id["prod-045-sale-ready-missing"]["runtime_decision"]["call_control"] == "continue-call", by_id["prod-045-sale-ready-missing"])
    assert_condition(by_id["prod-045-product-detail"]["runtime_decision"]["call_control"] == "bridge-then-continue", by_id["prod-045-product-detail"])
    assert_condition(by_id["prod-045-scheduling"]["runtime_decision"]["call_control"] == "schedule-and-end", by_id["prod-045-scheduling"])


def validate_review_and_docs() -> None:
    doc_text = REQUIRED_FILES["doc"].read_text(encoding="utf-8").lower()
    for marker in ("prod-045", "generic clarification", "runtime behavior changed: `true`", "retrieval enabled: `false`"):
        assert_condition(marker in doc_text, f"doc missing {marker}")
    html_text = REQUIRED_FILES["review_html"].read_text(encoding="utf-8").lower()
    for marker in ("evaluator hardening", "runtime regression cases", "applied runtime policy updates", "boundary summary"):
        assert_condition(marker in html_text, f"html missing {marker}")

    for key in ("report", "review_html", "review_data", "cases", "results", "hardening", "change_summary"):
        path = REQUIRED_FILES[key]
        text = path.read_text(encoding="utf-8")
        assert_condition("transcript_body" not in text.lower(), f"transcript body dump marker found in {key}")
        assert_condition(not PHONE_PATTERN.search(text), f"phone-like string found in {key}")
        assert_condition(not EMAIL_PATTERN.search(text), f"email-like string found in {key}")


def main() -> None:
    validate_existence()
    validate_sources()
    run_runner()
    validate_existence()
    result = validate_result()
    validate_hardening()
    validate_regressions()
    validate_review_and_docs()
    print(json.dumps({"checkpoint_id": CHECKPOINT_ID, "validation": {"passed": True}, "summary": result["summary"]}, indent=2))


if __name__ == "__main__":
    main()
