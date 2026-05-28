#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import inspect
import json
from pathlib import Path
import sys
import time
import traceback
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.llm_brain.conversation_brain_schema import PRIMARY_MODEL_ID  # noqa: E402
from runtime.llm_brain.local_transformers_runner import hardware_summary  # noqa: E402
from scripts.train_local_qwen_planner_lora_001 import (  # noqa: E402
    PlannerDataset,
    adapter_files_committed,
    dependency_status,
    in_expected_llm_env,
    make_collator,
    read_jsonl,
    rel,
    safe_project_path,
)
from scripts.train_local_qwen_planner_lora_tiny_overfit_001 import (  # noqa: E402
    build_training_arguments,
    tokenize_rows_assistant_only,
)


EXPERIMENT_ID = "LOCAL-QWEN-LORA-MIXED-REPLAY-TRAINING-001"
DATASET_EXPERIMENT_ID = "LOCAL-QWEN-MIXED-REPLAY-TRAINING-DATASET-001"
CONFIG_PATH = ROOT / "runtime" / "llm_brain" / "training" / "qwen_mixed_replay_lora_config.json"
DATASET_DIR = ROOT / "research" / "experiments" / "generated" / DATASET_EXPERIMENT_ID
TRAIN_PATH = DATASET_DIR / "mixed_train.jsonl"
VALIDATION_PATH = DATASET_DIR / "validation.jsonl"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / EXPERIMENT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"


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


def validate_config(config: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    expected = {
        "base_model_id": PRIMARY_MODEL_ID,
        "base_model_path": "local_artifacts/models/qwen2.5-7b-instruct",
        "dataset_dir": "research/experiments/generated/LOCAL-QWEN-BALANCED-SFT-DATASET-001",
        "mixed_replay_dataset_dir": "research/experiments/generated/LOCAL-QWEN-MIXED-REPLAY-TRAINING-DATASET-001",
        "output_adapter_dir": "local_artifacts/adapters/qwen2.5-sales-brain-lora-mixed-replay-001",
        "cache_dir": "local_artifacts/cache/huggingface",
        "quantization": "4bit",
        "target": "compact planner JSON",
        "training_strategy": "mixed_replay_balanced_sampling",
        "device": "cuda",
    }
    for key, value in expected.items():
        if config.get(key) != value:
            errors.append(f"{key} must be {value}")
    for key in ("final_stage_mixing_required", "validation_test_held_out", "ood_test_separate", "start_from_base_model_only"):
        if config.get(key) is not True:
            errors.append(f"{key} must be true")
    if config.get("final_stage_only_stage3_rows_allowed") is not False:
        errors.append("final_stage_only_stage3_rows_allowed must be false")
    for key in ("base_model_path", "cache_dir", "output_adapter_dir", "mixed_replay_dataset_dir"):
        value = str(config.get(key) or "")
        try:
            path = safe_project_path(value)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        if key == "base_model_path" and not path.is_dir():
            errors.append(f"base_model_path does not exist: {value}")
        if key == "mixed_replay_dataset_dir" and not (path / "mixed_train.jsonl").is_file():
            errors.append(f"mixed replay train missing: {value}")
        if key == "output_adapter_dir" and not value.replace("\\", "/").startswith("local_artifacts/adapters/"):
            errors.append("output_adapter_dir must stay under local_artifacts/adapters")
    for key in ("max_seq_length", "per_device_train_batch_size", "gradient_accumulation_steps", "lora_r", "lora_alpha", "seed"):
        if not isinstance(config.get(key), int) or int(config[key]) <= 0:
            errors.append(f"{key} must be a positive integer")
    if int(config.get("max_seq_length") or 0) not in {1024, 1536}:
        errors.append("max_seq_length must be 1024 or 1536")
    if int(config.get("per_device_train_batch_size") or 0) != 1:
        errors.append("per_device_train_batch_size must be 1")
    if int(config.get("gradient_accumulation_steps") or 0) not in {2, 4}:
        errors.append("gradient_accumulation_steps must be 2 or 4")
    if float(config.get("learning_rate") or 0) not in {0.0001, 0.0002}:
        errors.append("learning_rate must be 0.0001 or 0.0002")
    if float(config.get("lora_dropout") or -1) != 0.05:
        errors.append("lora_dropout must be 0.05")
    return errors


def base_result(args: argparse.Namespace, config: dict[str, Any], deps: dict[str, Any]) -> dict[str, Any]:
    adapter_path = safe_project_path(str(config.get("output_adapter_dir") or "local_artifacts/adapters/missing"))
    return {
        "experiment_id": EXPERIMENT_ID,
        "generated_at": utc_now(),
        "status": "not_run",
        "phase": "mixed_replay_lora_training",
        "config_path": rel(CONFIG_PATH),
        "config": config,
        "python_executable": sys.executable,
        "expected_python_environment": ".venv-llm",
        "expected_python_environment_active": in_expected_llm_env(),
        "dependency_status": deps,
        "hardware_summary": hardware_summary(),
        "cuda_available": bool(hardware_summary().get("cuda_available")),
        "gpu_name": hardware_summary().get("gpu_name"),
        "dry_run_config_only": bool(args.dry_run_config_only),
        "skip_train_if_missing_deps": bool(args.skip_train_if_missing_deps),
        "resume_requested": str(args.resume).lower() == "true",
        "limit_train_rows": args.limit_train_rows,
        "eval_during_training": bool(args.eval_during_training),
        "training_attempted": False,
        "training_completed": False,
        "max_steps_requested": int(args.max_steps or config.get("max_steps") or 0),
        "train_steps_completed": 0,
        "train_row_count": 0,
        "validation_row_count": 0,
        "train_loss": None,
        "eval_loss": None,
        "train_runtime_seconds": None,
        "peak_gpu_memory_bytes": None,
        "model_loaded": False,
        "adapter_saved": False,
        "adapter_path": rel(adapter_path),
        "adapter_files_committed": adapter_files_committed(),
        "exact_blocker": None,
        "blocker_classification": None,
        "tokenization": {},
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
        "raw_private_transcript_included": False,
        "raw_private_transcript_copied_to_public_evidence": False,
        "case_text_stored_in_evidence": False,
        "notes": [],
    }


def write_report(result: dict[str, Any]) -> None:
    lines = [
        f"# {EXPERIMENT_ID}",
        "",
        f"- status: {result.get('status')}",
        f"- training_attempted: {str(result.get('training_attempted')).lower()}",
        f"- training_completed: {str(result.get('training_completed')).lower()}",
        f"- exact_blocker: {result.get('exact_blocker')}",
        f"- max_steps_requested: {result.get('max_steps_requested')}",
        f"- train_steps_completed: {result.get('train_steps_completed')}",
        f"- train_loss: {result.get('train_loss')}",
        f"- eval_loss: {result.get('eval_loss')}",
        f"- adapter_path: `{result.get('adapter_path')}`",
        f"- adapter_saved: {str(result.get('adapter_saved')).lower()}",
        f"- adapter_files_committed: {str(result.get('adapter_files_committed')).lower()}",
        f"- peak_gpu_memory_bytes: {result.get('peak_gpu_memory_bytes')}",
        f"- provider_calls_made: {str(result.get('provider_calls_made')).lower()}",
        f"- openai_api_calls_made: {str(result.get('openai_api_calls_made')).lower()}",
        f"- live_tts_calls_made: {str(result.get('live_tts_calls_made')).lower()}",
        f"- runtime_behavior_changed: {str(result.get('runtime_behavior_changed')).lower()}",
        f"- response_text_changed: {str(result.get('response_text_changed')).lower()}",
        "",
        "## Tokenization",
        "",
        json.dumps(result.get("tokenization") or {}, indent=2, ensure_ascii=False),
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


def run_training(args: argparse.Namespace, result: dict[str, Any], config: dict[str, Any]) -> int:
    import torch  # type: ignore
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training  # type: ignore
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, Trainer  # type: ignore

    rows = read_jsonl(TRAIN_PATH)
    validation_rows = read_jsonl(VALIDATION_PATH)
    if args.limit_train_rows is not None:
        rows = rows[: int(args.limit_train_rows)]
    result["train_row_count"] = len(rows)
    result["validation_row_count"] = len(validation_rows)
    result["raw_private_transcript_included"] = any(row.get("raw_private_transcript_included") is not False for row in rows)
    if result["raw_private_transcript_included"]:
        raise RuntimeError("mixed replay dataset includes raw private transcripts")

    model_path = safe_project_path(str(config["base_model_path"]))
    cache_dir = safe_project_path(str(config["cache_dir"]))
    adapter_path = safe_project_path(str(args.output_adapter_dir or config["output_adapter_dir"]))
    trainer_output_dir = adapter_path / "trainer-output"
    if adapter_path.exists() and not result["resume_requested"]:
        if (adapter_path / "adapter_config.json").is_file():
            raise FileExistsError(f"adapter path already exists: {rel(adapter_path)}")
    tokenizer = AutoTokenizer.from_pretrained(
        str(model_path),
        cache_dir=str(cache_dir),
        local_files_only=True,
        trust_remote_code=False,
    )
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenized_train = tokenize_rows_assistant_only(rows, tokenizer, int(config["max_seq_length"]))
    tokenized_eval = tokenize_rows_assistant_only(validation_rows[: min(24, len(validation_rows))], tokenizer, int(config["max_seq_length"]))
    result["tokenization"] = {
        "train": tokenized_train.stats,
        "validation_sample": tokenized_eval.stats,
    }
    result["training_attempted"] = True
    persist(result)

    quantization_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
    )
    if torch.cuda.is_available():
        torch.cuda.reset_peak_memory_stats()
    started = time.perf_counter()
    model = AutoModelForCausalLM.from_pretrained(
        str(model_path),
        cache_dir=str(cache_dir),
        local_files_only=True,
        device_map="auto",
        torch_dtype="auto",
        low_cpu_mem_usage=True,
        quantization_config=quantization_config,
        trust_remote_code=False,
    )
    result["model_loaded"] = True
    result["local_model_calls_made"] = True
    model.config.use_cache = False
    use_gradient_checkpointing = bool(config.get("gradient_checkpointing", True))
    if use_gradient_checkpointing:
        model.gradient_checkpointing_enable()
    prepare_kwargs: dict[str, Any] = {}
    if "use_gradient_checkpointing" in inspect.signature(prepare_model_for_kbit_training).parameters:
        prepare_kwargs["use_gradient_checkpointing"] = use_gradient_checkpointing
    model = prepare_model_for_kbit_training(model, **prepare_kwargs)
    lora_config = LoraConfig(
        r=int(config["lora_r"]),
        lora_alpha=int(config["lora_alpha"]),
        target_modules=list(config.get("lora_target_modules") or []),
        lora_dropout=float(config["lora_dropout"]),
        bias="none",
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    train_config = dict(config)
    train_config["output_adapter_dir"] = rel(adapter_path)
    max_steps = int(args.max_steps or config["max_steps"])
    training_args = build_training_arguments(train_config, max_steps, trainer_output_dir)
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=PlannerDataset(tokenized_train.rows),
        eval_dataset=PlannerDataset(tokenized_eval.rows),
        data_collator=make_collator(tokenizer),
    )
    train_output = trainer.train(resume_from_checkpoint=result["resume_requested"] or None)
    eval_metrics = trainer.evaluate()
    adapter_path.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(str(adapter_path))
    tokenizer.save_pretrained(str(adapter_path))
    result["training_completed"] = True
    result["status"] = "completed"
    result["adapter_path"] = rel(adapter_path)
    result["adapter_saved"] = (adapter_path / "adapter_config.json").is_file()
    result["train_steps_completed"] = int(getattr(trainer.state, "global_step", 0) or 0)
    result["train_loss"] = (
        float(train_output.metrics["train_loss"])
        if isinstance(getattr(train_output, "metrics", None), dict)
        and train_output.metrics.get("train_loss") is not None
        else None
    )
    result["eval_loss"] = float(eval_metrics["eval_loss"]) if eval_metrics.get("eval_loss") is not None else None
    result["train_runtime_seconds"] = round(time.perf_counter() - started, 3)
    result["peak_gpu_memory_bytes"] = int(torch.cuda.max_memory_allocated()) if torch.cuda.is_available() else None
    result["notes"].append("Mixed-replay adapter saved under ignored local_artifacts; no runtime wiring changed.")
    persist(result)
    return 0


def classify_training_blocker(exc: Exception) -> str:
    text = f"{type(exc).__name__}: {exc}".lower()
    if "out of memory" in text or ("cuda" in text and "memory" in text):
        return "gpu_memory_or_cuda_issue"
    if "adapter path already exists" in text:
        return "adapter_path_already_exists"
    if "no assistant target tokens" in text:
        return "assistant_token_masking_issue"
    if "does not exist" in text or "missing" in text:
        return "local_artifact_missing"
    return "python_windows_training_issue"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Train local Qwen mixed-replay compact-planner QLoRA adapter.")
    parser.add_argument("--max-steps", type=int, default=None)
    parser.add_argument("--output-adapter-dir", default=None)
    parser.add_argument("--dry-run-config-only", action="store_true")
    parser.add_argument("--skip-train-if-missing-deps", action="store_true")
    parser.add_argument("--resume", choices=["true", "false"], default="false")
    parser.add_argument("--limit-train-rows", type=int, default=None)
    parser.add_argument("--eval-during-training", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.max_steps is not None and args.max_steps <= 0:
        raise SystemExit("--max-steps must be positive")
    if args.limit_train_rows is not None and args.limit_train_rows <= 0:
        raise SystemExit("--limit-train-rows must be positive")
    config = read_json(CONFIG_PATH)
    if args.output_adapter_dir:
        config["output_adapter_dir"] = args.output_adapter_dir
    if args.max_steps is not None:
        config["max_steps"] = int(args.max_steps)
    deps = dependency_status()
    result = base_result(args, config, deps)
    config_errors = validate_config(config)
    if not in_expected_llm_env():
        result["status"] = "wrong_python_environment"
        result["exact_blocker"] = "Run with .venv-llm\\Scripts\\python.exe"
        persist(result)
        print(json.dumps({"status": result["status"], "exact_blocker": result["exact_blocker"]}, indent=2))
        return 1
    if config_errors:
        result["status"] = "config_invalid"
        result["exact_blocker"] = "; ".join(config_errors)
        result["blocker_classification"] = "config_invalid"
        persist(result)
        print(json.dumps({"status": result["status"], "errors": config_errors}, indent=2))
        return 1
    if args.dry_run_config_only:
        result["status"] = "dry_run_config_valid"
        persist(result)
        print(json.dumps({"status": result["status"], "config_valid": True}, indent=2))
        return 0
    if not deps.get("ready"):
        result["status"] = "missing_dependencies"
        result["exact_blocker"] = json.dumps(deps.get("missing_required") or [])
        result["blocker_classification"] = "missing_dependencies"
        persist(result)
        print(json.dumps({"status": result["status"], "dependency_status": deps}, indent=2))
        return 0 if args.skip_train_if_missing_deps else 1
    try:
        return run_training(args, result, config)
    except Exception as exc:
        result["status"] = "blocked"
        result["exact_blocker"] = f"{type(exc).__name__}: {exc}"
        result["blocker_classification"] = classify_training_blocker(exc)
        result["traceback_excerpt"] = traceback.format_exc(limit=8)[-4000:]
        persist(result)
        print(json.dumps({"status": result["status"], "exact_blocker": result["exact_blocker"]}, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
