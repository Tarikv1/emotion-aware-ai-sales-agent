#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import argparse
import json
import math
from pathlib import Path
import sys
import time
import traceback
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.llm_brain.compact_planner_contract import (  # noqa: E402
    compact_label_quality_issues,
    validate_compact_value_contract,
)
from runtime.llm_brain.conversation_brain_schema import (  # noqa: E402
    COMPACT_PLANNER_MAX_OUTPUT_TOKENS,
    COMPACT_PLANNER_SCHEMA_MODE,
    LocalConversationBrainConfig,
    PRIMARY_MODEL_ID,
)
from runtime.llm_brain.local_transformers_runner import (  # noqa: E402
    generate_text,
    hardware_summary,
    parse_and_repair_planner_output,
)
from scripts.evaluate_local_qwen_planner_lora_001 import evaluate_payload, summarize_case_results  # noqa: E402
from scripts.train_local_qwen_planner_lora_001 import (  # noqa: E402
    adapter_files_committed,
    dependency_status,
    read_jsonl,
    rel,
    safe_project_path,
    target_json_text,
)
from scripts.train_local_qwen_planner_lora_curriculum_001 import (  # noqa: E402
    CURRICULUM_CONFIG,
    DEFAULT_ADAPTER_PATH,
)
from scripts.train_local_qwen_planner_lora_tiny_overfit_001 import render_eval_chat  # noqa: E402


EXPERIMENT_ID = "LOCAL-QWEN-LORA-CURRICULUM-EVAL-001"
DATASET_EXPERIMENT_ID = "LOCAL-QWEN-CURRICULUM-DATASET-001"
TRAINING_EXPERIMENT_ID = "LOCAL-QWEN-LORA-CURRICULUM-TRAINING-001"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / EXPERIMENT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"
DATASET_DIR = ROOT / "research" / "experiments" / "generated" / DATASET_EXPERIMENT_ID
TRAINING_RESULT_PATH = ROOT / "research" / "experiments" / "generated" / TRAINING_EXPERIMENT_ID / "result.json"
TINY_RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "LOCAL-QWEN-LORA-TINY-OVERFIT-001" / "result.json"
TINY_DATASET_PATH = ROOT / "research" / "experiments" / "generated" / "LOCAL-QWEN-TINY-OVERFIT-DATASET-001" / "train.jsonl"
SPLIT_FILES = {
    "tiny_comparison": DATASET_DIR / "stage1_tiny.jsonl",
    "train_sample": DATASET_DIR / "stage2_20.jsonl",
    "validation": DATASET_DIR / "validation.jsonl",
    "test": DATASET_DIR / "test.jsonl",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


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


def generation_config() -> LocalConversationBrainConfig:
    return LocalConversationBrainConfig(
        provider="local_transformers",
        model_id=PRIMARY_MODEL_ID,
        model_path=str(CURRICULUM_CONFIG["base_model_path"]),
        cache_dir=str(CURRICULUM_CONFIG["cache_dir"]),
        device="cuda",
        quantization_mode="4bit",
        max_input_tokens=int(CURRICULUM_CONFIG["max_seq_length"]),
        max_output_tokens=COMPACT_PLANNER_MAX_OUTPUT_TOKENS,
        timeout_ms=60000,
        planner_schema_mode=COMPACT_PLANNER_SCHEMA_MODE,
        structured_output_required=True,
        enabled=False,
    )


def load_curriculum_model(adapter_path: str) -> tuple[Any, Any, float, bool]:
    import torch  # type: ignore
    from peft import PeftModel  # type: ignore
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig  # type: ignore

    model_path = safe_project_path(str(CURRICULUM_CONFIG["base_model_path"]))
    cache_dir = safe_project_path(str(CURRICULUM_CONFIG["cache_dir"]))
    tokenizer = AutoTokenizer.from_pretrained(
        str(model_path),
        cache_dir=str(cache_dir),
        local_files_only=True,
        trust_remote_code=False,
    )
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
        trust_remote_code=False,
    )
    model = PeftModel.from_pretrained(base_model, str(safe_project_path(adapter_path)), local_files_only=True)
    model.eval()
    return model, tokenizer, round((time.perf_counter() - started) * 1000, 3), True


def unload_model(model: Any, tokenizer: Any) -> None:
    del model
    del tokenizer
    try:
        import torch  # type: ignore

        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except Exception:
        pass


def render_prompt(tokenizer: Any, row: dict[str, Any]) -> str:
    return render_eval_chat(tokenizer, row)


def evaluate_case(model: Any, tokenizer: Any, config: LocalConversationBrainConfig, split: str, row: dict[str, Any]) -> dict[str, Any]:
    prompt = render_prompt(tokenizer, row)
    target_compact = row.get("target_compact_json") if isinstance(row.get("target_compact_json"), dict) else {}
    raw_output, latency = generate_text(model, tokenizer, prompt, config)
    expanded, diagnostics = parse_and_repair_planner_output(raw_output, schema_mode=COMPACT_PLANNER_SCHEMA_MODE)
    compact_output = diagnostics.compact_planner_output
    compact_schema_errors = diagnostics.compact_schema_errors
    compact_adapter_errors = diagnostics.compact_adapter_errors
    compact_contract_errors = (
        validate_compact_value_contract(compact_output) if isinstance(compact_output, dict) else ["compact output missing"]
    )
    compact_quality_issues = compact_label_quality_issues(compact_output) if isinstance(compact_output, dict) else []
    evaluation = evaluate_payload(expanded, row)
    exact_match = isinstance(compact_output, dict) and compact_output == target_compact
    generic_count = sum(
        1
        for issue in compact_quality_issues
        if issue.get("issue") in {"generic_action", "generic_sub_intent", "generic_act"}
    )
    deprecated_count = sum(1 for issue in compact_quality_issues if issue.get("issue") == "deprecated_label")
    case_id_label_leak_count = sum(1 for issue in compact_quality_issues if issue.get("issue") == "case_id_label_leak")
    compact_contract_valid = (
        isinstance(compact_output, dict)
        and not compact_schema_errors
        and not compact_adapter_errors
        and not compact_contract_errors
        and deprecated_count == 0
        and case_id_label_leak_count == 0
        and generic_count == 0
    )
    malformed = not isinstance(compact_output, dict) or bool(compact_schema_errors or compact_adapter_errors)
    failure_classes: list[str] = []
    if evaluation["schema_errors"]:
        failure_classes.append("schema")
    if evaluation["verifier_errors"]:
        failure_classes.append("verifier")
    if not compact_contract_valid:
        failure_classes.append("compact_contract")
    if evaluation["semantic_mismatches"]:
        failure_classes.append("strict_gold_semantic")
    response_plan_mismatches = [
        mismatch
        for mismatch in evaluation["semantic_mismatches"]
        if mismatch == "response_plan" or mismatch.startswith("response_plan.")
    ]
    if response_plan_mismatches:
        failure_classes.append("strict_gold_response_plan")
    if malformed:
        failure_classes.append("malformed_output")
    return {
        "case_id": row.get("case_id"),
        "split": split,
        "category": row.get("category") or row.get("source_type"),
        "schema_valid": isinstance(expanded, dict) and not evaluation["schema_errors"],
        "verifier_pass": evaluation["verifier_pass"],
        "semantic_match": evaluation["semantic_match"],
        "compact_contract_valid": compact_contract_valid,
        "strict_gold_semantic_match": evaluation["gold_section_semantic_match"],
        "strict_gold_response_plan_match": evaluation["gold_response_plan_match"],
        "exact_match": exact_match,
        "deprecated_label_count": deprecated_count,
        "case_id_label_leak_count": case_id_label_leak_count,
        "generic_label_count": generic_count,
        "malformed_output": malformed,
        "failure_classes": failure_classes,
        "compact_planner_output": compact_output,
        "compact_schema_errors": compact_schema_errors,
        "compact_adapter_errors": compact_adapter_errors,
        "compact_contract_errors": compact_contract_errors,
        "compact_label_quality_issues": compact_quality_issues,
        "parse_errors": diagnostics.parse_errors,
        "verifier_errors": evaluation["verifier_errors"],
        "semantic_mismatches": evaluation["semantic_mismatches"],
        "gold_response_plan_mismatches": response_plan_mismatches,
        "latency_metrics": latency,
        "raw_output_excerpt": raw_output[:400],
        "target_present_in_generation_prompt": target_json_text(row) in prompt,
    }


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
    peaks = [
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
        "average_first_output_latency_ms": round(sum(first_latencies) / len(first_latencies), 3)
        if first_latencies
        else None,
        "peak_gpu_memory_bytes": max(peaks) if peaks else None,
    }


def summarize_items(items: list[dict[str, Any]], model_load_time_ms: float | None) -> dict[str, Any]:
    base = summarize_case_results(
        [
            {
                **item,
                "exact_target_match": item.get("exact_match"),
                "gold_section_semantic_match": item.get("strict_gold_semantic_match"),
                "gold_response_plan_match": item.get("strict_gold_response_plan_match"),
            }
            for item in items
        ]
    )
    failure_counts = Counter(kind for item in items for kind in item.get("failure_classes") or [])
    base.update(
        {
            "case_count": len(items),
            "strict_gold_response_plan_match_count": sum(1 for item in items if item.get("strict_gold_response_plan_match")),
            "exact_match_count": sum(1 for item in items if item.get("exact_match")),
            "deprecated_label_count": sum(int(item.get("deprecated_label_count") or 0) for item in items),
            "case_id_label_leak_count": sum(int(item.get("case_id_label_leak_count") or 0) for item in items),
            "generic_label_count": sum(int(item.get("generic_label_count") or 0) for item in items),
            "malformed_output_count": sum(1 for item in items if item.get("malformed_output")),
            "failure_class_counts": dict(failure_counts),
            "latency_metrics": aggregate_latency(items, model_load_time_ms),
            "target_present_in_generation_prompt_count": sum(1 for item in items if item.get("target_present_in_generation_prompt")),
        }
    )
    return base


def evaluate_curriculum_adapter(adapter_path: str, split_limits: dict[str, int | None]) -> dict[str, Any]:
    model = None
    tokenizer = None
    result: dict[str, Any] = {
        "adapter_path": adapter_path,
        "adapter_exists": (safe_project_path(adapter_path) / "adapter_config.json").is_file(),
        "adapter_loaded": False,
        "status": "not_run",
        "splits": {},
        "exact_blocker": None,
    }
    if not result["adapter_exists"]:
        result["status"] = "adapter_missing"
        return result
    try:
        model, tokenizer, load_ms, adapter_loaded = load_curriculum_model(adapter_path)
        result["adapter_loaded"] = adapter_loaded
        config = generation_config()
        for split, path in SPLIT_FILES.items():
            rows = read_jsonl(path)
            limit = split_limits.get(split)
            if limit is not None:
                rows = rows[:limit]
            case_results: list[dict[str, Any]] = []
            for index, row in enumerate(rows, start=1):
                item = evaluate_case(model, tokenizer, config, split, row)
                case_results.append(item)
                print(
                    json.dumps(
                        {
                            "event": "curriculum_eval_case",
                            "split": split,
                            "index": index,
                            "total": len(rows),
                            "case_id": row.get("case_id"),
                            "schema_valid": item["schema_valid"],
                            "contract": item["compact_contract_valid"],
                            "strict": item["strict_gold_semantic_match"],
                            "strict_response": item["strict_gold_response_plan_match"],
                            "exact": item["exact_match"],
                            "latency_ms": item["latency_metrics"].get("total_generation_latency_ms"),
                        },
                        ensure_ascii=False,
                    ),
                    flush=True,
                )
            result["splits"][split] = {
                "path": rel(path),
                "case_count": len(rows),
                "cases": case_results,
                "metrics": summarize_items(case_results, load_ms if split == "tiny_comparison" else None),
            }
        result["status"] = "completed"
        return result
    except Exception as exc:
        result["status"] = "blocked"
        result["exact_blocker"] = f"{type(exc).__name__}: {exc}"
        result["traceback_excerpt"] = traceback.format_exc(limit=8)[-4000:]
        return result
    finally:
        if model is not None and tokenizer is not None:
            unload_model(model, tokenizer)


def prior_comparison_from_tiny_result() -> dict[str, Any]:
    tiny_result = read_json(TINY_RESULT_PATH)
    evaluation = tiny_result.get("evaluation") if isinstance(tiny_result.get("evaluation"), dict) else {}
    comparison = evaluation.get("comparison") if isinstance(evaluation.get("comparison"), dict) else {}
    return {
        "source": rel(TINY_RESULT_PATH) if TINY_RESULT_PATH.is_file() else None,
        "status": "available" if comparison else "missing",
        "base_qwen": comparison.get("base_qwen"),
        "lora_002": comparison.get("lora_002"),
        "tiny_adapter": comparison.get("tiny_adapter"),
    }


def split_gate(metrics: dict[str, Any]) -> bool:
    count = int(metrics.get("case_count") or 0)
    return (
        count > 0
        and int(metrics.get("schema_valid_count") or 0) == count
        and int(metrics.get("verifier_pass_count") or 0) == count
        and int(metrics.get("compact_contract_valid_count") or 0) == count
        and int(metrics.get("strict_gold_semantic_match_count") or 0) == count
        and int(metrics.get("strict_gold_response_plan_match_count") or 0) == count
        and int(metrics.get("deprecated_label_count") or 0) == 0
        and int(metrics.get("case_id_label_leak_count") or 0) == 0
        and int(metrics.get("generic_label_count") or 0) == 0
        and int(metrics.get("malformed_output_count") or 0) == 0
        and int(metrics.get("target_present_in_generation_prompt_count") or 0) == 0
    )


def write_report(result: dict[str, Any]) -> None:
    curriculum = result.get("curriculum_adapter") if isinstance(result.get("curriculum_adapter"), dict) else {}
    split_summary = {
        split: payload.get("metrics")
        for split, payload in (curriculum.get("splits") or {}).items()
        if isinstance(payload, dict)
    }
    lines = [
        f"# {EXPERIMENT_ID}",
        "",
        f"- status: {result.get('status')}",
        f"- adapter_path: `{result.get('adapter_path')}`",
        f"- adapter_live_ready: {str(result.get('adapter_live_ready')).lower()}",
        f"- quality_gate_passed: {str(result.get('quality_gate_passed')).lower()}",
        f"- provider_calls_made: {str(result.get('provider_calls_made')).lower()}",
        f"- openai_api_calls_made: {str(result.get('openai_api_calls_made')).lower()}",
        f"- live_tts_calls_made: {str(result.get('live_tts_calls_made')).lower()}",
        f"- runtime_behavior_changed: {str(result.get('runtime_behavior_changed')).lower()}",
        f"- response_text_changed: {str(result.get('response_text_changed')).lower()}",
        "",
        "## Split Metrics",
        "",
        json.dumps(split_summary, indent=2, ensure_ascii=False),
        "",
        "## Prior Base/Tiny Comparison",
        "",
        json.dumps(result.get("prior_tiny_probe_comparison") or {}, indent=2, ensure_ascii=False),
    ]
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate local Qwen curriculum LoRA adapter.")
    parser.add_argument("--adapter-path", default=DEFAULT_ADAPTER_PATH)
    parser.add_argument("--train-sample-limit", type=int, default=20)
    parser.add_argument("--tiny-comparison-limit", type=int, default=8)
    parser.add_argument("--validation-limit", type=int, default=None)
    parser.add_argument("--test-limit", type=int, default=None)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.train_sample_limit is not None and args.train_sample_limit <= 0:
        raise SystemExit("--train-sample-limit must be positive")
    split_limits = {
        "tiny_comparison": args.tiny_comparison_limit,
        "train_sample": args.train_sample_limit,
        "validation": args.validation_limit,
        "test": args.test_limit,
    }
    training_result = read_json(TRAINING_RESULT_PATH)
    curriculum = evaluate_curriculum_adapter(args.adapter_path, split_limits)
    splits = curriculum.get("splits") if isinstance(curriculum.get("splits"), dict) else {}
    validation_metrics = (splits.get("validation") or {}).get("metrics") if isinstance(splits.get("validation"), dict) else {}
    test_metrics = (splits.get("test") or {}).get("metrics") if isinstance(splits.get("test"), dict) else {}
    quality_gate_passed = curriculum.get("status") == "completed" and split_gate(validation_metrics) and split_gate(test_metrics)
    result = {
        "experiment_id": EXPERIMENT_ID,
        "generated_at": utc_now(),
        "status": "completed" if curriculum.get("status") == "completed" else curriculum.get("status"),
        "dataset_experiment_id": DATASET_EXPERIMENT_ID,
        "training_experiment_id": TRAINING_EXPERIMENT_ID,
        "training_status": training_result.get("status"),
        "training_completed": training_result.get("training_completed"),
        "completed_stages": training_result.get("completed_stages"),
        "adapter_path": args.adapter_path,
        "adapter_files_committed": adapter_files_committed(),
        "curriculum_adapter": curriculum,
        "prior_tiny_probe_comparison": prior_comparison_from_tiny_result(),
        "quality_gate_passed": quality_gate_passed,
        "adapter_live_ready": False,
        "adapter_live_ready_reason": "No live dialogue wiring in this phase; strict gates are evidence only.",
        "validation_metrics": validation_metrics,
        "test_metrics": test_metrics,
        "provider_calls_made": False,
        "openai_api_calls_made": False,
        "live_tts_calls_made": False,
        "provider_side_effects_made": False,
        "runtime_behavior_changed": False,
        "response_text_changed": False,
        "raw_private_transcript_included": False,
        "raw_private_transcript_copied_to_public_evidence": False,
        "case_text_stored_in_evidence": False,
        "eval_hardware_summary": hardware_summary(),
        "dependency_status": dependency_status(),
    }
    write_json(RESULT_PATH, result)
    write_report(result)
    print(
        json.dumps(
            {
                "status": result["status"],
                "quality_gate_passed": quality_gate_passed,
                "adapter_live_ready": False,
                "validation": validation_metrics,
                "test": test_metrics,
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0 if result["status"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
