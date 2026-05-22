#!/usr/bin/env python3
from __future__ import annotations

import importlib
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


CHECKPOINT_ID = "UNIVERSAL-SALES-CONVERSATION-KNOWLEDGE-001"
GENERATED_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
RESULT_PATH = GENERATED_DIR / "result.json"
REPORT_PATH = GENERATED_DIR / "report.md"
MODULE_PATH = ROOT / "runtime" / "core" / "universal_sales_conversation_knowledge.py"


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
KNOWN_GARBLED_PHRASES = {
    "play a double be good",
    "yadav would be good",
    "repeal timings are long",
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

    evidence["id_counts"] = {
        "buyer_moves": len(buyer_moves),
        "conversation_stages": len(stages),
        "response_shapes": len(shapes),
        "call_controls": len(call_controls),
        "campaign_fact_slots": len(fact_slots),
        "asr_cases": len(asr_cases),
    }
    assert_condition(failures, REQUIRED_BUYER_MOVES <= buyer_moves, f"missing buyer moves: {sorted(REQUIRED_BUYER_MOVES - buyer_moves)}")
    assert_condition(failures, REQUIRED_STAGES <= stages, f"missing stages: {sorted(REQUIRED_STAGES - stages)}")
    assert_condition(failures, REQUIRED_RESPONSE_SHAPES <= shapes, f"missing response shapes: {sorted(REQUIRED_RESPONSE_SHAPES - shapes)}")
    assert_condition(failures, REQUIRED_CALL_CONTROLS <= call_controls, f"missing call controls: {sorted(REQUIRED_CALL_CONTROLS - call_controls)}")
    assert_condition(failures, REQUIRED_FACT_SLOTS <= fact_slots, f"missing campaign fact slots: {sorted(REQUIRED_FACT_SLOTS - fact_slots)}")
    assert_condition(failures, REQUIRED_ASR_CASES <= asr_cases, f"missing ASR cases: {sorted(REQUIRED_ASR_CASES - asr_cases)}")
    assert_condition(failures, REQUIRED_FIXTURES <= fixtures, f"missing validator fixtures: {sorted(REQUIRED_FIXTURES - fixtures)}")
    assert_condition(failures, REQUIRED_TEST_CASES <= test_cases, f"missing validator test cases: {sorted(REQUIRED_TEST_CASES - test_cases)}")


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
    rules = uk.UNIVERSAL_REPAIR_RULES
    missing_rules = sorted(required_rule_ids - set(rules))
    assert_condition(failures, not missing_rules, f"missing repair rules: {missing_rules}")
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
            "- Required buyer moves, stages, response shapes, call controls, fact slots, and ASR cases",
            "- Campaign-specific leakage outside the fixture matrix",
            "- Response-shape required steps",
            "- Call-control constraints",
            "- ASR repair boundary",
            "- Campaign fact slot responsibilities",
            "- Side-effect flags",
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
        assert_condition(failures, uk.KNOWLEDGE_ID == CHECKPOINT_ID, "unexpected KNOWLEDGE_ID")
        assert_condition(failures, uk.SCHEMA_VERSION == 1, "unexpected SCHEMA_VERSION")

        check_required_ids(failures, evidence, uk)
        check_no_leakage(failures, evidence, uk)
        check_response_shapes(failures, evidence, uk)
        check_buyer_moves(failures, evidence, uk)
        check_stage_policy(failures, evidence, uk)
        check_repair_rules(failures, evidence, uk)
        check_call_control(failures, evidence, uk)
        check_asr_boundary(failures, evidence, uk)
        check_fact_boundaries(failures, evidence, uk)
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
