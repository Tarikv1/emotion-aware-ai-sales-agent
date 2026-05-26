#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter, defaultdict
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
    SIDE_EFFECT_KEYS,
    build_turn,
    response_text,
    side_effect_flags,
)
from runtime.campaigns import public_openai_chatgpt_plans_dialogue as public_openai_dialogue  # noqa: E402
from runtime.core import contextual_buyer_semantics  # noqa: E402


CHECKPOINT_ID = "PUBLIC-OPENAI-SEMANTIC-UNDERSTANDING-001"
FIXTURE_PATH = ROOT / "runtime" / "campaigns" / "examples" / "public-openai-chatgpt-plans.json"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"
FULL_PIPELINE_GROUPS = {"stability_guard_pass_through"}
_CAMPAIGN_CACHE: dict[str, Any] | None = None

BANNED_INTERNAL_RE = re.compile(
    r"i should not assume buying intent|first i need the adoption state|\badoption state\b|"
    r"current call scope|source-grounded|internal policy|plan fit still needs|"
    r"we already have the use case|approved qualified reviewer path|legacy compatibility|"
    r"human_followup_owner|appointment_target",
    re.I,
)
SOURCE_SCAFFOLD_RE = re.compile(
    r"article lists|article describes|according to|source of truth|source-grounded|"
    r"official sources state|official sources say|the official page says|"
    r"exact tier details should be checked against official openai sources",
    re.I,
)
TERMINAL_NO_SPEECH_CONTROLS = {"end-call", "hang-up", "schedule-and-end"}
TEAM_ROUTE_RE = re.compile(r"team_plan_fit|basic team workspace|enterprise requirements like|for team use", re.I)
DISCOVERY_LOOP_RE = re.compile(
    r"are you using chatgpt today.*another ai tool|mostly not using ai yet|before i can|first i need|"
    r"what would you mainly use chatgpt for",
    re.I,
)
PLAN_LABELS = ["Free", "Plus", "Pro", "Business", "Enterprise"]
ASR_ALIASES = [
    "chachu PT",
    "chachu BT",
    "chat jpt",
    "chat gbt",
    "chat gb t",
    "chat g p t",
    "chad GPT",
    "chat gee pee tee",
]


def normalize(text: Any) -> str:
    return re.sub(r"\s+", " ", str(text or "").strip().lower())


def sha12(text: str) -> str:
    return hashlib.sha256(str(text or "").encode("utf-8")).hexdigest()[:12]


def compact_signature(text: str) -> str:
    tokens = [
        token
        for token in re.findall(r"[a-z0-9]+", normalize(text))
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
    return " ".join(tokens[:24])


def scenario(
    scenario_id: str,
    group: str,
    turns: list[str],
    expectation: dict[str, Any],
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
    return ["__agent_open__", "yeah sure", *turns]


def plan_mentions(text: str) -> list[str]:
    lowered = normalize(text)
    return [label for label in PLAN_LABELS if re.search(rf"\b{label.lower()}\b", lowered)]


def build_orientation_scenarios() -> list[dict[str, Any]]:
    specs = [
        (
            "call_orientation",
            [
                "what is this",
                "what is this about",
                "what are you calling about",
                "what is this call asking",
                "why are you calling me about this",
                "what is the point here",
                "what is this for exactly",
                "what are you trying to explain",
                "why are you mentioning Enterprise",
                "why did you bring up ChatGPT plans",
            ],
            ["call about ChatGPT subscription plans", "public plan options"],
        ),
        (
            "plan_category_explanation",
            [
                "what are these plans",
                "what are the plans",
                "what are those plans",
                "which plans are you talking about",
                "what plans are available",
                "what are the ChatGPT plan names",
                "what are all those plan names",
                "explain the plans",
                "what do you mean by plans",
                "what are Free Plus Pro Business Enterprise",
            ],
            ["subscription options", "Free", "Plus", "Pro", "Business", "Enterprise"],
        ),
        (
            "specific_plan_label_explanation",
            [
                "what are Free Plus and Pro",
                "what is Free Plus Pro",
                "what does Free mean",
                "what does Plus mean",
                "what does Pro mean",
                "explain Free Plus Pro",
                "Free Plus Pro are what exactly",
                "what is the plan called Pro",
                "what is Free compared with Pro",
                "what does Enterprise mean in that list",
            ],
            ["Free", "Plus", "Pro"],
        ),
        (
            "subscription_model_question",
            [
                "is this a subscription thing",
                "is this subscription based",
                "is this a monthly subscription",
                "are these subscriptions",
                "is this a one off purchase",
                "is this a product purchase or subscription",
                "do these plans mean subscription",
                "is this about monthly plans",
                "is this about paying monthly",
                "is this a subscription model",
            ],
            ["subscription plans", "not a one-off product purchase"],
        ),
        (
            "model_vs_product_question",
            [
                "are these models or products",
                "are these products or plans",
                "are these ChatGPT products or plans",
                "are these model names",
                "what are these models",
                "are Free Plus Pro models",
                "are Business and Enterprise models",
                "is Enterprise a product or a plan",
                "is Pro a model name",
                "is this a model or a plan",
            ],
            ["plan options", "not model names"],
        ),
        (
            "simpler_explanation_request",
            [
                "I don't understand what you're talking about",
                "I do not understand what you are talking about",
                "I am confused",
                "I am lost",
                "explain this simply",
                "say that simply",
                "plain English please",
                "make it simple",
                "what is it in one sentence",
                "simpler please",
            ],
            ["Simple version", "choosing the right ChatGPT plan", "Free is enough"],
        ),
        (
            "source_disclosure",
            [
                "where did you get this from",
                "what source is this",
                "whose information is this based on",
                "are you from OpenAI",
                "do you represent OpenAI",
                "is this official OpenAI sales",
                "who are you with",
                "are you affiliated with OpenAI",
                "is OpenAI calling me",
                "what is the source",
            ],
            ["not calling from OpenAI"],
        ),
        (
            "call_orientation",
            [
                "what exactly",
                "what are you talking about",
                "what is this again",
                "why this call",
                "what should I understand first",
                "what are you asking me",
                "why mention plans",
                "why mention paid plans",
                "what is the topic",
                "what is the quick version",
            ],
            ["ChatGPT"],
        ),
    ]
    scenarios: list[dict[str, Any]] = []
    for spec_index, (sub_intent, utterances, required) in enumerate(specs, start=1):
        for index, utterance in enumerate(utterances, start=1):
            turns = with_open(utterance) if index % 2 else [utterance]
            expectation: dict[str, Any] = {
                "semantic_family": "orientation_or_explanation",
                "sub_intent": sub_intent,
                "required_response_fragments": required,
                "forbid_team_route": True,
            }
            if sub_intent == "source_disclosure":
                expectation.pop("sub_intent")
                expectation["sub_intent_in"] = {"source_disclosure", "affiliation_boundary"}
            scenarios.append(
                scenario(
                    f"orientation-{spec_index:02d}-{index:03d}",
                    "orientation_explanation_sub_intents",
                    turns,
                    expectation,
                    note="sanitized-live-derived" if utterance in {"what is this", "I don't understand what you're talking about"} else "",
                )
            )
    return scenarios


def build_plan_label_traps() -> list[dict[str, Any]]:
    forms = ["what is", "explain", "I don't understand", "are these", "is this"]
    combos = [
        ["Free", "Plus"],
        ["Plus", "Pro"],
        ["Free", "Plus", "Pro"],
        ["Business", "Enterprise"],
        ["Free", "Business", "Enterprise"],
        ["Free", "Plus", "Pro", "Business", "Enterprise"],
        ["Enterprise", "Business", "Pro", "Plus", "Free"],
        ["Pro", "Business"],
        ["Free", "Enterprise"],
        ["Plus", "Business", "Enterprise"],
    ]
    punctuation = [" ", ", ", " / ", " and ", " or "]
    scenarios: list[dict[str, Any]] = []
    case_id = 1
    for form in forms:
        for combo in combos:
            for sep in punctuation[:2]:
                phrase = sep.join(combo)
                utterance = f"{form} {phrase}"
                if form == "I don't understand":
                    utterance = f"{form} {phrase}, are they plans or products"
                if form == "are these":
                    utterance = f"{form} {phrase} products or plans"
                if form == "is this":
                    utterance = f"{form} about {phrase}"
                scenarios.append(
                    scenario(
                        f"plan-label-trap-{case_id:03d}",
                        "plan_label_trap_fuzzing",
                        with_open(utterance),
                        {
                            "semantic_family": "orientation_or_explanation",
                            "sub_intent_in": {
                                "plan_category_explanation",
                                "specific_plan_label_explanation",
                                "model_vs_product_question",
                                "simpler_explanation_request",
                            },
                            "object_mentions": combo,
                            "forbid_team_route": True,
                            "forbid_recommendation_state": True,
                        },
                    )
                )
                case_id += 1
                if case_id > 100:
                    return scenarios
    return scenarios


def build_team_controls() -> list[dict[str, Any]]:
    utterances = [
        "we have a team",
        "my company needs SSO",
        "procurement needs terms",
        "we need admin controls",
        "employees need a workspace",
        "our security team needs review",
        "legal needs procurement terms",
        "we need SCIM",
        "we need domain verification",
        "our company needs admin and billing controls",
        "this is for a team workspace",
        "we have employees using it",
        "security review is required",
        "procurement wants contract terms",
        "my company needs enterprise controls",
        "our organization needs SSO",
        "we need workspace controls",
        "our admins need member management",
        "we need a company plan",
        "this is for our business users",
    ]
    scenarios: list[dict[str, Any]] = []
    for index in range(30):
        utterance = utterances[index % len(utterances)]
        scenarios.append(
            scenario(
                f"positive-team-intent-{index + 1:03d}",
                "positive_team_intent_controls",
                with_open(utterance),
                {
                    "semantic_family_in": {"plan_fit", "use_case"},
                    "sub_intent_in": {"team_or_enterprise_fit", "team_plan_fit", "business_enterprise_team_need"},
                    "require_team_route": True,
                },
            )
        )
    return scenarios


def build_and_or_fidelity() -> list[dict[str, Any]]:
    cases = [
        ("I use ChatGPT and other AI tools", "and", "current_chatgpt_and_other_ai_user"),
        ("I use ChatGPT plus other AI tools", "and", "current_chatgpt_and_other_ai_user"),
        ("I use both ChatGPT and Claude", "both", "current_chatgpt_and_other_ai_user"),
        ("I use Claude and ChatGPT depending on the task", "and", "current_chatgpt_and_other_ai_user"),
        ("I use ChatGPT and Gemini too", "and", "current_chatgpt_and_other_ai_user"),
        ("I use ChatGPT or another AI tool, not sure", "either_or", "current_chatgpt_or_other_ai_unknown"),
        ("I may be using ChatGPT or maybe Claude", "either_or", "current_chatgpt_or_other_ai_unknown"),
        ("It might be ChatGPT or another AI tool", "or", "current_chatgpt_or_other_ai_unknown"),
        ("I only use another LLM", "unknown", "current_other_ai_user"),
        ("I use another AI tool, not ChatGPT", "unknown", "current_other_ai_user"),
    ]
    scenarios: list[dict[str, Any]] = []
    for index in range(60):
        utterance, relation, buyer_state = cases[index % len(cases)]
        scenarios.append(
            scenario(
                f"and-or-fidelity-{index + 1:03d}",
                "and_or_fidelity",
                with_open(utterance),
                {
                    "semantic_family": "adoption_state",
                    "conjunction_relation": relation,
                    "buyer_state": buyer_state,
                    "preserve_relation": True,
                },
                note="sanitized-live-derived" if index == 0 else "",
            )
        )
    return scenarios


def build_asr_aliases() -> list[dict[str, Any]]:
    prefixes = ["I use", "I'm using", "do you mean", "why switch to", "I use"]
    suffixes = ["", " and other tools", " plus Claude", " or maybe Claude", " for coding"]
    scenarios: list[dict[str, Any]] = []
    for index in range(80):
        alias = ASR_ALIASES[index % len(ASR_ALIASES)]
        prefix = prefixes[index % len(prefixes)]
        suffix = suffixes[(index // len(ASR_ALIASES)) % len(suffixes)]
        utterance = f"{prefix} {alias}{suffix}"
        scenarios.append(
            scenario(
                f"asr-product-alias-{index + 1:03d}",
                "asr_product_alias_generalization",
                with_open(utterance),
                {
                    "normalized_entity": "ChatGPT",
                    "forbid_stability_owner": True,
                    "forbid_internal_policy": True,
                },
                note="sanitized-live-derived" if alias in {"chachu PT", "chachu BT"} else "",
            )
        )
    return scenarios


def build_direct_questions() -> list[dict[str, Any]]:
    cases = [
        ("how much does Plus cost", "direct_price_question"),
        ("what are the prices", "direct_price_question"),
        ("how do I sign up", "signup_path"),
        ("where do I upgrade", "signup_path"),
        ("is Plus enough for coding", "plus_sufficiency"),
        ("would Plus be enough though", "plus_sufficiency"),
        ("which Pro tier should I use", "pro_tier_choice"),
        ("should I use 100 or 200 Pro", "pro_tier_choice"),
        ("is API included", "api_boundary"),
        ("does this include tokens", "api_boundary"),
        ("why switch from Claude", "competitor_switch_question"),
        ("why would I switch from another LLM", "competitor_switch_question"),
        ("can I change to 200 mid-month", "midcycle_upgrade_question"),
        ("what happens if I upgrade later", "midcycle_upgrade_question"),
        ("that is expensive", "price_objection"),
        ("why would I pay that much", "price_objection"),
    ]
    scenarios: list[dict[str, Any]] = []
    base = with_open("I use ChatGPT for coding and writing", "I use it heavily every day")
    for index in range(80):
        utterance, sub_intent = cases[index % len(cases)]
        turns = [*base, "which Pro tier should I use", utterance] if "mid" in sub_intent else [*base, utterance]
        scenarios.append(
            scenario(
                f"direct-question-priority-{index + 1:03d}",
                "direct_question_priority",
                turns,
                {
                    "sub_intent": sub_intent,
                    "should_answer_directly": True,
                    "forbid_discovery_loop": True,
                },
            )
        )
    return scenarios


def build_state_invariants() -> list[dict[str, Any]]:
    cases = [
        (
            ["I use ChatGPT for coding and writing", "what are these plans", "I use it heavily every day"],
            {"known_use_case": "coding", "explanation_no_team_mutation": True},
        ),
        (
            ["I use it heavily every day for coding and writing", "which Pro tier should I use", "what happens if I move to 200 mid-month"],
            {"decision_frame": "pro_100_vs_200"},
        ),
        (
            ["what are Free Plus Pro Business Enterprise", "I am just trying to understand"],
            {"no_recommendation_from_explanation": True},
        ),
        (
            ["I don't understand what you're talking about", "what are these plans", "are those models"],
            {"no_team_from_confusion": True},
        ),
        (
            ["I do not use AI tools", "explain this simply"],
            {"buyer_state": "no_ai_user"},
        ),
        (
            ["I use ChatGPT or another AI tool not sure", "what are the plans"],
            {"buyer_state": "current_chatgpt_or_other_ai_unknown"},
        ),
    ]
    scenarios: list[dict[str, Any]] = []
    for index in range(60):
        turns, expectation = cases[index % len(cases)]
        scenarios.append(
            scenario(
                f"state-transition-invariant-{index + 1:03d}",
                "state_transition_invariants",
                with_open(*turns),
                expectation,
            )
        )
    return scenarios


def build_response_variation() -> list[dict[str, Any]]:
    chains = [
        ["what is this", "no, what are the plans", "are those models"],
        ["what are these plans", "what are Free Plus and Pro", "is this subscription thing"],
        ["I don't understand what you're talking about", "explain Free Plus Pro", "what is this call about"],
        ["what are Free Plus Pro Business Enterprise", "are those products or plans", "explain this simply"],
        ["what are you calling about", "what are these plans", "what does Pro mean"],
    ]
    scenarios: list[dict[str, Any]] = []
    for index in range(50):
        scenarios.append(
            scenario(
                f"response-variation-{index + 1:03d}",
                "response_variation_no_canned_repetition",
                with_open(*chains[index % len(chains)]),
                {"response_variation_required": True},
            )
        )
    return scenarios


def build_internal_policy_ban() -> list[dict[str, Any]]:
    utterances = [
        "what is this",
        "I use ChatGPT and other AI tools",
        "what are Free Plus Pro Business Enterprise",
        "why switch from Claude",
        "how much does Pro cost",
        "which Pro tier should I use",
        "how do I sign up",
        "I don't understand what you're talking about",
        "do you mean chachu PT",
        "is this a subscription thing",
    ]
    scenarios: list[dict[str, Any]] = []
    for index in range(50):
        scenarios.append(
            scenario(
                f"internal-policy-ban-{index + 1:03d}",
                "internal_policy_leak_ban",
                with_open(utterances[index % len(utterances)]),
                {"forbid_internal_policy": True, "forbid_blank_response": True},
            )
        )
    return scenarios


def build_stability_pass_through() -> list[dict[str, Any]]:
    utterances = [
        "what is this",
        "what are these plans",
        "I use ChatGPT and other AI tools",
        "I use ChatGPT or another AI tool not sure",
        "chachu PT and other tools",
        "why switch from chad GPT",
        "how much is Plus",
        "how do I sign up",
    ]
    scenarios: list[dict[str, Any]] = []
    for index in range(40):
        scenarios.append(
            scenario(
                f"stability-pass-through-{index + 1:03d}",
                "stability_guard_pass_through",
                with_open(utterances[index % len(utterances)]),
                {"forbid_stability_owner": True, "confidence_min_for_strategy": 0.7},
            )
        )
    return scenarios


def build_scenarios() -> list[dict[str, Any]]:
    scenarios = []
    scenarios.extend(build_orientation_scenarios())
    scenarios.extend(build_plan_label_traps())
    scenarios.extend(build_team_controls())
    scenarios.extend(build_and_or_fidelity())
    scenarios.extend(build_asr_aliases())
    scenarios.extend(build_direct_questions())
    scenarios.extend(build_state_invariants())
    scenarios.extend(build_response_variation())
    scenarios.extend(build_internal_policy_ban())
    scenarios.extend(build_stability_pass_through())
    return scenarios


def manager(packet: dict[str, Any]) -> dict[str, Any]:
    value = packet.get("dialogue_manager")
    return value if isinstance(value, dict) else {}


def semantic_frame(packet: dict[str, Any]) -> dict[str, Any]:
    value = manager(packet).get("contextual_buyer_semantics")
    return value if isinstance(value, dict) else {}


def memory_state(packet: dict[str, Any]) -> dict[str, Any]:
    memory = packet.get("demo_conversation_memory") or packet.get("conversation_memory") or {}
    if not isinstance(memory, dict):
        return {}
    state = memory.get("openai_chatgpt_plan_state")
    return state if isinstance(state, dict) else {}


def source_text(packet: dict[str, Any]) -> str:
    guard = packet.get("demo_conversation_stability_guard")
    if not isinstance(guard, dict):
        guard = packet.get("pre_speech_conversation_stability_guard") if isinstance(packet.get("pre_speech_conversation_stability_guard"), dict) else {}
    mgr = manager(packet)
    return " ".join(
        str(item or "")
        for item in [
            mgr.get("final_response_source"),
            mgr.get("stability_guard_reason"),
            guard.get("reason"),
        ]
    )


def load_campaign() -> dict[str, Any]:
    global _CAMPAIGN_CACHE
    if _CAMPAIGN_CACHE is None:
        _CAMPAIGN_CACHE = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    return dict(_CAMPAIGN_CACHE)


def append_synthetic_turn(
    state: dict[str, Any],
    *,
    transcript: str,
    response: str,
    frame: dict[str, Any],
    memory: dict[str, Any],
) -> None:
    state.setdefault("turns", []).append(
        {
            "transcript": transcript,
            "summary": {
                "transcript": transcript,
                "final_response": response,
            },
            "continuity": {
                "contextual_buyer_semantics": frame,
            },
            "conversation_memory": dict(memory),
            "dialogue_manager": {
                "contextual_buyer_semantics": frame,
                "final_response": response,
                "final_response_source": "contextual_buyer_semantics",
            },
        }
    )


def synthetic_packet(transcript: str, response: str, frame: dict[str, Any], memory: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "summary": {
            "transcript": transcript,
            "final_response": response,
        },
        "dialogue_manager": {
            "contextual_buyer_semantics": frame,
            "final_response": response,
            "final_response_source": "contextual_buyer_semantics",
            "stability_guard_reason": "semantic_direct_validator_path",
        },
        "demo_conversation_memory": dict(memory or {}),
        "provider_calls_made": False,
        "local_llm_calls_made": False,
        "sends_email": False,
        "creates_calendar_event": False,
        "writes_crm": False,
        "opens_prod_102": False,
    }


def run_semantic_direct_sequence(item: dict[str, Any]) -> dict[str, Any]:
    campaign = load_campaign()
    state: dict[str, Any] = {"turns": []}
    memory: dict[str, Any] = {}
    packets: list[dict[str, Any]] = []
    responses: list[str] = []
    final_transcript = ""
    for turn in item["turns"]:
        if turn == "__agent_open__":
            response = "This is a call about ChatGPT subscription plans."
            frame: dict[str, Any] = {}
            append_synthetic_turn(state, transcript=turn, response=response, frame=frame, memory=memory)
            packets.append(synthetic_packet(turn, response, frame, memory))
            responses.append(response)
            continue
        final_transcript = turn
        frame = contextual_buyer_semantics.classify_contextual_buyer_semantics(turn, state, campaign)
        response = str(frame.get("candidate_response") or "")
        state_update = public_openai_dialogue.memory_update_for_turn(
            transcript=turn,
            turns=list(state.get("turns") or []),
            final_response=response,
            campaign=campaign,
            current_memory=memory,
        )
        if state_update:
            memory[public_openai_dialogue.OPENAI_STATE_KEY] = state_update
        append_synthetic_turn(state, transcript=turn, response=response, frame=frame, memory=memory)
        packets.append(synthetic_packet(turn, response, frame, memory))
        responses.append(response)
    return {
        "packets": packets,
        "responses": responses,
        "final_packet": packets[-1] if packets else synthetic_packet(final_transcript, "", {}, memory),
        "final_response": responses[-1] if responses else "",
        "final_semantic": semantic_frame(packets[-1]) if packets else {},
        "final_memory": memory_state(packets[-1]) if packets else {},
        "final_source": source_text(packets[-1]) if packets else "",
    }


def run_full_pipeline_sequence(item: dict[str, Any]) -> dict[str, Any]:
    state: dict[str, Any] = {"turns": []}
    packets: list[dict[str, Any]] = []
    responses: list[str] = []
    for turn in item["turns"]:
        packet = build_turn(turn, state, item["id"])
        packets.append(packet)
        responses.append(response_text(packet))
    return {
        "packets": packets,
        "responses": responses,
        "final_packet": packets[-1] if packets else {},
        "final_response": responses[-1] if responses else "",
        "final_semantic": semantic_frame(packets[-1]) if packets else {},
        "final_memory": memory_state(packets[-1]) if packets else {},
        "final_source": source_text(packets[-1]) if packets else "",
    }


def run_turn_sequence(item: dict[str, Any]) -> dict[str, Any]:
    if item["group"] in FULL_PIPELINE_GROUPS:
        return run_full_pipeline_sequence(item)
    return run_semantic_direct_sequence(item)


def contains_all(text: str, fragments: list[str]) -> bool:
    lowered = normalize(text)
    return all(normalize(fragment) in lowered for fragment in fragments)


def evaluate_scenario(item: dict[str, Any]) -> dict[str, Any]:
    run = run_turn_sequence(item)
    response = run["final_response"]
    frame = run["final_semantic"]
    state = run["final_memory"]
    expected = item["expectation"]
    failures: list[str] = []

    if not response.strip():
        call_control = str(manager(run["final_packet"]).get("call_control") or "")
        if call_control not in TERMINAL_NO_SPEECH_CONTROLS:
            failures.append("blank final_response without documented terminal call_control")
    if BANNED_INTERNAL_RE.search(response):
        failures.append("internal policy language spoken")
    if expected.get("forbid_internal_policy") and BANNED_INTERNAL_RE.search(response):
        failures.append("banned internal phrase present")

    family = str(frame.get("semantic_family") or "")
    speech_act = str(frame.get("speech_act") or "")
    sub_intent = str(frame.get("sub_intent") or "")
    relation = str(frame.get("conjunction_relation") or "")
    buyer_state = str(frame.get("buyer_state") or "")
    source = run["final_source"]
    if SOURCE_SCAFFOLD_RE.search(response) and sub_intent != "source_disclosure":
        failures.append("source/scaffold language spoken in normal sales answer")

    if expected.get("semantic_family") and family != expected["semantic_family"]:
        failures.append(f"semantic_family expected {expected['semantic_family']} got {family or '<missing>'}")
    if expected.get("semantic_family_in") and family not in expected["semantic_family_in"]:
        failures.append(f"semantic_family {family or '<missing>'} not in allowed set")
    if expected.get("sub_intent") and sub_intent != expected["sub_intent"]:
        failures.append(f"sub_intent expected {expected['sub_intent']} got {sub_intent or '<missing>'}")
    if expected.get("sub_intent_in") and sub_intent not in expected["sub_intent_in"]:
        failures.append(f"sub_intent {sub_intent or '<missing>'} not in allowed set")
    if expected.get("conjunction_relation") and relation != expected["conjunction_relation"]:
        failures.append(f"conjunction_relation expected {expected['conjunction_relation']} got {relation or '<missing>'}")
    if expected.get("buyer_state"):
        memory_buyer_state = str(state.get("openai_adoption_state") or "")
        if buyer_state != expected["buyer_state"] and memory_buyer_state != expected["buyer_state"]:
            failures.append(f"buyer_state expected {expected['buyer_state']} got {buyer_state or memory_buyer_state or '<missing>'}")

    object_mentions = frame.get("object_mentions") if isinstance(frame.get("object_mentions"), list) else []
    for mention in expected.get("object_mentions") or []:
        if mention not in object_mentions:
            failures.append(f"plan label {mention!r} missing from object_mentions")
    if expected.get("normalized_entity"):
        entities = frame.get("normalized_entities") if isinstance(frame.get("normalized_entities"), dict) else {}
        entity_text = json.dumps(entities, sort_keys=True)
        if expected["normalized_entity"] not in entity_text:
            failures.append(f"normalized entity {expected['normalized_entity']} missing")

    required_fragments = expected.get("required_response_fragments") or []
    if required_fragments and not contains_all(response, required_fragments):
        failures.append(f"response missing required fragments: {required_fragments}")
    if expected.get("forbid_team_route") and (TEAM_ROUTE_RE.search(response) or state.get("decision_frame") == "business_vs_enterprise"):
        failures.append("plan label or explanation question routed to team/Enterprise")
    if expected.get("require_team_route") and not (TEAM_ROUTE_RE.search(response) or state.get("decision_frame") == "business_vs_enterprise"):
        failures.append("positive team intent did not route to Business/Enterprise")
    if expected.get("forbid_recommendation_state") and state.get("openai_recommended_path") not in {None, "", "unknown"}:
        failures.append("explanation question created recommendation state")
    if expected.get("forbid_discovery_loop") and DISCOVERY_LOOP_RE.search(response):
        failures.append("direct question answered with discovery loop")
    if expected.get("should_answer_directly") and frame.get("should_answer_directly") is not True:
        failures.append("semantic frame did not mark direct-answer priority")
    if expected.get("preserve_relation"):
        text = normalize(response)
        if relation in {"and", "both"} and " or another ai tool" in text:
            failures.append("buyer said AND/BOTH but response changed it to OR")
        if relation in {"or", "either_or"} and " and other ai tools" in text:
            failures.append("buyer was uncertain/OR but response changed it to AND")
    if expected.get("forbid_stability_owner"):
        if "pre_speech_conversation_stability_guard" in source:
            failures.append("stability guard owned recognized commercial turn")
    if expected.get("confidence_min_for_strategy") is not None:
        confidence = float(frame.get("confidence") or 0.0)
        strategy = str(frame.get("response_strategy") or "")
        if confidence >= float(expected["confidence_min_for_strategy"]) and strategy and "pre_speech_conversation_stability_guard" in source:
            failures.append("medium/high confidence semantic strategy routed through stability guard")

    if expected.get("response_variation_required"):
        signatures = [compact_signature(item) for item in run["responses"] if item.strip()]
        final_three = signatures[-3:]
        if len(final_three) != len(set(final_three)):
            failures.append("same response signature repeated across new semantic objects")

    if expected.get("known_use_case"):
        use_case_text = json.dumps(state.get("openai_use_case") or "")
        if expected["known_use_case"] not in normalize(use_case_text):
            failures.append("use case did not persist across explanation turn")
    if expected.get("decision_frame") and state.get("active_decision_frame") != expected["decision_frame"]:
        failures.append(f"decision frame expected {expected['decision_frame']} got {state.get('active_decision_frame')}")
    if expected.get("no_recommendation_from_explanation") and state.get("openai_recommended_path") not in {None, "", "unknown"}:
        failures.append("explanation/curiosity mutated recommendation")
    if expected.get("no_team_from_confusion") and state.get("decision_frame") == "business_vs_enterprise":
        failures.append("confusion created team state")

    flags = side_effect_flags(run["final_packet"])
    side_effect_failures = [key for key in SIDE_EFFECT_KEYS if flags.get(key)]
    if flags.get("live_tts_used") or flags.get("tts_provider_calls_made") or flags.get("audio_file_created"):
        side_effect_failures.append("validator must not use live TTS, provider calls, or audio files")
    failures.extend(side_effect_failures)

    return {
        "id": item["id"],
        "group": item["group"],
        "status": "pass" if not failures else "fail",
        "turn_count": len(item["turns"]),
        "multi_turn": item["multi_turn"],
        "semantic_family": family,
        "speech_act": speech_act,
        "sub_intent": sub_intent,
        "response_strategy": str(frame.get("response_strategy") or ""),
        "object_type": str(frame.get("object_type") or ""),
        "conjunction_relation": relation,
        "buyer_state": buyer_state,
        "next_best_sales_action": str(frame.get("next_best_sales_action") or ""),
        "raw_buyer_text": item["turns"][-1] if item["turns"] else "",
        "normalized_buyer_text": normalize(item["turns"][-1] if item["turns"] else ""),
        "final_response_hash": sha12(response),
        "final_response": response,
        "final_response_source": str(manager(run["final_packet"]).get("final_response_source") or ""),
        "stability_guard_reason": str(manager(run["final_packet"]).get("stability_guard_reason") or ""),
        "failures": failures,
        "note": item.get("note", ""),
    }


def summarize_group_results(traces: list[dict[str, Any]]) -> dict[str, Any]:
    group_results: dict[str, Any] = {}
    for group in sorted({trace["group"] for trace in traces}):
        group_traces = [trace for trace in traces if trace["group"] == group]
        group_results[group] = {
            "scenario_count": len(group_traces),
            "passed_count": sum(1 for trace in group_traces if trace["status"] == "pass"),
            "failed_count": sum(1 for trace in group_traces if trace["status"] != "pass"),
        }
    return group_results


def main() -> int:
    scenarios = build_scenarios()
    traces = [evaluate_scenario(item) for item in scenarios]
    failed = [trace for trace in traces if trace["status"] != "pass"]
    group_counts = dict(sorted(Counter(item["group"] for item in scenarios).items()))
    sub_intent_responses: dict[str, set[str]] = defaultdict(set)
    for trace in traces:
        if trace["group"] == "orientation_explanation_sub_intents" and trace["sub_intent"]:
            sub_intent_responses[trace["sub_intent"]].add(trace["final_response_hash"])
    hash_to_sub_intents: dict[str, set[str]] = defaultdict(set)
    for sub_intent, hashes in sub_intent_responses.items():
        for response_hash in hashes:
            hash_to_sub_intents[response_hash].add(sub_intent)
    variation_failures = [
        ",".join(sorted(sub_intents))
        for sub_intents in hash_to_sub_intents.values()
        if len(sub_intents) > 1
    ]
    side_effects_false = all(
        "provider_calls_made" not in " ".join(trace["failures"])
        and "tts_provider_calls_made" not in " ".join(trace["failures"])
        and "audio_file_created" not in " ".join(trace["failures"])
        for trace in traces
    )
    representative_ids = {
        "orientation-call": "orientation-01-001",
        "orientation-plans": "orientation-02-001",
        "specific-labels": "plan-label-trap-001",
        "and-fidelity": "and-or-fidelity-001",
        "or-fidelity": "and-or-fidelity-031",
        "asr-alias": "asr-product-alias-001",
        "direct-price": "direct-question-priority-001",
        "stability-pass-through": "stability-pass-through-001",
    }
    representative_frame_evidence = []
    for label, trace_id in representative_ids.items():
        match = next((trace for trace in traces if trace["id"] == trace_id), None)
        if not match:
            continue
        representative_frame_evidence.append(
            {
                "label": label,
                "raw_buyer_text": match["raw_buyer_text"],
                "normalized_buyer_text": match["normalized_buyer_text"],
                "semantic_family": match["semantic_family"],
                "speech_act": match["speech_act"],
                "sub_intent": match["sub_intent"],
                "conjunction_relation": match["conjunction_relation"],
                "object_type": match["object_type"],
                "response_strategy": match["response_strategy"],
                "next_best_sales_action": match["next_best_sales_action"],
                "final_response_source": match["final_response_source"],
                "final_response": match["final_response"],
            }
        )
    result = {
        "checkpoint_id": CHECKPOINT_ID,
        "status": "pass"
        if not failed
        and len(scenarios) >= 550
        and sum(1 for item in scenarios if item["multi_turn"]) >= 300
        and not variation_failures
        and side_effects_false
        else "fail",
        "scenario_count": len(scenarios),
        "multi_turn_scenario_count": sum(1 for item in scenarios if item["multi_turn"]),
        "group_counts": group_counts,
        "group_results": summarize_group_results(traces),
        "failed_count": len(failed),
        "failed_cases": failed[:40],
        "orientation_sub_intent_response_hash_counts": {
            key: len(value) for key, value in sorted(sub_intent_responses.items())
        },
        "response_variation_failures": variation_failures,
        "representative_frame_evidence": representative_frame_evidence,
        "side_effects_false": side_effects_false,
        "provider_calls_made": False,
        "local_llm_calls_made": False,
        "live_tts_used": False,
        "raw_private_transcript_copied": False,
    }
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
            "",
            "## Group Counts",
            "",
            json.dumps(result["group_counts"], indent=2, sort_keys=True),
            "",
            "## Group Results",
            "",
            json.dumps(result["group_results"], indent=2, sort_keys=True),
            "",
            "## Orientation Response Variation",
            "",
            json.dumps(result["orientation_sub_intent_response_hash_counts"], indent=2, sort_keys=True),
            "",
            "## Representative Frame Evidence",
            "",
            json.dumps(result["representative_frame_evidence"], indent=2, sort_keys=True),
            "",
            "## Failed Cases",
            "",
            json.dumps(result["failed_cases"], indent=2, sort_keys=True),
            "",
        ]
    )
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(json.dumps({key: result[key] for key in ["status", "scenario_count", "multi_turn_scenario_count", "failed_count"]}, sort_keys=True))
    if result["status"] != "pass":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
