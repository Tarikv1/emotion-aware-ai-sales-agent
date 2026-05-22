from __future__ import annotations

from copy import deepcopy
from typing import Any


KNOWLEDGE_ID = "UNIVERSAL-SALES-CONVERSATION-KNOWLEDGE-001"
SCHEMA_VERSION = 1

REQUIRED_RESPONSE_STEPS = [
    "acknowledge buyer meaning",
    "answer direct question if asked",
    "use campaign facts only from allowed slots",
    "respect blocked claims and regulated cautions",
    "choose one next action",
]

SIDE_EFFECT_FLAGS = {
    "provider_calls_made": False,
    "live_tts_used": False,
    "local_llm_calls_made": False,
    "sends_email": False,
    "creates_calendar_event": False,
    "writes_crm": False,
    "opens_prod_102": False,
    "real_customer_data_used": False,
    "private_transcript_content_copied": False,
}

BASE_FACT_SLOTS = [
    "campaign_id",
    "client_name",
    "product_or_offer_name",
    "vertical_id",
    "objective",
    "caller_identity",
    "language",
    "human_followup_owner",
    "appointment_target",
    "allowed_claims",
    "blocked_claims",
    "regulated_cautions",
    "diagnostic_gaps",
    "core_diagnostic_gaps",
    "gap_order",
    "gap_label",
    "gap_definition",
    "gap_review_focus",
    "gap_customer_language",
    "gap_value_bridge",
]

SAFE_RESPONSE_FACT_SLOTS = [
    "client_name",
    "product_or_offer_name",
    "human_followup_owner",
    "appointment_target",
    "allowed_claims",
    "blocked_claims",
    "regulated_cautions",
    "gap_label",
    "gap_review_focus",
    "gap_value_bridge",
]

DEFAULT_FORBIDDEN_PATTERNS = [
    "internal policy wording",
    "approved qualified reviewer path",
    "repeated full diagnostic menu after direct answer",
    "invented guarantee",
    "invented coverage promise",
    "invented refund promise",
    "invented exact price",
    "invented security proof",
    "invented ROI or revenue claim",
]


def _shape(
    shape_id: str,
    *,
    allowed_fact_slots: list[str],
    forbidden_patterns: list[str] | None = None,
    allowed_call_control: list[str] | None = None,
    appointment_pressure_level: str = "none",
    example_outline: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "id": shape_id,
        "required_steps": list(REQUIRED_RESPONSE_STEPS),
        "allowed_fact_slots": list(allowed_fact_slots),
        "forbidden_patterns": list(forbidden_patterns or DEFAULT_FORBIDDEN_PATTERNS),
        "allowed_call_control": list(allowed_call_control or ["continue-call"]),
        "appointment_pressure_level": appointment_pressure_level,
        "example_outline": list(example_outline or []),
    }


RESPONSE_SHAPE_LIBRARY: dict[str, dict[str, Any]] = {
    "acknowledge_then_one_short_diagnostic": _shape(
        "acknowledge_then_one_short_diagnostic",
        allowed_fact_slots=["gap_label", "core_diagnostic_gaps", "diagnostic_gaps"],
        forbidden_patterns=DEFAULT_FORBIDDEN_PATTERNS + ["appointment ask before pain"],
        appointment_pressure_level="none",
        example_outline=[
            "acknowledge permission or neutral answer",
            "ask one short diagnostic question using campaign gap labels",
            "avoid broad menus after a concrete buyer answer",
        ],
    ),
    "acknowledge_time_constraint_then_one_question": _shape(
        "acknowledge_time_constraint_then_one_question",
        allowed_fact_slots=["gap_label", "core_diagnostic_gaps"],
        forbidden_patterns=DEFAULT_FORBIDDEN_PATTERNS + ["long diagnostic menu", "appointment ask"],
        appointment_pressure_level="none",
        example_outline=[
            "acknowledge the buyer has little time",
            "ask one compressed fit question",
            "make the next step optional",
        ],
    ),
    "acknowledge_pain_bridge_to_appointment": _shape(
        "acknowledge_pain_bridge_to_appointment",
        allowed_fact_slots=["human_followup_owner", "appointment_target", "gap_label", "gap_review_focus", "gap_value_bridge"],
        allowed_call_control=["continue-call"],
        appointment_pressure_level="direct",
        example_outline=[
            "acknowledge the named issue",
            "bridge only to the allowed human review target",
            "ask for a time when appointment-setting is appropriate",
        ],
    ),
    "acknowledge_tentative_gap_offer_review_or_stop": _shape(
        "acknowledge_tentative_gap_offer_review_or_stop",
        allowed_fact_slots=["human_followup_owner", "appointment_target", "gap_label", "gap_review_focus"],
        forbidden_patterns=DEFAULT_FORBIDDEN_PATTERNS + ["confirm pain from maybe", "transfer-or-escalate"],
        appointment_pressure_level="low",
        example_outline=[
            "acknowledge uncertainty",
            "do not treat tentative language as confirmed pain",
            "offer review or stop",
        ],
    ),
    "answer_product_scope_limit_continue": _shape(
        "answer_product_scope_limit_continue",
        allowed_fact_slots=["product_or_offer_name", "human_followup_owner", "appointment_target", "allowed_claims", "blocked_claims", "gap_review_focus"],
        forbidden_patterns=DEFAULT_FORBIDDEN_PATTERNS + ["transfer-or-escalate", "product advice beyond allowed claims"],
        appointment_pressure_level="low",
        example_outline=[
            "answer that detailed product advice is outside this call",
            "explain the call purpose using allowed facts",
            "offer one next step or stop",
        ],
    ),
    "regulated_claim_boundary_no_advice": _shape(
        "regulated_claim_boundary_no_advice",
        allowed_fact_slots=["human_followup_owner", "blocked_claims", "regulated_cautions", "gap_review_focus"],
        forbidden_patterns=DEFAULT_FORBIDDEN_PATTERNS + ["regulated advice", "guarantee", "exact quote"],
        appointment_pressure_level="low",
        example_outline=[
            "acknowledge the regulated question",
            "do not answer the claim",
            "route only to allowed human review or stop",
        ],
    ),
    "explain_why_asking_preserve_context": _shape(
        "explain_why_asking_preserve_context",
        allowed_fact_slots=["human_followup_owner", "appointment_target", "gap_label", "gap_review_focus"],
        forbidden_patterns=DEFAULT_FORBIDDEN_PATTERNS + ["repeat diagnostic menu", "erase confirmed gap"],
        appointment_pressure_level="low",
        example_outline=[
            "acknowledge the purpose challenge",
            "explain the reason for the current question",
            "preserve existing gap memory and choose one next step",
        ],
    ),
    "contradiction_repair_clarify_role": _shape(
        "contradiction_repair_clarify_role",
        allowed_fact_slots=["human_followup_owner", "appointment_target", "gap_label", "gap_review_focus"],
        forbidden_patterns=DEFAULT_FORBIDDEN_PATTERNS + ["repeat confusing contact boundary", "defensive wording"],
        appointment_pressure_level="low",
        example_outline=[
            "acknowledge the contradiction",
            "clarify the agent can ask basic fit questions",
            "separate basic fit from specialist advice",
        ],
    ),
    "already_answered_preserve_gap": _shape(
        "already_answered_preserve_gap",
        allowed_fact_slots=["gap_label", "gap_review_focus", "appointment_target"],
        forbidden_patterns=DEFAULT_FORBIDDEN_PATTERNS + ["ask the same answered diagnostic", "erase prior answer"],
        appointment_pressure_level="low",
        example_outline=[
            "acknowledge the buyer already answered",
            "summarize the stored answer",
            "move to one next step or stop",
        ],
    ),
    "confusion_explain_plainly": _shape(
        "confusion_explain_plainly",
        allowed_fact_slots=["gap_label", "gap_definition", "appointment_target"],
        forbidden_patterns=DEFAULT_FORBIDDEN_PATTERNS + ["appointment pressure while confused"],
        appointment_pressure_level="none",
        example_outline=[
            "acknowledge confusion",
            "plainly restate the question or term",
            "ask one simple follow-up",
        ],
    ),
    "ask_repeat_for_asr_garble": _shape(
        "ask_repeat_for_asr_garble",
        allowed_fact_slots=["language"],
        forbidden_patterns=DEFAULT_FORBIDDEN_PATTERNS + ["infer pain", "capture appointment", "diagnostic menu"],
        appointment_pressure_level="none",
        example_outline=[
            "acknowledge the transcript was unclear",
            "ask for repeat or short rephrase",
            "do not advance the sales state",
        ],
    ),
    "send_info_contact_capture": _shape(
        "send_info_contact_capture",
        allowed_fact_slots=["human_followup_owner", "appointment_target", "gap_label", "gap_review_focus"],
        forbidden_patterns=DEFAULT_FORBIDDEN_PATTERNS + ["send real email", "invent contact"],
        appointment_pressure_level="low",
        example_outline=[
            "acknowledge request for details",
            "state only a summary/contact path can be noted",
            "ask for email or callback time",
        ],
    ),
    "callback_time_capture": _shape(
        "callback_time_capture",
        allowed_fact_slots=["appointment_target", "human_followup_owner", "language"],
        allowed_call_control=["continue-call", "schedule-and-end"],
        appointment_pressure_level="direct",
        example_outline=[
            "confirm the provided time if usable",
            "ask one clarification if date or time is missing",
            "do not create a real calendar event",
        ],
    ),
    "right_person_capture": _shape(
        "right_person_capture",
        allowed_fact_slots=["appointment_target", "human_followup_owner", "gap_label"],
        forbidden_patterns=DEFAULT_FORBIDDEN_PATTERNS + ["treat contact routing as product pain"],
        appointment_pressure_level="none",
        example_outline=[
            "acknowledge the speaker may not own the issue",
            "ask for right person, team, or safe contact path",
            "offer to stop",
        ],
    ),
    "support_boundary": _shape(
        "support_boundary",
        allowed_fact_slots=["human_followup_owner", "blocked_claims", "regulated_cautions", "appointment_target"],
        forbidden_patterns=DEFAULT_FORBIDDEN_PATTERNS + ["provide account support", "change order", "handle claim"],
        appointment_pressure_level="none",
        example_outline=[
            "acknowledge the support request",
            "state the call cannot handle support/account/order/claim work",
            "offer allowed review path or stop",
        ],
    ),
    "stop_close_politely": _shape(
        "stop_close_politely",
        allowed_fact_slots=["language"],
        forbidden_patterns=DEFAULT_FORBIDDEN_PATTERNS + ["continue selling", "ask diagnostic"],
        allowed_call_control=["end-call"],
        appointment_pressure_level="none",
        example_outline=[
            "acknowledge stop or refusal",
            "close without another question",
            "preserve terminal state",
        ],
    ),
}


def _move(
    move_id: str,
    *,
    description: str,
    examples: list[str],
    expected_response_shape_id: str,
    allowed_stages: list[str],
    default_call_control_allowed: list[str] | None = None,
    memory_policy: str = "preserve_confirmed_and_cleared_gaps",
    must_acknowledge: bool = True,
    must_answer_direct_question: bool = False,
    must_not_do: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "id": move_id,
        "description": description,
        "examples": list(examples),
        "expected_response_shape_id": expected_response_shape_id,
        "allowed_stages": list(allowed_stages),
        "default_call_control_allowed": list(default_call_control_allowed or ["continue-call"]),
        "memory_policy": memory_policy,
        "must_acknowledge": bool(must_acknowledge),
        "must_answer_direct_question": bool(must_answer_direct_question),
        "must_not_do": list(must_not_do or DEFAULT_FORBIDDEN_PATTERNS),
    }


BUYER_MOVE_TAXONOMY: dict[str, dict[str, Any]] = {
    "permission_acknowledgement": _move(
        "permission_acknowledgement",
        description="Buyer grants permission to continue after an opening or permission check.",
        examples=["yes", "yeah sure", "go ahead"],
        expected_response_shape_id="acknowledge_then_one_short_diagnostic",
        allowed_stages=["permission", "opening"],
        memory_policy="do_not_mark_pain_or_appointment",
        must_not_do=["classify as pain", "classify as appointment consent", "ask for time immediately"],
    ),
    "time_constrained_permission": _move(
        "time_constrained_permission",
        description="Buyer grants limited time and asks the caller to be quick.",
        examples=["make it quick", "one quick minute", "short minute"],
        expected_response_shape_id="acknowledge_time_constraint_then_one_question",
        allowed_stages=["permission", "opening"],
        memory_policy="do_not_mark_pain_or_appointment",
        must_not_do=["use full diagnostic menu", "ask appointment before pain"],
    ),
    "pain_confirmed": _move(
        "pain_confirmed",
        description="Buyer confirms a relevant problem, risk, cost, delay, friction, or gap.",
        examples=["that is a problem", "timing is usually long", "manual work is the issue"],
        expected_response_shape_id="acknowledge_pain_bridge_to_appointment",
        allowed_stages=["diagnostic", "value_bridge", "permission"],
        memory_policy="store_confirmed_gap_preserve_cleared_gaps",
        must_not_do=["repeat full diagnostic menu", "invent outcome claim"],
    ),
    "tentative_gap_interest": _move(
        "tentative_gap_interest",
        description="Buyer gives a hedged or uncertain indication that a named gap may matter.",
        examples=["maybe coverage fit", "possibly timing", "could be integration"],
        expected_response_shape_id="acknowledge_tentative_gap_offer_review_or_stop",
        allowed_stages=["diagnostic", "value_bridge", "scope_limit"],
        memory_policy="store_tentative_gap_without_confirming_pain",
        must_not_do=["confirm pain from maybe", "transfer-or-escalate", "repeat full diagnostic menu"],
    ),
    "no_pain_clear": _move(
        "no_pain_clear",
        description="Buyer says the current gap, asked scope, or whole topic is handled or not a problem.",
        examples=["that is handled", "no issue there", "that part is fine"],
        expected_response_shape_id="acknowledge_then_one_short_diagnostic",
        allowed_stages=["diagnostic", "value_bridge"],
        memory_policy="store_cleared_gap_preserve_confirmed_gaps",
        must_not_do=["classify as pain", "erase confirmed pain"],
    ),
    "not_relevant": _move(
        "not_relevant",
        description="Buyer says the campaign topic does not apply or is not useful.",
        examples=["not relevant", "we do not need this", "no need"],
        expected_response_shape_id="stop_close_politely",
        allowed_stages=["opening", "permission", "diagnostic", "value_bridge"],
        default_call_control_allowed=["continue-call", "end-call"],
        memory_policy="respect_no_fit_or_one_safe_save_question_by_stage",
        must_not_do=["push appointment", "repeat diagnostic menu"],
    ),
    "product_detail_question": _move(
        "product_detail_question",
        description="Buyer asks what the offer is, what it includes, or how the product works.",
        examples=["what does your product do?", "what is included?", "can you give details?"],
        expected_response_shape_id="answer_product_scope_limit_continue",
        allowed_stages=["opening", "permission", "diagnostic", "scope_limit", "value_bridge"],
        memory_policy="preserve_existing_gap_context",
        must_answer_direct_question=True,
        must_not_do=["invent product details", "repeat diagnostic menu", "transfer-or-escalate"],
    ),
    "scope_limit_question": _move(
        "scope_limit_question",
        description="Buyer asks whether the caller can give detailed advice or only route to a human reviewer.",
        examples=["so you cannot give me details?", "are you only setting up a review?"],
        expected_response_shape_id="answer_product_scope_limit_continue",
        allowed_stages=["scope_limit", "diagnostic", "value_bridge"],
        memory_policy="preserve_existing_gap_context",
        must_answer_direct_question=True,
        must_not_do=["sound internal", "transfer-or-escalate", "erase confirmed gap"],
    ),
    "regulated_claim_question": _move(
        "regulated_claim_question",
        description="Buyer asks for a claim that requires verified facts, licensed advice, policy review, exact quote, guarantee, or regulated answer.",
        examples=["can you guarantee that?", "am I covered?", "what exact price?"],
        expected_response_shape_id="regulated_claim_boundary_no_advice",
        allowed_stages=["scope_limit", "diagnostic", "value_bridge"],
        default_call_control_allowed=["continue-call", "transfer-or-escalate"],
        memory_policy="preserve_context_apply_regulated_boundary",
        must_answer_direct_question=True,
        must_not_do=["give regulated advice", "invent guarantee", "invent exact quote"],
    ),
    "why_are_you_asking": _move(
        "why_are_you_asking",
        description="Buyer challenges the purpose of the question or asks why the information is needed.",
        examples=["why are you asking?", "why do you need this?", "why ask that?"],
        expected_response_shape_id="explain_why_asking_preserve_context",
        allowed_stages=["diagnostic", "value_bridge", "scope_limit"],
        memory_policy="preserve_existing_gap_context",
        must_answer_direct_question=True,
        must_not_do=["repeat full diagnostic menu", "ignore purpose challenge"],
    ),
    "contradiction_challenge": _move(
        "contradiction_challenge",
        description="Buyer points out the caller's role or prior wording seems contradictory.",
        examples=["if you are not the right person why ask?", "why did you say you could ask?"],
        expected_response_shape_id="contradiction_repair_clarify_role",
        allowed_stages=["diagnostic", "scope_limit", "handoff_right_person"],
        memory_policy="preserve_existing_gap_context",
        must_answer_direct_question=True,
        must_not_do=["repeat confusing boundary", "be defensive", "drop confirmed gap"],
    ),
    "already_answered_challenge": _move(
        "already_answered_challenge",
        description="Buyer says they already answered or the agent missed their prior answer.",
        examples=["I already told you", "you didn't answer me", "you already asked that"],
        expected_response_shape_id="already_answered_preserve_gap",
        allowed_stages=["diagnostic", "value_bridge", "scope_limit", "appointment_progression"],
        memory_policy="preserve_and_restate_last_relevant_answer",
        must_answer_direct_question=True,
        must_not_do=["ask same diagnostic again", "erase prior answer"],
    ),
    "confusion_not_clear": _move(
        "confusion_not_clear",
        description="Buyer does not understand the question, term, purpose, or requested next step.",
        examples=["what do you mean?", "I do not understand", "not clear"],
        expected_response_shape_id="confusion_explain_plainly",
        allowed_stages=["permission", "diagnostic", "scope_limit", "value_bridge"],
        memory_policy="do_not_change_gap_state_until_clarified",
        must_answer_direct_question=True,
        must_not_do=["push appointment while confused", "treat confusion as no-pain"],
    ),
    "repeat_or_rephrase_request": _move(
        "repeat_or_rephrase_request",
        description="Buyer explicitly asks for repetition or simpler wording.",
        examples=["repeat that", "say that again", "can you rephrase?"],
        expected_response_shape_id="confusion_explain_plainly",
        allowed_stages=["opening", "permission", "diagnostic", "value_bridge", "scope_limit"],
        memory_policy="do_not_change_gap_state_until_clarified",
        must_answer_direct_question=True,
        must_not_do=["change topic", "ask appointment"],
    ),
    "send_info_request": _move(
        "send_info_request",
        description="Buyer asks for written details, a summary, or information instead of continuing live.",
        examples=["send me details", "email it to me", "send information"],
        expected_response_shape_id="send_info_contact_capture",
        allowed_stages=["permission", "diagnostic", "value_bridge", "scope_limit", "send_info_capture"],
        memory_policy="open_send_info_state_without_sending_email",
        must_not_do=["send real email", "confirm appointment without time"],
    ),
    "callback_request": _move(
        "callback_request",
        description="Buyer requests a later call or says now is not the right time.",
        examples=["call me later", "not now", "try next week"],
        expected_response_shape_id="callback_time_capture",
        allowed_stages=["permission", "diagnostic", "value_bridge", "callback_capture"],
        memory_policy="request_or_capture_callback_time",
        must_not_do=["continue pitch after bad timing", "invent time"],
    ),
    "callback_time_provided": _move(
        "callback_time_provided",
        description="Buyer provides a usable callback or appointment time.",
        examples=["tomorrow at 3 works", "Friday morning", "next Tuesday at noon"],
        expected_response_shape_id="callback_time_capture",
        allowed_stages=["callback_capture", "appointment_progression", "send_info_capture"],
        default_call_control_allowed=["continue-call", "schedule-and-end"],
        memory_policy="capture_time_without_calendar_write",
        must_not_do=["create calendar event", "continue diagnostics after terminal confirmation"],
    ),
    "appointment_interest": _move(
        "appointment_interest",
        description="Buyer indicates a human follow-up or review would be useful but may not provide time.",
        examples=["that would be good", "yes please", "sounds useful"],
        expected_response_shape_id="acknowledge_pain_bridge_to_appointment",
        allowed_stages=["value_bridge", "appointment_progression"],
        memory_policy="request_time_if_missing",
        must_not_do=["treat as scheduled without time", "invent appointment"],
    ),
    "right_person_redirect": _move(
        "right_person_redirect",
        description="Buyer says another person, department, or role owns the topic.",
        examples=["talk to operations", "my manager handles that", "wrong person"],
        expected_response_shape_id="right_person_capture",
        allowed_stages=["permission", "diagnostic", "handoff_right_person"],
        memory_policy="capture_right_person_without_selecting_product_gap",
        must_not_do=["treat contact routing as product pain", "pressure wrong person"],
    ),
    "support_request": _move(
        "support_request",
        description="Buyer asks for account, support, order, claim, warranty, cancellation, password, or operational handling.",
        examples=["help with my account", "check my order", "handle my claim"],
        expected_response_shape_id="support_boundary",
        allowed_stages=["opening", "permission", "diagnostic", "scope_limit", "handoff_right_person"],
        memory_policy="do_not_handle_support_or_account_work",
        must_answer_direct_question=True,
        must_not_do=["provide support", "change account", "invent support outcome"],
    ),
    "stop_request": _move(
        "stop_request",
        description="Buyer explicitly asks the caller to stop, not call, or end the conversation.",
        examples=["stop calling", "remove me", "do not call again"],
        expected_response_shape_id="stop_close_politely",
        allowed_stages=["opening", "permission", "diagnostic", "value_bridge", "scope_limit", "appointment_progression"],
        default_call_control_allowed=["end-call"],
        memory_policy="preserve_terminal_stop_state",
        must_not_do=["continue selling", "ask another question"],
    ),
    "asr_garbled_or_low_confidence": _move(
        "asr_garbled_or_low_confidence",
        description="The transcript is empty, low-confidence, garbled, phonetically implausible, or incompatible with the previous question.",
        examples=["play a double be good", "yadav would be good", "repeal timings are long"],
        expected_response_shape_id="ask_repeat_for_asr_garble",
        allowed_stages=["opening", "permission", "diagnostic", "value_bridge", "scope_limit", "appointment_progression"],
        memory_policy="preserve_memory_do_not_advance_state",
        must_not_do=["infer pain", "capture appointment", "repeat diagnostic menu", "transfer-or-escalate"],
    ),
}


CONVERSATION_STAGE_POLICY: dict[str, dict[str, Any]] = {
    "opening": {
        "id": "opening",
        "purpose": "Identify the caller role and campaign purpose without diagnosing before permission.",
        "allowed_buyer_moves": ["permission_acknowledgement", "time_constrained_permission", "not_relevant", "product_detail_question", "repeat_or_rephrase_request", "support_request", "stop_request", "asr_garbled_or_low_confidence"],
        "preferred_next_actions": ["ask_permission", "clarify_purpose", "close_if_refused"],
        "unsafe_next_actions": ["diagnose_before_permission", "pressure_for_appointment", "state_unverified_claims"],
        "allowed_call_control": ["continue-call", "end-call"],
    },
    "permission": {
        "id": "permission",
        "purpose": "Determine whether the buyer has time and willingness to continue.",
        "allowed_buyer_moves": ["permission_acknowledgement", "time_constrained_permission", "callback_request", "not_relevant", "product_detail_question", "confusion_not_clear", "repeat_or_rephrase_request", "send_info_request", "right_person_redirect", "support_request", "stop_request", "asr_garbled_or_low_confidence"],
        "preferred_next_actions": ["continue_to_diagnostic", "request_callback_time", "close_if_stop"],
        "unsafe_next_actions": ["treat_permission_as_pain", "ask_appointment_without_context", "ignore_stop"],
        "allowed_call_control": ["continue-call", "schedule-and-end", "end-call"],
    },
    "diagnostic": {
        "id": "diagnostic",
        "purpose": "Ask and interpret narrow evidence about relevant gaps.",
        "allowed_buyer_moves": ["pain_confirmed", "tentative_gap_interest", "no_pain_clear", "not_relevant", "product_detail_question", "scope_limit_question", "regulated_claim_question", "why_are_you_asking", "contradiction_challenge", "already_answered_challenge", "confusion_not_clear", "repeat_or_rephrase_request", "send_info_request", "callback_request", "right_person_redirect", "support_request", "stop_request", "asr_garbled_or_low_confidence"],
        "preferred_next_actions": ["acknowledge_evidence", "ask_one_clarifier", "bridge_to_review_if_pain"],
        "unsafe_next_actions": ["repeat_full_menu_after_answer", "invent_gap", "claim_fit_without_evidence"],
        "allowed_call_control": ["continue-call", "end-call"],
    },
    "value_bridge": {
        "id": "value_bridge",
        "purpose": "Connect confirmed or tentative evidence to a safe human review next step.",
        "allowed_buyer_moves": ["pain_confirmed", "tentative_gap_interest", "no_pain_clear", "not_relevant", "product_detail_question", "scope_limit_question", "regulated_claim_question", "why_are_you_asking", "already_answered_challenge", "send_info_request", "callback_request", "appointment_interest", "right_person_redirect", "stop_request", "asr_garbled_or_low_confidence"],
        "preferred_next_actions": ["offer_review", "request_time", "offer_summary_or_stop"],
        "unsafe_next_actions": ["invent_roi", "promise_outcome", "push_after_no_pain"],
        "allowed_call_control": ["continue-call", "schedule-and-end", "end-call"],
    },
    "scope_limit": {
        "id": "scope_limit",
        "purpose": "Answer product/detail/scope limits and preserve safe boundaries.",
        "allowed_buyer_moves": ["product_detail_question", "scope_limit_question", "regulated_claim_question", "why_are_you_asking", "contradiction_challenge", "already_answered_challenge", "confusion_not_clear", "support_request", "send_info_request", "callback_request", "stop_request", "asr_garbled_or_low_confidence"],
        "preferred_next_actions": ["answer_scope", "offer_review_or_stop", "apply_regulated_boundary"],
        "unsafe_next_actions": ["invent_product_detail", "give_regulated_advice", "escalate_without_trigger"],
        "allowed_call_control": ["continue-call", "transfer-or-escalate", "end-call"],
    },
    "appointment_progression": {
        "id": "appointment_progression",
        "purpose": "Capture concrete time only after valid interest or confirmed pain.",
        "allowed_buyer_moves": ["appointment_interest", "callback_time_provided", "callback_request", "send_info_request", "already_answered_challenge", "confusion_not_clear", "not_relevant", "stop_request", "asr_garbled_or_low_confidence"],
        "preferred_next_actions": ["request_time", "confirm_time", "clarify_missing_time"],
        "unsafe_next_actions": ["confirm_without_time", "create_calendar_event", "continue_after_confirmed_terminal_time"],
        "allowed_call_control": ["continue-call", "schedule-and-end", "end-call"],
    },
    "callback_capture": {
        "id": "callback_capture",
        "purpose": "Capture or clarify callback time without real scheduling side effects.",
        "allowed_buyer_moves": ["callback_request", "callback_time_provided", "repeat_or_rephrase_request", "confusion_not_clear", "stop_request", "asr_garbled_or_low_confidence"],
        "preferred_next_actions": ["ask_missing_time", "confirm_callback_time", "close_if_stop"],
        "unsafe_next_actions": ["invent_callback_time", "create_calendar_event", "restart_diagnostic"],
        "allowed_call_control": ["continue-call", "schedule-and-end", "end-call"],
    },
    "send_info_capture": {
        "id": "send_info_capture",
        "purpose": "Capture contact path for a summary without sending email or confirming a meeting.",
        "allowed_buyer_moves": ["send_info_request", "callback_time_provided", "callback_request", "repeat_or_rephrase_request", "confusion_not_clear", "stop_request", "asr_garbled_or_low_confidence"],
        "preferred_next_actions": ["request_email_or_callback_time", "capture_contact_path", "close_if_contact_refused"],
        "unsafe_next_actions": ["send_real_email", "invent_contact", "confirm_appointment_without_time"],
        "allowed_call_control": ["continue-call", "schedule-and-end", "end-call"],
    },
    "handoff_right_person": {
        "id": "handoff_right_person",
        "purpose": "Capture the correct person, team, or contact path when the speaker is not the owner.",
        "allowed_buyer_moves": ["right_person_redirect", "support_request", "contradiction_challenge", "send_info_request", "callback_request", "callback_time_provided", "stop_request", "asr_garbled_or_low_confidence"],
        "preferred_next_actions": ["ask_right_person", "capture_contact_path", "offer_stop"],
        "unsafe_next_actions": ["pressure_wrong_person", "treat_department_as_pain", "invent_contact"],
        "allowed_call_control": ["continue-call", "schedule-and-end", "end-call"],
    },
    "stop_close": {
        "id": "stop_close",
        "purpose": "Respect refusal, no need, or explicit stop and avoid further selling.",
        "allowed_buyer_moves": ["stop_request", "not_relevant"],
        "preferred_next_actions": ["acknowledge_close", "preserve_terminal_state"],
        "unsafe_next_actions": ["continue_selling", "ask_diagnostic", "request_appointment"],
        "allowed_call_control": ["end-call"],
    },
}


UNIVERSAL_REPAIR_RULES: dict[str, dict[str, Any]] = {
    "why_are_you_asking_rule": {
        "buyer_move_id": "why_are_you_asking",
        "recognition_notes": ["buyer asks why the caller needs the answer", "purpose challenge after a diagnostic or value bridge"],
        "response_shape_id": "explain_why_asking_preserve_context",
        "memory_policy": "preserve_existing_gap_context",
        "call_control_constraints": ["continue-call only unless buyer stops"],
        "forbidden_response_patterns": ["repeat full diagnostic menu", "ignore direct purpose question"],
        "campaign_fact_slots_allowed": ["human_followup_owner", "appointment_target", "gap_label", "gap_review_focus"],
    },
    "did_not_answer_rule": {
        "buyer_move_id": "already_answered_challenge",
        "recognition_notes": ["buyer says the prior question was not answered", "buyer asks for the actual answer instead of another diagnostic"],
        "response_shape_id": "already_answered_preserve_gap",
        "memory_policy": "preserve_and_restate_last_relevant_answer",
        "call_control_constraints": ["continue-call unless buyer stops"],
        "forbidden_response_patterns": ["ask same question again", "change subject"],
        "campaign_fact_slots_allowed": ["gap_label", "gap_review_focus", "appointment_target"],
    },
    "not_right_contact_why_ask_rule": {
        "buyer_move_id": "contradiction_challenge",
        "recognition_notes": ["buyer challenges a role contradiction", "buyer asks why basic questions were asked if a specialist owns details"],
        "response_shape_id": "contradiction_repair_clarify_role",
        "memory_policy": "preserve_existing_gap_context",
        "call_control_constraints": ["continue-call only unless buyer stops"],
        "forbidden_response_patterns": ["repeat contact boundary", "defensive wording", "erase confirmed gap"],
        "campaign_fact_slots_allowed": ["human_followup_owner", "appointment_target", "gap_label", "gap_review_focus"],
    },
    "already_told_you_rule": {
        "buyer_move_id": "already_answered_challenge",
        "recognition_notes": ["buyer says they already answered", "buyer objects to repeated questioning"],
        "response_shape_id": "already_answered_preserve_gap",
        "memory_policy": "preserve_and_restate_last_relevant_answer",
        "call_control_constraints": ["continue-call or stop_close if buyer refuses"],
        "forbidden_response_patterns": ["repeat answered diagnostic", "drop stored answer"],
        "campaign_fact_slots_allowed": ["gap_label", "gap_review_focus", "appointment_target"],
    },
    "tentative_gap_rule": {
        "buyer_move_id": "tentative_gap_interest",
        "recognition_notes": ["maybe plus known gap language", "uncertain statement about a campaign gap"],
        "response_shape_id": "acknowledge_tentative_gap_offer_review_or_stop",
        "memory_policy": "store_tentative_gap_without_confirming_pain",
        "call_control_constraints": ["continue-call", "forbid transfer-or-escalate"],
        "forbidden_response_patterns": ["confirm pain from maybe", "repeat full diagnostic menu"],
        "campaign_fact_slots_allowed": ["human_followup_owner", "appointment_target", "gap_label", "gap_review_focus"],
    },
    "time_pressure_rule": {
        "buyer_move_id": "time_constrained_permission",
        "recognition_notes": ["make it quick", "short minute", "limited time permission"],
        "response_shape_id": "acknowledge_time_constraint_then_one_question",
        "memory_policy": "do_not_mark_pain_or_appointment",
        "call_control_constraints": ["continue-call", "no appointment before pain"],
        "forbidden_response_patterns": ["long menu", "multi-step explanation"],
        "campaign_fact_slots_allowed": ["gap_label", "core_diagnostic_gaps"],
    },
    "clean_confirmation_rule": {
        "buyer_move_id": "appointment_interest",
        "recognition_notes": ["clean acceptance after explanation or review offer", "positive acknowledgement compatible with previous question"],
        "response_shape_id": "acknowledge_pain_bridge_to_appointment",
        "memory_policy": "request_time_if_missing",
        "call_control_constraints": ["continue-call until usable time is captured"],
        "forbidden_response_patterns": ["treat as scheduled without time", "restart diagnostics"],
        "campaign_fact_slots_allowed": ["human_followup_owner", "appointment_target", "gap_label", "gap_review_focus"],
    },
    "asr_garbled_phrase_rule": {
        "buyer_move_id": "asr_garbled_or_low_confidence",
        "recognition_notes": ["phonetic nonsense", "previous question mismatch", "accepted transcript still implausible"],
        "response_shape_id": "ask_repeat_for_asr_garble",
        "memory_policy": "preserve_memory_do_not_advance_state",
        "call_control_constraints": ["continue-call", "forbid transfer-or-escalate"],
        "forbidden_response_patterns": ["infer pain", "capture appointment", "repeat diagnostic menu"],
        "campaign_fact_slots_allowed": ["language"],
    },
    "product_detail_question_rule": {
        "buyer_move_id": "product_detail_question",
        "recognition_notes": ["buyer asks what the offer does or includes", "buyer asks for details beyond the call purpose"],
        "response_shape_id": "answer_product_scope_limit_continue",
        "memory_policy": "preserve_existing_gap_context",
        "call_control_constraints": ["continue-call", "forbid transfer-or-escalate"],
        "forbidden_response_patterns": ["invent product details", "sound internal", "repeat diagnostic menu"],
        "campaign_fact_slots_allowed": ["product_or_offer_name", "human_followup_owner", "appointment_target", "allowed_claims", "blocked_claims", "gap_review_focus"],
    },
    "regulated_claim_question_rule": {
        "buyer_move_id": "regulated_claim_question",
        "recognition_notes": ["question asks for guarantee, exact price, coverage, refund, compliance, security, or regulated advice"],
        "response_shape_id": "regulated_claim_boundary_no_advice",
        "memory_policy": "preserve_context_apply_regulated_boundary",
        "call_control_constraints": ["continue-call by default", "transfer-or-escalate only for true regulated escalation requirement"],
        "forbidden_response_patterns": ["make claim", "invent guarantee", "quote exact price"],
        "campaign_fact_slots_allowed": ["human_followup_owner", "blocked_claims", "regulated_cautions", "gap_review_focus"],
    },
    "support_request_rule": {
        "buyer_move_id": "support_request",
        "recognition_notes": ["buyer requests account, order, support, claim, warranty, cancellation, password, or operational help"],
        "response_shape_id": "support_boundary",
        "memory_policy": "do_not_handle_support_or_account_work",
        "call_control_constraints": ["continue-call or end-call", "do not transfer unless configured"],
        "forbidden_response_patterns": ["provide support", "change account", "invent support outcome"],
        "campaign_fact_slots_allowed": ["human_followup_owner", "blocked_claims", "regulated_cautions", "appointment_target"],
    },
    "stop_request_rule": {
        "buyer_move_id": "stop_request",
        "recognition_notes": ["buyer asks to stop, remove, not call, or end"],
        "response_shape_id": "stop_close_politely",
        "memory_policy": "preserve_terminal_stop_state",
        "call_control_constraints": ["end-call"],
        "forbidden_response_patterns": ["continue selling", "ask diagnostic", "request appointment"],
        "campaign_fact_slots_allowed": ["language"],
    },
}


ASR_REPAIR_BOUNDARY: dict[str, Any] = {
    "id": "universal_asr_repair_boundary",
    "location": "before buyer move classification and before appointment or pain routing",
    "cases": {
        "explicit_low_confidence": {
            "id": "explicit_low_confidence",
            "description": "ASR engine reports confidence below the accepted threshold.",
            "examples": ["low confidence numeric score"],
            "policy": "ask_repeat_for_asr_garble",
        },
        "empty_or_fragment": {
            "id": "empty_or_fragment",
            "description": "Transcript is empty or ends as a fragment.",
            "examples": ["", "about the", "for"],
            "policy": "ask_repeat_for_asr_garble",
        },
        "phonetic_nonsense": {
            "id": "phonetic_nonsense",
            "description": "Recognized words form an implausible phrase for the previous sales question.",
            "examples": ["play a double be good", "yadav would be good"],
            "policy": "ask_repeat_for_asr_garble",
        },
        "previous_question_mismatch": {
            "id": "previous_question_mismatch",
            "description": "The transcript does not answer the immediately previous question and is too risky to infer.",
            "examples": ["unrelated phrase after appointment-time request"],
            "policy": "ask_repeat_for_asr_garble",
        },
        "domain_near_miss": {
            "id": "domain_near_miss",
            "description": "Transcript contains a likely phonetic near-miss around a domain term.",
            "examples": ["repeal timings are long"],
            "policy": "ask_repeat_for_asr_garble_or_confirm_term",
        },
        "high_risk_appointment_time": {
            "id": "high_risk_appointment_time",
            "description": "Time, date, or scheduling phrase is ambiguous or likely misheard.",
            "examples": ["garbled phrase after time request"],
            "policy": "ask_repeat_for_asr_garble",
        },
        "high_risk_email_or_contact": {
            "id": "high_risk_email_or_contact",
            "description": "Email, phone, name, or contact routing text is likely misheard.",
            "examples": ["unclear contact details"],
            "policy": "ask_repeat_for_asr_garble",
        },
        "high_risk_regulated_claim": {
            "id": "high_risk_regulated_claim",
            "description": "Potential regulated claim terms are unclear enough that the agent must not answer substantively.",
            "examples": ["unclear coverage, price, refund, warranty, or security phrase"],
            "policy": "ask_repeat_for_asr_garble",
        },
    },
    "expected_policy": {
        "required_behavior": ["ask for repeat/rephrase", "preserve existing confirmed/cleared memory"],
        "forbidden_behavior": ["infer pain", "capture appointment", "repeat diagnostic menu", "call providers"],
        "side_effect_flags": dict(SIDE_EFFECT_FLAGS),
    },
}


CALL_CONTROL_POLICY: dict[str, dict[str, Any]] = {
    "continue-call": {
        "id": "continue-call",
        "description": "Continue the current conversation safely.",
        "allowed_when": ["non-terminal clarification", "diagnostic", "scope answer", "repair", "time clarification"],
        "forbidden_when": ["explicit stop already accepted"],
    },
    "schedule-and-end": {
        "id": "schedule-and-end",
        "description": "Close after a valid callback or appointment time has been captured locally.",
        "allowed_when": ["valid callback time", "valid appointment time"],
        "forbidden_when": ["missing time", "garbled time", "no buyer consent"],
    },
    "end-call": {
        "id": "end-call",
        "description": "End after explicit stop, refusal, or safe no-fit close.",
        "allowed_when": ["stop/refusal", "terminal no-fit", "confirmed callback/appointment close"],
        "forbidden_when": ["buyer asked a direct question still unanswered"],
    },
    "transfer-or-escalate": {
        "id": "transfer-or-escalate",
        "description": "Escalation boundary for explicit transfer request, configured escalation trigger, or true regulated escalation requirement.",
        "allowed_only_when": ["explicit_transfer_request", "configured_escalation_trigger", "true_regulated_escalation_requirement"],
        "forbidden_when": ["ordinary uncertainty", "product detail limitation", "ASR garble"],
    },
    "ordinary_uncertainty": {
        "id": "ordinary_uncertainty",
        "allowed_call_control": ["continue-call"],
        "forbidden_call_control": ["transfer-or-escalate", "schedule-and-end"],
        "reason": "Uncertainty needs clarification, not escalation.",
    },
    "product_detail_limitation": {
        "id": "product_detail_limitation",
        "allowed_call_control": ["continue-call", "end-call"],
        "forbidden_call_control": ["transfer-or-escalate"],
        "reason": "Scope limitation should be answered plainly unless the buyer asks for transfer or the campaign has a true escalation trigger.",
    },
    "asr_garble": {
        "id": "asr_garble",
        "allowed_call_control": ["continue-call"],
        "forbidden_call_control": ["transfer-or-escalate", "schedule-and-end", "end-call"],
        "reason": "Garbled transcript needs a repeat request and must not advance state.",
    },
    "valid_callback_or_appointment_time": {
        "id": "valid_callback_or_appointment_time",
        "allowed_call_control": ["continue-call", "schedule-and-end"],
        "forbidden_call_control": ["transfer-or-escalate"],
        "reason": "A usable time can be confirmed locally without provider, email, calendar, or CRM side effects.",
    },
    "stop_or_refusal": {
        "id": "stop_or_refusal",
        "allowed_call_control": ["end-call"],
        "forbidden_call_control": ["continue-call", "schedule-and-end", "transfer-or-escalate"],
        "reason": "Explicit stop or refusal must close without further selling.",
    },
}


CAMPAIGN_FACT_SLOTS: dict[str, dict[str, Any]] = {
    slot_id: {
        "id": slot_id,
        "description": f"Campaign/adapted playbook fact slot: {slot_id}.",
        "source": "campaign_config_or_campaign_playbook_adapter",
        "runtime_strategy_owner": "universal_conversation_policy",
    }
    for slot_id in BASE_FACT_SLOTS
}

FORBIDDEN_CAMPAIGN_RESPONSIBILITIES = [
    "generic acknowledgement strategy",
    "why-are-you-asking repair strategy",
    "product-detail limitation response shape",
    "loop repair strategy",
    "ASR-garble handling",
    "appointment progression policy",
    "transfer/escalate policy except explicit configured escalation triggers",
]

FORBIDDEN_CUSTOMER_FACING_PATTERNS = [
    {
        "id": "internal_policy_wording",
        "phrases": ["I should", "approved qualified reviewer path"],
        "reason": "Customer-facing wording must not expose internal policy or reviewer-route terms.",
    },
    {
        "id": "late_diagnostic_menu_reopen",
        "phrases": ["I am asking whether after concrete answer", "repeated full diagnostic menu after direct answer"],
        "reason": "After a concrete answer, the response must acknowledge and progress or clarify, not reset the menu.",
    },
    {
        "id": "conditional_relevance_after_pain",
        "phrases": ["if X are actually relevant after concrete pain"],
        "reason": "Concrete pain should not be undermined as merely hypothetical.",
    },
    {
        "id": "contact_boundary_misuse",
        "phrases": ["not the right contact unless true support/right-person boundary"],
        "reason": "This wording creates contradiction when the agent can still ask basic fit questions.",
    },
    {
        "id": "default_demo_terms_in_generic_fixtures",
        "phrases": ["default demo brand terms", "default company names", "default plan tier names", "default plan prices"],
        "reason": "Generic fixtures must not leak default-demo brand, company, tier, or price copy.",
    },
    {
        "id": "invented_claims",
        "phrases": ["invented guarantee", "invented coverage", "invented refund", "invented exact price", "invented security", "invented ROI", "invented revenue"],
        "reason": "Claims must stay inside allowed claims and regulated cautions.",
    },
]

VALIDATOR_MATRIX = {
    "fixtures": [
        "routesignal_live_demo",
        "synthetic-insurance-review",
        "synthetic-b2b-saas-operations",
        "synthetic-automotive-service-review",
        "synthetic-home-services-estimate",
    ],
    "buyer_move_test_cases": [
        "make it quick",
        "maybe X",
        "X is usually a problem",
        "what does your product do?",
        "so you can't give me details?",
        "why are you asking?",
        "you didn't answer my question",
        "if you're not the right person, why ask?",
        "I already told you",
        "yeah that would be good",
        "play a double be good",
        "yadav would be good",
        "repeal timings are long",
        "send me details",
        "tomorrow at 3 works",
        "no thanks",
        "stop calling",
    ],
    "assertions": [
        "buyer meaning acknowledged",
        "direct question answered when asked",
        "no repeated full menu after answer",
        "no internal policy wording",
        "no transfer/escalate unless required",
        "no campaign leakage",
        "appointment ask only when appropriate",
        "safe claim boundaries preserved",
        "side-effect flags false",
    ],
}


def buyer_move(move_id: str) -> dict[str, Any]:
    return deepcopy(BUYER_MOVE_TAXONOMY.get(str(move_id)) or {})


def conversation_stage(stage_id: str) -> dict[str, Any]:
    return deepcopy(CONVERSATION_STAGE_POLICY.get(str(stage_id)) or {})


def response_shape(shape_id: str) -> dict[str, Any]:
    return deepcopy(RESPONSE_SHAPE_LIBRARY.get(str(shape_id)) or {})


def repair_rule(rule_id: str) -> dict[str, Any]:
    return deepcopy(UNIVERSAL_REPAIR_RULES.get(str(rule_id)) or {})


def call_control_rule(call_control_id: str) -> dict[str, Any]:
    key = str(call_control_id)
    if key == "transfer_or_escalate":
        key = "transfer-or-escalate"
    return deepcopy(CALL_CONTROL_POLICY.get(key) or {})


def asr_repair_case(case_id: str) -> dict[str, Any]:
    return deepcopy((ASR_REPAIR_BOUNDARY.get("cases") or {}).get(str(case_id)) or {})


def campaign_fact_slot(slot_id: str) -> dict[str, Any]:
    return deepcopy(CAMPAIGN_FACT_SLOTS.get(str(slot_id)) or {})


def forbidden_customer_patterns() -> list[dict[str, Any]]:
    return deepcopy(FORBIDDEN_CUSTOMER_FACING_PATTERNS)


def validator_matrix() -> dict[str, Any]:
    return deepcopy(VALIDATOR_MATRIX)


def all_buyer_move_ids() -> list[str]:
    return list(BUYER_MOVE_TAXONOMY)


def all_response_shape_ids() -> list[str]:
    return list(RESPONSE_SHAPE_LIBRARY)


def all_conversation_stage_ids() -> list[str]:
    return list(CONVERSATION_STAGE_POLICY)


def _missing(required: list[str], actual: list[str]) -> list[str]:
    return [item for item in required if item not in actual]


def validate_universal_sales_conversation_knowledge() -> dict[str, Any]:
    failures: list[str] = []
    response_shape_ids = all_response_shape_ids()
    buyer_move_ids = all_buyer_move_ids()

    for move_id, move in BUYER_MOVE_TAXONOMY.items():
        if move.get("id") != move_id:
            failures.append(f"{move_id}: id mismatch")
        if move.get("expected_response_shape_id") not in response_shape_ids:
            failures.append(f"{move_id}: unknown response shape")
        if not move.get("examples"):
            failures.append(f"{move_id}: examples required")
        if not move.get("must_not_do"):
            failures.append(f"{move_id}: must_not_do required")

    for stage_id, stage in CONVERSATION_STAGE_POLICY.items():
        if stage.get("id") != stage_id:
            failures.append(f"{stage_id}: id mismatch")
        unknown_moves = [move for move in stage.get("allowed_buyer_moves", []) if move not in buyer_move_ids]
        if unknown_moves:
            failures.append(f"{stage_id}: unknown allowed buyer moves {unknown_moves}")
        if not stage.get("preferred_next_actions") or not stage.get("unsafe_next_actions"):
            failures.append(f"{stage_id}: next-action policy incomplete")

    for shape_id, shape in RESPONSE_SHAPE_LIBRARY.items():
        if shape.get("id") != shape_id:
            failures.append(f"{shape_id}: id mismatch")
        missing_steps = _missing(REQUIRED_RESPONSE_STEPS, list(shape.get("required_steps") or []))
        if missing_steps:
            failures.append(f"{shape_id}: missing required steps {missing_steps}")
        if shape.get("appointment_pressure_level") not in {"none", "low", "medium", "direct"}:
            failures.append(f"{shape_id}: invalid appointment pressure")
        if not shape.get("example_outline"):
            failures.append(f"{shape_id}: example outline required")

    for rule_id, rule in UNIVERSAL_REPAIR_RULES.items():
        if rule.get("buyer_move_id") not in buyer_move_ids:
            failures.append(f"{rule_id}: unknown buyer move")
        if rule.get("response_shape_id") not in response_shape_ids:
            failures.append(f"{rule_id}: unknown response shape")

    asr_policy = ASR_REPAIR_BOUNDARY.get("expected_policy") or {}
    if "ask for repeat/rephrase" not in asr_policy.get("required_behavior", []):
        failures.append("asr boundary must ask for repeat/rephrase")
    for forbidden in ["infer pain", "capture appointment", "repeat diagnostic menu"]:
        if forbidden not in asr_policy.get("forbidden_behavior", []):
            failures.append(f"asr boundary must forbid {forbidden}")

    return {
        "knowledge_id": KNOWLEDGE_ID,
        "schema_version": SCHEMA_VERSION,
        "status": "pass" if not failures else "fail",
        "failures": failures,
        "counts": {
            "buyer_moves": len(BUYER_MOVE_TAXONOMY),
            "conversation_stages": len(CONVERSATION_STAGE_POLICY),
            "response_shapes": len(RESPONSE_SHAPE_LIBRARY),
            "repair_rules": len(UNIVERSAL_REPAIR_RULES),
            "campaign_fact_slots": len(CAMPAIGN_FACT_SLOTS),
            "asr_cases": len(ASR_REPAIR_BOUNDARY.get("cases") or {}),
        },
        "declarative_only": True,
        "no_dialogue_manager_import": True,
        "no_contextual_buyer_semantics_import": True,
        "no_live_voice_session_policy_import": True,
        "no_final_runtime_response_generation": True,
        **dict(SIDE_EFFECT_FLAGS),
    }
