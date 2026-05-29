from __future__ import annotations

from non_llm_action_selector_artifact_checks_001 import (
    SHADOW_SAFETY_DIR,
    forbidden_import_failures,
    no_shadow_text_or_runtime_change_failures,
    read_json,
    tracked_weight_failures,
    write_status,
)


def main() -> int:
    failures: list[str] = []
    for path in [SHADOW_SAFETY_DIR / "result.json", SHADOW_SAFETY_DIR / "report.md"]:
        if not path.is_file():
            failures.append(f"missing required artifact: {path}")

    result = read_json(SHADOW_SAFETY_DIR / "result.json")
    if result:
        if result.get("status") != "pass":
            failures.append(f"shadow safety result status is not pass: {result.get('status')}")
        if result.get("safety_blockers_count") != 0:
            failures.append(f"shadow safety blockers must be 0: {result.get('safety_blockers_count')}")
        audit = result.get("audit")
        if not isinstance(audit, dict):
            failures.append("shadow safety result missing audit object")
        else:
            for key, value in audit.items():
                if isinstance(value, int) and value != 0 and key.endswith("_count"):
                    failures.append(f"audit {key} must be 0: {value}")
        failures.extend(no_shadow_text_or_runtime_change_failures(result, "shadow_safety_result"))

    failures.extend(forbidden_import_failures())
    failures.extend(tracked_weight_failures())
    return write_status("validate_non_llm_action_selector_shadow_safety_001", failures)


if __name__ == "__main__":
    raise SystemExit(main())
