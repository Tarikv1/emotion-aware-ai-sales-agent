#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.llm_brain.compact_planner_contract import (  # noqa: E402
    COMPACT_VALUE_CONTRACT_VERSION,
    DEPRECATED_COMPACT_LABELS_BY_FIELD,
    GENERIC_ACTION_VALUES,
    GENERIC_SUB_INTENT_VALUES,
    OVERLY_GENERIC_ACT_VALUES,
    allowed_values_for,
    is_case_id_like_label,
)
from scripts.train_local_qwen_planner_lora_001 import chat_messages  # noqa: E402


EXPERIMENT_ID = "LOCAL-QWEN-LORA-CONTRACT-FAILURE-AUDIT-001"
EVAL_DIR = ROOT / "research" / "experiments" / "generated" / "LOCAL-QWEN-LORA-EVAL-001"
SFT_DIR = ROOT / "research" / "experiments" / "generated" / "LOCAL-QWEN-SFT-DATASET-001"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / EXPERIMENT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"
SPLITS = ("train", "validation", "test")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{rel(path)} must contain a JSON object")
    return payload


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


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


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


def adapter_version_label(result: dict[str, Any], fallback: str) -> str:
    explicit = result.get("adapter_version_label")
    if isinstance(explicit, str) and explicit:
        return explicit
    adapter_path = str(result.get("adapter_path") or "")
    match = re.search(r"lora-(\d+)", adapter_path.replace("\\", "/"))
    if match:
        return f"lora-{match.group(1)}"
    return fallback


def load_sft_rows() -> dict[str, list[dict[str, Any]]]:
    rows_by_split: dict[str, list[dict[str, Any]]] = {}
    for split_name in SPLITS:
        rows_by_split[split_name] = read_jsonl(SFT_DIR / f"{split_name}.jsonl")
    return rows_by_split


def target_values_by_field(rows_by_split: dict[str, list[dict[str, Any]]]) -> dict[str, set[str]]:
    values: dict[str, set[str]] = defaultdict(set)
    for rows in rows_by_split.values():
        for row in rows:
            compact = row.get("target_compact_json") if isinstance(row.get("target_compact_json"), dict) else {}
            for field_name in ("act", "sub", "action", "strategy"):
                value = compact.get(field_name)
                if isinstance(value, str):
                    values[field_name].add(value)
    return values


def target_contract_issue_count(rows_by_split: dict[str, list[dict[str, Any]]]) -> int:
    issue_count = 0
    for rows in rows_by_split.values():
        for row in rows:
            compact = row.get("target_compact_json") if isinstance(row.get("target_compact_json"), dict) else {}
            for field_name in ("act", "sub", "action", "strategy"):
                value = compact.get(field_name)
                if isinstance(value, str) and value not in allowed_values_for(field_name):
                    issue_count += 1
    return issue_count


def classify_invalid_value(field_name: str, value: str) -> dict[str, bool]:
    return {
        "allowed_by_active_contract": value in allowed_values_for(field_name),
        "deprecated_label": value in DEPRECATED_COMPACT_LABELS_BY_FIELD.get(field_name, ()),
        "case_id_like_label": is_case_id_like_label(value),
        "generic_label": (
            (field_name == "act" and value in OVERLY_GENERIC_ACT_VALUES)
            or (field_name == "sub" and value in GENERIC_SUB_INTENT_VALUES)
            or (field_name == "action" and value in GENERIC_ACTION_VALUES)
        ),
    }


def compact_errors_by_case(case: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for error in case.get("compact_contract_errors") or []:
        match = re.search(r"compact\.([a-z_]+) value not allowed: '([^']+)'", str(error))
        if match:
            field_name, value = match.groups()
            if (field_name, value) not in seen:
                seen.add((field_name, value))
                errors.append({"field": field_name, "value": value, "error": str(error), **classify_invalid_value(field_name, value)})
            continue
        match = re.search(r"compact\.([a-z_]+) ([a-z_]+): '([^']+)'", str(error))
        if match:
            field_name, issue, value = match.groups()
            if (field_name, value) not in seen:
                seen.add((field_name, value))
                errors.append({"field": field_name, "value": value, "issue": issue, "error": str(error), **classify_invalid_value(field_name, value)})
    for issue in case.get("compact_label_quality_issues") or []:
        if not isinstance(issue, dict):
            continue
        field_name = str(issue.get("field") or "")
        value = str(issue.get("value") or "")
        if not field_name or not value:
            continue
        if (field_name, value) in seen:
            continue
        seen.add((field_name, value))
        record = {"field": field_name, "value": value, "issue": issue.get("issue"), **classify_invalid_value(field_name, value)}
        errors.append(record)
    return errors


def summarize_eval_result(
    label: str,
    path: Path,
    result: dict[str, Any],
    target_values: dict[str, set[str]],
) -> dict[str, Any]:
    cases = result.get("cases") if isinstance(result.get("cases"), list) else []
    metrics = result.get("adapter_metrics") if isinstance(result.get("adapter_metrics"), dict) else {}
    invalid_counter: Counter[tuple[str, str]] = Counter()
    errors_by_field: Counter[str] = Counter()
    deprecated_counter: Counter[tuple[str, str]] = Counter()
    case_id_counter: Counter[tuple[str, str]] = Counter()
    generic_counter: Counter[tuple[str, str]] = Counter()
    missing_required_fields: Counter[str] = Counter()
    list_type_errors: Counter[str] = Counter()
    schema_errors: list[dict[str, Any]] = []
    examples: list[dict[str, Any]] = []

    for case in cases:
        if not isinstance(case, dict):
            continue
        compact = case.get("compact_planner_output") if isinstance(case.get("compact_planner_output"), dict) else {}
        for error in case.get("compact_schema_errors") or []:
            error_text = str(error)
            schema_errors.append({"case_id": case.get("case_id"), "split": case.get("split"), "error": error_text})
            lowered = error_text.lower()
            if "missing" in lowered or "required" in lowered:
                missing_required_fields[error_text] += 1
            if "list" in lowered or "array" in lowered or "type" in lowered:
                list_type_errors[error_text] += 1
        case_invalids = compact_errors_by_case(case)
        for invalid in case_invalids:
            field_name = str(invalid["field"])
            value = str(invalid["value"])
            invalid_counter[(field_name, value)] += 1
            errors_by_field[field_name] += 1
            if invalid.get("deprecated_label"):
                deprecated_counter[(field_name, value)] += 1
            if invalid.get("case_id_like_label"):
                case_id_counter[(field_name, value)] += 1
            if invalid.get("generic_label"):
                generic_counter[(field_name, value)] += 1
        if case.get("compact_contract_valid") is not True and len(examples) < 10:
            examples.append(
                {
                    "case_id": case.get("case_id"),
                    "split": case.get("split"),
                    "labels": {field: compact.get(field) for field in ("act", "sub", "action", "strategy")},
                    "compact_contract_errors": case.get("compact_contract_errors") or [],
                    "compact_schema_errors": case.get("compact_schema_errors") or [],
                    "failure_classes": case.get("failure_classes") or [],
                }
            )

    invalid_values = [
        {
            "field": field_name,
            "value": value,
            "count": count,
            "in_training_targets": value in target_values.get(field_name, set()),
            "allowed_by_active_contract": value in allowed_values_for(field_name),
            "deprecated_label": value in DEPRECATED_COMPACT_LABELS_BY_FIELD.get(field_name, ()),
            "case_id_like_label": is_case_id_like_label(value),
            "generic_label": (
                (field_name == "act" and value in OVERLY_GENERIC_ACT_VALUES)
                or (field_name == "sub" and value in GENERIC_SUB_INTENT_VALUES)
                or (field_name == "action" and value in GENERIC_ACTION_VALUES)
            ),
        }
        for (field_name, value), count in invalid_counter.most_common()
    ]
    invalid_values_in_targets = [item for item in invalid_values if item["in_training_targets"]]
    output_copies_old_labels = bool(deprecated_counter or case_id_counter or generic_counter)
    adapter_loaded = result.get("adapter_loaded") is True
    prompt_alignment = result.get("prompt_alignment") if isinstance(result.get("prompt_alignment"), dict) else {}
    eval_prompt_allowed = prompt_alignment.get("eval_prompt_has_allowed_values")
    dataset_prompt_allowed = prompt_alignment.get("dataset_prompt_has_allowed_values")
    training_eval_contract_match = prompt_alignment.get("training_eval_contract_versions_match")
    prompt_evidence_missing = not bool(prompt_alignment)
    status = result.get("adapter_quality_status") or ("pass" if result.get("quality_gate_passed") else "not_ready")

    likely_causes = {
        "training_duration_issue": bool(invalid_values and not invalid_values_in_targets),
        "prompt_eval_mismatch": "unknown_legacy_evidence_missing"
        if prompt_evidence_missing
        else training_eval_contract_match is False,
        "dataset_target_issue": bool(invalid_values_in_targets),
        "adapter_loading_issue": not adapter_loaded or result.get("adapter_evaluated_path", result.get("adapter_path")) != result.get("adapter_path"),
        "contract_too_strict": False,
        "model_not_trained_enough": bool(invalid_values and not invalid_values_in_targets and adapter_loaded),
        "prompt_allowed_value_evidence_missing": prompt_evidence_missing,
        "eval_prompt_omitted_allowed_values": "unknown_legacy_evidence_missing"
        if prompt_evidence_missing
        else eval_prompt_allowed is False,
    }
    diagnosis = []
    if invalid_values:
        diagnosis.append("Adapter outputs use off-contract semantic synonyms rather than the exact cleaned label set.")
    if not invalid_values_in_targets:
        diagnosis.append("Invalid output labels were not present in rebuilt SFT targets.")
    if output_copies_old_labels:
        diagnosis.append("Some outputs copy deprecated, generic, or case-ID-like labels.")
    if not output_copies_old_labels and invalid_values:
        diagnosis.append("Outputs do not mainly copy old case-ID labels; they drift to new but unallowed aliases.")
    if adapter_loaded:
        diagnosis.append("Adapter evidence says the adapter loaded; base-model-only evaluation is unlikely.")
    if prompt_evidence_missing:
        diagnosis.append("Legacy eval snapshot does not record prompt-contract alignment fields.")
    elif eval_prompt_allowed is True and dataset_prompt_allowed is True:
        diagnosis.append("Current eval evidence shows dataset/eval prompts expose the active allowed values.")

    return {
        "label": label,
        "source_path": rel(path),
        "adapter_path": result.get("adapter_path"),
        "adapter_version_label": adapter_version_label(result, label),
        "adapter_quality_status": status,
        "adapter_live_ready": bool(result.get("adapter_live_ready")),
        "quality_gate_passed": bool(result.get("quality_gate_passed")),
        "schema_valid_count": {
            "validation": (metrics.get("validation") or {}).get("schema_valid_count"),
            "test": (metrics.get("test") or {}).get("schema_valid_count"),
        },
        "verifier_pass_count": {
            "validation": (metrics.get("validation") or {}).get("verifier_pass_count"),
            "test": (metrics.get("test") or {}).get("verifier_pass_count"),
        },
        "strict_gold_semantic_match_count": {
            "validation": (metrics.get("validation") or {}).get("strict_gold_semantic_match_count"),
            "test": (metrics.get("test") or {}).get("strict_gold_semantic_match_count"),
        },
        "compact_contract_valid_count": {
            "validation": (metrics.get("validation") or {}).get("compact_contract_valid_count"),
            "test": (metrics.get("test") or {}).get("compact_contract_valid_count"),
        },
        "contract_errors_by_field": dict(errors_by_field),
        "invalid_values_by_field": {
            field_name: [
                {"value": value, "count": count}
                for (counter_field, value), count in invalid_counter.most_common()
                if counter_field == field_name
            ]
            for field_name in ("act", "sub", "action", "strategy", "neg", "buyer", "intent", "flags")
        },
        "deprecated_labels_used": [
            {"field": field_name, "value": value, "count": count}
            for (field_name, value), count in deprecated_counter.most_common()
        ],
        "case_id_like_labels_used": [
            {"field": field_name, "value": value, "count": count}
            for (field_name, value), count in case_id_counter.most_common()
        ],
        "generic_labels_used": [
            {"field": field_name, "value": value, "count": count}
            for (field_name, value), count in generic_counter.most_common()
        ],
        "missing_required_fields": dict(missing_required_fields),
        "list_type_errors": dict(list_type_errors),
        "top_repeated_invalid_values": invalid_values[:20],
        "invalid_values_present_in_training_targets": invalid_values_in_targets,
        "training_targets_contained_invalid_values": bool(invalid_values_in_targets),
        "prompt_allowed_those_invalid_values": False,
        "eval_prompt_and_training_prompt_aligned": training_eval_contract_match,
        "eval_prompt_allowed_values_shown_to_model": eval_prompt_allowed,
        "dataset_prompt_allowed_values_shown_to_model": dataset_prompt_allowed,
        "model_output_appears_to_copy_old_labels": output_copies_old_labels,
        "likely_causes": likely_causes,
        "diagnosis": diagnosis,
        "schema_error_examples": schema_errors[:10],
        "contract_error_examples": examples,
    }


def eval_sources() -> list[tuple[str, Path]]:
    candidates = [
        ("adapter_v1_snapshot", EVAL_DIR / "result-v1-strict.json"),
        ("adapter_v2_snapshot", EVAL_DIR / "result-v2-strict.json"),
        ("current_eval_result", EVAL_DIR / "result.json"),
    ]
    return [(label, path) for label, path in candidates if path.is_file()]


def build_report(result: dict[str, Any]) -> str:
    lines = [
        f"# {EXPERIMENT_ID}",
        "",
        f"- status: {result['status']}",
        f"- active_contract_version: `{result['active_contract_version']}`",
        f"- sft_target_contract_issue_count: {result['sft_target_contract_issue_count']}",
        f"- provider_calls_made: false",
        f"- openai_api_calls_made: false",
        f"- live_tts_calls_made: false",
        f"- runtime_behavior_changed: false",
        f"- response_text_changed: false",
        "",
        "## Prompt Alignment",
        "",
        json.dumps(result["current_prompt_alignment"], indent=2, ensure_ascii=False),
    ]
    for summary in result["adapter_summaries"]:
        lines.extend(
            [
                "",
                f"## {summary['label']}",
                "",
                f"- adapter_path: `{summary.get('adapter_path')}`",
                f"- adapter_quality_status: {summary.get('adapter_quality_status')}",
                f"- adapter_live_ready: {str(summary.get('adapter_live_ready')).lower()}",
                f"- quality_gate_passed: {str(summary.get('quality_gate_passed')).lower()}",
                f"- validation_schema_valid: {summary['schema_valid_count'].get('validation')}",
                f"- validation_verifier_pass: {summary['verifier_pass_count'].get('validation')}",
                f"- validation_strict_gold_semantic: {summary['strict_gold_semantic_match_count'].get('validation')}",
                f"- validation_compact_contract_valid: {summary['compact_contract_valid_count'].get('validation')}",
                f"- test_schema_valid: {summary['schema_valid_count'].get('test')}",
                f"- test_verifier_pass: {summary['verifier_pass_count'].get('test')}",
                f"- test_strict_gold_semantic: {summary['strict_gold_semantic_match_count'].get('test')}",
                f"- test_compact_contract_valid: {summary['compact_contract_valid_count'].get('test')}",
                f"- model_output_appears_to_copy_old_labels: {str(summary['model_output_appears_to_copy_old_labels']).lower()}",
                "",
                "### Top Invalid Values",
                "",
            ]
        )
        for item in summary["top_repeated_invalid_values"][:10]:
            lines.append(
                f"- {item['field']}: `{item['value']}` x{item['count']} "
                f"(in_targets={str(item['in_training_targets']).lower()}, "
                f"allowed={str(item['allowed_by_active_contract']).lower()})"
            )
        lines.extend(["", "### Likely Causes", ""])
        for name, value in summary["likely_causes"].items():
            lines.append(f"- {name}: {str(value).lower()}")
        lines.extend(["", "### Diagnosis", ""])
        lines.extend(f"- {item}" for item in summary["diagnosis"])
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    rows_by_split = load_sft_rows()
    target_values = target_values_by_field(rows_by_split)
    sample_rows = [row for rows in rows_by_split.values() for row in rows[:1]]
    dataset_prompt_ok = all(prompt_contains_active_allowed_values(str(row.get("prompt") or "")) for row in sample_rows)
    eval_prompt_ok = all(
        prompt_contains_active_allowed_values("\n".join(message["content"] for message in chat_messages(row, include_target=False)))
        for row in sample_rows
    )
    summaries = [
        summarize_eval_result(label, path, read_json(path), target_values)
        for label, path in eval_sources()
    ]
    result = {
        "experiment_id": EXPERIMENT_ID,
        "generated_at": utc_now(),
        "status": "pass",
        "active_contract_version": COMPACT_VALUE_CONTRACT_VERSION,
        "source_eval_dir": rel(EVAL_DIR),
        "sft_dataset_dir": rel(SFT_DIR),
        "sft_target_contract_issue_count": target_contract_issue_count(rows_by_split),
        "current_prompt_alignment": {
            "dataset_prompt_has_allowed_values": dataset_prompt_ok,
            "eval_prompt_has_allowed_values": eval_prompt_ok,
            "eval_prompt_uses_training_chat_builder": True,
            "active_contract_version": COMPACT_VALUE_CONTRACT_VERSION,
        },
        "adapter_summaries": summaries,
        "side_effects": {
            "provider_calls_made": False,
            "openai_api_calls_made": False,
            "live_tts_calls_made": False,
            "provider_side_effects_made": False,
            "runtime_behavior_changed": False,
            "response_text_changed": False,
            "raw_private_transcript_included": False,
        },
    }
    write_json(RESULT_PATH, result)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(build_report(result), encoding="utf-8")
    print(json.dumps({"status": result["status"], "adapter_summaries": len(summaries)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
