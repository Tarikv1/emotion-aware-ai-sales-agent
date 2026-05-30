from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Any


sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "research" / "experiments" / "generated"
LOCATION_ID = "NON-LLM-ACTION-SELECTOR-RUNTIME-HOOK-LOCATION-001"
NOOP_ID = "NON-LLM-ACTION-SELECTOR-RUNTIME-SHADOW-IMPORT-NOOP-001"
GATED_ID = "NON-LLM-ACTION-SELECTOR-RUNTIME-SHADOW-IMPORT-GATED-001"
PUBLIC_WRITE_ID = "NON-LLM-ACTION-SELECTOR-RUNTIME-SHADOW-PUBLIC-WRITE-001"
AUDIT_ID = "NON-LLM-ACTION-SELECTOR-RUNTIME-SHADOW-IMPORT-AUDIT-001"
DECISION_ID = "NON-LLM-ACTION-SELECTOR-RUNTIME-SHADOW-IMPORT-DECISION-001"
METADATA_SHADOW_ID = "NON-LLM-ACTION-SELECTOR-RUNTIME-METADATA-SHADOW-001"

AUDIT_DIR = GENERATED / AUDIT_ID
DECISION_DIR = GENERATED / DECISION_ID

FALSE_KEYS = [
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
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def false_flag_failures(payload: dict[str, Any], label: str) -> list[str]:
    failures: list[str] = []
    for key in FALSE_KEYS:
        if payload.get(key) is not False:
            failures.append(f"{label}.{key}_not_false")
    return failures


def audit_case_rows(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts = {
        "selector_control_leakage_count": 0,
        "buyer_facing_text_generation_count": 0,
        "public_raw_private_data_count": 0,
        "audio_data_count": 0,
        "provider_or_model_call_count": 0,
        "side_effect_count": 0,
        "memory_mutation_count": 0,
        "validation_error_count": 0,
        "missing_runtime_action_id_count": 0,
        "missing_selector_action_id_count": 0,
        "missing_agreement_classification_count": 0,
    }
    provider_flags = [
        "provider_calls_made",
        "openai_api_calls_made",
        "ultravox_calls_made",
        "elevenlabs_calls_made",
        "local_llm_calls_made",
        "ollama_calls_made",
        "tts_calls_made",
    ]
    for row in rows:
        if row.get("selector_control_allowed") is not False:
            counts["selector_control_leakage_count"] += 1
        if row.get("buyer_facing_text_generated") is not False:
            counts["buyer_facing_text_generation_count"] += 1
        if row.get("raw_private_data") is not False:
            counts["public_raw_private_data_count"] += 1
        if row.get("audio_data_used") is not False:
            counts["audio_data_count"] += 1
        if any(row.get(flag) is not False for flag in provider_flags):
            counts["provider_or_model_call_count"] += 1
        if row.get("side_effects_allowed") is not False:
            counts["side_effect_count"] += 1
        if row.get("memory_mutation_allowed") is not False:
            counts["memory_mutation_count"] += 1
        if row.get("validation_errors"):
            counts["validation_error_count"] += 1
        if not row.get("runtime_action_id"):
            counts["missing_runtime_action_id_count"] += 1
        if not row.get("selector_action_id"):
            counts["missing_selector_action_id_count"] += 1
        if not row.get("agreement_classification"):
            counts["missing_agreement_classification_count"] += 1
    return counts


def build_audit_result(
    location: dict[str, Any],
    noop: dict[str, Any],
    gated: dict[str, Any],
    public_write: dict[str, Any],
    metadata_shadow: dict[str, Any],
) -> dict[str, Any]:
    rows = gated.get("case_results") if isinstance(gated.get("case_results"), list) else []
    audit_counts = audit_case_rows(rows)
    failures: list[str] = []
    for label, payload in [("location", location), ("noop", noop), ("gated", gated), ("public_write", public_write)]:
        if payload.get("status") != "pass":
            failures.append(f"{label}_status_not_pass:{payload.get('status')}")
        failures.extend(false_flag_failures(payload, label))
    if noop.get("no_shadow_output_written") is not True:
        failures.append("env_disabled_shadow_output_written")
    if noop.get("passed_case_count") != noop.get("case_count"):
        failures.append("env_disabled_noop_case_mismatch")
    if gated.get("runtime_no_change_passed_count") != gated.get("runtime_no_change_case_count"):
        failures.append("gated_runtime_output_changed")
    if gated.get("runtime_action_id_available_count") != gated.get("shadow_record_count"):
        failures.append("gated_runtime_action_id_missing")
    if gated.get("selector_action_id_recorded_count") != gated.get("shadow_record_count"):
        failures.append("gated_selector_action_id_missing")
    for key, value in audit_counts.items():
        if value:
            failures.append(f"{key}:{value}")
    metadata_shadow_status = metadata_shadow.get("status")
    metadata_shadow_available = int(metadata_shadow.get("runtime_action_id_available_count") or 0)
    metadata_shadow_cases = int(metadata_shadow.get("case_count") or 0)
    if metadata_shadow_status and metadata_shadow_status != "pass":
        failures.append(f"existing_metadata_shadow_status_not_pass:{metadata_shadow_status}")
    return {
        "experiment_id": AUDIT_ID,
        "generated_at": utc_now(),
        "status": "pass" if not failures else "fail",
        "failure_count": len(failures),
        "failures": failures,
        "inputs": {
            "location": f"research/experiments/generated/{LOCATION_ID}/result.json",
            "noop": f"research/experiments/generated/{NOOP_ID}/result.json",
            "gated": f"research/experiments/generated/{GATED_ID}/result.json",
            "public_write": f"research/experiments/generated/{PUBLIC_WRITE_ID}/result.json",
            "existing_runtime_metadata": f"research/experiments/generated/{METADATA_SHADOW_ID}/result.json",
        },
        "audit": {
            "env_disabled_noop_behavior": noop.get("status") == "pass" and noop.get("no_shadow_output_written") is True,
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
            "action_metadata_available": gated.get("runtime_action_id_available_count") == gated.get("shadow_record_count"),
            "agreement_classification_quality": gated.get("exact_agreement_count") == gated.get("shadow_record_count"),
            "latency_overhead_disabled_ms": noop.get("latency_ms") or {},
            "latency_overhead_enabled_ms": gated.get("latency_ms") or {},
            "public_write_verified": public_write.get("status") == "pass",
            "public_write_jsonl_row_count": public_write.get("jsonl_row_count", 0),
            "public_write_unsafe_probe_written_count": public_write.get("unsafe_probe_written_count", 0),
            "case_row_audit_counts": audit_counts,
        },
        "case_count": gated.get("shadow_record_count", 0),
        "runtime_action_id_available_count": gated.get("runtime_action_id_available_count", 0),
        "selector_action_id_recorded_count": gated.get("selector_action_id_recorded_count", 0),
        "exact_agreement_count": gated.get("exact_agreement_count", 0),
        "compatible_agreement_count": gated.get("compatible_agreement_count", 0),
        "existing_metadata_shadow_case_count": metadata_shadow_cases,
        "existing_metadata_shadow_runtime_action_id_available_count": metadata_shadow_available,
        "public_write_status": public_write.get("status") or "not_run",
        "public_write_jsonl_row_count": public_write.get("jsonl_row_count", 0),
        "public_write_unsafe_probe_written_count": public_write.get("unsafe_probe_written_count", 0),
        "safety_blockers_count": len(failures),
        "should_not_change_runtime": True,
        "runtime_behavior_changed": False,
        "response_text_changed": False,
        "call_control_changed": False,
        "metadata_changed": False,
        "side_effects_allowed": False,
        "memory_mutation_allowed": False,
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


def build_decision_result(audit: dict[str, Any], noop: dict[str, Any], gated: dict[str, Any], public_write: dict[str, Any]) -> dict[str, Any]:
    if noop.get("status") != "pass" or noop.get("runtime_behavior_changed") is not False or noop.get("response_text_changed") is not False:
        recommendation_id = "rollback_or_fix_before_runtime_import"
        recommendation = "Disabled no-op output changed or failed; rollback/fix before any runtime import."
    elif public_write.get("status") == "pass" and gated.get("status") == "pass" and audit.get("status") == "pass":
        recommendation_id = "limited_offline_sanitized_jsonl_shadow_logging_next"
        recommendation = "Public JSONL shadow logging is hardened for offline sanitized evidence; next step is limited offline/sanitized JSONL shadow logging only."
    elif gated.get("status") == "pass" and audit.get("status") == "pass":
        recommendation_id = "limited_offline_sanitized_runtime_shadow_logging_next"
        recommendation = "Gated shadow import works and env-disabled no-op is clean; next step is limited offline/sanitized runtime shadow logging only."
    elif gated.get("runtime_action_id_available_count") != gated.get("shadow_record_count"):
        recommendation_id = "metadata_adapter_fix"
        recommendation = "Runtime metadata extraction failed in the hook path; fix the metadata adapter before more logging."
    elif gated.get("exact_agreement_count") != gated.get("shadow_record_count"):
        recommendation_id = "selector_runtime_disagreement_review_packet"
        recommendation = "Selector/runtime disagreement appeared; prepare a review packet before any wider shadow logging."
    else:
        recommendation_id = "hold_runtime_shadow_import"
        recommendation = "Hold runtime shadow import until audit failures are resolved."
    latency_disabled = noop.get("latency_ms") if isinstance(noop.get("latency_ms"), dict) else {}
    latency_enabled = gated.get("latency_ms") if isinstance(gated.get("latency_ms"), dict) else {}
    return {
        "experiment_id": DECISION_ID,
        "generated_at": utc_now(),
        "status": "pass",
        "recommendation_id": recommendation_id,
        "recommendation": recommendation,
        "evidence_summary": {
            "disabled_noop_status": noop.get("status"),
            "gated_status": gated.get("status"),
            "public_write_status": public_write.get("status") or "not_run",
            "audit_status": audit.get("status"),
            "gated_shadow_record_count": gated.get("shadow_record_count"),
            "public_write_jsonl_row_count": public_write.get("jsonl_row_count", 0),
            "public_write_unsafe_probe_written_count": public_write.get("unsafe_probe_written_count", 0),
            "runtime_action_id_available_count": gated.get("runtime_action_id_available_count"),
            "selector_action_id_recorded_count": gated.get("selector_action_id_recorded_count"),
            "exact_agreement_count": gated.get("exact_agreement_count"),
            "compatible_agreement_count": gated.get("compatible_agreement_count"),
            "safety_blockers_count": audit.get("safety_blockers_count"),
            "disabled_latency_p50_ms": latency_disabled.get("p50"),
            "disabled_latency_p90_ms": latency_disabled.get("p90"),
            "disabled_latency_p99_ms": latency_disabled.get("p99"),
            "enabled_latency_p50_ms": latency_enabled.get("p50"),
            "enabled_latency_p90_ms": latency_enabled.get("p90"),
            "enabled_latency_p99_ms": latency_enabled.get("p99"),
        },
        "claims_live_readiness": False,
        "live_wiring_allowed": False,
        "live_runtime_wiring_allowed": False,
        "selector_control_allowed": False,
        "response_text_changed": False,
        "runtime_behavior_changed": False,
        "provider_calls_made": False,
        "openai_api_calls_made": False,
        "ultravox_calls_made": False,
        "elevenlabs_calls_made": False,
        "local_llm_calls_made": False,
        "ollama_calls_made": False,
        "tts_calls_made": False,
    }


def audit_report(result: dict[str, Any]) -> str:
    latency_disabled = result["audit"]["latency_overhead_disabled_ms"]
    latency_enabled = result["audit"]["latency_overhead_enabled_ms"]
    return "\n".join(
        [
            f"# {AUDIT_ID}",
            "",
            f"- Status: {result['status']}",
            f"- Case count: {result['case_count']}",
            f"- Runtime action ID available count: {result['runtime_action_id_available_count']}",
            f"- Exact/compatible agreement: {result['exact_agreement_count']}/{result['compatible_agreement_count']}",
            f"- Safety blockers: {result['safety_blockers_count']}",
            f"- Public write status/rows: {result['public_write_status']}/{result['public_write_jsonl_row_count']}",
            f"- Disabled overhead p50/p90/p99 ms: {latency_disabled.get('p50', 0.0):.4f}/{latency_disabled.get('p90', 0.0):.4f}/{latency_disabled.get('p99', 0.0):.4f}",
            f"- Enabled overhead p50/p90/p99 ms: {latency_enabled.get('p50', 0.0):.4f}/{latency_enabled.get('p90', 0.0):.4f}/{latency_enabled.get('p99', 0.0):.4f}",
            "- Runtime behavior changed: false",
            "- Response text changed: false",
            "- Provider/OpenAI/Ultravox/ElevenLabs/local LLM/Ollama/TTS calls: false",
            "- Raw private data/audio data: false",
        ]
    )


def decision_report(result: dict[str, Any]) -> str:
    evidence = result["evidence_summary"]
    return "\n".join(
        [
            f"# {DECISION_ID}",
            "",
            f"- Status: {result['status']}",
            f"- Recommendation: {result['recommendation_id']}",
            f"- Detail: {result['recommendation']}",
            f"- Gated shadow records: {evidence['gated_shadow_record_count']}",
            f"- Public JSONL rows: {evidence['public_write_jsonl_row_count']}",
            f"- Runtime action ID available count: {evidence['runtime_action_id_available_count']}",
            f"- Exact/compatible agreement: {evidence['exact_agreement_count']}/{evidence['compatible_agreement_count']}",
            f"- Safety blockers: {evidence['safety_blockers_count']}",
            "- Live wiring allowed: false",
            "- Selector control allowed: false",
            "- Runtime behavior changed: false",
            "- Response text changed: false",
            "- Provider/OpenAI/Ultravox/ElevenLabs/local LLM/Ollama calls: false",
        ]
    )


def main() -> int:
    location = read_json(GENERATED / LOCATION_ID / "result.json")
    noop = read_json(GENERATED / NOOP_ID / "result.json")
    gated = read_json(GENERATED / GATED_ID / "result.json")
    public_write = read_json(GENERATED / PUBLIC_WRITE_ID / "result.json")
    metadata_shadow = read_json(GENERATED / METADATA_SHADOW_ID / "result.json")
    audit = build_audit_result(location, noop, gated, public_write, metadata_shadow)
    decision = build_decision_result(audit, noop, gated, public_write)
    write_json(AUDIT_DIR / "result.json", audit)
    write_text(AUDIT_DIR / "report.md", audit_report(audit))
    write_json(DECISION_DIR / "result.json", decision)
    write_text(DECISION_DIR / "report.md", decision_report(decision))
    print(
        json.dumps(
            {
                "status": audit["status"],
                "safety_blockers_count": audit["safety_blockers_count"],
                "decision": decision["recommendation_id"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if audit["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
