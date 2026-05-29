from __future__ import annotations

from non_llm_action_selector_artifact_checks_001 import (
    SHADOW_REPLAY_DIR,
    controlled_label_failures,
    false_flag_failures,
    forbidden_import_failures,
    no_private_or_audio_shadow_failures,
    read_json,
    shadow_replay_rows,
    tracked_weight_failures,
    write_status,
)


def main() -> int:
    failures: list[str] = []
    for path in [SHADOW_REPLAY_DIR / "replay.jsonl", SHADOW_REPLAY_DIR / "result.json", SHADOW_REPLAY_DIR / "report.md"]:
        if not path.is_file():
            failures.append(f"missing required artifact: {path}")

    rows = shadow_replay_rows()
    if len(rows) < 100:
        failures.append(f"shadow replay has fewer than 100 rows: {len(rows)}")
    required_fields = {
        "replay_case_id",
        "source_file",
        "source_case_id",
        "campaign_id",
        "buyer_utterance_text",
        "context",
        "expected_action_id",
        "existing_runtime_action_id",
        "existing_runtime_response_text_available",
        "sanitized",
        "raw_private_data",
    }
    for index, row in enumerate(rows, start=1):
        missing = sorted(required_fields - set(row))
        if missing:
            failures.append(f"shadow_replay[{index}] missing fields: {missing}")
    failures.extend(no_private_or_audio_shadow_failures(rows))
    failures.extend(controlled_label_failures({"shadow_replay": [{"target_action_id": row.get("expected_action_id")} for row in rows if row.get("expected_action_id")]}))

    result = read_json(SHADOW_REPLAY_DIR / "result.json")
    if result:
        if result.get("status") != "pass":
            failures.append(f"shadow replay result status is not pass: {result.get('status')}")
        if result.get("raw_private_data") is not False:
            failures.append("shadow replay result raw_private_data must be false")
        if result.get("audio_data_used") is not False:
            failures.append("shadow replay result audio_data_used must be false")
        failures.extend(
            false_flag_failures(
                result,
                [
                    "provider_calls_made",
                    "openai_api_calls_made",
                    "ultravox_calls_made",
                    "elevenlabs_calls_made",
                    "local_llm_calls_made",
                    "ollama_calls_made",
                    "side_effects_allowed",
                    "buyer_facing_text_generated",
                    "live_runtime_wiring_allowed",
                    "response_text_changed",
                    "runtime_behavior_changed",
                ],
                "shadow_replay_result",
            )
        )

    failures.extend(forbidden_import_failures())
    failures.extend(tracked_weight_failures())
    return write_status("validate_non_llm_action_selector_shadow_replay_001", failures, {"replay_case_count": len(rows)})


if __name__ == "__main__":
    raise SystemExit(main())
