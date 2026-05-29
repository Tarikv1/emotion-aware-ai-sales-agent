from __future__ import annotations

from non_llm_action_selector_artifact_checks_001 import (
    RUNTIME_SHADOW_CONFIG_PATH,
    RUNTIME_SHADOW_HOOK_PATH,
    RUNTIME_SHADOW_LOGGER_PATH,
    RUNTIME_SHADOW_POINTS_DIR,
    forbidden_import_failures,
    read_json,
    tracked_weight_failures,
    write_status,
)


def main() -> int:
    failures: list[str] = []
    for path in [
        RUNTIME_SHADOW_POINTS_DIR / "result.json",
        RUNTIME_SHADOW_POINTS_DIR / "report.md",
        RUNTIME_SHADOW_CONFIG_PATH,
        RUNTIME_SHADOW_LOGGER_PATH,
        RUNTIME_SHADOW_HOOK_PATH,
    ]:
        if not path.is_file():
            failures.append(f"missing required artifact: {path}")

    result = read_json(RUNTIME_SHADOW_POINTS_DIR / "result.json")
    if result:
        if result.get("status") != "pass":
            failures.append(f"runtime shadow points status is not pass: {result.get('status')}")
        candidates = result.get("candidate_observation_points")
        if not isinstance(candidates, list) or not candidates:
            failures.append("runtime shadow points missing candidate_observation_points")
        else:
            for index, point in enumerate(candidates, start=1):
                if point.get("can_be_read_only") is not True:
                    failures.append(f"candidate_observation_points[{index}].can_be_read_only must be true")
                if point.get("might_alter_runtime_behavior") is True and point.get("risk_level") not in {"medium", "high"}:
                    failures.append(f"candidate_observation_points[{index}] behavior risk must be labeled")
        if not result.get("recommended_safest_hook_point"):
            failures.append("runtime shadow points missing recommended_safest_hook_point")
        if result.get("implementation_mode_recommendation") not in {"design_only", "disabled_by_default_instrumentation"}:
            failures.append("runtime shadow points must recommend design_only or disabled_by_default_instrumentation")
        if result.get("live_runtime_wiring_allowed") is not False:
            failures.append("runtime shadow points live_runtime_wiring_allowed must be false")
        if result.get("runtime_behavior_changed") is not False:
            failures.append("runtime shadow points runtime_behavior_changed must be false")

    config = read_json(RUNTIME_SHADOW_CONFIG_PATH)
    if config:
        expected_false = [
            "enabled_by_default",
            "live_runtime_wiring_allowed",
            "response_text_change_allowed",
            "runtime_behavior_change_allowed",
            "memory_mutation_allowed",
            "provider_calls_allowed",
            "side_effects_allowed",
            "buyer_facing_text_generation_allowed",
        ]
        for key in expected_false:
            if config.get(key) is not False:
                failures.append(f"runtime shadow config {key} must be false")
        if config.get("env_gate") != "ACTION_SELECTOR_SHADOW_LOGGING_ENABLED=1":
            failures.append("runtime shadow config env_gate mismatch")
        if "live_control" not in set(config.get("disallowed_modes") or []):
            failures.append("runtime shadow config must disallow live_control")

    failures.extend(forbidden_import_failures())
    failures.extend(tracked_weight_failures())
    return write_status("validate_non_llm_action_selector_runtime_shadow_points_001", failures)


if __name__ == "__main__":
    raise SystemExit(main())
