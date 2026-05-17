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
from prod_087_english_guided_option_selection_runtime_patch import TEST_CAMPAIGN, runtime_case, word_count  # noqa: E402
from prod_090_english_guided_option_synonym_coverage_narrow_probe import CONTROL_CASES, POSITIVE_CASES  # noqa: E402


CHECKPOINT_ID = "PROD-091-english-guided-option-synonym-coverage-runtime-patch"
CHECKPOINT_NAME = "English Guided Option Synonym Coverage Runtime Patch"
SOURCE_CHECKPOINT_ID = "PROD-090-english-guided-option-synonym-coverage-narrow-probe"
NEXT_CHECKPOINT_ID = "PROD-092-english-guided-option-synonym-coverage-post-patch-regression"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
SOURCE_DIR = ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID
SOURCE_VALIDATOR = ROOT / "scripts" / "validate_prod_090_english_guided_option_synonym_coverage_narrow_probe.py"
RUNTIME_FILE = ROOT / "runtime" / "core" / "realtime_turns.py"

BOUNDARY_FLAGS = {
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

CONTROL_EXPECTED_DIFFICULTY = {
    "prod-090-card-payment-control": "payment-safety-boundary",
    "prod-090-payment-details-control": "payment-safety-boundary",
    "prod-090-coverage-control": "coverage-boundary-route",
    "prod-090-autonomy-control": "autonomy-check",
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


def run_source_validator() -> dict[str, Any]:
    completed = subprocess.run(
        [sys.executable, str(SOURCE_VALIDATOR)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=360,
        check=False,
    )
    return {
        "command": f"python {rel(SOURCE_VALIDATOR)}",
        "returncode": completed.returncode,
        "stdout_tail": completed.stdout.strip().splitlines()[-8:],
        "stderr_tail": completed.stderr.strip().splitlines()[-8:],
        "passed": completed.returncode == 0,
    }


def load_source() -> tuple[dict[str, Any], dict[str, Any]]:
    source_result = read_json(SOURCE_DIR / "result.json")
    gap_analysis = read_json(SOURCE_DIR / "current_runtime_gap_analysis.json")
    if source_result["validation"]["passed"] is not True:
        raise RuntimeError("PROD-090 must pass before PROD-091.")
    if source_result["summary"]["recommended_next_checkpoint"] != CHECKPOINT_ID:
        raise RuntimeError("PROD-090 must recommend PROD-091.")
    if gap_analysis["runtime_gap_count"] != 2:
        raise RuntimeError("PROD-090 must identify exactly two runtime gaps.")
    return source_result, gap_analysis


def run_positive_cases() -> dict[str, Any]:
    cases = []
    for case in POSITIVE_CASES:
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
            "no_contract_claim": "contract" not in response.lower() and "sign up" not in response.lower(),
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


def run_control_cases() -> dict[str, Any]:
    cases = []
    for case in CONTROL_CASES:
        decision = build_runtime_decision(runtime_case(case["case_id"], case["customer_turn"]), campaign=TEST_CAMPAIGN)
        expected = CONTROL_EXPECTED_DIFFICULTY.get(case["case_id"])
        passed = decision["sales_difficulty"] == expected if expected else decision["sales_difficulty"] != "guided-option-selection"
        cases.append(
            {
                "case_id": case["case_id"],
                "customer_turn": case["customer_turn"],
                "expected": expected or "not guided-option-selection",
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


def build_patch_summary(gap_analysis: dict[str, Any]) -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "runtime_file": rel(RUNTIME_FILE),
        "runtime_patch_applied": True,
        "selected_gap_case_ids": [item["case_id"] for item in gap_analysis["runtime_gaps"]],
        "added_option_signals": ["start small", "fuller option", "side by side"],
        "added_action_signals": ["show", "side by side", "worth it", "worth"],
        "added_response_branches": ["worth it", "side by side", "start small/fuller option"],
        "provider_side_by_side_guard_added": True,
        "review_html_created": False,
    }


def build_evidence(source_result: dict[str, Any], gap_analysis: dict[str, Any], source_validator: dict[str, Any]) -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "source_validation": source_result["validation"],
        "source_summary": source_result["summary"],
        "source_gap_count_before_patch": gap_analysis["runtime_gap_count"],
        "source_validator_run": source_validator,
    }


def summarize(positives: dict[str, Any], controls: dict[str, Any], gap_analysis: dict[str, Any], source_validator: dict[str, Any]) -> dict[str, Any]:
    return {
        "runtime_patch_applied": True,
        "runtime_behavior_changed": True,
        "response_text_behavior_changed": True,
        "classifier_behavior_changed": True,
        "source_validator_passed": source_validator["passed"],
        "selected_gap_fixed_count": len(gap_analysis["runtime_gaps"]),
        "positive_case_count": positives["case_count"],
        "positive_case_failures": positives["failure_count"],
        "control_case_count": controls["case_count"],
        "control_case_failures": controls["failure_count"],
        "current_runtime_gap_count_before_patch": gap_analysis["runtime_gap_count"],
        "review_html_created": False,
        "recommended_next_checkpoint": NEXT_CHECKPOINT_ID,
        **BOUNDARY_FLAGS,
    }


def render_report(summary: dict[str, Any], patch: dict[str, Any]) -> str:
    lines = [
        "# PROD-091 English Guided Option Synonym Coverage Runtime Patch",
        "",
        "`PROD-091` applies the smallest runtime trigger expansion for the two `PROD-090` guided-option synonym gaps.",
        "",
        "## Result",
        "",
        f"- Runtime patch applied: `{str(summary['runtime_patch_applied']).lower()}`",
        f"- Selected gap fixed count: `{summary['selected_gap_fixed_count']}`",
        f"- Positive case failures: `{summary['positive_case_failures']}`",
        f"- Control case failures: `{summary['control_case_failures']}`",
        f"- Review HTML created: `{str(summary['review_html_created']).lower()}`",
        f"- Recommended next checkpoint: `{summary['recommended_next_checkpoint']}`",
        "",
        "## Patch Summary",
        "",
        f"- Added option signals: `{', '.join(patch['added_option_signals'])}`",
        f"- Added action signals: `{', '.join(patch['added_action_signals'])}`",
        f"- Provider side-by-side guard added: `{str(patch['provider_side_by_side_guard_added']).lower()}`",
        "",
        "## Boundary Status",
        "",
        f"- Runtime behavior changed: `{str(summary['runtime_behavior_changed']).lower()}`",
        f"- Response text behavior changed: `{str(summary['response_text_behavior_changed']).lower()}`",
        f"- Classifier behavior changed: `{str(summary['classifier_behavior_changed']).lower()}`",
    ]
    for key in BOUNDARY_FLAGS:
        lines.append(f"- {key.replace('_', ' ').capitalize()}: `{str(summary[key]).lower()}`")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    source_result, gap_analysis = load_source()
    source_validator = run_source_validator()
    positives = run_positive_cases()
    controls = run_control_cases()
    patch = build_patch_summary(gap_analysis)
    evidence = build_evidence(source_result, gap_analysis, source_validator)
    summary = summarize(positives, controls, gap_analysis, source_validator)
    result = {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "validation": {
            "passed": source_validator["passed"] and positives["failure_count"] == 0 and controls["failure_count"] == 0,
            "runtime_patch_verified": positives["failure_count"] == 0 and controls["failure_count"] == 0,
        },
        "summary": summary,
    }
    write_json(OUT_DIR / "runtime_patch_summary.json", patch)
    write_json(OUT_DIR / "positive_runtime_cases.json", positives)
    write_json(OUT_DIR / "control_runtime_cases.json", controls)
    write_json(OUT_DIR / "evidence_summary.json", evidence)
    write_text(OUT_DIR / "report.md", render_report(summary, patch))
    write_json(OUT_DIR / "result.json", result)
    print(json.dumps({"checkpoint_id": CHECKPOINT_ID, "validation": result["validation"], "summary": summary}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
