#!/usr/bin/env python3
from __future__ import annotations

import argparse
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
    render_eval_chat,
    render_train_chat,
    tokenize_rows_assistant_only,
)


EXPERIMENT_ID = "LOCAL-QWEN-LORA-CURRICULUM-TRAINING-001"
DATASET_EXPERIMENT_ID = "LOCAL-QWEN-CURRICULUM-DATASET-001"
CONFIG_PATH = ROOT / "runtime" / "llm_brain" / "training" / "qwen_lora_curriculum_planner_config.json"
DATASET_DIR = ROOT / "research" / "experiments" / "generated" / DATASET_EXPERIMENT_ID
OUT_DIR = ROOT / "research" / "experiments" / "generated" / EXPERIMENT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"
DEFAULT_ADAPTER_PATH = "local_artifacts/adapters/qwen2.5-sales-brain-lora-curriculum-001"
STAGE_ORDER = ("tiny", "20", "60")
STAGE_FILES = {
    "tiny": DATASET_DIR / "stage1_tiny.jsonl",
    "20": DATASET_DIR / "stage2_20.jsonl",
    "60": DATASET_DIR / "stage3_60.jsonl",
}
DEFAULT_STAGE_STEPS = {"tiny": 30, "20": 75, "60": 150}


def load_curriculum_config() -> dict[str, Any]:
    payload = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"curriculum config must be an object: {rel(CONFIG_PATH)}")
    payload.setdefault("batch_size", payload.get("per_device_train_batch_size", 1))
    payload.setdefault("curriculum_dataset_dir", f"research/experiments/generated/{DATASET_EXPERIMENT_ID}")
    return payload


CURRICULUM_CONFIG = load_curriculum_config()


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


def selected_stages(stage: str) -> list[str]:
    return list(STAGE_ORDER) if stage == "all" else [stage]


def stage_steps(stage: str, max_steps_override: int | None) -> int:
    return int(max_steps_override or DEFAULT_STAGE_STEPS[stage])


def validate_config(config: dict[str, Any], stages: list[str], adapter_path: Path, resume_path: str | None) -> list[str]:
    errors: list[str] = []
    if config.get("base_model_id") != PRIMARY_MODEL_ID:
        errors.append(f"base_model_id must be {PRIMARY_MODEL_ID}")
    if config.get("quantization") != "4bit":
        errors.append("quantization must be 4bit")
    if config.get("target") != "compact planner JSON":
        errors.append("target must be compact planner JSON")
    if config.get("device") != "cuda":
        errors.append("device must be cuda")
    for key in ("base_model_path", "dataset_dir", "cache_dir"):
        value = str(config.get(key) or "")
        try:
            path = safe_project_path(value)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        if key == "base_model_path" and not path.is_dir():
            errors.append(f"base_model_path does not exist: {value}")
        if key == "dataset_dir" and not path.is_dir():
            errors.append(f"dataset_dir does not exist: {value}")
    if not str(config.get("output_adapter_dir") or "").replace("\\", "/").startswith("local_artifacts/adapters/"):
        errors.append("output_adapter_dir must stay under local_artifacts/adapters")
    if not str(adapter_path.relative_to(ROOT)).replace("\\", "/").startswith("local_artifacts/adapters/"):
        errors.append("resolved output_adapter_dir must stay under local_artifacts/adapters")
    for stage in stages:
        if stage not in STAGE_FILES:
            errors.append(f"unknown stage: {stage}")
        elif not STAGE_FILES[stage].is_file():
            errors.append(f"stage dataset missing: {rel(STAGE_FILES[stage])}")
    if resume_path:
        resume = safe_project_path(resume_path)
        if not (resume / "adapter_config.json").is_file():
            errors.append(f"resume adapter missing adapter_config.json: {resume_path}")
    for key in ("max_seq_length", "batch_size", "gradient_accumulation_steps", "eval_steps", "lora_r"):
        if not isinstance(config.get(key), int) or int(config.get(key)) <= 0:
            errors.append(f"{key} must be a positive integer")
    if not isinstance(config.get("learning_rate"), (int, float)) or float(config["learning_rate"]) <= 0:
        errors.append("learning_rate must be positive")
    return errors


def base_result(args: argparse.Namespace, config: dict[str, Any], deps: dict[str, Any]) -> dict[str, Any]:
    adapter_path = safe_project_path(args.output_adapter_dir)
    stages = selected_stages(args.stage)
    return {
        "experiment_id": EXPERIMENT_ID,
        "generated_at": utc_now(),
        "status": "not_run",
        "dataset_experiment_id": DATASET_EXPERIMENT_ID,
        "config": config,
        "stage": args.stage,
        "selected_stages": stages,
        "stage_default_steps": DEFAULT_STAGE_STEPS,
        "max_steps_override": args.max_steps,
        "resume_from_adapter": args.resume_from_adapter,
        "output_adapter_dir": rel(adapter_path),
        "adapter_path": rel(adapter_path),
        "python_executable": sys.executable,
        "expected_python_environment": ".venv-llm",
        "expected_python_environment_active": in_expected_llm_env(),
        "dependency_status": deps,
        "hardware_summary": hardware_summary(),
        "cuda_available": bool(hardware_summary().get("cuda_available")),
        "dry_run_config_only": bool(args.dry_run_config_only),
        "skip_train_if_missing_deps": bool(args.skip_train_if_missing_deps),
        "overwrite_adapter": bool(args.overwrite_adapter),
        "training_attempted": False,
        "training_completed": False,
        "completed_stages": [],
        "stage_results": [],
        "train_steps_by_stage": {},
        "train_losses_by_stage": {},
        "eval_losses_by_stage": {},
        "tokenization_by_stage": {},
        "train_row_counts_by_stage": {},
        "exact_blocker": None,
        "blocker_classification": None,
        "model_loaded": False,
        "adapter_saved": False,
        "adapter_files_committed": adapter_files_committed(),
        "peak_gpu_memory_bytes": None,
        "train_runtime_seconds": None,
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
        "adapter_live_ready": False,
        "quality_gate_passed": False,
        "notes": [],
    }


def write_report(result: dict[str, Any]) -> None:
    lines = [
        f"# {EXPERIMENT_ID}",
        "",
        f"- status: {result.get('status')}",
        f"- training_attempted: {str(result.get('training_attempted')).lower()}",
        f"- training_completed: {str(result.get('training_completed')).lower()}",
        f"- completed_stages: {', '.join(result.get('completed_stages') or [])}",
        f"- exact_blocker: {result.get('exact_blocker')}",
        f"- blocker_classification: {result.get('blocker_classification')}",
        f"- adapter_path: `{result.get('adapter_path')}`",
        f"- adapter_saved: {str(result.get('adapter_saved')).lower()}",
        f"- adapter_files_committed: {str(result.get('adapter_files_committed')).lower()}",
        f"- train_runtime_seconds: {result.get('train_runtime_seconds')}",
        f"- peak_gpu_memory_bytes: {result.get('peak_gpu_memory_bytes')}",
        f"- provider_calls_made: {str(result.get('provider_calls_made')).lower()}",
        f"- openai_api_calls_made: {str(result.get('openai_api_calls_made')).lower()}",
        f"- live_tts_calls_made: {str(result.get('live_tts_calls_made')).lower()}",
        f"- runtime_behavior_changed: {str(result.get('runtime_behavior_changed')).lower()}",
        f"- response_text_changed: {str(result.get('response_text_changed')).lower()}",
        f"- adapter_live_ready: {str(result.get('adapter_live_ready')).lower()}",
        f"- quality_gate_passed: {str(result.get('quality_gate_passed')).lower()}",
        "",
        "## Stage Results",
        "",
        json.dumps(result.get("stage_results") or [], indent=2, ensure_ascii=False),
        "",
        "## Tokenization",
        "",
        json.dumps(result.get("tokenization_by_stage") or {}, indent=2, ensure_ascii=False),
    ]
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def persist(result: dict[str, Any]) -> None:
    result["adapter_files_committed"] = adapter_files_committed()
    write_json(RESULT_PATH, result)
    write_report(result)


def load_tokenizer_and_model(config: dict[str, Any], resume_from_adapter: str | None) -> tuple[Any, Any]:
    import torch  # type: ignore
    from peft import LoraConfig, PeftModel, get_peft_model, prepare_model_for_kbit_training  # type: ignore
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
    model.config.use_cache = False
    use_gradient_checkpointing = bool(config.get("gradient_checkpointing", True))
    if use_gradient_checkpointing:
        model.gradient_checkpointing_enable()
    prepare_kwargs: dict[str, Any] = {}
    if "use_gradient_checkpointing" in inspect.signature(prepare_model_for_kbit_training).parameters:
        prepare_kwargs["use_gradient_checkpointing"] = use_gradient_checkpointing
    model = prepare_model_for_kbit_training(model, **prepare_kwargs)
    if resume_from_adapter:
        model = PeftModel.from_pretrained(model, str(safe_project_path(resume_from_adapter)), local_files_only=True, is_trainable=True)
    else:
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
    return model, tokenizer


def train_stage(
    *,
    stage: str,
    model: Any,
    tokenizer: Any,
    config: dict[str, Any],
    max_steps: int,
    adapter_path: Path,
) -> dict[str, Any]:
    import torch  # type: ignore
    from transformers import Trainer  # type: ignore

    rows = read_jsonl(STAGE_FILES[stage])
    tokenized = tokenize_rows_assistant_only(rows, tokenizer, int(config["max_seq_length"]))
    trainer_output_dir = adapter_path / "trainer-output" / stage
    stage_config = dict(config)
    stage_config["max_steps"] = max_steps
    training_args = build_training_arguments(stage_config, max_steps, trainer_output_dir)
    dataset = PlannerDataset(tokenized.rows)
    started = time.perf_counter()
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=dataset,
        eval_dataset=dataset,
        data_collator=make_collator(tokenizer),
    )
    train_output = trainer.train()
    eval_metrics = trainer.evaluate()
    adapter_path.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(str(adapter_path))
    tokenizer.save_pretrained(str(adapter_path))
    return {
        "stage": stage,
        "row_count": len(rows),
        "max_steps": max_steps,
        "global_step": int(getattr(trainer.state, "global_step", 0) or 0),
        "train_loss": (
            float(train_output.metrics["train_loss"])
            if isinstance(getattr(train_output, "metrics", None), dict)
            and train_output.metrics.get("train_loss") is not None
            else None
        ),
        "eval_loss": float(eval_metrics["eval_loss"]) if eval_metrics.get("eval_loss") is not None else None,
        "runtime_seconds": round(time.perf_counter() - started, 3),
        "tokenization": tokenized.stats,
        "adapter_saved_after_stage": (adapter_path / "adapter_config.json").is_file(),
        "peak_gpu_memory_bytes_after_stage": int(torch.cuda.max_memory_allocated()) if torch.cuda.is_available() else None,
    }


def run_training(args: argparse.Namespace, result: dict[str, Any], config: dict[str, Any]) -> int:
    import torch  # type: ignore

    adapter_path = safe_project_path(args.output_adapter_dir)
    if adapter_path.exists() and not args.resume_from_adapter:
        if not args.overwrite_adapter:
            raise FileExistsError(f"adapter path already exists: {rel(adapter_path)}")
        result["notes"].append(
            "Existing adapter directory retained for Windows-safe overwrite; model is loaded from base and adapter files are overwritten at stage saves."
        )
    if torch.cuda.is_available():
        torch.cuda.reset_peak_memory_stats()
    result["training_attempted"] = True
    started = time.perf_counter()
    model, tokenizer = load_tokenizer_and_model(config, args.resume_from_adapter)
    result["model_loaded"] = True
    result["local_model_calls_made"] = True
    raw_private = False
    for stage in result["selected_stages"]:
        rows = read_jsonl(STAGE_FILES[stage])
        raw_private = raw_private or any(row.get("raw_private_transcript_included") is not False for row in rows)
        steps = stage_steps(stage, args.max_steps)
        stage_result = train_stage(
            stage=stage,
            model=model,
            tokenizer=tokenizer,
            config=config,
            max_steps=steps,
            adapter_path=adapter_path,
        )
        result["stage_results"].append(stage_result)
        result["completed_stages"].append(stage)
        result["train_steps_by_stage"][stage] = stage_result["global_step"]
        result["train_losses_by_stage"][stage] = stage_result["train_loss"]
        result["eval_losses_by_stage"][stage] = stage_result["eval_loss"]
        result["tokenization_by_stage"][stage] = stage_result["tokenization"]
        result["train_row_counts_by_stage"][stage] = stage_result["row_count"]
        result["adapter_saved"] = bool(stage_result["adapter_saved_after_stage"])
        persist(result)
    result["raw_private_transcript_included"] = raw_private
    result["training_completed"] = result["completed_stages"] == result["selected_stages"]
    result["status"] = "completed" if result["training_completed"] else "partial"
    result["train_runtime_seconds"] = round(time.perf_counter() - started, 3)
    result["peak_gpu_memory_bytes"] = int(torch.cuda.max_memory_allocated()) if torch.cuda.is_available() else None
    result["notes"].append("Curriculum adapter saved under ignored local_artifacts; no runtime wiring changed.")
    persist(result)
    return 0


def classify_training_blocker(exc: Exception) -> str:
    text = f"{type(exc).__name__}: {exc}".lower()
    if "out of memory" in text or ("cuda" in text and "memory" in text):
        return "Python/Windows training issue"
    if "adapter path already exists" in text:
        return "adapter path already exists"
    if "no assistant target tokens" in text:
        return "labels not masked correctly"
    if "does not exist" in text:
        return "Python/Windows training issue"
    return "Python/Windows training issue"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Train staged local Qwen compact-planner curriculum LoRA.")
    parser.add_argument("--stage", choices=["tiny", "20", "60", "all"], default="all")
    parser.add_argument("--max-steps", type=int, default=None, help="Override max steps for each selected stage.")
    parser.add_argument("--resume-from-adapter", default=None, help="Project-relative adapter path to resume from.")
    parser.add_argument("--output-adapter-dir", default=DEFAULT_ADAPTER_PATH)
    parser.add_argument("--dry-run-config-only", action="store_true")
    parser.add_argument("--skip-train-if-missing-deps", action="store_true")
    parser.add_argument("--overwrite-adapter", action="store_true", help="Delete existing output adapter before training.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.max_steps is not None and args.max_steps <= 0:
        raise SystemExit("--max-steps must be positive")
    config = dict(CURRICULUM_CONFIG)
    config["output_adapter_dir"] = args.output_adapter_dir
    stages = selected_stages(args.stage)
    deps = dependency_status()
    result = base_result(args, config, deps)
    config_errors = validate_config(config, stages, safe_project_path(args.output_adapter_dir), args.resume_from_adapter)
    dataset_result = read_json(DATASET_DIR / "result.json")
    result["dataset_status"] = dataset_result.get("status")
    result["curriculum_stage_counts"] = (dataset_result.get("counts") if isinstance(dataset_result.get("counts"), dict) else {})
    result["held_out_contamination"] = dataset_result.get("held_out_contamination")
    if not in_expected_llm_env():
        result["status"] = "wrong_python_environment"
        result["exact_blocker"] = "Run with .venv-llm\\Scripts\\python.exe"
        persist(result)
        print(json.dumps({"status": result["status"], "exact_blocker": result["exact_blocker"]}, indent=2))
        return 1
    if dataset_result.get("status") != "pass":
        config_errors.append("curriculum dataset status is not pass")
    if config_errors:
        result["status"] = "config_invalid"
        result["exact_blocker"] = "; ".join(config_errors)
        result["blocker_classification"] = "Python/Windows training issue"
        persist(result)
        print(json.dumps({"status": result["status"], "errors": config_errors}, indent=2))
        return 1
    tokenizer = None
    try:
        from transformers import AutoTokenizer  # type: ignore

        tokenizer = AutoTokenizer.from_pretrained(
            str(safe_project_path(str(config["base_model_path"]))),
            cache_dir=str(safe_project_path(str(config["cache_dir"]))),
            local_files_only=True,
            trust_remote_code=False,
        )
        if tokenizer.pad_token_id is None:
            tokenizer.pad_token = tokenizer.eos_token
        result["dry_run_tokenization_by_stage"] = {
            stage: tokenize_rows_assistant_only(read_jsonl(STAGE_FILES[stage]), tokenizer, int(config["max_seq_length"])).stats
            for stage in stages
        }
    except Exception as exc:
        result["status"] = "config_invalid"
        result["exact_blocker"] = f"{type(exc).__name__}: {exc}"
        result["blocker_classification"] = "Python/Windows training issue"
        persist(result)
        print(json.dumps({"status": result["status"], "exact_blocker": result["exact_blocker"]}, indent=2))
        return 1
    if args.dry_run_config_only:
        result["status"] = "dry_run_pass"
        persist(result)
        print(json.dumps({"status": result["status"], "stages": stages, "tokenization": result["dry_run_tokenization_by_stage"]}, indent=2))
        return 0
    if not deps.get("ready"):
        result["status"] = "dependency_missing"
        result["exact_blocker"] = "; ".join(deps.get("missing_required") or []) or "training dependency import failed"
        result["blocker_classification"] = "Python/Windows training issue"
        persist(result)
        print(json.dumps({"status": result["status"], "exact_blocker": result["exact_blocker"]}, indent=2))
        return 0 if args.skip_train_if_missing_deps else 1
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
                    "completed_stages": result["completed_stages"],
                    "adapter_saved": result["adapter_saved"],
                    "adapter_path": result["adapter_path"],
                    "train_steps_by_stage": result["train_steps_by_stage"],
                    "train_losses_by_stage": result["train_losses_by_stage"],
                    "eval_losses_by_stage": result["eval_losses_by_stage"],
                },
                indent=2,
            )
        )
        return code
    except KeyboardInterrupt:
        result["status"] = "interrupted"
        result["training_completed"] = False
        result["exact_blocker"] = "KeyboardInterrupt: training interrupted"
        result["blocker_classification"] = "Python/Windows training issue"
        result["train_runtime_seconds"] = result.get("train_runtime_seconds")
        persist(result)
        print(json.dumps({"status": result["status"], "completed_stages": result["completed_stages"]}, indent=2))
        return 130
    except Exception as exc:
        result["status"] = "blocked"
        result["training_completed"] = False
        result["exact_blocker"] = f"{type(exc).__name__}: {exc}"
        result["blocker_classification"] = classify_training_blocker(exc)
        result["traceback_excerpt"] = traceback.format_exc(limit=8)[-4000:]
        persist(result)
        print(json.dumps({"status": result["status"], "exact_blocker": result["exact_blocker"]}, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
