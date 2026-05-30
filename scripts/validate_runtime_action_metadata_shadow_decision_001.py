from __future__ import annotations

from non_llm_action_selector_artifact_checks_001 import (
    RUNTIME_METADATA_SHADOW_DECISION_DIR,
    forbidden_import_failures,
    read_json,
    tracked_weight_failures,
    write_status,
)


def main() -> int:
    failures: list[str] = []
    for path in [RUNTIME_METADATA_SHADOW_DECISION_DIR / "result.json", RUNTIME_METADATA_SHADOW_DECISION_DIR / "report.md"]:
        if not path.is_file():
            failures.append(f"missing required artifact: {path}")
    result = read_json(RUNTIME_METADATA_SHADOW_DECISION_DIR / "result.json")
    if result:
        if result.get("status") != "pass":
            failures.append(f"metadata shadow decision status is not pass: {result.get('status')}")
        for key in ("recommendation_id", "recommendation", "evidence_summary"):
            if key not in result:
                failures.append(f"metadata shadow decision missing {key}")
        if result.get("claims_live_readiness") is not False:
            failures.append("metadata shadow decision must not claim live readiness")
        if result.get("live_wiring_allowed") is not False:
            failures.append("metadata shadow decision live_wiring_allowed must be false")
        for key in [
            "response_text_changed",
            "runtime_behavior_changed",
            "provider_calls_made",
            "local_llm_calls_made",
        ]:
            if result.get(key) is not False:
                failures.append(f"metadata shadow decision {key} must be false")

    failures.extend(forbidden_import_failures())
    failures.extend(tracked_weight_failures())
    return write_status("validate_runtime_action_metadata_shadow_decision_001", failures)


if __name__ == "__main__":
    raise SystemExit(main())
