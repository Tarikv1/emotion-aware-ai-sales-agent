from __future__ import annotations

from non_llm_action_selector_artifact_checks_001 import (
    RUNTIME_SHADOW_LOG_DIR,
    RUNTIME_SHADOW_REPLAY_DIR,
    controlled_label_failures,
    forbidden_import_failures,
    read_json,
    runtime_shadow_log_rows,
    tracked_weight_failures,
    write_status,
)


FALSE_FLAGS = [
    "side_effects_allowed",
    "buyer_facing_text_generated",
    "live_runtime_wiring_allowed",
    "response_text_changed",
    "runtime_behavior_changed",
    "provider_calls_made",
    "openai_api_calls_made",
    "ultravox_calls_made",
    "elevenlabs_calls_made",
    "local_llm_calls_made",
    "ollama_calls_made",
]


def false_flag_failures(payload: dict, label: str) -> list[str]:
    return [f"{label}.{key} must be false" for key in FALSE_FLAGS if payload.get(key) is not False]


def main() -> int:
    failures: list[str] = []
    for path in [
        RUNTIME_SHADOW_REPLAY_DIR / "result.json",
        RUNTIME_SHADOW_REPLAY_DIR / "report.md",
        RUNTIME_SHADOW_LOG_DIR / "result.jsonl",
    ]:
        if not path.is_file():
            failures.append(f"missing required artifact: {path}")

    result = read_json(RUNTIME_SHADOW_REPLAY_DIR / "result.json")
    case_results = result.get("case_results") if isinstance(result.get("case_results"), list) else []
    if result:
        if result.get("status") != "pass":
            failures.append(f"runtime shadow replay status is not pass: {result.get('status')}")
        if result.get("replay_case_count", 0) < 100:
            failures.append(f"runtime shadow replay has fewer than 100 cases: {result.get('replay_case_count')}")
        if result.get("selector_valid_action_count") != result.get("replay_case_count"):
            failures.append("runtime shadow replay selector_valid_action_count must equal replay_case_count")
        if result.get("public_evidence_sanitized") is not True:
            failures.append("runtime shadow replay public_evidence_sanitized must be true")
        if result.get("raw_private_data") is not False:
            failures.append("runtime shadow replay raw_private_data must be false")
        if result.get("audio_data_used") is not False:
            failures.append("runtime shadow replay audio_data_used must be false")
        if result.get("safety_blocker_count") != 0:
            failures.append(f"runtime shadow replay safety_blocker_count must be 0: {result.get('safety_blocker_count')}")
        latency = result.get("latency_ms") if isinstance(result.get("latency_ms"), dict) else {}
        for key in ("p50", "p90", "p99", "max"):
            if not isinstance(latency.get(key), (int, float)):
                failures.append(f"runtime shadow replay latency_ms.{key} missing")
        failures.extend(false_flag_failures(result, "runtime_shadow_replay_result"))
        if result.get("should_not_change_runtime") is not True:
            failures.append("runtime shadow replay should_not_change_runtime must be true")

    required_fields = {
        "shadow_record_id",
        "timestamp",
        "mode",
        "evidence_source",
        "campaign_id",
        "turn_id",
        "buyer_utterance_text_sanitized",
        "context_summary",
        "runtime_response_text_available",
        "runtime_action_id_if_available",
        "selector_action_id",
        "selector_confidence",
        "selector_reasons",
        "selector_matched_features",
        "agreement_classification",
        "safety_status",
        "possible_improvement",
        "possible_regression",
        "validation_errors",
        "should_not_change_runtime",
        "live_runtime_wiring_allowed",
        "response_text_changed",
        "runtime_behavior_changed",
    }
    rows = runtime_shadow_log_rows()
    if len(rows) < 100:
        failures.append(f"runtime shadow log has fewer than 100 rows: {len(rows)}")
    for index, row in enumerate(rows, start=1):
        missing = sorted(required_fields - set(row))
        if missing:
            failures.append(f"runtime_shadow_log[{index}] missing fields: {missing}")
        failures.extend(false_flag_failures(row, f"runtime_shadow_log[{index}]"))
        if row.get("should_not_change_runtime") is not True:
            failures.append(f"runtime_shadow_log[{index}].should_not_change_runtime must be true")
        if row.get("validation_errors") not in ([], None):
            failures.append(f"runtime_shadow_log[{index}].validation_errors must be empty")
        source = str(row.get("evidence_source") or "").replace("\\", "/").casefold()
        if "data/private" in source or "private-restricted" in source:
            failures.append(f"runtime_shadow_log[{index}].evidence_source references private data")

    failures.extend(
        controlled_label_failures(
            {
                "runtime_shadow_log": [
                    {"target_action_id": row.get("selector_action_id")}
                    for row in rows
                    if row.get("selector_action_id")
                ],
                "runtime_shadow_replay": [
                    {"target_action_id": row.get("selector_action_id")}
                    for row in case_results
                    if row.get("selector_action_id")
                ],
            }
        )
    )
    failures.extend(forbidden_import_failures())
    failures.extend(tracked_weight_failures())
    return write_status(
        "validate_non_llm_action_selector_runtime_shadow_replay_001",
        failures,
        {"replay_case_count": result.get("replay_case_count", 0), "log_row_count": len(rows)},
    )


if __name__ == "__main__":
    raise SystemExit(main())
