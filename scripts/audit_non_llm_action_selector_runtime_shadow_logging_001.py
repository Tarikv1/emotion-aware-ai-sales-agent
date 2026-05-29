from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
GENERATED_DIR = ROOT / "research" / "experiments" / "generated"
REPLAY_RESULT_PATH = GENERATED_DIR / "NON-LLM-ACTION-SELECTOR-RUNTIME-SHADOW-REPLAY-001" / "result.json"
CONFIG_PATH = ROOT / "runtime" / "action_selector" / "shadow_runtime_logging_config.json"
AUDIT_ID = "NON-LLM-ACTION-SELECTOR-RUNTIME-SHADOW-AUDIT-001"
DECISION_ID = "NON-LLM-ACTION-SELECTOR-RUNTIME-SHADOW-DECISION-001"
AUDIT_DIR = GENERATED_DIR / AUDIT_ID
DECISION_DIR = GENERATED_DIR / DECISION_ID

BOUNDARY_ACTIONS = {"respect_boundary", "answer_privacy_boundary"}
REPAIR_ACTIONS = {"repair_already_told_you", "repair_buyer_correction", "repair_asr_uncertainty", "avoid_repetition_rephrase"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def _text(row: dict[str, Any]) -> str:
    return str(row.get("buyer_utterance_text_sanitized") or "").casefold()


def audit_cases(case_results: list[dict[str, Any]], config: dict[str, Any]) -> dict[str, int]:
    audit = {
        "response_text_changed_true_count": 0,
        "runtime_behavior_changed_true_count": 0,
        "side_effects_allowed_true_count": 0,
        "buyer_facing_text_generated_true_count": 0,
        "live_runtime_wiring_allowed_true_count": 0,
        "memory_mutation_allowed_true_count": 0,
        "provider_or_model_call_flag_true_count": 0,
        "tts_call_flag_true_count": 0,
        "raw_private_data_in_evidence_count": 0,
        "unsafe_selector_outputs_count": 0,
        "boundary_mishandling_count": 0,
        "terminal_close_regression_count": 0,
        "already_told_you_regression_count": 0,
        "not_team_team_drift_count": 0,
        "voice_writing_drift_count": 0,
        "and_or_drift_count": 0,
        "fake_crm_email_calendar_implication_count": 0,
    }
    provider_flags = [
        "provider_calls_made",
        "openai_api_calls_made",
        "ultravox_calls_made",
        "elevenlabs_calls_made",
        "local_llm_calls_made",
        "ollama_calls_made",
    ]
    for row in case_results:
        text = _text(row)
        selector_action = str(row.get("selector_action_id") or "")
        expected_action = str(row.get("expected_action_id") or "")
        matched = " ".join(str(item) for item in row.get("selector_matched_features") or []).casefold()
        source = str(row.get("evidence_source") or "").replace("\\", "/").casefold()
        if row.get("response_text_changed") is not False:
            audit["response_text_changed_true_count"] += 1
        if row.get("runtime_behavior_changed") is not False:
            audit["runtime_behavior_changed_true_count"] += 1
        if row.get("side_effects_allowed") is not False:
            audit["side_effects_allowed_true_count"] += 1
        if row.get("buyer_facing_text_generated") is not False:
            audit["buyer_facing_text_generated_true_count"] += 1
        if row.get("live_runtime_wiring_allowed") is not False:
            audit["live_runtime_wiring_allowed_true_count"] += 1
        if row.get("memory_mutation_allowed") is not False:
            audit["memory_mutation_allowed_true_count"] += 1
        if any(row.get(flag) is not False for flag in provider_flags):
            audit["provider_or_model_call_flag_true_count"] += 1
        if row.get("tts_calls_made") is not False:
            audit["tts_call_flag_true_count"] += 1
        if row.get("raw_private_data") is not False or "data/private" in source or "private-restricted" in source:
            audit["raw_private_data_in_evidence_count"] += 1
        if str(row.get("safety_status") or "").startswith("unsafe") or row.get("validation_errors"):
            audit["unsafe_selector_outputs_count"] += 1
        if expected_action in BOUNDARY_ACTIONS and selector_action not in BOUNDARY_ACTIONS:
            audit["boundary_mishandling_count"] += 1
        if expected_action == "terminal_close" and selector_action != "terminal_close":
            audit["terminal_close_regression_count"] += 1
        if ("already told you" in text or expected_action in REPAIR_ACTIONS) and selector_action not in REPAIR_ACTIONS:
            audit["already_told_you_regression_count"] += 1
        if any(marker in text for marker in ("not a team", "not team", "by myself", "just me", "personal use only")) and selector_action == "recommend_business_or_enterprise":
            audit["not_team_team_drift_count"] += 1
        if "voice" in text and "mode:writing" in matched and "mode:voice" not in matched:
            audit["voice_writing_drift_count"] += 1
        if " and " in f" {text} " and "relation:or" in matched and "relation:and" not in matched:
            audit["and_or_drift_count"] += 1
        if " or " in f" {text} " and "relation:and" in matched and "relation:or" not in matched:
            audit["and_or_drift_count"] += 1
        if any(marker in text for marker in ("email", "calendar", "crm", "hubspot", "salesforce")) and row.get("side_effects_allowed") is not False:
            audit["fake_crm_email_calendar_implication_count"] += 1
    if config.get("memory_mutation_allowed") is not False:
        audit["memory_mutation_allowed_true_count"] += 1
    if config.get("provider_calls_allowed") is not False:
        audit["provider_or_model_call_flag_true_count"] += 1
    if config.get("side_effects_allowed") is not False:
        audit["side_effects_allowed_true_count"] += 1
    if config.get("buyer_facing_text_generation_allowed") is not False:
        audit["buyer_facing_text_generated_true_count"] += 1
    if config.get("live_runtime_wiring_allowed") is not False:
        audit["live_runtime_wiring_allowed_true_count"] += 1
    return audit


def build_audit_result(replay: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    case_results = replay.get("case_results") if isinstance(replay.get("case_results"), list) else []
    audit = audit_cases(case_results, config)
    blockers = sum(audit.values())
    return {
        "experiment_id": AUDIT_ID,
        "generated_at": utc_now(),
        "status": "pass" if blockers == 0 else "fail",
        "input": "research/experiments/generated/NON-LLM-ACTION-SELECTOR-RUNTIME-SHADOW-REPLAY-001/result.json",
        "case_count": len(case_results),
        "safety_blockers_count": blockers,
        "audit": audit,
        "side_effects_allowed": False,
        "buyer_facing_text_generated": False,
        "live_runtime_wiring_allowed": False,
        "should_not_change_runtime": True,
        "response_text_changed": False,
        "runtime_behavior_changed": False,
        "memory_mutation_allowed": False,
        "provider_calls_made": False,
        "openai_api_calls_made": False,
        "ultravox_calls_made": False,
        "elevenlabs_calls_made": False,
        "local_llm_calls_made": False,
        "ollama_calls_made": False,
        "tts_calls_made": False,
        "raw_private_data": False,
    }


def build_decision_result(audit: dict[str, Any], replay: dict[str, Any]) -> dict[str, Any]:
    replay_count = int(replay.get("replay_case_count") or 0)
    agreement = int(replay.get("agreement_with_expected_count") or 0)
    compatible = int(replay.get("compatible_with_expected_count") or 0)
    blockers = int(audit.get("safety_blockers_count") or 0)
    runtime_action_count = int(replay.get("runtime_action_id_available_count") or 0)
    exact_rate = agreement / replay_count if replay_count else 0.0
    compatible_rate = compatible / replay_count if replay_count else 0.0
    latency = replay.get("latency_ms") if isinstance(replay.get("latency_ms"), dict) else {}
    if blockers:
        recommendation_id = "cleanup_before_any_runtime_import"
        recommendation = "Shadow logging design has safety blockers; clean those before any runtime import."
    elif runtime_action_count == 0:
        recommendation_id = "add_runtime_action_metadata_extraction_before_real_runtime_comparison"
        recommendation = (
            "Offline replay is safety-clean, but runtime action IDs are still unavailable; add runtime action metadata "
            "extraction before claiming real runtime agreement."
        )
    elif replay_count >= 100 and exact_rate >= 0.90 and compatible_rate >= 0.90:
        recommendation_id = "disabled_by_default_runtime_import_design_next"
        recommendation = "Offline replay is strong and safety-clean; design a disabled-by-default runtime import next."
    elif replay.get("possible_regression_count", 0) > 0:
        recommendation_id = "targeted_rule_data_augmentation"
        recommendation = "Selector has possible regressions; add targeted rule/data augmentation before runtime import."
    else:
        recommendation_id = "offline_read_only_shadow_only"
        recommendation = "Keep the selector as offline/read-only shadow evidence until agreement improves."
    return {
        "experiment_id": DECISION_ID,
        "generated_at": utc_now(),
        "status": "pass",
        "recommendation_id": recommendation_id,
        "recommendation": recommendation,
        "evidence_summary": {
            "replay_case_count": replay_count,
            "selector_valid_action_count": replay.get("selector_valid_action_count"),
            "runtime_action_id_available_count": runtime_action_count,
            "runtime_response_text_available_count": replay.get("runtime_response_text_available_count"),
            "agreement_with_expected_count": agreement,
            "compatible_with_expected_count": compatible,
            "exact_rate": exact_rate,
            "compatible_rate": compatible_rate,
            "possible_improvement_count": replay.get("possible_improvement_count"),
            "possible_regression_count": replay.get("possible_regression_count"),
            "safety_blockers_count": blockers,
            "latency_p50_ms": latency.get("p50"),
            "latency_p90_ms": latency.get("p90"),
            "latency_p99_ms": latency.get("p99"),
        },
        "claims_live_readiness": False,
        "live_wiring_allowed": False,
        "live_runtime_wiring_allowed": False,
        "response_text_changed": False,
        "runtime_behavior_changed": False,
        "provider_calls_made": False,
        "openai_api_calls_made": False,
        "ultravox_calls_made": False,
        "elevenlabs_calls_made": False,
        "local_llm_calls_made": False,
        "ollama_calls_made": False,
    }


def audit_report(result: dict[str, Any]) -> str:
    lines = [
        f"# {AUDIT_ID}",
        "",
        f"- Status: {result['status']}",
        f"- Case count: {result['case_count']}",
        f"- Safety blockers: {result['safety_blockers_count']}",
        "- Response/runtime behavior changed: false",
        "- Provider/OpenAI/Ultravox/ElevenLabs/local LLM/Ollama/TTS calls: false",
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
            f"- Replay cases: {evidence['replay_case_count']}",
            f"- Runtime action ID available count: {evidence['runtime_action_id_available_count']}",
            f"- Agreement/compatible with expected: {evidence['agreement_with_expected_count']}/{evidence['compatible_with_expected_count']}",
            f"- Possible improvement/regression: {evidence['possible_improvement_count']}/{evidence['possible_regression_count']}",
            f"- Safety blockers: {evidence['safety_blockers_count']}",
            f"- Latency p50/p90/p99 ms: {evidence['latency_p50_ms']:.4f}/{evidence['latency_p90_ms']:.4f}/{evidence['latency_p99_ms']:.4f}",
            "- Live wiring allowed: false",
            "- Response text changed: false",
            "- Runtime behavior changed: false",
            "- Provider/OpenAI/Ultravox/ElevenLabs/local LLM/Ollama calls: false",
        ]
    )


def main() -> int:
    replay = read_json(REPLAY_RESULT_PATH)
    config = read_json(CONFIG_PATH)
    audit = build_audit_result(replay, config)
    decision = build_decision_result(audit, replay)
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
