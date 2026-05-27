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


EXPERIMENT_ID = "LOCAL-QWEN-CURRICULUM-AUDITS-VALIDATION-001"
FORGETTING_ID = "LOCAL-QWEN-CURRICULUM-FORGETTING-AUDIT-001"
ERROR_ID = "LOCAL-QWEN-CURRICULUM-EVAL-ERROR-AUDIT-001"
PLAN_ID = "LOCAL-QWEN-NEXT-TRAINING-PLAN-001"
FORGETTING_RESULT_PATH = GENERATED_DIR / FORGETTING_ID / "result.json"
FORGETTING_REPORT_PATH = GENERATED_DIR / FORGETTING_ID / "report.md"
ERROR_RESULT_PATH = GENERATED_DIR / ERROR_ID / "result.json"
ERROR_REPORT_PATH = GENERATED_DIR / ERROR_ID / "report.md"
PLAN_RESULT_PATH = GENERATED_DIR / PLAN_ID / "result.json"
PLAN_REPORT_PATH = GENERATED_DIR / PLAN_ID / "report.md"
OUT_DIR = GENERATED_DIR / EXPERIMENT_ID
VALIDATION_RESULT_PATH = OUT_DIR / "result.json"
VALIDATION_REPORT_PATH = OUT_DIR / "report.md"

SCRIPT_PATHS = [
    ROOT / "scripts" / "local_qwen_audit_utils_001.py",
    ROOT / "scripts" / "audit_local_qwen_curriculum_forgetting_001.py",
    ROOT / "scripts" / "audit_local_qwen_curriculum_eval_errors_001.py",
    ROOT / "scripts" / "validate_local_qwen_curriculum_audits_001.py",
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
REQUIRED_ERROR_CLASSES = (
    "schema_issue",
    "verifier_issue",
    "strict_semantic_mismatch",
    "response_plan_mismatch",
    "wrong_act",
    "wrong_sub",
    "wrong_action",
    "wrong_strategy",
    "wrong_update",
    "wrong_preserve_avoid",
    "wrong_facts",
    "wrong_say",
    "acceptable_alternative",
    "unacceptable_wrong_sales_move",
)
ALLOWED_PLAN_OPTIONS = {
    "option_1_data_expansion_needed",
    "option_2_curriculum_replay_fix",
    "option_3_label_simplification",
    "option_4_eval_strictness_adjustment",
    "option_5_constrained_decoding_or_grammar",
}


def side_effects_clean(label: str, payload: dict[str, Any], failures: list[str]) -> None:
    side_effects = payload.get("side_effects") if isinstance(payload.get("side_effects"), dict) else {}
    for key in SIDE_EFFECT_FALSE_KEYS:
        if side_effects.get(key) is not False:
            failures.append(f"{label}.side_effects.{key} must be false")


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
    for path in (
        FORGETTING_RESULT_PATH,
        FORGETTING_REPORT_PATH,
        ERROR_RESULT_PATH,
        ERROR_REPORT_PATH,
        PLAN_RESULT_PATH,
        PLAN_REPORT_PATH,
    ):
        if not path.is_file():
            failures.append(f"missing evidence file: {rel(path)}")
            continue
        text = path.read_text(encoding="utf-8").lower()
        for term in FORBIDDEN_EVIDENCE_TERMS:
            if term in text:
                failures.append(f"{rel(path)} contains forbidden raw/private evidence term: {term}")


def main() -> int:
    failures: list[str] = []
    forgetting = read_json(FORGETTING_RESULT_PATH)
    error_audit = read_json(ERROR_RESULT_PATH)
    plan = read_json(PLAN_RESULT_PATH)

    for label, path in (
        ("forgetting result", FORGETTING_RESULT_PATH),
        ("forgetting report", FORGETTING_REPORT_PATH),
        ("error result", ERROR_RESULT_PATH),
        ("error report", ERROR_REPORT_PATH),
        ("plan result", PLAN_RESULT_PATH),
        ("plan report", PLAN_REPORT_PATH),
    ):
        if not path.is_file():
            failures.append(f"missing {label}: {rel(path)}")
    if forgetting.get("status") != "pass":
        failures.append("forgetting audit status must be pass")
    if error_audit.get("status") != "pass":
        failures.append("error audit status must be pass")
    if plan.get("status") != "pass":
        failures.append("next training plan status must be pass")
    if not isinstance(forgetting.get("forgotten_cases"), list):
        failures.append("forgetting audit must include forgotten_cases")
    replay = forgetting.get("training_replay_diagnostics") if isinstance(forgetting.get("training_replay_diagnostics"), dict) else {}
    for key in (
        "sequential_overwrite_without_mixed_replay",
        "tiny_replay_examples_in_later_stages",
        "learning_rate_steps_likely_caused_forgetting",
        "replay_weighting_or_balanced_sampling_recommended",
    ):
        if key not in replay:
            failures.append(f"forgetting audit missing replay diagnostic: {key}")
    class_counts = error_audit.get("class_counts") if isinstance(error_audit.get("class_counts"), dict) else {}
    for name in REQUIRED_ERROR_CLASSES:
        if name not in class_counts:
            failures.append(f"error audit missing class count: {name}")
    for key in (
        "top_wrong_labels_predicted",
        "top_expected_labels_missed",
        "confusion_matrix",
        "deterministic_baseline_clearly_better_case_ids",
        "model_output_acceptable_but_strict_gold_too_narrow_case_ids",
        "cases_needing_more_training_examples",
    ):
        if key not in error_audit:
            failures.append(f"error audit missing section: {key}")
    if plan.get("selected_option") not in ALLOWED_PLAN_OPTIONS:
        failures.append(f"next training plan selected_option invalid: {plan.get('selected_option')}")
    if plan.get("adapter_live_ready") is not False:
        failures.append("next training plan must not claim adapter_live_ready")
    if plan.get("quality_gate_passed") is not False:
        failures.append("next training plan must not claim quality_gate_passed")
    if plan.get("more_training_recommended_now") is not False:
        failures.append("next training plan must not recommend immediate more training")
    if ((plan.get("live_wiring") or {}).get("recommended")) is not False:
        failures.append("next training plan must not recommend live wiring")
    side_effects_clean("forgetting", forgetting, failures)
    side_effects_clean("error_audit", error_audit, failures)
    side_effects_clean("next_training_plan", plan, failures)
    validate_no_blocked_patterns(failures)
    validate_no_raw_private_evidence(failures)
    tracked = tracked_model_or_adapter_files()
    if tracked:
        failures.append(f"tracked model/adapter files are forbidden: {tracked[:20]}")

    result = {
        "experiment_id": EXPERIMENT_ID,
        "validated_at": utc_now(),
        "status": "pass" if not failures else "fail",
        "forgetting_result": rel(FORGETTING_RESULT_PATH),
        "error_result": rel(ERROR_RESULT_PATH),
        "next_training_plan": rel(PLAN_RESULT_PATH),
        "checks": {
            "evidence_exists": all(
                path.is_file()
                for path in (
                    FORGETTING_RESULT_PATH,
                    FORGETTING_REPORT_PATH,
                    ERROR_RESULT_PATH,
                    ERROR_REPORT_PATH,
                    PLAN_RESULT_PATH,
                    PLAN_REPORT_PATH,
                )
            ),
            "no_provider_openai_tts_calls": not any("provider/API/TTS" in item for item in failures),
            "no_raw_private_transcript": not any("raw/private evidence" in item for item in failures),
            "no_model_adapter_files_committed": not tracked,
            "runtime_behavior_changed": False,
            "response_text_changed": False,
            "next_training_plan_live_ready": False,
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
