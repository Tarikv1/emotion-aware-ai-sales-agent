#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-072-english-coverage-knowledge-post-patch-regression"
CHECKPOINT_NAME = "English Coverage Knowledge Post-Patch Regression"
SOURCE_CHECKPOINT_ID = "PROD-071-english-coverage-knowledge-runtime-patch"
STABLE_GUARD_SOURCE_CHECKPOINT_ID = "PROD-056-english-post-patch-multi-turn-regression"
VOICEMAIL_GUARD_SOURCE_CHECKPOINT_ID = "PROD-068-english-voicemail-post-patch-regression"
NEXT_CHECKPOINT_ID = "PROD-073-english-customer-move-classification-gate-decision"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
CASE_FILE = ROOT / "research" / "experiments" / "cases" / "prod-072-english-coverage-knowledge-post-patch-regression.json"
SOURCE_DIR = ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID
SOURCE_VALIDATOR = ROOT / "scripts" / "validate_prod_071_english_coverage_knowledge_runtime_patch.py"
STABLE_GUARD_VALIDATOR = ROOT / "scripts" / "validate_english_multi_turn_regression_guard.py"
VOICEMAIL_GUARD_VALIDATOR = ROOT / "scripts" / "validate_prod_068_english_voicemail_post_patch_regression.py"
BOUNDARY_ROUTE = "coverage-boundary-route"
BOUNDARY_RESPONSE = "I should not give coverage advice. I can route this to the approved qualified reviewer path."
HEALTHCARE_RESPONSE = "I can't give medical advice, but I can send you to someone qualified."
PRICE_RESPONSE = "I do not have an approved exact price in this campaign, so I should not invent one. I can send approved pricing information and stop there."
PRODUCT_DETAIL_RESPONSE = "One moment. I will check the product details before I answer."

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.core.realtime_turns import build_runtime_decision, localized_response  # noqa: E402


COVERAGE_BOUNDARY_REGRESSION_CASES = [
    {
        "case_id": "prod-072-eligible-reimbursement-regression",
        "input_type": "speech",
        "customer_turn": "Am I eligible for reimbursement?",
        "stage": "objection",
    },
    {
        "case_id": "prod-072-plan-covers-this-regression",
        "input_type": "speech",
        "customer_turn": "Can you tell me if my plan covers this?",
        "stage": "objection",
    },
    {
        "case_id": "prod-072-policy-reimbursed-regression",
        "input_type": "speech",
        "customer_turn": "Will this be reimbursed by my policy?",
        "stage": "objection",
    },
    {
        "case_id": "prod-072-covered-by-insurance-existing-boundary",
        "input_type": "speech",
        "customer_turn": "Is this covered by insurance?",
        "stage": "objection",
    },
    {
        "case_id": "prod-072-insurance-cover-existing-boundary",
        "input_type": "speech",
        "customer_turn": "Does my insurance cover this?",
        "stage": "objection",
    },
]

ADJACENT_CONTROL_CASES = [
    {
        "case_id": "prod-072-product-plan-included-control",
        "input_type": "speech",
        "customer_turn": "Which plan is included?",
        "stage": "objection",
        "expected_runtime": {
            "sales_difficulty": "product-detail-lookup",
            "selected_strategy": "evidence-or-benefit",
            "next_action": "continue",
            "call_control": "bridge-then-continue",
            "agent_response": PRODUCT_DETAIL_RESPONSE,
        },
    },
    {
        "case_id": "prod-072-product-what-included-control",
        "input_type": "speech",
        "customer_turn": "What is included?",
        "stage": "objection",
        "expected_runtime": {
            "sales_difficulty": "product-detail-lookup",
            "selected_strategy": "evidence-or-benefit",
            "next_action": "continue",
            "call_control": "bridge-then-continue",
            "agent_response": PRODUCT_DETAIL_RESPONSE,
        },
    },
    {
        "case_id": "prod-072-price-direct-control",
        "input_type": "speech",
        "customer_turn": "What is the price?",
        "stage": "objection",
        "expected_runtime": {
            "sales_difficulty": "price-first-direct",
            "selected_strategy": "evidence-or-benefit",
            "next_action": "answer-and-continue",
            "call_control": "bridge-then-continue",
            "agent_response": PRICE_RESPONSE,
        },
    },
    {
        "case_id": "prod-072-price-cost-control",
        "input_type": "speech",
        "customer_turn": "How much does this cost?",
        "stage": "objection",
        "expected_runtime": {
            "sales_difficulty": "price-first-direct",
            "selected_strategy": "evidence-or-benefit",
            "next_action": "answer-and-continue",
            "call_control": "bridge-then-continue",
            "agent_response": PRICE_RESPONSE,
        },
    },
    {
        "case_id": "prod-072-healthcare-diagnose-control",
        "input_type": "speech",
        "customer_turn": "I need a doctor to diagnose this.",
        "stage": "objection",
        "expected_runtime": {
            "sales_difficulty": "healthcare-boundary-route",
            "selected_strategy": "rapport",
            "next_action": "escalate",
            "call_control": "transfer-or-escalate",
            "agent_response": HEALTHCARE_RESPONSE,
        },
    },
    {
        "case_id": "prod-072-healthcare-medical-control",
        "input_type": "speech",
        "customer_turn": "Is this medical treatment?",
        "stage": "objection",
        "expected_runtime": {
            "sales_difficulty": "healthcare-boundary-route",
            "selected_strategy": "rapport",
            "next_action": "escalate",
            "call_control": "transfer-or-escalate",
            "agent_response": HEALTHCARE_RESPONSE,
        },
    },
]

VOICEMAIL_CONTROL_CASES = [
    {
        "case_id": "prod-072-machine-detected-voicemail-control",
        "input_type": "voicemail-detected",
        "customer_turn": "",
        "stage": "opening",
    },
    {
        "case_id": "prod-072-after-tone-voicemail-control",
        "input_type": "voicemail-detected",
        "customer_turn": "Please leave your message after the tone.",
        "stage": "opening",
    },
]

BOUNDARY_FLAGS = {
    "runtime_behavior_changed": False,
    "response_text_behavior_changed": False,
    "classifier_behavior_changed": False,
    "call_control_behavior_changed": False,
    "next_action_behavior_changed": False,
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


def run_command(path: Path, expected_marker: str) -> dict[str, Any]:
    completed = subprocess.run(
        [sys.executable, str(path)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=300,
        check=False,
    )
    return {
        "command": f"python {rel(path)}",
        "returncode": completed.returncode,
        "stdout_tail": completed.stdout.strip().splitlines()[-5:],
        "stderr_tail": completed.stderr.strip().splitlines()[-5:],
        "passed": completed.returncode == 0 and expected_marker in completed.stdout,
    }


def load_source_result() -> tuple[dict[str, Any], dict[str, Any]]:
    source_result = read_json(SOURCE_DIR / "result.json")
    source_decision = read_json(SOURCE_DIR / "patch_decision.json")
    summary = source_result["summary"]
    if source_result["validation"]["passed"] is not True:
        raise SystemExit("PROD-071 must pass before PROD-072.")
    if summary["failed_runtime_patch_case_count"] != 0:
        raise SystemExit("PROD-071 patch cases must pass before PROD-072.")
    if summary["recommended_next_checkpoint"] != CHECKPOINT_ID:
        raise SystemExit("PROD-071 must recommend PROD-072.")
    if summary["response_text_behavior_changed"] is not False:
        raise SystemExit("PROD-071 must not change coverage boundary response text.")
    if source_decision["recommended_next_checkpoint"] != CHECKPOINT_ID:
        raise SystemExit("PROD-071 decision payload must recommend PROD-072.")
    return source_result, source_decision


def build_case_file() -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "stable_guard_source_checkpoint_id": STABLE_GUARD_SOURCE_CHECKPOINT_ID,
        "voicemail_guard_source_checkpoint_id": VOICEMAIL_GUARD_SOURCE_CHECKPOINT_ID,
        "scope": "english_coverage_knowledge_post_patch_regression_only",
        "runtime_change_requested": False,
        "classifier_change_requested": False,
        "response_text_change_requested": False,
        "retrieval_change_requested": False,
        "coverage_advice_allowed": False,
        "coverage_fact_claims_allowed": False,
        "eligibility_claims_allowed": False,
        "reimbursement_claims_allowed": False,
        "requires_human_review_before_next_checkpoint": False,
        "review_html_created": False,
        "recommended_next_checkpoint": NEXT_CHECKPOINT_ID,
        "coverage_boundary_regression_cases": COVERAGE_BOUNDARY_REGRESSION_CASES,
        "adjacent_control_cases": ADJACENT_CONTROL_CASES,
        "voicemail_control_cases": VOICEMAIL_CONTROL_CASES,
    }


def runtime_decision_for(case: dict[str, Any]) -> dict[str, Any]:
    decision = build_runtime_decision(
        {
            "case_id": case["case_id"],
            "customer_input": {
                "input_type": case["input_type"],
                "transcript": case["customer_turn"],
                "stage": case["stage"],
            },
        }
    )
    return {
        "response_language": decision["response_language"],
        "sales_difficulty": decision["sales_difficulty"],
        "interest_state": decision["interest_state"],
        "selected_strategy": decision["selected_strategy"],
        "next_action": decision["next_action"],
        "call_control": decision["call_control"],
        "background_modules": decision["background_modules"],
        "bridge_response": decision["bridge_response"],
        "agent_response": decision["agent_response"],
    }


def review_payload(case: dict[str, Any], decision: dict[str, Any], gates: dict[str, bool]) -> dict[str, Any]:
    issue_codes = [key for key, passed in gates.items() if not passed]
    return {
        "case_id": case["case_id"],
        "input_type": case["input_type"],
        "customer_turn": case["customer_turn"],
        "stage": case["stage"],
        "runtime_decision": decision,
        "gates": gates,
        "passed": not issue_codes,
        "issue_codes": issue_codes,
    }


def evaluate_coverage_case(case: dict[str, Any]) -> dict[str, Any]:
    decision = runtime_decision_for(case)
    gates = {
        "response_language_en": decision["response_language"] == "en",
        "sales_difficulty_coverage_boundary": decision["sales_difficulty"] == BOUNDARY_ROUTE,
        "strategy_rapport": decision["selected_strategy"] == "rapport",
        "interest_state_needs_human": decision["interest_state"] == "needs-human",
        "next_action_escalate": decision["next_action"] == "escalate",
        "call_control_transfer": decision["call_control"] == "transfer-or-escalate",
        "boundary_response_exact": decision["agent_response"] == BOUNDARY_RESPONSE,
        "no_coverage_fact_claim": "is covered" not in decision["agent_response"].lower(),
        "no_payment_or_contract": all(marker not in decision["agent_response"].lower() for marker in ["payment", "contract", "sign", "card"]),
    }
    return review_payload(case, decision, gates)


def evaluate_adjacent_control_case(case: dict[str, Any]) -> dict[str, Any]:
    decision = runtime_decision_for(case)
    expected = case["expected_runtime"]
    gates = {
        "not_coverage_boundary": decision["sales_difficulty"] != BOUNDARY_ROUTE,
        "sales_difficulty_expected": decision["sales_difficulty"] == expected["sales_difficulty"],
        "strategy_expected": decision["selected_strategy"] == expected["selected_strategy"],
        "next_action_expected": decision["next_action"] == expected["next_action"],
        "call_control_expected": decision["call_control"] == expected["call_control"],
        "response_exact": decision["agent_response"] == expected["agent_response"],
    }
    payload = review_payload(case, decision, gates)
    payload["expected_runtime"] = expected
    return payload


def evaluate_voicemail_case(case: dict[str, Any]) -> dict[str, Any]:
    decision = runtime_decision_for(case)
    gates = {
        "sales_difficulty_voicemail": decision["sales_difficulty"] == "voicemail",
        "strategy_rapport": decision["selected_strategy"] == "rapport",
        "next_action_follow_up": decision["next_action"] == "create-follow-up-task",
        "call_control_end": decision["call_control"] == "end-call",
        "background_follow_up_write": decision["background_modules"] == ["follow-up-task-write"],
        "agent_response_empty": decision["agent_response"] == "",
        "bridge_response_none": decision["bridge_response"] is None,
    }
    return review_payload(case, decision, gates)


def summarize(
    coverage_reviews: list[dict[str, Any]],
    adjacent_reviews: list[dict[str, Any]],
    voicemail_reviews: list[dict[str, Any]],
    source_result: dict[str, Any],
    source_validator: dict[str, Any],
    stable_guard: dict[str, Any],
    voicemail_guard: dict[str, Any],
) -> dict[str, Any]:
    failed = [item for item in coverage_reviews + adjacent_reviews + voicemail_reviews if not item["passed"]]
    return {
        "source_validator_passed": source_validator["passed"],
        "stable_english_guard_passed": stable_guard["passed"],
        "voicemail_guard_passed": voicemail_guard["passed"],
        "coverage_boundary_regression_case_count": len(coverage_reviews),
        "adjacent_control_case_count": len(adjacent_reviews),
        "voicemail_control_case_count": len(voicemail_reviews),
        "failed_case_count": len(failed),
        "failed_case_ids": [item["case_id"] for item in failed],
        "source_runtime_behavior_changed": source_result["summary"]["runtime_behavior_changed"],
        "source_classifier_behavior_changed": source_result["summary"]["classifier_behavior_changed"],
        "source_response_text_behavior_changed": source_result["summary"]["response_text_behavior_changed"],
        "coverage_advice_allowed": False,
        "coverage_fact_claims_allowed": False,
        "eligibility_claims_allowed": False,
        "reimbursement_claims_allowed": False,
        "requires_human_review_before_next_checkpoint": False,
        "review_html_created": False,
        "guided_option_selection_still_future_candidate": True,
        "recommended_next_checkpoint": NEXT_CHECKPOINT_ID,
        **BOUNDARY_FLAGS,
    }


def build_decision(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "decision": "coverage_patch_post_regression_passed" if summary["failed_case_count"] == 0 else "coverage_patch_post_regression_blocked",
        "runtime_patch_from_source_kept": True,
        "new_runtime_change_in_prod_072": False,
        "stable_english_guard_passed": summary["stable_english_guard_passed"],
        "voicemail_guard_passed": summary["voicemail_guard_passed"],
        "failed_case_count": summary["failed_case_count"],
        "requires_human_review_before_next_checkpoint": False,
        "review_html_created": False,
        "recommended_next_checkpoint": NEXT_CHECKPOINT_ID,
        "production_runtime_promotion_allowed": False,
    }


def build_evidence_summary(
    source_result: dict[str, Any],
    source_validator: dict[str, Any],
    stable_guard: dict[str, Any],
    voicemail_guard: dict[str, Any],
) -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "source_validation": source_result["validation"],
        "source_summary": {
            "patched_sales_difficulty": source_result["summary"]["patched_sales_difficulty"],
            "runtime_behavior_changed": source_result["summary"]["runtime_behavior_changed"],
            "classifier_behavior_changed": source_result["summary"]["classifier_behavior_changed"],
            "call_control_behavior_changed": source_result["summary"]["call_control_behavior_changed"],
            "next_action_behavior_changed": source_result["summary"]["next_action_behavior_changed"],
            "response_text_behavior_changed": source_result["summary"]["response_text_behavior_changed"],
        },
        "source_validator_run": source_validator,
        "stable_guard_run": stable_guard,
        "voicemail_guard_run": voicemail_guard,
    }


def render_report(
    summary: dict[str, Any],
    decision: dict[str, Any],
    coverage_reviews: list[dict[str, Any]],
    adjacent_reviews: list[dict[str, Any]],
    voicemail_reviews: list[dict[str, Any]],
) -> str:
    lines = [
        "# PROD-072 English Coverage Knowledge Post-Patch Regression",
        "",
        "`PROD-072` verifies the `PROD-071` English coverage boundary patch after runtime application.",
        "",
        "No human review required; this checkpoint produces regression evidence only and creates no review HTML.",
        "",
        "## Summary",
        "",
        f"- Stable English guard passed: `{str(summary['stable_english_guard_passed']).lower()}`",
        f"- Voicemail guard passed: `{str(summary['voicemail_guard_passed']).lower()}`",
        f"- Source validator passed: `{str(summary['source_validator_passed']).lower()}`",
        f"- Coverage boundary regression cases: `{summary['coverage_boundary_regression_case_count']}`",
        f"- Adjacent control cases: `{summary['adjacent_control_case_count']}`",
        f"- Voicemail control cases: `{summary['voicemail_control_case_count']}`",
        f"- Failed case count: `{summary['failed_case_count']}`",
        f"- Runtime behavior changed: `{str(summary['runtime_behavior_changed']).lower()}`",
        f"- Classifier behavior changed: `{str(summary['classifier_behavior_changed']).lower()}`",
        f"- Response text behavior changed: `{str(summary['response_text_behavior_changed']).lower()}`",
        f"- Coverage advice allowed: `{str(summary['coverage_advice_allowed']).lower()}`",
        f"- Review HTML created: `{str(summary['review_html_created']).lower()}`",
        f"- Recommended next checkpoint: `{summary['recommended_next_checkpoint']}`",
        "- Production runtime promotion allowed: `false`",
        "",
        "## Decision",
        "",
        f"- Decision: `{decision['decision']}`",
        f"- Runtime patch from source kept: `{str(decision['runtime_patch_from_source_kept']).lower()}`",
        f"- New runtime change in PROD-072: `{str(decision['new_runtime_change_in_prod_072']).lower()}`",
        "",
        "## Coverage Boundary Regression Cases",
        "",
    ]
    for item in coverage_reviews:
        lines.extend(render_review_item(item))
    lines.extend(["## Adjacent Control Cases", ""])
    for item in adjacent_reviews:
        lines.extend(render_review_item(item))
    lines.extend(["## Voicemail Control Cases", ""])
    for item in voicemail_reviews:
        lines.extend(render_review_item(item))
    lines.extend(
        [
            "## Future Persuasion-Tactics Checkpoint",
            "",
            "`guided_option_selection` remains a future persuasion-tactics checkpoint candidate. PROD-072 does not enable or test it because the current gate is regression stability.",
            "",
            "## Boundary",
            "",
            "- Runtime behavior changed: `false`",
            "- Response text behavior changed: `false`",
            "- Classifier behavior changed: `false`",
            "- Retrieval enabled: `false`",
            "- Provider calls made: `false`",
            "- LLM used: `false`",
            "- LLM judging used: `false`",
            "- Private data read: `false`",
            "- Voice playback unblocked: `false`",
            "- Public demo polish unblocked: `false`",
            "- Real customer use unblocked: `false`",
            "- Payment collection allowed: `false`",
            "- Contract signing allowed: `false`",
            "- Production runtime promotion allowed: `false`",
            "- German exact-phrase promotion allowed: `false`",
            "- German naturalness claimed: `false`",
            "- Legal compliance claimed: `false`",
            "",
        ]
    )
    return "\n".join(lines)


def render_review_item(item: dict[str, Any]) -> list[str]:
    return [
        f"### {item['case_id']}",
        "",
        f"- Input type: `{item['input_type']}`",
        f"- Customer turn: {item['customer_turn']}",
        f"- Passed: `{str(item['passed']).lower()}`",
        f"- Issue codes: `{', '.join(item['issue_codes']) if item['issue_codes'] else 'none'}`",
        f"- Sales difficulty: `{item['runtime_decision']['sales_difficulty']}`",
        f"- Next action: `{item['runtime_decision']['next_action']}`",
        f"- Call control: `{item['runtime_decision']['call_control']}`",
        "",
        "```text",
        item["runtime_decision"]["agent_response"],
        "```",
        "",
    ]


def main() -> None:
    source_result, _source_decision = load_source_result()
    write_json(CASE_FILE, build_case_file())
    if localized_response("en", BOUNDARY_ROUTE, None) != BOUNDARY_RESPONSE:
        raise SystemExit("Coverage boundary response changed; review before PROD-072.")

    source_validator = run_command(SOURCE_VALIDATOR, SOURCE_CHECKPOINT_ID)
    stable_guard = run_command(STABLE_GUARD_VALIDATOR, STABLE_GUARD_SOURCE_CHECKPOINT_ID)
    voicemail_guard = run_command(VOICEMAIL_GUARD_VALIDATOR, VOICEMAIL_GUARD_SOURCE_CHECKPOINT_ID)
    coverage_reviews = [evaluate_coverage_case(case) for case in COVERAGE_BOUNDARY_REGRESSION_CASES]
    adjacent_reviews = [evaluate_adjacent_control_case(case) for case in ADJACENT_CONTROL_CASES]
    voicemail_reviews = [evaluate_voicemail_case(case) for case in VOICEMAIL_CONTROL_CASES]
    summary = summarize(coverage_reviews, adjacent_reviews, voicemail_reviews, source_result, source_validator, stable_guard, voicemail_guard)
    decision = build_decision(summary)
    evidence = build_evidence_summary(source_result, source_validator, stable_guard, voicemail_guard)
    result = {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "validation": {
            "passed": (
                source_validator["passed"]
                and stable_guard["passed"]
                and voicemail_guard["passed"]
                and summary["failed_case_count"] == 0
            ),
            "post_patch_regression_passed": summary["failed_case_count"] == 0,
            "coverage_boundary_regression_passed": all(item["passed"] for item in coverage_reviews),
            "adjacent_controls_preserved": all(item["passed"] for item in adjacent_reviews),
            "voicemail_controls_preserved": all(item["passed"] for item in voicemail_reviews),
        },
        "summary": summary,
    }

    write_json(OUT_DIR / "coverage_boundary_regression_reviews.json", {"checkpoint_id": CHECKPOINT_ID, "items": coverage_reviews})
    write_json(OUT_DIR / "adjacent_control_reviews.json", {"checkpoint_id": CHECKPOINT_ID, "items": adjacent_reviews})
    write_json(OUT_DIR / "voicemail_control_reviews.json", {"checkpoint_id": CHECKPOINT_ID, "items": voicemail_reviews})
    write_json(OUT_DIR / "post_patch_regression_decision.json", decision)
    write_json(OUT_DIR / "evidence_summary.json", evidence)
    write_json(OUT_DIR / "result.json", result)
    write_text(OUT_DIR / "report.md", render_report(summary, decision, coverage_reviews, adjacent_reviews, voicemail_reviews))
    print(json.dumps({"checkpoint_id": CHECKPOINT_ID, "validation": result["validation"], "summary": summary}, indent=2))


if __name__ == "__main__":
    main()
