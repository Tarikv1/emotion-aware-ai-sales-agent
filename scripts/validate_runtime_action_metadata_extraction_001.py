from __future__ import annotations

from non_llm_action_selector_artifact_checks_001 import (
    RUNTIME_ACTION_METADATA_EXTRACTOR_PATH,
    RUNTIME_METADATA_EXTRACTION_DIR,
    controlled_label_failures,
    forbidden_import_failures,
    read_json,
    tracked_weight_failures,
    write_status,
)


def main() -> int:
    failures: list[str] = []
    for path in [
        RUNTIME_ACTION_METADATA_EXTRACTOR_PATH,
        RUNTIME_METADATA_EXTRACTION_DIR / "result.json",
        RUNTIME_METADATA_EXTRACTION_DIR / "report.md",
    ]:
        if not path.is_file():
            failures.append(f"missing required artifact: {path}")

    result = read_json(RUNTIME_METADATA_EXTRACTION_DIR / "result.json")
    cases = result.get("case_results") if isinstance(result.get("case_results"), list) else []
    if result:
        if result.get("status") != "pass":
            failures.append(f"extraction status is not pass: {result.get('status')}")
        if result.get("case_count", 0) < 60:
            failures.append(f"extraction case_count must be at least 60: {result.get('case_count')}")
        if result.get("extraction_success_count") != result.get("case_count"):
            failures.append("extraction_success_count must equal case_count")
        if result.get("action_id_mapped_count") != result.get("case_count"):
            failures.append("action_id_mapped_count must equal case_count")
        if result.get("expected_action_match_count") != result.get("case_count"):
            failures.append("expected_action_match_count must equal case_count")
        if result.get("unmapped_count") != 0:
            failures.append(f"unmapped_count must be 0: {result.get('unmapped_count')}")
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
                failures.append(f"extraction {key} must be false")
        latency = result.get("latency_ms") if isinstance(result.get("latency_ms"), dict) else {}
        for key in ("p50", "p90", "p99"):
            if not isinstance(latency.get(key), (int, float)):
                failures.append(f"extraction latency_ms.{key} missing")

    failures.extend(
        controlled_label_failures(
            {
                "runtime_metadata_extraction": [
                    {"target_action_id": row.get("runtime_action_id")}
                    for row in cases
                    if row.get("runtime_action_id")
                ]
            }
        )
    )
    failures.extend(forbidden_import_failures())
    failures.extend(tracked_weight_failures())
    return write_status(
        "validate_runtime_action_metadata_extraction_001",
        failures,
        {"case_count": result.get("case_count", 0)},
    )


if __name__ == "__main__":
    raise SystemExit(main())
