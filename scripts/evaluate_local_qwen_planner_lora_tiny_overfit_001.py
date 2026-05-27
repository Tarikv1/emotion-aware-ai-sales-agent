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
    COMPACT_VALUE_CONTRACT_VERSION,
    allowed_values_for,
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
from scripts.evaluate_local_qwen_planner_lora_001 import (  # noqa: E402
    evaluate_payload,
    summarize_case_results,
)
from scripts.train_local_qwen_planner_lora_001 import (  # noqa: E402
    adapter_files_committed,
    dependency_status,
    read_jsonl,
    rel,
    safe_project_path,
    target_json_text,
)
from scripts.train_local_qwen_planner_lora_tiny_overfit_001 import (  # noqa: E402
    DATASET_EXPERIMENT_ID,
    EXPERIMENT_ID,
    RESULT_PATH,
    TINY_ADAPTER_PATH,
    TINY_CONFIG,
    TRAIN_PATH,
    render_eval_chat,
    write_report as write_training_report,
)


REPORT_PATH = ROOT / "research" / "experiments" / "generated" / EXPERIMENT_ID / "report.md"
LORA_002_ADAPTER_PATH = "local_artifacts/adapters/qwen2.5-sales-brain-lora-002"
MODEL_LABELS = ("base_qwen", "lora_002", "tiny_adapter")


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
    return {
        "model_load_time_ms": model_load_time_ms,
        "total_generation_latency_ms": round(sum(latencies), 3) if latencies else None,
        "average_generation_latency_ms": round(sum(latencies) / len(latencies), 3) if latencies else None,
        "p50_generation_latency_ms": percentile(latencies, 0.50),
        "p90_generation_latency_ms": percentile(latencies, 0.90),
        "average_first_output_latency_ms": round(sum(first_latencies) / len(first_latencies), 3)
        if first_latencies
        else None,
    }


def load_model(config: dict[str, Any], adapter_path: str | None) -> tuple[Any, Any, float, bool]:
    import torch  # type: ignore
    from peft import PeftModel  # type: ignore
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig  # type: ignore

    model_path = safe_project_path(str(config["base_model_path"]))
    cache_dir = safe_project_path(str(config["cache_dir"]))
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
    adapter_loaded = False
    model = base_model
    if adapter_path:
        resolved_adapter = safe_project_path(adapter_path)
        model = PeftModel.from_pretrained(base_model, str(resolved_adapter), local_files_only=True)
        adapter_loaded = True
    model.eval()
    return model, tokenizer, round((time.perf_counter() - started) * 1000, 3), adapter_loaded


def unload_model(model: Any, tokenizer: Any) -> None:
    del model
    del tokenizer
    try:
        import torch  # type: ignore

        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except Exception:
        pass


def generation_config() -> LocalConversationBrainConfig:
    return LocalConversationBrainConfig(
        provider="local_transformers",
        model_id=PRIMARY_MODEL_ID,
        model_path=str(TINY_CONFIG["base_model_path"]),
        cache_dir=str(TINY_CONFIG["cache_dir"]),
        device="cuda",
        quantization_mode="4bit",
        max_input_tokens=int(TINY_CONFIG["max_seq_length"]),
        max_output_tokens=COMPACT_PLANNER_MAX_OUTPUT_TOKENS,
        timeout_ms=60000,
        planner_schema_mode=COMPACT_PLANNER_SCHEMA_MODE,
        structured_output_required=True,
        enabled=False,
    )


def render_prompt(tokenizer: Any, row: dict[str, Any]) -> str:
    return render_eval_chat(tokenizer, row)


def generation_prompt_excludes_target(tokenizer: Any, row: dict[str, Any]) -> bool:
    prompt = render_prompt(tokenizer, row)
    return target_json_text(row) not in prompt


def evaluate_case(
    *,
    model_label: str,
    row: dict[str, Any],
    model: Any,
    tokenizer: Any,
    config: LocalConversationBrainConfig,
) -> dict[str, Any]:
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
    compact_contract_valid = (
        isinstance(compact_output, dict)
        and not compact_schema_errors
        and not compact_adapter_errors
        and not compact_contract_errors
        and not compact_quality_issues
    )
    evaluation = evaluate_payload(expanded, row)
    exact_target_match = isinstance(compact_output, dict) and compact_output == target_compact
    failure_classes: list[str] = []
    if evaluation["schema_errors"]:
        failure_classes.append("schema")
    if evaluation["verifier_errors"]:
        failure_classes.append("verifier")
    if not compact_contract_valid:
        failure_classes.append("compact_contract")
    if evaluation["semantic_mismatches"]:
        failure_classes.append("gold_semantic")
    malformed_compact_object = not isinstance(compact_output, dict) or bool(compact_schema_errors or compact_adapter_errors)
    return {
        "case_id": row.get("case_id"),
        "category": row.get("category"),
        "model_label": model_label,
        "status": "pass" if evaluation["semantic_match"] and compact_contract_valid else "fail",
        "schema_valid": isinstance(expanded, dict) and not evaluation["schema_errors"],
        "verifier_pass": evaluation["verifier_pass"],
        "semantic_match": evaluation["semantic_match"],
        "strict_gold_semantic_match": evaluation["gold_section_semantic_match"],
        "gold_response_plan_match": evaluation["gold_response_plan_match"],
        "compact_contract_valid": compact_contract_valid,
        "exact_target_match": exact_target_match,
        "malformed_compact_object": malformed_compact_object,
        "deprecated_or_case_id_or_generic_label_count": len(
            [
                issue
                for issue in compact_quality_issues
                if issue.get("issue") in {"deprecated_label", "case_id_label_leak", "generic_action", "generic_sub_intent", "generic_act"}
            ]
        ),
        "compact_planner_output": compact_output,
        "compact_schema_errors": compact_schema_errors,
        "compact_adapter_errors": compact_adapter_errors,
        "compact_contract_errors": compact_contract_errors,
        "compact_label_quality_issues": compact_quality_issues,
        "parse_errors": diagnostics.parse_errors,
        "verifier_errors": evaluation["verifier_errors"],
        "semantic_mismatches": evaluation["semantic_mismatches"],
        "exact_mismatches": evaluation["exact_mismatches"],
        "failure_classes": failure_classes,
        "latency_metrics": latency,
        "raw_output_excerpt": raw_output[:400],
    }


def summarize_tiny_items(items: list[dict[str, Any]]) -> dict[str, Any]:
    base = summarize_case_results(
        [
            {
                **item,
                "exact_match": item.get("exact_target_match"),
                "gold_section_semantic_match": item.get("strict_gold_semantic_match"),
            }
            for item in items
        ]
    )
    base["exact_target_match_count"] = sum(1 for item in items if item.get("exact_target_match"))
    base["malformed_compact_object_count"] = sum(1 for item in items if item.get("malformed_compact_object"))
    base["deprecated_case_id_generic_label_count"] = sum(
        int(item.get("deprecated_or_case_id_or_generic_label_count") or 0) for item in items
    )
    return base


def evaluate_model_label(
    model_label: str,
    adapter_path: str | None,
    rows: list[dict[str, Any]],
    *,
    skip_missing_adapter: bool = True,
) -> dict[str, Any]:
    adapter_exists = True
    if adapter_path is not None:
        adapter_exists = (safe_project_path(adapter_path) / "adapter_config.json").is_file()
    result: dict[str, Any] = {
        "model_label": model_label,
        "adapter_path": adapter_path,
        "adapter_exists": adapter_exists,
        "adapter_loaded": False,
        "model_loaded": False,
        "status": "not_run",
        "case_count": len(rows),
        "cases": [],
        "metrics": {},
        "latency_metrics": {},
        "exact_blocker": None,
    }
    if adapter_path is not None and not adapter_exists and skip_missing_adapter:
        result["status"] = "adapter_missing"
        result["metrics"] = {
            "case_count": len(rows),
            "schema_valid_count": 0,
            "verifier_pass_count": 0,
            "compact_contract_valid_count": 0,
            "strict_gold_semantic_match_count": 0,
            "exact_target_match_count": 0,
            "malformed_compact_object_count": 0,
        }
        return result
    model = None
    tokenizer = None
    try:
        model, tokenizer, model_load_time_ms, adapter_loaded = load_model(TINY_CONFIG, adapter_path)
        result["model_loaded"] = True
        result["adapter_loaded"] = adapter_loaded
        config = generation_config()
        case_results: list[dict[str, Any]] = []
        prompt_excludes_target = []
        for index, row in enumerate(rows, start=1):
            prompt_excludes_target.append(generation_prompt_excludes_target(tokenizer, row))
            item = evaluate_case(model_label=model_label, row=row, model=model, tokenizer=tokenizer, config=config)
            case_results.append(item)
            print(
                json.dumps(
                    {
                        "event": "tiny_overfit_eval_case",
                        "model": model_label,
                        "index": index,
                        "total": len(rows),
                        "case_id": row.get("case_id"),
                        "schema_valid": item["schema_valid"],
                        "contract": item["compact_contract_valid"],
                        "strict": item["strict_gold_semantic_match"],
                        "exact": item["exact_target_match"],
                        "latency_ms": item["latency_metrics"].get("total_generation_latency_ms"),
                    },
                    ensure_ascii=False,
                ),
                flush=True,
            )
        metrics = summarize_tiny_items(case_results)
        result.update(
            {
                "status": "completed",
                "cases": case_results,
                "metrics": metrics,
                "latency_metrics": aggregate_latency(case_results, model_load_time_ms),
                "generation_prompt_excludes_target": all(prompt_excludes_target),
            }
        )
        return result
    except Exception as exc:
        result["status"] = "blocked"
        result["exact_blocker"] = f"{type(exc).__name__}: {exc}"
        result["traceback_excerpt"] = traceback.format_exc(limit=8)[-4000:]
        return result
    finally:
        if model is not None and tokenizer is not None:
            unload_model(model, tokenizer)


def compact_value_learning_summary(items: list[dict[str, Any]]) -> dict[str, Any]:
    fields = ("act", "sub", "rel", "neg", "buyer", "intent", "action", "strategy")
    learned_counts = {field: 0 for field in fields}
    valid_counts = {field: 0 for field in fields}
    for item in items:
        output = item.get("compact_planner_output") if isinstance(item.get("compact_planner_output"), dict) else {}
        target = {}
        case_id = item.get("case_id")
        row = next((candidate for candidate in read_jsonl(TRAIN_PATH) if candidate.get("case_id") == case_id), None)
        if isinstance(row, dict):
            target = row.get("target_compact_json") if isinstance(row.get("target_compact_json"), dict) else {}
        for field in fields:
            if output.get(field) in allowed_values_for(field):
                valid_counts[field] += 1
            if output.get(field) == target.get(field):
                learned_counts[field] += 1
    return {"allowed_label_counts": valid_counts, "target_label_match_counts": learned_counts}


def tiny_passed(metrics: dict[str, Any]) -> bool:
    count = int(metrics.get("case_count") or 0)
    return (
        count > 0
        and int(metrics.get("schema_valid_count") or 0) == count
        and int(metrics.get("verifier_pass_count") or 0) == count
        and int(metrics.get("compact_contract_valid_count") or 0) == count
        and int(metrics.get("strict_gold_semantic_match_count") or 0) == count
        and int(metrics.get("deprecated_case_id_generic_label_count") or 0) == 0
        and int(metrics.get("malformed_compact_object_count") or 0) == 0
    )


def classify_tiny_blocker(tiny_result: dict[str, Any], training_result: dict[str, Any], audit_result: dict[str, Any]) -> str | None:
    if tiny_result.get("status") != "completed":
        if tiny_result.get("adapter_loaded") is not True:
            return "adapter not loaded"
        return "Python/Windows training issue"
    if training_result.get("training_completed") is not True:
        return str(training_result.get("blocker_classification") or "Python/Windows training issue")
    audit_checks = audit_result.get("checks") if isinstance(audit_result.get("checks"), dict) else {}
    if audit_checks and audit_checks.get("target_compact_json_is_assistant_message") is not True:
        return "target not in assistant message"
    if audit_checks and audit_checks.get("labels_train_only_assistant_tokens") is not True:
        return "labels not masked correctly"
    if tiny_result.get("generation_prompt_excludes_target") is not True:
        return "prompt/eval mismatch"
    metrics = tiny_result.get("metrics") if isinstance(tiny_result.get("metrics"), dict) else {}
    if int(metrics.get("malformed_compact_object_count") or 0) > 0:
        return "generation decoding issue"
    if int(metrics.get("compact_contract_valid_count") or 0) < int(metrics.get("case_count") or 0):
        return "not enough steps"
    if int(metrics.get("schema_valid_count") or 0) < int(metrics.get("case_count") or 0):
        return "schema too complex"
    if int(metrics.get("strict_gold_semantic_match_count") or 0) < int(metrics.get("case_count") or 0):
        return "not enough steps"
    return None


def comparison_summary(model_results: dict[str, dict[str, Any]]) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    for label, result in model_results.items():
        metrics = result.get("metrics") if isinstance(result.get("metrics"), dict) else {}
        summary[label] = {
            "status": result.get("status"),
            "adapter_loaded": result.get("adapter_loaded"),
            "case_count": metrics.get("case_count"),
            "schema_valid_count": metrics.get("schema_valid_count"),
            "verifier_pass_count": metrics.get("verifier_pass_count"),
            "compact_contract_valid_count": metrics.get("compact_contract_valid_count"),
            "strict_gold_semantic_match_count": metrics.get("strict_gold_semantic_match_count"),
            "exact_target_match_count": metrics.get("exact_target_match_count"),
            "malformed_compact_object_count": metrics.get("malformed_compact_object_count"),
            "deprecated_case_id_generic_label_count": metrics.get("deprecated_case_id_generic_label_count"),
            "latency_metrics": result.get("latency_metrics"),
        }
    return summary


def write_combined_report(result: dict[str, Any]) -> None:
    write_training_report(result)
    evaluation = result.get("evaluation") if isinstance(result.get("evaluation"), dict) else {}
    lines = REPORT_PATH.read_text(encoding="utf-8").rstrip().splitlines() if REPORT_PATH.is_file() else []
    lines.extend(
        [
            "",
            "## Tiny Overfit Evaluation",
            "",
            f"- status: {evaluation.get('status')}",
            f"- tiny_overfit_passed: {str(evaluation.get('tiny_overfit_passed')).lower()}",
            f"- blocker_classification: {evaluation.get('blocker_classification')}",
            f"- exact_target_match_count: {evaluation.get('tiny_exact_target_match_count')}",
            f"- compact_contract_pass_count: {evaluation.get('tiny_compact_contract_pass_count')}",
            f"- strict_semantic_pass_count: {evaluation.get('tiny_strict_semantic_pass_count')}",
            "",
            "## Base Vs Adapter",
            "",
            json.dumps(evaluation.get("comparison") or {}, indent=2, ensure_ascii=False),
        ]
    )
    REPORT_PATH.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate tiny Qwen LoRA overfit adapter on exact train cases.")
    parser.add_argument("--skip-lora-002", action="store_true", help="Skip previous lora-002 comparison.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    rows = read_jsonl(TRAIN_PATH)
    deps = dependency_status()
    result = read_json(RESULT_PATH)
    if not result:
        result = {
            "experiment_id": EXPERIMENT_ID,
            "generated_at": utc_now(),
            "status": "training_result_missing",
            "adapter_path": TINY_ADAPTER_PATH,
        }
    model_results: dict[str, dict[str, Any]] = {}
    model_results["base_qwen"] = evaluate_model_label("base_qwen", None, rows, skip_missing_adapter=False)
    if args.skip_lora_002:
        model_results["lora_002"] = {"model_label": "lora_002", "status": "skipped", "metrics": {"case_count": len(rows)}}
    else:
        model_results["lora_002"] = evaluate_model_label("lora_002", LORA_002_ADAPTER_PATH, rows)
    model_results["tiny_adapter"] = evaluate_model_label("tiny_adapter", TINY_ADAPTER_PATH, rows)
    tiny_result = model_results["tiny_adapter"]
    tiny_metrics = tiny_result.get("metrics") if isinstance(tiny_result.get("metrics"), dict) else {}
    audit_result = read_json(
        ROOT
        / "research"
        / "experiments"
        / "generated"
        / "LOCAL-QWEN-LORA-TRAINING-PIPELINE-AUDIT-001"
        / "result.json"
    )
    passed = tiny_passed(tiny_metrics)
    blocker = None if passed else classify_tiny_blocker(tiny_result, result, audit_result)
    tiny_cases = tiny_result.get("cases") if isinstance(tiny_result.get("cases"), list) else []
    result.update(
        {
            "evaluation_completed_at": utc_now(),
            "dependency_status_at_eval": deps,
            "eval_hardware_summary": hardware_summary(),
            "local_model_calls_made": True,
            "provider_calls_made": False,
            "openai_api_calls_made": False,
            "live_tts_calls_made": False,
            "provider_side_effects_made": False,
            "runtime_behavior_changed": False,
            "response_text_changed": False,
            "raw_private_transcript_copied_to_public_evidence": False,
            "case_text_stored_in_evidence": False,
            "adapter_files_committed": adapter_files_committed(),
            "evaluation": {
                "experiment_id": EXPERIMENT_ID,
                "dataset_experiment_id": DATASET_EXPERIMENT_ID,
                "status": "pass" if passed else "fail",
                "tiny_overfit_passed": passed,
                "blocker_classification": blocker,
                "pass_condition": {
                    "schema_valid_all_cases": passed and tiny_metrics.get("schema_valid_count") == tiny_metrics.get("case_count"),
                    "compact_contract_valid_all_cases": passed
                    and tiny_metrics.get("compact_contract_valid_count") == tiny_metrics.get("case_count"),
                    "verifier_pass_all_cases": passed
                    and tiny_metrics.get("verifier_pass_count") == tiny_metrics.get("case_count"),
                    "strict_gold_semantic_all_cases": passed
                    and tiny_metrics.get("strict_gold_semantic_match_count") == tiny_metrics.get("case_count"),
                    "deprecated_case_id_generic_labels_zero": tiny_metrics.get("deprecated_case_id_generic_label_count") == 0,
                    "malformed_compact_object_count_zero": tiny_metrics.get("malformed_compact_object_count") == 0,
                },
                "comparison": comparison_summary(model_results),
                "models": model_results,
                "tiny_exact_target_match_count": tiny_metrics.get("exact_target_match_count"),
                "tiny_compact_contract_pass_count": tiny_metrics.get("compact_contract_valid_count"),
                "tiny_strict_semantic_pass_count": tiny_metrics.get("strict_gold_semantic_match_count"),
                "tiny_allowed_label_learning": compact_value_learning_summary(tiny_cases),
                "tiny_learned_full_compact_shape": tiny_metrics.get("malformed_compact_object_count") == 0
                and tiny_metrics.get("schema_valid_count") == tiny_metrics.get("case_count"),
                "provider_side_effect_result": {
                    "provider_calls_made": False,
                    "openai_api_calls_made": False,
                    "live_tts_calls_made": False,
                    "provider_side_effects_made": False,
                },
            },
        }
    )
    write_json(RESULT_PATH, result)
    write_combined_report(result)
    print(
        json.dumps(
            {
                "status": result["evaluation"]["status"],
                "tiny_overfit_passed": passed,
                "blocker_classification": blocker,
                "comparison": result["evaluation"]["comparison"],
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
