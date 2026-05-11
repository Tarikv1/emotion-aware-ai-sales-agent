#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-046B-german-response-wording-quality-pass"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID

REQUIRED_FILES = {
    "module": ROOT / "scripts" / "prod_046b_german_response_wording_quality_pass.py",
    "runner": ROOT / "scripts" / "run_prod_046b_german_response_wording_quality_pass.py",
    "validator": ROOT / "scripts" / "validate_prod_046b_german_response_wording_quality_pass.py",
    "doc": ROOT / "docs" / "product" / "PROD_046B_GERMAN_RESPONSE_WORDING_QUALITY_PASS.md",
    "result": OUT_DIR / "result.json",
    "report": OUT_DIR / "report.md",
    "before_after": OUT_DIR / "german_wording_before_after.json",
    "findings": OUT_DIR / "german_wording_findings.json",
    "rerun_results": OUT_DIR / "german_regression_rerun_results.json",
    "review_data": OUT_DIR / "prod_046b_review_data.json",
    "review_html": OUT_DIR / "prod_046b_review.html",
    "prod_045_result": ROOT / "research" / "experiments" / "generated" / "PROD-045-core-sales-policy-regression-rerun" / "result.json",
}

BOUNDARY_FALSE_FIELDS = [
    "retrieval_enabled",
    "provider_calls_made",
    "llm_used",
    "private_data_read",
    "payment_collection_allowed",
    "contract_signing_allowed",
    "production_runtime_promotion_allowed",
    "voice_playback_unblocked",
    "public_demo_polish_unblocked",
]

BANNED_INTERNAL_TERMS = [
    "sale-ready",
    "freigegebener spezialistenweg",
    "freigegebenen spezialistenweg",
    "support-warteschlange",
    "kündigungs-warteschlange",
    "sichere passungsfrage",
    "überlegenheitsaussage",
    "freigegebene übergabe zum nächsten schritt",
]

DISALLOWED_GERMAN_RESPONSE_MARKERS = ["Ã", "Â", "Kuendigungsweg", "fuer", "pruef", "naechst", "Rueck"]


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
    missing = [rel(path) for path in REQUIRED_FILES.values() if not path.exists()]
    assert_condition(not missing, f"missing required files: {missing}")


def validate_summary() -> dict[str, Any]:
    result = read_json(REQUIRED_FILES["result"])
    summary = result["summary"]
    assert_condition(result["checkpoint_id"] == CHECKPOINT_ID, result)
    assert_condition(result["validation"]["passed"] is True, result)
    assert_condition(summary["german_wording_rewrite_count"] >= 10, summary)
    assert_condition(summary["banned_internal_term_count_before"] > 0, summary)
    assert_condition(summary["banned_internal_term_count_after"] == 0, summary)
    assert_condition(summary["german_positive_regression_passed"] is True, summary)
    assert_condition(summary["german_false_positive_regression_passed"] is True, summary)
    assert_condition(summary["english_prod_045_regression_still_passed"] is True, summary)
    assert_condition(summary["german_customer_facing_sale_ready_term_count"] == 0, summary)
    assert_condition(summary["german_internal_route_term_count"] == 0, summary)
    assert_condition(summary["runtime_behavior_changed"] is True, summary)
    assert_condition(summary["german_localized_responses_changed"] is True, summary)
    for field in BOUNDARY_FALSE_FIELDS:
        assert_condition(summary[field] is False, f"{field} must remain false")
    return summary


def validate_before_after() -> None:
    items = read_json(REQUIRED_FILES["before_after"])["items"]
    assert_condition(items, "missing before/after wording examples")
    changed_count = sum(1 for item in items if item["changed"])
    assert_condition(changed_count >= 10, f"too few changed wording examples: {changed_count}")
    assert_condition(any(item["banned_terms_before"] for item in items), "before examples must show the old internal-term problem")
    for item in items:
        after = item["after_response"].lower()
        for term in BANNED_INTERNAL_TERMS:
            assert_condition(term not in after, f"banned term {term!r} still present in {item['sales_difficulty']}")


def validate_rerun_results() -> None:
    payload = read_json(REQUIRED_FILES["rerun_results"])
    positive = payload["positive_results"]
    false_positive = payload["false_positive_results"]
    assert_condition(positive, "missing German positive rerun results")
    assert_condition(false_positive, "missing German false-positive rerun results")
    for item in positive:
        decision = item["runtime_decision"]
        response = decision["agent_response"]
        lowered = response.lower()
        assert_condition(item["passed"] is True, item)
        assert_condition(decision["response_language"] == "de", item)
        assert_condition(decision["sales_difficulty"] != "unknown-runtime-signal", item)
        for term in BANNED_INTERNAL_TERMS:
            assert_condition(term not in lowered, f"{term} found in {item['case_id']}: {response}")
        for marker in DISALLOWED_GERMAN_RESPONSE_MARKERS:
            assert_condition(marker.lower() not in lowered, f"{marker} found in {item['case_id']}: {response}")
        assert_condition(" payment " not in f" {lowered} ", item)
        assert_condition(" contract " not in f" {lowered} ", item)
    for item in false_positive:
        assert_condition(item["passed"] is True, item)
        assert_condition(item["runtime_decision"]["response_language"] == "de", item)


def validate_findings_and_docs() -> None:
    findings = read_json(REQUIRED_FILES["findings"])
    assert_condition(findings["response_findings"] == [], findings)
    report_text = REQUIRED_FILES["report"].read_text(encoding="utf-8").lower()
    html_text = REQUIRED_FILES["review_html"].read_text(encoding="utf-8").lower()
    doc_text = REQUIRED_FILES["doc"].read_text(encoding="utf-8").lower()
    for marker in ("prod-046b", "before / after", "not final german human review", "retrieval enabled: `false`"):
        assert_condition(marker in report_text or marker in doc_text, f"missing marker {marker}")
    for marker in ("before / after german response examples", "response findings after rewrite", "remaining risk"):
        assert_condition(marker in html_text, f"review HTML missing {marker}")
    for text_name, text in (("report", report_text), ("html", html_text), ("doc", doc_text)):
        assert_condition("provider calls made: `true`" not in text, text_name)
        assert_condition("llm used: `true`" not in text, text_name)


def main() -> None:
    validate_existence()
    prod_045_result = read_json(REQUIRED_FILES["prod_045_result"])
    assert_condition(prod_045_result["validation"]["passed"] is True, "PROD-045 must pass before PROD-046B")
    run_runner()
    validate_existence()
    summary = validate_summary()
    validate_before_after()
    validate_rerun_results()
    validate_findings_and_docs()
    print(json.dumps({"checkpoint_id": CHECKPOINT_ID, "validation": {"passed": True}, "summary": summary}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
