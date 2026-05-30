from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.action_selector.non_llm_action_selector import RuleBasedActionSelector


CHECKPOINT_ID = "PHASE-4K11-BOUNDARY-SENSITIVE-SELECTOR-GENERALIZATION-001"
GENERATED = ROOT / "research" / "experiments" / "generated"
OUT_DIR = GENERATED / CHECKPOINT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"

RECONCILIATION_4K10A_ID = "PHASE-4K10A-SELECTOR-RUNTIME-RECONCILIATION-001"
REPAIR_4K10_ID = "PHASE-4K10-SPOKEN-RESPONSE-REPAIR-001"
EXPANSION_ID = "NON-LLM-ACTION-SELECTOR-RUNTIME-SHADOW-EXPANSION-001"
RECONCILIATION_4K10A_RESULT = GENERATED / RECONCILIATION_4K10A_ID / "result.json"
REPAIR_4K10_RESULT = GENERATED / REPAIR_4K10_ID / "result.json"
EXPANSION_RESULT = GENERATED / EXPANSION_ID / "result.json"

POSITIVE_CASES = [
    "Does it integrate securely with Salesforce?",
    "Can you guarantee Salesforce integration works?",
    "Is it compliant with our security requirements?",
    "Can you prove HubSpot integration is secure?",
    "Can you guarantee the CRM setup?",
]

NEGATIVE_CASES = [
    "What CRM does this work with at a high level?",
    "How does the workflow routing work?",
    "What does the integration review check?",
    "Is this about CRM follow-up reminders?",
    "What kind of security details would a reviewer need?",
    "Can you explain the setup process at a high level?",
]

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
    "selector_control_allowed",
    "live_selector_control_recommended",
    "response_replacement_performed",
    "side_effects_allowed",
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


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def selector_matrix() -> list[dict[str, Any]]:
    selector = RuleBasedActionSelector()
    rows: list[dict[str, Any]] = []
    for expected_group, utterances in [("positive", POSITIVE_CASES), ("negative", NEGATIVE_CASES)]:
        for index, utterance in enumerate(utterances, start=1):
            output = selector.select({"buyer_utterance_text": utterance})
            expected_action_id = "respect_boundary" if expected_group == "positive" else "not_respect_boundary"
            passed = output.action_id == "respect_boundary" if expected_group == "positive" else output.action_id != "respect_boundary"
            rows.append(
                {
                    "case_id": f"4k11_{expected_group}_{index:03d}",
                    "utterance": utterance,
                    "expected_group": expected_group,
                    "expected_action_id": expected_action_id,
                    "selector_action_id": output.action_id,
                    "selector_confidence": output.confidence,
                    "selector_reasons": output.reasons,
                    "selector_matched_features": output.matched_features,
                    "passed": passed,
                }
            )
    return rows


def matrix_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    positives = [row for row in rows if row["expected_group"] == "positive"]
    negatives = [row for row in rows if row["expected_group"] == "negative"]
    return {
        "case_count": len(rows),
        "positive_case_count": len(positives),
        "negative_case_count": len(negatives),
        "positive_pass_count": sum(1 for row in positives if row["passed"]),
        "negative_pass_count": sum(1 for row in negatives if row["passed"]),
        "positive_failures": [row["case_id"] for row in positives if not row["passed"]],
        "negative_failures": [row["case_id"] for row in negatives if not row["passed"]],
    }


def live_demo_statuses(repair_4k10: dict[str, Any]) -> dict[str, dict[str, Any]]:
    source = repair_4k10.get("live_demo_results")
    if not isinstance(source, dict):
        source = repair_4k10.get("live_demo_statuses")
    if not isinstance(source, dict):
        return {}
    result: dict[str, dict[str, Any]] = {}
    for checkpoint in ["LIVE-DEMO-002", "LIVE-DEMO-009", "LIVE-DEMO-014"]:
        payload = source.get(checkpoint) if isinstance(source.get(checkpoint), dict) else {}
        result[checkpoint] = {
            "checkpoint_id": payload.get("checkpoint_id") or "",
            "status": payload.get("status") or "deferred_or_fail",
            "failure_count": payload.get("failure_count"),
            "provider_calls_made": payload.get("provider_calls_made") is True,
            "intentionally_untouched_in_4k11": True,
        }
    return result


def build_result() -> dict[str, Any]:
    reconciliation = read_json(RECONCILIATION_4K10A_RESULT)
    repair = read_json(REPAIR_4K10_RESULT)
    expansion = read_json(EXPANSION_RESULT)
    target = reconciliation.get("target_case") if isinstance(reconciliation.get("target_case"), dict) else {}
    after_4k10a = reconciliation.get("after") if isinstance(reconciliation.get("after"), dict) else {}
    rows = selector_matrix()
    summary = matrix_summary(rows)
    route_signal = live_demo_statuses(repair)
    false_flags = {key: False for key in FALSE_FLAG_KEYS}
    provider_flags_remain_false = all(expansion.get(key) is False for key in [
        "provider_calls_made",
        "model_calls_made",
        "tts_calls_made",
        "crm_calls_made",
        "email_calls_made",
        "calendar_calls_made",
    ])
    acceptance = {
        "positive_boundary_sensitive_cases_select_respect_boundary": summary["positive_pass_count"] == summary["positive_case_count"],
        "benign_product_scope_cases_do_not_select_respect_boundary": summary["negative_pass_count"] == summary["negative_case_count"],
        "salesforce_case_remains_resolved_same_action": target.get("case_id") == "phase_4k8_b2b_saas_003"
        and target.get("runtime_action_id") == "respect_boundary"
        and target.get("selector_action_id") == "respect_boundary"
        and target.get("disagreement_review_classification") == "same_action"
        and target.get("agreement_disagreement_type") == "same_action",
        "false_asr_mapping_count_remains_zero": after_4k10a.get("false_asr_mapping_count") == 0,
        "genuine_selector_runtime_disagreement_count_remains_zero_or_non_actionable": after_4k10a.get(
            "genuine_selector_runtime_disagreement_count"
        )
        == 0,
        "naturalness_count_at_or_below_4k10": int(repair.get("after_naturalness_issue_count") or 999) <= 14,
        "routesignal_002_009_014_remain_deferred": all(
            route_signal.get(checkpoint, {}).get("status") == "deferred_or_fail"
            and route_signal.get(checkpoint, {}).get("intentionally_untouched_in_4k11") is True
            for checkpoint in ["LIVE-DEMO-002", "LIVE-DEMO-009", "LIVE-DEMO-014"]
        ),
        "selector_control_allowed_remains_false": expansion.get("selector_control_allowed") is False,
        "live_selector_control_recommended_remains_false": expansion.get("live_selector_control_recommended") is False,
        "response_replacement_performed_remains_false": expansion.get("response_replacement_performed") is False,
        "provider_model_tts_crm_email_calendar_flags_remain_false": provider_flags_remain_false,
        "raw_candidate_responses_absent_from_public_shadow_records": expansion.get("raw_candidate_response_recorded_count") == 0,
    }
    status = "pass" if all(acceptance.values()) else "fail"
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "generated_at": utc_now(),
        "status": status,
        "scope": "selector_only_boundary_sensitive_generalization_audit",
        "selector_matrix": rows,
        "selector_matrix_summary": summary,
        "acceptance": acceptance,
        "prior_evidence": {
            "phase_4k10a_checkpoint_id": RECONCILIATION_4K10A_ID,
            "phase_4k10_checkpoint_id": REPAIR_4K10_ID,
            "shadow_expansion_id": EXPANSION_ID,
            "salesforce_target_case": {
                "case_id": target.get("case_id") or "",
                "utterance": target.get("utterance") or "",
                "runtime_action_id": target.get("runtime_action_id") or "",
                "selector_action_id": target.get("selector_action_id") or "",
                "agreement_disagreement_type": target.get("agreement_disagreement_type") or "",
                "disagreement_review_classification": target.get("disagreement_review_classification") or "",
                "resolution_status": target.get("resolution_status") or "",
            },
            "selector_runtime_disagreement_count": after_4k10a.get("selector_runtime_disagreement_count"),
            "genuine_selector_runtime_disagreement_count": after_4k10a.get("genuine_selector_runtime_disagreement_count"),
            "false_asr_mapping_count": after_4k10a.get("false_asr_mapping_count"),
            "naturalness_issue_count": repair.get("after_naturalness_issue_count"),
        },
        "routesignal_deferred_status": route_signal,
        "raw_candidate_responses_absent_from_public_shadow_records": acceptance[
            "raw_candidate_responses_absent_from_public_shadow_records"
        ],
        **false_flags,
    }


def build_report(result: dict[str, Any]) -> str:
    prior = result["prior_evidence"]
    summary = result["selector_matrix_summary"]
    lines = [
        f"# {CHECKPOINT_ID}",
        "",
        f"- Status: {result['status']}",
        "- Scope: selector-only boundary-sensitive generalization audit",
        f"- Positive boundary-sensitive pass count: {summary['positive_pass_count']}/{summary['positive_case_count']}",
        f"- Benign product-scope pass count: {summary['negative_pass_count']}/{summary['negative_case_count']}",
        f"- Salesforce case remains same_action: {str(result['acceptance']['salesforce_case_remains_resolved_same_action']).lower()}",
        f"- False ASR mapping count: {prior['false_asr_mapping_count']}",
        f"- Genuine selector/runtime disagreement count: {prior['genuine_selector_runtime_disagreement_count']}",
        f"- 4K10 naturalness issue count: {prior['naturalness_issue_count']}",
        "- Selector control allowed: false",
        "- Live selector control recommended: false",
        "- Response replacement performed: false",
        "- Provider/model/TTS/CRM/email/calendar/side-effect path enabled: false",
        "- Raw candidate responses in public shadow records: false",
        "",
        "## Selector Matrix",
        "",
        "| Case | Expected | Selector action | Pass | Utterance |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in result["selector_matrix"]:
        lines.append(
            f"| {row['case_id']} | {row['expected_action_id']} | {row['selector_action_id']} | "
            f"{str(row['passed']).lower()} | {row['utterance']} |"
        )
    lines.extend(["", "## RouteSignal Deferred Status", ""])
    for checkpoint in ["LIVE-DEMO-002", "LIVE-DEMO-009", "LIVE-DEMO-014"]:
        payload = result["routesignal_deferred_status"].get(checkpoint, {})
        lines.append(
            f"- {checkpoint}: {payload.get('status')} "
            f"(failure_count={payload.get('failure_count')}, untouched_in_4k11=true)"
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- This phase did not enable live selector control.",
            "- This phase did not enable response replacement.",
            "- This phase did not call providers, models, TTS, CRM, email, calendar, payment, or account APIs.",
            "- This phase did not add private raw transcript/audio or raw candidate responses to public shadow evidence.",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    result = build_result()
    write_json(RESULT_PATH, result)
    write_text(REPORT_PATH, build_report(result))
    print(
        json.dumps(
            {
                "status": result["status"],
                "positive_pass_count": result["selector_matrix_summary"]["positive_pass_count"],
                "negative_pass_count": result["selector_matrix_summary"]["negative_pass_count"],
                "salesforce_same_action": result["acceptance"]["salesforce_case_remains_resolved_same_action"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
