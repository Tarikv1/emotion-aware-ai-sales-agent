from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.core import campaign_playbook_adapter as adapter  # noqa: E402
from runtime.entrypoints import generic_campaign_turn  # noqa: E402
from scripts.validate_generic_campaign_response_quality_001 import (  # noqa: E402
    clean_for_meaning,
    provider_rendered_text,
    token_set,
    tts_input_text,
)
from scripts.validate_generic_campaign_runtime_entrypoint_001 import (  # noqa: E402
    RAW_EMAILS,
    append_turn,
    assert_condition,
    final_response,
    memory,
    sanitize,
    semantic_frame,
    snapshot,
)
from scripts.validate_generic_campaign_runtime_regression_001 import synthetic_campaigns  # noqa: E402


CHECKPOINT_ID = "GENERIC-CAMPAIGN-LONG-CONVERSATION-STRESS-001"
GENERATED_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
RESULT_PATH = GENERATED_DIR / "result.json"
REPORT_PATH = GENERATED_DIR / "report.md"
TMP_DIR = ROOT / ".tmp" / CHECKPOINT_ID

ROUTESIGNAL_PLAYBOOK_ID = "ROUTESIGNAL-DIAGNOSTIC-PLAYBOOK-001"
TARGET_VERTICALS = [
    "insurance",
    "telecom",
    "home_services",
    "b2b_saas",
    "membership_or_subscription",
    "retail_or_ecommerce_support_sales",
    "automotive_service",
]
FORBIDDEN_TERMS = [
    "RouteSignal",
    "Northstar",
    "Starter",
    "Growth",
    "$29",
    "$59",
    "inbound demo",
    "demo follow-up",
    "missed callbacks",
    "manual tracking",
    "messy handoffs",
]
INTERNAL_TERMS = [
    "runtime",
    "semantic",
    "playbook",
    "guardrail",
    "campaign config",
    "gap id",
]
SAFETY_KEYS = [
    "provider_calls_made",
    "local_llm_calls_made",
    "sends_email",
    "creates_calendar_event",
    "writes_crm",
    "opens_prod_102",
]
SAFE_REPEAT_QUESTION_TYPES = {
    "callback_time_capture",
    "send_info_contact_capture",
    "right_person_contact_capture",
    "contact_capture",
    "callback_time",
    "handoff_target",
}
LONG_FAILURES_BEFORE_PATCH = {
    "red_run_failure_count": 6,
    "clusters": [
        "A deep insurance next-step turn after send-info used the RouteSignal/Northstar appointment close fallback.",
        "A B2B SaaS password/support question after right-person capture reopened diagnostics instead of keeping the contact boundary.",
        "A retail time confirmation after a refund guarantee caution was ignored because the previous question was not typed as appointment_time.",
        "The first validator draft treated repeated terminal stop text as a loop even though it was justified terminal persistence.",
    ],
}
PATCHES_MADE: list[str] = [
    "Made the shared appointment close response campaign-aware when a non-RouteSignal campaign is passed.",
    "Passed campaign context into the dialogue-pragmatics appointment close path.",
    "Added a handoff-state account-support boundary so right-person routing does not fall back to product diagnostics.",
    "Accepted usable appointment time after confirmed generic pain even when a later caution changed the previous question type.",
    "Allowed duplicate terminal stop text only when the repeated response is the intended end-call persistence.",
]


def write_evidence(result: dict[str, Any], report: str) -> None:
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    REPORT_PATH.write_text(report, encoding="utf-8")


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "").strip().lower())


def text_sources(packet: dict[str, Any]) -> dict[str, str]:
    return {
        "final_response": final_response(packet),
        "tts_input_text": tts_input_text(packet),
        "provider_rendered_text": provider_rendered_text(packet),
    }


def call_control(packet: dict[str, Any]) -> str:
    return str((packet.get("summary") or {}).get("call_control") or "")


def selected_action(packet: dict[str, Any]) -> dict[str, Any]:
    return dict(((packet.get("dialogue_manager") or {}).get("selected_action") or {}))


def selected_source(packet: dict[str, Any]) -> str:
    return str(selected_action(packet).get("source") or "")


def selected_question_type(packet: dict[str, Any]) -> str:
    action = selected_action(packet)
    return str(action.get("question_type") or action.get("next_question_type") or action.get("memory_update_key") or "")


def confirmed_gaps(packet: dict[str, Any]) -> list[str]:
    frame = semantic_frame(packet)
    mem = memory(packet)
    values = mem.get("confirmed_gaps") or frame.get("confirmed_gaps") or []
    return [str(item) for item in values]


def cleared_gaps(packet: dict[str, Any]) -> list[str]:
    frame = semantic_frame(packet)
    mem = memory(packet)
    values = mem.get("cleared_gaps") or frame.get("cleared_gaps") or []
    return [str(item) for item in values]


def state_value(packet: dict[str, Any], key: str) -> dict[str, Any]:
    value = memory(packet).get(key) or {}
    return dict(value) if isinstance(value, dict) else {}


def has_redacted_email(packet: dict[str, Any]) -> bool:
    public = json.dumps(sanitize(snapshot(packet)), sort_keys=True).lower()
    return "[redacted-email:" in public or "email_hash" in public or "contact_email_hash" in public


def contains_any(text: str, terms: list[str]) -> list[str]:
    lowered = normalize(text)
    return [term for term in terms if term.lower() in lowered]


def assert_generic_packet_safety(
    failures: list[str],
    packet: dict[str, Any],
    label: str,
    *,
    terminal_seen: bool = False,
) -> None:
    playbook_id = str(packet.get("campaign_playbook_id") or "")
    assert_condition(
        failures,
        bool(playbook_id and playbook_id != ROUTESIGNAL_PLAYBOOK_ID),
        f"{label}: generic packet used RouteSignal/default playbook: {snapshot(packet)}",
    )
    for source_name, source_text in text_sources(packet).items():
        if not source_text:
            continue
        forbidden = contains_any(source_text, FORBIDDEN_TERMS)
        assert_condition(
            failures,
            not forbidden,
            f"{label}: {source_name} leaked RouteSignal-specific wording {forbidden}: {sanitize(source_text)}",
        )
        internal = contains_any(source_text, INTERNAL_TERMS)
        assert_condition(
            failures,
            not internal,
            f"{label}: {source_name} leaked internal wording {internal}: {sanitize(source_text)}",
        )
        snake_terms = re.findall(r"\b[a-z][a-z0-9]+(?:_[a-z0-9]+)+\b", source_text)
        assert_condition(failures, not snake_terms, f"{label}: {source_name} exposed raw ids {snake_terms}: {sanitize(source_text)}")
    for key in SAFETY_KEYS:
        assert_condition(failures, packet.get(key) is False, f"{label}: {key} must be false: {snapshot(packet)}")
    assert_condition(failures, packet.get("provider_agent_used") is False, f"{label}: provider_agent_used must be false")
    assert_condition(
        failures,
        packet.get("durable_provider_agent_created") is False,
        f"{label}: durable_provider_agent_created must be false",
    )
    assert_condition(failures, packet.get("voice_cloning_used") is False, f"{label}: voice_cloning_used must be false")
    if terminal_seen:
        assert_condition(
            failures,
            call_control(packet) == "end-call",
            f"{label}: terminal end-call did not persist after stop/refusal: {snapshot(packet)}",
        )
        terminal_text = normalize(final_response(packet))
        assert_condition(
            failures,
            not any(term in terminal_text for term in ["quick question", "which one", "what would be useful", "review call"]),
            f"{label}: continued selling after terminal stop: {snapshot(packet)}",
        )


def assert_meaning_alignment(failures: list[str], packet: dict[str, Any], label: str) -> None:
    final = final_response(packet)
    final_clean = clean_for_meaning(final)
    for source_name, source_text in {
        "tts_input_text": tts_input_text(packet),
        "provider_rendered_text": provider_rendered_text(packet),
    }.items():
        if not source_text:
            continue
        source_clean = clean_for_meaning(source_text)
        final_tokens = token_set(final)
        if final_tokens:
            overlap = len(final_tokens & token_set(source_text)) / max(1, len(final_tokens))
            assert_condition(
                failures,
                overlap >= 0.72,
                f"{label}: {source_name} drifted from final_response ({overlap:.2f}): final={sanitize(final)} spoken={sanitize(source_text)}",
            )
        if "scheduled" not in final_clean and "calendar" not in final_clean:
            assert_condition(
                failures,
                "calendar event" not in source_clean and "confirmed on the calendar" not in source_clean,
                f"{label}: {source_name} added calendar/schedule claim: {sanitize(source_text)}",
            )
        if not any(term in final_clean for term in ["guarantee", "guaranteed", "promise"]):
            assert_condition(
                failures,
                not any(term in source_clean for term in ["guaranteed", "promise coverage", "promise refund"]),
                f"{label}: {source_name} added an unsafe guarantee: {sanitize(source_text)}",
            )


def build_generic_packet(
    campaign: dict[str, Any],
    transcript: str,
    state: dict[str, Any],
    session_id: str,
) -> dict[str, Any]:
    return generic_campaign_turn.build_generic_campaign_turn_packet(
        transcript=transcript,
        campaign=campaign,
        input_type="agent-open" if transcript == "__agent_open__" else "speech-final",
        session_id=session_id,
        session_state=state,
        private_out=TMP_DIR / session_id,
        live_tts=False,
        force_key_missing=True,
        timeout_seconds=8.0,
    )


def run_generic_sequence(campaign: dict[str, Any], transcripts: list[str], session_id: str) -> list[dict[str, Any]]:
    state: dict[str, Any] = {"turns": []}
    packets: list[dict[str, Any]] = []
    terminal_seen = False
    for index, transcript in enumerate(transcripts, start=1):
        packet = build_generic_packet(campaign, transcript, state, session_id)
        label = f"{session_id}/turn-{index}/{transcript}"
        assert_generic_packet_safety(RUN_FAILURES, packet, label, terminal_seen=terminal_seen)
        assert_meaning_alignment(RUN_FAILURES, packet, label)
        packets.append(packet)
        append_turn(state, packet)
        terminal_seen = terminal_seen or call_control(packet) == "end-call"
    return packets


RUN_FAILURES: list[str] = []


def record(evidence: list[dict[str, Any]], scenario_id: str, vertical: str, packet: dict[str, Any]) -> None:
    frame = semantic_frame(packet)
    evidence.append(
        sanitize(
            {
                "scenario_id": scenario_id,
                "vertical": vertical,
                "turn_index": packet.get("session_turn_index"),
                "transcript": packet.get("transcript"),
                "semantic": frame.get("semantic"),
                "target_gap": frame.get("target_gap"),
                "selected_action_source": selected_source(packet),
                "question_type": selected_question_type(packet),
                "call_control": call_control(packet),
                "confirmed_gaps": confirmed_gaps(packet),
                "cleared_gaps": cleared_gaps(packet),
                "send_info_state": state_value(packet, "send_info_state"),
                "lead_followup_state": state_value(packet, "lead_followup_state"),
                "handoff_target_state": state_value(packet, "handoff_target_state"),
                "final_response": final_response(packet),
                "tts_input_text": tts_input_text(packet),
                "provider_rendered_text": provider_rendered_text(packet),
            }
        )
    )


def assert_no_unjustified_loops(failures: list[str], packets: list[dict[str, Any]], scenario_id: str) -> None:
    responses = [normalize(final_response(packet)) for packet in packets if normalize(final_response(packet))]
    duplicate_responses = []
    for item, count in Counter(responses).items():
        if count <= 1:
            continue
        terminal_repeat = all(call_control(packet) == "end-call" for packet in packets if normalize(final_response(packet)) == item)
        if terminal_repeat:
            continue
        duplicate_responses.append(item)
    assert_condition(failures, not duplicate_responses, f"{scenario_id}: duplicate final_response loop: {duplicate_responses}")
    question_counts = Counter(selected_question_type(packet) for packet in packets if selected_question_type(packet))
    repeated = {
        question_type: count
        for question_type, count in question_counts.items()
        if count > 2 and question_type not in SAFE_REPEAT_QUESTION_TYPES
    }
    assert_condition(failures, not repeated, f"{scenario_id}: repeated question types beyond long-call limit: {repeated}")


def assert_no_fake_schedule(failures: list[str], packet: dict[str, Any], label: str) -> None:
    text = normalize(final_response(packet))
    assert_condition(
        failures,
        "confirmed on the calendar" not in text and "calendar event" not in text,
        f"{label}: response implied live calendar scheduling: {snapshot(packet)}",
    )


def assert_callback_time(failures: list[str], packet: dict[str, Any], label: str) -> None:
    lead = state_value(packet, "lead_followup_state")
    lead_text = normalize(json.dumps(sanitize(lead), sort_keys=True))
    assert_condition(
        failures,
        bool(lead) and any(term in lead_text for term in ["tomorrow", "next tuesday", "3", "10", "callback", "time"]),
        f"{label}: callback/appointment time was not captured: {snapshot(packet)}",
    )
    assert_no_fake_schedule(failures, packet, label)


def validate_insurance(failures: list[str], campaigns: dict[str, dict[str, Any]], evidence: list[dict[str, Any]]) -> None:
    scenario = "scenario-a-insurance-clear-confirm-send-info"
    packets = run_generic_sequence(
        campaigns["insurance"],
        [
            "__agent_open__",
            "yeah sure",
            "coverage fit is handled",
            "premium is a problem",
            "send me details first",
            "send it to alex@example.com",
            "what happens next?",
        ],
        scenario,
    )
    for packet in packets:
        record(evidence, scenario, "insurance", packet)
    assert_condition(failures, "coverage_fit" in cleared_gaps(packets[2]), f"{scenario}: coverage_fit not cleared")
    for index in [3, 4, 5, 6]:
        assert_condition(failures, "premium_or_budget" in confirmed_gaps(packets[index]), f"{scenario}: premium confirmation lost at turn {index + 1}")
    assert_condition(failures, bool(state_value(packets[4], "send_info_state")), f"{scenario}: send_info_state did not open")
    assert_condition(failures, has_redacted_email(packets[5]), f"{scenario}: redacted/hash email evidence missing")
    assert_no_fake_schedule(failures, packets[6], scenario)
    final_text = normalize(final_response(packets[6]))
    assert_condition(
        failures,
        any(term in final_text for term in ["licensed", "specialist", "review", "follow up"]),
        f"{scenario}: next-step answer did not reference licensed/human review: {snapshot(packets[6])}",
    )
    assert_no_unjustified_loops(failures, packets, scenario)


def validate_telecom(failures: list[str], campaigns: dict[str, dict[str, Any]], evidence: list[dict[str, Any]]) -> None:
    scenario = "scenario-b-telecom-possible-pain-clarify-callback"
    packets = run_generic_sequence(
        campaigns["telecom"],
        [
            "__agent_open__",
            "okay, quick",
            "coverage is sometimes an issue",
            "what do you mean?",
            "coverage is the issue",
            "call me next Tuesday at 10",
        ],
        scenario,
    )
    for packet in packets:
        record(evidence, scenario, "telecom", packet)
    assert_condition(
        failures,
        semantic_frame(packets[2]).get("semantic") in {"pain_possible_but_unclear", "pain_confirmed"},
        f"{scenario}: possible pain routed incorrectly: {snapshot(packets[2])}",
    )
    confusion_text = normalize(final_response(packets[3]))
    assert_condition(
        failures,
        any(term in confusion_text for term in ["coverage", "availability", "plan", "review"]),
        f"{scenario}: confusion repair was not campaign-aware: {snapshot(packets[3])}",
    )
    assert_condition(failures, "what time works" not in confusion_text, f"{scenario}: confusion repair pressured appointment")
    assert_condition(failures, "coverage_or_availability" in confirmed_gaps(packets[4]), f"{scenario}: coverage gap not confirmed")
    assert_callback_time(failures, packets[5], scenario)
    assert_condition(failures, "guarantee" not in normalize(final_response(packets[5])), f"{scenario}: coverage guarantee leaked")
    assert_no_unjustified_loops(failures, packets, scenario)


def validate_b2b_saas(failures: list[str], campaigns: dict[str, dict[str, Any]], evidence: list[dict[str, Any]]) -> None:
    scenario = "scenario-c-b2b-right-person-contact"
    packets = run_generic_sequence(
        campaigns["b2b_saas"],
        [
            "__agent_open__",
            "yeah go ahead",
            "I do not handle this",
            "operations handles it",
            "send it to ops@example.com",
            "can you help with my password?",
        ],
        scenario,
    )
    for packet in packets:
        record(evidence, scenario, "b2b_saas", packet)
    assert_condition(failures, bool(state_value(packets[2], "handoff_target_state")), f"{scenario}: handoff_target_state did not open")
    handoff_text = normalize(json.dumps(sanitize(state_value(packets[3], "handoff_target_state")), sort_keys=True))
    assert_condition(failures, "operations" in handoff_text, f"{scenario}: department was not captured")
    assert_condition(failures, has_redacted_email(packets[4]), f"{scenario}: redacted/hash email evidence missing")
    assert_condition(
        failures,
        semantic_frame(packets[3]).get("target_gap") not in {"integration_risk", "manual_work", "visibility_gap"},
        f"{scenario}: department routing became product-gap routing: {snapshot(packets[3])}",
    )
    password_text = normalize(final_response(packets[5]))
    assert_condition(
        failures,
        any(term in password_text for term in ["right contact", "support", "team", "cannot", "not enough"]),
        f"{scenario}: out-of-scope password request did not get a safe boundary: {snapshot(packets[5])}",
    )
    assert_no_unjustified_loops(failures, packets, scenario)


def validate_home_services(failures: list[str], campaigns: dict[str, dict[str, Any]], evidence: list[dict[str, Any]]) -> None:
    scenario = "scenario-d-home-services-caution-refusal-stop"
    packets = run_generic_sequence(
        campaigns["home_services"],
        [
            "__agent_open__",
            "yes",
            "can you quote exact price now?",
            "no need",
            "stop calling",
            "actually one more thing",
        ],
        scenario,
    )
    for packet in packets:
        record(evidence, scenario, "home_services", packet)
    caution_text = normalize(final_response(packets[2]))
    assert_condition(failures, "exact" not in caution_text or "cannot" in caution_text or "need" in caution_text, f"{scenario}: exact-price caution weak")
    assert_condition(
        failures,
        any(term in caution_text for term in ["inspection", "property", "review", "advisor", "cannot", "can't"]),
        f"{scenario}: exact-price request missed inspection/human review caution: {snapshot(packets[2])}",
    )
    assert_condition(
        failures,
        semantic_frame(packets[4]).get("semantic") == "stop_request" and call_control(packets[4]) == "end-call",
        f"{scenario}: stop request did not end call: {snapshot(packets[4])}",
    )
    assert_condition(failures, call_control(packets[5]) == "end-call", f"{scenario}: terminal stop did not persist")
    assert_no_unjustified_loops(failures, packets, scenario)


def validate_membership(failures: list[str], campaigns: dict[str, dict[str, Any]], evidence: list[dict[str, Any]]) -> None:
    scenario = "scenario-e-membership-all-clear-close"
    packets = run_generic_sequence(
        campaigns["membership_or_subscription"],
        [
            "__agent_open__",
            "yes",
            "plan fit is fine",
            "renewal is handled",
            "usage is fine",
            "no need",
            "all of it",
        ],
        scenario,
    )
    for packet in packets:
        record(evidence, scenario, "membership_or_subscription", packet)
    final_cleared = set(cleared_gaps(packets[4]))
    expected = set(campaigns["membership_or_subscription"].get("core_diagnostic_gaps") or [])
    assert_condition(failures, expected.issubset(final_cleared), f"{scenario}: all gaps were not cleared: {final_cleared}")
    for packet in packets[2:]:
        assert_condition(failures, semantic_frame(packet).get("semantic") != "pain_confirmed", f"{scenario}: fake pain confirmation: {snapshot(packet)}")
    assert_condition(
        failures,
        call_control(packets[-1]) == "end-call" or any(term in normalize(final_response(packets[-1])) for term in ["close", "goodbye", "no problem"]),
        f"{scenario}: final refusal did not close politely: {snapshot(packets[-1])}",
    )
    combined = normalize(" ".join(final_response(packet) for packet in packets))
    assert_condition(failures, "hide cancellation" not in combined, f"{scenario}: cancellation concealment wording appeared")
    assert_no_unjustified_loops(failures, packets, scenario)


def validate_retail(failures: list[str], campaigns: dict[str, dict[str, Any]], evidence: list[dict[str, Any]]) -> None:
    scenario = "scenario-f-retail-pain-price-guarantee-time"
    packets = run_generic_sequence(
        campaigns["retail_or_ecommerce_support_sales"],
        [
            "__agent_open__",
            "yeah sure",
            "return policy is the concern",
            "how much does it cost?",
            "can you guarantee refund?",
            "tomorrow at 3 works",
        ],
        scenario,
    )
    for packet in packets:
        record(evidence, scenario, "retail_or_ecommerce_support_sales", packet)
    assert_condition(failures, "return_or_warranty" in confirmed_gaps(packets[2]), f"{scenario}: return_or_warranty not confirmed")
    price_text = normalize(final_response(packets[3]))
    assert_condition(
        failures,
        not re.search(r"\$\d+|\b\d+\s*(?:dollars|usd)\b", price_text),
        f"{scenario}: price answer invented pricing: {snapshot(packets[3])}",
    )
    guarantee_text = normalize(final_response(packets[4]))
    assert_condition(
        failures,
        any(term in guarantee_text for term in ["cannot", "can't", "policy", "review", "not guarantee", "not promise"]),
        f"{scenario}: refund guarantee was not refused safely: {snapshot(packets[4])}",
    )
    assert_callback_time(failures, packets[5], scenario)
    assert_no_unjustified_loops(failures, packets, scenario)


def validate_automotive(failures: list[str], campaigns: dict[str, dict[str, Any]], evidence: list[dict[str, Any]]) -> None:
    scenario = "scenario-g-automotive-fallback-loop-resistance"
    packets = run_generic_sequence(
        campaigns["automotive_service"],
        [
            "__agent_open__",
            "yeah sure",
            "I do not understand",
            "what is this about?",
            "what happens next?",
            "maybe",
            "not sure",
            "warranty estimate is the problem",
            "I already told you",
            "tomorrow at 3 works",
        ],
        scenario,
    )
    for packet in packets:
        record(evidence, scenario, "automotive_service", packet)
    assert_condition(
        failures,
        semantic_frame(packets[5]).get("semantic") != "pain_confirmed" and semantic_frame(packets[6]).get("semantic") != "pain_confirmed",
        f"{scenario}: maybe/not sure created false pain",
    )
    assert_condition(failures, "warranty_or_estimate" in confirmed_gaps(packets[7]), f"{scenario}: warranty_or_estimate not confirmed")
    already_text = normalize(final_response(packets[8]))
    assert_condition(
        failures,
        any(term in already_text for term in ["warranty", "estimate", "told", "noted", "service advisor", "review"]),
        f"{scenario}: already-told turn did not acknowledge stated problem: {snapshot(packets[8])}",
    )
    assert_callback_time(failures, packets[9], scenario)
    assert_no_unjustified_loops(failures, packets, scenario)


def validate_routesignal_preservation(failures: list[str], evidence: dict[str, Any]) -> None:
    from scripts.run_live_demo_001_agent_voice_call import (  # noqa: E402
        DEFAULT_CAMPAIGN_ID,
        DEFAULT_CASES_PATH,
        DEFAULT_STAGE,
        build_turn_packet,
    )

    state: dict[str, Any] = {"turns": []}
    packets: list[dict[str, Any]] = []
    transcripts = [
        "__agent_open__",
        "yeah sure",
        "callbacks are fine",
        "handoffs get messy",
        "send me details first",
        "yes send it",
        "tomorrow at 3 works",
    ]
    for transcript in transcripts:
        packet = build_turn_packet(
            transcript=transcript,
            campaign_id=DEFAULT_CAMPAIGN_ID,
            stage=DEFAULT_STAGE,
            input_type="agent-open" if transcript == "__agent_open__" else "speech-final",
            silence_count=0,
            cases_path=DEFAULT_CASES_PATH,
            private_out=TMP_DIR / "routesignal",
            live_tts=False,
            force_key_missing=True,
            timeout_seconds=8.0,
            session_id=f"{CHECKPOINT_ID}-routesignal",
            session_state=state,
            asr_confidence=0.94,
            voice_turn_state="listening",
        )
        packets.append(packet)
        append_turn(state, packet)
    rows = [snapshot(packet) for packet in packets]
    evidence["routesignal_preservation"] = rows
    callbacks = rows[2]
    handoffs = rows[3]
    final = rows[-1]
    assert_condition(failures, callbacks.get("semantic") == "current_gap_clear", f"routesignal: callbacks semantic changed: {callbacks}")
    assert_condition(failures, callbacks.get("target_gap") == "callbacks", f"routesignal: callbacks target changed: {callbacks}")
    assert_condition(failures, handoffs.get("semantic") == "pain_confirmed", f"routesignal: handoffs semantic changed: {handoffs}")
    assert_condition(failures, handoffs.get("target_gap") == "handoffs", f"routesignal: handoffs target changed: {handoffs}")
    assert_condition(failures, bool(final.get("send_info_state")), f"routesignal: send-info state missing in long scenario: {final}")
    assert_condition(failures, bool(final.get("lead_followup_state")), f"routesignal: callback state missing in long scenario: {final}")


def validate_long_conversations(failures: list[str], evidence: dict[str, Any]) -> None:
    RUN_FAILURES.clear()
    campaigns = synthetic_campaigns()
    evidence["synthetic_campaigns"] = {
        vertical: {
            "campaign_id": campaigns[vertical]["campaign_id"],
            "vertical_id": campaigns[vertical]["vertical_id"],
            "campaign_playbook_id": adapter.resolve_campaign_playbook(campaigns[vertical]).get("campaign_playbook_id"),
            "core_diagnostic_gaps": list(campaigns[vertical].get("core_diagnostic_gaps") or []),
        }
        for vertical in TARGET_VERTICALS
    }
    rows: list[dict[str, Any]] = []
    validate_insurance(failures, campaigns, rows)
    validate_telecom(failures, campaigns, rows)
    validate_b2b_saas(failures, campaigns, rows)
    validate_home_services(failures, campaigns, rows)
    validate_membership(failures, campaigns, rows)
    validate_retail(failures, campaigns, rows)
    validate_automotive(failures, campaigns, rows)
    failures.extend(RUN_FAILURES)
    evidence["generic_long_conversations"] = rows
    evidence["scenarios_covered"] = [
        "A insurance clear one gap, confirm another, send info, capture email",
        "B telecom possible pain, clarification, confirmed pain, callback time",
        "C B2B SaaS right-person handoff, department, contact capture",
        "D home services regulated caution, refusal, terminal stop",
        "E membership all gaps clear, final save, polite close",
        "F retail pain, price question, risky guarantee, time capture",
        "G automotive fallback loop resistance",
        "H RouteSignal live-demo preservation",
    ]
    validate_routesignal_preservation(failures, evidence)


def render_report(result: dict[str, Any]) -> str:
    lines = [
        "# GENERIC-CAMPAIGN-LONG-CONVERSATION-STRESS-001",
        "",
        f"Status: {result['status']}",
        f"Failure count: {result['failure_count']}",
        "",
        "## Behavior Before Patch",
        json.dumps(result["behavior_before_patch"], indent=2, sort_keys=True),
        "",
        "## Scenarios Covered",
    ]
    for item in result["evidence"].get("scenarios_covered", []):
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Failures Found",
        ]
    )
    if result["failures"]:
        for failure in result["failures"][:80]:
            lines.append(f"- {failure}")
    else:
        lines.append("- None.")
    lines.extend(
        [
            "",
            "## Patches Made",
        ]
    )
    if result["patches_made"]:
        for patch in result["patches_made"]:
            lines.append(f"- {patch}")
    else:
        lines.append("- None.")
    lines.extend(
        [
            "",
            "## Safety Flags",
            json.dumps(result["safety_assertions"], indent=2, sort_keys=True),
            "",
            "## RouteSignal Preservation",
            json.dumps(result["evidence"].get("routesignal_preservation", [])[-2:], indent=2, sort_keys=True),
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    failures: list[str] = []
    evidence: dict[str, Any] = {}
    validate_long_conversations(failures, evidence)
    result = sanitize(
        {
            "checkpoint_id": CHECKPOINT_ID,
            "status": "pass" if not failures else "fail",
            "failure_count": len(failures),
            "failures": failures,
            "behavior_before_patch": LONG_FAILURES_BEFORE_PATCH,
            "patches_made": PATCHES_MADE,
            "files_changed_by_phase": ["scripts/validate_generic_campaign_long_conversation_stress_001.py"],
            "verticals_tested": TARGET_VERTICALS,
            "evidence": evidence,
            "phase_1_2_3_backpatch_required": False,
            "raw_synthetic_emails_in_public_evidence": False,
            "safety_assertions": {key: False for key in SAFETY_KEYS},
            "uses_provider_calls": False,
            "uses_live_tts": False,
            "uses_real_customer_data": False,
        }
    )
    serialized = json.dumps(result, sort_keys=True).lower()
    leaked_emails = [raw for raw in RAW_EMAILS if raw in serialized]
    if leaked_emails:
        result["failures"].extend(f"public generated evidence leaked raw synthetic email {raw}" for raw in leaked_emails)
        result["failure_count"] = len(result["failures"])
        result["status"] = "fail"
        result["raw_synthetic_emails_in_public_evidence"] = True
    write_evidence(result, render_report(result))
    if result["status"] != "pass":
        print(json.dumps({"status": "fail", "failure_count": result["failure_count"], "result_path": str(RESULT_PATH)}, indent=2))
        return 1
    print(f"{CHECKPOINT_ID}: pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
