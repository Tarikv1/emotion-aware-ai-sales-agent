from __future__ import annotations

from non_llm_action_selector_artifact_checks_001 import (
    RUNTIME_METADATA_SHADOW_DIR,
    controlled_label_failures,
    forbidden_import_failures,
    read_json,
    tracked_weight_failures,
    write_status,
)


def main() -> int:
    failures: list[str] = []
    for path in [RUNTIME_METADATA_SHADOW_DIR / "result.json", RUNTIME_METADATA_SHADOW_DIR / "report.md"]:
        if not path.is_file():
            failures.append(f"missing required artifact: {path}")
    result = read_json(RUNTIME_METADATA_SHADOW_DIR / "result.json")
    cases = result.get("case_results") if isinstance(result.get("case_results"), list) else []
    if result:
        if result.get("status") != "pass":
            failures.append(f"metadata shadow status is not pass: {result.get('status')}")
        if result.get("case_count", 0) < 60:
            failures.append(f"metadata shadow case_count must be at least 60: {result.get('case_count')}")
        if result.get("runtime_action_id_available_count") != result.get("case_count"):
            failures.append("runtime_action_id_available_count must equal case_count")
        if result.get("selector_valid_action_count") != result.get("case_count"):
            failures.append("selector_valid_action_count must equal case_count")
        if result.get("safety_blocker_count") != 0:
            failures.append(f"safety_blocker_count must be 0: {result.get('safety_blocker_count')}")
        for key in [
            "runtime_behavior_changed",
            "response_text_changed",
            "side_effects_allowed",
            "live_runtime_wiring_allowed",
            "memory_mutation_allowed",
            "provider_calls_made",
            "openai_api_calls_made",
            "ultravox_calls_made",
            "elevenlabs_calls_made",
            "local_llm_calls_made",
            "ollama_calls_made",
            "raw_private_data",
        ]:
            if result.get(key) is not False:
                failures.append(f"metadata shadow {key} must be false")
        latency = result.get("latency_ms") if isinstance(result.get("latency_ms"), dict) else {}
        for key in ("p50", "p90", "p99"):
            if not isinstance(latency.get(key), (int, float)):
                failures.append(f"metadata shadow latency_ms.{key} missing")
        for index, row in enumerate(cases, start=1):
            if row.get("runtime_metadata_available") is not True:
                failures.append(f"case_results[{index}].runtime_metadata_available must be true")
            if not row.get("runtime_action_id"):
                failures.append(f"case_results[{index}].runtime_action_id missing")
            if "disagreement_type" not in row:
                failures.append(f"case_results[{index}].disagreement_type missing")

    failures.extend(
        controlled_label_failures(
            {
                "metadata_shadow_runtime": [
                    {"target_action_id": row.get("runtime_action_id")}
                    for row in cases
                    if row.get("runtime_action_id")
                ],
                "metadata_shadow_selector": [
                    {"target_action_id": row.get("selector_action_id")}
                    for row in cases
                    if row.get("selector_action_id")
                ],
            }
        )
    )
    failures.extend(forbidden_import_failures())
    failures.extend(tracked_weight_failures())
    return write_status(
        "validate_runtime_action_metadata_shadow_001",
        failures,
        {"case_count": result.get("case_count", 0)},
    )


if __name__ == "__main__":
    raise SystemExit(main())
