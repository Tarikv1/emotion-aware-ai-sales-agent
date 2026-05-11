#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-046C-german-campaign-field-interpolation-guard"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID

REQUIRED_FILES = {
    "module": ROOT / "scripts" / "prod_046c_german_campaign_field_interpolation_guard.py",
    "runner": ROOT / "scripts" / "run_prod_046c_german_campaign_field_interpolation_guard.py",
    "validator": ROOT / "scripts" / "validate_prod_046c_german_campaign_field_interpolation_guard.py",
    "doc": ROOT / "docs" / "product" / "PROD_046C_GERMAN_CAMPAIGN_FIELD_INTERPOLATION_GUARD.md",
    "result": OUT_DIR / "result.json",
    "report": OUT_DIR / "report.md",
    "cases": OUT_DIR / "german_interpolation_cases.json",
    "results": OUT_DIR / "german_interpolation_results.json",
    "before_after": OUT_DIR / "german_interpolation_before_after.json",
    "review_data": OUT_DIR / "german_interpolation_review_data.json",
    "review_html": OUT_DIR / "german_interpolation_review.html",
    "prod_045_result": ROOT / "research" / "experiments" / "generated" / "PROD-045-core-sales-policy-regression-rerun" / "result.json",
    "prod_046a_result": ROOT / "research" / "experiments" / "generated" / "PROD-046A-german-naturalized-policy-regression" / "result.json",
    "prod_046b_result": ROOT / "research" / "experiments" / "generated" / "PROD-046B-german-response-wording-quality-pass" / "result.json",
}

BOUNDARY_FALSE_FIELDS = [
    "retrieval_enabled",
    "provider_calls_made",
    "llm_used",
    "private_data_read",
    "voice_playback_unblocked",
    "public_demo_polish_unblocked",
    "payment_collection_allowed",
    "contract_signing_allowed",
    "production_runtime_promotion_allowed",
]

MALFORMED_GERMAN_MARKERS = [
    "bei beim",
    "bei bei",
    "um ein kurzer",
    "um ein Abgleich",
    "um der Grund",
    "Support-Warteschlange",
    "Kündigungs-Warteschlange",
    "freigegebener Spezialistenweg",
    "freigegebenen Spezialistenweg",
    "sichere Passungsfrage",
    "Überlegenheitsaussage",
    "sale-ready",
    "freigegebene Übergabe",
]

ENGLISH_OPERATIONAL_MARKERS = [
    "support queue",
    "specialist route",
    "approved specialist path",
    "payment details",
    "contract signing",
    "unknown-runtime-signal",
]

UTF8_GERMAN_MARKERS = ["Ã", "Kuendigungsweg", "fuer", "Rueckruf", "naechst", "pruef"]


def assert_condition(condition: bool, message: Any) -> None:
    if not condition:
        raise AssertionError(message)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def contains_marker(text: str, markers: list[str]) -> list[str]:
    lowered = text.lower()
    return [marker for marker in markers if marker.lower() in lowered]


def has_duplicate_specialist_phrase(text: str) -> bool:
    return any(sentence.lower().count("zuständige fachperson") > 1 for sentence in re.split(r"[.!?]", text))


def validate_required_files() -> None:
    missing = [rel(path) for path in REQUIRED_FILES.values() if not path.exists()]
    assert_condition(not missing, f"missing required files: {missing}")


def validate_source_results() -> None:
    for key in ("prod_045_result", "prod_046a_result", "prod_046b_result"):
        result = read_json(REQUIRED_FILES[key])
        assert_condition(result.get("validation", {}).get("passed") is True, f"{key} must pass")


def validate_summary() -> dict[str, Any]:
    result = read_json(REQUIRED_FILES["result"])
    summary = result["summary"]
    assert_condition(result["checkpoint_id"] == CHECKPOINT_ID, result)
    assert_condition(result["validation"]["passed"] is True, result)
    assert_condition(summary["english_prod_045_regression_still_passed"] is True, summary)
    assert_condition(summary["german_prod_046a_regression_still_passed"] is True, summary)
    assert_condition(summary["german_prod_046b_wording_regression_still_passed"] is True, summary)
    assert_condition(summary["malformed_german_response_count"] == 0, summary)
    assert_condition(summary["duplicate_specialist_phrase_count"] == 0, summary)
    assert_condition(summary["response_language_mismatch_count"] == 0, summary)
    assert_condition(summary["german_positive_unknown_runtime_signal_count"] == 0, summary)
    assert_condition(summary["german_positive_generic_clarification_count"] == 0, summary)
    assert_condition("german_false_positive_unknown_runtime_signal_count" in summary, summary)
    assert_condition("german_false_positive_generic_clarification_count" in summary, summary)
    for field in BOUNDARY_FALSE_FIELDS:
        assert_condition(summary[field] is False, f"{field} must remain false")
    return summary


def validate_cases_and_results() -> None:
    cases = read_json(REQUIRED_FILES["cases"])["items"]
    results = read_json(REQUIRED_FILES["results"])["items"]
    assert_condition(cases, "missing interpolation cases")
    assert_condition(results, "missing interpolation results")
    assert_condition(len(cases) == len(results), "case/result count mismatch")
    assert_condition(any(case["case_id"].startswith("interp-legacy-") for case in cases), "legacy fragment guard cases missing")
    for item in results:
        decision = item["runtime_decision"]
        response = decision["agent_response"]
        assert_condition(item["passed"] is True, item)
        assert_condition(decision["response_language"] == "de", item)
        malformed = contains_marker(response, MALFORMED_GERMAN_MARKERS)
        assert_condition(not malformed, f"malformed German markers {malformed} in {item['case_id']}: {response}")
        english_hits = contains_marker(response, ENGLISH_OPERATIONAL_MARKERS)
        assert_condition(not english_hits, f"English operational markers {english_hits} in {item['case_id']}: {response}")
        utf8_hits = contains_marker(response, UTF8_GERMAN_MARKERS)
        assert_condition(not utf8_hits, f"UTF-8/ascii German markers {utf8_hits} in {item['case_id']}: {response}")
        assert_condition(not has_duplicate_specialist_phrase(response), f"duplicate zuständige Fachperson in {item['case_id']}: {response}")


def validate_review_outputs() -> None:
    review = read_json(REQUIRED_FILES["review_data"])
    before_after = read_json(REQUIRED_FILES["before_after"])["items"]
    assert_condition(review["checkpoint_id"] == CHECKPOINT_ID, review)
    assert_condition(review["response_findings"] == [], review["response_findings"])
    assert_condition(before_after, "missing before/after interpolation evidence")
    assert_condition(any(item["prod_046b_malformed_hits"] for item in before_after), "PROD-046B malformed baseline evidence missing")
    assert_condition(all(not item["prod_046c_malformed_hits"] for item in before_after), before_after)
    html = REQUIRED_FILES["review_html"].read_text(encoding="utf-8").lower()
    report = REQUIRED_FILES["report"].read_text(encoding="utf-8").lower()
    doc = REQUIRED_FILES["doc"].read_text(encoding="utf-8").lower()
    for marker in ("prod-046c", "interpolation", "malformed german response count"):
        assert_condition(marker in html or marker in report or marker in doc, f"missing {marker}")
    for text_name, text in (("html", html), ("report", report), ("doc", doc)):
        assert_condition("retrieval enabled: `true`" not in text, text_name)
        assert_condition("provider calls made: `true`" not in text, text_name)
        assert_condition("llm used: `true`" not in text, text_name)


def main() -> None:
    validate_required_files()
    validate_source_results()
    summary = validate_summary()
    validate_cases_and_results()
    validate_review_outputs()
    print(json.dumps({"checkpoint_id": CHECKPOINT_ID, "validation": {"passed": True}, "summary": summary}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
