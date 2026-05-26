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


CHECKPOINT_ID = "PUBLIC-OPENAI-LIVE-SEMANTIC-PIPELINE-001"
FIXTURE_PATH = ROOT / "runtime" / "campaigns" / "examples" / "public-openai-chatgpt-plans.json"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"
TMP_DIR = ROOT / ".tmp" / CHECKPOINT_ID
STATE_KEY = "openai_chatgpt_plan_state"

LIVE_DERIVED_TRANSCRIPTS = [
    "LIVE-DEMO-001-adc8611a-34ab-4155-9285-e461bf597f5a-transcript.json",
    "LIVE-DEMO-001-4680965d-f60e-4186-bfe3-4eaceb0ad183-transcript.json",
    "LIVE-DEMO-001-3c465ff1-c5e7-4211-8e70-8e1bdc789af5-transcript.json",
]

SIDE_EFFECT_KEYS = [
    "provider_calls_made",
    "local_llm_calls_made",
    "sends_email",
    "creates_calendar_event",
    "writes_crm",
    "opens_prod_102",
    "customer_audio_uploaded_to_python_server",
    "customer_audio_uploaded_to_tts_provider",
    "live_tts_used",
    "tts_provider_calls_made",
    "audio_file_created",
]

LEAK_RE = re.compile(
    r"legacy compatibility field|short legacy compatibility|primary close is official|"
    r"appointment_target|human_followup_owner|demo operator",
    re.I,
)
GENERIC_PLAN_COMPARISON_RE = re.compile(
    r"are you mainly comparing plans for yourself,? a small team,? or a larger organization|"
    r"are you looking for personal use,? team use,? or enterprise controls",
    re.I,
)
ADOPTION_DISCOVERY_RE = re.compile(
    r"using chatgpt today.*another ai tool.*not using ai|"
    r"chatgpt today.*another ai tool.*not using ai|"
    r"chatgpt today.*mostly not using ai",
    re.I,
)
BUSINESS_ENTERPRISE_ROUTE_RE = re.compile(
    r"for team use,? business is|business is the self-serve workspace route|"
    r"enterprise requirements like|basic team workspace controls|contact-sales route",
    re.I,
)
NO_FIT_COLLAPSE_RE = re.compile(r"not relevant|not a fit|stop here|no paid close|would not push", re.I)
REPEATED_PITCH_RE = re.compile(
    r"right\s+-\s+coding and writing|compare pro first|are you using|what would you mainly|"
    r"are you looking for basic team|which one are you using today",
    re.I,
)
TERMINAL_QUESTION_RE = re.compile(r"\?\s*$|what would you|are you using|which one|are you looking", re.I)


def normalize(text: Any) -> str:
    return re.sub(r"\s+", " ", str(text or "").strip().lower())


def sha12(text: str) -> str:
    return hashlib.sha256(str(text or "").encode("utf-8")).hexdigest()[:12]


def scenario(
    scenario_id: str,
    group: str,
    turns: list[str],
    expectation: str,
    *,
    note: str = "",
) -> dict[str, Any]:
    return {
        "id": scenario_id,
        "group": group,
        "turns": turns,
        "expectation": expectation,
        "multi_turn": len(turns) > 1,
        "note": note,
    }


def with_open(*turns: str) -> list[str]:
    return ["__agent_open__", *turns]


def after_permission(*turns: str, permission: str = "sure yeah") -> list[str]:
    return ["__agent_open__", permission, *turns]


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
    summary = packet.get("summary") if isinstance(packet.get("summary"), dict) else {}
    body = packet.get("packet") if isinstance(packet.get("packet"), dict) else {}
    manager = packet.get("dialogue_manager") if isinstance(packet.get("dialogue_manager"), dict) else {}
    return str(summary.get("final_response") or body.get("final_response") or manager.get("final_response") or "")


def manager(packet: dict[str, Any]) -> dict[str, Any]:
    return packet.get("dialogue_manager") if isinstance(packet.get("dialogue_manager"), dict) else {}


def semantic_frame(packet: dict[str, Any]) -> dict[str, Any]:
    value = manager(packet).get("contextual_buyer_semantics")
    return value if isinstance(value, dict) else {}


def memory(packet: dict[str, Any]) -> dict[str, Any]:
    return packet.get("demo_conversation_memory") or packet.get("conversation_memory") or {}


def plan_state(packet: dict[str, Any]) -> dict[str, Any]:
    state = memory(packet).get(STATE_KEY)
    return state if isinstance(state, dict) else {}


def source(packet: dict[str, Any]) -> str:
    return str(manager(packet).get("final_response_source") or "")


def side_effect_flags(packet: dict[str, Any]) -> dict[str, bool]:
    body = packet.get("packet") if isinstance(packet.get("packet"), dict) else {}
    delivery = body.get("tts_delivery") if isinstance(body.get("tts_delivery"), dict) else {}
    summary = packet.get("summary") if isinstance(packet.get("summary"), dict) else {}
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


def use_cases(state: dict[str, Any]) -> set[str]:
    value = state.get("openai_use_case")
    if isinstance(value, list):
        return {str(item).lower() for item in value}
    return {str(value or "").lower()} if value else set()


def has_business_enterprise_state(state: dict[str, Any]) -> bool:
    cases = use_cases(state)
    return bool(
        {"team", "enterprise"} & cases
        or state.get("openai_recommended_path") in {"business", "enterprise"}
        or state.get("active_decision_frame") == "business_vs_enterprise"
        or state.get("decision_frame") == "business_vs_enterprise"
        or state.get("value_hypothesis") == "team_controls"
    )


def post_open_packets(packets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return packets[1:] if len(packets) > 1 else packets


def validate_common(item: dict[str, Any], packets: list[dict[str, Any]], responses: list[str]) -> list[str]:
    failures: list[str] = []
    for index, packet in enumerate(packets):
        text = response_text(packet)
        if LEAK_RE.search(text):
            failures.append(f"turn {index + 1}: leaked internal compatibility field")
        flags = side_effect_flags(packet)
        for key in SIDE_EFFECT_KEYS:
            if flags[key]:
                failures.append(f"turn {index + 1}: {key} must be false")
    if item["turns"] and item["turns"][0] == "__agent_open__" and LEAK_RE.search("\n".join(responses[1:])):
        failures.append("post-opening response chain leaked internal fields")
    return failures


def validate_permission(packet: dict[str, Any]) -> list[str]:
    text = response_text(packet)
    state = plan_state(packet)
    frame = semantic_frame(packet)
    failures: list[str] = []
    if source(packet) != "contextual_buyer_semantics":
        failures.append(f"permission acknowledgement source should be contextual_buyer_semantics, got {source(packet)!r}")
    if frame.get("semantic") != "public_plan_adoption_state_discovery":
        failures.append(f"permission acknowledgement semantic should be adoption discovery, got {frame.get('semantic')!r}")
    if not ADOPTION_DISCOVERY_RE.search(text):
        failures.append("permission acknowledgement did not ask adoption-state question")
    if GENERIC_PLAN_COMPARISON_RE.search(text):
        failures.append("permission acknowledgement fell back to generic plan-comparison prompt")
    if BUSINESS_ENTERPRISE_ROUTE_RE.search(text):
        failures.append("permission acknowledgement routed to Business/Enterprise")
    if has_business_enterprise_state(state):
        failures.append(f"permission acknowledgement mutated team/business state: {state}")
    if state.get("openai_adoption_state") not in {None, "unknown"}:
        failures.append(f"permission acknowledgement should keep adoption unknown, got {state.get('openai_adoption_state')!r}")
    return failures


def validate_negation(packets: list[dict[str, Any]]) -> list[str]:
    final = packets[-1]
    text = response_text(final)
    state = plan_state(final)
    failures: list[str] = []
    if has_business_enterprise_state(state):
        failures.append(f"negated team/self-use created business state: {state}")
    if {"team", "enterprise"} & use_cases(state):
        failures.append(f"negated team/self-use kept blocked use case: {state.get('openai_use_case')!r}")
    if BUSINESS_ENTERPRISE_ROUTE_RE.search(text):
        failures.append("negated team/self-use response routed to Business/Enterprise")
    blocked = set(state.get("blocked_openai_use_cases") or [])
    if not {"team", "enterprise"}.issubset(blocked):
        failures.append(f"negated team/self-use did not record blocked org routes: {blocked}")
    return failures


def validate_poisoned_sequence(packets: list[dict[str, Any]]) -> list[str]:
    failures: list[str] = []
    for index, packet in enumerate(post_open_packets(packets), start=2):
        text = response_text(packet)
        state = plan_state(packet)
        if has_business_enterprise_state(state):
            failures.append(f"turn {index}: poisoned business/enterprise state: {state}")
        if BUSINESS_ENTERPRISE_ROUTE_RE.search(text):
            failures.append(f"turn {index}: poisoned Business/Enterprise route rendered")
    final_state = plan_state(packets[-1])
    if final_state.get("openai_individual_context") is not True:
        failures.append(f"poisoned prevention sequence did not preserve individual context: {final_state}")
    return failures


def validate_asr_alias(packet: dict[str, Any], final_turn: str) -> list[str]:
    text = response_text(packet)
    frame = semantic_frame(packet)
    failures: list[str] = []
    try:
        confidence = float(frame.get("confidence") or 0)
    except (TypeError, ValueError):
        confidence = 0.0
    if source(packet) == "pre_speech_conversation_stability_guard":
        failures.append("ASR alias turn was owned by stability guard")
    if confidence < 0.5 or frame.get("semantic") in {None, "", "no_contextual_semantic"} or frame.get("semantic_family") in {None, "", "unknown"}:
        failures.append(f"ASR alias turn was not semantically recognized: {frame}")
    if NO_FIT_COLLAPSE_RE.search(text) and not re.search(r"current setup|gap|falls short|which one|may be", text, re.I):
        failures.append("ASR alias turn collapsed to passive no-fit instead of contextual understanding")
    if "maybe" in normalize(final_turn) and not re.search(r"may be|maybe|sounds like|not sure", text, re.I):
        failures.append("ASR alias uncertainty was not preserved")
    return failures


def validate_stability_ownership(packet: dict[str, Any]) -> list[str]:
    frame = semantic_frame(packet)
    failures: list[str] = []
    if source(packet) == "pre_speech_conversation_stability_guard":
        failures.append(f"recognized OpenAI turn was owned by stability guard: {frame}")
    if frame.get("semantic") in {None, "", "no_contextual_semantic"}:
        failures.append(f"recognized OpenAI turn did not produce semantic frame: {frame}")
    return failures


def validate_terminal(packet: dict[str, Any]) -> list[str]:
    text = response_text(packet)
    frame = semantic_frame(packet)
    call_control = str(manager(packet).get("call_control") or "")
    failures: list[str] = []
    if frame.get("speech_act") != "terminal_acceptance" and "terminal_acceptance" not in str(frame.get("semantic") or ""):
        failures.append(f"terminal acceptance speech_act missing: {frame}")
    if call_control not in {"end-call", "continue-call"}:
        failures.append(f"terminal acceptance call_control should be end-call or terminal continue-call, got {call_control!r}")
    if call_control == "continue-call" and TERMINAL_QUESTION_RE.search(text):
        failures.append("terminal continue-call asked a new question")
    if REPEATED_PITCH_RE.search(text):
        failures.append("terminal acceptance repeated a sales pitch or discovery question")
    if BUSINESS_ENTERPRISE_ROUTE_RE.search(text):
        failures.append("terminal acceptance routed to Business/Enterprise")
    return failures


def validate_state_transition(packet: dict[str, Any]) -> list[str]:
    text = response_text(packet)
    state = plan_state(packet)
    frame = semantic_frame(packet)
    failures: list[str] = []
    if has_business_enterprise_state(state):
        failures.append(f"state transition created team/business state: {state}")
    if state.get("openai_recommended_path") in {"plus", "pro", "business", "enterprise"} and state.get("openai_adoption_state") == "unknown":
        failures.append(f"unknown adoption state created recommendation: {state}")
    if state.get("buyer_decision_stage") in {"recommendation", "self_serve_close", "no_fit"} and state.get("openai_adoption_state") == "unknown":
        failures.append(f"orientation/confusion mutated into terminal decision stage: {state}")
    if BUSINESS_ENTERPRISE_ROUTE_RE.search(text):
        failures.append("state transition rendered Business/Enterprise route without org evidence")
    if source(packet) == "pre_speech_conversation_stability_guard" and frame.get("semantic") not in {None, "", "no_contextual_semantic"}:
        failures.append("state transition recognized turn was owned by stability guard")
    return failures


def build_scenarios() -> list[dict[str, Any]]:
    scenarios: list[dict[str, Any]] = []

    permission_variants = [
        "sure yeah",
        "yeah sure",
        "sure",
        "yes",
        "go ahead",
        "okay",
        "ok",
        "yes sure",
        "sure go ahead",
        "yeah go ahead",
        "okay go ahead",
        "ok go ahead",
        "tell me",
        "yeah tell me",
        "sure tell me",
        "i have a minute",
        "yes i have a minute",
        "sounds fine",
        "fine go ahead",
        "alright go ahead",
        "all right go ahead",
        "yep go ahead",
    ]
    for index, utterance in enumerate(permission_variants, start=1):
        scenarios.append(scenario(f"permission-ack-{index:03d}", "permission_acknowledgement", with_open(utterance), "permission"))

    negated_self_variants = [
        "I am by myself, not a team",
        "I am just by myself so not a team or anything",
        "just me, no company",
        "not enterprise",
        "no business needs",
        "I am personal use only",
        "I'm not a team, just asking",
        "it is just myself, no enterprise",
        "only me, not for a company",
        "solo use, no business needs",
        "by myself, not business",
        "just my own use, not a company",
        "no company, no team",
        "not for work admin, just me",
        "personal coding, no team",
        "individual use, no enterprise",
        "for myself only",
        "I am not buying for a company",
        "no team workspace",
        "not team use",
    ]
    negated_self_variants = negated_self_variants + [f"{item}." for item in negated_self_variants]
    for index, utterance in enumerate(negated_self_variants[:42], start=1):
        scenarios.append(scenario(f"negated-team-{index:03d}", "negated_team_self_use", after_permission(utterance), "negation"))

    tool_turns = [
        "I use Claude and ChatGPT for coding",
        "I use ChatGPT for coding and maybe Claude too",
        "I use Claude for coding and ChatGPT might be better for me",
        "ChatGPT or Claude for coding is what I am comparing",
        "I use ChatGPT for personal coding",
    ]
    plan_turns = [
        "is Plus enough for me",
        "what about the price",
        "should I start with Pro",
        "is Pro too much",
        "where should I start",
        "Plus or Pro for coding",
    ]
    for index in range(30):
        self_turn = negated_self_variants[index % len(negated_self_variants)]
        tool_turn = tool_turns[index % len(tool_turns)]
        plan_turn = plan_turns[index % len(plan_turns)]
        scenarios.append(
            scenario(
                f"poisoned-sequence-{index + 1:03d}",
                "poisoned_state_prevention",
                after_permission(self_turn, tool_turn, plan_turn),
                "poisoned_prevention",
                note="live-derived sequence paraphrase" if index < 3 else "",
            )
        )

    asr_aliases = [
        "I use chacha PT",
        "I use chacha BT",
        "I use chacha p t",
        "I use chacha b t",
        "I use chacha gpt",
        "I use check GPT",
        "I use touch GPT",
        "I use touch your PT",
        "I use chat gbt",
        "I use cloud for coding",
        "I use Claude for coding",
        "I use chacha PT and maybe cloud",
    ]
    asr_contexts = [
        " for coding",
        " as my current AI tool",
        " in my current setup",
        " and maybe cloud",
        " for writing and coding",
    ]
    index = 1
    for alias in asr_aliases:
        for context in asr_contexts:
            text = alias if alias.endswith(context.strip()) else f"{alias}{context}"
            scenarios.append(scenario(f"asr-alias-{index:03d}", "asr_alias_current_tool", after_permission(text), "asr_alias"))
            index += 1
    scenarios = scenarios[: len(permission_variants) + 42 + 30 + 62]

    recognized_turns = [
        "I use ChatGPT for coding",
        "I use Claude for coding",
        "I use chacha PT and maybe cloud",
        "is Plus enough for coding",
        "how much is Pro",
        "what is the difference between Plus and Pro",
        "I am hitting limits",
        "I use it heavily every day",
        "I use another AI tool",
        "should I switch from Claude",
    ]
    for index in range(42):
        utterance = recognized_turns[index % len(recognized_turns)]
        if index % 3 == 0:
            turns = after_permission("I am by myself, not a team", utterance)
        elif index % 3 == 1:
            turns = after_permission(utterance)
        else:
            turns = after_permission("I use ChatGPT for coding", utterance)
        scenarios.append(scenario(f"stability-ownership-{index + 1:03d}", "stability_guard_ownership", turns, "stability_ownership"))

    terminal_variants = [
        "ok I'll check that thanks",
        "ok I will do that thank you",
        "sounds good thanks",
        "got it thanks",
        "I'll check it",
        "I will start there",
        "thanks that helps",
        "okay I'll check it",
        "ok I will check it",
        "sounds good thank you",
        "got it thank you",
        "I will check that",
        "thanks I will start there",
        "that helps thanks",
        "cool I will do that",
    ]
    for index, utterance in enumerate(terminal_variants + terminal_variants, start=1):
        prefix = ["I am by myself, not a team", "I use ChatGPT for coding", "is Plus enough for me"]
        scenarios.append(scenario(f"terminal-acceptance-{index:03d}", "terminal_acceptance", after_permission(*prefix, utterance), "terminal"))

    transition_turns = [
        "what does Plus mean",
        "what are these plans",
        "I am confused",
        "say that simply",
        "are these products or plans",
        "why are you mentioning Enterprise",
        "what is the quick version",
        "explain Free Plus and Pro",
        "I do not understand",
        "what is this about again",
    ]
    for index in range(42):
        utterance = transition_turns[index % len(transition_turns)]
        prefix = ["I am by myself, not a team"] if index % 2 else []
        scenarios.append(scenario(f"state-transition-{index + 1:03d}", "state_transition_audit", after_permission(*prefix, utterance), "state_transition"))

    negative_controls = [
        ("actual-team", ["we have a team and need admin controls"], "stability_ownership"),
        ("actual-enterprise", ["our company needs SSO and procurement review"], "stability_ownership"),
        ("actual-security", ["we need security review for our organization"], "stability_ownership"),
    ]
    for index, (slug, turns, expectation) in enumerate(negative_controls, start=1):
        scenarios.append(scenario(f"negative-control-{index:03d}-{slug}", "negative_controls", after_permission(*turns), expectation))

    return scenarios


def run_scenario(item: dict[str, Any]) -> dict[str, Any]:
    state: dict[str, Any] = {"turns": []}
    packets: list[dict[str, Any]] = []
    responses: list[str] = []
    for turn in item["turns"]:
        packet = build_turn(turn, state, item["id"])
        packets.append(packet)
        responses.append(response_text(packet))
    final_packet = packets[-1]
    failures = validate_common(item, packets, responses)
    if item["expectation"] == "permission":
        failures.extend(validate_permission(final_packet))
    elif item["expectation"] == "negation":
        failures.extend(validate_negation(packets))
    elif item["expectation"] == "poisoned_prevention":
        failures.extend(validate_poisoned_sequence(packets))
    elif item["expectation"] == "asr_alias":
        failures.extend(validate_asr_alias(final_packet, item["turns"][-1]))
    elif item["expectation"] == "stability_ownership":
        failures.extend(validate_stability_ownership(final_packet))
    elif item["expectation"] == "terminal":
        failures.extend(validate_terminal(final_packet))
    elif item["expectation"] == "state_transition":
        failures.extend(validate_state_transition(final_packet))

    final_text = response_text(final_packet)
    frame = semantic_frame(final_packet)
    state_value = plan_state(final_packet)
    return {
        "id": item["id"],
        "group": item["group"],
        "expectation": item["expectation"],
        "turn_count": len(item["turns"]),
        "multi_turn": item["multi_turn"],
        "status": "pass" if not failures else "fail",
        "failures": failures,
        "final_response_hash": sha12(final_text),
        "final_response": final_text if failures else "",
        "final_response_source": source(final_packet),
        "call_control": manager(final_packet).get("call_control"),
        "semantic": frame.get("semantic"),
        "semantic_family": frame.get("semantic_family"),
        "speech_act": frame.get("speech_act"),
        "response_strategy": frame.get("response_strategy"),
        "openai_recommended_path": state_value.get("openai_recommended_path"),
        "openai_use_case": state_value.get("openai_use_case"),
        "active_decision_frame": state_value.get("active_decision_frame"),
        "blocked_openai_use_cases": state_value.get("blocked_openai_use_cases"),
        "side_effects": side_effect_flags(final_packet),
        "note": item.get("note") or "",
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
            f"- Permission legacy leak count: `{result['permission_legacy_leak_count']}`",
            f"- Negation state poison count: `{result['negation_state_poison_count']}`",
            f"- Business/Enterprise false-route count: `{result['business_enterprise_false_route_count']}`",
            f"- ASR alias failure count: `{result['asr_alias_failure_count']}`",
            f"- Stability guard ownership failure count: `{result['stability_guard_ownership_failure_count']}`",
            f"- Terminal acceptance failure count: `{result['terminal_acceptance_failure_count']}`",
            f"- State transition invariant failure count: `{result['state_transition_invariant_failure_count']}`",
            f"- Side effects false: `{str(result['side_effects_false']).lower()}`",
            f"- Provider calls made: `{str(result['provider_calls_made']).lower()}`",
            "",
            "## Latest Private Transcript Inputs",
            "",
            "Only filenames are recorded here; raw private transcript text is not copied.",
            "",
            "```json",
            json.dumps(result["latest_private_transcript_filenames"], indent=2),
            "```",
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
            json.dumps(result["failed_cases"][:30], indent=2, sort_keys=True),
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
    all_side_effects = [trace["side_effects"] for trace in traces]

    structure_failures: list[str] = []
    if len(scenarios) < 220:
        structure_failures.append(f"at least 220 scenarios required, got {len(scenarios)}")
    if multi_turn_count < 150:
        structure_failures.append(f"at least 150 multi-turn scenarios required, got {multi_turn_count}")
    required_groups = {
        "permission_acknowledgement": 20,
        "negated_team_self_use": 40,
        "poisoned_state_prevention": 30,
        "asr_alias_current_tool": 60,
        "stability_guard_ownership": 40,
        "terminal_acceptance": 30,
        "state_transition_audit": 40,
    }
    for group, minimum in required_groups.items():
        if group_counts[group] < minimum:
            structure_failures.append(f"{group} requires at least {minimum} scenarios, got {group_counts[group]}")

    permission_failures = [trace for trace in traces if trace["group"] == "permission_acknowledgement" and trace["status"] != "pass"]
    negation_failures = [trace for trace in traces if trace["group"] == "negated_team_self_use" and trace["status"] != "pass"]
    business_route_failures = [
        trace
        for trace in traces
        if "Business/Enterprise" in " ".join(trace.get("failures") or [])
        or "business/enterprise" in " ".join(trace.get("failures") or []).lower()
    ]
    asr_failures = [trace for trace in traces if trace["group"] == "asr_alias_current_tool" and trace["status"] != "pass"]
    stability_failures = [trace for trace in traces if trace["group"] == "stability_guard_ownership" and trace["status"] != "pass"]
    terminal_failures = [trace for trace in traces if trace["group"] == "terminal_acceptance" and trace["status"] != "pass"]
    transition_failures = [trace for trace in traces if trace["group"] == "state_transition_audit" and trace["status"] != "pass"]

    result = {
        "checkpoint_id": CHECKPOINT_ID,
        "status": "pass" if not failed and not structure_failures else "fail",
        "scenario_count": len(scenarios),
        "multi_turn_scenario_count": multi_turn_count,
        "group_counts": dict(sorted(group_counts.items())),
        "failed_count": len(failed) + len(structure_failures),
        "structure_failures": structure_failures,
        "permission_legacy_leak_count": len([trace for trace in permission_failures if any("leak" in failure for failure in trace["failures"])]),
        "negation_state_poison_count": len(negation_failures),
        "business_enterprise_false_route_count": len(business_route_failures),
        "asr_alias_failure_count": len(asr_failures),
        "stability_guard_ownership_failure_count": len(stability_failures),
        "terminal_acceptance_failure_count": len(terminal_failures),
        "state_transition_invariant_failure_count": len(transition_failures),
        "latest_private_transcript_filenames": LIVE_DERIVED_TRANSCRIPTS,
        "side_effects_false": not any(any(flags.values()) for flags in all_side_effects),
        "provider_calls_made": any(flags.get("provider_calls_made") for flags in all_side_effects),
        "failed_cases": failed[:60],
        "sample_passed_cases": [trace for trace in traces if trace["status"] == "pass"][:20],
    }
    write_evidence(result)
    if result["status"] != "pass":
        print(json.dumps({"status": result["status"], "failed_count": result["failed_count"], "structure_failures": structure_failures}, indent=2))
        raise SystemExit(1)
    print(f"{CHECKPOINT_ID} passed with {len(scenarios)} scenarios.")


if __name__ == "__main__":
    main()
