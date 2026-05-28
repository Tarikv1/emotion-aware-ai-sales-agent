#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import time
from typing import Any

from benchmark_local_qwen_live_action_latency_001 import (  # noqa: E402
    FACT_IDS,
    FACT_SUMMARIES,
    benchmark_cases,
    live_action_prompt,
    summarize_mode,
)
from local_ollama_qwen_utils_001 import (  # noqa: E402
    GENERATED_DIR,
    OLLAMA_MODEL,
    TARGETS_SECONDS,
    approx_token_count,
    audit_side_effects,
    env_gate_report,
    http_json,
    mode_target_met,
    ollama_benchmark_enabled,
    qwen_ollama_model_present,
    utc_now,
    write_json,
    write_text,
)
from runtime.llm_brain.live_action_prompt import default_available_action_ids  # noqa: E402
from runtime.llm_brain.live_action_verifier import parse_live_action_json, verify_live_action_output  # noqa: E402


EXPERIMENT_ID = "LOCAL-QWEN-OLLAMA-LIVE-ACTION-BENCHMARK-001"
OUT_DIR = GENERATED_DIR / EXPERIMENT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"
MODE_NUM_PREDICT = {
    "minimal_live_action_prompt": 64,
    "minimal_live_action_prompt_with_replan_context": 64,
    "constrained_action_selector_prompt": 32,
}


def constrained_action_selector_prompt(case: dict[str, Any]) -> str:
    memory = case.get("memory") or {}
    context = {
        "buyer": case["buyer"],
        "memory": memory,
        "action_ids": default_available_action_ids(),
        "approved_fact_ids": FACT_IDS,
        "approved_fact_summaries": FACT_SUMMARIES,
    }
    return "\n".join(
        [
            "You are the LLM conversation brain. Pick the next sales-call action and short buyer-facing wording.",
            "Return exactly one JSON object with action_id, slots, memory_updates, uncertainty, say.",
            "Use one provided action_id. slots and memory_updates must be JSON objects.",
            "say must be natural, short, buyer-facing, and must not mention schemas, routing, policy, or confidence.",
            "Do not claim email, calendar, CRM, purchase, ticket, TTS, or other side effects happened.",
            "Context:",
            json.dumps(context, ensure_ascii=False, separators=(",", ":")),
        ]
    )


def modes_for_case(case: dict[str, Any]) -> dict[str, str]:
    return {
        "minimal_live_action_prompt": live_action_prompt(case),
        "minimal_live_action_prompt_with_replan_context": live_action_prompt(case, with_replan_context=True),
        "constrained_action_selector_prompt": constrained_action_selector_prompt(case),
    }


def base_result(limit: int | None) -> dict[str, Any]:
    cases = benchmark_cases()
    if limit is not None:
        cases = cases[:limit]
    return {
        "experiment_id": EXPERIMENT_ID,
        "generated_at": utc_now(),
        "status": "not_run",
        "benchmark_run": False,
        "not_run_reason": "",
        "backend": "ollama_local",
        "model_name": OLLAMA_MODEL,
        "localhost_api_base": "http://localhost:11434",
        "localhost_only": True,
        "provider_api": False,
        "env_gates": env_gate_report(),
        "case_count": len(cases),
        "mode_names": sorted(MODE_NUM_PREDICT),
        "latency_targets_seconds": TARGETS_SECONDS,
        "target_met": None,
        "quality_acceptable": False,
        "fastest_mode": "",
        "metrics_by_mode": {},
        "warm_metrics_by_mode": {},
        "cold_request": {},
        "rows": [],
        "local_model_calls_made": False,
        "ollama_localhost_calls_made": False,
        "ollama_local_model_call_count": 0,
        "ollama_pull_attempted": False,
        "training_rerun": False,
        "provider_calls_made": False,
        "openai_api_calls_made": False,
        "live_tts_calls_made": False,
        "provider_side_effects_made": False,
        "actual_pruning_performed": False,
        "runtime_behavior_changed": False,
        "response_text_changed": False,
        "adapter_live_ready": False,
        "live_wiring_allowed": False,
        "side_effects": audit_side_effects(),
    }


def generate_ollama(prompt: str, *, mode: str) -> tuple[str, dict[str, Any], float]:
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt + "\n\nReturn exactly one JSON object and no markdown.",
        "stream": False,
        "format": "json",
        "keep_alive": "30m",
        "options": {
            "temperature": 0,
            "num_predict": MODE_NUM_PREDICT[mode],
        },
    }
    started = time.perf_counter()
    response, error = http_json("/api/generate", method="POST", payload=payload, timeout_s=180.0)
    wall_s = round(time.perf_counter() - started, 3)
    if response is None:
        raise RuntimeError(error or "ollama generate failed")
    return str(response.get("response") or ""), response, wall_s


def summarize_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    summary = summarize_mode(rows)
    hard_blocks = [row.get("verifier") or {} for row in rows]
    summary["hard_block_count"] = sum(1 for item in hard_blocks if item.get("hard_block") is True)
    summary["target_met"] = mode_target_met(summary)
    return summary


def fastest_mode(metrics_by_mode: dict[str, Any]) -> str:
    candidates: list[tuple[float, str]] = []
    for mode, metrics in metrics_by_mode.items():
        if not isinstance(metrics, dict):
            continue
        value = metrics.get("total_generation_latency_p50_s")
        if isinstance(value, (int, float)):
            candidates.append((float(value), str(mode)))
    return sorted(candidates)[0][1] if candidates else ""


def run_benchmark(limit: int | None) -> dict[str, Any]:
    result = base_result(limit)
    if not ollama_benchmark_enabled():
        result["not_run_reason"] = "ENABLE_LOCAL_LLM_BRAIN_EXPERIMENT=1, LOCAL_LLM_ENABLED=true, and LOCAL_OLLAMA_BENCHMARK_ENABLED=1 are required before localhost Ollama generation."
        return result

    tags_payload, tags_error = http_json("/api/tags", timeout_s=10.0)
    result["ollama_localhost_calls_made"] = tags_payload is not None
    model_present, resolved_model, parameter_size = qwen_ollama_model_present(tags_payload)
    result["qwen_model_present"] = model_present
    result["qwen_resolved_model"] = resolved_model
    result["qwen_resolved_parameter_size"] = parameter_size
    if not tags_payload:
        result["status"] = "not_run_ollama_unreachable"
        result["not_run_reason"] = f"localhost Ollama API is not reachable: {tags_error}"
        result["side_effects"] = audit_side_effects(ollama_localhost_calls_made=False)
        return result
    if not model_present:
        result["status"] = "not_run_model_missing"
        result["not_run_reason"] = f"{OLLAMA_MODEL} is not present locally; this benchmark will not pull unless LOCAL_OLLAMA_ALLOW_MODEL_PULL=1."
        result["side_effects"] = audit_side_effects(ollama_localhost_calls_made=True)
        return result

    cases = benchmark_cases()
    if limit is not None:
        cases = cases[:limit]
    rows: list[dict[str, Any]] = []
    request_index = 0
    for case in cases:
        for mode, prompt in modes_for_case(case).items():
            raw_output, response, wall_s = generate_ollama(prompt, mode=mode)
            request_phase = "cold" if request_index == 0 else "warm"
            prompt_tokens = response.get("prompt_eval_count")
            generated_tokens = response.get("eval_count")
            if not isinstance(prompt_tokens, int):
                prompt_tokens = approx_token_count(prompt)
            if not isinstance(generated_tokens, int):
                generated_tokens = approx_token_count(raw_output)
            payload, parse_errors = parse_live_action_json(raw_output)
            malformed = bool(parse_errors) or payload is None
            verifier = {"status": "not_applicable"}
            if payload is not None:
                verifier = verify_live_action_output(
                    payload,
                    memory=case.get("memory") or {},
                    approved_fact_ids=FACT_IDS,
                    approved_fact_summaries=FACT_SUMMARIES,
                ).to_dict()
            rows.append(
                {
                    "case_id": case["case_id"],
                    "mode": mode,
                    "backend": "ollama_local",
                    "model_name": resolved_model or OLLAMA_MODEL,
                    "request_phase": request_phase,
                    "prompt_token_count": prompt_tokens,
                    "generated_token_count": generated_tokens,
                    "first_output_latency_s": None,
                    "first_output_latency_note": "stream=false initial benchmark; first output latency unavailable",
                    "total_generation_latency_s": wall_s,
                    "ollama_total_duration_s": round(float(response.get("total_duration") or 0) / 1_000_000_000, 3) if response.get("total_duration") else None,
                    "ollama_load_duration_s": round(float(response.get("load_duration") or 0) / 1_000_000_000, 3) if response.get("load_duration") else None,
                    "ollama_prompt_eval_duration_s": round(float(response.get("prompt_eval_duration") or 0) / 1_000_000_000, 3) if response.get("prompt_eval_duration") else None,
                    "ollama_eval_duration_s": round(float(response.get("eval_duration") or 0) / 1_000_000_000, 3) if response.get("eval_duration") else None,
                    "malformed_output": malformed,
                    "parse_errors": parse_errors,
                    "verifier": verifier,
                }
            )
            request_index += 1

    by_mode: dict[str, list[dict[str, Any]]] = {}
    warm_by_mode: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        by_mode.setdefault(str(row["mode"]), []).append(row)
        if row.get("request_phase") == "warm":
            warm_by_mode.setdefault(str(row["mode"]), []).append(row)
    result["status"] = "pass"
    result["benchmark_run"] = True
    result["rows"] = rows
    result["metrics_by_mode"] = {mode: summarize_rows(mode_rows) for mode, mode_rows in sorted(by_mode.items())}
    result["warm_metrics_by_mode"] = {mode: summarize_rows(mode_rows) for mode, mode_rows in sorted(warm_by_mode.items())}
    result["cold_request"] = rows[0] if rows else {}
    result["local_model_calls_made"] = True
    result["ollama_localhost_calls_made"] = True
    result["ollama_local_model_call_count"] = len(rows)
    live_metrics = result["warm_metrics_by_mode"].get("minimal_live_action_prompt") or result["metrics_by_mode"].get("minimal_live_action_prompt") or {}
    result["target_met"] = mode_target_met(live_metrics)
    result["quality_acceptable"] = bool(
        live_metrics.get("malformed_output_count") == 0
        and live_metrics.get("verifier_pass_count") == live_metrics.get("case_count")
        and live_metrics.get("hard_block_count") == 0
    )
    result["fastest_mode"] = fastest_mode(result["warm_metrics_by_mode"] or result["metrics_by_mode"])
    result["side_effects"] = audit_side_effects(local_model_calls_made=True, ollama_localhost_calls_made=True)
    return result


def parse_args(argv: list[str]) -> int | None:
    if "--limit" not in argv:
        return None
    index = argv.index("--limit")
    try:
        value = int(argv[index + 1])
    except (IndexError, ValueError):
        raise SystemExit("--limit requires a positive integer")
    return value if value > 0 else None


def write_report(result: dict[str, Any]) -> None:
    lines = [
        f"# {EXPERIMENT_ID}",
        "",
        f"- status: {result['status']}",
        f"- benchmark_run: {str(result['benchmark_run']).lower()}",
        f"- not_run_reason: {result.get('not_run_reason') or 'none'}",
        f"- model_name: {result.get('qwen_resolved_model') or result.get('model_name')}",
        f"- local_model_calls_made: {str(result['local_model_calls_made']).lower()}",
        f"- ollama_local_model_call_count: {result['ollama_local_model_call_count']}",
        f"- target_met: {result['target_met']}",
        f"- quality_acceptable: {str(result['quality_acceptable']).lower()}",
        f"- fastest_mode: {result.get('fastest_mode') or 'none'}",
        f"- provider_calls_made: {str(result['provider_calls_made']).lower()}",
        f"- openai_api_calls_made: {str(result['openai_api_calls_made']).lower()}",
        f"- live_tts_calls_made: {str(result['live_tts_calls_made']).lower()}",
        "",
        "## Metrics By Mode",
        "",
        json.dumps(result.get("metrics_by_mode") or {}, indent=2, ensure_ascii=False),
        "",
        "## Warm Metrics By Mode",
        "",
        json.dumps(result.get("warm_metrics_by_mode") or {}, indent=2, ensure_ascii=False),
        "",
        "## Cold Request",
        "",
        json.dumps(result.get("cold_request") or {}, indent=2, ensure_ascii=False),
    ]
    write_text(REPORT_PATH, "\n".join(lines))


def main(argv: list[str]) -> int:
    result = run_benchmark(parse_args(argv))
    write_json(RESULT_PATH, result)
    write_report(result)
    try:
        from audit_qwen7b_pruning_feasibility_001 import write_backend_pruning_decision

        write_backend_pruning_decision()
    except Exception:
        pass
    print(
        json.dumps(
            {
                "status": result["status"],
                "benchmark_run": result["benchmark_run"],
                "target_met": result["target_met"],
                "fastest_mode": result.get("fastest_mode"),
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
