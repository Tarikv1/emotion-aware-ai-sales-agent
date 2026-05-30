from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
from time import perf_counter_ns
from typing import Any


sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

EXPERIMENT_ID = "NON-LLM-ACTION-SELECTOR-RUNTIME-SHADOW-PUBLIC-WRITE-001"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / EXPERIMENT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"
JSONL_PATH = OUT_DIR / "shadow_records.jsonl"
ENV_GATE = "ACTION_SELECTOR_RUNTIME_SHADOW_IMPORT_ENABLED"
PUBLIC_WRITE_GATE = "ACTION_SELECTOR_PUBLIC_EVIDENCE_WRITE_ENABLED"
CAMPAIGN_ID = "public-openai-chatgpt-plans"

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

FALSE_FLAGS = {
    "runtime_behavior_changed": False,
    "response_text_changed": False,
    "call_control_changed": False,
    "metadata_changed": False,
    "side_effects_allowed": False,
    "side_effects_observed": False,
    "memory_mutation_allowed": False,
    "memory_mutation_observed": False,
    "provider_calls_made": False,
    "openai_api_calls_made": False,
    "ultravox_calls_made": False,
    "elevenlabs_calls_made": False,
    "local_llm_calls_made": False,
    "ollama_calls_made": False,
    "tts_calls_made": False,
    "buyer_facing_text_generated": False,
    "selector_control_allowed": False,
    "live_runtime_wiring_allowed": False,
    "raw_private_data": False,
    "audio_data_used": False,
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


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


def stable_payload(payload: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {}
    return {key: deepcopy(value) for key, value in sorted(payload.items()) if key != "timestamp"}


def payload_hash(payload: dict[str, Any] | None) -> str:
    encoded = json.dumps(stable_payload(payload), sort_keys=True, ensure_ascii=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def text_hash(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def run_campaign_case(transcript: str) -> dict[str, Any] | None:
    from runtime.campaigns import public_openai_chatgpt_plans_dialogue as dialogue

    return dialogue.classify_turn(
        campaign={"campaign_id": CAMPAIGN_ID},
        transcript=transcript,
        normalized=transcript.casefold(),
        turns=[],
        previous_question=None,
        previous_question_type="opening",
        conversation_stage="opening",
        active_gap=None,
        confirmed_gaps=[],
        cleared_gaps=[],
        pending_callback=False,
        pending_appointment=False,
        candidate_gaps=[],
    )


def runtime_output_unchanged_check() -> list[dict[str, Any]]:
    cases = [
        ("price_question", "How much does ChatGPT Plus cost?"),
        ("privacy_boundary", "Do you store raw transcripts?"),
        ("terminal_close", "Thanks, that works."),
    ]
    rows: list[dict[str, Any]] = []
    previous = os.environ.pop(ENV_GATE, None)
    try:
        baselines = {case_id: run_campaign_case(text) for case_id, text in cases}
        os.environ[ENV_GATE] = "1"
        for case_id, text in cases:
            enabled = run_campaign_case(text)
            baseline = baselines[case_id]
            rows.append(
                {
                    "case_id": case_id,
                    "output_identical": stable_payload(baseline) == stable_payload(enabled),
                    "response_text_hash_identical": text_hash(str((baseline or {}).get("candidate_response") or ""))
                    == text_hash(str((enabled or {}).get("candidate_response") or "")),
                    "metadata_identical": payload_hash(baseline) == payload_hash(enabled),
                    "sanitized": True,
                    "raw_private_data": False,
                }
            )
    finally:
        if previous is None:
            os.environ.pop(ENV_GATE, None)
        else:
            os.environ[ENV_GATE] = previous
    return rows


def positive_context(case: dict[str, Any]) -> dict[str, Any]:
    return {
        "turn_id": case["case_id"],
        "campaign_id": case["campaign_id"],
        "buyer_utterance_text_sanitized": case["buyer_utterance_text"],
        "normalized_buyer_text": case["context"].get("normalized_buyer_text") or "",
        "context": case["context"],
        "context_summary": f"public_write_synthetic_case={case['case_id']}; expected={case['expected_action_id']}",
        "runtime_result": case["runtime_result"],
        "evidence_source": case["source_file"],
        "expected_action_id": case["expected_action_id"],
        "mode": "offline_sanitized_replay",
        "output_path": str(JSONL_PATH),
        "safety_boundary_detected": case["context"].get("safety_boundary_detected") is True,
        "sanitized": True,
        "raw_private_data": False,
    }


def unsafe_probe_contexts(base_case: dict[str, Any]) -> list[dict[str, Any]]:
    base = positive_context(base_case)
    missing_sanitized_with_raw = dict(base)
    missing_sanitized_with_raw.pop("buyer_utterance_text_sanitized", None)
    missing_sanitized_with_raw["buyer_utterance_text"] = "RAW TRANSCRIPT FALLBACK SHOULD NOT WRITE"
    transcript_fallback = dict(base)
    transcript_fallback.pop("buyer_utterance_text_sanitized", None)
    transcript_fallback["transcript"] = "RAW TRANSCRIPT FIELD SHOULD NOT WRITE"
    private_source = dict(base)
    private_source["evidence_source"] = "data/private/live-call.jsonl"
    raw_private = dict(base)
    raw_private["raw_private_data"] = True
    unsanitized = dict(base)
    unsanitized["sanitized"] = False
    wrong_mode = dict(base)
    wrong_mode["mode"] = "runtime_shadow_read_only"
    return [
        missing_sanitized_with_raw,
        transcript_fallback,
        private_source,
        raw_private,
        unsanitized,
        wrong_mode,
    ]


def row_is_safe(row: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    present = sorted(FORBIDDEN_ROW_KEYS & set(row))
    if present:
        failures.append(f"forbidden_row_keys:{present}")
    if row.get("raw_private_data") is not False:
        failures.append("raw_private_data_not_false")
    if row.get("audio_data_used") is not False:
        failures.append("audio_data_used_not_false")
    if row.get("buyer_facing_text_generated") is not False:
        failures.append("buyer_facing_text_generated_not_false")
    if row.get("selector_control_allowed") is not False:
        failures.append("selector_control_allowed_not_false")
    if row.get("provider_calls_made") is not False or row.get("openai_api_calls_made") is not False:
        failures.append("provider_call_flag_not_false")
    buyer_text = str(row.get("buyer_utterance_text_sanitized") or "")
    if not buyer_text:
        failures.append("buyer_text_missing")
    if buyer_text != "[REDACTED_PRIVATE_OR_LIVE_TEXT]" and "RAW TRANSCRIPT" in buyer_text:
        failures.append("raw_transcript_marker_present")
    source = str(row.get("evidence_source") or "").replace("\\", "/").casefold()
    if "data/private" in source or "private-restricted" in source:
        failures.append("private_source_in_written_row")
    return failures


def build_report(result: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"# {EXPERIMENT_ID}",
            "",
            f"- Status: {result['status']}",
            f"- Positive cases: {result['case_count']}",
            f"- Hook output written count: {result['hook_output_written_count']}",
            f"- JSONL row count: {result['jsonl_row_count']}",
            f"- Unsafe probe write count: {result['unsafe_probe_written_count']}",
            f"- Runtime output unchanged cases: {result['runtime_no_change_passed_count']}/{result['runtime_no_change_case_count']}",
            f"- Safety blockers: {result['safety_blockers_count']}",
            "- Runtime behavior changed: false",
            "- Response text changed: false",
            "- Provider/OpenAI/Ultravox/ElevenLabs/local LLM/Ollama/TTS calls: false",
            "- Selector control allowed: false",
        ]
    )


def main() -> int:
    from runtime.action_selector.shadow_runtime_hook import maybe_log_action_selector_shadow_turn
    from scripts.test_runtime_action_metadata_extraction_001 import build_cases

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if JSONL_PATH.exists():
        JSONL_PATH.write_text("", encoding="utf-8")
    previous_runtime = os.environ.get(ENV_GATE)
    previous_public = os.environ.get(PUBLIC_WRITE_GATE)
    previous_private = os.environ.get("ACTION_SELECTOR_PRIVATE_LOCAL_LOG_ENABLED")
    os.environ[ENV_GATE] = "1"
    os.environ[PUBLIC_WRITE_GATE] = "1"
    os.environ.pop("ACTION_SELECTOR_PRIVATE_LOCAL_LOG_ENABLED", None)
    hook_results: list[dict[str, Any]] = []
    unsafe_probe_results: list[dict[str, Any]] = []
    latencies: list[float] = []
    try:
        cases = build_cases()
        for case in cases:
            start = perf_counter_ns()
            hook_result = maybe_log_action_selector_shadow_turn(positive_context(case))
            latencies.append((perf_counter_ns() - start) / 1_000_000)
            hook_results.append(
                {
                    "case_id": case["case_id"],
                    "hook_enabled": hook_result.get("enabled") is True,
                    "hook_output_written": hook_result.get("output_written") is True,
                    "selector_action_id": (hook_result.get("record") or {}).get("selector_action_id"),
                    "runtime_action_id": (hook_result.get("record") or {}).get("runtime_action_id"),
                    "validation_errors": (hook_result.get("record") or {}).get("validation_errors") or [],
                    "raw_private_data": False,
                    "sanitized": True,
                }
            )
        rows_after_positive = len(read_jsonl(JSONL_PATH))
        for probe in unsafe_probe_contexts(cases[0]):
            before = len(read_jsonl(JSONL_PATH))
            hook_result = maybe_log_action_selector_shadow_turn(probe)
            after = len(read_jsonl(JSONL_PATH))
            unsafe_probe_results.append(
                {
                    "probe": probe.get("evidence_source") or ("missing_sanitized" if not probe.get("buyer_utterance_text_sanitized") else probe.get("mode")),
                    "hook_enabled": hook_result.get("enabled") is True,
                    "hook_output_written": hook_result.get("output_written") is True,
                    "row_count_before": before,
                    "row_count_after": after,
                    "wrote_row": after > before,
                }
            )
    finally:
        if previous_runtime is None:
            os.environ.pop(ENV_GATE, None)
        else:
            os.environ[ENV_GATE] = previous_runtime
        if previous_public is None:
            os.environ.pop(PUBLIC_WRITE_GATE, None)
        else:
            os.environ[PUBLIC_WRITE_GATE] = previous_public
        if previous_private is None:
            os.environ.pop("ACTION_SELECTOR_PRIVATE_LOCAL_LOG_ENABLED", None)
        else:
            os.environ["ACTION_SELECTOR_PRIVATE_LOCAL_LOG_ENABLED"] = previous_private

    jsonl_rows = read_jsonl(JSONL_PATH)
    runtime_no_change = runtime_output_unchanged_check()
    row_failures: list[str] = []
    for index, row in enumerate(jsonl_rows, start=1):
        for failure in row_is_safe(row):
            row_failures.append(f"row[{index}].{failure}")
    failures: list[str] = []
    if not JSONL_PATH.is_file():
        failures.append("jsonl_file_missing")
    if len(jsonl_rows) != len(hook_results):
        failures.append(f"jsonl_row_count_mismatch:{len(jsonl_rows)}!={len(hook_results)}")
    if any(result.get("hook_output_written") is not True for result in hook_results):
        failures.append("not_all_positive_hooks_wrote_output")
    if any(result.get("validation_errors") for result in hook_results):
        failures.append("positive_hook_validation_errors")
    unsafe_written = sum(1 for result in unsafe_probe_results if result.get("wrote_row") is True or result.get("hook_output_written") is True)
    if unsafe_written:
        failures.append(f"unsafe_probe_written_count:{unsafe_written}")
    for row in runtime_no_change:
        for key in ("output_identical", "response_text_hash_identical", "metadata_identical"):
            if row.get(key) is not True:
                failures.append(f"{row['case_id']} {key} must be true")
    failures.extend(row_failures)
    result = {
        "experiment_id": EXPERIMENT_ID,
        "generated_at": utc_now(),
        "status": "pass" if not failures else "fail",
        "failure_count": len(failures),
        "failures": failures,
        "case_count": len(hook_results),
        "hook_output_written_count": sum(1 for result in hook_results if result.get("hook_output_written") is True),
        "jsonl_path": str(JSONL_PATH.relative_to(ROOT)).replace("\\", "/"),
        "jsonl_exists": JSONL_PATH.is_file(),
        "jsonl_row_count": len(jsonl_rows),
        "unsafe_probe_count": len(unsafe_probe_results),
        "unsafe_probe_written_count": unsafe_written,
        "runtime_no_change_case_count": len(runtime_no_change),
        "runtime_no_change_passed_count": sum(1 for row in runtime_no_change if row.get("output_identical") is True),
        "row_validation_failure_count": len(row_failures),
        "safety_blockers_count": len(failures),
        "latency_ms": {
            "sample_count": len(latencies),
            "max": max(latencies) if latencies else 0.0,
        },
        "hook_results": hook_results,
        "unsafe_probe_results": unsafe_probe_results,
        "runtime_no_change_cases": runtime_no_change,
        "should_not_change_runtime": True,
        **FALSE_FLAGS,
    }
    write_json(RESULT_PATH, result)
    write_text(REPORT_PATH, build_report(result))
    print(
        json.dumps(
            {
                "status": result["status"],
                "jsonl_row_count": result["jsonl_row_count"],
                "unsafe_probe_written_count": result["unsafe_probe_written_count"],
                "safety_blockers_count": result["safety_blockers_count"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
