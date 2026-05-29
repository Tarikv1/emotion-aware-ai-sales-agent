from __future__ import annotations

from non_llm_action_selector_artifact_checks_001 import (
    RUNTIME_SHADOW_AUDIT_DIR,
    forbidden_import_failures,
    read_json,
    tracked_weight_failures,
    write_status,
)


def main() -> int:
    failures: list[str] = []
    for path in [RUNTIME_SHADOW_AUDIT_DIR / "result.json", RUNTIME_SHADOW_AUDIT_DIR / "report.md"]:
        if not path.is_file():
            failures.append(f"missing required artifact: {path}")

    result = read_json(RUNTIME_SHADOW_AUDIT_DIR / "result.json")
    if result:
        if result.get("status") != "pass":
            failures.append(f"runtime shadow audit status is not pass: {result.get('status')}")
        if result.get("safety_blockers_count") != 0:
            failures.append(f"runtime shadow audit safety_blockers_count must be 0: {result.get('safety_blockers_count')}")
        audit = result.get("audit")
        if not isinstance(audit, dict):
            failures.append("runtime shadow audit missing audit object")
        else:
            for key, value in audit.items():
                if key.endswith("_count") and value != 0:
                    failures.append(f"runtime shadow audit {key} must be 0: {value}")
        for key in [
            "side_effects_allowed",
            "buyer_facing_text_generated",
            "live_runtime_wiring_allowed",
            "response_text_changed",
            "runtime_behavior_changed",
            "memory_mutation_allowed",
            "provider_calls_made",
            "openai_api_calls_made",
            "ultravox_calls_made",
            "elevenlabs_calls_made",
            "local_llm_calls_made",
            "ollama_calls_made",
            "tts_calls_made",
            "raw_private_data",
        ]:
            if result.get(key) is not False:
                failures.append(f"runtime shadow audit {key} must be false")

    failures.extend(forbidden_import_failures())
    failures.extend(tracked_weight_failures())
    return write_status("validate_non_llm_action_selector_runtime_shadow_audit_001", failures)


if __name__ == "__main__":
    raise SystemExit(main())
