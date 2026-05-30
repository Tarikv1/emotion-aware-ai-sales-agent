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

OUT_DIR = ROOT / "research" / "experiments" / "generated" / "NON-LLM-ACTION-SELECTOR-RUNTIME-METADATA-SHADOW-001"
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"
EXPERIMENT_ID = "NON-LLM-ACTION-SELECTOR-RUNTIME-METADATA-SHADOW-001"

from runtime.action_selector.action_selector_contract import action_labels  # noqa: E402
from runtime.action_selector.shadow_runtime_logger import run_shadow_selector_read_only  # noqa: E402
from scripts.test_runtime_action_metadata_extraction_001 import build_cases  # noqa: E402


FALSE_FLAGS = {
    "runtime_behavior_changed": False,
    "response_text_changed": False,
    "side_effects_allowed": False,
    "live_runtime_wiring_allowed": False,
    "memory_mutation_allowed": False,
    "provider_calls_made": False,
    "openai_api_calls_made": False,
    "ultravox_calls_made": False,
    "elevenlabs_calls_made": False,
    "local_llm_calls_made": False,
    "ollama_calls_made": False,
    "tts_calls_made": False,
    "raw_private_data": False,
    "buyer_facing_text_generated": False,
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def percentile(values: list[float], percentile_value: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, round((percentile_value / 100.0) * (len(ordered) - 1))))
    return ordered[index]


def turn_context_from_case(case: dict[str, Any]) -> dict[str, Any]:
    return {
        "turn_id": case["case_id"],
        "campaign_id": case["campaign_id"],
        "buyer_utterance_text_sanitized": case["buyer_utterance_text"],
        "normalized_buyer_text": case["context"].get("normalized_buyer_text") or "",
        "context": case["context"],
        "context_summary": f"synthetic_runtime_metadata_case={case['case_id']}; expected={case['expected_action_id']}",
        "runtime_result": case["runtime_result"],
        "evidence_source": case["source_file"],
        "expected_action_id": case["expected_action_id"],
        "safety_boundary_detected": case["context"].get("safety_boundary_detected") is True,
        "raw_private_data": False,
    }


def run_case(case: dict[str, Any]) -> tuple[dict[str, Any], float]:
    start = perf_counter_ns()
    record = run_shadow_selector_read_only(
        turn_context_from_case(case),
        expected_action_id=str(case.get("expected_action_id") or ""),
        mode="offline_replay_shadow",
    )
    latency_ms = (perf_counter_ns() - start) / 1_000_000
    record["case_id"] = case["case_id"]
    record["latency_ms"] = latency_ms
    record["sanitized"] = True
    record["raw_private_data"] = False
    return record, latency_ms


def build_result(case_results: list[dict[str, Any]], latencies: list[float]) -> dict[str, Any]:
    compatible_types = {"same_action", "compatible_action", "selector_more_specific", "runtime_more_specific"}
    classifications = Counter(str(row.get("disagreement_type") or "") for row in case_results)
    selector_counts = Counter(str(row.get("selector_action_id") or "") for row in case_results)
    runtime_counts = Counter(str(row.get("runtime_action_id") or "") for row in case_results)
    validation_error_count = sum(len(row.get("validation_errors") or []) for row in case_results)
    unsafe_count = sum(1 for row in case_results if str(row.get("safety_status") or "").startswith("unsafe"))
    case_count = len(case_results)
    result = {
        "experiment_id": EXPERIMENT_ID,
        "generated_at": utc_now(),
        "status": "pass",
        "case_count": case_count,
        "replay_case_count": case_count,
        "selector_valid_action_count": sum(1 for row in case_results if row.get("selector_action_id") in action_labels()),
        "runtime_action_id_available_count": sum(1 for row in case_results if row.get("runtime_action_id") in action_labels()),
        "runtime_metadata_available_count": sum(1 for row in case_results if row.get("runtime_metadata_available") is True),
        "exact_agreement_count": sum(1 for row in case_results if row.get("disagreement_type") == "same_action"),
        "compatible_agreement_count": sum(1 for row in case_results if row.get("disagreement_type") in compatible_types),
        "agreement_with_expected_count": sum(1 for row in case_results if row.get("agreement_with_expected") is True),
        "possible_improvement_count": sum(1 for row in case_results if row.get("possible_improvement") is True),
        "possible_regression_count": sum(1 for row in case_results if row.get("possible_regression") is True),
        "safety_blocker_count": validation_error_count + unsafe_count,
        "validation_error_count": validation_error_count,
        "unsafe_selector_count": unsafe_count,
        "agreement_classification_counts": dict(sorted(classifications.items())),
        "selector_action_counts": dict(sorted(selector_counts.items())),
        "runtime_action_counts": dict(sorted(runtime_counts.items())),
        "rare_case_counts": {
            "boundary": sum(1 for row in case_results if row.get("selector_action_id") in {"respect_boundary", "answer_privacy_boundary"}),
            "repair": sum(1 for row in case_results if str(row.get("selector_action_id") or "").startswith("repair_") or row.get("selector_action_id") == "avoid_repetition_rephrase"),
            "no_fit": sum(1 for row in case_results if row.get("selector_action_id") == "disqualify_no_fit"),
            "terminal_close": sum(1 for row in case_results if row.get("selector_action_id") == "terminal_close"),
        },
        "latency_ms": {
            "sample_count": len(latencies),
            "p50": percentile(latencies, 50),
            "p90": percentile(latencies, 90),
            "p99": percentile(latencies, 99),
            "max": max(latencies) if latencies else 0.0,
            "mean": statistics.mean(latencies) if latencies else 0.0,
        },
        "public_evidence_sanitized": True,
        "should_not_change_runtime": True,
        "case_results": case_results,
        **FALSE_FLAGS,
    }
    if (
        case_count < 60
        or result["selector_valid_action_count"] != case_count
        or result["runtime_action_id_available_count"] != case_count
        or result["runtime_metadata_available_count"] != case_count
        or result["safety_blocker_count"] != 0
    ):
        result["status"] = "fail"
    return result


def build_report(result: dict[str, Any]) -> str:
    latency = result["latency_ms"]
    lines = [
        f"# {EXPERIMENT_ID}",
        "",
        f"- Status: {result['status']}",
        f"- Cases: {result['case_count']}",
        f"- Runtime action ID available count: {result['runtime_action_id_available_count']}",
        f"- Selector valid action count: {result['selector_valid_action_count']}",
        f"- Exact/compatible agreement: {result['exact_agreement_count']}/{result['compatible_agreement_count']}",
        f"- Agreement with expected: {result['agreement_with_expected_count']}",
        f"- Possible improvement/regression: {result['possible_improvement_count']}/{result['possible_regression_count']}",
        f"- Safety blockers: {result['safety_blocker_count']}",
        f"- Latency ms p50/p90/p99/max: {latency['p50']:.4f}/{latency['p90']:.4f}/{latency['p99']:.4f}/{latency['max']:.4f}",
        "- Runtime behavior changed: false",
        "- Response text changed: false",
        "- Provider/OpenAI/Ultravox/ElevenLabs/local LLM/Ollama/TTS calls: false",
        "- Raw private data: false",
        "",
        "## Agreement Classification Counts",
        "",
    ]
    for key, value in result["agreement_classification_counts"].items():
        lines.append(f"- {key}: {value}")
    return "\n".join(lines)


def main() -> int:
    case_results: list[dict[str, Any]] = []
    latencies: list[float] = []
    for case in build_cases():
        record, latency_ms = run_case(case)
        case_results.append(record)
        latencies.append(latency_ms)
    result = build_result(case_results, latencies)
    write_json(RESULT_PATH, result)
    write_text(REPORT_PATH, build_report(result))
    print(
        json.dumps(
            {
                "status": result["status"],
                "case_count": result["case_count"],
                "exact_agreement_count": result["exact_agreement_count"],
                "safety_blocker_count": result["safety_blocker_count"],
            },
            indent=2,
        )
    )
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
