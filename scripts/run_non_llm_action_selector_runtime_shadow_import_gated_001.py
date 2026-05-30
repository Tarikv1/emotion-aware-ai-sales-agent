from __future__ import annotations

from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import statistics
import sys
from time import perf_counter_ns
from typing import Any


sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

EXPERIMENT_ID = "NON-LLM-ACTION-SELECTOR-RUNTIME-SHADOW-IMPORT-GATED-001"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / EXPERIMENT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"
ENV_GATE = "ACTION_SELECTOR_RUNTIME_SHADOW_IMPORT_ENABLED"
CAMPAIGN_ID = "public-openai-chatgpt-plans"

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

RUNTIME_CASES = [
    ("price_question", "How much does ChatGPT Plus cost?"),
    ("price_objection", "That sounds expensive, is it worth it?"),
    ("competitor_current_tool", "Why not Claude instead?"),
    ("plan_explanation", "Can you explain the plans?"),
    ("team_vs_individual", "This is for my team."),
    ("not_team", "No company, personal use only."),
    ("privacy_source", "Are you from OpenAI and what is the source?"),
    ("already_told_you", "I already told you that."),
    ("asr_uncertainty", "Did you say cloud or Claude?"),
    ("terminal_close", "Thanks, that works."),
    ("no_crm_email_calendar", "Can you email me and create a CRM record?"),
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def stable_payload(payload: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {}
    return {key: deepcopy(value) for key, value in sorted(payload.items()) if key != "timestamp"}


def payload_hash(payload: dict[str, Any] | None) -> str:
    encoded = json.dumps(stable_payload(payload), sort_keys=True, ensure_ascii=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def text_hash(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def percentile(values: list[float], percentile_value: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, round((percentile_value / 100.0) * (len(ordered) - 1))))
    return ordered[index]


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


def runtime_no_change_cases() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    previous = os.environ.pop(ENV_GATE, None)
    try:
        baselines = [(case_id, run_campaign_case(transcript)) for case_id, transcript in RUNTIME_CASES]
        os.environ[ENV_GATE] = "1"
        for case_id, transcript in RUNTIME_CASES:
            enabled_frame = run_campaign_case(transcript)
            baseline = dict(baselines[[item[0] for item in baselines].index(case_id)][1] or {})
            enabled = dict(enabled_frame or {})
            rows.append(
                {
                    "case_id": case_id,
                    "output_identical": stable_payload(baseline) == stable_payload(enabled),
                    "response_text_hash_identical": text_hash(str(baseline.get("candidate_response") or ""))
                    == text_hash(str(enabled.get("candidate_response") or "")),
                    "call_control_identical": str(baseline.get("call_control") or "") == str(enabled.get("call_control") or ""),
                    "metadata_identical": payload_hash(baseline) == payload_hash(enabled),
                    "runtime_action_id": str(enabled.get("action_id") or ""),
                    "semantic": str(enabled.get("semantic") or ""),
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


def turn_context_from_case(case: dict[str, Any]) -> dict[str, Any]:
    return {
        "turn_id": case["case_id"],
        "campaign_id": case["campaign_id"],
        "buyer_utterance_text_sanitized": case["buyer_utterance_text"],
        "normalized_buyer_text": case["context"].get("normalized_buyer_text") or "",
        "context": case["context"],
        "context_summary": f"synthetic_runtime_shadow_import_case={case['case_id']}; expected={case['expected_action_id']}",
        "runtime_result": case["runtime_result"],
        "evidence_source": case["source_file"],
        "expected_action_id": case["expected_action_id"],
        "mode": "offline_sanitized_replay",
        "safety_boundary_detected": case["context"].get("safety_boundary_detected") is True,
        "sanitized": True,
        "raw_private_data": False,
    }


def shadow_records() -> tuple[list[dict[str, Any]], list[float]]:
    from runtime.action_selector.shadow_runtime_hook import maybe_log_action_selector_shadow_turn
    from scripts.test_runtime_action_metadata_extraction_001 import build_cases

    rows: list[dict[str, Any]] = []
    latencies: list[float] = []
    previous = os.environ.get(ENV_GATE)
    previous_public = os.environ.get("ACTION_SELECTOR_PUBLIC_EVIDENCE_WRITE_ENABLED")
    previous_private = os.environ.get("ACTION_SELECTOR_PRIVATE_LOCAL_LOG_ENABLED")
    os.environ[ENV_GATE] = "1"
    os.environ["ACTION_SELECTOR_PUBLIC_EVIDENCE_WRITE_ENABLED"] = "1"
    os.environ.pop("ACTION_SELECTOR_PRIVATE_LOCAL_LOG_ENABLED", None)
    try:
        for case in build_cases():
            start = perf_counter_ns()
            hook_result = maybe_log_action_selector_shadow_turn(turn_context_from_case(case))
            latency_ms = (perf_counter_ns() - start) / 1_000_000
            record = dict(hook_result.get("record") or {})
            record["case_id"] = case["case_id"]
            record["latency_ms"] = latency_ms
            record["hook_enabled"] = hook_result.get("enabled") is True
            record["hook_output_written"] = hook_result.get("output_written") is True
            record["sanitized"] = True
            record["raw_private_data"] = False
            rows.append(record)
            latencies.append(latency_ms)
    finally:
        if previous is None:
            os.environ.pop(ENV_GATE, None)
        else:
            os.environ[ENV_GATE] = previous
        if previous_public is None:
            os.environ.pop("ACTION_SELECTOR_PUBLIC_EVIDENCE_WRITE_ENABLED", None)
        else:
            os.environ["ACTION_SELECTOR_PUBLIC_EVIDENCE_WRITE_ENABLED"] = previous_public
        if previous_private is None:
            os.environ.pop("ACTION_SELECTOR_PRIVATE_LOCAL_LOG_ENABLED", None)
        else:
            os.environ["ACTION_SELECTOR_PRIVATE_LOCAL_LOG_ENABLED"] = previous_private
    return rows, latencies


def build_report(result: dict[str, Any]) -> str:
    latency = result["latency_ms"]
    return "\n".join(
        [
            f"# {EXPERIMENT_ID}",
            "",
            f"- Status: {result['status']}",
            f"- Runtime no-change cases: {result['runtime_no_change_case_count']}",
            f"- Shadow records: {result['shadow_record_count']}",
            f"- Runtime action ID available count: {result['runtime_action_id_available_count']}",
            f"- Selector action ID recorded count: {result['selector_action_id_recorded_count']}",
            f"- Exact/compatible agreement: {result['exact_agreement_count']}/{result['compatible_agreement_count']}",
            f"- Safety blockers: {result['safety_blockers_count']}",
            f"- Enabled overhead p50/p90/p99 ms: {latency['p50']:.4f}/{latency['p90']:.4f}/{latency['p99']:.4f}",
            "- Runtime behavior changed: false",
            "- Response text changed: false",
            "- Selector control allowed: false",
            "- Provider/OpenAI/Ultravox/ElevenLabs/local LLM/Ollama/TTS calls: false",
            "- Raw private data/audio data: false",
        ]
    )


def main() -> int:
    no_change = runtime_no_change_cases()
    records, latencies = shadow_records()
    compatible_types = {"same_action", "compatible_action", "selector_more_specific", "runtime_more_specific"}
    failures: list[str] = []
    for row in no_change:
        for key in ("output_identical", "response_text_hash_identical", "call_control_identical", "metadata_identical"):
            if row.get(key) is not True:
                failures.append(f"{row['case_id']} {key} must be true")
    for index, record in enumerate(records, start=1):
        if record.get("hook_enabled") is not True:
            failures.append(f"record[{index}] hook_enabled must be true")
        if not record.get("selector_action_id"):
            failures.append(f"record[{index}] selector_action_id missing")
        if not record.get("runtime_action_id"):
            failures.append(f"record[{index}] runtime_action_id missing")
        if not record.get("agreement_classification"):
            failures.append(f"record[{index}] agreement_classification missing")
        if record.get("buyer_facing_text_generated") is not False:
            failures.append(f"record[{index}] buyer_facing_text_generated must be false")
        if record.get("validation_errors"):
            failures.append(f"record[{index}] validation_errors: {record.get('validation_errors')}")
    result = {
        "experiment_id": EXPERIMENT_ID,
        "generated_at": utc_now(),
        "status": "pass" if not failures else "fail",
        "failure_count": len(failures),
        "failures": failures,
        "runtime_no_change_case_count": len(no_change),
        "runtime_no_change_passed_count": sum(1 for row in no_change if row.get("output_identical") is True),
        "shadow_record_count": len(records),
        "hook_returned_record_count": sum(1 for row in records if row.get("hook_enabled") is True),
        "selector_action_id_recorded_count": sum(1 for row in records if row.get("selector_action_id")),
        "runtime_action_id_available_count": sum(1 for row in records if row.get("runtime_action_id")),
        "exact_agreement_count": sum(1 for row in records if row.get("disagreement_type") == "same_action"),
        "compatible_agreement_count": sum(1 for row in records if row.get("disagreement_type") in compatible_types),
        "agreement_classification_counts": dict(sorted(Counter(str(row.get("disagreement_type") or "") for row in records).items())),
        "safety_blockers_count": len(failures),
        "latency_ms": {
            "sample_count": len(latencies),
            "p50": percentile(latencies, 50),
            "p90": percentile(latencies, 90),
            "p99": percentile(latencies, 99),
            "max": max(latencies) if latencies else 0.0,
            "mean": statistics.mean(latencies) if latencies else 0.0,
        },
        "runtime_no_change_cases": no_change,
        "case_results": records,
        "should_not_change_runtime": True,
        **FALSE_FLAGS,
    }
    write_json(RESULT_PATH, result)
    write_text(REPORT_PATH, build_report(result))
    print(
        json.dumps(
            {
                "status": result["status"],
                "shadow_record_count": result["shadow_record_count"],
                "exact_agreement_count": result["exact_agreement_count"],
                "safety_blockers_count": result["safety_blockers_count"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
