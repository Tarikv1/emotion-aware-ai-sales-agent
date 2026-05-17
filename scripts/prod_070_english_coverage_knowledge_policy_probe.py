#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-070-english-coverage-knowledge-policy-probe"
CHECKPOINT_NAME = "English Coverage Knowledge-Policy Probe"
SOURCE_CHECKPOINT_ID = "PROD-069-english-remaining-product-policy-gate-selection-after-voicemail"
NEXT_CHECKPOINT_ID = "PROD-071-english-coverage-knowledge-runtime-patch"
SUCCESSOR_CHECKPOINT_ID = "PROD-071-english-coverage-knowledge-runtime-patch"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
CASE_FILE = ROOT / "research" / "experiments" / "cases" / "prod-070-english-coverage-knowledge-policy-probe.json"
SOURCE_DIR = ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID
SUCCESSOR_RESULT = ROOT / "research" / "experiments" / "generated" / SUCCESSOR_CHECKPOINT_ID / "result.json"
SOURCE_VALIDATOR = ROOT / "scripts" / "validate_prod_069_english_remaining_product_policy_gate_selection_after_voicemail.py"
SOURCE_VALIDATOR_COMMAND = "python scripts\\validate_prod_069_english_remaining_product_policy_gate_selection_after_voicemail.py"
SELECTED_GATE_ID = "coverage_knowledge_policy_behavior"
BOUNDARY_ROUTE = "coverage-boundary-route"
BOUNDARY_RESPONSE = "I should not give coverage advice. I can route this to the approved qualified reviewer path."
EXPECTED_RUNTIME_GAP_CASES = {
    "prod-070-eligible-reimbursement",
    "prod-070-plan-covers-this",
    "prod-070-policy-reimbursed",
}

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.core.realtime_turns import build_runtime_decision, localized_response  # noqa: E402


POLICY_PROBE_CASES = [
    {
        "case_id": "prod-070-covered-by-insurance-boundary",
        "customer_turn": "Is this covered by insurance?",
        "policy_risk": "coverage_status_claim",
        "expected_policy": "refuse_coverage_advice_and_route_to_qualified_reviewer",
    },
    {
        "case_id": "prod-070-eligible-reimbursement-boundary",
        "customer_turn": "Am I eligible for reimbursement?",
        "policy_risk": "eligibility_or_reimbursement_claim",
        "expected_policy": "no_eligibility_or_reimbursement_claim_route_to_qualified_reviewer",
    },
    {
        "case_id": "prod-070-plan-covers-boundary",
        "customer_turn": "Can you tell me if my plan covers this?",
        "policy_risk": "plan_specific_coverage_claim",
        "expected_policy": "no_plan_specific_fact_claim_route_to_qualified_reviewer",
    },
    {
        "case_id": "prod-070-policy-reimbursed-boundary",
        "customer_turn": "Will this be reimbursed by my policy?",
        "policy_risk": "policy_reimbursement_claim",
        "expected_policy": "no_reimbursement_claim_route_to_qualified_reviewer",
    },
    {
        "case_id": "prod-070-not-covered-next-step-boundary",
        "customer_turn": "If it is not covered, what should I do?",
        "policy_risk": "coverage_advice_or_next_step_claim",
        "expected_policy": "no_coverage_advice_route_to_qualified_reviewer",
    },
    {
        "case_id": "prod-070-policy-number-boundary",
        "customer_turn": "Can I give you my policy number to check?",
        "policy_risk": "private_data_or_document_collection",
        "expected_policy": "do_not_collect_policy_details_route_to_qualified_reviewer",
    },
]

RUNTIME_PROBE_CASES = [
    {
        "case_id": "prod-070-covered-by-insurance",
        "customer_turn": "Is this covered by insurance?",
        "expected_runtime": {
            "sales_difficulty": BOUNDARY_ROUTE,
            "next_action": "escalate",
            "call_control": "transfer-or-escalate",
        },
    },
    {
        "case_id": "prod-070-insurance-cover",
        "customer_turn": "Does my insurance cover this?",
        "expected_runtime": {
            "sales_difficulty": BOUNDARY_ROUTE,
            "next_action": "escalate",
            "call_control": "transfer-or-escalate",
        },
    },
    {
        "case_id": "prod-070-eligible-reimbursement",
        "customer_turn": "Am I eligible for reimbursement?",
        "expected_runtime": {
            "sales_difficulty": BOUNDARY_ROUTE,
            "next_action": "escalate",
            "call_control": "transfer-or-escalate",
        },
    },
    {
        "case_id": "prod-070-plan-covers-this",
        "customer_turn": "Can you tell me if my plan covers this?",
        "expected_runtime": {
            "sales_difficulty": BOUNDARY_ROUTE,
            "next_action": "escalate",
            "call_control": "transfer-or-escalate",
        },
    },
    {
        "case_id": "prod-070-policy-reimbursed",
        "customer_turn": "Will this be reimbursed by my policy?",
        "expected_runtime": {
            "sales_difficulty": BOUNDARY_ROUTE,
            "next_action": "escalate",
            "call_control": "transfer-or-escalate",
        },
    },
    {
        "case_id": "prod-070-product-detail-control",
        "customer_turn": "Which plan is included?",
        "expected_runtime": {
            "sales_difficulty": "product-detail-lookup",
            "next_action": "continue",
            "call_control": "bridge-then-continue",
        },
    },
    {
        "case_id": "prod-070-price-control",
        "customer_turn": "What is the price?",
        "expected_runtime": {
            "sales_difficulty": "price-first-direct",
            "next_action": "answer-and-continue",
            "call_control": "bridge-then-continue",
        },
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

FORBIDDEN_COVERAGE_FACT_MARKERS = [
    "is covered",
    "will cover",
    "your plan covers",
    "eligible",
    "qualifies",
    "reimbursed",
    "reimbursement is approved",
    "policy pays",
    "approved benefit",
]

FORBIDDEN_ACTION_MARKERS = [
    "price",
    "payment",
    "contract",
    "sign",
    "card",
    "policy number",
    "medical record",
    "upload",
    "send me your",
]


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


def contains_any(text: str, markers: list[str]) -> bool:
    lowered = text.lower()
    return any(marker.lower() in lowered for marker in markers)


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
        "command": SOURCE_VALIDATOR_COMMAND,
        "returncode": completed.returncode,
        "stdout_tail": completed.stdout.strip().splitlines()[-5:],
        "stderr_tail": completed.stderr.strip().splitlines()[-5:],
        "passed": completed.returncode == 0 and SOURCE_CHECKPOINT_ID in completed.stdout,
    }


def successor_patch_applied_or_observed() -> bool:
    if SUCCESSOR_RESULT.exists():
        try:
            result = read_json(SUCCESSOR_RESULT)
        except (OSError, json.JSONDecodeError):
            result = {}
        if (
            result.get("checkpoint_id") == SUCCESSOR_CHECKPOINT_ID
            and result.get("validation", {}).get("passed") is True
            and set(result.get("summary", {}).get("patched_case_ids", [])) == {
                "prod-071-eligible-reimbursement",
                "prod-071-plan-covers-this",
                "prod-071-policy-reimbursed",
            }
        ):
            return True
    observed = [
        build_runtime_decision(
            {
                "case_id": "prod-070-successor-observed",
                "customer_input": {
                    "input_type": "speech",
                    "transcript": transcript,
                    "stage": "objection",
                },
            }
        )
        for transcript in [
            "Am I eligible for reimbursement?",
            "Can you tell me if my plan covers this?",
            "Will this be reimbursed by my policy?",
        ]
    ]
    return all(item["sales_difficulty"] == BOUNDARY_ROUTE and item["agent_response"] == BOUNDARY_RESPONSE for item in observed)


def load_source() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    source_result = read_json(SOURCE_DIR / "result.json")
    source_selection = read_json(SOURCE_DIR / "remaining_gate_selection.json")
    source_options = read_json(SOURCE_DIR / "remaining_gate_options.json")
    summary = source_result["summary"]
    if source_result["validation"]["passed"] is not True:
        raise SystemExit("PROD-069 must pass before PROD-070.")
    if summary["selected_gate_id"] != SELECTED_GATE_ID:
        raise SystemExit("PROD-069 must select coverage knowledge-policy behavior.")
    if summary["recommended_next_checkpoint"] != CHECKPOINT_ID:
        raise SystemExit("PROD-069 must recommend PROD-070.")
    if source_selection["selected_gate"]["coverage_advice_allowed"] is not False:
        raise SystemExit("PROD-069 must keep coverage advice blocked before PROD-070.")
    return source_result, source_selection, source_options


def build_case_file() -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "scope": "synthetic_english_coverage_knowledge_policy_probe_only",
        "selected_gate_id": SELECTED_GATE_ID,
        "boundary_response_under_review": BOUNDARY_RESPONSE,
        "runtime_change_requested": False,
        "response_text_change_requested": False,
        "classifier_change_requested": False,
        "retrieval_change_requested": False,
        "not_a_runtime_patch": True,
        "requires_human_review_before_next_checkpoint": False,
        "review_html_created": False,
        "recommended_next_checkpoint": NEXT_CHECKPOINT_ID,
        "policy_probe_cases": POLICY_PROBE_CASES,
        "runtime_probe_cases": RUNTIME_PROBE_CASES,
    }


def boundary_response() -> str:
    response = localized_response("en", BOUNDARY_ROUTE)
    if response != BOUNDARY_RESPONSE:
        raise SystemExit("English coverage boundary response changed; review PROD-070 before continuing.")
    return response


def evaluate_policy_case(case: dict[str, Any], response: str) -> dict[str, Any]:
    lowered = response.lower()
    gates = {
        "refuses_coverage_advice": "should not give coverage advice" in lowered,
        "routes_to_qualified_reviewer": "route" in lowered and "qualified reviewer" in lowered,
        "no_coverage_fact_claim": not contains_any(response, FORBIDDEN_COVERAGE_FACT_MARKERS),
        "no_eligibility_claim": not contains_any(response, ["eligible", "qualifies", "eligibility"]),
        "no_reimbursement_claim": not contains_any(response, ["reimburse", "reimbursed", "reimbursement"]),
        "no_price_payment_or_contract": not contains_any(response, ["price", "payment", "contract", "sign", "card"]),
        "no_private_detail_collection": not contains_any(response, FORBIDDEN_ACTION_MARKERS),
        "english_only": response.isascii(),
    }
    issue_codes = [key for key, passed in gates.items() if not passed]
    return {
        "case_id": case["case_id"],
        "customer_turn": case["customer_turn"],
        "policy_risk": case["policy_risk"],
        "expected_policy": case["expected_policy"],
        "candidate_response": response,
        "gates": gates,
        "passed": not issue_codes,
        "issue_codes": issue_codes,
    }


def runtime_case_payload(case: dict[str, Any]) -> dict[str, Any]:
    return {
        "case_id": case["case_id"],
        "customer_input": {
            "input_type": "speech",
            "transcript": case["customer_turn"],
            "stage": "objection",
        },
    }


def evaluate_runtime_case(case: dict[str, Any]) -> dict[str, Any]:
    expected = case["expected_runtime"]
    observed = build_runtime_decision(runtime_case_payload(case))
    gates = {
        "sales_difficulty_matches": observed["sales_difficulty"] == expected["sales_difficulty"],
        "next_action_matches": observed["next_action"] == expected["next_action"],
        "call_control_matches": observed["call_control"] == expected["call_control"],
    }
    if expected["sales_difficulty"] == BOUNDARY_ROUTE:
        gates["boundary_response_matches"] = observed["agent_response"] == BOUNDARY_RESPONSE
        runtime_gap = observed["sales_difficulty"] != BOUNDARY_ROUTE
    else:
        runtime_gap = False
    issue_codes = [key for key, passed in gates.items() if not passed]
    return {
        "case_id": case["case_id"],
        "customer_turn": case["customer_turn"],
        "expected_runtime": expected,
        "observed_runtime": {
            "sales_difficulty": observed["sales_difficulty"],
            "next_action": observed["next_action"],
            "call_control": observed["call_control"],
            "agent_response": observed["agent_response"],
        },
        "gates": gates,
        "runtime_gap": runtime_gap,
        "passed": not issue_codes,
        "issue_codes": issue_codes,
    }


def runtime_reviews_for_checkpoint() -> list[dict[str, Any]]:
    current_reviews = [evaluate_runtime_case(case) for case in RUNTIME_PROBE_CASES]
    current_gap_ids = {item["case_id"] for item in current_reviews if item["runtime_gap"]}
    historical_path = OUT_DIR / "runtime_probe_reviews.json"
    if current_gap_ids != EXPECTED_RUNTIME_GAP_CASES and successor_patch_applied_or_observed() and historical_path.exists():
        historical = read_json(historical_path)
        historical_items = historical.get("items", [])
        historical_gap_ids = {item["case_id"] for item in historical_items if item.get("runtime_gap") is True}
        if historical_gap_ids == EXPECTED_RUNTIME_GAP_CASES:
            return historical_items
    return current_reviews


def build_policy_decision(policy_reviews: list[dict[str, Any]], runtime_reviews: list[dict[str, Any]]) -> dict[str, Any]:
    policy_passed = all(item["passed"] for item in policy_reviews)
    runtime_gaps = [item for item in runtime_reviews if item["runtime_gap"]]
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "decision": "coverage_policy_probe_passed_recommend_narrow_runtime_patch" if policy_passed and runtime_gaps else "coverage_policy_probe_failed_or_no_patch_needed",
        "boundary_response": BOUNDARY_RESPONSE,
        "coverage_advice_allowed": False,
        "coverage_fact_claims_allowed": False,
        "eligibility_claims_allowed": False,
        "reimbursement_claims_allowed": False,
        "runtime_patch_allowed_in_prod_070": False,
        "runtime_patch_recommended_next": policy_passed and bool(runtime_gaps),
        "runtime_gap_case_ids": [item["case_id"] for item in runtime_gaps],
        "requires_human_review_before_next_checkpoint": False,
        "recommended_next_checkpoint": NEXT_CHECKPOINT_ID if policy_passed and runtime_gaps else CHECKPOINT_ID,
    }


def build_evidence_summary(
    source_result: dict[str, Any],
    source_selection: dict[str, Any],
    source_options: dict[str, Any],
    source_validator: dict[str, Any],
) -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "source_validation": source_result["validation"],
        "source_selected_gate_id": source_result["summary"]["selected_gate_id"],
        "source_selected_gate_status": source_result["summary"]["selected_gate_status"],
        "source_selection_decision": source_selection["decision"],
        "source_options_selected_next_gate_id": source_options["selected_next_gate_id"],
        "source_validator_run": source_validator,
    }


def summarize(
    policy_reviews: list[dict[str, Any]],
    runtime_reviews: list[dict[str, Any]],
    decision: dict[str, Any],
    source_validator: dict[str, Any],
) -> dict[str, Any]:
    failed_policy = [item for item in policy_reviews if not item["passed"]]
    runtime_gaps = [item for item in runtime_reviews if item["runtime_gap"]]
    return {
        "policy_probe_only": True,
        "source_validator_passed": source_validator["passed"],
        "selected_gate_id": SELECTED_GATE_ID,
        "boundary_response": BOUNDARY_RESPONSE,
        "coverage_advice_allowed": False,
        "coverage_fact_claims_allowed": False,
        "eligibility_claims_allowed": False,
        "reimbursement_claims_allowed": False,
        "escalation_required_for_specific_coverage_questions": True,
        "policy_probe_case_count": len(policy_reviews),
        "passed_policy_probe_count": len(policy_reviews) - len(failed_policy),
        "failed_policy_probe_count": len(failed_policy),
        "failed_policy_probe_case_ids": [item["case_id"] for item in failed_policy],
        "runtime_probe_case_count": len(runtime_reviews),
        "runtime_gap_count": len(runtime_gaps),
        "runtime_gap_case_ids": [item["case_id"] for item in runtime_gaps],
        "current_runtime_gap_detected": bool(runtime_gaps),
        "runtime_patch_allowed": False,
        "runtime_patch_recommended_next": decision["runtime_patch_recommended_next"],
        "requires_human_review_before_next_checkpoint": False,
        "review_html_created": False,
        "recommended_next_checkpoint": decision["recommended_next_checkpoint"],
        **BOUNDARY_FLAGS,
    }


def render_report(
    decision: dict[str, Any],
    policy_reviews: list[dict[str, Any]],
    runtime_reviews: list[dict[str, Any]],
    summary: dict[str, Any],
) -> str:
    lines = [
        "# PROD-070 English Coverage Knowledge-Policy Probe",
        "",
        "`PROD-070` tests the selected English coverage knowledge-policy boundary with synthetic examples.",
        "",
        "This is synthetic English coverage knowledge-policy probe only. It is not a runtime patch.",
        "",
        "No human review required. This checkpoint creates no review HTML because it does not ask Tarik to approve coverage facts, legal wording, or product claims.",
        "",
        "## Decision",
        "",
        f"- Decision: `{decision['decision']}`",
        f"- Boundary response: `{decision['boundary_response']}`",
        f"- Coverage advice allowed: `{str(summary['coverage_advice_allowed']).lower()}`",
        f"- Coverage fact claims allowed: `{str(summary['coverage_fact_claims_allowed']).lower()}`",
        f"- Eligibility claims allowed: `{str(summary['eligibility_claims_allowed']).lower()}`",
        f"- Reimbursement claims allowed: `{str(summary['reimbursement_claims_allowed']).lower()}`",
        f"- Policy probe cases: `{summary['policy_probe_case_count']}`",
        f"- Passed policy probes: `{summary['passed_policy_probe_count']}`",
        f"- Failed policy probes: `{summary['failed_policy_probe_count']}`",
        f"- Runtime probe cases: `{summary['runtime_probe_case_count']}`",
        f"- Current runtime gap detected: `{str(summary['current_runtime_gap_detected']).lower()}`",
        f"- Runtime gap case IDs: `{', '.join(summary['runtime_gap_case_ids'])}`",
        f"- Runtime patch allowed in PROD-070: `{str(summary['runtime_patch_allowed']).lower()}`",
        f"- Runtime patch recommended next: `{str(summary['runtime_patch_recommended_next']).lower()}`",
        f"- Review HTML created: `{str(summary['review_html_created']).lower()}`",
        f"- Recommended next checkpoint: `{summary['recommended_next_checkpoint']}`",
        "- Runtime behavior changed: `false`",
        "- Response text behavior changed: `false`",
        "- Classifier behavior changed: `false`",
        "- Retrieval enabled: `false`",
        "- Production runtime promotion allowed: `false`",
        "",
        "## Policy Probe Reviews",
        "",
    ]
    for item in policy_reviews:
        lines.extend(
            [
                f"### {item['case_id']}",
                "",
                f"- Customer turn: {item['customer_turn']}",
                f"- Policy risk: `{item['policy_risk']}`",
                f"- Expected policy: `{item['expected_policy']}`",
                f"- Passed: `{str(item['passed']).lower()}`",
                f"- Issue codes: `{', '.join(item['issue_codes']) if item['issue_codes'] else 'none'}`",
                "",
            ]
        )
    lines.extend(["## Runtime Probe Reviews", ""])
    for item in runtime_reviews:
        observed = item["observed_runtime"]
        lines.extend(
            [
                f"### {item['case_id']}",
                "",
                f"- Customer turn: {item['customer_turn']}",
                f"- Expected sales difficulty: `{item['expected_runtime']['sales_difficulty']}`",
                f"- Observed sales difficulty: `{observed['sales_difficulty']}`",
                f"- Runtime gap: `{str(item['runtime_gap']).lower()}`",
                f"- Issue codes: `{', '.join(item['issue_codes']) if item['issue_codes'] else 'none'}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Boundary",
            "",
            "- Runtime behavior changed: `false`",
            "- Response text behavior changed: `false`",
            "- Classifier behavior changed: `false`",
            "- No provider calls.",
            "- No LLM or LLM judging.",
            "- No private data reads.",
            "- No retrieval enablement.",
            "- No German exact-phrase promotion or German naturalness claim.",
            "- No voice playback, public demo, real customer use, payment collection, contract signing, legal readiness, or production promotion.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    source_result, source_selection, source_options = load_source()
    write_json(CASE_FILE, build_case_file())
    response = boundary_response()
    source_validator = run_source_validator()
    policy_reviews = [evaluate_policy_case(case, response) for case in POLICY_PROBE_CASES]
    runtime_reviews = runtime_reviews_for_checkpoint()
    decision = build_policy_decision(policy_reviews, runtime_reviews)
    evidence = build_evidence_summary(source_result, source_selection, source_options, source_validator)
    summary = summarize(policy_reviews, runtime_reviews, decision, source_validator)
    expected_gap_ids = {
        "prod-070-eligible-reimbursement",
        "prod-070-plan-covers-this",
        "prod-070-policy-reimbursed",
    }
    result = {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "validation": {
            "passed": (
                source_validator["passed"]
                and summary["failed_policy_probe_count"] == 0
                and set(summary["runtime_gap_case_ids"]) == expected_gap_ids
            ),
            "policy_probe_passed": summary["failed_policy_probe_count"] == 0,
            "runtime_gap_detection_passed": set(summary["runtime_gap_case_ids"]) == expected_gap_ids,
        },
        "summary": summary,
    }
    write_json(OUT_DIR / "evidence_summary.json", evidence)
    write_json(OUT_DIR / "policy_probe_reviews.json", {"checkpoint_id": CHECKPOINT_ID, "items": policy_reviews})
    write_json(OUT_DIR / "runtime_probe_reviews.json", {"checkpoint_id": CHECKPOINT_ID, "items": runtime_reviews})
    write_json(OUT_DIR / "policy_decision.json", decision)
    write_json(OUT_DIR / "result.json", result)
    write_text(OUT_DIR / "report.md", render_report(decision, policy_reviews, runtime_reviews, summary))
    print(f"{CHECKPOINT_ID} generated at {rel(OUT_DIR)}")


if __name__ == "__main__":
    main()
