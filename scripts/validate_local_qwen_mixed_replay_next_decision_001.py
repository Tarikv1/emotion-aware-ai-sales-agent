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
    audit_side_effects,
    read_json,
    rel,
    runtime_behavior_changed_by_files,
    tracked_model_or_adapter_files,
    utc_now,
    write_json,
    write_text,
)


EXPERIMENT_ID = "LOCAL-QWEN-MIXED-REPLAY-NEXT-DECISION-VALIDATION-001"
DECISION_ID = "LOCAL-QWEN-MIXED-REPLAY-NEXT-DECISION-001"
DECISION_RESULT_PATH = GENERATED_DIR / DECISION_ID / "result.json"
DECISION_REPORT_PATH = GENERATED_DIR / DECISION_ID / "report.md"
OUT_DIR = GENERATED_DIR / EXPERIMENT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"
SCRIPT_PATHS = [
    ROOT / "scripts" / "audit_local_qwen_mixed_replay_decoding_001.py",
    ROOT / "scripts" / "validate_local_qwen_mixed_replay_next_decision_001.py",
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


def git_lines(args: list[str]) -> list[str]:
    completed = subprocess.run(["git", "--no-optional-locks", *args], cwd=ROOT, capture_output=True, text=True, timeout=20, check=False)
    if completed.returncode != 0:
        return []
    return [line.strip().replace("\\", "/") for line in completed.stdout.splitlines() if line.strip()]


def changed_files() -> list[str]:
    return git_lines(["diff", "--name-only", "HEAD"])


def validate_no_blocked_patterns(failures: list[str]) -> None:
    for path in SCRIPT_PATHS:
        if not path.is_file():
            failures.append(f"missing script: {rel(path)}")
            continue
        text = path.read_text(encoding="utf-8")
        for label, pattern in BLOCKED_PATTERNS.items():
            if pattern in text:
                failures.append(f"{rel(path)} contains blocked model/training/provider pattern: {label}")


def main() -> int:
    failures: list[str] = []
    if not DECISION_RESULT_PATH.is_file():
        failures.append(f"missing next decision result: {rel(DECISION_RESULT_PATH)}")
    if not DECISION_REPORT_PATH.is_file():
        failures.append(f"missing next decision report: {rel(DECISION_REPORT_PATH)}")
    decision = read_json(DECISION_RESULT_PATH)
    if decision.get("status") != "pass":
        failures.append("next decision status must be pass")
    if not decision.get("recommended_next_option"):
        failures.append("next decision missing recommended_next_option")
    if decision.get("more_training_recommended_immediately") is not False:
        failures.append("next decision must not recommend immediate more training")
    if decision.get("adapter_live_ready") is not False:
        failures.append("adapter_live_ready must remain false")
    if decision.get("live_wiring_allowed") is not False:
        failures.append("live_wiring_allowed must remain false")
    if decision.get("quality_gate_passed") is not False:
        failures.append("quality_gate_passed must remain false")
    if decision.get("recommendation_does_not_claim_live_readiness") is not True:
        failures.append("decision must explicitly avoid live readiness claim")
    for key in (
        "local_model_calls_made",
        "training_rerun",
        "provider_side_effects_made",
        "runtime_behavior_changed",
        "response_text_changed",
    ):
        if decision.get(key) is not False:
            failures.append(f"decision.{key} must be false")
    for key in (
        "data_expansion_recommended",
        "label_simplification_recommended",
        "constrained_decoding_recommended",
        "two_head_architecture_recommended",
        "rejected_options",
        "rationale",
    ):
        if key not in decision:
            failures.append(f"next decision missing field: {key}")
    report_text = DECISION_REPORT_PATH.read_text(encoding="utf-8").lower() if DECISION_REPORT_PATH.is_file() else ""
    if "live-ready: true" in report_text or "adapter_live_ready: true" in report_text or "live_wiring_allowed: true" in report_text:
        failures.append("next decision report claims live readiness")
    validate_no_blocked_patterns(failures)
    tracked = tracked_model_or_adapter_files()
    if tracked:
        failures.append(f"tracked model/adapter/local_artifact files are forbidden: {tracked[:20]}")
    files_changed = changed_files()
    runtime_behavior_changed = runtime_behavior_changed_by_files(files_changed)
    response_text_changed = any(path.startswith("runtime/dialogue") or path.startswith("runtime/responses") for path in files_changed)
    if runtime_behavior_changed:
        failures.append("runtime behavior changed")
    if response_text_changed:
        failures.append("response text changed")

    result = {
        "experiment_id": EXPERIMENT_ID,
        "validated_at": utc_now(),
        "status": "pass" if not failures else "fail",
        "decision_result": rel(DECISION_RESULT_PATH),
        "checks": {
            "next_decision_exists": DECISION_RESULT_PATH.is_file() and DECISION_REPORT_PATH.is_file(),
            "adapter_live_ready": False,
            "live_wiring_allowed": False,
            "recommendation_does_not_claim_live_readiness": decision.get("recommendation_does_not_claim_live_readiness") is True,
            "no_local_qwen_calls": decision.get("local_model_calls_made") is False,
            "no_training": decision.get("training_rerun") is False,
            "no_provider_openai_tts_calls": decision.get("provider_side_effects_made") is False,
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
