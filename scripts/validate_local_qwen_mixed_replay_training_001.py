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

from scripts.train_local_qwen_planner_lora_001 import read_jsonl, rel, safe_project_path  # noqa: E402


EXPERIMENT_ID = "LOCAL-QWEN-MIXED-REPLAY-VALIDATION-001"
DATASET_ID = "LOCAL-QWEN-MIXED-REPLAY-TRAINING-DATASET-001"
TRAINING_ID = "LOCAL-QWEN-LORA-MIXED-REPLAY-TRAINING-001"
EVAL_ID = "LOCAL-QWEN-LORA-MIXED-REPLAY-EVAL-001"
DATASET_DIR = ROOT / "research" / "experiments" / "generated" / DATASET_ID
TRAINING_DIR = ROOT / "research" / "experiments" / "generated" / TRAINING_ID
EVAL_DIR = ROOT / "research" / "experiments" / "generated" / EVAL_ID
OUT_DIR = ROOT / "research" / "experiments" / "generated" / EXPERIMENT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"
WEIGHT_SUFFIXES = (".safetensors", ".bin", ".gguf", ".pt", ".pth", ".ckpt")


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


def git_lines(args: list[str]) -> list[str]:
    completed = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, timeout=20, check=False)
    if completed.returncode != 0:
        return []
    return [line.strip().replace("\\", "/") for line in completed.stdout.splitlines() if line.strip()]


def tracked_weight_files() -> list[str]:
    tracked = git_lines(["ls-files"])
    return [path for path in tracked if path.lower().endswith(WEIGHT_SUFFIXES)]


def changed_files() -> list[str]:
    return git_lines(["diff", "--name-only", "HEAD"])


def normalized_text(row: dict[str, Any]) -> str:
    return " ".join(str(row.get("sanitized_buyer_text") or "").casefold().split())


def contamination_recheck() -> dict[str, Any]:
    paths = {
        "mixed_train": DATASET_DIR / "mixed_train.jsonl",
        "validation": DATASET_DIR / "validation.jsonl",
        "test": DATASET_DIR / "test.jsonl",
        "ood_test": DATASET_DIR / "ood_test.jsonl",
    }
    if not all(path.is_file() for path in paths.values()):
        return {"passed": False, "reason": "missing split files"}
    mixed = read_jsonl(paths["mixed_train"])
    heldout = [*read_jsonl(paths["validation"]), *read_jsonl(paths["test"]), *read_jsonl(paths["ood_test"])]
    heldout_ids = {str(row.get("case_id") or "") for row in heldout}
    heldout_texts = {normalized_text(row) for row in heldout}
    leaks = [
        str(row.get("case_id") or "")
        for row in mixed
        if str(row.get("mixed_replay_source_case_id") or row.get("original_case_id") or "") in heldout_ids
        or normalized_text(row) in heldout_texts
    ]
    return {"passed": not leaks, "leak_count": len(leaks), "leak_case_ids": leaks[:25]}


def eval_metrics_reported(eval_result: dict[str, Any]) -> bool:
    return bool(eval_result.get("validation_metrics")) and bool(eval_result.get("test_metrics")) and bool(eval_result.get("ood_metrics"))


def write_report(result: dict[str, Any]) -> None:
    lines = [
        f"# {EXPERIMENT_ID}",
        "",
        f"- status: {result.get('status')}",
        f"- pass: {str(result.get('pass')).lower()}",
        f"- blocker_count: {len(result.get('blockers') or [])}",
        f"- warning_count: {len(result.get('warnings') or [])}",
        f"- quality_gate_passed: {str(result.get('quality_gate_passed')).lower()}",
        f"- adapter_live_ready: {str(result.get('adapter_live_ready')).lower()}",
        f"- live_wiring_allowed: {str(result.get('live_wiring_allowed')).lower()}",
        "",
        "## Blockers",
        "",
        *(f"- {item}" for item in result.get("blockers") or []),
        "",
        "## Warnings",
        "",
        *(f"- {item}" for item in result.get("warnings") or []),
        "",
        "## Metrics",
        "",
        json.dumps(result.get("metrics") or {}, indent=2, ensure_ascii=False),
    ]
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    dataset_result = read_json(DATASET_DIR / "result.json")
    training_result = read_json(TRAINING_DIR / "result.json")
    eval_result = read_json(EVAL_DIR / "result.json")
    blockers: list[str] = []
    warnings: list[str] = []
    for path in (
        DATASET_DIR / "mixed_train.jsonl",
        DATASET_DIR / "validation.jsonl",
        DATASET_DIR / "test.jsonl",
        DATASET_DIR / "ood_test.jsonl",
        DATASET_DIR / "result.json",
        TRAINING_DIR / "result.json",
        EVAL_DIR / "result.json",
    ):
        if not path.is_file():
            blockers.append(f"missing required evidence: {rel(path)}")

    contamination = contamination_recheck()
    if not contamination.get("passed"):
        blockers.append(f"held-out contamination detected: {contamination}")
    if dataset_result.get("status") != "pass":
        blockers.append("mixed replay dataset result is not pass")
    if dataset_result.get("raw_private_transcript_included"):
        blockers.append("mixed replay dataset includes raw private transcript flag")
    if training_result.get("training_completed"):
        adapter_path = str(training_result.get("adapter_path") or "")
        if not adapter_path.startswith("local_artifacts/adapters/"):
            blockers.append("completed adapter path is not under local_artifacts/adapters")
        elif not (safe_project_path(adapter_path) / "adapter_config.json").is_file():
            blockers.append("training completed but adapter_config.json is missing")
    else:
        warnings.append(f"training not completed: {training_result.get('status')} {training_result.get('exact_blocker')}")
    if not eval_metrics_reported(eval_result):
        blockers.append("evaluation metrics were not reported for validation/test/OOD")
    for key in ("provider_calls_made", "openai_api_calls_made", "live_tts_calls_made", "provider_side_effects_made"):
        if training_result.get(key) or eval_result.get(key) or dataset_result.get(key):
            blockers.append(f"side effect flag true: {key}")
    for key in ("runtime_behavior_changed", "response_text_changed", "raw_private_transcript_copied_to_public_evidence"):
        if training_result.get(key) or eval_result.get(key) or dataset_result.get(key):
            blockers.append(f"integrity flag true: {key}")
    tracked_weights = tracked_weight_files()
    if tracked_weights:
        blockers.append(f"model/adapter/checkpoint weights tracked by git: {tracked_weights[:10]}")
    files_changed = changed_files()
    runtime_behavior_changed = any(
        path.startswith("runtime/") and not path.startswith("runtime/llm_brain/training/")
        for path in files_changed
    )
    if runtime_behavior_changed:
        blockers.append("runtime behavior file changed outside runtime/llm_brain/training")
    response_text_changed = any(path.startswith("runtime/dialogue") or path.startswith("runtime/responses") for path in files_changed)
    if response_text_changed:
        blockers.append("response text file changed")
    quality_gate_passed = bool(eval_result.get("quality_gate_passed"))
    adapter_live_ready = bool(eval_result.get("adapter_live_ready"))
    if adapter_live_ready and not quality_gate_passed:
        blockers.append("adapter_live_ready true while quality gate is false")
    if eval_result.get("live_wiring_allowed"):
        blockers.append("live wiring allowed true")
    if not quality_gate_passed:
        warnings.append("quality gate did not pass; evidence validator allows this because no readiness claim is required")

    result = {
        "experiment_id": EXPERIMENT_ID,
        "generated_at": utc_now(),
        "status": "pass" if not blockers else "fail",
        "pass": not blockers,
        "blockers": blockers,
        "warnings": warnings,
        "dataset_status": dataset_result.get("status"),
        "training_status": training_result.get("status"),
        "training_completed": training_result.get("training_completed"),
        "eval_status": eval_result.get("status"),
        "quality_gate_passed": quality_gate_passed,
        "adapter_live_ready": adapter_live_ready,
        "live_wiring_allowed": bool(eval_result.get("live_wiring_allowed")),
        "adapter_files_committed": bool(tracked_weights),
        "tracked_weight_files": tracked_weights,
        "changed_files": files_changed,
        "held_out_contamination": contamination,
        "metrics": {
            "validation": eval_result.get("validation_metrics"),
            "test": eval_result.get("test_metrics"),
            "ood": eval_result.get("ood_metrics"),
        },
        "provider_calls_made": False,
        "openai_api_calls_made": False,
        "live_tts_calls_made": False,
        "provider_side_effects_made": False,
        "runtime_behavior_changed": runtime_behavior_changed,
        "response_text_changed": response_text_changed,
    }
    write_json(RESULT_PATH, result)
    write_report(result)
    print(json.dumps({"status": result["status"], "blockers": blockers, "warnings": warnings}, indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
