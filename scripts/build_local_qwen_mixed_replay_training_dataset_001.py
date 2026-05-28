#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
import copy
import hashlib
import json
import math
from pathlib import Path
import random
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.llm_brain.compact_planner_contract import (  # noqa: E402
    compact_label_quality_issues,
    validate_compact_value_contract,
)
from runtime.llm_brain.conversation_brain_schema import (  # noqa: E402
    expand_compact_planner_output,
    validate_compact_conversation_brain_output,
)
from runtime.llm_brain.conversation_brain_verifier import verify_conversation_brain_output  # noqa: E402
from scripts.train_local_qwen_planner_lora_001 import read_jsonl, rel, safe_project_path  # noqa: E402


EXPERIMENT_ID = "LOCAL-QWEN-MIXED-REPLAY-TRAINING-DATASET-001"
BALANCED_DATASET_ID = "LOCAL-QWEN-BALANCED-SFT-DATASET-001"
TINY_DATASET_ID = "LOCAL-QWEN-TINY-OVERFIT-DATASET-001"
ORIGINAL_DATASET_ID = "LOCAL-QWEN-SFT-DATASET-001"
BALANCED_DIR = ROOT / "research" / "experiments" / "generated" / BALANCED_DATASET_ID
TINY_TRAIN_PATH = ROOT / "research" / "experiments" / "generated" / TINY_DATASET_ID / "train.jsonl"
ORIGINAL_TRAIN_PATH = ROOT / "research" / "experiments" / "generated" / ORIGINAL_DATASET_ID / "train.jsonl"
PLAN_PATH = ROOT / "runtime" / "llm_brain" / "training" / "qwen_mixed_replay_training_plan.json"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / EXPERIMENT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"
SPLITS = ("train", "validation", "test", "ood_test")
SEED = 42020


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


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")


def normalized_text(row: dict[str, Any]) -> str:
    text = str(row.get("sanitized_buyer_text") or "")
    return " ".join(text.casefold().split())


def compact_target(row: dict[str, Any]) -> dict[str, Any]:
    target = row.get("target_compact_json")
    return target if isinstance(target, dict) else {}


def target_signature(row: dict[str, Any]) -> str:
    target = compact_target(row)
    fields = (
        str(row.get("target_card_id") or ""),
        str(target.get("act") or ""),
        str(target.get("sub") or ""),
        str(target.get("action") or ""),
        str(target.get("strategy") or ""),
    )
    return "|".join(fields)


def row_hash(row: dict[str, Any]) -> str:
    payload = {
        "case_id": row.get("case_id"),
        "text": normalized_text(row),
        "target": compact_target(row),
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def validate_row(row: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    target = compact_target(row)
    if not target:
        return ["missing target_compact_json"]
    failures.extend(f"compact_schema:{item}" for item in validate_compact_conversation_brain_output(target))
    failures.extend(f"compact_contract:{item}" for item in validate_compact_value_contract(target))
    failures.extend(
        f"compact_label:{item.get('field')}:{item.get('issue')}:{item.get('value')}"
        for item in compact_label_quality_issues(target)
    )
    expanded, adapter_errors = expand_compact_planner_output(target)
    failures.extend(f"compact_adapter:{item}" for item in adapter_errors)
    if not adapter_errors:
        failures.extend(f"verifier:{item}" for item in verify_conversation_brain_output(expanded, row))
    if row.get("raw_private_transcript_included") is not False:
        failures.append("raw_private_transcript_included_not_false")
    return failures


def load_split(name: str) -> list[dict[str, Any]]:
    return read_jsonl(BALANCED_DIR / f"{name}.jsonl")


def group_counts(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(key) or "") for row in rows).items()))


def pick_equivalent_train_rows(train_rows: list[dict[str, Any]], anchor_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    by_card: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_core: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in train_rows:
        target = compact_target(row)
        by_card[str(row.get("target_card_id") or "")].append(row)
        by_core[
            (
                str(target.get("act") or ""),
                str(target.get("sub") or ""),
                str(target.get("action") or ""),
                str(target.get("strategy") or ""),
            )
        ].append(row)

    selected: list[dict[str, Any]] = []
    missing: list[str] = []
    seen: set[str] = set()
    for anchor in anchor_rows:
        target = compact_target(anchor)
        card_id = str(anchor.get("target_card_id") or "")
        candidates = by_card.get(card_id) or by_core.get(
            (
                str(target.get("act") or ""),
                str(target.get("sub") or ""),
                str(target.get("action") or ""),
                str(target.get("strategy") or ""),
            ),
            [],
        )
        if not candidates:
            missing.append(str(anchor.get("case_id") or card_id or target_signature(anchor)))
            continue
        chosen = sorted(candidates, key=lambda item: str(item.get("case_id") or ""))[0]
        case_id = str(chosen.get("case_id") or "")
        if case_id not in seen:
            selected.append(chosen)
            seen.add(case_id)
    return selected, missing


def build_mixed_train(train_rows: list[dict[str, Any]], plan: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rng = random.Random(SEED)
    semantic_weights = plan.get("semantic_group_weights") if isinstance(plan.get("semantic_group_weights"), dict) else {}
    replay_weights = plan.get("replay_weights") if isinstance(plan.get("replay_weights"), dict) else {}
    by_group: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in train_rows:
        by_group[str(row.get("semantic_group") or "unknown")].append(row)
    max_group_count = max((len(rows) for rows in by_group.values()), default=0)
    group_targets: dict[str, int] = {}
    for group, rows in by_group.items():
        weight = float(semantic_weights.get(group, 1.0) or 1.0)
        group_targets[group] = max(len(rows), int(math.ceil(max_group_count * min(weight, 1.5))))

    tiny_rows = read_jsonl(TINY_TRAIN_PATH) if TINY_TRAIN_PATH.is_file() else []
    original_rows = read_jsonl(ORIGINAL_TRAIN_PATH) if ORIGINAL_TRAIN_PATH.is_file() else []
    tiny_equivalents, tiny_missing = pick_equivalent_train_rows(train_rows, tiny_rows)
    original_equivalents, original_missing = pick_equivalent_train_rows(train_rows, original_rows)
    priority_case_roles: dict[str, set[str]] = defaultdict(set)
    for row in tiny_equivalents:
        priority_case_roles[str(row.get("case_id") or "")].add("tiny_core_equivalent")
    for row in original_equivalents:
        priority_case_roles[str(row.get("case_id") or "")].add("original_gold_equivalent")

    mixed_rows: list[dict[str, Any]] = []
    replay_instances: Counter[str] = Counter()

    def append_replay(source_row: dict[str, Any], role: str, weight: float) -> None:
        original_case_id = str(source_row.get("case_id") or "")
        replay_instances[original_case_id] += 1
        instance = replay_instances[original_case_id]
        row = copy.deepcopy(source_row)
        row["original_case_id"] = original_case_id
        row["case_id"] = f"mixed_replay_{len(mixed_rows) + 1:04d}__{original_case_id}"
        row["mixed_replay_source_case_id"] = original_case_id
        row["mixed_replay_instance"] = instance
        row["mixed_replay_strategy"] = "mixed_replay_balanced_sampling"
        row["replay_role"] = role
        row["replay_weight"] = weight
        row["validation_test_held_out"] = True
        row["ood_test_separate"] = True
        row["raw_private_transcript_included"] = False
        mixed_rows.append(row)

    for row in sorted(train_rows, key=lambda item: (str(item.get("semantic_group") or ""), str(item.get("case_id") or ""))):
        case_id = str(row.get("case_id") or "")
        roles = priority_case_roles.get(case_id)
        if roles:
            for role in sorted(roles):
                append_replay(row, role, float(replay_weights.get("tiny_overfit_examples" if role.startswith("tiny") else "original_80_gold_rows", 1.0)))
        append_replay(row, "balanced_expanded", float(replay_weights.get("balanced_expanded_rows", 1.0)))

    for group in sorted(by_group):
        rows = list(by_group[group])
        rng.shuffle(rows)
        current = sum(1 for item in mixed_rows if item.get("semantic_group") == group)
        target_count = group_targets[group]
        index = 0
        while current < target_count:
            append_replay(rows[index % len(rows)], "semantic_balance_oversample", float(semantic_weights.get(group, 1.0) or 1.0))
            current += 1
            index += 1

    rng.shuffle(mixed_rows)
    for index, row in enumerate(mixed_rows, start=1):
        original_case_id = str(row.get("mixed_replay_source_case_id") or row.get("original_case_id") or "")
        row["case_id"] = f"mixed_replay_{index:04d}__{original_case_id}"
    metadata = {
        "seed": SEED,
        "group_targets": group_targets,
        "tiny_anchor_rows_available": len(tiny_rows),
        "tiny_core_equivalent_train_rows": len(tiny_equivalents),
        "tiny_core_missing_from_train": tiny_missing,
        "original_anchor_rows_available": len(original_rows),
        "original_gold_equivalent_train_rows": len(original_equivalents),
        "original_gold_missing_from_train": original_missing,
        "replay_role_counts": group_counts(mixed_rows, "replay_role"),
    }
    return mixed_rows, metadata


def contamination_check(mixed_rows: list[dict[str, Any]], heldout_rows: list[dict[str, Any]]) -> dict[str, Any]:
    heldout_case_ids = {str(row.get("case_id") or "") for row in heldout_rows}
    heldout_texts = {normalized_text(row) for row in heldout_rows}
    heldout_hashes = {row_hash(row) for row in heldout_rows}
    leaked_case_ids = sorted(
        {
            str(row.get("mixed_replay_source_case_id") or row.get("original_case_id") or row.get("case_id") or "")
            for row in mixed_rows
            if str(row.get("mixed_replay_source_case_id") or row.get("original_case_id") or row.get("case_id") or "") in heldout_case_ids
        }
    )
    leaked_text_case_ids = sorted(
        str(row.get("case_id") or "") for row in mixed_rows if normalized_text(row) in heldout_texts
    )
    leaked_hash_case_ids = sorted(
        str(row.get("case_id") or "") for row in mixed_rows if row_hash(row) in heldout_hashes
    )
    return {
        "held_out_case_id_leak_count": len(leaked_case_ids),
        "held_out_text_overlap_count": len(leaked_text_case_ids),
        "held_out_exact_row_hash_overlap_count": len(leaked_hash_case_ids),
        "held_out_case_ids_in_mixed_train": leaked_case_ids[:25],
        "held_out_text_overlap_case_ids": leaked_text_case_ids[:25],
        "held_out_exact_row_hash_overlap_case_ids": leaked_hash_case_ids[:25],
        "passed": not leaked_case_ids and not leaked_text_case_ids and not leaked_hash_case_ids,
    }


def write_report(result: dict[str, Any]) -> None:
    lines = [
        f"# {EXPERIMENT_ID}",
        "",
        f"- status: {result.get('status')}",
        f"- mixed_train_row_count: {result.get('mixed_train_row_count')}",
        f"- source_train_row_count: {result.get('source_train_row_count')}",
        f"- held_out_contamination_passed: {str((result.get('held_out_contamination') or {}).get('passed')).lower()}",
        f"- validation_untouched: {str(result.get('validation_untouched')).lower()}",
        f"- test_untouched: {str(result.get('test_untouched')).lower()}",
        f"- ood_test_untouched: {str(result.get('ood_test_untouched')).lower()}",
        f"- raw_private_transcript_included: {str(result.get('raw_private_transcript_included')).lower()}",
        "",
        "## Semantic Groups",
        "",
        json.dumps(result.get("semantic_group_counts") or {}, indent=2, ensure_ascii=False),
        "",
        "## Source Types",
        "",
        json.dumps(result.get("source_type_counts") or {}, indent=2, ensure_ascii=False),
        "",
        "## Replay Weighting",
        "",
        json.dumps(result.get("replay_weighting_summary") or {}, indent=2, ensure_ascii=False),
        "",
        "## Held-Out Contamination",
        "",
        json.dumps(result.get("held_out_contamination") or {}, indent=2, ensure_ascii=False),
    ]
    REPORT_PATH.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    plan = read_json(PLAN_PATH)
    splits = {name: load_split(name) for name in SPLITS}
    train_rows = splits["train"]
    mixed_train, replay_metadata = build_mixed_train(train_rows, plan)
    validation_failures = {
        str(row.get("case_id") or f"row_{index}"): failures
        for index, row in enumerate(mixed_train, start=1)
        if (failures := validate_row(row))
    }
    heldout_rows = [*splits["validation"], *splits["test"], *splits["ood_test"]]
    contamination = contamination_check(mixed_train, heldout_rows)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    write_jsonl(OUT_DIR / "mixed_train.jsonl", mixed_train)
    for split in ("validation", "test", "ood_test"):
        write_jsonl(OUT_DIR / f"{split}.jsonl", splits[split])

    result = {
        "experiment_id": EXPERIMENT_ID,
        "generated_at": utc_now(),
        "status": "pass" if not validation_failures and contamination["passed"] else "fail",
        "balanced_dataset_id": BALANCED_DATASET_ID,
        "source_train_path": rel(BALANCED_DIR / "train.jsonl"),
        "source_train_row_count": len(train_rows),
        "mixed_train_path": rel(OUT_DIR / "mixed_train.jsonl"),
        "mixed_train_row_count": len(mixed_train),
        "split_counts": {
            "mixed_train": len(mixed_train),
            "validation": len(splits["validation"]),
            "test": len(splits["test"]),
            "ood_test": len(splits["ood_test"]),
        },
        "semantic_group_counts": group_counts(mixed_train, "semantic_group"),
        "source_type_counts": group_counts(mixed_train, "source_type"),
        "target_card_counts": group_counts(mixed_train, "target_card_id"),
        "replay_weighting_summary": replay_metadata,
        "held_out_contamination": contamination,
        "tiny_core_target_card_coverage": {
            "equivalent_train_rows": replay_metadata["tiny_core_equivalent_train_rows"],
            "missing_anchor_ids": replay_metadata["tiny_core_missing_from_train"],
        },
        "validation_untouched": splits["validation"] == read_jsonl(OUT_DIR / "validation.jsonl"),
        "test_untouched": splits["test"] == read_jsonl(OUT_DIR / "test.jsonl"),
        "ood_test_untouched": splits["ood_test"] == read_jsonl(OUT_DIR / "ood_test.jsonl"),
        "compact_targets_valid": not validation_failures,
        "expanded_targets_verifier_pass": not validation_failures,
        "validation_failures": validation_failures,
        "raw_private_transcript_included": any(row.get("raw_private_transcript_included") is not False for row in mixed_train),
        "local_model_calls_made": False,
        "provider_calls_made": False,
        "openai_api_calls_made": False,
        "live_tts_calls_made": False,
        "runtime_behavior_changed": False,
        "response_text_changed": False,
        "raw_private_transcript_copied_to_public_evidence": False,
    }
    write_json(RESULT_PATH, result)
    write_report(result)
    print(json.dumps({"status": result["status"], "mixed_train_rows": len(mixed_train), "contamination": contamination}, indent=2))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
