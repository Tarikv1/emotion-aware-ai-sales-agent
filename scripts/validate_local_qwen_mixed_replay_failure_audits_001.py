#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import subprocess
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


EXPERIMENT_ID = "LOCAL-QWEN-MIXED-REPLAY-FAILURE-AUDITS-VALIDATION-001"
AUDIT_IDS = (
    "LOCAL-QWEN-MIXED-REPLAY-EVAL-FAILURE-AUDIT-001",
    "LOCAL-QWEN-MIXED-REPLAY-TRAIN-VS-EVAL-AUDIT-001",
    "LOCAL-QWEN-MIXED-REPLAY-DECODING-AUDIT-001",
)
OUT_DIR = GENERATED_DIR / EXPERIMENT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"
SCRIPT_PATHS = [
    ROOT / "scripts" / "audit_local_qwen_mixed_replay_eval_failures_001.py",
    ROOT / "scripts" / "audit_local_qwen_mixed_replay_train_vs_eval_001.py",
    ROOT / "scripts" / "audit_local_qwen_mixed_replay_decoding_001.py",
    ROOT / "scripts" / "validate_local_qwen_mixed_replay_failure_audits_001.py",
]
BLOCKED_PATTERNS = {
    "transformers_model_load": "Auto" + "Model",
    "peft_model_load": "Peft" + "Model",
    "trainer": "Trainer" + "(",
    "training_args": "Training" + "Arguments",
    "openai_import": "from " + "openai",
    "openai_client": "openai" + ".OpenAI",
    "openai_key": "OPENAI" + "_API_KEY",
    "requests_post": "requests" + ".post",
    "httpx_post": "httpx" + ".post",
    "smtp": "smtp" + "lib",
    "tts": "live_" + "tts(",
}
FORBIDDEN_EVIDENCE_TERMS = (
    "normalized_transcript",
    "data/private/",
    "data/private-restricted",
    "private transcript text",
)


def git_lines(args: list[str]) -> list[str]:
    completed = subprocess.run(["git", "--no-optional-locks", *args], cwd=ROOT, capture_output=True, text=True, timeout=20, check=False)
    if completed.returncode != 0:
        return []
    return [line.strip().replace("\\", "/") for line in completed.stdout.splitlines() if line.strip()]


def changed_files() -> list[str]:
    return git_lines(["diff", "--name-only", "HEAD"])


def side_effects_clean(label: str, payload: dict[str, Any], failures: list[str]) -> None:
    side_effects = payload.get("side_effects") if isinstance(payload.get("side_effects"), dict) else {}
    for key in SIDE_EFFECT_FALSE_KEYS:
        if side_effects.get(key) is not False:
            failures.append(f"{label}.side_effects.{key} must be false")
    for key in (
        "local_model_calls_made",
        "training_rerun",
        "provider_calls_made",
        "openai_api_calls_made",
        "live_tts_calls_made",
        "provider_side_effects_made",
        "runtime_behavior_changed",
        "response_text_changed",
        "adapter_live_ready",
        "live_wiring_allowed",
        "raw_private_transcript_copied_to_public_evidence",
    ):
        if payload.get(key) is not False:
            failures.append(f"{label}.{key} must be false")


def validate_no_blocked_patterns(failures: list[str]) -> None:
    for path in SCRIPT_PATHS:
        if not path.is_file():
            failures.append(f"missing script: {rel(path)}")
            continue
        text = path.read_text(encoding="utf-8")
        for label, pattern in BLOCKED_PATTERNS.items():
            if pattern in text:
                failures.append(f"{rel(path)} contains blocked model/training/provider pattern: {label}")


def validate_no_private_evidence(failures: list[str]) -> None:
    for audit_id in AUDIT_IDS:
        for filename in ("result.json", "report.md"):
            path = GENERATED_DIR / audit_id / filename
            if not path.is_file():
                failures.append(f"missing evidence file: {rel(path)}")
                continue
            text = path.read_text(encoding="utf-8").lower()
            for term in FORBIDDEN_EVIDENCE_TERMS:
                if term in text:
                    failures.append(f"{rel(path)} contains forbidden private evidence term: {term}")


def main() -> int:
    failures: list[str] = []
    payloads: dict[str, dict[str, Any]] = {}
    for audit_id in AUDIT_IDS:
        result_path = GENERATED_DIR / audit_id / "result.json"
        report_path = GENERATED_DIR / audit_id / "report.md"
        if not result_path.is_file():
            failures.append(f"missing audit result: {rel(result_path)}")
        if not report_path.is_file():
            failures.append(f"missing audit report: {rel(report_path)}")
        payload = read_json(result_path)
        payloads[audit_id] = payload
        if payload.get("status") != "pass":
            failures.append(f"{audit_id} status must be pass")
        side_effects_clean(audit_id, payload, failures)

    failure_audit = payloads.get("LOCAL-QWEN-MIXED-REPLAY-EVAL-FAILURE-AUDIT-001", {})
    for key in (
        "failure_counts_by_class",
        "failure_counts_by_semantic_group",
        "failure_counts_by_target_card_id",
        "failure_counts_by_split",
        "top_expected_labels_missed",
        "top_predicted_wrong_labels",
        "confusion_matrices",
        "wrong_output_examples_sanitized",
        "verifier_passed_but_strict_semantic_failed",
        "schema_or_contract_failed_cases",
        "safe_but_commercially_wrong_cases",
        "unsafe_or_side_effect_risky_cases",
    ):
        if key not in failure_audit:
            failures.append(f"failure audit missing section: {key}")
    for name in (
        "schema_failure",
        "compact_contract_failure",
        "verifier_failure",
        "safety_failure",
        "strict_semantic_failure",
        "response_plan_failure",
        "wrong_action",
        "wrong_strategy",
        "training_signal_issue",
        "decoding_issue",
    ):
        if name not in (failure_audit.get("failure_counts_by_class") or {}):
            failures.append(f"failure audit missing class count: {name}")

    train_audit = payloads.get("LOCAL-QWEN-MIXED-REPLAY-TRAIN-VS-EVAL-AUDIT-001", {})
    for key in (
        "train_sample_vs_heldout",
        "semantic_groups_pass_train_fail_heldout",
        "target_cards_underrepresented_in_train",
        "target_cards_represented_but_still_fail",
        "source_type_correlation",
        "buyer_text_length_correlation",
        "target_json_length_correlation",
        "say_diversity_correlation",
        "rare_label_failure_correlation",
        "sales_safety_explanation_category_performance",
        "classification",
    ):
        if key not in train_audit:
            failures.append(f"train-vs-eval audit missing section: {key}")

    decoding = payloads.get("LOCAL-QWEN-MIXED-REPLAY-DECODING-AUDIT-001", {})
    for key in (
        "malformed_output_count",
        "incomplete_json_count",
        "extra_text_outside_json_count",
        "invalid_compact_field_count",
        "compact_contract_failures_by_field",
        "max_output_token_truncation_count",
        "timeout_count",
        "first_complete_json_stop_behavior",
        "average_generated_tokens",
        "failures_are_mostly_semantic_not_formatting",
        "constrained_decoding_or_label_normalization",
    ):
        if key not in decoding:
            failures.append(f"decoding audit missing section: {key}")

    validate_no_blocked_patterns(failures)
    validate_no_private_evidence(failures)
    tracked = tracked_model_or_adapter_files()
    if tracked:
        failures.append(f"tracked model/adapter/local_artifact files are forbidden: {tracked[:20]}")
    files_changed = changed_files()
    runtime_behavior_changed = any(
        path.startswith("runtime/") and not path.startswith("runtime/llm_brain/training/")
        for path in files_changed
    )
    response_text_changed = any(path.startswith("runtime/dialogue") or path.startswith("runtime/responses") for path in files_changed)
    if runtime_behavior_changed:
        failures.append("runtime behavior changed")
    if response_text_changed:
        failures.append("response text changed")

    result = {
        "experiment_id": EXPERIMENT_ID,
        "validated_at": utc_now(),
        "status": "pass" if not failures else "fail",
        "audit_ids": list(AUDIT_IDS),
        "checks": {
            "audit_evidence_exists": all((GENERATED_DIR / audit_id / "result.json").is_file() and (GENERATED_DIR / audit_id / "report.md").is_file() for audit_id in AUDIT_IDS),
            "no_local_qwen_calls": not any("local_model_calls_made" in failure for failure in failures),
            "no_training": not any("training_rerun" in failure for failure in failures),
            "no_provider_openai_tts_calls": not any("provider" in failure or "openai" in failure or "tts" in failure for failure in failures),
            "no_raw_private_transcript_copied": not any("private evidence" in failure for failure in failures),
            "no_model_adapters_committed": not tracked,
            "runtime_behavior_changed": runtime_behavior_changed,
            "response_text_changed": response_text_changed,
        },
        "changed_files": files_changed,
        "failures": failures,
        "side_effects": audit_side_effects(),
    }
    write_json(RESULT_PATH, result)
    write_text(
        REPORT_PATH,
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
