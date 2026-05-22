#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.validate_human_review_findings_001 import (  # noqa: E402
    DEFAULT_CAMPAIGN_ID,
    GENERIC_FORBIDDEN_CONCEPTS,
    RAW_EMAILS,
    SAFETY_KEYS,
    assert_condition,
    assert_generic_common,
    assert_no_side_effects,
    contains_any,
    final_response,
    memory,
    normalize,
    provider_rendered_text,
    run_generic_sequence,
    run_routesignal_sequence,
    sanitize,
    selected_action,
    semantic_frame,
    snapshot,
    text_sources,
    tts_input_text,
)
from scripts.validate_generic_campaign_runtime_regression_001 import synthetic_campaigns  # noqa: E402


CHECKPOINT_ID = "HUMAN-SEMANTIC-DELTA-FINDINGS-002"
GENERATED_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
RESULT_PATH = GENERATED_DIR / "result.json"
REPORT_PATH = GENERATED_DIR / "report.md"

NEXT_STEP_CASES = {
    "insurance": ("premium is a problem", "premium_or_budget"),
    "telecom": ("coverage is the issue", "coverage_or_availability"),
    "healthcare_admin_or_medical_equipment": ("specialist review is needed", "specialist_review_needed"),
    "retail_or_ecommerce_support_sales": ("return policy is the concern", "return_or_warranty"),
    "membership_or_subscription": ("renewal is the issue", "renewal_or_cancellation"),
    "automotive_service": ("warranty estimate is the problem", "warranty_or_estimate"),
}
SUPPORT_BOUNDARY_CASES = {
    "insurance": "can you handle my claim?",
    "telecom": "can you change my plan?",
    "automotive_service": "can you check my warranty?",
    "retail_or_ecommerce_support_sales": "can you help with my order?",
    "membership_or_subscription": "can you cancel my account?",
}
UNCERTAINTY_CASES = {
    "b2b_saas": ["__agent_open__", "yeah sure", "maybe", "not sure"],
    "insurance": ["__agent_open__", "yeah sure", "maybe", "not sure"],
    "automotive_service": ["__agent_open__", "yeah sure", "I do not understand", "what is this about?", "maybe", "not sure"],
}
CONFUSION_CASES = {
    "b2b_saas": ["__agent_open__", "yeah sure", "I don't understand", "what do you mean?"],
    "insurance": ["__agent_open__", "yeah sure", "I don't understand", "what are you asking?"],
    "automotive_service": ["__agent_open__", "yeah sure", "I do not understand", "what is this about?"],
}
PAIN_CASES = {
    "b2b_saas": ("visibility is the problem", "visibility_gap"),
    "insurance": ("premium is a problem", "premium_or_budget"),
    "telecom": ("coverage is the issue", "coverage_or_availability"),
    "home_services": ("estimate is unclear", "estimate_or_property_details"),
    "healthcare_admin_or_medical_equipment": ("specialist review is needed", "specialist_review_needed"),
    "automotive_service": ("warranty estimate is the problem", "warranty_or_estimate"),
    "membership_or_subscription": ("renewal is the issue", "renewal_or_cancellation"),
    "retail_or_ecommerce_support_sales": ("return policy is the concern", "return_or_warranty"),
}
CALLBACK_CASES = ["insurance", "b2b_saas", "telecom"]
NEXT_STEP_SEMANTICS = {
    "next_step_question_after_confirmed_pain",
    "appointment_next_step_question",
    "process_question_after_confirmed_pain",
}
UNCERTAINTY_SEMANTICS = {"uncertainty_after_diagnostic", "possible_pain_unclear", "tentative_continue"}
SUPPORT_BOUNDARY_SEMANTICS = {"account_support_boundary", "vertical_support_boundary", "support_boundary"}
INITIAL_RED_REPLAY_FAILURE_COUNT = 55


def semantic(packet: dict[str, Any]) -> str:
    return str(semantic_frame(packet).get("semantic") or selected_action(packet).get("semantic") or "")


def text_blob(packet: dict[str, Any]) -> str:
    return "\n".join(text for text in text_sources(packet).values() if text)


def confirmed_gaps(packet: dict[str, Any]) -> list[str]:
    mem = memory(packet)
    frame = semantic_frame(packet)
    value = mem.get("confirmed_gaps") or frame.get("confirmed_gaps") or []
    return [str(item) for item in value]


def cleared_gaps(packet: dict[str, Any]) -> list[str]:
    mem = memory(packet)
    frame = semantic_frame(packet)
    value = mem.get("cleared_gaps") or frame.get("cleared_gaps") or []
    return [str(item) for item in value]


def assert_no_generic_leakage(failures: list[str], packet: dict[str, Any], label: str) -> None:
    for source_name, text in text_sources(packet).items():
        matches = contains_any(text, GENERIC_FORBIDDEN_CONCEPTS)
        assert_condition(
            failures,
            not matches,
            f"{label}: {source_name} leaked forbidden RouteSignal concept {matches}: {snapshot(packet)}",
        )


def assert_no_raw_emails_in_result(result: dict[str, Any]) -> None:
    serialized = json.dumps(result, sort_keys=True).lower()
    leaked = [raw for raw in RAW_EMAILS if raw.lower() in serialized]
    if leaked:
        raise AssertionError(f"raw synthetic emails leaked in public evidence: {leaked}")


def campaign_review_text(campaign: dict[str, Any], gap_id: str) -> list[str]:
    gap = (campaign.get("diagnostic_gaps") or {}).get(gap_id) or {}
    return [
        normalize(campaign.get("appointment_target") or ""),
        normalize(campaign.get("human_followup_owner") or ""),
        normalize(gap.get("review_focus") or ""),
        normalize(gap.get("label") or ""),
    ]


def validate_next_step_after_confirmed_pain(failures: list[str], evidence: dict[str, Any], campaigns: dict[str, dict[str, Any]]) -> None:
    evidence["next_step_after_confirmed_pain"] = {}
    for vertical, (pain_phrase, gap_id) in NEXT_STEP_CASES.items():
        packets = run_generic_sequence(
            f"delta-findings-next-step-{vertical}",
            campaigns[vertical],
            ["__agent_open__", "yeah sure", pain_phrase, "what happens next?"],
        )
        evidence["next_step_after_confirmed_pain"][vertical] = [snapshot(packet) for packet in packets]
        assert_generic_common(failures, packets, f"next_step_{vertical}")
        final = packets[-1]
        text = normalize(text_blob(final))
        sem = semantic(final)
        review_terms = [term for term in campaign_review_text(campaigns[vertical], gap_id) if term]
        assert_condition(failures, sem in NEXT_STEP_SEMANTICS, f"next_step_{vertical}: wrong semantic {sem}: {snapshot(final)}")
        assert_condition(failures, gap_id in confirmed_gaps(final), f"next_step_{vertical}: confirmed gap was not preserved: {snapshot(final)}")
        assert_condition(
            failures,
            any(term in text for term in review_terms),
            f"next_step_{vertical}: response did not mention confirmed focus/owner/target {review_terms}: {snapshot(final)}",
        )
        assert_condition(
            failures,
            "no problem. i will not schedule anything without a specific time" not in text,
            f"next_step_{vertical}: used vague-callback no-schedule fallback: {snapshot(final)}",
        )
        assert_condition(failures, sem != "no_contextual_semantic", f"next_step_{vertical}: fell through to no_contextual_semantic: {snapshot(final)}")


def validate_vertical_support_boundaries(failures: list[str], evidence: dict[str, Any], campaigns: dict[str, dict[str, Any]]) -> None:
    evidence["vertical_support_boundaries"] = {}
    for vertical, utterance in SUPPORT_BOUNDARY_CASES.items():
        packets = run_generic_sequence(
            f"delta-findings-support-{vertical}",
            campaigns[vertical],
            ["__agent_open__", "yeah sure", utterance],
        )
        evidence["vertical_support_boundaries"][vertical] = [snapshot(packet) for packet in packets]
        assert_generic_common(failures, packets, f"support_{vertical}")
        final = packets[-1]
        sem = semantic(final)
        text = normalize(final_response(final))
        assert_condition(failures, sem in SUPPORT_BOUNDARY_SEMANTICS, f"support_{vertical}: wrong semantic {sem}: {snapshot(final)}")
        assert_condition(
            failures,
            any(term in text for term in ["support", "account", "claim", "order", "warranty", "authorized", "outside this call", "cannot handle", "can't handle"]),
            f"support_{vertical}: missing support/account boundary wording: {snapshot(final)}",
        )
        assert_condition(
            failures,
            not any(term in text for term in ["which of those", "which one", "which part", "next step would be a short", "schedule a", "review call"]),
            f"support_{vertical}: reopened diagnostic or pushed appointment/review: {snapshot(final)}",
        )
        assert_condition(
            failures,
            not any(term in text for term in ["i can change", "i can cancel", "i can check your warranty", "i can handle your claim", "i can help with your order"]),
            f"support_{vertical}: implied fake support action: {snapshot(final)}",
        )


def validate_routesignal_support_boundary(failures: list[str], evidence: dict[str, Any]) -> None:
    packets = run_routesignal_sequence(
        "delta-findings-routesignal-password",
        ["__agent_open__", "yeah sure", "can you help with my password?"],
    )
    evidence["routesignal_support_boundary"] = [snapshot(packet) for packet in packets]
    for index, packet in enumerate(packets, start=1):
        assert_no_side_effects(failures, packet, f"routesignal_password_turn{index}")
    final = packets[-1]
    text = normalize(final_response(final))
    assert_condition(
        failures,
        any(term in text for term in ["password", "account", "support", "outside this call", "cannot help", "can't help"]),
        f"routesignal_password: missing password/account support boundary: {snapshot(final)}",
    )
    assert_condition(
        failures,
        not any(term in text for term in ["callback reminders", "manual tracking", "spreadsheet", "which of those", "which one"]),
        f"routesignal_password: routed into callback/manual-tracking diagnostic: {snapshot(final)}",
    )


def validate_routesignal_already_told_you(failures: list[str], evidence: dict[str, Any]) -> None:
    packets = run_routesignal_sequence(
        "delta-findings-routesignal-already-told-you",
        ["__agent_open__", "yeah sure", "handoffs get messy", "I already told you"],
    )
    evidence["routesignal_already_told_you"] = [snapshot(packet) for packet in packets]
    for index, packet in enumerate(packets, start=1):
        assert_no_side_effects(failures, packet, f"routesignal_already_told_you_turn{index}")
    final = packets[-1]
    text = normalize(final_response(final))
    assert_condition(failures, "handoffs" in confirmed_gaps(final), f"routesignal_already_told_you: confirmed handoffs not preserved: {snapshot(final)}")
    assert_condition(
        failures,
        "handoffs" in text and any(term in text for term in ["already", "you said", "you're right", "you are right"]),
        f"routesignal_already_told_you: did not acknowledge already-stated handoffs pain: {snapshot(final)}",
    )
    assert_condition(
        failures,
        "no problem. we can leave it here" not in text,
        f"routesignal_already_told_you: treated repeated context as stop: {snapshot(final)}",
    )
    assert_condition(
        failures,
        any(term in text for term in ["next step", "callback", "time", "stop", "leave it here"]),
        f"routesignal_already_told_you: did not offer next step/callback/stop: {snapshot(final)}",
    )


def validate_uncertainty_ownership(failures: list[str], evidence: dict[str, Any], campaigns: dict[str, dict[str, Any]]) -> None:
    evidence["uncertainty_ownership"] = {}
    for vertical, transcripts in UNCERTAINTY_CASES.items():
        packets = run_generic_sequence(f"delta-findings-uncertainty-{vertical}", campaigns[vertical], transcripts)
        evidence["uncertainty_ownership"][vertical] = [snapshot(packet) for packet in packets]
        assert_generic_common(failures, packets, f"uncertainty_{vertical}")
        final = packets[-1]
        sem = semantic(final)
        text = normalize(final_response(final))
        assert_condition(failures, sem in UNCERTAINTY_SEMANTICS, f"uncertainty_{vertical}: wrong semantic {sem}: {snapshot(final)}")
        assert_condition(failures, sem != "no_contextual_semantic", f"uncertainty_{vertical}: no contextual ownership: {snapshot(final)}")
        assert_condition(
            failures,
            not any(term in text for term in ["next step would be a short", "schedule", "book", "review focused on"]),
            f"uncertainty_{vertical}: uncertainty jumped to appointment/review pressure: {snapshot(final)}",
        )
        assert_condition(
            failures,
            text.count(", or ") <= 1,
            f"uncertainty_{vertical}: repeated full diagnostic loop instead of a simpler question: {snapshot(final)}",
        )


def validate_confusion_explanation_quality(failures: list[str], evidence: dict[str, Any], campaigns: dict[str, dict[str, Any]]) -> None:
    evidence["confusion_explanation_quality"] = {}
    for vertical, transcripts in CONFUSION_CASES.items():
        packets = run_generic_sequence(f"delta-findings-confusion-{vertical}", campaigns[vertical], transcripts)
        evidence["confusion_explanation_quality"][vertical] = [snapshot(packet) for packet in packets]
        assert_generic_common(failures, packets, f"confusion_{vertical}")
        final = packets[-1]
        text = normalize(final_response(final))
        assert_condition(
            failures,
            any(term in text for term in ["i'm asking whether", "i am asking whether", "worth a", "if none", "if not", "stop here", "what i mean"]),
            f"confusion_{vertical}: response did not explain the purpose in plain terms: {snapshot(final)}",
        )
        assert_condition(
            failures,
            not any(term in text for term in ["next step would be a short", "schedule", "book"]),
            f"confusion_{vertical}: confusion got appointment pressure: {snapshot(final)}",
        )
        assert_no_generic_leakage(failures, final, f"confusion_{vertical}")


def validate_pain_bridge_wording(failures: list[str], evidence: dict[str, Any], campaigns: dict[str, dict[str, Any]]) -> None:
    evidence["pain_bridge_wording"] = {}
    for vertical, (pain_phrase, gap_id) in PAIN_CASES.items():
        packets = run_generic_sequence(f"delta-findings-pain-{vertical}", campaigns[vertical], ["__agent_open__", "yeah sure", pain_phrase])
        evidence["pain_bridge_wording"][vertical] = [snapshot(packet) for packet in packets]
        assert_generic_common(failures, packets, f"pain_{vertical}")
        final = packets[-1]
        blob = normalize(text_blob(final))
        assert_condition(failures, "real gap" not in blob, f"pain_{vertical}: generic response used 'real gap': {snapshot(final)}")
        assert_condition(failures, gap_id in confirmed_gaps(final), f"pain_{vertical}: confirmed gap missing: {snapshot(final)}")
        target = normalize(campaigns[vertical].get("appointment_target") or "")
        owner = normalize(campaigns[vertical].get("human_followup_owner") or "")
        assert_condition(
            failures,
            target in blob or owner in blob,
            f"pain_{vertical}: follow-up owner/target missing after pain confirmation: {snapshot(final)}",
        )


def validate_callback_confirmation_wording(failures: list[str], evidence: dict[str, Any], campaigns: dict[str, dict[str, Any]]) -> None:
    evidence["callback_confirmation_wording"] = {}
    for vertical in CALLBACK_CASES:
        packets = run_generic_sequence(
            f"delta-findings-callback-{vertical}",
            campaigns[vertical],
            ["__agent_open__", "yeah sure", "send me details", "maybe later", "tomorrow at 3 works"],
        )
        evidence["callback_confirmation_wording"][vertical] = [snapshot(packet) for packet in packets]
        assert_generic_common(failures, packets, f"callback_{vertical}")
        final = packets[-1]
        text = normalize(final_response(final))
        target = normalize(campaigns[vertical].get("appointment_target") or "")
        owner = normalize(campaigns[vertical].get("human_followup_owner") or "")
        assert_condition(
            failures,
            "record that callback time for" not in text,
            f"callback_{vertical}: used clunky callback wording: {snapshot(final)}",
        )
        assert_condition(
            failures,
            target in text or owner in text,
            f"callback_{vertical}: did not name appointment target or owner naturally: {snapshot(final)}",
        )
        assert_condition(
            failures,
            not any(term in text for term in ["calendar", "invite", "emailed", "sent"]),
            f"callback_{vertical}: implied calendar/email side effect: {snapshot(final)}",
        )
        assert_condition(
            failures,
            (final.get("summary") or {}).get("call_control") == "schedule-and-end",
            f"callback_{vertical}: usable callback time did not schedule-and-end: {snapshot(final)}",
        )

    packets = run_routesignal_sequence(
        "delta-findings-routesignal-callback",
        ["__agent_open__", "yeah sure", "send me details", "maybe later", "tomorrow at 3 works"],
    )
    evidence["callback_confirmation_wording"]["routesignal_live_demo"] = [snapshot(packet) for packet in packets]
    for index, packet in enumerate(packets, start=1):
        assert_no_side_effects(failures, packet, f"routesignal_callback_turn{index}")
    final = packets[-1]
    assert_condition(
        failures,
        bool(memory(final).get("lead_followup_state")),
        f"routesignal_callback: callback state missing: {snapshot(final)}",
    )


def validate_route_signal_preservation(failures: list[str], evidence: dict[str, Any]) -> None:
    cases = {
        "callbacks_clear": ["__agent_open__", "yeah sure", "callbacks are fine"],
        "handoffs_pain": ["__agent_open__", "yeah sure", "handoffs get messy"],
        "send_info_yes": ["__agent_open__", "yeah sure", "send me details first", "yes send it"],
        "callback_time": ["__agent_open__", "yeah sure", "send me details", "tomorrow at 3 works"],
    }
    evidence["routesignal_preservation"] = {}
    for label, transcripts in cases.items():
        packets = run_routesignal_sequence(f"delta-findings-routesignal-preserve-{label}", transcripts)
        evidence["routesignal_preservation"][label] = [snapshot(packet) for packet in packets]
        for index, packet in enumerate(packets, start=1):
            assert_no_side_effects(failures, packet, f"routesignal_preserve_{label}_turn{index}")
        final = packets[-1]
        sem = semantic(final)
        if label == "callbacks_clear":
            assert_condition(failures, sem == "current_gap_clear", f"routesignal callbacks clear changed: {snapshot(final)}")
            assert_condition(failures, semantic_frame(final).get("target_gap") == "callbacks", f"routesignal callbacks target changed: {snapshot(final)}")
        if label == "handoffs_pain":
            assert_condition(failures, sem == "pain_confirmed", f"routesignal handoffs pain changed: {snapshot(final)}")
            assert_condition(failures, semantic_frame(final).get("target_gap") == "handoffs", f"routesignal handoffs target changed: {snapshot(final)}")
        if label == "send_info_yes":
            assert_condition(failures, bool(memory(final).get("send_info_state")), f"routesignal send-info state missing: {snapshot(final)}")
        if label == "callback_time":
            assert_condition(failures, bool(memory(final).get("lead_followup_state")), f"routesignal callback state missing: {snapshot(final)}")


def validate_all() -> tuple[list[str], dict[str, Any]]:
    failures: list[str] = []
    campaigns = synthetic_campaigns()
    evidence: dict[str, Any] = {
        "checkpoint_id": CHECKPOINT_ID,
        "source_packet": "HUMAN-SEMANTIC-DELTA-REVIEW-PACKET-002",
        "replayed_against_current_runtime": True,
        "synthetic_campaigns": sorted(campaigns),
        "route_signal_campaign": DEFAULT_CAMPAIGN_ID,
        "scenarios_added": [
            "generic next-step after confirmed pain",
            "vertical support/account boundaries",
            "RouteSignal password/account support boundary",
            "RouteSignal already-told-you after confirmed pain",
            "generic uncertainty semantic ownership",
            "generic confusion explanation quality",
            "generic pain bridge wording",
            "generic callback confirmation wording",
            "RouteSignal preservation",
        ],
    }
    validate_next_step_after_confirmed_pain(failures, evidence, campaigns)
    validate_vertical_support_boundaries(failures, evidence, campaigns)
    validate_routesignal_support_boundary(failures, evidence)
    validate_routesignal_already_told_you(failures, evidence)
    validate_uncertainty_ownership(failures, evidence, campaigns)
    validate_confusion_explanation_quality(failures, evidence, campaigns)
    validate_pain_bridge_wording(failures, evidence, campaigns)
    validate_callback_confirmation_wording(failures, evidence, campaigns)
    validate_route_signal_preservation(failures, evidence)
    return failures, sanitize(evidence)


def render_report(result: dict[str, Any]) -> str:
    lines = [
        f"# {CHECKPOINT_ID}",
        "",
        "## Summary",
        "",
        f"- Status: {result['status']}",
        f"- Initial red replay failures reproduced before patch: {result['initial_red_replay_failure_count']}",
        f"- Current failure count: {result['failure_count']}",
        f"- Runtime behavior changed by patch: {result['runtime_behavior_changed']}",
        f"- Phase 1/2/3 backpatch required: {result['phase_1_2_3_backpatch_required']}",
        "",
        "## Validator Scenarios Added",
        "",
    ]
    for scenario in result["scenarios_added"]:
        lines.append(f"- {scenario}")
    lines.extend(["", "## Patches Made", ""])
    for patch in result["patches_made"]:
        lines.append(f"- {patch}")
    lines.extend(["", "## Failures", ""])
    if result["failures"]:
        for failure in result["failures"]:
            lines.append(f"- {failure}")
    else:
        lines.append("- None.")
    lines.extend(
        [
            "",
            "## RouteSignal Preservation",
            "",
            f"- RouteSignal preservation result: {result['routesignal_preservation_result']}",
            "",
            "## Safety",
            "",
            "- Synthetic generic campaigns only.",
            "- RouteSignal live-demo path used only for RouteSignal-specific checks.",
            "- Provider calls false.",
            "- Local LLM calls false.",
            "- Email/calendar/CRM writes false.",
            "- PROD-102 false.",
            "- Raw synthetic emails redacted in public evidence.",
            "",
        ]
    )
    return "\n".join(lines)


def write_evidence(result: dict[str, Any]) -> None:
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    sanitized = sanitize(result)
    assert_no_raw_emails_in_result(sanitized)
    RESULT_PATH.write_text(json.dumps(sanitized, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    REPORT_PATH.write_text(render_report(sanitized), encoding="utf-8")


def main() -> int:
    failures, evidence = validate_all()
    result = {
        "checkpoint_id": CHECKPOINT_ID,
        "status": "pass" if not failures else "fail",
        "source_packet": "HUMAN-SEMANTIC-DELTA-REVIEW-PACKET-002",
        "initial_red_replay_failure_count": INITIAL_RED_REPLAY_FAILURE_COUNT,
        "current_replayed_failures_reproduced": bool(failures),
        "failure_count": len(failures),
        "failures": failures,
        "evidence": evidence,
        "scenarios_added": evidence["scenarios_added"],
        "patches_made": [
            "Added confirmed-pain next-step ownership and response wording.",
            "Added vertical account/support boundary classification and response wording.",
            "Added RouteSignal password/account boundary and already-told-you handling.",
            "Added explicit uncertainty-after-diagnostic ownership.",
            "Improved confusion explanation wording.",
            "Removed generic 'real gap' pain bridge wording.",
            "Polished generic callback confirmation wording.",
        ],
        "routesignal_preservation_result": "pass" if not failures else "blocked_by_current_failures",
        "runtime_behavior_changed": True,
        "phase_1_2_3_backpatch_required": False,
        "provider_calls_made": False,
        "local_llm_calls_made": False,
        "sends_email": False,
        "creates_calendar_event": False,
        "writes_crm": False,
        "opens_prod_102": False,
    }
    write_evidence(result)
    print(json.dumps({"status": result["status"], "failure_count": len(failures)}, indent=2, sort_keys=True))
    if failures:
        for failure in failures[:30]:
            print(f"FAIL: {failure}", file=sys.stderr)
        if len(failures) > 30:
            print(f"FAIL: ... {len(failures) - 30} more failures", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
