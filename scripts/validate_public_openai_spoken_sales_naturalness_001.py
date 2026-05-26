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

from scripts.validate_commercial_sales_performance_001 import RAW_URL_RE, SIDE_EFFECT_KEYS, normalize  # noqa: E402
from runtime.campaigns import public_openai_chatgpt_plans_dialogue as dialogue  # noqa: E402


CHECKPOINT_ID = "PUBLIC-OPENAI-SPOKEN-SALES-NATURALNESS-001"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"
FIXTURE_PATH = ROOT / "runtime" / "campaigns" / "examples" / "public-openai-chatgpt-plans.json"

REQUIRED_GROUP_COUNTS = {
    "source_note_wording_banned": 20,
    "pro_tier_answer_naturalness": 16,
    "midcycle_plan_change_followup": 16,
    "repeated_answer_prevention": 20,
    "internal_process_wording_banned": 20,
    "terminal_acceptance_polite_close": 12,
    "heavy_headroom_state_preservation": 16,
}
MIN_SCENARIOS = 120
MIN_MULTI_TURN_SCENARIOS = 90

SOURCE_NOTE_RE = re.compile(
    r"\b(article lists|article describes|according to|source of truth|source-grounded|"
    r"official sources state|official sources say|official openai sources|the official page says|"
    r"the official chatgpt pricing page is the source of truth|exact tier details should be checked against official openai sources)\b",
    re.I,
)
TRUST_ALLOWED_RE = re.compile(r"\b(public openai pricing|public openai help|openai pricing|help pages|not representing openai)\b", re.I)
INTERNAL_PROCESS_RE = re.compile(
    r"\b(we already have the use case|adoption state|i should not assume buying intent|"
    r"plan fit still needs|current call scope|internal policy|legacy compatibility|"
    r"human_followup_owner|appointment_target|fixture|semantic|classifier|state machine)\b",
    re.I,
)
PRO_TIER_DECISION_RE = re.compile(
    r"\b(lower pro tier|lower tier|100 dollar|100|higher pro tier|higher tier|200 dollar|200|maximum headroom|most headroom)\b",
    re.I,
)
PRO_TIER_REGRESSION_RE = re.compile(r"\b(plus versus pro|pro versus plus|compare plus versus pro|next decision is pro versus plus)\b", re.I)
MIDCYCLE_DIRECT_RE = re.compile(r"\b(mid-?month|switch|move up|change|billing|proration|prorated|plan terms|terms|before switching)\b", re.I)
INVENTED_BILLING_RE = re.compile(
    r"\b(will be prorated|will prorate|guaranteed prorated|you will get a refund|you get a credit|"
    r"charged only the difference|billing definitely)\b",
    re.I,
)
TERMINAL_ASK_RE = re.compile(r"\?\s*$|\b(are you|what would|which plan are|do you want me|should i|can i help)\b", re.I)
ACCEPTANCE_ACK_RE = re.compile(r"\b(sounds good|got it|that is the cleanest path|start with|no problem|you are set)\b", re.I)


def sha12(text: str) -> str:
    return hashlib.sha256(str(text or "").encode("utf-8")).hexdigest()[:12]


def call_control(packet: dict[str, Any]) -> str:
    return str(packet.get("call_control") or "")


def memory_state(packet: dict[str, Any]) -> dict[str, Any]:
    memory = packet.get("demo_conversation_memory") or packet.get("conversation_memory") or {}
    if not isinstance(memory, dict):
        return {}
    state = memory.get("openai_chatgpt_plan_state")
    return state if isinstance(state, dict) else {}


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


def load_campaign() -> dict[str, Any]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def side_effect_flags_for_packet(_packet: dict[str, Any]) -> dict[str, bool]:
    return {
        "provider_calls_made": False,
        "local_llm_calls_made": False,
        "sends_email": False,
        "creates_calendar_event": False,
        "writes_crm": False,
        "opens_prod_102": False,
        "customer_audio_uploaded_to_python_server": False,
        "customer_audio_uploaded_to_tts_provider": False,
        "live_tts_used": False,
        "tts_provider_calls_made": False,
        "audio_file_created": False,
    }


def run_turn_sequence(turns: list[str], session_id: str) -> dict[str, Any]:
    campaign = load_campaign()
    state: dict[str, Any] = {}
    prior_turns: list[dict[str, Any]] = []
    packets: list[dict[str, Any]] = []
    responses: list[str] = []
    for turn in turns:
        if turn in {"__agent_open__", "yeah sure"}:
            continue
        normalized = normalize(turn)
        frame = dialogue.classify_turn(
            campaign=campaign,
            transcript=turn,
            normalized=normalized,
            turns=prior_turns,
            previous_question=None,
            previous_question_type=str(state.get("last_agent_question_type") or "none"),
            conversation_stage="qualification",
            active_gap=None,
            confirmed_gaps=[],
            cleared_gaps=[],
            pending_callback=False,
            pending_appointment=False,
            candidate_gaps=[],
        ) or {}
        response = str(frame.get("candidate_response") or "")
        memory_update = dialogue.memory_update_for_turn(
            transcript=turn,
            turns=prior_turns,
            final_response=response,
            campaign=campaign,
            current_memory={"openai_chatgpt_plan_state": state} if state else None,
        ) or state
        state = dict(memory_update)
        action_id = str(frame.get("action_id") or "continue_with_session_policy")
        packet = {
            "summary": {"final_response": response, "call_control": "end-call" if action_id == "end_call_stop_request" else "continue-call"},
            "transcript": turn,
            "semantic": frame.get("semantic"),
            "call_control": "end-call" if action_id == "end_call_stop_request" else "continue-call",
            "conversation_memory": {"openai_chatgpt_plan_state": state},
        }
        packets.append(packet)
        responses.append(response)
        prior_turns.append(
            {
                "transcript": turn,
                "summary": packet["summary"],
                "conversation_memory": packet["conversation_memory"],
            }
        )
    final_packet = packets[-1] if packets else {}
    return {
        "turns": turns,
        "packets": packets,
        "responses": responses,
        "final_packet": final_packet,
        "final_response": responses[-1] if responses else "",
        "final_memory": memory_state(final_packet),
        "call_control": call_control(final_packet),
    }


def compact_signature(text: str) -> str:
    lowered = normalize(text)
    lowered = re.sub(r"\b(100|one hundred)\b", "100", lowered)
    lowered = re.sub(r"\b(200|two hundred)\b", "200", lowered)
    tokens = [
        token
        for token in re.findall(r"[a-z0-9]+", lowered)
        if token
        not in {
            "the",
            "a",
            "an",
            "and",
            "or",
            "to",
            "for",
            "of",
            "if",
            "you",
            "are",
            "is",
            "it",
            "with",
            "that",
            "this",
            "i",
            "would",
        }
    ]
    return " ".join(tokens[:28])


def common_failures(run: dict[str, Any]) -> list[str]:
    text = run["final_response"]
    failures: list[str] = []
    if SOURCE_NOTE_RE.search(text):
        failures.append("source-note wording was spoken")
    if INTERNAL_PROCESS_RE.search(text):
        failures.append("internal/process wording was spoken")
    if RAW_URL_RE.search(text):
        failures.append("raw URL was spoken")
    flags = side_effect_flags_for_packet(run["final_packet"])
    for key in SIDE_EFFECT_KEYS:
        if flags.get(key):
            failures.append(f"side effect flag was true: {key}")
    if flags.get("live_tts_used") or flags.get("tts_provider_calls_made") or flags.get("audio_file_created"):
        failures.append("validator used live TTS, provider calls, or audio output")
    return failures


def validate_source_note_wording(run: dict[str, Any]) -> list[str]:
    text = run["final_response"]
    failures = common_failures(run)
    if run.get("expectation", {}).get("source_trust") and not TRUST_ALLOWED_RE.search(text):
        failures.append("source/trust answer did not preserve public OpenAI grounding")
    if "where are you getting" in normalize(" ".join(run["turns"])) and not TRUST_ALLOWED_RE.search(text):
        failures.append("source question was not answered with natural public OpenAI page wording")
    return failures


def validate_pro_tier_answer(run: dict[str, Any]) -> list[str]:
    text = run["final_response"]
    lowered = normalize(text)
    failures = common_failures(run)
    if not PRO_TIER_DECISION_RE.search(text):
        failures.append("Pro-tier answer lacked 100-vs-200 decision rule")
    if PRO_TIER_REGRESSION_RE.search(text) or ("plus is" in lowered and "lower pro" not in lowered):
        failures.append("Pro-tier answer regressed to Plus-vs-Pro")
    if not re.search(r"\b(start|choose|move|upgrade|headroom|limits|ceiling)\b", lowered):
        failures.append("Pro-tier answer lacked practical buyer guidance")
    if "http" in lowered or "www." in lowered:
        failures.append("Pro-tier answer spoke a raw URL")
    memory = run["final_memory"]
    if memory.get("active_decision_frame") != "pro_100_vs_200":
        failures.append("memory did not preserve active_decision_frame=pro_100_vs_200")
    if memory.get("buyer_decision_stage") != "pro_tier_selection":
        failures.append("memory did not preserve buyer_decision_stage=pro_tier_selection")
    if memory.get("openai_recommended_path") != "pro":
        failures.append("Pro-tier buyer was not preserved on Pro recommendation path")
    return failures


def validate_midcycle_followup(run: dict[str, Any]) -> list[str]:
    text = run["final_response"]
    lowered = normalize(text)
    failures = common_failures(run)
    if not MIDCYCLE_DIRECT_RE.search(text):
        failures.append("mid-cycle/change follow-up was not answered directly")
    if not re.search(r"\b(can't promise|cannot promise|depends on|check|current plan terms|plan page|terms)\b", lowered):
        failures.append("mid-cycle answer did not preserve billing-term safety")
    if INVENTED_BILLING_RE.search(text):
        failures.append("mid-cycle answer invented billing/proration mechanics")
    previous = run["responses"][-2] if len(run["responses"]) >= 2 else ""
    if normalize(text) == normalize(previous):
        failures.append("mid-cycle follow-up repeated the prior Pro-tier response exactly")
    if compact_signature(text) == compact_signature(previous):
        failures.append("mid-cycle follow-up repeated the prior Pro-tier response signature")
    if not re.search(r"\b(start|lower pro|move up|only if|limits|headroom)\b", lowered):
        failures.append("mid-cycle answer lacked practical buying guidance")
    return failures


def validate_repeated_answer_prevention(run: dict[str, Any]) -> list[str]:
    responses = [item for item in run["responses"] if item]
    text = run["final_response"]
    lowered = normalize(text)
    failures = common_failures(run)
    normalized_responses = [normalize(item) for item in responses]
    if len(normalized_responses) != len(set(normalized_responses)):
        failures.append("exact response hash repeated in one scenario")
    signatures = [compact_signature(item) for item in responses if item]
    if len(signatures) != len(set(signatures)):
        failures.append("same response signature repeated in one scenario")
    if run["expectation"].get("same_question_repeat") and not re.search(r"\b(simple version|put simply|short version|simpler)\b", lowered):
        failures.append("same repeated question was not answered with simpler wording")
    if run["expectation"].get("new_detail") and not re.search(r"\b(mid-?month|move up|billing|terms|switch|headroom|limits|lower pro)\b", lowered):
        failures.append("new follow-up detail was not answered")
    return failures


def validate_internal_process_wording(run: dict[str, Any]) -> list[str]:
    return common_failures(run)


def validate_terminal_acceptance(run: dict[str, Any]) -> list[str]:
    text = run["final_response"]
    failures = common_failures(run)
    if not ACCEPTANCE_ACK_RE.search(text):
        failures.append("terminal acceptance did not receive concise close guidance")
    if TERMINAL_ASK_RE.search(text):
        failures.append("terminal acceptance was followed by a new sales question")
    if len(text.split()) > 55:
        failures.append("terminal close was too long")
    if "?" in text:
        failures.append("terminal close included a question")
    if call_control(run["final_packet"]) not in {"end-call", "continue-call", ""}:
        failures.append("terminal close used unexpected call_control")
    return failures


def validate_heavy_headroom_state(run: dict[str, Any]) -> list[str]:
    text = run["final_response"]
    lowered = normalize(text)
    memory = run["final_memory"]
    failures = common_failures(run)
    if memory.get("openai_usage_intensity") not in {"heavy", "medium_heavy"}:
        failures.append("heavy/headroom language did not set heavy or medium_heavy usage")
    if memory.get("active_decision_frame") != "pro_100_vs_200":
        failures.append("heavy/headroom Pro-tier buyer did not keep pro_100_vs_200 frame")
    if memory.get("openai_recommended_path") != "pro":
        failures.append("heavy/headroom Pro-tier buyer was downgraded away from Pro")
    if "plus is" in lowered and "lower pro" not in lowered and "lower cost" not in lowered:
        failures.append("heavy/headroom answer drifted back to Plus")
    if not re.search(r"\b(pro|headroom|limits|100|200|lower tier|higher tier)\b", lowered):
        failures.append("heavy/headroom answer did not preserve Pro-tier decision language")
    return failures


GROUP_VALIDATORS = {
    "source_note_wording_banned": validate_source_note_wording,
    "pro_tier_answer_naturalness": validate_pro_tier_answer,
    "midcycle_plan_change_followup": validate_midcycle_followup,
    "repeated_answer_prevention": validate_repeated_answer_prevention,
    "internal_process_wording_banned": validate_internal_process_wording,
    "terminal_acceptance_polite_close": validate_terminal_acceptance,
    "heavy_headroom_state_preservation": validate_heavy_headroom_state,
}


def build_scenarios() -> list[dict[str, Any]]:
    scenarios: list[dict[str, Any]] = []

    source_turns = [
        ["how much are the plans"],
        ["I use it for coding and writing", "how much does Pro cost"],
        ["I use it for coding and writing", "I use it heavily every day", "which Pro should I choose"],
        ["is API included with ChatGPT Plus"],
        ["does the API come with Pro"],
        ["where are you getting this information"],
        ["are these official OpenAI prices"],
        ["can I trust this plan information"],
        ["what happens if I change plans later"],
        ["can I start lower and upgrade later"],
        ["I use it for writing", "what is the price"],
        ["I use it heavily", "what is the 200 dollar tier"],
        ["I need headroom", "what is the difference between Pro tiers"],
        ["what is ChatGPT Business pricing"],
        ["what is Enterprise pricing"],
        ["does Plus include API tokens"],
        ["what do I get for 20 dollars"],
        ["why is Pro more expensive"],
        ["should I choose 100 or 200 Pro"],
        ["what page should I check before upgrading"],
    ]
    for index, turns in enumerate(source_turns, start=1):
        tag = " source_trust" if any("where are you getting" in turn or "trust" in turn or "official" in turn for turn in turns) else ""
        scenarios.append(
            scenario(
                f"source-note-banned-{index:03d}",
                "source_note_wording_banned",
                with_open(turns),
                {"source_trust": bool(tag)},
            )
        )

    pro_questions = [
        "should I use the 100 dollar or 200 dollar Pro",
        "which Pro should I use",
        "do I need the 200 dollar one",
        "I use heavily but I am not sure",
        "what is the practical difference between 100 and 200 Pro",
        "should I start with the lower Pro tier",
        "is the higher Pro tier necessary",
        "which paid Pro level should I use",
        "I might max out usage but I am not sure which Pro",
        "I use it for heavy coding and writing; which Pro should I pick",
        "I want Pro but which tier",
        "does the lower Pro tier make sense first",
        "how do I choose between Pro tiers",
        "I need headroom but I do not know how much",
        "I am deciding between the two Pro prices",
        "is 200 worth it over 100 for Pro",
    ]
    for index, question in enumerate(pro_questions, start=1):
        scenarios.append(
            scenario(
                f"pro-tier-natural-{index:03d}",
                "pro_tier_answer_naturalness",
                with_open(["I use it for coding and writing", "I do use my tools a little heavily maybe more than a little", question]),
            )
        )

    midcycle_questions = [
        "what happens if I move to 200 mid-month",
        "can I start at 100 and upgrade later",
        "if I choose 100 now can I move up",
        "should I start at 200 right away",
        "if I start lower and move to 200 in the middle of the month what happens",
        "does changing from 100 to 200 mid month change billing",
        "can I switch Pro tiers after I hit the ceiling",
        "what if I choose lower now and need more headroom later",
        "can I upgrade from the lower Pro tier later",
        "should I avoid 100 because I might need 200 later",
        "if I move up after two weeks what should I expect",
        "do I lose anything if I start at 100 and upgrade",
        "can I change tier once I know my usage",
        "is there a penalty for starting lower and moving up",
        "what about proration if I change to 200",
        "what are the billing mechanics if I switch tiers",
    ]
    for index, question in enumerate(midcycle_questions, start=1):
        scenarios.append(
            scenario(
                f"midcycle-followup-{index:03d}",
                "midcycle_plan_change_followup",
                with_open(["I use it for coding and writing", "I use it heavily every day", "should I use 100 or 200 Pro", question]),
            )
        )

    repeated_sequences = [
        (["I use it for coding and writing", "I use it heavily every day", "which Pro should I use", "which Pro should I use"], {"same_question_repeat": True}),
        (["coding and writing", "heavy daily use", "should I choose 100 or 200 Pro", "same question, 100 or 200"], {"same_question_repeat": True}),
        (["coding and writing", "heavy", "which Pro tier", "explain it simpler"], {"same_question_repeat": True}),
        (["I use it for coding and writing", "I use it heavily every day", "which Pro should I use", "what happens if I move to 200 mid-month"], {"new_detail": True}),
        (["coding and writing", "heavy", "100 or 200 Pro", "can I start lower and upgrade later"], {"new_detail": True}),
        (["writing and coding", "heavy side", "do I need 200 Pro", "if I choose 100 now can I move up"], {"new_detail": True}),
        (["coding", "I need headroom", "which Pro tier", "what about proration if I switch"], {"new_detail": True}),
        (["coding", "heavy", "which Pro", "should I start at 200 right away"], {"new_detail": True}),
        (["I use another AI too", "coding and writing", "heavy", "which Pro should I use", "what if 100 becomes limiting"], {"new_detail": True}),
        (["coding and writing", "I use it every day", "Plus enough?", "Pro seems safer", "which Pro"], {"new_detail": True}),
        (["coding and writing", "heavy", "how much are the plans", "which Pro should I choose"], {"new_detail": True}),
        (["coding and writing", "heavy", "which Pro should I use", "why not 200 immediately"], {"new_detail": True}),
        (["coding and writing", "a little heavily", "which Pro", "give me the simple version"], {"same_question_repeat": True}),
        (["coding and writing", "more than casual use", "100 or 200 Pro", "say that shorter"], {"same_question_repeat": True}),
        (["coding and writing", "need headroom", "which Pro", "what changes if I move up later"], {"new_detail": True}),
        (["coding and writing", "hit limits sometimes", "which Pro", "can I switch once I hit limits"], {"new_detail": True}),
        (["coding and writing", "heavy", "100 or 200", "100 or 200, I still do not get it"], {"same_question_repeat": True}),
        (["coding and writing", "heavy", "which Pro tier", "if I pick lower now am I stuck"], {"new_detail": True}),
        (["coding and writing", "heavy", "which Pro", "what is the safest low-risk move"], {"new_detail": True}),
        (["coding and writing", "heavy", "which Pro", "what is the exact mid-month billing treatment"], {"new_detail": True}),
    ]
    for index, (turns, expectation) in enumerate(repeated_sequences, start=1):
        scenarios.append(scenario(f"repeat-prevention-{index:03d}", "repeated_answer_prevention", with_open(turns), expectation))

    internal_sequences = [
        ["I use it for coding and writing"],
        ["how much are the plans"],
        ["how do I sign up"],
        ["which Pro tier should I choose"],
        ["thanks"],
        ["I already told you coding and writing"],
        ["what do you mean"],
        ["what is the next step"],
        ["I use another LLM too"],
        ["Plus enough?"],
        ["Pro is probably better"],
        ["where do I upgrade"],
        ["send me a link"],
        ["what happens after I say yes"],
        ["is API included"],
        ["what is Enterprise"],
        ["I need headroom"],
        ["what if I switch later"],
        ["current tool is okay"],
        ["I use it heavily"],
    ]
    for index, turns in enumerate(internal_sequences, start=1):
        base = ["I use it for coding and writing", "I use it heavily every day"] if index % 2 == 0 else []
        scenarios.append(scenario(f"internal-wording-{index:03d}", "internal_process_wording_banned", with_open([*base, *turns])))

    terminal_turns = [
        "ok I will do that thank you",
        "sounds good thanks",
        "okay I'll check it",
        "got it, thanks",
        "I will start there",
        "that is clear thank you",
        "okay I will use the plan page",
        "thanks I will start lower",
        "makes sense, thank you",
        "ok I will try that",
        "cool I will do that",
        "thank you, that answers it",
    ]
    for index, close_turn in enumerate(terminal_turns, start=1):
        scenarios.append(
            scenario(
                f"terminal-acceptance-{index:03d}",
                "terminal_acceptance_polite_close",
                with_open(["I use it for coding and writing", "I use it heavily every day", "which Pro should I use", close_turn]),
            )
        )

    heavy_sequences = [
        ["I do use my tools a little heavily maybe more than a little", "I am deciding between Pro tiers"],
        ["I need headroom", "which Pro tier should I use"],
        ["I do need headroom", "should I choose 100 or 200 Pro"],
        ["I am deciding between Pro tiers", "do I need the 200 dollar one"],
        ["I might max out usage", "which Pro is safer"],
        ["heavy coding and writing", "100 or 200 Pro"],
        ["I use it more than casually", "which Pro tier"],
        ["I rely on it heavily", "lower or higher Pro tier"],
        ["I need maximum headroom maybe", "should I start at 200"],
        ["I use it all day", "which Pro"],
        ["serious daily coding", "I want Pro but which tier"],
        ["I hit limits sometimes", "which Pro plan tier is right"],
        ["usage ceiling matters", "should I start lower"],
        ["I am a power user", "what is the practical Pro choice"],
        ["more than a little heavy", "which paid Pro level should I use"],
        ["I want enough headroom", "100 versus 200 Pro"],
    ]
    for index, turns in enumerate(heavy_sequences, start=1):
        scenarios.append(
            scenario(
                f"heavy-headroom-{index:03d}",
                "heavy_headroom_state_preservation",
                with_open(["I use it for coding and writing", *turns]),
            )
        )

    return scenarios


def run_scenario(item: dict[str, Any]) -> dict[str, Any]:
    run = run_turn_sequence(item["turns"], item["id"])
    run["expectation"] = item.get("expectation") or {}
    failures = GROUP_VALIDATORS[item["group"]](run)
    return {
        "id": item["id"],
        "group": item["group"],
        "turn_count": len(item["turns"]),
        "multi_turn": item["multi_turn"],
        "status": "pass" if not failures else "fail",
        "failures": list(dict.fromkeys(failures)),
        "final_response": run["final_response"],
        "final_response_hash": sha12(run["final_response"]),
        "response_hashes": [sha12(item) for item in run["responses"]],
        "call_control": run["call_control"],
        "final_memory": {
            key: run["final_memory"].get(key)
            for key in [
                "openai_usage_intensity",
                "openai_recommended_path",
                "buyer_decision_stage",
                "active_decision_frame",
                "current_buyer_question_type",
                "openai_next_best_action",
            ]
        },
        "side_effects": side_effect_flags_for_packet(run["final_packet"]),
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
            "## Failed Cases",
            "",
            "```json",
            json.dumps(result["failed_cases"][:25], indent=2, sort_keys=True),
            "```",
            "",
        ]
    )
    REPORT_PATH.write_text(report, encoding="utf-8")


def main() -> None:
    scenarios = build_scenarios()
    traces = [run_scenario(item) for item in scenarios]
    failed = [trace for trace in traces if trace["status"] != "pass"]
    group_counts = Counter(item["group"] for item in scenarios)
    missing_groups = {
        group: required
        for group, required in REQUIRED_GROUP_COUNTS.items()
        if group_counts[group] < required
    }
    side_effects_false = all(not any(trace["side_effects"].get(key) for key in SIDE_EFFECT_KEYS) for trace in traces)
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
    structural_failures = []
    if len(scenarios) < MIN_SCENARIOS:
        structural_failures.append(f"scenario count below {MIN_SCENARIOS}")
    multi_turn_count = sum(1 for item in scenarios if item["multi_turn"])
    if multi_turn_count < MIN_MULTI_TURN_SCENARIOS:
        structural_failures.append(f"multi-turn count below {MIN_MULTI_TURN_SCENARIOS}")
    if missing_groups:
        structural_failures.append(f"missing required group counts: {missing_groups}")
    if not side_effects_false or provider_calls or live_tts_calls:
        structural_failures.append("validator caused disallowed side effects")

    result = {
        "checkpoint_id": CHECKPOINT_ID,
        "status": "pass" if not failed and not structural_failures else "fail",
        "scenario_count": len(scenarios),
        "multi_turn_scenario_count": multi_turn_count,
        "group_counts": dict(sorted(group_counts.items())),
        "required_group_counts": REQUIRED_GROUP_COUNTS,
        "failed_count": len(failed),
        "structural_failures": structural_failures,
        "side_effects_false": side_effects_false,
        "provider_calls_made": provider_calls,
        "live_tts_calls_made": live_tts_calls,
        "local_llm_calls_made": False,
        "raw_private_transcript_copied_to_public_evidence": False,
        "failed_cases": [
            {
                "id": trace["id"],
                "group": trace["group"],
                "failures": trace["failures"],
                "final_response": trace["final_response"],
                "final_response_hash": trace["final_response_hash"],
                "final_memory": trace["final_memory"],
                "call_control": trace["call_control"],
            }
            for trace in failed
        ],
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
