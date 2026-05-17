#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-071-english-coverage-knowledge-runtime-patch"
CHECKPOINT_NAME = "English Coverage Knowledge Runtime Patch"
SOURCE_CHECKPOINT_ID = "PROD-070-english-coverage-knowledge-policy-probe"
NEXT_CHECKPOINT_ID = "PROD-072-english-coverage-knowledge-post-patch-regression"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
CASE_FILE = ROOT / "research" / "experiments" / "cases" / "prod-071-english-coverage-knowledge-runtime-patch.json"
SOURCE_DIR = ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID
SOURCE_VALIDATOR = ROOT / "scripts" / "validate_prod_070_english_coverage_knowledge_policy_probe.py"
SOURCE_VALIDATOR_COMMAND = "python scripts\\validate_prod_070_english_coverage_knowledge_policy_probe.py"
BOUNDARY_ROUTE = "coverage-boundary-route"
BOUNDARY_RESPONSE = "I should not give coverage advice. I can route this to the approved qualified reviewer path."

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.core.realtime_turns import build_runtime_decision, localized_response  # noqa: E402


RUNTIME_PATCH_CASES = [
    {
        "case_id": "prod-071-eligible-reimbursement",
        "case_type": "patched_boundary_phrase",
        "customer_turn": "Am I eligible for reimbursement?",
        "expected_runtime": {
            "sales_difficulty": BOUNDARY_ROUTE,
            "selected_strategy": "rapport",
            "interest_state": "needs-human",
            "next_action": "escalate",
            "call_control": "transfer-or-escalate",
            "agent_response": BOUNDARY_RESPONSE,
        },
    },
    {
        "case_id": "prod-071-plan-covers-this",
        "case_type": "patched_boundary_phrase",
        "customer_turn": "Can you tell me if my plan covers this?",
        "expected_runtime": {
            "sales_difficulty": BOUNDARY_ROUTE,
            "selected_strategy": "rapport",
            "interest_state": "needs-human",
            "next_action": "escalate",
            "call_control": "transfer-or-escalate",
            "agent_response": BOUNDARY_RESPONSE,
        },
    },
    {
        "case_id": "prod-071-policy-reimbursed",
        "case_type": "patched_boundary_phrase",
        "customer_turn": "Will this be reimbursed by my policy?",
        "expected_runtime": {
            "sales_difficulty": BOUNDARY_ROUTE,
            "selected_strategy": "rapport",
            "interest_state": "needs-human",
            "next_action": "escalate",
            "call_control": "transfer-or-escalate",
            "agent_response": BOUNDARY_RESPONSE,
        },
    },
    {
        "case_id": "prod-071-product-detail-control",
        "case_type": "control",
        "customer_turn": "Which plan is included?",
        "expected_runtime": {
            "sales_difficulty": "product-detail-lookup",
            "next_action": "continue",
            "call_control": "bridge-then-continue",
        },
    },
    {
        "case_id": "prod-071-price-control",
        "case_type": "control",
        "customer_turn": "What is the price?",
        "expected_runtime": {
            "sales_difficulty": "price-first-direct",
            "next_action": "answer-and-continue",
            "call_control": "bridge-then-continue",
        },
    },
    {
        "case_id": "prod-071-healthcare-control",
        "case_type": "control",
        "customer_turn": "I need a doctor to diagnose this.",
        "expected_runtime": {
            "sales_difficulty": "healthcare-boundary-route",
            "next_action": "escalate",
            "call_control": "transfer-or-escalate",
        },
    },
]

FUTURE_PERSUASION_TACTIC_CANDIDATE = {
    "tactic_id": "guided_option_selection",
    "track": "future_persuasion_tactics_checkpoint",
    "description": "After fit and interest are established, present two real paid options with clear tradeoffs and let the customer choose.",
    "not_in_prod_071_scope": True,
    "runtime_enabled": False,
    "unlock_condition": "Open a dedicated persuasion-tactics checkpoint after coverage-boundary and post-patch regression work is stable.",
    "required_guardrails": [
        "only after fit or interest is established",
        "both options must be real and fairly described",
        "neither, not now, and explain the difference remain valid customer choices",
        "no fake urgency",
        "no pretending the customer already agreed",
    ],
}

BOUNDARY_FLAGS = {
    "response_text_behavior_changed": False,
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
        "command": SOURCE_VALIDATOR_COMMAND,
        "returncode": completed.returncode,
        "stdout_tail": completed.stdout.strip().splitlines()[-5:],
        "stderr_tail": completed.stderr.strip().splitlines()[-5:],
        "passed": completed.returncode == 0 and SOURCE_CHECKPOINT_ID in completed.stdout,
    }


def load_source() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    source_result = read_json(SOURCE_DIR / "result.json")
    policy_decision = read_json(SOURCE_DIR / "policy_decision.json")
    runtime_reviews = read_json(SOURCE_DIR / "runtime_probe_reviews.json")
    summary = source_result["summary"]
    if source_result["validation"]["passed"] is not True:
        raise SystemExit("PROD-070 must pass before PROD-071.")
    if summary["runtime_patch_recommended_next"] is not True:
        raise SystemExit("PROD-070 must recommend a runtime patch before PROD-071.")
    if summary["recommended_next_checkpoint"] != CHECKPOINT_ID:
        raise SystemExit("PROD-070 must recommend PROD-071.")
    if policy_decision["runtime_patch_allowed_in_prod_070"] is not False:
        raise SystemExit("PROD-070 must not apply the runtime patch itself.")
    return source_result, policy_decision, runtime_reviews


def build_case_file() -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "scope": "english_coverage_knowledge_classifier_reachability_patch_only",
        "runtime_path": "runtime/core/realtime_turns.py",
        "patched_sales_difficulty": BOUNDARY_ROUTE,
        "boundary_response": BOUNDARY_RESPONSE,
        "runtime_change_requested": True,
        "classifier_change_requested": True,
        "response_text_change_requested": False,
        "retrieval_change_requested": False,
        "coverage_advice_allowed": False,
        "coverage_fact_claims_allowed": False,
        "eligibility_claims_allowed": False,
        "reimbursement_claims_allowed": False,
        "requires_human_review_before_next_checkpoint": False,
        "review_html_created": False,
        "recommended_next_checkpoint": NEXT_CHECKPOINT_ID,
        "runtime_patch_cases": RUNTIME_PATCH_CASES,
        "future_persuasion_tactic_candidate": FUTURE_PERSUASION_TACTIC_CANDIDATE,
    }


def runtime_decision_for(case: dict[str, Any]) -> dict[str, Any]:
    decision = build_runtime_decision(
        {
            "case_id": case["case_id"],
            "customer_input": {
                "input_type": "speech",
                "transcript": case["customer_turn"],
                "stage": "objection",
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
        "agent_response": decision["agent_response"],
    }


def evaluate_runtime_case(case: dict[str, Any]) -> dict[str, Any]:
    observed = runtime_decision_for(case)
    expected = case["expected_runtime"]
    gates = {
        "sales_difficulty_matches": observed["sales_difficulty"] == expected["sales_difficulty"],
        "next_action_matches": observed["next_action"] == expected["next_action"],
        "call_control_matches": observed["call_control"] == expected["call_control"],
    }
    if case["case_type"] == "patched_boundary_phrase":
        gates.update(
            {
                "response_language_en": observed["response_language"] == "en",
                "strategy_rapport": observed["selected_strategy"] == expected["selected_strategy"],
                "interest_state_needs_human": observed["interest_state"] == expected["interest_state"],
                "boundary_response_matches": observed["agent_response"] == expected["agent_response"],
                "no_coverage_fact_claim": "is covered" not in observed["agent_response"].lower(),
                "no_payment_or_contract": all(marker not in observed["agent_response"].lower() for marker in ["payment", "contract", "sign", "card"]),
            }
        )
    issue_codes = [key for key, passed in gates.items() if not passed]
    return {
        "case_id": case["case_id"],
        "case_type": case["case_type"],
        "customer_turn": case["customer_turn"],
        "expected_runtime": expected,
        "observed_runtime": observed,
        "gates": gates,
        "passed": not issue_codes,
        "issue_codes": issue_codes,
    }


def build_patch_decision(reviews: list[dict[str, Any]]) -> dict[str, Any]:
    failed = [item for item in reviews if not item["passed"]]
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "decision": "english_coverage_knowledge_runtime_patch_applied",
        "runtime_path": "runtime/core/realtime_turns.py",
        "patched_sales_difficulty": BOUNDARY_ROUTE,
        "patched_trigger_markers": ["eligible", "reimbursement", "reimbursed", "plan covers"],
        "response_text_change": False,
        "classifier_change": True,
        "call_control_change_for_patched_phrases": True,
        "next_action_change_for_patched_phrases": True,
        "runtime_patch_case_count": len(reviews),
        "failed_runtime_patch_case_count": len(failed),
        "requires_human_review_before_next_checkpoint": False,
        "recommended_next_checkpoint": NEXT_CHECKPOINT_ID,
        "production_runtime_promotion_allowed": False,
    }


def build_evidence_summary(
    source_result: dict[str, Any],
    policy_decision: dict[str, Any],
    runtime_reviews: dict[str, Any],
    source_validator: dict[str, Any],
) -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "source_runtime_gap_case_ids": source_result["summary"]["runtime_gap_case_ids"],
        "source_policy_decision": policy_decision["decision"],
        "source_runtime_gap_count": sum(1 for item in runtime_reviews["items"] if item["runtime_gap"]),
        "source_validator_run": source_validator,
        "future_persuasion_tactic_candidate": FUTURE_PERSUASION_TACTIC_CANDIDATE,
    }


def summarize(reviews: list[dict[str, Any]], patch_decision: dict[str, Any], source_validator: dict[str, Any]) -> dict[str, Any]:
    failed = [item for item in reviews if not item["passed"]]
    patched = [item for item in reviews if item["case_type"] == "patched_boundary_phrase"]
    controls = [item for item in reviews if item["case_type"] == "control"]
    return {
        "runtime_behavior_changed": True,
        "classifier_behavior_changed": True,
        "call_control_behavior_changed": True,
        "next_action_behavior_changed": True,
        "english_only_runtime_patch": True,
        "source_validator_passed": source_validator["passed"],
        "patched_sales_difficulty": BOUNDARY_ROUTE,
        "runtime_patch_case_count": len(reviews),
        "patched_case_count": len(patched),
        "patched_case_ids": [item["case_id"] for item in patched],
        "control_case_count": len(controls),
        "failed_runtime_patch_case_count": len(failed),
        "failed_runtime_patch_case_ids": [item["case_id"] for item in failed],
        "coverage_advice_allowed": False,
        "coverage_fact_claims_allowed": False,
        "eligibility_claims_allowed": False,
        "reimbursement_claims_allowed": False,
        "requires_human_review_before_next_checkpoint": False,
        "review_html_created": False,
        "future_persuasion_tactic_candidate_recorded": True,
        "guided_option_selection_recorded": True,
        "recommended_next_checkpoint": patch_decision["recommended_next_checkpoint"],
        **BOUNDARY_FLAGS,
    }


def render_report(patch_decision: dict[str, Any], reviews: list[dict[str, Any]], summary: dict[str, Any]) -> str:
    lines = [
        "# PROD-071 English Coverage Knowledge Runtime Patch",
        "",
        "`PROD-071` applies a narrow English coverage knowledge classifier reachability patch for the three `PROD-070` runtime gap phrases.",
        "",
        "This is an English coverage knowledge classifier reachability patch only. It is not a response-text patch, not retrieval, and not coverage advice.",
        "",
        "No human review required. This checkpoint creates no review HTML because it applies an already-probed boundary route and does not ask Tarik to approve product/legal wording or coverage facts.",
        "",
        "## Decision",
        "",
        f"- Decision: `{patch_decision['decision']}`",
        f"- Runtime path: `{patch_decision['runtime_path']}`",
        f"- Patched sales difficulty: `{summary['patched_sales_difficulty']}`",
        f"- Patched trigger markers: `{', '.join(patch_decision['patched_trigger_markers'])}`",
        f"- Runtime behavior changed: `{str(summary['runtime_behavior_changed']).lower()}`",
        f"- Classifier behavior changed: `{str(summary['classifier_behavior_changed']).lower()}`",
        f"- Response text behavior changed: `{str(summary['response_text_behavior_changed']).lower()}`",
        f"- Call-control behavior changed for patched phrases: `{str(summary['call_control_behavior_changed']).lower()}`",
        f"- Next-action behavior changed for patched phrases: `{str(summary['next_action_behavior_changed']).lower()}`",
        f"- Retrieval enabled: `{str(summary['retrieval_enabled']).lower()}`",
        f"- Coverage advice allowed: `{str(summary['coverage_advice_allowed']).lower()}`",
        f"- Review HTML created: `{str(summary['review_html_created']).lower()}`",
        f"- Recommended next checkpoint: `{summary['recommended_next_checkpoint']}`",
        "- Production runtime promotion allowed: `false`",
        "",
        "## Runtime Patch Reviews",
        "",
    ]
    for item in reviews:
        observed = item["observed_runtime"]
        lines.extend(
            [
                f"### {item['case_id']}",
                "",
                f"- Case type: `{item['case_type']}`",
                f"- Customer turn: {item['customer_turn']}",
                f"- Passed: `{str(item['passed']).lower()}`",
                f"- Issue codes: `{', '.join(item['issue_codes']) if item['issue_codes'] else 'none'}`",
                f"- Sales difficulty: `{observed['sales_difficulty']}`",
                f"- Next action: `{observed['next_action']}`",
                f"- Call control: `{observed['call_control']}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Future Persuasion-Tactics Checkpoint",
            "",
            "`guided_option_selection` is recorded as a future persuasion-tactics checkpoint candidate, not as PROD-071 runtime behavior.",
            "",
            "Definition: after fit and interest are established, present two real paid options with clear tradeoffs and let the customer choose.",
            "",
            "Guardrails: both options must be real and fairly described; neither, not now, and explain the difference remain valid choices; no fake urgency; no pretending the customer already agreed.",
            "",
            "## Boundary",
            "",
            "- Response text behavior changed: `false`",
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


def main() -> None:
    source_result, policy_decision, runtime_reviews = load_source()
    write_json(CASE_FILE, build_case_file())
    if localized_response("en", BOUNDARY_ROUTE, None) != BOUNDARY_RESPONSE:
        raise SystemExit("Coverage boundary response changed; review before applying PROD-071.")
    source_validator = run_source_validator()
    reviews = [evaluate_runtime_case(case) for case in RUNTIME_PATCH_CASES]
    patch_decision = build_patch_decision(reviews)
    evidence = build_evidence_summary(source_result, policy_decision, runtime_reviews, source_validator)
    summary = summarize(reviews, patch_decision, source_validator)
    result = {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "validation": {
            "passed": source_validator["passed"] and summary["failed_runtime_patch_case_count"] == 0,
            "runtime_patch_passed": summary["failed_runtime_patch_case_count"] == 0,
            "controls_preserved": all(item["passed"] for item in reviews if item["case_type"] == "control"),
        },
        "summary": summary,
    }
    write_json(OUT_DIR / "evidence_summary.json", evidence)
    write_json(OUT_DIR / "runtime_patch_reviews.json", {"checkpoint_id": CHECKPOINT_ID, "items": reviews})
    write_json(OUT_DIR / "patch_decision.json", patch_decision)
    write_json(OUT_DIR / "result.json", result)
    write_text(OUT_DIR / "report.md", render_report(patch_decision, reviews, summary))
    print(json.dumps({"checkpoint_id": CHECKPOINT_ID, "validation": result["validation"], "summary": summary}, indent=2))


if __name__ == "__main__":
    main()
