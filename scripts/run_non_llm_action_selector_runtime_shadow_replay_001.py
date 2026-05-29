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

SOURCE_REPLAY_DIR = ROOT / "research" / "experiments" / "generated" / "NON-LLM-ACTION-SELECTOR-SHADOW-REPLAY-001"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / "NON-LLM-ACTION-SELECTOR-RUNTIME-SHADOW-REPLAY-001"
LOG_DIR = ROOT / "research" / "experiments" / "generated" / "NON-LLM-ACTION-SELECTOR-RUNTIME-SHADOW-LOG-001"
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"
LOG_PATH = LOG_DIR / "result.jsonl"
EXPERIMENT_ID = "NON-LLM-ACTION-SELECTOR-RUNTIME-SHADOW-REPLAY-001"

from runtime.action_selector.action_selector_contract import action_labels  # noqa: E402
from runtime.action_selector.shadow_runtime_logger import append_shadow_record_jsonl, run_shadow_selector_read_only  # noqa: E402


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


def turn_context_from_replay(row: dict[str, Any]) -> dict[str, Any]:
    context = row.get("context") if isinstance(row.get("context"), dict) else {}
    return {
        "turn_id": str(row.get("replay_case_id") or ""),
        "campaign_id": str(row.get("campaign_id") or ""),
        "buyer_utterance_text_sanitized": str(row.get("buyer_utterance_text") or ""),
        "normalized_buyer_text": str(context.get("normalized_buyer_text") or ""),
        "context": context,
        "context_summary": compact_context_summary(context),
        "runtime_response_text_available": row.get("existing_runtime_response_text_available") is True,
        "runtime_action_id_if_available": str(row.get("existing_runtime_action_id") or ""),
        "evidence_source": str(row.get("source_file") or ""),
        "expected_action_id": str(row.get("expected_action_id") or ""),
        "safety_boundary_detected": context.get("safety_boundary_detected") is True,
        "raw_private_data": False,
    }


def compact_context_summary(context: dict[str, Any]) -> str:
    compact = context.get("compact_target") if isinstance(context.get("compact_target"), dict) else {}
    pieces = [
        f"team={context.get('known_team_status') or ''}",
        "use=" + ",".join(str(item) for item in context.get("known_use_case", []) if str(item or "").strip())
        if isinstance(context.get("known_use_case"), list)
        else "",
        "tools=" + ",".join(str(item) for item in context.get("known_tools", []) if str(item or "").strip())
        if isinstance(context.get("known_tools"), list)
        else "",
        f"safety={context.get('safety_boundary_detected') is True}",
        f"compact_action={compact.get('action') or ''}",
        f"compact_sub={compact.get('sub') or ''}",
    ]
    return "; ".join(piece for piece in pieces if piece and not piece.endswith("="))


def run_case(row: dict[str, Any]) -> tuple[dict[str, Any], float]:
    context = turn_context_from_replay(row)
    start = perf_counter_ns()
    record = run_shadow_selector_read_only(
        context,
        expected_action_id=str(row.get("expected_action_id") or ""),
        mode="offline_replay_shadow",
    )
    latency_ms = (perf_counter_ns() - start) / 1_000_000
    record["latency_ms"] = latency_ms
    record["category"] = row.get("category") or "other"
    record["source_case_id"] = row.get("source_case_id") or ""
    record["sanitized"] = row.get("sanitized") is True
    return record, latency_ms


def build_result(case_results: list[dict[str, Any]], latencies: list[float]) -> dict[str, Any]:
    compatible_types = {"same_action", "compatible_action", "selector_more_specific", "runtime_more_specific"}
    classifications = Counter(str(row.get("agreement_classification") or "") for row in case_results)
    selector_counts = Counter(str(row.get("selector_action_id") or "") for row in case_results)
    expected_counts = Counter(str(row.get("expected_action_id") or "") for row in case_results if row.get("expected_action_id"))
    runtime_available = [row for row in case_results if row.get("runtime_action_id_if_available")]
    validation_error_count = sum(len(row.get("validation_errors") or []) for row in case_results)
    unsafe_count = sum(1 for row in case_results if str(row.get("safety_status") or "").startswith("unsafe"))
    return {
        "experiment_id": EXPERIMENT_ID,
        "generated_at": utc_now(),
        "status": "pass" if validation_error_count == 0 and unsafe_count == 0 and len(case_results) >= 100 else "fail",
        "source_replay": "research/experiments/generated/NON-LLM-ACTION-SELECTOR-SHADOW-REPLAY-001/replay.jsonl",
        "shadow_log": "research/experiments/generated/NON-LLM-ACTION-SELECTOR-RUNTIME-SHADOW-LOG-001/result.jsonl",
        "replay_case_count": len(case_results),
        "selector_valid_action_count": sum(1 for row in case_results if row.get("selector_action_id") in action_labels()),
        "runtime_action_id_available_count": len(runtime_available),
        "runtime_response_text_available_count": sum(1 for row in case_results if row.get("runtime_response_text_available") is True),
        "agreement_with_expected_count": sum(1 for row in case_results if row.get("agreement_with_expected") is True),
        "compatible_with_expected_count": sum(1 for row in case_results if row.get("agreement_classification") in compatible_types),
        "possible_improvement_count": sum(1 for row in case_results if row.get("possible_improvement") is True),
        "possible_regression_count": sum(1 for row in case_results if row.get("possible_regression") is True),
        "safety_blocker_count": validation_error_count + unsafe_count,
        "validation_error_count": validation_error_count,
        "unsafe_selector_count": unsafe_count,
        "agreement_classification_counts": dict(sorted(classifications.items())),
        "selector_action_counts": dict(sorted(selector_counts.items())),
        "expected_action_counts": dict(sorted(expected_counts.items())),
        "latency_ms": {
            "sample_count": len(latencies),
            "p50": percentile(latencies, 50),
            "p90": percentile(latencies, 90),
            "p99": percentile(latencies, 99),
            "max": max(latencies) if latencies else 0.0,
            "mean": statistics.mean(latencies) if latencies else 0.0,
        },
        "public_evidence_sanitized": True,
        "raw_private_data": False,
        "audio_data_used": False,
        "should_not_change_runtime": True,
        "side_effects_allowed": False,
        "buyer_facing_text_generated": False,
        "live_runtime_wiring_allowed": False,
        "response_text_changed": False,
        "runtime_behavior_changed": False,
        "memory_mutation_allowed": False,
        "provider_calls_made": False,
        "openai_api_calls_made": False,
        "ultravox_calls_made": False,
        "elevenlabs_calls_made": False,
        "local_llm_calls_made": False,
        "ollama_calls_made": False,
        "tts_calls_made": False,
        "case_results": case_results,
    }


def build_report(result: dict[str, Any]) -> str:
    latency = result["latency_ms"]
    lines = [
        f"# {EXPERIMENT_ID}",
        "",
        f"- Status: {result['status']}",
        f"- Replay cases: {result['replay_case_count']}",
        f"- Selector valid action count: {result['selector_valid_action_count']}",
        f"- Runtime action ID available count: {result['runtime_action_id_available_count']}",
        f"- Runtime response text available count: {result['runtime_response_text_available_count']}",
        f"- Agreement with expected: {result['agreement_with_expected_count']}",
        f"- Compatible with expected: {result['compatible_with_expected_count']}",
        f"- Possible improvement/regression: {result['possible_improvement_count']}/{result['possible_regression_count']}",
        f"- Safety blockers: {result['safety_blocker_count']}",
        f"- Latency ms p50/p90/p99/max: {latency['p50']:.4f}/{latency['p90']:.4f}/{latency['p99']:.4f}/{latency['max']:.4f}",
        "- Public evidence sanitized: true",
        "- Raw private data/audio used: false",
        "- Provider/OpenAI/Ultravox/ElevenLabs/local LLM/Ollama/TTS calls: false",
        "- Live runtime wiring allowed: false",
        "- Runtime behavior changed: false",
        "- Response text changed: false",
        "",
        "## Classification Counts",
        "",
    ]
    for key, value in result["agreement_classification_counts"].items():
        lines.append(f"- {key}: {value}")
    return "\n".join(lines)


def main() -> int:
    rows = read_jsonl(SOURCE_REPLAY_DIR / "replay.jsonl")
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    LOG_PATH.write_text("", encoding="utf-8")
    case_results: list[dict[str, Any]] = []
    latencies: list[float] = []
    for row in rows:
        record, latency_ms = run_case(row)
        append_shadow_record_jsonl(LOG_PATH, record)
        case_results.append(record)
        latencies.append(latency_ms)
    result = build_result(case_results, latencies)
    write_json(RESULT_PATH, result)
    write_text(REPORT_PATH, build_report(result))
    print(
        json.dumps(
            {
                "status": result["status"],
                "replay_case_count": result["replay_case_count"],
                "selector_valid_action_count": result["selector_valid_action_count"],
                "safety_blocker_count": result["safety_blocker_count"],
            },
            indent=2,
        )
    )
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
