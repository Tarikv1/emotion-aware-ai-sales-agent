from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
GENERATED_DIR = ROOT / "research" / "experiments" / "generated"
SHADOW_RESULT_PATH = GENERATED_DIR / "NON-LLM-ACTION-SELECTOR-RUNTIME-METADATA-SHADOW-001" / "result.json"
AUDIT_ID = "RUNTIME-ACTION-METADATA-SHADOW-SAFETY-AUDIT-001"
DECISION_ID = "RUNTIME-ACTION-METADATA-SHADOW-DECISION-001"
AUDIT_DIR = GENERATED_DIR / AUDIT_ID
DECISION_DIR = GENERATED_DIR / DECISION_ID


FALSE_RESULT_FLAGS = {
    "runtime_behavior_changed": False,
    "response_text_changed": False,
    "memory_mutation_allowed": False,
    "provider_calls_made": False,
    "openai_api_calls_made": False,
    "ultravox_calls_made": False,
    "elevenlabs_calls_made": False,
    "local_llm_calls_made": False,
    "ollama_calls_made": False,
    "tts_calls_made": False,
    "buyer_facing_text_generated": False,
    "side_effects_allowed": False,
    "raw_private_data": False,
    "live_runtime_wiring_allowed": False,
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def empty_audit() -> dict[str, int]:
    return {
        "runtime_behavior_changed_true_count": 0,
        "response_text_changed_true_count": 0,
        "memory_mutation_allowed_true_count": 0,
        "provider_call_flag_true_count": 0,
        "local_llm_call_flag_true_count": 0,
        "tts_call_flag_true_count": 0,
        "buyer_facing_text_generated_true_count": 0,
        "side_effects_allowed_true_count": 0,
        "live_runtime_wiring_allowed_true_count": 0,
        "raw_private_data_count": 0,
        "unsafe_mapping_count": 0,
        "terminal_close_regression_count": 0,
        "boundary_regression_count": 0,
        "no_fit_regression_count": 0,
        "already_told_you_regression_count": 0,
        "not_team_team_drift_count": 0,
        "and_or_drift_count": 0,
        "voice_writing_drift_count": 0,
        "response_text_key_leak_count": 0,
    }


def _text(row: dict[str, Any]) -> str:
    return str(row.get("buyer_utterance_text_sanitized") or "").casefold()


def audit_shadow_result(shadow: dict[str, Any]) -> dict[str, int]:
    audit = empty_audit()
    provider_flags = [
        "provider_calls_made",
        "openai_api_calls_made",
        "ultravox_calls_made",
        "elevenlabs_calls_made",
        "local_llm_calls_made",
        "ollama_calls_made",
    ]
    boundary_actions = {"respect_boundary", "answer_privacy_boundary"}
    repair_actions = {
        "repair_already_told_you",
        "repair_buyer_correction",
        "repair_asr_uncertainty",
        "avoid_repetition_rephrase",
    }
    for row in shadow.get("case_results") if isinstance(shadow.get("case_results"), list) else []:
        expected = str(row.get("expected_action_id") or "")
        selector = str(row.get("selector_action_id") or "")
        runtime = str(row.get("runtime_action_id") or "")
        text = _text(row)
        matched = " ".join(str(item) for item in row.get("selector_matched_features") or []).casefold()
        if row.get("runtime_behavior_changed") is not False:
            audit["runtime_behavior_changed_true_count"] += 1
        if row.get("response_text_changed") is not False:
            audit["response_text_changed_true_count"] += 1
        if row.get("memory_mutation_allowed") is not False:
            audit["memory_mutation_allowed_true_count"] += 1
        if any(row.get(flag) is not False for flag in provider_flags):
            audit["provider_call_flag_true_count"] += 1
        if row.get("local_llm_calls_made") is not False or row.get("ollama_calls_made") is not False:
            audit["local_llm_call_flag_true_count"] += 1
        if row.get("tts_calls_made") is not False:
            audit["tts_call_flag_true_count"] += 1
        if row.get("buyer_facing_text_generated") is not False:
            audit["buyer_facing_text_generated_true_count"] += 1
        if row.get("side_effects_allowed") is not False:
            audit["side_effects_allowed_true_count"] += 1
        if row.get("live_runtime_wiring_allowed") is not False:
            audit["live_runtime_wiring_allowed_true_count"] += 1
        if row.get("raw_private_data") is not False:
            audit["raw_private_data_count"] += 1
        if selector != expected or runtime != expected:
            audit["unsafe_mapping_count"] += 1
        if expected == "terminal_close" and selector != "terminal_close":
            audit["terminal_close_regression_count"] += 1
        if expected in boundary_actions and selector not in boundary_actions:
            audit["boundary_regression_count"] += 1
        if expected == "disqualify_no_fit" and selector != "disqualify_no_fit":
            audit["no_fit_regression_count"] += 1
        if (expected == "repair_already_told_you" or "already told" in text) and selector not in repair_actions:
            audit["already_told_you_regression_count"] += 1
        if any(marker in text for marker in ("not a team", "not team", "just me", "personal use only")) and selector == "recommend_business_or_enterprise":
            audit["not_team_team_drift_count"] += 1
        if " and " in f" {text} " and "relation:or" in matched and "relation:and" not in matched:
            audit["and_or_drift_count"] += 1
        if " or " in f" {text} " and "relation:and" in matched and "relation:or" not in matched:
            audit["and_or_drift_count"] += 1
        if "voice" in text and "mode:writing" in matched and "mode:voice" not in matched:
            audit["voice_writing_drift_count"] += 1
        if sorted({"response_text", "buyer_facing_response", "draft_response", "say"} & set(row)):
            audit["response_text_key_leak_count"] += 1
    return audit


def build_audit_result(shadow: dict[str, Any]) -> dict[str, Any]:
    audit = audit_shadow_result(shadow)
    blockers = sum(audit.values()) + int(shadow.get("safety_blocker_count") or 0)
    return {
        "experiment_id": AUDIT_ID,
        "generated_at": utc_now(),
        "status": "pass" if blockers == 0 else "fail",
        "input": "research/experiments/generated/NON-LLM-ACTION-SELECTOR-RUNTIME-METADATA-SHADOW-001/result.json",
        "case_count": shadow.get("case_count", 0),
        "safety_blockers_count": blockers,
        "audit": audit,
        "should_not_change_runtime": True,
        **FALSE_RESULT_FLAGS,
    }


def build_decision_result(audit: dict[str, Any], shadow: dict[str, Any]) -> dict[str, Any]:
    case_count = int(shadow.get("case_count") or 0)
    exact = int(shadow.get("exact_agreement_count") or 0)
    compatible = int(shadow.get("compatible_agreement_count") or 0)
    runtime_available = int(shadow.get("runtime_action_id_available_count") or 0)
    blockers = int(audit.get("safety_blockers_count") or 0)
    exact_rate = exact / case_count if case_count else 0.0
    compatible_rate = compatible / case_count if case_count else 0.0
    latency = shadow.get("latency_ms") if isinstance(shadow.get("latency_ms"), dict) else {}
    if blockers:
        recommendation_id = "cleanup_before_any_runtime_shadow_import"
        recommendation = "Runtime metadata shadow comparison has safety blockers; clean those before any runtime import."
    elif runtime_available != case_count:
        recommendation_id = "expand_metadata_extraction_before_real_runtime_comparison"
        recommendation = "Metadata extraction did not produce a runtime action ID for every case; expand the contract or map before runtime import."
    elif exact_rate >= 0.9 and compatible_rate >= 0.95:
        recommendation_id = "disabled_by_default_runtime_shadow_import_next"
        recommendation = "Extraction is safety-clean and shadow agreement is strong; next step is a disabled-by-default runtime shadow import design, not live wiring."
    elif int(shadow.get("possible_regression_count") or 0) > 0:
        recommendation_id = "targeted_rule_cleanup_before_runtime_import"
        recommendation = "Possible regressions remain; review targeted selector and mapping cases before runtime import."
    else:
        recommendation_id = "keep_offline_metadata_shadow_only"
        recommendation = "Keep the work offline/read-only until agreement improves."
    return {
        "experiment_id": DECISION_ID,
        "generated_at": utc_now(),
        "status": "pass",
        "recommendation_id": recommendation_id,
        "recommendation": recommendation,
        "evidence_summary": {
            "case_count": case_count,
            "runtime_action_id_available_count": runtime_available,
            "selector_valid_action_count": shadow.get("selector_valid_action_count"),
            "exact_agreement_count": exact,
            "compatible_agreement_count": compatible,
            "exact_rate": exact_rate,
            "compatible_rate": compatible_rate,
            "possible_improvement_count": shadow.get("possible_improvement_count"),
            "possible_regression_count": shadow.get("possible_regression_count"),
            "safety_blockers_count": blockers,
            "latency_p50_ms": latency.get("p50"),
            "latency_p90_ms": latency.get("p90"),
            "latency_p99_ms": latency.get("p99"),
        },
        "claims_live_readiness": False,
        "live_wiring_allowed": False,
        **FALSE_RESULT_FLAGS,
    }


def audit_report(result: dict[str, Any]) -> str:
    lines = [
        f"# {AUDIT_ID}",
        "",
        f"- Status: {result['status']}",
        f"- Case count: {result['case_count']}",
        f"- Safety blockers: {result['safety_blockers_count']}",
        "- Runtime behavior changed: false",
        "- Response text changed: false",
        "- Provider/OpenAI/Ultravox/ElevenLabs/local LLM/Ollama/TTS calls: false",
        "- Buyer-facing text generated: false",
        "- Raw private data: false",
        "",
        "## Audit Counts",
        "",
    ]
    for key, value in result["audit"].items():
        lines.append(f"- {key}: {value}")
    return "\n".join(lines)


def decision_report(result: dict[str, Any]) -> str:
    evidence = result["evidence_summary"]
    return "\n".join(
        [
            f"# {DECISION_ID}",
            "",
            f"- Status: {result['status']}",
            f"- Recommendation: {result['recommendation_id']}",
            f"- Detail: {result['recommendation']}",
            f"- Cases: {evidence['case_count']}",
            f"- Runtime action ID available: {evidence['runtime_action_id_available_count']}",
            f"- Exact/compatible agreement: {evidence['exact_agreement_count']}/{evidence['compatible_agreement_count']}",
            f"- Possible improvement/regression: {evidence['possible_improvement_count']}/{evidence['possible_regression_count']}",
            f"- Safety blockers: {evidence['safety_blockers_count']}",
            f"- Latency p50/p90/p99 ms: {evidence['latency_p50_ms']:.4f}/{evidence['latency_p90_ms']:.4f}/{evidence['latency_p99_ms']:.4f}",
            "- Claims live readiness: false",
            "- Live wiring allowed: false",
            "- Runtime behavior changed: false",
            "- Response text changed: false",
            "- Provider/OpenAI/Ultravox/ElevenLabs/local LLM/Ollama calls: false",
        ]
    )


def main() -> int:
    shadow = read_json(SHADOW_RESULT_PATH)
    audit = build_audit_result(shadow)
    decision = build_decision_result(audit, shadow)
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
        )
    )
    return 0 if audit["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
