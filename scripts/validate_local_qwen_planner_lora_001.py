#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.llm_brain.compact_planner_contract import (  # noqa: E402
    COMPACT_VALUE_CONTRACT_VERSION,
    allowed_values_for,
    validate_compact_value_contract,
)
from scripts.train_local_qwen_planner_lora_001 import chat_messages  # noqa: E402

CONFIG_PATH = ROOT / "runtime" / "llm_brain" / "training" / "qwen_qlora_planner_config.json"
TRAIN_SCRIPT = ROOT / "scripts" / "train_local_qwen_planner_lora_001.py"
EVAL_SCRIPT = ROOT / "scripts" / "evaluate_local_qwen_planner_lora_001.py"
TRAINING_EXPERIMENT_ID = "LOCAL-QWEN-QLORA-TRAINING-DRY-RUN-001"
EVAL_EXPERIMENT_ID = "LOCAL-QWEN-LORA-EVAL-001"
SFT_EXPERIMENT_ID = "LOCAL-QWEN-SFT-DATASET-001"
TRAINING_RESULT_PATH = ROOT / "research" / "experiments" / "generated" / TRAINING_EXPERIMENT_ID / "result.json"
TRAINING_REPORT_PATH = ROOT / "research" / "experiments" / "generated" / TRAINING_EXPERIMENT_ID / "report.md"
EVAL_RESULT_PATH = ROOT / "research" / "experiments" / "generated" / EVAL_EXPERIMENT_ID / "result.json"
EVAL_REPORT_PATH = ROOT / "research" / "experiments" / "generated" / EVAL_EXPERIMENT_ID / "report.md"
SFT_RESULT_PATH = ROOT / "research" / "experiments" / "generated" / SFT_EXPERIMENT_ID / "result.json"
SFT_SPLIT_PATHS = {
    "train": ROOT / "research" / "experiments" / "generated" / SFT_EXPERIMENT_ID / "train.jsonl",
    "validation": ROOT / "research" / "experiments" / "generated" / SFT_EXPERIMENT_ID / "validation.jsonl",
    "test": ROOT / "research" / "experiments" / "generated" / SFT_EXPERIMENT_ID / "test.jsonl",
}
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


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        payload = json.loads(stripped)
        if not isinstance(payload, dict):
            raise ValueError(f"{rel(path)} line {line_number} must contain a JSON object")
        rows.append(payload)
    return rows


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


def prompt_contains_active_allowed_values(prompt_text: str) -> bool:
    if "Allowed compact semantic labels:" not in prompt_text:
        return False
    for field_name in ("act", "sub", "action", "strategy"):
        if f"- {field_name}:" not in prompt_text:
            return False
        for value in allowed_values_for(field_name):
            if value not in prompt_text:
                return False
    return True


def load_dataset_rows(failures: list[str]) -> dict[str, list[dict[str, Any]]]:
    rows_by_split: dict[str, list[dict[str, Any]]] = {}
    for split_name, path in SFT_SPLIT_PATHS.items():
        if not path.is_file():
            failures.append(f"missing SFT split file: {rel(path)}")
            rows_by_split[split_name] = []
            continue
        try:
            rows_by_split[split_name] = read_jsonl(path)
        except Exception as exc:
            failures.append(f"SFT split {split_name} invalid: {type(exc).__name__}: {exc}")
            rows_by_split[split_name] = []
    return rows_by_split


def validate_dataset_contract_alignment(rows_by_split: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    if not SFT_RESULT_PATH.is_file():
        failures.append(f"missing SFT dataset result: {rel(SFT_RESULT_PATH)}")
        return
    dataset_result = read_json(SFT_RESULT_PATH)
    if dataset_result.get("compact_value_contract_version") != COMPACT_VALUE_CONTRACT_VERSION:
        failures.append(
            "SFT dataset contract version mismatch: "
            f"{dataset_result.get('compact_value_contract_version')} != {COMPACT_VALUE_CONTRACT_VERSION}"
        )
    for split_name, rows in rows_by_split.items():
        for index, row in enumerate(rows, start=1):
            if row.get("compact_value_contract_version") != COMPACT_VALUE_CONTRACT_VERSION:
                failures.append(f"SFT {split_name}[{index}] compact_value_contract_version mismatch")
            target = row.get("target_compact_json")
            if isinstance(target, dict):
                for error in validate_compact_value_contract(target):
                    failures.append(f"SFT {split_name}[{index}] target violates active compact contract: {error}")


def validate_prompt_alignment(
    rows_by_split: dict[str, list[dict[str, Any]]],
    result: dict[str, Any],
    failures: list[str],
) -> None:
    sample_rows = [row for rows in rows_by_split.values() for row in rows[:1]]
    dataset_prompts = [str(row.get("prompt") or "") for row in sample_rows]
    eval_prompts = ["\n".join(message["content"] for message in chat_messages(row, include_target=False)) for row in sample_rows]
    if not dataset_prompts or not all(prompt_contains_active_allowed_values(prompt) for prompt in dataset_prompts):
        failures.append("SFT dataset prompt omits active compact allowed values")
    if not eval_prompts or not all(prompt_contains_active_allowed_values(prompt) for prompt in eval_prompts):
        failures.append("eval prompt omits active compact allowed values")
    prompt_alignment = result.get("prompt_alignment") if isinstance(result.get("prompt_alignment"), dict) else {}
    if prompt_alignment:
        if prompt_alignment.get("dataset_prompt_has_allowed_values") is not True:
            failures.append("eval evidence prompt_alignment.dataset_prompt_has_allowed_values must be true")
        if prompt_alignment.get("eval_prompt_has_allowed_values") is not True:
            failures.append("eval evidence prompt_alignment.eval_prompt_has_allowed_values must be true")
        if prompt_alignment.get("training_eval_contract_versions_match") is not True:
            failures.append("eval evidence prompt_alignment.training_eval_contract_versions_match must be true")
    if result.get("training_contract_version") != COMPACT_VALUE_CONTRACT_VERSION:
        failures.append("eval.training_contract_version must match active compact contract")
    if result.get("eval_contract_version") != COMPACT_VALUE_CONTRACT_VERSION:
        failures.append("eval.eval_contract_version must match active compact contract")
    if result.get("adapter_evaluated_path") != result.get("adapter_path"):
        failures.append("eval.adapter_evaluated_path must equal adapter_path")


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
            "validation_strict_gold_semantic_match_count",
            "validation_strict_gold_response_plan_match_count",
            "validation_compact_contract_valid_count",
            "test_schema_valid_count",
            "test_verifier_pass_count",
            "test_semantic_match_count",
            "test_strict_gold_semantic_match_count",
            "test_strict_gold_response_plan_match_count",
            "test_compact_contract_valid_count",
        ):
            if not isinstance(result.get(key), int):
                failures.append(f"eval.{key} must be an integer after completed evaluation")
        if result.get("adapter_loaded") is not True:
            failures.append("eval completed but adapter_loaded is not true")
        if result.get("adapter_evaluated_path") != result.get("adapter_path"):
            failures.append("eval completed but adapter_evaluated_path does not match adapter_path")
        if result.get("adapter_quality_status") not in {"pass", "fail", "not_ready"}:
            failures.append("eval.adapter_quality_status must be pass, fail, or not_ready")
        if not isinstance(result.get("quality_gate_passed"), bool):
            failures.append("eval.quality_gate_passed must be boolean")
        if not isinstance(result.get("evidence_integrity_passed"), bool):
            failures.append("eval.evidence_integrity_passed must be boolean")
        if not isinstance(result.get("adapter_live_ready"), bool):
            failures.append("eval.adapter_live_ready must be boolean")
        metrics = result.get("adapter_metrics") if isinstance(result.get("adapter_metrics"), dict) else {}
        cases = result.get("cases") if isinstance(result.get("cases"), list) else []
        quality_failures: list[str] = []
        for split_name in ("validation", "test"):
            split_metrics = metrics.get(split_name) if isinstance(metrics.get(split_name), dict) else {}
            case_count = int(split_metrics.get("case_count") or 0)
            if case_count <= 0:
                failures.append(f"eval.{split_name}.case_count must be positive")
            if int(split_metrics.get("schema_valid_count") or 0) != case_count:
                quality_failures.append(f"{split_name}.schema_valid_count")
            if int(split_metrics.get("verifier_pass_count") or 0) != case_count:
                quality_failures.append(f"{split_name}.verifier_pass_count")
            if int(split_metrics.get("compact_contract_valid_count") or 0) != case_count:
                quality_failures.append(f"{split_name}.compact_contract_valid_count")
            if int(split_metrics.get("strict_gold_semantic_match_count") or 0) != case_count:
                quality_failures.append(f"{split_name}.strict_gold_semantic_match_count")
            if int(split_metrics.get("deprecated_label_count") or 0) != 0:
                quality_failures.append(f"{split_name}.deprecated_label_count")
            if int(split_metrics.get("case_id_label_leak_count") or 0) != 0:
                quality_failures.append(f"{split_name}.case_id_label_leak_count")
            if int(split_metrics.get("generic_action_count") or 0) != 0:
                quality_failures.append(f"{split_name}.generic_action_count")
            if int(split_metrics.get("generic_sub_intent_count") or 0) != 0:
                quality_failures.append(f"{split_name}.generic_sub_intent_count")
            if int(split_metrics.get("generic_act_count") or 0) != 0:
                quality_failures.append(f"{split_name}.generic_act_count")
            if split_metrics.get("semantic_match_count") != split_metrics.get("strict_gold_semantic_match_count"):
                failures.append(f"eval.{split_name}.semantic_match_count must equal strict_gold_semantic_match_count")
        if quality_failures:
            if result.get("quality_gate_passed") is not False:
                failures.append("eval.quality_gate_passed must be false when quality metrics fail")
            if result.get("adapter_live_ready") is not False:
                failures.append("eval.adapter_live_ready must be false when quality metrics fail")
            if result.get("adapter_quality_status") not in {"not_ready", "fail"}:
                failures.append("eval.adapter_quality_status must be not_ready or fail when quality metrics fail")
            reported_failures = result.get("quality_gate_failures") if isinstance(result.get("quality_gate_failures"), list) else []
            if not reported_failures:
                failures.append("eval.quality_gate_failures must list failed quality metrics")
        elif result.get("quality_gate_passed") is not True:
            failures.append("eval.quality_gate_passed must be true when all quality metrics pass")
        if cases and result.get("compact_contract_failure_count") != sum(
            1 for case in cases if isinstance(case, dict) and case.get("compact_contract_valid") is not True
        ):
            failures.append("eval.compact_contract_failure_count is inconsistent with cases")
        if cases and result.get("strict_gold_semantic_failure_count") != sum(
            1 for case in cases if isinstance(case, dict) and case.get("gold_section_semantic_match") is not True
        ):
            failures.append("eval.strict_gold_semantic_failure_count is inconsistent with cases")
        if int(result.get("compact_contract_failure_count") or 0) > 0:
            if not result.get("adapter_contract_error_examples"):
                failures.append("eval.adapter_contract_error_examples must list compact contract failures")
            if not result.get("adapter_invalid_label_examples"):
                failures.append("eval.adapter_invalid_label_examples must list invalid labels")
        for case in cases:
            if not isinstance(case, dict):
                continue
            case_id = case.get("case_id")
            if case.get("verifier_pass") is True and case.get("gold_section_semantic_match") is not True:
                if case.get("semantic_match") is True:
                    failures.append(f"eval case {case_id} counts semantic_match despite gold-section failure")
            if case.get("verifier_pass") is not True:
                failure_classes = case.get("failure_classes") if isinstance(case.get("failure_classes"), list) else []
                verifier_errors = case.get("verifier_errors") if isinstance(case.get("verifier_errors"), list) else []
                if verifier_errors and "verifier" not in failure_classes:
                    failures.append(f"eval case {case_id} verifier failure is not explicitly classified")
            if case.get("compact_contract_valid") is not True:
                failure_classes = case.get("failure_classes") if isinstance(case.get("failure_classes"), list) else []
                if "compact_contract" not in failure_classes:
                    failures.append(f"eval case {case_id} compact contract failure is not explicitly classified")
        if result.get("evidence_integrity_passed") is not True:
            failures.append("eval.evidence_integrity_passed must be true for completed honest diagnostic evidence")
    if status == "adapter_missing" and result.get("local_model_calls_made") is not False:
        failures.append("adapter_missing eval must not make local model calls")
    if status in {"blocked", "dependency_missing"} and not result.get("exact_blocker"):
        failures.append("eval blocker status must include exact_blocker")
    return status


def main() -> int:
    failures: list[str] = []
    config = validate_config(failures)
    validate_no_provider_calls(failures)
    sft_rows = load_dataset_rows(failures)
    validate_dataset_contract_alignment(sft_rows, failures)
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
    if EVAL_RESULT_PATH.is_file():
        try:
            validate_prompt_alignment(sft_rows, read_json(EVAL_RESULT_PATH), failures)
        except Exception as exc:
            failures.append(f"prompt alignment validation failed: {type(exc).__name__}: {exc}")
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
        "dataset_targets_match_active_contract": not any("target violates active compact contract" in failure for failure in failures),
        "training_eval_prompt_contract_aligned": not any("prompt" in failure.lower() or "contract version" in failure for failure in failures),
        "quality_gate_separate_from_evidence_integrity": eval_status != "completed"
        or not any("schema_valid_count must equal" in failure or "compact_contract_valid_count must equal" in failure for failure in failures),
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
