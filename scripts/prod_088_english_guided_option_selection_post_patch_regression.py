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

from runtime.core.realtime_turns import build_runtime_decision
from prod_087_english_guided_option_selection_runtime_patch import (
    CONTROL_CASES as PROD_087_CONTROL_CASES,
    POSITIVE_CASES as PROD_087_POSITIVE_CASES,
    TEST_CAMPAIGN,
    runtime_case,
    word_count,
)


CHECKPOINT_ID = "PROD-088-english-guided-option-selection-post-patch-regression"
CHECKPOINT_NAME = "English Guided Option Selection Post-Patch Regression"
SOURCE_CHECKPOINT_ID = "PROD-087-english-guided-option-selection-runtime-patch"
NEXT_CHECKPOINT_ID = "PROD-089-english-customer-move-remaining-slice-selection-after-guided-option"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
SOURCE_DIR = ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID
SOURCE_VALIDATOR = ROOT / "scripts" / "validate_prod_087_english_guided_option_selection_runtime_patch.py"
ENGLISH_GUARD = ROOT / "scripts" / "validate_english_multi_turn_regression_guard.py"

ADDITIONAL_ADJACENT_CONTROLS = [
    {
        "case_id": "prod-088-provider-comparison-control",
        "customer_turn": "How is this different from our current provider?",
        "campaign": TEST_CAMPAIGN,
        "expected_sales_difficulty": "provider-comparison",
    },
    {
        "case_id": "prod-088-existing-provider-control",
        "customer_turn": "We already have a provider and I do not want to switch.",
        "campaign": TEST_CAMPAIGN,
        "expected_sales_difficulty": "existing-provider-gap",
    },
    {
        "case_id": "prod-088-autonomy-control",
        "customer_turn": "I need time to think. Do not rush.",
        "campaign": TEST_CAMPAIGN,
        "expected_sales_difficulty": "autonomy-check",
    },
    {
        "case_id": "prod-088-product-detail-control",
        "customer_turn": "Which exact plan is included?",
        "campaign": TEST_CAMPAIGN,
        "expected_sales_difficulty": "product-detail-lookup",
    },
    {
        "case_id": "prod-088-unknown-control",
        "customer_turn": "That sounds interesting, but I need more context.",
        "campaign": TEST_CAMPAIGN,
        "expected_sales_difficulty": "unknown-runtime-signal",
    },
]

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
    result = read_json(SOURCE_DIR / "result.json")
    if result["validation"]["passed"] is not True:
        raise RuntimeError("PROD-087 must pass before PROD-088.")
    if result["summary"]["recommended_next_checkpoint"] != CHECKPOINT_ID:
        raise RuntimeError("PROD-087 must recommend PROD-088.")
    return result


def run_guided_option_cases() -> dict[str, Any]:
    cases = []
    for case in PROD_087_POSITIVE_CASES:
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
    for case in [*PROD_087_CONTROL_CASES, *ADDITIONAL_ADJACENT_CONTROLS]:
        decision = build_runtime_decision(
            runtime_case(case["case_id"], case["customer_turn"]),
            campaign=case.get("campaign", TEST_CAMPAIGN),
        )
        if "expected_sales_difficulty" in case:
            passed = decision["sales_difficulty"] == case["expected_sales_difficulty"]
            expected = case["expected_sales_difficulty"]
        else:
            passed = decision["sales_difficulty"] != case["expected_not_sales_difficulty"]
            expected = f"not {case['expected_not_sales_difficulty']}"
        cases.append(
            {
                "case_id": case["case_id"],
                "customer_turn": case["customer_turn"],
                "expected": expected,
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


def build_summary(guided: dict[str, Any], adjacent: dict[str, Any], stable_guard: dict[str, Any]) -> dict[str, Any]:
    return {
        "post_patch_regression_only": True,
        "guided_option_positive_failures": guided["failure_count"],
        "adjacent_control_failures": adjacent["failure_count"],
        "stable_english_guard_passed": stable_guard["passed"],
        "review_html_created": False,
        "recommended_next_checkpoint": NEXT_CHECKPOINT_ID,
        "recommended_next_checkpoint_requires_human_review": False,
        **BOUNDARY_FLAGS,
    }


def render_report(summary: dict[str, Any], guided: dict[str, Any], adjacent: dict[str, Any]) -> str:
    lines = [
        "# PROD-088 English Guided Option Selection Post-Patch Regression",
        "",
        "`PROD-088` verifies the `PROD-087` runtime patch after application.",
        "",
        "No new runtime behavior is patched in this checkpoint.",
        "",
        "## Result",
        "",
        f"- Guided option positive failures: `{summary['guided_option_positive_failures']}`",
        f"- Adjacent control failures: `{summary['adjacent_control_failures']}`",
        f"- Stable English guard passed: `{str(summary['stable_english_guard_passed']).lower()}`",
        f"- Guided option positive cases: `{guided['case_count']}`",
        f"- Adjacent control cases: `{adjacent['case_count']}`",
        f"- Review HTML created: `{str(summary['review_html_created']).lower()}`",
        f"- Recommended next checkpoint: `{summary['recommended_next_checkpoint']}`",
        "",
        "## Boundary Status",
        "",
    ]
    for key in BOUNDARY_FLAGS:
        label = key.replace("_", " ")
        lines.append(f"- {label}: `{str(summary[key]).lower()}`")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    source_result = load_source()
    source_validator = run_validator(SOURCE_VALIDATOR)
    if not source_validator["passed"]:
        raise RuntimeError("Source validator failed; refusing PROD-088 regression.")
    stable_guard = run_validator(ENGLISH_GUARD)
    guided = run_guided_option_cases()
    adjacent = run_adjacent_controls()
    evidence = build_evidence(source_result, source_validator, stable_guard)
    summary = build_summary(guided, adjacent, stable_guard)
    result = {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "validation": {
            "passed": guided["failure_count"] == 0 and adjacent["failure_count"] == 0 and stable_guard["passed"],
            "post_patch_regression_completed": True,
        },
        "summary": summary,
    }

    write_json(OUT_DIR / "guided_option_regression_cases.json", guided)
    write_json(OUT_DIR / "adjacent_control_cases.json", adjacent)
    write_json(OUT_DIR / "stable_english_guard_summary.json", stable_guard)
    write_json(OUT_DIR / "evidence_summary.json", evidence)
    write_json(OUT_DIR / "result.json", result)
    write_text(OUT_DIR / "report.md", render_report(summary, guided, adjacent))
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
