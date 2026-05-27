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

from scripts.train_local_qwen_planner_lora_001 import rel  # noqa: E402


EXPERIMENT_ID = "LOCAL-QWEN-CURRICULUM-VALIDATION-001"
DATASET_RESULT = ROOT / "research" / "experiments" / "generated" / "LOCAL-QWEN-CURRICULUM-DATASET-001" / "result.json"
DATASET_DIR = DATASET_RESULT.parent
TRAINING_RESULT = ROOT / "research" / "experiments" / "generated" / "LOCAL-QWEN-LORA-CURRICULUM-TRAINING-001" / "result.json"
EVAL_RESULT = ROOT / "research" / "experiments" / "generated" / "LOCAL-QWEN-LORA-CURRICULUM-EVAL-001" / "result.json"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / EXPERIMENT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def git_ls_files(pathspec: str) -> list[str]:
    completed = subprocess.run(
        ["git", "--no-optional-locks", "ls-files", pathspec],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        return [f"git ls-files failed: {completed.stderr.strip()}"]
    return [line for line in completed.stdout.splitlines() if line.strip()]


def false_flags(payload: dict[str, Any], keys: list[str]) -> dict[str, bool]:
    return {key: payload.get(key) is False for key in keys}


def write_report(result: dict[str, Any]) -> None:
    lines = [
        f"# {EXPERIMENT_ID}",
        "",
        f"- status: {result.get('status')}",
        f"- quality_gate_passed: {str(result.get('quality_gate_passed')).lower()}",
        f"- adapter_live_ready: {str(result.get('adapter_live_ready')).lower()}",
        f"- failure_count: {len(result.get('failures') or [])}",
        "",
        "## Checks",
        "",
        json.dumps(result.get("checks") or {}, indent=2, ensure_ascii=False),
        "",
        "## Failures",
        "",
        json.dumps(result.get("failures") or [], indent=2, ensure_ascii=False),
    ]
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    dataset = read_json(DATASET_RESULT)
    training = read_json(TRAINING_RESULT)
    evaluation = read_json(EVAL_RESULT)
    adapter_path = str(training.get("adapter_path") or evaluation.get("adapter_path") or "")
    tracked_local_artifacts = git_ls_files("local_artifacts")
    heldout = dataset.get("held_out_contamination") if isinstance(dataset.get("held_out_contamination"), dict) else {}
    validation_clean = (heldout.get("validation") or {}).get("held_out_clean") is True
    test_clean = (heldout.get("test") or {}).get("held_out_clean") is True
    side_effect_keys = [
        "provider_calls_made",
        "openai_api_calls_made",
        "live_tts_calls_made",
        "provider_side_effects_made",
        "runtime_behavior_changed",
        "response_text_changed",
        "raw_private_transcript_included",
        "raw_private_transcript_copied_to_public_evidence",
    ]
    checks = {
        "dataset_result_exists": DATASET_RESULT.is_file(),
        "stage1_tiny_exists": (DATASET_DIR / "stage1_tiny.jsonl").is_file(),
        "stage2_20_exists": (DATASET_DIR / "stage2_20.jsonl").is_file(),
        "stage3_60_exists": (DATASET_DIR / "stage3_60.jsonl").is_file(),
        "validation_split_exists": (DATASET_DIR / "validation.jsonl").is_file(),
        "test_split_exists": (DATASET_DIR / "test.jsonl").is_file(),
        "training_result_exists": TRAINING_RESULT.is_file(),
        "eval_result_exists": EVAL_RESULT.is_file(),
        "curriculum_dataset_status_pass": dataset.get("status") == "pass",
        "validation_held_out_clean": validation_clean,
        "test_held_out_clean": test_clean,
        "adapter_path_under_local_artifacts": adapter_path.replace("\\", "/").startswith("local_artifacts/adapters/"),
        "adapter_model_weights_not_committed": not tracked_local_artifacts,
        "training_side_effect_flags_false": all(false_flags(training, side_effect_keys).values()),
        "eval_side_effect_flags_false": all(false_flags(evaluation, side_effect_keys).values()),
        "training_evidence_status_allowed": training.get("status") in {"completed", "partial", "interrupted", "blocked", "dry_run_pass"},
        "eval_evidence_status_allowed": evaluation.get("status") in {"completed", "adapter_missing", "blocked"},
        "adapter_live_ready_reported": isinstance(evaluation.get("adapter_live_ready"), bool),
        "adapter_live_ready_not_true_without_quality_gate": not (
            evaluation.get("adapter_live_ready") is True and evaluation.get("quality_gate_passed") is not True
        ),
        "quality_gate_reported": isinstance(evaluation.get("quality_gate_passed"), bool),
        "adapter_files_committed_false_training": training.get("adapter_files_committed") is False,
        "adapter_files_committed_false_eval": evaluation.get("adapter_files_committed") is False,
    }
    failures = [name for name, passed in checks.items() if not passed]
    result = {
        "experiment_id": EXPERIMENT_ID,
        "validated_at": utc_now(),
        "status": "pass" if not failures else "fail",
        "dataset_result": rel(DATASET_RESULT),
        "training_result": rel(TRAINING_RESULT),
        "eval_result": rel(EVAL_RESULT),
        "adapter_path": adapter_path,
        "quality_gate_passed": evaluation.get("quality_gate_passed"),
        "adapter_live_ready": evaluation.get("adapter_live_ready"),
        "checks": checks,
        "failures": failures,
        "tracked_local_artifacts": tracked_local_artifacts,
    }
    write_json(RESULT_PATH, result)
    write_report(result)
    print(json.dumps({"status": result["status"], "failures": failures}, indent=2))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
