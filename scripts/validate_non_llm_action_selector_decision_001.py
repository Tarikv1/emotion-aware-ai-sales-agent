from __future__ import annotations

from non_llm_action_selector_artifact_checks_001 import (
    DECISION_DIR,
    false_flag_failures,
    forbidden_import_failures,
    read_json,
    tracked_weight_failures,
    write_status,
)


def main() -> int:
    failures: list[str] = []
    for path in [DECISION_DIR / "result.json", DECISION_DIR / "report.md"]:
        if not path.is_file():
            failures.append(f"missing required artifact: {path}")

    result = read_json(DECISION_DIR / "result.json")
    if result:
        if result.get("status") != "pass":
            failures.append(f"decision result status is not pass: {result.get('status')}")
        for key in [
            "recommendation_id",
            "recommendation",
            "non_llm_selector_role",
            "evidence_summary",
        ]:
            if key not in result:
                failures.append(f"decision result missing {key}")
        if result.get("claims_live_readiness") is not False:
            failures.append("decision must not claim live readiness")
        failures.extend(
            false_flag_failures(
                result,
                [
                    "live_wiring_allowed",
                    "response_text_changed",
                    "runtime_behavior_changed",
                    "provider_calls_made",
                    "openai_api_calls_made",
                    "ultravox_calls_made",
                    "elevenlabs_calls_made",
                    "local_llm_calls_made",
                    "ollama_calls_made",
                    "model_training_performed",
                ],
                "decision_result",
            )
        )

    failures.extend(forbidden_import_failures())
    failures.extend(tracked_weight_failures())
    return write_status("validate_non_llm_action_selector_decision_001", failures)


if __name__ == "__main__":
    raise SystemExit(main())
