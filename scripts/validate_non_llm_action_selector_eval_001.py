from __future__ import annotations

from non_llm_action_selector_artifact_checks_001 import (
    EVAL_DIR,
    controlled_label_failures,
    false_flag_failures,
    forbidden_import_failures,
    read_json,
    tracked_weight_failures,
    write_status,
)


def main() -> int:
    failures: list[str] = []
    for path in [EVAL_DIR / "result.json", EVAL_DIR / "report.md"]:
        if not path.is_file():
            failures.append(f"missing required artifact: {path}")

    result = read_json(EVAL_DIR / "result.json")
    if result:
        if result.get("status") != "pass":
            failures.append(f"eval result status is not pass: {result.get('status')}")
        baseline_metrics = result.get("baseline_metrics")
        if not isinstance(baseline_metrics, dict) or "rule_based" not in baseline_metrics:
            failures.append("eval result missing rule_based baseline metrics")
        else:
            rule_metrics = baseline_metrics.get("rule_based") or {}
            for split in ("validation", "test"):
                split_metrics = rule_metrics.get(split)
                if not isinstance(split_metrics, dict):
                    failures.append(f"rule_based metrics missing {split}")
                    continue
                for key in ("accuracy", "macro_f1", "fallback_rate"):
                    if not isinstance(split_metrics.get(key), (int, float)):
                        failures.append(f"rule_based {split}.{key} is missing")
            latency = rule_metrics.get("latency_ms")
            if not isinstance(latency, dict):
                failures.append("rule_based latency_ms is missing")
            else:
                for key in ("p50", "p90", "p99", "max"):
                    if not isinstance(latency.get(key), (int, float)):
                        failures.append(f"rule_based latency_ms.{key} is missing")
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
                "eval_result",
            )
        )

    failures.extend(controlled_label_failures())
    failures.extend(forbidden_import_failures())
    failures.extend(tracked_weight_failures())
    return write_status("validate_non_llm_action_selector_eval_001", failures)


if __name__ == "__main__":
    raise SystemExit(main())
