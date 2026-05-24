#!/usr/bin/env python3
"""Validate broad menu suppression across permission, correction, challenge, and callback turns."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import run_live_demo_001_agent_voice_call as demo  # noqa: E402


CHECKPOINT_ID = "BROAD-MENU-SUPPRESSION-001"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
TMP_DIR = ROOT / ".tmp" / CHECKPOINT_ID
EXAMPLES = ROOT / "runtime" / "campaigns" / "examples"

SIDE_EFFECT_KEYS = [
    "provider_calls_made",
    "local_llm_calls_made",
    "live_tts_used",
    "tts_provider_calls_made",
    "audio_file_created",
    "sends_email",
    "creates_calendar_event",
    "writes_crm",
    "opens_prod_102",
    "customer_audio_uploaded_to_python_server",
    "customer_audio_uploaded_to_tts_provider",
]

FORBIDDEN_MENU = [
    "which part is least clear",
    "which part is more familiar",
    "which part should i check first",
    "which one is causing trouble",
    "which part causes trouble",
    "which gap should i keep",
    "manual tracking or missed callbacks",
    "callback reminders for demo follow-up",
    "premium or budget, coverage fit",
    "plan fit, coverage or availability",
    "vehicle issue, repair timing",
    "manual work, integration",
    "if not, i can stop here; which",
    "if not i can stop here; which",
]

FORBIDDEN_INTERNAL = [
    "approved qualified reviewer path",
    "approved scope",
    "internal policy",
    "transfer-or-escalate",
    "prod-102",
]


@dataclass(frozen=True)
class Campaign:
    campaign_id: str
    config_path: Path | None
    primary_terms: tuple[str, ...]
    no_problem: str
    configured_gap_phrases: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class Scenario:
    scenario_id: str
    group: str
    campaign: Campaign
    buyer_script: tuple[str, ...]
    expected_move_ids: frozenset[str] = frozenset()
    expected_reason_contains: str | None = None
    required_terms: tuple[str, ...] = ()
    forbidden_terms: tuple[str, ...] = ()
    allow_end_call: bool = False
    require_end_call: bool = False
    negative_control: bool = False
    time_pressure: bool = False


CAMPAIGNS = [
    Campaign(
        "routesignal_live_demo",
        None,
        ("inbound demo", "demo follow-up", "follow-up slipping"),
        "callbacks are not a problem",
        (
            ("callbacks thing is confusing", "callbacks"),
            ("handoffs are unclear", "handoffs"),
            ("what do you mean by callbacks", "callbacks"),
            ("call bags are confusing", "callbacks"),
        ),
    ),
    Campaign(
        "synthetic-insurance-review",
        EXAMPLES / "synthetic-insurance-review.json",
        ("premium pressure", "premium"),
        "coverage is not confusing",
        (
            ("coverage thing is confusing", "coverage"),
            ("coverage fit is unclear", "coverage"),
            ("what do you mean by coverage fit", "coverage"),
            ("payment pressure is confusing", "premium"),
        ),
    ),
    Campaign(
        "synthetic-telecom-plan-review",
        EXAMPLES / "synthetic-telecom-plan-review.json",
        ("plan fit", "plan"),
        "coverage availability is not confusing",
        (
            ("plane fit is confusing", "plan"),
            ("contact switching is confusing", "contract"),
            ("what do you mean by plan fit", "plan"),
            ("coverage availability is unclear", "coverage"),
        ),
    ),
    Campaign(
        "synthetic-automotive-service-review",
        EXAMPLES / "synthetic-automotive-service-review.json",
        ("repair timing", "repair"),
        "repair timing is not a problem",
        (
            ("repair timing is confusing", "repair"),
            ("warranty estimate thing is unclear", "warranty"),
            ("what do you mean by repair timing", "repair"),
            ("service timing is confusing", "timing"),
        ),
    ),
    Campaign(
        "synthetic-membership-plan-review",
        EXAMPLES / "synthetic-membership-plan-review.json",
        ("plan fit", "plan"),
        "plan fit is not a problem",
        (
            ("plan thing is confusing", "plan"),
            ("usage thing is unclear", "usage"),
            ("what do you mean by plan fit", "plan"),
            ("cancel timing is confusing", "cancel"),
        ),
    ),
    Campaign(
        "synthetic-b2b-saas-operations",
        EXAMPLES / "synthetic-b2b-saas-operations.json",
        ("manual work", "manual"),
        "manual work is not a problem",
        (
            ("integration thing is confusing", "integration"),
            ("visibility thing is unclear", "visibility"),
            ("what do you mean by integration risk", "integration"),
            ("manual trucking is confusing", "manual"),
        ),
    ),
]


def norm(value: Any) -> str:
    return " ".join(str(value or "").lower().replace("'", " ").split())


def contains_any(text: str, phrases: tuple[str, ...] | list[str] | set[str]) -> bool:
    return any(phrase in text for phrase in phrases)


def selected_action(packet: dict[str, Any]) -> dict[str, Any]:
    value = (packet.get("dialogue_manager") or {}).get("selected_action") or {}
    return value if isinstance(value, dict) else {}


def universal_frame(packet: dict[str, Any]) -> dict[str, Any]:
    value = packet.get("universal_policy_frame") or (packet.get("dialogue_manager") or {}).get("universal_policy_frame") or {}
    return value if isinstance(value, dict) else {}


def contextual_frame(packet: dict[str, Any]) -> dict[str, Any]:
    value = packet.get("contextual_buyer_semantics") or (packet.get("dialogue_manager") or {}).get("contextual_buyer_semantics") or {}
    return value if isinstance(value, dict) else {}


def final_response(packet: dict[str, Any]) -> str:
    return str((packet.get("summary") or {}).get("final_response") or packet.get("final_response") or "")


def call_control(packet: dict[str, Any]) -> str:
    return str((packet.get("summary") or {}).get("call_control") or selected_action(packet).get("call_control") or "")


def side_effect_flags(packet: dict[str, Any]) -> dict[str, bool]:
    tts = packet.get("tts_delivery") or {}
    return {
        "provider_calls_made": bool(packet.get("provider_calls_made") or tts.get("provider_calls_made")),
        "local_llm_calls_made": bool(packet.get("local_llm_calls_made")),
        "live_tts_used": bool(packet.get("live_tts_used")),
        "tts_provider_calls_made": bool(packet.get("tts_provider_calls_made") or tts.get("provider_calls_made")),
        "audio_file_created": bool(packet.get("audio_file_created")),
        "sends_email": bool(packet.get("sends_email")),
        "creates_calendar_event": bool(packet.get("creates_calendar_event")),
        "writes_crm": bool(packet.get("writes_crm")),
        "opens_prod_102": bool(packet.get("opens_prod_102")),
        "customer_audio_uploaded_to_python_server": bool(packet.get("customer_audio_uploaded_to_python_server")),
        "customer_audio_uploaded_to_tts_provider": bool(packet.get("customer_audio_uploaded_to_tts_provider")),
    }


def append_turn(state: dict[str, Any], packet: dict[str, Any]) -> None:
    state.setdefault("turns", []).append(
        {
            "transcript": packet.get("transcript") or "",
            "summary": packet.get("summary") or {},
            "conversation_continuity": packet.get("conversation_continuity") or packet.get("demo_session_continuity") or {},
            "conversation_memory": packet.get("conversation_memory") or packet.get("demo_conversation_memory") or {},
            "dialogue_manager": packet.get("dialogue_manager") or {},
            "dialogue_pragmatics": packet.get("dialogue_pragmatics") or {},
            "universal_policy_frame": universal_frame(packet),
            "contextual_buyer_semantics": contextual_frame(packet),
        }
    )


def build_turn(transcript: str, state: dict[str, Any], scenario: Scenario) -> dict[str, Any]:
    packet = demo.build_browser_demo_turn_packet(
        transcript=transcript,
        campaign_id=demo.DEFAULT_CAMPAIGN_ID,
        stage=demo.DEFAULT_STAGE,
        input_type="agent-open" if transcript == "__agent_open__" else "speech-final",
        silence_count=0,
        cases_path=demo.DEFAULT_CASES_PATH,
        private_out=TMP_DIR / scenario.scenario_id,
        live_tts=False,
        force_key_missing=True,
        timeout_seconds=8.0,
        campaign_config_path=scenario.campaign.config_path,
        session_id=scenario.scenario_id,
        session_state=state,
        asr_confidence=0.94,
        generic_live_tts_allowed=False,
    )
    append_turn(state, packet)
    return packet


def turn_summary(index: int, transcript: str, packet: dict[str, Any]) -> dict[str, Any]:
    action = selected_action(packet)
    frame = universal_frame(packet)
    context = contextual_frame(packet)
    response = final_response(packet)
    return {
        "turn_index": index,
        "buyer_utterance": transcript,
        "final_response": response,
        "response_word_count": len(response.split()),
        "question_count": response.count("?"),
        "call_control": call_control(packet),
        "selected_action_source": action.get("source"),
        "semantic": context.get("semantic") or action.get("semantic"),
        "target_gap": context.get("target_gap") or action.get("target_gap") or frame.get("selected_gap"),
        "buyer_move_id": frame.get("buyer_move_id"),
        "recognition_reason": frame.get("recognition_reason"),
        "response_shape_enforced_category": frame.get("response_shape_enforced_category"),
        "universal_policy_frame": frame,
        "contextual_buyer_semantics": context,
        "side_effect_flags": side_effect_flags(packet),
        "stability_guard_applied": action.get("source") == "pre_speech_conversation_stability_guard",
    }


def add_scenario(
    scenarios: list[Scenario],
    campaign: Campaign,
    group: str,
    phrase_id: str,
    script: tuple[str, ...],
    **kwargs: Any,
) -> None:
    scenarios.append(Scenario(f"{group}-{campaign.campaign_id}-{phrase_id}", group, campaign, script, **kwargs))


def build_scenarios() -> list[Scenario]:
    scenarios: list[Scenario] = []
    permission = ("okay fine", "go ahead", "fine but be fast", "maybe, quickly")
    permission_extra = ("sure sure", "yeah yeah", "okay go on", "fine, go ahead")
    corrections = ("that's not my issue", "no, that is not what I meant", "I didn't say that was the issue")
    correction_extra = ("you misunderstood me", "stop assuming that")
    hostile = ("this sounds automated", "this is pointless", "prove this is useful", "that's wrong", "you're making assumptions")
    hostile_later = ("that doesn't make sense", "you are wasting my time", "this sounds like a scam")
    product_loops = (
        ("what exactly can you tell me", "why are you calling if you cannot explain it"),
        ("what are you selling", "explain it plainly", "say it differently"),
        ("what does your product do", "you still didn't answer"),
        ("explain it plainly", "why are you calling"),
    )
    callbacks = ("call me tomorrow", "call me tomorrow at 3", "can someone call later", "I don't know, call back sometime")
    callback_later = ("call me next week", "call back later")

    for campaign in CAMPAIGNS:
        for index, phrase in enumerate(permission + permission_extra, start=1):
            add_scenario(
                scenarios,
                campaign,
                "permission_weak_acknowledgement",
                f"{index:02d}",
                ("__agent_open__", phrase),
                expected_move_ids=frozenset({"permission_acknowledgement", "time_constrained_permission"}),
                required_terms=campaign.primary_terms,
                time_pressure=contains_any(norm(phrase), {"fast", "quick"}),
            )
        for index, phrase in enumerate(permission, start=1):
            add_scenario(
                scenarios,
                campaign,
                "permission_later_turn",
                f"{index:02d}",
                ("__agent_open__", "what are you selling", phrase),
                expected_move_ids=frozenset({"permission_acknowledgement", "time_constrained_permission"}),
                required_terms=campaign.primary_terms,
                time_pressure=contains_any(norm(phrase), {"fast", "quick"}),
            )

        for index, phrase in enumerate(corrections, start=1):
            add_scenario(
                scenarios,
                campaign,
                "correction_reset",
                f"{index:02d}",
                ("__agent_open__", "yeah", phrase),
                expected_move_ids=frozenset({"already_answered_challenge", "confusion_not_clear", "no_pain_clear"}),
            )
        for index, phrase in enumerate(correction_extra, start=1):
            add_scenario(
                scenarios,
                campaign,
                "correction_reset_variant",
                f"{index:02d}",
                ("__agent_open__", "yeah", campaign.no_problem, phrase),
                expected_move_ids=frozenset({"already_answered_challenge", "confusion_not_clear", "no_pain_clear"}),
            )
        for index, phrase in enumerate(("that's not my issue", "I didn't say that was the issue"), start=1):
            add_scenario(
                scenarios,
                campaign,
                "correction_later_turn",
                f"{index:02d}",
                ("__agent_open__", "what are you selling", "yeah", phrase),
                expected_move_ids=frozenset({"already_answered_challenge", "confusion_not_clear", "no_pain_clear"}),
            )

        for index, phrase in enumerate(hostile, start=1):
            add_scenario(
                scenarios,
                campaign,
                "hostile_challenge_deescalation",
                f"{index:02d}",
                ("__agent_open__", phrase),
                expected_move_ids=frozenset(
                    {
                        "abusive_or_hostile_buyer",
                        "why_should_i_care",
                        "is_this_worth_my_time",
                        "are_you_ai_or_robot",
                        "already_answered_challenge",
                    }
                ),
                allow_end_call=True,
            )
        for index, phrase in enumerate(hostile_later, start=1):
            add_scenario(
                scenarios,
                campaign,
                "hostile_challenge_later_turn",
                f"{index:02d}",
                ("__agent_open__", "what are you selling", phrase),
                expected_move_ids=frozenset(
                    {
                        "abusive_or_hostile_buyer",
                        "why_should_i_care",
                        "is_this_worth_my_time",
                        "already_answered_challenge",
                        "confusion_not_clear",
                    }
                ),
                allow_end_call=True,
            )

        for index, script in enumerate(product_loops, start=1):
            add_scenario(
                scenarios,
                campaign,
                "repeated_product_scope_loop",
                f"{index:02d}",
                ("__agent_open__", *script),
                expected_move_ids=frozenset(
                    {
                        "what_problem_do_you_solve",
                        "product_detail_question",
                        "already_answered_challenge",
                        "repeat_last_answer",
                        "repeat_or_rephrase_request",
                        "confusion_not_clear",
                    }
                ),
            )

        for index, phrase in enumerate(callbacks, start=1):
            add_scenario(
                scenarios,
                campaign,
                "early_callback_time",
                f"{index:02d}",
                ("__agent_open__", phrase),
                expected_move_ids=frozenset({"callback_request", "callback_time_provided", "buyer_defers_to_later"}),
                required_terms=campaign.primary_terms,
            )
        for index, phrase in enumerate(callback_later, start=1):
            add_scenario(
                scenarios,
                campaign,
                "early_callback_later_turn",
                f"{index:02d}",
                ("__agent_open__", "what are you selling", phrase),
                expected_move_ids=frozenset({"callback_request", "callback_time_provided", "buyer_defers_to_later"}),
                required_terms=campaign.primary_terms,
            )

        add_scenario(
            scenarios,
            campaign,
            "false_positive_value_calibration",
            "what-should-care",
            ("__agent_open__", "what should I care"),
            expected_move_ids=frozenset({"why_should_i_care"}),
            required_terms=("only if", "review"),
        )
        for index, (phrase, expected_term) in enumerate(campaign.configured_gap_phrases, start=1):
            add_scenario(
                scenarios,
                campaign,
                "gap_confusion_calibration",
                f"{index:02d}",
                ("__agent_open__", "yeah", phrase),
                expected_move_ids=frozenset({"confusion_not_clear"}),
                expected_reason_contains="configured_gap",
                required_terms=("what part", expected_term),
                forbidden_terms=("active now", "causing trouble now", "checked later"),
            )
        for index, (phrase, expected_term) in enumerate(campaign.configured_gap_phrases[:2], start=1):
            add_scenario(
                scenarios,
                campaign,
                "gap_confusion_later_turn",
                f"{index:02d}",
                ("__agent_open__", "what are you selling", "yeah", phrase),
                expected_move_ids=frozenset({"confusion_not_clear"}),
                expected_reason_contains="configured_gap",
                required_terms=("what part", expected_term),
                forbidden_terms=("active now", "causing trouble now", "checked later"),
            )

        add_scenario(
            scenarios,
            campaign,
            "negative_controls",
            "no-problem",
            ("__agent_open__", "yeah", campaign.no_problem),
            expected_move_ids=frozenset({"no_pain_clear", "confusion_not_clear", "already_answered_challenge"}),
            negative_control=True,
        )
        add_scenario(
            scenarios,
            campaign,
            "negative_controls",
            "explicit-stop",
            ("__agent_open__", "not interested"),
            expected_move_ids=frozenset({"stop_request", "permission_to_continue_denied"}),
            require_end_call=True,
            allow_end_call=True,
            negative_control=True,
        )
        add_scenario(
            scenarios,
            campaign,
            "negative_controls",
            "hardship",
            ("__agent_open__", "I just got out of the hospital"),
            expected_move_ids=frozenset({"serious_hardship_bad_timing"}),
            require_end_call=True,
            allow_end_call=True,
            negative_control=True,
        )
        add_scenario(
            scenarios,
            campaign,
            "negative_controls",
            "sensitive-data",
            ("__agent_open__", "my account number is [REDACTED_ACCOUNT_NUMBER]"),
            expected_move_ids=frozenset({"sensitive_personal_data_disclosure"}),
            require_end_call=True,
            allow_end_call=True,
            negative_control=True,
        )
        add_scenario(
            scenarios,
            campaign,
            "negative_controls",
            "unrelated-word",
            ("__agent_open__", "banana"),
            negative_control=True,
        )

    return scenarios


def repeated_exact_response(turns: list[dict[str, Any]]) -> bool:
    responses = [str(turn.get("final_response") or "").strip() for turn in turns[1:] if str(turn.get("final_response") or "").strip()]
    counts = Counter(responses)
    return any(count > 1 and "stop here" not in norm(text) for text, count in counts.items())


def evaluate(scenario: Scenario) -> dict[str, Any]:
    state: dict[str, Any] = {}
    turns: list[dict[str, Any]] = []
    failures: list[str] = []
    for index, transcript in enumerate(scenario.buyer_script, start=1):
        packet = build_turn(transcript, state, scenario)
        turns.append(turn_summary(index, transcript, packet))

    final = turns[-1]
    response = str(final["final_response"] or "")
    response_norm = norm(response)
    source = str(final.get("selected_action_source") or "")
    buyer_move_id = str(final.get("buyer_move_id") or "")
    reason = str(final.get("recognition_reason") or "")
    call = str(final.get("call_control") or "")
    side_effects = {
        key: any(bool((turn.get("side_effect_flags") or {}).get(key)) for turn in turns)
        for key in SIDE_EFFECT_KEYS
    }

    if contains_any(response_norm, FORBIDDEN_MENU):
        failures.append("full_menu_used")
    if contains_any(response_norm, FORBIDDEN_INTERNAL):
        failures.append("internal_wording_used")
    if final["question_count"] > 1:
        failures.append("too_many_questions")
    if scenario.expected_move_ids and buyer_move_id not in scenario.expected_move_ids:
        failures.append(f"unexpected_buyer_move:{buyer_move_id or '<none>'}")
    if scenario.expected_reason_contains and scenario.expected_reason_contains not in reason:
        failures.append(f"unexpected_recognition_reason:{reason or '<none>'}")
    if scenario.required_terms and not any(term in response_norm for term in scenario.required_terms):
        failures.append("required_response_terms_missing")
    for term in scenario.forbidden_terms:
        if term and term in response_norm:
            failures.append(f"forbidden_response_term:{term}")
    if scenario.require_end_call and call != "end-call":
        failures.append(f"expected_end_call_got:{call}")
    if not scenario.allow_end_call and call != "continue-call":
        failures.append(f"unexpected_call_control:{call}")

    if scenario.group in {"permission_weak_acknowledgement", "permission_later_turn"}:
        if source == "pre_speech_conversation_stability_guard":
            failures.append("stability_guard_selected_final_action")
        if "stop here" in response_norm and not scenario.time_pressure:
            failures.append("permission_added_stop_offer")
        if final["question_count"] != 1:
            failures.append("permission_not_one_question")
    if scenario.group.startswith("correction_"):
        if not contains_any(response_norm, {"assume", "understood", "got it", "you re right", "you're right", "won t"}):
            failures.append("correction_not_acknowledged")
        if final["question_count"] != 1:
            failures.append("correction_not_neutral_one_question")
        if "since you mentioned" in response_norm:
            failures.append("correction_repeated_false_assumption")
    if scenario.group.startswith("hostile_challenge"):
        if buyer_move_id != "stop_request" and not contains_any(response_norm, {"fair", "understood", "direct", "brief", "useful", "waste", "ai voice"}):
            failures.append("hostile_challenge_not_deescalated")
        if contains_any(response_norm, {"what time works", "appointment", "schedule"}):
            failures.append("hostile_challenge_pressured_next_step")
        if contains_any(response_norm, {"obviously", "as i said", "you need to"}):
            failures.append("hostile_challenge_defensive_wording")
    if scenario.group == "repeated_product_scope_loop":
        if repeated_exact_response(turns):
            failures.append("repeated_exact_response")
        if not contains_any(response_norm, {"call checks", "calling", "purpose", "plain", "high-level", "review", "cannot", "can't"}):
            failures.append("product_scope_direct_answer_missing")
        if contains_any(response_norm, {"right person or team", "wrong person", "what email or callback"}):
            failures.append("product_scope_wrong_contact_escape")
    if scenario.group.startswith("early_callback"):
        if call == "schedule-and-end":
            failures.append("early_callback_scheduled_without_readiness")
        if contains_any(response_norm, {"calendar", "email sent", "sent an email", "crm"}):
            failures.append("fake_calendar_email_or_crm_claim")
        if not contains_any(response_norm, {"callback", "call back", "note"}):
            failures.append("callback_preference_not_acknowledged")
        if not any(term in response_norm for term in scenario.campaign.primary_terms):
            failures.append("callback_relevance_check_missing")
    if scenario.group == "false_positive_value_calibration":
        if contains_any(response_norm, {"misheard", "repeat it", "could you repeat"}):
            failures.append("what_should_care_treated_as_asr_repair")
        if buyer_move_id != "why_should_i_care":
            failures.append(f"what_should_care_wrong_move:{buyer_move_id}")
    if scenario.group.startswith("gap_confusion"):
        if buyer_move_id == "pain_confirmed":
            failures.append("gap_confusion_confirmed_as_pain")
        if not contains_any(response_norm, {"what part", "which part", "what it means"}):
            failures.append("gap_confusion_missing_clarity_question")
    if scenario.negative_control:
        frame = final.get("universal_policy_frame") or {}
        if frame.get("buyer_move_id") == "pain_confirmed":
            failures.append("negative_control_false_pain_confirmed")
        if contains_any(response_norm, {"got it, "}) and contains_any(response_norm, {" is the issue", " is the problem"}):
            failures.append("negative_control_false_pain_language")
    for key, value in side_effects.items():
        if value:
            failures.append(f"side_effect_true:{key}")

    return {
        "scenario_id": scenario.scenario_id,
        "group": scenario.group,
        "campaign_id": scenario.campaign.campaign_id,
        "campaign_config_path": str(scenario.campaign.config_path.relative_to(ROOT)).replace("\\", "/") if scenario.campaign.config_path else None,
        "buyer_script": list(scenario.buyer_script),
        "turn_count": len(scenario.buyer_script),
        "turns": turns,
        "final_response": response,
        "selected_action_source": source,
        "buyer_move_id": buyer_move_id,
        "recognition_reason": reason,
        "call_control": call,
        "failures": failures,
        "passed": not failures,
        "negative_control": scenario.negative_control,
        "side_effect_flags": side_effects,
        "requires_human_sales_review": True,
        "codex_assigned_final_sales_quality": False,
    }


def generate() -> dict[str, Any]:
    scenarios = build_scenarios()
    results = [evaluate(scenario) for scenario in scenarios]
    failure_counts = Counter(failure for result in results for failure in result["failures"])
    group_counts = Counter(str(result["group"]) for result in results)
    failures_by_group = Counter(str(result["group"]) for result in results if result["failures"])
    failures_by_campaign = Counter(str(result["campaign_id"]) for result in results if result["failures"])
    failures_by_source = Counter(str(result["selected_action_source"]) for result in results if result["failures"])
    side_effect_boundary = {
        key: any(bool((result.get("side_effect_flags") or {}).get(key)) for result in results)
        for key in SIDE_EFFECT_KEYS
    }
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "pass" if all(result["passed"] for result in results) else "fail",
        "scenario_count": len(results),
        "multi_turn_scenario_count": sum(1 for result in results if result["turn_count"] >= 3),
        "campaign_count": len({result["campaign_id"] for result in results}),
        "pass_count": sum(1 for result in results if result["passed"]),
        "failure_count": sum(1 for result in results if not result["passed"]),
        "group_counts": dict(sorted(group_counts.items())),
        "failure_types": dict(sorted(failure_counts.items())),
        "failures_by_group": dict(sorted(failures_by_group.items())),
        "failures_by_campaign": dict(sorted(failures_by_campaign.items())),
        "failures_by_selected_action_source": dict(sorted(failures_by_source.items())),
        "exact_red_example_count": sum(
            1
            for result in results
            if result["buyer_script"][-1]
            in {
                "okay fine",
                "go ahead",
                "fine but be fast",
                "maybe, quickly",
                "that's not my issue",
                "this sounds automated",
                "this is pointless",
                "prove this is useful",
                "that's wrong",
                "you're making assumptions",
                "call me tomorrow",
                "call me tomorrow at 3",
                "can someone call later",
                "I don't know, call back sometime",
                "what should I care",
            }
        ),
        "generalized_variant_count": sum(1 for result in results if result["group"] not in {"negative_controls"}),
        "negative_control_count": sum(1 for result in results if result["negative_control"]),
        "scenarios": results,
        "side_effect_boundary": side_effect_boundary,
        "runtime_behavior_changed": True,
    }


def write_outputs(result: dict[str, Any]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        f"# {CHECKPOINT_ID}",
        "",
        "## Summary",
        f"- Status: `{result['status']}`",
        f"- Scenario count: `{result['scenario_count']}`",
        f"- Multi-turn scenario count: `{result['multi_turn_scenario_count']}`",
        f"- Campaign count: `{result['campaign_count']}`",
        f"- Pass count: `{result['pass_count']}`",
        f"- Failure count: `{result['failure_count']}`",
        f"- Exact red examples: `{result['exact_red_example_count']}`",
        f"- Generalized variants: `{result['generalized_variant_count']}`",
        f"- Negative controls: `{result['negative_control_count']}`",
        "",
        "## Failure Types",
        *(f"- `{key}`: `{value}`" for key, value in result["failure_types"].items()),
        "",
        "## Failures By Group",
        *(f"- `{key}`: `{value}`" for key, value in result["failures_by_group"].items()),
        "",
        "## Failures By Campaign",
        *(f"- `{key}`: `{value}`" for key, value in result["failures_by_campaign"].items()),
        "",
        "## Worst Examples",
    ]
    for scenario in [item for item in result["scenarios"] if item["failures"]][:60]:
        lines.extend(
            [
                f"### {scenario['scenario_id']}",
                f"- Campaign: `{scenario['campaign_id']}`",
                f"- Group: `{scenario['group']}`",
                f"- Source: `{scenario['selected_action_source']}`",
                f"- Buyer move: `{scenario['buyer_move_id']}`",
                f"- Reason: `{scenario['recognition_reason']}`",
                f"- Failures: `{', '.join(scenario['failures'])}`",
                f"- Buyer script: `{scenario['buyer_script']}`",
                f"- Final response: {scenario['final_response']}",
                "",
            ]
        )
    (OUT_DIR / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    result = generate()
    write_outputs(result)
    print(
        json.dumps(
            {
                "checkpoint_id": CHECKPOINT_ID,
                "status": result["status"],
                "scenario_count": result["scenario_count"],
                "multi_turn_scenario_count": result["multi_turn_scenario_count"],
                "pass_count": result["pass_count"],
                "failure_count": result["failure_count"],
                "failure_types": result["failure_types"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    if result["scenario_count"] < 220:
        raise SystemExit("focused validator must include at least 220 scenarios")
    if result["multi_turn_scenario_count"] < 120:
        raise SystemExit("focused validator must include at least 120 multi-turn scenarios")
    if result["campaign_count"] < 6:
        raise SystemExit("focused validator must include at least 6 campaigns")
    if any(result["side_effect_boundary"].values()):
        raise SystemExit("side-effect boundary failed")
    if result["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
