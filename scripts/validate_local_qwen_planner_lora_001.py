#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "runtime" / "llm_brain" / "training" / "qwen_qlora_planner_config.json"
TRAIN_SCRIPT = ROOT / "scripts" / "train_local_qwen_planner_lora_001.py"
EVAL_SCRIPT = ROOT / "scripts" / "evaluate_local_qwen_planner_lora_001.py"
TRAINING_EXPERIMENT_ID = "LOCAL-QWEN-QLORA-TRAINING-DRY-RUN-001"
EVAL_EXPERIMENT_ID = "LOCAL-QWEN-LORA-EVAL-001"
TRAINING_RESULT_PATH = ROOT / "research" / "experiments" / "generated" / TRAINING_EXPERIMENT_ID / "result.json"
TRAINING_REPORT_PATH = ROOT / "research" / "experiments" / "generated" / TRAINING_EXPERIMENT_ID / "report.md"
EVAL_RESULT_PATH = ROOT / "research" / "experiments" / "generated" / EVAL_EXPERIMENT_ID / "result.json"
EVAL_REPORT_PATH = ROOT / "research" / "experiments" / "generated" / EVAL_EXPERIMENT_ID / "report.md"
WEIGHT_SUFFIXES = (".safetensors", ".bin", ".gguf", ".pt", ".pth", ".ckpt")


BLOCKED_PROVIDER_PATTERNS = {
    "openai_import": "from openai",
    "openai_client": "openai.OpenAI",
    "openai_api_key": "OPENAI_API_KEY",
    "requests_post": "requests.post",
    "httpx_post": "httpx.post",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def safe_project_path(relative_path: str) -> Path:
    path = Path(relative_path)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"path must be project-relative: {relative_path!r}")
    return ROOT / path


def git_ls_files(prefix: str = "") -> list[str]:
    cmd = ["git", "ls-files"]
    if prefix:
        cmd.append(prefix)
    try:
        completed = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=10, check=False)
    except Exception:
        return []
    if completed.returncode != 0:
        return []
    return [line.strip().replace("\\", "/") for line in completed.stdout.splitlines() if line.strip()]


def tracked_model_or_adapter_weights() -> list[str]:
    return [path for path in git_ls_files() if path.lower().endswith(WEIGHT_SUFFIXES)]


def validate_no_provider_calls(failures: list[str]) -> None:
    for path in (TRAIN_SCRIPT, EVAL_SCRIPT):
        if not path.is_file():
            failures.append(f"missing script: {rel(path)}")
            continue
        text = path.read_text(encoding="utf-8")
        for label, pattern in BLOCKED_PROVIDER_PATTERNS.items():
            if pattern in text:
                failures.append(f"{rel(path)} contains blocked provider/API pattern: {label}")


def validate_config(failures: list[str]) -> dict[str, Any]:
    if not CONFIG_PATH.is_file():
        failures.append(f"missing config: {rel(CONFIG_PATH)}")
        return {}
    try:
        config = read_json(CONFIG_PATH)
    except json.JSONDecodeError as exc:
        failures.append(f"config invalid JSON: {exc}")
        return {}
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
    missing = sorted(required - set(config))
    if missing:
        failures.append(f"config missing field(s): {missing}")
    if config.get("base_model_id") != "Qwen/Qwen2.5-7B-Instruct":
        failures.append("config.base_model_id must be Qwen/Qwen2.5-7B-Instruct")
    if config.get("quantization") != "4bit":
        failures.append("config.quantization must be 4bit")
    if config.get("target") != "compact planner JSON":
        failures.append("config.target must be compact planner JSON")
    adapter_path = str(config.get("output_adapter_dir") or "")
    if not adapter_path.replace("\\", "/").startswith("local_artifacts/adapters/"):
        failures.append("config.output_adapter_dir must be under local_artifacts/adapters")
    for key in ("base_model_path", "dataset_dir", "output_adapter_dir", "cache_dir"):
        value = str(config.get(key) or "")
        try:
            safe_project_path(value)
        except ValueError as exc:
            failures.append(str(exc))
    return config


def validate_evidence_common(result: dict[str, Any], failures: list[str], label: str) -> None:
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
            failures.append(f"{label}.{key} must be false")
    if result.get("raw_private_transcript_included") is not False:
        failures.append(f"{label}.raw_private_transcript_included must be false")
    if result.get("adapter_files_committed") is not False:
        failures.append(f"{label}.adapter_files_committed must be false")


def validate_training_evidence(failures: list[str]) -> str:
    if not TRAINING_RESULT_PATH.exists() and not TRAINING_REPORT_PATH.exists():
        return "not_run"
    if not TRAINING_RESULT_PATH.is_file():
        failures.append(f"missing training result: {rel(TRAINING_RESULT_PATH)}")
        return "invalid"
    if not TRAINING_REPORT_PATH.is_file():
        failures.append(f"missing training report: {rel(TRAINING_REPORT_PATH)}")
    result = read_json(TRAINING_RESULT_PATH)
    if result.get("experiment_id") != TRAINING_EXPERIMENT_ID:
        failures.append("training experiment_id mismatch")
    allowed = {
        "not_run",
        "config_validated",
        "completed",
        "blocked",
        "dependency_missing",
        "gpu_missing",
        "model_missing",
        "wrong_python_environment",
        "config_invalid",
    }
    status = str(result.get("status") or "")
    if status not in allowed:
        failures.append(f"training status is not allowed: {status}")
    validate_evidence_common(result, failures, "training")
    for key in ("train_row_count", "validation_row_count", "test_row_count"):
        if not isinstance(result.get(key), int):
            failures.append(f"training.{key} must be an integer")
    if result.get("training_completed") is True:
        if result.get("adapter_saved") is not True:
            failures.append("training completed but adapter_saved is not true")
        if not isinstance(result.get("train_steps_completed"), int) or result.get("train_steps_completed") <= 0:
            failures.append("training completed but train_steps_completed is not positive")
    if status in {"blocked", "dependency_missing", "gpu_missing", "model_missing", "wrong_python_environment", "config_invalid"}:
        if not result.get("exact_blocker"):
            failures.append("training blocker status must include exact_blocker")
    return status


def validate_eval_evidence(failures: list[str]) -> str:
    if not EVAL_RESULT_PATH.exists() and not EVAL_REPORT_PATH.exists():
        return "not_run"
    if not EVAL_RESULT_PATH.is_file():
        failures.append(f"missing eval result: {rel(EVAL_RESULT_PATH)}")
        return "invalid"
    if not EVAL_REPORT_PATH.is_file():
        failures.append(f"missing eval report: {rel(EVAL_REPORT_PATH)}")
    result = read_json(EVAL_RESULT_PATH)
    if result.get("experiment_id") != EVAL_EXPERIMENT_ID:
        failures.append("eval experiment_id mismatch")
    allowed = {"not_run", "completed", "adapter_missing", "blocked", "dependency_missing"}
    status = str(result.get("status") or "")
    if status not in allowed:
        failures.append(f"eval status is not allowed: {status}")
    validate_evidence_common(result, failures, "eval")
    for key in ("validation_row_count", "test_row_count"):
        if not isinstance(result.get(key), int):
            failures.append(f"eval.{key} must be an integer")
    if status == "completed":
        for key in (
            "validation_schema_valid_count",
            "validation_verifier_pass_count",
            "validation_semantic_match_count",
            "test_schema_valid_count",
            "test_verifier_pass_count",
            "test_semantic_match_count",
        ):
            if not isinstance(result.get(key), int):
                failures.append(f"eval.{key} must be an integer after completed evaluation")
        if result.get("adapter_loaded") is not True:
            failures.append("eval completed but adapter_loaded is not true")
    if status == "adapter_missing" and result.get("local_model_calls_made") is not False:
        failures.append("adapter_missing eval must not make local model calls")
    if status in {"blocked", "dependency_missing"} and not result.get("exact_blocker"):
        failures.append("eval blocker status must include exact_blocker")
    return status


def main() -> int:
    failures: list[str] = []
    config = validate_config(failures)
    validate_no_provider_calls(failures)
    tracked_weights = tracked_model_or_adapter_weights()
    if tracked_weights:
        failures.append(f"model/adapter weights are tracked by git: {tracked_weights}")
    local_artifacts_tracked = git_ls_files("local_artifacts")
    if local_artifacts_tracked:
        failures.append(f"local_artifacts contains tracked files: {local_artifacts_tracked}")
    adapter_path = ""
    if config:
        adapter_path = str(config.get("output_adapter_dir") or "")
        try:
            resolved = safe_project_path(adapter_path)
            if adapter_path and adapter_path.replace("\\", "/").startswith("local_artifacts/"):
                pass
            else:
                failures.append("adapter path is not under ignored local_artifacts")
            if (resolved / "adapter_model.safetensors").is_file() and str(resolved).startswith(str(ROOT)):
                pass
        except ValueError:
            pass
    training_status = validate_training_evidence(failures)
    eval_status = validate_eval_evidence(failures)
    checks = {
        "training_script_exists": TRAIN_SCRIPT.is_file(),
        "eval_script_exists": EVAL_SCRIPT.is_file(),
        "config_exists": CONFIG_PATH.is_file(),
        "adapter_output_path_ignored": bool(adapter_path.replace("\\", "/").startswith("local_artifacts/adapters/")),
        "no_adapter_or_model_weights_committed": not tracked_weights and not local_artifacts_tracked,
        "training_evidence_status_allowed": training_status not in {"invalid"},
        "eval_evidence_status_allowed": eval_status not in {"invalid"},
        "provider_openai_tts_false_in_evidence": not any("provider" in failure or "openai" in failure or "tts" in failure for failure in failures),
        "runtime_behavior_changed_false": not any("runtime_behavior_changed" in failure for failure in failures),
        "response_text_changed_false": not any("response_text_changed" in failure for failure in failures),
        "no_raw_private_transcripts": not any("raw_private" in failure for failure in failures),
    }
    validation = {
        "experiment_id": "LOCAL-QWEN-PLANNER-LORA-VALIDATION-001",
        "validated_at": utc_now(),
        "status": "pass" if not failures else "fail",
        "training_status": training_status,
        "eval_status": eval_status,
        "checks": checks,
        "failures": failures,
    }
    print(json.dumps(validation, indent=2, ensure_ascii=False))
    if failures:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
