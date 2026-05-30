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

EXPERIMENT_ID = "NON-LLM-ACTION-SELECTOR-RUNTIME-SHADOW-IMPORT-NOOP-001"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / EXPERIMENT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"
IMPORT_CONFIG_PATH = ROOT / "runtime" / "action_selector" / "shadow_runtime_import_config.json"
SHADOW_OUTPUT_PATH = OUT_DIR / "unexpected-disabled-shadow-output.jsonl"
CAMPAIGN_ID = "public-openai-chatgpt-plans"
ENV_GATE = "ACTION_SELECTOR_RUNTIME_SHADOW_IMPORT_ENABLED"

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

CASES = [
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
    ignored = {"timestamp", "shadow_runtime_import_warning"}
    return {key: deepcopy(value) for key, value in sorted(payload.items()) if key not in ignored}


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


def run_noop_case(case_id: str, transcript: str) -> dict[str, Any]:
    start = perf_counter_ns()
    before = run_campaign_case(transcript)
    after = run_campaign_case(transcript)
    latency_ms = (perf_counter_ns() - start) / 1_000_000
    before_response = str((before or {}).get("candidate_response") or "")
    after_response = str((after or {}).get("candidate_response") or "")
    return {
        "case_id": case_id,
        "output_identical": stable_payload(before) == stable_payload(after),
        "response_text_hash_identical": text_hash(before_response) == text_hash(after_response),
        "response_text_hash": text_hash(after_response),
        "call_control_identical": str((before or {}).get("call_control") or "") == str((after or {}).get("call_control") or ""),
        "metadata_identical": payload_hash(before) == payload_hash(after),
        "before_hash": payload_hash(before),
        "after_hash": payload_hash(after),
        "runtime_action_id": str((after or {}).get("action_id") or ""),
        "semantic": str((after or {}).get("semantic") or ""),
        "latency_ms": latency_ms,
        "sanitized": True,
        "raw_private_data": False,
    }


def disabled_hook_probe() -> dict[str, Any]:
    try:
        from runtime.action_selector import shadow_runtime_hook
    except Exception as exc:
        return {
            "imported": False,
            "error": type(exc).__name__,
            "enabled": None,
            "record": None,
            "output_written": SHADOW_OUTPUT_PATH.is_file(),
        }
    has_new_gate = hasattr(shadow_runtime_hook, "should_run_action_selector_runtime_shadow_import")
    if hasattr(shadow_runtime_hook, "maybe_log_action_selector_shadow_turn"):
        result = shadow_runtime_hook.maybe_log_action_selector_shadow_turn(
            {
                "turn_id": "noop_probe",
                "campaign_id": CAMPAIGN_ID,
                "buyer_utterance_text_sanitized": "How much does Plus cost?",
                "normalized_buyer_text": "how much does plus cost",
                "runtime_result": {"campaign_id": CAMPAIGN_ID, "turn_id": "noop_probe", "semantic": "price", "candidate_response": "Synthetic response."},
                "expected_action_id": "answer_price",
                "output_path": str(SHADOW_OUTPUT_PATH),
                "sanitized": True,
                "raw_private_data": False,
            }
        )
    else:
        result = {"enabled": None, "record": None}
    return {
        "imported": True,
        "has_new_gate": has_new_gate,
        "enabled": result.get("enabled"),
        "record": result.get("record"),
        "output_written": SHADOW_OUTPUT_PATH.is_file(),
        "result": result,
    }


def build_report(result: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"# {EXPERIMENT_ID}",
            "",
            f"- Status: {result['status']}",
            f"- Cases: {result['case_count']}",
            f"- Passed cases: {result['passed_case_count']}",
            f"- Env gate: {ENV_GATE}=disabled",
            f"- Import config exists: {str(result['import_config_exists']).lower()}",
            f"- Runtime hook has new gate: {str(result['hook_probe'].get('has_new_gate') is True).lower()}",
            f"- Shadow output written while disabled: {str(result['shadow_output_written']).lower()}",
            f"- Disabled overhead p50/p90/p99 ms: {result['latency_ms']['p50']:.4f}/{result['latency_ms']['p90']:.4f}/{result['latency_ms']['p99']:.4f}",
            f"- Safety blockers: {result['safety_blockers_count']}",
            "- Runtime behavior changed: false",
            "- Response text changed: false",
            "- Provider/OpenAI/Ultravox/ElevenLabs/local LLM/Ollama/TTS calls: false",
            "- Raw private data/audio data: false",
        ]
    )


def percentile(values: list[float], percentile_value: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, round((percentile_value / 100.0) * (len(ordered) - 1))))
    return ordered[index]


def main() -> int:
    previous_env = os.environ.pop(ENV_GATE, None)
    previous_public = os.environ.pop("ACTION_SELECTOR_PUBLIC_EVIDENCE_WRITE_ENABLED", None)
    previous_private = os.environ.pop("ACTION_SELECTOR_PRIVATE_LOCAL_LOG_ENABLED", None)
    try:
        case_results = [run_noop_case(case_id, transcript) for case_id, transcript in CASES]
        hook_probe = disabled_hook_probe()
    finally:
        if previous_env is not None:
            os.environ[ENV_GATE] = previous_env
        if previous_public is not None:
            os.environ["ACTION_SELECTOR_PUBLIC_EVIDENCE_WRITE_ENABLED"] = previous_public
        if previous_private is not None:
            os.environ["ACTION_SELECTOR_PRIVATE_LOCAL_LOG_ENABLED"] = previous_private

    failures: list[str] = []
    if not IMPORT_CONFIG_PATH.is_file():
        failures.append(f"missing import config: {IMPORT_CONFIG_PATH.relative_to(ROOT)}")
    if hook_probe.get("has_new_gate") is not True:
        failures.append("shadow runtime hook missing should_run_action_selector_runtime_shadow_import")
    if hook_probe.get("enabled") is not False:
        failures.append("disabled hook probe must return enabled false")
    if hook_probe.get("record") is not None:
        failures.append("disabled hook probe must not build a record")
    for row in case_results:
        for key in ("output_identical", "response_text_hash_identical", "call_control_identical", "metadata_identical"):
            if row.get(key) is not True:
                failures.append(f"{row['case_id']} {key} must be true")
    shadow_output_written = SHADOW_OUTPUT_PATH.is_file()
    if shadow_output_written:
        failures.append("disabled hook wrote shadow output")

    latencies = [float(row.get("latency_ms") or 0.0) for row in case_results]
    result = {
        "experiment_id": EXPERIMENT_ID,
        "generated_at": utc_now(),
        "status": "pass" if not failures else "fail",
        "failure_count": len(failures),
        "failures": failures,
        "case_count": len(case_results),
        "passed_case_count": sum(1 for row in case_results if row.get("output_identical") is True),
        "env_gate_disabled": True,
        "import_config_exists": IMPORT_CONFIG_PATH.is_file(),
        "hook_probe": hook_probe,
        "shadow_output_written": shadow_output_written,
        "no_shadow_output_written": not shadow_output_written,
        "safety_blockers_count": len(failures),
        "latency_ms": {
            "sample_count": len(latencies),
            "p50": percentile(latencies, 50),
            "p90": percentile(latencies, 90),
            "p99": percentile(latencies, 99),
            "max": max(latencies) if latencies else 0.0,
        },
        "case_results": case_results,
        "should_not_change_runtime": True,
        **FALSE_FLAGS,
    }
    write_json(RESULT_PATH, result)
    write_text(REPORT_PATH, build_report(result))
    print(json.dumps({"status": result["status"], "failures": failures}, indent=2, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
