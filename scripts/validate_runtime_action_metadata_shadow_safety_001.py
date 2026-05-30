from __future__ import annotations

from non_llm_action_selector_artifact_checks_001 import (
    RUNTIME_METADATA_SHADOW_AUDIT_DIR,
    forbidden_import_failures,
    read_json,
    tracked_weight_failures,
    write_status,
)


def main() -> int:
    failures: list[str] = []
    for path in [RUNTIME_METADATA_SHADOW_AUDIT_DIR / "result.json", RUNTIME_METADATA_SHADOW_AUDIT_DIR / "report.md"]:
        if not path.is_file():
            failures.append(f"missing required artifact: {path}")
    result = read_json(RUNTIME_METADATA_SHADOW_AUDIT_DIR / "result.json")
    if result:
        if result.get("status") != "pass":
            failures.append(f"metadata shadow safety status is not pass: {result.get('status')}")
        if result.get("safety_blockers_count") != 0:
            failures.append(f"safety_blockers_count must be 0: {result.get('safety_blockers_count')}")
        audit = result.get("audit")
        if not isinstance(audit, dict):
            failures.append("metadata shadow safety missing audit object")
        else:
            for key, value in audit.items():
                if key.endswith("_count") and value != 0:
                    failures.append(f"audit {key} must be 0: {value}")
        for key in [
            "runtime_behavior_changed",
            "response_text_changed",
            "memory_mutation_allowed",
            "provider_calls_made",
            "local_llm_calls_made",
            "buyer_facing_text_generated",
            "side_effects_allowed",
            "raw_private_data",
        ]:
            if result.get(key) is not False:
                failures.append(f"metadata shadow safety {key} must be false")

    failures.extend(forbidden_import_failures())
    failures.extend(tracked_weight_failures())
    return write_status("validate_runtime_action_metadata_shadow_safety_001", failures)


if __name__ == "__main__":
    raise SystemExit(main())
