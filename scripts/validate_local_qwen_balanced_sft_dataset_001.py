#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_local_qwen_balanced_sft_dataset_001 import (  # noqa: E402
    EXPERIMENT_ID,
    REPORT_PATH,
    RESULT_PATH,
    SPLIT_PATHS,
    build_report,
    load_cards,
    read_jsonl,
    validate_dataset,
    write_json,
    write_text,
)


def main() -> int:
    failures: list[str] = []
    splits = {}
    for split, path in SPLIT_PATHS.items():
        if not path.is_file():
            failures.append(f"missing split file: {path.relative_to(ROOT)}")
            splits[split] = []
            continue
        splits[split] = read_jsonl(path)
    cards = load_cards()
    result = validate_dataset(splits, cards)
    if failures:
        result["status"] = "fail"
        result["failures"] = [*failures, *result.get("failures", [])]
    write_json(RESULT_PATH, result)
    write_text(REPORT_PATH, build_report(result))
    print(
        json.dumps(
            {
                "experiment_id": EXPERIMENT_ID,
                "status": result["status"],
                "total_rows": result["total_rows"],
                "split_counts": result["split_counts"],
                "failure_count": len(result["failures"]),
            },
            indent=2,
        )
    )
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
