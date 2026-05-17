#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-063-english-autonomy-check-runtime-wording-patch"
CHECKPOINT_NAME = "English Autonomy-Check Runtime Wording Patch"
SOURCE_CHECKPOINT_ID = "PROD-062-english-context-sensitive-autonomy-policy-probe"
NEXT_CHECKPOINT_ID = "PROD-064-english-autonomy-post-patch-multi-turn-regression"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
CASE_FILE = ROOT / "research" / "experiments" / "cases" / "prod-063-english-autonomy-check-runtime-wording-patch.json"
SOURCE_DIR = ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID
SOURCE_VALIDATOR = ROOT / "scripts" / "validate_prod_062_english_context_sensitive_autonomy_policy_probe.py"
SOURCE_VALIDATOR_COMMAND = "python scripts\\validate_prod_062_english_context_sensitive_autonomy_policy_probe.py"
EXPECTED_RESPONSE = "Okay, no rush. We can keep this low-pressure and only clarify what you need."
OLD_RESPONSE = "That makes sense. We can keep this low pressure and clarify only what you need before any next step."

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.core.realtime_turns import build_runtime_decision, localized_response  # noqa: E402

RUNTIME_PROBE_CASES = [
    {
        "case_id": "prod-063-time-to-think",
        "transcript": "I need time to think. Do not rush.",
        "stage": "objection",
    },
    {
        "case_id": "prod-063-do-not-rush",
        "transcript": "Please do not rush me.",
        "stage": "objection",
    },
    {
        "case_id": "prod-063-time-before-anything",
        "transcript": "I need time to think before anything else.",
        "stage": "objection",
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


def load_sources() -> tuple[dict[str, Any], dict[str, Any]]:
    source_result = read_json(SOURCE_DIR / "result.json")
    policy_decision = read_json(SOURCE_DIR / "policy_decision.json")
    if source_result["validation"]["passed"] is not True:
        raise SystemExit("PROD-062 must pass before PROD-063.")
    if source_result["summary"]["candidate_response"] != EXPECTED_RESPONSE:
        raise SystemExit("PROD-062 candidate response changed; review before PROD-063.")
    if source_result["summary"]["runtime_patch_recommended_next"] is not True:
        raise SystemExit("PROD-062 must recommend a runtime patch before PROD-063.")
    if source_result["summary"]["recommended_next_checkpoint"] != CHECKPOINT_ID:
        raise SystemExit("PROD-062 must recommend PROD-063.")
    if policy_decision["runtime_patch_allowed_in_prod_062"] is not False:
        raise SystemExit("PROD-062 must not apply the runtime patch itself.")
    return source_result, policy_decision


def build_case_file() -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "scope": "english_autonomy_check_response_text_patch_only",
        "old_response": OLD_RESPONSE,
        "expected_response": EXPECTED_RESPONSE,
        "runtime_path": "runtime/core/realtime_turns.py",
        "runtime_change_requested": True,
        "response_text_change_requested": True,
        "classifier_change_requested": False,
        "call_control_change_requested": False,
        "requires_human_review_before_next_checkpoint": False,
        "recommended_next_checkpoint": NEXT_CHECKPOINT_ID,
        "runtime_probe_cases": RUNTIME_PROBE_CASES,
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


def evaluate_runtime_case(case: dict[str, Any]) -> dict[str, Any]:
    decision = runtime_decision_for(case)
    gates = {
        "response_language_en": decision["response_language"] == "en",
        "sales_difficulty_unchanged": decision["sales_difficulty"] == "autonomy-check",
        "strategy_unchanged": decision["selected_strategy"] == "inquiry",
        "next_action_unchanged": decision["next_action"] == "ask-follow-up",
        "call_control_unchanged": decision["call_control"] == "continue-call",
        "response_patched": decision["agent_response"] == EXPECTED_RESPONSE,
        "old_response_absent": decision["agent_response"] != OLD_RESPONSE,
        "no_commitment_or_payment": all(marker not in decision["agent_response"].lower() for marker in ["commit", "payment", "contract", "sign"]),
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


def build_patch_decision(reviews: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "decision": "english_autonomy_check_runtime_wording_patch_applied",
        "runtime_path": "runtime/core/realtime_turns.py",
        "patched_sales_difficulty": "autonomy-check",
        "old_response": OLD_RESPONSE,
        "patched_response": EXPECTED_RESPONSE,
        "classifier_change": False,
        "call_control_change": False,
        "german_text_change": False,
        "runtime_probe_count": len(reviews),
        "failed_runtime_probe_count": sum(1 for item in reviews if not item["passed"]),
        "requires_human_review_before_next_checkpoint": False,
        "recommended_next_checkpoint": NEXT_CHECKPOINT_ID,
        "production_runtime_promotion_allowed": False,
    }


def build_evidence_summary(source_result: dict[str, Any], policy_decision: dict[str, Any], source_validator: dict[str, Any]) -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "source_candidate_response": source_result["summary"]["candidate_response"],
        "source_policy_decision": policy_decision["decision"],
        "source_probe_passed": source_result["validation"]["policy_probe_passed"],
        "source_validator_run": source_validator,
    }


def summarize(reviews: list[dict[str, Any]], patch_decision: dict[str, Any], source_validator: dict[str, Any]) -> dict[str, Any]:
    failed = [item for item in reviews if not item["passed"]]
    return {
        "runtime_behavior_changed": True,
        "response_text_behavior_changed": True,
        "classifier_behavior_changed": False,
        "english_only_runtime_patch": True,
        "source_validator_passed": source_validator["passed"],
        "patched_sales_difficulty": "autonomy-check",
        "patched_response": EXPECTED_RESPONSE,
        "runtime_probe_count": len(reviews),
        "failed_runtime_probe_count": len(failed),
        "failed_runtime_probe_case_ids": [item["case_id"] for item in failed],
        "requires_human_review_before_next_checkpoint": False,
        "recommended_next_checkpoint": NEXT_CHECKPOINT_ID,
        **BOUNDARY_FLAGS,
    }


def render_report(patch_decision: dict[str, Any], reviews: list[dict[str, Any]], summary: dict[str, Any]) -> str:
    lines = [
        "# PROD-063 English Autonomy-Check Runtime Wording Patch",
        "",
        "`PROD-063` applies the `PROD-062` autonomy wording candidate to the English `autonomy-check` runtime response only.",
        "",
        "No human review required before this checkpoint because `PROD-062` was an agent-owned synthetic policy probe.",
        "",
        "## Decision",
        "",
        f"- Decision: `{patch_decision['decision']}`",
        f"- Runtime path: `{patch_decision['runtime_path']}`",
        f"- Old response: `{patch_decision['old_response']}`",
        f"- Patched response: `{patch_decision['patched_response']}`",
        f"- Runtime behavior changed: `{str(summary['runtime_behavior_changed']).lower()}`",
        f"- Response text behavior changed: `{str(summary['response_text_behavior_changed']).lower()}`",
        f"- Classifier behavior changed: `{str(summary['classifier_behavior_changed']).lower()}`",
        f"- Recommended next checkpoint: `{patch_decision['recommended_next_checkpoint']}`",
        "- Production runtime promotion allowed: `false`",
        "",
        "## Runtime Patch Reviews",
        "",
    ]
    for item in reviews:
        lines.extend(
            [
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
        )
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


def main() -> None:
    source_result, policy_decision = load_sources()
    case_payload = build_case_file()
    write_json(CASE_FILE, case_payload)
    source_validator = run_source_validator()
    reviews = [evaluate_runtime_case(case) for case in RUNTIME_PROBE_CASES]
    patch_decision = build_patch_decision(reviews)
    evidence = build_evidence_summary(source_result, policy_decision, source_validator)
    summary = summarize(reviews, patch_decision, source_validator)
    result = {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "validation": {
            "passed": source_validator["passed"] and summary["failed_runtime_probe_count"] == 0,
            "runtime_patch_passed": summary["failed_runtime_probe_count"] == 0,
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
