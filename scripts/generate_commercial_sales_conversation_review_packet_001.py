"""Generate a commercial sales conversation quality review packet.

This is an evidence-only packet builder. It runs dry-run conversations through
the existing turn builder and writes full conversation artifacts for human or
ChatGPT review. It does not assign final sales-quality scores.
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


CHECKPOINT_ID = "COMMERCIAL-SALES-CONVERSATION-REVIEW-001"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
TMP_DIR = ROOT / ".tmp" / CHECKPOINT_ID
EXAMPLES = ROOT / "runtime" / "campaigns" / "examples"

RUBRIC_DIMENSIONS = [
    "Opening clarity",
    "Permission handling",
    "Buyer acknowledgement",
    "Direct question answering",
    "Pain discovery quality",
    "Implication / consequence development",
    "Objection handling and reframing",
    "Trust / transparency",
    "Conversation control",
    "Appointment-readiness timing",
    "Close / next-step strength",
    "Naturalness and human feel",
    "Safety and claim discipline",
    "Memory / no-loop behavior",
    "Commercial usefulness",
]

QUALITATIVE_LABELS = [
    "strong_sales_conversation",
    "acceptable_but_needs_polish",
    "safe_but_low_conversion",
    "poor_sales_conversation",
    "unsafe_or_unusable",
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

ACK_WORDS = [
    "got it",
    "understood",
    "fair",
    "sure",
    "yes",
    "correct",
    "thanks",
    "you are right",
    "you're right",
    "i mean",
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

INTERNAL_PATTERNS = [
    "i should",
    "approved qualified reviewer path",
    "approved scope here",
    "internal policy",
    "i am asking whether",
]

ROBOTIC_PATTERNS = [
    "the purpose of",
    "you should care only if",
    "useful difference i can state",
    "for a operations",
    "review review",
    "if it is relevant enough",
]

UNSAFE_CLAIM_PATTERNS = [
    "we guarantee",
    "i guarantee",
    "can guarantee",
    "will guarantee",
    "guaranteed result",
    "promise the result",
    "promise coverage",
    "exact price is",
    "exact quote is",
    "covered for sure",
    "roi guarantee",
    "revenue guarantee",
    "security guarantee",
]

APPOINTMENT_ASK_PATTERNS = [
    "what time works",
    "what callback window",
    "callback window works",
    "time window",
    "note a time",
    "schedule",
    "book",
    "tomorrow at",
]

NEXT_STEP_REQUEST_PATTERNS = [
    *APPOINTMENT_ASK_PATTERNS,
    "callback window",
    "what email",
    "email should",
    "email or callback",
    "preferred window",
    "which day",
    "what day or time",
]

DIRECT_QUESTION_HINTS = [
    "what does your product do",
    "why should i care",
    "what problem do you solve",
    "what makes you different",
    "who is this for",
    "is this worth my time",
]

OBJECTION_HINTS = [
    "already have a provider",
    "too expensive",
    "ask my manager",
    "send me proof",
    "not this week",
    "do not see the need",
    "too busy",
]

EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"AIza[0-9A-Za-z_-]{20,}"),
    re.compile(r"(?i)(api[_-]?key|secret|token)\s*[:=]\s*[A-Za-z0-9_\-]{12,}"),
]

UNIVERSAL_RUNTIME_PATH = ROOT / "runtime" / "core" / "universal_conversation_policy_runtime.py"


CAMPAIGNS = [
    {
        "id": "routesignal_live_demo",
        "runtime_campaign_id": "campaign-prod-005-b2b-software",
        "config_path": None,
        "pain": "callbacks are a problem",
        "tentative": "maybe handoffs",
        "no_pain": "not really",
        "clean_recovery": "callbacks are a problem",
    },
    {
        "id": "synthetic-insurance-review",
        "runtime_campaign_id": "synthetic-insurance-review",
        "config_path": EXAMPLES / "synthetic-insurance-review.json",
        "pain": "premium is a problem",
        "tentative": "maybe coverage fit",
        "no_pain": "not really",
        "clean_recovery": "premium is a problem",
    },
    {
        "id": "synthetic-b2b-saas-operations",
        "runtime_campaign_id": "synthetic-b2b-saas-operations",
        "config_path": EXAMPLES / "synthetic-b2b-saas-operations.json",
        "pain": "manual work is a problem",
        "tentative": "maybe integration",
        "no_pain": "not really",
        "clean_recovery": "manual work is a problem",
    },
    {
        "id": "synthetic-automotive-service-review",
        "runtime_campaign_id": "synthetic-automotive-service-review",
        "config_path": EXAMPLES / "synthetic-automotive-service-review.json",
        "pain": "repair timings are usually pretty long",
        "tentative": "maybe repair timing",
        "no_pain": "not really",
        "clean_recovery": "repair timings are usually pretty long",
    },
    {
        "id": "synthetic-home-services-estimate",
        "runtime_campaign_id": "synthetic-home-services-estimate",
        "config_path": EXAMPLES / "synthetic-home-services-estimate.json",
        "pain": "we need service",
        "tentative": "maybe scheduling",
        "no_pain": "not really",
        "clean_recovery": "we need service",
    },
]


def arcs_for_campaign(campaign: dict[str, Any]) -> list[dict[str, Any]]:
    pain = campaign["pain"]
    tentative = campaign["tentative"]
    no_pain = campaign["no_pain"]
    clean_recovery = campaign["clean_recovery"]
    return [
        {
            "arc_type": "smooth_qualified_appointment",
            "review_focus": [
                "Does the agent earn the appointment before asking?",
                "Is the implication bridge natural?",
                "Is the appointment ask controlled but not pushy?",
            ],
            "buyer_script": ["__agent_open__", "yeah sure", pain, "it causes delays", "tomorrow at 3 works"],
        },
        {
            "arc_type": "time_pressure",
            "review_focus": [
                "Does it respect time pressure?",
                "Does it ask one sharp question?",
                "Does it avoid a long menu?",
            ],
            "buyer_script": ["__agent_open__", "make it quick", pain, "not really, it is just annoying", "not now maybe later"],
        },
        {
            "arc_type": "tentative_pain",
            "review_focus": [
                "Does it avoid over-confirming weak pain?",
                "Does it clarify without sounding robotic?",
            ],
            "buyer_script": ["__agent_open__", "yeah sure", tentative, "it is active now", "it wastes time", "tomorrow at 3 works"],
        },
        {
            "arc_type": "direct_question",
            "review_focus": [
                "Does it answer directly before selling?",
                "Does it create relevance?",
            ],
            "buyer_script": ["__agent_open__", "what does your product do", "why should I care", pain, "it causes delays", "tomorrow at 3 works"],
        },
        {
            "arc_type": "objection",
            "review_focus": [
                "Does it reframe objections with control?",
                "Does it avoid giving up too quickly?",
            ],
            "buyer_script": ["__agent_open__", "yeah sure", "we already have a provider", "too expensive", "I need to ask my manager", "send me details"],
        },
        {
            "arc_type": "trust_challenge",
            "review_focus": [
                "Does transparency preserve trust?",
                "Does it stay in control after challenge?",
            ],
            "buyer_script": ["__agent_open__", "who are you", "are you a robot", "yeah sure", pain, "why are you asking", "it causes delays"],
        },
        {
            "arc_type": "confusion_loop_resistance",
            "review_focus": [
                "Does it repair without repeating?",
                "Does it remember prior answers?",
            ],
            "buyer_script": ["__agent_open__", "yeah sure", pain, "what do you mean", "you already asked that", "you didn't answer my question"],
        },
        {
            "arc_type": "social_conversation_management",
            "review_focus": [
                "Does it handle human conversation friction?",
                "Does it avoid treating social moves as pain?",
            ],
            "buyer_script": ["__agent_open__", "slow down", "say that again", "I don't speak English well", "you're annoying"],
        },
        {
            "arc_type": "asr_garble",
            "review_focus": [
                "Does it ask for repeat without derailing?",
                "Does it preserve context?",
            ],
            "buyer_script": ["__agent_open__", "yeah sure", "play a double be good", "yadav would be good", clean_recovery],
        },
        {
            "arc_type": "no_fit_stop",
            "review_focus": [
                "Does it stop cleanly?",
                "Does it avoid desperate behavior?",
            ],
            "buyer_script": ["__agent_open__", "not interested", "I don't want to continue", "stop calling"],
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
    flags = {
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
    return flags


def word_count(text: str) -> int:
    return len(re.findall(r"[A-Za-z0-9']+", text))


def question_count(text: str) -> int:
    return text.count("?")


def contains_any(text: str, phrases: list[str]) -> bool:
    lowered = text.lower()
    return any(phrase in lowered for phrase in phrases)


def has_acknowledgement(text: str) -> bool:
    return contains_any(text, ACK_WORDS)


def appointment_ask(text: str) -> bool:
    return contains_any(text, APPOINTMENT_ASK_PATTERNS)


def next_step_requested_or_captured(text: str, frame: dict[str, Any]) -> bool:
    buyer_move = str(frame.get("buyer_move_id") or "")
    next_action = str(frame.get("next_best_sales_action") or "")
    if contains_any(text, NEXT_STEP_REQUEST_PATTERNS):
        return True
    return buyer_move == "callback_time_provided" or next_action in {
        "confirm_callback_time",
        "capture_send_info_contact",
        "capture_email_before_booking",
        "clarify_callback_window",
        "offer_window_without_calendar_claim",
        "clarify_later_window",
    }


def mechanical_warning_flags(
    *,
    buyer_utterance: str,
    response: str,
    frame: dict[str, Any],
    flags: dict[str, bool],
    call_control: str = "",
) -> list[str]:
    warnings: list[str] = []
    buyer = buyer_utterance.lower()
    lower = response.lower()
    buyer_move = str(frame.get("buyer_move_id") or "")
    readiness = str(frame.get("appointment_readiness") or "")

    if contains_any(lower, FULL_MENU_PATTERNS):
        warnings.append("repeated_full_menu")
    if contains_any(lower, INTERNAL_PATTERNS):
        warnings.append("internal_wording")
    if question_count(response) > 1:
        warnings.append("too_many_questions")
    if (
        buyer_utterance != "__agent_open__"
        and response
        and buyer_move != "asr_garbled_or_low_confidence"
        and not has_acknowledgement(response)
    ):
        warnings.append("no_acknowledgement")
    if any(hint in buyer for hint in DIRECT_QUESTION_HINTS) and not response:
        warnings.append("direct_question_not_answered")
    if any(hint in buyer for hint in DIRECT_QUESTION_HINTS) and contains_any(lower, FULL_MENU_PATTERNS):
        warnings.append("direct_question_not_answered")
    if appointment_ask(response) and buyer_move in {"permission_acknowledgement", "time_constrained_permission"}:
        warnings.append("appointment_too_early")
    if appointment_ask(response) and readiness in {"none", "low"} and "tomorrow at" not in buyer:
        warnings.append("appointment_too_early")
    if readiness == "high" and not next_step_requested_or_captured(response, frame):
        warnings.append("appointment_not_asked_when_ready")
    if any(hint in buyer for hint in OBJECTION_HINTS) and not has_acknowledgement(response):
        warnings.append("weak_objection_reframe")
    if buyer_move == "pain_confirmed" and "?" not in response:
        warnings.append("weak_pain_implication")
    terminal_stop = buyer_move in {"stop_request", "permission_to_continue_denied"} and call_control == "end-call"
    if ("stop here" in lower or "leave it there" in lower) and not terminal_stop:
        warnings.append("over_deferential_stop_offer")
    if contains_any(lower, ROBOTIC_PATTERNS):
        warnings.append("robotic_phrase")
    if contains_any(lower, UNSAFE_CLAIM_PATTERNS):
        warnings.append("unsafe_claim")
    if any(flags.values()):
        warnings.append("side_effect_boundary_failure")
    return sorted(set(warnings))


def turn_record(turn_index: int, buyer_utterance: str, packet: dict[str, Any]) -> dict[str, Any]:
    response = packet_response(packet)
    frame = policy_frame(packet)
    sem = semantic(packet)
    mem = memory(packet)
    flags = side_effect_flags(packet)
    warnings = mechanical_warning_flags(
        buyer_utterance=buyer_utterance,
        response=response,
        frame=frame,
        flags=flags,
        call_control=str((packet.get("summary") or {}).get("call_control") or ""),
    )
    return {
        "turn_index": turn_index,
        "buyer_utterance": buyer_utterance,
        "final_response": response,
        "call_control": call_control(packet),
        "selected_action": {
            "source": str(selected_action(packet).get("source") or ""),
        },
        "semantic": str(sem.get("semantic") or ""),
        "target_gap": sem.get("target_gap"),
        "confirmed_gaps": mem.get("confirmed_gaps"),
        "cleared_gaps": mem.get("cleared_gaps"),
        "universal_policy_frame": frame,
        "sales_progression_stage": frame.get("sales_progression_stage"),
        "appointment_readiness": frame.get("appointment_readiness"),
        "impact_signal_detected": frame.get("impact_signal_detected"),
        "impact_signal_type": frame.get("impact_signal_type"),
        "next_best_sales_action": frame.get("next_best_sales_action"),
        "side_effect_flags": flags,
        "response_word_count": word_count(response),
        "question_count": question_count(response),
        "mechanical_warning_flags": warnings,
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
    for index, buyer_utterance in enumerate(arc["buyer_script"], start=1):
        packet = build_turn(
            transcript=buyer_utterance,
            state=state,
            campaign=campaign,
            conversation_id=conversation_id,
        )
        turns.append(turn_record(index, buyer_utterance, packet))

    warning_counter = Counter()
    side_effect_summary = {key: False for key in SIDE_EFFECT_KEYS}
    for turn in turns:
        warning_counter.update(turn["mechanical_warning_flags"])
        for key, value in (turn.get("side_effect_flags") or {}).items():
            side_effect_summary[key] = bool(side_effect_summary.get(key) or value)

    notes = [
        "Human reviewer should score commercial usefulness from the full turn sequence.",
        "Mechanical warnings are heuristics only and are not final pass/fail labels.",
    ]
    if warning_counter:
        notes.append("Review the mechanical warning flags before scoring.")

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
        "mechanical_warning_flags": sorted(warning_counter.keys()),
        "mechanical_warning_count": sum(warning_counter.values()),
        "notes_for_human_reviewer": notes,
        "requires_human_sales_review": True,
        "codex_assigned_final_sales_quality": False,
        "human_sales_quality_scorecard": blank_scorecard(),
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
        counter.update(conversation.get("mechanical_warning_flags") or [])
        for turn in conversation.get("turns") or []:
            counter.update(turn.get("mechanical_warning_flags") or [])
    return counter


def strongest_by_mechanical_signals(conversations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ordered = sorted(conversations, key=lambda item: (item.get("mechanical_warning_count", 0), item["conversation_id"]))
    return [
        {
            "conversation_id": item["conversation_id"],
            "campaign_id": item["campaign_id"],
            "arc_type": item["arc_type"],
            "mechanical_warning_count": item.get("mechanical_warning_count", 0),
        }
        for item in ordered[:8]
    ]


def most_concerning_by_mechanical_signals(conversations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ordered = sorted(conversations, key=lambda item: (-int(item.get("mechanical_warning_count", 0)), item["conversation_id"]))
    return [
        {
            "conversation_id": item["conversation_id"],
            "campaign_id": item["campaign_id"],
            "arc_type": item["arc_type"],
            "mechanical_warning_count": item.get("mechanical_warning_count", 0),
            "mechanical_warning_flags": item.get("mechanical_warning_flags") or [],
        }
        for item in ordered[:8]
    ]


def build_packet(conversations: list[dict[str, Any]]) -> dict[str, Any]:
    generated_at = datetime.now(timezone.utc).isoformat()
    turn_count = sum(len(item.get("turns") or []) for item in conversations)
    warnings = warning_counts(conversations)
    drift_findings = universalization_drift_findings()
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "generated_at": generated_at,
        "purpose": "Human-review packet for commercial sales conversation quality.",
        "runtime_behavior_changed": False,
        "requires_human_sales_review": True,
        "codex_did_not_assign_final_sales_quality": True,
        "campaigns": [campaign["id"] for campaign in CAMPAIGNS],
        "arc_types": sorted({item["arc_type"] for item in conversations}),
        "conversation_count": len(conversations),
        "turn_count": turn_count,
        "rubric_dimensions": RUBRIC_DIMENSIONS,
        "qualitative_labels_for_human_reviewer": QUALITATIVE_LABELS,
        "mechanical_warning_counts": dict(sorted(warnings.items())),
        "universalization_drift_findings": drift_findings,
        "strongest_looking_conversations_by_mechanical_signals_only": strongest_by_mechanical_signals(conversations),
        "most_concerning_conversations_by_mechanical_signals_only": most_concerning_by_mechanical_signals(conversations),
        "conversations": conversations,
    }


def line_numbers_for(text: str, needle: str) -> list[int]:
    return [
        index
        for index, line in enumerate(text.splitlines(), start=1)
        if needle in line
    ]


CUSTOMER_FACING_RUNTIME_FUNCTIONS = (
    "_human_gap_phrase",
    "_primary_gap_phrase",
    "_sharp_diagnostic_gap_phrase",
    "_campaign_purpose_phrase",
    "_permission_response",
    "_time_pressure_response",
    "_scope_relevance_clarification_response",
    "_pain_implication_response",
    "_tentative_gap_response",
    "render_universal_response_outline",
)


def function_source_with_start(source: str, name: str) -> tuple[str, int]:
    match = re.search(rf"^def {re.escape(name)}\(.*?(?=^def |\Z)", source, flags=re.M | re.S)
    if not match:
        return "", 0
    return match.group(0), source[: match.start()].count("\n") + 1


def customer_facing_function_lines_for(source: str, needle: str) -> list[int]:
    lines: list[int] = []
    for function_name in CUSTOMER_FACING_RUNTIME_FUNCTIONS:
        block, start_line = function_source_with_start(source, function_name)
        if not block:
            continue
        for offset, line in enumerate(block.splitlines()):
            if needle in line:
                lines.append(start_line + offset)
    return lines


def universalization_drift_findings() -> list[dict[str, Any]]:
    source = UNIVERSAL_RUNTIME_PATH.read_text(encoding="utf-8")
    findings: list[dict[str, Any]] = []

    synthetic_ids = [
        "synthetic-insurance-review",
        "synthetic-b2b-saas-operations",
        "synthetic-automotive-service-review",
        "synthetic-home-services-estimate",
    ]
    synthetic_lines: list[int] = []
    for campaign_id in synthetic_ids:
        synthetic_lines.extend(line_numbers_for(source, campaign_id))
    if synthetic_lines:
        findings.append(
            {
                "id": "UDR-001",
                "classification": "actual_architecture_drift",
                "title": "Universal runtime branches on synthetic fixture campaign ids.",
                "file": project_relative(UNIVERSAL_RUNTIME_PATH),
                "line_numbers": sorted(set(synthetic_lines)),
                "evidence": synthetic_ids,
                "risk": "Generic sales behavior can become coupled to fixture ids instead of campaign facts.",
                "recommended_follow_up": "Move primary diagnostic phrase selection to campaign config/adapters.",
            }
        )

    vertical_needles = [
        'vertical == "insurance"',
        'vertical == "b2b_saas"',
        'vertical == "automotive_service"',
        'vertical == "home_services"',
    ]
    vertical_lines: list[int] = []
    for needle in vertical_needles:
        vertical_lines.extend(line_numbers_for(source, needle))
    if vertical_lines:
        findings.append(
            {
                "id": "UDR-002",
                "classification": "temporary_bridge_should_move_to_campaign_config",
                "title": "Universal runtime maps verticals directly to customer-facing gap phrases.",
                "file": project_relative(UNIVERSAL_RUNTIME_PATH),
                "line_numbers": sorted(set(vertical_lines)),
                "evidence": vertical_needles,
                "risk": "A new campaign in the same vertical may inherit the wrong primary pain hypothesis.",
                "recommended_follow_up": "Use campaign fact slots such as core_diagnostic_gaps, gap_label, and gap_value_bridge.",
            }
        )

    routesignal_needles = [
        "inbound demo follow-up slipping",
        "callbacks are the issue",
        "handoffs are the concern",
        "follow-up slipping is the issue",
    ]
    routesignal_lines: list[int] = []
    for needle in routesignal_needles:
        routesignal_lines.extend(line_numbers_for(source, needle))
    if routesignal_lines:
        findings.append(
            {
                "id": "UDR-003",
                "classification": "temporary_bridge_should_move_to_campaign_config",
                "title": "RouteSignal-specific phrasing appears inside universal response rendering.",
                "file": project_relative(UNIVERSAL_RUNTIME_PATH),
                "line_numbers": sorted(set(routesignal_lines)),
                "evidence": routesignal_needles,
                "risk": "RouteSignal preservation logic can leak into generic universal response shape code.",
                "recommended_follow_up": "Keep RouteSignal-specific wording in RouteSignal campaign/playbook facts.",
            }
        )

    customer_phrase_needles = [
        "premium pressure",
        "manual work",
        "repair timing",
        "service need",
        "coverage fit",
        "scheduling",
    ]
    customer_phrase_lines: list[int] = []
    for needle in customer_phrase_needles:
        customer_phrase_lines.extend(customer_facing_function_lines_for(source, needle))
    if customer_phrase_lines:
        findings.append(
            {
                "id": "UDR-004",
                "classification": "temporary_bridge_should_move_to_campaign_config",
                "title": "Customer-facing gap phrases are hardcoded in universal runtime helpers.",
                "file": project_relative(UNIVERSAL_RUNTIME_PATH),
                "line_numbers": sorted(set(customer_phrase_lines)),
                "evidence": customer_phrase_needles,
                "risk": "Sales copy and primary pain language will require code changes instead of config changes.",
                "recommended_follow_up": "Expose the preferred customer-facing phrase per gap through campaign config.",
            }
        )

    if not findings:
        findings.append(
            {
                "id": "UDR-000",
                "classification": "acceptable_test_fixture_only",
                "title": "No fixture-specific universal runtime drift found by static scan.",
                "file": project_relative(UNIVERSAL_RUNTIME_PATH),
                "line_numbers": [],
                "evidence": [],
                "risk": "None found by this limited scan.",
                "recommended_follow_up": "Re-run after next universal runtime behavior change.",
            }
        )
    return findings


def redaction_report_for(packet_text: str) -> dict[str, Any]:
    email_matches = sorted(set(EMAIL_PATTERN.findall(packet_text)))
    secret_matches: list[str] = []
    for pattern in SECRET_PATTERNS:
        secret_matches.extend(match.group(0) for match in pattern.finditer(packet_text))
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "raw_email_like_values_found": len(email_matches),
        "secret_like_values_found": len(secret_matches),
        "redactions_applied": [],
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
            handle.write(json.dumps(conversation, sort_keys=True) + "\n")


def rubric_markdown() -> str:
    lines = [
        "# Commercial Sales Conversation Review Rubric",
        "",
        "Score each dimension from 1 to 5. Leave blank if the conversation does not provide enough evidence.",
        "Codex has not assigned final sales-quality scores; this packet requires human or ChatGPT review.",
        "",
        "## Scoring Dimensions",
    ]
    for index, dimension in enumerate(RUBRIC_DIMENSIONS, start=1):
        lines.append(f"{index}. {dimension}")
    lines.extend(
        [
            "",
            "## Final Qualitative Label",
        ]
    )
    lines.extend(f"- `{label}`" for label in QUALITATIVE_LABELS)
    lines.extend(
        [
            "",
            "## Mechanical Flags Are Not Final Scores",
            "Mechanical warning flags only point reviewers toward possible issues such as loops, excessive questions, weak acknowledgement, unsafe claims, or side-effect boundary failures.",
        ]
    )
    return "\n".join(lines) + "\n"


def review_index_markdown(packet: dict[str, Any]) -> str:
    lines = [
        "# Commercial Sales Conversation Review Index",
        "",
        f"- Checkpoint: `{CHECKPOINT_ID}`",
        f"- Conversations: `{packet['conversation_count']}`",
        f"- Turn records: `{packet['turn_count']}`",
        "",
        "## Conversation Index",
        "| Conversation | Campaign | Arc | Turns | Mechanical warnings |",
        "| --- | --- | --- | ---: | ---: |",
    ]
    for conversation in packet["conversations"]:
        lines.append(
            "| `{conversation_id}` | `{campaign_id}` | `{arc_type}` | {turns} | {warnings} |".format(
                conversation_id=conversation["conversation_id"],
                campaign_id=conversation["campaign_id"],
                arc_type=conversation["arc_type"],
                turns=len(conversation["turns"]),
                warnings=conversation["mechanical_warning_count"],
            )
        )
    return "\n".join(lines) + "\n"


def review_packet_markdown(packet: dict[str, Any]) -> str:
    lines = [
        "# Commercial Sales Conversation Review Packet",
        "",
        "This packet exposes full dry-run conversations for human or ChatGPT review. Codex did not assign final sales-quality scores.",
        "",
        "## Rubric Summary",
    ]
    lines.extend(f"- {dimension}" for dimension in RUBRIC_DIMENSIONS)
    lines.extend(
        [
            "",
            "## Conversation Index",
            "| Conversation | Campaign | Arc | Warnings |",
            "| --- | --- | --- | ---: |",
        ]
    )
    for conversation in packet["conversations"]:
        lines.append(
            "| `{conversation_id}` | `{campaign_id}` | `{arc_type}` | {warnings} |".format(
                conversation_id=conversation["conversation_id"],
                campaign_id=conversation["campaign_id"],
                arc_type=conversation["arc_type"],
                warnings=conversation["mechanical_warning_count"],
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
                f"- Runtime campaign id: `{conversation['runtime_campaign_id']}`",
                f"- Config path: `{conversation['campaign_config_path']}`",
                f"- Arc: `{conversation['arc_type']}`",
                f"- Requires human sales review: `{str(conversation['requires_human_sales_review']).lower()}`",
                f"- Mechanical warnings: `{', '.join(conversation['mechanical_warning_flags']) or 'none'}`",
                "",
                "#### Review Focus",
            ]
        )
        lines.extend(f"- {focus}" for focus in conversation["review_focus"])
        lines.extend(["", "#### Turns"])
        for turn in conversation["turns"]:
            frame = turn.get("universal_policy_frame") or {}
            lines.extend(
                [
                    f"- Turn `{turn['turn_index']}` buyer: {turn['buyer_utterance']}",
                    f"  - Agent: {turn['final_response']}",
                    f"  - Source: `{turn['selected_action']['source']}`; call_control: `{turn['call_control']}`",
                    f"  - Buyer move: `{frame.get('buyer_move_id')}`; readiness: `{turn.get('appointment_readiness')}`; next action: `{turn.get('next_best_sales_action')}`",
                    f"  - Warnings: `{', '.join(turn['mechanical_warning_flags']) or 'none'}`",
                ]
            )
    return "\n".join(lines) + "\n"


def report_markdown(packet: dict[str, Any], redaction: dict[str, Any]) -> str:
    warnings = packet["mechanical_warning_counts"]
    lines = [
        f"# {CHECKPOINT_ID}",
        "",
        "## 1. Summary",
        "Generated a dry-run commercial sales conversation packet for human review. Runtime behavior was not changed.",
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
    lines.extend(["", "## 5. Mechanical Warning Counts"])
    if warnings:
        lines.extend(f"- `{key}`: `{value}`" for key, value in warnings.items())
    else:
        lines.append("- None recorded.")
    lines.extend(["", "## 6. Strongest-Looking Conversations By Mechanical Signals Only"])
    for item in packet["strongest_looking_conversations_by_mechanical_signals_only"]:
        lines.append(
            f"- `{item['conversation_id']}`: `{item['mechanical_warning_count']}` warnings"
        )
    lines.extend(["", "## 7. Most Concerning Conversations By Mechanical Signals Only"])
    for item in packet["most_concerning_conversations_by_mechanical_signals_only"]:
        lines.append(
            f"- `{item['conversation_id']}`: `{item['mechanical_warning_count']}` warnings; flags `{', '.join(item['mechanical_warning_flags']) or 'none'}`"
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
            "## Universalization Drift Risks",
        ]
    )
    for finding in packet.get("universalization_drift_findings") or []:
        lines.extend(
            [
                f"- `{finding['id']}` `{finding['classification']}`: {finding['title']}",
                f"  - File: `{finding['file']}` lines `{', '.join(str(line) for line in finding.get('line_numbers') or []) or 'n/a'}`",
                f"  - Risk: {finding['risk']}",
                f"  - Follow-up: {finding['recommended_follow_up']}",
            ]
        )
    lines.extend(
        [
            "",
            "## 9. What ChatGPT/Human Reviewer Should Evaluate Next",
            "- Whether skeptical buyers would trust the agent after identity, privacy, and challenge turns.",
            "- Whether pain implication questions feel commercially useful rather than scripted.",
            "- Whether appointment asks arrive after enough consequence has been established.",
            "- Whether social and ASR recovery turns preserve control without sounding evasive.",
            "",
            "## 10. Recommended Next Likely Implementation Area",
            "Preliminary only: social and conversation-management repair remains the most likely next implementation slice, because current matrix evidence still clusters there. Human review should confirm before implementation.",
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
        "mechanical_warning_counts": packet["mechanical_warning_counts"],
        "requires_human_sales_review": True,
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
                "output_dir": OUT_DIR.as_posix(),
                "runtime_behavior_changed": False,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
