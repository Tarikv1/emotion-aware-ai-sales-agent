from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "NON-LLM-ACTION-SELECTOR-RUNTIME-SHADOW-IMPORT-DECISION-001" / "result.json"
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
            failures.append(f"decision status is not pass: {result.get('status')}")
        if result.get("claims_live_readiness") is not False:
            failures.append("decision must not claim live readiness")
        if result.get("live_wiring_allowed") is not False:
            failures.append("decision live_wiring_allowed must be false")
        if result.get("selector_control_allowed") is not False:
            failures.append("decision selector_control_allowed must be false")
        for key in [
            "response_text_changed",
            "runtime_behavior_changed",
            "provider_calls_made",
            "openai_api_calls_made",
            "ultravox_calls_made",
            "elevenlabs_calls_made",
            "local_llm_calls_made",
            "ollama_calls_made",
            "tts_calls_made",
        ]:
            if result.get(key) is not False:
                failures.append(f"decision {key} must be false")
        recommendation = " ".join([str(result.get("recommendation_id") or ""), str(result.get("recommendation") or "")]).casefold()
        if "live ready" in recommendation or "enable live" in recommendation or "selector control" in recommendation:
            failures.append("decision must not claim live readiness or selector control")
        if result.get("recommendation_id") not in {
            "rollback_or_fix_before_runtime_import",
            "limited_offline_sanitized_jsonl_shadow_logging_next",
            "limited_offline_sanitized_runtime_shadow_logging_next",
            "metadata_adapter_fix",
            "selector_runtime_disagreement_review_packet",
            "hold_runtime_shadow_import",
        }:
            failures.append(f"unexpected recommendation_id: {result.get('recommendation_id')}")
    print(json.dumps({"validator": "validate_non_llm_action_selector_runtime_shadow_import_decision_001", "status": "pass" if not failures else "fail", "failure_count": len(failures), "failures": failures}, indent=2, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
