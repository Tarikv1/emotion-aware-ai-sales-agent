#!/usr/bin/env python3
from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

from campaign_profile_contract import (
    CHECKPOINT_ID,
    CHECKPOINT_NAME,
    NEXT_CHECKPOINT_ID,
    REQUIRED_POLICY_GROUPS,
    ROOT,
    guard_matrix_payload,
    read_json,
    schema_payload,
    validate_campaign_profile,
    validation_cases,
    write_example_profiles,
    write_json,
)


OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
PROD_046_RESULT = ROOT / "research" / "experiments" / "generated" / "PROD-046-core-sales-policy-human-review" / "result.json"


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def render_html(review_data: dict[str, Any]) -> str:
    rows = []
    for item in review_data["validation_results"]:
        validation = item["validation"]
        rows.append(
            "<tr>"
            f"<td>{html.escape(item['case_id'])}</td>"
            f"<td>{html.escape(validation['campaign_id'])}</td>"
            f"<td>{html.escape(str(validation['language']))}</td>"
            f"<td>{validation['is_valid']}</td>"
            f"<td>{item['passed_expected']}</td>"
            f"<td>{len(validation['missing_fields'])}</td>"
            f"<td>{len(validation['internal_customer_facing_terms'])}</td>"
            f"<td>{len(validation['language_shape_errors'])}</td>"
            f"<td>{len(validation['safety_boundary_errors'])}</td>"
            f"<td>{html.escape('; '.join(validation['recommended_fix']))}</td>"
            "</tr>"
        )
    summary = review_data["summary"]
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>PROD-047 Campaign Profile Contract Validator</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 24px; color: #202124; }}
    .summary {{ border: 1px solid #d7dce2; border-radius: 8px; padding: 14px; margin-bottom: 16px; }}
    table {{ border-collapse: collapse; width: 100%; margin: 12px 0 24px; }}
    th, td {{ border: 1px solid #d7dce2; padding: 8px; text-align: left; vertical-align: top; }}
    code {{ background: #f4f6f8; padding: 2px 4px; }}
  </style>
</head>
<body>
  <h1>PROD-047 Campaign Profile Contract Validator</h1>
  <section class="summary">
    <h2>Summary</h2>
    <p>This campaign-profile contract keeps campaign fields blocked from promotion until their shape, source boundary, review status, and safety defaults are valid.</p>
    <p>Validation cases: <code>{summary['validation_case_count']}</code></p>
    <p>Valid campaigns: <code>{summary['valid_campaign_count']}</code></p>
    <p>Invalid campaigns: <code>{summary['invalid_campaign_count']}</code></p>
    <p>Policy group coverage: <code>{summary['policy_group_coverage_count']}</code></p>
    <p>Default readiness: <code>blocked_for_voice</code>, <code>blocked_for_public_demo</code>, and <code>blocked_for_customer_use</code> until explicit review statuses are present.</p>
    <p>Runtime behavior changed: <code>false</code></p>
  </section>
  <h2>Validation Results</h2>
  <table><tr><th>Case</th><th>Campaign</th><th>Language</th><th>Valid</th><th>Expected</th><th>Missing</th><th>Internal terms</th><th>Shape errors</th><th>Safety errors</th><th>Recommended fix</th></tr>{''.join(rows)}</table>
  <h2>Boundaries</h2>
  <p>Retrieval, providers, LLMs, private-data reads, voice playback, public demo polish, payment collection, contract signing, and production promotion remain blocked.</p>
</body>
</html>
"""


def build_report(summary: dict[str, Any], results: list[dict[str, Any]]) -> str:
    lines = [
        "# PROD-047 Campaign Profile Contract Validator",
        "",
        "PROD-047 creates a reusable deterministic campaign-profile contract and validator. It does not modify runtime behavior.",
        "",
        "## Results",
        "",
        f"- Validation cases: {summary['validation_case_count']}",
        f"- Valid campaigns: {summary['valid_campaign_count']}",
        f"- Invalid campaigns: {summary['invalid_campaign_count']}",
        f"- Unexpected results: {summary['unexpected_result_count']}",
        f"- Policy group coverage: {summary['policy_group_coverage_count']} / {len(REQUIRED_POLICY_GROUPS)}",
        f"- PROD-046 source result passed: `{summary['prod_046_result_validation_passed']}`",
        "",
        "## Validator Behavior",
        "",
        "- Valid English and German campaigns pass only for offline regression/internal product review by default.",
        "- Readiness defaults remain `blocked_for_voice`, `blocked_for_public_demo`, and `blocked_for_customer_use` unless explicit review statuses are present.",
        "- German voice/demo/customer promotion remains blocked unless native review and explicit promotion statuses are present.",
        "- Internal customer-facing terms, malformed German interpolation, unsafe payment/contract flags, missing regulated boundaries, missing native review status, and missing close criteria fail deterministically.",
        "",
        "## Campaign Examples",
        "",
    ]
    for item in results:
        validation = item["validation"]
        lines.append(f"- `{validation['campaign_id']}`: valid=`{validation['is_valid']}`, expected=`{item['expected_valid']}`")
    lines.extend(
        [
            "",
            "## Boundaries",
            "",
            "- Runtime behavior changed: `false`",
            "- Retrieval enabled: `false`",
            "- Provider calls made: `false`",
            "- LLM used: `false`",
            "- Private data read: `false`",
            "- Voice playback unblocked: `false`",
            "- Public demo polish unblocked: `false`",
            "- Payment collection allowed: `false`",
            "- Contract signing allowed: `false`",
            "- Production runtime promotion allowed: `false`",
            "",
            f"Next recommended checkpoint: `{NEXT_CHECKPOINT_ID}`.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    if not PROD_046_RESULT.exists():
        raise SystemExit(f"Missing source result: {rel(PROD_046_RESULT)}")

    example_paths = write_example_profiles()
    cases = validation_cases(example_paths)
    results = []
    for case in cases:
        profile = read_json(ROOT / case["path"])
        validation = validate_campaign_profile(profile)
        results.append(
            {
                **case,
                "validation": validation,
                "passed_expected": validation["is_valid"] is case["expected_valid"],
            }
        )

    prod_046_passed = read_json(PROD_046_RESULT).get("validation", {}).get("passed") is True
    unexpected = [item for item in results if not item["passed_expected"]]
    summary = {
        "source_checkpoint_id": "PROD-046-core-sales-policy-human-review",
        "prod_046_result_validation_passed": prod_046_passed,
        "validation_case_count": len(results),
        "valid_campaign_count": sum(1 for item in results if item["validation"]["is_valid"]),
        "invalid_campaign_count": sum(1 for item in results if not item["validation"]["is_valid"]),
        "unexpected_result_count": len(unexpected),
        "policy_group_coverage_count": len(REQUIRED_POLICY_GROUPS),
        "valid_en_internal_review_passed": next(item for item in results if item["case_id"] == "valid-en-internal-review")["validation"]["is_valid"],
        "valid_de_source_informed_passed": next(item for item in results if item["case_id"] == "valid-de-source-informed")["validation"]["is_valid"],
        "invalid_de_fragment_interpolation_failed": not next(item for item in results if item["case_id"] == "invalid-de-fragment-interpolation")["validation"]["is_valid"],
        "invalid_en_internal_copy_failed": not next(item for item in results if item["case_id"] == "invalid-en-internal-copy")["validation"]["is_valid"],
        "payment_enabled_campaign_failed": not next(item for item in results if item["case_id"] == "invalid-payment-enabled")["validation"]["is_valid"],
        "missing_regulated_boundary_campaign_failed": not next(item for item in results if item["case_id"] == "invalid-missing-regulated-boundary")["validation"]["is_valid"],
        "missing_native_review_status_campaign_failed": not next(item for item in results if item["case_id"] == "invalid-missing-native-review-status")["validation"]["is_valid"],
        "sale_ready_without_close_criteria_failed": not next(item for item in results if item["case_id"] == "invalid-sale-ready-without-close-criteria")["validation"]["is_valid"],
        "support_cancellation_route_label_campaign_failed": not next(item for item in results if item["case_id"] == "invalid-support-cancellation-route-label")["validation"]["is_valid"],
        "incomplete_identity_reason_campaign_failed": not next(item for item in results if item["case_id"] == "incomplete-identity-reason")["validation"]["is_valid"],
        "runtime_behavior_changed": False,
        "retrieval_enabled": False,
        "provider_calls_made": False,
        "llm_used": False,
        "private_data_read": False,
        "voice_playback_unblocked": False,
        "public_demo_polish_unblocked": False,
        "payment_collection_allowed": False,
        "contract_signing_allowed": False,
        "production_runtime_promotion_allowed": False,
    }
    passed = prod_046_passed and not unexpected and summary["valid_campaign_count"] == 2 and summary["invalid_campaign_count"] >= 8

    review_data = {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "summary": summary,
        "schema": schema_payload(),
        "guard_matrix": guard_matrix_payload(),
        "validation_cases": cases,
        "validation_results": results,
    }
    result = {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "summary": summary,
        "outputs": {
            "report": rel(OUT_DIR / "report.md"),
            "campaign_contract_schema": rel(OUT_DIR / "campaign_contract_schema.json"),
            "campaign_guard_matrix": rel(OUT_DIR / "campaign_guard_matrix.json"),
            "validation_cases": rel(OUT_DIR / "validation_cases.json"),
            "validation_results": rel(OUT_DIR / "validation_results.json"),
            "campaign_profile_review": rel(OUT_DIR / "campaign_profile_review.html"),
        },
        "validation": {"passed": passed},
        "next_checkpoint_recommended": NEXT_CHECKPOINT_ID,
    }

    write_json(OUT_DIR / "campaign_contract_schema.json", schema_payload())
    write_json(OUT_DIR / "campaign_guard_matrix.json", guard_matrix_payload())
    write_json(OUT_DIR / "validation_cases.json", {"items": cases})
    write_json(OUT_DIR / "validation_results.json", {"items": results})
    write_json(OUT_DIR / "result.json", result)
    write_json(OUT_DIR / "prod_047_review_data.json", review_data)
    (OUT_DIR / "report.md").write_text(build_report(summary, results), encoding="utf-8")
    (OUT_DIR / "campaign_profile_review.html").write_text(render_html(review_data), encoding="utf-8")

    print(json.dumps({"checkpoint_id": CHECKPOINT_ID, "validation": {"passed": passed}, "summary": summary}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
