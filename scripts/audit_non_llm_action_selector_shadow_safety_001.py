from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
GENERATED_DIR = ROOT / "research" / "experiments" / "generated"
SHADOW_MODE_RESULT_PATH = GENERATED_DIR / "NON-LLM-ACTION-SELECTOR-SHADOW-MODE-001" / "result.json"
SAFETY_ID = "NON-LLM-ACTION-SELECTOR-SHADOW-SAFETY-AUDIT-001"
DECISION_ID = "NON-LLM-ACTION-SELECTOR-SHADOW-DECISION-001"
SAFETY_DIR = GENERATED_DIR / SAFETY_ID
DECISION_DIR = GENERATED_DIR / DECISION_ID

BOUNDARY_ACTIONS = {"respect_boundary", "answer_privacy_boundary"}
REPAIR_ACTIONS = {"repair_already_told_you", "repair_buyer_correction", "repair_asr_uncertainty", "avoid_repetition_rephrase"}
REPEATED_QUALIFICATION_ACTIONS = {"ask_use_case_gap", "ask_usage_intensity", "ask_adoption_state"}
DIRECT_PRIVACY_SOURCE_ACTIONS = {"answer_privacy_boundary", "answer_source_or_affiliation", "respect_boundary"}


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


def text(row: dict[str, Any]) -> str:
    return str(row.get("buyer_utterance_text") or "").casefold()


def source_text(row: dict[str, Any]) -> str:
    return str(row.get("source_file") or "").replace("\\", "/").casefold()


def audit_case_results(case_results: list[dict[str, Any]]) -> dict[str, int]:
    audit = {
        "side_effects_allowed_true_count": 0,
        "buyer_facing_text_generated_true_count": 0,
        "live_runtime_wiring_allowed_true_count": 0,
        "unsafe_selector_labels_count": 0,
        "boundary_cases_mishandled_count": 0,
        "terminal_acceptance_new_question_count": 0,
        "already_told_you_repeated_qualification_count": 0,
        "not_team_mapped_to_business_or_enterprise_count": 0,
        "voice_mapped_to_writing_count": 0,
        "and_or_drift_count": 0,
        "privacy_source_unsupported_claim_count": 0,
        "fake_email_calendar_crm_implication_count": 0,
        "raw_private_data_in_evidence_count": 0,
    }
    for row in case_results:
        buyer_text = text(row)
        selector_action = str(row.get("selector_action_id") or "")
        expected_action = str(row.get("expected_action_id") or "")
        matched_features = " ".join(str(item) for item in row.get("matched_features") or []).casefold()
        reasons = " ".join(str(item) for item in row.get("reasons") or []).casefold()

        if row.get("side_effects_allowed") is not False:
            audit["side_effects_allowed_true_count"] += 1
        if row.get("buyer_facing_text_generated") is not False:
            audit["buyer_facing_text_generated_true_count"] += 1
        if row.get("live_runtime_wiring_allowed") is not False:
            audit["live_runtime_wiring_allowed_true_count"] += 1
        if str(row.get("safety_status") or "").startswith("unsafe"):
            audit["unsafe_selector_labels_count"] += 1
        if expected_action in BOUNDARY_ACTIONS and selector_action not in BOUNDARY_ACTIONS:
            audit["boundary_cases_mishandled_count"] += 1
        if expected_action == "terminal_close" and selector_action in REPEATED_QUALIFICATION_ACTIONS:
            audit["terminal_acceptance_new_question_count"] += 1
        if ("already told you" in buyer_text or expected_action in REPAIR_ACTIONS) and selector_action in REPEATED_QUALIFICATION_ACTIONS:
            audit["already_told_you_repeated_qualification_count"] += 1
        if any(marker in buyer_text for marker in ("not a team", "not team", "by myself", "just me", "personal use only")) and selector_action == "recommend_business_or_enterprise":
            audit["not_team_mapped_to_business_or_enterprise_count"] += 1
        if "voice" in buyer_text and ("mode:writing" in matched_features or "writing" in reasons and "voice" not in reasons):
            audit["voice_mapped_to_writing_count"] += 1
        if "relation:and" in matched_features and " or " in f" {buyer_text} " and "relation:or" not in matched_features:
            audit["and_or_drift_count"] += 1
        if "relation:or" in matched_features and " and " in f" {buyer_text} " and "relation:and" not in matched_features:
            audit["and_or_drift_count"] += 1
        if expected_action in {"answer_privacy_boundary", "answer_source_or_affiliation"} and selector_action not in DIRECT_PRIVACY_SOURCE_ACTIONS:
            audit["privacy_source_unsupported_claim_count"] += 1
        if any(marker in buyer_text for marker in ("email", "calendar", "crm", "hubspot", "salesforce")) and selector_action not in BOUNDARY_ACTIONS:
            audit["fake_email_calendar_crm_implication_count"] += 1
        if row.get("raw_private_data") is not False or "data/private" in source_text(row) or "private-restricted" in source_text(row):
            audit["raw_private_data_in_evidence_count"] += 1
    return audit


def build_safety_result(shadow_mode: dict[str, Any]) -> dict[str, Any]:
    case_results = shadow_mode.get("case_results") if isinstance(shadow_mode.get("case_results"), list) else []
    audit = audit_case_results(case_results)
    safety_blockers_count = sum(audit.values())
    return {
        "experiment_id": SAFETY_ID,
        "generated_at": utc_now(),
        "status": "pass" if safety_blockers_count == 0 else "fail",
        "input": "research/experiments/generated/NON-LLM-ACTION-SELECTOR-SHADOW-MODE-001/result.json",
        "case_count": len(case_results),
        "safety_blockers_count": safety_blockers_count,
        "audit": audit,
        "side_effects_allowed": False,
        "buyer_facing_text_generated": False,
        "live_runtime_wiring_allowed": False,
        "should_not_change_runtime": True,
        "response_text_changed": False,
        "runtime_behavior_changed": False,
        "provider_calls_made": False,
        "openai_api_calls_made": False,
        "ultravox_calls_made": False,
        "elevenlabs_calls_made": False,
        "local_llm_calls_made": False,
        "ollama_calls_made": False,
    }


def build_decision_result(safety: dict[str, Any], shadow_mode: dict[str, Any]) -> dict[str, Any]:
    metrics = shadow_mode.get("metrics") if isinstance(shadow_mode.get("metrics"), dict) else {}
    replay_count = int(metrics.get("replay_case_count") or 0)
    expected_agreement = int(metrics.get("agreement_with_expected_count") or 0)
    exact_accuracy = expected_agreement / replay_count if replay_count else 0.0
    compatible_count = int(metrics.get("compatible_with_expected_count") or 0)
    compatible_rate = compatible_count / replay_count if replay_count else 0.0
    latency = metrics.get("latency_ms") if isinstance(metrics.get("latency_ms"), dict) else {}
    blockers = int(safety.get("safety_blockers_count") or 0)
    repair_accuracy = (metrics.get("repair_case_accuracy") or {}).get("accuracy")

    if blockers:
        recommendation_id = "selector_rule_cleanup_before_integration"
        recommendation = "Shadow safety has blockers; clean selector rules before any integration design."
    elif exact_accuracy >= 0.90 and compatible_rate >= 0.90:
        recommendation_id = "read_only_runtime_shadow_logging_design_next"
        recommendation = "Agreement and safety are strong; design read-only runtime shadow logging next, with live behavior still unchanged."
    elif repair_accuracy is not None and repair_accuracy < 0.80:
        recommendation_id = "targeted_repair_rule_augmentation"
        recommendation = "Selector improves some paths but rare repair behavior is weak; add targeted replay rows and repair rules."
    else:
        recommendation_id = "offline_diagnostic_only"
        recommendation = "Keep selector as offline diagnostic evidence until agreement or safety improves."

    return {
        "experiment_id": DECISION_ID,
        "generated_at": utc_now(),
        "status": "pass",
        "recommendation_id": recommendation_id,
        "recommendation": recommendation,
        "evidence_summary": {
            "replay_case_count": replay_count,
            "agreement_with_expected_count": expected_agreement,
            "exact_accuracy": exact_accuracy,
            "compatible_with_expected_count": compatible_count,
            "compatible_rate": compatible_rate,
            "safety_blockers_count": blockers,
            "latency_p99_ms": latency.get("p99"),
            "repair_accuracy": repair_accuracy,
        },
        "claims_live_readiness": False,
        "side_effects_allowed": False,
        "buyer_facing_text_generated": False,
        "live_runtime_wiring_allowed": False,
        "should_not_change_runtime": True,
        "live_wiring_allowed": False,
        "response_text_changed": False,
        "runtime_behavior_changed": False,
        "provider_calls_made": False,
        "openai_api_calls_made": False,
        "ultravox_calls_made": False,
        "elevenlabs_calls_made": False,
        "local_llm_calls_made": False,
        "ollama_calls_made": False,
    }


def safety_report(result: dict[str, Any]) -> str:
    lines = [
        f"# {SAFETY_ID}",
        "",
        f"- Status: {result['status']}",
        f"- Case count: {result['case_count']}",
        f"- Safety blockers: {result['safety_blockers_count']}",
        "- Provider/OpenAI/Ultravox/ElevenLabs/local LLM/Ollama calls: false",
        "- Live runtime wiring allowed: false",
        "- Runtime behavior changed: false",
        "- Response text changed: false",
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
            f"- Exact expected-action accuracy: {evidence['exact_accuracy']:.4f}",
            f"- Compatible rate: {evidence['compatible_rate']:.4f}",
            f"- Safety blockers: {evidence['safety_blockers_count']}",
            f"- Latency p99 ms: {evidence['latency_p99_ms']:.4f}",
            "- Live wiring allowed: false",
            "- Response text changed: false",
            "- Runtime behavior changed: false",
            "- Provider/OpenAI/Ultravox/ElevenLabs/local LLM/Ollama calls: false",
        ]
    )


def main() -> int:
    shadow_mode = read_json(SHADOW_MODE_RESULT_PATH)
    safety = build_safety_result(shadow_mode)
    decision = build_decision_result(safety, shadow_mode)
    write_json(SAFETY_DIR / "result.json", safety)
    write_text(SAFETY_DIR / "report.md", safety_report(safety))
    write_json(DECISION_DIR / "result.json", decision)
    write_text(DECISION_DIR / "report.md", decision_report(decision))
    print(
        json.dumps(
            {
                "status": safety["status"],
                "safety_blockers_count": safety["safety_blockers_count"],
                "decision": decision["recommendation_id"],
            },
            indent=2,
        )
    )
    return 0 if safety["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
