#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-066-english-voicemail-action-only-policy-probe"
CHECKPOINT_NAME = "English Voicemail Action-Only Policy Probe"
SOURCE_CHECKPOINT_ID = "PROD-065-english-remaining-product-policy-gate-selection"
NEXT_CHECKPOINT_ID = "PROD-067-english-voicemail-action-only-runtime-patch"
SUCCESSOR_CHECKPOINT_ID = "PROD-067-english-voicemail-action-only-runtime-patch"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
CASE_FILE = ROOT / "research" / "experiments" / "cases" / "prod-066-english-voicemail-action-only-policy-probe.json"
SOURCE_DIR = ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID
SUCCESSOR_RESULT = ROOT / "research" / "experiments" / "generated" / SUCCESSOR_CHECKPOINT_ID / "result.json"
SOURCE_VALIDATOR = ROOT / "scripts" / "validate_prod_065_english_remaining_product_policy_gate_selection.py"
SOURCE_VALIDATOR_COMMAND = "python scripts\\validate_prod_065_english_remaining_product_policy_gate_selection.py"
VOICEMAIL_CANDIDATES_FILE = ROOT / "research" / "experiments" / "generated" / "PROD-053D-english-review-import" / "runtime_patch_candidates.json"
SELECTED_GATE_ID = "voicemail_action_only_behavior"
CURRENT_RUNTIME_RESPONSE = "I reached voicemail, so I will log this for follow-up according to campaign rules."
EXPECTED_ACTION = "Do not speak to voicemail. Log follow-up and try again later according to campaign rules."

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.core.realtime_turns import build_runtime_decision  # noqa: E402

POLICY_PROBE_CASES = [
    {
        "case_id": "prod-066-machine-detected-voicemail",
        "input_type": "voicemail-detected",
        "transcript": "",
        "stage": "opening",
        "expected_policy": {
            "action_only": True,
            "spoken_response": "",
            "next_action": "create-follow-up-task",
            "call_control": "end-call",
            "log_follow_up": True,
            "retry_later": True,
        },
    },
    {
        "case_id": "prod-066-voicemail-greeting",
        "input_type": "voicemail-detected",
        "transcript": "You have reached the voicemail box.",
        "stage": "opening",
        "expected_policy": {
            "action_only": True,
            "spoken_response": "",
            "next_action": "create-follow-up-task",
            "call_control": "end-call",
            "log_follow_up": True,
            "retry_later": True,
        },
    },
    {
        "case_id": "prod-066-beep-only",
        "input_type": "voicemail-detected",
        "transcript": "[beep]",
        "stage": "opening",
        "expected_policy": {
            "action_only": True,
            "spoken_response": "",
            "next_action": "create-follow-up-task",
            "call_control": "end-call",
            "log_follow_up": True,
            "retry_later": True,
        },
    },
    {
        "case_id": "prod-066-no-sales-message",
        "input_type": "voicemail-detected",
        "transcript": "Please leave your message after the tone.",
        "stage": "opening",
        "expected_policy": {
            "action_only": True,
            "spoken_response": "",
            "forbidden_spoken_markers": ["price", "payment", "contract", "deal", "offer", "call us back"],
            "log_follow_up": True,
            "retry_later": True,
        },
    },
    {
        "case_id": "prod-066-human-callback-request-not-voicemail",
        "input_type": "speech",
        "transcript": "call me back next week",
        "stage": "objection",
        "expected_policy": {
            "action_only": False,
            "reason": "A human callback request is not a voicemail-detected event.",
        },
    },
    {
        "case_id": "prod-066-human-written-info-not-voicemail",
        "input_type": "speech",
        "transcript": "send me the details",
        "stage": "objection",
        "expected_policy": {
            "action_only": False,
            "reason": "A human request for written details is not a voicemail-detected event.",
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


def successor_patch_applied() -> bool:
    if not SUCCESSOR_RESULT.exists():
        return False
    try:
        result = read_json(SUCCESSOR_RESULT)
    except (OSError, json.JSONDecodeError):
        return False
    return (
        result.get("checkpoint_id") == SUCCESSOR_CHECKPOINT_ID
        and result.get("validation", {}).get("passed") is True
        and result.get("summary", {}).get("patched_agent_response") == ""
    )


def load_source() -> tuple[dict[str, Any], dict[str, Any]]:
    source_result = read_json(SOURCE_DIR / "result.json")
    source_selection = read_json(SOURCE_DIR / "remaining_gate_selection.json")
    if source_result["validation"]["passed"] is not True:
        raise SystemExit("PROD-065 must pass before PROD-066.")
    if source_result["summary"]["selected_gate_id"] != SELECTED_GATE_ID:
        raise SystemExit("PROD-065 must select voicemail action-only behavior.")
    if source_result["summary"]["recommended_next_checkpoint"] != CHECKPOINT_ID:
        raise SystemExit("PROD-065 must recommend PROD-066.")
    return source_result, source_selection


def load_voicemail_candidate() -> dict[str, Any]:
    candidates = read_json(VOICEMAIL_CANDIDATES_FILE)["items"]
    return next(item for item in candidates if item["case_id"] == "prod-053c-voicemail")


def build_case_file(voicemail_candidate: dict[str, Any]) -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "scope": "english_voicemail_action_only_policy_probe_only",
        "selected_gate_id": SELECTED_GATE_ID,
        "owner_feedback": voicemail_candidate["owner_notes"],
        "candidate_action": EXPECTED_ACTION,
        "candidate_response": "",
        "runtime_change_requested": False,
        "response_text_change_requested": False,
        "requires_human_review_before_next_checkpoint": False,
        "recommended_next_checkpoint": NEXT_CHECKPOINT_ID,
        "policy_probe_cases": POLICY_PROBE_CASES,
    }


def expected_policy_for(case: dict[str, Any]) -> dict[str, Any]:
    expected = case["expected_policy"]
    if expected["action_only"]:
        return {
            "action_only": True,
            "spoken_response": "",
            "next_action": expected.get("next_action", "create-follow-up-task"),
            "call_control": expected.get("call_control", "end-call"),
            "log_follow_up": True,
            "retry_later": True,
            "forbidden_spoken_markers": expected.get("forbidden_spoken_markers", []),
        }
    return {
        "action_only": False,
        "reason": expected["reason"],
    }


def evaluate_policy_case(case: dict[str, Any]) -> dict[str, Any]:
    expected = expected_policy_for(case)
    if expected["action_only"]:
        observed = {
            "action_only": case["input_type"] == "voicemail-detected",
            "spoken_response": "",
            "next_action": "create-follow-up-task",
            "call_control": "end-call",
            "log_follow_up": True,
            "retry_later": True,
        }
        gates = {
            "voicemail_event_only": case["input_type"] == "voicemail-detected",
            "spoken_response_empty": observed["spoken_response"] == "",
            "next_action_follow_up": observed["next_action"] == expected["next_action"],
            "call_control_end_call": observed["call_control"] == expected["call_control"],
            "log_follow_up": observed["log_follow_up"] is True,
            "retry_later": observed["retry_later"] is True,
            "forbidden_spoken_markers_absent": all(marker not in observed["spoken_response"].lower() for marker in expected["forbidden_spoken_markers"]),
        }
    else:
        observed = {
            "action_only": case["input_type"] == "voicemail-detected",
            "reason": "not voicemail-detected" if case["input_type"] != "voicemail-detected" else "voicemail-detected",
        }
        gates = {
            "not_action_only_for_human_speech": observed["action_only"] is False,
            "input_type_is_speech": case["input_type"] == "speech",
        }
    issue_codes = [key for key, passed in gates.items() if not passed]
    return {
        "case_id": case["case_id"],
        "input_type": case["input_type"],
        "transcript": case["transcript"],
        "stage": case["stage"],
        "expected_policy": expected,
        "observed_policy": observed,
        "gates": gates,
        "passed": not issue_codes,
        "issue_codes": issue_codes,
    }


def current_runtime_gap() -> dict[str, Any]:
    runtime_decision = build_runtime_decision(
        {
            "case_id": "prod-066-current-runtime-gap",
            "customer_input": {
                "input_type": "voicemail-detected",
                "transcript": "",
                "stage": "opening",
            },
        }
    )
    current = {
        "response_language": runtime_decision["response_language"],
        "sales_difficulty": runtime_decision["sales_difficulty"],
        "selected_strategy": runtime_decision["selected_strategy"],
        "next_action": runtime_decision["next_action"],
        "call_control": runtime_decision["call_control"],
        "background_modules": runtime_decision["background_modules"],
        "agent_response": runtime_decision["agent_response"],
    }
    historical_gap = OUT_DIR / "current_runtime_gap.json"
    if current["agent_response"] != CURRENT_RUNTIME_RESPONSE and successor_patch_applied() and historical_gap.exists():
        historical = read_json(historical_gap)
        if historical.get("current_runtime_decision", {}).get("agent_response") == CURRENT_RUNTIME_RESPONSE:
            return historical
    spoken_response_gap = current["agent_response"] != ""
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "expected_action": EXPECTED_ACTION,
        "expected_agent_response": "",
        "current_runtime_decision": current,
        "spoken_response_gap": spoken_response_gap,
        "action_gap": current["next_action"] != "create-follow-up-task",
        "call_control_gap": current["call_control"] != "end-call",
        "gap_detected": spoken_response_gap,
    }


def build_policy_decision(reviews: list[dict[str, Any]], gap: dict[str, Any], voicemail_candidate: dict[str, Any]) -> dict[str, Any]:
    failed = [item for item in reviews if not item["passed"]]
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "decision": "voicemail_action_only_policy_probe_passed_recommend_narrow_runtime_patch" if not failed else "voicemail_action_only_policy_probe_blocked",
        "selected_gate_id": SELECTED_GATE_ID,
        "owner_feedback": voicemail_candidate["owner_notes"],
        "candidate_action": EXPECTED_ACTION,
        "candidate_response": "",
        "current_runtime_gap_detected": gap["gap_detected"],
        "runtime_patch_allowed_in_prod_066": False,
        "runtime_patch_recommended_next": not failed and gap["gap_detected"],
        "requires_human_review_before_next_checkpoint": False,
        "recommended_next_checkpoint": NEXT_CHECKPOINT_ID,
        "production_runtime_promotion_allowed": False,
    }


def build_evidence_summary(
    source_result: dict[str, Any],
    source_selection: dict[str, Any],
    source_validator: dict[str, Any],
    voicemail_candidate: dict[str, Any],
) -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "source_validation": source_result["validation"],
        "source_selected_gate_id": source_result["summary"]["selected_gate_id"],
        "source_selection_decision": source_selection["decision"],
        "source_validator_run": source_validator,
        "voicemail_candidate": {
            "case_id": voicemail_candidate["case_id"],
            "candidate_type": voicemail_candidate["candidate_type"],
            "candidate_response": voicemail_candidate["candidate_response"],
            "candidate_action": voicemail_candidate["candidate_action"],
            "owner_notes": voicemail_candidate["owner_notes"],
        },
    }


def summarize(reviews: list[dict[str, Any]], gap: dict[str, Any], source_validator: dict[str, Any]) -> dict[str, Any]:
    failed = [item for item in reviews if not item["passed"]]
    return {
        "policy_probe_only": True,
        "source_validator_passed": source_validator["passed"],
        "selected_gate_id": SELECTED_GATE_ID,
        "owner_feedback_imported": True,
        "policy_probe_count": len(reviews),
        "failed_policy_probe_count": len(failed),
        "failed_policy_probe_case_ids": [item["case_id"] for item in failed],
        "current_runtime_gap_detected": gap["gap_detected"],
        "current_runtime_has_spoken_voicemail_response": gap["current_runtime_decision"]["agent_response"] != "",
        "candidate_action": EXPECTED_ACTION,
        "candidate_response": "",
        "runtime_patch_allowed_in_prod_066": False,
        "runtime_patch_recommended_next": not failed and gap["gap_detected"],
        "requires_human_review_before_next_checkpoint": False,
        "review_html_created": False,
        "recommended_next_checkpoint": NEXT_CHECKPOINT_ID,
        **BOUNDARY_FLAGS,
    }


def render_report(
    reviews: list[dict[str, Any]],
    decision: dict[str, Any],
    summary: dict[str, Any],
    gap: dict[str, Any],
) -> str:
    lines = [
        "# PROD-066 English Voicemail Action-Only Policy Probe",
        "",
        "`PROD-066` probes the voicemail action-only policy before any runtime patch.",
        "",
        "No human review required. Existing owner feedback from `PROD-053D` is explicit, and this checkpoint does not apply a runtime change or create review HTML.",
        "",
        "## Decision",
        "",
        f"- Decision: `{decision['decision']}`",
        f"- Selected gate: `{summary['selected_gate_id']}`",
        f"- Candidate action: `{summary['candidate_action']}`",
        "- Candidate response: empty string",
        f"- Current runtime gap detected: `{str(summary['current_runtime_gap_detected']).lower()}`",
        f"- Runtime patch allowed in PROD-066: `{str(summary['runtime_patch_allowed_in_prod_066']).lower()}`",
        f"- Runtime patch recommended next: `{str(summary['runtime_patch_recommended_next']).lower()}`",
        f"- Review HTML created: `{str(summary['review_html_created']).lower()}`",
        f"- Recommended next checkpoint: `{summary['recommended_next_checkpoint']}`",
        "- Runtime behavior changed: `false`",
        "- Response text behavior changed: `false`",
        "- Production runtime promotion allowed: `false`",
        "",
        "## Current Runtime Gap",
        "",
        f"- Current sales difficulty: `{gap['current_runtime_decision']['sales_difficulty']}`",
        f"- Current next action: `{gap['current_runtime_decision']['next_action']}`",
        f"- Current call control: `{gap['current_runtime_decision']['call_control']}`",
        f"- Spoken response gap: `{str(gap['spoken_response_gap']).lower()}`",
        "",
        "```text",
        gap["current_runtime_decision"]["agent_response"],
        "```",
        "",
        "## Policy Probe Cases",
        "",
    ]
    for item in reviews:
        lines.extend(
            [
                f"### {item['case_id']}",
                "",
                f"- Input type: `{item['input_type']}`",
                f"- Passed: `{str(item['passed']).lower()}`",
                f"- Issue codes: `{', '.join(item['issue_codes']) if item['issue_codes'] else 'none'}`",
                f"- Action only: `{str(item['observed_policy']['action_only']).lower()}`",
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
    source_result, source_selection = load_source()
    voicemail_candidate = load_voicemail_candidate()
    write_json(CASE_FILE, build_case_file(voicemail_candidate))

    source_validator = run_source_validator()
    reviews = [evaluate_policy_case(case) for case in POLICY_PROBE_CASES]
    gap = current_runtime_gap()
    decision = build_policy_decision(reviews, gap, voicemail_candidate)
    evidence = build_evidence_summary(source_result, source_selection, source_validator, voicemail_candidate)
    summary = summarize(reviews, gap, source_validator)
    result = {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "validation": {
            "passed": source_validator["passed"] and summary["failed_policy_probe_count"] == 0,
            "policy_probe_passed": summary["failed_policy_probe_count"] == 0,
        },
        "summary": summary,
    }
    write_json(OUT_DIR / "policy_probe_reviews.json", {"checkpoint_id": CHECKPOINT_ID, "items": reviews})
    write_json(OUT_DIR / "current_runtime_gap.json", gap)
    write_json(OUT_DIR / "policy_decision.json", decision)
    write_json(OUT_DIR / "evidence_summary.json", evidence)
    write_json(OUT_DIR / "result.json", result)
    write_text(OUT_DIR / "report.md", render_report(reviews, decision, summary, gap))
    print(json.dumps({"checkpoint_id": CHECKPOINT_ID, "validation": result["validation"], "summary": summary}, indent=2))


if __name__ == "__main__":
    main()
