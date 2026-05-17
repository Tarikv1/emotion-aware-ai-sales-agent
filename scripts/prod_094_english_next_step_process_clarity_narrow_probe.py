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


CHECKPOINT_ID = "PROD-094-english-next-step-process-clarity-narrow-probe"
CHECKPOINT_NAME = "English Next-Step Process Clarity Narrow Probe"
SOURCE_CHECKPOINT_ID = "PROD-093-english-customer-move-remaining-slice-selection-after-guided-option-synonyms"
NEXT_CHECKPOINT_ID = "PROD-095-english-next-step-process-clarity-runtime-patch"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
SOURCE_DIR = ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID
SOURCE_VALIDATOR = ROOT / "scripts" / "validate_prod_093_english_customer_move_remaining_slice_selection_after_guided_option_synonyms.py"

SELECTED_SOURCE_SLICE = "next_step_process_clarity"
SELECTED_SOURCE_CASE_ID = "prod-081-next-step-01"
PROCESS_RESPONSE = "I'll send the link by email. You can review the plan and register there. No payment on this call."

POSITIVE_CASES = [
    {
        "case_id": "prod-094-after-yes",
        "customer_turn": "What happens after I say yes?",
        "expected_contains": ["link", "email", "review", "register", "No payment on this call"],
    },
    {
        "case_id": "prod-094-next-step-move-forward",
        "customer_turn": "What is the next step if I want to move forward?",
        "expected_contains": ["link", "email", "review", "register", "No payment on this call"],
    },
    {
        "case_id": "prod-094-after-this-call",
        "customer_turn": "If I choose one, what do I do after this call?",
        "expected_contains": ["link", "email", "review", "register", "No payment on this call"],
    },
    {
        "case_id": "prod-094-register-after-review",
        "customer_turn": "How do I register after I review the plan?",
        "expected_contains": ["link", "email", "review", "register", "No payment on this call"],
    },
    {
        "case_id": "prod-094-picked-plan-next",
        "customer_turn": "So if I pick the $59 plan, what happens next?",
        "expected_contains": ["link", "email", "review", "register", "No payment on this call"],
    },
]

CONTROL_CASES = [
    {
        "case_id": "prod-094-card-payment-control",
        "customer_turn": "Can I pay now with my card?",
        "expected_candidate_response": None,
        "why_control": "Payment/card handling stays outside this process-clarity probe.",
    },
    {
        "case_id": "prod-094-payment-details-control",
        "customer_turn": "Can you take my payment details if I choose one?",
        "expected_candidate_response": None,
        "why_control": "Payment detail collection stays blocked.",
    },
    {
        "case_id": "prod-094-signup-control",
        "customer_turn": "Can you sign me up on this call?",
        "expected_candidate_response": None,
        "why_control": "Signup or contract execution stays outside this slice.",
    },
    {
        "case_id": "prod-094-register-and-pay-control",
        "customer_turn": "I want to register and pay now.",
        "expected_candidate_response": None,
        "why_control": "Register plus pay-now language must not trigger the process response.",
    },
    {
        "case_id": "prod-094-advice-roleplay-control",
        "customer_turn": "What would you do in my position?",
        "expected_candidate_response": None,
        "why_control": "Advice roleplay remains deferred for review.",
    },
    {
        "case_id": "prod-094-generic-confusion-control",
        "customer_turn": "I am listening, but I do not know what I am supposed to decide yet.",
        "expected_candidate_response": None,
        "why_control": "Generic confusion stays unknown.",
    },
    {
        "case_id": "prod-094-provider-comparison-control",
        "customer_turn": "Can you show our current provider and your offer side by side?",
        "expected_candidate_response": None,
        "why_control": "Provider comparison stays in its existing bounded route.",
    },
    {
        "case_id": "prod-094-coverage-control",
        "customer_turn": "Does the plan cover reimbursement?",
        "expected_candidate_response": None,
        "why_control": "Coverage knowledge stays outside this slice.",
    },
    {
        "case_id": "prod-094-guided-option-control",
        "customer_turn": "Should I start small or go with the fuller option?",
        "expected_candidate_response": None,
        "why_control": "Guided-option selection is already handled by its own route.",
    },
    {
        "case_id": "prod-094-german-control",
        "customer_turn": "Was passiert, nachdem ich ja sage?",
        "expected_candidate_response": None,
        "why_control": "German exact-phrase promotion remains blocked.",
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


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def contains_any(text: str, needles: list[str]) -> bool:
    lowered = text.lower()
    return any(needle in lowered for needle in needles)


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


def load_source() -> dict[str, Any]:
    source_result = read_json(SOURCE_DIR / "result.json")
    if source_result["validation"]["passed"] is not True:
        raise RuntimeError("PROD-093 must pass before PROD-094.")
    if source_result["summary"]["recommended_next_checkpoint"] != CHECKPOINT_ID:
        raise RuntimeError("PROD-093 must recommend PROD-094.")
    return source_result


def build_case_file() -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "scope": "english_next_step_process_clarity_narrow_policy_probe",
        "policy_probe_only": True,
        "selected_source_slice": SELECTED_SOURCE_SLICE,
        "runtime_patch_allowed_inside_checkpoint": False,
        "review_html_created": False,
        "recommended_next_checkpoint": NEXT_CHECKPOINT_ID,
        "recommended_next_checkpoint_requires_human_review": False,
    }


def candidate_process_response(transcript: str) -> str | None:
    blocked_terms = [
        "payment",
        "card",
        "pay now",
        "sign me up",
        "sign up",
        "contract",
        "provider",
        "reimbursement",
        "coverage",
        "what would you do",
        "my position",
        "supposed to decide",
    ]
    if contains_any(transcript, blocked_terms):
        return None
    process_terms = [
        "what happens after",
        "next step",
        "after this call",
        "move forward",
        "register after",
        "what happens next",
    ]
    if contains_any(transcript, process_terms):
        return PROCESS_RESPONSE
    return None


def candidate_text_gates(response: str, expected_contains: list[str]) -> dict[str, bool]:
    lowered = response.lower()
    return {
        "has_expected_content": all(part in response for part in expected_contains),
        "short_enough": word_count(response) <= 22,
        "no_company_domain_placeholder": "companyname.com" not in lowered,
        "no_payment_details_collection": "payment details" not in lowered and "card" not in lowered,
        "no_payment_collection_language": "pay now" not in lowered and "take payment" not in lowered,
        "no_contract_or_signup_claim": "contract" not in lowered and "sign up" not in lowered,
        "not_fake_urgency": "today only" not in lowered and "now or never" not in lowered,
        "not_pretend_agreement": "you already chose" not in lowered and "since you agreed" not in lowered,
    }


def build_case_matrix() -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "positive_cases": POSITIVE_CASES,
        "control_cases": CONTROL_CASES,
        "positive_case_count": len(POSITIVE_CASES),
        "control_case_count": len(CONTROL_CASES),
    }


def build_policy_probe_result() -> dict[str, Any]:
    positives = []
    for case in POSITIVE_CASES:
        response = candidate_process_response(case["customer_turn"])
        gates = candidate_text_gates(response or "", case["expected_contains"])
        passed = response is not None and all(gates.values())
        positives.append(
            {
                **case,
                "candidate_response": response,
                "gates": gates,
                "passed": passed,
                "issue_codes": [] if passed else ["candidate_positive_failed"],
            }
        )
    controls = []
    for case in CONTROL_CASES:
        response = candidate_process_response(case["customer_turn"])
        passed = response is case["expected_candidate_response"]
        controls.append(
            {
                **case,
                "candidate_response": response,
                "passed": passed,
                "issue_codes": [] if passed else ["control_should_not_trigger"],
            }
        )
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "positive_cases": positives,
        "control_cases": controls,
        "positive_case_count": len(positives),
        "control_case_count": len(controls),
        "positive_failure_count": sum(1 for item in positives if not item["passed"]),
        "control_failure_count": sum(1 for item in controls if not item["passed"]),
        "failed_policy_case_count": sum(1 for item in positives + controls if not item["passed"]),
    }


def build_current_runtime_gap_analysis() -> dict[str, Any]:
    source_selection = read_json(SOURCE_DIR / "remaining_subtype_selection.json")
    source_turn = source_selection["selected_customer_turn"]
    decision = build_runtime_decision(runtime_case(SELECTED_SOURCE_CASE_ID, source_turn), campaign=TEST_CAMPAIGN)
    candidate = candidate_process_response(source_turn)
    item = {
        "case_id": SELECTED_SOURCE_CASE_ID,
        "customer_turn": source_turn,
        "observed_sales_difficulty": decision["sales_difficulty"],
        "observed_agent_response": decision["agent_response"],
        "checkpoint_time_sales_difficulty": "unknown-runtime-signal",
        "candidate_response": candidate,
        "runtime_gap": candidate is not None,
        "checkpoint_time_gap_evidence": True,
    }
    runtime_gaps = [item] if item["runtime_gap"] else []
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "items": [item],
        "runtime_gap_count": len(runtime_gaps),
        "runtime_gaps": runtime_gaps,
    }


def build_constraints() -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "selected_source_slice": SELECTED_SOURCE_SLICE,
        "selected_source_case_id": SELECTED_SOURCE_CASE_ID,
        "candidate_response": PROCESS_RESPONSE,
        "no_payment_on_call_default": True,
        "email_link_register_path_allowed": True,
        "no_payment_collection": True,
        "no_contract_signing": True,
        "advice_roleplay_boundary_deferred": True,
        "provider_comparison_boundary_preserved": True,
        "generic_confusion_deferred": True,
        "german_exact_phrase_promotion_blocked": True,
        "runtime_patch_allowed_inside_checkpoint": False,
        "review_html_created": False,
        "recommended_next_checkpoint": NEXT_CHECKPOINT_ID,
    }


def build_evidence(source_result: dict[str, Any], source_validator: dict[str, Any]) -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "source_validation": source_result["validation"],
        "source_summary": source_result["summary"],
        "source_validator_run": source_validator,
    }


def summarize(probe: dict[str, Any], gaps: dict[str, Any], source_validator: dict[str, Any]) -> dict[str, Any]:
    return {
        "policy_probe_only": True,
        "source_validator_passed": source_validator["passed"],
        "process_clarity_probe_passed": probe["failed_policy_case_count"] == 0,
        "selected_source_slice": SELECTED_SOURCE_SLICE,
        "positive_case_count": probe["positive_case_count"],
        "control_case_count": probe["control_case_count"],
        "failed_policy_case_count": probe["failed_policy_case_count"],
        "current_runtime_gap_count": gaps["runtime_gap_count"],
        "no_payment_on_call_default": True,
        "email_link_register_path_allowed": True,
        "requires_human_review_before_next_checkpoint": False,
        "recommended_next_checkpoint_requires_human_review": False,
        "review_html_created": False,
        "recommended_next_checkpoint": NEXT_CHECKPOINT_ID,
        **BOUNDARY_FLAGS,
    }


def render_report(summary: dict[str, Any], probe: dict[str, Any], gaps: dict[str, Any], constraints: dict[str, Any]) -> str:
    lines = [
        "# PROD-094 English Next-Step Process Clarity Narrow Probe",
        "",
        "`PROD-094` tests whether the selected post-yes process-clarity slice can use concise email-link/register wording before any runtime patch.",
        "",
        "This checkpoint is policy-probe-only. It changes no runtime behavior, response text, classifier reachability, retrieval, provider usage, private-data handling, voice playback, payment handling, contract signing, legal readiness, German wording, or production runtime promotion.",
        "",
        "## Result",
        "",
        f"- Policy probe only: `{str(summary['policy_probe_only']).lower()}`",
        f"- Process clarity probe passed: `{str(summary['process_clarity_probe_passed']).lower()}`",
        f"- Selected source slice: `{summary['selected_source_slice']}`",
        f"- Positive case count: `{summary['positive_case_count']}`",
        f"- Control case count: `{summary['control_case_count']}`",
        f"- Failed policy case count: `{summary['failed_policy_case_count']}`",
        f"- Current runtime gap count: `{summary['current_runtime_gap_count']}`",
        f"- No payment on this call default: `{str(summary['no_payment_on_call_default']).lower()}`",
        f"- Email link register path allowed: `{str(summary['email_link_register_path_allowed']).lower()}`",
        f"- Requires human review before next checkpoint: `{str(summary['requires_human_review_before_next_checkpoint']).lower()}`",
        f"- Recommended next checkpoint requires human review: `{str(summary['recommended_next_checkpoint_requires_human_review']).lower()}`",
        f"- Review HTML created: `{str(summary['review_html_created']).lower()}`",
        f"- Recommended next checkpoint: `{summary['recommended_next_checkpoint']}`",
        "",
        "## Candidate Response",
        "",
        f"`{constraints['candidate_response']}`",
        "",
        "## Runtime Gap",
        "",
    ]
    for item in gaps["runtime_gaps"]:
        lines.append(f"- `{item['case_id']}` -> `{item['checkpoint_time_sales_difficulty']}`: {item['customer_turn']}")
    lines.extend(["", "## Candidate Positive Cases", ""])
    for item in probe["positive_cases"]:
        lines.append(f"- `{item['case_id']}` passed `{str(item['passed']).lower()}`: {item['candidate_response']}")
    lines.extend(["", "## Boundary Status", ""])
    for key in BOUNDARY_FLAGS:
        lines.append(f"- {key.replace('_', ' ').capitalize()}: `{str(summary[key]).lower()}`")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    source_result = load_source()
    source_validator = run_source_validator()
    matrix = build_case_matrix()
    probe = build_policy_probe_result()
    gaps = build_current_runtime_gap_analysis()
    constraints = build_constraints()
    evidence = build_evidence(source_result, source_validator)
    summary = summarize(probe, gaps, source_validator)
    result = {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "validation": {
            "passed": source_validator["passed"] and probe["failed_policy_case_count"] == 0 and gaps["runtime_gap_count"] == 1,
            "policy_probe_passed": probe["failed_policy_case_count"] == 0,
        },
        "summary": summary,
    }

    write_json(OUT_DIR / "candidate_policy_constraints.json", constraints)
    write_json(OUT_DIR / "process_clarity_probe_case_matrix.json", matrix)
    write_json(OUT_DIR / "policy_probe_result.json", probe)
    write_json(OUT_DIR / "current_runtime_gap_analysis.json", gaps)
    write_json(OUT_DIR / "evidence_summary.json", evidence)
    write_text(OUT_DIR / "report.md", render_report(summary, probe, gaps, constraints))
    write_json(OUT_DIR / "result.json", result)
    print(json.dumps({"checkpoint_id": CHECKPOINT_ID, "validation": result["validation"], "summary": summary}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
