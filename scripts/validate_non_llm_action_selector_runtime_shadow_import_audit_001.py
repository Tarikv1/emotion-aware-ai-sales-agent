from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "NON-LLM-ACTION-SELECTOR-RUNTIME-SHADOW-IMPORT-AUDIT-001" / "result.json"
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
            failures.append(f"audit status is not pass: {result.get('status')}")
        if result.get("safety_blockers_count") != 0:
            failures.append(f"safety_blockers_count must be 0: {result.get('safety_blockers_count')}")
        audit = result.get("audit") if isinstance(result.get("audit"), dict) else {}
        expected = {
            "env_disabled_noop_behavior": True,
            "runtime_behavior_changed": False,
            "response_text_changed": False,
            "call_control_changed": False,
            "memory_mutation": False,
            "side_effects": False,
            "provider_calls": False,
            "local_model_calls": False,
            "buyer_facing_text_generation": False,
            "public_raw_private_data": False,
            "selector_control_leakage": False,
            "exception_handling_safety": True,
            "action_metadata_available": True,
            "agreement_classification_quality": True,
        }
        for key, value in expected.items():
            if audit.get(key) is not value:
                failures.append(f"audit.{key} must be {value}")
        for key in [
            "runtime_behavior_changed",
            "response_text_changed",
            "side_effects_allowed",
            "memory_mutation_allowed",
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
                failures.append(f"audit {key} must be false")
    print(json.dumps({"validator": "validate_non_llm_action_selector_runtime_shadow_import_audit_001", "status": "pass" if not failures else "fail", "failure_count": len(failures), "failures": failures}, indent=2, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
