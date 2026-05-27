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

from scripts.build_local_qwen_balanced_sft_dataset_001 import (  # noqa: E402
    RESULT_PATH as BALANCED_DATASET_RESULT_PATH,
    WEIGHT_SUFFIXES,
    read_json,
    rel,
    write_json,
    write_text,
)


EXPERIMENT_ID = "LOCAL-QWEN-NEXT-MIXED-REPLAY-TRAINING-PLAN-001"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / EXPERIMENT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"
PLAN_PATH = ROOT / "runtime" / "llm_brain" / "training" / "qwen_mixed_replay_training_plan.json"
EQUIVALENCE_POLICY_PATH = ROOT / "runtime" / "llm_brain" / "training" / "qwen_eval_equivalence_policy.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def git_ls_files(prefix: str | None = None) -> list[str]:
    command = ["git", "--no-optional-locks", "ls-files"]
    if prefix:
        command.append(prefix)
    try:
        completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=20, check=False)
    except Exception:
        return []
    if completed.returncode != 0:
        return []
    return [line.strip().replace("\\", "/") for line in completed.stdout.splitlines() if line.strip()]


def validate_side_effect_policy(plan: dict[str, Any], failures: list[str]) -> None:
    side_effect_policy = plan.get("side_effect_policy") if isinstance(plan.get("side_effect_policy"), dict) else {}
    for key in (
        "local_model_calls_made",
        "provider_calls_made",
        "openai_api_calls_made",
        "live_tts_calls_made",
        "runtime_behavior_changed",
        "response_text_changed",
        "model_or_adapter_weights_committed",
    ):
        if side_effect_policy.get(key) is not False:
            failures.append(f"side_effect_policy.{key} must be false")


def build_report(result: dict[str, Any]) -> str:
    lines = [
        f"# {EXPERIMENT_ID}",
        "",
        f"- Status: {result['status']}",
        f"- Selected strategy: {result['training_strategy']}",
        f"- Balanced dataset: {result['balanced_dataset_id']}",
        f"- More training recommended now: {result['more_training_recommended_now']}",
        f"- Future mixed replay recommended after approval: {result['future_mixed_replay_training_recommended_after_data_passes']}",
        f"- Adapter live ready claimed: {result['adapter_live_ready_claimed']}",
        f"- Live wiring allowed: {result['live_wiring_allowed_in_this_phase']}",
        f"- Final-stage mixing required: {result['checks']['final_stage_mixing_required']}",
        f"- Final-stage only stage3 allowed: {not result['checks']['final_stage_only_stage3_rows_allowed_false']}",
        f"- Provider/OpenAI/TTS calls made: false",
        f"- Runtime behavior changed: false",
        f"- Response text changed: false",
    ]
    if result["failures"]:
        lines.extend(["", "## Failures", ""])
        lines.extend(f"- {failure}" for failure in result["failures"])
    return "\n".join(lines)


def main() -> int:
    failures: list[str] = []
    if not PLAN_PATH.is_file():
        failures.append(f"missing mixed replay plan: {rel(PLAN_PATH)}")
        plan: dict[str, Any] = {}
    else:
        plan = read_json(PLAN_PATH)
    if not EQUIVALENCE_POLICY_PATH.is_file():
        failures.append(f"missing equivalence policy: {rel(EQUIVALENCE_POLICY_PATH)}")
    dataset_result = read_json(BALANCED_DATASET_RESULT_PATH) if BALANCED_DATASET_RESULT_PATH.is_file() else {}
    if dataset_result.get("status") != "pass":
        failures.append("balanced dataset result must exist and pass before validating next training plan")
    required_fields = {
        "base_model_id",
        "balanced_dataset_id",
        "output_adapter_dir",
        "adapter_version",
        "training_strategy",
        "replay_sources",
        "replay_weights",
        "semantic_group_weights",
        "rare_group_weighting",
        "final_stage_mixing_required",
        "final_stage_only_stage3_rows_allowed",
        "validation_test_held_out",
        "ood_test_separate",
        "stop_conditions",
        "quality_gate_thresholds",
        "latency_gate_thresholds",
        "live_ready_required_metrics",
    }
    if plan:
        missing = sorted(required_fields - set(plan))
        if missing:
            failures.append(f"mixed replay plan missing required field(s): {missing}")
        if plan.get("base_model_id") != "Qwen/Qwen2.5-7B-Instruct":
            failures.append("base_model_id must be Qwen/Qwen2.5-7B-Instruct")
        if plan.get("balanced_dataset_id") != "LOCAL-QWEN-BALANCED-SFT-DATASET-001":
            failures.append("balanced_dataset_id must reference LOCAL-QWEN-BALANCED-SFT-DATASET-001")
        if plan.get("training_strategy") != "mixed_replay_balanced_sampling":
            failures.append("training_strategy must be mixed_replay_balanced_sampling")
        if plan.get("final_stage_mixing_required") is not True:
            failures.append("final_stage_mixing_required must be true")
        if plan.get("final_stage_only_stage3_rows_allowed") is not False:
            failures.append("final_stage_only_stage3_rows_allowed must be false")
        if plan.get("validation_test_held_out") is not True:
            failures.append("validation_test_held_out must be true")
        if plan.get("ood_test_separate") is not True:
            failures.append("ood_test_separate must be true")
        if plan.get("train_again_in_this_phase") is not False:
            failures.append("train_again_in_this_phase must be false")
        output_adapter_dir = str(plan.get("output_adapter_dir") or "").replace("\\", "/")
        if not output_adapter_dir.startswith("local_artifacts/adapters/"):
            failures.append("output_adapter_dir must be under ignored local_artifacts/adapters")
        live_metrics = plan.get("live_ready_required_metrics") if isinstance(plan.get("live_ready_required_metrics"), dict) else {}
        if live_metrics.get("adapter_live_ready") is not False:
            failures.append("adapter_live_ready must not be claimed in the plan")
        if live_metrics.get("live_wiring_allowed_in_this_phase") is not False:
            failures.append("live_wiring_allowed_in_this_phase must be false")
        validate_side_effect_policy(plan, failures)
    tracked_weights = [path for path in git_ls_files() if path.lower().endswith(WEIGHT_SUFFIXES)]
    tracked_local_artifacts = git_ls_files("local_artifacts")
    if tracked_weights:
        failures.append(f"model/adapter weights tracked by git: {tracked_weights}")
    if tracked_local_artifacts:
        failures.append(f"local_artifacts tracked by git: {tracked_local_artifacts}")
    live_metrics = plan.get("live_ready_required_metrics") if isinstance(plan.get("live_ready_required_metrics"), dict) else {}
    result = {
        "experiment_id": EXPERIMENT_ID,
        "generated_at": utc_now(),
        "status": "pass" if not failures else "fail",
        "plan_path": rel(PLAN_PATH),
        "equivalence_policy_path": rel(EQUIVALENCE_POLICY_PATH),
        "balanced_dataset_result_path": rel(BALANCED_DATASET_RESULT_PATH),
        "training_strategy": plan.get("training_strategy"),
        "balanced_dataset_id": plan.get("balanced_dataset_id"),
        "more_training_recommended_now": False,
        "future_mixed_replay_training_recommended_after_data_passes": dataset_result.get("status") == "pass",
        "adapter_live_ready_claimed": live_metrics.get("adapter_live_ready") is not False,
        "live_wiring_allowed_in_this_phase": live_metrics.get("live_wiring_allowed_in_this_phase") is not False,
        "adapter_live_ready": False,
        "quality_gate_passed": False,
        "live_wiring": {
            "recommended": False,
            "reason": "This phase is planning and dataset expansion only; no adapter was trained or evaluated for live readiness.",
        },
        "checks": {
            "final_stage_mixing_required": plan.get("final_stage_mixing_required") is True,
            "final_stage_only_stage3_rows_allowed_false": plan.get("final_stage_only_stage3_rows_allowed") is False,
            "validation_test_held_out": plan.get("validation_test_held_out") is True,
            "ood_test_separate": plan.get("ood_test_separate") is True,
            "no_training_performed": plan.get("train_again_in_this_phase") is False,
            "no_model_or_adapter_weights_committed": not tracked_weights and not tracked_local_artifacts,
            "equivalence_policy_exists": EQUIVALENCE_POLICY_PATH.is_file(),
        },
        "side_effects": {
            "local_model_calls_made": False,
            "provider_calls_made": False,
            "openai_api_calls_made": False,
            "live_tts_calls_made": False,
            "provider_side_effects_made": False,
            "model_download_attempted": False,
            "model_redownloaded": False,
            "model_weights_committed": False,
            "adapter_files_committed": False,
            "runtime_behavior_changed": False,
            "response_text_changed": False,
            "raw_private_transcript_included": False,
        },
        "failures": failures,
    }
    write_json(RESULT_PATH, result)
    write_text(REPORT_PATH, build_report(result))
    print(json.dumps({"status": result["status"], "failure_count": len(failures), "more_training_recommended_now": False}, indent=2))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
