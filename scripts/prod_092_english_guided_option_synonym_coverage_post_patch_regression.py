#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.core.realtime_turns import build_runtime_decision  # noqa: E402
from prod_087_english_guided_option_selection_runtime_patch import (  # noqa: E402
    CONTROL_CASES as PROD_087_CONTROL_CASES,
    POSITIVE_CASES as PROD_087_POSITIVE_CASES,
    TEST_CAMPAIGN,
    runtime_case,
    word_count,
)
from prod_090_english_guided_option_synonym_coverage_narrow_probe import (  # noqa: E402
    CONTROL_CASES as PROD_090_CONTROL_CASES,
    POSITIVE_CASES as PROD_090_POSITIVE_CASES,
)
from prod_091_english_guided_option_synonym_coverage_runtime_patch import CONTROL_EXPECTED_DIFFICULTY  # noqa: E402


CHECKPOINT_ID = "PROD-092-english-guided-option-synonym-coverage-post-patch-regression"
CHECKPOINT_NAME = "English Guided Option Synonym Coverage Post-Patch Regression"
SOURCE_CHECKPOINT_ID = "PROD-091-english-guided-option-synonym-coverage-runtime-patch"
NEXT_CHECKPOINT_ID = "PROD-093-english-customer-move-remaining-slice-selection-after-guided-option-synonyms"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
SOURCE_DIR = ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID
SOURCE_VALIDATOR = ROOT / "scripts" / "validate_prod_091_english_guided_option_synonym_coverage_runtime_patch.py"
ENGLISH_GUARD = ROOT / "scripts" / "validate_english_multi_turn_regression_guard.py"

BOUNDARY_FLAGS = {
    "runtime_behavior_changed": False,
    "response_text_behavior_changed": False,
    "classifier_behavior_changed": False,
    "retrieval_enabled": False,
    "provider_calls_made": False,
    "llm_used": False,
    "llm_judging_used": False,
    "private_data_read": False,
    "voice_playback_unblocked": False,
    "public_demo_polish_unblocked": False,
    "real_customer_use_unblocked": False,
    "payment_collection_allowed": False,
    "contract_signing_allowed": False,
    "production_runtime_promotion_allowed": False,
    "german_exact_phrase_promotion_allowed": False,
    "german_naturalness_claimed": False,
    "legal_compliance_claimed": False,
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def run_validator(path: Path) -> dict[str, Any]:
    completed = subprocess.run(
        [sys.executable, str(path)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=360,
        check=False,
    )
    return {
        "command": f"python {rel(path)}",
        "returncode": completed.returncode,
        "stdout_tail": completed.stdout.strip().splitlines()[-8:],
        "stderr_tail": completed.stderr.strip().splitlines()[-8:],
        "passed": completed.returncode == 0,
    }


def load_source() -> dict[str, Any]:
    source_result = read_json(SOURCE_DIR / "result.json")
    if source_result["validation"]["passed"] is not True:
        raise RuntimeError("PROD-091 must pass before PROD-092.")
    if source_result["summary"]["recommended_next_checkpoint"] != CHECKPOINT_ID:
        raise RuntimeError("PROD-091 must recommend PROD-092.")
    return source_result


def run_synonym_regression_cases() -> dict[str, Any]:
    cases = []
    for case in [*PROD_090_POSITIVE_CASES, *PROD_087_POSITIVE_CASES]:
        decision = build_runtime_decision(runtime_case(case["case_id"], case["customer_turn"]), campaign=TEST_CAMPAIGN)
        response = decision["agent_response"]
        gates = {
            "sales_difficulty": decision["sales_difficulty"] == "guided-option-selection",
            "selected_strategy": decision["selected_strategy"] == "guided-option-selection",
            "next_action": decision["next_action"] == "answer-and-continue",
            "expected_text": all(part in response for part in case["expected_contains"]),
            "short_enough": word_count(response) <= 38,
            "no_company_domain_placeholder": "companyname.com" not in response.lower(),
            "no_payment_details_collection": "payment details" not in response.lower() and "card" not in response.lower(),
        }
        cases.append(
            {
                "case_id": case["case_id"],
                "customer_turn": case["customer_turn"],
                "sales_difficulty": decision["sales_difficulty"],
                "selected_strategy": decision["selected_strategy"],
                "next_action": decision["next_action"],
                "agent_response": response,
                "gates": gates,
                "passed": all(gates.values()),
            }
        )
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "case_count": len(cases),
        "cases": cases,
        "failure_count": sum(1 for case in cases if not case["passed"]),
    }


def run_adjacent_controls() -> dict[str, Any]:
    cases = []
    for case in [*PROD_090_CONTROL_CASES, *PROD_087_CONTROL_CASES]:
        campaign = case.get("campaign", TEST_CAMPAIGN)
        decision = build_runtime_decision(runtime_case(case["case_id"], case["customer_turn"]), campaign=campaign)
        expected = CONTROL_EXPECTED_DIFFICULTY.get(case["case_id"]) or case.get("expected_sales_difficulty")
        if expected:
            passed = decision["sales_difficulty"] == expected
            expected_label = expected
        else:
            not_expected = case.get("expected_not_sales_difficulty", "guided-option-selection")
            passed = decision["sales_difficulty"] != not_expected
            expected_label = f"not {not_expected}"
        cases.append(
            {
                "case_id": case["case_id"],
                "customer_turn": case["customer_turn"],
                "expected": expected_label,
                "sales_difficulty": decision["sales_difficulty"],
                "agent_response": decision["agent_response"],
                "passed": passed,
            }
        )
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "case_count": len(cases),
        "cases": cases,
        "failure_count": sum(1 for case in cases if not case["passed"]),
    }


def build_evidence(source_result: dict[str, Any], source_validator: dict[str, Any], stable_guard: dict[str, Any]) -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "source_validation": source_result["validation"],
        "source_summary": source_result["summary"],
        "source_validator_run": source_validator,
        "stable_english_guard": stable_guard,
    }


def summarize(synonym: dict[str, Any], adjacent: dict[str, Any], stable_guard: dict[str, Any]) -> dict[str, Any]:
    return {
        "post_patch_regression_only": True,
        "synonym_positive_failures": synonym["failure_count"],
        "adjacent_control_failures": adjacent["failure_count"],
        "stable_english_guard_passed": stable_guard["passed"],
        "review_html_created": False,
        "recommended_next_checkpoint": NEXT_CHECKPOINT_ID,
        **BOUNDARY_FLAGS,
    }


def render_report(summary: dict[str, Any], synonym: dict[str, Any], adjacent: dict[str, Any]) -> str:
    lines = [
        "# PROD-092 English Guided Option Synonym Coverage Post-Patch Regression",
        "",
        "`PROD-092` verifies the `PROD-091` guided-option synonym runtime patch after application.",
        "",
        "No new runtime behavior is patched in this checkpoint.",
        "",
        "## Result",
        "",
        f"- Synonym positive failures: `{summary['synonym_positive_failures']}`",
        f"- Adjacent control failures: `{summary['adjacent_control_failures']}`",
        f"- Stable English guard passed: `{str(summary['stable_english_guard_passed']).lower()}`",
        f"- Synonym regression cases: `{synonym['case_count']}`",
        f"- Adjacent control cases: `{adjacent['case_count']}`",
        f"- Review HTML created: `{str(summary['review_html_created']).lower()}`",
        f"- Recommended next checkpoint: `{summary['recommended_next_checkpoint']}`",
        "",
        "## Boundary Status",
        "",
    ]
    for key in BOUNDARY_FLAGS:
        lines.append(f"- {key.replace('_', ' ').capitalize()}: `{str(summary[key]).lower()}`")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    source_result = load_source()
    source_validator = run_validator(SOURCE_VALIDATOR)
    if not source_validator["passed"]:
        raise RuntimeError("Source validator failed; refusing PROD-092 regression.")
    stable_guard = run_validator(ENGLISH_GUARD)
    synonym = run_synonym_regression_cases()
    adjacent = run_adjacent_controls()
    evidence = build_evidence(source_result, source_validator, stable_guard)
    summary = summarize(synonym, adjacent, stable_guard)
    result = {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "validation": {
            "passed": synonym["failure_count"] == 0 and adjacent["failure_count"] == 0 and stable_guard["passed"],
            "post_patch_regression_completed": True,
        },
        "summary": summary,
    }

    write_json(OUT_DIR / "synonym_regression_cases.json", synonym)
    write_json(OUT_DIR / "adjacent_control_cases.json", adjacent)
    write_json(OUT_DIR / "stable_english_guard_summary.json", stable_guard)
    write_json(OUT_DIR / "evidence_summary.json", evidence)
    write_json(OUT_DIR / "result.json", result)
    write_text(OUT_DIR / "report.md", render_report(summary, synonym, adjacent))
    print(json.dumps({"checkpoint_id": CHECKPOINT_ID, "validation": result["validation"], "summary": summary}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
