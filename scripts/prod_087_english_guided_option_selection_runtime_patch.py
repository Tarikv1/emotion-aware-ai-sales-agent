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


CHECKPOINT_ID = "PROD-087-english-guided-option-selection-runtime-patch"
CHECKPOINT_NAME = "English Guided Option Selection Runtime Patch"
SOURCE_CHECKPOINT_ID = "PROD-086-english-guided-option-selection-narrow-policy-probe"
NEXT_CHECKPOINT_ID = "PROD-088-english-guided-option-selection-post-patch-regression"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
SOURCE_DIR = ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID
SOURCE_VALIDATOR = ROOT / "scripts" / "validate_prod_086_english_guided_option_selection_narrow_policy_probe.py"
RUNTIME_FILE = ROOT / "runtime" / "core" / "realtime_turns.py"
PAYMENT_RESPONSE = "No payment on this call. I'll send you the link by email, and you can review the plan and register there."

TEST_CAMPAIGN = {
    "language": "en",
    "guided_option_plan_29_features": "[feature X] and [feature Y]",
    "guided_option_plan_59_added_features": "[feature A] and [feature B]",
    "guided_option_customer_goal": "[customer goal]",
    "guided_option_customer_pain": "[customer pain]",
    "guided_option_payment_email_link_allowed": True,
}

POSITIVE_CASES = [
    {
        "case_id": "prod-087-rewrite-binary-choice",
        "customer_turn": "So do I choose the $29 option or the $59 option?",
        "expected_contains": ["I mean", "$29", "$59", "[feature X]", "[feature A]"],
    },
    {
        "case_id": "prod-087-rewrite-fit-unclear",
        "customer_turn": "I can see both paths, I am just not sure which one fits me.",
        "expected_contains": ["$59", "$29", "upgrade later", "[feature A]"],
    },
    {
        "case_id": "prod-087-rewrite-recommendation",
        "customer_turn": "Which route would you suggest for someone like me?",
        "expected_contains": ["Honestly, like", "$59", "$29", "[customer pain]"],
    },
    {
        "case_id": "prod-087-rewrite-difference",
        "customer_turn": "What is the real difference between the $29 option and the $59 option?",
        "expected_contains": ["$29 covers", "$59 adds", "[feature X]", "[feature A]"],
    },
    {
        "case_id": "prod-087-rewrite-decide-later",
        "customer_turn": "Can I choose later instead of deciding on this call?",
        "expected_contains": ["Yes", "differences in writing", "both options open"],
    },
    {
        "case_id": "prod-087-rewrite-neither-uncertain",
        "customer_turn": "I'm not sure either is right.",
        "expected_contains": ["you know", "$29", "$59", "[customer goal]"],
    },
    {
        "case_id": "prod-087-rewrite-payment-path",
        "customer_turn": "If I pick one, can I pay now?",
        "expected_contains": ["No payment on this call", "link by email", "register there"],
    },
    {
        "case_id": "prod-087-rewrite-upgrade-path",
        "customer_turn": "Could I start smaller and change later if it works?",
        "expected_contains": ["start with $29", "move you to $59", "[feature A]"],
    },
]

CONTROL_CASES = [
    {
        "case_id": "prod-087-missing-feature-matrix",
        "customer_turn": "So do I choose the $29 option or the $59 option?",
        "campaign": {"language": "en"},
        "expected_not_sales_difficulty": "guided-option-selection",
    },
    {
        "case_id": "prod-087-card-payment-boundary",
        "customer_turn": "Can I pay now with my card?",
        "campaign": TEST_CAMPAIGN,
        "expected_sales_difficulty": "payment-safety-boundary",
    },
    {
        "case_id": "prod-087-payment-details-boundary",
        "customer_turn": "Can you take my payment details if I choose one?",
        "campaign": TEST_CAMPAIGN,
        "expected_sales_difficulty": "payment-safety-boundary",
    },
    {
        "case_id": "prod-087-price-only-control",
        "customer_turn": "How much does this cost?",
        "campaign": TEST_CAMPAIGN,
        "expected_sales_difficulty": "price-first-direct",
    },
    {
        "case_id": "prod-087-written-info-control",
        "customer_turn": "Can you send me the details in writing?",
        "campaign": TEST_CAMPAIGN,
        "expected_sales_difficulty": "written-info-request",
    },
    {
        "case_id": "prod-087-coverage-boundary-control",
        "customer_turn": "Does the plan cover reimbursement?",
        "campaign": TEST_CAMPAIGN,
        "expected_sales_difficulty": "coverage-boundary-route",
    },
    {
        "case_id": "prod-087-contract-signing-control",
        "customer_turn": "Can you sign me up on this call?",
        "campaign": TEST_CAMPAIGN,
        "expected_not_sales_difficulty": "guided-option-selection",
    },
    {
        "case_id": "prod-087-german-control",
        "customer_turn": "Soll ich die 29 Euro oder 59 Euro Option nehmen?",
        "campaign": {"language": "de"},
        "expected_not_sales_difficulty": "guided-option-selection",
    },
]

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
        timeout=300,
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
    constraints = read_json(SOURCE_DIR / "candidate_policy_constraints.json")
    if source_result["validation"]["passed"] is not True:
        raise RuntimeError("PROD-086 must pass before PROD-087.")
    if source_result["summary"]["policy_probe_passed"] is not True:
        raise RuntimeError("PROD-086 policy probe must pass before runtime patch.")
    if source_result["summary"]["recommended_next_checkpoint"] != CHECKPOINT_ID:
        raise RuntimeError("PROD-086 must recommend PROD-087.")
    if constraints["approved_payment_response"] != PAYMENT_RESPONSE:
        raise RuntimeError("Approved payment response changed.")
    return source_result, constraints


def runtime_case(case_id: str, customer_turn: str) -> dict[str, Any]:
    return {
        "case_id": case_id,
        "customer_input": {
            "input_type": "speech",
            "transcript": customer_turn,
            "stage": "objection-handling",
        },
    }


def word_count(text: str) -> int:
    return len(text.replace("/", " ").replace("-", " ").split())


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
        }
        passed = all(gates.values())
        cases.append(
            {
                "case_id": case["case_id"],
                "customer_turn": case["customer_turn"],
                "sales_difficulty": decision["sales_difficulty"],
                "selected_strategy": decision["selected_strategy"],
                "next_action": decision["next_action"],
                "agent_response": response,
                "gates": gates,
                "passed": passed,
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


def build_runtime_patch_summary() -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "runtime_file": "runtime/core/realtime_turns.py",
        "new_sales_difficulty": "guided-option-selection",
        "requires_plan_feature_matrix": True,
        "requires_customer_facts_for_steering": True,
        "requires_no_payment_on_call_default": True,
        "requires_no_company_domain_in_generic_payment_wording": True,
        "payment_response": PAYMENT_RESPONSE,
        "runtime_patch_applied": True,
        "review_html_created": False,
    }


def build_evidence(source_result: dict[str, Any], source_validator: dict[str, Any]) -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "source_validation": source_result["validation"],
        "source_summary": source_result["summary"],
        "source_validator_run": source_validator,
    }


def build_summary(positives: dict[str, Any], controls: dict[str, Any]) -> dict[str, Any]:
    return {
        "runtime_patch_applied": True,
        "runtime_behavior_changed": True,
        "response_text_behavior_changed": True,
        "classifier_behavior_changed": True,
        "positive_case_count": positives["case_count"],
        "positive_case_failures": positives["failure_count"],
        "control_case_count": controls["case_count"],
        "control_case_failures": controls["failure_count"],
        "review_html_created": False,
        "recommended_next_checkpoint": NEXT_CHECKPOINT_ID,
        "recommended_next_checkpoint_requires_human_review": False,
        **BOUNDARY_FLAGS,
    }


def render_report(summary: dict[str, Any], patch: dict[str, Any]) -> str:
    lines = [
        "# PROD-087 English Guided Option Selection Runtime Patch",
        "",
        "`PROD-087` applies the narrow English guided-option-selection runtime route approved by `PROD-086`.",
        "",
        "## Result",
        "",
        f"- Runtime patch applied: `{str(summary['runtime_patch_applied']).lower()}`",
        f"- Positive runtime cases: `{summary['positive_case_count']}`",
        f"- Positive runtime failures: `{summary['positive_case_failures']}`",
        f"- Control runtime cases: `{summary['control_case_count']}`",
        f"- Control runtime failures: `{summary['control_case_failures']}`",
        f"- Review HTML created: `{str(summary['review_html_created']).lower()}`",
        f"- Recommended next checkpoint: `{summary['recommended_next_checkpoint']}`",
        "",
        "## Runtime Patch",
        "",
        f"- New sales difficulty: `{patch['new_sales_difficulty']}`",
        f"- Requires plan feature matrix: `{str(patch['requires_plan_feature_matrix']).lower()}`",
        f"- Requires customer facts for steering: `{str(patch['requires_customer_facts_for_steering']).lower()}`",
        f"- Payment response: `{patch['payment_response']}`",
        "",
        "## Boundary Status",
        "",
        f"- Runtime behavior changed: `{str(summary['runtime_behavior_changed']).lower()}`",
        f"- Response text behavior changed: `{str(summary['response_text_behavior_changed']).lower()}`",
        f"- Classifier behavior changed: `{str(summary['classifier_behavior_changed']).lower()}`",
    ]
    for key in BOUNDARY_FLAGS:
        label = key.replace("_", " ")
        lines.append(f"- {label}: `{str(summary[key]).lower()}`")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    source_result, _constraints = load_source()
    source_validator = run_source_validator()
    if not source_validator["passed"]:
        raise RuntimeError("Source validator failed; refusing to verify PROD-087.")

    patch = build_runtime_patch_summary()
    positives = run_positive_cases()
    controls = run_control_cases()
    evidence = build_evidence(source_result, source_validator)
    summary = build_summary(positives, controls)
    result = {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "validation": {
            "passed": positives["failure_count"] == 0 and controls["failure_count"] == 0,
            "runtime_patch_verified": True,
        },
        "summary": summary,
    }

    write_json(OUT_DIR / "runtime_patch_summary.json", patch)
    write_json(OUT_DIR / "positive_runtime_cases.json", positives)
    write_json(OUT_DIR / "control_runtime_cases.json", controls)
    write_json(OUT_DIR / "evidence_summary.json", evidence)
    write_json(OUT_DIR / "result.json", result)
    write_text(OUT_DIR / "report.md", render_report(summary, patch))
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
