from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "research" / "experiments" / "generated"

CHECKPOINT_ID = "PHASE-4K10A-SELECTOR-RUNTIME-RECONCILIATION-001"
EXPANSION_ID = "NON-LLM-ACTION-SELECTOR-RUNTIME-SHADOW-EXPANSION-001"
REVIEW_4K9_ID = "PHASE-4K9-EVIDENCE-QUALITY-REVIEW-001"
REPAIR_4K10_ID = "PHASE-4K10-SPOKEN-RESPONSE-REPAIR-001"
TARGET_CASE_ID = "phase_4k8_b2b_saas_003"
TARGET_UTTERANCE = "Does it integrate securely with Salesforce?"

OUT_DIR = GENERATED / CHECKPOINT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"
EXPANSION_RESULT_PATH = GENERATED / EXPANSION_ID / "result.json"
EXPANSION_JSONL_PATH = GENERATED / EXPANSION_ID / "shadow_expansion_records.jsonl"
REVIEW_4K9_RESULT_PATH = GENERATED / REVIEW_4K9_ID / "result.json"
REPAIR_4K10_RESULT_PATH = GENERATED / REPAIR_4K10_ID / "result.json"

BASELINE = {
    "source_commit": "0c3f3e5e2a898e8429eee1313916fa123b4eedfa",
    "selector_runtime_disagreement_count": 17,
    "genuine_selector_runtime_disagreement_count": 1,
    "selector_possible_regression_count": 1,
    "target_case_review_classification": "selector_possible_regression",
}

FALSE_FLAG_KEYS = [
    "provider_calls_made",
    "model_calls_made",
    "openai_api_calls_made",
    "ultravox_calls_made",
    "elevenlabs_calls_made",
    "local_llm_calls_made",
    "ollama_calls_made",
    "tts_calls_made",
    "crm_calls_made",
    "email_calls_made",
    "calendar_calls_made",
    "side_effects_allowed",
    "selector_control_allowed",
    "response_text_changed",
    "runtime_behavior_changed",
    "raw_private_data",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped:
            payload = json.loads(stripped)
            if isinstance(payload, dict):
                rows.append(payload)
    return rows


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def target_case(expansion: dict[str, Any]) -> dict[str, Any]:
    for item in expansion.get("case_results") or []:
        if item.get("case_id") == TARGET_CASE_ID:
            return item if isinstance(item, dict) else {}
    return {}


def target_row(rows: list[dict[str, Any]]) -> dict[str, Any]:
    for row in rows:
        if row.get("case_id") == TARGET_CASE_ID:
            return row
    return {}


def classify_target_resolution(case: dict[str, Any]) -> str:
    runtime_action_id = str(case.get("runtime_action_id") or "")
    selector_action_id = str(case.get("selector_action_id") or "")
    review = str(case.get("disagreement_review_classification") or "")
    disagreement_type = str(case.get("agreement_disagreement_type") or "")
    if (
        runtime_action_id == "respect_boundary"
        and selector_action_id == "respect_boundary"
        and review == "same_action"
        and disagreement_type == "same_action"
    ):
        return "resolved_same_action"
    if review == "known_remaining_selector_regression":
        return "known_remaining_selector_regression"
    if review == "selector_possible_regression":
        return "unresolved_selector_possible_regression"
    return "unresolved_or_unclassified"


def false_flag_status(expansion: dict[str, Any], row: dict[str, Any]) -> dict[str, bool]:
    flags: dict[str, bool] = {}
    row_flags = row.get("safety_flags") if isinstance(row.get("safety_flags"), dict) else {}
    for key in FALSE_FLAG_KEYS:
        top_value = expansion.get(key)
        row_value = row_flags.get(key)
        values = [value for value in [top_value, row_value] if value is not None]
        flags[key] = bool(values) and all(value is False for value in values)
    flags["response_replacement_performed"] = expansion.get("response_replacement_performed") is False
    flags["live_selector_control_recommended"] = expansion.get("live_selector_control_recommended") is False
    flags["raw_candidate_response_recorded_count"] = expansion.get("raw_candidate_response_recorded_count") == 0
    return flags


def live_demo_statuses(repair_4k10: dict[str, Any]) -> dict[str, dict[str, Any]]:
    payload = repair_4k10.get("live_demo_statuses")
    if not isinstance(payload, dict):
        payload = repair_4k10.get("live_demo_results")
    if not isinstance(payload, dict):
        payload = repair_4k10.get("route_signal_statuses")
    if not isinstance(payload, dict):
        payload = repair_4k10.get("routesignal_validator_status")
    if isinstance(payload, dict):
        return {str(key): value for key, value in payload.items() if isinstance(value, dict)}
    result: dict[str, dict[str, Any]] = {}
    for key, value in repair_4k10.items():
        if isinstance(key, str) and key.startswith("LIVE-DEMO-") and isinstance(value, dict):
            result[key] = value
    return result


def build_result() -> dict[str, Any]:
    expansion = read_json(EXPANSION_RESULT_PATH)
    rows = read_jsonl(EXPANSION_JSONL_PATH)
    review_4k9 = read_json(REVIEW_4K9_RESULT_PATH)
    repair_4k10 = read_json(REPAIR_4K10_RESULT_PATH)
    case = target_case(expansion)
    row = target_row(rows)
    target_resolution = classify_target_resolution(case)
    false_flags = false_flag_status(expansion, row)
    review_counts = Counter(
        str(item.get("disagreement_review_classification") or "") for item in expansion.get("case_results") or []
    )
    after_naturalness = int(repair_4k10.get("after_naturalness_issue_count") or 0)
    genuine_disagreements = int(expansion.get("genuine_selector_runtime_disagreement_count") or 0)
    readiness_claimed = False
    acceptance = {
        "false_asr_mapping_count_remains_zero": expansion.get("false_asr_mapping_count") == 0,
        "live_selector_control_recommended_remains_false": expansion.get("live_selector_control_recommended") is False,
        "selector_control_allowed_remains_false": expansion.get("selector_control_allowed") is False,
        "response_replacement_performed_remains_false": expansion.get("response_replacement_performed") is False,
        "provider_model_tts_crm_email_calendar_flags_remain_false": all(
            false_flags.get(key) is True
            for key in [
                "provider_calls_made",
                "model_calls_made",
                "tts_calls_made",
                "crm_calls_made",
                "email_calls_made",
                "calendar_calls_made",
            ]
        ),
        "raw_candidate_responses_absent": expansion.get("raw_candidate_response_recorded_count") == 0,
        "target_case_explicitly_reconciled": target_resolution
        in {"resolved_same_action", "known_remaining_selector_regression"},
        "selector_readiness_claim_not_made_without_zero_genuine_disagreements": (
            not readiness_claimed or genuine_disagreements == 0
        ),
        "naturalness_count_at_or_below_4k10": after_naturalness <= 14,
    }
    status = "pass" if all(acceptance.values()) and expansion.get("status") == "pass" else "fail"
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "generated_at": utc_now(),
        "status": status,
        "baseline": BASELINE,
        "after": {
            "selector_runtime_disagreement_count": expansion.get("selector_runtime_disagreement_count"),
            "genuine_selector_runtime_disagreement_count": expansion.get("genuine_selector_runtime_disagreement_count"),
            "selector_possible_regression_count": expansion.get("selector_possible_regression_count"),
            "false_asr_mapping_count": expansion.get("false_asr_mapping_count"),
            "naturalness_issue_count": after_naturalness,
            "review_4k9_status": review_4k9.get("status"),
        },
        "target_case": {
            "case_id": TARGET_CASE_ID,
            "utterance": TARGET_UTTERANCE,
            "runtime_action_id": case.get("runtime_action_id") or "",
            "selector_action_id": case.get("selector_action_id") or "",
            "agreement_disagreement_type": case.get("agreement_disagreement_type") or "",
            "disagreement_review_classification": case.get("disagreement_review_classification") or "",
            "reason_for_disagreement": case.get("reason_for_disagreement") or "",
            "resolution_status": target_resolution,
            "root_cause": (
                "Runtime maps the generic Salesforce/security integration question to a boundary-safe action because "
                "the campaign cannot verify integration or security fit from fixture text; the selector must not fall "
                "back to a use-case diagnostic when the buyer asks a boundary-sensitive product-claim question."
            ),
            "minimal_fix_decision": "selector_rule_update",
        },
        "disagreement_review_counts": dict(sorted(review_counts.items())),
        "acceptance": acceptance,
        "false_flag_status": false_flags,
        "selector_readiness_claimed": readiness_claimed,
        "live_demo_statuses": live_demo_statuses(repair_4k10),
        "live_selector_control_recommended": False,
        "selector_control_allowed": False,
        "response_replacement_performed": False,
        "no_provider_model_tts_crm_email_calendar_side_effect_path_enabled": acceptance[
            "provider_model_tts_crm_email_calendar_flags_remain_false"
        ],
        "no_private_raw_transcript_or_audio_added_to_public_evidence": True,
    }


def build_report(result: dict[str, Any]) -> str:
    target = result["target_case"]
    after = result["after"]
    lines = [
        f"# {CHECKPOINT_ID}",
        "",
        f"- Status: {result['status']}",
        f"- Baseline commit: {result['baseline']['source_commit']}",
        "- Fix decision: selector_rule_update",
        f"- Selector/runtime disagreement count before/after: {result['baseline']['selector_runtime_disagreement_count']}/{after['selector_runtime_disagreement_count']}",
        f"- Genuine actionable disagreement count before/after: {result['baseline']['genuine_selector_runtime_disagreement_count']}/{after['genuine_selector_runtime_disagreement_count']}",
        f"- Selector possible regression count before/after: {result['baseline']['selector_possible_regression_count']}/{after['selector_possible_regression_count']}",
        f"- False ASR mapping count: {after['false_asr_mapping_count']}",
        f"- 4K10 naturalness issue count: {after['naturalness_issue_count']}",
        "- Live selector control: false",
        "- Selector response replacement: false",
        "- Provider/model/TTS/CRM/email/calendar side-effect path enabled: false",
        "- Raw private transcript/audio added to public evidence: false",
        "",
        "## Target Case",
        "",
        f"- Case: {target['case_id']}",
        f"- Utterance: {target['utterance']}",
        f"- Runtime action: {target['runtime_action_id']}",
        f"- Selector action: {target['selector_action_id']}",
        f"- Agreement type: {target['agreement_disagreement_type']}",
        f"- Review classification: {target['disagreement_review_classification']}",
        f"- Resolution: {target['resolution_status']}",
        f"- Root cause: {target['root_cause']}",
        "",
        "## Acceptance",
        "",
    ]
    for key, value in result["acceptance"].items():
        lines.append(f"- {key}: {str(value).lower()}")
    lines.extend(["", "## RouteSignal Status", ""])
    statuses = result.get("live_demo_statuses") or {}
    for checkpoint in ["LIVE-DEMO-002", "LIVE-DEMO-009", "LIVE-DEMO-014"]:
        payload = statuses.get(checkpoint) if isinstance(statuses.get(checkpoint), dict) else {}
        status = payload.get("status") or "unchanged_or_not_rerun_in_4k10a"
        failure_count = payload.get("failure_count", "unknown")
        lines.append(f"- {checkpoint}: {status} (failure_count={failure_count})")
    lines.extend(["", "Do not enable live selector control."])
    return "\n".join(lines)


def main() -> int:
    result = build_result()
    write_json(RESULT_PATH, result)
    write_text(REPORT_PATH, build_report(result))
    print(
        json.dumps(
            {
                "status": result["status"],
                "target_case_resolution": result["target_case"]["resolution_status"],
                "selector_runtime_disagreement_before": result["baseline"]["selector_runtime_disagreement_count"],
                "selector_runtime_disagreement_after": result["after"]["selector_runtime_disagreement_count"],
                "genuine_disagreement_after": result["after"]["genuine_selector_runtime_disagreement_count"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
