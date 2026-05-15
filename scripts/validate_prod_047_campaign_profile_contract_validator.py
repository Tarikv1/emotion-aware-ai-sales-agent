#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from campaign_profile_contract import (
    BOUNDARY_FALSE_FIELDS,
    CHECKPOINT_ID,
    REQUIRED_POLICY_GROUPS,
    validate_campaign_profile,
)


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
EXAMPLE_DIR = ROOT / "runtime" / "campaigns" / "examples"

REQUIRED_FILES = {
    "module": ROOT / "scripts" / "campaign_profile_contract.py",
    "runtime_module": ROOT / "runtime" / "contracts" / "campaign_profile_contract.py",
    "runner": ROOT / "scripts" / "run_prod_047_campaign_profile_contract_validator.py",
    "validator": ROOT / "scripts" / "validate_prod_047_campaign_profile_contract_validator.py",
    "doc": ROOT / "docs" / "product" / "PROD_047_CAMPAIGN_PROFILE_CONTRACT_VALIDATOR.md",
    "valid_en": EXAMPLE_DIR / "campaign-prod-047-valid-en-internal-review.json",
    "valid_de": EXAMPLE_DIR / "campaign-prod-047-valid-de-source-informed.json",
    "invalid_de_fragment": EXAMPLE_DIR / "campaign-prod-047-invalid-de-fragment-interpolation.json",
    "invalid_en_internal": EXAMPLE_DIR / "campaign-prod-047-invalid-en-internal-copy.json",
    "invalid_payment": EXAMPLE_DIR / "campaign-prod-047-invalid-payment-enabled.json",
    "invalid_regulated": EXAMPLE_DIR / "campaign-prod-047-invalid-missing-regulated-boundary.json",
    "invalid_native": EXAMPLE_DIR / "campaign-prod-047-invalid-missing-native-review-status.json",
    "invalid_sale_ready": EXAMPLE_DIR / "campaign-prod-047-invalid-sale-ready-without-close-criteria.json",
    "invalid_routes": EXAMPLE_DIR / "campaign-prod-047-invalid-support-cancellation-route-label.json",
    "invalid_identity": EXAMPLE_DIR / "campaign-prod-047-incomplete-identity-reason.json",
    "result": OUT_DIR / "result.json",
    "report": OUT_DIR / "report.md",
    "schema": OUT_DIR / "campaign_contract_schema.json",
    "matrix": OUT_DIR / "campaign_guard_matrix.json",
    "cases": OUT_DIR / "validation_cases.json",
    "results": OUT_DIR / "validation_results.json",
    "review_html": OUT_DIR / "campaign_profile_review.html",
}

SOURCE_VALIDATORS = [
    ROOT / "scripts" / "validate_prod_045_core_sales_policy_regression_rerun.py",
    ROOT / "scripts" / "validate_prod_046a_german_naturalized_policy_regression.py",
    ROOT / "scripts" / "validate_prod_046b_german_response_wording_quality_pass.py",
    ROOT / "scripts" / "validate_prod_046c_german_campaign_field_interpolation_guard.py",
    ROOT / "scripts" / "validate_prod_046d_german_source_informed_wording_quality_guard.py",
    ROOT / "scripts" / "validate_prod_046_core_sales_policy_human_review.py",
]


def assert_condition(condition: bool, message: Any) -> None:
    if not condition:
        raise AssertionError(message)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def validate_required_files() -> None:
    missing = [rel(path) for path in REQUIRED_FILES.values() if not path.exists()]
    assert_condition(not missing, f"missing required files: {missing}")
    missing_validators = [rel(path) for path in SOURCE_VALIDATORS if not path.exists()]
    assert_condition(not missing_validators, f"missing source validators: {missing_validators}")


def validate_result_summary() -> dict[str, Any]:
    result = read_json(REQUIRED_FILES["result"])
    summary = result["summary"]
    assert_condition(result["checkpoint_id"] == CHECKPOINT_ID, result)
    assert_condition(result["validation"]["passed"] is True, result)
    assert_condition(result["next_checkpoint_recommended"] == "PROD-048-native-german-wording-review", result)
    assert_condition(summary["validation_case_count"] >= 10, summary)
    assert_condition(summary["valid_campaign_count"] == 2, summary)
    assert_condition(summary["invalid_campaign_count"] >= 8, summary)
    assert_condition(summary["unexpected_result_count"] == 0, summary)
    assert_condition(summary["policy_group_coverage_count"] == len(REQUIRED_POLICY_GROUPS), summary)
    assert_condition(summary["runtime_behavior_changed"] is False, summary)
    for field in BOUNDARY_FALSE_FIELDS:
        assert_condition(summary[field] is False, f"{field} must be false")
    return summary


def validate_cases_and_results() -> None:
    cases = read_json(REQUIRED_FILES["cases"])["items"]
    results = read_json(REQUIRED_FILES["results"])["items"]
    assert_condition(len(cases) == len(results), "case/result count mismatch")
    by_case = {item["case_id"]: item for item in results}
    required_case_ids = {
        "valid-en-internal-review",
        "valid-de-source-informed",
        "invalid-de-fragment-interpolation",
        "invalid-en-internal-copy",
        "invalid-payment-enabled",
        "invalid-missing-regulated-boundary",
        "invalid-missing-native-review-status",
        "invalid-sale-ready-without-close-criteria",
        "invalid-support-cancellation-route-label",
        "incomplete-identity-reason",
    }
    assert_condition(required_case_ids <= set(by_case), by_case.keys())
    assert_condition(by_case["valid-en-internal-review"]["passed_expected"] is True, by_case["valid-en-internal-review"])
    assert_condition(by_case["valid-en-internal-review"]["validation"]["is_valid"] is True, by_case["valid-en-internal-review"])
    assert_condition(by_case["valid-en-internal-review"]["validation"]["readiness"]["valid_for_internal_product_review"] is True, by_case["valid-en-internal-review"])
    assert_condition(by_case["valid-en-internal-review"]["validation"]["readiness"]["blocked_for_voice"] is True, by_case["valid-en-internal-review"])
    assert_condition(by_case["valid-de-source-informed"]["validation"]["is_valid"] is True, by_case["valid-de-source-informed"])
    assert_condition(by_case["valid-de-source-informed"]["validation"]["readiness"]["valid_for_internal_product_review"] is True, by_case["valid-de-source-informed"])
    assert_condition(by_case["valid-de-source-informed"]["validation"]["readiness"]["blocked_for_voice"] is True, by_case["valid-de-source-informed"])
    for case_id in required_case_ids - {"valid-en-internal-review", "valid-de-source-informed"}:
        assert_condition(by_case[case_id]["validation"]["is_valid"] is False, by_case[case_id])
        assert_condition(by_case[case_id]["passed_expected"] is True, by_case[case_id])
    assert_condition(by_case["invalid-payment-enabled"]["validation"]["safety_boundary_errors"], "payment-enabled must fail safety")
    assert_condition(by_case["invalid-de-fragment-interpolation"]["validation"]["language_shape_errors"], "German fragment interpolation must fail shape/language")
    assert_condition(by_case["invalid-en-internal-copy"]["validation"]["internal_customer_facing_terms"], "English internal copy must be detected")
    assert_condition(by_case["invalid-missing-regulated-boundary"]["validation"]["missing_fields"], "regulated boundary missing field must be detected")
    assert_condition(by_case["invalid-missing-native-review-status"]["validation"]["review_status_errors"], "German native review status error required")
    assert_condition(by_case["invalid-sale-ready-without-close-criteria"]["validation"]["safety_boundary_errors"], "sale-ready close criteria error required")


def validate_matrix_and_schema() -> None:
    matrix = read_json(REQUIRED_FILES["matrix"])
    schema = read_json(REQUIRED_FILES["schema"])
    assert_condition(set(matrix["policy_groups"].keys()) == set(REQUIRED_POLICY_GROUPS), matrix)
    for group, config in matrix["policy_groups"].items():
        assert_condition(config["required_field_ids"], f"{group} missing required field ids")
        assert_condition(config["blocked_until_contract_validated"] is True, config)
    assert_condition(set(schema["allowed_languages"]) == {"en", "de"}, schema)
    for key in ("allowed_field_shapes", "allowed_source_boundaries", "allowed_review_statuses", "required_safety_defaults"):
        assert_condition(schema[key], f"schema missing {key}")


def validate_direct_contract_reuse() -> None:
    valid_en = read_json(REQUIRED_FILES["valid_en"])
    invalid_payment = read_json(REQUIRED_FILES["invalid_payment"])
    assert_condition(validate_campaign_profile(valid_en)["is_valid"] is True, "valid EN profile must pass reusable validator")
    assert_condition(validate_campaign_profile(invalid_payment)["is_valid"] is False, "payment-enabled profile must fail reusable validator")


def validate_docs() -> None:
    doc = REQUIRED_FILES["doc"].read_text(encoding="utf-8").lower()
    report = REQUIRED_FILES["report"].read_text(encoding="utf-8").lower()
    html = REQUIRED_FILES["review_html"].read_text(encoding="utf-8").lower()
    roadmap = (ROOT / "docs" / "thesis" / "ROADMAP.md").read_text(encoding="utf-8").lower()
    commands = (ROOT / "docs" / "product" / "COMMANDS.md").read_text(encoding="utf-8").lower()
    index = (ROOT / "docs" / "product" / "CHECKPOINT_INDEX.md").read_text(encoding="utf-8").lower()
    methodology = (ROOT / "docs" / "thesis" / "METHODOLOGY_LOG.md").read_text(encoding="utf-8").lower()
    decision = (ROOT / "docs" / "thesis" / "DECISION_LOG.md").read_text(encoding="utf-8").lower()
    for text in (doc, report, html):
        assert_condition("campaign-profile contract" in text, "missing campaign contract language")
        assert_condition("blocked_for_voice" in text or "blocked for voice" in text, "missing voice block")
        assert_condition("payment_collection_allowed" in text or "payment collection" in text, "missing payment boundary")
    assert_condition("prod-047-campaign-profile-contract-validator" in roadmap, "roadmap missing PROD-047")
    assert_condition("run_prod_047_campaign_profile_contract_validator" in commands, "commands missing PROD-047")
    assert_condition("prod_047_campaign_profile_contract_validator" in index, "index missing PROD-047")
    assert_condition("prod-047" in methodology and "campaign-profile contract" in methodology, "methodology missing PROD-047")
    assert_condition("campaign-profile contract" in decision and "voice/demo/customer" in decision, "decision log missing PROD-047 decision")


def main() -> None:
    validate_required_files()
    summary = validate_result_summary()
    validate_cases_and_results()
    validate_matrix_and_schema()
    validate_direct_contract_reuse()
    validate_docs()
    print(json.dumps({"checkpoint_id": CHECKPOINT_ID, "validation": {"passed": True}, "summary": summary}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
