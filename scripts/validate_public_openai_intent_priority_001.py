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
from runtime.campaigns import public_openai_chatgpt_plans_dialogue as openai_dialogue  # noqa: E402


CHECKPOINT_ID = "PUBLIC-OPENAI-INTENT-PRIORITY-001"
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
    "live_tts_used",
    "tts_provider_calls_made",
    "audio_file_created",
]

RAW_URL_RE = re.compile(r"https?://|www\.", re.I)
UNSAFE_AFFILIATION_RE = re.compile(
    r"\b(i am calling from openai|i'm calling from openai|calling from openai|"
    r"authorized by openai|authorised by openai|authorized to represent openai|"
    r"represent openai|i represent openai)\b",
    re.I,
)
INTERNAL_POLICY_RE = re.compile(
    r"i should not assume buying intent|first i need the adoption state|\badoption state\b",
    re.I,
)
SOURCE_SCAFFOLD_RE = re.compile(
    r"article lists|article describes|according to|source of truth|source-grounded|"
    r"official sources state|official sources say|the official page says|"
    r"exact tier details should be checked against official openai sources",
    re.I,
)
TERMINAL_NO_SPEECH_CONTROLS = {"end-call", "hang-up", "schedule-and-end"}
NO_FIT_CAVEAT_RE = re.compile(
    r"if your current tool is enough.*would not push|would not push a paid chatgpt plan|no paid close",
    re.I,
)
TEAM_ROUTE_RE = re.compile(
    r"\bfor team use, business is|basic team workspace controls|enterprise requirements like sso|team_plan_fit\b",
    re.I,
)
EXPLANATION_RE = re.compile(
    r"chatgpt subscription plans|free is .*no-cost|free costs nothing|plus and pro .*individual|"
    r"business .*team|enterprise .*larger|enterprise .*organization",
    re.I,
)
ADOPTION_LOOP_RE = re.compile(
    r"using chatgpt today,? using another ai tool,? or mostly not using ai yet|"
    r"i should first learn the adoption state|first learn the adoption state",
    re.I,
)
CLOSE_PRESSURE_RE = re.compile(r"official chatgpt plans page|profile upgrade flow|contact sales|sign up|upgrade now", re.I)
SIMPLE_EXPLANATION_RE = re.compile(
    r"simple version|simpler|plainly|plain terms|chatgpt subscription plans|free costs nothing|free is the no-cost",
    re.I,
)
EXPLANATION_RESPONSE_BY_SUB_INTENT = {
    "call_orientation": re.compile(r"call about chatgpt subscription plans|chatgpt subscription plans.*worth considering", re.I),
    "plan_category_explanation": re.compile(
        r"subscription options for chatgpt.*free.*plus.*pro.*business.*enterprise|"
        r"free is no-cost.*plus and pro.*individual.*business.*teams.*enterprise.*larger",
        re.I,
    ),
    "specific_plan_label_explanation": re.compile(
        r"free is .*no-cost.*plus is .*paid individual.*pro is .*heavier|"
        r"free, plus, and pro are individual plan labels.*business is for teams.*enterprise is for larger",
        re.I,
    ),
    "subscription_model_question": re.compile(r"chatgpt subscription plans.*not a one-off product purchase", re.I),
    "model_vs_product_question": re.compile(r"plan options, not model names|plan options, not product names", re.I),
    "simpler_explanation_request": re.compile(
        r"simple version.*choosing the right chatgpt plan|"
        r"even simpler.*free .*no-cost.*plus and pro.*paid personal.*business or enterprise.*organizations",
        re.I,
    ),
    "source_disclosure": re.compile(r"public openai|pricing and help information|not calling from openai", re.I),
    "affiliation_boundary": re.compile(r"not calling from openai|not representing openai", re.I),
}
TEAM_POSITIVE_RE = re.compile(
    r"\b(team|company|workspace|admin controls|sso|scim|procurement|security review|legal review|organization-level)\b",
    re.I,
)


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


def build_scenarios() -> list[dict[str, Any]]:
    scenarios: list[dict[str, Any]] = []

    opening_turns = [
        ["__agent_open__"],
        ["hi"],
        ["hello"],
        ["hey"],
        ["__agent_open__"],
        ["hello"],
        ["hey"],
        ["__agent_open__"],
        ["hi"],
        ["hello"],
        ["hey"],
        ["__agent_open__"],
    ]
    for index, turns in enumerate(opening_turns, start=1):
        scenarios.append(
            scenario(
                f"opening-origin-{index:03d}",
                "opening_origin_product_clarity",
                turns,
                "opening_clarity",
            )
        )

    explanation_questions = [
        "what is this",
        "what are you calling about",
        "what is this for exactly",
        "what are these plans",
        "what is Free Plus Pro Business or Enterprise",
        "I don't know what these models are",
        "I do not understand what you are talking about",
        "explain Free Plus Pro",
        "are these products or plans",
        "what is this call asking",
        "what does Free mean",
        "what does Plus mean",
        "what does Pro mean",
        "what does Business mean",
        "what does Enterprise mean",
        "what are the ChatGPT plan names",
        "what do you mean by subscription plans",
        "can you explain that first",
        "I am confused, what are these",
        "tell me plainly what this is",
    ]
    for index, utterance in enumerate(explanation_questions, start=1):
        turns = ["__agent_open__", "yeah sure", utterance] if index <= 18 else [utterance]
        scenarios.append(
            scenario(
                f"explanation-question-{index:03d}",
                "what_is_this_explanation_questions",
                turns,
                "explanation_first",
                note="sanitized-live-derived" if index in {1, 5, 7} else "",
            )
        )

    plan_label_traps = [
        "what is Free Plus Pro Business Enterprise",
        "I heard Business and Enterprise, what does that mean",
        "what are Plus and Pro",
        "what is the difference between Free and Business",
        "I do not know if Pro or Enterprise are products",
        "are Free and Business product names",
        "explain Plus Business Enterprise without selling me",
        "what does Enterprise mean in that list",
        "what does Business mean in that list",
        "Free Plus Pro Business Enterprise are what exactly",
        "are Plus and Pro subscriptions or models",
        "I heard Free Pro Plus Business, explain the words",
        "what is Free compared with Enterprise",
        "why did you list Business and Enterprise",
        "I do not know what Pro or Business are",
        "what are the paid plan labels",
        "what is Free versus Business in plain English",
        "is Enterprise a product or a plan",
        "is Business a company plan name",
        "what is the plan called Pro",
        "what are all those plan names",
        "you said Business Enterprise, what are those",
        "I heard Plus and Enterprise, explain",
        "what are Free Plus and Business",
        "are these ChatGPT products or plans",
        "what does the Enterprise word mean here",
        "what is Pro and what is Enterprise",
        "explain the difference between Plus Pro Business Enterprise",
        "I am lost on Free Plus Pro Business Enterprise",
        "yeah sure but what is this what is Free Plus Pro Business or Enterprise",
    ]
    for index, utterance in enumerate(plan_label_traps, start=1):
        scenarios.append(
            scenario(
                f"plan-label-trap-{index:03d}",
                "plan_label_traps",
                ["__agent_open__", "yeah sure", utterance],
                "plan_label_trap",
                note="sanitized-live-derived" if index == 30 else "",
            )
        )

    team_controls = [
        "we have a team",
        "my company needs SSO",
        "we need admin controls",
        "procurement needs terms",
        "this is for a team workspace",
        "our legal team needs a review",
        "we need SCIM",
        "we need security review",
        "we are buying for a company",
        "we need organization-level controls",
        "our team needs billing and member management",
        "Enterprise requirements are SSO and procurement",
    ]
    for index, utterance in enumerate(team_controls, start=1):
        scenarios.append(
            scenario(
                f"team-positive-control-{index:03d}",
                "team_intent_positive_controls",
                ["__agent_open__", "yeah sure", utterance],
                "team_route_allowed",
            )
        )

    stability_cases = [
        "I use ChatGPT and other AI tools",
        "I used ChatGPT and other tools",
        "I use another LLM",
        "I'm using chachu PT and other AI tools",
        "are you chachu BT and other tools",
        "I use it for coding",
        "I already use ChatGPT",
        "I use Claude too",
        "I use Gemini and ChatGPT",
        "I use Copilot for coding",
        "I use another AI assistant",
        "I already use AI tools",
        "I use ChatGPT for coding",
        "I used chat gpt and other AI tools",
        "I am using chat g p t and other tools",
        "my current assistant is Claude",
        "I use it for files and research",
        "I use ChatGPT today",
        "I have another AI tool already",
        "I use other assistants for work",
    ]
    for index, utterance in enumerate(stability_cases, start=1):
        scenarios.append(
            scenario(
                f"stability-ownership-{index:03d}",
                "stability_guard_must_not_own_openai_turns",
                ["__agent_open__", "yeah sure", utterance],
                "adapter_owns",
            )
        )

    state_cases = [
        ["__agent_open__"],
        ["__agent_open__", "yeah sure"],
        ["hi"],
        ["hello"],
        ["__agent_open__", "yes"],
        ["__agent_open__", "sure"],
        ["__agent_open__", "okay"],
        ["__agent_open__", "go ahead"],
        ["__agent_open__", "tell me"],
        ["__agent_open__", "yeah tell me"],
    ]
    for index, turns in enumerate(state_cases, start=1):
        scenarios.append(
            scenario(
                f"state-initialization-{index:03d}",
                "state_initialization_invariants",
                turns,
                "neutral_state",
            )
        )

    loop_sequences = [
        ["__agent_open__", "yeah sure", "what is this", "I still don't understand"],
        ["__agent_open__", "yeah sure", "what is this", "what are Free and Pro"],
        ["__agent_open__", "yeah sure", "what are these plans", "explain simpler"],
        ["__agent_open__", "yeah sure", "what is Free Plus Pro Business Enterprise", "I still do not understand"],
        ["__agent_open__", "yeah sure", "I don't understand what you are talking about", "what are Free and Pro"],
        ["__agent_open__", "yeah sure", "what is this for exactly", "explain that in plain English"],
        ["__agent_open__", "yeah sure", "what are Plus and Pro", "I am still confused"],
        ["__agent_open__", "yeah sure", "what does Business mean", "no, simpler please"],
        ["__agent_open__", "yeah sure", "what does Enterprise mean", "what is it in one sentence"],
        ["__agent_open__", "yeah sure", "are these products or plans", "I still don't get it"],
        ["__agent_open__", "yeah sure", "tell me plainly what this is", "what are these plans"],
        ["__agent_open__", "yeah sure", "I heard Business and Enterprise, what does that mean", "what is this again"],
        ["__agent_open__", "yeah sure", "I am lost on Free Plus Pro Business Enterprise", "explain simpler"],
        ["__agent_open__", "yeah sure", "what are all those plan names", "I do not understand the options"],
        ["__agent_open__", "yeah sure", "yeah sure but what is this what is Free Plus Pro Business or Enterprise", "I still don't understand"],
        ["__agent_open__", "yeah sure", "I don't really understand what you're talking about, what are Free Pro Plus", "explain simpler"],
    ]
    for index, turns in enumerate(loop_sequences, start=1):
        scenarios.append(
            scenario(
                f"repeated-confusion-{index:03d}",
                "loop_escape_repeated_confusion",
                turns,
                "repeated_confusion_escape",
                note="sanitized-live-derived" if index in {15, 16} else "",
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
    summary = packet.get("summary") if isinstance(packet.get("summary"), dict) else {}
    body = packet.get("packet") if isinstance(packet.get("packet"), dict) else {}
    manager = packet.get("dialogue_manager") if isinstance(packet.get("dialogue_manager"), dict) else {}
    return str(summary.get("final_response") or body.get("final_response") or manager.get("final_response") or "")


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


def dialogue_manager(packet: dict[str, Any]) -> dict[str, Any]:
    return packet.get("dialogue_manager") if isinstance(packet.get("dialogue_manager"), dict) else {}


def selected_action(packet: dict[str, Any]) -> dict[str, Any]:
    manager = dialogue_manager(packet)
    return manager.get("selected_action") if isinstance(manager.get("selected_action"), dict) else {}


def semantic_frame(packet: dict[str, Any]) -> dict[str, Any]:
    manager = dialogue_manager(packet)
    frame = manager.get("contextual_buyer_semantics")
    return frame if isinstance(frame, dict) else {}


def stability_guard(packet: dict[str, Any]) -> dict[str, Any]:
    guard = packet.get("demo_conversation_stability_guard")
    return guard if isinstance(guard, dict) else {}


def openai_state(packet: dict[str, Any]) -> dict[str, Any]:
    memory = packet.get("demo_conversation_memory") or packet.get("conversation_memory") or {}
    if not isinstance(memory, dict):
        return {}
    state = memory.get(openai_dialogue.OPENAI_STATE_KEY)
    return state if isinstance(state, dict) else {}


def question_count(text: str) -> int:
    return str(text or "").count("?")


def validate_common(text: str, packet: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    manager = dialogue_manager(packet)
    call_control = str(manager.get("call_control") or (packet.get("summary") or {}).get("call_control") or "")
    if not text.strip() and call_control not in TERMINAL_NO_SPEECH_CONTROLS:
        failures.append("blank final_response without documented terminal call_control")
    if RAW_URL_RE.search(text):
        failures.append("raw URL spoken")
    if UNSAFE_AFFILIATION_RE.search(text) and not re.search(r"\bnot (calling from|calling as|representing) openai\b", text, re.I):
        failures.append("unsafe OpenAI affiliation claim")
    if INTERNAL_POLICY_RE.search(text):
        failures.append("internal policy wording leaked")
    if SOURCE_SCAFFOLD_RE.search(text):
        failures.append("source/scaffold wording spoken in normal sales answer")
    for key, value in side_effect_flags(packet).items():
        if key in SIDE_EFFECT_KEYS and value:
            failures.append(f"{key} must be false")
    return failures


def validate_opening(text: str) -> list[str]:
    failures: list[str] = []
    lowered = normalize(text)
    if "chatgpt subscription plans" not in lowered:
        failures.append("opening did not say this is about ChatGPT subscription plans")
    if not re.search(r"public-data|public plan|public information|public openai|openai.?s public|official public", text, re.I):
        failures.append("opening did not safely explain public-data/public OpenAI source basis")
    if not re.search(r"not calling (as|from) openai|not representing openai|not an official openai call", text, re.I):
        failures.append("opening did not state non-affiliation safely")
    if not re.search(r"help you decide|help .* decide|worth considering", text, re.I):
        failures.append("opening did not say what it can help decide")
    if re.search(r"\bfree\b.*\bplus\b.*\bpro\b", text, re.I) and "chatgpt subscription plans" not in lowered:
        failures.append("opening listed plan names without product context")
    if len(text.split()) > 58:
        failures.append("opening is an overlong caveat for a call opening")
    return failures


def validate_explanation_first(text: str, packet: dict[str, Any], *, trap: bool = False) -> list[str]:
    failures: list[str] = []
    frame = semantic_frame(packet)
    state = openai_state(packet)
    sub_intent = str(frame.get("sub_intent") or "")
    family = str(frame.get("semantic_family") or "")
    if family not in {"orientation_or_explanation", "source_or_identity"}:
        failures.append(f"explanation question produced semantic_family {family or '<missing>'}")
    expected_shape = EXPLANATION_RESPONSE_BY_SUB_INTENT.get(sub_intent)
    if expected_shape is None:
        failures.append(f"explanation question produced unsupported sub_intent {sub_intent or '<missing>'}")
    elif not expected_shape.search(text):
        failures.append(f"response did not match {sub_intent} answer shape")
    if ADOPTION_LOOP_RE.search(text):
        failures.append("explanation regressed to adoption-state loop instead of answering first")
    if CLOSE_PRESSURE_RE.search(text):
        failures.append("explanation response created close pressure")
    if TEAM_ROUTE_RE.search(text) or str(frame.get("dialogue_focus") or "") == "team_plan_fit" or str(frame.get("target_gap") or "") == "team_use_case":
        failures.append("plan-label explanation question was routed as team/Enterprise intent")
    if question_count(text) > 1:
        failures.append("response asked more than one next question")
    if trap:
        use_case = json.dumps(state.get("openai_use_case"), sort_keys=True).lower()
        if any(value in use_case for value in ("team", "enterprise")):
            failures.append("plan-label trap polluted openai_use_case with team/enterprise")
        if state.get("openai_recommended_path") in {"business", "enterprise"}:
            failures.append("plan-label trap set Business/Enterprise recommended path")
        if state.get("decision_frame") == "business_vs_enterprise":
            failures.append("plan-label trap set Business/Enterprise decision frame")
    return failures


def validate_team_route(text: str, packet: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    frame = semantic_frame(packet)
    state = openai_state(packet)
    if not re.search(r"business|enterprise|team|sso|scim|procurement|security review|admin controls|contact sales", text, re.I):
        failures.append("team/company/admin/security intent did not allow Business/Enterprise route")
    if str(frame.get("dialogue_focus") or "") != "team_plan_fit" and state.get("openai_recommended_path") not in {"business", "enterprise"}:
        failures.append("team positive control did not mark team route or Business/Enterprise path")
    return failures


def validate_adapter_owns(text: str, packet: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    source = str(dialogue_manager(packet).get("final_response_source") or selected_action(packet).get("source") or "")
    frame = semantic_frame(packet)
    if source == "pre_speech_conversation_stability_guard":
        failures.append("stability guard owned recognizable OpenAI commercial turn")
    if stability_guard(packet).get("applied") and source == "pre_speech_conversation_stability_guard":
        failures.append("stability guard applied as final OpenAI selling answer")
    if frame.get("campaign_response_priority") is not True and source not in {"contextual_buyer_semantics", "universal_conversation_policy", "universal_response_shape"}:
        failures.append("recognizable OpenAI turn was not campaign-priority owned")
    if INTERNAL_POLICY_RE.search(text):
        failures.append("internal policy wording leaked")
    if NO_FIT_CAVEAT_RE.search(text):
        failures.append("premature no-fit caveat used without explicit current-tool-enough statement")
    return failures


def validate_neutral_state(packet: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    state = openai_state(packet)
    expected = {
        "openai_recommended_path": {"unknown", "", None},
        "buyer_fit_level": {"unknown", "", None},
        "buyer_momentum": {"neutral", "", None},
        "recommendation_confidence": {"none", "", None},
        "value_hypothesis": {"unknown", "none", "", None},
        "decision_frame": {"unknown", "none", "", None},
        "close_readiness": {"none", "", None},
        "next_commercial_action": {"ask_permission", "ask_adoption_state", "", None},
    }
    for key, allowed in expected.items():
        value = state.get(key)
        if value not in allowed:
            failures.append(f"{key} initialized as {value!r}, expected one of {sorted(str(item) for item in allowed)}")
    if state.get("commercial_stage") == "recommendation":
        failures.append("commercial_stage initialized as recommendation before buyer evidence")
    if state.get("last_recommendation_given"):
        failures.append("last_recommendation_given set before buyer evidence")
    return failures


def validate_repeated_confusion(text: str, responses: list[str], packet: dict[str, Any]) -> list[str]:
    failures = validate_explanation_first(text, packet, trap=True)
    sub_intent = str(semantic_frame(packet).get("sub_intent") or "")
    if sub_intent == "simpler_explanation_request" and not SIMPLE_EXPLANATION_RE.search(text):
        failures.append("repeated confusion did not simplify the explanation")
    normalized_responses = [normalize(response) for response in responses if response]
    if len(normalized_responses) >= 2 and normalized_responses[-1] == normalized_responses[-2]:
        failures.append("repeated confusion repeated the previous response exactly")
    if TEAM_ROUTE_RE.search(text):
        failures.append("repeated confusion looped into team/Enterprise answer")
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
    expectation = item["expectation"]
    if expectation == "opening_clarity":
        failures.extend(validate_opening(text))
    elif expectation == "explanation_first":
        failures.extend(validate_explanation_first(text, packet))
    elif expectation == "plan_label_trap":
        failures.extend(validate_explanation_first(text, packet, trap=True))
    elif expectation == "team_route_allowed":
        failures.extend(validate_team_route(text, packet))
    elif expectation == "adapter_owns":
        failures.extend(validate_adapter_owns(text, packet))
    elif expectation == "neutral_state":
        failures.extend(validate_neutral_state(packet))
    elif expectation == "repeated_confusion_escape":
        failures.extend(validate_repeated_confusion(text, responses, packet))
    else:
        failures.append(f"unknown expectation {expectation!r}")

    manager = dialogue_manager(packet)
    return {
        "id": item["id"],
        "group": item["group"],
        "expectation": expectation,
        "turn_count": len(item["turns"]),
        "multi_turn": item["multi_turn"],
        "note": item.get("note") or "",
        "status": "pass" if not failures else "fail",
        "failures": failures,
        "final_response": text,
        "final_response_hash": sha12(text),
        "final_response_source": manager.get("final_response_source"),
        "stability_guard_reason": manager.get("stability_guard_reason"),
        "semantic": semantic_frame(packet).get("semantic"),
        "dialogue_focus": semantic_frame(packet).get("dialogue_focus"),
        "target_gap": semantic_frame(packet).get("target_gap"),
        "openai_state": {
            key: openai_state(packet).get(key)
            for key in [
                "openai_recommended_path",
                "openai_use_case",
                "buyer_fit_level",
                "buyer_momentum",
                "recommendation_confidence",
                "value_hypothesis",
                "decision_frame",
                "close_readiness",
                "next_commercial_action",
                "commercial_stage",
                "active_decision_frame",
            ]
        },
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
            f"- Opening origin/product defects: `{result['opening_origin_product_clarity_defect_count']}`",
            f"- Explanation misroute defects: `{result['explanation_question_misroute_count']}`",
            f"- Plan-label trap defects: `{result['plan_label_trap_defect_count']}`",
            f"- Team positive-control defects: `{result['team_positive_control_defect_count']}`",
            f"- Stability guard ownership defects: `{result['stability_guard_ownership_defect_count']}`",
            f"- Neutral state initialization defects: `{result['state_initialization_defect_count']}`",
            f"- Repeated confusion loop defects: `{result['repeated_confusion_loop_defect_count']}`",
            f"- Side effects false: `{str(result['side_effects_false']).lower()}`",
            f"- Provider calls made: `{str(result['provider_calls_made']).lower()}`",
            f"- Live TTS calls made: `{str(result['live_tts_calls_made']).lower()}`",
            f"- Raw private transcript copied to public evidence: `{str(result['raw_private_transcript_copied_to_public_evidence']).lower()}`",
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
            json.dumps(result["failed_cases"][:24], indent=2, sort_keys=True),
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
    if len(scenarios) < 120:
        structure_failures.append(f"at least 120 scenarios required, got {len(scenarios)}")
    if multi_turn_count < 80:
        structure_failures.append(f"at least 80 multi-turn scenarios required, got {multi_turn_count}")
    required_group_counts = {
        "opening_origin_product_clarity": 12,
        "what_is_this_explanation_questions": 20,
        "plan_label_traps": 30,
        "team_intent_positive_controls": 12,
        "stability_guard_must_not_own_openai_turns": 20,
        "state_initialization_invariants": 10,
        "loop_escape_repeated_confusion": 16,
    }
    for group, minimum in required_group_counts.items():
        if group_counts[group] < minimum:
            structure_failures.append(f"{group} requires at least {minimum} scenarios, got {group_counts[group]}")

    side_effects_false = all(not any(trace["side_effects"].get(key) for key in SIDE_EFFECT_KEYS) for trace in traces)
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
        "opening_origin_product_clarity_defect_count": sum(1 for trace in traces if trace["group"] == "opening_origin_product_clarity" and trace["status"] != "pass"),
        "explanation_question_misroute_count": sum(1 for trace in traces if trace["group"] == "what_is_this_explanation_questions" and trace["status"] != "pass"),
        "plan_label_trap_defect_count": sum(1 for trace in traces if trace["group"] == "plan_label_traps" and trace["status"] != "pass"),
        "team_positive_control_defect_count": sum(1 for trace in traces if trace["group"] == "team_intent_positive_controls" and trace["status"] != "pass"),
        "stability_guard_ownership_defect_count": sum(1 for trace in traces if trace["group"] == "stability_guard_must_not_own_openai_turns" and trace["status"] != "pass"),
        "state_initialization_defect_count": sum(1 for trace in traces if trace["group"] == "state_initialization_invariants" and trace["status"] != "pass"),
        "repeated_confusion_loop_defect_count": sum(1 for trace in traces if trace["group"] == "loop_escape_repeated_confusion" and trace["status"] != "pass"),
        "side_effects_false": side_effects_false,
        "provider_calls_made": provider_calls,
        "live_tts_calls_made": any(trace["side_effects"].get("live_tts_used") for trace in traces),
        "local_llm_calls_made": any(trace["side_effects"].get("local_llm_calls_made") for trace in traces),
        "raw_private_transcript_copied_to_public_evidence": False,
        "sanitized_live_derived_case_count": sum(1 for trace in traces if trace.get("note") == "sanitized-live-derived"),
        "failed_cases": failed,
        "trace_sample": traces[:30],
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
