#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from typing import Any

from local_ollama_qwen_utils_001 import (
    GENERATED_DIR,
    audit_side_effects,
    changed_files,
    pruned_weight_files,
    read_json,
    rel,
    runtime_behavior_changed_by_files,
    tracked_model_or_adapter_files,
    utc_now,
    write_json,
    write_text,
)


EXPERIMENT_ID = "LOCAL-QWEN-OLLAMA-BACKEND-PROBE-001"
VALIDATION_ID = "LOCAL-QWEN-OLLAMA-BACKEND-PROBE-VALIDATION-001"
RESULT_PATH = GENERATED_DIR / EXPERIMENT_ID / "result.json"
REPORT_PATH = GENERATED_DIR / EXPERIMENT_ID / "report.md"
OUT_DIR = GENERATED_DIR / VALIDATION_ID
VALIDATION_RESULT_PATH = OUT_DIR / "result.json"
VALIDATION_REPORT_PATH = OUT_DIR / "report.md"


def false_flag(payload: dict[str, Any], key: str, failures: list[str]) -> None:
    if payload.get(key) is not False:
        failures.append(f"{key} must be false")


def main() -> int:
    failures: list[str] = []
    if not RESULT_PATH.is_file():
        failures.append(f"missing probe result: {rel(RESULT_PATH)}")
    if not REPORT_PATH.is_file():
        failures.append(f"missing probe report: {rel(REPORT_PATH)}")
    payload = read_json(RESULT_PATH)
    if payload.get("experiment_id") != EXPERIMENT_ID:
        failures.append("probe result has wrong experiment_id")
    for key in (
        "local_model_calls_made",
        "provider_calls_made",
        "openai_api_calls_made",
        "live_tts_calls_made",
        "provider_side_effects_made",
        "training_rerun",
        "runtime_behavior_changed",
        "response_text_changed",
        "live_wiring_allowed",
        "adapter_live_ready",
    ):
        false_flag(payload, key, failures)
    if "ollama_localhost_calls_made" not in payload:
        failures.append("probe must report ollama_localhost_calls_made separately")
    if payload.get("ollama_pull_attempted") is True and payload.get("ollama_pull_allowed") is not True:
        failures.append("probe pull attempted without explicit pull allowance")
    side_effects = payload.get("side_effects") if isinstance(payload.get("side_effects"), dict) else {}
    for key in ("provider_calls_made", "openai_api_calls_made", "live_tts_calls_made", "provider_side_effects_made", "training_rerun", "actual_pruning_performed"):
        if side_effects.get(key) is not False:
            failures.append(f"side_effects.{key} must be false")
    tracked = tracked_model_or_adapter_files()
    if tracked:
        failures.append(f"tracked model/adapter/local_artifact files are forbidden: {tracked[:20]}")
    pruned = pruned_weight_files()
    if pruned:
        failures.append(f"pruned weights exist but this phase must not create them: {pruned[:20]}")
    files = changed_files()
    runtime_behavior_changed = runtime_behavior_changed_by_files(files)
    response_text_changed = any(path.startswith("runtime/dialogue") or path.startswith("runtime/responses") for path in files)
    if runtime_behavior_changed:
        failures.append("runtime behavior changed")
    if response_text_changed:
        failures.append("response text changed")

    result = {
        "experiment_id": VALIDATION_ID,
        "validated_at": utc_now(),
        "status": "pass" if not failures else "fail",
        "probe_result": rel(RESULT_PATH),
        "ollama_command_exists": payload.get("ollama_command_exists"),
        "ollama_api_reachable": payload.get("ollama_api_reachable"),
        "qwen_model_present": payload.get("qwen_model_present"),
        "ollama_pull_attempted": payload.get("ollama_pull_attempted"),
        "changed_files": files,
        "failures": failures,
        "side_effects": audit_side_effects(ollama_localhost_calls_made=payload.get("ollama_localhost_calls_made") is True),
    }
    write_json(VALIDATION_RESULT_PATH, result)
    write_text(
        VALIDATION_REPORT_PATH,
        "\n".join(
            [
                f"# {VALIDATION_ID}",
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
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
