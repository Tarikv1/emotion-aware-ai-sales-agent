#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-049-safe-end-call-bridge-continue-review"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID

REQUIRED_FILES = {
    "module": ROOT / "scripts" / "prod_049_safe_end_call_bridge_continue_review.py",
    "runner": ROOT / "scripts" / "run_prod_049_safe_end_call_bridge_continue_review.py",
    "validator": ROOT / "scripts" / "validate_prod_049_safe_end_call_bridge_continue_review.py",
    "doc": ROOT / "docs" / "product" / "PROD_049_SAFE_END_CALL_BRIDGE_CONTINUE_REVIEW.md",
    "result": OUT_DIR / "result.json",
    "report": OUT_DIR / "report.md",
    "candidate_matrix": OUT_DIR / "bridge_continue_candidate_matrix.json",
    "boundary_results": OUT_DIR / "protected_boundary_results.json",
    "review_packet": OUT_DIR / "safe_end_call_review_packet.json",
    "review_html": OUT_DIR / "prod_049_review.html",
}

SOURCE_RESULTS = {
    "prod_048c": ROOT / "research" / "experiments" / "generated" / "PROD-048C-german-wording-feedback-patch" / "result.json",
    "prod_047": ROOT / "research" / "experiments" / "generated" / "PROD-047-campaign-profile-contract-validator" / "result.json",
    "prod_046": ROOT / "research" / "experiments" / "generated" / "PROD-046-core-sales-policy-human-review" / "result.json",
    "prod_045": ROOT / "research" / "experiments" / "generated" / "PROD-045-core-sales-policy-regression-rerun" / "result.json",
}

SOURCE_CALL_CONTROL_FINDINGS = (
    ROOT
    / "research"
    / "experiments"
    / "generated"
    / "PROD-046-core-sales-policy-human-review"
    / "call_control_findings.json"
)

BRIDGE_CANDIDATE_DIFFICULTIES = {
    "price-first-direct",
    "written-info-request",
    "stakeholder-review",
    "partner-review",
}

PROTECTED_DIFFICULTIES = {
    "email-only-boundary",
    "scam-safety-boundary",
    "payment-safety-boundary",
    "sale-ready-commitment",
    "callback-request",
}

BOUNDARY_FALSE_FIELDS = [
    "runtime_behavior_changed",
    "call_control_behavior_changed",
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

FORBIDDEN_PRESSURE_MARKERS = [
    "payment now",
    "pay now",
    "card number",
    "sign now",
    "contract today",
    "must decide",
    "only available today",
    "ignore your cancellation",
    "keep selling",
]

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


def validate_required_files() -> None:
    missing = [rel(path) for path in [*REQUIRED_FILES.values(), *SOURCE_RESULTS.values(), SOURCE_CALL_CONTROL_FINDINGS] if not path.exists()]
    assert_condition(not missing, f"missing required files: {missing}")


def validate_sources() -> None:
    for key, path in SOURCE_RESULTS.items():
        result = read_json(path)
        assert_condition(result.get("validation", {}).get("passed") is True, f"{key} must pass")
    source_findings = read_json(SOURCE_CALL_CONTROL_FINDINGS)["items"]
    assert_condition(len(source_findings) == 45, f"expected 45 source call-control findings, found {len(source_findings)}")


def validate_result() -> dict[str, Any]:
    result = read_json(REQUIRED_FILES["result"])
    summary = result["summary"]
    assert_condition(result["checkpoint_id"] == CHECKPOINT_ID, result)
    assert_condition(result["validation"]["passed"] is True, result)
    assert_condition(summary["source_call_control_finding_count"] == 45, summary)
    assert_condition(summary["bridge_then_continue_candidate_count"] == 22, summary)
    assert_condition(summary["protected_end_or_escalation_count"] == 23, summary)
    assert_condition(summary["candidate_language_counts"] == {"en": 4, "de": 18}, summary)
    assert_condition(summary["protected_boundary_probe_count"] >= 8, summary)
    assert_condition(summary["protected_boundary_pass_count"] == summary["protected_boundary_probe_count"], summary)
    assert_condition(summary["support_cancellation_do_not_call_softened"] is False, summary)
    assert_condition(summary["email_only_softened"] is False, summary)
    assert_condition(summary["payment_or_scam_softened"] is False, summary)
    assert_condition(summary["sale_ready_softened"] is False, summary)
    assert_condition(summary["recommended_next_checkpoint"] == "PROD-050-safe-call-control-softening-regression", summary)
    for field in BOUNDARY_FALSE_FIELDS:
        assert_condition(summary[field] is False, f"{field} must remain false")
    return result


def validate_candidate_matrix() -> None:
    payload = read_json(REQUIRED_FILES["candidate_matrix"])
    items = payload["items"]
    assert_condition(len(items) == 45, len(items))
    candidate_items = [item for item in items if item["bridge_then_continue_candidate"] is True]
    protected_items = [item for item in items if item["bridge_then_continue_candidate"] is False]
    assert_condition(len(candidate_items) == 22, len(candidate_items))
    assert_condition(len(protected_items) == 23, len(protected_items))
    assert_condition({item["sales_difficulty"] for item in candidate_items}.issubset(BRIDGE_CANDIDATE_DIFFICULTIES), candidate_items)
    assert_condition({item["sales_difficulty"] for item in protected_items}.issubset(PROTECTED_DIFFICULTIES), protected_items)
    for item in candidate_items:
        assert_condition(item["current_call_control"] in {"end-call"}, item)
        assert_condition(item["candidate_call_control"] == "bridge-then-continue", item)
        assert_condition(item["runtime_change_applied"] is False, item)
        assert_condition(item["requires_future_regression"] is True, item)
        assert_condition(item["guardrail_preserved"] is True, item)
    for item in protected_items:
        assert_condition(item["candidate_call_control"] == item["current_call_control"], item)
        assert_condition(item["exclusion_reason"], item)
        assert_condition(item["runtime_change_applied"] is False, item)


def validate_protected_boundaries() -> None:
    payload = read_json(REQUIRED_FILES["boundary_results"])
    items = payload["items"]
    assert_condition(len(items) >= 8, items)
    by_case = {item["case_id"]: item for item in items}
    expected_controls = {
        "prod-049-support-boundary": "transfer-or-escalate",
        "prod-049-cancellation-boundary": "transfer-or-escalate",
        "prod-049-do-not-call-boundary": "end-call",
        "prod-049-human-request-boundary": "transfer-or-escalate",
        "prod-049-email-only-boundary": "end-call",
        "prod-049-payment-safety-boundary": "end-call",
        "prod-049-scam-safety-boundary": "end-call",
        "prod-049-sale-ready-boundary": "close-and-log-sale-ready",
    }
    for case_id, expected_call_control in expected_controls.items():
        item = by_case[case_id]
        decision = item["runtime_decision"]
        assert_condition(item["passed"] is True, item)
        assert_condition(decision["call_control"] == expected_call_control, item)
        assert_condition(decision["call_control"] != "bridge-then-continue", item)
        response = decision.get("agent_response", "").lower()
        for marker in FORBIDDEN_PRESSURE_MARKERS:
            assert_condition(marker not in response, f"{case_id} contains pressure marker {marker}")


def validate_review_packet_and_docs() -> None:
    packet = read_json(REQUIRED_FILES["review_packet"])
    assert_condition(packet["checkpoint_id"] == CHECKPOINT_ID, packet)
    assert_condition(packet["decision"]["selected_non_refusal_cases_should_be_tested_as_bridge_then_continue"] is True, packet)
    assert_condition(packet["decision"]["runtime_change_applied"] is False, packet)
    assert_condition(packet["decision"]["do_not_change_support_cancellation_or_refusal_boundaries"] is True, packet)
    assert_condition(packet["decision"]["requires_future_regression_checkpoint_before_runtime_change"] is True, packet)

    doc = REQUIRED_FILES["doc"].read_text(encoding="utf-8")
    report = REQUIRED_FILES["report"].read_text(encoding="utf-8")
    html = REQUIRED_FILES["review_html"].read_text(encoding="utf-8")
    for text in (doc, report, html):
        lowered = text.lower()
        assert_condition("prod-049" in lowered, text[:300])
        assert_condition("bridge-then-continue" in lowered, text[:300])
        assert_condition("runtime behavior changed" in lowered, text[:300])
        assert_condition("provider calls made" in lowered, text[:300])
        assert_condition("production runtime promotion allowed" in lowered, text[:300])
        assert_condition(not PHONE_PATTERN.search(text), "phone-like string found")
        assert_condition(not EMAIL_PATTERN.search(text), "email-like string found")


def main() -> None:
    validate_required_files()
    validate_sources()
    run_runner()
    validate_required_files()
    result = validate_result()
    validate_candidate_matrix()
    validate_protected_boundaries()
    validate_review_packet_and_docs()
    print(json.dumps({"checkpoint_id": CHECKPOINT_ID, "validation": {"passed": True}, "summary": result["summary"]}, indent=2))


if __name__ == "__main__":
    main()
