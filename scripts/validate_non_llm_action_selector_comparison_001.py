from __future__ import annotations

from non_llm_action_selector_artifact_checks_001 import (
    COMPARISON_DIR,
    false_flag_failures,
    forbidden_import_failures,
    read_json,
    tracked_weight_failures,
    write_status,
)


def main() -> int:
    failures: list[str] = []
    for path in [COMPARISON_DIR / "result.json", COMPARISON_DIR / "report.md"]:
        if not path.is_file():
            failures.append(f"missing required artifact: {path}")

    result = read_json(COMPARISON_DIR / "result.json")
    if result:
        if result.get("status") != "pass":
            failures.append(f"comparison result status is not pass: {result.get('status')}")
        required = [
            "latency",
            "action_id_validity",
            "malformed_rate",
            "verifier_pass",
            "portability",
            "interpretability",
            "data_training_cost",
            "live_safety_risk",
            "project_owned_selector_candidate",
        ]
        for key in required:
            if key not in result:
                failures.append(f"comparison result missing {key}")
        if result.get("reran_ollama") is not False:
            failures.append("comparison must not rerun Ollama")
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
                    "live_runtime_wiring_allowed",
                    "runtime_behavior_changed",
                    "response_text_changed",
                ],
                "comparison_result",
            )
        )

    failures.extend(forbidden_import_failures())
    failures.extend(tracked_weight_failures())
    return write_status("validate_non_llm_action_selector_comparison_001", failures)


if __name__ == "__main__":
    raise SystemExit(main())
