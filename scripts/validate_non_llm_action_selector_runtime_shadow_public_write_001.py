from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT_ID = "NON-LLM-ACTION-SELECTOR-RUNTIME-SHADOW-PUBLIC-WRITE-001"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / EXPERIMENT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"
JSONL_PATH = OUT_DIR / "shadow_records.jsonl"
FORBIDDEN_ROW_KEYS = {
    "candidate_response",
    "response_text",
    "agent_response",
    "final_response",
    "audio",
    "audio_path",
    "audio_file",
    "wav_path",
    "mp3_path",
    "raw_url",
}


def read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        payload = json.loads(line)
        if not isinstance(payload, dict):
            raise ValueError(f"{path}:{line_number} is not an object")
        rows.append(payload)
    return rows


def main() -> int:
    failures: list[str] = []
    if not RESULT_PATH.is_file():
        failures.append(f"missing required artifact: {RESULT_PATH}")
    if not REPORT_PATH.is_file():
        failures.append(f"missing required artifact: {REPORT_PATH}")
    if not JSONL_PATH.is_file():
        failures.append(f"missing required artifact: {JSONL_PATH}")
    result = read_json(RESULT_PATH)
    rows = read_jsonl(JSONL_PATH)
    if result:
        if result.get("status") != "pass":
            failures.append(f"public write status is not pass: {result.get('status')}")
        if result.get("jsonl_exists") is not True:
            failures.append("jsonl_exists must be true")
        if result.get("jsonl_row_count") != result.get("case_count"):
            failures.append("jsonl_row_count must equal case_count")
        if len(rows) != result.get("case_count"):
            failures.append("actual JSONL row count must equal case_count")
        if result.get("hook_output_written_count") != result.get("case_count"):
            failures.append("hook_output_written_count must equal case_count")
        if result.get("unsafe_probe_written_count") != 0:
            failures.append(f"unsafe_probe_written_count must be 0: {result.get('unsafe_probe_written_count')}")
        if result.get("runtime_no_change_passed_count") != result.get("runtime_no_change_case_count"):
            failures.append("runtime output changed in public write run")
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
                failures.append(f"public write {key} must be false")
    for index, row in enumerate(rows, start=1):
        present = sorted(FORBIDDEN_ROW_KEYS & set(row))
        if present:
            failures.append(f"row[{index}] contains forbidden key(s): {present}")
        for key in [
            "raw_private_data",
            "audio_data_used",
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
            "side_effects_allowed",
            "memory_mutation_allowed",
        ]:
            if row.get(key) is not False:
                failures.append(f"row[{index}].{key} must be false")
        if row.get("mode") != "offline_sanitized_replay":
            failures.append(f"row[{index}].mode must be offline_sanitized_replay")
        buyer_text = str(row.get("buyer_utterance_text_sanitized") or "")
        if not buyer_text:
            failures.append(f"row[{index}].buyer_utterance_text_sanitized missing")
        if buyer_text != "[REDACTED_PRIVATE_OR_LIVE_TEXT]" and "RAW TRANSCRIPT" in buyer_text:
            failures.append(f"row[{index}] contains raw transcript fallback marker")
        source = str(row.get("evidence_source") or "").replace("\\", "/").casefold()
        if "data/private" in source or "private-restricted" in source:
            failures.append(f"row[{index}] references private evidence source")
    print(json.dumps({"validator": "validate_non_llm_action_selector_runtime_shadow_public_write_001", "status": "pass" if not failures else "fail", "failure_count": len(failures), "failures": failures}, indent=2, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
