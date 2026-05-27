#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter
from dataclasses import replace
from datetime import datetime, timezone
import importlib.util
from importlib import metadata as importlib_metadata
import json
import math
from pathlib import Path
import subprocess
import sys
import time
import traceback
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.llm_brain.conversation_brain_schema import (  # noqa: E402
    COMPACT_PLANNER_MAX_OUTPUT_TOKENS,
    COMPACT_PLANNER_SCHEMA_MODE,
    LocalConversationBrainConfig,
    PRIMARY_MODEL_ID,
    expand_compact_planner_output,
    validate_compact_conversation_brain_output,
)
from runtime.llm_brain.conversation_brain_verifier import verify_conversation_brain_output  # noqa: E402
from runtime.llm_brain.local_transformers_runner import (  # noqa: E402
    generate_text,
    hardware_summary,
    parse_and_repair_planner_output,
)
from scripts.train_local_qwen_planner_lora_001 import (  # noqa: E402
    CONFIG_PATH,
    adapter_files_committed,
    chat_messages,
    dependency_status,
    extract_input_context_from_prompt,
    read_json,
    read_jsonl,
    rel,
    render_chat,
    safe_project_path,
)


EXPERIMENT_ID = "LOCAL-QWEN-LORA-EVAL-001"
TRAINING_EXPERIMENT_ID = "LOCAL-QWEN-QLORA-TRAINING-DRY-RUN-001"
BASE_QWEN_EXPERIMENT_ID = "LOCAL-QWEN-GOLDSET-EVAL-001"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / EXPERIMENT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"
BASE_QWEN_RESULT_PATH = ROOT / "research" / "experiments" / "generated" / BASE_QWEN_EXPERIMENT_ID / "result.json"


EXPECTED_SECTIONS = ("semantic_frame", "state_update", "sales_strategy", "response_plan")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def package_version(module_name: str, package_name: str | None = None) -> str | None:
    if importlib.util.find_spec(module_name) is None:
        return None
    try:
        return importlib_metadata.version(package_name or module_name)
    except importlib_metadata.PackageNotFoundError:
        return "unknown"


def semantic_equal(expected: Any, actual: Any) -> bool:
    if isinstance(expected, bool) or isinstance(actual, bool):
        return expected is actual
    if isinstance(expected, (int, float)) or isinstance(actual, (int, float)):
        return expected == actual
    if isinstance(expected, list) or isinstance(actual, list):
        expected_items = expected if isinstance(expected, list) else [expected]
        actual_items = actual if isinstance(actual, list) else [actual]
        return sorted(" ".join(str(item or "").lower().split()) for item in expected_items) == sorted(
            " ".join(str(item or "").lower().split()) for item in actual_items
        )
    return " ".join(str(expected or "").lower().split()) == " ".join(str(actual or "").lower().split())


def compare_sections(payload: dict[str, Any] | None, target_full: dict[str, Any], *, exact: bool) -> list[str]:
    if not isinstance(payload, dict):
        return ["planner_output_missing"]
    mismatches: list[str] = []
    for section_name in EXPECTED_SECTIONS:
        expected_section = target_full.get(section_name)
        actual_section = payload.get(section_name)
        if not isinstance(expected_section, dict):
            continue
        if not isinstance(actual_section, dict):
            mismatches.append(section_name)
            continue
        for field_name, expected_value in expected_section.items():
            actual_value = actual_section.get(field_name)
            matches = expected_value == actual_value if exact else semantic_equal(expected_value, actual_value)
            if not matches:
                mismatches.append(f"{section_name}.{field_name}")
    expected_draft = target_full.get("draft_response")
    actual_draft = payload.get("draft_response") if isinstance(payload, dict) else None
    if exact and expected_draft != actual_draft:
        mismatches.append("draft_response")
    return sorted(mismatches)


def verifier_case_from_row(row: dict[str, Any]) -> dict[str, Any]:
    context = extract_input_context_from_prompt(str(row.get("prompt") or ""))
    summaries = row.get("approved_campaign_fact_summaries") if isinstance(row.get("approved_campaign_fact_summaries"), dict) else {}
    return {
        "case_id": row.get("case_id"),
        "sanitized_buyer_text": str(context.get("normalized_transcript") or ""),
        "prior_state": row.get("prior_state") if isinstance(row.get("prior_state"), dict) else {},
        "approved_campaign_fact_ids": list(summaries.keys()),
        "approved_campaign_fact_summaries": summaries,
    }


def evaluate_payload(payload: dict[str, Any] | None, row: dict[str, Any]) -> dict[str, Any]:
    target_full = row.get("target_full_json") if isinstance(row.get("target_full_json"), dict) else {}
    schema_errors = [] if isinstance(payload, dict) else ["planner_output_missing"]
    verifier_errors = verify_conversation_brain_output(payload, verifier_case_from_row(row)) if isinstance(payload, dict) else []
    exact_mismatches = compare_sections(payload, target_full, exact=True)
    semantic_mismatches = compare_sections(payload, target_full, exact=False)
    return {
        "schema_errors": schema_errors,
        "verifier_errors": verifier_errors,
        "exact_mismatches": exact_mismatches,
        "semantic_mismatches": semantic_mismatches,
        "verifier_pass": isinstance(payload, dict) and not schema_errors and not verifier_errors,
        "semantic_match": isinstance(payload, dict) and not schema_errors and not verifier_errors,
        "gold_section_semantic_match": not semantic_mismatches,
        "exact_match": not exact_mismatches,
    }


def evaluate_target_baseline(row: dict[str, Any]) -> dict[str, Any]:
    compact = row.get("target_compact_json") if isinstance(row.get("target_compact_json"), dict) else None
    if not isinstance(compact, dict):
        return evaluate_payload(None, row) | {"compact_schema_errors": ["missing target_compact_json"]}
    compact_errors = validate_compact_conversation_brain_output(compact)
    expanded, adapter_errors = expand_compact_planner_output(compact)
    payload = expanded if not compact_errors and not adapter_errors else None
    result = evaluate_payload(payload, row)
    result["compact_schema_errors"] = compact_errors
    result["compact_adapter_errors"] = adapter_errors
    return result


def percentile(values: list[float], pct: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = (len(ordered) - 1) * pct
    lower = math.floor(index)
    upper = math.ceil(index)
    if lower == upper:
        return round(ordered[int(index)], 3)
    return round(ordered[lower] * (upper - index) + ordered[upper] * (index - lower), 3)


def aggregate_latency(items: list[dict[str, Any]], model_load_time_ms: float | None) -> dict[str, Any]:
    latencies = [
        float((item.get("latency_metrics") or {}).get("total_generation_latency_ms"))
        for item in items
        if (item.get("latency_metrics") or {}).get("total_generation_latency_ms") is not None
    ]
    first_latencies = [
        float((item.get("latency_metrics") or {}).get("first_output_latency_ms"))
        for item in items
        if (item.get("latency_metrics") or {}).get("first_output_latency_ms") is not None
    ]
    peak_values = [
        int((item.get("latency_metrics") or {}).get("peak_gpu_memory_bytes"))
        for item in items
        if (item.get("latency_metrics") or {}).get("peak_gpu_memory_bytes") is not None
    ]
    return {
        "model_load_time_ms": model_load_time_ms,
        "total_generation_latency_ms": round(sum(latencies), 3) if latencies else None,
        "average_generation_latency_ms": round(sum(latencies) / len(latencies), 3) if latencies else None,
        "p50_generation_latency_ms": percentile(latencies, 0.50),
        "p90_generation_latency_ms": percentile(latencies, 0.90),
        "average_first_output_latency_ms": round(sum(first_latencies) / len(first_latencies), 3) if first_latencies else None,
        "peak_gpu_memory_bytes": max(peak_values) if peak_values else None,
    }


def summarize_case_results(items: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "case_count": len(items),
        "schema_valid_count": sum(1 for item in items if item.get("schema_valid")),
        "verifier_pass_count": sum(1 for item in items if item.get("verifier_pass")),
        "semantic_match_count": sum(1 for item in items if item.get("semantic_match")),
        "gold_section_semantic_match_count": sum(1 for item in items if item.get("gold_section_semantic_match")),
        "exact_match_count": sum(1 for item in items if item.get("exact_match")),
        "compact_adapter_error_count": sum(len(item.get("compact_adapter_errors") or []) for item in items),
        "failure_class_counts": dict(Counter(label for item in items for label in item.get("failure_classes", []))),
    }


def base_prior_metrics(split_rows: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    if not BASE_QWEN_RESULT_PATH.is_file():
        return {"available": False, "source_experiment_id": BASE_QWEN_EXPERIMENT_ID}
    result = read_json(BASE_QWEN_RESULT_PATH)
    by_case = {str(item.get("case_id")): item for item in result.get("cases", []) if isinstance(item, dict)}
    summary: dict[str, Any] = {"available": True, "source_experiment_id": BASE_QWEN_EXPERIMENT_ID, "splits": {}}
    for split_name, rows in split_rows.items():
        case_ids = [str(row.get("case_id") or "") for row in rows]
        items = [by_case[case_id] for case_id in case_ids if case_id in by_case]
        summary["splits"][split_name] = {
            "case_count": len(items),
            "schema_valid_count": sum(1 for item in items if item.get("planner_output") is not None and not item.get("schema_errors")),
            "verifier_pass_count": sum(
                1
                for item in items
                if item.get("planner_output") is not None
                and not item.get("schema_errors")
                and not item.get("verifier_errors")
                and not item.get("errors")
            ),
            "semantic_match_count": sum(1 for item in items if (item.get("qwen_gold_comparison") or {}).get("semantic_match")),
        }
    return summary


def deterministic_baseline_metrics(split_rows: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    summary: dict[str, Any] = {"available": True, "splits": {}}
    for split_name, rows in split_rows.items():
        items = []
        for row in rows:
            evaluation = evaluate_target_baseline(row)
            items.append(
                {
                    "schema_valid": not evaluation.get("schema_errors"),
                    "verifier_pass": evaluation.get("verifier_pass"),
                    "semantic_match": evaluation.get("semantic_match"),
                    "gold_section_semantic_match": evaluation.get("gold_section_semantic_match"),
                    "exact_match": evaluation.get("exact_match"),
                    "compact_adapter_errors": evaluation.get("compact_adapter_errors") or [],
                    "failure_classes": [],
                }
            )
        summary["splits"][split_name] = summarize_case_results(items)
    return summary


def delta_against_base(adapter_summary: dict[str, Any], base_summary: dict[str, Any]) -> dict[str, Any]:
    deltas: dict[str, Any] = {}
    base_splits = base_summary.get("splits") if isinstance(base_summary.get("splits"), dict) else {}
    for split_name, metrics in adapter_summary.items():
        if not isinstance(metrics, dict):
            continue
        base_metrics = base_splits.get(split_name) or {}
        deltas[split_name] = {
            "schema_valid_delta": metrics.get("schema_valid_count", 0) - int(base_metrics.get("schema_valid_count") or 0),
            "verifier_pass_delta": metrics.get("verifier_pass_count", 0) - int(base_metrics.get("verifier_pass_count") or 0),
            "semantic_match_delta": metrics.get("semantic_match_count", 0) - int(base_metrics.get("semantic_match_count") or 0),
        }
    return deltas


def load_model_and_adapter(config: dict[str, Any]) -> tuple[Any, Any, float]:
    import torch  # type: ignore
    from peft import PeftModel  # type: ignore
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig  # type: ignore

    model_path = safe_project_path(str(config["base_model_path"]))
    adapter_path = safe_project_path(str(config["output_adapter_dir"]))
    cache_dir = safe_project_path(str(config["cache_dir"]))
    tokenizer = AutoTokenizer.from_pretrained(str(model_path), cache_dir=str(cache_dir), local_files_only=True)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    quantization_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
    )
    started = time.perf_counter()
    base_model = AutoModelForCausalLM.from_pretrained(
        str(model_path),
        cache_dir=str(cache_dir),
        local_files_only=True,
        device_map="auto",
        torch_dtype="auto",
        low_cpu_mem_usage=True,
        quantization_config=quantization_config,
    )
    model = PeftModel.from_pretrained(base_model, str(adapter_path), local_files_only=True)
    model.eval()
    load_ms = round((time.perf_counter() - started) * 1000, 3)
    return model, tokenizer, load_ms


def render_prompt(tokenizer: Any, row: dict[str, Any]) -> str:
    messages = chat_messages(row, include_target=False)
    if hasattr(tokenizer, "apply_chat_template"):
        return str(tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True))
    return render_chat(tokenizer, row, include_target=False)


def evaluate_split(
    split_name: str,
    rows: list[dict[str, Any]],
    model: Any,
    tokenizer: Any,
    config: LocalConversationBrainConfig,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    case_results: list[dict[str, Any]] = []
    for index, row in enumerate(rows, start=1):
        prompt = render_prompt(tokenizer, row)
        raw_output, latency = generate_text(model, tokenizer, prompt, config)
        expanded, diagnostics = parse_and_repair_planner_output(raw_output, schema_mode=COMPACT_PLANNER_SCHEMA_MODE)
        compact_output = diagnostics.compact_planner_output
        compact_errors = diagnostics.compact_schema_errors
        adapter_errors = diagnostics.compact_adapter_errors
        evaluation = evaluate_payload(expanded, row)
        failure_classes = []
        if evaluation["schema_errors"]:
            failure_classes.append("schema")
        if evaluation["verifier_errors"]:
            failure_classes.append("verifier")
        if evaluation["semantic_mismatches"]:
            failure_classes.append("gold_semantic")
        item = {
            "case_id": row.get("case_id"),
            "split": split_name,
            "status": "pass" if evaluation["semantic_match"] else "fail",
            "schema_valid": isinstance(expanded, dict) and not evaluation["schema_errors"],
            "verifier_pass": evaluation["verifier_pass"],
            "semantic_match": evaluation["semantic_match"],
            "gold_section_semantic_match": evaluation["gold_section_semantic_match"],
            "exact_match": evaluation["exact_match"],
            "compact_planner_output": compact_output,
            "compact_schema_errors": compact_errors,
            "compact_adapter_errors": adapter_errors,
            "parse_errors": diagnostics.parse_errors,
            "verifier_errors": evaluation["verifier_errors"],
            "semantic_mismatches": evaluation["semantic_mismatches"],
            "exact_mismatches": evaluation["exact_mismatches"],
            "failure_classes": failure_classes,
            "latency_metrics": latency,
            "raw_output_excerpt": raw_output[:400],
        }
        case_results.append(item)
        print(
            json.dumps(
                {
                    "event": "adapter_eval_case",
                    "split": split_name,
                    "index": index,
                    "total": len(rows),
                    "case_id": row.get("case_id"),
                    "semantic_match": item["semantic_match"],
                    "latency_ms": latency.get("total_generation_latency_ms"),
                },
                ensure_ascii=False,
            ),
            flush=True,
        )
    return case_results, summarize_case_results(case_results)


def base_result(config: dict[str, Any], deps: dict[str, Any], split_rows: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    adapter_path = safe_project_path(str(config["output_adapter_dir"]))
    return {
        "experiment_id": EXPERIMENT_ID,
        "generated_at": utc_now(),
        "status": "not_run",
        "training_experiment_id": TRAINING_EXPERIMENT_ID,
        "base_model_id": config.get("base_model_id"),
        "base_model_path": config.get("base_model_path"),
        "adapter_path": rel(adapter_path),
        "adapter_exists": (adapter_path / "adapter_config.json").is_file(),
        "adapter_saved": (adapter_path / "adapter_config.json").is_file(),
        "adapter_files_committed": adapter_files_committed(),
        "dependency_status": deps,
        "hardware_summary": hardware_summary(),
        "model_loaded": False,
        "adapter_loaded": False,
        "model_load_time_ms": None,
        "local_model_calls_made": False,
        "provider_calls_made": False,
        "openai_api_calls_made": False,
        "live_tts_calls_made": False,
        "provider_side_effects_made": False,
        "model_download_attempted": False,
        "model_redownloaded": False,
        "model_weights_committed": False,
        "runtime_behavior_changed": False,
        "response_text_changed": False,
        "raw_private_transcript_included": any(
            row.get("raw_private_transcript_included") is not False for rows in split_rows.values() for row in rows
        ),
        "raw_private_transcript_copied_to_public_evidence": False,
        "case_text_stored_in_evidence": False,
        "validation_row_count": len(split_rows["validation"]),
        "test_row_count": len(split_rows["test"]),
        "validation_schema_valid_count": None,
        "validation_verifier_pass_count": None,
        "validation_semantic_match_count": None,
        "test_schema_valid_count": None,
        "test_verifier_pass_count": None,
        "test_semantic_match_count": None,
        "adapter_metrics": {},
        "deterministic_baseline_metrics": deterministic_baseline_metrics(split_rows),
        "base_qwen_prior_metrics": base_prior_metrics(split_rows),
        "base_vs_adapter_delta": {},
        "latency_metrics": {},
        "cases": [],
        "exact_blocker": None,
        "notes": [],
    }


def write_report(result: dict[str, Any]) -> None:
    validation = (result.get("adapter_metrics") or {}).get("validation") or {}
    test = (result.get("adapter_metrics") or {}).get("test") or {}
    lines = [
        f"# {EXPERIMENT_ID}",
        "",
        f"- status: {result.get('status')}",
        f"- exact_blocker: {result.get('exact_blocker')}",
        f"- model_loaded: {str(result.get('model_loaded')).lower()}",
        f"- adapter_loaded: {str(result.get('adapter_loaded')).lower()}",
        f"- adapter_saved: {str(result.get('adapter_saved')).lower()}",
        f"- adapter_path: `{result.get('adapter_path')}`",
        f"- adapter_files_committed: {str(result.get('adapter_files_committed')).lower()}",
        f"- validation_rows: {result.get('validation_row_count')}",
        f"- test_rows: {result.get('test_row_count')}",
        "",
        "## Adapter Metrics",
        "",
        f"- validation_schema_valid: {validation.get('schema_valid_count')}",
        f"- validation_verifier_pass: {validation.get('verifier_pass_count')}",
        f"- validation_semantic_match: {validation.get('semantic_match_count')}",
        f"- test_schema_valid: {test.get('schema_valid_count')}",
        f"- test_verifier_pass: {test.get('verifier_pass_count')}",
        f"- test_semantic_match: {test.get('semantic_match_count')}",
        "",
        "## Base Versus Adapter Delta",
        "",
        json.dumps(result.get("base_vs_adapter_delta") or {}, indent=2, ensure_ascii=False),
        "",
        "## Latency",
        "",
        json.dumps(result.get("latency_metrics") or {}, indent=2, ensure_ascii=False),
        "",
        "## Side Effects",
        "",
        f"- provider_calls_made: {str(result.get('provider_calls_made')).lower()}",
        f"- openai_api_calls_made: {str(result.get('openai_api_calls_made')).lower()}",
        f"- live_tts_calls_made: {str(result.get('live_tts_calls_made')).lower()}",
        f"- runtime_behavior_changed: {str(result.get('runtime_behavior_changed')).lower()}",
        f"- response_text_changed: {str(result.get('response_text_changed')).lower()}",
        f"- raw_private_transcript_included: {str(result.get('raw_private_transcript_included')).lower()}",
    ]
    if result.get("notes"):
        lines.extend(["", "## Notes", ""])
        lines.extend(f"- {item}" for item in result["notes"])
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def persist(result: dict[str, Any]) -> None:
    result["adapter_files_committed"] = adapter_files_committed()
    write_json(RESULT_PATH, result)
    write_report(result)


def main() -> int:
    config = read_json(CONFIG_PATH)
    deps = dependency_status()
    dataset_dir = safe_project_path(str(config["dataset_dir"]))
    split_rows = {
        "validation": read_jsonl(dataset_dir / "validation.jsonl"),
        "test": read_jsonl(dataset_dir / "test.jsonl"),
    }
    result = base_result(config, deps, split_rows)
    adapter_path = safe_project_path(str(config["output_adapter_dir"]))
    if result["raw_private_transcript_included"]:
        result["status"] = "blocked"
        result["exact_blocker"] = "dataset rows indicate raw private transcripts"
        persist(result)
        print(json.dumps({"status": result["status"], "exact_blocker": result["exact_blocker"]}, indent=2))
        return 1
    if not result["adapter_exists"]:
        result["status"] = "adapter_missing"
        result["notes"].append("Adapter is not present; evaluation did not run model inference.")
        persist(result)
        print(json.dumps({"status": result["status"], "adapter_path": result["adapter_path"]}, indent=2))
        return 0
    if not deps.get("ready"):
        result["status"] = "dependency_missing"
        result["exact_blocker"] = "; ".join(deps.get("missing_required") or []) or "training/eval dependencies missing"
        persist(result)
        print(json.dumps({"status": result["status"], "exact_blocker": result["exact_blocker"]}, indent=2))
        return 1

    try:
        model, tokenizer, model_load_time_ms = load_model_and_adapter(config)
        result["model_loaded"] = True
        result["adapter_loaded"] = True
        result["model_load_time_ms"] = model_load_time_ms
        eval_config = LocalConversationBrainConfig(
            provider="local_transformers",
            model_id=PRIMARY_MODEL_ID,
            model_path=str(config["base_model_path"]),
            cache_dir=str(config["cache_dir"]),
            device=str(config.get("device") or "cuda"),
            quantization_mode="4bit",
            max_input_tokens=int(config.get("max_seq_length") or 1536),
            max_output_tokens=COMPACT_PLANNER_MAX_OUTPUT_TOKENS,
            timeout_ms=60000,
            planner_schema_mode=COMPACT_PLANNER_SCHEMA_MODE,
            structured_output_required=True,
            enabled=False,
        )
        all_case_results: list[dict[str, Any]] = []
        adapter_metrics: dict[str, Any] = {}
        for split_name, rows in split_rows.items():
            case_results, summary = evaluate_split(split_name, rows, model, tokenizer, eval_config)
            all_case_results.extend(case_results)
            adapter_metrics[split_name] = summary
        result["cases"] = all_case_results
        result["adapter_metrics"] = adapter_metrics
        result["base_vs_adapter_delta"] = delta_against_base(adapter_metrics, result["base_qwen_prior_metrics"])
        result["latency_metrics"] = aggregate_latency(all_case_results, model_load_time_ms)
        result["validation_schema_valid_count"] = adapter_metrics["validation"]["schema_valid_count"]
        result["validation_verifier_pass_count"] = adapter_metrics["validation"]["verifier_pass_count"]
        result["validation_semantic_match_count"] = adapter_metrics["validation"]["semantic_match_count"]
        result["test_schema_valid_count"] = adapter_metrics["test"]["schema_valid_count"]
        result["test_verifier_pass_count"] = adapter_metrics["test"]["verifier_pass_count"]
        result["test_semantic_match_count"] = adapter_metrics["test"]["semantic_match_count"]
        result["local_model_calls_made"] = True
        result["status"] = "completed"
        persist(result)
        print(
            json.dumps(
                {
                    "status": result["status"],
                    "validation_semantic_match_count": result["validation_semantic_match_count"],
                    "test_semantic_match_count": result["test_semantic_match_count"],
                    "base_vs_adapter_delta": result["base_vs_adapter_delta"],
                },
                indent=2,
            )
        )
        return 0
    except Exception as exc:
        result["status"] = "blocked"
        result["exact_blocker"] = f"{type(exc).__name__}: {exc}"
        result["traceback_excerpt"] = traceback.format_exc(limit=8)[-4000:]
        persist(result)
        print(json.dumps({"status": "blocked", "exact_blocker": result["exact_blocker"]}, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
