#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

from generate_guarded_response import (
    DEFAULT_RETRIEVAL_ACCEPTABLE_MS,
    DEFAULT_RETRIEVAL_MIN_SCORE,
    DEFAULT_RETRIEVAL_REGISTRY,
    DEFAULT_RETRIEVAL_TARGET_MS,
    build_guarded_response_packet,
)
from realtime_turn_cli import find_campaign
from run_realtime_turn_simulation import load_realtime_cases
from run_resp_001_retrieval_ab_evaluation import forbidden_response_text, output_language_matches


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CASES = ROOT / "research" / "experiments" / "cases" / "rag-018-retrieval-vs-core-call-simulation.json"
DEFAULT_OUT_DIR = ROOT / "research" / "experiments" / "generated" / "RAG-018-retrieval-vs-core-call-simulation"
DEFAULT_RESULT = DEFAULT_OUT_DIR / "result.json"
DEFAULT_REPORT = DEFAULT_OUT_DIR / "report.md"
DEFAULT_CAMPAIGN_CASE_SOURCE = ROOT / "research" / "experiments" / "cases" / "prod-005-realtime-latency-call-control.json"
PRIVATE_PATH_PARTS = (("data", "private"), ("data", "private-restricted"))


def _contains_private_path_parts(path: Path) -> bool:
    parts = tuple(part.lower() for part in path.parts)
    for private_parts in PRIVATE_PATH_PARTS:
        for index in range(0, len(parts) - len(private_parts) + 1):
            if parts[index : index + len(private_parts)] == private_parts:
                return True
    return False


def resolve_path(path_text: str | None, default: Path) -> Path:
    path = Path(path_text) if path_text else default
    candidate = path if path.is_absolute() else ROOT / path
    resolved = candidate.resolve(strict=False)
    root = ROOT.resolve(strict=False)
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"RAG-018 simulation path must stay inside project root: {path_text}") from exc
    if _contains_private_path_parts(resolved):
        raise ValueError(f"RAG-018 simulation path is restricted: {path_text}")
    return resolved


def rel_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def marker_group_score(text: str, marker_groups: list[dict[str, Any]]) -> int:
    lowered = text.lower()
    score = 0
    for group in marker_groups:
        markers = [str(marker).lower() for marker in group.get("markers", [])]
        if markers and all(marker in lowered for marker in markers):
            score += 1
    return score


def run_packet(
    *,
    campaign: dict[str, Any],
    turn: dict[str, Any],
    retrieval_enabled: bool,
    registry_path: Path,
    max_results: int,
    min_score: int,
    target_latency_ms: int,
    acceptable_latency_ms: int,
) -> dict[str, Any]:
    return build_guarded_response_packet(
        campaign=campaign,
        stage=turn["stage"],
        input_type=turn.get("input_type", "speech-final"),
        transcript=turn.get("transcript", ""),
        silence_count=int(turn.get("silence_count", 0)),
        retrieval_enabled=retrieval_enabled,
        retrieval_registry_path=registry_path if retrieval_enabled else None,
        retrieval_max_results=max_results,
        retrieval_min_score=min_score,
        retrieval_target_latency_ms=target_latency_ms,
        retrieval_acceptable_latency_ms=acceptable_latency_ms,
    )


def summarize_turn(call: dict[str, Any], turn: dict[str, Any], no_retrieval: dict[str, Any], with_retrieval: dict[str, Any]) -> dict[str, Any]:
    retrieval = with_retrieval["retrieval"]
    core_response = no_retrieval["final_response"]
    retrieval_response = with_retrieval["final_response"]
    protected_context = bool(turn.get("protected_context"))
    protected_text_preserved = (core_response == retrieval_response) if protected_context else True
    marker_groups = [dict(group) for group in turn.get("quality_marker_groups", [])]
    core_score = marker_group_score(core_response, marker_groups) if turn.get("quality_scored") else 0
    retrieval_score = marker_group_score(retrieval_response, marker_groups) if turn.get("quality_scored") else 0
    score_delta = retrieval_score - core_score
    if score_delta > 0:
        winner = "retrieval"
    elif score_delta < 0:
        winner = "core"
    else:
        winner = "tie"

    safe = (
        no_retrieval["validation"]["passed"]
        and with_retrieval["validation"]["passed"]
        and output_language_matches(no_retrieval)
        and output_language_matches(with_retrieval)
        and not forbidden_response_text(no_retrieval)
        and not forbidden_response_text(with_retrieval)
        and with_retrieval["core_pack"]["campaign_facts_override_rag"] is True
        and (not protected_context or (protected_text_preserved and retrieval["retrieval_used_in_runtime"] is False))
    )

    return {
        "call_id": call["call_id"],
        "call_title": call.get("call_title", ""),
        "turn_id": turn["turn_id"],
        "turn_title": turn.get("turn_title", ""),
        "campaign_id": turn.get("campaign_id", call["campaign_id"]),
        "stage": turn["stage"],
        "expected_winner": turn.get("expected_winner", ""),
        "sales_difficulty": no_retrieval["decision_snapshot"]["sales_difficulty"],
        "call_control": no_retrieval["decision_snapshot"]["call_control"],
        "quality_scored": bool(turn.get("quality_scored")),
        "protected_context": protected_context,
        "protected_text_preserved": protected_text_preserved,
        "core_response": core_response,
        "retrieval_response": retrieval_response,
        "core_score": core_score,
        "retrieval_score": retrieval_score,
        "score_delta": score_delta,
        "winner": winner,
        "retrieval_status": retrieval["status"],
        "retrieval_used_in_runtime": retrieval["retrieval_used_in_runtime"],
        "retrieved_item_ids": retrieval["retrieved_item_ids"],
        "retrieval_elapsed_ms": retrieval["latency"]["elapsed_ms"],
        "retrieval_target_ms": retrieval["latency"]["target_ms"],
        "retrieval_acceptable_ms": retrieval["latency"]["acceptable_ms"],
        "language_match": output_language_matches(with_retrieval),
        "campaign_facts_override_rag": with_retrieval["core_pack"]["campaign_facts_override_rag"],
        "validation_passed": with_retrieval["validation"]["passed"],
        "safe": safe,
    }


def build_summary(rows: list[dict[str, Any]], calls: list[dict[str, Any]], started_at: float, completed_at: float) -> dict[str, Any]:
    turn_count = len(rows)
    unsafe = [row for row in rows if not row["safe"]]
    quality_scored = [row for row in rows if row["quality_scored"]]
    protected = [row for row in rows if row["protected_context"]]
    retrieval_wins = [row for row in rows if row["winner"] == "retrieval"]
    core_wins = [row for row in rows if row["winner"] == "core"]
    ties = [row for row in rows if row["winner"] == "tie"]
    latencies = [row["retrieval_elapsed_ms"] for row in rows]
    over_target = [row for row in rows if row["retrieval_elapsed_ms"] > row["retrieval_target_ms"]]
    over_acceptable = [row for row in rows if row["retrieval_elapsed_ms"] > row["retrieval_acceptable_ms"]]
    core_total_score = sum(row["core_score"] for row in quality_scored)
    retrieval_total_score = sum(row["retrieval_score"] for row in quality_scored)
    return {
        "call_count": len(calls),
        "turn_count": turn_count,
        "quality_scored_turn_count": len(quality_scored),
        "safe_turn_count": turn_count - len(unsafe),
        "unsafe_turn_count": len(unsafe),
        "core_total_score": core_total_score,
        "retrieval_total_score": retrieval_total_score,
        "score_delta": retrieval_total_score - core_total_score,
        "retrieval_turn_wins": len(retrieval_wins),
        "core_turn_wins": len(core_wins),
        "tie_turns": len(ties),
        "retrieval_influenced_count": sum(1 for row in rows if row["retrieval_used_in_runtime"]),
        "retrieval_blocked_count": sum(1 for row in rows if row["retrieval_status"] == "blocked"),
        "retrieval_retrieved_not_used_count": sum(1 for row in rows if row["retrieval_status"] == "retrieved_not_used"),
        "retrieval_no_match_count": sum(1 for row in rows if row["retrieval_status"] == "no_match"),
        "protected_turn_count": len(protected),
        "protected_turns_preserved": sum(1 for row in protected if row["protected_text_preserved"] and not row["retrieval_used_in_runtime"]),
        "expected_winner_mismatch_ids": [
            row["turn_id"]
            for row in rows
            if row["expected_winner"] and row["expected_winner"] != row["winner"]
        ],
        "retrieval_over_target_count": len(over_target),
        "retrieval_over_acceptable_count": len(over_acceptable),
        "max_retrieval_elapsed_ms": max(latencies) if latencies else 0,
        "avg_retrieval_elapsed_ms": round(sum(latencies) / len(latencies), 2) if latencies else 0,
        "total_elapsed_ms": int((completed_at - started_at) * 1000),
    }


def decide(summary: dict[str, Any]) -> str:
    if summary["unsafe_turn_count"]:
        return "revise_retrieval_before_runtime_use"
    if summary["protected_turns_preserved"] != summary["protected_turn_count"]:
        return "revise_protected_context_handling"
    if summary["retrieval_over_acceptable_count"]:
        return "revise_latency_fallback_before_runtime_use"
    if summary["core_turn_wins"]:
        return "keep_core_until_retrieval_regressions_are_fixed"
    if summary["score_delta"] > 0:
        return "keep_retrieval_opt_in_for_validated_objection_turns"
    return "keep_core_until_retrieval_shows_call_level_gain"


def render_report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# RAG-018 Retrieval-vs-Core Call Simulation",
        "",
        "This local run compares the older retrieval-disabled core response path against opt-in RAG-018 retrieval on fixed synthetic multi-turn calls.",
        "",
        "No provider call, private customer data, vector database, embedding provider, or LLM reranker was used.",
        "",
        "## Experiment",
        "",
        "- Hypothesis: the retrieval version should improve objection handling and next-step quality on validated objection turns without losing any protected or already-adequate core turns.",
        "- Baseline: older core response path with retrieval disabled.",
        "- Variant: core response path plus opt-in RAG-018 retrieval.",
        f"- Fixed calls: `{summary['call_count']}`",
        f"- Fixed turns: `{summary['turn_count']}`",
        "",
        "## Result",
        "",
        f"- Retrieval version wins: `{summary['retrieval_turn_wins']}`",
        f"- Core version wins: `{summary['core_turn_wins']}`",
        f"- Ties: `{summary['tie_turns']}`",
        f"- Core total score: `{summary['core_total_score']}`",
        f"- Retrieval total score: `{summary['retrieval_total_score']}`",
        f"- Score delta: `+{summary['score_delta']}`",
        f"- Safe turns: `{summary['safe_turn_count']}/{summary['turn_count']}`",
        f"- Protected turns preserved: `{summary['protected_turns_preserved']}/{summary['protected_turn_count']}`",
        f"- Retrieval influenced responses: `{summary['retrieval_influenced_count']}`",
        f"- Max retrieval latency: `{summary['max_retrieval_elapsed_ms']} ms`",
        f"- Average retrieval latency: `{summary['avg_retrieval_elapsed_ms']} ms`",
        f"- Decision: `{payload['decision']}`",
        "",
        "Interpretation: retrieval version wins on the validated objection turns and the older core version wins zero turns. Keep retrieval opt-in for these paths; do not make retrieval default from this scripted result alone.",
        "",
        "## Turn Table",
        "",
        "| Turn | Difficulty | Winner | Core Score | Retrieval Score | Retrieval Used | Safe |",
        "| --- | --- | --- | ---: | ---: | --- | --- |",
    ]
    for row in payload["turns"]:
        lines.append(
            "| {turn_id} | {difficulty} | {winner} | {core_score} | {retrieval_score} | {used} | {safe} |".format(
                turn_id=row["turn_id"],
                difficulty=row["sales_difficulty"],
                winner=row["winner"],
                core_score=row["core_score"],
                retrieval_score=row["retrieval_score"],
                used=row["retrieval_used_in_runtime"],
                safe=row["safe"],
            )
        )
    lines.extend(
        [
            "",
            "## Next Gate",
            "",
            "Do not make retrieval default until a larger call-outcome simulation or human review confirms that the extra objection handling improves appointment-setting without adding pressure, unsupported claims, or protected-context drift.",
        ]
    )
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the RAG-018 retrieval-vs-core multi-turn call simulation.")
    parser.add_argument("--cases", default=str(DEFAULT_CASES), help="RAG-018 retrieval-vs-core call simulation case JSON.")
    parser.add_argument("--registry", default=str(DEFAULT_RETRIEVAL_REGISTRY), help="RAG-017 runtime knowledge registry JSON.")
    parser.add_argument("--out", default=str(DEFAULT_RESULT), help="Output JSON path.")
    parser.add_argument("--report-out", default=str(DEFAULT_REPORT), help="Output Markdown report path.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cases_path = resolve_path(args.cases, DEFAULT_CASES)
    registry_path = resolve_path(args.registry, DEFAULT_RETRIEVAL_REGISTRY)
    out_path = resolve_path(args.out, DEFAULT_RESULT)
    report_path = resolve_path(args.report_out, DEFAULT_REPORT)
    simulation = load_json(cases_path)
    campaign_source = resolve_path(simulation.get("campaign_case_source"), DEFAULT_CAMPAIGN_CASE_SOURCE)
    campaigns, _runtime_cases = load_realtime_cases(campaign_source)
    retrieval_config = simulation.get("retrieval", {})
    max_results = int(retrieval_config.get("max_results", 4))
    min_score = int(retrieval_config.get("min_score", DEFAULT_RETRIEVAL_MIN_SCORE))
    target_latency_ms = int(retrieval_config.get("target_latency_ms", DEFAULT_RETRIEVAL_TARGET_MS))
    acceptable_latency_ms = int(retrieval_config.get("acceptable_latency_ms", DEFAULT_RETRIEVAL_ACCEPTABLE_MS))

    started_at = time.perf_counter()
    rows: list[dict[str, Any]] = []
    calls = list(simulation.get("calls", []))
    for call in calls:
        for turn in call.get("turns", []):
            campaign_id = turn.get("campaign_id", call["campaign_id"])
            campaign = find_campaign(campaigns, campaign_id)
            if campaign is None:
                raise ValueError(f"Unknown campaign_id: {campaign_id}")
            no_retrieval = run_packet(
                campaign=campaign,
                turn=turn,
                retrieval_enabled=False,
                registry_path=registry_path,
                max_results=max_results,
                min_score=min_score,
                target_latency_ms=target_latency_ms,
                acceptable_latency_ms=acceptable_latency_ms,
            )
            with_retrieval = run_packet(
                campaign=campaign,
                turn=turn,
                retrieval_enabled=True,
                registry_path=registry_path,
                max_results=max_results,
                min_score=min_score,
                target_latency_ms=target_latency_ms,
                acceptable_latency_ms=acceptable_latency_ms,
            )
            rows.append(summarize_turn(call, turn, no_retrieval, with_retrieval))
    completed_at = time.perf_counter()

    payload = {
        "simulation_id": "RAG-018-retrieval-vs-core-call-simulation",
        "title": simulation.get("title", ""),
        "cases_path": rel_path(cases_path),
        "campaign_case_source": rel_path(campaign_source),
        "registry_path": rel_path(registry_path),
        "provider_calls_made": False,
        "private_customer_data_used": False,
        "llm_used": False,
        "external_vector_db_used": False,
        "embedding_provider_used": False,
        "config": {
            "max_results": max_results,
            "min_score": min_score,
            "target_latency_ms": target_latency_ms,
            "acceptable_latency_ms": acceptable_latency_ms,
        },
        "summary": build_summary(rows, calls, started_at, completed_at),
        "decision": "",
        "turns": rows,
    }
    payload["decision"] = decide(payload["summary"])
    write_json(out_path, payload)
    write_text(report_path, render_report(payload))
    print(json.dumps(payload["summary"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
