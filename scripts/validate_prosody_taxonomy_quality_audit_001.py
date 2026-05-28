#!/usr/bin/env python3
from __future__ import annotations

import json
import sys

from prosody_quality_common import (
    TAXONOMY_AUDIT_DIR,
    assert_common_no_side_effects,
    load_json,
)


def main() -> int:
    failures: list[str] = []
    result_path = TAXONOMY_AUDIT_DIR / "result.json"
    report_path = TAXONOMY_AUDIT_DIR / "report.md"
    if not result_path.is_file():
        failures.append(f"missing file: {result_path}")
    if not report_path.is_file():
        failures.append(f"missing file: {report_path}")
    result = load_json(result_path) if result_path.is_file() else {}
    for key in (
        "duplicate_label_count",
        "risky_label_count",
        "label_assessments",
        "backend_mapping_boilerplate_label_count",
        "blocker_count",
        "warning_count",
        "unsafe_labels_blocked",
    ):
        if key not in result:
            failures.append(f"taxonomy audit missing {key}")
    if int(result.get("taxonomy_label_count") or 0) < 250:
        failures.append("taxonomy audit did not cover at least 250 labels")
    if result.get("fish_tags_internal_only") is not True:
        failures.append("Fish tags must be internal only")
    if result.get("raw_fish_tags_allowed_in_elevenlabs_text") is not False:
        failures.append("raw Fish tags must not be allowed in ElevenLabs text")
    if result.get("unsafe_labels_blocked") is not True:
        failures.append("unsafe labels are not blocked")
    failures.extend(assert_common_no_side_effects(result))
    output = {
        "status": "pass" if not failures else "fail",
        "result": str(result_path),
        "duplicate_label_count": result.get("duplicate_label_count"),
        "risky_label_count": result.get("risky_label_count"),
        "failures": failures,
    }
    print(json.dumps(output, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
