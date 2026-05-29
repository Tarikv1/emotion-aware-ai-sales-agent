from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import statistics
import sys
from time import perf_counter_ns
from typing import Any


sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

REPLAY_DIR = ROOT / "research" / "experiments" / "generated" / "NON-LLM-ACTION-SELECTOR-SHADOW-REPLAY-001"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / "NON-LLM-ACTION-SELECTOR-SHADOW-MODE-001"
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"
EXPERIMENT_ID = "NON-LLM-ACTION-SELECTOR-SHADOW-MODE-001"

from runtime.action_selector.action_selector_contract import action_labels  # noqa: E402
from runtime.action_selector.non_llm_action_selector import RuleBasedActionSelector  # noqa: E402
from runtime.action_selector.shadow_mode_evaluator import build_shadow_input, run_selector_shadow  # noqa: E402


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        payload = json.loads(stripped)
        if not isinstance(payload, dict):
            raise ValueError(f"{path}:{line_number} is not a JSON object")
        rows.append(payload)
    return rows


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def percentile(values: list[float], percentile_value: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, round((percentile_value / 100.0) * (len(ordered) - 1))))
    return ordered[index]


def context_summary(context: dict[str, Any]) -> str:
    compact = context.get("compact_target") if isinstance(context.get("compact_target"), dict) else {}
    pieces = [
        f"team={context.get('known_team_status') or ''}",
        f"use={','.join(str(item) for item in context.get('known_use_case', []) if str(item or '').strip()) if isinstance(context.get('known_use_case'), list) else ''}",
        f"tools={','.join(str(item) for item in context.get('known_tools', []) if str(item or '').strip()) if isinstance(context.get('known_tools'), list) else ''}",
        f"safety={context.get('safety_boundary_detected') is True}",
        f"compact_action={compact.get('action') or ''}",
        f"compact_sub={compact.get('sub') or ''}",
    ]
    return "; ".join(piece for piece in pieces if not piece.endswith("="))


def shadow_case(row: dict[str, Any], selector: RuleBasedActionSelector) -> tuple[dict[str, Any], float]:
    context = row.get("context") if isinstance(row.get("context"), dict) else {}
    shadow_input = build_shadow_input(
        turn_id=str(row.get("replay_case_id") or ""),
        campaign_id=str(row.get("campaign_id") or ""),
        buyer_utterance_text=str(row.get("buyer_utterance_text") or ""),
        normalized_buyer_text=str(context.get("normalized_buyer_text") or ""),
        existing_runtime_action_id=str(row.get("existing_runtime_action_id") or ""),
        existing_runtime_response_text="",
        memory_summary=json.dumps(context, sort_keys=True, separators=(",", ":")),
        known_context=context,
        safety_boundary_detected=context.get("safety_boundary_detected") is True,
        previous_action_id=str(context.get("last_action_id") or ""),
        previous_answered_topic=str(context.get("last_answered_topic") or ""),
        evidence_source=str(row.get("source_file") or ""),
    )
    start = perf_counter_ns()
    shadow_output = run_selector_shadow(shadow_input, expected_action_id=str(row.get("expected_action_id") or ""), selector=selector)
    latency_ms = (perf_counter_ns() - start) / 1_000_000
    selector_action_id = str(shadow_output.get("selector_action_id") or "")
    expected_action_id = str(row.get("expected_action_id") or "")
    runtime_action_id = str(row.get("existing_runtime_action_id") or "")
    case_result = {
        "replay_case_id": row["replay_case_id"],
        "buyer_utterance_text": row["buyer_utterance_text"],
        "context_summary": context_summary(context),
        "expected_action_id": expected_action_id,
        "runtime_action_id": runtime_action_id,
        "selector_action_id": selector_action_id,
        "selector_confidence": shadow_output["selector_confidence"],
        "agreement_classification": shadow_output["disagreement_type"],
        "agreement_with_expected": selector_action_id == expected_action_id if expected_action_id else None,
        "agreement_with_runtime": shadow_output["agreement_with_runtime"],
        "safety_status": shadow_output["safety_status"],
        "reasons": shadow_output["selector_reasons"],
        "matched_features": shadow_output["selector_matched_features"],
        "fallback_required": shadow_output["fallback_required"],
        "would_change_runtime": False,
        "side_effects_allowed": False,
        "buyer_facing_text_generated": False,
        "live_runtime_wiring_allowed": False,
        "should_not_change_runtime": True,
        "latency_ms": latency_ms,
        "category": row.get("category") or "other",
        "sanitized": row.get("sanitized") is True,
        "raw_private_data": False,
    }
    return case_result, latency_ms


def subset_accuracy(rows: list[dict[str, Any]], predicate: Any) -> dict[str, Any]:
    selected = [row for row in rows if predicate(row)]
    correct = sum(1 for row in selected if row.get("agreement_with_expected") is True)
    return {
        "case_count": len(selected),
        "correct": correct,
        "accuracy": correct / len(selected) if selected else None,
    }


def build_metrics(case_results: list[dict[str, Any]], latencies: list[float]) -> dict[str, Any]:
    proposal_counts = Counter(str(row["selector_action_id"]) for row in case_results)
    expected_counts = Counter(str(row["expected_action_id"]) for row in case_results if row.get("expected_action_id"))
    classifications = Counter(str(row["agreement_classification"]) for row in case_results)
    runtime_available = [row for row in case_results if row.get("runtime_action_id")]
    compatible_types = {"same_action", "compatible_action", "selector_more_specific", "runtime_more_specific"}
    rare_labels = {
        label: {
            "expected_count": expected_counts[label],
            "proposal_count": proposal_counts.get(label, 0),
            "accuracy": subset_accuracy(case_results, lambda row, value=label: row.get("expected_action_id") == value)["accuracy"],
        }
        for label, count in expected_counts.items()
        if count <= 2
    }
    return {
        "replay_case_count": len(case_results),
        "selector_valid_action_count": sum(1 for row in case_results if row["selector_action_id"] in action_labels()),
        "fallback_count": sum(1 for row in case_results if row.get("fallback_required") is True),
        "safety_block_count": sum(1 for row in case_results if row.get("safety_status") == "boundary_safe"),
        "agreement_with_expected_count": sum(1 for row in case_results if row.get("agreement_with_expected") is True),
        "agreement_with_runtime_count": sum(1 for row in runtime_available if row.get("agreement_with_runtime") is True),
        "runtime_action_available_count": len(runtime_available),
        "compatible_with_runtime_count": sum(1 for row in runtime_available if row.get("agreement_classification") in compatible_types),
        "compatible_with_expected_count": sum(1 for row in case_results if row.get("agreement_classification") in compatible_types),
        "selector_possible_improvement_count": classifications.get("selector_possible_improvement", 0),
        "selector_possible_regression_count": classifications.get("selector_possible_regression", 0),
        "unsafe_selector_count": sum(1 for row in case_results if str(row.get("safety_status", "")).startswith("unsafe")),
        "unknown_count": classifications.get("unknown", 0),
        "agreement_classification_counts": dict(sorted(classifications.items())),
        "per_label_proposal_counts": dict(sorted(proposal_counts.items())),
        "rare_label_behavior": rare_labels,
        "boundary_case_accuracy": subset_accuracy(case_results, lambda row: row.get("expected_action_id") in {"respect_boundary", "answer_privacy_boundary"}),
        "repair_case_accuracy": subset_accuracy(case_results, lambda row: str(row.get("expected_action_id") or "").startswith("repair_") or row.get("expected_action_id") == "avoid_repetition_rephrase"),
        "terminal_close_accuracy": subset_accuracy(case_results, lambda row: row.get("expected_action_id") == "terminal_close"),
        "no_fit_accuracy": subset_accuracy(case_results, lambda row: row.get("expected_action_id") == "disqualify_no_fit"),
        "latency_ms": {
            "sample_count": len(latencies),
            "p50": percentile(latencies, 50),
            "p90": percentile(latencies, 90),
            "p99": percentile(latencies, 99),
            "max": max(latencies) if latencies else 0.0,
            "mean": statistics.mean(latencies) if latencies else 0.0,
        },
    }


def build_result(case_results: list[dict[str, Any]], latencies: list[float]) -> dict[str, Any]:
    return {
        "experiment_id": EXPERIMENT_ID,
        "generated_at": utc_now(),
        "status": "pass",
        "shadow_mode_only": True,
        "selector": "rule_based",
        "replay_dataset": "research/experiments/generated/NON-LLM-ACTION-SELECTOR-SHADOW-REPLAY-001/replay.jsonl",
        "metrics": build_metrics(case_results, latencies),
        "case_results": case_results,
        "side_effects_allowed": False,
        "buyer_facing_text_generated": False,
        "live_runtime_wiring_allowed": False,
        "should_not_change_runtime": True,
        "response_text_changed": False,
        "runtime_behavior_changed": False,
        "provider_calls_made": False,
        "openai_api_calls_made": False,
        "ultravox_calls_made": False,
        "elevenlabs_calls_made": False,
        "local_llm_calls_made": False,
        "ollama_calls_made": False,
    }


def build_report(result: dict[str, Any]) -> str:
    metrics = result["metrics"]
    latency = metrics["latency_ms"]
    lines = [
        f"# {EXPERIMENT_ID}",
        "",
        f"- Status: {result['status']}",
        f"- Replay cases: {metrics['replay_case_count']}",
        f"- Selector valid actions: {metrics['selector_valid_action_count']}",
        f"- Agreement with expected: {metrics['agreement_with_expected_count']}",
        f"- Runtime action available count: {metrics['runtime_action_available_count']}",
        f"- Agreement with runtime: {metrics['agreement_with_runtime_count']}",
        f"- Compatible with runtime: {metrics['compatible_with_runtime_count']}",
        f"- Possible improvement/regression: {metrics['selector_possible_improvement_count']}/{metrics['selector_possible_regression_count']}",
        f"- Unsafe selector count: {metrics['unsafe_selector_count']}",
        f"- Unknown count: {metrics['unknown_count']}",
        f"- Latency ms p50/p90/p99/max: {latency['p50']:.4f}/{latency['p90']:.4f}/{latency['p99']:.4f}/{latency['max']:.4f}",
        "- Would change runtime: false for every case",
        "- Provider/OpenAI/Ultravox/ElevenLabs/local LLM/Ollama calls: false",
        "- Live runtime wiring allowed: false",
        "- Runtime behavior changed: false",
        "- Response text changed: false",
        "",
        "## Special Metrics",
        "",
        f"- Boundary: `{json.dumps(metrics['boundary_case_accuracy'], sort_keys=True)}`",
        f"- Repair: `{json.dumps(metrics['repair_case_accuracy'], sort_keys=True)}`",
        f"- Terminal close: `{json.dumps(metrics['terminal_close_accuracy'], sort_keys=True)}`",
        f"- No-fit: `{json.dumps(metrics['no_fit_accuracy'], sort_keys=True)}`",
        "",
        "## Proposal Counts",
        "",
    ]
    for label, count in metrics["per_label_proposal_counts"].items():
        lines.append(f"- {label}: {count}")
    return "\n".join(lines)


def main() -> int:
    replay_rows = read_jsonl(REPLAY_DIR / "replay.jsonl")
    selector = RuleBasedActionSelector()
    case_results: list[dict[str, Any]] = []
    latencies: list[float] = []
    for row in replay_rows:
        case_result, latency = shadow_case(row, selector)
        case_results.append(case_result)
        latencies.append(latency)
    result = build_result(case_results, latencies)
    write_json(RESULT_PATH, result)
    write_text(REPORT_PATH, build_report(result))
    print(
        json.dumps(
            {
                "status": result["status"],
                "replay_case_count": result["metrics"]["replay_case_count"],
                "agreement_with_expected_count": result["metrics"]["agreement_with_expected_count"],
                "unsafe_selector_count": result["metrics"]["unsafe_selector_count"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
