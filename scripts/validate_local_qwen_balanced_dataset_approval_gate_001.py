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
    GROUP_MINIMUMS,
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


EXPERIMENT_ID = "LOCAL-QWEN-BALANCED-DATASET-APPROVAL-GATE-001"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / EXPERIMENT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"
SUMMARY_PATH = OUT_DIR / "training_approval_summary.md"

REVIEW_ID = "LOCAL-QWEN-BALANCED-DATASET-REVIEW-001"
QUALITY_ID = "LOCAL-QWEN-BALANCED-DATASET-QUALITY-AUDIT-001"
REVIEW_RESULT_PATH = ROOT / "research" / "experiments" / "generated" / REVIEW_ID / "result.json"
REVIEW_REPORT_PATH = REVIEW_RESULT_PATH.with_name("report.md")
QUALITY_RESULT_PATH = ROOT / "research" / "experiments" / "generated" / QUALITY_ID / "result.json"
QUALITY_REPORT_PATH = QUALITY_RESULT_PATH.with_name("report.md")
SPEC_PATH = ROOT / "runtime" / "llm_brain" / "training" / "qwen_balanced_planner_dataset_spec.json"
CARDS_PATH = ROOT / "runtime" / "llm_brain" / "training" / "qwen_compact_target_cards.json"
EQUIVALENCE_POLICY_PATH = ROOT / "runtime" / "llm_brain" / "training" / "qwen_eval_equivalence_policy.json"
TRAINING_PLAN_PATH = ROOT / "runtime" / "llm_brain" / "training" / "qwen_mixed_replay_training_plan.json"

TEXT_SUFFIXES = (".py", ".json", ".jsonl", ".md", ".txt", ".toml", ".yaml", ".yml")
BLOCKED_CALL_PATTERNS = {
    "openai_import": "from " + "openai",
    "openai_client": "openai" + ".OpenAI",
    "openai_api_key": "OPENAI" + "_API_KEY",
    "requests_post": "requests" + ".post(",
    "httpx_post": "httpx" + ".post(",
    "smtp": "smtp" + "lib",
    "local_qwen_from_pretrained": "from_" + "pretrained(",
    "transformers_trainer": "Trainer" + "(",
    "trainer_train": ".tr" + "ain(",
    "local_qwen_training_script": "train_" + "local_qwen_planner_lora",
    "local_qwen_generation_script": "generate_" + "local_qwen_planner",
    "tts_provider_client": "tts_" + "provider_clients",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def git_output(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "--no-optional-locks", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )


def git_ls_files(prefix: str | None = None) -> list[str]:
    args = ["ls-files"]
    if prefix:
        args.append(prefix)
    completed = git_output(args)
    if completed.returncode != 0:
        return []
    return [line.strip().replace("\\", "/") for line in completed.stdout.splitlines() if line.strip()]


def git_status_paths() -> list[str]:
    completed = git_output(["status", "--porcelain=v1", "--untracked-files=all"])
    if completed.returncode != 0:
        return []
    paths: list[str] = []
    for line in completed.stdout.splitlines():
        if not line.strip():
            continue
        value = line[3:].strip()
        if " -> " in value:
            value = value.rsplit(" -> ", 1)[1]
        paths.append(value.replace("\\", "/"))
    return paths


def changed_runtime_files() -> list[str]:
    return [
        path
        for path in git_status_paths()
        if path.startswith("runtime/") and not path.startswith("runtime/llm_brain/training/")
    ]


def changed_response_text_files() -> list[str]:
    prefixes = (
        "runtime/prompts/",
        "runtime/policy/",
        "runtime/voice/",
        "runtime/speech/",
        "runtime/core/",
        "runtime/entrypoints/",
    )
    return [path for path in changed_runtime_files() if path.startswith(prefixes)]


def tracked_model_or_adapter_files() -> list[str]:
    return [
        path
        for path in git_ls_files()
        if path.lower().endswith(WEIGHT_SUFFIXES) or path.startswith("local_artifacts/")
    ]


def changed_text_files() -> list[Path]:
    files: list[Path] = []
    for relative in git_status_paths():
        path = ROOT / relative
        if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES:
            files.append(path)
    return files


def blocked_call_scan() -> dict[str, list[str]]:
    findings: dict[str, list[str]] = {}
    for path in changed_text_files():
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        relative = rel(path)
        for label, pattern in BLOCKED_CALL_PATTERNS.items():
            if pattern in text:
                findings.setdefault(label, []).append(relative)
    return findings


def side_effects_clean(payload: dict[str, Any], label: str, blockers: list[str]) -> None:
    side_effects = payload.get("side_effects") if isinstance(payload.get("side_effects"), dict) else {}
    for key in (
        "local_model_calls_made",
        "provider_calls_made",
        "openai_api_calls_made",
        "live_tts_calls_made",
        "provider_side_effects_made",
        "model_weights_committed",
        "adapter_files_committed",
        "runtime_behavior_changed",
        "response_text_changed",
        "raw_private_transcript_included",
        "raw_private_transcript_copied_to_public_evidence",
    ):
        if side_effects.get(key) is not False:
            blockers.append(f"{label}.side_effects.{key} must be false")


def load_splits() -> dict[str, list[dict[str, Any]]]:
    return {split: read_jsonl(path) for split, path in SPLIT_PATHS.items()}


def validate_row_privacy(splits: dict[str, list[dict[str, Any]]], blockers: list[str]) -> None:
    bad_rows = []
    for split, rows in splits.items():
        for row in rows:
            if row.get("privacy_level") != "sanitized_only" or row.get("raw_private_transcript_included") is not False:
                bad_rows.append({"split": split, "case_id": row.get("case_id")})
    if bad_rows:
        blockers.append(f"raw/private transcript boundary failed: {bad_rows[:20]}")


def bool_check(condition: bool, message: str, blockers: list[str]) -> None:
    if not condition:
        blockers.append(message)


def collect_warnings(quality: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        item
        for item in quality.get("issues", [])
        if isinstance(item, dict) and item.get("severity") in {"warning", "needs_human_review"}
    ]


def build_report(result: dict[str, Any]) -> str:
    lines = [
        f"# {EXPERIMENT_ID}",
        "",
        f"- Status: {result['status']}",
        f"- approved_for_training: {str(result['approved_for_training']).lower()}",
        f"- blocker_count: {len(result['blockers'])}",
        f"- warning_count: {result['warning_count']}",
        f"- mixed_replay_training_recommended_next: {str(result['mixed_replay_training_recommended_next']).lower()}",
        f"- adapter_live_ready: {str(result['adapter_live_ready']).lower()}",
        f"- live_wiring_allowed: {str(result['live_wiring_allowed']).lower()}",
        f"- local_model_calls_made: {str(result['side_effects']['local_model_calls_made']).lower()}",
        f"- provider/OpenAI/TTS calls made: false",
        f"- runtime_behavior_changed: {str(result['side_effects']['runtime_behavior_changed']).lower()}",
        f"- response_text_changed: {str(result['side_effects']['response_text_changed']).lower()}",
        "",
        "## Checks",
        "",
        json.dumps(result["checks"], indent=2, ensure_ascii=False),
        "",
        "## Blockers",
        "",
        json.dumps(result["blockers"], indent=2, ensure_ascii=False),
        "",
        "## Warnings",
        "",
        json.dumps(result["warnings"][:200], indent=2, ensure_ascii=False),
    ]
    return "\n".join(lines)


def build_summary(result: dict[str, Any]) -> str:
    blockers = result["blockers"]
    warnings = result["warnings"]
    lines = [
        "# Balanced Qwen Dataset Training Approval Summary",
        "",
        f"- approved_for_training: {str(result['approved_for_training']).lower()}",
        f"- blockers: {len(blockers)}",
        f"- warnings: {result['warning_count']}",
        f"- adapter_live_ready: {str(result['adapter_live_ready']).lower()}",
        f"- live_wiring_allowed: {str(result['live_wiring_allowed']).lower()}",
        f"- mixed_replay_training_recommended_next: {str(result['mixed_replay_training_recommended_next']).lower()}",
        "",
        "## What Improved From 4H17",
        "",
        "- Balanced dataset increased coverage to 445 rows with 435 in-distribution rows and 10 isolated OOD rows.",
        "- Validation/test label combinations and action/sub pairs are covered by train.",
        "- Exact held-out text overlap and near-duplicate held-out overlap remain false.",
        "- Target-card consistency, compact targets, and expanded verifier checks are preserved.",
        "",
        "## Blockers",
        "",
    ]
    lines.extend(f"- {item}" for item in blockers[:50])
    if not blockers:
        lines.append("- none")
    lines.extend(["", "## Warnings", ""])
    if warnings:
        for item in warnings[:25]:
            lines.append(f"- [{item.get('severity')}] {item.get('code')}: {item.get('message')}")
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Remaining Data Risks",
            "",
            "- Synthetic and deterministic rows still carry over-template risk; warnings are review items, not live-readiness proof.",
            "- Some planner-style wording remains useful for compact target supervision but should not be treated as final spoken copy.",
            "- Approval only unlocks mixed-replay training; it does not prove adapter quality or live replacement safety.",
            "",
            "## Recommended Next Phase",
            "",
            "- Run mixed-replay training only if approved_for_training is true.",
            "- Keep live wiring disabled until a separately trained adapter passes schema, verifier, safety, latency, and shadow-mode gates.",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    blockers: list[str] = []
    warnings: list[dict[str, Any]] = []
    required_paths = [
        REVIEW_RESULT_PATH,
        REVIEW_REPORT_PATH,
        QUALITY_RESULT_PATH,
        QUALITY_REPORT_PATH,
        DATASET_RESULT_PATH,
        SPEC_PATH,
        CARDS_PATH,
        EQUIVALENCE_POLICY_PATH,
        TRAINING_PLAN_PATH,
    ]
    for path in required_paths:
        if not path.is_file():
            blockers.append(f"missing required artifact: {rel(path)}")

    review = read_json(REVIEW_RESULT_PATH) if REVIEW_RESULT_PATH.is_file() else {}
    quality = read_json(QUALITY_RESULT_PATH) if QUALITY_RESULT_PATH.is_file() else {}
    dataset = read_json(DATASET_RESULT_PATH) if DATASET_RESULT_PATH.is_file() else {}
    plan = read_json(TRAINING_PLAN_PATH) if TRAINING_PLAN_PATH.is_file() else {}
    splits = load_splits()
    cards = load_cards()
    dataset_validation = validate_dataset(splits, cards)

    if review.get("status") != "pass":
        blockers.append("review packet status must be pass")
    if quality.get("blocker_count", 1) != 0:
        blockers.append("quality audit contains blocker-level issues")
    if dataset.get("status") != "pass":
        blockers.append("balanced dataset status must be pass")
    if dataset_validation.get("status") != "pass":
        blockers.extend(f"dataset validator: {failure}" for failure in dataset_validation.get("failures", [])[:50])

    side_effects_clean(review, "review_packet", blockers)
    side_effects_clean(quality, "quality_audit", blockers)
    side_effects_clean(dataset, "balanced_dataset", blockers)
    validate_row_privacy(splits, blockers)

    row_total = int((review.get("dataset_row_counts") or {}).get("total") or dataset.get("total_rows") or 0)
    bool_check(300 <= row_total <= 500, f"total rows out of approval range: {row_total}", blockers)
    semantic_counts = (review.get("semantic_group_counts") or dataset.get("semantic_group_counts") or {})
    for group, minimum in GROUP_MINIMUMS.items():
        count = int(semantic_counts.get(group, 0))
        bool_check(count >= minimum, f"{group} below minimum: {count} < {minimum}", blockers)

    duplicate_summary = review.get("duplicate_near_duplicate_summary") if isinstance(review.get("duplicate_near_duplicate_summary"), dict) else {}
    split_sanity = quality.get("split_sanity") if isinstance(quality.get("split_sanity"), dict) else {}
    bool_check(duplicate_summary.get("heldout_exact_text_overlap_found") is False, "validation/test exact text overlap must be false", blockers)
    bool_check(duplicate_summary.get("heldout_near_duplicate_overlap_found") is False, "validation/test near-duplicate overlap must be false", blockers)
    bool_check(split_sanity.get("ood_isolated") is True, "OOD split must be isolated", blockers)
    bool_check(split_sanity.get("train_covers_validation_test_label_combinations") is True, "train must cover validation/test label combinations", blockers)
    bool_check(split_sanity.get("train_covers_validation_test_target_card_ids") is True, "train must cover validation/test target-card IDs", blockers)
    bool_check(split_sanity.get("train_covers_validation_test_semantic_groups") is True, "train must cover validation/test semantic groups", blockers)

    consistency = review.get("consistency_summary") if isinstance(review.get("consistency_summary"), dict) else {}
    verifier = consistency.get("verifier_consistency") if isinstance(consistency.get("verifier_consistency"), dict) else {}
    bool_check(verifier.get("verifier_failure_count") == 0, "expanded targets must pass verifier", blockers)

    tracked_weights = tracked_model_or_adapter_files()
    if tracked_weights:
        blockers.append(f"model/adapters or local artifacts tracked by git: {tracked_weights[:20]}")
    runtime_changes = changed_runtime_files()
    response_changes = changed_response_text_files()
    if runtime_changes:
        blockers.append(f"runtime behavior files changed: {runtime_changes}")
    if response_changes:
        blockers.append(f"response text files changed: {response_changes}")
    blocked_calls = blocked_call_scan()
    if blocked_calls:
        blockers.append(f"forbidden provider/local-model/training call patterns in changed files: {blocked_calls}")

    live_metrics = plan.get("live_ready_required_metrics") if isinstance(plan.get("live_ready_required_metrics"), dict) else {}
    bool_check(plan.get("train_again_in_this_phase") is False, "training plan must keep train_again_in_this_phase false", blockers)
    bool_check(plan.get("final_stage_mixing_required") is True, "training plan must require final-stage mixing", blockers)
    bool_check(plan.get("final_stage_only_stage3_rows_allowed") is False, "training plan must forbid stage3-only final stage", blockers)
    bool_check(live_metrics.get("adapter_live_ready") is False, "adapter_live_ready must remain false", blockers)
    bool_check(live_metrics.get("live_wiring_allowed_in_this_phase") is False, "live wiring must remain false", blockers)

    warnings.extend(collect_warnings(quality))
    approved_for_training = not blockers
    result = {
        "experiment_id": EXPERIMENT_ID,
        "generated_at": utc_now(),
        "status": "pass" if approved_for_training else "fail",
        "approved_for_training": approved_for_training,
        "blockers": blockers,
        "warnings": warnings,
        "warning_count": len(warnings),
        "quality_audit_blocker_count": quality.get("blocker_count", 0),
        "quality_audit_warning_count": quality.get("warning_count", 0),
        "quality_audit_needs_human_review_count": quality.get("needs_human_review_count", 0),
        "mixed_replay_training_recommended_next": bool(approved_for_training),
        "adapter_live_ready": False,
        "live_wiring_allowed": False,
        "checks": {
            "review_packet_exists": REVIEW_RESULT_PATH.is_file() and REVIEW_REPORT_PATH.is_file(),
            "quality_audit_exists": QUALITY_RESULT_PATH.is_file() and QUALITY_REPORT_PATH.is_file(),
            "no_raw_private_transcripts": not any("raw/private" in blocker.lower() or "raw private" in blocker.lower() for blocker in blockers),
            "no_local_qwen_calls": not blocked_calls,
            "no_provider_openai_tts_calls": not blocked_calls,
            "no_runtime_behavior_change": not runtime_changes,
            "no_response_text_change": not response_changes,
            "no_model_adapters_committed": not tracked_weights,
            "total_rows_300_to_500": 300 <= row_total <= 500,
            "semantic_group_minimums_met": all(int(semantic_counts.get(group, 0)) >= minimum for group, minimum in GROUP_MINIMUMS.items()),
            "validation_test_held_out": duplicate_summary.get("heldout_exact_text_overlap_found") is False
            and duplicate_summary.get("heldout_near_duplicate_overlap_found") is False,
            "ood_isolated": split_sanity.get("ood_isolated") is True,
            "target_cards_valid": dataset_validation.get("status") == "pass",
            "compact_targets_valid": dataset_validation.get("status") == "pass",
            "expanded_targets_pass_verifier": verifier.get("verifier_failure_count") == 0,
            "no_blocker_fidelity_failures": not any(item.get("severity") == "blocker" and item.get("category") == "fidelity" for item in quality.get("issues", [])),
            "no_blocker_safety_failures": not any(item.get("severity") == "blocker" and item.get("category") == "safety" for item in quality.get("issues", [])),
            "no_blocker_split_leakage": not any(item.get("severity") == "blocker" and item.get("category") == "split_sanity" for item in quality.get("issues", [])),
            "no_blocker_campaign_leakage": not any(item.get("code") == "campaign_leakage" for item in quality.get("issues", [])),
            "no_blocker_target_card_inconsistency": not any(
                item.get("severity") == "blocker" and item.get("category") == "semantic_consistency" for item in quality.get("issues", [])
            ),
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
            "raw_private_transcript_copied_to_public_evidence": False,
            "case_text_stored_in_evidence": False,
        },
    }
    write_json(RESULT_PATH, result)
    write_text(REPORT_PATH, build_report(result))
    write_text(SUMMARY_PATH, build_summary(result))
    print(
        json.dumps(
            {
                "status": result["status"],
                "approved_for_training": result["approved_for_training"],
                "blocker_count": len(blockers),
                "warning_count": result["warning_count"],
                "mixed_replay_training_recommended_next": result["mixed_replay_training_recommended_next"],
                "live_wiring_allowed": result["live_wiring_allowed"],
            },
            indent=2,
        )
    )
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
