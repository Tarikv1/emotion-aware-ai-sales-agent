#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
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
from scripts.train_local_qwen_planner_lora_001 import read_jsonl, rel  # noqa: E402


EXPERIMENT_ID = "LOCAL-QWEN-CURRICULUM-DATASET-001"
SOURCE_SFT_EXPERIMENT_ID = "LOCAL-QWEN-SFT-DATASET-001"
SOURCE_TINY_EXPERIMENT_ID = "LOCAL-QWEN-TINY-OVERFIT-DATASET-001"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / EXPERIMENT_ID
SOURCE_SFT_DIR = ROOT / "research" / "experiments" / "generated" / SOURCE_SFT_EXPERIMENT_ID
SOURCE_TINY_DIR = ROOT / "research" / "experiments" / "generated" / SOURCE_TINY_EXPERIMENT_ID
STAGE_TINY_PATH = OUT_DIR / "stage1_tiny.jsonl"
STAGE_20_PATH = OUT_DIR / "stage2_20.jsonl"
STAGE_60_PATH = OUT_DIR / "stage3_60.jsonl"
LEGACY_STAGE_PATHS = [
    OUT_DIR / "stage_tiny.jsonl",
    OUT_DIR / "stage_20.jsonl",
    OUT_DIR / "stage_60.jsonl",
]
VALIDATION_PATH = OUT_DIR / "validation.jsonl"
TEST_PATH = OUT_DIR / "test.jsonl"
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n" for row in rows),
        encoding="utf-8",
    )


def extract_input_context(row: dict[str, Any]) -> dict[str, Any]:
    prompt = str(row.get("prompt") or "")
    marker = "Input context:\n"
    if marker not in prompt:
        return {}
    raw = prompt.rsplit(marker, 1)[1].strip()
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}


def normalize_row(row: dict[str, Any], *, source_split: str, curriculum_stage: str) -> dict[str, Any]:
    context = extract_input_context(row)
    buyer_text = str(row.get("sanitized_buyer_text") or context.get("normalized_transcript") or "")
    normalized = dict(row)
    normalized["sanitized_buyer_text"] = buyer_text
    approved_summaries = normalized.get("approved_campaign_fact_summaries")
    if not isinstance(approved_summaries, dict):
        approved_summaries = context.get("approved_campaign_fact_summaries") if isinstance(context.get("approved_campaign_fact_summaries"), dict) else {}
    normalized["approved_campaign_fact_summaries"] = approved_summaries
    approved_ids = normalized.get("approved_campaign_fact_ids")
    if not isinstance(approved_ids, list):
        context_ids = context.get("approved_campaign_fact_ids")
        approved_ids = context_ids if isinstance(context_ids, list) else sorted(approved_summaries.keys())
    normalized["approved_campaign_fact_ids"] = approved_ids
    normalized["curriculum_source_experiment_id"] = (
        SOURCE_TINY_EXPERIMENT_ID if source_split == "tiny" else SOURCE_SFT_EXPERIMENT_ID
    )
    normalized["curriculum_source_split"] = source_split
    normalized["curriculum_stage"] = curriculum_stage
    normalized["curriculum_prompt_renderer"] = "scripts.train_local_qwen_planner_lora_tiny_overfit_001.render_eval_chat"
    normalized["compact_value_contract_version"] = COMPACT_VALUE_CONTRACT_VERSION
    normalized["raw_private_transcript_included"] = bool(normalized.get("raw_private_transcript_included"))
    return normalized


def validate_row(row: dict[str, Any]) -> dict[str, Any]:
    target = row.get("target_compact_json")
    errors: list[str] = []
    if not isinstance(target, dict):
        return {"case_id": row.get("case_id"), "valid": False, "errors": ["target_compact_json missing"]}
    compact_contract_errors = validate_compact_value_contract(target)
    label_quality_issues = compact_label_quality_issues(target)
    schema_errors = validate_compact_conversation_brain_output(target)
    expanded, adapter_errors = expand_compact_planner_output(target)
    verifier_errors = verify_conversation_brain_output(expanded, row) if not adapter_errors else []
    errors.extend(f"contract:{item}" for item in compact_contract_errors)
    errors.extend(f"label:{item}" for item in label_quality_issues)
    errors.extend(f"schema:{item}" for item in schema_errors)
    errors.extend(f"adapter:{item}" for item in adapter_errors)
    errors.extend(f"verifier:{item}" for item in verifier_errors)
    if not row.get("sanitized_buyer_text"):
        errors.append("sanitized_buyer_text missing")
    if row.get("raw_private_transcript_included") is not False:
        errors.append("raw_private_transcript_included must be false")
    return {"case_id": row.get("case_id"), "valid": not errors, "errors": errors}


def contamination(train_rows: list[dict[str, Any]], heldout_rows: list[dict[str, Any]]) -> dict[str, Any]:
    train_ids = {str(row.get("case_id") or "") for row in train_rows}
    heldout_ids = {str(row.get("case_id") or "") for row in heldout_rows}
    train_texts = {str(row.get("sanitized_buyer_text") or "").strip().lower() for row in train_rows}
    heldout_texts = {str(row.get("sanitized_buyer_text") or "").strip().lower() for row in heldout_rows}
    train_texts.discard("")
    heldout_texts.discard("")
    return {
        "case_id_overlap_count": len(train_ids & heldout_ids),
        "case_id_overlap": sorted(train_ids & heldout_ids),
        "exact_buyer_text_overlap_count": len(train_texts & heldout_texts),
        "exact_buyer_text_overlap": sorted(train_texts & heldout_texts),
        "held_out_clean": not (train_ids & heldout_ids) and not (train_texts & heldout_texts),
    }


def write_report(result: dict[str, Any]) -> None:
    lines = [
        f"# {EXPERIMENT_ID}",
        "",
        f"- status: {result.get('status')}",
        f"- source_sft_experiment_id: {SOURCE_SFT_EXPERIMENT_ID}",
        f"- source_tiny_experiment_id: {SOURCE_TINY_EXPERIMENT_ID}",
        f"- compact_value_contract_version: {COMPACT_VALUE_CONTRACT_VERSION}",
        f"- raw_private_transcript_included: {str(result.get('raw_private_transcript_included')).lower()}",
        f"- provider_calls_made: {str(result.get('provider_calls_made')).lower()}",
        f"- openai_api_calls_made: {str(result.get('openai_api_calls_made')).lower()}",
        f"- live_tts_calls_made: {str(result.get('live_tts_calls_made')).lower()}",
        "",
        "## Counts",
        "",
        json.dumps(result.get("counts") or {}, indent=2, ensure_ascii=False),
        "",
        "## Held-Out Contamination",
        "",
        json.dumps(result.get("held_out_contamination") or {}, indent=2, ensure_ascii=False),
        "",
        "## Validation",
        "",
        json.dumps(result.get("validation_summary") or {}, indent=2, ensure_ascii=False),
    ]
    REPORT_PATH.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    tiny_rows = [normalize_row(row, source_split="tiny", curriculum_stage="tiny") for row in read_jsonl(SOURCE_TINY_DIR / "train.jsonl")]
    train60 = [normalize_row(row, source_split="train", curriculum_stage="60") for row in read_jsonl(SOURCE_SFT_DIR / "train.jsonl")]
    train20 = [dict(row, curriculum_stage="20") for row in train60[:20]]
    validation_rows = [
        normalize_row(row, source_split="validation", curriculum_stage="heldout")
        for row in read_jsonl(SOURCE_SFT_DIR / "validation.jsonl")
    ]
    test_rows = [
        normalize_row(row, source_split="test", curriculum_stage="heldout")
        for row in read_jsonl(SOURCE_SFT_DIR / "test.jsonl")
    ]

    validation_results = {
        "tiny": [validate_row(row) for row in tiny_rows],
        "20": [validate_row(row) for row in train20],
        "60": [validate_row(row) for row in train60],
        "validation": [validate_row(row) for row in validation_rows],
        "test": [validate_row(row) for row in test_rows],
    }
    invalid = [
        {"split": split, **item}
        for split, items in validation_results.items()
        for item in items
        if not item["valid"]
    ]
    heldout = {
        "validation": contamination(train60, validation_rows),
        "test": contamination(train60, test_rows),
    }
    raw_private = any(
        row.get("raw_private_transcript_included") is not False
        for rows in (tiny_rows, train20, train60, validation_rows, test_rows)
        for row in rows
    )
    stage_categories = {
        "tiny": dict(Counter(str(row.get("category") or row.get("source_type") or "") for row in tiny_rows)),
        "20": dict(Counter(str(row.get("category") or row.get("source_type") or "") for row in train20)),
        "60": dict(Counter(str(row.get("category") or row.get("source_type") or "") for row in train60)),
    }
    result = {
        "experiment_id": EXPERIMENT_ID,
        "generated_at": utc_now(),
        "status": "pass" if not invalid and not raw_private and heldout["validation"]["held_out_clean"] and heldout["test"]["held_out_clean"] else "fail",
        "source_sft_experiment_id": SOURCE_SFT_EXPERIMENT_ID,
        "source_tiny_experiment_id": SOURCE_TINY_EXPERIMENT_ID,
        "paths": {
            "stage1_tiny": rel(STAGE_TINY_PATH),
            "stage2_20": rel(STAGE_20_PATH),
            "stage3_60": rel(STAGE_60_PATH),
            "validation": rel(VALIDATION_PATH),
            "test": rel(TEST_PATH),
        },
        "counts": {
            "stage1_tiny": len(tiny_rows),
            "stage2_20": len(train20),
            "stage3_60": len(train60),
            "validation": len(validation_rows),
            "test": len(test_rows),
        },
        "stage_categories": stage_categories,
        "held_out_contamination": heldout,
        "validation_summary": {
            "invalid_count": len(invalid),
            "invalid_cases": invalid[:50],
            "target_validation_totals": {split: len(items) for split, items in validation_results.items()},
            "target_validation_pass_counts": {
                split: sum(1 for item in items if item["valid"]) for split, items in validation_results.items()
            },
        },
        "raw_private_transcript_included": raw_private,
        "provider_calls_made": False,
        "openai_api_calls_made": False,
        "live_tts_calls_made": False,
        "provider_side_effects_made": False,
        "runtime_behavior_changed": False,
        "response_text_changed": False,
    }
    legacy_cleanup: list[dict[str, str]] = []
    for legacy_path in LEGACY_STAGE_PATHS:
        if legacy_path.exists():
            try:
                legacy_path.unlink()
                legacy_cleanup.append({"path": rel(legacy_path), "status": "removed"})
            except OSError as exc:
                legacy_cleanup.append({"path": rel(legacy_path), "status": "skipped", "error": str(exc)})
    result["legacy_stage_cleanup"] = legacy_cleanup
    write_jsonl(STAGE_TINY_PATH, tiny_rows)
    write_jsonl(STAGE_20_PATH, train20)
    write_jsonl(STAGE_60_PATH, train60)
    write_jsonl(VALIDATION_PATH, validation_rows)
    write_jsonl(TEST_PATH, test_rows)
    write_json(RESULT_PATH, result)
    write_report(result)
    print(json.dumps({"status": result["status"], "counts": result["counts"], "invalid_count": len(invalid)}, indent=2))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
