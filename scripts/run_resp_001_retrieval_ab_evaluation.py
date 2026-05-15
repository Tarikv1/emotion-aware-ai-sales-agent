#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from runtime.entrypoints.generate_guarded_response import (
    DEFAULT_RETRIEVAL_ACCEPTABLE_MS,
    DEFAULT_RETRIEVAL_MIN_SCORE,
    DEFAULT_RETRIEVAL_REGISTRY,
    DEFAULT_RETRIEVAL_TARGET_MS,
    build_guarded_response_packet,
)
from runtime.core.realtime_turns import load_realtime_cases, normalize_response_language
from runtime.entrypoints.realtime_turn_cli import find_campaign


DEFAULT_CASES = ROOT / "research" / "experiments" / "cases" / "prod-005-realtime-latency-call-control.json"
DEFAULT_OUT_DIR = ROOT / "research" / "experiments" / "generated" / "RESP-001-retrieval-ab-evaluation"


def resolve_path(path_text: str | None, default: Path) -> Path:
    if not path_text:
        return default
    path = Path(path_text)
    return path if path.is_absolute() else ROOT / path


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def forbidden_response_text(payload: dict[str, Any]) -> bool:
    text = json.dumps(payload, ensure_ascii=False).lower().replace("\\", "/")
    forbidden = [
        "source_excerpt",
        "data/private",
        "data/private-restricted",
        "you are angry",
        "you are anxious",
        "i can tell you feel",
        "i know exactly how you feel",
        "only today",
        "discount ends",
    ]
    return any(token in text for token in forbidden)


def output_language_matches(packet: dict[str, Any]) -> bool:
    campaign_language = normalize_response_language(packet["campaign"].get("language"))
    response_language = normalize_response_language(packet["decision_snapshot"].get("response_language"))
    return campaign_language == response_language


def case_input(case: dict[str, Any]) -> dict[str, Any]:
    customer_input = case.get("customer_input", {})
    return {
        "stage": customer_input.get("stage", "relevance-check"),
        "input_type": customer_input.get("input_type", "speech-final"),
        "transcript": customer_input.get("transcript", ""),
        "silence_count": int(customer_input.get("silence_count", 0)),
    }


def run_packet(
    *,
    campaign: dict[str, Any],
    case: dict[str, Any],
    retrieval_enabled: bool,
    registry_path: Path,
    max_results: int,
    min_score: int,
    target_latency_ms: int,
    acceptable_latency_ms: int,
) -> dict[str, Any]:
    inputs = case_input(case)
    return build_guarded_response_packet(
        campaign=campaign,
        stage=inputs["stage"],
        input_type=inputs["input_type"],
        transcript=inputs["transcript"],
        silence_count=inputs["silence_count"],
        retrieval_enabled=retrieval_enabled,
        retrieval_registry_path=registry_path if retrieval_enabled else None,
        retrieval_max_results=max_results,
        retrieval_min_score=min_score,
        retrieval_target_latency_ms=target_latency_ms,
        retrieval_acceptable_latency_ms=acceptable_latency_ms,
    )


def summarize_case(case: dict[str, Any], no_retrieval: dict[str, Any], with_retrieval: dict[str, Any]) -> dict[str, Any]:
    retrieval = with_retrieval["retrieval"]
    policy_response = no_retrieval["policy_response"]
    core_response = no_retrieval["final_response"]
    rag_response = with_retrieval["final_response"]
    blocked_expected = no_retrieval["decision_snapshot"]["sales_difficulty"] in {
        "do-not-call",
        "human-request",
        "voicemail",
        "repeated-silence",
        "scheduling-confirmation",
    }
    safe = (
        no_retrieval["validation"]["passed"]
        and with_retrieval["validation"]["passed"]
        and output_language_matches(no_retrieval)
        and output_language_matches(with_retrieval)
        and not forbidden_response_text(no_retrieval)
        and not forbidden_response_text(with_retrieval)
        and with_retrieval["core_pack"]["campaign_facts_override_rag"] is True
    )
    if blocked_expected:
        safe = safe and retrieval["retrieval_used_in_runtime"] is False
    return {
        "case_id": case["case_id"],
        "case_title": case.get("case_title", ""),
        "campaign_id": case["campaign_id"],
        "sales_difficulty": no_retrieval["decision_snapshot"]["sales_difficulty"],
        "call_control": no_retrieval["decision_snapshot"]["call_control"],
        "policy_response": policy_response,
        "core_playbook_response": core_response,
        "live_rag_response": rag_response,
        "core_changed_from_policy": core_response != policy_response,
        "rag_changed_from_core": rag_response != core_response,
        "retrieval_status": retrieval["status"],
        "retrieval_used_in_runtime": retrieval["retrieval_used_in_runtime"],
        "retrieved_item_ids": retrieval["retrieved_item_ids"],
        "retrieval_elapsed_ms": retrieval["latency"]["elapsed_ms"],
        "retrieval_target_ms": retrieval["latency"]["target_ms"],
        "retrieval_acceptable_ms": retrieval["latency"]["acceptable_ms"],
        "validation_passed": with_retrieval["validation"]["passed"],
        "language_match": output_language_matches(with_retrieval),
        "safe": safe,
        "blocked_expected": blocked_expected,
    }


def build_summary(rows: list[dict[str, Any]], started_at: float, completed_at: float) -> dict[str, Any]:
    case_count = len(rows)
    influenced = [row for row in rows if row["retrieval_used_in_runtime"]]
    blocked = [row for row in rows if row["retrieval_status"] == "blocked"]
    no_match = [row for row in rows if row["retrieval_status"] == "no_match"]
    unsafe = [row for row in rows if not row["safe"]]
    latencies = [row["retrieval_elapsed_ms"] for row in rows]
    over_target = [row for row in rows if row["retrieval_elapsed_ms"] > row["retrieval_target_ms"]]
    over_acceptable = [row for row in rows if row["retrieval_elapsed_ms"] > row["retrieval_acceptable_ms"]]
    return {
        "case_count": case_count,
        "safe_case_count": case_count - len(unsafe),
        "unsafe_case_count": len(unsafe),
        "retrieval_influenced_count": len(influenced),
        "retrieval_blocked_count": len(blocked),
        "retrieval_no_match_count": len(no_match),
        "retrieval_over_target_count": len(over_target),
        "retrieval_over_acceptable_count": len(over_acceptable),
        "max_retrieval_elapsed_ms": max(latencies) if latencies else 0,
        "avg_retrieval_elapsed_ms": round(sum(latencies) / len(latencies), 2) if latencies else 0,
        "total_elapsed_ms": int((completed_at - started_at) * 1000),
    }


def decision(summary: dict[str, Any]) -> str:
    if summary["unsafe_case_count"]:
        return "revise_before_runtime_use"
    if summary["retrieval_over_acceptable_count"]:
        return "revise_latency_fallback_before_runtime_use"
    if summary["retrieval_influenced_count"] == 0:
        return "keep_core_playbook_and_raise_retrieval_relevance"
    return "keep_hybrid_opt_in_and_run_larger_call_simulation"


def render_report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# RESP-001 Retrieval A/B Evaluation",
        "",
        "This controlled local run compares the existing policy response, the always-on core sales delivery playbook, and opt-in live RAG retrieval on the frozen PROD-005 realtime cases.",
        "",
        "## Experiment",
        "",
        "- Hypothesis: live RAG should add relevant advisory hints without changing protected text, campaign facts, language, or compliance behavior.",
        f"- Cases: `{summary['case_count']}` frozen PROD-005 cases",
        "- Baseline: policy response from deterministic realtime core",
        "- Variant A: core sales delivery playbook with retrieval disabled",
        "- Variant B: core sales delivery playbook plus opt-in live RAG",
        f"- Retrieval latency target: `{payload['config']['target_latency_ms']} ms`",
        f"- Retrieval latency acceptable: `{payload['config']['acceptable_latency_ms']} ms`",
        f"- Retrieval min score: `{payload['config']['min_score']}`",
        "",
        "## Result",
        "",
        f"- Safe cases: `{summary['safe_case_count']}/{summary['case_count']}`",
        f"- Retrieval influenced responses: `{summary['retrieval_influenced_count']}`",
        f"- Retrieval blocked by guardrails: `{summary['retrieval_blocked_count']}`",
        f"- Retrieval no-match cases: `{summary['retrieval_no_match_count']}`",
        f"- Max retrieval latency: `{summary['max_retrieval_elapsed_ms']} ms`",
        f"- Average retrieval latency: `{summary['avg_retrieval_elapsed_ms']} ms`",
        f"- Over 150 ms target: `{summary['retrieval_over_target_count']}`",
        f"- Over 300 ms acceptable: `{summary['retrieval_over_acceptable_count']}`",
        f"- Decision: `{payload['decision']}`",
        "",
        "## Case Table",
        "",
        "| Case | Difficulty | Retrieval | Used | Latency | Safe | Change |",
        "| --- | --- | --- | --- | ---: | --- | --- |",
    ]
    for row in payload["cases"]:
        change = "RAG changed core" if row["rag_changed_from_core"] else ("core changed policy" if row["core_changed_from_policy"] else "no wording change")
        lines.append(
            "| {case_id} | {difficulty} | {status} | {used} | {latency} ms | {safe} | {change} |".format(
                case_id=row["case_id"],
                difficulty=row["sales_difficulty"],
                status=row["retrieval_status"],
                used=row["retrieval_used_in_runtime"],
                latency=row["retrieval_elapsed_ms"],
                safe=row["safe"],
                change=change,
            )
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "Keep live retrieval opt-in for now. The test checks safety and routing behavior; it does not prove better appointment-setting yet because these are deterministic single-turn cases, not full call outcomes.",
            "",
            "## Next Gate",
            "",
            "Run a larger scripted call simulation with scored objection resolution and next-step quality before making live RAG default for any campaign.",
        ]
    )
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a local RESP-001 retrieval A/B evaluation.")
    parser.add_argument("--cases", default=str(DEFAULT_CASES), help="Frozen realtime case file.")
    parser.add_argument("--registry", default=str(DEFAULT_RETRIEVAL_REGISTRY), help="RAG-017 registry JSON file.")
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR), help="Output directory for result JSON and report.")
    parser.add_argument("--retrieval-max-results", type=int, default=4, help="Maximum retrieved advisory hints.")
    parser.add_argument("--retrieval-min-score", type=int, default=DEFAULT_RETRIEVAL_MIN_SCORE, help="Minimum retrieval score.")
    parser.add_argument("--retrieval-target-latency-ms", type=int, default=DEFAULT_RETRIEVAL_TARGET_MS)
    parser.add_argument("--retrieval-acceptable-latency-ms", type=int, default=DEFAULT_RETRIEVAL_ACCEPTABLE_MS)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cases_path = resolve_path(args.cases, DEFAULT_CASES)
    registry_path = resolve_path(args.registry, DEFAULT_RETRIEVAL_REGISTRY)
    out_dir = resolve_path(args.out_dir, DEFAULT_OUT_DIR)
    campaigns, cases = load_realtime_cases(cases_path)
    started_at = time.perf_counter()
    rows: list[dict[str, Any]] = []
    for case in cases:
        campaign = find_campaign(campaigns, case["campaign_id"])
        no_retrieval = run_packet(
            campaign=campaign,
            case=case,
            retrieval_enabled=False,
            registry_path=registry_path,
            max_results=args.retrieval_max_results,
            min_score=args.retrieval_min_score,
            target_latency_ms=args.retrieval_target_latency_ms,
            acceptable_latency_ms=args.retrieval_acceptable_latency_ms,
        )
        with_retrieval = run_packet(
            campaign=campaign,
            case=case,
            retrieval_enabled=True,
            registry_path=registry_path,
            max_results=args.retrieval_max_results,
            min_score=args.retrieval_min_score,
            target_latency_ms=args.retrieval_target_latency_ms,
            acceptable_latency_ms=args.retrieval_acceptable_latency_ms,
        )
        rows.append(summarize_case(case, no_retrieval, with_retrieval))
    completed_at = time.perf_counter()
    payload = {
        "experiment_id": "RESP-001-retrieval-ab-evaluation",
        "provider_calls_made": False,
        "private_customer_data_used": False,
        "config": {
            "cases_path": str(cases_path.relative_to(ROOT)),
            "registry_path": str(registry_path.relative_to(ROOT)),
            "max_results": args.retrieval_max_results,
            "min_score": args.retrieval_min_score,
            "target_latency_ms": args.retrieval_target_latency_ms,
            "acceptable_latency_ms": args.retrieval_acceptable_latency_ms,
        },
        "summary": build_summary(rows, started_at, completed_at),
        "decision": "",
        "cases": rows,
    }
    payload["decision"] = decision(payload["summary"])
    write_json(out_dir / "result.json", payload)
    write_text(out_dir / "report.md", render_report(payload))
    print(json.dumps(payload, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
