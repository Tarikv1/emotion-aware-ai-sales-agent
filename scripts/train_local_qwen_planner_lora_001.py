#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import importlib
import importlib.util
from importlib import metadata as importlib_metadata
import inspect
import json
from pathlib import Path
import subprocess
import sys
import traceback
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.llm_brain.conversation_brain_schema import (  # noqa: E402
    COMPACT_PLANNER_SCHEMA_MODE,
    PRIMARY_MODEL_ID,
    REQUIRED_COMPACT_PLANNER_FIELDS,
)
from runtime.llm_brain.local_transformers_runner import hardware_summary  # noqa: E402


EXPERIMENT_ID = "LOCAL-QWEN-QLORA-TRAINING-DRY-RUN-001"
CONFIG_PATH = ROOT / "runtime" / "llm_brain" / "training" / "qwen_qlora_planner_config.json"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / EXPERIMENT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"
SFT_EXPERIMENT_ID = "LOCAL-QWEN-SFT-DATASET-001"
WEIGHT_SUFFIXES = (".safetensors", ".bin", ".gguf", ".pt", ".pth", ".ckpt")


SYSTEM_MESSAGE = (
    "You are a local-only sales conversation brain. Return exactly one strict compact "
    "planner JSON object. Preserve the buyer's current words, conjunctions, and negation. "
    "Use only sanitized input context and approved campaign fact summaries. Do not claim "
    "provider, OpenAI API, email, calendar, CRM, TTS, or live side effects."
)


USER_INSTRUCTION = (
    "Use the sanitized input context below to produce compact planner JSON only. "
    f"Required compact keys in order: {', '.join(REQUIRED_COMPACT_PLANNER_FIELDS)}. "
    "The assistant response must be the target compact JSON object and nothing else."
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            value = json.loads(stripped)
            if not isinstance(value, dict):
                raise ValueError(f"{rel(path)} line {line_number} is not a JSON object")
            rows.append(value)
    return rows


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def safe_project_path(relative_path: str) -> Path:
    path = Path(relative_path)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"path must be project-relative: {relative_path!r}")
    return ROOT / path


def package_version(module_name: str, package_name: str | None = None) -> str | None:
    if importlib.util.find_spec(module_name) is None:
        return None
    try:
        return importlib_metadata.version(package_name or module_name)
    except importlib_metadata.PackageNotFoundError:
        return "unknown"


def import_check(import_statement: str) -> tuple[bool, str | None]:
    try:
        exec(import_statement, {})
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"
    return True, None


def dependency_status() -> dict[str, Any]:
    modules = {
        "torch": importlib.util.find_spec("torch") is not None,
        "transformers": importlib.util.find_spec("transformers") is not None,
        "accelerate": importlib.util.find_spec("accelerate") is not None,
        "bitsandbytes": importlib.util.find_spec("bitsandbytes") is not None,
        "peft": importlib.util.find_spec("peft") is not None,
        "datasets": importlib.util.find_spec("datasets") is not None,
        "trl": importlib.util.find_spec("trl") is not None,
        "evaluate": importlib.util.find_spec("evaluate") is not None,
        "sentencepiece": importlib.util.find_spec("sentencepiece") is not None,
        "protobuf": importlib.util.find_spec("google.protobuf") is not None,
    }
    versions = {
        "torch": package_version("torch"),
        "transformers": package_version("transformers"),
        "accelerate": package_version("accelerate"),
        "bitsandbytes": package_version("bitsandbytes"),
        "peft": package_version("peft"),
        "datasets": package_version("datasets"),
        "trl": package_version("trl"),
        "evaluate": package_version("evaluate"),
        "sentencepiece": package_version("sentencepiece"),
        "protobuf": package_version("google.protobuf", "protobuf"),
    }
    required = ["torch", "transformers", "accelerate", "bitsandbytes", "peft", "datasets"]
    optional = ["trl", "evaluate", "sentencepiece", "protobuf"]
    missing_required = [name for name in required if not modules[name]]
    peft_import_ok, peft_import_error = import_check(
        "from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training"
    )
    trainer_import_ok, trainer_import_error = import_check(
        "from transformers import Trainer, TrainingArguments"
    )
    trl_import_ok, trl_import_error = import_check("from trl import SFTTrainer, SFTConfig")
    return {
        "modules": modules,
        "versions": versions,
        "required": required,
        "optional": optional,
        "missing_required": missing_required,
        "ready": not missing_required and peft_import_ok and trainer_import_ok,
        "peft_import_ok": peft_import_ok,
        "peft_import_error": peft_import_error,
        "transformers_trainer_import_ok": trainer_import_ok,
        "transformers_trainer_import_error": trainer_import_error,
        "trl_sft_trainer_import_ok": trl_import_ok,
        "trl_sft_trainer_import_error": trl_import_error,
        "training_backend": "transformers_trainer_peft_qlora",
    }


def in_expected_llm_env() -> bool:
    executable = Path(sys.executable).resolve()
    expected = (ROOT / ".venv-llm" / "Scripts" / "python.exe").resolve()
    return executable == expected


def git_tracked_local_artifacts() -> list[str]:
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
        return []
    if completed.returncode != 0:
        return []
    return [line.strip().replace("\\", "/") for line in completed.stdout.splitlines() if line.strip()]


def adapter_files_committed() -> bool:
    tracked = git_tracked_local_artifacts()
    return any(path.lower().endswith(WEIGHT_SUFFIXES) for path in tracked)


def extract_input_context_from_prompt(prompt: str) -> dict[str, Any]:
    marker = "Input context:\n"
    marker_index = prompt.rfind(marker)
    if marker_index == -1:
        return {}
    text = prompt[marker_index + len(marker) :].strip()
    decoder = json.JSONDecoder()
    try:
        value, _end = decoder.raw_decode(text)
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}


def sanitized_context_for_row(row: dict[str, Any]) -> dict[str, Any]:
    context = extract_input_context_from_prompt(str(row.get("prompt") or ""))
    if not context:
        context = {
            "normalized_transcript": "",
            "prior_state": row.get("prior_state") if isinstance(row.get("prior_state"), dict) else {},
            "approved_campaign_fact_ids": list((row.get("approved_campaign_fact_summaries") or {}).keys()),
            "approved_campaign_fact_summaries": row.get("approved_campaign_fact_summaries") or {},
            "smoke_contract": {},
            "last_agent_question": "",
            "campaign_id": row.get("campaign_id") or "",
        }
    return {
        "normalized_transcript": str(context.get("normalized_transcript") or ""),
        "prior_state": context.get("prior_state") if isinstance(context.get("prior_state"), dict) else {},
        "approved_campaign_fact_ids": [
            str(item) for item in context.get("approved_campaign_fact_ids") or []
        ],
        "approved_campaign_fact_summaries": (
            context.get("approved_campaign_fact_summaries")
            if isinstance(context.get("approved_campaign_fact_summaries"), dict)
            else {}
        ),
        "smoke_contract": context.get("smoke_contract") if isinstance(context.get("smoke_contract"), dict) else {},
        "last_agent_question": str(context.get("last_agent_question") or ""),
        "campaign_id": str(context.get("campaign_id") or row.get("campaign_id") or ""),
    }


def target_json_text(row: dict[str, Any]) -> str:
    target = row.get("target_compact_json")
    if not isinstance(target, dict):
        raise ValueError(f"{row.get('case_id')} target_compact_json must be an object")
    return json.dumps(target, ensure_ascii=False, separators=(",", ":"))


def chat_messages(row: dict[str, Any], *, include_target: bool) -> list[dict[str, str]]:
    context = sanitized_context_for_row(row)
    user_payload = {
        "case_id": str(row.get("case_id") or ""),
        "source_type": str(row.get("source_type") or ""),
        "campaign_id": str(row.get("campaign_id") or context.get("campaign_id") or ""),
        "privacy_level": str(row.get("privacy_level") or ""),
        "raw_private_transcript_included": bool(row.get("raw_private_transcript_included")),
        "input_context": context,
        "expected_safety_constraints": row.get("expected_safety_constraints") or {},
    }
    messages = [
        {"role": "system", "content": SYSTEM_MESSAGE},
        {
            "role": "user",
            "content": USER_INSTRUCTION + "\n\nSanitized input context:\n"
            + json.dumps(user_payload, ensure_ascii=False, separators=(",", ":")),
        },
    ]
    if include_target:
        messages.append({"role": "assistant", "content": target_json_text(row)})
    return messages


def render_chat(tokenizer: Any, row: dict[str, Any], *, include_target: bool) -> str:
    messages = chat_messages(row, include_target=include_target)
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


@dataclass(frozen=True)
class TokenizedRows:
    rows: list[dict[str, list[int]]]
    stats: dict[str, Any]


def tokenize_rows(rows: list[dict[str, Any]], tokenizer: Any, max_seq_length: int) -> TokenizedRows:
    tokenized_rows: list[dict[str, list[int]]] = []
    prompt_lengths: list[int] = []
    full_lengths: list[int] = []
    target_token_lengths: list[int] = []
    truncated_count = 0
    label_token_count = 0
    for row in rows:
        prompt_text = render_chat(tokenizer, row, include_target=False)
        full_text = render_chat(tokenizer, row, include_target=True)
        prompt_ids = tokenizer(prompt_text, add_special_tokens=False)["input_ids"]
        full = tokenizer(
            full_text,
            add_special_tokens=False,
            truncation=True,
            max_length=max_seq_length,
        )
        input_ids = list(full["input_ids"])
        attention_mask = list(full["attention_mask"])
        labels = list(input_ids)
        prompt_len = min(len(prompt_ids), len(labels))
        labels[:prompt_len] = [-100] * prompt_len
        if all(label == -100 for label in labels):
            raise ValueError(f"{row.get('case_id')} has no target tokens after max_seq_length truncation")
        full_len_untruncated = len(tokenizer(full_text, add_special_tokens=False)["input_ids"])
        target_tokens = sum(1 for label in labels if label != -100)
        prompt_lengths.append(len(prompt_ids))
        full_lengths.append(full_len_untruncated)
        target_token_lengths.append(target_tokens)
        label_token_count += target_tokens
        if full_len_untruncated > max_seq_length:
            truncated_count += 1
        tokenized_rows.append(
            {
                "input_ids": input_ids,
                "attention_mask": attention_mask,
                "labels": labels,
            }
        )
    stats = {
        "row_count": len(rows),
        "max_prompt_tokens": max(prompt_lengths) if prompt_lengths else 0,
        "max_full_tokens": max(full_lengths) if full_lengths else 0,
        "max_target_tokens": max(target_token_lengths) if target_token_lengths else 0,
        "min_target_tokens": min(target_token_lengths) if target_token_lengths else 0,
        "truncated_example_count": truncated_count,
        "label_token_count": label_token_count,
    }
    return TokenizedRows(rows=tokenized_rows, stats=stats)


class PlannerDataset:
    def __init__(self, rows: list[dict[str, list[int]]]) -> None:
        self.rows = rows

    def __len__(self) -> int:
        return len(self.rows)

    def __getitem__(self, index: int) -> dict[str, list[int]]:
        return self.rows[index]


def make_collator(tokenizer: Any):
    pad_token_id = tokenizer.pad_token_id
    if pad_token_id is None:
        pad_token_id = tokenizer.eos_token_id

    def collate(features: list[dict[str, list[int]]]) -> dict[str, Any]:
        import torch  # type: ignore

        max_length = max(len(item["input_ids"]) for item in features)
        batch: dict[str, list[list[int]]] = {"input_ids": [], "attention_mask": [], "labels": []}
        for item in features:
            pad_length = max_length - len(item["input_ids"])
            batch["input_ids"].append(item["input_ids"] + [pad_token_id] * pad_length)
            batch["attention_mask"].append(item["attention_mask"] + [0] * pad_length)
            batch["labels"].append(item["labels"] + [-100] * pad_length)
        return {key: torch.tensor(value, dtype=torch.long) for key, value in batch.items()}

    return collate


def dataset_summary(config: dict[str, Any]) -> dict[str, Any]:
    dataset_dir = safe_project_path(str(config["dataset_dir"]))
    splits: dict[str, dict[str, Any]] = {}
    raw_private = False
    for split_name in ("train", "validation", "test"):
        path = dataset_dir / f"{split_name}.jsonl"
        rows = read_jsonl(path) if path.is_file() else []
        raw_private = raw_private or any(row.get("raw_private_transcript_included") is not False for row in rows)
        splits[split_name] = {"path": rel(path), "count": len(rows)}
    return {
        "dataset_dir": rel(dataset_dir),
        "splits": splits,
        "row_count": sum(item["count"] for item in splits.values()),
        "raw_private_transcript_included": raw_private,
    }


def validate_config(config: dict[str, Any]) -> list[str]:
    required = {
        "base_model_id",
        "base_model_path",
        "dataset_dir",
        "output_adapter_dir",
        "cache_dir",
        "quantization",
        "target",
        "max_seq_length",
        "learning_rate",
        "batch_size",
        "gradient_accumulation_steps",
        "max_steps",
        "eval_steps",
        "save_steps",
        "seed",
        "device",
        "lora_r",
        "lora_alpha",
        "lora_dropout",
    }
    errors: list[str] = []
    missing = sorted(required - set(config))
    if missing:
        errors.append(f"config missing field(s): {missing}")
    if config.get("base_model_id") != PRIMARY_MODEL_ID:
        errors.append(f"base_model_id must be {PRIMARY_MODEL_ID}")
    if config.get("quantization") != "4bit":
        errors.append("quantization must be 4bit for this dry run")
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
        if key == "output_adapter_dir" and not value.replace("\\", "/").startswith("local_artifacts/adapters/"):
            errors.append("output_adapter_dir must stay under local_artifacts/adapters")
        if key == "base_model_path" and not path.is_dir():
            errors.append(f"base_model_path does not exist: {value}")
        if key == "dataset_dir" and not path.is_dir():
            errors.append(f"dataset_dir does not exist: {value}")
    for key in ("max_seq_length", "batch_size", "gradient_accumulation_steps", "max_steps", "eval_steps", "lora_r"):
        if not isinstance(config.get(key), int) or int(config.get(key)) <= 0:
            errors.append(f"{key} must be a positive integer")
    if not isinstance(config.get("learning_rate"), (int, float)) or float(config.get("learning_rate")) <= 0:
        errors.append("learning_rate must be positive")
    return errors


def load_dataset_rows(config: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    dataset_dir = safe_project_path(str(config["dataset_dir"]))
    return (
        read_jsonl(dataset_dir / "train.jsonl"),
        read_jsonl(dataset_dir / "validation.jsonl"),
        read_jsonl(dataset_dir / "test.jsonl"),
    )


def base_result(args: argparse.Namespace, config: dict[str, Any], deps: dict[str, Any]) -> dict[str, Any]:
    adapter_path = safe_project_path(str(config.get("output_adapter_dir") or "local_artifacts/adapters/missing"))
    hardware = hardware_summary()
    return {
        "experiment_id": EXPERIMENT_ID,
        "generated_at": utc_now(),
        "status": "not_run",
        "config_path": rel(CONFIG_PATH),
        "config": config,
        "python_executable": sys.executable,
        "expected_python_environment": ".venv-llm",
        "expected_python_environment_active": in_expected_llm_env(),
        "dependency_status": deps,
        "dependency_install_attempted_by_script": False,
        "hardware_summary": hardware,
        "cuda_available": bool(hardware.get("cuda_available")),
        "gpu_name": hardware.get("gpu_name"),
        "dry_run_config_only": bool(args.dry_run_config_only),
        "training_attempted": False,
        "training_completed": False,
        "exact_blocker": None,
        "model_loaded": False,
        "adapter_saved": False,
        "adapter_path": rel(adapter_path),
        "adapter_files_committed": adapter_files_committed(),
        "train_row_count": 0,
        "validation_row_count": 0,
        "test_row_count": 0,
        "tokenization": {},
        "train_steps_completed": 0,
        "train_loss": None,
        "eval_loss": None,
        "peak_gpu_memory_bytes": None,
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
        f"- dry_run_config_only: {str(result.get('dry_run_config_only')).lower()}",
        f"- dependency_ready: {str((result.get('dependency_status') or {}).get('ready')).lower()}",
        f"- training_attempted: {str(result.get('training_attempted')).lower()}",
        f"- training_completed: {str(result.get('training_completed')).lower()}",
        f"- exact_blocker: {result.get('exact_blocker')}",
        f"- model_loaded: {str(result.get('model_loaded')).lower()}",
        f"- adapter_saved: {str(result.get('adapter_saved')).lower()}",
        f"- adapter_path: `{result.get('adapter_path')}`",
        f"- adapter_files_committed: {str(result.get('adapter_files_committed')).lower()}",
        f"- train_rows: {result.get('train_row_count')}",
        f"- validation_rows: {result.get('validation_row_count')}",
        f"- test_rows: {result.get('test_row_count')}",
        f"- train_steps_completed: {result.get('train_steps_completed')}",
        f"- train_loss: {result.get('train_loss')}",
        f"- eval_loss: {result.get('eval_loss')}",
        f"- peak_gpu_memory_bytes: {result.get('peak_gpu_memory_bytes')}",
        f"- provider_calls_made: {str(result.get('provider_calls_made')).lower()}",
        f"- openai_api_calls_made: {str(result.get('openai_api_calls_made')).lower()}",
        f"- live_tts_calls_made: {str(result.get('live_tts_calls_made')).lower()}",
        f"- runtime_behavior_changed: {str(result.get('runtime_behavior_changed')).lower()}",
        f"- response_text_changed: {str(result.get('response_text_changed')).lower()}",
        f"- raw_private_transcript_included: {str(result.get('raw_private_transcript_included')).lower()}",
        "",
        "## Tokenization",
        "",
        json.dumps(result.get("tokenization") or {}, indent=2, ensure_ascii=False),
        "",
        "## Dependency Notes",
        "",
        json.dumps(result.get("dependency_status") or {}, indent=2, ensure_ascii=False),
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
    return TrainingArguments(**kwargs)


def run_training(args: argparse.Namespace, config: dict[str, Any], result: dict[str, Any]) -> int:
    import torch  # type: ignore
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training  # type: ignore
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, Trainer  # type: ignore

    train_rows, validation_rows, test_rows = load_dataset_rows(config)
    result["train_row_count"] = len(train_rows)
    result["validation_row_count"] = len(validation_rows)
    result["test_row_count"] = len(test_rows)
    result["raw_private_transcript_included"] = any(
        row.get("raw_private_transcript_included") is not False
        for row in [*train_rows, *validation_rows, *test_rows]
    )
    if result["raw_private_transcript_included"]:
        raise RuntimeError("dataset includes raw private transcripts")

    model_path = safe_project_path(str(config["base_model_path"]))
    cache_dir = safe_project_path(str(config["cache_dir"]))
    output_adapter_dir = safe_project_path(str(config["output_adapter_dir"]))
    trainer_output_dir = output_adapter_dir / "trainer-output"
    tokenizer = AutoTokenizer.from_pretrained(
        str(model_path),
        cache_dir=str(cache_dir),
        local_files_only=True,
        trust_remote_code=False,
    )
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token

    train_tokenized = tokenize_rows(train_rows, tokenizer, int(config["max_seq_length"]))
    validation_tokenized = tokenize_rows(validation_rows, tokenizer, int(config["max_seq_length"]))
    result["tokenization"] = {
        "train": train_tokenized.stats,
        "validation": validation_tokenized.stats,
        "max_seq_length": int(config["max_seq_length"]),
    }
    if args.dry_run_config_only:
        result["status"] = "config_validated"
        result["notes"].append("Dry-run config validation completed without loading model weights.")
        persist(result)
        return 0

    result["training_attempted"] = True
    quantization_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
    )
    if torch.cuda.is_available():
        torch.cuda.reset_peak_memory_stats()
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
    if bool(config.get("gradient_checkpointing", True)):
        model.gradient_checkpointing_enable()
    model = prepare_model_for_kbit_training(model)
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
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=PlannerDataset(train_tokenized.rows),
        eval_dataset=PlannerDataset(validation_tokenized.rows),
        data_collator=make_collator(tokenizer),
    )
    train_output = trainer.train()
    eval_metrics = trainer.evaluate()
    output_adapter_dir.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(str(output_adapter_dir))
    tokenizer.save_pretrained(str(output_adapter_dir))

    result["training_completed"] = True
    result["status"] = "completed"
    result["adapter_saved"] = (output_adapter_dir / "adapter_config.json").is_file()
    result["train_steps_completed"] = int(getattr(trainer.state, "global_step", 0) or 0)
    result["train_loss"] = (
        float(train_output.metrics["train_loss"])
        if isinstance(getattr(train_output, "metrics", None), dict)
        and train_output.metrics.get("train_loss") is not None
        else None
    )
    result["eval_loss"] = float(eval_metrics["eval_loss"]) if eval_metrics.get("eval_loss") is not None else None
    result["peak_gpu_memory_bytes"] = int(torch.cuda.max_memory_allocated()) if torch.cuda.is_available() else None
    result["local_model_calls_made"] = True
    result["notes"].append("Adapter saved under ignored local_artifacts; no runtime wiring changed.")
    persist(result)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Local Qwen compact planner PEFT/QLoRA dry-run trainer.")
    parser.add_argument("--dry-run-config-only", action="store_true", help="Validate config, dataset, and tokenization only.")
    parser.add_argument("--max-steps", type=int, default=None, help="Override configured max_steps for this dry run.")
    parser.add_argument(
        "--skip-train-if-missing-deps",
        action="store_true",
        help="Write dependency evidence and exit 0 when required training dependencies are missing.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.max_steps is not None and args.max_steps <= 0:
        raise SystemExit("--max-steps must be positive")
    config = read_json(CONFIG_PATH)
    deps = dependency_status()
    result = base_result(args, config, deps)
    config_errors = validate_config(config)
    dataset = dataset_summary(config)
    result["dataset_summary"] = dataset
    result["train_row_count"] = dataset["splits"]["train"]["count"]
    result["validation_row_count"] = dataset["splits"]["validation"]["count"]
    result["test_row_count"] = dataset["splits"]["test"]["count"]
    result["raw_private_transcript_included"] = bool(dataset["raw_private_transcript_included"])

    if not in_expected_llm_env():
        result["status"] = "wrong_python_environment"
        result["exact_blocker"] = "Run with .venv-llm\\Scripts\\python.exe"
        persist(result)
        print(json.dumps({"status": result["status"], "exact_blocker": result["exact_blocker"]}, indent=2))
        return 1
    if config_errors:
        result["status"] = "config_invalid"
        result["exact_blocker"] = "; ".join(config_errors)
        persist(result)
        print(json.dumps({"status": result["status"], "errors": config_errors}, indent=2))
        return 1
    if not deps["ready"]:
        result["status"] = "dependency_missing"
        result["exact_blocker"] = "; ".join(deps.get("missing_required") or []) or (
            deps.get("peft_import_error") or deps.get("transformers_trainer_import_error") or "training dependency import failed"
        )
        persist(result)
        print(json.dumps({"status": result["status"], "dependency_status": deps}, indent=2))
        return 0 if args.skip_train_if_missing_deps else 1
    if not result["cuda_available"]:
        result["status"] = "gpu_missing"
        result["exact_blocker"] = "CUDA GPU is not available to torch"
        persist(result)
        print(json.dumps({"status": result["status"], "exact_blocker": result["exact_blocker"]}, indent=2))
        return 1

    try:
        code = run_training(args, config, result)
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
    except Exception as exc:
        result["status"] = "blocked"
        result["training_completed"] = False
        result["exact_blocker"] = f"{type(exc).__name__}: {exc}"
        result["traceback_excerpt"] = traceback.format_exc(limit=8)[-4000:]
        persist(result)
        print(json.dumps({"status": "blocked", "exact_blocker": result["exact_blocker"]}, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
