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
    RESULT_PATH as DATASET_RESULT_PATH,
    SPLIT_PATHS,
    WEIGHT_SUFFIXES,
    load_cards,
    read_json,
    read_jsonl,
    rel,
    validate_dataset,
    write_json,
    write_text,
)


EXPERIMENT_ID = "LOCAL-QWEN-BALANCED-DATASET-ARTIFACTS-VALIDATION-001"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / EXPERIMENT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"
SPEC_PATH = ROOT / "runtime" / "llm_brain" / "training" / "qwen_balanced_planner_dataset_spec.json"
CARDS_PATH = ROOT / "runtime" / "llm_brain" / "training" / "qwen_compact_target_cards.json"
EQUIVALENCE_PATH = ROOT / "runtime" / "llm_brain" / "training" / "qwen_eval_equivalence_policy.json"
PLAN_PATH = ROOT / "runtime" / "llm_brain" / "training" / "qwen_mixed_replay_training_plan.json"


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


def changed_runtime_files() -> list[str]:
    try:
        completed = subprocess.run(
            ["git", "--no-optional-locks", "diff", "--name-only", "HEAD", "--", "runtime"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
    except Exception:
        return []
    if completed.returncode != 0:
        return []
    return [line.strip().replace("\\", "/") for line in completed.stdout.splitlines() if line.strip()]


def side_effects_false(payload: dict[str, Any], failures: list[str], label: str) -> None:
    side_effects = payload.get("side_effects") if isinstance(payload.get("side_effects"), dict) else {}
    for key in (
        "local_model_calls_made",
        "provider_calls_made",
        "openai_api_calls_made",
        "live_tts_calls_made",
        "runtime_behavior_changed",
        "response_text_changed",
        "raw_private_transcript_included",
    ):
        if side_effects.get(key) is not False:
            failures.append(f"{label}.side_effects.{key} must be false")


def build_report(result: dict[str, Any]) -> str:
    lines = [
        f"# {EXPERIMENT_ID}",
        "",
        f"- Status: {result['status']}",
        f"- Balanced dataset exists: {result['checks']['balanced_dataset_exists']}",
        f"- Dataset size in range: {result['checks']['dataset_size_in_range']}",
        f"- Target cards referenced: {result['checks']['target_cards_referenced']}",
        f"- Equivalence policy exists: {result['checks']['equivalence_policy_exists']}",
        f"- Mixed replay plan exists: {result['checks']['mixed_replay_plan_exists']}",
        f"- No provider/OpenAI/TTS calls: {result['checks']['no_provider_openai_tts_calls']}",
        f"- Runtime behavior changed: {result['checks']['runtime_behavior_changed']}",
        f"- Response text changed: {result['checks']['response_text_changed']}",
        f"- Live readiness claimed: {result['checks']['live_readiness_claimed']}",
    ]
    if result["failures"]:
        lines.extend(["", "## Failures", ""])
        lines.extend(f"- {failure}" for failure in result["failures"])
    return "\n".join(lines)


def main() -> int:
    failures: list[str] = []
    for path in (SPEC_PATH, CARDS_PATH, EQUIVALENCE_PATH, PLAN_PATH):
        if not path.is_file():
            failures.append(f"missing artifact: {rel(path)}")
    splits = {}
    for split, path in SPLIT_PATHS.items():
        if not path.is_file():
            failures.append(f"missing dataset split: {rel(path)}")
            splits[split] = []
        else:
            splits[split] = read_jsonl(path)
    cards = load_cards() if CARDS_PATH.is_file() else []
    validation = validate_dataset(splits, cards) if cards else {"status": "fail", "failures": ["missing target cards"], "total_rows": 0}
    failures.extend(validation.get("failures", []))
    dataset_result = read_json(DATASET_RESULT_PATH) if DATASET_RESULT_PATH.is_file() else {}
    if not dataset_result:
        failures.append(f"missing dataset result: {rel(DATASET_RESULT_PATH)}")
    elif dataset_result.get("status") != "pass":
        failures.append("balanced dataset result status must be pass")
    side_effects_false(dataset_result, failures, "balanced_dataset")
    plan = read_json(PLAN_PATH) if PLAN_PATH.is_file() else {}
    if plan:
        if plan.get("final_stage_only_stage3_rows_allowed") is not False:
            failures.append("mixed replay plan must set final_stage_only_stage3_rows_allowed false")
        if plan.get("final_stage_mixing_required") is not True:
            failures.append("mixed replay plan must set final_stage_mixing_required true")
        live_metrics = plan.get("live_ready_required_metrics") if isinstance(plan.get("live_ready_required_metrics"), dict) else {}
        if live_metrics.get("adapter_live_ready") is not False:
            failures.append("mixed replay plan must not claim adapter live readiness")
        if live_metrics.get("live_wiring_allowed_in_this_phase") is not False:
            failures.append("mixed replay plan must keep live wiring disabled")
    tracked_weights = [path for path in git_ls_files() if path.lower().endswith(WEIGHT_SUFFIXES)]
    tracked_local_artifacts = git_ls_files("local_artifacts")
    if tracked_weights:
        failures.append(f"model/adapter weights tracked by git: {tracked_weights}")
    if tracked_local_artifacts:
        failures.append(f"local_artifacts tracked by git: {tracked_local_artifacts}")
    runtime_non_training_changes = [
        path for path in changed_runtime_files()
        if not path.startswith("runtime/llm_brain/training/")
    ]
    if runtime_non_training_changes:
        failures.append(f"runtime behavior files changed outside training artifacts: {runtime_non_training_changes}")
    total_rows = validation.get("total_rows", 0)
    checks = {
        "balanced_dataset_exists": all(path.is_file() for path in SPLIT_PATHS.values()),
        "dataset_size_in_range": 300 <= int(total_rows or 0) <= 500,
        "all_compact_targets_valid": validation.get("status") == "pass",
        "target_cards_exist": CARDS_PATH.is_file(),
        "target_cards_referenced": validation.get("status") == "pass",
        "equivalence_policy_exists": EQUIVALENCE_PATH.is_file(),
        "mixed_replay_plan_exists": PLAN_PATH.is_file(),
        "final_stage_only_stage3_rows_allowed_false": bool(plan) and plan.get("final_stage_only_stage3_rows_allowed") is False,
        "final_stage_mixing_required_true": bool(plan) and plan.get("final_stage_mixing_required") is True,
        "no_provider_openai_tts_calls": not any("provider" in failure.lower() or "openai" in failure.lower() or "tts" in failure.lower() for failure in failures),
        "no_raw_private_transcripts": not any("raw private transcript flags present" in failure.lower() for failure in failures),
        "no_model_adapters_committed": not tracked_weights and not tracked_local_artifacts,
        "runtime_behavior_changed": bool(runtime_non_training_changes),
        "response_text_changed": False,
        "live_readiness_claimed": bool(plan) and (plan.get("live_ready_required_metrics") or {}).get("adapter_live_ready") is not False,
    }
    result = {
        "experiment_id": EXPERIMENT_ID,
        "validated_at": utc_now(),
        "status": "pass" if not failures else "fail",
        "checks": checks,
        "dataset_validation_status": validation.get("status"),
        "dataset_total_rows": total_rows,
        "failures": failures,
    }
    write_json(RESULT_PATH, result)
    write_text(REPORT_PATH, build_report(result))
    print(json.dumps({"status": result["status"], "failure_count": len(failures), "dataset_total_rows": total_rows}, indent=2))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
