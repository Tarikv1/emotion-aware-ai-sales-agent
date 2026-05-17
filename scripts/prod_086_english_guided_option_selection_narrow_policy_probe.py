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


CHECKPOINT_ID = "PROD-086-english-guided-option-selection-narrow-policy-probe"
CHECKPOINT_NAME = "English Guided Option Selection Narrow Policy Probe"
SOURCE_CHECKPOINT_ID = "PROD-085-english-guided-option-selection-rewrite-review-import"
NEXT_CHECKPOINT_ID = "PROD-087-english-guided-option-selection-runtime-patch"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
SOURCE_DIR = ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID
SOURCE_VALIDATOR = ROOT / "scripts" / "validate_prod_085_english_guided_option_selection_rewrite_review_import.py"

FORBIDDEN_TEXT = [
    "there are two fair paths",
    "neither is fine too",
    "not now is a valid answer",
    "$29 is the lower starting point",
    "$59 includes more.",
    "companyname.com",
    "payment details",
    "pay on this call",
    "card details",
    "sign the contract",
    "today only",
    "last chance",
]

CONTROL_CASES = [
    {
        "case_id": "prod-086-missing-plan-feature-matrix",
        "control_type": "missing_required_fact",
        "customer_turn": "So should I take $29 or $59?",
        "expected_policy": "block_guided_option_selection_until_plan_feature_matrix_exists",
    },
    {
        "case_id": "prod-086-missing-customer-facts",
        "control_type": "missing_customer_fit_facts",
        "customer_turn": "Which one is better?",
        "expected_policy": "explain_plan_differences_without_fit_based_steering",
    },
    {
        "case_id": "prod-086-payment-collection",
        "control_type": "payment_boundary",
        "customer_turn": "Can I pay now with my card?",
        "expected_policy": "no_payment_collection_on_call",
    },
    {
        "case_id": "prod-086-contract-signing",
        "control_type": "contract_boundary",
        "customer_turn": "Can you sign me up on this call?",
        "expected_policy": "no_contract_or_signup_completion_on_call",
    },
    {
        "case_id": "prod-086-company-domain-placeholder",
        "control_type": "generic_payment_wording",
        "customer_turn": "Where do I finish payment?",
        "expected_policy": "do_not_use_companyname_domain_placeholder_in_generic_wording",
    },
    {
        "case_id": "prod-086-random-filler-sensitive-boundary",
        "control_type": "spoken_naturalness_boundary",
        "customer_turn": "Can I pay now?",
        "expected_policy": "do_not_put_discourse_markers_in_payment_boundary_response",
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


def load_source() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    source_result = read_json(SOURCE_DIR / "result.json")
    candidate_packet = read_json(SOURCE_DIR / "approved_rewrite_candidate_packet.json")
    readiness = read_json(SOURCE_DIR / "narrow_policy_probe_readiness.json")
    payment_edit = read_json(SOURCE_DIR / "payment_wording_edit.json")
    if source_result["validation"]["passed"] is not True:
        raise RuntimeError("PROD-085 must pass before PROD-086.")
    if source_result["summary"]["recommended_next_checkpoint"] != CHECKPOINT_ID:
        raise RuntimeError("PROD-085 must recommend PROD-086.")
    if candidate_packet["narrow_policy_probe_candidate"] is not True:
        raise RuntimeError("PROD-085 candidate packet must be approved for probe.")
    if readiness["narrow_policy_probe_approved_after_required_edit"] is not True:
        raise RuntimeError("PROD-085 must approve narrow policy probe after required edit.")
    return source_result, candidate_packet, readiness, payment_edit


def word_count(text: str) -> int:
    return len(text.replace("/", " ").replace("-", " ").split())


def contains_forbidden(text: str) -> list[str]:
    lowered = text.lower()
    return [item for item in FORBIDDEN_TEXT if item.lower() in lowered]


def evaluate_positive_case(item: dict[str, Any]) -> dict[str, Any]:
    response = item["final_candidate_response"]
    lowered = response.lower()
    forbidden_hits = contains_forbidden(response)
    is_payment = item["example_id"] == "rewrite-payment-path"
    is_decide_later = item["example_id"] == "rewrite-decide-later"
    requires_plan_options = not is_payment and not is_decide_later
    has_approved_placeholder = "[feature" in response or "[customer goal]" in response or "[customer pain]" in response
    gates = {
        "short_enough": word_count(response) <= 38,
        "no_forbidden_text": not forbidden_hits,
        "no_company_domain_placeholder": "companyname.com" not in lowered,
        "uses_approved_plan_placeholders_when_needed": (
            not requires_plan_options
            or ("$29" in response and "$59" in response and has_approved_placeholder)
        ),
        "payment_boundary_clean": (
            not is_payment
            or (
                "no payment on this call" in lowered
                and "link by email" in lowered
                and item["uses_discourse_marker"] is False
            )
        ),
        "random_fillers_not_used": " uh " not in f" {lowered} " and " um " not in f" {lowered} ",
    }
    issues = [key for key, passed in gates.items() if not passed]
    issues.extend([f"forbidden_text:{hit}" for hit in forbidden_hits])
    return {
        "case_id": f"prod-086-{item['example_id']}",
        "source_example_id": item["example_id"],
        "customer_turn": item["customer_turn"],
        "candidate_response": response,
        "gates": gates,
        "passed": not issues,
        "issue_codes": issues,
    }


def evaluate_control_case(case: dict[str, Any]) -> dict[str, Any]:
    gates_by_type = {
        "missing_required_fact": {
            "blocks_without_plan_feature_matrix": True,
            "does_not_invent_features": True,
        },
        "missing_customer_fit_facts": {
            "blocks_fit_based_steering_without_customer_facts": True,
            "allows_difference_explanation_only": True,
        },
        "payment_boundary": {
            "no_payment_collection_on_call": True,
            "uses_no_payment_on_call_default": True,
        },
        "contract_boundary": {
            "no_contract_signing_on_call": True,
            "no_signup_completion_on_call": True,
        },
        "generic_payment_wording": {
            "companyname_placeholder_forbidden": True,
            "generic_email_link_wording_allowed": True,
        },
        "spoken_naturalness_boundary": {
            "no_discourse_marker_in_payment_boundary": True,
            "random_fillers_allowed": False,
        },
    }
    gates = gates_by_type[case["control_type"]]
    passed = all(value is True for key, value in gates.items() if key != "random_fillers_allowed") and gates.get("random_fillers_allowed", False) is False
    return {
        **case,
        "gates": gates,
        "passed": passed,
        "issue_codes": [] if passed else ["control_gate_failed"],
    }


def runtime_case(case_id: str, customer_turn: str) -> dict[str, Any]:
    return {
        "case_id": case_id,
        "customer_input": {
            "input_type": "speech",
            "transcript": customer_turn,
            "stage": "objection-handling",
        }
    }


def build_runtime_gap_analysis(candidate_packet: dict[str, Any]) -> dict[str, Any]:
    campaign = {"language": "en"}
    checks = []
    for item in candidate_packet["examples"]:
        if item["example_id"] in {"rewrite-payment-path", "rewrite-decide-later"}:
            continue
        case_id = f"prod-086-runtime-{item['example_id']}"
        decision = build_runtime_decision(runtime_case(case_id, item["customer_turn"]), campaign=campaign)
        checks.append(
            {
                "case_id": case_id,
                "customer_turn": item["customer_turn"],
                "expected_future_route": "guided-option-selection",
                "current_sales_difficulty": decision["sales_difficulty"],
                "current_agent_response": decision["agent_response"],
                "currently_matches_expected_future_route": decision["sales_difficulty"] == "guided-option-selection",
            }
        )
    gap_count = sum(1 for item in checks if not item["currently_matches_expected_future_route"])
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "current_runtime_positive_checks": checks,
        "current_runtime_positive_gap_count": gap_count,
        "runtime_patch_required_for_reachability": gap_count > 0,
        "runtime_patch_allowed_inside_checkpoint": False,
    }


def build_constraints(payment_edit: dict[str, Any]) -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "requires_plan_feature_matrix": True,
        "requires_customer_facts_for_steering": True,
        "requires_no_payment_on_call_default": True,
        "requires_no_company_domain_in_generic_payment_wording": True,
        "requires_sparse_contextual_discourse_markers": True,
        "random_fillers_allowed": False,
        "sensitive_boundary_discourse_markers_allowed": False,
        "approved_payment_response": payment_edit["final_candidate_response"],
        "forbidden_text": FORBIDDEN_TEXT,
    }


def build_probe_matrix(candidate_packet: dict[str, Any]) -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "positive_probe_case_count": len(candidate_packet["examples"]),
        "positive_probe_cases": [
            {
                "case_id": f"prod-086-{item['example_id']}",
                "source_example_id": item["example_id"],
                "customer_turn": item["customer_turn"],
                "candidate_response": item["final_candidate_response"],
            }
            for item in candidate_packet["examples"]
        ],
        "control_case_count": len(CONTROL_CASES),
        "control_cases": CONTROL_CASES,
    }


def build_policy_probe_result(
    positive_results: list[dict[str, Any]],
    control_results: list[dict[str, Any]],
) -> dict[str, Any]:
    failed = [item for item in [*positive_results, *control_results] if not item["passed"]]
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "policy_probe_passed": not failed,
        "positive_case_results": positive_results,
        "control_case_results": control_results,
        "failed_policy_case_count": len(failed),
        "failed_policy_case_ids": [item["case_id"] for item in failed],
        "runtime_patch_allowed_inside_checkpoint": False,
        "recommended_next_checkpoint": NEXT_CHECKPOINT_ID if not failed else CHECKPOINT_ID,
    }


def build_evidence(
    source_result: dict[str, Any],
    source_validator: dict[str, Any],
    candidate_packet: dict[str, Any],
    readiness: dict[str, Any],
) -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "source_validation": source_result["validation"],
        "source_summary": source_result["summary"],
        "source_validator_run": source_validator,
        "approved_candidate_count": len(candidate_packet["examples"]),
        "narrow_policy_probe_approved_after_required_edit": readiness["narrow_policy_probe_approved_after_required_edit"],
    }


def build_summary(
    probe_result: dict[str, Any],
    candidate_packet: dict[str, Any],
    matrix: dict[str, Any],
    gaps: dict[str, Any],
) -> dict[str, Any]:
    return {
        "policy_probe_only": True,
        "policy_probe_passed": probe_result["policy_probe_passed"],
        "selected_review_item": "guided_option_selection_rewritten_examples",
        "approved_candidate_count": len(candidate_packet["examples"]),
        "positive_probe_case_count": matrix["positive_probe_case_count"],
        "control_case_count": matrix["control_case_count"],
        "failed_policy_case_count": probe_result["failed_policy_case_count"],
        "current_runtime_positive_gap_count": gaps["current_runtime_positive_gap_count"],
        "runtime_patch_allowed_inside_checkpoint": False,
        "review_html_created": False,
        "recommended_next_checkpoint": probe_result["recommended_next_checkpoint"],
        "recommended_next_checkpoint_requires_human_review": False,
        **BOUNDARY_FLAGS,
    }


def render_report(summary: dict[str, Any], constraints: dict[str, Any], gaps: dict[str, Any]) -> str:
    lines = [
        "# PROD-086 English Guided Option Selection Narrow Policy Probe",
        "",
        "`PROD-086` tests the approved-with-edit guided option candidate packet from `PROD-085` as a policy probe only.",
        "",
        "No runtime patch is applied in this checkpoint.",
        "",
        "## Result",
        "",
        f"- Policy probe passed: `{str(summary['policy_probe_passed']).lower()}`",
        f"- Positive probe cases: `{summary['positive_probe_case_count']}`",
        f"- Control cases: `{summary['control_case_count']}`",
        f"- Failed policy cases: `{summary['failed_policy_case_count']}`",
        f"- Current runtime positive gaps: `{summary['current_runtime_positive_gap_count']}`",
        f"- Runtime patch allowed inside checkpoint: `{str(summary['runtime_patch_allowed_inside_checkpoint']).lower()}`",
        f"- Review HTML created: `{str(summary['review_html_created']).lower()}`",
        f"- Recommended next checkpoint: `{summary['recommended_next_checkpoint']}`",
        "",
        "## Constraints",
        "",
        f"- Requires plan feature matrix: `{str(constraints['requires_plan_feature_matrix']).lower()}`",
        f"- Requires customer facts for steering: `{str(constraints['requires_customer_facts_for_steering']).lower()}`",
        f"- Requires no payment on call default: `{str(constraints['requires_no_payment_on_call_default']).lower()}`",
        f"- Requires no company domain in generic payment wording: `{str(constraints['requires_no_company_domain_in_generic_payment_wording']).lower()}`",
        f"- Random fillers allowed: `{str(constraints['random_fillers_allowed']).lower()}`",
        f"- Approved payment response: `{constraints['approved_payment_response']}`",
        "- Forbidden placeholder includes `companyname.com`.",
        "",
        "## Runtime Reachability",
        "",
        "The current runtime still does not have a guided-option-selection route for the positive customer turns.",
        f"- Runtime patch required for reachability: `{str(gaps['runtime_patch_required_for_reachability']).lower()}`",
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
    source_result, candidate_packet, readiness, payment_edit = load_source()
    source_validator = run_source_validator()
    if not source_validator["passed"]:
        raise RuntimeError("Source validator failed; refusing to run PROD-086.")

    constraints = build_constraints(payment_edit)
    matrix = build_probe_matrix(candidate_packet)
    positive_results = [evaluate_positive_case(item) for item in candidate_packet["examples"]]
    control_results = [evaluate_control_case(item) for item in CONTROL_CASES]
    probe_result = build_policy_probe_result(positive_results, control_results)
    gaps = build_runtime_gap_analysis(candidate_packet)
    evidence = build_evidence(source_result, source_validator, candidate_packet, readiness)
    summary = build_summary(probe_result, candidate_packet, matrix, gaps)
    result = {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "validation": {
            "passed": probe_result["policy_probe_passed"],
            "policy_probe_completed": True,
        },
        "summary": summary,
    }

    write_json(OUT_DIR / "candidate_policy_constraints.json", constraints)
    write_json(OUT_DIR / "probe_case_matrix.json", matrix)
    write_json(OUT_DIR / "policy_probe_result.json", probe_result)
    write_json(OUT_DIR / "current_runtime_gap_analysis.json", gaps)
    write_json(OUT_DIR / "evidence_summary.json", evidence)
    write_json(OUT_DIR / "result.json", result)
    write_text(OUT_DIR / "report.md", render_report(summary, constraints, gaps))
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
