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
from prod_094_english_next_step_process_clarity_narrow_probe import CONTROL_CASES, POSITIVE_CASES, PROCESS_RESPONSE  # noqa: E402


CHECKPOINT_ID = "PROD-096-english-next-step-process-clarity-post-patch-regression"
CHECKPOINT_NAME = "English Next-Step Process Clarity Post-Patch Regression"
SOURCE_CHECKPOINT_ID = "PROD-095-english-next-step-process-clarity-runtime-patch"
NEXT_CHECKPOINT_ID = "PROD-097-english-customer-move-remaining-slice-selection-after-process-clarity"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
SOURCE_DIR = ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID
SOURCE_VALIDATOR = ROOT / "scripts" / "validate_prod_095_english_next_step_process_clarity_runtime_patch.py"
STABLE_ENGLISH_GUARD = ROOT / "scripts" / "validate_english_multi_turn_regression_guard.py"

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

CONTROL_EXPECTED_DIFFICULTY = {
    "prod-094-card-payment-control": "payment-safety-boundary",
    "prod-094-payment-details-control": "payment-safety-boundary",
    "prod-094-coverage-control": "coverage-boundary-route",
    "prod-094-guided-option-control": "guided-option-selection",
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
        raise RuntimeError("PROD-095 must pass before PROD-096.")
    if source_result["summary"]["recommended_next_checkpoint"] != CHECKPOINT_ID:
        raise RuntimeError("PROD-095 must recommend PROD-096.")
    return source_result


def run_process_clarity_regression_cases() -> dict[str, Any]:
    cases = []
    for case in POSITIVE_CASES:
        decision = build_runtime_decision(runtime_case(case["case_id"], case["customer_turn"]), campaign=TEST_CAMPAIGN)
        response = decision["agent_response"]
        gates = {
            "sales_difficulty": decision["sales_difficulty"] == "next-step-process-clarity",
            "selected_strategy": decision["selected_strategy"] == "process-clarity",
            "next_action": decision["next_action"] == "answer-and-continue",
            "expected_text": all(part in response for part in case["expected_contains"]),
            "exact_candidate_response": response == PROCESS_RESPONSE,
            "short_enough": word_count(response) <= 22,
            "no_payment_details_collection": "payment details" not in response.lower() and "card" not in response.lower(),
            "no_contract_or_signup_claim": "contract" not in response.lower() and "sign up" not in response.lower(),
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


def run_adjacent_control_cases() -> dict[str, Any]:
    cases = []
    for case in CONTROL_CASES:
        decision = build_runtime_decision(runtime_case(case["case_id"], case["customer_turn"]), campaign=TEST_CAMPAIGN)
        expected = CONTROL_EXPECTED_DIFFICULTY.get(case["case_id"])
        passed = decision["sales_difficulty"] == expected if expected else decision["sales_difficulty"] != "next-step-process-clarity"
        cases.append(
            {
                "case_id": case["case_id"],
                "customer_turn": case["customer_turn"],
                "expected": expected or "not next-step-process-clarity",
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
        "stable_english_guard_run": stable_guard,
    }


def summarize(positives: dict[str, Any], controls: dict[str, Any], source_validator: dict[str, Any], stable_guard: dict[str, Any]) -> dict[str, Any]:
    return {
        "post_patch_regression_only": True,
        "source_validator_passed": source_validator["passed"],
        "process_clarity_positive_failures": positives["failure_count"],
        "adjacent_control_failures": controls["failure_count"],
        "stable_english_guard_passed": stable_guard["passed"],
        "review_html_created": False,
        "recommended_next_checkpoint": NEXT_CHECKPOINT_ID,
        **BOUNDARY_FLAGS,
    }


def render_report(summary: dict[str, Any], positives: dict[str, Any], controls: dict[str, Any]) -> str:
    lines = [
        "# PROD-096 English Next-Step Process Clarity Post-Patch Regression",
        "",
        "`PROD-096` verifies the `PROD-095` English process-clarity runtime patch after application.",
        "",
        "This checkpoint is post-patch regression only. It changes no runtime behavior, response text, classifier reachability, retrieval, provider usage, private-data handling, voice playback, payment handling, contract signing, legal readiness, German wording, or production runtime promotion.",
        "",
        "## Result",
        "",
        f"- Post-patch regression only: `{str(summary['post_patch_regression_only']).lower()}`",
        f"- Process clarity positive failures: `{summary['process_clarity_positive_failures']}`",
        f"- Adjacent control failures: `{summary['adjacent_control_failures']}`",
        f"- Stable English guard passed: `{str(summary['stable_english_guard_passed']).lower()}`",
        f"- Review HTML created: `{str(summary['review_html_created']).lower()}`",
        f"- Recommended next checkpoint: `{summary['recommended_next_checkpoint']}`",
        "",
        "## Process Clarity Cases",
        "",
    ]
    for item in positives["cases"]:
        lines.append(f"- `{item['case_id']}` -> `{item['sales_difficulty']}`, passed `{str(item['passed']).lower()}`")
    lines.extend(["", "## Adjacent Controls", ""])
    for item in controls["cases"]:
        lines.append(f"- `{item['case_id']}` expected `{item['expected']}`, observed `{item['sales_difficulty']}`, passed `{str(item['passed']).lower()}`")
    lines.extend(["", "## Boundary Status", ""])
    for key in BOUNDARY_FLAGS:
        lines.append(f"- {key.replace('_', ' ').capitalize()}: `{str(summary[key]).lower()}`")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    source_result = load_source()
    source_validator = run_validator(SOURCE_VALIDATOR)
    stable_guard = run_validator(STABLE_ENGLISH_GUARD)
    positives = run_process_clarity_regression_cases()
    controls = run_adjacent_control_cases()
    evidence = build_evidence(source_result, source_validator, stable_guard)
    summary = summarize(positives, controls, source_validator, stable_guard)
    result = {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "validation": {
            "passed": source_validator["passed"]
            and stable_guard["passed"]
            and positives["failure_count"] == 0
            and controls["failure_count"] == 0,
            "post_patch_regression_completed": True,
        },
        "summary": summary,
    }

    write_json(OUT_DIR / "process_clarity_regression_cases.json", positives)
    write_json(OUT_DIR / "adjacent_control_cases.json", controls)
    write_json(OUT_DIR / "stable_english_guard_summary.json", stable_guard)
    write_json(OUT_DIR / "evidence_summary.json", evidence)
    write_text(OUT_DIR / "report.md", render_report(summary, positives, controls))
    write_json(OUT_DIR / "result.json", result)
    print(json.dumps({"checkpoint_id": CHECKPOINT_ID, "validation": result["validation"], "summary": summary}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
