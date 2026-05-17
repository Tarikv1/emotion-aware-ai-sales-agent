#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-067-english-voicemail-action-only-runtime-patch"
CHECKPOINT_NAME = "English Voicemail Action-Only Runtime Patch"
SOURCE_CHECKPOINT_ID = "PROD-066-english-voicemail-action-only-policy-probe"
NEXT_CHECKPOINT_ID = "PROD-068-english-voicemail-post-patch-regression"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
CASE_FILE = ROOT / "research" / "experiments" / "cases" / "prod-067-english-voicemail-action-only-runtime-patch.json"
SOURCE_DIR = ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID
EXPECTED_ACTION = "Do not speak to voicemail. Log follow-up and try again later according to campaign rules."
EXPECTED_RESPONSE = ""
OLD_RESPONSE = "I reached voicemail, so I will log this for follow-up according to campaign rules."

import sys

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.core.realtime_turns import build_runtime_decision  # noqa: E402

RUNTIME_PROBE_CASES = [
    {
        "case_id": "prod-067-machine-detected-voicemail",
        "input_type": "voicemail-detected",
        "transcript": "",
        "stage": "opening",
    },
    {
        "case_id": "prod-067-voicemail-greeting",
        "input_type": "voicemail-detected",
        "transcript": "You have reached the voicemail box.",
        "stage": "opening",
    },
    {
        "case_id": "prod-067-beep-only",
        "input_type": "voicemail-detected",
        "transcript": "[beep]",
        "stage": "opening",
    },
    {
        "case_id": "prod-067-no-sales-message",
        "input_type": "voicemail-detected",
        "transcript": "Please leave your message after the tone.",
        "stage": "opening",
    },
]

NON_VOICEMAIL_GUARD_CASES = [
    {
        "case_id": "prod-067-human-callback-request-not-voicemail",
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
        "case_id": "prod-067-human-written-info-not-voicemail",
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
]

BOUNDARY_FLAGS = {
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


def load_source() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    source_result = read_json(SOURCE_DIR / "result.json")
    source_decision = read_json(SOURCE_DIR / "policy_decision.json")
    source_gap = read_json(SOURCE_DIR / "current_runtime_gap.json")
    if source_result["validation"]["passed"] is not True:
        raise SystemExit("PROD-066 must pass before PROD-067.")
    if source_result["summary"]["recommended_next_checkpoint"] != CHECKPOINT_ID:
        raise SystemExit("PROD-066 must recommend PROD-067.")
    if source_result["summary"]["runtime_patch_recommended_next"] is not True:
        raise SystemExit("PROD-066 must recommend a runtime patch.")
    if source_result["summary"]["candidate_response"] != EXPECTED_RESPONSE:
        raise SystemExit("PROD-066 candidate response must remain empty.")
    if source_gap["current_runtime_decision"]["agent_response"] != OLD_RESPONSE:
        raise SystemExit("PROD-066 source gap no longer matches the expected pre-patch spoken response.")
    if source_decision["runtime_patch_allowed_in_prod_066"] is not False:
        raise SystemExit("PROD-066 must not have applied the runtime patch itself.")
    return source_result, source_decision, source_gap


def build_case_file() -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "scope": "english_voicemail_action_only_runtime_patch",
        "candidate_action": EXPECTED_ACTION,
        "expected_response": EXPECTED_RESPONSE,
        "old_response": OLD_RESPONSE,
        "runtime_path": "runtime/core/realtime_turns.py",
        "runtime_change_requested": True,
        "response_text_change_requested": True,
        "classifier_change_requested": False,
        "call_control_change_requested": False,
        "next_action_change_requested": False,
        "english_only_runtime_patch": True,
        "requires_human_review_before_next_checkpoint": False,
        "review_html_created": False,
        "recommended_next_checkpoint": NEXT_CHECKPOINT_ID,
        "runtime_probe_cases": RUNTIME_PROBE_CASES,
        "non_voicemail_guard_cases": NON_VOICEMAIL_GUARD_CASES,
    }


def runtime_decision_for(case: dict[str, Any]) -> dict[str, Any]:
    decision = build_runtime_decision(
        {
            "case_id": case["case_id"],
            "customer_input": {
                "input_type": case["input_type"],
                "transcript": case["transcript"],
                "stage": case["stage"],
            },
        }
    )
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


def evaluate_runtime_case(case: dict[str, Any]) -> dict[str, Any]:
    decision = runtime_decision_for(case)
    gates = {
        "response_language_en": decision["response_language"] == "en",
        "response_mode_fast": decision["response_mode"] == "fast-response",
        "sales_difficulty_voicemail": decision["sales_difficulty"] == "voicemail",
        "strategy_unchanged": decision["selected_strategy"] == "rapport",
        "next_action_follow_up": decision["next_action"] == "create-follow-up-task",
        "call_control_end_call": decision["call_control"] == "end-call",
        "background_follow_up_write": decision["background_modules"] == ["follow-up-task-write"],
        "agent_response_empty": decision["agent_response"] == "",
        "bridge_response_none": decision["bridge_response"] is None,
    }
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


def evaluate_non_voicemail_case(case: dict[str, Any]) -> dict[str, Any]:
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
    issue_codes = [key for key, passed in gates.items() if not passed]
    return {
        "case_id": case["case_id"],
        "input_type": case["input_type"],
        "transcript": case["transcript"],
        "stage": case["stage"],
        "expected_runtime": expected,
        "runtime_decision": decision,
        "gates": gates,
        "passed": not issue_codes,
        "issue_codes": issue_codes,
    }


def build_patch_decision(runtime_reviews: list[dict[str, Any]], guard_reviews: list[dict[str, Any]]) -> dict[str, Any]:
    failed_count = sum(1 for item in runtime_reviews + guard_reviews if not item["passed"])
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "decision": "english_voicemail_action_only_runtime_patch_applied" if failed_count == 0 else "english_voicemail_action_only_runtime_patch_blocked",
        "runtime_path": "runtime/core/realtime_turns.py",
        "patched_sales_difficulty": "voicemail",
        "old_response": OLD_RESPONSE,
        "patched_agent_response": EXPECTED_RESPONSE,
        "candidate_action": EXPECTED_ACTION,
        "classifier_change": False,
        "call_control_change": False,
        "next_action_change": False,
        "german_text_change": False,
        "runtime_probe_count": len(runtime_reviews),
        "non_voicemail_guard_count": len(guard_reviews),
        "failed_probe_count": failed_count,
        "requires_human_review_before_next_checkpoint": False,
        "review_html_created": False,
        "recommended_next_checkpoint": NEXT_CHECKPOINT_ID,
        "production_runtime_promotion_allowed": False,
    }


def build_evidence_summary(source_result: dict[str, Any], source_decision: dict[str, Any], source_gap: dict[str, Any]) -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "source_summary": {
            "selected_gate_id": source_result["summary"]["selected_gate_id"],
            "candidate_action": source_result["summary"]["candidate_action"],
            "candidate_response": source_result["summary"]["candidate_response"],
            "current_runtime_gap_detected": source_result["summary"]["current_runtime_gap_detected"],
            "runtime_patch_recommended_next": source_result["summary"]["runtime_patch_recommended_next"],
        },
        "source_decision": {
            "decision": source_decision["decision"],
            "runtime_patch_allowed_in_prod_066": source_decision["runtime_patch_allowed_in_prod_066"],
            "recommended_next_checkpoint": source_decision["recommended_next_checkpoint"],
        },
        "source_gap": {
            "pre_patch_agent_response": source_gap["current_runtime_decision"]["agent_response"],
            "gap_detected": source_gap["gap_detected"],
        },
    }


def summarize(runtime_reviews: list[dict[str, Any]], guard_reviews: list[dict[str, Any]]) -> dict[str, Any]:
    failed_runtime = [item for item in runtime_reviews if not item["passed"]]
    failed_guards = [item for item in guard_reviews if not item["passed"]]
    runtime_text = (ROOT / "runtime" / "core" / "realtime_turns.py").read_text(encoding="utf-8")
    return {
        "runtime_behavior_changed": True,
        "response_text_behavior_changed": True,
        "english_only_runtime_patch": True,
        "patched_sales_difficulty": "voicemail",
        "patched_agent_response": EXPECTED_RESPONSE,
        "candidate_action": EXPECTED_ACTION,
        "old_spoken_response_absent": OLD_RESPONSE not in runtime_text,
        "runtime_probe_count": len(runtime_reviews),
        "failed_runtime_probe_count": len(failed_runtime),
        "failed_runtime_probe_case_ids": [item["case_id"] for item in failed_runtime],
        "non_voicemail_guard_count": len(guard_reviews),
        "failed_non_voicemail_guard_count": len(failed_guards),
        "failed_non_voicemail_guard_case_ids": [item["case_id"] for item in failed_guards],
        "requires_human_review_before_next_checkpoint": False,
        "review_html_created": False,
        "recommended_next_checkpoint": NEXT_CHECKPOINT_ID,
        **BOUNDARY_FLAGS,
    }


def render_report(
    patch_decision: dict[str, Any],
    runtime_reviews: list[dict[str, Any]],
    guard_reviews: list[dict[str, Any]],
    summary: dict[str, Any],
) -> str:
    lines = [
        "# PROD-067 English Voicemail Action-Only Runtime Patch",
        "",
        "`PROD-067` applies the accepted English voicemail action-only behavior to the deterministic runtime.",
        "",
        "No human review required. `PROD-066` already imported explicit owner feedback, and this checkpoint only closes the recorded runtime gap.",
        "",
        "## Decision",
        "",
        f"- Decision: `{patch_decision['decision']}`",
        f"- Runtime path: `{patch_decision['runtime_path']}`",
        f"- Candidate action: `{patch_decision['candidate_action']}`",
        "- Agent response: empty string",
        f"- Old response absent: `{str(summary['old_spoken_response_absent']).lower()}`",
        f"- Runtime behavior changed: `{str(summary['runtime_behavior_changed']).lower()}`",
        f"- Response text behavior changed: `{str(summary['response_text_behavior_changed']).lower()}`",
        f"- Classifier behavior changed: `{str(summary['classifier_behavior_changed']).lower()}`",
        f"- Call-control behavior changed: `{str(summary['call_control_behavior_changed']).lower()}`",
        f"- Next-action behavior changed: `{str(summary['next_action_behavior_changed']).lower()}`",
        f"- Review HTML created: `{str(summary['review_html_created']).lower()}`",
        f"- Recommended next checkpoint: `{summary['recommended_next_checkpoint']}`",
        "- Production runtime promotion allowed: `false`",
        "",
        "## Runtime Patch Reviews",
        "",
    ]
    for item in runtime_reviews:
        lines.extend(render_review_item(item))
    lines.extend(["## Non-Voicemail Guard Reviews", ""])
    for item in guard_reviews:
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
    source_result, source_decision, source_gap = load_source()
    write_json(CASE_FILE, build_case_file())
    runtime_reviews = [evaluate_runtime_case(case) for case in RUNTIME_PROBE_CASES]
    guard_reviews = [evaluate_non_voicemail_case(case) for case in NON_VOICEMAIL_GUARD_CASES]
    patch_decision = build_patch_decision(runtime_reviews, guard_reviews)
    summary = summarize(runtime_reviews, guard_reviews)
    evidence = build_evidence_summary(source_result, source_decision, source_gap)
    result = {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "validation": {
            "passed": summary["failed_runtime_probe_count"] == 0 and summary["failed_non_voicemail_guard_count"] == 0,
            "runtime_patch_passed": summary["failed_runtime_probe_count"] == 0,
        },
        "summary": summary,
    }
    write_json(OUT_DIR / "runtime_patch_reviews.json", {"checkpoint_id": CHECKPOINT_ID, "items": runtime_reviews})
    write_json(OUT_DIR / "non_voicemail_guard_reviews.json", {"checkpoint_id": CHECKPOINT_ID, "items": guard_reviews})
    write_json(OUT_DIR / "patch_decision.json", patch_decision)
    write_json(OUT_DIR / "evidence_summary.json", evidence)
    write_json(OUT_DIR / "result.json", result)
    write_text(OUT_DIR / "report.md", render_report(patch_decision, runtime_reviews, guard_reviews, summary))
    print(json.dumps({"checkpoint_id": CHECKPOINT_ID, "validation": result["validation"], "summary": summary}, indent=2))


if __name__ == "__main__":
    main()
