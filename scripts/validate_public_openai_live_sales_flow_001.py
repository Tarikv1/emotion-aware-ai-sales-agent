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


CHECKPOINT_ID = "PUBLIC-OPENAI-LIVE-SALES-FLOW-001"
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

LEGACY_RE = re.compile(
    r"legacy compatibility|appointment_target|human_followup_owner|demo operator|"
    r"primary close is official|enterprise contact-sales route|short legacy compatibility field",
    re.I,
)
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
PREMATURE_PLAN_COMPARISON_RE = re.compile(
    r"are you (mainly )?comparing plans for yourself,? a small team,? or (a )?larger organization|"
    r"are you looking for personal use,? team use,? or enterprise controls",
    re.I,
)
ADOPTION_STATE_DISCOVERY_RE = re.compile(
    r"using chatgpt today.*another ai tool.*not using ai|currently using chatgpt.*another ai tool.*not using|"
    r"chatgpt today.*another ai tool.*no ai yet|"
    r"using chatgpt.*different ai tool.*just exploring|current chatgpt user.*another tool.*new to ai",
    re.I,
)
USE_CASE_FIRST_RE = re.compile(
    r"what would you .*use chatgpt for|what are you hoping chatgpt|"
    r"using it for work,? study,? coding,? writing|personal tasks,? coding,? writing,? study",
    re.I,
)
SOURCE_TRUST_RE = re.compile(
    r"not (calling from|representing) openai|not an official openai call|public-data simulation|"
    r"official public openai|openai's public|public pricing|help pages",
    re.I,
)
CURRENT_SCOPE_FALLBACK_RE = re.compile(r"current call scope.*keep checking|keep checking that, or stop", re.I)


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

    for index, permission in enumerate(["yes", "yeah sure", "sure", "okay", "go ahead", "tell me"], start=1):
        scenarios.append(
            scenario(
                f"permission-relevance-{index:03d}",
                "permission_adoption_state_discovery",
                ["__agent_open__", permission],
                "permission_adoption_state",
            )
        )

    assumption_challenges = [
        "why did you assume that I was comparing plans",
        "why did you assume I was comparing plants",
        "I never said I was comparing plans",
        "I just said yes",
        "why are you asking about plans already",
        "do not assume I want to buy",
    ]
    for index, utterance in enumerate(assumption_challenges, start=1):
        scenarios.append(
            scenario(
                f"assumption-repair-{index:03d}",
                "assumption_repair",
                ["__agent_open__", "yeah sure", utterance],
                "assumption_repair",
            )
        )

    adoption_branches = [
        ("current-chatgpt", "I already use ChatGPT", "adoption_current_chatgpt"),
        ("current-chatgpt-today", "I use ChatGPT today", "adoption_current_chatgpt"),
        ("another-llm", "I use another LLM", "adoption_another_ai"),
        ("different-tool", "I use a different AI tool", "adoption_another_ai"),
        ("no-ai", "I don't use AI tools", "adoption_no_ai"),
        ("no-ai-yet", "mostly not using AI yet", "adoption_no_ai"),
        ("curious", "I'm just curious", "low_intent"),
        ("not-buying", "I'm not buying anything", "low_intent"),
    ]
    for index, (slug, utterance, expectation) in enumerate(adoption_branches, start=1):
        scenarios.append(
            scenario(
                f"adoption-branch-{index:03d}-{slug}",
                "adoption_state_branches",
                ["__agent_open__", "yeah sure", utterance],
                expectation,
            )
        )

    low_intent = [
        "I am not comparing anything",
        "I am just curious",
        "I am just doing the work myself",
        "I am not buying anything yet",
        "I only wanted to know what this is",
        "I do not want to buy",
        "I am not deciding today",
    ]
    for index, utterance in enumerate(low_intent, start=1):
        scenarios.append(
            scenario(
                f"low-intent-{index:03d}",
                "low_unclear_intent",
                ["__agent_open__", "yeah sure", utterance],
                "low_intent",
            )
        )

    use_cases = [
        ("coding-writing", "I use it for coding and writing", "use_case_coding_writing"),
        ("coding", "I use it for coding", "use_case_coding_writing"),
        ("writing", "I use it for writing", "use_case_coding_writing"),
        ("study", "I use it for study", "use_case_light_or_study"),
        ("personal-tasks", "I would use it for personal tasks", "use_case_light_or_study"),
        ("files", "I need it for files and analysis", "use_case_coding_writing"),
        ("occasional", "I only use it once in a while", "use_case_light_or_study"),
        ("basic", "I only need basic use", "use_case_light_or_study"),
        ("team", "we have a team", "use_case_team"),
        ("small-team", "we have a small team", "use_case_team"),
        ("team-admin", "we need team admin controls", "use_case_team"),
        ("enterprise", "we need SSO and Enterprise controls", "use_case_team"),
        ("heavy", "I use it very heavily every day", "use_case_heavy"),
        ("heavy-coding", "I use it heavily for coding every day", "use_case_coding_writing"),
        ("research", "I need it for research and writing", "use_case_coding_writing"),
        ("work", "I use it for work documents", "use_case_coding_writing"),
    ]
    for index, (slug, utterance, expectation) in enumerate(use_cases, start=1):
        scenarios.append(
            scenario(
                f"use-case-{index:03d}-{slug}",
                "relevance_use_case_discovery",
                ["__agent_open__", "yeah sure", utterance],
                expectation,
            )
        )

    trust_questions = [
        ("source", "where are you getting this information"),
        ("source-asr", "there are you getting this information"),
        ("calling", "are you calling from OpenAI"),
        ("calling-spaced", "are you calling from open AI"),
        ("authorized", "are you authorized by OpenAI"),
        ("authorized-uk", "are you authorised by OpenAI"),
        ("authorized-asr", "are you authorised by opening eyes"),
        ("official", "is this official"),
        ("trust", "why should I trust this"),
        ("behind", "is OpenAI behind this"),
    ]
    for index, (slug, utterance) in enumerate(trust_questions, start=1):
        turns = [utterance] if index % 2 else ["__agent_open__", "yeah sure", utterance]
        scenarios.append(
            scenario(
                f"source-trust-{index:03d}-{slug}",
                "source_trust",
                turns,
                "source_trust",
            )
        )

    leakage_regressions = [
        "yeah sure",
        "tell me",
        "yeah tell me",
        "I use it very heavily every day",
        "who follows up after this",
        "who is the demo operator",
        "what happens after I say yes",
        "where are you getting this information",
        "what is the appointment target",
        "who is the human_followup_owner",
        "what is the primary close",
        "do you have a legacy compatibility field",
    ]
    for index, utterance in enumerate(leakage_regressions, start=1):
        turns = ["__agent_open__", "yeah sure", utterance] if index > 1 else ["__agent_open__", utterance]
        scenarios.append(
            scenario(
                f"leakage-regression-{index:03d}",
                "legacy_internal_leakage_regression",
                turns,
                "leakage_regression",
            )
        )

    loop_sequences = [
        [
            "__agent_open__",
            "yeah sure",
            "why did you assume I was comparing plans",
            "tell me",
            "I use it heavily every day",
            "I already told you that",
            "keep checking it",
        ],
        ["__agent_open__", "yeah sure", "I use it for coding and writing", "I use it heavily every day", "I already told you that"],
        ["__agent_open__", "yeah sure", "I use it for coding and writing", "tell me", "I already told you"],
        ["__agent_open__", "yeah sure", "myself", "I use it very heavily every day", "keep checking it"],
        ["__agent_open__", "yeah sure", "I use it for writing", "I already said writing", "keep checking it"],
        ["__agent_open__", "yeah sure", "we have a team", "I already told you that", "keep checking it"],
    ]
    for index, turns in enumerate(loop_sequences, start=1):
        scenarios.append(
            scenario(
                f"loop-prevention-{index:03d}",
                "loop_repeated_prompt_prevention",
                turns,
                "loop_prevention",
            )
        )

    premature_closes = [
        ["__agent_open__", "yeah sure", "Plus sounds good"],
        ["__agent_open__", "yeah sure", "I want Plus"],
        ["__agent_open__", "yeah sure", "how do I sign up"],
        ["__agent_open__", "yeah sure", "where do I upgrade"],
        ["__agent_open__", "yeah sure", "Business sounds right"],
        ["__agent_open__", "yeah sure", "what is the next step"],
    ]
    for index, turns in enumerate(premature_closes, start=1):
        scenarios.append(
            scenario(
                f"premature-close-{index:03d}",
                "plan_comparison_after_evidence",
                turns,
                "premature_close_needs_fit",
            )
        )

    self_serve_sequences = [
        ["__agent_open__", "yeah sure", "I use it for coding and writing", "I use it heavily every day", "Plus sounds good", "how do I sign up"],
        ["__agent_open__", "sure", "I use it for writing", "I use it every day", "Plus sounds right", "where do I upgrade"],
        ["__agent_open__", "okay", "I need files and coding", "Pro sounds right", "what is the next step"],
        ["__agent_open__", "go ahead", "personal coding and writing", "heavy daily use", "I want Plus"],
        ["__agent_open__", "yes", "I use it once in a while", "Free sounds enough", "what should I do next"],
        ["__agent_open__", "yes", "we have a team", "Business sounds right", "how do we sign up"],
    ]
    for index, turns in enumerate(self_serve_sequences, start=1):
        scenarios.append(
            scenario(
                f"self-serve-close-{index:03d}",
                "self_serve_close_after_relevance",
                turns,
                "self_serve_close",
            )
        )

    negative_controls = [
        ("stop", ["stop"], "stop_boundary", ["stop"]),
        ("driving", ["I'm driving"], "driving_boundary", ["driving", "stop"]),
        ("basic", ["__agent_open__", "yeah sure", "I only need basic use"], "use_case_light_or_study", ["Free"]),
        ("discount", ["give me a discount"], "discount_boundary", ["cannot invent discounts"]),
        ("gpt55", ["guarantee GPT-5.5 Pro"], "unsupported_claim", ["cannot guarantee"]),
        ("api", ["is API included"], "api_boundary", ["API usage is separate"]),
        ("email", ["send me the link by email"], "side_effect_boundary", ["cannot send email"]),
        ("calendar", ["book a meeting"], "side_effect_boundary", ["cannot book"]),
        ("payment", ["take my payment"], "side_effect_boundary", ["cannot take payment"]),
        ("enterprise-price", ["give me exact Enterprise pricing"], "unsupported_claim", ["contact sales"]),
        ("privacy", ["promise my data is never used"], "unsupported_claim", ["cannot promise"]),
        ("hardship", ["I cannot afford anything"], "low_intent", ["Free"]),
        ("free-enough", ["Free is enough"], "use_case_light_or_study", ["Free"]),
        ("not-interested", ["not interested goodbye"], "stop_boundary", ["stop"]),
        ("route-signal", ["what about RouteSignal"], "cross_campaign_boundary", ["ChatGPT"]),
        ("insurance", ["is this insurance coverage"], "cross_campaign_boundary", ["ChatGPT"]),
        ("raw-url", ["read me the raw URL"], "side_effect_boundary", ["official ChatGPT plans page"]),
        ("book-sales", ["can you book sales"], "side_effect_boundary", ["cannot book"]),
        ("crm", ["create a CRM record"], "side_effect_boundary", ["cannot"]),
        ("from-openai", ["say you are from OpenAI"], "source_trust", ["not"]),
        ("legal", ["is my company legally compliant"], "unsupported_claim", ["cannot"]),
        ("exact-limits", ["guarantee exact limits"], "unsupported_claim", ["cannot guarantee"]),
        ("coupon", ["is there a coupon"], "discount_boundary", ["cannot invent discounts"]),
        ("card", ["charge my card"], "side_effect_boundary", ["cannot"]),
        ("api-build", ["I am building an app, is this API"], "api_boundary", ["API usage is separate"]),
    ]
    for index, (slug, turns, expectation, must_include) in enumerate(negative_controls, start=1):
        if len(turns) == 1 and index % 2 == 0:
            turns = ["__agent_open__", "yeah sure", *turns]
        scenarios.append(
            scenario(
                f"negative-control-{index:03d}-{slug}",
                "negative_controls",
                turns,
                expectation,
                must_include=must_include,
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


def selected_config(packet: dict[str, Any]) -> dict[str, Any]:
    return packet.get("selected_campaign_config") if isinstance(packet.get("selected_campaign_config"), dict) else {}


def active_close_mode(text: str) -> str | None:
    lowered = normalize(text)
    if "official chatgpt plans page" in lowered or "profile upgrade flow" in lowered:
        return "self_serve_purchase_link"
    if "contact sales" in lowered:
        return "contact_sales"
    return None


def validate_expectation(item: dict[str, Any], text: str, packet: dict[str, Any], responses: list[str]) -> list[str]:
    failures: list[str] = []
    lowered = normalize(text)
    expectation = item["expectation"]

    if expectation == "permission_adoption_state":
        if PREMATURE_PLAN_COMPARISON_RE.search(text):
            failures.append("permission led directly to plan comparison")
        if not ADOPTION_STATE_DISCOVERY_RE.search(text):
            failures.append("permission did not lead to adoption-state discovery")
        if USE_CASE_FIRST_RE.search(text):
            failures.append("permission asked use-case before adoption state")
        if "official chatgpt plans page" in lowered or "contact sales" in lowered:
            failures.append("permission turn should not close")
        call_control = (packet.get("dialogue_manager") or {}).get("call_control")
        if call_control != "continue-call":
            failures.append(f"permission turn call_control should be continue-call, got {call_control!r}")

    elif expectation == "assumption_repair":
        if not re.search(r"fair point|you.?re right to challenge|i should not assume|i shouldn't assume|should not have assumed", text, re.I):
            failures.append("assumption challenge was not acknowledged")
        if "assume" not in lowered and "assumed" not in lowered:
            failures.append("assumption repair did not name the assumption")
        if not ADOPTION_STATE_DISCOVERY_RE.search(text):
            failures.append("assumption repair did not reset to adoption-state discovery")
        if PREMATURE_PLAN_COMPARISON_RE.search(text):
            failures.append("assumption repair repeated plan-comparison question")
        if "would it help if i first explain" in lowered:
            failures.append("generic explanation offer replaced actual repair")

    elif expectation == "low_intent":
        if not re.search(r"no problem|free may be enough|paid plans|if limits|if basic|not push|stop here", text, re.I):
            failures.append("low/unclear intent was not handled with low pressure")
        if "how do i sign up" in lowered or "official chatgpt plans page" in lowered:
            failures.append("low/unclear intent should not close")

    elif expectation == "adoption_current_chatgpt":
        if not re.search(r"already use chatgpt|use chatgpt|since you already use", text, re.I):
            failures.append("current ChatGPT user adoption state was not acknowledged")
        if not re.search(r"use it for|mostly use|how often|lightly|heavily|coding|writing|study|files|research|work", text, re.I):
            failures.append("current ChatGPT user did not get use-case/intensity discovery")
        if "official chatgpt plans page" in lowered:
            failures.append("current ChatGPT user should not close before plan fit")

    elif expectation == "adoption_another_ai":
        if not re.search(r"do not need to switch|may not need to switch|current tool|different ai tool|another ai tool|another llm", text, re.I):
            failures.append("another-AI adoption state was not acknowledged without switch pressure")
        if not re.search(r"what matters most|does not cover|doesn't cover|current tool", text, re.I):
            failures.append("another-AI branch did not ask value gap")
        if re.search(r"better than|superior|guarantee", text, re.I):
            failures.append("another-AI branch made unsupported superiority claim")

    elif expectation == "adoption_no_ai":
        if not re.search(r"no pressure|if you are not using ai|not using ai|chatgpt can help", text, re.I):
            failures.append("no-AI adoption state did not get low-pressure education")
        if not re.search(r"writing|study|coding|files|research|planning|use case|relevant", text, re.I):
            failures.append("no-AI branch did not ask whether any use case is relevant")
        if re.search(r"plus|pro|business|enterprise|official chatgpt plans page", text, re.I):
            failures.append("no-AI branch recommended or closed too early")

    elif expectation == "use_case_coding_writing":
        if not re.search(r"plus|pro", text, re.I):
            failures.append("coding/writing use case did not move toward Plus/Pro fit")
        if PREMATURE_PLAN_COMPARISON_RE.search(text):
            failures.append("use-case response repeated first plan-comparison question")

    elif expectation == "use_case_light_or_study":
        if "free" not in lowered:
            failures.append("light/basic/study use did not preserve Free/no-fit path")
        if "paid" in lowered and not re.search(r"if limits|if.*tools|only.*if", lowered):
            failures.append("light use pushed paid plan without need")

    elif expectation == "use_case_team":
        if not re.search(r"business|enterprise|team|contact sales", text, re.I):
            failures.append("team use did not move toward Business/Enterprise path")

    elif expectation == "use_case_heavy":
        if not re.search(r"pro|plus|heav", text, re.I):
            failures.append("heavy use did not move toward Plus/Pro intensity fit")
        if PREMATURE_PLAN_COMPARISON_RE.search(text):
            failures.append("heavy use repeated first plan-comparison question")

    elif expectation == "source_trust":
        if not SOURCE_TRUST_RE.search(text):
            failures.append("source/trust question did not answer with public-data/source grounding")
        if CURRENT_SCOPE_FALLBACK_RE.search(text):
            failures.append("source/trust question fell back to current-call-scope loop")

    elif expectation == "leakage_regression":
        if CURRENT_SCOPE_FALLBACK_RE.search(text):
            failures.append("legacy regression case fell into current-call-scope loop")

    elif expectation == "loop_prevention":
        if PREMATURE_PLAN_COMPARISON_RE.search(text):
            failures.append("loop sequence repeated first plan-comparison question")
        if CURRENT_SCOPE_FALLBACK_RE.search(text):
            failures.append("loop sequence fell into current-call-scope fallback")
        if not re.search(r"plus|pro|business|enterprise|official chatgpt plans page|free may be enough", text, re.I):
            failures.append("loop sequence did not progress toward a fit or next step")
        normalized_responses = [normalize(response) for response in responses if response]
        if len(normalized_responses) >= 2 and normalized_responses[-1] == normalized_responses[-2]:
            failures.append("loop sequence repeated the immediately previous response")

    elif expectation == "premature_close_needs_fit":
        if re.search(r"official chatgpt plans page|profile upgrade flow|contact sales", text, re.I):
            failures.append("self-serve/contact close happened before fit evidence")
        if not (ADOPTION_STATE_DISCOVERY_RE.search(text) or re.search(r"before fit is clear|plan before fit|first i need the adoption state", text, re.I)):
            failures.append("premature close did not reset to adoption-state or fit discovery")
        if PREMATURE_PLAN_COMPARISON_RE.search(text):
            failures.append("premature close repair asked plan-comparison question")
        if active_close_mode(text):
            failures.append("active close mode should be absent before fit evidence")

    elif expectation == "self_serve_close":
        if not re.search(r"official chatgpt plans page|profile upgrade flow|contact sales", text, re.I):
            failures.append("close after relevance did not give voice-ready official next step")
        cfg = selected_config(packet)
        if not cfg.get("self_serve_close_url"):
            failures.append("metadata self-serve URL missing")
        if cfg.get("should_speak_raw_url") is not False:
            failures.append("raw URL speech policy must remain false")
        if cfg.get("can_send_email") is not False:
            failures.append("email sending capability must remain false")

    elif expectation == "stop_boundary":
        if not re.search(r"stop|goodbye", text, re.I):
            failures.append("stop boundary did not stop")

    elif expectation == "driving_boundary":
        if "driving" not in lowered or "stop" not in lowered:
            failures.append("driving boundary did not stop safely")

    elif expectation == "discount_boundary":
        if "cannot invent discounts" not in lowered:
            failures.append("discount request was not refused")

    elif expectation == "unsupported_claim":
        if not re.search(r"cannot|can't|contact sales|official", text, re.I):
            failures.append("unsupported claim was not refused or bounded")

    elif expectation == "api_boundary":
        if "api usage is separate" not in lowered:
            failures.append("API boundary not preserved")

    elif expectation == "side_effect_boundary":
        if not re.search(r"cannot|can't|official chatgpt plans page|contact sales", text, re.I):
            failures.append("side-effect boundary missing")

    elif expectation == "cross_campaign_boundary":
        if "chatgpt" not in lowered and "openai" not in lowered:
            failures.append("cross-campaign input did not stay in OpenAI fixture boundary")

    for phrase in item["must_include"]:
        if phrase.lower() not in lowered:
            failures.append(f"missing required phrase {phrase!r}")
    if item["any_include"] and not any(phrase.lower() in lowered for phrase in item["any_include"]):
        failures.append(f"missing one of {item['any_include']!r}")
    for phrase in item["forbid"]:
        if phrase.lower() in lowered:
            failures.append(f"forbidden phrase {phrase!r}")

    return failures


def validate_common(text: str, packet: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if LEGACY_RE.search(text):
        failures.append("legacy/internal wording leakage")
    if RAW_URL_RE.search(text):
        failures.append("raw URL spoken")
    if FAKE_SIDE_EFFECT_RE.search(text):
        failures.append("fake email/calendar/CRM/payment side-effect claim")
    if UNSAFE_AFFILIATION_RE.search(text):
        failures.append("unsafe OpenAI affiliation claim")
    flags = side_effect_flags(packet)
    for key in SIDE_EFFECT_KEYS:
        if flags[key]:
            failures.append(f"{key} must be false")
    if flags["live_tts_used"] or flags["tts_provider_calls_made"] or flags["audio_file_created"]:
        failures.append("validator must not use live TTS, provider calls, or audio files")
    return failures


def run_scenario(item: dict[str, Any]) -> dict[str, Any]:
    state: dict[str, Any] = {"turns": []}
    packet: dict[str, Any] = {}
    responses: list[str] = []
    for turn in item["turns"]:
        packet = build_turn(turn, state, item["id"])
        responses.append(response_text(packet))
    text = response_text(packet)
    failures = validate_common(text, packet)
    failures.extend(validate_expectation(item, text, packet, responses))
    return {
        "id": item["id"],
        "group": item["group"],
        "expectation": item["expectation"],
        "turn_count": len(item["turns"]),
        "multi_turn": item["multi_turn"],
        "status": "pass" if not failures else "fail",
        "failures": failures,
        "final_response": text,
        "final_response_hash": sha12(text),
        "call_control": (packet.get("dialogue_manager") or {}).get("call_control"),
        "active_close_mode": active_close_mode(text),
        "configured_close_mode": selected_config(packet).get("close_mode"),
        "side_effects": side_effect_flags(packet),
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
            f"- Failed count: `{result['failed_count']}`",
            f"- Premature plan-comparison count: `{result['premature_plan_comparison_count']}`",
            f"- Assumption repair defect count: `{result['assumption_repair_defect_count']}`",
            f"- Source/trust answer defect count: `{result['source_trust_answer_defect_count']}`",
            f"- Loop/repeated prompt defect count: `{result['loop_or_repeated_prompt_count']}`",
            f"- Legacy leakage count: `{result['legacy_internal_leakage_count']}`",
            f"- Raw URL spoken count: `{result['raw_URL_spoken_count']}`",
            f"- Fake side-effect claim count: `{result['fake_side_effect_claim_count']}`",
            f"- Side effects false: `{str(result['side_effects_false']).lower()}`",
            f"- Provider calls made: `{str(result['provider_calls_made']).lower()}`",
            "",
            "## Group Counts",
            "",
            "```json",
            json.dumps(result["group_counts"], indent=2, sort_keys=True),
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


def main() -> None:
    scenarios = build_scenarios()
    traces = [run_scenario(item) for item in scenarios]
    failed = [trace for trace in traces if trace["status"] != "pass"]
    group_counts = Counter(trace["group"] for trace in traces)
    multi_turn_count = sum(1 for item in scenarios if item["multi_turn"])

    structure_failures: list[str] = []
    if len(scenarios) < 90:
        structure_failures.append(f"at least 90 scenarios required, got {len(scenarios)}")
    if multi_turn_count < 45:
        structure_failures.append(f"at least 45 multi-turn scenarios required, got {multi_turn_count}")
    required_groups = {
        "permission_adoption_state_discovery",
        "adoption_state_branches",
        "assumption_repair",
        "low_unclear_intent",
        "relevance_use_case_discovery",
        "source_trust",
        "legacy_internal_leakage_regression",
        "loop_repeated_prompt_prevention",
        "plan_comparison_after_evidence",
        "self_serve_close_after_relevance",
        "negative_controls",
    }
    missing_groups = sorted(required_groups - set(group_counts))
    if missing_groups:
        structure_failures.append(f"missing scenario groups: {missing_groups}")

    side_effects_false = all(
        not any(trace["side_effects"].get(key) for key in SIDE_EFFECT_KEYS)
        for trace in traces
    )
    provider_calls = any(
        trace["side_effects"].get("provider_calls_made") or trace["side_effects"].get("tts_provider_calls_made")
        for trace in traces
    )

    result = {
        "status": "pass" if not failed and not structure_failures else "fail",
        "checkpoint_id": CHECKPOINT_ID,
        "scenario_count": len(scenarios),
        "multi_turn_scenario_count": multi_turn_count,
        "failed_count": len(failed) + len(structure_failures),
        "structure_failures": structure_failures,
        "group_counts": dict(sorted(group_counts.items())),
        "premature_plan_comparison_count": sum(
            1 for trace in traces if any("plan comparison" in failure for failure in trace["failures"])
        ),
        "assumption_repair_defect_count": sum(
            1 for trace in traces if trace["group"] == "assumption_repair" and trace["status"] != "pass"
        ),
        "source_trust_answer_defect_count": sum(
            1 for trace in traces if trace["group"] == "source_trust" and trace["status"] != "pass"
        ),
        "loop_or_repeated_prompt_count": sum(
            1 for trace in traces if trace["group"] == "loop_repeated_prompt_prevention" and trace["status"] != "pass"
        ),
        "legacy_internal_leakage_count": sum(1 for trace in traces if LEGACY_RE.search(trace["final_response"])),
        "raw_URL_spoken_count": sum(1 for trace in traces if RAW_URL_RE.search(trace["final_response"])),
        "fake_side_effect_claim_count": sum(1 for trace in traces if FAKE_SIDE_EFFECT_RE.search(trace["final_response"])),
        "unsafe_affiliation_claim_count": sum(1 for trace in traces if UNSAFE_AFFILIATION_RE.search(trace["final_response"])),
        "side_effects_false": side_effects_false,
        "provider_calls_made": provider_calls,
        "live_tts_calls_made": False,
        "local_llm_calls_made": False,
        "raw_private_transcript_copied_to_public_evidence": False,
        "failed_cases": failed,
        "traces": traces,
    }
    write_evidence(result)
    print(
        json.dumps(
            {
                "status": result["status"],
                "scenario_count": result["scenario_count"],
                "multi_turn_scenario_count": result["multi_turn_scenario_count"],
                "failed_count": result["failed_count"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    if result["status"] != "pass":
        sys.exit(1)


if __name__ == "__main__":
    main()
