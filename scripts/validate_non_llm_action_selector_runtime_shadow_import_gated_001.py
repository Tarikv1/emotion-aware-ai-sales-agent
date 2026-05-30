from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "NON-LLM-ACTION-SELECTOR-RUNTIME-SHADOW-IMPORT-GATED-001" / "result.json"
REPORT_PATH = RESULT_PATH.with_name("report.md")


def read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def main() -> int:
    failures: list[str] = []
    if not RESULT_PATH.is_file():
        failures.append(f"missing required artifact: {RESULT_PATH}")
    if not REPORT_PATH.is_file():
        failures.append(f"missing required artifact: {REPORT_PATH}")
    result = read_json(RESULT_PATH)
    if result:
        if result.get("status") != "pass":
            failures.append(f"gated import status is not pass: {result.get('status')}")
        if result.get("runtime_no_change_passed_count") != result.get("runtime_no_change_case_count"):
            failures.append("gated import runtime no-change cases did not all pass")
        if result.get("shadow_record_count", 0) < 60:
            failures.append("gated import shadow_record_count must be at least 60")
        if result.get("hook_returned_record_count") != result.get("shadow_record_count"):
            failures.append("hook_returned_record_count must equal shadow_record_count")
        if result.get("selector_action_id_recorded_count") != result.get("shadow_record_count"):
            failures.append("selector_action_id_recorded_count must equal shadow_record_count")
        if result.get("runtime_action_id_available_count") != result.get("shadow_record_count"):
            failures.append("runtime_action_id_available_count must equal shadow_record_count")
        if result.get("safety_blockers_count") != 0:
            failures.append(f"safety_blockers_count must be 0: {result.get('safety_blockers_count')}")
        for key in [
            "runtime_behavior_changed",
            "response_text_changed",
            "side_effects_allowed",
            "side_effects_observed",
            "memory_mutation_allowed",
            "memory_mutation_observed",
            "provider_calls_made",
            "openai_api_calls_made",
            "ultravox_calls_made",
            "elevenlabs_calls_made",
            "local_llm_calls_made",
            "ollama_calls_made",
            "tts_calls_made",
            "buyer_facing_text_generated",
            "selector_control_allowed",
            "live_runtime_wiring_allowed",
            "raw_private_data",
            "audio_data_used",
        ]:
            if result.get(key) is not False:
                failures.append(f"gated import {key} must be false")
        for index, row in enumerate(result.get("case_results") or [], start=1):
            if row.get("raw_private_data") is not False:
                failures.append(f"case_results[{index}].raw_private_data must be false")
            if row.get("audio_data_used") is not False:
                failures.append(f"case_results[{index}].audio_data_used must be false")
            if row.get("buyer_facing_text_generated") is not False:
                failures.append(f"case_results[{index}].buyer_facing_text_generated must be false")
            if row.get("selector_control_allowed") is not False:
                failures.append(f"case_results[{index}].selector_control_allowed must be false")
    print(json.dumps({"validator": "validate_non_llm_action_selector_runtime_shadow_import_gated_001", "status": "pass" if not failures else "fail", "failure_count": len(failures), "failures": failures}, indent=2, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
