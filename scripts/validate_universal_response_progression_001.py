#!/usr/bin/env python3
"""Validate universal response progression and challenge de-escalation.

This is a dry-run validator. It does not call providers, live TTS, email,
calendar, CRM, local LLMs, or PROD-102.
"""

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


CHECKPOINT_ID = "UNIVERSAL-RESPONSE-PROGRESSION-001"
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
    "manual tracking or missed callbacks",
    "premium or budget, coverage fit",
    "plan fit, coverage or availability",
    "vehicle issue, repair timing",
    "manual work, integration",
]

FORBIDDEN_INTERNAL = [
    "approved qualified reviewer path",
    "internal policy",
    "transfer-or-escalate",
    "prod-102",
]


@dataclass(frozen=True)
class Campaign:
    campaign_id: str
    config_path: Path | None
    primary_issue: str
    primary_terms: tuple[str, ...]
    pain: str
    impact: str
    weak_impact: str
    no_problem: str
    configured_gap_pain: str
    configured_gap_clarity: str
    other_campaign_phrase: str
    other_campaign_term: str


@dataclass(frozen=True)
class Scenario:
    scenario_id: str
    group: str
    campaign: Campaign
    buyer_script: tuple[str, ...]
    exact_red_example: bool = False
    paraphrase_variant: bool = False
    later_turn_variant: bool = False
    negative_control: bool = False
    allow_end_call: bool = False
    require_end_call: bool = False


CAMPAIGNS = [
    Campaign(
        "routesignal_live_demo",
        None,
        "inbound demo follow-up",
        ("inbound demo", "follow-up", "callback"),
        "callbacks are a problem",
        "it causes delays",
        "just annoying",
        "callbacks are not a problem",
        "handoffs are messy",
        "what do you mean by callbacks",
        "premium pressure is the issue",
        "premium",
    ),
    Campaign(
        "synthetic-insurance-review",
        EXAMPLES / "synthetic-insurance-review.json",
        "premium pressure",
        ("premium",),
        "premium is a problem",
        "it wastes time",
        "not really",
        "coverage is not confusing",
        "coverage fit is a problem",
        "what do you mean by coverage fit",
        "callbacks are a problem",
        "callbacks",
    ),
    Campaign(
        "synthetic-telecom-plan-review",
        EXAMPLES / "synthetic-telecom-plan-review.json",
        "plan fit",
        ("plan", "coverage"),
        "plan fit is a problem",
        "customers wait",
        "just annoying",
        "coverage availability is not confusing",
        "coverage availability is the issue",
        "what do you mean by plan fit",
        "repair timings are usually pretty long",
        "repair",
    ),
    Campaign(
        "synthetic-automotive-service-review",
        EXAMPLES / "synthetic-automotive-service-review.json",
        "repair timing",
        ("repair",),
        "repair timings are usually pretty long",
        "it slows us down",
        "not a big deal",
        "repair timing is not a problem",
        "warranty estimate is the issue",
        "what do you mean by repair timing",
        "coverage availability is the issue",
        "coverage",
    ),
    Campaign(
        "synthetic-membership-plan-review",
        EXAMPLES / "synthetic-membership-plan-review.json",
        "plan fit",
        ("plan", "membership"),
        "plan fit is a problem",
        "it costs money",
        "just annoying",
        "plan fit is not a problem",
        "usage limits are a problem",
        "what do you mean by plan fit",
        "inbound demo follow-up is slipping",
        "inbound demo",
    ),
    Campaign(
        "synthetic-b2b-saas-operations",
        EXAMPLES / "synthetic-b2b-saas-operations.json",
        "manual work",
        ("manual",),
        "manual work is a problem",
        "it wastes time",
        "not really",
        "manual work is not a problem",
        "integration risk is a problem",
        "what do you mean by integration risk",
        "premium pressure is the issue",
        "premium",
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
            "continuity": packet.get("conversation_continuity") or packet.get("demo_session_continuity") or {},
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
        "appointment_readiness": frame.get("appointment_readiness"),
        "next_best_sales_action": frame.get("next_best_sales_action"),
        "universal_policy_frame": frame,
        "contextual_buyer_semantics": context,
        "side_effect_flags": side_effect_flags(packet),
        "stability_guard_applied": action.get("source") == "pre_speech_conversation_stability_guard",
    }


def add(
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
    for campaign in CAMPAIGNS:
        repeated_scripts = [
            ("exact", ("__agent_open__", "yeah", campaign.pain, "that would be useful", "okay what now"), True, False),
            ("paraphrase-useful", ("__agent_open__", "yeah", campaign.pain, "that sounds useful", "what happens next"), False, True),
            ("later-turn", ("__agent_open__", "what does your product do", "yeah", campaign.pain, "okay what now"), False, False),
            ("impact-exact", ("__agent_open__", "yeah", campaign.pain, campaign.impact, "that would be useful", "okay what now"), True, False),
            ("impact-paraphrase", ("__agent_open__", "yeah", campaign.pain, campaign.impact, "sure what next"), False, True),
        ]
        for phrase_id, script, exact, paraphrase in repeated_scripts:
            add(
                scenarios,
                campaign,
                "repeated_response_progression",
                phrase_id,
                script,
                exact_red_example=exact,
                paraphrase_variant=paraphrase,
                later_turn_variant=phrase_id == "later-turn",
            )

        for index, phrase in enumerate(("that's wrong", "that doesn't make sense", "you're making assumptions", "this sounds automated"), start=1):
            add(
                scenarios,
                campaign,
                "hostile_challenge_clarification",
                f"exact-{index:02d}",
                ("__agent_open__", phrase),
                exact_red_example=phrase != "this sounds automated",
            )
            add(
                scenarios,
                campaign,
                "hostile_challenge_later_turn",
                f"later-{index:02d}",
                ("__agent_open__", "what does your product do", phrase),
                later_turn_variant=True,
            )

        for index, phrase in enumerate(("tomorrow works", "call me tomorrow", "tomorrow at 3 works"), start=1):
            add(
                scenarios,
                campaign,
                "early_callback_before_readiness",
                f"exact-{index:02d}",
                ("__agent_open__", phrase),
                exact_red_example=phrase == "tomorrow works",
            )
        add(
            scenarios,
            campaign,
            "callback_after_readiness_preservation",
            "pain-impact-tomorrow",
            ("__agent_open__", "yeah", campaign.pain, campaign.impact, "tomorrow works"),
            allow_end_call=True,
        )

        mismatch_scripts = [
            ("exact", ("__agent_open__", campaign.other_campaign_phrase), True),
            ("why-something-else", ("__agent_open__", campaign.other_campaign_phrase, "why are you talking about something else?"), False),
            ("why-relevant", ("__agent_open__", campaign.other_campaign_phrase, "why is that relevant"), False),
            ("paraphrase", ("__agent_open__", campaign.other_campaign_phrase.replace(" is the issue", " is what I mean"), "is this about that or something else"), False),
        ]
        for phrase_id, script, exact in mismatch_scripts:
            add(
                scenarios,
                campaign,
                "out_of_campaign_mismatch",
                phrase_id,
                script,
                exact_red_example=exact,
                paraphrase_variant=phrase_id == "paraphrase",
            )

        direct_answer_loops = [
            ("product-repeat", ("__agent_open__", "what does your product do", "what does your product do")),
            ("scope-repeat", ("__agent_open__", "so you cannot give details", "so you cannot give details")),
            ("did-not-answer", ("__agent_open__", "you didn't answer", "you didn't answer")),
            ("later-product", ("__agent_open__", "yeah", campaign.pain, "what does your product do", "what does your product do")),
        ]
        for phrase_id, script in direct_answer_loops:
            add(
                scenarios,
                campaign,
                "repeated_direct_answer_progression",
                phrase_id,
                script,
                paraphrase_variant=phrase_id != "product-repeat",
            )

        negative_scripts = [
            ("explicit-stop", ("__agent_open__", "not interested"), True, False),
            ("hardship", ("__agent_open__", "I just got out of the hospital"), True, False),
            ("sensitive-data", ("__agent_open__", "my account number is [REDACTED_ACCOUNT_NUMBER]"), True, False),
            ("no-problem", ("__agent_open__", "yeah", campaign.no_problem), False, False),
            ("weak-impact", ("__agent_open__", "yeah", campaign.pain, campaign.weak_impact), False, False),
            ("configured-gap-pain", ("__agent_open__", "yeah", campaign.configured_gap_pain), False, False),
            ("configured-gap-clarity", ("__agent_open__", "yeah", campaign.configured_gap_clarity), False, False),
            ("stop-after-callback", ("__agent_open__", "call me tomorrow", "not interested"), True, False),
        ]
        for phrase_id, script, allow_end, require_end in negative_scripts:
            add(
                scenarios,
                campaign,
                "negative_controls",
                phrase_id,
                script,
                negative_control=True,
                allow_end_call=allow_end,
                require_end_call=require_end,
            )
    return scenarios


def repeated_exact_response(turns: list[dict[str, Any]]) -> bool:
    responses = [str(turn.get("final_response") or "").strip() for turn in turns[1:] if str(turn.get("final_response") or "").strip()]
    counts = Counter(responses)
    return any(count > 1 and "stop here" not in norm(text) for text, count in counts.items())


def repeated_pain_diagnostic(response_norm: str, campaign: Campaign) -> bool:
    primary = norm(campaign.primary_issue)
    return (
        f"is {primary} causing any issue right now" in response_norm
        or f"is {primary} causing any issue" in response_norm
        or f"is {primary} still a problem" in response_norm
        or "quick check for a short" in response_norm and "causing any issue right now" in response_norm
    )


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
    script_norm = norm(" ".join(scenario.buyer_script))
    call = str(final.get("call_control") or "")
    buyer_move_id = str(final.get("buyer_move_id") or "")
    readiness = str(final.get("appointment_readiness") or "")
    side_effects = {
        key: any(bool((turn.get("side_effect_flags") or {}).get(key)) for turn in turns)
        for key in SIDE_EFFECT_KEYS
    }

    if scenario.group != "repeated_direct_answer_progression" and contains_any(response_norm, FORBIDDEN_MENU):
        failures.append("full_menu_used")
    if contains_any(response_norm, FORBIDDEN_INTERNAL):
        failures.append("internal_wording_used")
    if final["question_count"] > 1:
        failures.append("too_many_questions")
    if scenario.require_end_call and call != "end-call":
        failures.append(f"expected_end_call_got:{call}")
    if not scenario.allow_end_call and call != "continue-call":
        failures.append(f"unexpected_call_control:{call}")

    if scenario.group == "repeated_response_progression":
        if repeated_pain_diagnostic(response_norm, scenario.campaign):
            failures.append("repeated_pain_question_after_confirmed_pain")
        if "impact" not in response_norm and not contains_any(response_norm, {"delay", "delays", "extra work", "wasting time", "costing time", "callback window", "time window"}):
            failures.append("progression_missing_impact_or_next_step")
        if scenario.buyer_script[-2] == scenario.campaign.impact and not contains_any(response_norm, {"callback", "time window", "day or time", "what time", "window works"}):
            failures.append("impact_confirmed_did_not_move_to_callback")
        if scenario.buyer_script[-2] != scenario.campaign.impact and contains_any(response_norm, {"what time", "what day", "schedule", "confirmed"}):
            failures.append("appointment_too_early_after_pain_only")
    elif scenario.group.startswith("hostile_challenge"):
        last = norm(scenario.buyer_script[-1])
        if "automated" in last:
            if "ai" not in response_norm and "automated" not in response_norm:
                failures.append("automated_challenge_not_transparent")
            if contains_any(response_norm, {"i am human", "not automated"}):
                failures.append("automated_challenge_pretended_human")
        elif "wrong" in last:
            if not contains_any(response_norm, {"what part is wrong", "what should i correct", "which part is wrong"}):
                failures.append("wrong_challenge_missing_specific_correction")
        elif "make sense" in last:
            if not contains_any(response_norm, {"what does not make sense", "what doesn't make sense", "what part does not make sense", "what part doesn't make sense"}):
                failures.append("nonsense_challenge_missing_specific_correction")
        elif "assumption" in last:
            if not contains_any(response_norm, {"what should i correct", "what assumption", "what did i assume"}):
                failures.append("assumption_challenge_missing_specific_correction")
        if contains_any(response_norm, {"let me reset", "is there any issue here you actually want reviewed", "what time works"}):
            failures.append("hostile_challenge_generic_reset_or_pressure")
    elif scenario.group == "early_callback_before_readiness":
        if call == "schedule-and-end":
            failures.append("early_callback_scheduled_without_readiness")
        if readiness in {"medium", "high"}:
            failures.append(f"early_callback_readiness_too_high:{readiness}")
        if not contains_any(response_norm, {"callback", "call back", "note"}):
            failures.append("callback_preference_not_acknowledged")
        if not any(term in response_norm for term in scenario.campaign.primary_terms):
            failures.append("callback_relevance_check_missing")
        if contains_any(response_norm, {"calendar", "email sent", "crm"}):
            failures.append("fake_calendar_email_or_crm_claim")
    elif scenario.group == "callback_after_readiness_preservation":
        if call != "schedule-and-end":
            failures.append(f"callback_after_readiness_not_captured:{call}")
        if not contains_any(response_norm, {"note", "follow up", "callback"}):
            failures.append("callback_after_readiness_confirmation_missing")
    elif scenario.group == "out_of_campaign_mismatch":
        if scenario.campaign.other_campaign_term not in response_norm:
            failures.append("mismatch_not_acknowledged")
        if not any(term in response_norm for term in scenario.campaign.primary_terms):
            failures.append("current_scope_not_stated")
        if contains_any(response_norm, {"causing any issue right now", "is happening and causing"}):
            failures.append("mismatch_forced_immediate_diagnostic")
        if contains_any(response_norm, {"outside this call's scope", "outside this call scope", "outside scope"}):
            failures.append("mismatch_abrupt_scope_reset")
    elif scenario.group == "repeated_direct_answer_progression":
        if repeated_exact_response(turns):
            failures.append("repeated_exact_response")
        if not contains_any(response_norm, {"already", "different wording", "same boundary", "direct answer", "i answered"}):
            failures.append("repeated_direct_answer_not_marked_as_repeat")
        if contains_any(response_norm, {"what email or callback", "right person or team"}):
            failures.append("repeated_direct_answer_wrong_contact_escape")
    elif scenario.negative_control:
        if "explicit-stop" in scenario.scenario_id or "stop-after-callback" in scenario.scenario_id:
            if call != "end-call":
                failures.append(f"stop_not_respected:{call}")
        if "hardship" in scenario.scenario_id or "sensitive-data" in scenario.scenario_id:
            if call != "end-call":
                failures.append(f"terminal_rapport_not_respected:{call}")
        if "no-problem" in scenario.scenario_id and contains_any(response_norm, {"what time", "callback window", "schedule"}):
            failures.append("no_problem_created_appointment_pressure")
        if "weak-impact" in scenario.scenario_id and contains_any(response_norm, {"what time", "callback window", "schedule"}):
            failures.append("weak_impact_created_appointment_pressure")
        if "configured-gap-pain" in scenario.scenario_id and buyer_move_id != "pain_confirmed":
            failures.append(f"configured_gap_pain_not_recognized:{buyer_move_id}")
        if "configured-gap-clarity" in scenario.scenario_id and not contains_any(
            response_norm,
            {"what part", "what it means", "what does", "what callback means", "what it covers"},
        ):
            failures.append("configured_gap_clarity_not_preserved")
        if universal_frame_from_summary(final).get("buyer_move_id") == "pain_confirmed" and "no-problem" in scenario.scenario_id:
            failures.append("negative_no_problem_false_pain")

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
        "selected_action_source": final.get("selected_action_source"),
        "buyer_move_id": buyer_move_id,
        "recognition_reason": final.get("recognition_reason"),
        "appointment_readiness": readiness,
        "next_best_sales_action": final.get("next_best_sales_action"),
        "call_control": call,
        "failures": failures,
        "passed": not failures,
        "exact_red_example": scenario.exact_red_example,
        "paraphrase_variant": scenario.paraphrase_variant,
        "later_turn_variant": scenario.later_turn_variant,
        "negative_control": scenario.negative_control,
        "side_effect_flags": side_effects,
        "requires_human_sales_review": True,
        "codex_assigned_final_sales_quality": False,
    }


def universal_frame_from_summary(turn: dict[str, Any]) -> dict[str, Any]:
    frame = turn.get("universal_policy_frame") or {}
    return frame if isinstance(frame, dict) else {}


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
        "exact_red_example_count": sum(1 for result in results if result["exact_red_example"]),
        "paraphrase_variant_count": sum(1 for result in results if result["paraphrase_variant"]),
        "later_turn_variant_count": sum(1 for result in results if result["later_turn_variant"]),
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
        f"- Paraphrase variants: `{result['paraphrase_variant_count']}`",
        f"- Later-turn variants: `{result['later_turn_variant_count']}`",
        f"- Negative controls: `{result['negative_control_count']}`",
        "",
        "## Failure Types",
        *(f"- `{key}`: `{value}`" for key, value in result["failure_types"].items()),
        "",
        "## Failures By Group",
        *(f"- `{key}`: `{value}`" for key, value in result["failures_by_group"].items()),
        "",
        "## Worst Examples",
    ]
    for scenario in [item for item in result["scenarios"] if item["failures"]][:80]:
        lines.extend(
            [
                f"### {scenario['scenario_id']}",
                f"- Campaign: `{scenario['campaign_id']}`",
                f"- Group: `{scenario['group']}`",
                f"- Source: `{scenario['selected_action_source']}`",
                f"- Buyer move: `{scenario['buyer_move_id']}`",
                f"- Reason: `{scenario['recognition_reason']}`",
                f"- Readiness: `{scenario['appointment_readiness']}`",
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
    if result["scenario_count"] < 180:
        raise SystemExit("focused validator must include at least 180 scenarios")
    if result["multi_turn_scenario_count"] < 100:
        raise SystemExit("focused validator must include at least 100 multi-turn scenarios")
    if result["campaign_count"] < 6:
        raise SystemExit("focused validator must include at least 6 campaigns")
    if any(result["side_effect_boundary"].values()):
        raise SystemExit("side-effect boundary failed")
    if result["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
