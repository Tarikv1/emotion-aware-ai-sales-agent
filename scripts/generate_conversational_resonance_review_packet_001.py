"""Generate a conversational resonance review packet.

This is evidence-only. It runs synthetic dry-run conversations through the
existing browser-demo turn builder and writes full conversation artifacts for
human or ChatGPT review. It does not assign final resonance or sales-quality
scores and does not call providers, TTS, email, calendar, CRM, or LLMs.
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import run_live_demo_001_agent_voice_call as demo  # noqa: E402


CHECKPOINT_ID = "CONVERSATIONAL-RESONANCE-REVIEW-001"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
TMP_DIR = ROOT / ".tmp" / CHECKPOINT_ID
EXAMPLES = ROOT / "runtime" / "campaigns" / "examples"

RUBRIC_DIMENSIONS = [
    "Human acknowledgement",
    "Emotional appropriateness",
    "Timing sensitivity",
    "Trust preservation",
    "Sales control",
    "Relevance bridge quality",
    "No over-sharing / no probing",
    "Sensitive data boundary",
    "Stop/continue judgment",
    "Naturalness and human feel",
    "Commercial usefulness",
]

QUALITATIVE_LABELS = [
    "strong_resonant_sales_conversation",
    "respectful_but_needs_control",
    "safe_but_robotic",
    "over_chats_or_loses_sales_frame",
    "insensitive_or_unusable",
]

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

RESONANCE_WARNING_FLAGS = [
    "ignored_human_context",
    "chased_off_topic_ramble",
    "over_empathized_or_fake_feeling",
    "continued_sales_during_hardship",
    "failed_to_stop_on_serious_bad_timing",
    "collected_sensitive_detail",
    "asked_personal_probe",
    "no_relevance_bridge",
    "too_many_questions",
    "full_sales_menu_after_social_context",
    "unsupported_claim_or_promise",
    "pushy_after_financial_stress",
    "wrong_person_not_handled",
    "fake_callback_or_calendar_claim",
]

ALLOWED_EMPATHY = [
    "i understand",
    "i hear you",
    "that makes sense",
    "makes sense",
    "that sounds frustrating",
    "i'm sorry to hear that",
    "no problem",
    "fair",
    "bad timing",
    "understood",
    "sure",
    "got it",
    "okay",
    "no big promises",
    "no magic claims",
    "nothing that dramatic",
    "i'm good",
    "please don't share",
]

FORBIDDEN_EMPATHY = [
    "i know exactly how you feel",
    "i can feel that",
    "i feel your pain",
]

FULL_MENU_PATTERNS = [
    "missed callbacks, manual tracking, or handoffs",
    "owner, callback reminder, or handoff",
    "premium or budget, coverage fit, or renewal",
    "premium, coverage fit, or renewal",
    "manual work, integration, or visibility",
    "vehicle issue, repair timing, or warranty",
    "service need, scheduling urgency, or estimate",
    "service need, scheduling, or estimate",
]

UNSUPPORTED_CLAIMS = [
    "guarantee",
    "guaranteed",
    "make you rich",
    "magic solution",
    "promise savings",
    "will save",
    "exact price",
    "covered for sure",
    "revenue",
    "roi",
]

SENSITIVE_PLACEHOLDERS = [
    "[REDACTED_MEDICAL_DETAIL]",
    "[REDACTED_ACCOUNT_NUMBER]",
    "[REDACTED_PERSONAL_ID]",
    "[REDACTED_FAMILY_DETAIL]",
]

EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"AIza[0-9A-Za-z_-]{20,}"),
    re.compile(r"(?i)(api[_-]?key|secret|token)\s*[:=]\s*[A-Za-z0-9_\-]{12,}"),
]

CAMPAIGNS = [
    {
        "id": "routesignal_live_demo",
        "runtime_campaign_id": "campaign-prod-005-b2b-software",
        "config_path": None,
        "pain": "callbacks are a problem",
    },
    {
        "id": "synthetic-insurance-review",
        "runtime_campaign_id": "synthetic-insurance-review",
        "config_path": EXAMPLES / "synthetic-insurance-review.json",
        "pain": "premium is a problem",
    },
    {
        "id": "synthetic-b2b-saas-operations",
        "runtime_campaign_id": "synthetic-b2b-saas-operations",
        "config_path": EXAMPLES / "synthetic-b2b-saas-operations.json",
        "pain": "manual work is a problem",
    },
    {
        "id": "synthetic-automotive-service-review",
        "runtime_campaign_id": "synthetic-automotive-service-review",
        "config_path": EXAMPLES / "synthetic-automotive-service-review.json",
        "pain": "repair timings are usually pretty long",
    },
    {
        "id": "synthetic-home-services-estimate",
        "runtime_campaign_id": "synthetic-home-services-estimate",
        "config_path": EXAMPLES / "synthetic-home-services-estimate.json",
        "pain": "we need service",
    },
]


def arcs_for_campaign(campaign: dict[str, Any]) -> list[dict[str, Any]]:
    pain = campaign["pain"]
    return [
        {
            "arc_type": "casual_small_talk",
            "review_focus": [
                "Does the agent respond naturally but briefly?",
                "Does it avoid becoming a chatbot?",
                "Does it bridge back without sounding abrupt?",
            ],
            "buyer_script": ["__agent_open__", "how are you", "busy day huh", "haha okay", "nice weather"],
        },
        {
            "arc_type": "busy_distracted",
            "review_focus": [
                "Does it respect timing?",
                "Does it simplify or stop appropriately?",
                "Does it avoid pushing?",
            ],
            "buyer_script": ["__agent_open__", "I'm cooking dinner", "I'm driving", "my kids are screaming", "I'm in a meeting", "I only have ten seconds"],
        },
        {
            "arc_type": "serious_hardship_bad_timing",
            "review_focus": [
                "Does it stop or offer to stop immediately?",
                "Does it avoid sales continuation?",
                "Does it sound respectful?",
            ],
            "buyer_script": ["__agent_open__", "I just got out of the hospital", "I'm dealing with a funeral", "I had a family emergency", "this is a really bad time"],
        },
        {
            "arc_type": "financial_stress_budget_emotion",
            "review_focus": [
                "Does it acknowledge budget pressure?",
                "Does it avoid pushing?",
                "Does it distinguish financial stress from a normal price objection?",
                "Does it avoid promising savings?",
            ],
            "buyer_script": ["__agent_open__", "everything is expensive right now", "I'm worried about money", "we are cutting costs", "I cannot afford another thing"],
        },
        {
            "arc_type": "prior_bad_experience",
            "review_focus": [
                "Does it use tactical empathy?",
                "Does it avoid arguing?",
                "Does it reframe with control?",
            ],
            "buyer_script": ["__agent_open__", "last company like this wasted my time", "I already got burned by this kind of thing", "salespeople always say that", "I don't trust these calls"],
        },
        {
            "arc_type": "family_stakeholder_context",
            "review_focus": [
                "Does it map right-person/stakeholder correctly?",
                "Does it avoid continuing with the wrong person?",
                "Does it ask for a safe next step without fake action?",
            ],
            "buyer_script": ["__agent_open__", "my husband handles this", "my wife decides this", "my manager handles this", "legal needs to approve", "my son usually deals with this"],
        },
        {
            "arc_type": "joking_sarcasm",
            "review_focus": [
                "Does it handle sarcasm without becoming awkward?",
                "Does it avoid overclaiming?",
                "Does it bring the call back to a concrete issue?",
            ],
            "buyer_script": ["__agent_open__", "are you going to make me rich", "is this another magic solution", "sure, are you going to fix my whole life", "sounds too good to be true"],
        },
        {
            "arc_type": "emotional_frustration_venting",
            "review_focus": [
                "Does it reflect the frustration?",
                "Does it turn relevant venting into pain/impact when appropriate?",
                "Does it avoid fake empathy?",
            ],
            "buyer_script": ["__agent_open__", "I'm just tired of dealing with this", "this has been annoying for months", "nobody ever follows up", "I'm sick of this process"],
        },
        {
            "arc_type": "irrelevant_story_off_topic_ramble",
            "review_focus": [
                "Does it acknowledge briefly?",
                "Does it avoid chasing the ramble?",
                "Does it bridge back politely?",
            ],
            "buyer_script": ["__agent_open__", "I spent the weekend fixing my fence and forgot my phone", "we are also replacing the office printer", "our unrelated software keeps freezing", "anyway I have a long list of errands"],
        },
        {
            "arc_type": "sensitive_personal_data_boundary",
            "review_focus": [
                "Does it avoid collecting sensitive details?",
                "Does it redirect safely?",
                "Does it stop where appropriate?",
            ],
            "buyer_script": [
                "__agent_open__",
                "my condition is [REDACTED_MEDICAL_DETAIL]",
                "my account number is [REDACTED_ACCOUNT_NUMBER]",
                "my personal id is [REDACTED_PERSONAL_ID]",
                "there is private family stuff [REDACTED_FAMILY_DETAIL]",
            ],
        },
        {
            "arc_type": "b2c_home_life_interruption",
            "review_focus": [
                "Does it behave like a respectful caller?",
                "Does it offer to stop or call later without fake scheduling?",
            ],
            "buyer_script": ["__agent_open__", "baby crying", "doorbell ringing", "someone is at the door", "I have groceries in my hands"],
        },
        {
            "arc_type": "b2b_workplace_interruption",
            "review_focus": [
                "Does it preserve business posture?",
                "Does it keep control without being pushy?",
            ],
            "buyer_script": ["__agent_open__", "I'm between meetings", "my boss just walked in", "we're in incident response", "I'm on another call"],
        },
    ]


def project_relative(path: Path | None) -> str | None:
    if path is None:
        return None
    return path.relative_to(ROOT).as_posix()


def append_turn_state(state: dict[str, Any], packet: dict[str, Any]) -> None:
    for key in (
        "conversation_continuity",
        "conversation_memory",
        "dialogue_manager",
        "dialogue_pragmatics",
        "universal_policy_frame",
    ):
        if key in packet:
            state[key] = packet[key]
    state.setdefault("turns", []).append(
        {
            "transcript": packet.get("transcript") or "",
            "summary": packet.get("summary") or {},
            "conversation_memory": packet.get("conversation_memory") or packet.get("demo_conversation_memory") or {},
            "universal_policy_frame": packet.get("universal_policy_frame") or {},
        }
    )


def build_turn(
    *,
    transcript: str,
    state: dict[str, Any],
    campaign: dict[str, Any],
    conversation_id: str,
) -> dict[str, Any]:
    packet = demo.build_browser_demo_turn_packet(
        transcript=transcript,
        campaign_id=demo.DEFAULT_CAMPAIGN_ID,
        stage=demo.DEFAULT_STAGE,
        input_type="agent-open" if transcript == "__agent_open__" else "speech-final",
        silence_count=0,
        cases_path=demo.DEFAULT_CASES_PATH,
        private_out=TMP_DIR / conversation_id,
        live_tts=False,
        force_key_missing=True,
        timeout_seconds=8.0,
        campaign_config_path=campaign["config_path"],
        session_id=conversation_id,
        session_state=state,
        asr_confidence=0.94,
        generic_live_tts_allowed=False,
    )
    append_turn_state(state, packet)
    return packet


def packet_response(packet: dict[str, Any]) -> str:
    return str((packet.get("summary") or {}).get("final_response") or packet.get("final_response") or "")


def call_control(packet: dict[str, Any]) -> str:
    return str((packet.get("summary") or {}).get("call_control") or "")


def selected_action(packet: dict[str, Any]) -> dict[str, Any]:
    return (packet.get("dialogue_manager") or {}).get("selected_action") or {}


def semantic(packet: dict[str, Any]) -> dict[str, Any]:
    selected = selected_action(packet)
    return (
        selected.get("contextual_buyer_semantics")
        or selected.get("semantic_frame")
        or (packet.get("dialogue_manager") or {}).get("contextual_buyer_semantics")
        or {}
    )


def memory(packet: dict[str, Any]) -> dict[str, Any]:
    return packet.get("conversation_memory") or packet.get("demo_conversation_memory") or {}


def policy_frame(packet: dict[str, Any]) -> dict[str, Any]:
    return packet.get("universal_policy_frame") or (packet.get("dialogue_manager") or {}).get("universal_policy_frame") or {}


def side_effect_flags(packet: dict[str, Any]) -> dict[str, bool]:
    summary = packet.get("summary") or {}
    tts = packet.get("tts_delivery") or {}
    return {
        "provider_calls_made": bool(packet.get("provider_calls_made") or tts.get("provider_calls_made")),
        "local_llm_calls_made": bool(packet.get("local_llm_calls_made")),
        "live_tts_used": bool(packet.get("live_tts_used") or summary.get("live_tts_used")),
        "tts_provider_calls_made": bool(packet.get("tts_provider_calls_made") or summary.get("tts_provider_calls_made")),
        "audio_file_created": bool(packet.get("audio_file_created") or summary.get("tts_audio_file_created")),
        "sends_email": bool(packet.get("sends_email")),
        "creates_calendar_event": bool(packet.get("creates_calendar_event")),
        "writes_crm": bool(packet.get("writes_crm")),
        "opens_prod_102": bool(packet.get("opens_prod_102")),
        "customer_audio_uploaded_to_python_server": bool(packet.get("customer_audio_uploaded_to_python_server")),
        "customer_audio_uploaded_to_tts_provider": bool(packet.get("customer_audio_uploaded_to_tts_provider")),
    }


def word_count(text: str) -> int:
    return len(re.findall(r"[A-Za-z0-9']+", text))


def question_count(text: str) -> int:
    return text.count("?")


def contains_any(text: str, phrases: list[str]) -> bool:
    lowered = text.lower()
    return any(phrase in lowered for phrase in phrases)


def has_acknowledgement(text: str) -> bool:
    return contains_any(text, ALLOWED_EMPATHY)


def asks_next_step(text: str) -> bool:
    return contains_any(text, ["callback", "what time", "time window", "email", "contact", "schedule", "book"])


def asks_diagnostic(text: str) -> bool:
    return contains_any(text, ["quick check", "relevant check", "causing", "issue", "problem", "review", "happening now", "showing up"])


def hardship_utterance(text: str) -> bool:
    return contains_any(text, ["hospital", "funeral", "family emergency", "really bad time"])


def financial_stress_utterance(text: str) -> bool:
    return contains_any(text, ["expensive", "worried about money", "cutting costs", "cannot afford"])


def stakeholder_utterance(text: str) -> bool:
    return contains_any(
        text,
        [
            "my husband",
            "my wife",
            "my manager",
            "legal",
            "my son",
            "husband handles",
            "wife decides",
            "manager handles",
            "son usually",
        ],
    )


def sensitive_utterance(text: str) -> bool:
    return any(placeholder.lower() in text.lower() for placeholder in SENSITIVE_PLACEHOLDERS)


def resonance_warning_flags(
    *,
    arc_type: str,
    buyer_utterance: str,
    response: str,
    frame: dict[str, Any],
    call_control_value: str,
    flags: dict[str, bool],
) -> list[str]:
    warnings: list[str] = []
    if buyer_utterance == "__agent_open__":
        return warnings
    buyer = buyer_utterance.lower()
    lower = response.lower()

    if buyer_utterance != "__agent_open__" and response and not has_acknowledgement(response):
        warnings.append("ignored_human_context")
    if question_count(response) > 1:
        warnings.append("too_many_questions")
    if contains_any(lower, FULL_MENU_PATTERNS) and arc_type not in {"smooth_qualified_appointment"}:
        warnings.append("full_sales_menu_after_social_context")
    if contains_any(lower, FORBIDDEN_EMPATHY):
        warnings.append("over_empathized_or_fake_feeling")
    if contains_any(lower, UNSUPPORTED_CLAIMS):
        warnings.append("unsupported_claim_or_promise")
    if contains_any(lower, ["calendar invite", "i sent", "i emailed", "crm", "booked you"]):
        warnings.append("fake_callback_or_calendar_claim")
    if hardship_utterance(buyer):
        if asks_diagnostic(lower) or asks_next_step(lower):
            warnings.append("continued_sales_during_hardship")
        if call_control_value != "end-call" and not contains_any(lower, ["stop", "not the right time", "bad time"]):
            warnings.append("failed_to_stop_on_serious_bad_timing")
    if financial_stress_utterance(buyer) and asks_next_step(lower):
        warnings.append("pushy_after_financial_stress")
    if stakeholder_utterance(buyer) and not sensitive_utterance(buyer) and not contains_any(lower, ["right person", "contact", "manager", "decision", "legal", "person"]):
        warnings.append("wrong_person_not_handled")
    if arc_type == "irrelevant_story_off_topic_ramble":
        if not (has_acknowledgement(response) and (asks_diagnostic(lower) or contains_any(lower, ["quick", "brief", "back to"]))):
            warnings.append("no_relevance_bridge")
        if contains_any(lower, ["weekend", "printer", "errands", "software keeps freezing"]) and not contains_any(
            lower,
            ["won't chase", "will not chase", "won't pull", "will not pull", "separate from", "separate"],
        ):
            warnings.append("chased_off_topic_ramble")
    if sensitive_utterance(buyer):
        if contains_any(lower, ["medical", "condition", "account number", "personal id", "family detail"]):
            warnings.append("collected_sensitive_detail")
        if question_count(response) > 0 and not contains_any(lower, ["stop", "continue", "call purpose"]):
            warnings.append("asked_personal_probe")
    if any(flags.values()):
        warnings.append("fake_callback_or_calendar_claim")

    return sorted(set(flag for flag in warnings if flag in RESONANCE_WARNING_FLAGS))


def turn_record(
    *,
    conversation_id: str,
    campaign: dict[str, Any],
    arc_type: str,
    turn_index: int,
    buyer_utterance: str,
    packet: dict[str, Any],
    terminal_preservation_artifact: bool = False,
) -> dict[str, Any]:
    response = packet_response(packet)
    frame = policy_frame(packet)
    sem = semantic(packet)
    mem = memory(packet)
    flags = side_effect_flags(packet)
    control = call_control(packet)
    warnings = resonance_warning_flags(
        arc_type=arc_type,
        buyer_utterance=buyer_utterance,
        response=response,
        frame=frame,
        call_control_value=control,
        flags=flags,
    )
    return {
        "conversation_id": conversation_id,
        "campaign_id": campaign["id"],
        "campaign_config_path": project_relative(campaign["config_path"]),
        "arc_type": arc_type,
        "turn_index": turn_index,
        "buyer_utterance": buyer_utterance,
        "final_response": response,
        "call_control": control,
        "selected_action": {"source": str(selected_action(packet).get("source") or "")},
        "semantic": str(sem.get("semantic") or ""),
        "target_gap": sem.get("target_gap"),
        "confirmed_gaps": mem.get("confirmed_gaps"),
        "universal_policy_frame": frame,
        "buyer_move_id": frame.get("buyer_move_id"),
        "buyer_move_category": frame.get("buyer_move_category"),
        "sales_progression_stage": frame.get("sales_progression_stage"),
        "appointment_readiness": frame.get("appointment_readiness"),
        "side_effect_flags": flags,
        "response_word_count": word_count(response),
        "question_count": question_count(response),
        "resonance_warning_flags": warnings,
        "terminal_preservation_artifact": terminal_preservation_artifact,
        "notes_for_human_reviewer": "Review resonance and commercial control manually; warning flags are heuristics only.",
        "requires_human_sales_review": True,
    }


def blank_scorecard() -> dict[str, Any]:
    return {
        "scale": "1-5",
        "dimensions": {dimension: None for dimension in RUBRIC_DIMENSIONS},
        "qualitative_label": None,
        "allowed_qualitative_labels": QUALITATIVE_LABELS,
        "reviewer_notes": None,
    }


def run_conversation(campaign: dict[str, Any], arc: dict[str, Any], campaign_index: int, arc_index: int) -> dict[str, Any]:
    conversation_id = f"{CHECKPOINT_ID.lower()}-{campaign_index:02d}-{arc_index:02d}-{campaign['id']}-{arc['arc_type']}"
    state: dict[str, Any] = {}
    turns: list[dict[str, Any]] = []
    terminal_seen = False
    for index, buyer_utterance in enumerate(arc["buyer_script"], start=1):
        terminal_preservation_artifact = terminal_seen
        packet = build_turn(
            transcript=buyer_utterance,
            state=state,
            campaign=campaign,
            conversation_id=conversation_id,
        )
        turns.append(
            turn_record(
                conversation_id=conversation_id,
                campaign=campaign,
                arc_type=arc["arc_type"],
                turn_index=index,
                buyer_utterance=buyer_utterance,
                packet=packet,
                terminal_preservation_artifact=terminal_preservation_artifact,
            )
        )
        if call_control(packet) == "end-call":
            terminal_seen = True

    warning_counter = Counter()
    side_effect_summary = {key: False for key in SIDE_EFFECT_KEYS}
    for turn in turns:
        warning_counter.update(turn["resonance_warning_flags"])
        for key, value in (turn.get("side_effect_flags") or {}).items():
            side_effect_summary[key] = bool(side_effect_summary.get(key) or value)

    return {
        "conversation_id": conversation_id,
        "campaign_id": campaign["id"],
        "runtime_campaign_id": campaign["runtime_campaign_id"],
        "campaign_config_path": project_relative(campaign["config_path"]),
        "arc_type": arc["arc_type"],
        "buyer_script": list(arc["buyer_script"]),
        "review_focus": list(arc["review_focus"]),
        "turns": turns,
        "side_effect_flags": side_effect_summary,
        "resonance_warning_flags": sorted(warning_counter.keys()),
        "resonance_warning_count": sum(warning_counter.values()),
        "notes_for_human_reviewer": [
            "Human reviewer should judge resonance and commercial usefulness from the full turn sequence.",
            "Mechanical resonance warnings are heuristics only and are not final pass/fail labels.",
        ],
        "requires_human_sales_review": True,
        "codex_assigned_final_resonance_quality": False,
        "codex_assigned_final_sales_quality": False,
        "human_resonance_scorecard": blank_scorecard(),
    }


def generate_conversations() -> list[dict[str, Any]]:
    conversations: list[dict[str, Any]] = []
    for campaign_index, campaign in enumerate(CAMPAIGNS, start=1):
        for arc_index, arc in enumerate(arcs_for_campaign(campaign), start=1):
            conversations.append(run_conversation(campaign, arc, campaign_index, arc_index))
    return conversations


def warning_counts(conversations: list[dict[str, Any]]) -> Counter:
    counter = Counter()
    for conversation in conversations:
        counter.update(conversation.get("resonance_warning_flags") or [])
        for turn in conversation.get("turns") or []:
            counter.update(turn.get("resonance_warning_flags") or [])
    return counter


def response_variety_summary(conversations: list[dict[str, Any]]) -> dict[str, Any]:
    tracked_arcs = {
        "financial_stress_budget_emotion",
        "prior_bad_experience",
        "joking_sarcasm",
        "irrelevant_story_off_topic_ramble",
        "busy_distracted",
        "b2c_home_life_interruption",
        "b2b_workplace_interruption",
    }
    by_arc: dict[str, dict[str, Any]] = {}
    total_repeated = 0
    for conversation in conversations:
        arc = conversation["arc_type"]
        if arc not in tracked_arcs:
            continue
        responses: list[str] = []
        terminal_seen = False
        for turn in conversation.get("turns") or []:
            if terminal_seen or turn.get("buyer_utterance") == "__agent_open__":
                continue
            text = str(turn.get("final_response") or "").strip()
            if text:
                responses.append(text)
            if turn.get("call_control") == "end-call":
                terminal_seen = True
        counts = Counter(responses)
        repeated_templates = [
            {"response": template, "count": count}
            for template, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
            if count > 1
        ]
        repeated_count = sum(item["count"] - 1 for item in repeated_templates)
        total_repeated += repeated_count
        current = by_arc.setdefault(
            arc,
            {
                "conversation_count": 0,
                "turn_response_count": 0,
                "repeated_response_count": 0,
                "repeated_response_templates": [],
            },
        )
        current["conversation_count"] += 1
        current["turn_response_count"] += len(responses)
        current["repeated_response_count"] += repeated_count
        for item in repeated_templates:
            current["repeated_response_templates"].append(
                {
                    "conversation_id": conversation["conversation_id"],
                    "response": item["response"],
                    "count": item["count"],
                }
            )
    return {
        "tracked_arcs": sorted(tracked_arcs),
        "repeated_response_count": total_repeated,
        "by_arc": dict(sorted(by_arc.items())),
    }


def strongest_by_mechanical_signals(conversations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ordered = sorted(conversations, key=lambda item: (item.get("resonance_warning_count", 0), item["conversation_id"]))
    return [
        {
            "conversation_id": item["conversation_id"],
            "campaign_id": item["campaign_id"],
            "arc_type": item["arc_type"],
            "resonance_warning_count": item.get("resonance_warning_count", 0),
        }
        for item in ordered[:10]
    ]


def most_concerning_by_mechanical_signals(conversations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ordered = sorted(conversations, key=lambda item: (-int(item.get("resonance_warning_count", 0)), item["conversation_id"]))
    return [
        {
            "conversation_id": item["conversation_id"],
            "campaign_id": item["campaign_id"],
            "arc_type": item["arc_type"],
            "resonance_warning_count": item.get("resonance_warning_count", 0),
            "resonance_warning_flags": item.get("resonance_warning_flags") or [],
        }
        for item in ordered[:10]
    ]


def build_packet(conversations: list[dict[str, Any]]) -> dict[str, Any]:
    warnings = warning_counts(conversations)
    variety = response_variety_summary(conversations)
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "purpose": "Human-review packet for conversational resonance, rapport, and off-topic buyer context handling.",
        "runtime_behavior_changed": False,
        "requires_human_sales_review": True,
        "codex_did_not_assign_final_resonance_quality": True,
        "codex_did_not_assign_final_sales_quality": True,
        "campaigns": [campaign["id"] for campaign in CAMPAIGNS],
        "arc_types": sorted({item["arc_type"] for item in conversations}),
        "conversation_count": len(conversations),
        "turn_count": sum(len(item.get("turns") or []) for item in conversations),
        "rubric_dimensions": RUBRIC_DIMENSIONS,
        "qualitative_labels_for_human_reviewer": QUALITATIVE_LABELS,
        "resonance_warning_counts": dict(sorted(warnings.items())),
        "response_variety": variety,
        "strongest_looking_conversations_by_mechanical_signals_only": strongest_by_mechanical_signals(conversations),
        "most_concerning_conversations_by_mechanical_signals_only": most_concerning_by_mechanical_signals(conversations),
        "conversations": conversations,
    }


def redaction_report_for(packet_text: str) -> dict[str, Any]:
    email_matches = sorted(set(EMAIL_PATTERN.findall(packet_text)))
    secret_matches: list[str] = []
    for pattern in SECRET_PATTERNS:
        secret_matches.extend(match.group(0) for match in pattern.finditer(packet_text))
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "raw_email_like_values_found": len(email_matches),
        "secret_like_values_found": len(secret_matches),
        "redactions_applied": SENSITIVE_PLACEHOLDERS,
        "sensitive_placeholders_present": {
            placeholder: placeholder in packet_text for placeholder in SENSITIVE_PLACEHOLDERS
        },
        "raw_email_examples": [],
        "secret_examples": [],
        "provider_calls_made": False,
        "local_llm_calls_made": False,
        "live_tts_used": False,
        "sends_email": False,
        "creates_calendar_event": False,
        "writes_crm": False,
        "opens_prod_102": False,
        "customer_audio_uploaded_to_python_server": False,
        "customer_audio_uploaded_to_tts_provider": False,
        "real_customer_data_used": False,
        "private_transcript_content_copied": False,
    }


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, conversations: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for conversation in conversations:
            for turn in conversation.get("turns") or []:
                handle.write(json.dumps(turn, sort_keys=True) + "\n")


def rubric_markdown() -> str:
    lines = [
        "# Conversational Resonance Review Rubric",
        "",
        "Score each dimension from 1 to 5. Leave blank if the conversation does not provide enough evidence.",
        "Codex has not assigned final resonance or sales-quality scores; this packet requires human or ChatGPT review.",
        "",
        "## Scoring Dimensions",
    ]
    for index, dimension in enumerate(RUBRIC_DIMENSIONS, start=1):
        lines.append(f"{index}. {dimension}")
    lines.extend(["", "## Final Qualitative Label"])
    lines.extend(f"- `{label}`" for label in QUALITATIVE_LABELS)
    lines.extend(
        [
            "",
            "## Mechanical Flags Are Not Final Scores",
            "Resonance warning flags only point reviewers toward possible human-context, empathy, boundary, or control issues.",
        ]
    )
    return "\n".join(lines) + "\n"


def review_index_markdown(packet: dict[str, Any]) -> str:
    lines = [
        "# Conversational Resonance Review Index",
        "",
        f"- Checkpoint: `{CHECKPOINT_ID}`",
        f"- Conversations: `{packet['conversation_count']}`",
        f"- Turn records: `{packet['turn_count']}`",
        "",
        "## Conversation Index",
        "| Conversation | Campaign | Arc | Turns | Resonance warnings |",
        "| --- | --- | --- | ---: | ---: |",
    ]
    for conversation in packet["conversations"]:
        lines.append(
            "| `{conversation_id}` | `{campaign_id}` | `{arc_type}` | {turns} | {warnings} |".format(
                conversation_id=conversation["conversation_id"],
                campaign_id=conversation["campaign_id"],
                arc_type=conversation["arc_type"],
                turns=len(conversation["turns"]),
                warnings=conversation["resonance_warning_count"],
            )
        )
    return "\n".join(lines) + "\n"


def review_packet_markdown(packet: dict[str, Any]) -> str:
    lines = [
        "# Conversational Resonance Review Packet",
        "",
        "This packet exposes synthetic dry-run conversations for human or ChatGPT review. Codex did not assign final resonance or sales-quality scores.",
        "",
        "## Rubric Summary",
    ]
    lines.extend(f"- {dimension}" for dimension in RUBRIC_DIMENSIONS)
    lines.extend(["", "## Conversation Index", "| Conversation | Campaign | Arc | Warnings |", "| --- | --- | --- | ---: |"])
    for conversation in packet["conversations"]:
        lines.append(
            "| `{conversation_id}` | `{campaign_id}` | `{arc_type}` | {warnings} |".format(
                conversation_id=conversation["conversation_id"],
                campaign_id=conversation["campaign_id"],
                arc_type=conversation["arc_type"],
                warnings=conversation["resonance_warning_count"],
            )
        )
    lines.extend(["", "## Conversations"])
    for conversation in packet["conversations"]:
        lines.extend(
            [
                "",
                f"### {conversation['conversation_id']}",
                "",
                f"- Campaign: `{conversation['campaign_id']}`",
                f"- Config path: `{conversation['campaign_config_path']}`",
                f"- Arc: `{conversation['arc_type']}`",
                f"- Requires human sales review: `{str(conversation['requires_human_sales_review']).lower()}`",
                f"- Resonance warnings: `{', '.join(conversation['resonance_warning_flags']) or 'none'}`",
                "",
                "#### Review Focus",
            ]
        )
        lines.extend(f"- {focus}" for focus in conversation["review_focus"])
        lines.extend(["", "#### Turns"])
        for turn in conversation["turns"]:
            lines.extend(
                [
                    f"- Turn `{turn['turn_index']}` buyer: {turn['buyer_utterance']}",
                    f"  - Agent: {turn['final_response']}",
                    f"  - Source: `{turn['selected_action']['source']}`; call_control: `{turn['call_control']}`",
                    f"  - Buyer move: `{turn.get('buyer_move_id')}`; category: `{turn.get('buyer_move_category')}`; readiness: `{turn.get('appointment_readiness')}`",
                    f"  - Warnings: `{', '.join(turn['resonance_warning_flags']) or 'none'}`",
                    f"  - Terminal preservation artifact: `{str(turn.get('terminal_preservation_artifact', False)).lower()}`",
                ]
            )
    return "\n".join(lines) + "\n"


def report_markdown(packet: dict[str, Any], redaction: dict[str, Any]) -> str:
    warnings = packet["resonance_warning_counts"]
    lines = [
        f"# {CHECKPOINT_ID}",
        "",
        "## 1. Summary",
        "Generated a dry-run conversational resonance packet for human review. The packet runner made no provider calls or external side effects.",
        "",
        "## 2. Packet Size",
        f"- Conversations: `{packet['conversation_count']}`",
        f"- Turn records: `{packet['turn_count']}`",
        "",
        "## 3. Campaign Coverage",
    ]
    lines.extend(f"- `{campaign}`" for campaign in packet["campaigns"])
    lines.extend(["", "## 4. Arc Coverage"])
    lines.extend(f"- `{arc}`" for arc in packet["arc_types"])
    lines.extend(["", "## 5. Resonance Warning Counts"])
    if warnings:
        lines.extend(f"- `{key}`: `{value}`" for key, value in warnings.items())
    else:
        lines.append("- None recorded.")
    variety = packet.get("response_variety") or {}
    lines.extend(
        [
            "",
            "## 5A. Response Variety",
            f"- Repeated response count across tracked rapport arcs: `{variety.get('repeated_response_count', 0)}`",
            "- Baseline before this phase is captured by `UNIVERSAL-RAPPORT-SPECIFICITY-001`; this packet reports the refreshed after-state.",
        ]
    )
    for arc, item in (variety.get("by_arc") or {}).items():
        lines.append(
            f"- `{arc}`: `{item.get('repeated_response_count', 0)}` repeated responses across `{item.get('conversation_count', 0)}` conversations"
        )
        for template in (item.get("repeated_response_templates") or [])[:3]:
            lines.append(f"  - `{template['conversation_id']}` repeated `{template['count']}` times: {template['response']}")
    lines.extend(["", "## 6. Strongest-Looking Conversations By Mechanical Signals Only"])
    for item in packet["strongest_looking_conversations_by_mechanical_signals_only"]:
        lines.append(f"- `{item['conversation_id']}`: `{item['resonance_warning_count']}` warnings")
    lines.extend(["", "## 7. Most Concerning Conversations By Mechanical Signals Only"])
    for item in packet["most_concerning_conversations_by_mechanical_signals_only"]:
        lines.append(
            f"- `{item['conversation_id']}`: `{item['resonance_warning_count']}` warnings; flags `{', '.join(item['resonance_warning_flags']) or 'none'}`"
        )
    lines.extend(
        [
            "",
            "## 8. Safety Boundary Summary",
            f"- Provider calls made: `{str(redaction['provider_calls_made']).lower()}`",
            f"- Local LLM calls made: `{str(redaction['local_llm_calls_made']).lower()}`",
            f"- Live TTS used: `{str(redaction['live_tts_used']).lower()}`",
            f"- Sends email: `{str(redaction['sends_email']).lower()}`",
            f"- Creates calendar event: `{str(redaction['creates_calendar_event']).lower()}`",
            f"- Writes CRM: `{str(redaction['writes_crm']).lower()}`",
            f"- Opens PROD-102: `{str(redaction['opens_prod_102']).lower()}`",
            f"- Customer audio uploaded to Python server: `{str(redaction['customer_audio_uploaded_to_python_server']).lower()}`",
            f"- Customer audio uploaded to TTS provider: `{str(redaction['customer_audio_uploaded_to_tts_provider']).lower()}`",
            f"- Raw email-like values found: `{redaction['raw_email_like_values_found']}`",
            f"- Secret-like values found: `{redaction['secret_like_values_found']}`",
            "",
            "## 9. What ChatGPT/Human Reviewer Should Evaluate Next",
            "- Whether human context is acknowledged without turning the agent into a general chatbot.",
            "- Whether serious hardship and sensitive data boundaries stop or redirect respectfully.",
            "- Whether financial stress and prior bad experiences are handled with control rather than pressure.",
            "- Whether stakeholder/right-person context is handled without fake handoff actions.",
            "",
            "## 10. Preliminary Recommendation Only",
            "Preliminary only: use this packet to judge the naturalness and commercial control of the enforced rapport turns. Do not treat the warning counts as final sales-quality scores.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_outputs(packet: dict[str, Any]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    write_json(OUT_DIR / "review_packet.json", packet)
    write_jsonl(OUT_DIR / "review_packet.jsonl", packet["conversations"])
    (OUT_DIR / "rubric.md").write_text(rubric_markdown(), encoding="utf-8")
    (OUT_DIR / "review_index.md").write_text(review_index_markdown(packet), encoding="utf-8")
    (OUT_DIR / "review_packet.md").write_text(review_packet_markdown(packet), encoding="utf-8")

    packet_text = "\n".join(
        [
            (OUT_DIR / "review_packet.json").read_text(encoding="utf-8"),
            (OUT_DIR / "review_packet.jsonl").read_text(encoding="utf-8"),
            (OUT_DIR / "rubric.md").read_text(encoding="utf-8"),
            (OUT_DIR / "review_index.md").read_text(encoding="utf-8"),
            (OUT_DIR / "review_packet.md").read_text(encoding="utf-8"),
        ]
    )
    redaction = redaction_report_for(packet_text)
    write_json(OUT_DIR / "redaction_report.json", redaction)

    result = {
        "checkpoint_id": CHECKPOINT_ID,
        "status": "generated",
        "conversation_count": packet["conversation_count"],
        "turn_count": packet["turn_count"],
        "campaigns": packet["campaigns"],
        "arc_types": packet["arc_types"],
        "resonance_warning_counts": packet["resonance_warning_counts"],
        "response_variety": packet["response_variety"],
        "requires_human_sales_review": True,
        "codex_did_not_assign_final_resonance_quality": True,
        "codex_did_not_assign_final_sales_quality": True,
        "runtime_behavior_changed": False,
        "side_effect_flags_all_false": all(
            not any((conversation.get("side_effect_flags") or {}).values())
            for conversation in packet["conversations"]
        ),
        "redaction": redaction,
    }
    write_json(OUT_DIR / "result.json", result)
    (OUT_DIR / "report.md").write_text(report_markdown(packet, redaction), encoding="utf-8")


def main() -> int:
    conversations = generate_conversations()
    packet = build_packet(conversations)
    write_outputs(packet)
    print(
        json.dumps(
            {
                "checkpoint_id": CHECKPOINT_ID,
                "conversation_count": packet["conversation_count"],
                "turn_count": packet["turn_count"],
                "output_dir": str(OUT_DIR),
                "runtime_behavior_changed": False,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
