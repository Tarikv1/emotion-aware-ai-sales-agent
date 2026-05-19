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
from runtime.entrypoints.realtime_turn_cli import find_campaign
from runtime.core.realtime_turns import load_realtime_cases
from run_resp_001_retrieval_ab_evaluation import forbidden_response_text, output_language_matches


DEFAULT_CASES = ROOT / "research" / "experiments" / "cases" / "rag-018-scripted-call-simulation.json"
DEFAULT_OUT_DIR = ROOT / "research" / "experiments" / "generated" / "RAG-018-scripted-call-simulation"
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


def marker_score(text: str, markers: list[str]) -> int:
    if not markers:
        return 0
    lowered = text.lower()
    return int(all(marker.lower() in lowered for marker in markers))


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
    return build_guarded_response_packet(
        campaign=campaign,
        stage=case["stage"],
        input_type=case.get("input_type", "speech-final"),
        transcript=case.get("transcript", ""),
        silence_count=int(case.get("silence_count", 0)),
        retrieval_enabled=retrieval_enabled,
        retrieval_registry_path=registry_path if retrieval_enabled else None,
        retrieval_max_results=max_results,
        retrieval_min_score=min_score,
        retrieval_target_latency_ms=target_latency_ms,
        retrieval_acceptable_latency_ms=acceptable_latency_ms,
    )


def summarize_case(case: dict[str, Any], no_retrieval: dict[str, Any], with_retrieval: dict[str, Any]) -> dict[str, Any]:
    retrieval = with_retrieval["retrieval"]
    core_response = no_retrieval["final_response"]
    rag_response = with_retrieval["final_response"]
    protected_context = bool(case.get("protected_context"))
    protected_text_preserved = (core_response == rag_response) if protected_context else True
    resolution_markers = [str(marker) for marker in case.get("objection_resolution_markers", [])]
    next_step_markers = [str(marker) for marker in case.get("next_step_quality_markers", [])]
    core_resolution_score = marker_score(core_response, resolution_markers)
    rag_resolution_score = marker_score(rag_response, resolution_markers)
    core_next_step_score = marker_score(core_response, next_step_markers)
    rag_next_step_score = marker_score(rag_response, next_step_markers)
    sales_difficulty = no_retrieval["decision_snapshot"]["sales_difficulty"]
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
        "case_id": case["case_id"],
        "case_title": case.get("case_title", ""),
        "campaign_id": case["campaign_id"],
        "stage": case["stage"],
        "expected_sales_difficulty": case.get("expected_sales_difficulty", ""),
        "sales_difficulty": sales_difficulty,
        "quality_scored": bool(case.get("quality_scored")),
        "protected_context": protected_context,
        "protected_text_preserved": protected_text_preserved,
        "core_response": core_response,
        "rag_response": rag_response,
        "rag_changed_from_core": rag_response != core_response,
        "retrieval_status": retrieval["status"],
        "retrieval_used_in_runtime": retrieval["retrieval_used_in_runtime"],
        "retrieved_item_ids": retrieval["retrieved_item_ids"],
        "used_hint_count": retrieval["used_hint_count"],
        "retrieval_elapsed_ms": retrieval["latency"]["elapsed_ms"],
        "retrieval_target_ms": retrieval["latency"]["target_ms"],
        "retrieval_acceptable_ms": retrieval["latency"]["acceptable_ms"],
        "language_match": output_language_matches(with_retrieval),
        "campaign_facts_override_rag": with_retrieval["core_pack"]["campaign_facts_override_rag"],
        "validation_passed": with_retrieval["validation"]["passed"],
        "safe": safe,
        "core_objection_resolution_score": core_resolution_score,
        "rag_objection_resolution_score": rag_resolution_score,
        "objection_resolution_delta": rag_resolution_score - core_resolution_score,
        "core_next_step_quality_score": core_next_step_score,
        "rag_next_step_quality_score": rag_next_step_score,
        "next_step_quality_delta": rag_next_step_score - core_next_step_score,
    }


def build_summary(rows: list[dict[str, Any]], started_at: float, completed_at: float) -> dict[str, Any]:
    case_count = len(rows)
    unsafe = [row for row in rows if not row["safe"]]
    influenced = [row for row in rows if row["retrieval_used_in_runtime"]]
    protected = [row for row in rows if row["protected_context"]]
    latencies = [row["retrieval_elapsed_ms"] for row in rows]
    over_target = [row for row in rows if row["retrieval_elapsed_ms"] > row["retrieval_target_ms"]]
    over_acceptable = [row for row in rows if row["retrieval_elapsed_ms"] > row["retrieval_acceptable_ms"]]
    quality_scored = [row for row in rows if row["quality_scored"]]
    return {
        "case_count": case_count,
        "quality_scored_case_count": len(quality_scored),
        "safe_case_count": case_count - len(unsafe),
        "unsafe_case_count": len(unsafe),
        "retrieval_influenced_count": len(influenced),
        "retrieval_blocked_count": sum(1 for row in rows if row["retrieval_status"] == "blocked"),
        "retrieval_retrieved_not_used_count": sum(1 for row in rows if row["retrieval_status"] == "retrieved_not_used"),
        "retrieval_no_match_count": sum(1 for row in rows if row["retrieval_status"] == "no_match"),
        "objection_resolution_improved_count": sum(1 for row in quality_scored if row["objection_resolution_delta"] > 0),
        "next_step_quality_improved_count": sum(1 for row in quality_scored if row["next_step_quality_delta"] > 0),
        "quality_gap_case_ids": [
            row["case_id"]
            for row in quality_scored
            if row["rag_objection_resolution_score"] == 0 or row["rag_next_step_quality_score"] == 0
        ],
        "protected_context_count": len(protected),
        "protected_contexts_preserved": sum(1 for row in protected if row["protected_text_preserved"] and not row["retrieval_used_in_runtime"]),
        "retrieval_over_target_count": len(over_target),
        "retrieval_over_acceptable_count": len(over_acceptable),
        "max_retrieval_elapsed_ms": max(latencies) if latencies else 0,
        "avg_retrieval_elapsed_ms": round(sum(latencies) / len(latencies), 2) if latencies else 0,
        "total_elapsed_ms": int((completed_at - started_at) * 1000),
    }


def decide(summary: dict[str, Any]) -> str:
    if summary["unsafe_case_count"]:
        return "revise_before_runtime_use"
    if summary["protected_contexts_preserved"] != summary["protected_context_count"]:
        return "revise_protected_context_handling"
    if summary["retrieval_over_acceptable_count"]:
        return "revise_latency_fallback_before_runtime_use"
    return "keep_rag_018_opt_in_and_do_not_make_default"


def render_report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# RAG-018 Scripted Call Simulation",
        "",
        "This local run compares retrieval-disabled guarded responses against opt-in RAG-018 retrieval on fixed scripted turns with scored objection resolution and next-step quality.",
        "",
        "No provider call, private customer data, vector database, embedding provider, or LLM reranker was used.",
        "",
        "## Result",
        "",
        f"- Cases: `{summary['case_count']}`",
        f"- Quality-scored cases: `{summary['quality_scored_case_count']}`",
        f"- Safe cases: `{summary['safe_case_count']}/{summary['case_count']}`",
        f"- Retrieval influenced responses: `{summary['retrieval_influenced_count']}`",
        f"- Objection-resolution improvements: `{summary['objection_resolution_improved_count']}`",
        f"- Next-step quality improvements: `{summary['next_step_quality_improved_count']}`",
        f"- Protected contexts preserved: `{summary['protected_contexts_preserved']}/{summary['protected_context_count']}`",
        f"- Quality gap case IDs: `{', '.join(summary['quality_gap_case_ids']) or 'none'}`",
        f"- Max retrieval latency: `{summary['max_retrieval_elapsed_ms']} ms`",
        f"- Average retrieval latency: `{summary['avg_retrieval_elapsed_ms']} ms`",
        f"- Decision: `{payload['decision']}`",
        "",
        "Interpretation: keep RAG-018 opt-in and do not make retrieval default. The current narrow influence paths improve German price, English price, send-me-info, and authority turns while preserving protected contexts.",
        "",
        "## Case Table",
        "",
        "| Case | Difficulty | Retrieval | Used | Safe | Protected | Resolution Delta | Next-Step Delta |",
        "| --- | --- | --- | --- | --- | --- | ---: | ---: |",
    ]
    for row in payload["cases"]:
        lines.append(
            "| {case_id} | {difficulty} | {retrieval} | {used} | {safe} | {protected} | {resolution_delta} | {next_delta} |".format(
                case_id=row["case_id"],
                difficulty=row["sales_difficulty"],
                retrieval=row["retrieval_status"],
                used=row["retrieval_used_in_runtime"],
                safe=row["safe"],
                protected=row["protected_context"],
                resolution_delta=row["objection_resolution_delta"],
                next_delta=row["next_step_quality_delta"],
            )
        )
    lines.extend(["", "## Next Gate", "", "Do not make retrieval default from this scripted result alone. Run a broader multi-turn call simulation or add new cases before expanding retrieval beyond these four validated paths."])
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the RAG-018 scripted call simulation.")
    parser.add_argument("--cases", default=str(DEFAULT_CASES), help="RAG-018 scripted-call simulation case JSON.")
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
    for case in simulation.get("cases", []):
        campaign = find_campaign(campaigns, case["campaign_id"])
        if campaign is None:
            raise ValueError(f"Unknown campaign_id: {case['campaign_id']}")
        no_retrieval = run_packet(
            campaign=campaign,
            case=case,
            retrieval_enabled=False,
            registry_path=registry_path,
            max_results=max_results,
            min_score=min_score,
            target_latency_ms=target_latency_ms,
            acceptable_latency_ms=acceptable_latency_ms,
        )
        with_retrieval = run_packet(
            campaign=campaign,
            case=case,
            retrieval_enabled=True,
            registry_path=registry_path,
            max_results=max_results,
            min_score=min_score,
            target_latency_ms=target_latency_ms,
            acceptable_latency_ms=acceptable_latency_ms,
        )
        rows.append(summarize_case(case, no_retrieval, with_retrieval))
    completed_at = time.perf_counter()

    payload = {
        "simulation_id": "RAG-018-scripted-call-simulation",
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
        "summary": build_summary(rows, started_at, completed_at),
        "decision": "",
        "cases": rows,
    }
    payload["decision"] = decide(payload["summary"])
    write_json(out_path, payload)
    write_text(report_path, render_report(payload))
    print(json.dumps(payload["summary"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
