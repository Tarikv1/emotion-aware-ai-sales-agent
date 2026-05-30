from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


CHECKPOINT_ID = "PHASE-4K12-ROUTESIGNAL-CALLBACK-APPOINTMENT-PROGRESSION-001"
GENERATED = ROOT / "research" / "experiments" / "generated"
OUT_DIR = GENERATED / CHECKPOINT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"

LIVE_DEMO_IDS = {
    "LIVE-DEMO-002": "LIVE-DEMO-002-conversation-stability-callback-disambiguation",
    "LIVE-DEMO-009": "LIVE-DEMO-009-appointment-lead-close",
    "LIVE-DEMO-014": "LIVE-DEMO-014-clear-pain-callback-followup",
}
PHASE_4K10_RESULT = GENERATED / "PHASE-4K10-SPOKEN-RESPONSE-REPAIR-001" / "result.json"
PHASE_4K10A_RESULT = GENERATED / "PHASE-4K10A-SELECTOR-RUNTIME-RECONCILIATION-001" / "result.json"
PHASE_4K11_RESULT = GENERATED / "PHASE-4K11-BOUNDARY-SENSITIVE-SELECTOR-GENERALIZATION-001" / "result.json"
SHADOW_EXPANSION_ID = "NON-LLM-ACTION-SELECTOR-RUNTIME-SHADOW-EXPANSION-001"
SHADOW_EXPANSION_RESULT = GENERATED / SHADOW_EXPANSION_ID / "result.json"

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
    "payment_calls_made",
    "account_side_effects_made",
    "selector_control_allowed",
    "live_selector_control_recommended",
    "response_replacement_performed",
    "side_effects_allowed",
    "raw_private_data",
    "raw_transcript_or_audio_public",
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


def normalize(text: str) -> str:
    return " ".join(str(text or "").casefold().split())


def live_demo_statuses() -> dict[str, dict[str, Any]]:
    statuses: dict[str, dict[str, Any]] = {}
    for short_id, checkpoint_id in LIVE_DEMO_IDS.items():
        payload = read_json(GENERATED / checkpoint_id / "result.json")
        statuses[short_id] = {
            "checkpoint_id": checkpoint_id,
            "passed": payload.get("passed") is True,
            "failure_count": payload.get("failure_count"),
            "provider_calls_made": payload.get("provider_calls_made") is True,
            "local_llm_calls_made": payload.get("local_llm_calls_made") is True,
            "status": "pass" if payload.get("passed") is True else "fail",
        }
    return statuses


def live_demo_evidence() -> dict[str, Any]:
    demo_002 = read_json(GENERATED / LIVE_DEMO_IDS["LIVE-DEMO-002"] / "result.json")
    demo_009 = read_json(GENERATED / LIVE_DEMO_IDS["LIVE-DEMO-009"] / "result.json")
    demo_014 = read_json(GENERATED / LIVE_DEMO_IDS["LIVE-DEMO-014"] / "result.json")
    workflow_rows = (
        ((demo_002.get("evidence") or {}).get("callback_workflow_gap") or [])
        if isinstance(demo_002.get("evidence"), dict)
        else []
    )
    scheduling = ((demo_009.get("evidence") or {}).get("scheduling_controls") or {}) if isinstance(demo_009.get("evidence"), dict) else {}
    appointment = (
        ((demo_009.get("evidence") or {}).get("appointment_time_confirmation") or {})
        if isinstance(demo_009.get("evidence"), dict)
        else {}
    )
    demo_014_evidence = demo_014.get("evidence") if isinstance(demo_014.get("evidence"), dict) else {}
    missed = demo_014_evidence.get("missed_callbacks") if isinstance(demo_014_evidence.get("missed_callbacks"), dict) else {}
    think = demo_014_evidence.get("think_about_it") if isinstance(demo_014_evidence.get("think_about_it"), dict) else {}
    callback_yes = demo_014_evidence.get("callback_later_yes") if isinstance(demo_014_evidence.get("callback_later_yes"), dict) else {}
    return {
        "live_demo_002": {
            "workflow_case_count": len(workflow_rows),
            "workflow_semantics": [row.get("semantic") for row in workflow_rows if isinstance(row, dict)],
            "workflow_responses": [
                {
                    "transcript": row.get("transcript"),
                    "response": row.get("response"),
                    "semantic": row.get("semantic"),
                }
                for row in workflow_rows
                if isinstance(row, dict)
            ],
            "callback_scheduling_controls": (demo_002.get("evidence") or {}).get("callback_scheduling_controls"),
            "stress_duplicate_response_count": (demo_002.get("evidence") or {}).get("stress_duplicate_response_count"),
            "stress_question_type_counts": (demo_002.get("evidence") or {}).get("stress_question_type_counts"),
        },
        "live_demo_009": {
            "scheduling_request_continuity_reason": (scheduling.get("request_continuity") or {}).get("reason"),
            "scheduling_time_call_control": scheduling.get("time_call_control"),
            "appointment_time_continuity_reason": (appointment.get("time_continuity") or {}).get("reason"),
            "appointment_time_call_control": appointment.get("time_call_control"),
        },
        "live_demo_014": {
            "all_clear_call_control": (demo_014_evidence.get("all_clear") or {}).get("call_control"),
            "missed_callbacks_response": missed.get("response"),
            "think_about_it_response": think.get("response"),
            "think_about_it_call_control": think.get("call_control"),
            "callback_later_yes_response": callback_yes.get("response"),
            "callback_later_yes_call_control": callback_yes.get("call_control"),
        },
    }


def prior_evidence() -> dict[str, Any]:
    phase_4k10 = read_json(PHASE_4K10_RESULT)
    phase_4k10a = read_json(PHASE_4K10A_RESULT)
    phase_4k11 = read_json(PHASE_4K11_RESULT)
    shadow = read_json(SHADOW_EXPANSION_RESULT)
    target = phase_4k10a.get("target_case") if isinstance(phase_4k10a.get("target_case"), dict) else {}
    after_4k10a = phase_4k10a.get("after") if isinstance(phase_4k10a.get("after"), dict) else {}
    return {
        "phase_4k10_status": phase_4k10.get("status"),
        "phase_4k10_after_naturalness_issue_count": phase_4k10.get("after_naturalness_issue_count"),
        "phase_4k10_live_demo_results": phase_4k10.get("live_demo_results"),
        "phase_4k10a_status": phase_4k10a.get("status"),
        "phase_4k10a_salesforce_case": {
            "case_id": target.get("case_id"),
            "utterance": target.get("utterance"),
            "runtime_action_id": target.get("runtime_action_id"),
            "selector_action_id": target.get("selector_action_id"),
            "agreement_disagreement_type": target.get("agreement_disagreement_type"),
            "disagreement_review_classification": target.get("disagreement_review_classification"),
        },
        "false_asr_mapping_count": after_4k10a.get("false_asr_mapping_count"),
        "genuine_selector_runtime_disagreement_count": after_4k10a.get("genuine_selector_runtime_disagreement_count"),
        "selector_runtime_disagreement_count": after_4k10a.get("selector_runtime_disagreement_count"),
        "phase_4k11_status": phase_4k11.get("status"),
        "phase_4k11_selector_matrix_summary": phase_4k11.get("selector_matrix_summary"),
        "shadow_expansion_flags": {
            "selector_control_allowed": shadow.get("selector_control_allowed"),
            "live_selector_control_recommended": shadow.get("live_selector_control_recommended"),
            "response_replacement_performed": shadow.get("response_replacement_performed"),
            "provider_calls_made": shadow.get("provider_calls_made"),
            "model_calls_made": shadow.get("model_calls_made"),
            "tts_calls_made": shadow.get("tts_calls_made"),
            "crm_calls_made": shadow.get("crm_calls_made"),
            "email_calls_made": shadow.get("email_calls_made"),
            "calendar_calls_made": shadow.get("calendar_calls_made"),
            "raw_candidate_response_recorded_count": shadow.get("raw_candidate_response_recorded_count"),
        },
    }


def build_acceptance(evidence: dict[str, Any], prior: dict[str, Any], statuses: dict[str, dict[str, Any]]) -> dict[str, bool]:
    live_009 = evidence["live_demo_009"]
    live_014 = evidence["live_demo_014"]
    missed = normalize(live_014.get("missed_callbacks_response"))
    think = normalize(live_014.get("think_about_it_response"))
    callback_yes = normalize(live_014.get("callback_later_yes_response"))
    target = prior["phase_4k10a_salesforce_case"]
    shadow = prior["shadow_expansion_flags"]
    return {
        "live_demo_002_009_014_pass": all(item.get("passed") is True and item.get("failure_count") == 0 for item in statuses.values()),
        "live_demo_002_callback_workflow_cases_remain_workflow_not_scheduling": evidence["live_demo_002"]["workflow_case_count"] >= 8
        and all(semantic == "callback_workflow_gap" for semantic in evidence["live_demo_002"]["workflow_semantics"]),
        "live_demo_009_callback_request_reason_preserved": live_009.get("scheduling_request_continuity_reason") == "callback_request_time_needed",
        "live_demo_009_appointment_time_confirmation_preserved": live_009.get("appointment_time_continuity_reason") == "appointment_time_confirmed"
        and live_009.get("appointment_time_call_control") == "schedule-and-end",
        "live_demo_014_missed_callbacks_moves_to_workflow_review": "short workflow review" in missed
        and "northstar" in missed
        and "missed callback" in missed,
        "live_demo_014_deferred_callback_keeps_time_capture_open": live_014.get("think_about_it_call_control") == "continue-call"
        and ("callback" in think or "call back" in think)
        and "what time" in think
        and live_014.get("callback_later_yes_call_control") == "continue-call"
        and ("callback" in callback_yes or "call back" in callback_yes)
        and "what time" in callback_yes,
        "phase_4k10_naturalness_count_at_or_below_14": int(prior.get("phase_4k10_after_naturalness_issue_count") or 999) <= 14,
        "salesforce_case_remains_same_action": target.get("case_id") == "phase_4k8_b2b_saas_003"
        and target.get("runtime_action_id") == "respect_boundary"
        and target.get("selector_action_id") == "respect_boundary"
        and target.get("agreement_disagreement_type") == "same_action"
        and target.get("disagreement_review_classification") == "same_action",
        "false_asr_mapping_count_remains_zero": prior.get("false_asr_mapping_count") == 0,
        "genuine_selector_runtime_disagreement_count_remains_zero": prior.get("genuine_selector_runtime_disagreement_count") == 0,
        "phase_4k11_selector_matrix_still_passes": prior.get("phase_4k11_status") == "pass",
        "selector_control_and_response_replacement_remain_blocked": shadow.get("selector_control_allowed") is False
        and shadow.get("live_selector_control_recommended") is False
        and shadow.get("response_replacement_performed") is False,
        "provider_model_tts_crm_email_calendar_flags_remain_false": all(
            shadow.get(key) is False
            for key in [
                "provider_calls_made",
                "model_calls_made",
                "tts_calls_made",
                "crm_calls_made",
                "email_calls_made",
                "calendar_calls_made",
            ]
        ),
        "raw_candidate_responses_absent_from_public_shadow_records": shadow.get("raw_candidate_response_recorded_count") == 0,
    }


def build_result() -> dict[str, Any]:
    statuses = live_demo_statuses()
    evidence = live_demo_evidence()
    prior = prior_evidence()
    acceptance = build_acceptance(evidence, prior, statuses)
    false_flags = {key: False for key in FALSE_FLAG_KEYS}
    result = {
        "checkpoint_id": CHECKPOINT_ID,
        "generated_at": utc_now(),
        "status": "pass" if all(acceptance.values()) else "fail",
        "scope": "routesignal_runtime_dialogue_repair_only",
        "live_demo_statuses": statuses,
        "routesignal_evidence": evidence,
        "prior_evidence": prior,
        "acceptance": acceptance,
        "public_openai_plan_dialogue_modified": False,
        "raw_private_transcript_or_audio_added_to_public_evidence": False,
        "raw_candidate_responses_absent_from_public_shadow_records": acceptance[
            "raw_candidate_responses_absent_from_public_shadow_records"
        ],
        **false_flags,
    }
    return result


def build_report(result: dict[str, Any]) -> str:
    acceptance = result["acceptance"]
    prior = result["prior_evidence"]
    live_009 = result["routesignal_evidence"]["live_demo_009"]
    live_014 = result["routesignal_evidence"]["live_demo_014"]
    lines = [
        f"# {CHECKPOINT_ID}",
        "",
        f"- Status: {result['status']}",
        "- Scope: RouteSignal runtime/dialogue repair only",
        f"- LIVE-DEMO-002/009/014 pass: {str(acceptance['live_demo_002_009_014_pass']).lower()}",
        f"- Salesforce case remains same_action: {str(acceptance['salesforce_case_remains_same_action']).lower()}",
        f"- False ASR mapping count: {prior['false_asr_mapping_count']}",
        f"- Genuine selector/runtime disagreement count: {prior['genuine_selector_runtime_disagreement_count']}",
        f"- Selector/runtime disagreement count: {prior['selector_runtime_disagreement_count']}",
        f"- 4K10 naturalness issue count: {prior['phase_4k10_after_naturalness_issue_count']}",
        "- Selector control allowed: false",
        "- Live selector control recommended: false",
        "- Response replacement performed: false",
        "- Provider/model/TTS/CRM/email/calendar/payment/account side-effect path enabled: false",
        "- Raw private transcript/audio in public evidence: false",
        "- Raw candidate responses in public shadow records: false",
        "",
        "## RouteSignal Results",
        "",
    ]
    for short_id, payload in result["live_demo_statuses"].items():
        lines.append(f"- {short_id}: {payload['status']} (failure_count={payload['failure_count']})")
    lines.extend(
        [
            "",
            "## Key Progression Checks",
            "",
            f"- LIVE-DEMO-009 callback request reason: {live_009['scheduling_request_continuity_reason']}",
            f"- LIVE-DEMO-009 appointment time reason/control: {live_009['appointment_time_continuity_reason']} / {live_009['appointment_time_call_control']}",
            f"- LIVE-DEMO-014 missed callbacks response: {live_014['missed_callbacks_response']}",
            f"- LIVE-DEMO-014 think-about-it response: {live_014['think_about_it_response']}",
            f"- LIVE-DEMO-014 callback-later yes response: {live_014['callback_later_yes_response']}",
            "",
            "## Acceptance",
            "",
        ]
    )
    for key, value in acceptance.items():
        lines.append(f"- {key}: {str(value).lower()}")
    return "\n".join(lines)


def main() -> int:
    result = build_result()
    write_json(RESULT_PATH, result)
    write_text(REPORT_PATH, build_report(result))
    print(json.dumps({"status": result["status"], "acceptance": result["acceptance"]}, indent=2, sort_keys=True))
    if result["status"] != "pass":
        raise AssertionError(f"{CHECKPOINT_ID} failed. See {RESULT_PATH}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
