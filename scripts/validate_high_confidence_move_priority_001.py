#!/usr/bin/env python3
"""Validate that high-confidence buyer moves outrank fallback stability repairs."""

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


CHECKPOINT_ID = "HIGH-CONFIDENCE-MOVE-PRIORITY-001"
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
    "name the point",
]

FORBIDDEN_MENU_SCOPE_LISTS = [
    "manual tracking or missed callbacks",
    "premium or budget, coverage fit, or renewal",
    "plan fit, coverage or availability, or contract or switching",
    "manual work, integration, or visibility",
    "vehicle issue, repair timing, or warranty",
]

MENU_PROMPT_TERMS = [
    "which part",
    "what part",
    "name the point",
    "check first",
    "choose",
    "pick",
]

FORBIDDEN_INTERNAL = [
    "approved qualified reviewer path",
    "approved scope",
    "internal policy",
    "transfer-or-escalate",
    "i should not",
    "i may not be the right contact",
    "would it help if i first explain",
    "route this to a specialist instead of continuing automatically",
]

DIRECT_MOVE_IDS = {
    "product_detail_question",
    "what_problem_do_you_solve",
    "why_should_i_care",
    "explain_plainly_request",
    "one_sentence_request",
    "scope_limit_question",
}

CHALLENGE_MOVE_IDS = {
    "already_answered_challenge",
    "buyer_says_agent_wrong",
    "buyer_says_agent_not_listening",
    "false_assumption_correction",
}

MISMATCH_MOVE_IDS = {
    "out_of_campaign_relevance_challenge",
    "campaign_mismatch_question",
    "confusion_not_clear",
    "scope_limit_question",
}

WHY_HUMAN_MOVE_IDS = {
    "why_human_review",
    "scope_limit_question",
    "why_are_you_asking",
}


@dataclass(frozen=True)
class Campaign:
    campaign_id: str
    config_path: Path | None
    primary_issue: str
    false_issue: str
    pain: str
    impact: str
    near_misses: tuple[tuple[str, str, tuple[str, ...]], ...]
    negative_controls: tuple[str, ...]
    out_of_campaign_request: str


@dataclass(frozen=True)
class Scenario:
    scenario_id: str
    group: str
    campaign: Campaign
    buyer_script: tuple[str, ...]
    expected_move_ids: frozenset[str]
    expected_gap: str | None = None
    expected_terms: tuple[str, ...] = ()
    forbidden_response_terms: tuple[str, ...] = ()
    require_end_call: bool = False
    allow_terminal: bool = False
    negative_control: bool = False


CAMPAIGNS = [
    Campaign(
        "routesignal_live_demo",
        None,
        "inbound demo follow-up",
        "callbacks",
        "callbacks are a problem",
        "it causes delays",
        (
            ("call bags are a problem", "callbacks", ("callback",)),
            ("call backs are the problem", "callbacks", ("callback",)),
            ("hand offs are messy", "handoffs", ("handoff",)),
            ("manual truck tracking is a problem", "manual_tracking", ("manual", "tracking")),
        ),
        ("premium pressure is a problem", "repair timing is confusing"),
        "I need insurance coverage",
    ),
    Campaign(
        "synthetic-insurance-review",
        EXAMPLES / "synthetic-insurance-review.json",
        "premium pressure",
        "premium",
        "premium is a problem",
        "it wastes time",
        (
            ("premon pressure is a problem", "premium_or_budget", ("premium", "budget", "payment")),
            ("payment pressure is a problem", "premium_or_budget", ("premium", "budget", "payment")),
            ("cover fit is the issue", "coverage_fit", ("coverage",)),
            ("coverage thing is confusing", "coverage_fit", ("coverage",)),
        ),
        ("manual tracking is a problem", "repair timing is confusing"),
        "callbacks are a problem",
    ),
    Campaign(
        "synthetic-telecom-plan-review",
        EXAMPLES / "synthetic-telecom-plan-review.json",
        "plan fit",
        "plan fit",
        "plan fit is a problem",
        "customers wait",
        (
            ("plane fit is a problem", "plan_fit", ("plan",)),
            ("plane fit is confusing", "plan_fit", ("plan",)),
            ("cover availability is the issue", "coverage_or_availability", ("coverage", "availability")),
            ("contact switching is confusing", "contract_or_switching", ("contract", "switching")),
        ),
        ("repair timing is a problem", "premium pressure is confusing"),
        "repair timing is the issue",
    ),
    Campaign(
        "synthetic-automotive-service-review",
        EXAMPLES / "synthetic-automotive-service-review.json",
        "repair timing",
        "repair timing",
        "repair timings are usually pretty long",
        "it slows us down",
        (
            ("repair timings are a problem", "repair_timing", ("repair", "timing")),
            ("repair time is the issue", "repair_timing", ("repair", "timing")),
            ("warranty estimate thing is confusing", "warranty_or_estimate", ("warranty", "estimate")),
            ("repair schedule is a problem", "repair_timing", ("repair", "schedule")),
        ),
        ("plan fit is a problem", "premium pressure is confusing"),
        "plan fit is the issue",
    ),
    Campaign(
        "synthetic-membership-plan-review",
        EXAMPLES / "synthetic-membership-plan-review.json",
        "plan fit",
        "plan fit",
        "plan fit is a problem",
        "it costs money",
        (
            ("membership level is wrong", "plan_fit", ("membership", "plan", "fit")),
            ("cancel timing is confusing", "renewal_or_cancellation", ("cancel", "timing")),
            ("usage thing is unclear", "usage_or_value", ("usage",)),
            ("plan thing is a problem", "plan_fit", ("plan",)),
        ),
        ("repair timing is a problem", "premium pressure is confusing"),
        "warranty estimate is the issue",
    ),
    Campaign(
        "synthetic-b2b-saas-operations",
        EXAMPLES / "synthetic-b2b-saas-operations.json",
        "manual work",
        "manual work",
        "manual work is a problem",
        "it wastes time",
        (
            ("manual trucking is a problem", "manual_work", ("manual", "work", "tracking")),
            ("manual tracking is a problem", "manual_work", ("manual", "work", "tracking")),
            ("integration thing is confusing", "integration_risk", ("integration",)),
            ("visibility thing is unclear", "visibility_gap", ("visibility",)),
        ),
        ("premium pressure is a problem", "repair timing is confusing"),
        "cancellation terms are the issue",
    ),
]


def norm(text: Any) -> str:
    return " ".join(str(text or "").lower().replace("'", " ").split())


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


def scenario_turn_summary(index: int, transcript: str, packet: dict[str, Any]) -> dict[str, Any]:
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
        "target_gap": context.get("target_gap") or action.get("target_gap"),
        "buyer_move_id": frame.get("buyer_move_id"),
        "buyer_move_category": frame.get("buyer_move_category"),
        "recognition_reason": frame.get("recognition_reason"),
        "recognition_confidence": frame.get("recognition_confidence"),
        "response_shape_enforced_category": frame.get("response_shape_enforced_category"),
        "high_confidence_move_priority_protected": frame.get("high_confidence_move_priority_protected"),
        "universal_policy_frame": frame,
        "contextual_buyer_semantics": context,
        "side_effect_flags": side_effect_flags(packet),
        "stability_guard_applied": action.get("source") == "pre_speech_conversation_stability_guard",
    }


def contains_any(text: str, patterns: list[str] | tuple[str, ...] | set[str]) -> bool:
    return any(pattern in text for pattern in patterns)


def looks_like_forbidden_menu(text: str) -> bool:
    if contains_any(text, FORBIDDEN_MENU):
        return True
    return contains_any(text, FORBIDDEN_MENU_SCOPE_LISTS) and contains_any(text, MENU_PROMPT_TERMS)


def response_has_answer(text: str) -> bool:
    return contains_any(
        text,
        {
            "this call",
            "checks",
            "checking",
            "review",
            "specialist",
            "direct answer",
            "in one sentence",
            "because",
            "scope",
            "useful",
            "value",
            "helps",
            "avoid",
            "fit check",
            "crm workflow tool",
        },
    )


def evaluate(scenario: Scenario) -> dict[str, Any]:
    state: dict[str, Any] = {}
    turns: list[dict[str, Any]] = []
    failures: list[str] = []
    for index, transcript in enumerate(scenario.buyer_script, start=1):
        packet = build_turn(transcript, state, scenario)
        turns.append(scenario_turn_summary(index, transcript, packet))

    final = turns[-1]
    response_norm = norm(final["final_response"])
    source = str(final.get("selected_action_source") or "")
    buyer_move_id = str(final.get("buyer_move_id") or "")
    semantic = str(final.get("semantic") or "")
    target_gap = str(final.get("target_gap") or "")
    frame = final.get("universal_policy_frame") or {}
    frame_gap = str(frame.get("selected_gap") or frame.get("confirmed_gap_id") or "")
    side_effects = {
        key: any(bool((turn.get("side_effect_flags") or {}).get(key)) for turn in turns)
        for key in SIDE_EFFECT_KEYS
    }

    if looks_like_forbidden_menu(response_norm):
        failures.append("full_menu_or_point_picker_used")
    if contains_any(response_norm, FORBIDDEN_INTERNAL):
        failures.append("internal_or_legacy_fallback_wording_used")
    if source == "pre_speech_conversation_stability_guard":
        failures.append("stability_guard_selected_final_action")
    if source == "live_voice_session_policy" and scenario.group in {
        "direct_explanation_priority",
        "why_human_review",
        "agent_wrong_not_listening",
        "out_of_campaign_mismatch",
        "later_turn_priority",
    }:
        failures.append("live_policy_fallback_selected_for_protected_move")
    if final["question_count"] > 1:
        failures.append("too_many_questions")
    if not scenario.allow_terminal and final["call_control"] not in {"continue-call"}:
        failures.append(f"unexpected_call_control:{final['call_control']}")
    if scenario.require_end_call and final["call_control"] != "end-call":
        failures.append(f"expected_end_call_got:{final['call_control']}")
    if scenario.expected_move_ids and buyer_move_id not in scenario.expected_move_ids:
        failures.append(f"unexpected_buyer_move:{buyer_move_id or '<none>'}")
    if scenario.expected_gap and not scenario.negative_control and scenario.expected_gap not in {target_gap, frame_gap}:
        failures.append(f"expected_gap_not_preserved:{scenario.expected_gap}")
    if scenario.expected_terms and not any(term in response_norm for term in scenario.expected_terms):
        failures.append("response_does_not_reference_expected_terms")
    for forbidden in scenario.forbidden_response_terms:
        if forbidden in response_norm:
            failures.append(f"forbidden_response_term:{forbidden}")
    if scenario.group in {"direct_explanation_priority", "why_human_review", "later_turn_priority"} and not response_has_answer(response_norm):
        failures.append("direct_question_not_answered")
    if scenario.group == "agent_wrong_not_listening" and not contains_any(
        response_norm,
        {"right", "understood", "won t assume", "won't assume", "let me reset", "direct answer", "fair", "got it"},
    ):
        failures.append("critique_or_correction_not_acknowledged")
    if scenario.group == "out_of_campaign_mismatch" and not contains_any(
        response_norm,
        {"this call", "campaign", "not", scenario.campaign.primary_issue.lower()},
    ):
        failures.append("mismatch_scope_not_explained")
    if scenario.group == "asr_near_miss_generalization" and not scenario.negative_control:
        if not (scenario.expected_gap in {target_gap, frame_gap} or any(term in response_norm for term in scenario.expected_terms)):
            failures.append(f"near_miss_not_mapped_or_clarified:{scenario.expected_gap}")
    if scenario.negative_control:
        if str(frame.get("buyer_move_id") or "") == "pain_confirmed":
            failures.append("negative_control_false_pain_confirmed")
        if scenario.expected_gap and scenario.expected_gap in {target_gap, frame_gap}:
            failures.append(f"negative_control_cross_campaign_gap_matched:{scenario.expected_gap}")
    for key, value in side_effects.items():
        if value:
            failures.append(f"side_effect_true:{key}")

    return {
        "scenario_id": scenario.scenario_id,
        "group": scenario.group,
        "campaign_id": scenario.campaign.campaign_id,
        "campaign_config_path": str(scenario.campaign.config_path.relative_to(ROOT)).replace("\\", "/") if scenario.campaign.config_path else None,
        "buyer_script": list(scenario.buyer_script),
        "expected_move_ids": sorted(scenario.expected_move_ids),
        "expected_gap": scenario.expected_gap,
        "negative_control": scenario.negative_control,
        "turns": turns,
        "final_response": final["final_response"],
        "selected_action_source": source,
        "buyer_move_id": buyer_move_id,
        "semantic": semantic,
        "target_gap": target_gap or frame_gap,
        "call_control": final["call_control"],
        "failures": failures,
        "passed": not failures,
        "side_effect_flags": side_effects,
        "requires_human_sales_review": True,
        "codex_assigned_final_sales_quality": False,
    }


def build_scenarios() -> list[Scenario]:
    scenarios: list[Scenario] = []
    for campaign in CAMPAIGNS:
        direct_scripts = [
            ("what-are-you-selling", ("__agent_open__", "what are you selling")),
            ("explain-plainly", ("__agent_open__", "what are you selling", "explain it plainly")),
            ("one-sentence", ("__agent_open__", "what are you selling", "explain it plainly", "say it in one sentence")),
            ("plain-paraphrase", ("__agent_open__", "what is this", "no, explain it plainly")),
        ]
        for suffix, script in direct_scripts:
            scenarios.append(
                Scenario(
                    f"direct-{campaign.campaign_id}-{suffix}",
                    "direct_explanation_priority",
                    campaign,
                    script,
                    frozenset(DIRECT_MOVE_IDS),
                    expected_terms=(campaign.primary_issue.split()[0].lower(), "review"),
                )
            )

        human_review_scripts = [
            ("why-human-review", ("__agent_open__", "why do I need a human review")),
            ("what-will-they-do", ("__agent_open__", "what will they do that you can't")),
            ("why-cant-you-tell", ("__agent_open__", "why can't you just tell me")),
        ]
        for suffix, script in human_review_scripts:
            scenarios.append(
                Scenario(
                    f"why-human-{campaign.campaign_id}-{suffix}",
                    "why_human_review",
                    campaign,
                    script,
                    frozenset(WHY_HUMAN_MOVE_IDS),
                    expected_terms=("review",),
                )
            )

        correction_scripts = [
            ("not-what-said", ("__agent_open__", "yeah", campaign.pain, "that is not what I said")),
            ("stop-assuming", ("__agent_open__", "yeah", campaign.pain, "stop assuming that")),
            ("not-listening", ("__agent_open__", "yeah", campaign.pain, "you are not listening")),
            ("looping", ("__agent_open__", "yeah", campaign.pain, "you keep repeating yourself")),
        ]
        for suffix, script in correction_scripts:
            scenarios.append(
                Scenario(
                    f"critique-{campaign.campaign_id}-{suffix}",
                    "agent_wrong_not_listening",
                    campaign,
                    script,
                    frozenset(CHALLENGE_MOVE_IDS),
                    forbidden_response_terms=(f"since you mentioned {campaign.false_issue.lower()}",),
                )
            )

        mismatch_scripts = [
            ("other-request", ("__agent_open__", campaign.out_of_campaign_request)),
            ("why-else", ("__agent_open__", campaign.out_of_campaign_request, "why are you talking about something else")),
        ]
        for suffix, script in mismatch_scripts:
            scenarios.append(
                Scenario(
                    f"mismatch-{campaign.campaign_id}-{suffix}",
                    "out_of_campaign_mismatch",
                    campaign,
                    script,
                    frozenset(MISMATCH_MOVE_IDS),
                    expected_terms=(campaign.primary_issue.split()[0].lower(),),
                )
            )

        for index, (utterance, expected_gap, terms) in enumerate(campaign.near_misses, start=1):
            scenarios.append(
                Scenario(
                    f"near-miss-{campaign.campaign_id}-{index}",
                    "asr_near_miss_generalization",
                    campaign,
                    ("__agent_open__", "yeah", utterance),
                    frozenset({"pain_confirmed", "tentative_gap_interest", "confusion_not_clear"}),
                    expected_gap=expected_gap,
                    expected_terms=terms,
                )
            )
            scenarios.append(
                Scenario(
                    f"near-miss-impact-{campaign.campaign_id}-{index}",
                    "asr_near_miss_generalization",
                    campaign,
                    ("__agent_open__", "yeah", utterance, campaign.impact),
                    frozenset({"pain_confirmed", "tentative_gap_interest", "implication_confirmed", "confusion_not_clear"}),
                    expected_gap=expected_gap,
                    expected_terms=terms,
                )
            )

        for index, utterance in enumerate(campaign.negative_controls, start=1):
            scenarios.append(
                Scenario(
                    f"negative-control-{campaign.campaign_id}-{index}",
                    "asr_near_miss_generalization",
                    campaign,
                    ("__agent_open__", "yeah", utterance),
                    frozenset({"confusion_not_clear", "scope_limit_question", "irrelevant_off_topic_context", "pain_confirmed"}),
                    expected_gap=campaign.near_misses[0][1],
                    negative_control=True,
                )
            )

        later_turn_scripts = [
            ("still-didnt-answer", ("__agent_open__", "yeah", "what does your product do", "explain it plainly", "you still didn't answer")),
            ("later-one-sentence", ("__agent_open__", "yeah", "what does your product do", "explain it plainly", "you still didn't answer", "say it in one sentence")),
            ("why-care-later", ("__agent_open__", "yeah", "what does your product do", "okay but why should I care")),
        ]
        for suffix, script in later_turn_scripts:
            scenarios.append(
                Scenario(
                    f"later-turn-{campaign.campaign_id}-{suffix}",
                    "later_turn_priority",
                    campaign,
                    script,
                    frozenset(DIRECT_MOVE_IDS | CHALLENGE_MOVE_IDS | {"why_should_i_care"}),
                    expected_terms=(
                        campaign.primary_issue.split()[0].lower(),
                        "review",
                        "value",
                        "fit",
                        "follow-up",
                        "replies",
                        "details",
                        "estimate",
                    ),
                )
            )

    preservation_campaign = CAMPAIGNS[0]
    scenarios.extend(
        [
            Scenario(
                "preserve-stop-refusal",
                "preservation",
                preservation_campaign,
                ("__agent_open__", "stop calling"),
                frozenset({"stop_request", "permission_to_continue_denied"}),
                require_end_call=True,
                allow_terminal=True,
            ),
            Scenario(
                "preserve-hardship",
                "preservation",
                preservation_campaign,
                ("__agent_open__", "I just got out of the hospital"),
                frozenset({"serious_hardship_bad_timing"}),
                require_end_call=True,
                allow_terminal=True,
            ),
            Scenario(
                "preserve-sensitive-data",
                "preservation",
                preservation_campaign,
                ("__agent_open__", "my account number is [REDACTED_ACCOUNT_NUMBER]"),
                frozenset({"sensitive_personal_data_disclosure"}),
                require_end_call=True,
                allow_terminal=True,
            ),
            Scenario(
                "preserve-callback-time",
                "preservation",
                preservation_campaign,
                ("__agent_open__", "yeah", "callbacks are a problem", "it causes delays", "tomorrow at 3 works"),
                frozenset({"callback_time_provided", "implication_confirmed"}),
                allow_terminal=True,
            ),
        ]
    )
    return scenarios


def generate() -> dict[str, Any]:
    scenario_results = [evaluate(scenario) for scenario in build_scenarios()]
    failure_counts = Counter(failure for scenario in scenario_results for failure in scenario["failures"])
    group_counts = Counter(str(scenario["group"]) for scenario in scenario_results)
    failures_by_group = Counter(str(scenario["group"]) for scenario in scenario_results if scenario["failures"])
    failures_by_campaign = Counter(str(scenario["campaign_id"]) for scenario in scenario_results if scenario["failures"])
    failures_by_source = Counter(str(scenario["selected_action_source"]) for scenario in scenario_results if scenario["failures"])
    result = {
        "checkpoint_id": CHECKPOINT_ID,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "pass" if all(scenario["passed"] for scenario in scenario_results) else "fail",
        "scenario_count": len(scenario_results),
        "multi_turn_scenario_count": sum(1 for scenario in scenario_results if len(scenario["buyer_script"]) >= 3),
        "campaign_count": len({scenario["campaign_id"] for scenario in scenario_results}),
        "pass_count": sum(1 for scenario in scenario_results if scenario["passed"]),
        "failure_count": sum(1 for scenario in scenario_results if not scenario["passed"]),
        "failure_types": dict(sorted(failure_counts.items())),
        "group_counts": dict(sorted(group_counts.items())),
        "failures_by_group": dict(sorted(failures_by_group.items())),
        "failures_by_campaign": dict(sorted(failures_by_campaign.items())),
        "failures_by_selected_action_source": dict(sorted(failures_by_source.items())),
        "exact_scripted_case_count": sum(1 for scenario in scenario_results if scenario["scenario_id"].endswith(("one-sentence", "why-human-review", "why-else"))),
        "negative_control_count": sum(1 for scenario in scenario_results if scenario["negative_control"]),
        "scenarios": scenario_results,
        "side_effect_boundary": {
            key: any(bool((scenario.get("side_effect_flags") or {}).get(key)) for scenario in scenario_results)
            for key in SIDE_EFFECT_KEYS
        },
        "runtime_behavior_changed": True,
    }
    return result


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
        f"- Negative controls: `{result['negative_control_count']}`",
        "",
        "## Failure Types",
        *(f"- `{key}`: `{value}`" for key, value in result["failure_types"].items()),
        "",
        "## Failures By Group",
        *(f"- `{key}`: `{value}`" for key, value in result["failures_by_group"].items()),
        "",
        "## Failures By Selected Action Source",
        *(f"- `{key}`: `{value}`" for key, value in result["failures_by_selected_action_source"].items()),
        "",
        "## Worst Examples",
    ]
    failing = [scenario for scenario in result["scenarios"] if scenario["failures"]]
    for scenario in failing[:30]:
        lines.extend(
            [
                f"### {scenario['scenario_id']}",
                f"- Campaign: `{scenario['campaign_id']}`",
                f"- Group: `{scenario['group']}`",
                f"- Source: `{scenario['selected_action_source']}`",
                f"- Buyer move: `{scenario['buyer_move_id']}`",
                f"- Target gap: `{scenario['target_gap']}`",
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
    summary = {
        "checkpoint_id": CHECKPOINT_ID,
        "status": result["status"],
        "scenario_count": result["scenario_count"],
        "multi_turn_scenario_count": result["multi_turn_scenario_count"],
        "pass_count": result["pass_count"],
        "failure_count": result["failure_count"],
        "failure_types": result["failure_types"],
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    if result["scenario_count"] < 120:
        raise SystemExit("focused validator must include at least 120 scenarios")
    if result["multi_turn_scenario_count"] < 60:
        raise SystemExit("focused validator must include at least 60 multi-turn scenarios")
    if result["campaign_count"] < 6:
        raise SystemExit("focused validator must include at least 6 campaigns")
    if result["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
