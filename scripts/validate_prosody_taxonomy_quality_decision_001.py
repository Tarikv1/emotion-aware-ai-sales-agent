#!/usr/bin/env python3
from __future__ import annotations

import json

from prosody_quality_common import (
    QUALITY_DECISION_DIR,
    assert_common_no_side_effects,
    load_json,
)


def main() -> int:
    failures: list[str] = []
    result_path = QUALITY_DECISION_DIR / "result.json"
    report_path = QUALITY_DECISION_DIR / "report.md"
    if not result_path.is_file():
        failures.append(f"missing file: {result_path}")
    if not report_path.is_file():
        failures.append(f"missing file: {report_path}")
    decision = load_json(result_path) if result_path.is_file() else {}
    blocker_count = int(decision.get("blocker_count") or 0)
    recommendation = str(decision.get("quality_decision_recommendation") or "").lower()
    if blocker_count and "cleanup" not in recommendation:
        failures.append("blockers exist, but decision does not recommend cleanup")
    if decision.get("live_wiring_allowed") is not False:
        failures.append("decision must keep live_wiring_allowed false")
    if decision.get("elevenlabs_calls_made") is not False:
        failures.append("decision must keep elevenlabs_calls_made false")
    if decision.get("runtime_behavior_changed") is not False:
        failures.append("decision must keep runtime_behavior_changed false")
    if decision.get("response_text_changed") is not False:
        failures.append("decision must keep response_text_changed false")
    if decision.get("does_not_claim_live_readiness") is not True:
        failures.append("decision must not claim live readiness")
    if decision.get("elevenlabs_mapping_prototype_recommended") is True and "no provider calls" not in recommendation:
        failures.append("prototype recommendation must explicitly be no-provider")
    failures.extend(assert_common_no_side_effects(decision))
    output = {
        "status": "pass" if not failures else "fail",
        "result": str(result_path),
        "recommendation": decision.get("quality_decision_recommendation"),
        "taxonomy_cleanup_needed": decision.get("taxonomy_cleanup_needed"),
        "elevenlabs_mapping_prototype_recommended": decision.get("elevenlabs_mapping_prototype_recommended"),
        "failures": failures,
    }
    print(json.dumps(output, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
