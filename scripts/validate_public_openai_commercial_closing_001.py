#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.validate_commercial_sales_performance_001 import (  # noqa: E402
    RAW_URL_RE,
    RUBRIC_DIMENSIONS,
    SIDE_EFFECT_KEYS,
    build_turn,
    has_commercial_action,
    normalize,
    response_text,
    score_commercial_response,
    side_effect_flags,
)


CHECKPOINT_ID = "PUBLIC-OPENAI-COMMERCIAL-CLOSING-001"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"

FAKE_SIDE_EFFECT_RE = re.compile(
    r"\b(i sent|i emailed|i booked|created .*calendar|created .*crm|processed your card|charged your card)\b",
    re.I,
)
AFFILIATION_RE = re.compile(r"\b(calling from openai|authorized by openai|represent openai|official openai call)\b", re.I)
GENERIC_DISCOVERY_RE = re.compile(
    r"what matters most|what would you mainly use|are you using it occasionally or heavily every day|"
    r"are you using chatgpt today|using another ai tool, or mostly not using",
    re.I,
)
VAGUE_PLAN_FIT_RE = re.compile(r"plan fit still needs|actual work before plan fit|only after that would", re.I)
SUPERIORITY_RE = re.compile(r"\b(better than claude|better than gemini|superior|guarantee)\b", re.I)
OVER_DEFENSIVE_RE = re.compile(r"cannot send.*book.*payment|cannot send.*book|book anything.*take payment", re.I)


def sha12(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def contains_any(text: str, fragments: list[str] | tuple[str, ...] | set[str]) -> bool:
    lowered = normalize(text)
    return any(fragment.lower() in lowered for fragment in fragments)


def scenario(
    scenario_id: str,
    group: str,
    turns: list[str],
    expectation: dict[str, Any],
) -> dict[str, Any]:
    return {
        "id": scenario_id,
        "group": group,
        "turns": turns,
        "expectation": expectation,
        "multi_turn": len(turns) > 1,
    }


def with_open(turns: list[str]) -> list[str]:
    return ["__agent_open__", "yeah sure", *turns]


def build_scenarios() -> list[dict[str, Any]]:
    scenarios: list[dict[str, Any]] = []

    use_cases = [
        "I use it for coding and writing",
        "mostly coding and writing",
        "coding and writing every week",
        "I use ChatGPT for coding",
        "I use it for writing and research",
        "I use it for code reviews and writing",
        "personal coding and writing",
        "I use it mostly for programming and drafting",
        "I use it for files, coding, and writing",
        "I use it for work documents and code",
        "I use ChatGPT and other AI tools for coding and writing",
        "I use another AI tool too for coding and writing",
        "I use Claude too for coding and writing",
        "I use Gemini and ChatGPT for coding and writing",
        "I use Copilot for code too, plus writing",
        "I use a different assistant now for coding and writing",
    ]
    plus_questions = [
        "is Plus enough?",
        "is Plus going to be enough for my use case?",
        "should I choose Plus?",
        "is Pro worth it over Plus?",
        "Plus or Pro?",
        "should I start with Plus?",
        "is Plus enough though?",
        "why Pro over Plus?",
        "would Plus cover that?",
        "is Plus the right plan?",
    ]
    for index, use_case in enumerate(use_cases, start=1):
        question = plus_questions[(index - 1) % len(plus_questions)]
        scenarios.append(
            scenario(
                f"plus-enough-direct-{index:03d}",
                "plus_enough_direct_answer",
                with_open([use_case, question]),
                {
                    "buying_question": True,
                    "expected_plan": "plus",
                    "decision_frame": "plus_vs_pro",
                    "buyer_terms": ["plus", "pro"],
                    "forbid": ["you may not need to switch", "what matters most", "plan fit still needs"],
                },
            )
        )

    intensities = [
        "I use it heavily every day",
        "heavy use",
        "very heavily",
        "every day for serious work",
        "heavy daily use",
        "a little bit on the heavy side",
        "I use it all day",
        "advanced tools all week",
        "heavy coding work",
        "lots of coding and writing",
        "constant writing and coding",
        "I use it several hours a day",
        "daily coding and writing",
        "I rely on it heavily",
        "I am a power user",
        "I use it more than casually",
        "serious daily use",
        "heavy work volume",
        "I need high usage",
        "I use it repeatedly every day",
    ]
    for index, intensity in enumerate(intensities, start=1):
        scenarios.append(
            scenario(
                f"heavy-usage-recommendation-{index:03d}",
                "heavy_usage_recommendation",
                with_open(["I use it for coding and writing", intensity, plus_questions[(index - 1) % len(plus_questions)]]),
                {
                    "buying_question": True,
                    "expected_plan": "pro",
                    "decision_frame": "plus_vs_pro",
                    "buyer_terms": ["coding", "writing"],
                    "forbid": ["plan fit still needs", "what matters most", "given you are hitting limits"],
                },
            )
        )

    pro_signals = [
        "so Pro is better for me probably",
        "Pro seems better",
        "sounds like Pro is the better fit",
        "then Pro makes more sense",
        "I guess Pro is safer",
        "so I should compare Pro first",
        "Pro is probably right",
        "that means Pro for me",
        "then Pro is the stronger choice",
        "I think Pro is better",
        "okay Pro sounds right",
        "so not Plus, Pro",
        "I should look at Pro then",
        "Pro fits my use better",
        "then I need Pro",
        "Pro probably works",
        "I am leaning Pro",
        "that pushes me to Pro",
        "Pro is the plan to compare",
        "Pro first then",
    ]
    for index, signal in enumerate(pro_signals, start=1):
        scenarios.append(
            scenario(
                f"buyer-agreement-pro-{index:03d}",
                "buyer_agreement_to_pro",
                with_open(["I use it for coding and writing", "I use it heavily every day", signal]),
                {
                    "buying_question": True,
                    "buying_signal": True,
                    "close_expected": True,
                    "expected_plan": "pro",
                    "decision_frame": "plus_vs_pro",
                    "buyer_terms": ["coding", "writing"],
                    "forbid": ["are you using it occasionally", "what matters most"],
                },
            )
        )

    price_questions = [
        "how much are the plans?",
        "what is the price?",
        "how much does Plus cost?",
        "what does Pro cost?",
        "how much is Plus and Pro?",
        "what are the paid tiers?",
        "tell me the pricing",
        "what does it cost monthly?",
        "is Plus twenty dollars?",
        "what is Free versus paid?",
        "price please",
        "how expensive is it?",
        "what should I budget?",
        "what are the current prices?",
        "how much would this be for me?",
        "what is the paid plan cost?",
        "how much are Plus and Pro now?",
        "what does the individual plan cost?",
        "do I pay for Plus or Pro?",
        "what is the difference in price?",
    ]
    for index, question in enumerate(price_questions, start=1):
        scenarios.append(
            scenario(
                f"price-known-use-{index:03d}",
                "price_with_known_use_case",
                with_open(["I use it for coding and writing", "I use it heavily every day", question]),
                {
                    "buying_question": True,
                    "expected_plan": "pro",
                    "decision_frame": "plus_vs_pro",
                    "buyer_terms": ["coding", "writing"],
                    "forbid": ["given you are hitting limits"],
                },
            )
        )

    limit_phrases = [
        "I am hitting limits",
        "I keep hitting limits",
        "limits are frustrating",
        "I run out of limits",
        "I am blocked by limits",
        "I already hit limits",
        "mostly hitting limits",
        "limits are the problem",
        "I hit the cap often",
        "usage limits block me",
        "I am running out",
        "the limits are annoying",
        "I need fewer limits",
        "I want to avoid limits",
        "I am frustrated by limits",
    ]
    for index, limit_phrase in enumerate(limit_phrases, start=1):
        scenarios.append(
            scenario(
                f"price-explicit-limits-{index:03d}",
                "price_with_explicit_limits_pain",
                with_open(["I use it for coding and writing", limit_phrase, price_questions[(index - 1) % len(price_questions)]]),
                {
                    "buying_question": True,
                    "expected_plan": "pro",
                    "decision_frame": "plus_vs_pro",
                    "buyer_terms": ["limits"],
                },
            )
        )

    signup_questions = [
        "how do I sign up?",
        "where do I upgrade?",
        "what is the next step?",
        "show me the official page",
        "where is the plan page?",
        "ready to start",
        "what should I do next?",
        "how would I get Pro?",
        "where would I click?",
        "how do I start?",
        "how do I upgrade to Pro?",
        "where can I compare the plan?",
        "what page should I use?",
        "how do I move forward?",
        "where do I buy it?",
    ]
    for index, question in enumerate(signup_questions, start=1):
        scenarios.append(
            scenario(
                f"signup-after-recommendation-{index:03d}",
                "signup_after_recommendation",
                with_open(["I use it for coding and writing", "I use it heavily every day", pro_signals[(index - 1) % len(pro_signals)], question]),
                {
                    "buying_question": True,
                    "buying_signal": True,
                    "close_expected": True,
                    "expected_plan": "pro",
                    "decision_frame": "plus_vs_pro",
                    "buyer_terms": ["coding", "writing"],
                    "forbid": ["given you are hitting limits", "i cannot send", "book anything", "take payment"],
                },
            )
        )

    competitor_sequences = [
        ["I use another LLM", "I use it for coding and writing", "why would I switch?"],
        ["I use Claude", "coding and writing mostly", "why use ChatGPT too?"],
        ["I already use Gemini", "writing and research", "what gap would ChatGPT cover?"],
        ["I pay for another tool", "I use it for code", "why compare ChatGPT?"],
        ["Copilot already helps me code", "I also write a lot", "why switch?"],
        ["My current assistant works", "coding and writing", "what is the reason to compare?"],
        ["I use another AI tool", "I need files and writing", "what would be different?"],
        ["I already have an LLM", "heavy coding use", "why Pro over what I have?"],
        ["I use a different AI tool", "research and writing", "convince me without hype"],
        ["My current model handles most things", "I use it daily", "should I switch?"],
        ["I use another LLM", "how much are the plans", "but why would I switch?"],
        ["I use Claude too", "is Plus enough?", "why not stay where I am?"],
        ["I already pay for another subscription", "coding and writing", "why add this?"],
        ["another tool covers my writing", "coding is the weak spot", "what should I compare?"],
        ["I use another AI", "my current tool is weak on files", "which plan should I compare?"],
    ]
    for index, turns in enumerate(competitor_sequences, start=1):
        scenarios.append(
            scenario(
                f"competitor-path-{index:03d}",
                "current_tool_competitor_path",
                with_open(turns),
                {
                    "buying_question": True,
                    "objection": "competitor",
                    "decision_frame": "stay_with_current_tool",
                    "buyer_terms": ["current tool"],
                    "forbid": ["better than", "superior", "guarantee"],
                    "max_words": 95,
                },
            )
        )

    no_fit_sequences = [
        ["current tool works fine", "I only use AI lightly", "I don't want to pay"],
        ["I am happy with my current tool", "basic writing only", "I do not want another subscription"],
        ["Free is enough", "I use it once in a while", "no paid plan"],
        ["I just wanted to know", "light personal use", "too expensive"],
        ["I don't use AI much", "I do not want to pay", "should I just stay free?"],
        ["my current tool covers everything", "I only write occasionally", "no budget"],
        ["I use AI lightly", "current setup is enough", "why pay?"],
        ["I do not need advanced tools", "once a week", "I prefer free"],
        ["not buying anything", "basic tasks only", "what should I do?"],
        ["I am worried about money", "light use", "should I skip paid?"],
        ["I don't want to pay", "current tool is fine", "is Free enough?"],
        ["only simple questions", "not heavy", "no subscription"],
        ["I use it rarely", "writing only", "no paid plan for now"],
        ["I am just curious", "light use", "should I upgrade?"],
        ["I can stay with what I have", "very light use", "do I need ChatGPT paid?"],
    ]
    for index, turns in enumerate(no_fit_sequences, start=1):
        scenarios.append(
            scenario(
                f"no-fit-path-{index:03d}",
                "no_fit_path",
                with_open(turns),
                {
                    "no_fit_expected": True,
                    "decision_frame": "no_fit",
                    "buyer_terms": ["free"],
                    "forbid": ["choose pro", "buy pro", "official chatgpt plans page"],
                },
            )
        )

    objections = [
        "too expensive",
        "I don't want another subscription",
        "I already pay for another tool",
        "why Pro over Plus?",
        "Plus is cheaper though",
        "I don't want to overpay",
        "what if Pro is too much?",
        "is this worth paying for?",
        "I am price sensitive",
        "why not just use Free?",
        "my current tool is already paid",
        "another subscription is annoying",
        "why pay more than Plus?",
        "I don't want pressure",
        "is Pro really necessary?",
        "Plus seems cheaper",
        "why not start lower?",
        "I don't know if I need paid",
        "what if I cancel my other tool?",
        "why would Pro be safer?",
    ]
    for index, objection in enumerate(objections, start=1):
        scenarios.append(
            scenario(
                f"objection-{index:03d}",
                "objections",
                with_open(["I use it for coding and writing", "I use it heavily every day", objection]),
                {
                    "buying_question": True,
                    "objection": "why_pro" if "pro" in objection.lower() or "plus" in objection.lower() else "price",
                    "expected_plan": "pro" if "pro" in objection.lower() or "plus" in objection.lower() else "",
                    "decision_frame": "plus_vs_pro",
                    "buyer_terms": ["plus", "pro"],
                    "forbid": ["you may not need to switch", "what matters most"],
                },
            )
        )

    loop_sequences = [
        ["I use it for coding and writing", "I use it heavily every day", "Plus enough?", "Pro better?", "price?", "sign up?", "Plus enough though?"],
        ["I use another LLM", "coding and writing", "Plus enough?", "why switch?", "price?", "Pro better?", "how do I sign up?"],
        ["coding and writing", "heavy", "is Plus enough?", "so Pro is better?", "how much?", "what next?", "Plus enough though?"],
        ["coding", "daily heavy use", "Plus or Pro?", "Pro seems better", "price", "where do I upgrade?", "is Plus cheaper?"],
        ["writing and research", "heavy use", "should I choose Plus?", "why Pro?", "too expensive", "price", "next step"],
        ["I use Claude", "coding and writing", "why switch?", "Plus enough?", "Pro better?", "how do I sign up?", "why Plus though?"],
        ["I use it for files and coding", "heavy", "Pro seems safer", "how much is Pro?", "how do I start?", "Plus enough though?"],
        ["personal coding and writing", "heavy daily", "is Pro worth it?", "yes Pro", "price?", "official page?", "Plus enough?"],
        ["coding/writing", "a little bit on the heavy side", "Plus enough?", "Pro is better probably", "sign up", "price", "Plus enough though?"],
        ["I use another AI", "current tool is weak on files", "which plan?", "Plus or Pro?", "Pro seems better", "how much?", "what next?"],
        ["coding and writing", "heavy", "why Pro over Plus?", "too expensive", "Plus enough?", "price?", "sign up?"],
        ["writing", "heavy daily", "Plus enough?", "I don't want another subscription", "Pro better?", "how do I upgrade?", "Plus enough though?"],
        ["coding", "every day", "Pro worth it?", "Plus cheaper", "price", "where is the page?", "why Pro?"],
        ["research and writing", "heavy", "Plus or Pro", "price", "Pro probably", "next step", "Plus enough?"],
        ["code reviews and writing", "I rely on it heavily", "Plus enough?", "why not Free?", "why Pro?", "sign up?", "price?"],
        ["programming and drafting", "heavy use", "is Plus enough?", "so Pro?", "how much", "how start", "Plus enough though?"],
        ["work documents and code", "daily", "Plus enough?", "Pro is safer", "what page?", "is Plus cheaper?"],
        ["I use Gemini", "coding", "why compare?", "Plus enough?", "Pro better?", "price", "sign up?"],
        ["I already pay for another tool", "writing and coding", "why switch?", "too expensive", "Plus enough?", "Pro?", "what next?"],
        ["coding and writing", "heavy work volume", "Plus enough?", "Pro first?", "price?", "signup?", "Plus enough though?"],
    ]
    for index, turns in enumerate(loop_sequences, start=1):
        scenarios.append(
            scenario(
                f"loop-prevention-commercial-{index:03d}",
                "loop_prevention_repeated_buyer_prompts",
                with_open(turns),
                {
                    "buying_question": True,
                    "buying_signal": True,
                    "close_expected": True,
                    "expected_plan": "pro",
                    "decision_frame": "plus_vs_pro",
                    "buyer_terms": ["plus", "pro"],
                    "forbid": ["what matters most", "plan fit still needs"],
                    "max_words": 105,
                },
            )
        )

    return scenarios


def build_information_advancement_scenarios() -> list[dict[str, Any]]:
    scenarios: list[dict[str, Any]] = []
    sequences = [
        ("info-advance-moderate-plus-001", ["I use it for coding and writing", "what is the difference between Plus and Pro?"], "plus"),
        ("info-advance-moderate-plus-002", ["personal writing and light coding", "explain the paid plans"], "plus"),
        ("info-advance-moderate-plus-003", ["I use ChatGPT a few times a week for drafts", "what do the plans include?"], "plus"),
        ("info-advance-moderate-plus-004", ["coding and writing, not heavy", "what should I know before paying?"], "plus"),
        ("info-advance-moderate-plus-005", ["I mostly write and research", "tell me Free versus Plus versus Pro"], "plus"),
        ("info-advance-heavy-pro-001", ["I use it heavily every day for coding and writing", "explain the difference between Plus and Pro"], "pro"),
        ("info-advance-heavy-pro-002", ["heavy coding work all week", "what do I get with paid plans?"], "pro"),
        ("info-advance-heavy-pro-003", ["I rely on it for code reviews and writing", "which tier should I compare?"], "pro"),
        ("info-advance-heavy-pro-004", ["I am a power user and hit usage limits", "explain pricing and plans"], "pro"),
        ("info-advance-heavy-pro-005", ["serious daily writing and coding", "give me the practical plan comparison"], "pro"),
        ("info-advance-competitor-001", ["I use another AI tool for code", "what would I compare in ChatGPT?"], ""),
        ("info-advance-no-fit-001", ["I use AI rarely and do not want to pay", "what are the plan options?"], ""),
    ]
    for scenario_id, turns, expected_plan in sequences:
        expectation: dict[str, Any] = {
            "buying_question": True,
            "decision_frame": "plus_vs_pro" if expected_plan else "free_vs_paid",
            "buyer_terms": ["plus", "pro"] if expected_plan else ["free"],
            "forbid": ["what matters most", "plan fit still needs", "you may not need to switch"],
        }
        if expected_plan:
            expectation["expected_plan"] = expected_plan
        elif "rarely" in " ".join(turns):
            expectation["no_fit_expected"] = True
            expectation["decision_frame"] = "no_fit"
        scenarios.append(
            scenario(
                scenario_id,
                "information_must_advance",
                with_open(turns),
                expectation,
            )
        )
    return scenarios


def build_live_derived_application_scenarios() -> list[dict[str, Any]]:
    """Focused 4H1 proof that OpenAI-specific dialogue applies the universal sales skill."""
    return [
        scenario(
            "live-derived-chatgpt-other-ai-plus-enough",
            "plus_enough_direct_answer",
            with_open(["I use ChatGPT and other AI tools", "I use it mostly for coding and writing", "is Plus enough?"]),
            {
                "buying_question": True,
                "expected_plan": "plus",
                "decision_frame": "plus_vs_pro",
                "buyer_terms": ["coding", "writing", "plus", "pro"],
                "forbid": ["you may not need to switch", "what matters most", "plan fit still needs"],
            },
        ),
        scenario(
            "live-derived-heavy-plus-enough",
            "heavy_usage_recommendation",
            with_open(["I use it for coding and writing", "I use it heavily every day", "is Plus enough?"]),
            {
                "buying_question": True,
                "expected_plan": "pro",
                "decision_frame": "plus_vs_pro",
                "buyer_terms": ["coding", "writing", "heavy"],
                "forbid": ["plan fit still needs", "what matters most", "given you are hitting limits"],
            },
        ),
        scenario(
            "live-derived-pro-probably-better",
            "buyer_agreement_to_pro",
            with_open(["I use it for coding and writing", "I use it heavily every day", "so Pro is better for me probably"]),
            {
                "buying_question": True,
                "buying_signal": True,
                "close_expected": True,
                "expected_plan": "pro",
                "decision_frame": "plus_vs_pro",
                "buyer_terms": ["coding", "writing"],
                "forbid": ["are you using it occasionally", "what matters most"],
            },
        ),
        scenario(
            "live-derived-price-known-use",
            "price_with_known_use_case",
            with_open(["I use it for coding and writing", "I use it heavily every day", "how much are the plans?"]),
            {
                "buying_question": True,
                "expected_plan": "pro",
                "decision_frame": "plus_vs_pro",
                "buyer_terms": ["coding", "writing", "heavy"],
                "forbid": ["given you are hitting limits"],
            },
        ),
        scenario(
            "live-derived-price-explicit-limits",
            "price_with_explicit_limits_pain",
            with_open(["I use it for coding and writing", "I am hitting limits", "how much are the plans?"]),
            {
                "buying_question": True,
                "expected_plan": "pro",
                "decision_frame": "plus_vs_pro",
                "buyer_terms": ["limits"],
            },
        ),
        scenario(
            "live-derived-signup-after-recommendation",
            "signup_after_recommendation",
            with_open(["I use it for coding and writing", "I use it heavily every day", "Pro seems better", "how do I sign up?"]),
            {
                "buying_question": True,
                "buying_signal": True,
                "close_expected": True,
                "expected_plan": "pro",
                "decision_frame": "plus_vs_pro",
                "buyer_terms": ["coding", "writing"],
                "forbid": ["given you are hitting limits", "i cannot send", "book anything", "take payment"],
            },
        ),
        scenario(
            "live-derived-why-switch-competitor",
            "current_tool_competitor_path",
            with_open(["I use another LLM", "I use it for coding and writing", "why would I switch?"]),
            {
                "buying_question": True,
                "objection": "competitor",
                "decision_frame": "stay_with_current_tool",
                "buyer_terms": ["current tool"],
                "forbid": ["better than", "superior", "guarantee"],
                "max_words": 95,
            },
        ),
        scenario(
            "live-derived-current-tool-enough",
            "no_fit_path",
            with_open(["current tool works fine", "I only use AI lightly", "I don't want to pay"]),
            {
                "no_fit_expected": True,
                "decision_frame": "no_fit",
                "buyer_terms": ["free"],
                "forbid": ["choose pro", "buy pro", "official chatgpt plans page"],
            },
        ),
        scenario(
            "live-derived-too-expensive",
            "objections",
            with_open(["I use it for coding and writing", "I use it heavily every day", "too expensive"]),
            {
                "buying_question": True,
                "objection": "price",
                "decision_frame": "plus_vs_pro",
                "buyer_terms": ["plus", "pro"],
                "forbid": ["you may not need to switch", "what matters most"],
            },
        ),
        scenario(
            "live-derived-another-subscription",
            "objections",
            with_open(["I use it for coding and writing", "I use it heavily every day", "I don't want another subscription"]),
            {
                "buying_question": True,
                "objection": "price",
                "decision_frame": "plus_vs_pro",
                "buyer_terms": ["plus", "pro"],
                "forbid": ["you may not need to switch", "what matters most"],
            },
        ),
        scenario(
            "live-derived-already-pay-other-tool",
            "objections",
            with_open(["I already pay for another tool", "I use it for coding and writing", "why would I add ChatGPT?"]),
            {
                "buying_question": True,
                "objection": "competitor",
                "decision_frame": "stay_with_current_tool",
                "buyer_terms": ["current tool"],
                "forbid": ["better than", "superior", "guarantee"],
            },
        ),
        scenario(
            "live-derived-why-pro-over-plus",
            "objections",
            with_open(["I use it for coding and writing", "I use it heavily every day", "why Pro over Plus?"]),
            {
                "buying_question": True,
                "objection": "why_pro",
                "expected_plan": "pro",
                "decision_frame": "plus_vs_pro",
                "buyer_terms": ["plus", "pro"],
                "forbid": ["you may not need to switch", "what matters most"],
            },
        ),
        scenario(
            "live-derived-loop-plus-pro-price-signup",
            "loop_prevention_repeated_buyer_prompts",
            with_open(
                [
                    "I use ChatGPT and other AI tools",
                    "mostly coding and writing",
                    "I use it heavily every day",
                    "is Plus enough?",
                    "so Pro is better for me probably",
                    "how much are the plans?",
                    "how do I sign up?",
                    "Plus enough though?",
                ]
            ),
            {
                "buying_question": True,
                "buying_signal": True,
                "close_expected": True,
                "expected_plan": "pro",
                "decision_frame": "plus_vs_pro",
                "buyer_terms": ["plus", "pro"],
                "forbid": ["what matters most", "plan fit still needs", "you may not need to switch"],
                "max_words": 105,
            },
        ),
    ]


def append_turn(state: dict[str, Any], packet: dict[str, Any]) -> None:
    state.setdefault("turns", []).append(
        {
            "summary": packet.get("summary", {}),
            "continuity": packet.get("demo_session_continuity") or packet.get("conversation_continuity") or {},
            "conversation_memory": packet.get("demo_conversation_memory") or packet.get("conversation_memory") or {},
            "dialogue_manager": packet.get("dialogue_manager", {}),
            "dialogue_pragmatics": packet.get("dialogue_pragmatics", {}),
            "universal_policy_frame": packet.get("universal_policy_frame", {}),
        }
    )


def run_turn_sequence(turns: list[str], session_id: str) -> tuple[dict[str, Any], list[str]]:
    state: dict[str, Any] = {"turns": []}
    packet: dict[str, Any] = {}
    responses: list[str] = []
    for turn in turns:
        packet = build_turn(turn, state, session_id)
        responses.append(response_text(packet))
    return packet, responses


def validate_expectation(item: dict[str, Any], text: str, responses: list[str]) -> list[str]:
    failures: list[str] = []
    lowered = normalize(text)
    group = item["group"]
    turns_text = normalize(" ".join(item["turns"]))

    if RAW_URL_RE.search(text):
        failures.append("raw URL spoken")
    if FAKE_SIDE_EFFECT_RE.search(text):
        failures.append("fake side-effect claim")
    if AFFILIATION_RE.search(text):
        failures.append("unsafe OpenAI affiliation claim")
    if SUPERIORITY_RE.search(text):
        failures.append("unsupported superiority or guarantee claim")
    if VAGUE_PLAN_FIT_RE.search(text):
        failures.append("vague plan-fit language")
    explicit_limit_text = re.search(r"hitting limits|hit limits|limits are|run out|running out|blocked by limits|usage limits|avoid limits|fewer limits|hit the cap", turns_text, re.I)
    if "given you are hitting limits" in lowered and not explicit_limit_text:
        failures.append("false limit-pain claim")

    if group == "plus_enough_direct_answer":
        if "plus" not in lowered or "pro" not in lowered:
            failures.append("Plus sufficiency answer did not include Plus vs Pro frame")
        if "you may not need to switch" in lowered and ("coding" in turns_text or "plus" in turns_text):
            failures.append("competitor caveat repeated after use case or plan intent")
        if GENERIC_DISCOVERY_RE.search(text):
            failures.append("Plus sufficiency asked generic discovery instead of recommending")
        if not contains_any(lowered, ["usually enough", "lower-cost", "starting point", "compare pro", "pro is safer"]):
            failures.append("Plus sufficiency did not answer directly")

    elif group == "heavy_usage_recommendation":
        if "pro" not in lowered or "plus" not in lowered:
            failures.append("heavy use did not produce Plus vs Pro recommendation")
        if not contains_any(lowered, ["compare pro", "pro is safer", "pro is the stronger", "pro seriously", "pro first"]):
            failures.append("heavy use did not recommend Pro as serious comparison")
        if not contains_any(lowered, ["lower-cost", "cheaper", "starting point"]):
            failures.append("heavy use did not preserve Plus as lower-cost option")
        if GENERIC_DISCOVERY_RE.search(text):
            failures.append("heavy use asked another generic discovery question")

    elif group == "buyer_agreement_to_pro":
        if not re.search(r"\byes\b|based on|right|pro", text, re.I):
            failures.append("Pro agreement was not confirmed")
        if "pro" not in lowered:
            failures.append("Pro agreement did not name Pro")
        if not contains_any(lowered, ["official chatgpt plans page", "profile upgrade flow", "next step", "price"]):
            failures.append("Pro agreement did not advance to close or price comparison")
        if GENERIC_DISCOVERY_RE.search(text):
            failures.append("Pro agreement reset to discovery")

    elif group == "price_with_known_use_case":
        if not contains_any(lowered, ["free is", "no-cost", "20 dollars", "pro"]):
            failures.append("price answer missing Free/Plus/Pro price content")
        if not contains_any(lowered, ["coding", "writing", "heavy", "plus", "pro"]):
            failures.append("price answer was not tied to known use case")
        if "given you are hitting limits" in lowered:
            failures.append("price answer falsely strengthened heavy use into hitting limits")

    elif group == "price_with_explicit_limits_pain":
        if "hitting limits" not in lowered and "limits" not in lowered:
            failures.append("explicit limit pain was not used in value frame")
        if "pro" not in lowered:
            failures.append("explicit limit pain did not lean Pro")
        if not contains_any(lowered, ["20 dollars", "100 dollar", "200 dollar", "free is", "source of truth"]):
            failures.append("limit-pain price answer missing price content")

    elif group == "signup_after_recommendation":
        if not contains_any(lowered, ["official chatgpt plans page", "profile upgrade flow"]):
            failures.append("sign-up answer missing self-serve close route")
        if "pro" not in lowered:
            failures.append("sign-up close did not include known recommendation")
        if OVER_DEFENSIVE_RE.search(text):
            failures.append("sign-up close over-defended limitations")

    elif group == "current_tool_competitor_path":
        if SUPERIORITY_RE.search(text):
            failures.append("competitor path made unsupported superiority claim")
        if "current tool" not in lowered and "current setup" not in lowered and "switch" not in lowered:
            failures.append("competitor path did not frame current-tool comparison")
        if "you may not need to switch" in lowered and "plus" in turns_text:
            failures.append("competitor caveat repeated after plan intent")
        question_count = text.count("?")
        if question_count > 1:
            failures.append("competitor path asked more than one gap question")

    elif group == "no_fit_path":
        if not contains_any(lowered, ["free", "not push", "stay with", "current tool", "no paid", "stay free", "stop here"]):
            failures.append("no-fit path did not close low-pressure")
        if contains_any(lowered, ["choose pro", "compare pro first", "official chatgpt plans page"]):
            failures.append("no-fit path pushed a paid close")

    elif group == "objections":
        if "plus" not in lowered or "pro" not in lowered:
            failures.append("objection answer did not preserve Plus vs Pro contrast")
        if not contains_any(lowered, ["lower-cost", "cheaper", "limits", "heavy", "start", "if price", "if avoiding"]):
            failures.append("objection answer lacked value contrast")
        if GENERIC_DISCOVERY_RE.search(text):
            failures.append("objection handling collapsed into discovery")

    elif group == "loop_prevention_repeated_buyer_prompts":
        normalized_responses = [normalize(response) for response in responses if response]
        if len(normalized_responses) != len(set(normalized_responses)) and not contains_any(lowered, ["official chatgpt plans page", "profile upgrade flow", "next step"]):
            failures.append("loop sequence repeated a previous response exactly")
        if GENERIC_DISCOVERY_RE.search(text):
            failures.append("loop sequence final response reset to generic discovery")
        if not contains_any(lowered, ["official chatgpt plans page", "profile upgrade flow", "next step", "choose", "compare pro", "summary"]):
            failures.append("loop sequence did not advance or summarize")

    elif group == "information_must_advance":
        if not contains_any(lowered, ["free", "plus", "pro", "paid", "plan"]):
            failures.append("informational answer omitted plan facts")
        if item["expectation"].get("expected_plan") and item["expectation"]["expected_plan"] not in lowered:
            failures.append("informational answer did not convert facts into the expected recommendation")
        if not has_commercial_action(text):
            failures.append("informational answer did not end with a recommendation, decision frame, or close")
        if GENERIC_DISCOVERY_RE.search(text):
            failures.append("informational answer asked generic discovery instead of advancing")

    return failures


def run_scenario(item: dict[str, Any]) -> dict[str, Any]:
    packet, responses = run_turn_sequence(item["turns"], item["id"])
    text = response_text(packet)
    failures = validate_expectation(item, text, responses)
    score = score_commercial_response(
        response=text,
        buyer_context=" ".join(turn for turn in item["turns"] if turn != "__agent_open__"),
        expectation=item["expectation"],
        prior_responses=responses[:-1],
    )
    flags = side_effect_flags(packet)
    side_effect_failures = [key for key in SIDE_EFFECT_KEYS if flags.get(key)]
    if flags.get("live_tts_used") or flags.get("tts_provider_calls_made") or flags.get("audio_file_created"):
        side_effect_failures.append("validator must not use live TTS, provider calls, or audio files")
    failures.extend(side_effect_failures)
    critical = list(dict.fromkeys(score["critical_failures"]))
    if score["status"] != "pass":
        failures.extend(score["failures"])
    failures.extend(critical)
    status = "pass" if score["status"] == "pass" and not failures else "fail"
    return {
        "id": item["id"],
        "group": item["group"],
        "turn_count": len(item["turns"]),
        "multi_turn": item["multi_turn"],
        "status": status,
        "score": score["score"],
        "dimension_scores": score["scores"],
        "failures": list(dict.fromkeys(failures)),
        "critical_failures": critical,
        "final_response": text,
        "final_response_hash": sha12(text),
        "side_effects": flags,
    }


def write_evidence(result: dict[str, Any]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report = "\n".join(
        [
            f"# {CHECKPOINT_ID}",
            "",
            f"- Status: `{result['status']}`",
            f"- Scenario count: `{result['scenario_count']}`",
            f"- Multi-turn scenario count: `{result['multi_turn_scenario_count']}`",
            f"- Average score: `{result['average_score']}`",
            f"- Minimum score: `{result['minimum_score']}`",
            f"- Failed count: `{result['failed_count']}`",
            f"- Critical failure count: `{result['critical_failure_count']}`",
            f"- Zero-dimension-score count: `{result['zero_dimension_score_count']}`",
            f"- Side effects false: `{str(result['side_effects_false']).lower()}`",
            f"- Provider calls made: `{str(result['provider_calls_made']).lower()}`",
            f"- Live TTS calls made: `{str(result['live_tts_calls_made']).lower()}`",
            f"- Raw private transcript copied: `{str(result['raw_private_transcript_copied_to_public_evidence']).lower()}`",
            "",
            "## Group Counts",
            "",
            "```json",
            json.dumps(result["group_counts"], indent=2, sort_keys=True),
            "```",
            "",
            "## Score By Dimension",
            "",
            "```json",
            json.dumps(result["dimension_score_averages"], indent=2, sort_keys=True),
            "```",
            "",
            "## Failed Cases",
            "",
            "```json",
            json.dumps(result["failed_cases"][:20], indent=2, sort_keys=True),
            "```",
            "",
        ]
    )
    REPORT_PATH.write_text(report, encoding="utf-8")


def build_expanded_commercial_closing_scenarios() -> list[dict[str, Any]]:
    group_targets = {
        "plus_enough_direct_answer": 12,
        "heavy_usage_recommendation": 12,
        "buyer_agreement_to_pro": 10,
        "price_with_known_use_case": 12,
        "price_with_explicit_limits_pain": 8,
        "signup_after_recommendation": 10,
        "current_tool_competitor_path": 12,
        "no_fit_path": 8,
        "objections": 12,
        "loop_prevention_repeated_buyer_prompts": 12,
        "information_must_advance": 10,
    }
    scenarios = build_live_derived_application_scenarios()
    used_ids = {item["id"] for item in scenarios}
    group_counts = Counter(item["group"] for item in scenarios)

    for candidate in [*build_scenarios(), *build_information_advancement_scenarios()]:
        group = candidate["group"]
        if group not in group_targets or candidate["id"] in used_ids:
            continue
        if group_counts[group] >= group_targets[group]:
            continue
        scenarios.append(candidate)
        used_ids.add(candidate["id"])
        group_counts[group] += 1

    return scenarios


def dimension_score_averages(traces: list[dict[str, Any]]) -> dict[str, float]:
    return {
        dimension: round(sum(trace["dimension_scores"][dimension] for trace in traces) / len(traces), 2)
        for dimension in RUBRIC_DIMENSIONS
    }


def main() -> None:
    scenarios = build_expanded_commercial_closing_scenarios()
    traces = [run_scenario(item) for item in scenarios]
    failed = [trace for trace in traces if trace["status"] != "pass"]
    group_counts = Counter(trace["group"] for trace in traces)
    multi_turn_count = sum(1 for item in scenarios if item["multi_turn"])
    structure_failures: list[str] = []
    required_groups = {
        "plus_enough_direct_answer",
        "heavy_usage_recommendation",
        "buyer_agreement_to_pro",
        "price_with_known_use_case",
        "price_with_explicit_limits_pain",
        "signup_after_recommendation",
        "current_tool_competitor_path",
        "no_fit_path",
        "objections",
        "loop_prevention_repeated_buyer_prompts",
        "information_must_advance",
    }
    required_group_minimums = {
        "plus_enough_direct_answer": 12,
        "heavy_usage_recommendation": 12,
        "buyer_agreement_to_pro": 10,
        "price_with_known_use_case": 12,
        "price_with_explicit_limits_pain": 8,
        "signup_after_recommendation": 10,
        "current_tool_competitor_path": 12,
        "no_fit_path": 8,
        "objections": 12,
        "loop_prevention_repeated_buyer_prompts": 12,
        "information_must_advance": 10,
    }
    missing_groups = sorted(required_groups - set(group_counts))
    if missing_groups:
        structure_failures.append(f"missing scenario groups: {missing_groups}")
    if len(scenarios) < 100:
        structure_failures.append("scenario count below 100")
    if multi_turn_count < 75:
        structure_failures.append("multi-turn scenario count below 75")
    for group, minimum in required_group_minimums.items():
        if group_counts[group] < minimum:
            structure_failures.append(f"group {group!r} has {group_counts[group]} cases; expected at least {minimum}")

    scores = [trace["score"] for trace in traces]
    critical_count = sum(len(trace["critical_failures"]) for trace in traces)
    zero_dimension_cases = [
        trace
        for trace in traces
        if any(value == 0 for value in trace["dimension_scores"].values())
    ]
    side_effects_false = all(not any(trace["side_effects"].get(key) for key in SIDE_EFFECT_KEYS) for trace in traces)
    provider_calls = any(
        trace["side_effects"].get("provider_calls_made") or trace["side_effects"].get("tts_provider_calls_made")
        for trace in traces
    )
    live_tts_calls = any(
        trace["side_effects"].get("live_tts_used") or trace["side_effects"].get("audio_file_created")
        for trace in traces
    )
    result = {
        "status": "pass"
        if (
            not failed
            and not structure_failures
            and not zero_dimension_cases
            and sum(scores) / len(scores) >= 90
            and min(scores) >= 85
            and critical_count == 0
        )
        else "fail",
        "checkpoint_id": CHECKPOINT_ID,
        "scenario_count": len(scenarios),
        "multi_turn_scenario_count": multi_turn_count,
        "average_score": round(sum(scores) / len(scores), 2),
        "minimum_score": min(scores),
        "failed_count": len(failed) + len(structure_failures),
        "critical_failure_count": critical_count,
        "zero_dimension_score_count": len(zero_dimension_cases),
        "structure_failures": structure_failures,
        "group_counts": dict(sorted(group_counts.items())),
        "required_group_minimums": required_group_minimums,
        "dimension_score_averages": dimension_score_averages(traces),
        "side_effects_false": side_effects_false,
        "provider_calls_made": provider_calls,
        "live_tts_calls_made": live_tts_calls,
        "local_llm_calls_made": False,
        "raw_private_transcript_copied_to_public_evidence": False,
        "failed_cases": failed,
        "zero_dimension_cases": zero_dimension_cases,
        "traces": traces,
    }
    write_evidence(result)
    print(
        json.dumps(
            {
                "status": result["status"],
                "scenario_count": result["scenario_count"],
                "multi_turn_scenario_count": result["multi_turn_scenario_count"],
                "average_score": result["average_score"],
                "minimum_score": result["minimum_score"],
                "failed_count": result["failed_count"],
                "critical_failure_count": result["critical_failure_count"],
                "zero_dimension_score_count": result["zero_dimension_score_count"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    if result["status"] != "pass":
        sys.exit(1)


if __name__ == "__main__":
    main()
