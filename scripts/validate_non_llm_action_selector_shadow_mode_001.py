from __future__ import annotations

from non_llm_action_selector_artifact_checks_001 import (
    SHADOW_MODE_DIR,
    controlled_label_failures,
    forbidden_import_failures,
    no_shadow_text_or_runtime_change_failures,
    read_json,
    tracked_weight_failures,
    write_status,
)


def main() -> int:
    failures: list[str] = []
    for path in [SHADOW_MODE_DIR / "result.json", SHADOW_MODE_DIR / "report.md"]:
        if not path.is_file():
            failures.append(f"missing required artifact: {path}")

    result = read_json(SHADOW_MODE_DIR / "result.json")
    case_count = 0
    if result:
        if result.get("status") != "pass":
            failures.append(f"shadow mode result status is not pass: {result.get('status')}")
        case_results = result.get("case_results")
        if not isinstance(case_results, list):
            failures.append("shadow mode result missing case_results list")
            case_results = []
        case_count = len(case_results)
        if case_count < 100:
            failures.append(f"shadow mode has fewer than 100 case results: {case_count}")
        for index, row in enumerate(case_results, start=1):
            if row.get("would_change_runtime") is not False:
                failures.append(f"case_results[{index}].would_change_runtime must be false")
            if row.get("buyer_facing_text_generated") is not False:
                failures.append(f"case_results[{index}].buyer_facing_text_generated must be false")
            if row.get("selector_action_id") is None:
                failures.append(f"case_results[{index}].selector_action_id missing")
        metrics = result.get("metrics")
        if not isinstance(metrics, dict):
            failures.append("shadow mode result missing metrics")
        else:
            for key in ("replay_case_count", "selector_valid_action_count", "latency_ms"):
                if key not in metrics:
                    failures.append(f"shadow mode metrics missing {key}")
            latency = metrics.get("latency_ms") if isinstance(metrics.get("latency_ms"), dict) else {}
            for key in ("p50", "p90", "p99", "max"):
                if not isinstance(latency.get(key), (int, float)):
                    failures.append(f"shadow mode latency_ms.{key} missing")
        failures.extend(no_shadow_text_or_runtime_change_failures(result, "shadow_mode_result"))
        failures.extend(controlled_label_failures({"case_results": [{"target_action_id": row.get("selector_action_id")} for row in case_results if row.get("selector_action_id")]}))

    failures.extend(forbidden_import_failures())
    failures.extend(tracked_weight_failures())
    return write_status("validate_non_llm_action_selector_shadow_mode_001", failures, {"case_count": case_count})


if __name__ == "__main__":
    raise SystemExit(main())
