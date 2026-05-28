#!/usr/bin/env python3
from __future__ import annotations

import json

from prosody_quality_common import (
    MAPPING_AUDIT_DIR,
    REQUIRED_CONTEXTS,
    assert_common_no_side_effects,
    load_json,
)


def main() -> int:
    failures: list[str] = []
    result_path = MAPPING_AUDIT_DIR / "result.json"
    report_path = MAPPING_AUDIT_DIR / "report.md"
    if not result_path.is_file():
        failures.append(f"missing file: {result_path}")
    if not report_path.is_file():
        failures.append(f"missing file: {report_path}")
    result = load_json(result_path) if result_path.is_file() else {}
    if int(result.get("mapping_count") or 0) < 80:
        failures.append("mapping audit did not cover at least 80 mappings after 4I4 cleanup")
    if result.get("missing_required_contexts"):
        failures.append(f"mapping audit missing contexts: {result.get('missing_required_contexts')}")
    if int(result.get("unsafe_label_mapping_count") or 0) != 0:
        failures.append("mapping audit found selected unsafe labels")
    if result.get("unsafe_labels_blocked") is not True:
        failures.append("unsafe labels must be blocked")
    for key in ("coverage_by_buyer_emotion", "coverage_by_sales_move", "coverage_by_objection_type", "mapping_assessments", "status_counts"):
        if key not in result:
            failures.append(f"mapping audit missing {key}")
    failures.extend(assert_common_no_side_effects(result))
    output = {
        "status": "pass" if not failures else "fail",
        "result": str(result_path),
        "mapping_count": result.get("mapping_count"),
        "status_counts": result.get("status_counts"),
        "failures": failures,
    }
    print(json.dumps(output, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
