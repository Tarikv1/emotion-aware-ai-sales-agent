#!/usr/bin/env python3
from __future__ import annotations

import json

from prosody_quality_common import (
    DRY_RUN_AUDIT_DIR,
    assert_common_no_side_effects,
    load_json,
)


def main() -> int:
    failures: list[str] = []
    result_path = DRY_RUN_AUDIT_DIR / "result.json"
    report_path = DRY_RUN_AUDIT_DIR / "report.md"
    if not result_path.is_file():
        failures.append(f"missing file: {result_path}")
    if not report_path.is_file():
        failures.append(f"missing file: {report_path}")
    result = load_json(result_path) if result_path.is_file() else {}
    if int(result.get("case_count") or 0) != 60:
        failures.append("planner dry-run audit must cover exactly 60 cases")
    if int(result.get("unsafe_label_case_count") or 0) != 0:
        failures.append("planner selected unsafe labels")
    if result.get("spoken_text_tag_injection_allowed") is not False:
        failures.append("spoken text tag injection must be false")
    cases = result.get("cases", [])
    if not isinstance(cases, list) or len(cases) != 60:
        failures.append("planner dry-run cases must be a 60-item list")
    for case in cases:
        if case.get("spoken_text_tag_injection_allowed") is not False:
            failures.append(f"{case.get('case_id')}: tag injection not blocked")
        if case.get("unsafe_labels_selected") is not False:
            failures.append(f"{case.get('case_id')}: unsafe labels selected")
    failures.extend(assert_common_no_side_effects(result))
    output = {
        "status": "pass" if not failures else "fail",
        "result": str(result_path),
        "dry_run_status_counts": result.get("dry_run_status_counts"),
        "failures": failures,
    }
    print(json.dumps(output, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
