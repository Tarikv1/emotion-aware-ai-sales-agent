#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.llm_brain.compact_planner_contract import (  # noqa: E402
    COMPACT_VALUE_CONTRACT_VERSION,
    compact_label_quality_issues,
    validate_compact_value_contract,
)
from runtime.llm_brain.conversation_brain_schema import (  # noqa: E402
    COMPACT_PLANNER_SCHEMA_MODE,
    expand_compact_planner_output,
    validate_compact_conversation_brain_output,
)
from runtime.llm_brain.conversation_brain_verifier import verify_conversation_brain_output  # noqa: E402
from scripts.train_local_qwen_planner_lora_001 import (  # noqa: E402
    read_jsonl,
    rel,
    safe_project_path,
    target_json_text,
)
from scripts.train_local_qwen_planner_lora_tiny_overfit_001 import (  # noqa: E402
    DATASET_EXPERIMENT_ID,
    TINY_ADAPTER_PATH,
    TINY_CONFIG,
    TRAIN_PATH,
    render_eval_chat,
    render_train_chat,
    tiny_chat_messages,
    tokenize_rows_assistant_only,
)


EXPERIMENT_ID = "LOCAL-QWEN-LORA-TRAINING-PIPELINE-AUDIT-001"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / EXPERIMENT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"
EVAL_SCRIPT_PATH = ROOT / "scripts" / "evaluate_local_qwen_planner_lora_tiny_overfit_001.py"
TRAIN_SCRIPT_PATH = ROOT / "scripts" / "train_local_qwen_planner_lora_tiny_overfit_001.py"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def target_verifier_case(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "case_id": row.get("case_id"),
        "sanitized_buyer_text": row.get("sanitized_buyer_text"),
        "approved_campaign_fact_ids": ["public_plan_names"],
        "approved_campaign_fact_summaries": row.get("approved_campaign_fact_summaries") or {},
    }


def validate_targets(rows: list[dict[str, Any]]) -> tuple[dict[str, Any], dict[str, list[str]]]:
    counts: Counter[str] = Counter()
    case_errors: dict[str, list[str]] = {}
    for row in rows:
        case_id = str(row.get("case_id") or "")
        compact = row.get("target_compact_json") if isinstance(row.get("target_compact_json"), dict) else {}
        compact_errors = validate_compact_conversation_brain_output(compact)
        contract_errors = validate_compact_value_contract(compact)
        quality_errors = [
            f"{item['field']}:{item['issue']}:{item['value']}" for item in compact_label_quality_issues(compact)
        ]
        expanded, adapter_errors = expand_compact_planner_output(compact)
        verifier_errors = verify_conversation_brain_output(expanded, target_verifier_case(row)) if not adapter_errors else []
        errors = [*compact_errors, *contract_errors, *quality_errors, *adapter_errors, *verifier_errors]
        if errors:
            case_errors[case_id] = errors
        counts["row_count"] += 1
        counts["schema_error_count"] += len(compact_errors)
        counts["contract_error_count"] += len(contract_errors)
        counts["label_quality_issue_count"] += len(quality_errors)
        counts["adapter_error_count"] += len(adapter_errors)
        counts["verifier_error_count"] += len(verifier_errors)
    return dict(counts), case_errors


def tokenizer_audit(rows: list[dict[str, Any]]) -> dict[str, Any]:
    from transformers import AutoTokenizer  # type: ignore

    model_path = safe_project_path(str(TINY_CONFIG["base_model_path"]))
    cache_dir = safe_project_path(str(TINY_CONFIG["cache_dir"]))
    tokenizer = AutoTokenizer.from_pretrained(
        str(model_path),
        cache_dir=str(cache_dir),
        local_files_only=True,
        trust_remote_code=False,
    )
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    sample = rows[0]
    train_text = render_train_chat(tokenizer, sample)
    eval_text = render_eval_chat(tokenizer, sample)
    tokenized = tokenize_rows_assistant_only(rows, tokenizer, int(TINY_CONFIG["max_seq_length"]))
    sample_prompt_ids = list(tokenizer(eval_text, add_special_tokens=False)["input_ids"])
    sample_full_ids = list(tokenizer(train_text, add_special_tokens=False)["input_ids"])
    sample_eos_appended = False
    if tokenizer.eos_token_id is not None and (not sample_full_ids or sample_full_ids[-1] != tokenizer.eos_token_id):
        sample_full_ids.append(int(tokenizer.eos_token_id))
        sample_eos_appended = True
    sample_labels = tokenized.rows[0]["labels"]
    prompt_len = min(len(sample_prompt_ids), len(sample_labels))
    masked_prefix_ok = all(label == -100 for label in sample_labels[:prompt_len])
    unmasked_labels = [label for label in sample_labels if label != -100]
    unmasked_text = tokenizer.decode(unmasked_labels, skip_special_tokens=False)
    target_text = target_json_text(sample)
    chat_template = str(getattr(tokenizer, "chat_template", "") or "")
    return {
        "tokenizer_class": tokenizer.__class__.__name__,
        "chat_template_available": hasattr(tokenizer, "apply_chat_template"),
        "chat_template_sha256": sha256_text(chat_template) if chat_template else None,
        "train_chat_template_used": "tokenizer.apply_chat_template" if hasattr(tokenizer, "apply_chat_template") else "fallback_role_join",
        "eval_chat_template_used": "tokenizer.apply_chat_template" if hasattr(tokenizer, "apply_chat_template") else "fallback_role_join",
        "train_prompt_sha256_sample": sha256_text(train_text),
        "eval_prompt_sha256_sample": sha256_text(eval_text),
        "dataset_prompt_sha256_sample": sha256_text(str(sample.get("prompt") or "")),
        "train_prompt_exact_text_sample": train_text,
        "eval_prompt_exact_text_sample": eval_text,
        "generation_prompt_excludes_target_answer": target_text not in eval_text,
        "target_text_present_in_training_render": target_text in train_text,
        "target_text_present_in_unmasked_labels": target_text in unmasked_text,
        "labels_mask_prompt_tokens": masked_prefix_ok,
        "labels_train_only_assistant_tokens": masked_prefix_ok and target_text in unmasked_text,
        "full_sequence_trained": not masked_prefix_ok,
        "tokenization_lengths": tokenized.stats,
        "sample_prompt_token_count": len(sample_prompt_ids),
        "sample_full_token_count": len(sample_full_ids),
        "sample_unmasked_label_token_count": len(unmasked_labels),
        "sample_eos_token_appended": sample_eos_appended,
        "eos_token_appended_count": tokenized.stats.get("eos_token_appended_count"),
        "eos_token_id": tokenizer.eos_token_id,
        "pad_token_id": tokenizer.pad_token_id,
        "pad_eos_ids_sane": tokenizer.eos_token_id is not None and tokenizer.pad_token_id is not None,
        "pad_equals_eos": tokenizer.pad_token_id == tokenizer.eos_token_id,
    }


def static_pipeline_checks() -> dict[str, Any]:
    eval_text = EVAL_SCRIPT_PATH.read_text(encoding="utf-8") if EVAL_SCRIPT_PATH.is_file() else ""
    train_text = TRAIN_SCRIPT_PATH.read_text(encoding="utf-8") if TRAIN_SCRIPT_PATH.is_file() else ""
    return {
        "train_script": rel(TRAIN_SCRIPT_PATH),
        "eval_script": rel(EVAL_SCRIPT_PATH),
        "planned_new_adapter_path": TINY_ADAPTER_PATH,
        "training_adapter_path_is_tiny_path": TINY_CONFIG.get("output_adapter_dir") == TINY_ADAPTER_PATH,
        "eval_script_references_tiny_adapter_path": "TINY_ADAPTER_PATH" in eval_text and "tiny_adapter" in eval_text,
        "adapter_path_evaluated_is_newly_trained_path": "TINY_ADAPTER_PATH" in eval_text,
        "base_model_id": TINY_CONFIG.get("base_model_id"),
        "base_model_path": TINY_CONFIG.get("base_model_path"),
        "base_model_and_adapter_loaded_together": "PeftModel.from_pretrained(base_model" in eval_text,
        "generation_prompt_excludes_target_by_design": "include_target=False" in eval_text,
        "train_uses_assistant_only_tokenizer": "tokenize_rows_assistant_only" in train_text,
        "no_provider_imports": all(pattern not in train_text + eval_text for pattern in ("from openai", "openai.OpenAI", "requests.post", "httpx.post")),
    }


def assistant_target_check(rows: list[dict[str, Any]]) -> dict[str, Any]:
    failures: list[str] = []
    for row in rows:
        messages = tiny_chat_messages(row, include_target=True)
        if not messages or messages[-1].get("role") != "assistant":
            failures.append(str(row.get("case_id")))
            continue
        if messages[-1].get("content") != target_json_text(row):
            failures.append(str(row.get("case_id")))
    return {
        "target_compact_json_is_assistant_message": not failures,
        "assistant_target_failures": failures,
    }


def build_report(result: dict[str, Any]) -> str:
    checks = result["checks"]
    lines = [
        f"# {EXPERIMENT_ID}",
        "",
        "## Summary",
        "",
        f"- status: {result['status']}",
        f"- dataset: `{result['dataset_path']}`",
        f"- row_count: {result['row_count']}",
        f"- target_compact_json_is_assistant_message: {str(checks['target_compact_json_is_assistant_message']).lower()}",
        f"- labels_train_only_assistant_tokens: {str(checks['labels_train_only_assistant_tokens']).lower()}",
        f"- full_sequence_trained: {str(checks['full_sequence_trained']).lower()}",
        f"- eos_token_appended_count: {checks['eos_token_appended_count']}",
        f"- pad_eos_ids_sane: {str(checks['pad_eos_ids_sane']).lower()}",
        f"- adapter_path_evaluated_is_newly_trained_path: {str(checks['adapter_path_evaluated_is_newly_trained_path']).lower()}",
        f"- base_model_and_adapter_loaded_together: {str(checks['base_model_and_adapter_loaded_together']).lower()}",
        f"- generation_prompt_excludes_target_answer: {str(checks['generation_prompt_excludes_target_answer']).lower()}",
        f"- targets_validate_before_training: {str(checks['targets_validate_before_training']).lower()}",
        "",
        "## Prompt Hashes",
        "",
        json.dumps(result["prompt_hashes"], indent=2, ensure_ascii=False),
        "",
        "## Tokenization",
        "",
        json.dumps(result["tokenization"], indent=2, ensure_ascii=False),
    ]
    if result.get("failures"):
        lines.extend(["", "## Failures", "", json.dumps(result["failures"], indent=2, ensure_ascii=False)])
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    rows = read_jsonl(TRAIN_PATH)
    target_counts, target_errors = validate_targets(rows)
    token_info = tokenizer_audit(rows)
    static_checks = static_pipeline_checks()
    assistant_check = assistant_target_check(rows)
    checks = {
        **static_checks,
        **assistant_check,
        "labels_mask_prompt_tokens": token_info["labels_mask_prompt_tokens"],
        "labels_train_only_assistant_tokens": token_info["labels_train_only_assistant_tokens"],
        "full_sequence_trained": token_info["full_sequence_trained"],
        "eos_token_appended_count": token_info["eos_token_appended_count"],
        "pad_eos_ids_sane": token_info["pad_eos_ids_sane"],
        "generation_prompt_excludes_target_answer": token_info["generation_prompt_excludes_target_answer"],
        "target_text_present_in_training_render": token_info["target_text_present_in_training_render"],
        "target_text_present_in_unmasked_labels": token_info["target_text_present_in_unmasked_labels"],
        "targets_validate_before_training": not target_errors,
    }
    failures: list[str] = []
    required_true = (
        "target_compact_json_is_assistant_message",
        "labels_train_only_assistant_tokens",
        "pad_eos_ids_sane",
        "adapter_path_evaluated_is_newly_trained_path",
        "base_model_and_adapter_loaded_together",
        "generation_prompt_excludes_target_answer",
        "target_text_present_in_training_render",
        "target_text_present_in_unmasked_labels",
        "targets_validate_before_training",
        "no_provider_imports",
    )
    for key in required_true:
        if checks.get(key) is not True:
            failures.append(f"{key} must be true")
    if checks.get("full_sequence_trained") is not False:
        failures.append("full_sequence_trained must be false")
    result = {
        "experiment_id": EXPERIMENT_ID,
        "generated_at": utc_now(),
        "status": "pass" if not failures else "fail",
        "dataset_experiment_id": DATASET_EXPERIMENT_ID,
        "dataset_path": rel(TRAIN_PATH),
        "row_count": len(rows),
        "compact_value_contract_version": COMPACT_VALUE_CONTRACT_VERSION,
        "planner_schema_mode": COMPACT_PLANNER_SCHEMA_MODE,
        "checks": checks,
        "target_validation": {"counts": target_counts, "case_errors": target_errors},
        "prompt_hashes": {
            "dataset_prompt_sha256_sample": token_info["dataset_prompt_sha256_sample"],
            "train_prompt_sha256_sample": token_info["train_prompt_sha256_sample"],
            "eval_prompt_sha256_sample": token_info["eval_prompt_sha256_sample"],
            "chat_template_sha256": token_info["chat_template_sha256"],
        },
        "prompt_samples": {
            "train_prompt_exact_text_sample": token_info["train_prompt_exact_text_sample"],
            "eval_prompt_exact_text_sample": token_info["eval_prompt_exact_text_sample"],
        },
        "tokenization": {
            key: value
            for key, value in token_info.items()
            if key
            not in {
                "train_prompt_exact_text_sample",
                "eval_prompt_exact_text_sample",
                "dataset_prompt_sha256_sample",
                "train_prompt_sha256_sample",
                "eval_prompt_sha256_sample",
            }
        },
        "side_effects": {
            "local_model_calls_made": False,
            "provider_calls_made": False,
            "openai_api_calls_made": False,
            "live_tts_calls_made": False,
            "provider_side_effects_made": False,
            "runtime_behavior_changed": False,
            "response_text_changed": False,
            "model_download_attempted": False,
            "model_redownloaded": False,
        },
        "failures": failures,
    }
    write_json(RESULT_PATH, result)
    REPORT_PATH.write_text(build_report(result), encoding="utf-8")
    print(json.dumps({"status": result["status"], "failures": failures}, indent=2))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
