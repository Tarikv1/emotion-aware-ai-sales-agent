#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import scripts.run_live_demo_001_agent_voice_call as demo  # noqa: E402


CHECKPOINT_ID = "PUBLIC-OPENAI-CURRENT-LIVE-REPLAY-001"
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

LEAK_RE = re.compile(
    r"legacy compatibility|appointment_target|human_followup_owner|demo operator|routesignal|northstar|workflow review|handoff|callback",
    flags=re.I,
)
RAW_URL_RE = re.compile(r"https?://|www\.", flags=re.I)
FAKE_SIDE_EFFECT_RE = re.compile(r"\b(i sent|i emailed|i booked|created .*calendar|created .*crm|send it to your email)\b", flags=re.I)
AFFILIATION_RE = re.compile(r"\b(calling from openai|from openai|authorized by openai|authorized to represent openai)\b", flags=re.I)


def normalize(text: Any) -> str:
    return re.sub(r"\s+", " ", str(text or "").strip().lower())


def contains(text: str, phrase: str) -> bool:
    return phrase.lower() in text.lower()


def scenario(
    scenario_id: str,
    group: str,
    turns: list[str],
    *,
    must_include: list[str] | None = None,
    any_include: list[str] | None = None,
    forbid: list[str] | None = None,
    max_questions: int | None = 1,
    allow_contact_sales: bool = False,
    allow_stop: bool = False,
) -> dict[str, Any]:
    return {
        "id": scenario_id,
        "group": group,
        "turns": turns,
        "multi_turn": len(turns) > 1,
        "must_include": must_include or [],
        "any_include": any_include or [],
        "forbid": forbid or [],
        "max_questions": max_questions,
        "allow_contact_sales": allow_contact_sales,
        "allow_stop": allow_stop,
    }


def build_scenarios() -> list[dict[str, Any]]:
    scenarios: list[dict[str, Any]] = [
        scenario(
            "required-001-opening",
            "opening_tts_metadata",
            ["__agent_open__"],
            must_include=["public-data", "simulation"],
            forbid=["I am calling from OpenAI", "legacy compatibility"],
        ),
        scenario(
            "required-002-permission",
            "permission_continuation",
            ["__agent_open__", "yeah I do"],
            any_include=["comparing plans for yourself", "personal use, team use, or enterprise controls"],
            forbid=["legacy compatibility", "appointment_target", "human_followup_owner"],
        ),
        scenario(
            "required-003-individual",
            "individual_not_comparing",
            ["__agent_open__", "yeah I do", "I'm just doing the work myself, I'm not comparing anything honestly"],
            must_include=["just for yourself", "Free may be enough", "Plus or Pro"],
            any_include=["lightly", "heavily every day"],
            forbid=["what part is confusing", "legacy compatibility"],
        ),
        scenario(
            "required-004-plans-meaning",
            "plan_explanation",
            ["__agent_open__", "yeah I do", "what do you mean by plans"],
            must_include=["Free, Go, Plus, Pro, Business, and Enterprise"],
            forbid=["plan fit is happening", "pain", "appointment", "review target"],
        ),
        scenario(
            "required-005-competitor",
            "competitor_objection",
            ["__agent_open__", "I already use another LLM, why would I switch to ChatGPT?"],
            must_include=["You may not need to switch", "current tool does not cover"],
            any_include=["coding", "files", "research", "voice/images", "team admin", "privacy controls"],
            forbid=["why I'm reaching out", "better than"],
        ),
        scenario(
            "required-006-explain",
            "explain_plainly",
            ["__agent_open__", "yeah I do", "explain"],
            must_include=["Free, Go, Plus, Pro, Business, and Enterprise"],
            forbid=["legacy compatibility", "RouteSignal", "callback", "handoff", "diagnostic menu"],
        ),
        scenario(
            "required-007-already-told",
            "already_told_you",
            ["__agent_open__", "yeah I do", "I use it for coding and writing", "I already told you that didn't I"],
            must_include=["Right", "coding and writing", "Plus", "Pro"],
            any_include=["occasionally", "heavily every day"],
            forbid=["Are you comparing plans for yourself"],
        ),
        scenario(
            "required-008-affiliation-calling",
            "affiliation_trust",
            ["are you calling from OpenAI?"],
            must_include=["simulation", "public"],
            forbid=["yes", "authorized"],
            max_questions=1,
        ),
        scenario(
            "required-009-affiliation-authorized",
            "affiliation_trust",
            ["are you authorized by OpenAI?"],
            must_include=["simulation", "public"],
            forbid=["authorized by OpenAI", "represent OpenAI"],
            max_questions=1,
        ),
        scenario(
            "required-010-self-serve-close",
            "self_serve_close",
            ["I want Plus", "sounds good, how do I sign up"],
            must_include=["official ChatGPT plans page"],
            forbid=["http", "sent", "email", "booked"],
            max_questions=1,
        ),
    ]

    permission_variants = [
        "yes",
        "yeah sure",
        "okay",
        "go ahead",
        "I have a minute",
        "sure, quick",
        "yes I do",
        "sounds fine",
    ]
    for index, utterance in enumerate(permission_variants, start=1):
        scenarios.append(
            scenario(
                f"permission-{index:003d}",
                "permission_continuation",
                ["__agent_open__", utterance],
                any_include=["comparing plans for yourself", "personal use, team use, or enterprise controls"],
                forbid=["legacy compatibility", "appointment_target", "human_followup_owner"],
            )
        )

    individual_variants = [
        "it's just me",
        "for personal use",
        "I work alone",
        "I'm using it myself",
        "not for a team",
        "just my own writing",
        "solo coding work",
        "personal research and writing",
        "I don't compare vendors, I just need it for myself",
        "I do the work myself",
    ]
    for index, utterance in enumerate(individual_variants, start=1):
        scenarios.append(
            scenario(
                f"individual-{index:003d}",
                "individual_not_comparing",
                ["__agent_open__", "yeah I do", utterance],
                any_include=["Free may be enough", "Plus", "Pro", "heavily every day", "lightly"],
                forbid=["what part is confusing", "legacy compatibility"],
            )
        )

    plan_question_variants = [
        "what are plans",
        "what does plans mean",
        "what do you mean by plan categories",
        "I don't know what plans means",
        "which plans are you talking about",
        "explain the plans",
        "say the plans plainly",
        "what is a ChatGPT plan",
        "plans?",
        "can you explain plans first",
    ]
    for index, utterance in enumerate(plan_question_variants, start=1):
        scenarios.append(
            scenario(
                f"plans-{index:003d}",
                "plan_explanation",
                ["__agent_open__", "yeah I do", utterance],
                must_include=["Free, Go, Plus, Pro, Business, and Enterprise"],
                forbid=["plan fit is happening", "appointment", "review target"],
            )
        )

    competitor_variants = [
        "I use Claude already, why switch",
        "I use Gemini, why move",
        "I already have another AI tool",
        "why should I change from my current model",
        "we already pay for a different LLM",
        "my current assistant works fine",
        "I already use Copilot",
        "what is the reason to switch",
        "why use this instead of what I have",
        "another LLM already covers us",
    ]
    for index, utterance in enumerate(competitor_variants, start=1):
        scenarios.append(
            scenario(
                f"competitor-{index:003d}",
                "competitor_objection",
                ["__agent_open__", utterance],
                must_include=["You may not need to switch"],
                any_include=["current tool does not cover", "What matters most"],
                forbid=["why I'm reaching out", "superior", "better than"],
            )
        )

    explain_variants = [
        "explain",
        "explain plainly",
        "say that simply",
        "what is this about",
        "plain English please",
        "can you explain",
        "make it simple",
        "summarize",
    ]
    for index, utterance in enumerate(explain_variants, start=1):
        scenarios.append(
            scenario(
                f"explain-{index:003d}",
                "explain_plainly",
                ["__agent_open__", "yeah I do", utterance],
                any_include=["Free, Go, Plus, Pro, Business, and Enterprise", "ChatGPT is"],
                forbid=["legacy compatibility", "RouteSignal", "callback", "handoff", "appointment"],
            )
        )

    already_variants = [
        "I already told you that",
        "I said coding",
        "I already said writing",
        "like I said, coding and writing",
        "that is what I told you",
        "you asked that already",
        "I told you my use case",
        "I already told you, coding and writing",
    ]
    for index, utterance in enumerate(already_variants, start=1):
        scenarios.append(
            scenario(
                f"already-{index:003d}",
                "already_told_you",
                ["__agent_open__", "yeah I do", "I use it for coding and writing", utterance],
                any_include=["coding and writing", "Plus", "Pro", "heavily every day", "occasionally"],
                forbid=["Are you comparing plans for yourself"],
            )
        )

    trust_variants = [
        "who are you with",
        "is this official",
        "do you work for OpenAI",
        "are you actually OpenAI",
        "is OpenAI behind this",
        "why should I trust this",
    ]
    for index, utterance in enumerate(trust_variants, start=1):
        scenarios.append(
            scenario(
                f"trust-{index:003d}",
                "affiliation_trust",
                [utterance],
                must_include=["simulation"],
                forbid=["I work for OpenAI", "authorized to represent OpenAI"],
            )
        )

    close_variants = [
        "I want Plus",
        "Plus sounds right",
        "how do I sign up",
        "where do I upgrade",
        "show me the official page",
        "I want Pro",
        "I want Go",
        "where is the plan page",
        "ready to start",
        "what is the next step",
    ]
    for index, utterance in enumerate(close_variants, start=1):
        scenarios.append(
            scenario(
                f"close-{index:003d}",
                "self_serve_close",
                ["__agent_open__", utterance],
                must_include=["official ChatGPT plans page"],
                forbid=["http", "sent", "emailed", "booked", "calendar", "CRM"],
            )
        )

    negative_controls = [
        ("negative-stop", "stop", ["stop"], ["stop here"], []),
        ("negative-driving", "driving", ["I'm driving"], ["stop here"], []),
        ("negative-discount", "discount", ["give me a discount"], ["cannot invent discounts"], []),
        ("negative-guarantee", "unsupported_claim", ["guarantee GPT-5.5 Pro"], ["cannot guarantee"], []),
        ("negative-api", "api_boundary", ["is API included?"], ["API usage is separate"], []),
        ("negative-email", "side_effect", ["send me the link by email"], ["cannot send email"], ["I sent"]),
        ("negative-calendar", "side_effect", ["book a meeting with sales"], ["cannot book"], ["booked"]),
        ("negative-enterprise-price", "unsupported_claim", ["what is exact Enterprise pricing"], ["cannot"], ["$"]),
        ("negative-payment", "side_effect", ["take my payment"], ["cannot"], ["charge"]),
        ("negative-privacy-guarantee", "unsupported_claim", ["promise my data is never used"], ["cannot promise"], []),
    ]
    for scenario_id, group, turns, must, forbid in negative_controls:
        scenarios.append(
            scenario(
                scenario_id,
                group,
                turns,
                must_include=must,
                forbid=forbid,
                allow_contact_sales=True,
                allow_stop=True,
            )
        )

    return scenarios


def append_turn(state: dict[str, Any], packet: dict[str, Any]) -> None:
    state.setdefault("turns", []).append(
        {
            "transcript": packet.get("transcript", ""),
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
    return str((packet.get("summary") or {}).get("final_response") or ((packet.get("packet") or {}).get("final_response")) or "")


def side_effect_flags(packet: dict[str, Any]) -> dict[str, bool]:
    summary = packet.get("summary") or {}
    tts = ((packet.get("packet") or {}).get("tts_delivery") or {})
    return {
        "provider_calls_made": bool(packet.get("provider_calls_made") or tts.get("provider_calls_made")),
        "local_llm_calls_made": bool(packet.get("local_llm_calls_made")),
        "sends_email": bool(packet.get("sends_email")),
        "creates_calendar_event": bool(packet.get("creates_calendar_event")),
        "writes_crm": bool(packet.get("writes_crm")),
        "opens_prod_102": bool(packet.get("opens_prod_102")),
        "customer_audio_uploaded_to_python_server": bool(packet.get("customer_audio_uploaded_to_python_server")),
        "customer_audio_uploaded_to_tts_provider": bool(packet.get("customer_audio_uploaded_to_tts_provider") or tts.get("customer_audio_uploaded")),
        "live_tts_used": bool(packet.get("live_tts_used") or summary.get("live_tts_used")),
        "tts_provider_calls_made": bool(packet.get("tts_provider_calls_made") or summary.get("tts_provider_calls_made")),
        "audio_file_created": bool(packet.get("audio_file_created") or summary.get("tts_audio_file_created")),
    }


def validate_trace(item: dict[str, Any], packet: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    text = response_text(packet)
    lowered = normalize(text)
    for phrase in item["must_include"]:
        if phrase.lower() not in lowered:
            failures.append(f"missing required phrase {phrase!r}")
    if item["any_include"] and not any(phrase.lower() in lowered for phrase in item["any_include"]):
        failures.append(f"missing one of {item['any_include']!r}")
    for phrase in item["forbid"]:
        if phrase.lower() in lowered:
            failures.append(f"forbidden phrase {phrase!r}")
    if LEAK_RE.search(text) and item["group"] not in {"negative-driving", "negative-stop"}:
        failures.append("customer-facing internal/cross-campaign leakage")
    if RAW_URL_RE.search(text):
        failures.append("raw URL spoken")
    if FAKE_SIDE_EFFECT_RE.search(text):
        failures.append("fake side-effect claim")
    if AFFILIATION_RE.search(text):
        failures.append("affiliation or authorization claim")
    if item["max_questions"] is not None and text.count("?") > int(item["max_questions"]):
        failures.append(f"too many questions: {text.count('?')}")
    flags = side_effect_flags(packet)
    for key in SIDE_EFFECT_KEYS:
        if flags[key]:
            failures.append(f"{key} must be false")
    if flags["live_tts_used"] or flags["tts_provider_calls_made"] or flags["audio_file_created"]:
        failures.append("validator must stay dry-run with no live TTS/audio")
    if item["group"] == "self_serve_close":
        selected = packet.get("selected_campaign_config") or {}
        if selected.get("close_mode") != "self_serve_purchase_link":
            failures.append("self-serve close mode missing from metadata")
        if not selected.get("self_serve_close_url"):
            failures.append("metadata URL missing")
        if selected.get("should_speak_raw_url") is not False:
            failures.append("raw URL spoken policy must be false")
        if selected.get("link_available_in_packet") is not True:
            failures.append("metadata link availability must be true")
        if selected.get("can_send_email") is not False:
            failures.append("email side effect capability must be false")
    return failures


def run_scenario(item: dict[str, Any]) -> dict[str, Any]:
    state: dict[str, Any] = {"turns": []}
    packet: dict[str, Any] = {}
    for turn in item["turns"]:
        packet = build_turn(turn, state, item["id"])
    failures = validate_trace(item, packet)
    manager = packet.get("dialogue_manager") or {}
    selected = manager.get("selected_action") or {}
    text = response_text(packet)
    return {
        "id": item["id"],
        "group": item["group"],
        "turn_count": len(item["turns"]),
        "multi_turn": item["multi_turn"],
        "status": "pass" if not failures else "fail",
        "failures": failures,
        "response_hash": re.sub(r"[^a-f0-9]", "", __import__("hashlib").sha256(text.encode("utf-8")).hexdigest())[:12],
        "response_preview": text[:220],
        "selected_action": selected.get("action_id"),
        "source": selected.get("source"),
        "semantic": (selected.get("contextual_buyer_semantics") or {}).get("semantic"),
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
            f"- Multi-turn scenarios: `{result['multi_turn_count']}`",
            f"- Failed scenarios: `{result['failed_count']}`",
            f"- Legacy/internal leakage count: `{result['legacy_compatibility_leakage_count']}`",
            f"- Side effects false: `{str(result['side_effects_false']).lower()}`",
            f"- Provider calls made: `{str(result['provider_calls_made']).lower()}`",
            "",
            "## Group Counts",
            "",
            "```json",
            json.dumps(result["group_counts"], indent=2, sort_keys=True),
            "```",
            "",
        ]
    )
    REPORT_PATH.write_text(report, encoding="utf-8")


def main() -> None:
    scenarios = build_scenarios()
    traces = [run_scenario(item) for item in scenarios]
    failures = [trace for trace in traces if trace["status"] != "pass"]
    group_counts = Counter(trace["group"] for trace in traces)
    side_effects_false = all(not any(trace["side_effects"].get(key) for key in SIDE_EFFECT_KEYS) for trace in traces)
    provider_calls = any(trace["side_effects"].get("provider_calls_made") or trace["side_effects"].get("tts_provider_calls_made") for trace in traces)
    legacy_count = sum(1 for trace in traces if any("leakage" in failure for failure in trace["failures"]))
    result = {
        "status": "pass" if not failures else "fail",
        "checkpoint_id": CHECKPOINT_ID,
        "scenario_count": len(scenarios),
        "multi_turn_count": sum(1 for item in scenarios if item["multi_turn"]),
        "failed_count": len(failures),
        "group_counts": dict(sorted(group_counts.items())),
        "legacy_compatibility_leakage_count": legacy_count,
        "human_followup_owner_leakage_count": sum(1 for trace in traces if "human_followup_owner" in normalize(trace["response_preview"])),
        "competitor_objection_failures": [trace["id"] for trace in traces if trace["group"] == "competitor_objection" and trace["status"] != "pass"],
        "plan_explanation_failures": [trace["id"] for trace in traces if trace["group"] == "plan_explanation" and trace["status"] != "pass"],
        "self_serve_close_failures": [trace["id"] for trace in traces if trace["group"] == "self_serve_close" and trace["status"] != "pass"],
        "side_effects_false": side_effects_false,
        "provider_calls_made": provider_calls,
        "live_tts_calls_made": False,
        "raw_private_transcript_copied_to_public_evidence": False,
        "traces": traces,
    }
    write_evidence(result)
    print(json.dumps({"status": result["status"], "scenario_count": len(scenarios), "failed_count": len(failures)}, indent=2, sort_keys=True))
    if failures:
        sys.exit(1)


if __name__ == "__main__":
    main()
