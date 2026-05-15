#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-056-english-post-patch-multi-turn-regression"
CHECKPOINT_NAME = "English Post-Patch Multi-Turn Regression"
SOURCE_CHECKPOINT_ID = "PROD-055-english-multi-turn-runtime-patch"
PREVIOUS_STRESS_CHECKPOINT_ID = "PROD-054-english-multi-turn-naturalness-stress-review"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
SOURCE_DIR = ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID
PREVIOUS_STRESS_DIR = ROOT / "research" / "experiments" / "generated" / PREVIOUS_STRESS_CHECKPOINT_ID
PREVIOUS_STRESS_CASE_FILE = (
    ROOT / "research" / "experiments" / "cases" / "prod-054-english-multi-turn-naturalness-stress-review.json"
)
CASE_FILE = ROOT / "research" / "experiments" / "cases" / "prod-056-english-post-patch-multi-turn-regression.json"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from runtime.core.realtime_turns import build_runtime_decision  # noqa: E402
from prod_053c_english_spoken_response_expansion_review import BASE_CAMPAIGN  # noqa: E402


TERMINAL_CALL_CONTROLS = {
    "end-call",
    "transfer-or-escalate",
    "schedule-and-end",
    "close-and-log-sale-ready",
}

FORBIDDEN_SECOND_TURN_MARKERS = [
    "i reached voicemail",
    "coverage advice",
    "give coverage advice",
    "give medical advice",
    "low pressure and clarify only what you need",
    "low-pressure and only clarify what you need",
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
    "payment_collection_allowed": False,
    "contract_signing_allowed": False,
    "production_runtime_promotion_allowed": False,
    "german_exact_phrase_promotion_allowed": False,
    "german_naturalness_claimed": False,
}

CALLBACK_SCHEDULING_SPEC = {
    "source_case_id": "prod-053c-callback-request",
    "case_goal": "After the post-patch callback answer asks for a time, keep the call open and confirm the supplied callback time.",
    "initial_customer_input": {
        "input_type": "speech",
        "transcript": "Can you call back later?",
        "stage": "objection",
    },
    "follow_up_customer_utterance": "Tomorrow at 10 works.",
    "follow_up_customer_input": {
        "input_type": "speech",
        "transcript": "Tomorrow at 10 works.",
        "stage": "scheduling",
    },
    "expected_first_turn": {
        "sales_difficulty": "callback-request",
        "next_action": "offer-scheduling",
        "call_control": "continue-call",
        "response_must_include_any": ["time"],
    },
    "expected_follow_up_turn": {
        "sales_difficulty": "scheduling-confirmation",
        "next_action": "confirm-scheduling",
        "call_control": "schedule-and-end",
        "response_must_include_any": ["note that time", "callback", "goodbye"],
    },
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def normalize_text(text: str) -> str:
    return " ".join(text.lower().split())


def marker_match(text: str, markers: list[str]) -> bool:
    normalized = normalize_text(text)
    return any(normalize_text(marker) in normalized for marker in markers)


def forbidden_marker(text: str) -> str | None:
    normalized = normalize_text(text)
    for marker in FORBIDDEN_SECOND_TURN_MARKERS:
        if normalize_text(marker) in normalized:
            return marker
    return None


def decision_summary(decision: dict[str, Any]) -> dict[str, Any]:
    return {
        "response_language": decision["response_language"],
        "sales_difficulty": decision["sales_difficulty"],
        "next_action": decision["next_action"],
        "call_control": decision["call_control"],
        "agent_response": decision["agent_response"],
    }


def load_source_result() -> dict[str, Any]:
    source = read_json(SOURCE_DIR / "result.json")
    summary = source["summary"]
    if source["validation"]["passed"] is not True or summary["post_patch_blocking_finding_count"] != 0:
        raise SystemExit("PROD-055 must pass with zero post-patch blocking findings before PROD-056.")
    return source


def load_previous_stress_cases() -> list[dict[str, Any]]:
    previous = read_json(PREVIOUS_STRESS_DIR / "result.json")
    if previous["validation"]["passed"] is not True or previous["validation"]["stress_gate_passed"] is not False:
        raise SystemExit("PROD-054 must remain the failing source stress gate for PROD-056.")
    return read_json(PREVIOUS_STRESS_CASE_FILE)["cases"]


def callback_regression_case(previous_case: dict[str, Any]) -> dict[str, Any]:
    return {
        "case_id": "prod-056-prod-053c-callback-request-scheduling-flow",
        "source_case_id": previous_case["source_case_id"],
        "source_sales_difficulty": previous_case["source_sales_difficulty"],
        "source_next_action_before_patch": previous_case["source_next_action"],
        "source_call_control_before_patch": previous_case["source_call_control"],
        "source_agent_response": previous_case["source_agent_response"],
        "language": "en",
        "next_turn_mode": "callback_scheduling_flow",
        "case_goal": CALLBACK_SCHEDULING_SPEC["case_goal"],
        "initial_customer_input": CALLBACK_SCHEDULING_SPEC["initial_customer_input"],
        "follow_up_customer_utterance": CALLBACK_SCHEDULING_SPEC["follow_up_customer_utterance"],
        "follow_up_customer_input": CALLBACK_SCHEDULING_SPEC["follow_up_customer_input"],
        "expected_first_turn": CALLBACK_SCHEDULING_SPEC["expected_first_turn"],
        "expected_follow_up_turn": CALLBACK_SCHEDULING_SPEC["expected_follow_up_turn"],
    }


def runtime_regression_case(previous_case: dict[str, Any]) -> dict[str, Any]:
    return {
        "case_id": previous_case["case_id"].replace("prod-054-", "prod-056-", 1),
        "source_case_id": previous_case["source_case_id"],
        "source_sales_difficulty": previous_case["source_sales_difficulty"],
        "source_next_action": previous_case["source_next_action"],
        "source_call_control": previous_case["source_call_control"],
        "source_agent_response": previous_case["source_agent_response"],
        "language": "en",
        "next_turn_mode": "runtime_second_turn",
        "case_goal": previous_case["case_goal"],
        "follow_up_customer_utterance": previous_case["follow_up_customer_utterance"],
        "follow_up_customer_input": previous_case["follow_up_customer_input"],
        "expected_second_turn": previous_case["expected_second_turn"],
        "terminal_boundary": None,
    }


def terminal_regression_case(previous_case: dict[str, Any]) -> dict[str, Any]:
    return {
        "case_id": previous_case["case_id"].replace("prod-054-", "prod-056-", 1),
        "source_case_id": previous_case["source_case_id"],
        "source_sales_difficulty": previous_case["source_sales_difficulty"],
        "source_next_action": previous_case["source_next_action"],
        "source_call_control": previous_case["source_call_control"],
        "source_agent_response": previous_case["source_agent_response"],
        "language": "en",
        "next_turn_mode": "terminal_boundary",
        "case_goal": previous_case["case_goal"],
        "follow_up_customer_utterance": None,
        "follow_up_customer_input": None,
        "expected_second_turn": None,
        "terminal_boundary": previous_case["terminal_boundary"],
    }


def build_cases(previous_cases: list[dict[str, Any]]) -> dict[str, Any]:
    cases: list[dict[str, Any]] = []
    for previous_case in previous_cases:
        if previous_case["source_case_id"] == "prod-053c-callback-request":
            cases.append(callback_regression_case(previous_case))
        elif previous_case["next_turn_mode"] == "runtime_second_turn":
            cases.append(runtime_regression_case(previous_case))
        else:
            cases.append(terminal_regression_case(previous_case))
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "previous_stress_checkpoint_id": PREVIOUS_STRESS_CHECKPOINT_ID,
        "cases": cases,
    }


def evaluate_runtime_regression_case(case: dict[str, Any]) -> dict[str, Any]:
    expected = case["expected_second_turn"]
    second_case = {
        "case_id": f"{case['case_id']}-second-turn",
        "customer_input": case["follow_up_customer_input"],
    }
    decision = build_runtime_decision(second_case, campaign=BASE_CAMPAIGN)
    response = decision["agent_response"]
    forbidden = forbidden_marker(response)
    gates = {
        "response_language_en": decision["response_language"] == "en",
        "not_exact_repeat": normalize_text(response) != normalize_text(case["source_agent_response"]),
        "sales_difficulty_match": decision["sales_difficulty"] == expected["sales_difficulty"],
        "next_action_match": decision["next_action"] == expected["next_action"],
        "call_control_match": decision["call_control"] == expected["call_control"],
        "required_marker_match": marker_match(response, expected["response_must_include_any"]),
        "forbidden_marker_absent": forbidden is None,
        "terminal_question_coherent": not (
            decision["call_control"] in TERMINAL_CALL_CONTROLS and response.strip().endswith("?")
        ),
    }
    issue_codes = [key for key, passed in gates.items() if not passed]
    if forbidden:
        issue_codes.append(f"forbidden_marker:{forbidden}")
    return {
        "case_id": case["case_id"],
        "source_case_id": case["source_case_id"],
        "source_sales_difficulty": case["source_sales_difficulty"],
        "case_goal": case["case_goal"],
        "source_agent_response": case["source_agent_response"],
        "follow_up_customer_utterance": case["follow_up_customer_utterance"],
        "expected_second_turn": expected,
        "runtime_second_turn": decision_summary(decision),
        "regression_gates": gates,
        "regression_gates_passed": not issue_codes,
        "issue_codes": issue_codes,
    }


def evaluate_callback_scheduling_case(case: dict[str, Any]) -> dict[str, Any]:
    first_turn = build_runtime_decision(
        {"case_id": f"{case['case_id']}-first-turn", "customer_input": case["initial_customer_input"]},
        campaign=BASE_CAMPAIGN,
    )
    follow_up_turn = build_runtime_decision(
        {"case_id": f"{case['case_id']}-follow-up-turn", "customer_input": case["follow_up_customer_input"]},
        campaign=BASE_CAMPAIGN,
    )
    first_expected = case["expected_first_turn"]
    follow_up_expected = case["expected_follow_up_turn"]
    first_response = first_turn["agent_response"]
    follow_up_response = follow_up_turn["agent_response"]
    gates = {
        "first_response_language_en": first_turn["response_language"] == "en",
        "first_sales_difficulty_match": first_turn["sales_difficulty"] == first_expected["sales_difficulty"],
        "first_next_action_match": first_turn["next_action"] == first_expected["next_action"],
        "first_call_control_match": first_turn["call_control"] == first_expected["call_control"],
        "first_marker_match": marker_match(first_response, first_expected["response_must_include_any"]),
        "first_question_keeps_call_open": first_turn["call_control"] == "continue-call" or not first_response.strip().endswith("?"),
        "follow_up_response_language_en": follow_up_turn["response_language"] == "en",
        "follow_up_sales_difficulty_match": follow_up_turn["sales_difficulty"]
        == follow_up_expected["sales_difficulty"],
        "follow_up_next_action_match": follow_up_turn["next_action"] == follow_up_expected["next_action"],
        "follow_up_call_control_match": follow_up_turn["call_control"] == follow_up_expected["call_control"],
        "follow_up_marker_match": marker_match(follow_up_response, follow_up_expected["response_must_include_any"]),
        "follow_up_terminal_question_coherent": not (
            follow_up_turn["call_control"] in TERMINAL_CALL_CONTROLS and follow_up_response.strip().endswith("?")
        ),
    }
    issue_codes = [key for key, passed in gates.items() if not passed]
    return {
        "case_id": case["case_id"],
        "source_case_id": case["source_case_id"],
        "case_goal": case["case_goal"],
        "initial_customer_input": case["initial_customer_input"],
        "follow_up_customer_utterance": case["follow_up_customer_utterance"],
        "expected_first_turn": first_expected,
        "expected_follow_up_turn": follow_up_expected,
        "first_turn": decision_summary(first_turn),
        "follow_up_turn": decision_summary(follow_up_turn),
        "callback_flow_gates": gates,
        "callback_flow_passed": not issue_codes,
        "issue_codes": issue_codes,
    }


def evaluate_terminal_boundary(case: dict[str, Any]) -> dict[str, Any]:
    response = case["source_agent_response"].strip()
    issue_codes: list[str] = []
    if case["source_call_control"] not in TERMINAL_CALL_CONTROLS:
        issue_codes.append("source_call_control_not_terminal")
    if response.endswith("?"):
        issue_codes.append("terminal_response_asks_question")
    return {
        "case_id": case["case_id"],
        "source_case_id": case["source_case_id"],
        "source_sales_difficulty": case["source_sales_difficulty"],
        "source_next_action": case["source_next_action"],
        "source_call_control": case["source_call_control"],
        "source_agent_response": case["source_agent_response"],
        "terminal_boundary": case["terminal_boundary"],
        "terminal_boundary_passed": not issue_codes,
        "issue_codes": issue_codes,
    }


def summarize(
    source: dict[str, Any],
    runtime_reviews: list[dict[str, Any]],
    callback_reviews: list[dict[str, Any]],
    terminal_reviews: list[dict[str, Any]],
) -> dict[str, Any]:
    runtime_failures = [item for item in runtime_reviews if not item["regression_gates_passed"]]
    callback_failures = [item for item in callback_reviews if not item["callback_flow_passed"]]
    terminal_failures = [item for item in terminal_reviews if not item["terminal_boundary_passed"]]
    blocking_ids = sorted(
        {
            item["source_case_id"]
            for item in [*runtime_failures, *callback_failures, *terminal_failures]
        }
    )
    regression_gate_passed = not blocking_ids
    source_summary = source["summary"]
    return {
        "source_patch_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "previous_stress_checkpoint_id": PREVIOUS_STRESS_CHECKPOINT_ID,
        "source_patch_blocking_finding_count": source_summary["post_patch_blocking_finding_count"],
        "source_promoted_response_count": len(runtime_reviews) + len(callback_reviews) + len(terminal_reviews),
        "runtime_second_turn_case_count": len(runtime_reviews),
        "callback_scheduling_case_count": len(callback_reviews),
        "terminal_boundary_case_count": len(terminal_reviews),
        "runtime_second_turn_pass_count": sum(1 for item in runtime_reviews if item["regression_gates_passed"]),
        "runtime_second_turn_failure_count": len(runtime_failures),
        "callback_scheduling_pass_count": sum(1 for item in callback_reviews if item["callback_flow_passed"]),
        "callback_scheduling_failure_count": len(callback_failures),
        "terminal_boundary_pass_count": sum(1 for item in terminal_reviews if item["terminal_boundary_passed"]),
        "terminal_boundary_failure_count": len(terminal_failures),
        "blocking_finding_count": len(blocking_ids),
        "blocking_case_ids": blocking_ids,
        "regression_gate_passed": regression_gate_passed,
        "runtime_promotion_allowed": False,
        "permanent_regression_guard_recommended": True,
        "needs_followup_checkpoint": False,
        **BOUNDARY_FLAGS,
    }


def render_report(
    runtime_reviews: list[dict[str, Any]],
    callback_reviews: list[dict[str, Any]],
    terminal_reviews: list[dict[str, Any]],
    summary: dict[str, Any],
) -> str:
    lines = [
        "# PROD-056 English Post-Patch Multi-Turn Regression",
        "",
        f"Source checkpoint: `{SOURCE_CHECKPOINT_ID}`.",
        f"Previous stress checkpoint: `{PREVIOUS_STRESS_CHECKPOINT_ID}`.",
        "",
        "## Summary",
        "",
        f"- Source promoted responses: `{summary['source_promoted_response_count']}`",
        f"- Runtime second-turn cases: `{summary['runtime_second_turn_case_count']}`",
        f"- Callback scheduling cases: `{summary['callback_scheduling_case_count']}`",
        f"- Terminal boundary cases: `{summary['terminal_boundary_case_count']}`",
        f"- Runtime second-turn failures: `{summary['runtime_second_turn_failure_count']}`",
        f"- Callback scheduling failures: `{summary['callback_scheduling_failure_count']}`",
        f"- Terminal boundary failures: `{summary['terminal_boundary_failure_count']}`",
        f"- Blocking finding count: `{summary['blocking_finding_count']}`",
        f"- Regression gate passed: `{str(summary['regression_gate_passed']).lower()}`",
        f"- Runtime behavior changed: `{str(summary['runtime_behavior_changed']).lower()}`",
        f"- Response text behavior changed: `{str(summary['response_text_behavior_changed']).lower()}`",
        "- Production runtime promotion allowed: `false`",
        "",
        "## Blocking Findings",
        "",
    ]
    if summary["blocking_case_ids"]:
        for case_id in summary["blocking_case_ids"]:
            lines.append(f"- `{case_id}`")
    else:
        lines.append("- None.")
    lines.extend(["", "## Runtime Second-Turn Regression", ""])
    for item in runtime_reviews:
        lines.extend(
            [
                f"### {item['source_case_id']}",
                "",
                f"- Passed: `{str(item['regression_gates_passed']).lower()}`",
                f"- Goal: {item['case_goal']}",
                f"- Follow-up customer turn: {item['follow_up_customer_utterance']}",
                f"- Issue codes: `{', '.join(item['issue_codes']) if item['issue_codes'] else 'none'}`",
                f"- Sales difficulty: `{item['runtime_second_turn']['sales_difficulty']}`",
                f"- Next action: `{item['runtime_second_turn']['next_action']}`",
                f"- Call control: `{item['runtime_second_turn']['call_control']}`",
                "",
                "```text",
                item["runtime_second_turn"]["agent_response"],
                "```",
                "",
            ]
        )
    lines.extend(["## Callback Scheduling Flow", ""])
    for item in callback_reviews:
        lines.extend(
            [
                f"### {item['source_case_id']}",
                "",
                f"- Passed: `{str(item['callback_flow_passed']).lower()}`",
                f"- Issue codes: `{', '.join(item['issue_codes']) if item['issue_codes'] else 'none'}`",
                f"- First-turn call control: `{item['first_turn']['call_control']}`",
                f"- Follow-up call control: `{item['follow_up_turn']['call_control']}`",
                "",
                "First turn:",
                "",
                "```text",
                item["first_turn"]["agent_response"],
                "```",
                "",
                "Follow-up turn:",
                "",
                "```text",
                item["follow_up_turn"]["agent_response"],
                "```",
                "",
            ]
        )
    lines.extend(["## Terminal Boundary Regression", ""])
    for item in terminal_reviews:
        if item["terminal_boundary_passed"]:
            continue
        lines.extend(
            [
                f"### {item['source_case_id']}",
                "",
                f"- Call control: `{item['source_call_control']}`",
                f"- Issue codes: `{', '.join(item['issue_codes'])}`",
                "",
                "```text",
                item["source_agent_response"],
                "```",
                "",
            ]
        )
    if all(item["terminal_boundary_passed"] for item in terminal_reviews):
        lines.append("- All terminal boundaries passed without generating a second automated sales turn.")
        lines.append("")
    lines.extend(
        [
            "## Boundary",
            "",
            "- No provider calls.",
            "- No LLM or LLM judging.",
            "- No private data reads.",
            "- No retrieval enablement.",
            "- No runtime behavior change.",
            "- No response text behavior change.",
            "- No German exact-phrase promotion or German naturalness claim.",
            "- No voice playback, payment collection, contract signing, or production runtime promotion.",
            "",
            "## Next Gate",
            "",
            "`PROD-057` should decide whether this post-patch regression becomes the permanent English multi-turn guard before any broader runtime promotion.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    source = load_source_result()
    previous_cases = load_previous_stress_cases()
    case_payload = build_cases(previous_cases)
    write_json(CASE_FILE, case_payload)

    runtime_cases = [case for case in case_payload["cases"] if case["next_turn_mode"] == "runtime_second_turn"]
    callback_cases = [case for case in case_payload["cases"] if case["next_turn_mode"] == "callback_scheduling_flow"]
    terminal_cases = [case for case in case_payload["cases"] if case["next_turn_mode"] == "terminal_boundary"]

    runtime_reviews = [evaluate_runtime_regression_case(case) for case in runtime_cases]
    callback_reviews = [evaluate_callback_scheduling_case(case) for case in callback_cases]
    terminal_reviews = [evaluate_terminal_boundary(case) for case in terminal_cases]
    summary = summarize(source, runtime_reviews, callback_reviews, terminal_reviews)
    result = {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "previous_stress_checkpoint_id": PREVIOUS_STRESS_CHECKPOINT_ID,
        "validation": {
            "passed": True,
            "regression_gate_passed": summary["regression_gate_passed"],
        },
        "summary": summary,
    }
    write_json(OUT_DIR / "runtime_regression_reviews.json", {"checkpoint_id": CHECKPOINT_ID, "items": runtime_reviews})
    write_json(OUT_DIR / "callback_scheduling_reviews.json", {"checkpoint_id": CHECKPOINT_ID, "items": callback_reviews})
    write_json(OUT_DIR / "terminal_boundary_reviews.json", {"checkpoint_id": CHECKPOINT_ID, "items": terminal_reviews})
    write_json(OUT_DIR / "result.json", result)
    write_text(OUT_DIR / "report.md", render_report(runtime_reviews, callback_reviews, terminal_reviews, summary))
    print(json.dumps({"checkpoint_id": CHECKPOINT_ID, "validation": result["validation"], "summary": summary}, indent=2))


if __name__ == "__main__":
    main()
