#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.local_qwen_audit_utils_001 import (  # noqa: E402
    GENERATED_DIR,
    SIDE_EFFECT_FALSE_KEYS,
    audit_side_effects,
    read_json,
    rel,
    tracked_model_or_adapter_files,
    utc_now,
    write_json,
    write_text,
)


EXPERIMENT_ID = "LOCAL-QWEN-DATASET-CONSISTENCY-AUDIT-VALIDATION-001"
AUDIT_ID = "LOCAL-QWEN-DATASET-CONSISTENCY-AUDIT-001"
AUDIT_DIR = GENERATED_DIR / AUDIT_ID
RESULT_PATH = AUDIT_DIR / "result.json"
REPORT_PATH = AUDIT_DIR / "report.md"
OUT_DIR = GENERATED_DIR / EXPERIMENT_ID
VALIDATION_RESULT_PATH = OUT_DIR / "result.json"
VALIDATION_REPORT_PATH = OUT_DIR / "report.md"

SCRIPT_PATHS = [
    ROOT / "scripts" / "local_qwen_audit_utils_001.py",
    ROOT / "scripts" / "audit_local_qwen_dataset_consistency_001.py",
    ROOT / "scripts" / "validate_local_qwen_dataset_consistency_audit_001.py",
]
BLOCKED_PATTERNS = {
    "openai_import": "from " + "openai",
    "openai_client": "openai" + ".OpenAI",
    "openai_api_key": "OPENAI" + "_API_KEY",
    "requests_post": "requests" + ".post",
    "httpx_post": "httpx" + ".post",
    "smtp": "smtp" + "lib",
}
FORBIDDEN_EVIDENCE_TERMS = (
    "normalized_transcript",
    "sanitized_buyer_text",
    "raw_output_excerpt",
    "data/private",
    "data/private-restricted",
)
REQUIRED_GOLD_CLASSES = (
    "true_model_failure",
    "gold_label_too_strict",
    "target_inconsistency",
    "split_distribution_issue",
    "insufficient_training_examples",
)


def side_effects_clean(payload: dict[str, Any], failures: list[str]) -> None:
    side_effects = payload.get("side_effects") if isinstance(payload.get("side_effects"), dict) else {}
    for key in SIDE_EFFECT_FALSE_KEYS:
        if side_effects.get(key) is not False:
            failures.append(f"side_effects.{key} must be false")


def validate_no_blocked_patterns(failures: list[str]) -> None:
    for path in SCRIPT_PATHS:
        if not path.is_file():
            failures.append(f"missing script: {rel(path)}")
            continue
        text = path.read_text(encoding="utf-8")
        for label, pattern in BLOCKED_PATTERNS.items():
            if pattern in text:
                failures.append(f"{rel(path)} contains blocked provider/API/TTS pattern: {label}")


def validate_no_raw_private_evidence(failures: list[str]) -> None:
    for path in (RESULT_PATH, REPORT_PATH):
        if not path.is_file():
            failures.append(f"missing evidence file: {rel(path)}")
            continue
        text = path.read_text(encoding="utf-8").lower()
        for term in FORBIDDEN_EVIDENCE_TERMS:
            if term in text:
                failures.append(f"{rel(path)} contains forbidden raw/private evidence term: {term}")


def main() -> int:
    failures: list[str] = []
    audit = read_json(RESULT_PATH)
    if not audit:
        failures.append(f"missing or invalid audit result: {rel(RESULT_PATH)}")
    if not REPORT_PATH.is_file():
        failures.append(f"missing audit report: {rel(REPORT_PATH)}")
    if audit.get("status") != "pass":
        failures.append("dataset consistency audit status must be pass")
    for key in (
        "label_distribution_by_split",
        "heldout_label_coverage",
        "similar_input_consistency",
        "target_response_plan_consistency",
        "gold_strictness_review",
    ):
        if not isinstance(audit.get(key), dict):
            failures.append(f"audit missing object: {key}")
    coverage = audit.get("heldout_label_coverage") if isinstance(audit.get("heldout_label_coverage"), dict) else {}
    if not isinstance((coverage.get("against_sft_train") or {}).get("validation"), dict):
        failures.append("heldout coverage missing validation against sft train")
    if not isinstance((coverage.get("against_sft_train") or {}).get("test"), dict):
        failures.append("heldout coverage missing test against sft train")
    groups = ((audit.get("similar_input_consistency") or {}).get("groups") or {})
    for group in (
        "current_tool_ai",
        "personal_not_team",
        "plan_explanation",
        "price_or_price_objection",
        "upgrade_midcycle",
        "terminal_acceptance",
        "safety_boundary",
        "use_case_coding_voice_writing_research",
    ):
        if group not in groups:
            failures.append(f"missing semantic neighborhood group: {group}")
    strictness = audit.get("gold_strictness_review") if isinstance(audit.get("gold_strictness_review"), dict) else {}
    class_counts = strictness.get("classification_counts") if isinstance(strictness.get("classification_counts"), dict) else {}
    for name in REQUIRED_GOLD_CLASSES:
        if name not in class_counts:
            failures.append(f"gold strictness missing classification count: {name}")
    side_effects_clean(audit, failures)
    validate_no_blocked_patterns(failures)
    validate_no_raw_private_evidence(failures)
    tracked = tracked_model_or_adapter_files()
    if tracked:
        failures.append(f"tracked model/adapter files are forbidden: {tracked[:20]}")

    result = {
        "experiment_id": EXPERIMENT_ID,
        "validated_at": utc_now(),
        "status": "pass" if not failures else "fail",
        "audit_result": rel(RESULT_PATH),
        "audit_report": rel(REPORT_PATH),
        "checks": {
            "evidence_exists": RESULT_PATH.is_file() and REPORT_PATH.is_file(),
            "no_provider_openai_tts_calls": not any("provider/API/TTS" in item for item in failures),
            "no_raw_private_transcript": not any("raw/private evidence" in item for item in failures),
            "no_model_adapter_files_committed": not tracked,
            "runtime_behavior_changed": False,
            "response_text_changed": False,
        },
        "failures": failures,
        "side_effects": audit_side_effects(),
    }
    write_json(VALIDATION_RESULT_PATH, result)
    write_text(
        VALIDATION_REPORT_PATH,
        "\n".join(
            [
                f"# {EXPERIMENT_ID}",
                "",
                f"- status: {result['status']}",
                f"- failure_count: {len(failures)}",
                "",
                "## Failures",
                "",
                json.dumps(failures, indent=2, ensure_ascii=False),
            ]
        ),
    )
    print(json.dumps({"status": result["status"], "failures": failures}, indent=2, ensure_ascii=False))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
