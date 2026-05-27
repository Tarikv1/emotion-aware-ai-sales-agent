#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import inspect
import json
from pathlib import Path
import shutil
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
)
from runtime.llm_brain.conversation_brain_schema import (  # noqa: E402
    PRIMARY_MODEL_ID,
    REQUIRED_COMPACT_PLANNER_FIELDS,
)
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
    target_json_text,
)


EXPERIMENT_ID = "LOCAL-QWEN-LORA-TINY-OVERFIT-001"
DATASET_EXPERIMENT_ID = "LOCAL-QWEN-TINY-OVERFIT-DATASET-001"
DATASET_DIR = ROOT / "research" / "experiments" / "generated" / DATASET_EXPERIMENT_ID
TRAIN_PATH = DATASET_DIR / "train.jsonl"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / EXPERIMENT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"
TINY_ADAPTER_PATH = "local_artifacts/adapters/qwen2.5-sales-brain-lora-tiny-overfit-001"
TINY_CONFIG = {
    "base_model_id": PRIMARY_MODEL_ID,
    "base_model_path": "local_artifacts/models/qwen2.5-7b-instruct",
    "dataset_dir": f"research/experiments/generated/{DATASET_EXPERIMENT_ID}",
    "output_adapter_dir": TINY_ADAPTER_PATH,
    "cache_dir": "local_artifacts/cache/huggingface",
    "quantization": "4bit",
    "target": "compact planner JSON",
    "max_seq_length": 896,
    "learning_rate": 0.0002,
    "per_device_train_batch_size": 1,
    "batch_size": 1,
    "gradient_accumulation_steps": 1,
    "max_steps": 100,
    "eval_steps": 20,
    "save_strategy": "end_only",
    "seed": 42015,
    "device": "cuda",
    "lora_r": 16,
    "lora_alpha": 32,
    "lora_dropout": 0.0,
    "lora_target_modules": ["q_proj", "v_proj"],
    "optimizer": "adamw_torch",
    "fp16": True,
    "gradient_checkpointing": True,
    "local_files_only": True,
    "allow_model_download": False,
}

TINY_ALLOWED_VALUE_FIELDS = ("act", "sub", "buyer", "intent", "rel", "neg", "action", "strategy")
TINY_SYSTEM_MESSAGE = (
    "You are a local-only compact planner. Return one strict minified JSON object only. "
    "No prose, markdown, provider calls, OpenAI API calls, email, calendar, CRM, TTS, or side effects."
)


@dataclass(frozen=True)
class TinyTokenizedRows:
    rows: list[dict[str, list[int]]]
    stats: dict[str, Any]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def validate_config(config: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if config.get("base_model_id") != PRIMARY_MODEL_ID:
        errors.append(f"base_model_id must be {PRIMARY_MODEL_ID}")
    if config.get("quantization") != "4bit":
        errors.append("quantization must be 4bit")
    if config.get("target") != "compact planner JSON":
        errors.append("target must be compact planner JSON")
    if config.get("device") != "cuda":
        errors.append("device must be cuda")
    for key in ("base_model_path", "dataset_dir", "output_adapter_dir", "cache_dir"):
        value = str(config.get(key) or "")
        try:
            path = safe_project_path(value)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        if key == "base_model_path" and not path.is_dir():
            errors.append(f"base_model_path does not exist: {value}")
        if key == "dataset_dir" and not (path / "train.jsonl").is_file():
            errors.append(f"tiny train.jsonl does not exist: {value}")
        if key == "output_adapter_dir" and not value.replace("\\", "/").startswith("local_artifacts/adapters/"):
            errors.append("output_adapter_dir must stay under local_artifacts/adapters")
    for key in ("max_seq_length", "batch_size", "gradient_accumulation_steps", "max_steps", "eval_steps", "lora_r"):
        if not isinstance(config.get(key), int) or int(config.get(key)) <= 0:
            errors.append(f"{key} must be a positive integer")
    if not isinstance(config.get("learning_rate"), (int, float)) or float(config["learning_rate"]) <= 0:
        errors.append("learning_rate must be positive")
    return errors


def tiny_allowed_values_instruction() -> str:
    return "\n".join(f"{field}={','.join(allowed_values_for(field))}" for field in TINY_ALLOWED_VALUE_FIELDS)


def tiny_input_context(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "buyer_text": str(row.get("sanitized_buyer_text") or ""),
        "prior_state": row.get("prior_state") or {},
        "approved_fact_ids": sorted((row.get("approved_campaign_fact_summaries") or {}).keys()),
        "campaign_id": str(row.get("campaign_id") or ""),
    }


def tiny_chat_messages(row: dict[str, Any], *, include_target: bool) -> list[dict[str, str]]:
    user_content = "\n".join(
        [
            f"Contract={COMPACT_VALUE_CONTRACT_VERSION}",
            f"Required keys={','.join(REQUIRED_COMPACT_PLANNER_FIELDS)}",
            "Allowed values:",
            tiny_allowed_values_instruction(),
            "Rules: preserve buyer words, and/or, negation, and safety boundaries. Use listed labels only.",
            "Return compact JSON only. No extra keys. No case IDs or generic labels.",
            "Input=" + json.dumps(tiny_input_context(row), ensure_ascii=False, separators=(",", ":")),
        ]
    )
    messages = [
        {"role": "system", "content": TINY_SYSTEM_MESSAGE},
        {"role": "user", "content": user_content},
    ]
    if include_target:
        messages.append({"role": "assistant", "content": target_json_text(row)})
    return messages


def render_tiny_chat(tokenizer: Any, row: dict[str, Any], *, include_target: bool) -> str:
    messages = tiny_chat_messages(row, include_target=include_target)
    if hasattr(tokenizer, "apply_chat_template"):
        return str(
            tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=not include_target,
            )
        )
    rendered = "\n\n".join(f"{item['role'].upper()}: {item['content']}" for item in messages)
    return rendered + ("\n\nASSISTANT:" if not include_target else "")


def render_train_chat(tokenizer: Any, row: dict[str, Any]) -> str:
    return render_tiny_chat(tokenizer, row, include_target=True)


def render_eval_chat(tokenizer: Any, row: dict[str, Any]) -> str:
    return render_tiny_chat(tokenizer, row, include_target=False)


def tokenize_rows_assistant_only(rows: list[dict[str, Any]], tokenizer: Any, max_seq_length: int) -> TinyTokenizedRows:
    tokenized_rows: list[dict[str, list[int]]] = []
    prompt_lengths: list[int] = []
    full_lengths: list[int] = []
    target_token_lengths: list[int] = []
    truncated_count = 0
    eos_appended_count = 0
    label_token_count = 0
    for row in rows:
        prompt_text = render_eval_chat(tokenizer, row)
        full_text = render_train_chat(tokenizer, row)
        prompt_ids = list(tokenizer(prompt_text, add_special_tokens=False)["input_ids"])
        full_ids_untruncated = list(tokenizer(full_text, add_special_tokens=False)["input_ids"])
        eos_token_id = tokenizer.eos_token_id
        if eos_token_id is not None and (not full_ids_untruncated or full_ids_untruncated[-1] != eos_token_id):
            full_ids_untruncated.append(int(eos_token_id))
            eos_appended_count += 1
        input_ids = full_ids_untruncated[:max_seq_length]
        attention_mask = [1] * len(input_ids)
        labels = list(input_ids)
        prompt_len = min(len(prompt_ids), len(labels))
        labels[:prompt_len] = [-100] * prompt_len
        if all(label == -100 for label in labels):
            raise ValueError(f"{row.get('case_id')} has no assistant target tokens after truncation")
        target_tokens = sum(1 for label in labels if label != -100)
        prompt_lengths.append(len(prompt_ids))
        full_lengths.append(len(full_ids_untruncated))
        target_token_lengths.append(target_tokens)
        label_token_count += target_tokens
        if len(full_ids_untruncated) > max_seq_length:
            truncated_count += 1
        tokenized_rows.append({"input_ids": input_ids, "attention_mask": attention_mask, "labels": labels})
    stats = {
        "row_count": len(rows),
        "max_prompt_tokens": max(prompt_lengths) if prompt_lengths else 0,
        "max_full_tokens": max(full_lengths) if full_lengths else 0,
        "max_target_tokens": max(target_token_lengths) if target_token_lengths else 0,
        "min_target_tokens": min(target_token_lengths) if target_token_lengths else 0,
        "truncated_example_count": truncated_count,
        "label_token_count": label_token_count,
        "labels_mask_prompt_tokens": True,
        "labels_train_only_assistant_tokens": True,
        "full_sequence_trained": False,
        "eos_token_appended_count": eos_appended_count,
    }
    return TinyTokenizedRows(rows=tokenized_rows, stats=stats)


def build_training_arguments(config: dict[str, Any], max_steps: int, output_dir: Path) -> Any:
    from transformers import TrainingArguments  # type: ignore

    kwargs: dict[str, Any] = {
        "output_dir": str(output_dir),
        "per_device_train_batch_size": int(config["per_device_train_batch_size"]),
        "per_device_eval_batch_size": 1,
        "gradient_accumulation_steps": int(config["gradient_accumulation_steps"]),
        "learning_rate": float(config["learning_rate"]),
        "max_steps": int(max_steps),
        "logging_steps": 1,
        "eval_steps": int(config["eval_steps"]),
        "save_strategy": "no",
        "report_to": [],
        "remove_unused_columns": False,
        "dataloader_pin_memory": False,
        "seed": int(config["seed"]),
        "fp16": bool(config.get("fp16", True)),
        "optim": str(config.get("optimizer") or "paged_adamw_8bit"),
    }
    params = inspect.signature(TrainingArguments.__init__).parameters
    if "eval_strategy" in params:
        kwargs["eval_strategy"] = "steps"
    else:
        kwargs["evaluation_strategy"] = "steps"
    if "gradient_checkpointing" in params:
        kwargs["gradient_checkpointing"] = bool(config.get("gradient_checkpointing", True))
    if "overwrite_output_dir" in params:
        kwargs["overwrite_output_dir"] = bool(config.get("overwrite_output_dir", False))
    return TrainingArguments(**kwargs)


def base_result(args: argparse.Namespace, config: dict[str, Any], deps: dict[str, Any]) -> dict[str, Any]:
    hardware = hardware_summary()
    adapter_path = safe_project_path(str(config["output_adapter_dir"]))
    return {
        "experiment_id": EXPERIMENT_ID,
        "generated_at": utc_now(),
        "status": "not_run",
        "phase": "tiny_overfit_training",
        "config": config,
        "python_executable": sys.executable,
        "expected_python_environment": ".venv-llm",
        "expected_python_environment_active": in_expected_llm_env(),
        "dependency_status": deps,
        "hardware_summary": hardware,
        "cuda_available": bool(hardware.get("cuda_available")),
        "gpu_name": hardware.get("gpu_name"),
        "overwrite_adapter": bool(args.overwrite_adapter),
        "training_attempted": False,
        "training_completed": False,
        "exact_blocker": None,
        "blocker_classification": None,
        "model_loaded": False,
        "adapter_saved": False,
        "adapter_path": rel(adapter_path),
        "adapter_files_committed": adapter_files_committed(),
        "train_row_count": 0,
        "train_steps_completed": 0,
        "train_loss": None,
        "eval_loss": None,
        "train_runtime_seconds": None,
        "peak_gpu_memory_bytes": None,
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
        "## Training",
        "",
        f"- status: {result.get('status')}",
        f"- training_attempted: {str(result.get('training_attempted')).lower()}",
        f"- training_completed: {str(result.get('training_completed')).lower()}",
        f"- exact_blocker: {result.get('exact_blocker')}",
        f"- blocker_classification: {result.get('blocker_classification')}",
        f"- adapter_path: `{result.get('adapter_path')}`",
        f"- adapter_saved: {str(result.get('adapter_saved')).lower()}",
        f"- adapter_files_committed: {str(result.get('adapter_files_committed')).lower()}",
        f"- train_rows: {result.get('train_row_count')}",
        f"- train_steps_completed: {result.get('train_steps_completed')}",
        f"- train_loss: {result.get('train_loss')}",
        f"- eval_loss: {result.get('eval_loss')}",
        f"- train_runtime_seconds: {result.get('train_runtime_seconds')}",
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
    if result.get("evaluation"):
        lines.extend(["", "## Evaluation", "", json.dumps(result["evaluation"], indent=2, ensure_ascii=False)])
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
    result["train_row_count"] = len(rows)
    result["raw_private_transcript_included"] = any(row.get("raw_private_transcript_included") is not False for row in rows)
    if result["raw_private_transcript_included"]:
        raise RuntimeError("tiny dataset includes raw private transcripts")

    model_path = safe_project_path(str(config["base_model_path"]))
    cache_dir = safe_project_path(str(config["cache_dir"]))
    adapter_path = safe_project_path(str(config["output_adapter_dir"]))
    trainer_output_dir = adapter_path / "trainer-output"
    if adapter_path.exists():
        if not args.overwrite_adapter:
            raise FileExistsError(f"adapter path already exists: {rel(adapter_path)}")
        shutil.rmtree(adapter_path)
    tokenizer = AutoTokenizer.from_pretrained(
        str(model_path),
        cache_dir=str(cache_dir),
        local_files_only=True,
        trust_remote_code=False,
    )
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenized = tokenize_rows_assistant_only(rows, tokenizer, int(config["max_seq_length"]))
    result["tokenization"] = tokenized.stats
    result["training_attempted"] = True

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
    model.config.use_cache = False
    use_gradient_checkpointing = bool(config.get("gradient_checkpointing", True))
    if use_gradient_checkpointing:
        model.gradient_checkpointing_enable()
    prepare_kwargs: dict[str, Any] = {}
    if "use_gradient_checkpointing" in inspect.signature(prepare_model_for_kbit_training).parameters:
        prepare_kwargs["use_gradient_checkpointing"] = use_gradient_checkpointing
    model = prepare_model_for_kbit_training(model, **prepare_kwargs)
    result["prepare_model_for_kbit_training_kwargs"] = prepare_kwargs
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

    max_steps = int(args.max_steps or config["max_steps"])
    training_args = build_training_arguments(config, max_steps, trainer_output_dir)
    planner_dataset = PlannerDataset(tokenized.rows)
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=planner_dataset,
        eval_dataset=planner_dataset,
        data_collator=make_collator(tokenizer),
    )
    train_output = trainer.train()
    eval_metrics = trainer.evaluate()
    adapter_path.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(str(adapter_path))
    tokenizer.save_pretrained(str(adapter_path))
    result["training_completed"] = True
    result["status"] = "completed"
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
    result["local_model_calls_made"] = True
    result["notes"].append("Tiny adapter saved under ignored local_artifacts; no runtime wiring changed.")
    persist(result)
    return 0


def classify_training_blocker(exc: Exception) -> str:
    text = f"{type(exc).__name__}: {exc}".lower()
    if "out of memory" in text or "cuda" in text and "memory" in text:
        return "Python/Windows training issue"
    if "adapter path already exists" in text:
        return "adapter path already exists"
    if "no assistant target tokens" in text:
        return "labels not masked correctly"
    if "base_model_path" in text or "does not exist" in text:
        return "Python/Windows training issue"
    return "Python/Windows training issue"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Train tiny Qwen compact-planner LoRA overfit probe.")
    parser.add_argument("--max-steps", type=int, default=None, help="Override tiny overfit max steps.")
    parser.add_argument("--overwrite-adapter", action="store_true", help="Delete and recreate the tiny adapter path.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.max_steps is not None and args.max_steps <= 0:
        raise SystemExit("--max-steps must be positive")
    config = dict(TINY_CONFIG)
    if args.max_steps is not None:
        config["max_steps"] = int(args.max_steps)
    deps = dependency_status()
    result = read_json(RESULT_PATH)
    if result.get("evaluation"):
        result = {"previous_result_replaced_at": utc_now(), "previous_evaluation_status": result.get("evaluation", {}).get("status")}
    result = {**base_result(args, config, deps), **({"previous_result": result} if result else {})}
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
        result["blocker_classification"] = "Python/Windows training issue"
        persist(result)
        print(json.dumps({"status": result["status"], "errors": config_errors}, indent=2))
        return 1
    if not deps.get("ready"):
        result["status"] = "dependency_missing"
        result["exact_blocker"] = "; ".join(deps.get("missing_required") or []) or "training dependency import failed"
        result["blocker_classification"] = "Python/Windows training issue"
        persist(result)
        print(json.dumps({"status": result["status"], "exact_blocker": result["exact_blocker"]}, indent=2))
        return 1
    if not result["cuda_available"]:
        result["status"] = "gpu_missing"
        result["exact_blocker"] = "CUDA GPU is not available to torch"
        result["blocker_classification"] = "Python/Windows training issue"
        persist(result)
        print(json.dumps({"status": result["status"], "exact_blocker": result["exact_blocker"]}, indent=2))
        return 1
    try:
        code = run_training(args, result, config)
        print(
            json.dumps(
                {
                    "status": result["status"],
                    "training_completed": result["training_completed"],
                    "adapter_saved": result["adapter_saved"],
                    "adapter_path": result["adapter_path"],
                    "train_steps_completed": result["train_steps_completed"],
                    "train_loss": result["train_loss"],
                    "eval_loss": result["eval_loss"],
                },
                indent=2,
            )
        )
        return code
    except KeyboardInterrupt as exc:
        result["status"] = "interrupted"
        result["training_completed"] = False
        result["exact_blocker"] = f"{type(exc).__name__}: training interrupted by operator after slow checkpointed attempt"
        result["blocker_classification"] = "Python/Windows training issue"
        result["traceback_excerpt"] = traceback.format_exc(limit=8)[-4000:]
        persist(result)
        print(json.dumps({"status": "interrupted", "exact_blocker": result["exact_blocker"]}, indent=2))
        return 130
    except Exception as exc:
        result["status"] = "blocked"
        result["training_completed"] = False
        result["exact_blocker"] = f"{type(exc).__name__}: {exc}"
        result["blocker_classification"] = classify_training_blocker(exc)
        result["traceback_excerpt"] = traceback.format_exc(limit=8)[-4000:]
        persist(result)
        print(json.dumps({"status": "blocked", "exact_blocker": result["exact_blocker"]}, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
