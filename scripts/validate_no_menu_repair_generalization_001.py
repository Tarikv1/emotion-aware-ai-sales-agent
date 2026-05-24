#!/usr/bin/env python3
"""Validate generalized one-move repairs instead of menu resets."""

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


CHECKPOINT_ID = "NO-MENU-REPAIR-GENERALIZATION-001"
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
    "name the point",
    "which part should i check first",
    "manual tracking or missed callbacks",
    "premium or budget, coverage fit, or renewal",
    "plan fit, coverage or availability, or contract or switching",
    "manual work, integration, or visibility",
    "vehicle issue, repair timing, or warranty",
]

FORBIDDEN_INTERNAL = [
    "approved qualified reviewer path",
    "approved scope",
    "internal policy",
    "transfer-or-escalate",
    "i should not",
    "i may not be the right contact",
]


@dataclass(frozen=True)
class Campaign:
    campaign_id: str
    config_path: Path | None
    primary_issue: str
    pain: str
    out_of_campaign_request: str
    mismatch_topic: str
    clarity_phrases: tuple[tuple[str, str], ...]
    negative_control: str


@dataclass(frozen=True)
class Scenario:
    scenario_id: str
    group: str
    campaign: Campaign
    buyer_script: tuple[str, ...]
    expected_move_ids: frozenset[str] = frozenset()
    expected_reason_contains: str | None = None
    expected_response_terms: tuple[str, ...] = ()
    forbidden_response_terms: tuple[str, ...] = ()
    require_end_call: bool = False
    allow_end_call: bool = False
    negative_control: bool = False


CAMPAIGNS = [
    Campaign(
        "routesignal_live_demo",
        None,
        "inbound demo follow-up",
        "callbacks are a problem",
        "I need insurance coverage",
        "insurance",
        (
            ("callbacks thing is confusing", "callbacks"),
            ("handoffs are unclear", "handoffs"),
            ("what do you mean by callbacks", "callbacks"),
            ("call bags are confusing", "callbacks"),
        ),
        "premium pressure is not my issue",
    ),
    Campaign(
        "synthetic-insurance-review",
        EXAMPLES / "synthetic-insurance-review.json",
        "premium pressure",
        "premium is a problem",
        "software callbacks are the issue",
        "software callbacks",
        (
            ("coverage thing is confusing", "coverage"),
            ("coverage fit is unclear", "coverage"),
            ("what do you mean by coverage fit", "coverage"),
            ("payment pressure is confusing", "premium"),
        ),
        "manual tracking is not my issue",
    ),
    Campaign(
        "synthetic-telecom-plan-review",
        EXAMPLES / "synthetic-telecom-plan-review.json",
        "plan fit",
        "plan fit is a problem",
        "repair timing is the issue",
        "repair timing",
        (
            ("plane fit is confusing", "plan"),
            ("contact switching is confusing", "contract"),
            ("what do you mean by plan fit", "plan"),
            ("coverage availability is unclear", "coverage"),
        ),
        "repair timing is not my issue",
    ),
    Campaign(
        "synthetic-automotive-service-review",
        EXAMPLES / "synthetic-automotive-service-review.json",
        "repair timing",
        "repair timings are usually pretty long",
        "plan fit is the issue",
        "plan fit",
        (
            ("repair timing is confusing", "repair"),
            ("warranty estimate thing is unclear", "warranty"),
            ("what do you mean by repair timing", "repair"),
            ("service timing is confusing", "timing"),
        ),
        "coverage fit is not my issue",
    ),
    Campaign(
        "synthetic-membership-plan-review",
        EXAMPLES / "synthetic-membership-plan-review.json",
        "plan fit",
        "plan fit is a problem",
        "warranty estimate is the issue",
        "warranty",
        (
            ("plan thing is confusing", "plan"),
            ("usage thing is unclear", "usage"),
            ("what do you mean by plan fit", "plan"),
            ("cancel timing is confusing", "cancel"),
        ),
        "repair timing is not my issue",
    ),
    Campaign(
        "synthetic-b2b-saas-operations",
        EXAMPLES / "synthetic-b2b-saas-operations.json",
        "manual work",
        "manual work is a problem",
        "cancellation terms are the issue",
        "cancellation terms",
        (
            ("integration thing is confusing", "integration"),
            ("visibility thing is unclear", "visibility"),
            ("what do you mean by integration risk", "integration"),
            ("manual trucking is confusing", "manual"),
        ),
        "premium pressure is not my issue",
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


def contains_any(text: str, patterns: list[str] | tuple[str, ...] | set[str]) -> bool:
    return any(pattern in text for pattern in patterns)


def build_scenarios() -> list[Scenario]:
    scenarios: list[Scenario] = []
    correction_variants = [
        "that's not my issue",
        "no, that is not what I meant",
        "you misunderstood me",
        "stop assuming that",
        "that is not my problem",
        "I didn't say that was the issue",
    ]
    hostile_variants = [
        "this sounds like a scam",
        "this sounds automated",
        "prove this is useful",
        "are you wasting my time",
        "this is pointless",
        "stop pitching me",
    ]
    repeated_variants = [
        "you already said that",
        "you keep repeating yourself",
        "say it differently",
        "you still didn't answer",
        "explain it another way",
    ]
    early_callback_variants = [
        "call me tomorrow",
        "call me tomorrow at 3",
        "email me first",
        "can someone call later",
        "I don't know, call back sometime",
    ]
    negative_variants = [
        "not interested",
        "I just got out of the hospital",
        "my account number is [REDACTED_ACCOUNT_NUMBER]",
    ]

    for campaign in CAMPAIGNS:
        scenarios.append(
            Scenario(
                f"exact-not-my-issue-{campaign.campaign_id}",
                "exact_remaining_red_examples",
                campaign,
                ("__agent_open__", "yeah", "that's not my issue"),
                expected_move_ids=frozenset({"already_answered_challenge"}),
                expected_response_terms=("reset", "useful"),
            )
        )
        if campaign.campaign_id == "routesignal_live_demo":
            scenarios.append(
                Scenario(
                    "exact-routesignal-hostile-chain",
                    "exact_remaining_red_examples",
                    campaign,
                    ("__agent_open__", "this sounds automated", "prove this is useful", "this is pointless"),
                    expected_move_ids=frozenset({"abusive_or_hostile_buyer", "is_this_worth_my_time", "are_you_ai_or_robot"}),
                    expected_response_terms=("fair",),
                    allow_end_call=True,
                )
            )

        for index, phrase in enumerate(correction_variants, start=1):
            scenarios.append(
                Scenario(
                    f"correction-{campaign.campaign_id}-{index:02d}",
                    "paraphrase_correction_variants",
                    campaign,
                    ("__agent_open__", "yeah", campaign.pain, phrase),
                    expected_move_ids=frozenset({"already_answered_challenge"}),
                    expected_response_terms=("assume",),
                )
            )

        for index, phrase in enumerate(hostile_variants, start=1):
            scenarios.append(
                Scenario(
                    f"hostile-{campaign.campaign_id}-{index:02d}",
                    "hostile_challenge_variants",
                    campaign,
                    ("__agent_open__", phrase),
                    expected_move_ids=frozenset(
                        {
                            "abusive_or_hostile_buyer",
                            "why_should_i_care",
                            "is_this_worth_my_time",
                            "wants_proof_or_case_study",
                            "are_you_ai_or_robot",
                            "stop_request",
                        }
                    ),
                    expected_response_terms=("fair",),
                    allow_end_call=True,
                )
            )

        for index, phrase in enumerate(repeated_variants, start=1):
            scenarios.append(
                Scenario(
                    f"repeat-{campaign.campaign_id}-{index:02d}",
                    "repeated_answer_variants",
                    campaign,
                    ("__agent_open__", "what are you selling", phrase),
                    expected_move_ids=frozenset(
                        {
                            "already_answered_challenge",
                            "repeat_last_answer",
                            "repeat_or_rephrase_request",
                            "what_problem_do_you_solve",
                        }
                    ),
                    expected_response_terms=("direct", "short", "plain", "different", "reset"),
                )
            )

        mismatch_variants = [
            campaign.out_of_campaign_request,
            "why are you talking about something else",
            f"is this about {campaign.mismatch_topic} or {campaign.primary_issue}",
        ]
        for index, phrase in enumerate(mismatch_variants, start=1):
            scenarios.append(
                Scenario(
                    f"mismatch-{campaign.campaign_id}-{index:02d}",
                    "out_of_campaign_mismatch_variants",
                    campaign,
                    ("__agent_open__", phrase),
                    expected_move_ids=frozenset({"confusion_not_clear", "scope_limit_question"}),
                    expected_response_terms=(campaign.primary_issue.split()[0].lower(),),
                    forbidden_response_terms=(campaign.mismatch_topic.lower(),)
                    if campaign.mismatch_topic.lower() not in campaign.primary_issue.lower()
                    else (),
                )
            )

        for index, phrase in enumerate(early_callback_variants, start=1):
            scenarios.append(
                Scenario(
                    f"early-callback-{campaign.campaign_id}-{index:02d}",
                    "early_callback_time_variants",
                    campaign,
                    ("__agent_open__", phrase),
                    expected_move_ids=frozenset(
                        {
                            "callback_request",
                            "callback_time_provided",
                            "buyer_wants_email_before_booking",
                            "buyer_defers_to_later",
                        }
                    ),
                    expected_response_terms=("note", "email", "window", "time", "later"),
                    allow_end_call=True,
                )
            )

        for index, (phrase, expected_term) in enumerate(campaign.clarity_phrases, start=1):
            scenarios.append(
                Scenario(
                    f"gap-clarity-{campaign.campaign_id}-{index:02d}",
                    "configured_gap_clarity_request",
                    campaign,
                    ("__agent_open__", "yeah", phrase),
                    expected_move_ids=frozenset({"confusion_not_clear"}),
                    expected_reason_contains="configured_gap",
                    expected_response_terms=("confusing", "unclear", "what part", expected_term.lower()),
                    forbidden_response_terms=("maybe ", "active concern now", "checked later"),
                )
            )
            scenarios.append(
                Scenario(
                    f"gap-clarity-later-{campaign.campaign_id}-{index:02d}",
                    "configured_gap_clarity_request",
                    campaign,
                    ("__agent_open__", "yeah", "what does your product do", phrase),
                    expected_move_ids=frozenset({"confusion_not_clear"}),
                    expected_reason_contains="configured_gap",
                    expected_response_terms=("confusing", "unclear", "what part", expected_term.lower()),
                    forbidden_response_terms=("maybe ", "active concern now", "checked later"),
                )
            )

        scenarios.append(
            Scenario(
                f"negative-control-cross-gap-{campaign.campaign_id}",
                "negative_controls",
                campaign,
                ("__agent_open__", "yeah", campaign.negative_control),
                expected_move_ids=frozenset({"confusion_not_clear", "no_pain_clear", "already_answered_challenge"}),
                negative_control=True,
            )
        )
        for index, phrase in enumerate(negative_variants, start=1):
            scenarios.append(
                Scenario(
                    f"negative-control-{campaign.campaign_id}-{index:02d}",
                    "negative_controls",
                    campaign,
                    ("__agent_open__", phrase),
                    expected_move_ids=frozenset({"stop_request", "serious_hardship_bad_timing", "sensitive_personal_data_disclosure"}),
                    require_end_call=True,
                    allow_end_call=True,
                    negative_control=True,
                )
            )

    return scenarios


def evaluate(scenario: Scenario) -> dict[str, Any]:
    state: dict[str, Any] = {}
    turns: list[dict[str, Any]] = []
    failures: list[str] = []
    for index, transcript in enumerate(scenario.buyer_script, start=1):
        packet = build_turn(transcript, state, scenario)
        turns.append(turn_summary(index, transcript, packet))

    final = turns[-1]
    response_norm = norm(final["final_response"])
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
    if source == "pre_speech_conversation_stability_guard":
        failures.append("stability_guard_selected_final_action")
    if scenario.group != "negative_controls" and source == "live_voice_session_policy":
        failures.append("live_policy_fallback_selected")
    if final["question_count"] > 1:
        failures.append("too_many_questions")
    if scenario.expected_move_ids and buyer_move_id not in scenario.expected_move_ids:
        failures.append(f"unexpected_buyer_move:{buyer_move_id or '<none>'}")
    if scenario.expected_reason_contains and scenario.expected_reason_contains not in reason:
        failures.append(f"unexpected_recognition_reason:{reason or '<none>'}")
    if scenario.expected_response_terms and not any(term in response_norm for term in scenario.expected_response_terms):
        failures.append("expected_response_terms_missing")
    for forbidden in scenario.forbidden_response_terms:
        if forbidden and forbidden in response_norm:
            failures.append(f"forbidden_response_term:{forbidden}")
    if scenario.require_end_call and call != "end-call":
        failures.append(f"expected_end_call_got:{call}")
    if not scenario.allow_end_call and call != "continue-call":
        failures.append(f"unexpected_call_control:{call}")
    if scenario.group == "configured_gap_clarity_request":
        if buyer_move_id == "pain_confirmed":
            failures.append("clarity_request_confirmed_as_pain")
        if not contains_any(response_norm, {"what part", "which part", "do you mean", "trying to understand", "mean ", "means "}):
            failures.append("clarity_request_not_answered_as_clarification")
    if scenario.group == "hostile_challenge_variants":
        if buyer_move_id != "stop_request" and not contains_any(response_norm, {"fair", "understand", "concern", "direct", "waste"}):
            failures.append("hostile_challenge_not_deescalated")
        if "appointment" in response_norm or "what time" in response_norm:
            failures.append("hostile_challenge_pressured_next_step")
    if scenario.group == "early_callback_time_variants":
        if "calendar" in response_norm or "email sent" in response_norm or "send email" in response_norm:
            failures.append("fake_calendar_or_email_claim")
    if scenario.negative_control:
        frame = final.get("universal_policy_frame") or {}
        if frame.get("buyer_move_id") == "pain_confirmed":
            failures.append("negative_control_false_pain_confirmed")
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
        "final_response": final["final_response"],
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
        "exact_scripted_case_count": sum(1 for result in results if result["group"] == "exact_remaining_red_examples"),
        "generalized_variant_count": sum(1 for result in results if result["group"] not in {"exact_remaining_red_examples", "negative_controls"}),
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
        f"- Exact scripted cases: `{result['exact_scripted_case_count']}`",
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
    for scenario in [item for item in result["scenarios"] if item["failures"]][:40]:
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
