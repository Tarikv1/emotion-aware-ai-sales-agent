#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-064-english-autonomy-post-patch-multi-turn-regression"
CHECKPOINT_NAME = "English Autonomy Post-Patch Multi-Turn Regression"
SOURCE_CHECKPOINT_ID = "PROD-063-english-autonomy-check-runtime-wording-patch"
STABLE_GUARD_SOURCE_CHECKPOINT_ID = "PROD-056-english-post-patch-multi-turn-regression"
NEXT_CHECKPOINT_ID = "PROD-065-english-remaining-product-policy-gate-selection"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
CASE_FILE = ROOT / "research" / "experiments" / "cases" / "prod-064-english-autonomy-post-patch-multi-turn-regression.json"
SOURCE_DIR = ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID
SOURCE_VALIDATOR = ROOT / "scripts" / "validate_prod_063_english_autonomy_check_runtime_wording_patch.py"
STABLE_GUARD_VALIDATOR = ROOT / "scripts" / "validate_english_multi_turn_regression_guard.py"
EXPECTED_RESPONSE = "Okay, no rush. We can keep this low-pressure and only clarify what you need."
OLD_RESPONSE = "That makes sense. We can keep this low pressure and clarify only what you need before any next step."

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.core.realtime_turns import build_runtime_decision, localized_response  # noqa: E402

AUTONOMY_FIRST_TURN_CASES = [
    {
        "case_id": "prod-064-first-turn-time-to-think",
        "transcript": "I need time to think. Do not rush.",
        "stage": "objection",
    },
    {
        "case_id": "prod-064-first-turn-do-not-rush",
        "transcript": "Please do not rush me.",
        "stage": "objection",
    },
    {
        "case_id": "prod-064-first-turn-time-before-anything",
        "transcript": "I need time to think before anything else.",
        "stage": "objection",
    },
]

AUTONOMY_FOLLOW_UP_CASES = [
    {
        "case_id": "prod-064-follow-up-written-info",
        "transcript": "send me the details",
        "stage": "objection",
        "expected_runtime": {
            "sales_difficulty": "written-info-request",
            "selected_strategy": "evidence-or-benefit",
            "next_action": "answer-and-continue",
            "call_control": "bridge-then-continue",
        },
    },
    {
        "case_id": "prod-064-follow-up-product-detail",
        "transcript": "which plan is included",
        "stage": "objection",
        "expected_runtime": {
            "sales_difficulty": "product-detail-lookup",
            "selected_strategy": "evidence-or-benefit",
            "next_action": "continue",
            "call_control": "bridge-then-continue",
        },
    },
    {
        "case_id": "prod-064-follow-up-callback",
        "transcript": "call me back next week",
        "stage": "objection",
        "expected_runtime": {
            "sales_difficulty": "callback-request",
            "selected_strategy": "direct-ask-or-commitment",
            "next_action": "offer-scheduling",
            "call_control": "continue-call",
        },
    },
    {
        "case_id": "prod-064-follow-up-price",
        "transcript": "what is the price",
        "stage": "objection",
        "expected_runtime": {
            "sales_difficulty": "price-first-direct",
            "selected_strategy": "evidence-or-benefit",
            "next_action": "answer-and-continue",
            "call_control": "bridge-then-continue",
        },
    },
    {
        "case_id": "prod-064-follow-up-sale-ready",
        "transcript": "I am ready to move forward",
        "stage": "objection",
        "expected_runtime": {
            "sales_difficulty": "sale-ready-missing-criteria",
            "selected_strategy": "direct-ask-or-commitment",
            "next_action": "ask-follow-up",
            "call_control": "continue-call",
        },
    },
]

PROTECTED_BOUNDARY_CASES = [
    {
        "case_id": "prod-064-protected-do-not-call",
        "transcript": "please stop calling me",
        "stage": "objection",
        "expected_runtime": {
            "sales_difficulty": "do-not-call",
            "selected_strategy": "rapport",
            "next_action": "suppress-contact",
            "call_control": "end-call",
        },
    },
    {
        "case_id": "prod-064-protected-email-only",
        "transcript": "just email me",
        "stage": "objection",
        "expected_runtime": {
            "sales_difficulty": "email-only-boundary",
            "selected_strategy": "evidence-or-benefit",
            "next_action": "create-follow-up-task",
            "call_control": "end-call",
        },
    },
    {
        "case_id": "prod-064-protected-support",
        "transcript": "I need support with my account",
        "stage": "objection",
        "expected_runtime": {
            "sales_difficulty": "support-route",
            "selected_strategy": "rapport",
            "next_action": "escalate",
            "call_control": "transfer-or-escalate",
        },
    },
    {
        "case_id": "prod-064-protected-payment",
        "transcript": "I am not giving payment details",
        "stage": "objection",
        "expected_runtime": {
            "sales_difficulty": "payment-safety-boundary",
            "selected_strategy": "rapport",
            "next_action": "create-follow-up-task",
            "call_control": "end-call",
        },
    },
]

BOUNDARY_FLAGS = {
    "runtime_behavior_changed": False,
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
        raise SystemExit("PROD-063 must pass before PROD-064.")
    if summary["patched_response"] != EXPECTED_RESPONSE:
        raise SystemExit("PROD-063 patched response changed; review before PROD-064.")
    if summary["recommended_next_checkpoint"] != CHECKPOINT_ID:
        raise SystemExit("PROD-063 must recommend PROD-064.")
    if source_decision["patched_response"] != EXPECTED_RESPONSE:
        raise SystemExit("PROD-063 decision payload does not match expected patched response.")
    return source_result, source_decision


def build_case_file() -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "stable_guard_source_checkpoint_id": STABLE_GUARD_SOURCE_CHECKPOINT_ID,
        "scope": "english_autonomy_post_patch_regression_only",
        "expected_patched_response": EXPECTED_RESPONSE,
        "old_response": OLD_RESPONSE,
        "runtime_change_requested": False,
        "response_text_change_requested": False,
        "requires_human_review_before_next_checkpoint": False,
        "recommended_next_checkpoint": NEXT_CHECKPOINT_ID,
        "autonomy_first_turn_cases": AUTONOMY_FIRST_TURN_CASES,
        "autonomy_follow_up_cases": AUTONOMY_FOLLOW_UP_CASES,
        "protected_boundary_cases": PROTECTED_BOUNDARY_CASES,
    }


def runtime_decision_for(case: dict[str, Any]) -> dict[str, Any]:
    decision = build_runtime_decision(
        {
            "case_id": case["case_id"],
            "customer_input": {
                "input_type": "speech",
                "transcript": case["transcript"],
                "stage": case["stage"],
            },
        }
    )
    return {
        "response_language": decision["response_language"],
        "sales_difficulty": decision["sales_difficulty"],
        "selected_strategy": decision["selected_strategy"],
        "next_action": decision["next_action"],
        "call_control": decision["call_control"],
        "agent_response": decision["agent_response"],
    }


def evaluate_first_turn(case: dict[str, Any]) -> dict[str, Any]:
    decision = runtime_decision_for(case)
    gates = {
        "response_language_en": decision["response_language"] == "en",
        "sales_difficulty_autonomy": decision["sales_difficulty"] == "autonomy-check",
        "strategy_inquiry": decision["selected_strategy"] == "inquiry",
        "next_action_follow_up": decision["next_action"] == "ask-follow-up",
        "call_control_continue": decision["call_control"] == "continue-call",
        "patched_response_exact": decision["agent_response"] == EXPECTED_RESPONSE,
        "old_response_absent": decision["agent_response"] != OLD_RESPONSE,
        "no_commitment_or_payment_collection": all(
            marker not in decision["agent_response"].lower()
            for marker in ["payment details", "card details", "contract signing", "sign now"]
        ),
    }
    issue_codes = [key for key, passed in gates.items() if not passed]
    return {
        "case_id": case["case_id"],
        "transcript": case["transcript"],
        "stage": case["stage"],
        "runtime_decision": decision,
        "gates": gates,
        "passed": not issue_codes,
        "issue_codes": issue_codes,
    }


def evaluate_expected_case(case: dict[str, Any], *, protected: bool) -> dict[str, Any]:
    decision = runtime_decision_for(case)
    expected = case["expected_runtime"]
    gates = {
        "response_language_en": decision["response_language"] == "en",
        "sales_difficulty_expected": decision["sales_difficulty"] == expected["sales_difficulty"],
        "strategy_expected": decision["selected_strategy"] == expected["selected_strategy"],
        "next_action_expected": decision["next_action"] == expected["next_action"],
        "call_control_expected": decision["call_control"] == expected["call_control"],
        "does_not_loop_back_to_autonomy": decision["sales_difficulty"] != "autonomy-check",
        "old_response_absent": decision["agent_response"] != OLD_RESPONSE,
    }
    if protected:
        gates["protected_call_control_kept"] = decision["call_control"] in {"end-call", "transfer-or-escalate"}
    else:
        gates["follow_up_not_terminal_by_default"] = decision["call_control"] in {"continue-call", "bridge-then-continue"}
    issue_codes = [key for key, passed in gates.items() if not passed]
    return {
        "case_id": case["case_id"],
        "transcript": case["transcript"],
        "stage": case["stage"],
        "expected_runtime": expected,
        "runtime_decision": decision,
        "gates": gates,
        "passed": not issue_codes,
        "issue_codes": issue_codes,
    }


def build_decision(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "decision": "autonomy_patch_post_regression_passed" if summary["failed_case_count"] == 0 else "autonomy_patch_post_regression_blocked",
        "runtime_patch_from_source_kept": True,
        "new_runtime_change_in_prod_064": False,
        "stable_english_guard_passed": summary["stable_english_guard_passed"],
        "failed_case_count": summary["failed_case_count"],
        "requires_human_review_before_next_checkpoint": False,
        "recommended_next_checkpoint": NEXT_CHECKPOINT_ID,
        "production_runtime_promotion_allowed": False,
    }


def build_evidence_summary(
    source_result: dict[str, Any],
    source_validator: dict[str, Any],
    stable_guard: dict[str, Any],
) -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "source_validation": source_result["validation"],
        "source_summary": {
            "patched_response": source_result["summary"]["patched_response"],
            "runtime_behavior_changed": source_result["summary"]["runtime_behavior_changed"],
            "response_text_behavior_changed": source_result["summary"]["response_text_behavior_changed"],
            "classifier_behavior_changed": source_result["summary"]["classifier_behavior_changed"],
        },
        "source_validator_run": source_validator,
        "stable_guard_run": stable_guard,
    }


def summarize(
    source_result: dict[str, Any],
    first_turn_reviews: list[dict[str, Any]],
    follow_up_reviews: list[dict[str, Any]],
    protected_reviews: list[dict[str, Any]],
    source_validator: dict[str, Any],
    stable_guard: dict[str, Any],
) -> dict[str, Any]:
    failed = [item for item in first_turn_reviews + follow_up_reviews + protected_reviews if not item["passed"]]
    runtime_text = (ROOT / "runtime" / "core" / "realtime_turns.py").read_text(encoding="utf-8")
    return {
        "source_validator_passed": source_validator["passed"],
        "stable_english_guard_passed": stable_guard["passed"],
        "autonomy_first_turn_case_count": len(first_turn_reviews),
        "autonomy_follow_up_case_count": len(follow_up_reviews),
        "protected_boundary_case_count": len(protected_reviews),
        "failed_case_count": len(failed),
        "failed_case_ids": [item["case_id"] for item in failed],
        "patched_response": EXPECTED_RESPONSE,
        "old_response_absent": OLD_RESPONSE not in runtime_text,
        "source_runtime_behavior_changed": source_result["summary"]["runtime_behavior_changed"],
        "source_response_text_behavior_changed": source_result["summary"]["response_text_behavior_changed"],
        "classifier_behavior_changed": False,
        "requires_human_review_before_next_checkpoint": False,
        "recommended_next_checkpoint": NEXT_CHECKPOINT_ID,
        **BOUNDARY_FLAGS,
    }


def render_report(
    summary: dict[str, Any],
    decision: dict[str, Any],
    first_turn_reviews: list[dict[str, Any]],
    follow_up_reviews: list[dict[str, Any]],
    protected_reviews: list[dict[str, Any]],
) -> str:
    lines = [
        "# PROD-064 English Autonomy Post-Patch Multi-Turn Regression",
        "",
        "`PROD-064` verifies the `PROD-063` English autonomy wording patch after it entered the deterministic runtime.",
        "",
        "No human review required; this checkpoint produces regression evidence only and creates no review HTML.",
        "",
        "## Summary",
        "",
        f"- Stable English guard passed: `{str(summary['stable_english_guard_passed']).lower()}`",
        f"- Source validator passed: `{str(summary['source_validator_passed']).lower()}`",
        f"- Autonomy first-turn cases: `{summary['autonomy_first_turn_case_count']}`",
        f"- Autonomy follow-up cases: `{summary['autonomy_follow_up_case_count']}`",
        f"- Protected boundary cases: `{summary['protected_boundary_case_count']}`",
        f"- Failed case count: `{summary['failed_case_count']}`",
        f"- Runtime behavior changed: `{str(summary['runtime_behavior_changed']).lower()}`",
        f"- Response text behavior changed: `{str(summary['response_text_behavior_changed']).lower()}`",
        f"- Recommended next checkpoint: `{summary['recommended_next_checkpoint']}`",
        "- Production runtime promotion allowed: `false`",
        "",
        "## Decision",
        "",
        f"- Decision: `{decision['decision']}`",
        f"- Runtime patch from source kept: `{str(decision['runtime_patch_from_source_kept']).lower()}`",
        f"- New runtime change in PROD-064: `{str(decision['new_runtime_change_in_prod_064']).lower()}`",
        "",
        "## First-Turn Autonomy Cases",
        "",
    ]
    for item in first_turn_reviews:
        lines.extend(render_review_item(item))
    lines.extend(["## Follow-Up Cases", ""])
    for item in follow_up_reviews:
        lines.extend(render_review_item(item))
    lines.extend(["## Protected Boundary Cases", ""])
    for item in protected_reviews:
        lines.extend(render_review_item(item))
    lines.extend(
        [
            "## Boundary",
            "",
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
        f"- Transcript: {item['transcript']}",
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

    source_validator = run_command(SOURCE_VALIDATOR, SOURCE_CHECKPOINT_ID)
    stable_guard = run_command(STABLE_GUARD_VALIDATOR, STABLE_GUARD_SOURCE_CHECKPOINT_ID)
    first_turn_reviews = [evaluate_first_turn(case) for case in AUTONOMY_FIRST_TURN_CASES]
    follow_up_reviews = [evaluate_expected_case(case, protected=False) for case in AUTONOMY_FOLLOW_UP_CASES]
    protected_reviews = [evaluate_expected_case(case, protected=True) for case in PROTECTED_BOUNDARY_CASES]
    summary = summarize(source_result, first_turn_reviews, follow_up_reviews, protected_reviews, source_validator, stable_guard)
    decision = build_decision(summary)
    evidence = build_evidence_summary(source_result, source_validator, stable_guard)
    result = {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "validation": {
            "passed": source_validator["passed"] and stable_guard["passed"] and summary["failed_case_count"] == 0,
            "post_patch_regression_passed": summary["failed_case_count"] == 0,
        },
        "summary": summary,
    }

    write_json(OUT_DIR / "autonomy_first_turn_reviews.json", {"checkpoint_id": CHECKPOINT_ID, "items": first_turn_reviews})
    write_json(OUT_DIR / "autonomy_follow_up_reviews.json", {"checkpoint_id": CHECKPOINT_ID, "items": follow_up_reviews})
    write_json(OUT_DIR / "protected_boundary_reviews.json", {"checkpoint_id": CHECKPOINT_ID, "items": protected_reviews})
    write_json(OUT_DIR / "post_patch_regression_decision.json", decision)
    write_json(OUT_DIR / "evidence_summary.json", evidence)
    write_json(OUT_DIR / "result.json", result)
    write_text(OUT_DIR / "report.md", render_report(summary, decision, first_turn_reviews, follow_up_reviews, protected_reviews))
    print(json.dumps({"checkpoint_id": CHECKPOINT_ID, "validation": result["validation"], "summary": summary}, indent=2))


if __name__ == "__main__":
    main()
