#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-068-english-voicemail-post-patch-regression"
CHECKPOINT_NAME = "English Voicemail Post-Patch Regression"
SOURCE_CHECKPOINT_ID = "PROD-067-english-voicemail-action-only-runtime-patch"
STABLE_GUARD_SOURCE_CHECKPOINT_ID = "PROD-056-english-post-patch-multi-turn-regression"
NEXT_CHECKPOINT_ID = "PROD-069-english-remaining-product-policy-gate-selection-after-voicemail"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
CASE_FILE = ROOT / "research" / "experiments" / "cases" / "prod-068-english-voicemail-post-patch-regression.json"
SOURCE_DIR = ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID
SOURCE_VALIDATOR = ROOT / "scripts" / "validate_prod_067_english_voicemail_action_only_runtime_patch.py"
STABLE_GUARD_VALIDATOR = ROOT / "scripts" / "validate_english_multi_turn_regression_guard.py"
EXPECTED_ACTION = "Do not speak to voicemail. Log follow-up and try again later according to campaign rules."
EXPECTED_RESPONSE = ""
OLD_RESPONSE = "I reached voicemail, so I will log this for follow-up according to campaign rules."

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.core.realtime_turns import build_runtime_decision  # noqa: E402

VOICEMAIL_REGRESSION_CASES = [
    {
        "case_id": "prod-068-machine-detected-voicemail",
        "input_type": "voicemail-detected",
        "transcript": "",
        "stage": "opening",
    },
    {
        "case_id": "prod-068-voicemail-greeting",
        "input_type": "voicemail-detected",
        "transcript": "You have reached the voicemail box.",
        "stage": "opening",
    },
    {
        "case_id": "prod-068-beep-only",
        "input_type": "voicemail-detected",
        "transcript": "[beep]",
        "stage": "opening",
    },
    {
        "case_id": "prod-068-after-tone-message",
        "input_type": "voicemail-detected",
        "transcript": "Please leave your message after the tone.",
        "stage": "opening",
    },
    {
        "case_id": "prod-068-automated-greeting",
        "input_type": "voicemail-detected",
        "transcript": "The person you are trying to reach is not available.",
        "stage": "opening",
    },
]

NON_VOICEMAIL_GUARD_CASES = [
    {
        "case_id": "prod-068-human-callback-request",
        "input_type": "speech",
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
        "case_id": "prod-068-human-written-info",
        "input_type": "speech",
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
        "case_id": "prod-068-human-product-detail",
        "input_type": "speech",
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
        "case_id": "prod-068-human-price-question",
        "input_type": "speech",
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
        "case_id": "prod-068-repeated-silence",
        "input_type": "silence-timeout",
        "transcript": "",
        "stage": "opening",
        "silence_count": 2,
        "expected_runtime": {
            "sales_difficulty": "repeated-silence",
            "selected_strategy": "rapport",
            "next_action": "close-politely",
            "call_control": "end-call",
        },
    },
]

PROTECTED_BOUNDARY_CASES = [
    {
        "case_id": "prod-068-protected-do-not-call",
        "input_type": "speech",
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
        "case_id": "prod-068-protected-payment",
        "input_type": "speech",
        "transcript": "I am not giving payment details",
        "stage": "objection",
        "expected_runtime": {
            "sales_difficulty": "payment-safety-boundary",
            "selected_strategy": "rapport",
            "next_action": "create-follow-up-task",
            "call_control": "end-call",
        },
    },
    {
        "case_id": "prod-068-protected-support",
        "input_type": "speech",
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
        "case_id": "prod-068-protected-email-only",
        "input_type": "speech",
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
        "case_id": "prod-068-protected-human-request",
        "input_type": "speech",
        "transcript": "I want a human specialist",
        "stage": "objection",
        "expected_runtime": {
            "sales_difficulty": "human-request",
            "selected_strategy": "rapport",
            "next_action": "escalate",
            "call_control": "transfer-or-escalate",
        },
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
        raise SystemExit("PROD-067 must pass before PROD-068.")
    if summary["patched_agent_response"] != "":
        raise SystemExit("PROD-067 must leave English voicemail response empty.")
    if summary["recommended_next_checkpoint"] != CHECKPOINT_ID:
        raise SystemExit("PROD-067 must recommend PROD-068.")
    if source_decision["patched_agent_response"] != "":
        raise SystemExit("PROD-067 decision payload does not match expected patched response.")
    return source_result, source_decision


def build_case_file() -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "stable_guard_source_checkpoint_id": STABLE_GUARD_SOURCE_CHECKPOINT_ID,
        "scope": "english_voicemail_post_patch_regression_only",
        "expected_action": EXPECTED_ACTION,
        "expected_response": EXPECTED_RESPONSE,
        "old_response": OLD_RESPONSE,
        "runtime_change_requested": False,
        "response_text_change_requested": False,
        "classifier_change_requested": False,
        "call_control_change_requested": False,
        "next_action_change_requested": False,
        "requires_human_review_before_next_checkpoint": False,
        "review_html_created": False,
        "recommended_next_checkpoint": NEXT_CHECKPOINT_ID,
        "voicemail_regression_cases": VOICEMAIL_REGRESSION_CASES,
        "non_voicemail_guard_cases": NON_VOICEMAIL_GUARD_CASES,
        "protected_boundary_cases": PROTECTED_BOUNDARY_CASES,
    }


def runtime_decision_for(case: dict[str, Any]) -> dict[str, Any]:
    customer_input = {
        "input_type": case["input_type"],
        "transcript": case["transcript"],
        "stage": case["stage"],
    }
    if "silence_count" in case:
        customer_input["silence_count"] = case["silence_count"]
    decision = build_runtime_decision({"case_id": case["case_id"], "customer_input": customer_input})
    return {
        "response_language": decision["response_language"],
        "response_mode": decision["response_mode"],
        "sales_difficulty": decision["sales_difficulty"],
        "selected_strategy": decision["selected_strategy"],
        "next_action": decision["next_action"],
        "call_control": decision["call_control"],
        "background_modules": decision["background_modules"],
        "bridge_response": decision["bridge_response"],
        "agent_response": decision["agent_response"],
    }


def evaluate_voicemail_case(case: dict[str, Any]) -> dict[str, Any]:
    decision = runtime_decision_for(case)
    gates = {
        "response_language_en": decision["response_language"] == "en",
        "sales_difficulty_voicemail": decision["sales_difficulty"] == "voicemail",
        "strategy_rapport": decision["selected_strategy"] == "rapport",
        "next_action_follow_up": decision["next_action"] == "create-follow-up-task",
        "call_control_end_call": decision["call_control"] == "end-call",
        "background_follow_up_write": decision["background_modules"] == ["follow-up-task-write"],
        "agent_response_empty": decision["agent_response"] == "",
        "bridge_response_none": decision["bridge_response"] is None,
    }
    return review_payload(case, decision, gates)


def evaluate_expected_case(case: dict[str, Any]) -> dict[str, Any]:
    decision = runtime_decision_for(case)
    expected = case["expected_runtime"]
    gates = {
        "not_voicemail": decision["sales_difficulty"] != "voicemail",
        "response_not_empty": decision["agent_response"] != "",
        "sales_difficulty_expected": decision["sales_difficulty"] == expected["sales_difficulty"],
        "strategy_expected": decision["selected_strategy"] == expected["selected_strategy"],
        "next_action_expected": decision["next_action"] == expected["next_action"],
        "call_control_expected": decision["call_control"] == expected["call_control"],
    }
    payload = review_payload(case, decision, gates)
    payload["expected_runtime"] = expected
    return payload


def review_payload(case: dict[str, Any], decision: dict[str, Any], gates: dict[str, bool]) -> dict[str, Any]:
    issue_codes = [key for key, passed in gates.items() if not passed]
    return {
        "case_id": case["case_id"],
        "input_type": case["input_type"],
        "transcript": case["transcript"],
        "stage": case["stage"],
        "runtime_decision": decision,
        "gates": gates,
        "passed": not issue_codes,
        "issue_codes": issue_codes,
    }


def summarize(
    voicemail_reviews: list[dict[str, Any]],
    guard_reviews: list[dict[str, Any]],
    protected_reviews: list[dict[str, Any]],
    source_result: dict[str, Any],
    source_validator: dict[str, Any],
    stable_guard: dict[str, Any],
) -> dict[str, Any]:
    failed = [item for item in voicemail_reviews + guard_reviews + protected_reviews if not item["passed"]]
    runtime_text = (ROOT / "runtime" / "core" / "realtime_turns.py").read_text(encoding="utf-8")
    return {
        "source_validator_passed": source_validator["passed"],
        "stable_english_guard_passed": stable_guard["passed"],
        "voicemail_regression_case_count": len(voicemail_reviews),
        "non_voicemail_guard_case_count": len(guard_reviews),
        "protected_boundary_case_count": len(protected_reviews),
        "failed_case_count": len(failed),
        "failed_case_ids": [item["case_id"] for item in failed],
        "patched_agent_response": EXPECTED_RESPONSE,
        "old_spoken_response_absent": OLD_RESPONSE not in runtime_text,
        "source_runtime_behavior_changed": source_result["summary"]["runtime_behavior_changed"],
        "source_response_text_behavior_changed": source_result["summary"]["response_text_behavior_changed"],
        "requires_human_review_before_next_checkpoint": False,
        "review_html_created": False,
        "recommended_next_checkpoint": NEXT_CHECKPOINT_ID,
        **BOUNDARY_FLAGS,
    }


def build_decision(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "decision": "voicemail_patch_post_regression_passed" if summary["failed_case_count"] == 0 else "voicemail_patch_post_regression_blocked",
        "runtime_patch_from_source_kept": True,
        "new_runtime_change_in_prod_068": False,
        "stable_english_guard_passed": summary["stable_english_guard_passed"],
        "failed_case_count": summary["failed_case_count"],
        "requires_human_review_before_next_checkpoint": False,
        "review_html_created": False,
        "recommended_next_checkpoint": NEXT_CHECKPOINT_ID,
        "production_runtime_promotion_allowed": False,
    }


def build_evidence_summary(source_result: dict[str, Any], source_validator: dict[str, Any], stable_guard: dict[str, Any]) -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "source_validation": source_result["validation"],
        "source_summary": {
            "patched_agent_response": source_result["summary"]["patched_agent_response"],
            "runtime_behavior_changed": source_result["summary"]["runtime_behavior_changed"],
            "response_text_behavior_changed": source_result["summary"]["response_text_behavior_changed"],
            "classifier_behavior_changed": source_result["summary"]["classifier_behavior_changed"],
            "call_control_behavior_changed": source_result["summary"]["call_control_behavior_changed"],
            "next_action_behavior_changed": source_result["summary"]["next_action_behavior_changed"],
        },
        "source_validator_run": source_validator,
        "stable_guard_run": stable_guard,
    }


def render_report(
    summary: dict[str, Any],
    decision: dict[str, Any],
    voicemail_reviews: list[dict[str, Any]],
    guard_reviews: list[dict[str, Any]],
    protected_reviews: list[dict[str, Any]],
) -> str:
    lines = [
        "# PROD-068 English Voicemail Post-Patch Regression",
        "",
        "`PROD-068` verifies the `PROD-067` English voicemail action-only patch after runtime application.",
        "",
        "No human review required; this checkpoint produces regression evidence only and creates no review HTML.",
        "",
        "## Summary",
        "",
        f"- Stable English guard passed: `{str(summary['stable_english_guard_passed']).lower()}`",
        f"- Source validator passed: `{str(summary['source_validator_passed']).lower()}`",
        "- Agent response: empty string",
        f"- Voicemail regression cases: `{summary['voicemail_regression_case_count']}`",
        f"- Non-voicemail guard cases: `{summary['non_voicemail_guard_case_count']}`",
        f"- Protected boundary cases: `{summary['protected_boundary_case_count']}`",
        f"- Failed case count: `{summary['failed_case_count']}`",
        f"- Runtime behavior changed: `{str(summary['runtime_behavior_changed']).lower()}`",
        f"- Response text behavior changed: `{str(summary['response_text_behavior_changed']).lower()}`",
        f"- Classifier behavior changed: `{str(summary['classifier_behavior_changed']).lower()}`",
        f"- Review HTML created: `{str(summary['review_html_created']).lower()}`",
        f"- Recommended next checkpoint: `{summary['recommended_next_checkpoint']}`",
        "- Production runtime promotion allowed: `false`",
        "",
        "## Decision",
        "",
        f"- Decision: `{decision['decision']}`",
        f"- Runtime patch from source kept: `{str(decision['runtime_patch_from_source_kept']).lower()}`",
        f"- New runtime change in PROD-068: `{str(decision['new_runtime_change_in_prod_068']).lower()}`",
        "",
        "## Voicemail Regression Cases",
        "",
    ]
    for item in voicemail_reviews:
        lines.extend(render_review_item(item))
    lines.extend(["## Non-Voicemail Guard Cases", ""])
    for item in guard_reviews:
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
        f"- Input type: `{item['input_type']}`",
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
    voicemail_reviews = [evaluate_voicemail_case(case) for case in VOICEMAIL_REGRESSION_CASES]
    guard_reviews = [evaluate_expected_case(case) for case in NON_VOICEMAIL_GUARD_CASES]
    protected_reviews = [evaluate_expected_case(case) for case in PROTECTED_BOUNDARY_CASES]
    summary = summarize(voicemail_reviews, guard_reviews, protected_reviews, source_result, source_validator, stable_guard)
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

    write_json(OUT_DIR / "voicemail_regression_reviews.json", {"checkpoint_id": CHECKPOINT_ID, "items": voicemail_reviews})
    write_json(OUT_DIR / "non_voicemail_guard_reviews.json", {"checkpoint_id": CHECKPOINT_ID, "items": guard_reviews})
    write_json(OUT_DIR / "protected_boundary_reviews.json", {"checkpoint_id": CHECKPOINT_ID, "items": protected_reviews})
    write_json(OUT_DIR / "post_patch_regression_decision.json", decision)
    write_json(OUT_DIR / "evidence_summary.json", evidence)
    write_json(OUT_DIR / "result.json", result)
    write_text(OUT_DIR / "report.md", render_report(summary, decision, voicemail_reviews, guard_reviews, protected_reviews))
    print(json.dumps({"checkpoint_id": CHECKPOINT_ID, "validation": result["validation"], "summary": summary}, indent=2))


if __name__ == "__main__":
    main()
