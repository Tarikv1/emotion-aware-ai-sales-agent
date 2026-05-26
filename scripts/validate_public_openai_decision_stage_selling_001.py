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
    SIDE_EFFECT_KEYS,
    build_turn,
    normalize,
    response_text,
    side_effect_flags,
)


CHECKPOINT_ID = "PUBLIC-OPENAI-DECISION-STAGE-SELLING-001"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"

AFFILIATION_RE = re.compile(r"\b(calling from openai|from openai|official openai call|authorized by openai|represent openai)\b", re.I)
RAW_PRIVATE_RE = re.compile(r"LIVE-DEMO-001-[a-f0-9-]{36}|data[\\/]+private|raw-turns|browser-transcript", re.I)
FAKE_SIDE_EFFECT_RE = re.compile(
    r"\b(i sent|i emailed|i booked|created .*calendar|created .*crm|processed your card|charged your card|discount applied)\b",
    re.I,
)
UNSUPPORTED_RE = re.compile(r"\b(guarantee|guaranteed|better than claude|better than gemini|superior|unlimited with no limits)\b", re.I)
STABILITY_SOURCE_RE = re.compile(r"pre_speech_conversation_stability_guard|conversation_stability_repaired", re.I)
NO_FIT_CAVEAT_RE = re.compile(r"\b(i would not push|would not push|may not need to switch|no paid close|stay free or stop)\b", re.I)
GENERIC_DISCOVERY_RE = re.compile(
    r"are you using chatgpt today.*another ai tool|what would you mainly use chatgpt for|mostly not using ai yet|"
    r"what would you mainly use|actual use case before|adoption state",
    re.I,
)
PRICE_PARAGRAPH_RE = re.compile(r"free is the no-cost option.*20 dollars.*100 dollar.*200 dollar", re.I)
PLUS_VS_PRO_RE = re.compile(r"\bplus\b.*\bpro\b|\bpro\b.*\bplus\b", re.I)

REQUIRED_GROUP_COUNTS = {
    "opening_authority": 8,
    "ai_tool_usage_without_no_fit_collapse": 12,
    "price_objection_after_price_answer": 16,
    "pro_tier_selection": 20,
    "signup_after_pro_tier_decision": 12,
    "do_not_regress_stage": 16,
    "commercial_objection_handling_quality": 16,
    "negative_controls": 20,
}


def sha12(text: str) -> str:
    return hashlib.sha256(str(text or "").encode("utf-8")).hexdigest()[:12]


def contains_any(text: str, fragments: list[str] | tuple[str, ...] | set[str]) -> bool:
    lowered = normalize(text)
    return any(fragment.lower() in lowered for fragment in fragments)


def scenario(scenario_id: str, group: str, turns: list[str], expectation: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "id": scenario_id,
        "group": group,
        "turns": turns,
        "expectation": expectation or {},
        "multi_turn": len(turns) > 1,
    }


def with_open(turns: list[str]) -> list[str]:
    return ["__agent_open__", "yeah sure", *turns]


def manager_source(packet: dict[str, Any]) -> str:
    manager = packet.get("dialogue_manager") if isinstance(packet.get("dialogue_manager"), dict) else {}
    guard = packet.get("demo_conversation_stability_guard")
    if not isinstance(guard, dict):
        guard = packet.get("pre_speech_conversation_stability_guard") if isinstance(packet.get("pre_speech_conversation_stability_guard"), dict) else {}
    return " ".join(
        str(value or "")
        for value in [
            manager.get("final_response_source"),
            manager.get("stability_guard_reason"),
            guard.get("reason"),
        ]
    )


def memory_state(packet: dict[str, Any]) -> dict[str, Any]:
    memory = packet.get("demo_conversation_memory") or packet.get("conversation_memory") or {}
    if not isinstance(memory, dict):
        return {}
    state = memory.get("openai_chatgpt_plan_state")
    return state if isinstance(state, dict) else {}


def run_turn_sequence(turns: list[str], session_id: str) -> dict[str, Any]:
    state: dict[str, Any] = {"turns": []}
    packets: list[dict[str, Any]] = []
    responses: list[str] = []
    for turn in turns:
        packet = build_turn(turn, state, session_id)
        packets.append(packet)
        responses.append(response_text(packet))
    return {
        "turns": turns,
        "packets": packets,
        "responses": responses,
        "final_packet": packets[-1] if packets else {},
        "final_response": responses[-1] if responses else "",
        "final_source": manager_source(packets[-1]) if packets else "",
        "final_memory": memory_state(packets[-1]) if packets else {},
    }


def source_for_turn(run: dict[str, Any], index: int) -> str:
    packets = run["packets"]
    if not packets:
        return ""
    return manager_source(packets[index])


def response_for_turn(run: dict[str, Any], index: int) -> str:
    responses = run["responses"]
    if not responses:
        return ""
    return responses[index]


def build_scenarios() -> list[dict[str, Any]]:
    scenarios: list[dict[str, Any]] = []

    for index in range(1, 9):
        scenarios.append(scenario(f"opening-authority-{index:03d}", "opening_authority", ["__agent_open__"]))

    ai_tool_utterances = [
        "I used chat GPT and other tools",
        "I use ChatGPT and other tools",
        "I use another LLM",
        "I use ChatGPT and Claude",
        "I use AI tools already",
        "I already use AI tools",
        "I use Gemini for some things",
        "I use Copilot too",
        "I have another AI subscription",
        "I use Claude and ChatGPT depending on the task",
        "I use ChatGPT but also other assistants",
        "I already have an AI tool at work",
    ]
    for index, utterance in enumerate(ai_tool_utterances, start=1):
        scenarios.append(
            scenario(
                f"ai-tool-usage-gap-{index:03d}",
                "ai_tool_usage_without_no_fit_collapse",
                with_open([utterance]),
            )
        )

    price_objections = [
        "that is expensive",
        "it is expensive, why would I pay that much",
        "Pro is too expensive",
        "I do not want another subscription",
        "why would I pay that much",
        "why pay 100 or 200",
        "why 100 or 200 dollars",
        "why not just use Free",
        "paid is too much",
        "I am price sensitive",
        "I do not want to overpay",
        "that is a lot monthly",
        "why pay more than Plus",
        "what if Pro is too much",
        "why would Pro be worth it",
        "I already pay for another tool, why pay this too",
    ]
    for index, objection in enumerate(price_objections, start=1):
        scenarios.append(
            scenario(
                f"price-objection-after-price-{index:03d}",
                "price_objection_after_price_answer",
                with_open(["I use it for coding and writing", "I use it heavily every day", "how much are the plans", objection]),
            )
        )

    pro_tier_questions = [
        "which Pro should I use",
        "should I use the 100 dollar or 200 dollar Pro",
        "should I use $100 or $200 Pro",
        "I am not sure if I need the higher Pro tier",
        "I use heavily but do not know how heavy",
        "what is the difference between Pro tiers",
        "which Pro version should I choose",
        "I want to decide which version of Pro I want to go for",
        "I am not sure if I want the 100 version or 200 version",
        "do I need the higher Pro",
        "should I start with the lower Pro tier",
        "is the 200 dollar Pro necessary",
        "does the lower Pro tier make sense first",
        "how do I choose between Pro tiers",
        "I want Pro but which tier",
        "which paid Pro level should I use",
        "which Pro plan tier is right",
        "what is the practical difference between 100 and 200 Pro",
        "I might max out usage but I am not sure which Pro",
        "I use it for heavy coding and writing; which Pro should I pick",
    ]
    for index, question in enumerate(pro_tier_questions, start=1):
        scenarios.append(
            scenario(
                f"pro-tier-selection-{index:03d}",
                "pro_tier_selection",
                with_open(["I use it for coding and writing", "I use it heavily every day", question]),
            )
        )

    signup_questions = [
        "how do I sign up",
        "where do I upgrade",
        "sounds good, how do I sign up",
        "how do I get it",
        "how do I upgrade now",
        "where is the plan page",
        "show me the official page",
        "how do I start",
        "how would I get Pro",
        "what is the next step",
        "can you send me a link",
        "where do I choose the Pro tier",
    ]
    for index, question in enumerate(signup_questions, start=1):
        scenarios.append(
            scenario(
                f"signup-after-pro-tier-{index:03d}",
                "signup_after_pro_tier_decision",
                with_open(
                    [
                        "I use it for coding and writing",
                        "I use it heavily every day",
                        "I want to decide which version of Pro I want to go for",
                        question,
                    ]
                ),
            )
        )

    regression_sequences = [
        ["I use it for coding and writing", "I use it heavily every day", "Pro seems better", "which Pro should I use", "how do I sign up"],
        ["coding and writing", "heavy daily use", "Pro is safer", "should I use the 100 dollar or 200 dollar Pro", "where do I upgrade"],
        ["I use ChatGPT for files and coding", "limits slow me down", "Pro makes more sense", "which Pro tier", "show me the official page"],
        ["I use it for research and writing", "I rely on it heavily", "I think Pro", "what is the difference between Pro tiers", "how do I start"],
        ["personal coding and writing", "every day heavy", "then Pro", "I am not sure if I need the higher Pro tier", "how do I sign up"],
        ["I use another LLM for coding", "ChatGPT might help files and writing", "heavy use", "which Pro should I use", "what next"],
        ["I use ChatGPT and Claude", "coding and writing", "I use it heavily", "which Pro version should I choose", "where do I choose the Pro tier"],
        ["I use it for code reviews", "heavy work volume", "Pro probably works", "do I need the higher Pro", "how would I get Pro"],
        ["writing and research", "heavy every day", "Pro first then", "is the 200 dollar Pro necessary", "where is the plan page"],
        ["work documents and code", "heavy", "I need Pro", "how do I choose between Pro tiers", "sounds good how do I sign up"],
        ["programming and drafting", "limits are frustrating", "Pro is the stronger choice", "which Pro plan tier is right", "how do I upgrade now"],
        ["I use it for coding", "I hit usage limits", "that means Pro", "which paid Pro level should I use", "how do I get it"],
        ["I use it for files and writing", "usage headroom matters", "I should compare Pro", "what is the practical difference between 100 and 200 Pro", "can you send me a link"],
        ["I use it for coding and writing", "heavy side", "Pro fits", "I might max out usage but I am not sure which Pro", "what is the next step"],
        ["I already use AI tools", "coding workflow and files slow me down", "heavy daily use", "I want Pro but which tier", "where do I upgrade"],
        ["I use ChatGPT for coding and writing", "very heavy use", "Pro sounds right", "should I start with the lower Pro tier", "how do I sign up"],
    ]
    for index, turns in enumerate(regression_sequences, start=1):
        scenarios.append(scenario(f"do-not-regress-stage-{index:03d}", "do_not_regress_stage", with_open(turns)))

    objection_sequences = [
        ["my current tool is enough"],
        ["current tool works fine"],
        ["I already pay for another tool", "coding and writing is still slow"],
        ["not sure I need it", "I use it for writing and research"],
        ["too expensive", "I use it casually"],
        ["too expensive", "I use it for heavy coding and writing"],
        ["I do not want another subscription", "coding and writing every day"],
        ["current setup is enough"],
        ["I use Claude too", "files and coding are the weak parts"],
        ["I already have an LLM", "I hit limits with coding"],
        ["why switch", "I need better file handling"],
        ["not sure I need it", "coding and writing are important"],
        ["Plus is cheaper though", "heavy coding and writing"],
        ["why not start lower", "I use it heavily"],
        ["I already pay for another tool", "current tool covers everything"],
        ["why would I pay", "limits slow down my coding"],
    ]
    for index, turns in enumerate(objection_sequences, start=1):
        scenarios.append(scenario(f"commercial-objection-quality-{index:03d}", "commercial_objection_handling_quality", with_open(turns)))

    negative_controls = [
        ["stop"],
        ["do not call me"],
        ["are you OpenAI"],
        ["are you calling from OpenAI"],
        ["is API included"],
        ["do API tokens come with this"],
        ["give me a discount"],
        ["can you guarantee usage"],
        ["guarantee GPT 5.5 Pro"],
        ["take my payment"],
        ["send me the link by email"],
        ["book a meeting"],
        ["create a CRM record"],
        ["team plan for five people"],
        ["we need Enterprise and procurement"],
        ["what about privacy guarantees"],
        ["is my company legally compliant"],
        ["read me the raw url"],
        ["RouteSignal insurance coverage"],
        ["I cannot afford it"],
    ]
    for index, turns in enumerate(negative_controls, start=1):
        scenarios.append(scenario(f"negative-control-{index:03d}", "negative_controls", with_open(turns)))

    return scenarios


def common_failures(text: str, run: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if RAW_URL_RE.search(text):
        failures.append("raw URL spoken")
    if AFFILIATION_RE.search(text) and not re.search(r"\bnot (calling from|representing|affiliated with) openai\b", text, re.I):
        failures.append("unsafe OpenAI affiliation claim")
    if FAKE_SIDE_EFFECT_RE.search(text):
        failures.append("fake email/calendar/CRM/payment side effect")
    if RAW_PRIVATE_RE.search(text):
        failures.append("raw private transcript path copied to public evidence")
    flags = side_effect_flags(run["final_packet"])
    side_effect_failures = [key for key in SIDE_EFFECT_KEYS if flags.get(key)]
    if flags.get("live_tts_used") or flags.get("tts_provider_calls_made") or flags.get("audio_file_created"):
        side_effect_failures.append("validator must not use live TTS, provider calls, or audio files")
    failures.extend(side_effect_failures)
    return failures


def validate_opening(run: dict[str, Any]) -> list[str]:
    text = response_for_turn(run, 0)
    lowered = normalize(text)
    failures = common_failures(text, run)
    if "hi, this is maya" not in lowered:
        failures.append("opening did not identify Maya directly")
    if "chatgpt subscription plans" not in lowered:
        failures.append("opening did not say this is about ChatGPT subscription plans")
    if not contains_any(lowered, {"public plan information", "public-data", "public data", "public openai"}):
        failures.append("opening did not disclose public-source basis")
    if not contains_any(lowered, {"not calling as openai", "not calling from openai", "not representing openai", "not affiliated with openai"}):
        failures.append("opening did not avoid official OpenAI affiliation")
    if not contains_any(lowered, {"help you decide", "worth considering"}):
        failures.append("opening lacked buyer-value decision frame")
    if not all(plan in text for plan in ["Free", "Plus", "Pro", "Business", "Enterprise"]):
        failures.append("opening did not name the buyer's plan decision")
    if "do you have a minute" not in lowered:
        failures.append("opening did not ask concise time permission")
    if "testing a public-data" in lowered:
        failures.append("opening used weak testing wording")
    if "http" in lowered or "www." in lowered:
        failures.append("opening spoke a raw URL")
    if len(text.split()) > 58:
        failures.append("opening carried an overlong caveat")
    return failures


def validate_ai_tool_usage(run: dict[str, Any]) -> list[str]:
    text = run["final_response"]
    lowered = normalize(text)
    failures = common_failures(text, run)
    if NO_FIT_CAVEAT_RE.search(text):
        failures.append("mere AI-tool usage collapsed into no-fit/passive caveat")
    if not contains_any(lowered, {"current setup", "current tool", "slow", "weakest", "gap", "coding", "writing", "files", "research", "workflow"}):
        failures.append("AI-tool usage did not create a gap/use-case hypothesis")
    if STABILITY_SOURCE_RE.search(run["final_source"]):
        failures.append("stability guard owned an OpenAI selling turn")
    return failures


def validate_price_objection(run: dict[str, Any]) -> list[str]:
    text = run["final_response"]
    lowered = normalize(text)
    failures = common_failures(text, run)
    if PRICE_PARAGRAPH_RE.search(text):
        failures.append("price objection repeated the same price paragraph")
    if not contains_any(lowered, {"expensive", "price", "cost", "subscription", "overpay", "paying", "pay that much", "concern"}):
        failures.append("price objection was not acknowledged")
    if not contains_any(lowered, {"coding", "writing", "heavy", "usage headroom", "limits", "workflow", "friction"}):
        failures.append("price objection was not reframed by known use case")
    if not (
        ("plus" in lowered and "pro" in lowered and contains_any(lowered, {"start with plus", "lower-cost", "usage headroom", "limits"}))
        or ("lower pro" in lowered and "higher pro" in lowered)
    ):
        failures.append("price objection lacked a concrete decision rule")
    if NO_FIT_CAVEAT_RE.search(text) and "current tool covers everything" not in normalize(" ".join(run["turns"])):
        failures.append("price objection collapsed into no-fit without explicit no-fit signal")
    return failures


def validate_pro_tier(run: dict[str, Any]) -> list[str]:
    text = run["final_response"]
    lowered = normalize(text)
    memory = run["final_memory"]
    failures = common_failures(text, run)
    if not contains_any(lowered, {"lower pro tier", "start lower", "lower tier", "higher pro tier", "higher tier", "100", "200"}):
        failures.append("Pro-tier question was not answered as Pro-tier selection")
    if "plus" in lowered and "pro versus plus" in lowered:
        failures.append("Pro-tier selection regressed to Plus-vs-Pro")
    if "plus is" in lowered and "lower pro" not in lowered:
        failures.append("Pro-tier answer discussed Plus instead of Pro-tier choice")
    if not contains_any(lowered, {"if you are unsure", "start", "move", "maxing out", "usage", "headroom", "limits"}):
        failures.append("Pro-tier answer lacked practical decision rule")
    if not contains_any(lowered, {"official", "source of truth", "exact", "public", "limited", "help article"}):
        failures.append("Pro-tier answer lacked source-grounded caveat")
    if memory.get("buyer_decision_stage") != "pro_tier_selection":
        failures.append("memory did not record buyer_decision_stage=pro_tier_selection")
    if memory.get("active_decision_frame") != "pro_100_vs_200":
        failures.append("memory did not record active_decision_frame=pro_100_vs_200")
    if memory.get("current_buyer_question_type") != "which_pro_tier":
        failures.append("memory did not record current_buyer_question_type=which_pro_tier")
    return failures


def validate_signup_after_pro_tier(run: dict[str, Any]) -> list[str]:
    text = run["final_response"]
    lowered = normalize(text)
    memory = run["final_memory"]
    failures = common_failures(text, run)
    if not contains_any(lowered, {"official chatgpt plans page", "profile upgrade flow"}):
        failures.append("signup close did not use self-serve route")
    if not contains_any(lowered, {"lower pro tier", "lower pro", "higher pro", "higher tier", "maximum usage", "maxing out", "headroom"}):
        failures.append("signup close ignored active Pro-tier decision")
    if "plus" in lowered and not contains_any(lowered, {"lower pro", "higher pro"}):
        failures.append("signup after Pro-tier reset to Plus-vs-Pro")
    if memory.get("buyer_decision_stage") != "self_serve_close":
        failures.append("memory did not record buyer_decision_stage=self_serve_close")
    if memory.get("active_decision_frame") != "pro_100_vs_200":
        failures.append("memory did not preserve active_decision_frame=pro_100_vs_200")
    if memory.get("current_buyer_question_type") != "signup":
        failures.append("memory did not record current_buyer_question_type=signup")
    return failures


def validate_no_regression(run: dict[str, Any]) -> list[str]:
    text = run["final_response"]
    responses_after_pro = run["responses"][-2:]
    combined_after_pro = normalize(" ".join(responses_after_pro))
    memory = run["final_memory"]
    failures = common_failures(text, run)
    if GENERIC_DISCOVERY_RE.search(combined_after_pro):
        failures.append("stage regressed to adoption/use-case discovery after Pro-tier decision")
    if contains_any(combined_after_pro, {"next decision is pro versus plus", "plus versus pro", "compare plus versus pro"}):
        failures.append("stage regressed to Plus-vs-Pro after Pro-tier decision")
    normalized_responses = [normalize(item) for item in run["responses"] if item]
    if len(normalized_responses) != len(set(normalized_responses)):
        failures.append("same recommendation repeated after stage changed")
    if memory.get("should_not_regress_to_prior_decision_stage") is not True:
        failures.append("memory did not set should_not_regress_to_prior_decision_stage")
    if memory.get("active_decision_frame") != "pro_100_vs_200":
        failures.append("memory did not preserve Pro-tier decision frame through close")
    return failures


def validate_commercial_objection(run: dict[str, Any]) -> list[str]:
    text = run["final_response"]
    lowered = normalize(text)
    turns_text = normalize(" ".join(run["turns"]))
    failures = common_failures(text, run)
    explicit_no_fit = contains_any(turns_text, {"current tool is enough", "current tool works fine", "current setup is enough", "current tool covers everything", "use it casually"})
    if explicit_no_fit:
        if not contains_any(lowered, {"would not push", "stay", "free", "no paid", "current tool"}):
            failures.append("explicit no-fit objection was not disqualified cleanly")
        if contains_any(lowered, {"choose pro", "buy pro"}):
            failures.append("explicit no-fit path pushed Pro")
    else:
        if NO_FIT_CAVEAT_RE.search(text) and not contains_any(lowered, {"unless", "gap", "limits"}):
            failures.append("fit may remain but response collapsed into repeated no-fit caveat")
        if not contains_any(lowered, {"gap", "coding", "writing", "files", "limits", "usage headroom", "lower-cost", "current tool", "workflow"}):
            failures.append("commercial objection lacked specific gap/value reframe")
    if contains_any(lowered, {"better than claude", "better than gemini", "superior"}):
        failures.append("unsupported superiority claim")
    return failures


def validate_negative_control(run: dict[str, Any]) -> list[str]:
    text = run["final_response"]
    lowered = normalize(text)
    turns_text = normalize(" ".join(run["turns"]))
    failures = common_failures(text, run)
    if "stop" in turns_text or "do not call" in turns_text:
        if not contains_any(lowered, {"stop", "no problem"}):
            failures.append("stop request not honored")
    if "openai" in turns_text and "?" in turns_text:
        if not contains_any(lowered, {"not calling from openai", "not representing openai", "not affiliated"}):
            failures.append("OpenAI affiliation boundary missing")
    if "api" in turns_text or "tokens" in turns_text:
        if not contains_any(lowered, {"api usage is separate", "separate from chatgpt"}):
            failures.append("API boundary missing")
    if "discount" in turns_text:
        if "cannot invent discounts" not in lowered:
            failures.append("discount boundary missing")
    if "guarantee" in turns_text:
        if not contains_any(lowered, {"cannot guarantee", "official limits", "can change"}):
            failures.append("guarantee boundary missing")
    if contains_any(turns_text, {"team", "enterprise", "procurement"}):
        if not contains_any(lowered, {"business", "enterprise", "contact sales", "team"}):
            failures.append("team/enterprise path missing")
    return failures


GROUP_VALIDATORS = {
    "opening_authority": validate_opening,
    "ai_tool_usage_without_no_fit_collapse": validate_ai_tool_usage,
    "price_objection_after_price_answer": validate_price_objection,
    "pro_tier_selection": validate_pro_tier,
    "signup_after_pro_tier_decision": validate_signup_after_pro_tier,
    "do_not_regress_stage": validate_no_regression,
    "commercial_objection_handling_quality": validate_commercial_objection,
    "negative_controls": validate_negative_control,
}


def run_scenario(item: dict[str, Any]) -> dict[str, Any]:
    run = run_turn_sequence(item["turns"], item["id"])
    validator = GROUP_VALIDATORS[item["group"]]
    failures = validator(run)
    return {
        "id": item["id"],
        "group": item["group"],
        "turn_count": len(item["turns"]),
        "multi_turn": item["multi_turn"],
        "status": "pass" if not failures else "fail",
        "failures": list(dict.fromkeys(failures)),
        "final_response": run["final_response"],
        "final_response_hash": sha12(run["final_response"]),
        "final_source": run["final_source"],
        "final_memory": {
            key: run["final_memory"].get(key)
            for key in [
                "buyer_decision_stage",
                "active_decision_frame",
                "last_decision_question_answered",
                "current_buyer_question_type",
                "should_not_regress_to_prior_decision_stage",
            ]
        },
        "side_effects": side_effect_flags(run["final_packet"]),
    }


def write_evidence(result: dict[str, Any]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report = "\n".join(
        [
            "# PUBLIC-OPENAI-DECISION-STAGE-SELLING-001",
            "",
            f"- Status: `{result['status']}`",
            f"- Scenario count: `{result['scenario_count']}`",
            f"- Multi-turn scenario count: `{result['multi_turn_scenario_count']}`",
            f"- Failed count: `{result['failed_count']}`",
            f"- Side effects false: `{str(result['side_effects_false']).lower()}`",
            f"- Provider calls made: `{str(result['provider_calls_made']).lower()}`",
            f"- Live TTS calls made: `{str(result['live_tts_calls_made']).lower()}`",
            f"- Raw private transcript copied: `{str(result['raw_private_transcript_copied_to_public_evidence']).lower()}`",
            "",
            "## Group Counts",
            "",
            json.dumps(result["group_counts"], indent=2, sort_keys=True),
            "",
            "## Failed Cases",
            "",
            json.dumps(result["failed_cases"][:30], indent=2, sort_keys=True),
            "",
        ]
    )
    REPORT_PATH.write_text(report, encoding="utf-8")


def main() -> None:
    scenarios = build_scenarios()
    traces = [run_scenario(item) for item in scenarios]
    failed = [trace for trace in traces if trace["status"] != "pass"]
    group_counts = Counter(item["group"] for item in scenarios)
    missing_groups = [group for group in REQUIRED_GROUP_COUNTS if group not in group_counts]
    structure_failures: list[str] = []
    if missing_groups:
        structure_failures.append(f"missing scenario groups: {missing_groups}")
    for group, expected_count in REQUIRED_GROUP_COUNTS.items():
        if group_counts[group] < expected_count:
            structure_failures.append(f"group {group} has {group_counts[group]} scenarios, expected at least {expected_count}")
    if len(scenarios) < 120:
        structure_failures.append("scenario count below 120")
    multi_turn_count = sum(1 for item in scenarios if item["multi_turn"])
    if multi_turn_count < 90:
        structure_failures.append("multi-turn scenario count below 90")

    provider_calls = any(
        trace["side_effects"].get("provider_calls_made") or trace["side_effects"].get("tts_provider_calls_made")
        for trace in traces
    )
    live_tts_calls = any(
        trace["side_effects"].get("live_tts_used")
        or trace["side_effects"].get("tts_provider_calls_made")
        or trace["side_effects"].get("audio_file_created")
        for trace in traces
    )
    side_effects_false = not any(any(bool(value) for value in trace["side_effects"].values()) for trace in traces)

    result = {
        "checkpoint_id": CHECKPOINT_ID,
        "status": "pass" if not failed and not structure_failures and side_effects_false and not provider_calls and not live_tts_calls else "fail",
        "scenario_count": len(scenarios),
        "multi_turn_scenario_count": multi_turn_count,
        "group_counts": dict(sorted(group_counts.items())),
        "required_group_counts": REQUIRED_GROUP_COUNTS,
        "failed_count": len(failed),
        "structure_failures": structure_failures,
        "failed_cases": failed,
        "side_effects_false": side_effects_false,
        "provider_calls_made": provider_calls,
        "live_tts_calls_made": live_tts_calls,
        "raw_private_transcript_copied_to_public_evidence": False,
        "latest_live_derived_cases_included": [
            "I used chat GPT and other tools",
            "how much are the plans -> it is expensive, why would I pay that much",
            "which version of Pro / 100 versus 200 Pro",
            "how do I sign up after Pro-tier context",
        ],
    }
    write_evidence(result)
    print(
        json.dumps(
            {
                "status": result["status"],
                "scenario_count": result["scenario_count"],
                "multi_turn_scenario_count": result["multi_turn_scenario_count"],
                "failed_count": result["failed_count"],
                "structure_failures": result["structure_failures"],
                "side_effects_false": result["side_effects_false"],
                "provider_calls_made": result["provider_calls_made"],
                "live_tts_calls_made": result["live_tts_calls_made"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    if result["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
