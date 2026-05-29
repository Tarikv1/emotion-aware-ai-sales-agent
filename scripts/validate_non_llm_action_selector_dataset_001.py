from __future__ import annotations

from non_llm_action_selector_artifact_checks_001 import (
    DATASET_DIR,
    DATA_SOURCES_DIR,
    controlled_label_failures,
    dataset_rows,
    exact_overlap_failures,
    false_flag_failures,
    forbidden_import_failures,
    no_private_or_audio_failures,
    read_json,
    tracked_weight_failures,
    write_status,
)


def main() -> int:
    failures: list[str] = []
    for path in [
        DATA_SOURCES_DIR / "result.json",
        DATA_SOURCES_DIR / "report.md",
        DATASET_DIR / "train.jsonl",
        DATASET_DIR / "validation.jsonl",
        DATASET_DIR / "test.jsonl",
        DATASET_DIR / "result.json",
        DATASET_DIR / "report.md",
    ]:
        if not path.is_file():
            failures.append(f"missing required artifact: {path}")

    rows_by_split = dataset_rows()
    split_counts = {split: len(rows) for split, rows in rows_by_split.items()}
    if split_counts.get("train", 0) <= 0:
        failures.append("train split is empty")
    if split_counts.get("validation", 0) <= 0:
        failures.append("validation split is empty")
    if split_counts.get("test", 0) <= 0:
        failures.append("test split is empty")
    if sum(split_counts.values()) < 200:
        failures.append(f"dataset has fewer than 200 rows: {sum(split_counts.values())}")

    failures.extend(no_private_or_audio_failures(rows_by_split))
    failures.extend(exact_overlap_failures(rows_by_split))
    failures.extend(controlled_label_failures(rows_by_split))
    failures.extend(forbidden_import_failures())
    failures.extend(tracked_weight_failures())

    result = read_json(DATASET_DIR / "result.json")
    if result:
        if result.get("status") != "pass":
            failures.append(f"dataset result status is not pass: {result.get('status')}")
        failures.extend(
            false_flag_failures(
                result,
                [
                    "provider_calls_made",
                    "openai_api_calls_made",
                    "ultravox_calls_made",
                    "elevenlabs_calls_made",
                    "local_llm_calls_made",
                    "ollama_calls_made",
                    "model_training_performed",
                    "live_runtime_wiring_allowed",
                    "runtime_behavior_changed",
                    "response_text_changed",
                ],
                "dataset_result",
            )
        )

    return write_status(
        "validate_non_llm_action_selector_dataset_001",
        failures,
        {"split_counts": split_counts},
    )


if __name__ == "__main__":
    raise SystemExit(main())
