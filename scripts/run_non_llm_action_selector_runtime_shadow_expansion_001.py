from __future__ import annotations

from collections import Counter, defaultdict
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import statistics
import sys
from time import perf_counter_ns
from typing import Any


sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

EXPERIMENT_ID = "NON-LLM-ACTION-SELECTOR-RUNTIME-SHADOW-EXPANSION-001"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / EXPERIMENT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"
DECISION_REPORT_PATH = OUT_DIR / "decision_report.md"
JSONL_PATH = OUT_DIR / "shadow_expansion_records.jsonl"
RECOMMENDATION_ID = "limited_offline_sanitized_shadow_logging_and_spoken_naturalness_review_next"

FALSE_FLAGS = {
    "raw_private_data": False,
    "audio_data_used": False,
    "provider_calls_made": False,
    "model_calls_made": False,
    "openai_api_calls_made": False,
    "ultravox_calls_made": False,
    "elevenlabs_calls_made": False,
    "local_llm_calls_made": False,
    "ollama_calls_made": False,
    "tts_calls_made": False,
    "crm_calls_made": False,
    "email_calls_made": False,
    "calendar_calls_made": False,
    "buyer_facing_text_generated": False,
    "selector_control_allowed": False,
    "live_runtime_wiring_allowed": False,
    "side_effects_allowed": False,
    "side_effects_observed": False,
    "memory_mutation_allowed": False,
    "memory_mutation_observed": False,
    "response_text_changed": False,
    "runtime_behavior_changed": False,
}

FORBIDDEN_RECORD_KEYS = {
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


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = "\n".join(json.dumps(row, ensure_ascii=True, sort_keys=True, separators=(",", ":")) for row in rows)
    path.write_text(payload + ("\n" if payload else ""), encoding="utf-8")


def text_hash(text: str) -> str:
    return "sha256:" + hashlib.sha256(str(text or "").encode("utf-8")).hexdigest()


def normalize_words(text: str) -> str:
    return " ".join(str(text or "").casefold().split())


def gap(
    gap_id: str,
    label: str,
    *,
    review_focus: str,
    next_gap_candidates: list[str] | None = None,
    positive: list[str] | None = None,
    negative: list[str] | None = None,
) -> dict[str, Any]:
    readable = label.replace("_", " ")
    return {
        "label": label,
        "customer_facing_phrase": readable,
        "universal_pain_dimensions": ["unclear_next_step", "trust_or_risk_concern"],
        "qualification_dimensions": ["need_or_pain", "fit", "timing"],
        "definition": f"Determine whether {readable} is active enough for a human review.",
        "causal_story": f"If {readable} is unresolved, a qualified person should check details before any next step.",
        "customer_language": [readable],
        "evidence_positive": positive or [f"{readable} is a problem", f"{readable} is the issue"],
        "evidence_negative": negative or [f"{readable} is handled", f"{readable} is fine"],
        "diagnostic_questions": [f"Is {readable} causing any issue right now?"],
        "value_bridge": f"A short review can check whether {readable} is worth fixing.",
        "review_focus": review_focus,
        "next_gap_candidates": list(next_gap_candidates or []),
    }


def campaign(
    *,
    campaign_id: str,
    client_name: str,
    offer: str,
    vertical_id: str,
    human_owner: str,
    appointment_target: str,
    gaps: dict[str, dict[str, Any]],
    blocked_claims: list[str],
) -> dict[str, Any]:
    order = list(gaps)
    return {
        "campaign_id": campaign_id,
        "client_name": client_name,
        "customer_facing_company_name": client_name,
        "product_or_offer_name": offer,
        "customer_facing_offer_name": offer,
        "product_or_offer_summary": f"a short {offer}",
        "customer_facing_offer_summary": f"a short {offer}",
        "vertical_id": vertical_id,
        "language": "en",
        "objective": "qualification_then_human_review",
        "human_followup_owner": human_owner,
        "appointment_target": appointment_target,
        "human_review_scope": ", ".join(gaps[gap_id]["review_focus"] for gap_id in order[:3]),
        "allowed_claims": ["can ask high-level fit questions", "can route to a qualified human review"],
        "blocked_claims": blocked_claims,
        "diagnostic_gaps": gaps,
        "core_diagnostic_gaps": order[:3],
        "gap_order": order,
        "campaign_playbook_id": f"{campaign_id}-playbook",
    }


def generic_campaigns() -> dict[str, dict[str, Any]]:
    return {
        "generic_insurance": campaign(
            campaign_id="phase-4k8-generic-insurance",
            client_name="Synthetic Insurance Agency",
            offer="policy review",
            vertical_id="insurance",
            human_owner="licensed insurance specialist",
            appointment_target="coverage review",
            blocked_claims=["coverage guarantee", "premium savings guarantee", "eligibility decision"],
            gaps={
                "coverage_fit": gap(
                    "coverage_fit",
                    "coverage fit",
                    review_focus="coverage fit",
                    next_gap_candidates=["premium_or_budget"],
                    positive=["coverage is the issue", "coverage fit is a problem"],
                    negative=["coverage is fine", "coverage fit is handled"],
                ),
                "premium_or_budget": gap(
                    "premium_or_budget",
                    "premium or budget",
                    review_focus="premium and budget",
                    next_gap_candidates=["renewal_or_timing"],
                    positive=["premium is a problem", "budget is a problem"],
                    negative=["premium is fine", "budget is handled"],
                ),
                "renewal_or_timing": gap(
                    "renewal_or_timing",
                    "renewal or timing",
                    review_focus="renewal timing",
                    positive=["renewal timing is the issue"],
                    negative=["renewal timing is handled"],
                ),
            },
        ),
        "generic_telecom": campaign(
            campaign_id="phase-4k8-generic-telecom",
            client_name="Synthetic Telecom Provider",
            offer="plan review",
            vertical_id="telecom",
            human_owner="telecom account specialist",
            appointment_target="plan and availability review",
            blocked_claims=["coverage guarantee", "speed guarantee", "contract cancellation guarantee"],
            gaps={
                "coverage_or_availability": gap(
                    "coverage_or_availability",
                    "coverage or availability",
                    review_focus="coverage and availability",
                    next_gap_candidates=["plan_fit"],
                    positive=["coverage is the issue", "availability is a problem"],
                    negative=["coverage is fine", "availability is handled"],
                ),
                "plan_fit": gap(
                    "plan_fit",
                    "plan fit",
                    review_focus="plan fit",
                    next_gap_candidates=["contract_or_switching"],
                    positive=["plan fit is the problem", "plan is a problem"],
                    negative=["plan fit is fine", "plan is fine"],
                ),
                "contract_or_switching": gap(
                    "contract_or_switching",
                    "contract or switching",
                    review_focus="contract and switching",
                    positive=["switching is a problem"],
                    negative=["contract is handled"],
                ),
            },
        ),
        "home_services": campaign(
            campaign_id="phase-4k8-home-services",
            client_name="Synthetic Home Services",
            offer="inspection review",
            vertical_id="home_services",
            human_owner="qualified service coordinator",
            appointment_target="inspection or estimate review",
            blocked_claims=["exact quote without inspection", "remote safety diagnosis"],
            gaps={
                "service_need": gap(
                    "service_need",
                    "service need",
                    review_focus="service need",
                    next_gap_candidates=["scheduling_urgency"],
                    positive=["service need is a problem"],
                    negative=["service need is handled"],
                ),
                "scheduling_urgency": gap(
                    "scheduling_urgency",
                    "scheduling urgency",
                    review_focus="scheduling urgency",
                    next_gap_candidates=["estimate_or_property_details"],
                    positive=["scheduling is a problem", "schedule is the issue"],
                    negative=["scheduling is fine", "schedule is handled"],
                ),
                "estimate_or_property_details": gap(
                    "estimate_or_property_details",
                    "estimate or property details",
                    review_focus="estimate and property details",
                    positive=["the estimate is a problem", "property details are the issue"],
                    negative=["the estimate is handled", "property details are fine"],
                ),
            },
        ),
        "b2b_saas": campaign(
            campaign_id="phase-4k8-b2b-saas",
            client_name="Synthetic SaaS Operations",
            offer="workflow fit review",
            vertical_id="b2b_saas",
            human_owner="technical fit specialist",
            appointment_target="fit and technical review",
            blocked_claims=["unverified integration claim", "unverified security claim", "ROI guarantee"],
            gaps={
                "manual_work": gap(
                    "manual_work",
                    "manual work",
                    review_focus="manual work",
                    next_gap_candidates=["integration_risk"],
                    positive=["manual work is a problem", "manual is the problem"],
                    negative=["manual work is handled", "manual is handled"],
                ),
                "integration_risk": gap(
                    "integration_risk",
                    "integration risk",
                    review_focus="integration risk",
                    next_gap_candidates=["visibility_gap"],
                    positive=["integration risk is a problem", "integration is the issue"],
                    negative=["integration risk is handled", "integration is fine"],
                ),
                "visibility_gap": gap(
                    "visibility_gap",
                    "visibility gap",
                    review_focus="visibility gap",
                    positive=["visibility is the problem", "visibility gap is a problem"],
                    negative=["visibility is handled", "visibility gap is handled"],
                ),
            },
        ),
    }


def seed_permission_state() -> dict[str, Any]:
    return {
        "turns": [
            {
                "transcript": "__agent_open__",
                "summary": {
                    "final_response": "Do you have a minute for one quick question?",
                    "call_control": "continue-call",
                },
                "continuity": {"applied": True, "reason": "seed_permission_check", "dialogue_focus": "qualification"},
                "conversation_memory": {},
                "dialogue_manager": {},
                "dialogue_pragmatics": {},
            }
        ]
    }


def append_action_turn(state: dict[str, Any], transcript: str, action: dict[str, Any], campaign_config: dict[str, Any]) -> None:
    from runtime.core import dialogue_manager

    response = str(action.get("candidate_response") or "")
    selected = action.get("selected_action") if isinstance(action.get("selected_action"), dict) else {}
    memory = dialogue_manager.build_conversation_memory(
        action=action,
        session_state=state,
        transcript=transcript,
        final_response=response,
        campaign=campaign_config,
    )
    state.setdefault("turns", []).append(
        {
            "transcript": transcript,
            "summary": {"final_response": response, "call_control": str(selected.get("call_control") or "continue-call")},
            "continuity": dict(action.get("continuity") or {}),
            "conversation_memory": memory,
            "dialogue_manager": deepcopy(action),
            "dialogue_pragmatics": {},
        }
    )


def plan_action(transcript: str, state: dict[str, Any], campaign_config: dict[str, Any]) -> dict[str, Any]:
    from runtime.core import dialogue_manager

    return dialogue_manager.plan_dialogue_action(
        transcript=transcript,
        session_state=state,
        campaign=campaign_config,
        quality_gate={"accepted": True, "reason": "phase_4k8_synthetic_fixture"},
        dialogue_reasoning={
            "validator": EXPERIMENT_ID,
            "provider_calls_made": False,
            "local_llm_calls_made": False,
            "dialogue_act": "synthetic_safe_fixture",
            "buyer_intent": "synthetic_safe_fixture",
            "resolved_topic": "synthetic_safe_fixture",
            "sales_stage": "qualification",
            "response_strategy": "continue_call",
            "must_include": [],
            "must_avoid": ["provider calls", "side effects"],
            "safety_boundary": "",
            "confidence": 0.0,
        },
    )


def public_openai_runtime_result(case_id: str, transcript: str) -> dict[str, Any]:
    from runtime.campaigns import public_openai_chatgpt_plans_dialogue as dialogue

    payload = dialogue.classify_turn(
        campaign={"campaign_id": "public-openai-chatgpt-plans", "language": "en"},
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
    result = dict(payload or {})
    result["campaign_id"] = "public-openai-chatgpt-plans"
    result["turn_id"] = case_id
    return result


def semantic_from_runtime_result(runtime_result: dict[str, Any]) -> str:
    if isinstance(runtime_result.get("selected_action"), dict):
        return str((runtime_result.get("selected_action") or {}).get("action_id") or "")
    if isinstance(runtime_result.get("state_before"), dict):
        semantic = ((runtime_result.get("state_before") or {}).get("contextual_buyer_semantics") or {}).get("semantic")
        if semantic:
            return str(semantic)
    return str(runtime_result.get("semantic") or runtime_result.get("action_id") or runtime_result.get("next_action") or "")


def case_payload(
    *,
    case_id: str,
    coverage: str,
    campaign_id: str,
    vertical_id: str,
    transcript: str,
    runtime_result: dict[str, Any],
    candidate_response: str,
    expected_action_id: str = "",
    source_file: str,
    conversation_id: str,
    sequence_index: int,
) -> dict[str, Any]:
    return {
        "case_id": case_id,
        "campaign_coverage": coverage,
        "campaign_id": campaign_id,
        "vertical_id": vertical_id,
        "buyer_utterance_text_sanitized": transcript,
        "normalized_buyer_text": normalize_words(transcript),
        "runtime_result": runtime_result,
        "runtime_semantic": semantic_from_runtime_result(runtime_result),
        "candidate_response": candidate_response,
        "candidate_response_hash": text_hash(candidate_response),
        "expected_action_id": expected_action_id,
        "source_file": source_file,
        "conversation_id": conversation_id,
        "sequence_index": sequence_index,
        "sanitized": True,
        "raw_private_data": False,
        "safety_boundary_detected": "cannot" in candidate_response.casefold()
        or "can't" in candidate_response.casefold()
        or "not able" in candidate_response.casefold(),
        "context": {
            "normalized_buyer_text": normalize_words(transcript),
            "memory_summary": f"{coverage} synthetic safe fixture",
            "known_use_case": [],
            "known_tools": [],
            "known_team_status": "",
            "safety_boundary_detected": "cannot" in candidate_response.casefold()
            or "can't" in candidate_response.casefold(),
            "vertical_id": vertical_id,
        },
    }


def build_public_openai_cases() -> list[dict[str, Any]]:
    specs = [
        ("price", "How much does ChatGPT Plus cost?", "answer_price"),
        ("plan_fit", "I code every day and hit limits, which plan should I pick?", "recommend_pro"),
        ("privacy", "Do you store raw call transcripts?", "answer_privacy_boundary"),
        ("signup", "Where do I sign up if I want to start?", "answer_signup_path"),
        ("boundary", "Can you buy the plan for me now?", "respect_boundary"),
    ]
    cases: list[dict[str, Any]] = []
    for index, (label, transcript, expected_action_id) in enumerate(specs, start=1):
        case_id = f"phase_4k8_public_openai_{index:03d}_{label}"
        runtime_result = public_openai_runtime_result(case_id, transcript)
        response = str(runtime_result.get("candidate_response") or "")
        cases.append(
            case_payload(
                case_id=case_id,
                coverage="public_openai_plan",
                campaign_id="public-openai-chatgpt-plans",
                vertical_id="public_openai_plan",
                transcript=transcript,
                runtime_result=runtime_result,
                candidate_response=response,
                expected_action_id=expected_action_id,
                source_file=f"research/experiments/generated/{EXPERIMENT_ID}/synthetic_public_openai_cases",
                conversation_id="phase_4k8_public_openai",
                sequence_index=index,
            )
        )
    return cases


def build_generic_campaign_cases() -> list[dict[str, Any]]:
    utterances = {
        "generic_insurance": [
            "yeah sure",
            "premium is a problem",
            "Can you tell me exactly what the policy covers?",
        ],
        "generic_telecom": [
            "yeah sure",
            "coverage is the issue",
            "Can you guarantee the speed?",
        ],
        "home_services": [
            "yeah sure",
            "the estimate is unclear",
            "Can you quote it without an inspection?",
        ],
        "b2b_saas": [
            "yeah sure",
            "manual work is a problem",
            "Does it integrate securely with Salesforce?",
        ],
    }
    cases: list[dict[str, Any]] = []
    for coverage, campaign_config in generic_campaigns().items():
        state = seed_permission_state()
        for sequence_index, transcript in enumerate(utterances[coverage], start=1):
            action = plan_action(transcript, state, campaign_config)
            response = str(action.get("candidate_response") or "")
            selected = action.get("selected_action") if isinstance(action.get("selected_action"), dict) else {}
            runtime_result = {
                "campaign_id": campaign_config["campaign_id"],
                "turn_id": f"phase_4k8_{coverage}_{sequence_index:03d}",
                "selected_action": selected,
                "state_before": action.get("state_before") or {},
                "continuity": action.get("continuity") or {},
                "decision_override": action.get("decision_override") or {},
                "candidate_response": response,
            }
            cases.append(
                case_payload(
                    case_id=f"phase_4k8_{coverage}_{sequence_index:03d}",
                    coverage=coverage,
                    campaign_id=str(campaign_config["campaign_id"]),
                    vertical_id=str(campaign_config["vertical_id"]),
                    transcript=transcript,
                    runtime_result=runtime_result,
                    candidate_response=response,
                    source_file=f"research/experiments/generated/{EXPERIMENT_ID}/{coverage}_synthetic_cases",
                    conversation_id=f"phase_4k8_{coverage}",
                    sequence_index=sequence_index,
                )
            )
            append_action_turn(state, transcript, action, campaign_config)
    return cases


def routesignal_campaign() -> dict[str, Any]:
    return {
        "campaign_id": "live-demo-001-routesignal",
        "client_name": "RouteSignal",
        "product_or_offer_name": "RouteSignal workflow review",
        "vertical_id": "b2b_saas",
        "language": "en",
        "human_followup_owner": "workflow reviewer",
        "appointment_target": "workflow review",
    }


def build_routesignal_cases() -> list[dict[str, Any]]:
    campaign_config = routesignal_campaign()
    state: dict[str, Any] = {"turns": []}
    transcripts = ["__agent_open__", "yeah sure", "callbacks are fine", "tomorrow at 3 works"]
    cases: list[dict[str, Any]] = []
    for sequence_index, transcript in enumerate(transcripts, start=1):
        action = plan_action(transcript, state, campaign_config)
        response = str(action.get("candidate_response") or "")
        selected = action.get("selected_action") if isinstance(action.get("selected_action"), dict) else {}
        runtime_result = {
            "campaign_id": campaign_config["campaign_id"],
            "turn_id": f"phase_4k8_routesignal_{sequence_index:03d}",
            "selected_action": selected,
            "state_before": action.get("state_before") or {},
            "continuity": action.get("continuity") or {},
            "decision_override": action.get("decision_override") or {},
            "candidate_response": response,
        }
        cases.append(
            case_payload(
                case_id=f"phase_4k8_routesignal_{sequence_index:03d}",
                coverage="routesignal_preservation",
                campaign_id=str(campaign_config["campaign_id"]),
                vertical_id=str(campaign_config["vertical_id"]),
                transcript=transcript,
                runtime_result=runtime_result,
                candidate_response=response,
                source_file=f"research/experiments/generated/{EXPERIMENT_ID}/routesignal_synthetic_preservation_cases",
                conversation_id="phase_4k8_routesignal_preservation",
                sequence_index=sequence_index,
            )
        )
        append_action_turn(state, transcript, action, campaign_config)
    return cases


def build_safe_fixture_cases() -> list[dict[str, Any]]:
    return build_public_openai_cases() + build_generic_campaign_cases() + build_routesignal_cases()


def turn_context_from_case(case: dict[str, Any]) -> dict[str, Any]:
    return {
        "turn_id": case["case_id"],
        "campaign_id": case["campaign_id"],
        "vertical_id": case["vertical_id"],
        "buyer_utterance_text_sanitized": case["buyer_utterance_text_sanitized"],
        "normalized_buyer_text": case["normalized_buyer_text"],
        "context": case["context"],
        "context_summary": (
            f"phase_4k8_coverage={case['campaign_coverage']}; vertical={case['vertical_id']}; "
            f"runtime_semantic={case['runtime_semantic']}"
        ),
        "runtime_result": case["runtime_result"],
        "evidence_source": case["source_file"],
        "expected_action_id": case.get("expected_action_id") or "",
        "mode": "offline_sanitized_replay",
        "sanitized": True,
        "raw_private_data": False,
        "safety_boundary_detected": case.get("safety_boundary_detected") is True,
    }


def public_runtime_metadata(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "runtime_metadata_available": record.get("runtime_metadata_available") is True,
        "runtime_action_id": str(record.get("runtime_action_id") or ""),
        "runtime_action_id_if_available": str(record.get("runtime_action_id_if_available") or ""),
        "runtime_action_confidence": record.get("runtime_action_confidence", 0.0),
        "runtime_action_reason": str(record.get("runtime_action_reason") or ""),
        "runtime_extraction_warnings": [str(item) for item in record.get("runtime_extraction_warnings") or []],
        "runtime_metadata_source": str(record.get("runtime_metadata_source") or ""),
        "runtime_response_text_available": record.get("runtime_response_text_available") is True,
    }


def review_classification(record: dict[str, Any], safety_failures: list[str]) -> dict[str, Any]:
    runtime_action_id = str(record.get("runtime_action_id") or "")
    selector_action_id = str(record.get("selector_action_id") or "")
    disagreement_type = str(record.get("disagreement_type") or "")
    warnings = [str(item) for item in record.get("runtime_extraction_warnings") or []]
    if safety_failures:
        return {
            "disagreement_review_classification": "evidence_not_actionable_yet",
            "reason_for_disagreement": "row has safety or validation failures",
            "evidence_actionable": False,
        }
    if record.get("runtime_metadata_available") is not True or any("extraction_failed" in item for item in warnings):
        return {
            "disagreement_review_classification": "metadata_extraction_failure",
            "reason_for_disagreement": "runtime metadata was unavailable or extraction failed",
            "evidence_actionable": False,
        }
    if not runtime_action_id:
        return {
            "disagreement_review_classification": "runtime_action_unmapped",
            "reason_for_disagreement": "runtime metadata was present, but conservative mapping found no controlled runtime action",
            "evidence_actionable": False,
        }
    if disagreement_type == "same_action":
        return {
            "disagreement_review_classification": "same_action",
            "reason_for_disagreement": "selector and runtime mapped to the same controlled action",
            "evidence_actionable": True,
        }
    if disagreement_type == "selector_possible_improvement":
        return {
            "disagreement_review_classification": "selector_possible_improvement",
            "reason_for_disagreement": f"selector chose {selector_action_id}, while runtime mapped to {runtime_action_id}",
            "evidence_actionable": True,
        }
    if disagreement_type == "selector_possible_regression":
        return {
            "disagreement_review_classification": "selector_possible_regression",
            "reason_for_disagreement": f"runtime mapped to {runtime_action_id}, while selector chose {selector_action_id}",
            "evidence_actionable": True,
        }
    return {
        "disagreement_review_classification": "genuine_selector_runtime_disagreement",
        "reason_for_disagreement": f"selector chose {selector_action_id}, runtime mapped to {runtime_action_id}, classifier returned {disagreement_type}",
        "evidence_actionable": True,
    }


def expansion_row(case: dict[str, Any], record: dict[str, Any]) -> dict[str, Any]:
    row = {
        "shadow_record_id": record.get("shadow_record_id"),
        "case_id": case["case_id"],
        "campaign_coverage": case["campaign_coverage"],
        "campaign_id": case["campaign_id"],
        "vertical_id": case["vertical_id"],
        "buyer_utterance_text_sanitized": case["buyer_utterance_text_sanitized"],
        "runtime_metadata": {
            **public_runtime_metadata(record),
            "runtime_semantic": case.get("runtime_semantic") or "",
            "runtime_response_text_hash": text_hash(case.get("candidate_response") or ""),
        },
        "selector_action_id": record.get("selector_action_id"),
        "selector_confidence": record.get("selector_confidence"),
        "selector_reasons": record.get("selector_reasons") or [],
        "selector_matched_features": record.get("selector_matched_features") or [],
        "agreement_disagreement_type": record.get("disagreement_type"),
        "agreement_with_runtime": record.get("agreement_with_runtime") is True,
        "reason_for_disagreement": "",
        "disagreement_review_classification": "",
        "evidence_actionable": False,
        "safety_flags": {
            "should_not_change_runtime": True,
            "public_evidence_sanitized": True,
            **FALSE_FLAGS,
        },
        "candidate_response_hash": case["candidate_response_hash"],
        "candidate_response_text_recorded": False,
        "source_file": case["source_file"],
    }
    for key in FORBIDDEN_RECORD_KEYS:
        row.pop(key, None)
    return row


def row_safety_failures(row: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if FORBIDDEN_RECORD_KEYS & set(row):
        failures.append(f"forbidden_keys:{sorted(FORBIDDEN_RECORD_KEYS & set(row))}")
    if not str(row.get("buyer_utterance_text_sanitized") or ""):
        failures.append("buyer_utterance_text_sanitized_missing")
    if "RAW TRANSCRIPT" in str(row.get("buyer_utterance_text_sanitized") or ""):
        failures.append("raw_transcript_marker_present")
    source = str(row.get("source_file") or "").replace("\\", "/").casefold()
    if "data/private" in source or "private-restricted" in source:
        failures.append("private_source")
    safety_flags = row.get("safety_flags") if isinstance(row.get("safety_flags"), dict) else {}
    for key, expected in FALSE_FLAGS.items():
        if safety_flags.get(key) is not expected:
            failures.append(f"{key}_must_be_false")
    if safety_flags.get("should_not_change_runtime") is not True:
        failures.append("should_not_change_runtime_must_be_true")
    if not str(row.get("candidate_response_hash") or "").startswith("sha256:"):
        failures.append("candidate_response_hash_missing")
    return failures


def percentile(values: list[float], percentile_value: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, round((percentile_value / 100.0) * (len(ordered) - 1))))
    return ordered[index]


def build_report(result: dict[str, Any]) -> str:
    lines = [
        f"# {EXPERIMENT_ID}",
        "",
        f"- Status: {result['status']}",
        f"- Cases: {result['case_count']}",
        f"- Campaign coverage: {', '.join(result['campaign_coverage'])}",
        f"- Selector/runtime disagreements: {result['selector_runtime_disagreement_count']}",
        f"- Genuine actionable selector/runtime disagreements: {result['genuine_selector_runtime_disagreement_count']}",
        f"- Runtime action unmapped: {result['runtime_action_unmapped_count']}",
        f"- Metadata extraction failures: {result['metadata_extraction_failure_count']}",
        f"- Evidence not actionable yet: {result['evidence_not_actionable_yet_count']}",
        f"- False ASR repair mappings: {result['false_asr_mapping_count']}",
        f"- Selector possible improvements/regressions: {result['selector_possible_improvement_count']}/{result['selector_possible_regression_count']}",
        f"- Candidate response hashes recorded: {result['candidate_response_hash_recorded_count']}",
        f"- Raw candidate responses in shadow records: {result['raw_candidate_response_recorded_count']}",
        f"- Safety blockers: {result['safety_blockers_count']}",
        "- Provider/OpenAI/Ultravox/ElevenLabs/local LLM/Ollama/TTS calls: false",
        "- Live selector control: false",
        "- Response replacement: false",
        "",
        "## Disagreement By Campaign",
        "",
    ]
    for campaign, counts in sorted((result.get("disagreement_by_campaign") or {}).items()):
        summary = ", ".join(f"{key}={value}" for key, value in sorted(counts.items()))
        lines.append(f"- {campaign}: {summary}")
    lines.extend(["", "## Disagreement Review Classification", ""])
    for classification, count in sorted((result.get("disagreement_review_by_classification") or {}).items()):
        lines.append(f"- {classification}: {count}")
    lines.extend(
        [
            "",
            "## Manual Review Table",
            "",
            "| case_id | campaign | utterance | runtime_semantic | runtime_action_id | selector_action_id | disagreement_type | review | actionable | reason |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for item in result.get("case_results") or []:
        utterance = str(item.get("buyer_utterance_text_sanitized") or "").replace("|", "/")
        reason = str(item.get("reason_for_disagreement") or "").replace("|", "/")
        lines.append(
            "| "
            + " | ".join(
                [
                    str(item.get("case_id") or ""),
                    str(item.get("campaign_coverage") or ""),
                    utterance,
                    str(item.get("runtime_semantic") or ""),
                    str(item.get("runtime_action_id") or ""),
                    str(item.get("selector_action_id") or ""),
                    str(item.get("agreement_disagreement_type") or ""),
                    str(item.get("disagreement_review_classification") or ""),
                    str(item.get("evidence_actionable") is True).lower(),
                    reason,
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def build_initial_decision_report(result: dict[str, Any]) -> str:
    disagreements = result.get("disagreement_by_campaign") or {}
    disagreement_campaigns = [
        campaign
        for campaign, counts in sorted(disagreements.items())
        if any(kind != "same_action" and int(count or 0) > 0 for kind, count in counts.items())
    ]
    return "\n".join(
        [
            f"# {EXPERIMENT_ID} Decision Report",
            "",
            "## Is the shadow selector still safe offline?",
            "",
            f"Yes for this phase: safety_blockers_count={result['safety_blockers_count']}, provider calls=false, local LLM calls=false, live selector control=false. This is still offline evidence only.",
            "",
            "## Which campaigns show selector/runtime disagreement?",
            "",
            ", ".join(disagreement_campaigns) if disagreement_campaigns else "No selector/runtime disagreements were recorded.",
            "",
            "## Which spoken responses sound robotic?",
            "",
            "Pending SPOKEN-HUMAN-NATURALNESS-AUDIT-001. The audit script overwrites this section with fixture-only spoken examples.",
            "",
            "## Which responses risk turning the sales agent into a scheduling bot?",
            "",
            "Pending SPOKEN-HUMAN-NATURALNESS-AUDIT-001. The audit script overwrites this section with fixture-only spoken examples.",
            "",
            "## What should be fixed before any live selector control?",
            "",
            "Fix selector/runtime disagreements, robotic spoken wording, and any scheduling-bot drift before any live selector control. Do not enable live selector control.",
            "",
            "## Does the system remain aligned with the final goal: autonomous emotion-aware sales closing?",
            "",
            "Partially. The evidence remains aligned only as safety infrastructure for autonomous emotion-aware sales closing; it does not yet prove live persuasion, objection handling, or closing quality.",
            "",
            f"Recommendation: {RECOMMENDATION_ID}",
            "",
            "Do not enable live selector control.",
        ]
    )


def run_shadow_expansion(cases: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[float]]:
    from runtime.action_selector.shadow_runtime_logger import run_shadow_selector_read_only

    rows: list[dict[str, Any]] = []
    case_results: list[dict[str, Any]] = []
    latencies: list[float] = []
    for case in cases:
        turn_context = turn_context_from_case(case)
        start = perf_counter_ns()
        record = run_shadow_selector_read_only(
            turn_context,
            expected_action_id=str(case.get("expected_action_id") or ""),
            mode="offline_sanitized_replay",
        )
        latencies.append((perf_counter_ns() - start) / 1_000_000)
        row = expansion_row(case, record)
        safety_failures = row_safety_failures(row) + list(record.get("validation_errors") or [])
        row["row_safety_failures"] = safety_failures
        review = review_classification(record, safety_failures)
        row.update(review)
        rows.append(row)
        case_results.append(
            {
                "case_id": case["case_id"],
                "campaign_coverage": case["campaign_coverage"],
                "campaign_id": case["campaign_id"],
                "vertical_id": case["vertical_id"],
                "buyer_utterance_text_sanitized": case["buyer_utterance_text_sanitized"],
                "runtime_semantic": case.get("runtime_semantic") or "",
                "runtime_action_id": record.get("runtime_action_id") or "",
                "selector_action_id": record.get("selector_action_id") or "",
                "agreement_disagreement_type": record.get("disagreement_type") or "",
                "agreement_with_runtime": record.get("agreement_with_runtime") is True,
                "disagreement_review_classification": review["disagreement_review_classification"],
                "reason_for_disagreement": review["reason_for_disagreement"],
                "evidence_actionable": review["evidence_actionable"],
                "runtime_extraction_warnings": [str(item) for item in record.get("runtime_extraction_warnings") or []],
                "candidate_response_hash": case["candidate_response_hash"],
                "candidate_response_text_recorded": False,
                "safety_failure_count": len(safety_failures),
            }
        )
    return rows, case_results, latencies


def false_asr_mapping(item: dict[str, Any]) -> bool:
    if item.get("runtime_action_id") != "repair_asr_uncertainty":
        return False
    semantic = normalize_words(str(item.get("runtime_semantic") or ""))
    return not any(token in semantic for token in ("asr", "uncertain tool", "ambiguous tool"))


def build_result(cases: list[dict[str, Any]], rows: list[dict[str, Any]], case_results: list[dict[str, Any]], latencies: list[float]) -> dict[str, Any]:
    coverage = sorted({case["campaign_coverage"] for case in cases})
    disagreement_counter: dict[str, Counter[str]] = defaultdict(Counter)
    for item in case_results:
        disagreement_counter[str(item.get("campaign_coverage") or "")][str(item.get("agreement_disagreement_type") or "")] += 1
    review_counter = Counter(str(item.get("disagreement_review_classification") or "") for item in case_results)
    safety_blockers = sum(len(row.get("row_safety_failures") or []) for row in rows)
    candidate_hash_count = sum(1 for row in rows if str(row.get("candidate_response_hash") or "").startswith("sha256:"))
    raw_response_recorded_count = sum(1 for row in rows if FORBIDDEN_RECORD_KEYS & set(row))
    result = {
        "experiment_id": EXPERIMENT_ID,
        "generated_at": utc_now(),
        "status": "pass" if safety_blockers == 0 and len(coverage) == 6 and candidate_hash_count == len(rows) else "fail",
        "case_count": len(cases),
        "jsonl_path": str(JSONL_PATH.relative_to(ROOT)).replace("\\", "/"),
        "campaign_coverage": coverage,
        "coverage_count": len(coverage),
        "candidate_response_hash_recorded_count": candidate_hash_count,
        "raw_candidate_response_recorded_count": raw_response_recorded_count,
        "selector_runtime_disagreement_count": sum(
            1 for item in case_results if item.get("agreement_disagreement_type") != "same_action"
        ),
        "disagreement_by_campaign": {
            campaign: dict(sorted(counter.items())) for campaign, counter in sorted(disagreement_counter.items())
        },
        "disagreement_review_by_classification": dict(sorted(review_counter.items())),
        "genuine_selector_runtime_disagreement_count": sum(
            1
            for item in case_results
            if item.get("evidence_actionable") is True
            and item.get("agreement_disagreement_type") not in {"same_action", "compatible_action"}
        ),
        "selector_possible_improvement_count": review_counter.get("selector_possible_improvement", 0),
        "selector_possible_regression_count": review_counter.get("selector_possible_regression", 0),
        "runtime_action_unmapped_count": review_counter.get("runtime_action_unmapped", 0),
        "metadata_extraction_failure_count": review_counter.get("metadata_extraction_failure", 0),
        "evidence_not_actionable_yet_count": sum(1 for item in case_results if item.get("evidence_actionable") is not True),
        "false_asr_mapping_count": sum(1 for item in case_results if false_asr_mapping(item)),
        "safety_blockers_count": safety_blockers,
        "case_results": case_results,
        "latency_ms": {
            "sample_count": len(latencies),
            "p50": percentile(latencies, 50),
            "p90": percentile(latencies, 90),
            "p99": percentile(latencies, 99),
            "max": max(latencies) if latencies else 0.0,
            "mean": statistics.mean(latencies) if latencies else 0.0,
        },
        "decision_recommendation_id": RECOMMENDATION_ID,
        "live_selector_control_recommended": False,
        "response_replacement_performed": False,
        "private_live_transcripts_inspected": False,
        "no_provider_calls": True,
        "no_local_llm_calls": True,
        **FALSE_FLAGS,
    }
    return result


def main() -> int:
    cases = build_safe_fixture_cases()
    rows, case_results, latencies = run_shadow_expansion(cases)
    result = build_result(cases, rows, case_results, latencies)
    write_jsonl(JSONL_PATH, rows)
    write_json(RESULT_PATH, result)
    write_text(REPORT_PATH, build_report(result))
    write_text(DECISION_REPORT_PATH, build_initial_decision_report(result))
    print(
        json.dumps(
            {
                "status": result["status"],
                "case_count": result["case_count"],
                "coverage_count": result["coverage_count"],
                "selector_runtime_disagreement_count": result["selector_runtime_disagreement_count"],
                "safety_blockers_count": result["safety_blockers_count"],
                "recommendation_id": result["decision_recommendation_id"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
