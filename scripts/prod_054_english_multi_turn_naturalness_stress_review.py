#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-054-english-multi-turn-naturalness-stress-review"
CHECKPOINT_NAME = "English Multi-Turn Naturalness Stress Review"
SOURCE_CHECKPOINT_ID = "PROD-053E-english-runtime-wording-patch"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
SOURCE_DIR = ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID
CASE_FILE = ROOT / "research" / "experiments" / "cases" / "prod-054-english-multi-turn-naturalness-stress-review.json"

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

FOLLOW_UP_SPECS: dict[str, dict[str, Any]] = {
    "prod-045-manager": {
        "case_goal": "After agreeing to send review material, handle a manager-specific details request without repeating the first turn.",
        "follow_up_customer_utterance": "Send me the details for my manager.",
        "follow_up_stage": "follow-up",
        "expected_second_turn": {
            "sales_difficulty": "written-info-request",
            "next_action": "answer-and-continue",
            "call_control": "bridge-then-continue",
            "response_must_include_any": ["tailor", "send"],
        },
    },
    "prod-045-spouse": {
        "case_goal": "After partner-review relief, handle a written-info request without reusing the same review handoff line.",
        "follow_up_customer_utterance": "Send me information I can review with my partner.",
        "follow_up_stage": "follow-up",
        "expected_second_turn": {
            "sales_difficulty": "written-info-request",
            "next_action": "answer-and-continue",
            "call_control": "bridge-then-continue",
            "response_must_include_any": ["tailor", "send"],
        },
    },
    "prod-053c-product-detail-lookup": {
        "case_goal": "After the bridge response promises a product lookup, the next turn should not repeat the bridge phrase.",
        "follow_up_customer_utterance": "Yes, which exact plan is included?",
        "follow_up_stage": "follow-up",
        "expected_second_turn": {
            "sales_difficulty": "product-detail-lookup",
            "next_action": "continue",
            "call_control": "bridge-then-continue",
            "response_must_include_any": ["plan", "included"],
        },
    },
    "prod-053c-sale-ready-missing-criteria": {
        "case_goal": "If the missing close check needs a human, route safely instead of marking a sale ready.",
        "follow_up_customer_utterance": "I need a human to confirm that check.",
        "follow_up_stage": "follow-up",
        "expected_second_turn": {
            "sales_difficulty": "human-request",
            "next_action": "escalate",
            "call_control": "transfer-or-escalate",
            "response_must_include_any": ["human", "specialist"],
        },
    },
    "prod-053c-trust-gap": {
        "case_goal": "After a trust repair offer, handle a legitimacy verification request through the safe verification path.",
        "follow_up_customer_utterance": "Yes, verify this is legitimate first.",
        "follow_up_stage": "follow-up",
        "expected_second_turn": {
            "sales_difficulty": "scam-safety-boundary",
            "next_action": "create-follow-up-task",
            "call_control": "end-call",
            "response_must_include_any": ["verification path"],
        },
    },
    "prod-053c-price-objection": {
        "case_goal": "After asking whether the issue is price or effort, handle the effort answer without repeating the same question.",
        "follow_up_customer_utterance": "It is about whether this is worth the effort.",
        "follow_up_stage": "follow-up",
        "expected_second_turn": {
            "sales_difficulty": "price-objection",
            "next_action": "ask-follow-up",
            "call_control": "continue-call",
            "response_must_include_any": ["effort", "worth"],
        },
    },
    "prod-053c-unknown-runtime-signal": {
        "case_goal": "After asking for one clarifying question, ask a concrete product-relevant question instead of looping.",
        "follow_up_customer_utterance": "Yes, what is the quick question?",
        "follow_up_stage": "follow-up",
        "expected_second_turn": {
            "sales_difficulty": "unknown-runtime-signal",
            "next_action": "ask-follow-up",
            "call_control": "continue-call",
            "response_must_include_any": ["missed callbacks", "follow-up work"],
        },
    },
    "prod-053c-identity-repair": {
        "case_goal": "After identity repair, handle a details request as written-info rather than restarting identity repair.",
        "follow_up_customer_utterance": "Okay, send me the details.",
        "follow_up_stage": "follow-up",
        "expected_second_turn": {
            "sales_difficulty": "written-info-request",
            "next_action": "answer-and-continue",
            "call_control": "bridge-then-continue",
            "response_must_include_any": ["tailor", "send"],
        },
    },
    "prod-053c-procurement-review": {
        "case_goal": "After procurement-review relief, a written-only confirmation should not repeat the same procurement sentence.",
        "follow_up_customer_utterance": "Send written information only.",
        "follow_up_stage": "procurement-review",
        "expected_second_turn": {
            "sales_difficulty": "procurement-review",
            "next_action": "ask-follow-up",
            "call_control": "continue-call",
            "response_must_include_any": ["send"],
        },
    },
    "prod-053c-existing-provider-gap": {
        "case_goal": "After isolating a provider gap, handle the customer's gap confirmation instead of repeating the gap question.",
        "follow_up_customer_utterance": "Yes, our current provider misses follow-up work.",
        "follow_up_stage": "follow-up",
        "expected_second_turn": {
            "sales_difficulty": "existing-provider-gap",
            "next_action": "ask-follow-up",
            "call_control": "continue-call",
            "response_must_include_any": ["misses", "follow-up work"],
        },
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


def load_promoted_items() -> list[dict[str, Any]]:
    result = read_json(SOURCE_DIR / "result.json")
    if result["validation"]["passed"] is not True:
        raise SystemExit("PROD-053E must pass before PROD-054.")
    return read_json(SOURCE_DIR / "promoted_runtime_responses.json")["items"]


def case_for_promoted_item(item: dict[str, Any]) -> dict[str, Any]:
    source_id = item["case_id"]
    spec = FOLLOW_UP_SPECS.get(source_id)
    base = {
        "case_id": f"prod-054-{source_id}",
        "source_case_id": source_id,
        "source_sales_difficulty": item["sales_difficulty"],
        "source_next_action": item["runtime_next_action"],
        "source_call_control": item["runtime_call_control"],
        "source_agent_response": item["runtime_response"],
        "language": "en",
    }
    if spec:
        expected = dict(spec["expected_second_turn"])
        expected["response_must_not_include_any"] = FORBIDDEN_SECOND_TURN_MARKERS
        return {
            **base,
            "next_turn_mode": "runtime_second_turn",
            "case_goal": spec["case_goal"],
            "follow_up_customer_utterance": spec["follow_up_customer_utterance"],
            "follow_up_customer_input": {
                "input_type": "speech",
                "transcript": spec["follow_up_customer_utterance"],
                "stage": spec["follow_up_stage"],
            },
            "expected_second_turn": expected,
            "terminal_boundary": None,
        }
    return {
        **base,
        "next_turn_mode": "terminal_boundary",
        "case_goal": "The first turn already ended, transferred, scheduled, or logged the call, so no second automated sales turn should be generated.",
        "follow_up_customer_utterance": None,
        "follow_up_customer_input": None,
        "expected_second_turn": None,
        "terminal_boundary": {
            "no_second_agent_turn_expected": True,
            "terminal_call_controls": sorted(TERMINAL_CALL_CONTROLS),
            "reason": "Terminal or routed first-turn call control blocks same-loop continuation.",
        },
    }


def build_cases(promoted_items: list[dict[str, Any]]) -> dict[str, Any]:
    cases = [case_for_promoted_item(item) for item in promoted_items]
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "cases": cases,
    }


def second_turn_decision(case: dict[str, Any]) -> dict[str, Any]:
    second_case = {
        "case_id": f"{case['case_id']}-second-turn",
        "customer_input": case["follow_up_customer_input"],
    }
    return build_runtime_decision(second_case, campaign=BASE_CAMPAIGN)


def evaluate_second_turn(case: dict[str, Any]) -> dict[str, Any]:
    expected = case["expected_second_turn"]
    decision = second_turn_decision(case)
    response = decision["agent_response"]
    issue_codes: list[str] = []
    forbidden = forbidden_marker(response)
    gates = {
        "response_language_en": decision["response_language"] == "en",
        "not_exact_repeat": normalize_text(response) != normalize_text(case["source_agent_response"]),
        "sales_difficulty_match": decision["sales_difficulty"] == expected["sales_difficulty"],
        "next_action_match": decision["next_action"] == expected["next_action"],
        "call_control_match": decision["call_control"] == expected["call_control"],
        "required_marker_match": marker_match(response, expected["response_must_include_any"]),
        "forbidden_marker_absent": forbidden is None,
    }
    for key, passed in gates.items():
        if not passed:
            issue_codes.append(key)
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
        "runtime_second_turn": {
            "response_language": decision["response_language"],
            "sales_difficulty": decision["sales_difficulty"],
            "next_action": decision["next_action"],
            "call_control": decision["call_control"],
            "agent_response": response,
        },
        "stress_gates": gates,
        "stress_gates_passed": not issue_codes,
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


def summarize(second_turns: list[dict[str, Any]], terminal: list[dict[str, Any]]) -> dict[str, Any]:
    second_turn_failures = [item for item in second_turns if not item["stress_gates_passed"]]
    terminal_failures = [item for item in terminal if not item["terminal_boundary_passed"]]
    blocking_ids = sorted({item["source_case_id"] for item in [*second_turn_failures, *terminal_failures]})
    stress_gate_passed = not second_turn_failures and not terminal_failures
    return {
        "source_promoted_response_count": len(second_turns) + len(terminal),
        "runtime_second_turn_case_count": len(second_turns),
        "terminal_boundary_case_count": len(terminal),
        "runtime_second_turn_pass_count": sum(1 for item in second_turns if item["stress_gates_passed"]),
        "runtime_second_turn_failure_count": len(second_turn_failures),
        "terminal_boundary_pass_count": sum(1 for item in terminal if item["terminal_boundary_passed"]),
        "terminal_boundary_failure_count": len(terminal_failures),
        "blocking_finding_count": len(blocking_ids),
        "blocking_case_ids": blocking_ids,
        "stress_gate_passed": stress_gate_passed,
        "runtime_promotion_allowed": False,
        "needs_followup_checkpoint": True,
        **BOUNDARY_FLAGS,
    }


def render_report(second_turns: list[dict[str, Any]], terminal: list[dict[str, Any]], summary: dict[str, Any]) -> str:
    lines = [
        "# PROD-054 English Multi-Turn Naturalness Stress Review",
        "",
        f"Source checkpoint: `{SOURCE_CHECKPOINT_ID}`.",
        "",
        "## Summary",
        "",
        f"- Source promoted responses: `{summary['source_promoted_response_count']}`",
        f"- Runtime second-turn cases: `{summary['runtime_second_turn_case_count']}`",
        f"- Terminal boundary cases: `{summary['terminal_boundary_case_count']}`",
        f"- Runtime second-turn failures: `{summary['runtime_second_turn_failure_count']}`",
        f"- Terminal boundary failures: `{summary['terminal_boundary_failure_count']}`",
        f"- Blocking finding count: `{summary['blocking_finding_count']}`",
        f"- Stress gate passed: `{str(summary['stress_gate_passed']).lower()}`",
        "- Runtime promotion allowed: `false`",
        "",
        "## Blocking Findings",
        "",
    ]
    if summary["blocking_case_ids"]:
        for case_id in summary["blocking_case_ids"]:
            lines.append(f"- `{case_id}`")
    else:
        lines.append("- None.")
    lines.extend(["", "## Runtime Second-Turn Review", ""])
    for item in second_turns:
        lines.extend(
            [
                f"### {item['source_case_id']}",
                "",
                f"- Passed: `{str(item['stress_gates_passed']).lower()}`",
                f"- Goal: {item['case_goal']}",
                f"- Follow-up customer turn: {item['follow_up_customer_utterance']}",
                f"- Issue codes: `{', '.join(item['issue_codes']) if item['issue_codes'] else 'none'}`",
                "",
                "```text",
                item["runtime_second_turn"]["agent_response"],
                "```",
                "",
            ]
        )
    lines.extend(["## Terminal Boundary Review", ""])
    for item in terminal:
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
    lines.extend(
        [
            "## Boundary",
            "",
            "- No provider calls.",
            "- No LLM or LLM judging.",
            "- No private data reads.",
            "- No runtime behavior change.",
            "- No response text behavior change.",
            "- No German exact-phrase promotion or German naturalness claim.",
            "- No production runtime promotion.",
            "",
            "## Next Gate",
            "",
            "`PROD-055` should patch or explicitly defer the blocking second-turn findings before any broader runtime promotion.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    promoted = load_promoted_items()
    cases_payload = build_cases(promoted)
    write_json(CASE_FILE, cases_payload)

    second_turn_cases = [case for case in cases_payload["cases"] if case["next_turn_mode"] == "runtime_second_turn"]
    terminal_cases = [case for case in cases_payload["cases"] if case["next_turn_mode"] == "terminal_boundary"]
    second_turns = [evaluate_second_turn(case) for case in second_turn_cases]
    terminal = [evaluate_terminal_boundary(case) for case in terminal_cases]
    summary = summarize(second_turns, terminal)
    result = {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "validation": {
            "passed": True,
            "stress_gate_passed": summary["stress_gate_passed"],
        },
        "summary": summary,
    }
    write_json(OUT_DIR / "runtime_second_turn_reviews.json", {"checkpoint_id": CHECKPOINT_ID, "items": second_turns})
    write_json(OUT_DIR / "terminal_boundary_reviews.json", {"checkpoint_id": CHECKPOINT_ID, "items": terminal})
    write_json(OUT_DIR / "result.json", result)
    write_text(OUT_DIR / "report.md", render_report(second_turns, terminal, summary))
    print(json.dumps({"checkpoint_id": CHECKPOINT_ID, "validation": result["validation"], "summary": summary}, indent=2))


if __name__ == "__main__":
    main()
