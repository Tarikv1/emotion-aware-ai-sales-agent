#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-055-english-multi-turn-runtime-patch"
CHECKPOINT_NAME = "English Multi-Turn Runtime Patch"
SOURCE_CHECKPOINT_ID = "PROD-054-english-multi-turn-naturalness-stress-review"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
SOURCE_DIR = ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID
CASE_FILE = ROOT / "research" / "experiments" / "cases" / "prod-055-english-multi-turn-runtime-patch.json"

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

FORBIDDEN_PATCH_MARKERS = [
    "i reached voicemail",
    "coverage advice",
    "give coverage advice",
    "give medical advice",
    "low pressure and clarify only what you need",
    "low-pressure and only clarify what you need",
]

BOUNDARY_FLAGS = {
    "runtime_behavior_changed": True,
    "response_text_behavior_changed": True,
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

SOURCE_FINDINGS = [
    {
        "source_case_id": "prod-053c-callback-request",
        "source_issue": "Callback response asks for a time while the first-turn call control ends the call.",
        "source_issue_codes": ["terminal_response_asks_question"],
    },
    {
        "source_case_id": "prod-053c-existing-provider-gap",
        "source_issue": "After the customer confirms the provider gap, runtime repeats the gap-isolation sentence.",
        "source_issue_codes": ["not_exact_repeat", "required_marker_match"],
    },
    {
        "source_case_id": "prod-053c-price-objection",
        "source_issue": "After the customer answers effort rather than price, runtime repeats the price-or-effort question.",
        "source_issue_codes": ["not_exact_repeat"],
    },
    {
        "source_case_id": "prod-053c-procurement-review",
        "source_issue": "After the customer asks for written information only, runtime repeats the procurement-relief sentence.",
        "source_issue_codes": ["not_exact_repeat", "required_marker_match"],
    },
    {
        "source_case_id": "prod-053c-product-detail-lookup",
        "source_issue": "After the customer accepts the product lookup bridge, runtime repeats the bridge phrase.",
        "source_issue_codes": ["not_exact_repeat", "required_marker_match"],
    },
    {
        "source_case_id": "prod-053c-unknown-runtime-signal",
        "source_issue": "After the customer asks what the quick clarifying question is, runtime repeats the clarifying-question preface.",
        "source_issue_codes": ["not_exact_repeat", "required_marker_match"],
    },
]

PATCH_CASES = [
    {
        "case_id": "prod-055-callback-request-call-control",
        "source_case_id": "prod-053c-callback-request",
        "language": "en",
        "patch_mode": "current_first_turn",
        "source_agent_response": "Of course. Do you have a time in mind?",
        "customer_input": {"input_type": "speech", "transcript": "Can you call back later?", "stage": "objection"},
        "expected_runtime_after_patch": {
            "sales_difficulty": "callback-request",
            "next_action": "offer-scheduling",
            "call_control": "continue-call",
            "response_must_include_any": ["time"],
        },
    },
    {
        "case_id": "prod-055-product-detail-followup",
        "source_case_id": "prod-053c-product-detail-lookup",
        "language": "en",
        "patch_mode": "runtime_second_turn",
        "source_agent_response": "One moment. I will check the product details before I answer.",
        "customer_input": {
            "input_type": "speech",
            "transcript": "Yes, which exact plan is included?",
            "stage": "follow-up",
        },
        "expected_runtime_after_patch": {
            "sales_difficulty": "product-detail-lookup",
            "next_action": "continue",
            "call_control": "bridge-then-continue",
            "response_must_include_any": ["plan", "details"],
        },
    },
    {
        "case_id": "prod-055-price-effort-followup",
        "source_case_id": "prod-053c-price-objection",
        "language": "en",
        "patch_mode": "runtime_second_turn",
        "source_agent_response": "That makes sense. Is the main concern price, or whether it is worth the effort?",
        "customer_input": {
            "input_type": "speech",
            "transcript": "It is about whether this is worth the effort.",
            "stage": "follow-up",
        },
        "expected_runtime_after_patch": {
            "sales_difficulty": "price-objection",
            "next_action": "ask-follow-up",
            "call_control": "continue-call",
            "response_must_include_any": ["effort", "worth"],
        },
    },
    {
        "case_id": "prod-055-unknown-signal-followup",
        "source_case_id": "prod-053c-unknown-runtime-signal",
        "language": "en",
        "patch_mode": "runtime_second_turn",
        "source_agent_response": "Thanks. Can I ask one quick clarifying question?",
        "customer_input": {
            "input_type": "speech",
            "transcript": "Yes, what is the quick question?",
            "stage": "follow-up",
        },
        "expected_runtime_after_patch": {
            "sales_difficulty": "unknown-runtime-signal",
            "next_action": "ask-follow-up",
            "call_control": "continue-call",
            "response_must_include_any": ["missed callbacks", "follow-up work"],
        },
    },
    {
        "case_id": "prod-055-procurement-written-only-followup",
        "source_case_id": "prod-053c-procurement-review",
        "language": "en",
        "patch_mode": "runtime_second_turn",
        "source_agent_response": "Sure. I can keep this to written review information. Nothing firm today.",
        "customer_input": {
            "input_type": "speech",
            "transcript": "Send written information only.",
            "stage": "procurement-review",
        },
        "expected_runtime_after_patch": {
            "sales_difficulty": "procurement-review",
            "next_action": "ask-follow-up",
            "call_control": "continue-call",
            "response_must_include_any": ["send", "written information"],
        },
    },
    {
        "case_id": "prod-055-existing-provider-gap-followup",
        "source_case_id": "prod-053c-existing-provider-gap",
        "language": "en",
        "patch_mode": "runtime_second_turn",
        "source_agent_response": "I won't claim this replaces your provider. The useful check is whether there is a gap it does not cover.",
        "customer_input": {
            "input_type": "speech",
            "transcript": "Yes, our current provider misses follow-up work.",
            "stage": "follow-up",
        },
        "expected_runtime_after_patch": {
            "sales_difficulty": "existing-provider-gap",
            "next_action": "ask-follow-up",
            "call_control": "continue-call",
            "response_must_include_any": ["misses", "follow-up work"],
        },
    },
]


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
    for marker in FORBIDDEN_PATCH_MARKERS:
        if normalize_text(marker) in normalized:
            return marker
    return None


def load_source_result() -> dict[str, Any]:
    source = read_json(SOURCE_DIR / "result.json")
    if source["validation"]["passed"] is not True or source["validation"]["stress_gate_passed"] is not False:
        raise SystemExit("PROD-054 must contain the source blocking findings before PROD-055.")
    return source


def build_case_file() -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "source_findings": SOURCE_FINDINGS,
        "cases": PATCH_CASES,
    }


def evaluate_patch_case(case: dict[str, Any]) -> dict[str, Any]:
    decision = build_runtime_decision(
        {
            "case_id": case["case_id"],
            "customer_input": case["customer_input"],
        },
        campaign=BASE_CAMPAIGN,
    )
    expected = case["expected_runtime_after_patch"]
    response = decision["agent_response"]
    forbidden = forbidden_marker(response)
    gates = {
        "response_language_en": decision["response_language"] == "en",
        "sales_difficulty_match": decision["sales_difficulty"] == expected["sales_difficulty"],
        "next_action_match": decision["next_action"] == expected["next_action"],
        "call_control_match": decision["call_control"] == expected["call_control"],
        "required_marker_match": marker_match(response, expected["response_must_include_any"]),
        "forbidden_marker_absent": forbidden is None,
        "terminal_question_coherent": not (
            decision["call_control"] in TERMINAL_CALL_CONTROLS and response.strip().endswith("?")
        ),
    }
    if case["patch_mode"] == "runtime_second_turn":
        gates["not_exact_repeat"] = normalize_text(response) != normalize_text(case["source_agent_response"])
    issue_codes = [key for key, passed in gates.items() if not passed]
    if forbidden:
        issue_codes.append(f"forbidden_marker:{forbidden}")
    return {
        "case_id": case["case_id"],
        "source_case_id": case["source_case_id"],
        "patch_mode": case["patch_mode"],
        "source_agent_response": case["source_agent_response"],
        "customer_input": case["customer_input"],
        "expected_runtime_after_patch": expected,
        "runtime_decision": {
            "response_language": decision["response_language"],
            "sales_difficulty": decision["sales_difficulty"],
            "next_action": decision["next_action"],
            "call_control": decision["call_control"],
            "agent_response": response,
        },
        "patch_gates": gates,
        "passed": not issue_codes,
        "issue_codes": issue_codes,
    }


def summarize(source: dict[str, Any], reviews: list[dict[str, Any]]) -> dict[str, Any]:
    failed = [item for item in reviews if not item["passed"]]
    source_ids = source["summary"]["blocking_case_ids"]
    return {
        "source_blocking_finding_count": len(source_ids),
        "source_blocking_case_ids": source_ids,
        "patched_runtime_review_count": len(reviews),
        "post_patch_blocking_finding_count": len(failed),
        "post_patch_blocking_case_ids": [item["source_case_id"] for item in failed],
        "all_patch_cases_passed": not failed,
        "runtime_promotion_allowed": False,
        **BOUNDARY_FLAGS,
    }


def render_report(source_findings: list[dict[str, Any]], reviews: list[dict[str, Any]], summary: dict[str, Any]) -> str:
    lines = [
        "# PROD-055 English Multi-Turn Runtime Patch",
        "",
        f"Source checkpoint: `{SOURCE_CHECKPOINT_ID}`.",
        "",
        "## Summary",
        "",
        f"- Source blocking findings: `{summary['source_blocking_finding_count']}`",
        f"- Patched runtime reviews: `{summary['patched_runtime_review_count']}`",
        f"- Post-patch blocking findings: `{summary['post_patch_blocking_finding_count']}`",
        f"- Runtime behavior changed: `{str(summary['runtime_behavior_changed']).lower()}`",
        f"- Response text behavior changed: `{str(summary['response_text_behavior_changed']).lower()}`",
        "- Production runtime promotion allowed: `false`",
        "",
        "## Source Findings",
        "",
    ]
    for item in source_findings:
        lines.append(f"- `{item['source_case_id']}`: {item['source_issue']}")
    lines.extend(["", "## Patch Reviews", ""])
    for item in reviews:
        lines.extend(
            [
                f"### {item['source_case_id']}",
                "",
                f"- Passed: `{str(item['passed']).lower()}`",
                f"- Patch mode: `{item['patch_mode']}`",
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
            "- No provider calls.",
            "- No LLM or LLM judging.",
            "- No private data reads.",
            "- No retrieval enablement.",
            "- No German exact-phrase promotion or German naturalness claim.",
            "- No payment collection, contract signing, or production runtime promotion.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    source = load_source_result()
    case_payload = build_case_file()
    write_json(CASE_FILE, case_payload)
    reviews = [evaluate_patch_case(case) for case in PATCH_CASES]
    summary = summarize(source, reviews)
    result = {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "validation": {"passed": summary["all_patch_cases_passed"]},
        "summary": summary,
    }
    write_json(OUT_DIR / "source_blocking_findings.json", {"checkpoint_id": CHECKPOINT_ID, "items": SOURCE_FINDINGS})
    write_json(OUT_DIR / "patched_runtime_reviews.json", {"checkpoint_id": CHECKPOINT_ID, "items": reviews})
    write_json(OUT_DIR / "result.json", result)
    write_text(OUT_DIR / "report.md", render_report(SOURCE_FINDINGS, reviews, summary))
    print(json.dumps({"checkpoint_id": CHECKPOINT_ID, "validation": result["validation"], "summary": summary}, indent=2))


if __name__ == "__main__":
    main()
