#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

if str(ROOT := Path(__file__).resolve().parents[1]) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.core.dialogue_reasoner import (  # noqa: E402
    DIALOGUE_REASONER_ID,
    REASONER_SCHEMA_FIELDS,
    provider_boundary_packet,
    reason_about_turn,
)
from scripts.run_live_demo_001_agent_voice_call import DEFAULT_CASES_PATH, load_campaign  # noqa: E402


CASES_PATH = ROOT / "research" / "experiments" / "cases" / "dialogue-reasoner-001-live-demo-failures.json"
OUTPUT_DIR = ROOT / "research" / "experiments" / "generated" / DIALOGUE_REASONER_ID
RESULT_PATH = OUTPUT_DIR / "result.json"
REPORT_PATH = OUTPUT_DIR / "report.md"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def prior_turns_to_session_state(prior_turns: list[dict[str, Any]]) -> dict[str, Any]:
    turns = []
    for turn in prior_turns:
        turns.append(
            {
                "transcript": str(turn.get("transcript") or ""),
                "summary": {
                    "final_response": str(turn.get("final_response") or ""),
                    "sales_difficulty": str(turn.get("sales_difficulty") or ""),
                    "call_control": str(turn.get("call_control") or ""),
                },
                "continuity": {
                    "reason": str(turn.get("continuity_reason") or ""),
                    "dialogue_focus": str(turn.get("dialogue_focus") or ""),
                    "applied": True,
                },
            }
        )
    return {"turns": turns}


def compare_expected(reasoning: dict[str, Any], expected: dict[str, Any]) -> dict[str, Any]:
    mismatches = {}
    for key in [
        "dialogue_act",
        "buyer_intent",
        "resolved_topic",
        "sales_stage",
        "response_strategy",
        "safety_boundary",
    ]:
        if reasoning.get(key) != expected.get(key):
            mismatches[key] = {"expected": expected.get(key), "actual": reasoning.get(key)}
    return mismatches


def run_case(case: dict[str, Any], campaign: dict[str, Any]) -> dict[str, Any]:
    session_state = prior_turns_to_session_state(case.get("prior_turns") or [])
    reasoning = reason_about_turn(
        str(case["transcript"]),
        session_state,
        campaign,
        mode="baseline",
    )
    mismatches = compare_expected(reasoning, case["expected"])
    return {
        "case_id": case["case_id"],
        "transcript": case["transcript"],
        "prior_turn_count": len(case.get("prior_turns") or []),
        "reasoning": reasoning,
        "expected": case["expected"],
        "pass": not mismatches,
        "mismatches": mismatches,
    }


def coverage(case_results: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "dialogue_acts": sorted({case["reasoning"]["dialogue_act"] for case in case_results}),
        "buyer_intents": sorted({case["reasoning"]["buyer_intent"] for case in case_results}),
        "sales_stages": sorted({case["reasoning"]["sales_stage"] for case in case_results}),
        "response_strategies": sorted({case["reasoning"]["response_strategy"] for case in case_results}),
        "safety_boundaries": sorted({case["reasoning"]["safety_boundary"] for case in case_results}),
    }


def render_report(payload: dict[str, Any]) -> str:
    lines = [
        "# DIALOGUE-REASONER-001 Structured Runtime Reasoner",
        "",
        f"- Mode: `{payload['mode']}`",
        f"- Cases: `{payload['passed_count']}/{payload['case_count']}`",
        f"- Provider calls made: `{str(payload['provider_calls_made']).lower()}`",
        f"- Text sent to provider: `{str(payload['text_sent_to_provider']).lower()}`",
        f"- Live-demo response behavior changed: `{str(payload['live_demo_response_behavior_changed']).lower()}`",
        f"- Opens PROD-102: `{str(payload['opens_prod_102']).lower()}`",
        "",
        "## Coverage",
        "",
    ]
    for key, values in payload["coverage"].items():
        lines.append(f"- {key}: `{', '.join(values)}`")
    lines.extend(["", "## Cases", ""])
    for case in payload["case_results"]:
        status = "pass" if case["pass"] else "fail"
        reasoning = case["reasoning"]
        lines.append(
            f"- `{case['case_id']}`: `{status}` -> "
            f"{reasoning['dialogue_act']} / {reasoning['resolved_topic']} / {reasoning['response_strategy']}"
        )
    lines.append("")
    return "\n".join(lines)


def run() -> dict[str, Any]:
    case_payload = read_json(CASES_PATH)
    campaign = load_campaign(str(case_payload["default_campaign_id"]), DEFAULT_CASES_PATH)
    case_results = [run_case(case, campaign) for case in case_payload["cases"]]
    failed_cases = [case["case_id"] for case in case_results if not case["pass"]]
    boundary = provider_boundary_packet(mode="baseline")
    payload = {
        "experiment_id": DIALOGUE_REASONER_ID,
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "mode": "baseline",
        "default_llm_enabled": False,
        "provider_calls_made": boundary["provider_calls_made"],
        "text_sent_to_provider": boundary["text_sent_to_provider"],
        "opens_prod_102": False,
        "live_demo_response_behavior_changed": False,
        "baseline_live_demo_001_preserved": "not-run-by-reasoner-runner",
        "reasoner_schema": {
            "version": 1,
            "fields": REASONER_SCHEMA_FIELDS,
        },
        "case_source": str(CASES_PATH.relative_to(ROOT)).replace("\\", "/"),
        "case_count": len(case_results),
        "passed_count": sum(1 for case in case_results if case["pass"]),
        "failed_cases": failed_cases,
        "coverage": coverage(case_results),
        "runtime_modules_added": ["runtime.core.dialogue_reasoner"],
        "runtime_dependencies": [
            "runtime.core.live_voice_session_policy",
            "scripts.run_live_demo_001_agent_voice_call.load_campaign",
        ],
        "case_results": case_results,
    }
    write_json(RESULT_PATH, payload)
    write_text(REPORT_PATH, render_report(payload))
    return payload


def main() -> None:
    payload = run()
    print(json.dumps(
        {
            "experiment_id": payload["experiment_id"],
            "case_count": payload["case_count"],
            "passed_count": payload["passed_count"],
            "failed_cases": payload["failed_cases"],
            "provider_calls_made": payload["provider_calls_made"],
            "opens_prod_102": payload["opens_prod_102"],
        },
        indent=2,
        ensure_ascii=False,
    ))


if __name__ == "__main__":
    main()
