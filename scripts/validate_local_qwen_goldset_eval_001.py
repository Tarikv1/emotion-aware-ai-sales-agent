#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.llm_brain.conversation_brain_schema import (  # noqa: E402
    COMPACT_PLANNER_SCHEMA_MODE,
    PRIMARY_MODEL_ID,
    validate_compact_conversation_brain_output,
    validate_conversation_brain_output,
)


EXPERIMENT_ID = "LOCAL-QWEN-GOLDSET-EVAL-001"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / EXPERIMENT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"

BLOCKED_PROVIDER_PATTERNS = {
    "openai_import": "from openai",
    "openai_client": "openai.OpenAI",
    "openai_api_key": "OPENAI_API_KEY",
    "requests_post": "requests.post",
    "httpx_post": "httpx.post",
}


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def git_model_weights_committed() -> bool:
    try:
        completed = subprocess.run(
            ["git", "ls-files", "local_artifacts"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except Exception:
        return False
    if completed.returncode != 0:
        return False
    weight_suffixes = (".safetensors", ".bin", ".gguf", ".pt", ".pth")
    return any(line.strip().lower().endswith(weight_suffixes) for line in completed.stdout.splitlines())


def validate_no_provider_calls(failures: list[str]) -> None:
    runner_path = ROOT / "scripts" / "run_local_qwen_goldset_eval_001.py"
    if not runner_path.is_file():
        failures.append(f"missing runner script: {rel(runner_path)}")
        return
    text = runner_path.read_text(encoding="utf-8")
    for label, pattern in BLOCKED_PROVIDER_PATTERNS.items():
        if pattern in text:
            failures.append(f"{rel(runner_path)} contains blocked provider/API pattern: {label}")


def require_fields(result: dict[str, Any], failures: list[str]) -> None:
    required = {
        "experiment_id",
        "status",
        "quality_status",
        "runner_implemented",
        "primary_model",
        "planner_schema_mode",
        "gold_case_count_total",
        "case_count_attempted",
        "case_count_completed",
        "schema_valid_count",
        "verifier_pass_count",
        "gold_match_count",
        "exact_match_count",
        "semantic_match_count",
        "failed_case_count",
        "failed_cases",
        "failure_class_counts",
        "qwen_vs_deterministic_summary",
        "quality_property_summary",
        "current_utterance_fidelity_result",
        "and_or_fidelity_result",
        "negation_fidelity_result",
        "voice_not_writing_result",
        "team_state_poisoning_result",
        "internal_policy_leak_result",
        "fake_side_effect_result",
        "unsupported_claim_result",
        "sales_action_result",
        "latency_metrics",
        "local_model_calls_made",
        "provider_calls_made",
        "openai_api_calls_made",
        "live_tts_calls_made",
        "provider_side_effects_made",
        "model_download_attempted",
        "model_redownloaded",
        "model_weights_committed",
        "runtime_behavior_changed",
        "response_text_changed",
        "raw_private_transcript_copied_to_public_evidence",
        "case_text_stored_in_evidence",
        "cases",
    }
    missing = sorted(required - set(result))
    if missing:
        failures.append(f"result.json missing field(s): {missing}")


def validate_latency_metrics(result: dict[str, Any], failures: list[str]) -> None:
    metrics = result.get("latency_metrics")
    if not isinstance(metrics, dict):
        failures.append("latency_metrics must be an object")
        return
    required = {
        "model_load_time_ms",
        "total_generation_latency_ms",
        "average_generation_latency_ms",
        "p50_generation_latency_ms",
        "p90_generation_latency_ms",
        "slowest_cases",
        "tokens_generated",
        "prompt_tokens_total",
        "peak_gpu_memory_bytes",
        "correlation",
    }
    missing = sorted(required - set(metrics))
    if missing:
        failures.append(f"latency_metrics missing field(s): {missing}")
    if result.get("case_count_completed", 0) > 0:
        if not isinstance(metrics.get("slowest_cases"), list):
            failures.append("latency_metrics.slowest_cases must be a list")
        if metrics.get("total_generation_latency_ms") is None:
            failures.append("latency_metrics.total_generation_latency_ms is required after inference")
        if metrics.get("average_generation_latency_ms") is None:
            failures.append("latency_metrics.average_generation_latency_ms is required after inference")
        if metrics.get("p50_generation_latency_ms") is None:
            failures.append("latency_metrics.p50_generation_latency_ms is required after inference")
        if metrics.get("p90_generation_latency_ms") is None:
            failures.append("latency_metrics.p90_generation_latency_ms is required after inference")


def validate_cases(result: dict[str, Any], failures: list[str]) -> None:
    cases = result.get("cases")
    if not isinstance(cases, list):
        failures.append("cases must be a list")
        return
    if result.get("case_count_completed") != len(cases):
        failures.append("case_count_completed must equal len(cases)")
    for index, item in enumerate(cases, start=1):
        if not isinstance(item, dict):
            failures.append(f"cases[{index}] must be an object")
            continue
        planner_output = item.get("planner_output")
        schema_errors = item.get("schema_errors", [])
        if planner_output is not None:
            if not isinstance(planner_output, dict):
                failures.append(f"cases[{index}].planner_output must be object or null")
            else:
                actual_schema_errors = validate_conversation_brain_output(planner_output)
                if actual_schema_errors != schema_errors:
                    failures.append(
                        f"cases[{index}] schema_errors mismatch: expected {actual_schema_errors!r}, got {schema_errors!r}"
                    )
        if item.get("planner_schema_mode") != COMPACT_PLANNER_SCHEMA_MODE:
            failures.append(f"cases[{index}].planner_schema_mode must be compact")
        compact_output = item.get("compact_planner_output")
        if compact_output is not None:
            if not isinstance(compact_output, dict):
                failures.append(f"cases[{index}].compact_planner_output must be object or null")
            else:
                compact_errors = validate_compact_conversation_brain_output(compact_output)
                if compact_errors != item.get("compact_schema_errors", []):
                    failures.append(
                        f"cases[{index}] compact_schema_errors mismatch: expected {compact_errors!r}, got {item.get('compact_schema_errors', [])!r}"
                    )
        comparison = item.get("qwen_gold_comparison")
        if not isinstance(comparison, dict):
            failures.append(f"cases[{index}].qwen_gold_comparison is required")
        elif "semantic_match" not in comparison or "exact_match" not in comparison:
            failures.append(f"cases[{index}].qwen_gold_comparison missing match fields")
        deterministic = item.get("deterministic_gold_comparison")
        if not isinstance(deterministic, dict):
            failures.append(f"cases[{index}].deterministic_gold_comparison is required")
        qwen_vs_deterministic = item.get("qwen_vs_deterministic")
        if not isinstance(qwen_vs_deterministic, dict):
            failures.append(f"cases[{index}].qwen_vs_deterministic is required")


def validate_evidence(failures: list[str]) -> str:
    if not RESULT_PATH.exists() and not REPORT_PATH.exists():
        return "not_run"
    if not RESULT_PATH.is_file():
        failures.append(f"missing result evidence: {rel(RESULT_PATH)}")
        return "invalid"
    if not REPORT_PATH.is_file():
        failures.append(f"missing report evidence: {rel(REPORT_PATH)}")
    try:
        result = json.loads(RESULT_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        failures.append(f"result.json invalid JSON: {exc}")
        return "invalid"
    if not isinstance(result, dict):
        failures.append("result.json must be a JSON object")
        return "invalid"

    require_fields(result, failures)
    if result.get("experiment_id") != EXPERIMENT_ID:
        failures.append(f"experiment_id must be {EXPERIMENT_ID!r}")
    if result.get("runner_implemented") is not True:
        failures.append("runner_implemented must be true")
    if result.get("primary_model") != PRIMARY_MODEL_ID:
        failures.append(f"primary_model must be {PRIMARY_MODEL_ID!r}")
    if result.get("planner_schema_mode") != COMPACT_PLANNER_SCHEMA_MODE:
        failures.append("planner_schema_mode must be compact")
    for key in (
        "provider_calls_made",
        "openai_api_calls_made",
        "live_tts_calls_made",
        "provider_side_effects_made",
        "model_download_attempted",
        "model_redownloaded",
        "model_weights_committed",
        "runtime_behavior_changed",
        "response_text_changed",
        "raw_private_transcript_copied_to_public_evidence",
        "case_text_stored_in_evidence",
    ):
        if result.get(key) is not False:
            failures.append(f"{key} must be false")
    if git_model_weights_committed():
        failures.append("model weights are tracked by git under local_artifacts")

    completed = result.get("case_count_completed")
    attempted = result.get("case_count_attempted")
    if not isinstance(attempted, int):
        failures.append("case_count_attempted must be an integer")
    if not isinstance(completed, int):
        failures.append("case_count_completed must be an integer")
    if isinstance(completed, int) and completed > 0:
        for key in ("schema_valid_count", "verifier_pass_count", "gold_match_count", "semantic_match_count"):
            if not isinstance(result.get(key), int):
                failures.append(f"{key} must be an integer")
        if result.get("local_model_calls_made") is not True and result.get("local_model_call_count", 0) > 0:
            failures.append("local_model_calls_made must be true when local_model_call_count is positive")
        if result.get("failed_case_count", 0) > 0 and not result.get("failed_cases"):
            failures.append("failed_cases must list failures when failed_case_count is positive")

    raw_text = RESULT_PATH.read_text(encoding="utf-8")
    for blocked_field in ("raw_buyer_text", "sanitized_buyer_text", "normalized_transcript"):
        if f'"{blocked_field}"' in raw_text:
            failures.append(f"result evidence must not store {blocked_field}")

    validate_latency_metrics(result, failures)
    validate_cases(result, failures)
    return str(result.get("status") or "present")


def main() -> int:
    failures: list[str] = []
    validate_no_provider_calls(failures)
    evidence_status = validate_evidence(failures)
    summary = {
        "validator": "validate_local_qwen_goldset_eval_001",
        "status": "pass" if not failures else "fail",
        "evidence_status": evidence_status,
        "failures": failures,
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
