from __future__ import annotations

from non_llm_action_selector_artifact_checks_001 import (
    SHADOW_DECISION_DIR,
    forbidden_import_failures,
    no_shadow_text_or_runtime_change_failures,
    read_json,
    tracked_weight_failures,
    write_status,
)


def main() -> int:
    failures: list[str] = []
    for path in [SHADOW_DECISION_DIR / "result.json", SHADOW_DECISION_DIR / "report.md"]:
        if not path.is_file():
            failures.append(f"missing required artifact: {path}")

    result = read_json(SHADOW_DECISION_DIR / "result.json")
    if result:
        if result.get("status") != "pass":
            failures.append(f"shadow decision result status is not pass: {result.get('status')}")
        for key in ("recommendation_id", "recommendation", "evidence_summary"):
            if key not in result:
                failures.append(f"shadow decision missing {key}")
        if result.get("claims_live_readiness") is not False:
            failures.append("shadow decision must not claim live readiness")
        failures.extend(no_shadow_text_or_runtime_change_failures(result, "shadow_decision_result"))

    failures.extend(forbidden_import_failures())
    failures.extend(tracked_weight_failures())
    return write_status("validate_non_llm_action_selector_shadow_decision_001", failures)


if __name__ == "__main__":
    raise SystemExit(main())
