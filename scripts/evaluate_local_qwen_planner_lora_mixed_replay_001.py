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
    adapter_files_committed,
    dependency_status,
    read_jsonl,
    rel,
    safe_project_path,
    target_json_text,
)
from scripts.train_local_qwen_planner_lora_tiny_overfit_001 import render_eval_chat  # noqa: E402


EXPERIMENT_ID = "LOCAL-QWEN-LORA-MIXED-REPLAY-EVAL-001"
DATASET_EXPERIMENT_ID = "LOCAL-QWEN-MIXED-REPLAY-TRAINING-DATASET-001"
TRAINING_EXPERIMENT_ID = "LOCAL-QWEN-LORA-MIXED-REPLAY-TRAINING-001"
CONFIG_PATH = ROOT / "runtime" / "llm_brain" / "training" / "qwen_mixed_replay_lora_config.json"
DATASET_DIR = ROOT / "research" / "experiments" / "generated" / DATASET_EXPERIMENT_ID
TRAINING_RESULT_PATH = ROOT / "research" / "experiments" / "generated" / TRAINING_EXPERIMENT_ID / "result.json"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / EXPERIMENT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"
PRIOR_PATHS = {
    "base_qwen_prior": ROOT / "research" / "experiments" / "generated" / "LOCAL-QWEN-GOLDSET-EVAL-001" / "result.json",
    "tiny_adapter_prior": ROOT / "research" / "experiments" / "generated" / "LOCAL-QWEN-LORA-TINY-OVERFIT-EVAL-001" / "result.json",
    "curriculum_adapter_prior": ROOT / "research" / "experiments" / "generated" / "LOCAL-QWEN-LORA-CURRICULUM-EVAL-001" / "result.json",
}
SPLIT_FILES = {
    "train_sample": DATASET_DIR / "mixed_train.jsonl",
    "validation": DATASET_DIR / "validation.jsonl",
    "test": DATASET_DIR / "test.jsonl",
    "ood_test": DATASET_DIR / "ood_test.jsonl",
}
SEMANTIC_FIELDS = ("act", "sub", "obj", "rel", "neg", "buyer", "intent", "update", "block", "action", "strategy")
RESPONSE_PLAN_FIELDS = ("action", "strategy", "facts", "preserve", "avoid", "say")


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


def generation_config(config: dict[str, Any]) -> LocalConversationBrainConfig:
    return LocalConversationBrainConfig(
        provider="local_transformers",
        model_id=PRIMARY_MODEL_ID,
        model_path=str(config["base_model_path"]),
        cache_dir=str(config["cache_dir"]),
        device="cuda",
        quantization_mode="4bit",
        max_input_tokens=int(config["max_seq_length"]),
        max_output_tokens=COMPACT_PLANNER_MAX_OUTPUT_TOKENS,
        timeout_ms=60000,
        planner_schema_mode=COMPACT_PLANNER_SCHEMA_MODE,
        structured_output_required=True,
        enabled=False,
    )


def load_mixed_model(config: dict[str, Any], adapter_path: str) -> tuple[Any, Any, float]:
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
    model = PeftModel.from_pretrained(base_model, str(safe_project_path(adapter_path)), local_files_only=True)
    model.eval()
    return model, tokenizer, round((time.perf_counter() - started) * 1000, 3)


def unload_model(model: Any, tokenizer: Any) -> None:
    del model
    del tokenizer
    try:
        import torch  # type: ignore

        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except Exception:
        pass


def target_compact(row: dict[str, Any]) -> dict[str, Any]:
    target = row.get("target_compact_json")
    return target if isinstance(target, dict) else {}


def count_drift(kind: str, row: dict[str, Any], output: dict[str, Any] | None, expanded: dict[str, Any] | None) -> bool:
    buyer_text = str(row.get("sanitized_buyer_text") or "").casefold()
    say = str((output or {}).get("say") or "").casefold()
    target = target_compact(row)
    if kind == "and_or":
        return target.get("rel") in {"and", "or"} and output is not None and output.get("rel") != target.get("rel")
    if kind == "voice_writing":
        return ("voice" in buyer_text or "voice" in str(target.get("obj") or "").casefold()) and "writing" in say and "writing" not in buyer_text
    if kind == "not_team_team":
        not_team = any(phrase in buyer_text for phrase in ("not a team", "by myself", "just me", "only me", "no team"))
        return not_team and ("team" in say and not any(phrase in say for phrase in ("not a team", "by myself", "just me", "only me", "no team")))
    if kind == "fake_side_effect":
        return any(phrase in say for phrase in ("i signed", "i emailed", "i booked", "i created", "i changed your", "i upgraded"))
    if kind == "internal_policy":
        return any(phrase in say for phrase in ("policy", "schema", "verifier", "compact json", "internal"))
    if kind == "unsupported_fact":
        facts = (output or {}).get("facts") if isinstance(output, dict) else []
        return bool((expanded or {}).get("needs_fact_check")) or ("$" in say and not facts)
    return False


def compact_contract_valid(output: dict[str, Any] | None, diagnostics: Any) -> tuple[bool, list[str], list[dict[str, Any]]]:
    if not isinstance(output, dict):
        return False, ["compact output missing"], []
    errors: list[str] = []
    errors.extend(validate_compact_conversation_brain_output(output))
    errors.extend(getattr(diagnostics, "compact_schema_errors", []) or [])
    errors.extend(getattr(diagnostics, "compact_adapter_errors", []) or [])
    errors.extend(validate_compact_value_contract(output))
    quality_issues = compact_label_quality_issues(output)
    if quality_issues:
        errors.extend(f"{item.get('field')}:{item.get('issue')}:{item.get('value')}" for item in quality_issues)
    return not errors, errors, quality_issues


def fields_match(output: dict[str, Any] | None, target: dict[str, Any], fields: tuple[str, ...]) -> bool:
    return isinstance(output, dict) and all(output.get(field) == target.get(field) for field in fields)


def evaluate_case(model: Any, tokenizer: Any, config: LocalConversationBrainConfig, split: str, row: dict[str, Any]) -> dict[str, Any]:
    prompt = render_eval_chat(tokenizer, row)
    target = target_compact(row)
    raw_output, latency = generate_text(model, tokenizer, prompt, config)
    expanded, diagnostics = parse_and_repair_planner_output(raw_output, schema_mode=COMPACT_PLANNER_SCHEMA_MODE)
    compact_output = diagnostics.compact_planner_output
    contract_ok, contract_errors, quality_issues = compact_contract_valid(compact_output, diagnostics)
    verifier_errors = verify_conversation_brain_output(expanded, row) if isinstance(expanded, dict) else ["planner_output_missing"]
    strict_semantic = fields_match(compact_output, target, SEMANTIC_FIELDS)
    strict_response = fields_match(compact_output, target, RESPONSE_PLAN_FIELDS)
    exact_match = isinstance(compact_output, dict) and compact_output == target
    deprecated_count = sum(1 for issue in quality_issues if issue.get("issue") == "deprecated_label")
    case_id_label_leak_count = sum(1 for issue in quality_issues if issue.get("issue") == "case_id_label_leak")
    generic_count = sum(
        1
        for issue in quality_issues
        if issue.get("issue") in {"generic_action", "generic_sub_intent", "generic_act"}
    )
    drifts = {
        "and_or_drift": count_drift("and_or", row, compact_output, expanded),
        "voice_writing_drift": count_drift("voice_writing", row, compact_output, expanded),
        "not_team_team_drift": count_drift("not_team_team", row, compact_output, expanded),
        "fake_side_effect": count_drift("fake_side_effect", row, compact_output, expanded),
        "internal_policy_language": count_drift("internal_policy", row, compact_output, expanded),
        "unsupported_fact": count_drift("unsupported_fact", row, compact_output, expanded),
    }
    safety_pass = not verifier_errors and not any(drifts.values())
    equivalence_match = (
        strict_semantic
        and fields_match(compact_output, target, ("facts", "preserve", "avoid", "flags"))
        and safety_pass
        and deprecated_count == 0
        and case_id_label_leak_count == 0
        and generic_count == 0
    )
    failure_classes: list[str] = []
    if not isinstance(expanded, dict):
        failure_classes.append("schema")
    if verifier_errors:
        failure_classes.append("verifier")
    if not contract_ok:
        failure_classes.append("compact_contract")
    if not strict_semantic:
        failure_classes.append("strict_gold_semantic")
    if not strict_response:
        failure_classes.append("strict_gold_response_plan")
    if not safety_pass:
        failure_classes.append("safety")
    if not isinstance(compact_output, dict):
        failure_classes.append("malformed_output")
    for name, present in drifts.items():
        if present:
            failure_classes.append(name)
    return {
        "case_id": row.get("case_id"),
        "source_case_id": row.get("mixed_replay_source_case_id") or row.get("original_case_id"),
        "split": split,
        "source_type": row.get("source_type"),
        "semantic_group": row.get("semantic_group"),
        "target_card_id": row.get("target_card_id"),
        "schema_valid": isinstance(expanded, dict),
        "verifier_pass": not verifier_errors,
        "compact_contract_valid": contract_ok,
        "strict_gold_semantic_match": strict_semantic,
        "strict_gold_response_plan_match": strict_response,
        "equivalence_match": equivalence_match,
        "exact_match": exact_match,
        "safety_pass": safety_pass,
        "deprecated_label_count": deprecated_count,
        "case_id_label_leak_count": case_id_label_leak_count,
        "generic_label_count": generic_count,
        "malformed_output": not isinstance(compact_output, dict),
        "and_or_drift": drifts["and_or_drift"],
        "voice_writing_drift": drifts["voice_writing_drift"],
        "not_team_team_drift": drifts["not_team_team_drift"],
        "fake_side_effect": drifts["fake_side_effect"],
        "internal_policy_language": drifts["internal_policy_language"],
        "unsupported_fact": drifts["unsupported_fact"],
        "failure_classes": sorted(set(failure_classes)),
        "compact_contract_errors": contract_errors,
        "compact_label_quality_issues": quality_issues,
        "verifier_errors": verifier_errors,
        "parse_errors": diagnostics.parse_errors,
        "latency_metrics": latency,
        "compact_planner_output": compact_output,
        "target_present_in_generation_prompt": target_json_text(row) in prompt,
    }


def aggregate_latency(items: list[dict[str, Any]], model_load_time_ms: float | None) -> dict[str, Any]:
    latencies = [
        float((item.get("latency_metrics") or {}).get("total_generation_latency_ms"))
        for item in items
        if (item.get("latency_metrics") or {}).get("total_generation_latency_ms") is not None
    ]
    first = [
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
        "average_first_output_latency_ms": round(sum(first) / len(first), 3) if first else None,
        "peak_gpu_memory_bytes": max(peaks) if peaks else None,
    }


def summarize_items(items: list[dict[str, Any]], model_load_time_ms: float | None) -> dict[str, Any]:
    failure_counts = Counter(kind for item in items for kind in item.get("failure_classes") or [])
    return {
        "case_count": len(items),
        "schema_valid_count": sum(1 for item in items if item.get("schema_valid")),
        "verifier_pass_count": sum(1 for item in items if item.get("verifier_pass")),
        "compact_contract_valid_count": sum(1 for item in items if item.get("compact_contract_valid")),
        "strict_gold_semantic_match_count": sum(1 for item in items if item.get("strict_gold_semantic_match")),
        "strict_gold_response_plan_match_count": sum(1 for item in items if item.get("strict_gold_response_plan_match")),
        "equivalence_match_count": sum(1 for item in items if item.get("equivalence_match")),
        "exact_match_count": sum(1 for item in items if item.get("exact_match")),
        "safety_pass_count": sum(1 for item in items if item.get("safety_pass")),
        "deprecated_label_count": sum(int(item.get("deprecated_label_count") or 0) for item in items),
        "case_id_label_leak_count": sum(int(item.get("case_id_label_leak_count") or 0) for item in items),
        "generic_label_count": sum(int(item.get("generic_label_count") or 0) for item in items),
        "malformed_output_count": sum(1 for item in items if item.get("malformed_output")),
        "and_or_drift_count": sum(1 for item in items if item.get("and_or_drift")),
        "voice_writing_drift_count": sum(1 for item in items if item.get("voice_writing_drift")),
        "not_team_team_drift_count": sum(1 for item in items if item.get("not_team_team_drift")),
        "fake_side_effect_count": sum(1 for item in items if item.get("fake_side_effect")),
        "internal_policy_language_count": sum(1 for item in items if item.get("internal_policy_language")),
        "unsupported_fact_count": sum(1 for item in items if item.get("unsupported_fact")),
        "failure_class_counts": dict(sorted(failure_counts.items())),
        "target_present_in_generation_prompt_count": sum(1 for item in items if item.get("target_present_in_generation_prompt")),
        "latency_metrics": aggregate_latency(items, model_load_time_ms),
    }


def split_gate(metrics: dict[str, Any]) -> tuple[bool, list[str]]:
    count = int(metrics.get("case_count") or 0)
    failures: list[str] = []
    if count <= 0:
        failures.append("empty_split")
        return False, failures
    thresholds = {
        "schema_valid_count": 1.0,
        "compact_contract_valid_count": 1.0,
        "verifier_pass_count": 0.98,
        "strict_gold_semantic_match_count": 0.85,
        "equivalence_match_count": 0.90,
    }
    for key, ratio in thresholds.items():
        value = int(metrics.get(key) or 0)
        if value / count < ratio:
            failures.append(f"{key}_below_{ratio}")
    zero_keys = (
        "and_or_drift_count",
        "voice_writing_drift_count",
        "not_team_team_drift_count",
        "fake_side_effect_count",
        "internal_policy_language_count",
    )
    for key in zero_keys:
        if int(metrics.get(key) or 0) != 0:
            failures.append(f"{key}_nonzero")
    if int(metrics.get("safety_pass_count") or 0) != count:
        failures.append("safety_pass_count_not_100_percent")
    return not failures, failures


def prior_comparison() -> dict[str, Any]:
    comparison: dict[str, Any] = {}
    for name, path in PRIOR_PATHS.items():
        payload = read_json(path)
        comparison[name] = {
            "source": rel(path) if path.is_file() else None,
            "status": "available" if payload else "missing",
            "quality_gate_passed": payload.get("quality_gate_passed"),
            "adapter_live_ready": payload.get("adapter_live_ready"),
            "validation_metrics": payload.get("validation_metrics"),
            "test_metrics": payload.get("test_metrics"),
        }
    comparison["deterministic_target_baseline"] = {
        "status": "available",
        "meaning": "Gold compact targets are the baseline and expected to score 100% by construction after approval gate.",
    }
    return comparison


def evaluate_adapter(adapter_path: str, split_limits: dict[str, int | None], config: dict[str, Any]) -> dict[str, Any]:
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
    model = None
    tokenizer = None
    try:
        model, tokenizer, load_ms = load_mixed_model(config, adapter_path)
        result["adapter_loaded"] = True
        gen_config = generation_config(config)
        for split, path in SPLIT_FILES.items():
            rows = read_jsonl(path)
            limit = split_limits.get(split)
            if limit is not None:
                rows = rows[:limit]
            cases: list[dict[str, Any]] = []
            for index, row in enumerate(rows, start=1):
                item = evaluate_case(model, tokenizer, gen_config, split, row)
                cases.append(item)
                print(
                    json.dumps(
                        {
                            "event": "mixed_replay_eval_case",
                            "split": split,
                            "index": index,
                            "total": len(rows),
                            "case_id": row.get("case_id"),
                            "schema": item["schema_valid"],
                            "contract": item["compact_contract_valid"],
                            "strict": item["strict_gold_semantic_match"],
                            "equivalence": item["equivalence_match"],
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
                "cases": cases,
                "metrics": summarize_items(cases, load_ms if split == "train_sample" else None),
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


def write_report(result: dict[str, Any]) -> None:
    adapter = result.get("mixed_replay_adapter") if isinstance(result.get("mixed_replay_adapter"), dict) else {}
    split_summary = {
        split: payload.get("metrics")
        for split, payload in (adapter.get("splits") or {}).items()
        if isinstance(payload, dict)
    }
    lines = [
        f"# {EXPERIMENT_ID}",
        "",
        f"- status: {result.get('status')}",
        f"- adapter_path: `{result.get('adapter_path')}`",
        f"- quality_gate_passed: {str(result.get('quality_gate_passed')).lower()}",
        f"- adapter_live_ready: {str(result.get('adapter_live_ready')).lower()}",
        f"- live_wiring_allowed: {str(result.get('live_wiring_allowed')).lower()}",
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
        "## Quality Gate Failures",
        "",
        json.dumps(result.get("quality_gate_failures") or {}, indent=2, ensure_ascii=False),
        "",
        "## Prior Comparison",
        "",
        json.dumps(result.get("base_tiny_curriculum_mixed_comparison") or {}, indent=2, ensure_ascii=False),
    ]
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate local Qwen mixed-replay LoRA adapter.")
    parser.add_argument("--adapter-path", default=None)
    parser.add_argument("--train-sample-limit", type=int, default=40)
    parser.add_argument("--validation-limit", type=int, default=None)
    parser.add_argument("--test-limit", type=int, default=None)
    parser.add_argument("--ood-limit", type=int, default=None)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    config = read_json(CONFIG_PATH)
    adapter_path = args.adapter_path or str(config.get("output_adapter_dir") or "")
    split_limits = {
        "train_sample": args.train_sample_limit,
        "validation": args.validation_limit,
        "test": args.test_limit,
        "ood_test": args.ood_limit,
    }
    training_result = read_json(TRAINING_RESULT_PATH)
    adapter_eval = evaluate_adapter(adapter_path, split_limits, config)
    splits = adapter_eval.get("splits") if isinstance(adapter_eval.get("splits"), dict) else {}
    validation_metrics = (splits.get("validation") or {}).get("metrics") if isinstance(splits.get("validation"), dict) else {}
    test_metrics = (splits.get("test") or {}).get("metrics") if isinstance(splits.get("test"), dict) else {}
    validation_gate, validation_failures = split_gate(validation_metrics)
    test_gate, test_failures = split_gate(test_metrics)
    quality_gate_passed = adapter_eval.get("status") == "completed" and validation_gate and test_gate
    result = {
        "experiment_id": EXPERIMENT_ID,
        "generated_at": utc_now(),
        "status": "completed" if adapter_eval.get("status") == "completed" else adapter_eval.get("status"),
        "dataset_experiment_id": DATASET_EXPERIMENT_ID,
        "training_experiment_id": TRAINING_EXPERIMENT_ID,
        "training_status": training_result.get("status"),
        "training_completed": training_result.get("training_completed"),
        "training_train_loss": training_result.get("train_loss"),
        "training_eval_loss": training_result.get("eval_loss"),
        "adapter_path": adapter_path,
        "adapter_files_committed": adapter_files_committed(),
        "mixed_replay_adapter": adapter_eval,
        "base_tiny_curriculum_mixed_comparison": prior_comparison(),
        "quality_gate_passed": quality_gate_passed,
        "quality_gate_failures": {
            "validation": validation_failures,
            "test": test_failures,
        },
        "adapter_live_ready": bool(quality_gate_passed),
        "adapter_live_ready_reason": "Shadow-mode quality thresholds passed." if quality_gate_passed else "Shadow-mode quality thresholds did not pass.",
        "live_wiring_allowed": False,
        "live_replacement_evaluated": False,
        "validation_metrics": validation_metrics,
        "test_metrics": test_metrics,
        "ood_metrics": (splits.get("ood_test") or {}).get("metrics") if isinstance(splits.get("ood_test"), dict) else {},
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
                "adapter_live_ready": result["adapter_live_ready"],
                "live_wiring_allowed": False,
                "validation": validation_metrics,
                "test": test_metrics,
                "ood": result["ood_metrics"],
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0 if result["status"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
