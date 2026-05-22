#!/usr/bin/env python3
from __future__ import annotations

import ast
import importlib
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


MODULE_KNOWLEDGE_ID = "UNIVERSAL-SALES-CONVERSATION-KNOWLEDGE-001"
CHECKPOINT_ID = "UNIVERSAL-SALES-CONVERSATION-KNOWLEDGE-001A"
GENERATED_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
RESULT_PATH = GENERATED_DIR / "result.json"
REPORT_PATH = GENERATED_DIR / "report.md"
MODULE_PATH = ROOT / "runtime" / "core" / "universal_sales_conversation_knowledge.py"

MIN_BUYER_MOVE_COUNT = 70
MIN_RESPONSE_SHAPE_COUNT = 39
MIN_REPAIR_RULE_COUNT = 60
MIN_ASR_CASE_COUNT = 19


REQUIRED_BUYER_MOVES = {
    "permission_acknowledgement",
    "time_constrained_permission",
    "pain_confirmed",
    "tentative_gap_interest",
    "no_pain_clear",
    "not_relevant",
    "product_detail_question",
    "scope_limit_question",
    "regulated_claim_question",
    "why_are_you_asking",
    "contradiction_challenge",
    "already_answered_challenge",
    "confusion_not_clear",
    "repeat_or_rephrase_request",
    "send_info_request",
    "callback_request",
    "callback_time_provided",
    "appointment_interest",
    "right_person_redirect",
    "support_request",
    "stop_request",
    "asr_garbled_or_low_confidence",
}
REQUIRED_OBJECTION_MOVES = {
    "price_or_budget_objection",
    "timing_objection",
    "no_authority_or_needs_approval",
    "already_has_provider",
    "competitor_comparison",
    "trust_or_skepticism",
    "risk_or_liability_concern",
    "no_clear_need",
    "too_busy_now",
    "send_info_first",
    "wants_proof_or_case_study",
    "procurement_or_legal_review",
    "security_or_privacy_review",
    "contract_or_terms_question",
}
REQUIRED_IDENTITY_TRUST_PRIVACY_MOVES = {
    "who_are_you",
    "how_did_you_get_my_number",
    "are_you_ai_or_robot",
    "is_this_recorded",
    "privacy_data_use_question",
    "permission_to_continue_denied",
    "language_mismatch",
    "abusive_or_hostile_buyer",
    "sensitive_personal_data_disclosure",
}
REQUIRED_APPOINTMENT_NEGOTIATION_MOVES = {
    "appointment_time_vague",
    "appointment_time_conflict",
    "buyer_requests_available_times",
    "buyer_wants_email_before_booking",
    "buyer_defers_to_later",
    "buyer_accepts_callback_without_time",
    "buyer_changes_time",
    "buyer_confirms_time",
    "buyer_declines_after_interest",
}
REQUIRED_VALUE_DIFFERENTIATION_MOVES = {
    "why_should_i_care",
    "what_makes_you_different",
    "what_problem_do_you_solve",
    "what_result_can_i_expect",
    "is_this_worth_my_time",
    "who_is_this_for",
    "does_this_apply_to_us",
}
REQUIRED_SOCIAL_CONVERSATION_MOVES = {
    "small_talk",
    "humor_or_sarcasm",
    "silence_or_backchannel",
    "interruption_or_barge_in",
    "buyer_talks_over_agent",
    "repeat_last_answer",
    "slow_down_or_speak_faster",
    "pronunciation_or_name_correction",
    "emotional_frustration",
}
REQUIRED_BUYER_MOVES |= (
    REQUIRED_OBJECTION_MOVES
    | REQUIRED_IDENTITY_TRUST_PRIVACY_MOVES
    | REQUIRED_APPOINTMENT_NEGOTIATION_MOVES
    | REQUIRED_VALUE_DIFFERENTIATION_MOVES
    | REQUIRED_SOCIAL_CONVERSATION_MOVES
)
REQUIRED_STAGES = {
    "opening",
    "permission",
    "diagnostic",
    "value_bridge",
    "scope_limit",
    "appointment_progression",
    "callback_capture",
    "send_info_capture",
    "handoff_right_person",
    "stop_close",
}
REQUIRED_RESPONSE_SHAPES = {
    "acknowledge_then_one_short_diagnostic",
    "acknowledge_time_constraint_then_one_question",
    "acknowledge_pain_bridge_to_appointment",
    "acknowledge_tentative_gap_offer_review_or_stop",
    "answer_product_scope_limit_continue",
    "regulated_claim_boundary_no_advice",
    "explain_why_asking_preserve_context",
    "contradiction_repair_clarify_role",
    "already_answered_preserve_gap",
    "confusion_explain_plainly",
    "ask_repeat_for_asr_garble",
    "send_info_contact_capture",
    "callback_time_capture",
    "right_person_capture",
    "support_boundary",
    "stop_close_politely",
}
REQUIRED_RESPONSE_SHAPES |= {
    "answer_identity_then_permission",
    "answer_data_source_boundary",
    "ai_disclosure_then_continue_or_stop",
    "privacy_boundary_then_continue_or_stop",
    "objection_acknowledge_answer_bridge",
    "competitor_acknowledge_no_bashing",
    "price_boundary_without_quote",
    "authority_map_to_right_person",
    "timing_deferral_callback_capture",
    "value_question_answer_with_allowed_facts",
    "proof_request_offer_summary_or_human_review",
    "appointment_time_clarification",
    "appointment_time_confirmation",
    "language_mismatch_repair",
    "hostile_buyer_deescalation",
    "speech_rate_adjustment",
    "repeat_last_answer_shorter",
    "social_smalltalk_bridge_back",
    "clarify_missing_time",
    "offer_callback_window_without_calendar_claim",
    "confirm_time_without_calendar_write",
    "defer_politely_preserve_interest",
    "close_after_decline",
}
REQUIRED_RESPONSE_STEPS = [
    "acknowledge buyer meaning",
    "answer direct question if asked",
    "use campaign facts only from allowed slots",
    "respect blocked claims and regulated cautions",
    "choose one next action",
]
REQUIRED_CALL_CONTROLS = {"continue-call", "schedule-and-end", "end-call", "transfer-or-escalate"}
REQUIRED_FACT_SLOTS = {
    "campaign_id",
    "client_name",
    "product_or_offer_name",
    "vertical_id",
    "objective",
    "caller_identity",
    "language",
    "human_followup_owner",
    "appointment_target",
    "allowed_claims",
    "blocked_claims",
    "regulated_cautions",
    "diagnostic_gaps",
    "core_diagnostic_gaps",
    "gap_order",
    "gap_label",
    "gap_definition",
    "gap_review_focus",
    "gap_customer_language",
    "gap_value_bridge",
}
REQUIRED_ASR_CASES = {
    "explicit_low_confidence",
    "empty_or_fragment",
    "phonetic_nonsense",
    "previous_question_mismatch",
    "domain_near_miss",
    "high_risk_appointment_time",
    "high_risk_email_or_contact",
    "high_risk_regulated_claim",
}
REQUIRED_ASR_CASES |= {
    "homophone_or_near_miss",
    "non_english_or_mixed_language",
    "transcript_contains_command_noise",
    "transcript_contains_browser_noise",
    "transcript_has_wrong_named_entity",
    "ambiguous_yes_after_unanswered_question",
    "ambiguous_positive_after_explanation",
    "ambiguous_negative_after_multi_choice",
    "possible_time_misrecognition",
    "possible_email_misrecognition",
    "possible_name_misrecognition",
}
KNOWN_GARBLED_PHRASES = {
    "play a double be good",
    "yadav would be good",
    "repeal timings are long",
    "repair timings misheard as repeal timings",
    "yeah that would be good misheard as unrelated phrase",
    "tomorrow at three misheard as unrelated phrase",
}
REQUIRED_FIXTURES = {
    "routesignal_live_demo",
    "synthetic-insurance-review",
    "synthetic-b2b-saas-operations",
    "synthetic-automotive-service-review",
    "synthetic-home-services-estimate",
}
REQUIRED_TEST_CASES = {
    "make it quick",
    "maybe X",
    "X is usually a problem",
    "what does your product do?",
    "so you can't give me details?",
    "why are you asking?",
    "you didn't answer my question",
    "if you're not the right person, why ask?",
    "I already told you",
    "yeah that would be good",
    "play a double be good",
    "yadav would be good",
    "repeal timings are long",
    "send me details",
    "tomorrow at 3 works",
    "no thanks",
    "stop calling",
}
REQUIRED_TEST_CASES |= {
    "who are you?",
    "are you a robot?",
    "how did you get my number?",
    "is this recorded?",
    "what do you do with my data?",
    "we already have a provider",
    "how much does it cost?",
    "send me proof",
    "I need to ask my manager",
    "call me next week",
    "can you send available times?",
    "what makes you different?",
    "why should I care?",
    "not interested",
    "slow down",
    "say that again",
    "I don't speak English well",
    "that's not how you say my name",
    "you keep asking the same thing",
}
REQUIRED_FORBIDDEN_PATTERN_IDS = {
    "internal_policy_wording",
    "late_diagnostic_menu_reopen",
    "conditional_relevance_after_pain",
    "contact_boundary_misuse",
    "default_demo_terms_in_generic_fixtures",
    "invented_claims",
    "human_impersonation",
    "external_action_claims",
    "unsupported_result_claims",
    "argument_or_blame",
    "model_or_internal_terms",
    "looping_apology_or_diagnostic",
    "pressure_after_no",
    "sensitive_data_collection",
}
LEAKAGE_TERMS = [
    "RouteSignal",
    "Northstar",
    "Starter",
    "Growth",
    "$29",
    "$59",
    "demo lead",
    "inbound demo",
    "workflow review with Northstar",
    "Synthetic Insurance Agency",
    "Synthetic Automotive Service",
    "Synthetic SaaS Operations",
    "Synthetic Home Services",
]
SIDE_EFFECT_FLAGS = [
    "provider_calls_made",
    "live_tts_used",
    "local_llm_calls_made",
    "sends_email",
    "creates_calendar_event",
    "writes_crm",
    "opens_prod_102",
    "real_customer_data_used",
    "private_transcript_content_copied",
]


def assert_condition(failures: list[str], condition: bool, message: str) -> None:
    if not condition:
        failures.append(message)


def sanitize(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): sanitize(item) for key, item in value.items()}
    if isinstance(value, list):
        return [sanitize(item) for item in value]
    if isinstance(value, set):
        return sorted(str(item) for item in value)
    return value


def write_evidence(result: dict[str, Any], report: str) -> None:
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(sanitize(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    REPORT_PATH.write_text(report, encoding="utf-8")


def collect_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        strings: list[str] = []
        for key, item in value.items():
            strings.extend(collect_strings(key))
            strings.extend(collect_strings(item))
        return strings
    if isinstance(value, (list, tuple, set)):
        strings = []
        for item in value:
            strings.extend(collect_strings(item))
        return strings
    return []


def normalized_set(values: Any) -> set[str]:
    return {str(value) for value in list(values or [])}


def check_required_ids(failures: list[str], evidence: dict[str, Any], uk: Any) -> None:
    buyer_moves = set(uk.all_buyer_move_ids())
    stages = set(uk.all_conversation_stage_ids())
    shapes = set(uk.all_response_shape_ids())
    matrix = uk.validator_matrix()
    fixtures = set(matrix.get("fixtures") or [])
    test_cases = set(matrix.get("buyer_move_test_cases") or [])

    call_controls = {str(rule.get("id")) for rule in (uk.CALL_CONTROL_POLICY or {}).values()}
    fact_slots = {str(slot.get("id")) for slot in (uk.CAMPAIGN_FACT_SLOTS or {}).values()}
    asr_cases = {str(case.get("id")) for case in (uk.ASR_REPAIR_BOUNDARY or {}).get("cases", {}).values()}
    repair_rules = set((uk.UNIVERSAL_REPAIR_RULES or {}).keys())
    forbidden_pattern_ids = {str(pattern.get("id")) for pattern in (uk.FORBIDDEN_CUSTOMER_FACING_PATTERNS or [])}

    evidence["id_counts"] = {
        "buyer_moves": len(buyer_moves),
        "conversation_stages": len(stages),
        "response_shapes": len(shapes),
        "call_controls": len(call_controls),
        "campaign_fact_slots": len(fact_slots),
        "asr_cases": len(asr_cases),
        "repair_rules": len(repair_rules),
        "forbidden_customer_patterns": len(forbidden_pattern_ids),
    }
    assert_condition(failures, REQUIRED_BUYER_MOVES <= buyer_moves, f"missing buyer moves: {sorted(REQUIRED_BUYER_MOVES - buyer_moves)}")
    assert_condition(failures, REQUIRED_STAGES <= stages, f"missing stages: {sorted(REQUIRED_STAGES - stages)}")
    assert_condition(failures, REQUIRED_RESPONSE_SHAPES <= shapes, f"missing response shapes: {sorted(REQUIRED_RESPONSE_SHAPES - shapes)}")
    assert_condition(failures, REQUIRED_CALL_CONTROLS <= call_controls, f"missing call controls: {sorted(REQUIRED_CALL_CONTROLS - call_controls)}")
    assert_condition(failures, REQUIRED_FACT_SLOTS <= fact_slots, f"missing campaign fact slots: {sorted(REQUIRED_FACT_SLOTS - fact_slots)}")
    assert_condition(failures, REQUIRED_ASR_CASES <= asr_cases, f"missing ASR cases: {sorted(REQUIRED_ASR_CASES - asr_cases)}")
    assert_condition(failures, REQUIRED_FIXTURES <= fixtures, f"missing validator fixtures: {sorted(REQUIRED_FIXTURES - fixtures)}")
    assert_condition(failures, REQUIRED_TEST_CASES <= test_cases, f"missing validator test cases: {sorted(REQUIRED_TEST_CASES - test_cases)}")
    assert_condition(failures, REQUIRED_FORBIDDEN_PATTERN_IDS <= forbidden_pattern_ids, f"missing forbidden pattern ids: {sorted(REQUIRED_FORBIDDEN_PATTERN_IDS - forbidden_pattern_ids)}")


def check_material_widening(failures: list[str], evidence: dict[str, Any], uk: Any) -> None:
    buyer_moves = set(uk.all_buyer_move_ids())
    shapes = set(uk.all_response_shape_ids())
    repair_rules = uk.UNIVERSAL_REPAIR_RULES or {}
    asr_cases = (uk.ASR_REPAIR_BOUNDARY or {}).get("cases", {}) or {}
    category_counts = {
        "objections": len(REQUIRED_OBJECTION_MOVES & buyer_moves),
        "identity_trust_privacy": len(REQUIRED_IDENTITY_TRUST_PRIVACY_MOVES & buyer_moves),
        "appointment_negotiation": len(REQUIRED_APPOINTMENT_NEGOTIATION_MOVES & buyer_moves),
        "value_differentiation": len(REQUIRED_VALUE_DIFFERENTIATION_MOVES & buyer_moves),
        "social_conversation": len(REQUIRED_SOCIAL_CONVERSATION_MOVES & buyer_moves),
    }
    evidence["material_widening"] = {
        "minimums": {
            "buyer_moves": MIN_BUYER_MOVE_COUNT,
            "response_shapes": MIN_RESPONSE_SHAPE_COUNT,
            "repair_rules": MIN_REPAIR_RULE_COUNT,
            "asr_cases": MIN_ASR_CASE_COUNT,
        },
        "actual": {
            "buyer_moves": len(buyer_moves),
            "response_shapes": len(shapes),
            "repair_rules": len(repair_rules),
            "asr_cases": len(asr_cases),
        },
        "category_counts": category_counts,
    }
    assert_condition(failures, len(buyer_moves) >= MIN_BUYER_MOVE_COUNT, f"buyer move count did not widen materially: {len(buyer_moves)}")
    assert_condition(failures, len(shapes) >= MIN_RESPONSE_SHAPE_COUNT, f"response shape count did not widen materially: {len(shapes)}")
    assert_condition(failures, len(repair_rules) >= MIN_REPAIR_RULE_COUNT, f"repair rule count did not widen materially: {len(repair_rules)}")
    assert_condition(failures, len(asr_cases) >= MIN_ASR_CASE_COUNT, f"ASR case count did not widen materially: {len(asr_cases)}")
    assert_condition(failures, REQUIRED_OBJECTION_MOVES <= buyer_moves, "objection buyer moves missing")
    assert_condition(failures, REQUIRED_IDENTITY_TRUST_PRIVACY_MOVES <= buyer_moves, "identity/trust/privacy buyer moves missing")
    assert_condition(failures, REQUIRED_APPOINTMENT_NEGOTIATION_MOVES <= buyer_moves, "appointment negotiation buyer moves missing")
    assert_condition(failures, REQUIRED_VALUE_DIFFERENTIATION_MOVES <= buyer_moves, "value/differentiation buyer moves missing")
    assert_condition(failures, REQUIRED_SOCIAL_CONVERSATION_MOVES <= buyer_moves, "social/conversation-management buyer moves missing")


def check_no_leakage(failures: list[str], evidence: dict[str, Any], uk: Any) -> None:
    sections = {
        "buyer_moves": uk.BUYER_MOVE_TAXONOMY,
        "stages": uk.CONVERSATION_STAGE_POLICY,
        "response_shapes": uk.RESPONSE_SHAPE_LIBRARY,
        "repair_rules": uk.UNIVERSAL_REPAIR_RULES,
        "call_control_policy": uk.CALL_CONTROL_POLICY,
        "asr_repair_boundary": uk.ASR_REPAIR_BOUNDARY,
        "campaign_fact_slots": uk.CAMPAIGN_FACT_SLOTS,
        "forbidden_customer_patterns": uk.FORBIDDEN_CUSTOMER_FACING_PATTERNS,
    }
    leaks: dict[str, list[str]] = {}
    for section, value in sections.items():
        text = "\n".join(collect_strings(value))
        found = [term for term in LEAKAGE_TERMS if term.lower() in text.lower()]
        if found:
            leaks[section] = found
    evidence["leakage_scan"] = {"leaks": leaks, "validator_matrix_fixture_exception_applied": True}
    assert_condition(failures, not leaks, f"campaign-specific leakage found outside validator matrix: {leaks}")


def check_response_shapes(failures: list[str], evidence: dict[str, Any], uk: Any) -> None:
    bad_shapes: dict[str, list[str]] = {}
    for shape_id in uk.all_response_shape_ids():
        shape = uk.response_shape(shape_id)
        missing = [step for step in REQUIRED_RESPONSE_STEPS if step not in list(shape.get("required_steps") or [])]
        if missing:
            bad_shapes[shape_id] = missing
        assert_condition(failures, bool(shape.get("allowed_fact_slots")), f"{shape_id}: allowed_fact_slots must be non-empty")
        assert_condition(failures, bool(shape.get("forbidden_patterns")), f"{shape_id}: forbidden_patterns must be non-empty")
        assert_condition(failures, str(shape.get("appointment_pressure_level")) in {"none", "low", "medium", "direct"}, f"{shape_id}: invalid appointment_pressure_level")
        assert_condition(failures, "final_response" not in shape, f"{shape_id}: response shape must not contain final_response")
    evidence["response_shape_required_step_failures"] = bad_shapes
    assert_condition(failures, not bad_shapes, f"response shapes missing required steps: {bad_shapes}")


def check_buyer_moves(failures: list[str], evidence: dict[str, Any], uk: Any) -> None:
    failures_by_move: dict[str, list[str]] = {}
    for move_id in uk.all_buyer_move_ids():
        move = uk.buyer_move(move_id)
        missing: list[str] = []
        for key in [
            "id",
            "description",
            "examples",
            "expected_response_shape_id",
            "allowed_stages",
            "default_call_control_allowed",
            "memory_policy",
            "must_acknowledge",
            "must_answer_direct_question",
            "must_not_do",
        ]:
            if key not in move:
                missing.append(key)
        if move.get("expected_response_shape_id") not in uk.all_response_shape_ids():
            missing.append("expected_response_shape_id references unknown shape")
        if missing:
            failures_by_move[move_id] = missing
    evidence["buyer_move_contract_failures"] = failures_by_move
    assert_condition(failures, not failures_by_move, f"buyer move contract failures: {failures_by_move}")


def check_stage_policy(failures: list[str], evidence: dict[str, Any], uk: Any) -> None:
    failures_by_stage: dict[str, list[str]] = {}
    buyer_move_ids = set(uk.all_buyer_move_ids())
    for stage_id in uk.all_conversation_stage_ids():
        stage = uk.conversation_stage(stage_id)
        missing: list[str] = []
        for key in ["id", "purpose", "allowed_buyer_moves", "preferred_next_actions", "unsafe_next_actions", "allowed_call_control"]:
            if key not in stage:
                missing.append(key)
        unknown_moves = normalized_set(stage.get("allowed_buyer_moves")) - buyer_move_ids
        if unknown_moves:
            missing.append(f"unknown allowed_buyer_moves: {sorted(unknown_moves)}")
        if missing:
            failures_by_stage[stage_id] = missing
    evidence["stage_policy_failures"] = failures_by_stage
    assert_condition(failures, not failures_by_stage, f"stage policy failures: {failures_by_stage}")


def check_repair_rules(failures: list[str], evidence: dict[str, Any], uk: Any) -> None:
    required_rule_ids = {
        "why_are_you_asking_rule",
        "did_not_answer_rule",
        "not_right_contact_why_ask_rule",
        "already_told_you_rule",
        "tentative_gap_rule",
        "time_pressure_rule",
        "clean_confirmation_rule",
        "asr_garbled_phrase_rule",
        "product_detail_question_rule",
        "regulated_claim_question_rule",
        "support_request_rule",
        "stop_request_rule",
    }
    required_rule_ids |= {
        f"{move_id}_rule"
        for move_id in (
            REQUIRED_OBJECTION_MOVES
            | REQUIRED_IDENTITY_TRUST_PRIVACY_MOVES
            | REQUIRED_APPOINTMENT_NEGOTIATION_MOVES
            | REQUIRED_VALUE_DIFFERENTIATION_MOVES
            | REQUIRED_SOCIAL_CONVERSATION_MOVES
        )
    }
    rules = uk.UNIVERSAL_REPAIR_RULES
    missing_rules = sorted(required_rule_ids - set(rules))
    assert_condition(failures, not missing_rules, f"missing repair rules: {missing_rules}")
    covered_expanded_moves = {str(rule.get("buyer_move_id")) for rule in rules.values()}
    required_expanded_moves = (
        REQUIRED_OBJECTION_MOVES
        | REQUIRED_IDENTITY_TRUST_PRIVACY_MOVES
        | REQUIRED_APPOINTMENT_NEGOTIATION_MOVES
        | REQUIRED_VALUE_DIFFERENTIATION_MOVES
        | REQUIRED_SOCIAL_CONVERSATION_MOVES
    )
    uncovered_expanded_moves = sorted(required_expanded_moves - covered_expanded_moves)
    rule_failures: dict[str, list[str]] = {}
    for rule_id, rule in rules.items():
        missing: list[str] = []
        for key in [
            "buyer_move_id",
            "recognition_notes",
            "response_shape_id",
            "memory_policy",
            "call_control_constraints",
            "forbidden_response_patterns",
            "campaign_fact_slots_allowed",
        ]:
            if key not in rule:
                missing.append(key)
        if rule.get("buyer_move_id") not in uk.all_buyer_move_ids():
            missing.append("unknown buyer_move_id")
        if rule.get("response_shape_id") not in uk.all_response_shape_ids():
            missing.append("unknown response_shape_id")
        if missing:
            rule_failures[str(rule_id)] = missing
    evidence["repair_rule_failures"] = rule_failures
    evidence["repair_rule_coverage"] = {
        "required_rule_count": len(required_rule_ids),
        "actual_rule_count": len(rules),
        "uncovered_expanded_moves": uncovered_expanded_moves,
    }
    assert_condition(failures, not uncovered_expanded_moves, f"expanded buyer moves missing repair coverage: {uncovered_expanded_moves}")
    assert_condition(failures, not rule_failures, f"repair rule failures: {rule_failures}")


def check_call_control(failures: list[str], evidence: dict[str, Any], uk: Any) -> None:
    ordinary = uk.call_control_rule("ordinary_uncertainty")
    product = uk.call_control_rule("product_detail_limitation")
    asr = uk.call_control_rule("asr_garble")
    callback = uk.call_control_rule("valid_callback_or_appointment_time")
    stop = uk.call_control_rule("stop_or_refusal")
    transfer = uk.call_control_rule("transfer_or_escalate")
    evidence["call_control_checks"] = {
        "ordinary_uncertainty": ordinary,
        "product_detail_limitation": product,
        "asr_garble": asr,
        "valid_callback_or_appointment_time": callback,
        "stop_or_refusal": stop,
        "transfer_or_escalate": transfer,
    }
    assert_condition(failures, "transfer-or-escalate" in ordinary.get("forbidden_call_control", []), "ordinary uncertainty must forbid transfer-or-escalate")
    assert_condition(failures, "transfer-or-escalate" in product.get("forbidden_call_control", []), "product detail limitation must forbid transfer-or-escalate")
    assert_condition(failures, "transfer-or-escalate" in asr.get("forbidden_call_control", []), "ASR garble must forbid transfer-or-escalate")
    assert_condition(failures, "schedule-and-end" in callback.get("allowed_call_control", []), "valid appointment/callback time must allow schedule-and-end")
    assert_condition(failures, "end-call" in stop.get("allowed_call_control", []), "stop/refusal must allow end-call")
    assert_condition(
        failures,
        {"explicit_transfer_request", "configured_escalation_trigger", "true_regulated_escalation_requirement"} <= set(transfer.get("allowed_only_when") or []),
        "transfer-or-escalate must be limited to explicit/configured/true regulated escalation triggers",
    )


def check_asr_boundary(failures: list[str], evidence: dict[str, Any], uk: Any) -> None:
    boundary = uk.ASR_REPAIR_BOUNDARY
    text = "\n".join(collect_strings(boundary))
    missing_phrases = sorted(phrase for phrase in KNOWN_GARBLED_PHRASES if phrase not in text)
    policy = boundary.get("expected_policy") or {}
    evidence["asr_boundary_checks"] = {
        "missing_known_phrases": missing_phrases,
        "expected_policy": policy,
    }
    assert_condition(failures, not missing_phrases, f"ASR boundary missing known garbled phrases: {missing_phrases}")
    assert_condition(failures, "ask for repeat/rephrase" in policy.get("required_behavior", []), "ASR boundary must ask for repeat/rephrase")
    for forbidden in ["infer pain", "capture appointment", "repeat diagnostic menu"]:
        assert_condition(failures, forbidden in policy.get("forbidden_behavior", []), f"ASR boundary must forbid {forbidden}")


def check_fact_boundaries(failures: list[str], evidence: dict[str, Any], uk: Any) -> None:
    slots = uk.CAMPAIGN_FACT_SLOTS
    forbidden = uk.FORBIDDEN_CAMPAIGN_RESPONSIBILITIES
    text = "\n".join(collect_strings(forbidden))
    evidence["campaign_fact_boundary"] = {
        "slot_count": len(slots),
        "forbidden_responsibility_count": len(forbidden),
    }
    for slot_id in REQUIRED_FACT_SLOTS:
        slot = uk.campaign_fact_slot(slot_id)
        assert_condition(failures, slot.get("id") == slot_id, f"campaign fact slot lookup failed for {slot_id}")
    for phrase in [
        "generic acknowledgement strategy",
        "why-are-you-asking repair strategy",
        "product-detail limitation response shape",
        "loop repair strategy",
        "ASR-garble handling",
        "appointment progression policy",
        "transfer/escalate policy except explicit configured escalation triggers",
    ]:
        assert_condition(failures, phrase in text, f"forbidden campaign responsibility missing: {phrase}")


def check_forbidden_patterns(failures: list[str], evidence: dict[str, Any], uk: Any) -> None:
    patterns = uk.FORBIDDEN_CUSTOMER_FACING_PATTERNS or []
    ids = {str(pattern.get("id")) for pattern in patterns}
    text = "\n".join(collect_strings(patterns)).lower()
    required_phrases = [
        "pretending to be human",
        "claiming real calendar/email/crm action occurred",
        "claiming product results without allowed claims",
        "arguing with buyer",
        "blaming asr or the buyer",
        "as an ai language model",
        "using internal implementation terms",
        "over-apologizing in a loop",
        "asking the same diagnostic after direct answer",
        "pushing appointment after explicit no",
        "collecting unnecessary sensitive data",
    ]
    missing_ids = sorted(REQUIRED_FORBIDDEN_PATTERN_IDS - ids)
    missing_phrases = sorted(phrase for phrase in required_phrases if phrase not in text)
    evidence["expanded_forbidden_patterns"] = {
        "pattern_count": len(patterns),
        "missing_ids": missing_ids,
        "missing_phrases": missing_phrases,
    }
    assert_condition(failures, not missing_ids, f"expanded forbidden pattern ids missing: {missing_ids}")
    assert_condition(failures, not missing_phrases, f"expanded forbidden phrases missing: {missing_phrases}")


def check_declarative_boundaries(failures: list[str], evidence: dict[str, Any]) -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imported_modules.add(node.module)
    forbidden_imports = {
        "runtime.core.dialogue_manager",
        "runtime.core.contextual_buyer_semantics",
        "runtime.core.live_voice_session_policy",
        "dialogue_manager",
        "contextual_buyer_semantics",
        "live_voice_session_policy",
    }
    forbidden_generation_names = {"final_response", "build_turn_packet", "build_browser_demo_turn_packet"}
    imported_forbidden = sorted(module for module in imported_modules if module in forbidden_imports)
    generation_mentions = sorted(name for name in forbidden_generation_names if re.search(rf"\b{name}\b", source))
    evidence["declarative_boundary_scan"] = {
        "imported_modules": sorted(imported_modules),
        "forbidden_imports": imported_forbidden,
        "runtime_response_generation_mentions": generation_mentions,
    }
    assert_condition(failures, not imported_forbidden, f"module imports runtime routing components: {imported_forbidden}")
    assert_condition(failures, not generation_mentions, f"module appears to generate runtime responses: {generation_mentions}")


def check_module_validation(failures: list[str], evidence: dict[str, Any], uk: Any) -> None:
    validation = uk.validate_universal_sales_conversation_knowledge()
    evidence["module_validation"] = validation
    assert_condition(failures, validation.get("status") == "pass", f"module self-validation failed: {validation}")
    for key in SIDE_EFFECT_FLAGS:
        assert_condition(failures, validation.get(key) is False, f"module validation side-effect flag {key} must be false")


def build_report(result: dict[str, Any]) -> str:
    failures = result.get("failures") or []
    return "\n".join(
        [
            f"# {CHECKPOINT_ID}",
            "",
            f"Status: {'pass' if not failures else 'fail'}",
            f"Failure count: {len(failures)}",
            "",
            "## Checks",
            "",
            "- Module import and identity",
            "- Required buyer moves, stages, response shapes, call controls, fact slots, ASR cases, and expanded 4E1A categories",
            "- Material widening thresholds for buyer moves, response shapes, repair rules, and ASR repair cases",
            "- Campaign-specific leakage outside the fixture matrix",
            "- Response-shape required steps",
            "- Call-control constraints",
            "- ASR repair boundary",
            "- Campaign fact slot responsibilities",
            "- Expanded forbidden customer-facing patterns",
            "- Declarative-only import and runtime response-generation boundaries",
            "- Side-effect flags",
            "",
            "## Counts",
            "",
            json.dumps((result.get("evidence") or {}).get("id_counts") or {}, indent=2, sort_keys=True),
            "",
            "## Failures",
            "",
            *(f"- {failure}" for failure in failures),
            "" if failures else "- None",
            "",
            "## Side Effects",
            "",
            json.dumps(result.get("side_effects") or {}, indent=2, sort_keys=True),
            "",
        ]
    )


def main() -> int:
    failures: list[str] = []
    evidence: dict[str, Any] = {
        "checkpoint_id": CHECKPOINT_ID,
        "module_path": str(MODULE_PATH.relative_to(ROOT)),
    }
    side_effects = {key: False for key in SIDE_EFFECT_FLAGS}

    assert_condition(failures, MODULE_PATH.is_file(), f"module missing: {MODULE_PATH.relative_to(ROOT)}")
    try:
        uk = importlib.import_module("runtime.core.universal_sales_conversation_knowledge")
    except Exception as exc:
        uk = None
        evidence["import_error"] = repr(exc)
        failures.append(f"module import failed: {exc!r}")

    if uk is not None:
        evidence["identity"] = {
            "knowledge_id": getattr(uk, "KNOWLEDGE_ID", None),
            "schema_version": getattr(uk, "SCHEMA_VERSION", None),
        }
        assert_condition(failures, uk.KNOWLEDGE_ID == MODULE_KNOWLEDGE_ID, "unexpected KNOWLEDGE_ID")
        assert_condition(failures, uk.SCHEMA_VERSION == 1, "unexpected SCHEMA_VERSION")

        check_required_ids(failures, evidence, uk)
        check_material_widening(failures, evidence, uk)
        check_no_leakage(failures, evidence, uk)
        check_response_shapes(failures, evidence, uk)
        check_buyer_moves(failures, evidence, uk)
        check_stage_policy(failures, evidence, uk)
        check_repair_rules(failures, evidence, uk)
        check_call_control(failures, evidence, uk)
        check_asr_boundary(failures, evidence, uk)
        check_fact_boundaries(failures, evidence, uk)
        check_forbidden_patterns(failures, evidence, uk)
        check_declarative_boundaries(failures, evidence)
        check_module_validation(failures, evidence, uk)

    result = {
        "checkpoint_id": CHECKPOINT_ID,
        "status": "pass" if not failures else "fail",
        "failures": failures,
        "evidence": evidence,
        "side_effects": side_effects,
        **side_effects,
    }
    write_evidence(result, build_report(result))
    if failures:
        print(json.dumps(result, indent=2, sort_keys=True))
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
