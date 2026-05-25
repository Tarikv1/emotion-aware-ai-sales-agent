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

import scripts.run_live_demo_001_agent_voice_call as demo  # noqa: E402


CHECKPOINT_ID = "PUBLIC-OPENAI-LIVE-SALES-READINESS-001"
FIXTURE_PATH = ROOT / "runtime" / "campaigns" / "examples" / "public-openai-chatgpt-plans.json"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"
TMP_DIR = ROOT / ".tmp" / CHECKPOINT_ID

SIDE_EFFECT_KEYS = [
    "provider_calls_made",
    "local_llm_calls_made",
    "sends_email",
    "creates_calendar_event",
    "writes_crm",
    "opens_prod_102",
    "customer_audio_uploaded_to_python_server",
    "customer_audio_uploaded_to_tts_provider",
]

FORBIDDEN_CUSTOMER_RE = re.compile(
    r"i should not assume buying intent|first i need the adoption state|\badoption state\b|"
    r"legacy compatibility field|primary close is official self-serve plan page|"
    r"demo operator for simulation notes|human_followup_owner|appointment_target|"
    r"inbound demo request|missed callbacks|handoffs|owner, callback, or handoff|"
    r"what part is unclear\?|plan fit still needs the actual use case",
    re.I,
)
ROUTESIGNAL_RE = re.compile(r"routesignal|route signal|northstar workflow labs|northstar", re.I)
ROUTESIGNAL_CONTEXT_RE = re.compile(r"inbound demo request|missed callbacks|handoffs|callback reminders", re.I)
RAW_URL_RE = re.compile(r"https?://|www\.", re.I)
FAKE_SIDE_EFFECT_RE = re.compile(
    r"\b(i sent|i emailed|i booked|created .*calendar|created .*crm|send it to your email|"
    r"i will email|i'll email|i scheduled|i charged|processed your card)\b",
    re.I,
)
UNSAFE_AFFILIATION_RE = re.compile(
    r"\b(i am calling from openai|i'm calling from openai|authorized by openai|"
    r"authorised by openai|authorized to represent openai|i represent openai)\b",
    re.I,
)
ASR_REPAIR_RE = re.compile(r"only caught part|repeat the question|asr|audio was unclear", re.I)
ADOPTION_LOOP_RE = re.compile(r"using chatgpt today.*another ai tool.*not using ai|first i need", re.I)
OFFICIAL_SOURCE_RE = re.compile(r"official .*pricing page|source of truth|official chatgpt pricing page", re.I)
PLUS_PRO_RE = re.compile(r"\bplus\b.*\bpro\b|\bpro\b.*\bplus\b", re.I)


def normalize(text: Any) -> str:
    return re.sub(r"\s+", " ", str(text or "").strip().lower())


def sha12(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def scenario(
    scenario_id: str,
    group: str,
    turns: list[str],
    expectation: str,
    *,
    must_include: list[str] | None = None,
    any_include: list[str] | None = None,
    forbid: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "id": scenario_id,
        "group": group,
        "turns": turns,
        "expectation": expectation,
        "must_include": must_include or [],
        "any_include": any_include or [],
        "forbid": forbid or [],
        "multi_turn": len(turns) > 1,
    }


def build_scenarios() -> list[dict[str, Any]]:
    scenarios: list[dict[str, Any]] = []

    alias_utterances = [
        "I use chachu PT and other AI tools",
        "I use chachu BT and another AI tool",
        "I use chachu p t for writing",
        "I use chachu b t for research",
        "I use chachupt every day",
        "I use chat jpt",
        "I use chat gbt",
        "I use chat g p t",
        "I use chat gb t",
        "I use chatgbt",
        "I use chat gpt plan",
        "I use chat jpt plan",
        "why would I switch to chat jpt",
        "why switch from chachu PT",
        "why switch from chachu BT",
        "chachu PT for coding",
        "chachu BT plus",
        "chat jpt for coding and writing",
        "chat gbt plus for files",
        "chat g p t for research",
        "I already use chachu pt",
        "I already use chachu bt",
        "I am using chat jpt and Claude",
        "I use chatgbt and other AI tools",
        "so I use chachu BT and other AI tools at the same time",
        "I'm using chachu PT and other AI tools",
        "chat jpt handles my writing",
        "chat gbt handles coding",
    ]
    for index, utterance in enumerate(alias_utterances, start=1):
        prefix = ["__agent_open__", "yeah sure"] if index % 3 else ["__agent_open__", "yes"]
        scenarios.append(
            scenario(
                f"asr-alias-{index:03d}",
                "asr_alias_recognition",
                [*prefix, utterance],
                "asr_alias",
            )
        )

    price_questions = [
        "how much are the plans",
        "how much is Plus",
        "how much is Pro",
        "what do I get for 20 dollars",
        "before I move forward I want to know the price",
        "is it expensive",
        "but like how much are they before I move forward I would like to know the price",
        "what are the prices",
        "tell me the cost first",
        "what does Plus cost",
        "what does Pro cost",
        "how much monthly",
        "what is the monthly price",
        "what is the paid plan price",
        "what do the paid tiers cost",
        "price before I decide",
        "what do I pay for Plus",
        "what do I pay for Pro",
        "is Plus twenty dollars",
        "is Pro one hundred dollars",
        "how much is Business",
        "how much is Enterprise",
        "is there a free option",
        "is Free really free",
        "tell me the public plan structure and price",
        "I asked the price",
        "why are you not answering the price",
        "answer the price directly",
    ]
    for index, utterance in enumerate(price_questions, start=1):
        turns = ["__agent_open__", "yeah sure", utterance] if index % 4 else [utterance]
        scenarios.append(
            scenario(
                f"price-question-{index:03d}",
                "price_questions",
                turns,
                "price_question",
            )
        )

    plus_sequences = [
        ["I use it for coding and writing", "is Plus enough"],
        ["I use it for coding and writing", "a little bit on the heavy side", "is Plus going to be enough for my use case"],
        ["I use it for coding and writing", "heavy side", "should I start with Plus or Pro"],
        ["I use it for coding", "I use it every day", "is Plus enough"],
        ["I use it for writing", "a little heavy", "is Plus enough"],
        ["chat jpt for coding and writing", "a little bit on the heavy side", "is Plus enough"],
        ["I already use ChatGPT", "coding and writing", "is Pro worth it"],
        ["I already use chachu PT", "coding and writing", "is Pro worth it"],
        ["I use chat gbt for files and code", "heavy daily", "is Plus enough"],
        ["I use it for coding and writing", "I hit limits", "is Pro worth it"],
        ["I use it for coding and writing", "I do not hit limits", "is Plus enough"],
        ["I use it for coding and writing", "before upgrading, is Plus enough"],
        ["I use it for research and writing", "heavy side", "Plus or Pro"],
        ["personal coding and writing", "heavy side", "what should I choose"],
        ["coding and writing", "advanced tools all week", "is Pro worth it"],
        ["writing and code", "every day", "is Plus enough"],
        ["I use ChatGPT for coding and writing", "a little bit heavy", "which plan"],
        ["chachu BT for coding", "heavy", "Plus enough or Pro"],
        ["chat jpt for writing", "heavy daily", "Plus enough"],
        ["I use it for coding and writing", "a little bit on the heavy side", "why Pro"],
        ["I use it for coding and writing", "a little bit on the heavy side", "what do I get for 20 dollars"],
        ["I use it for coding and writing", "a little bit on the heavy side", "how much is Plus"],
    ]
    for index, suffix in enumerate(plus_sequences, start=1):
        scenarios.append(
            scenario(
                f"plus-fit-{index:03d}",
                "plus_sufficiency_recommendation",
                ["__agent_open__", "yeah sure", *suffix],
                "plus_sufficiency",
            )
        )

    ask_questions = [
        "what do you want me to do",
        "what are you asking me",
        "what is the next step",
        "I do not understand what you want from me",
        "what do you need from me",
        "what are you trying to get me to do",
        "so what do you want me to do what are you asking me",
        "what is your ask",
        "what is the point here",
        "what decision are you asking for",
        "do you want me to buy now",
        "are you asking me to sign up",
        "what should I do next",
        "what are you asking after I said coding and writing",
        "plainly what do you want",
        "what action do you expect",
        "I do not understand the ask",
        "what is this call asking",
    ]
    for index, utterance in enumerate(ask_questions, start=1):
        turns = ["__agent_open__", "yeah sure", "I use it for coding and writing", utterance]
        scenarios.append(
            scenario(
                f"plain-ask-{index:03d}",
                "plain_ask_explanation",
                turns,
                "plain_ask",
            )
        )

    stability_sequences = [
        ["I use it for coding and writing", "how much are the plans"],
        ["I use it for coding and writing", "is Plus enough"],
        ["I use it for coding and writing", "how do I sign up"],
        ["I already use chachu PT", "how much is Plus"],
        ["I already use chat jpt", "what do I get for 20 dollars"],
        ["I use another LLM", "why would I switch to chat jpt"],
        ["I use it for coding and writing", "a little bit on the heavy side", "is Plus enough"],
        ["I use it for coding and writing", "a little bit on the heavy side", "how much is Pro"],
        ["I use it for coding and writing", "what are you asking me"],
        ["I use it for coding and writing", "can you send me a link"],
        ["I use it for coding and writing", "is API included"],
        ["I use it for coding and writing", "give me a discount"],
        ["I use chachu BT and other AI tools", "price before I decide"],
        ["I use chat gbt and other AI tools", "Plus enough"],
        ["I use chat jpt", "what is the next step"],
        ["I use it for coding and writing", "answer the price directly"],
        ["I use it for coding and writing", "I asked the price"],
        ["I use another LLM", "what are you asking me"],
    ]
    for index, suffix in enumerate(stability_sequences, start=1):
        scenarios.append(
            scenario(
                f"direct-priority-{index:03d}",
                "stability_guard_direct_question_priority",
                ["__agent_open__", "yeah sure", *suffix],
                "direct_priority",
            )
        )

    loop_sequences = [
        ["I use another LLM", "how much are the plans", "but I asked the price"],
        ["I use another LLM", "how much are the plans", "why are you not answering"],
        ["I use chachu PT", "how much are the plans", "but I asked the price"],
        ["I use chat jpt", "how much is Plus", "answer the price directly"],
        ["I use it for coding and writing", "is Plus enough", "I already told you coding and writing"],
        ["I use it for coding and writing", "a little heavy", "why are you asking that again"],
        ["I use it for coding and writing", "how much are the plans", "but like how much are they"],
        ["I use another LLM", "why would I switch", "how much are the plans"],
        ["I use chat gbt", "what do you want me to do", "what are you asking me"],
        ["I use chachu BT and other AI tools", "why would I switch", "how much is Pro"],
        ["I use chat jpt", "is Plus enough", "a little bit heavy"],
        ["I use it for coding and writing", "is Plus enough", "is Pro worth it"],
        ["I use another AI tool", "before I move forward I want price", "I asked price"],
        ["I use chachu PT and other AI tools", "price", "why not answer"],
    ]
    for index, suffix in enumerate(loop_sequences, start=1):
        scenarios.append(
            scenario(
                f"loop-prevention-{index:03d}",
                "loop_prevention",
                ["__agent_open__", "yeah sure", *suffix],
                "loop_prevention",
            )
        )

    contamination_turns = [
        "what did you mean by that",
        "I did not understand the previous question",
        "what part are you asking about",
        "explain the last question",
        "what is unclear",
        "why are you asking",
        "what is the workflow",
        "what is the owner",
        "what is a handoff",
        "what is a callback",
        "what is RouteSignal",
        "what is Northstar Workflow Labs",
        "are you asking about inbound demo requests",
        "are callbacks part of this",
    ]
    for index, utterance in enumerate(contamination_turns, start=1):
        scenarios.append(
            scenario(
                f"contamination-negative-{index:03d}",
                "routesignal_contamination_negative_check",
                ["__agent_open__", "yeah sure", "I use it for coding and writing", utterance],
                "contamination_negative",
            )
        )

    safety_questions = [
        ("are you from OpenAI", "affiliation"),
        ("are you calling from OpenAI", "affiliation"),
        ("do you represent OpenAI", "affiliation"),
        ("is this official OpenAI", "affiliation"),
        ("is API included", "api"),
        ("is API usage included with Plus", "api"),
        ("I am building an app, is this API", "api"),
        ("can you send me a link", "link"),
        ("send me the link by email", "email"),
        ("read me the raw URL", "raw_url"),
        ("give me a discount", "discount"),
        ("is there a coupon", "discount"),
        ("guarantee GPT-5.5 Pro", "unsupported"),
        ("guarantee exact limits", "unsupported"),
        ("promise my data is never used", "unsupported"),
        ("is my company legally compliant", "unsupported"),
        ("take my payment", "payment"),
        ("book a meeting", "calendar"),
        ("create a CRM record", "crm"),
        ("exact Enterprise pricing", "enterprise_price"),
        ("what if Free is enough", "free"),
        ("I cannot afford it", "free"),
    ]
    for index, (utterance, expectation) in enumerate(safety_questions, start=1):
        turns = [utterance] if index % 5 == 0 else ["__agent_open__", "yeah sure", utterance]
        scenarios.append(
            scenario(
                f"source-safety-{index:03d}",
                "source_trust_and_safety_preservation",
                turns,
                expectation,
            )
        )

    return scenarios


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


def build_turn(transcript: str, state: dict[str, Any], session_id: str) -> dict[str, Any]:
    packet = demo.build_browser_demo_turn_packet(
        transcript=transcript,
        campaign_id=demo.DEFAULT_CAMPAIGN_ID,
        stage=demo.DEFAULT_STAGE,
        input_type="agent-open" if transcript == "__agent_open__" else "speech-final",
        silence_count=0,
        cases_path=demo.DEFAULT_CASES_PATH,
        private_out=TMP_DIR / session_id,
        live_tts=False,
        force_key_missing=True,
        timeout_seconds=8.0,
        campaign_config_path=FIXTURE_PATH,
        session_id=session_id,
        session_state=state,
        asr_confidence=0.94,
        generic_live_tts_allowed=False,
    )
    append_turn(state, packet)
    return packet


def response_text(packet: dict[str, Any]) -> str:
    summary = packet.get("summary") or {}
    body = packet.get("packet") or {}
    manager = packet.get("dialogue_manager") or {}
    return str(summary.get("final_response") or body.get("final_response") or manager.get("final_response") or "")


def side_effect_flags(packet: dict[str, Any]) -> dict[str, bool]:
    body = packet.get("packet") or {}
    delivery = body.get("tts_delivery") or {}
    summary = packet.get("summary") or {}
    return {
        "provider_calls_made": bool(packet.get("provider_calls_made") or delivery.get("provider_calls_made")),
        "local_llm_calls_made": bool(packet.get("local_llm_calls_made")),
        "sends_email": bool(packet.get("sends_email")),
        "creates_calendar_event": bool(packet.get("creates_calendar_event")),
        "writes_crm": bool(packet.get("writes_crm")),
        "opens_prod_102": bool(packet.get("opens_prod_102")),
        "customer_audio_uploaded_to_python_server": bool(packet.get("customer_audio_uploaded_to_python_server")),
        "customer_audio_uploaded_to_tts_provider": bool(packet.get("customer_audio_uploaded_to_tts_provider") or delivery.get("customer_audio_uploaded")),
        "live_tts_used": bool(packet.get("live_tts_used") or summary.get("live_tts_used")),
        "tts_provider_calls_made": bool(packet.get("tts_provider_calls_made") or summary.get("tts_provider_calls_made")),
        "audio_file_created": bool(packet.get("audio_file_created") or summary.get("tts_audio_file_created")),
    }


def dialogue_manager(packet: dict[str, Any]) -> dict[str, Any]:
    return packet.get("dialogue_manager") if isinstance(packet.get("dialogue_manager"), dict) else {}


def final_response_source(packet: dict[str, Any]) -> str:
    return str(dialogue_manager(packet).get("final_response_source") or "")


def stability_reason(packet: dict[str, Any]) -> str:
    return str(dialogue_manager(packet).get("stability_guard_reason") or "")


def candidate_trace_texts(packet: dict[str, Any]) -> list[str]:
    manager = dialogue_manager(packet)
    texts = [
        response_text(packet),
        str(manager.get("final_response") or ""),
        str((manager.get("selected_action") or {}).get("candidate_response") or ""),
        str((manager.get("contextual_buyer_semantics") or {}).get("candidate_response") or ""),
        str((packet.get("demo_conversation_stability_guard") or {}).get("candidate_response") or ""),
    ]
    return [text for text in texts if text]


def has_source_fact(fixture: dict[str, Any], fact_id: str) -> bool:
    return any(
        item.get("fact_id") == fact_id and item.get("allowed_in_speech") is True
        for item in fixture.get("source_grounded_claims", [])
        if isinstance(item, dict)
    )


def validate_common(item: dict[str, Any], text: str, packet: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    lowered = normalize(text)
    if not text.strip():
        failures.append("empty final response")
    if FORBIDDEN_CUSTOMER_RE.search(text):
        failures.append("forbidden customer-facing internal or legacy phrase")
    if RAW_URL_RE.search(text):
        failures.append("raw URL spoken")
    if FAKE_SIDE_EFFECT_RE.search(text):
        failures.append("fake side-effect claim")
    if UNSAFE_AFFILIATION_RE.search(text):
        failures.append("unsafe OpenAI affiliation claim")
    for phrase in item["must_include"]:
        if phrase.lower() not in lowered:
            failures.append(f"missing required phrase {phrase!r}")
    if item["any_include"] and not any(phrase.lower() in lowered for phrase in item["any_include"]):
        failures.append(f"missing one of {item['any_include']!r}")
    for phrase in item["forbid"]:
        if phrase.lower() in lowered:
            failures.append(f"forbidden phrase {phrase!r}")
    for trace_text in candidate_trace_texts(packet):
        if FORBIDDEN_CUSTOMER_RE.search(trace_text):
            failures.append("forbidden phrase in final/candidate trace")
            break
    effects = side_effect_flags(packet)
    for key in SIDE_EFFECT_KEYS:
        if effects.get(key):
            failures.append(f"side effect flag true: {key}")
    if effects["live_tts_used"] or effects["tts_provider_calls_made"] or effects["audio_file_created"]:
        failures.append("validator made live TTS or audio side effect")
    return failures


def validate_expectation(item: dict[str, Any], text: str, packet: dict[str, Any], fixture: dict[str, Any]) -> list[str]:
    failures = validate_common(item, text, packet)
    lowered = normalize(text)
    expectation = item["expectation"]

    if expectation == "asr_alias":
        if ASR_REPAIR_RE.search(text):
            failures.append("ASR alias was treated as unclear audio")
        if ADOPTION_LOOP_RE.search(text):
            failures.append("ASR alias fell into adoption-state loop")
        if not re.search(r"chatgpt|current tool|current setup|another ai tool|switch|coding|writing|useful comparison", text, re.I):
            failures.append("ASR alias was not handled as ChatGPT or AI-tool context")

    elif expectation == "price_question":
        if not OFFICIAL_SOURCE_RE.search(text):
            failures.append("price answer lacks official source-of-truth caveat")
        if not re.search(r"free|plus|pro|business|enterprise|20|100|200|25", text, re.I):
            failures.append("price question did not answer plan price/category directly")
        if ADOPTION_LOOP_RE.search(text):
            failures.append("price question was refused for adoption-state discovery")
        amounts = set(re.findall(r"\b\d{2,4}\b", lowered))
        allowed = {"20", "25", "100", "200"}
        if amounts - allowed:
            failures.append(f"unsupported exact price numbers: {sorted(amounts - allowed)!r}")
        if "discount" in lowered and "cannot invent" not in lowered:
            failures.append("price answer appeared to invent a discount")
        if "plus" in lowered and "20" in lowered and not has_source_fact(fixture, "plus_price_20_001"):
            failures.append("Plus exact price spoken without fixture source fact")
        if ("100" in lowered or "200" in lowered) and not has_source_fact(fixture, "pro_tiers_100_200_001"):
            failures.append("Pro exact price spoken without fixture source fact")

    elif expectation == "plus_sufficiency":
        if not PLUS_PRO_RE.search(text):
            failures.append("Plus sufficiency did not compare Plus and Pro directly")
        if not re.search(r"coding|writing|limits|heavy|first paid plan|safer starting point", text, re.I):
            failures.append("Plus sufficiency ignored known use case or intensity")
        if re.search(r"occasionally or heavily every day|what would you mainly use", text, re.I) and re.search(r"heavy|little bit on the heavy side|limits", " ".join(item["turns"]), re.I):
            failures.append("Plus sufficiency repeated use-case/intensity discovery after it was known")

    elif expectation == "plain_ask":
        if not re.search(r"not asking you to do anything yet|helping you decide|next useful choice|plus versus pro", text, re.I):
            failures.append("plain ask was not explained in buyer-facing sales language")
        if re.search(r"appointment|review|callback|raw url|legacy", text, re.I):
            failures.append("plain ask leaked appointment/review/link/internal framing")

    elif expectation == "direct_priority":
        if ADOPTION_LOOP_RE.search(text):
            failures.append("direct question lost to adoption-state discovery")
        if stability_reason(packet) == "conversation_stability_repaired":
            failures.append("stability guard rewrote direct OpenAI question")
        source = final_response_source(packet)
        if source not in {"contextual_buyer_semantics", "universal_conversation_policy", "universal_response_shape"}:
            failures.append(f"unexpected final_response_source {source!r}")
        if source != "contextual_buyer_semantics" and "api" not in " ".join(item["turns"]).lower():
            failures.append(f"direct OpenAI response did not come from campaign adapter: {source!r}")

    elif expectation == "loop_prevention":
        if ADOPTION_LOOP_RE.search(text):
            failures.append("loop sequence repeated adoption-state discovery")
        if ASR_REPAIR_RE.search(text):
            failures.append("loop sequence fell into ASR repair")
        if "price" in " ".join(item["turns"]).lower() and not re.search(r"source of truth|20|100|200|free|plus|pro", text, re.I):
            failures.append("loop sequence did not answer repeated price request")
        prior_responses = [str((turn.get("summary") or {}).get("final_response") or "") for turn in (packet.get("session_state") or {}).get("turns", [])]
        if text and prior_responses.count(text) > 1:
            failures.append("duplicate final response repeated")

    elif expectation == "contamination_negative":
        for trace_text in candidate_trace_texts(packet):
            if ROUTESIGNAL_RE.search(trace_text) or ROUTESIGNAL_CONTEXT_RE.search(trace_text):
                failures.append("RouteSignal contamination in final/candidate trace")
                break

    elif expectation == "affiliation":
        if not re.search(r"not .*openai|not calling from openai|not representing openai|public-data simulation", text, re.I):
            failures.append("affiliation boundary not preserved")

    elif expectation == "api":
        if not re.search(r"api usage is separate|api .*separate", text, re.I):
            failures.append("API boundary not preserved")

    elif expectation == "link":
        if "official chatgpt plans page" not in lowered:
            failures.append("link request did not use voice-safe official page label")
        if re.search(r"i sent|emailed|booked|http", text, re.I):
            failures.append("link request claimed side effect or raw URL")

    elif expectation == "email":
        if not re.search(r"cannot send email|can't send email", text, re.I):
            failures.append("email side-effect boundary not preserved")

    elif expectation == "raw_url":
        if RAW_URL_RE.search(text) or "raw url" not in lowered:
            failures.append("raw URL boundary not preserved")

    elif expectation == "discount":
        if not re.search(r"cannot invent discounts|no discount", text, re.I):
            failures.append("discount boundary not preserved")

    elif expectation in {"unsupported", "enterprise_price"}:
        if not re.search(r"cannot guarantee|cannot promise|cannot give|cannot quote|contact sales|official", text, re.I):
            failures.append("unsupported claim boundary not preserved")

    elif expectation in {"payment", "calendar", "crm"}:
        if not re.search(r"cannot take payment|cannot book|cannot create|cannot", text, re.I):
            failures.append("side-effect boundary not preserved")

    elif expectation == "free":
        if "free" not in lowered:
            failures.append("Free/no-fit boundary not preserved")

    return failures


def run_scenario(item: dict[str, Any], fixture: dict[str, Any]) -> dict[str, Any]:
    state: dict[str, Any] = {}
    packet: dict[str, Any] | None = None
    session_id = f"{CHECKPOINT_ID.lower()}-{item['id']}"
    for turn in item["turns"]:
        packet = build_turn(turn, state, session_id)
    assert packet is not None
    text = response_text(packet)
    failures = validate_expectation(item, text, packet, fixture)
    effects = side_effect_flags(packet)
    return {
        "id": item["id"],
        "group": item["group"],
        "expectation": item["expectation"],
        "multi_turn": item["multi_turn"],
        "turn_count": len(item["turns"]),
        "status": "pass" if not failures else "fail",
        "failures": failures,
        "final_response": text,
        "final_response_hash": sha12(text),
        "final_response_source": final_response_source(packet),
        "stability_guard_reason": stability_reason(packet),
        "repair_chain": list(dialogue_manager(packet).get("repair_chain") or []),
        "side_effects": effects,
    }


def write_report(result: dict[str, Any]) -> None:
    failed = result["failed_cases"]
    lines = [
        f"# {CHECKPOINT_ID}",
        "",
        f"- Status: {result['status']}",
        f"- Scenario count: {result['scenario_count']}",
        f"- Multi-turn scenario count: {result['multi_turn_scenario_count']}",
        f"- Failed count: {result['failed_count']}",
        f"- Side effects false: {result['side_effects_false']}",
        f"- Provider calls made: {result['provider_calls_made']}",
        f"- Live TTS calls made: {result['live_tts_calls_made']}",
        f"- Raw private transcript copied to public evidence: {result['raw_private_transcript_copied_to_public_evidence']}",
        "",
        "## Group Counts",
        "",
    ]
    for group, count in sorted(result["group_counts"].items()):
        lines.append(f"- {group}: {count}")
    lines.extend(["", "## Defect Counts", ""])
    for key in [
        "asr_product_alias_issue_count",
        "internal_policy_language_leak_count",
        "price_question_refusal_count",
        "plan_recommendation_stall_count",
        "legacy_field_leakage_count",
        "routesignal_contamination_count",
        "loop_or_repeated_prompt_count",
        "stability_override_count",
        "fake_side_effect_claim_count",
        "raw_url_spoken_count",
    ]:
        lines.append(f"- {key}: {result[key]}")
    lines.extend(["", "## Failed Cases", ""])
    if not failed:
        lines.append("- None")
    else:
        for item in failed[:40]:
            lines.append(f"- {item['id']} ({item['group']}): {'; '.join(item['failures'])}")
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    scenarios = build_scenarios()
    traces = [run_scenario(item, fixture) for item in scenarios]
    failed = [trace for trace in traces if trace["status"] != "pass"]
    all_side_effects = [trace["side_effects"] for trace in traces]
    side_effects_false = all(not flags.get(key) for flags in all_side_effects for key in SIDE_EFFECT_KEYS)
    provider_calls = any(flags.get("provider_calls_made") for flags in all_side_effects)
    live_tts_calls = any(flags.get("live_tts_used") or flags.get("tts_provider_calls_made") or flags.get("audio_file_created") for flags in all_side_effects)
    all_text = "\n".join(trace["final_response"] for trace in traces)

    structure_failures: list[str] = []
    if len(scenarios) < 140:
        structure_failures.append(f"scenario_count below 140: {len(scenarios)}")
    multi_turn_count = sum(1 for item in scenarios if item["multi_turn"])
    if multi_turn_count < 90:
        structure_failures.append(f"multi_turn_scenario_count below 90: {multi_turn_count}")

    result = {
        "checkpoint_id": CHECKPOINT_ID,
        "status": "pass" if not failed and not structure_failures and side_effects_false and not provider_calls and not live_tts_calls else "fail",
        "scenario_count": len(scenarios),
        "multi_turn_scenario_count": multi_turn_count,
        "group_counts": dict(Counter(item["group"] for item in scenarios)),
        "failed_count": len(failed),
        "failed_cases": failed,
        "structure_failures": structure_failures,
        "side_effects_false": side_effects_false,
        "provider_calls_made": provider_calls,
        "local_llm_calls_made": any(flags.get("local_llm_calls_made") for flags in all_side_effects),
        "live_tts_calls_made": live_tts_calls,
        "raw_private_transcript_copied_to_public_evidence": False,
        "asr_product_alias_issue_count": sum(1 for trace in failed if trace["group"] == "asr_alias_recognition"),
        "internal_policy_language_leak_count": len(FORBIDDEN_CUSTOMER_RE.findall(all_text)),
        "price_question_refusal_count": sum(1 for trace in failed if trace["group"] == "price_questions"),
        "plan_recommendation_stall_count": sum(1 for trace in failed if trace["group"] == "plus_sufficiency_recommendation"),
        "legacy_field_leakage_count": len(re.findall(r"legacy compatibility|appointment_target|human_followup_owner|demo operator", all_text, re.I)),
        "routesignal_contamination_count": sum(1 for trace in failed if trace["group"] == "routesignal_contamination_negative_check"),
        "loop_or_repeated_prompt_count": sum(1 for trace in failed if trace["group"] == "loop_prevention"),
        "stability_override_count": sum(1 for trace in failed if trace["group"] == "stability_guard_direct_question_priority"),
        "fake_side_effect_claim_count": len(FAKE_SIDE_EFFECT_RE.findall(all_text)),
        "raw_url_spoken_count": len(RAW_URL_RE.findall(all_text)),
        "traces": traces,
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_report(result)
    print(json.dumps({k: result[k] for k in ["checkpoint_id", "status", "scenario_count", "multi_turn_scenario_count", "failed_count"]}, indent=2))
    if structure_failures:
        for failure in structure_failures:
            print(f"STRUCTURE: {failure}", file=sys.stderr)
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
