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


OBJECTION_BUYER_MOVES = [
    "price_or_budget_objection",
    "timing_objection",
    "no_authority_or_needs_approval",
    "already_has_provider",
    "competitor_comparison",
    "trust_or_skepticism",
    "risk_or_liability_concern",
    "no_clear_need",
    "too_busy_now",
    "send_info_first",
    "wants_proof_or_case_study",
    "procurement_or_legal_review",
    "security_or_privacy_review",
    "contract_or_terms_question",
]

IDENTITY_TRUST_PRIVACY_BUYER_MOVES = [
    "who_are_you",
    "how_did_you_get_my_number",
    "are_you_ai_or_robot",
    "is_this_recorded",
    "privacy_data_use_question",
    "permission_to_continue_denied",
    "language_mismatch",
    "abusive_or_hostile_buyer",
    "sensitive_personal_data_disclosure",
]

APPOINTMENT_NEGOTIATION_BUYER_MOVES = [
    "appointment_time_vague",
    "appointment_time_conflict",
    "buyer_requests_available_times",
    "buyer_wants_email_before_booking",
    "buyer_defers_to_later",
    "buyer_accepts_callback_without_time",
    "buyer_changes_time",
    "buyer_confirms_time",
    "buyer_declines_after_interest",
]

VALUE_DIFFERENTIATION_BUYER_MOVES = [
    "why_should_i_care",
    "what_makes_you_different",
    "what_problem_do_you_solve",
    "what_result_can_i_expect",
    "is_this_worth_my_time",
    "who_is_this_for",
    "does_this_apply_to_us",
]

SOCIAL_CONVERSATION_BUYER_MOVES = [
    "small_talk",
    "humor_or_sarcasm",
    "silence_or_backchannel",
    "interruption_or_barge_in",
    "buyer_talks_over_agent",
    "repeat_last_answer",
    "slow_down_or_speak_faster",
    "pronunciation_or_name_correction",
    "emotional_frustration",
]


RESPONSE_SHAPE_LIBRARY.update(
    {
        "answer_identity_then_permission": _shape(
            "answer_identity_then_permission",
            allowed_fact_slots=["caller_identity", "client_name", "product_or_offer_name", "objective", "language"],
            forbidden_patterns=DEFAULT_FORBIDDEN_PATTERNS + ["invent identity", "claim human when automated"],
            appointment_pressure_level="none",
            example_outline=[
                "answer who is calling using caller identity and allowed campaign facts",
                "state the limited purpose of the call",
                "ask permission to continue or offer to stop",
            ],
        ),
        "answer_data_source_boundary": _shape(
            "answer_data_source_boundary",
            allowed_fact_slots=["caller_identity", "client_name", "allowed_claims", "blocked_claims", "language"],
            forbidden_patterns=DEFAULT_FORBIDDEN_PATTERNS + ["invent lead source", "name private source without evidence"],
            appointment_pressure_level="none",
            example_outline=[
                "answer that the agent cannot invent the data source",
                "state only configured caller identity and allowed facts",
                "offer to continue or stop",
            ],
        ),
        "ai_disclosure_then_continue_or_stop": _shape(
            "ai_disclosure_then_continue_or_stop",
            allowed_fact_slots=["caller_identity", "client_name", "language"],
            forbidden_patterns=DEFAULT_FORBIDDEN_PATTERNS + ["pretend to be human", "as an AI language model"],
            appointment_pressure_level="none",
            example_outline=[
                "answer the automation question directly",
                "do not claim to be human",
                "ask whether the buyer wants to continue or stop",
            ],
        ),
        "privacy_boundary_then_continue_or_stop": _shape(
            "privacy_boundary_then_continue_or_stop",
            allowed_fact_slots=["caller_identity", "client_name", "allowed_claims", "blocked_claims", "language"],
            forbidden_patterns=DEFAULT_FORBIDDEN_PATTERNS + ["request sensitive personal data", "invent privacy policy"],
            appointment_pressure_level="none",
            example_outline=[
                "acknowledge the privacy or recording question",
                "answer only with configured facts and safe limitations",
                "offer to continue or stop without collecting sensitive data",
            ],
        ),
        "objection_acknowledge_answer_bridge": _shape(
            "objection_acknowledge_answer_bridge",
            allowed_fact_slots=["allowed_claims", "blocked_claims", "gap_label", "gap_review_focus", "appointment_target", "human_followup_owner"],
            forbidden_patterns=DEFAULT_FORBIDDEN_PATTERNS + ["argue with buyer", "invent proof", "push appointment after no"],
            appointment_pressure_level="low",
            example_outline=[
                "acknowledge the objection without arguing",
                "answer with allowed facts or a safe boundary",
                "bridge to one relevant diagnostic, review, or stop option",
            ],
        ),
        "competitor_acknowledge_no_bashing": _shape(
            "competitor_acknowledge_no_bashing",
            allowed_fact_slots=["allowed_claims", "blocked_claims", "gap_label", "gap_review_focus"],
            forbidden_patterns=DEFAULT_FORBIDDEN_PATTERNS + ["bash competitor", "invent comparison", "claim superiority without allowed facts"],
            appointment_pressure_level="low",
            example_outline=[
                "acknowledge existing or compared provider",
                "avoid negative competitor claims",
                "ask whether one allowed fit area is still worth reviewing",
            ],
        ),
        "price_boundary_without_quote": _shape(
            "price_boundary_without_quote",
            allowed_fact_slots=["allowed_claims", "blocked_claims", "appointment_target", "human_followup_owner", "gap_review_focus"],
            forbidden_patterns=DEFAULT_FORBIDDEN_PATTERNS + ["exact quote", "invent discount", "guarantee savings"],
            appointment_pressure_level="low",
            example_outline=[
                "acknowledge price or budget concern",
                "state that exact pricing is not handled on this call unless explicitly allowed",
                "offer the appropriate human review or stop",
            ],
        ),
        "authority_map_to_right_person": _shape(
            "authority_map_to_right_person",
            allowed_fact_slots=["human_followup_owner", "appointment_target", "gap_label", "gap_review_focus"],
            forbidden_patterns=DEFAULT_FORBIDDEN_PATTERNS + ["pressure non-owner", "treat approval as pain"],
            appointment_pressure_level="none",
            example_outline=[
                "acknowledge the buyer is not the final authority",
                "ask for the right person or a safe follow-up path",
                "offer to stop if they cannot help",
            ],
        ),
        "timing_deferral_callback_capture": _shape(
            "timing_deferral_callback_capture",
            allowed_fact_slots=["appointment_target", "human_followup_owner", "language"],
            forbidden_patterns=DEFAULT_FORBIDDEN_PATTERNS + ["continue pitch after timing refusal", "invent callback time"],
            appointment_pressure_level="low",
            example_outline=[
                "acknowledge timing is not good now",
                "ask for a broad callback window or offer to stop",
                "do not create a real calendar event",
            ],
        ),
        "value_question_answer_with_allowed_facts": _shape(
            "value_question_answer_with_allowed_facts",
            allowed_fact_slots=["product_or_offer_name", "allowed_claims", "blocked_claims", "gap_label", "gap_review_focus", "gap_value_bridge"],
            forbidden_patterns=DEFAULT_FORBIDDEN_PATTERNS + ["invent ROI", "invent guarantee", "invent compliance proof"],
            appointment_pressure_level="low",
            example_outline=[
                "answer the value question using allowed facts only",
                "tie the answer to one relevant problem area",
                "ask one diagnostic or offer a review only if appropriate",
            ],
        ),
        "proof_request_offer_summary_or_human_review": _shape(
            "proof_request_offer_summary_or_human_review",
            allowed_fact_slots=["allowed_claims", "blocked_claims", "human_followup_owner", "appointment_target", "gap_review_focus"],
            forbidden_patterns=DEFAULT_FORBIDDEN_PATTERNS + ["invent case study", "send real email", "claim proof unavailable from config"],
            appointment_pressure_level="low",
            example_outline=[
                "acknowledge request for proof or written material",
                "offer only an allowed summary or human review path",
                "capture safe contact or callback preference without sending email",
            ],
        ),
        "appointment_time_clarification": _shape(
            "appointment_time_clarification",
            allowed_fact_slots=["appointment_target", "human_followup_owner", "language"],
            forbidden_patterns=DEFAULT_FORBIDDEN_PATTERNS + ["treat vague time as scheduled", "create calendar event"],
            appointment_pressure_level="direct",
            example_outline=[
                "acknowledge the vague or conflicting time",
                "ask for the missing date or time component",
                "do not confirm scheduling until usable",
            ],
        ),
        "appointment_time_confirmation": _shape(
            "appointment_time_confirmation",
            allowed_fact_slots=["appointment_target", "human_followup_owner", "language"],
            allowed_call_control=["continue-call", "schedule-and-end"],
            appointment_pressure_level="direct",
            example_outline=[
                "confirm the usable callback or review time locally",
                "state that the appropriate owner will follow up",
                "do not claim real calendar, email, or CRM write",
            ],
        ),
        "language_mismatch_repair": _shape(
            "language_mismatch_repair",
            allowed_fact_slots=["language", "caller_identity"],
            forbidden_patterns=DEFAULT_FORBIDDEN_PATTERNS + ["continue in wrong language", "pressure confused buyer"],
            appointment_pressure_level="none",
            example_outline=[
                "acknowledge language mismatch",
                "offer slower wording, a repeat, or to stop",
                "do not infer pain or appointment interest",
            ],
        ),
        "hostile_buyer_deescalation": _shape(
            "hostile_buyer_deescalation",
            allowed_fact_slots=["language"],
            forbidden_patterns=DEFAULT_FORBIDDEN_PATTERNS + ["argue with buyer", "mirror hostility", "continue after stop"],
            allowed_call_control=["continue-call", "end-call"],
            appointment_pressure_level="none",
            example_outline=[
                "acknowledge frustration briefly",
                "lower intensity and offer to stop",
                "continue only if buyer permits",
            ],
        ),
        "speech_rate_adjustment": _shape(
            "speech_rate_adjustment",
            allowed_fact_slots=["language", "caller_identity"],
            forbidden_patterns=DEFAULT_FORBIDDEN_PATTERNS + ["blame buyer", "ignore correction"],
            appointment_pressure_level="none",
            example_outline=[
                "acknowledge the requested speaking or pronunciation adjustment",
                "apply the adjustment in the next response",
                "return to one clear next action",
            ],
        ),
        "repeat_last_answer_shorter": _shape(
            "repeat_last_answer_shorter",
            allowed_fact_slots=["allowed_claims", "blocked_claims", "gap_label", "gap_review_focus", "appointment_target"],
            forbidden_patterns=DEFAULT_FORBIDDEN_PATTERNS + ["change answer", "add new claims", "repeat long diagnostic menu"],
            appointment_pressure_level="none",
            example_outline=[
                "acknowledge repeat request",
                "repeat the last answer in shorter plain wording",
                "ask one next question only if needed",
            ],
        ),
        "social_smalltalk_bridge_back": _shape(
            "social_smalltalk_bridge_back",
            allowed_fact_slots=["caller_identity", "language"],
            forbidden_patterns=DEFAULT_FORBIDDEN_PATTERNS + ["treat backchannel as pain", "linger on small talk"],
            appointment_pressure_level="none",
            example_outline=[
                "acknowledge small talk or backchannel lightly",
                "do not infer a sales signal",
                "return to the current question or offer to stop",
            ],
        ),
        "clarify_missing_time": _shape(
            "clarify_missing_time",
            allowed_fact_slots=["appointment_target", "human_followup_owner", "language"],
            forbidden_patterns=DEFAULT_FORBIDDEN_PATTERNS + ["confirm without time", "invent time"],
            appointment_pressure_level="direct",
            example_outline=[
                "acknowledge callback interest",
                "ask for the missing day, time, or window",
                "do not schedule until clear",
            ],
        ),
        "offer_callback_window_without_calendar_claim": _shape(
            "offer_callback_window_without_calendar_claim",
            allowed_fact_slots=["appointment_target", "human_followup_owner", "language"],
            forbidden_patterns=DEFAULT_FORBIDDEN_PATTERNS + ["claim calendar availability", "create calendar event"],
            appointment_pressure_level="medium",
            example_outline=[
                "acknowledge request for available times",
                "offer broad callback windows without claiming calendar access",
                "ask buyer to choose or suggest a time",
            ],
        ),
        "confirm_time_without_calendar_write": _shape(
            "confirm_time_without_calendar_write",
            allowed_fact_slots=["appointment_target", "human_followup_owner", "language"],
            allowed_call_control=["continue-call", "schedule-and-end"],
            forbidden_patterns=DEFAULT_FORBIDDEN_PATTERNS + ["claim real calendar write", "claim email sent", "claim CRM write"],
            appointment_pressure_level="direct",
            example_outline=[
                "confirm the time locally",
                "name the allowed follow-up owner or target",
                "avoid claiming any external write occurred",
            ],
        ),
        "defer_politely_preserve_interest": _shape(
            "defer_politely_preserve_interest",
            allowed_fact_slots=["appointment_target", "human_followup_owner", "gap_label", "gap_review_focus"],
            forbidden_patterns=DEFAULT_FORBIDDEN_PATTERNS + ["pressure after deferral", "erase interest"],
            appointment_pressure_level="low",
            example_outline=[
                "acknowledge the buyer wants to defer",
                "preserve the stated area of interest",
                "ask for a later window or close politely",
            ],
        ),
        "close_after_decline": _shape(
            "close_after_decline",
            allowed_fact_slots=["language"],
            forbidden_patterns=DEFAULT_FORBIDDEN_PATTERNS + ["push appointment after explicit no", "restart diagnostics"],
            allowed_call_control=["end-call"],
            appointment_pressure_level="none",
            example_outline=[
                "acknowledge the decline",
                "do not ask another sales question",
                "close politely",
            ],
        ),
    }
)


EXPANDED_BUYER_MOVE_SPECS = [
    ("price_or_budget_objection", "Buyer objects to price, budget, affordability, or asks about cost.", ["how much does it cost?", "too expensive", "we do not have budget"], "price_boundary_without_quote", ["diagnostic", "value_bridge", "scope_limit"], "preserve_context_answer_price_boundary", True, ["quote exact price", "invent discount", "guarantee savings"]),
    ("timing_objection", "Buyer says the timing is bad or the initiative is not timely.", ["bad timing", "not this quarter", "call later"], "timing_deferral_callback_capture", ["permission", "diagnostic", "value_bridge", "callback_capture"], "preserve_interest_request_callback_window", False, ["continue pitch after bad timing", "erase interest"]),
    ("no_authority_or_needs_approval", "Buyer says they need approval or are not the decision owner.", ["I need to ask my manager", "not my decision", "legal has to approve"], "authority_map_to_right_person", ["permission", "diagnostic", "handoff_right_person", "value_bridge"], "capture_authority_boundary_without_pressure", False, ["pressure non-owner", "treat as pain"]),
    ("already_has_provider", "Buyer says an existing provider, vendor, advisor, or solution is already in place.", ["we already have a provider", "we use someone else", "that is covered"], "competitor_acknowledge_no_bashing", ["permission", "diagnostic", "value_bridge"], "preserve_context_do_not_create_fake_gap", False, ["bash provider", "invent competitor weakness"]),
    ("competitor_comparison", "Buyer asks for comparison against another provider or option.", ["are you better than them?", "how do you compare?", "why switch?"], "competitor_acknowledge_no_bashing", ["diagnostic", "value_bridge", "scope_limit"], "answer_with_allowed_facts_only", True, ["bash competitor", "invent superiority"]),
    ("trust_or_skepticism", "Buyer questions legitimacy, credibility, or whether the call is worth trusting.", ["is this legit?", "why should I trust this?", "sounds like a scam"], "objection_acknowledge_answer_bridge", ["opening", "permission", "diagnostic", "value_bridge"], "answer_trust_concern_without_invention", True, ["argue with buyer", "invent credentials"]),
    ("risk_or_liability_concern", "Buyer raises risk, liability, compliance, warranty, claim, or responsibility concerns.", ["what if this goes wrong?", "who is liable?", "is there risk?"], "regulated_claim_boundary_no_advice", ["diagnostic", "scope_limit", "value_bridge"], "preserve_context_apply_claim_boundary", True, ["give legal advice", "invent liability promise"]),
    ("no_clear_need", "Buyer says they do not see a problem or clear reason to continue.", ["I do not need this", "not seeing the need", "nothing to fix"], "objection_acknowledge_answer_bridge", ["permission", "diagnostic", "value_bridge"], "respect_no_need_allow_one_relevance_check", False, ["push appointment after no", "repeat menu"]),
    ("too_busy_now", "Buyer is willing or neutral but too busy to continue right now.", ["too busy now", "in a meeting", "not a good time"], "timing_deferral_callback_capture", ["opening", "permission", "diagnostic"], "request_callback_or_close", False, ["continue pitch", "invent time"]),
    ("send_info_first", "Buyer asks to receive information before deciding whether to talk or book.", ["send info first", "email me first", "send details before booking"], "send_info_contact_capture", ["permission", "diagnostic", "value_bridge", "send_info_capture"], "open_send_info_state_without_sending_email", False, ["send real email", "confirm booked"]),
    ("wants_proof_or_case_study", "Buyer asks for proof, references, examples, or case-study evidence.", ["send me proof", "any case studies?", "show results"], "proof_request_offer_summary_or_human_review", ["diagnostic", "value_bridge", "scope_limit", "send_info_capture"], "answer_proof_request_with_allowed_facts_only", True, ["invent proof", "invent customer story"]),
    ("procurement_or_legal_review", "Buyer says procurement, legal, or formal review is required.", ["procurement has to review", "legal needs to see it", "send terms"], "authority_map_to_right_person", ["diagnostic", "value_bridge", "handoff_right_person", "send_info_capture"], "capture_review_owner_or_stop", False, ["act as legal", "claim terms approval"]),
    ("security_or_privacy_review", "Buyer asks about security, privacy review, or data handling obligations.", ["security needs to approve", "what about privacy?", "do you process data?"], "privacy_boundary_then_continue_or_stop", ["scope_limit", "value_bridge", "send_info_capture"], "answer_privacy_security_with_allowed_facts_only", True, ["invent security proof", "invent compliance claim"]),
    ("contract_or_terms_question", "Buyer asks about contract terms, commitment, cancellation, or legal language.", ["what are the terms?", "is there a contract?", "can we cancel?"], "objection_acknowledge_answer_bridge", ["scope_limit", "value_bridge", "send_info_capture"], "answer_terms_boundary_with_allowed_facts_only", True, ["invent terms", "give legal advice"]),
    ("who_are_you", "Buyer asks who is calling or who the agent represents.", ["who are you?", "who is this?", "where are you calling from?"], "answer_identity_then_permission", ["opening", "permission", "diagnostic"], "answer_identity_without_invention", True, ["invent identity", "hide caller identity"]),
    ("how_did_you_get_my_number", "Buyer asks about contact source or why they were called.", ["how did you get my number?", "why do you have my contact?", "where did this lead come from?"], "answer_data_source_boundary", ["opening", "permission", "scope_limit"], "answer_data_source_boundary_without_invention", True, ["invent data source", "continue if stop requested"]),
    ("are_you_ai_or_robot", "Buyer asks whether the caller is automated, AI, or a robot.", ["are you a robot?", "are you AI?", "is this automated?"], "ai_disclosure_then_continue_or_stop", ["opening", "permission", "scope_limit"], "disclose_automation_without_impersonation", True, ["claim human if automated", "use internal implementation terms"]),
    ("is_this_recorded", "Buyer asks whether the call is recorded or monitored.", ["is this recorded?", "are you recording?", "is this monitored?"], "privacy_boundary_then_continue_or_stop", ["opening", "permission", "scope_limit"], "answer_recording_boundary_with_configured_facts_only", True, ["invent recording policy", "ignore consent"]),
    ("privacy_data_use_question", "Buyer asks what is done with data or personal information.", ["what do you do with my data?", "how is my information used?", "what data do you keep?"], "privacy_boundary_then_continue_or_stop", ["opening", "permission", "scope_limit", "send_info_capture"], "answer_privacy_boundary_without_collecting_sensitive_data", True, ["invent privacy policy", "request sensitive data"]),
    ("permission_to_continue_denied", "Buyer denies permission to continue.", ["no", "not interested", "do not continue"], "stop_close_politely", ["opening", "permission"], "preserve_terminal_stop_state", False, ["continue selling", "ask diagnostic"]),
    ("language_mismatch", "Buyer says the current language is not workable or asks for another language.", ["I do not speak English well", "can you speak slower?", "not in this language"], "language_mismatch_repair", ["opening", "permission", "diagnostic"], "do_not_advance_until_language_repaired", True, ["continue in wrong language", "infer pain"]),
    ("abusive_or_hostile_buyer", "Buyer is hostile, insulting, or verbally aggressive.", ["this is stupid", "leave me alone", "angry profanity"], "hostile_buyer_deescalation", ["opening", "permission", "diagnostic", "value_bridge", "scope_limit"], "deescalate_or_close_without_retaliation", False, ["argue", "mirror hostility"]),
    ("sensitive_personal_data_disclosure", "Buyer volunteers sensitive personal, financial, medical, or credential-like data.", ["my password is", "my medical issue is", "my card number is"], "privacy_boundary_then_continue_or_stop", ["diagnostic", "scope_limit", "send_info_capture"], "do_not_store_or_request_sensitive_data", True, ["request sensitive personal data", "repeat sensitive data"]),
    ("appointment_time_vague", "Buyer gives an incomplete appointment or callback time.", ["later tomorrow", "sometime next week", "afternoon works"], "appointment_time_clarification", ["appointment_progression", "callback_capture"], "request_missing_time_without_scheduling", False, ["confirm without time", "invent missing detail"]),
    ("appointment_time_conflict", "Buyer rejects or conflicts with a proposed time.", ["not then", "that does not work", "I cannot do three"], "appointment_time_clarification", ["appointment_progression", "callback_capture"], "request_alternative_time", False, ["force same time", "end unless buyer stops"]),
    ("buyer_requests_available_times", "Buyer asks what times are available.", ["what times do you have?", "can you send available times?", "when can they call?"], "offer_callback_window_without_calendar_claim", ["appointment_progression", "callback_capture"], "offer_broad_windows_without_calendar_claim", True, ["claim calendar access", "invent availability"]),
    ("buyer_wants_email_before_booking", "Buyer wants written information before booking.", ["email me before booking", "send it then maybe", "details first"], "send_info_contact_capture", ["appointment_progression", "send_info_capture", "value_bridge"], "capture_send_info_preference_without_email_write", False, ["claim email sent", "force booking"]),
    ("buyer_defers_to_later", "Buyer defers decision or conversation to a later time.", ["call me next week", "not now, later", "maybe later"], "defer_politely_preserve_interest", ["permission", "diagnostic", "value_bridge", "appointment_progression"], "preserve_interest_request_later_window", False, ["pressure now", "erase prior gap"]),
    ("buyer_accepts_callback_without_time", "Buyer accepts follow-up but does not provide a usable time.", ["sure call me", "that would be good", "yes have them reach out"], "clarify_missing_time", ["value_bridge", "appointment_progression", "callback_capture"], "request_missing_time_if_followup_accepted", False, ["treat as scheduled", "invent time"]),
    ("buyer_changes_time", "Buyer updates a previously mentioned callback or appointment time.", ["make it four instead", "actually Friday", "change that to morning"], "confirm_time_without_calendar_write", ["appointment_progression", "callback_capture"], "update_local_time_without_external_write", False, ["claim calendar changed", "ignore new time"]),
    ("buyer_confirms_time", "Buyer confirms a clear proposed or captured callback time.", ["yes tomorrow at three", "that time works", "confirmed"], "confirm_time_without_calendar_write", ["appointment_progression", "callback_capture"], "confirm_time_without_external_write", False, ["claim calendar write", "restart diagnostics"]),
    ("buyer_declines_after_interest", "Buyer declines after previously showing interest.", ["actually no", "never mind", "not interested anymore"], "close_after_decline", ["value_bridge", "appointment_progression", "callback_capture"], "close_after_decline_preserve_no_state", False, ["push appointment", "ask diagnostic"]),
    ("why_should_i_care", "Buyer asks why the call matters to them.", ["why should I care?", "why does this matter?", "so what?"], "value_question_answer_with_allowed_facts", ["opening", "permission", "diagnostic", "value_bridge"], "answer_value_using_allowed_facts_only", True, ["invent ROI", "repeat menu"]),
    ("what_makes_you_different", "Buyer asks about differentiation.", ["what makes you different?", "why you?", "what is special?"], "value_question_answer_with_allowed_facts", ["diagnostic", "value_bridge", "scope_limit"], "answer_differentiation_using_allowed_facts_only", True, ["invent superiority", "bash competitors"]),
    ("what_problem_do_you_solve", "Buyer asks what problem the offer addresses.", ["what problem do you solve?", "what is this for?", "what do you help with?"], "value_question_answer_with_allowed_facts", ["opening", "permission", "diagnostic", "value_bridge"], "answer_problem_scope_with_allowed_facts", True, ["invent problem", "ask appointment before relevance"]),
    ("what_result_can_i_expect", "Buyer asks about expected results or outcome.", ["what result can I expect?", "what will this do for me?", "what improvement?"], "value_question_answer_with_allowed_facts", ["diagnostic", "value_bridge", "scope_limit"], "answer_outcome_boundary_with_allowed_claims", True, ["guarantee result", "invent savings"]),
    ("is_this_worth_my_time", "Buyer asks if continuing is worth their time.", ["is this worth my time?", "why stay on the phone?", "make it worth it"], "value_question_answer_with_allowed_facts", ["opening", "permission", "diagnostic"], "answer_time_value_then_one_question", True, ["overpitch", "invent claim"]),
    ("who_is_this_for", "Buyer asks what buyer, role, or situation the offer is for.", ["who is this for?", "who uses this?", "is this for me?"], "value_question_answer_with_allowed_facts", ["opening", "permission", "diagnostic", "value_bridge"], "answer_target_scope_with_allowed_facts", True, ["invent segment", "pressure no-fit buyer"]),
    ("does_this_apply_to_us", "Buyer asks whether the campaign is relevant to their situation.", ["does this apply to us?", "is this relevant for us?", "would this matter here?"], "value_question_answer_with_allowed_facts", ["permission", "diagnostic", "value_bridge"], "answer_relevance_then_one_diagnostic", True, ["claim fit without evidence", "repeat broad menu"]),
    ("small_talk", "Buyer makes light social conversation unrelated to the sale.", ["how are you?", "busy day", "nice weather"], "social_smalltalk_bridge_back", ["opening", "permission", "diagnostic"], "acknowledge_without_changing_sales_memory", False, ["linger on small talk", "infer pain"]),
    ("humor_or_sarcasm", "Buyer jokes or uses sarcasm.", ["sure, if it is free", "sounds thrilling", "funny comment"], "social_smalltalk_bridge_back", ["opening", "permission", "diagnostic", "value_bridge"], "acknowledge_tone_without_overreacting", False, ["argue with joke", "treat sarcasm as consent"]),
    ("silence_or_backchannel", "Buyer gives silence, filler, or low-information backchannel.", ["hmm", "okay", "uh huh"], "social_smalltalk_bridge_back", ["opening", "permission", "diagnostic", "value_bridge"], "preserve_prior_context_request_one_clear_answer", False, ["classify as pain", "schedule from backchannel"]),
    ("interruption_or_barge_in", "Buyer interrupts before the agent completes a point.", ["wait", "hold on", "let me stop you"], "speech_rate_adjustment", ["opening", "permission", "diagnostic", "value_bridge"], "stop_and_listen_preserve_context", True, ["talk over buyer", "ignore interruption"]),
    ("buyer_talks_over_agent", "Buyer starts speaking over the agent or corrects the flow.", ["buyer overlaps", "let me talk", "you are talking over me"], "speech_rate_adjustment", ["opening", "permission", "diagnostic", "value_bridge"], "yield_turn_and_preserve_context", True, ["keep talking", "restart script"]),
    ("repeat_last_answer", "Buyer asks the agent to repeat the last answer.", ["say that again", "repeat that", "what did you say?"], "repeat_last_answer_shorter", ["opening", "permission", "diagnostic", "value_bridge", "scope_limit"], "repeat_last_answer_without_new_claims", True, ["change answer", "add claims"]),
    ("slow_down_or_speak_faster", "Buyer asks for a different speed or cadence.", ["slow down", "speak faster", "too fast"], "speech_rate_adjustment", ["opening", "permission", "diagnostic", "value_bridge"], "adjust_cadence_without_state_change", True, ["blame buyer", "ignore request"]),
    ("pronunciation_or_name_correction", "Buyer corrects pronunciation, name, title, or identity wording.", ["that is not how you say my name", "call me Pat", "you said it wrong"], "speech_rate_adjustment", ["opening", "permission", "diagnostic"], "record_correction_without_repeating_sensitive_data", True, ["argue", "repeat incorrect name"]),
    ("emotional_frustration", "Buyer expresses frustration without necessarily stopping the call.", ["this is annoying", "you keep asking the same thing", "I am frustrated"], "hostile_buyer_deescalation", ["opening", "permission", "diagnostic", "value_bridge", "scope_limit"], "deescalate_preserve_context_or_close", True, ["over-apologize in loop", "repeat same question"]),
]

for (
    _move_id,
    _description,
    _examples,
    _shape_id,
    _allowed_stages,
    _memory_policy,
    _must_answer_direct_question,
    _must_not_do,
) in EXPANDED_BUYER_MOVE_SPECS:
    BUYER_MOVE_TAXONOMY[_move_id] = _move(
        _move_id,
        description=_description,
        examples=list(_examples),
        expected_response_shape_id=_shape_id,
        allowed_stages=list(_allowed_stages),
        default_call_control_allowed=["continue-call", "end-call"] if _shape_id in {"close_after_decline", "hostile_buyer_deescalation"} else ["continue-call"],
        memory_policy=_memory_policy,
        must_acknowledge=True,
        must_answer_direct_question=_must_answer_direct_question,
        must_not_do=list(_must_not_do),
    )


for _move_id in ["permission_to_continue_denied", "buyer_declines_after_interest"]:
    BUYER_MOVE_TAXONOMY[_move_id]["default_call_control_allowed"] = ["end-call"]

for _move_id in ["buyer_confirms_time", "buyer_changes_time", "callback_time_provided"]:
    if _move_id in BUYER_MOVE_TAXONOMY:
        BUYER_MOVE_TAXONOMY[_move_id]["default_call_control_allowed"] = ["continue-call", "schedule-and-end"]


def _append_unique(target: list[str], additions: list[str]) -> None:
    for item in additions:
        if item not in target:
            target.append(item)


_append_unique(CONVERSATION_STAGE_POLICY["opening"]["allowed_buyer_moves"], IDENTITY_TRUST_PRIVACY_BUYER_MOVES + VALUE_DIFFERENTIATION_BUYER_MOVES + SOCIAL_CONVERSATION_BUYER_MOVES)
_append_unique(CONVERSATION_STAGE_POLICY["permission"]["allowed_buyer_moves"], OBJECTION_BUYER_MOVES + IDENTITY_TRUST_PRIVACY_BUYER_MOVES + VALUE_DIFFERENTIATION_BUYER_MOVES + SOCIAL_CONVERSATION_BUYER_MOVES + APPOINTMENT_NEGOTIATION_BUYER_MOVES)
_append_unique(CONVERSATION_STAGE_POLICY["diagnostic"]["allowed_buyer_moves"], OBJECTION_BUYER_MOVES + IDENTITY_TRUST_PRIVACY_BUYER_MOVES + APPOINTMENT_NEGOTIATION_BUYER_MOVES + VALUE_DIFFERENTIATION_BUYER_MOVES + SOCIAL_CONVERSATION_BUYER_MOVES)
_append_unique(CONVERSATION_STAGE_POLICY["value_bridge"]["allowed_buyer_moves"], OBJECTION_BUYER_MOVES + APPOINTMENT_NEGOTIATION_BUYER_MOVES + VALUE_DIFFERENTIATION_BUYER_MOVES + SOCIAL_CONVERSATION_BUYER_MOVES)
_append_unique(CONVERSATION_STAGE_POLICY["scope_limit"]["allowed_buyer_moves"], OBJECTION_BUYER_MOVES + IDENTITY_TRUST_PRIVACY_BUYER_MOVES + VALUE_DIFFERENTIATION_BUYER_MOVES + SOCIAL_CONVERSATION_BUYER_MOVES)
_append_unique(CONVERSATION_STAGE_POLICY["appointment_progression"]["allowed_buyer_moves"], APPOINTMENT_NEGOTIATION_BUYER_MOVES + OBJECTION_BUYER_MOVES + SOCIAL_CONVERSATION_BUYER_MOVES)
_append_unique(CONVERSATION_STAGE_POLICY["callback_capture"]["allowed_buyer_moves"], APPOINTMENT_NEGOTIATION_BUYER_MOVES + SOCIAL_CONVERSATION_BUYER_MOVES)
_append_unique(CONVERSATION_STAGE_POLICY["send_info_capture"]["allowed_buyer_moves"], OBJECTION_BUYER_MOVES + IDENTITY_TRUST_PRIVACY_BUYER_MOVES + APPOINTMENT_NEGOTIATION_BUYER_MOVES + VALUE_DIFFERENTIATION_BUYER_MOVES)
_append_unique(CONVERSATION_STAGE_POLICY["handoff_right_person"]["allowed_buyer_moves"], OBJECTION_BUYER_MOVES + IDENTITY_TRUST_PRIVACY_BUYER_MOVES + SOCIAL_CONVERSATION_BUYER_MOVES)
_append_unique(CONVERSATION_STAGE_POLICY["stop_close"]["allowed_buyer_moves"], ["permission_to_continue_denied", "buyer_declines_after_interest", "abusive_or_hostile_buyer"])


def _repair_rule(
    rule_id: str,
    buyer_move_id: str,
    *,
    response_shape_id: str | None = None,
    memory_policy: str | None = None,
    call_control_constraints: list[str] | None = None,
    forbidden_response_patterns: list[str] | None = None,
    campaign_fact_slots_allowed: list[str] | None = None,
) -> dict[str, Any]:
    move = BUYER_MOVE_TAXONOMY[buyer_move_id]
    shape_id = response_shape_id or str(move.get("expected_response_shape_id"))
    shape = RESPONSE_SHAPE_LIBRARY[shape_id]
    return {
        "buyer_move_id": buyer_move_id,
        "recognition_notes": list(move.get("examples") or []) + [str(move.get("description"))],
        "response_shape_id": shape_id,
        "memory_policy": memory_policy or str(move.get("memory_policy")),
        "call_control_constraints": list(call_control_constraints or ["continue-call unless buyer stops", "forbid transfer-or-escalate unless explicitly required"]),
        "forbidden_response_patterns": list(forbidden_response_patterns or move.get("must_not_do") or DEFAULT_FORBIDDEN_PATTERNS),
        "campaign_fact_slots_allowed": list(campaign_fact_slots_allowed or shape.get("allowed_fact_slots") or []),
    }


for _move_id in (
    OBJECTION_BUYER_MOVES
    + IDENTITY_TRUST_PRIVACY_BUYER_MOVES
    + APPOINTMENT_NEGOTIATION_BUYER_MOVES
    + VALUE_DIFFERENTIATION_BUYER_MOVES
    + SOCIAL_CONVERSATION_BUYER_MOVES
):
    UNIVERSAL_REPAIR_RULES[f"{_move_id}_rule"] = _repair_rule(f"{_move_id}_rule", _move_id)

UNIVERSAL_REPAIR_RULES["permission_to_continue_denied_rule"]["call_control_constraints"] = ["end-call", "do not continue if consent is denied"]
UNIVERSAL_REPAIR_RULES["buyer_declines_after_interest_rule"]["call_control_constraints"] = ["end-call", "do not push appointment after decline"]
UNIVERSAL_REPAIR_RULES["buyer_confirms_time_rule"]["call_control_constraints"] = ["continue-call or schedule-and-end after usable time", "do not claim external scheduling write"]
UNIVERSAL_REPAIR_RULES["buyer_changes_time_rule"]["call_control_constraints"] = ["continue-call or schedule-and-end after usable time", "do not claim calendar changed"]
UNIVERSAL_REPAIR_RULES["are_you_ai_or_robot_rule"]["forbidden_response_patterns"] += ["claim human if automated"]
UNIVERSAL_REPAIR_RULES["privacy_data_use_question_rule"]["forbidden_response_patterns"] += ["request sensitive personal data"]
UNIVERSAL_REPAIR_RULES["sensitive_personal_data_disclosure_rule"]["forbidden_response_patterns"] += ["repeat sensitive data", "store sensitive data"]


ASR_REPAIR_BOUNDARY["cases"].update(
    {
        "homophone_or_near_miss": {
            "id": "homophone_or_near_miss",
            "description": "Transcript contains a plausible homophone or near-miss that changes the domain meaning.",
            "examples": ["repair timings misheard as repeal timings", "coverage fit misheard as cover age fit"],
            "policy": "ask_repeat_for_asr_garble_or_confirm_term",
        },
        "non_english_or_mixed_language": {
            "id": "non_english_or_mixed_language",
            "description": "Transcript switches language or mixes languages enough to make routing unsafe.",
            "examples": ["mixed-language answer after diagnostic question"],
            "policy": "ask_repeat_for_asr_garble",
        },
        "transcript_contains_command_noise": {
            "id": "transcript_contains_command_noise",
            "description": "Transcript includes command words, device commands, or dictation artifacts.",
            "examples": ["stop recording comma yes", "new line that would be good"],
            "policy": "ask_repeat_for_asr_garble",
        },
        "transcript_contains_browser_noise": {
            "id": "transcript_contains_browser_noise",
            "description": "Transcript includes browser, microphone, or page-control noise.",
            "examples": ["allow microphone", "click start button"],
            "policy": "ask_repeat_for_asr_garble",
        },
        "transcript_has_wrong_named_entity": {
            "id": "transcript_has_wrong_named_entity",
            "description": "Transcript includes a named entity that conflicts with campaign or prior conversation context.",
            "examples": ["wrong company or person name appears in transcript"],
            "policy": "ask_repeat_for_asr_garble_or_confirm_term",
        },
        "ambiguous_yes_after_unanswered_question": {
            "id": "ambiguous_yes_after_unanswered_question",
            "description": "Yes-like answer follows a question that still had multiple possible meanings.",
            "examples": ["yes after a two-part diagnostic"],
            "policy": "ask_repeat_for_asr_garble_or_confirm_term",
        },
        "ambiguous_positive_after_explanation": {
            "id": "ambiguous_positive_after_explanation",
            "description": "Positive phrase after an explanation may mean understood, interested, or ready for callback.",
            "examples": ["yeah that would be good misheard as unrelated phrase", "play a double be good"],
            "policy": "ask_repeat_for_asr_garble_or_confirm_term",
        },
        "ambiguous_negative_after_multi_choice": {
            "id": "ambiguous_negative_after_multi_choice",
            "description": "Negative phrase after a multi-choice question does not identify which option is being rejected.",
            "examples": ["no after several gap options"],
            "policy": "ask_repeat_for_asr_garble_or_confirm_term",
        },
        "possible_time_misrecognition": {
            "id": "possible_time_misrecognition",
            "description": "Appointment or callback time text appears misrecognized or incomplete.",
            "examples": ["tomorrow at three misheard as unrelated phrase", "free instead of three"],
            "policy": "ask_repeat_for_asr_garble",
        },
        "possible_email_misrecognition": {
            "id": "possible_email_misrecognition",
            "description": "Email address or written contact detail is likely misrecognized.",
            "examples": ["at symbol missing", "domain fragment unclear"],
            "policy": "ask_repeat_for_asr_garble",
        },
        "possible_name_misrecognition": {
            "id": "possible_name_misrecognition",
            "description": "Person, company, or contact name may be misheard.",
            "examples": ["name correction sounds inconsistent with prior context"],
            "policy": "ask_repeat_for_asr_garble_or_confirm_term",
        },
    }
)
_append_unique(
    ASR_REPAIR_BOUNDARY["expected_policy"]["required_behavior"],
    ["confirm high-risk terms before routing", "do not blame ASR or the buyer"],
)
_append_unique(
    ASR_REPAIR_BOUNDARY["expected_policy"]["forbidden_behavior"],
    ["blame ASR", "blame buyer", "route ambiguous yes as appointment", "collect risky contact detail without confirmation"],
)


FORBIDDEN_CUSTOMER_FACING_PATTERNS.extend(
    [
        {
            "id": "human_impersonation",
            "phrases": ["pretending to be human", "claim human if automated"],
            "reason": "Automation must not impersonate a human caller.",
        },
        {
            "id": "external_action_claims",
            "phrases": ["claiming real calendar/email/CRM action occurred", "claim calendar write", "claim email sent", "claim CRM write"],
            "reason": "The runtime must not claim external writes unless an approved integration actually performed them.",
        },
        {
            "id": "unsupported_result_claims",
            "phrases": ["claiming product results without allowed claims", "invent ROI", "invent savings", "invent compliance proof"],
            "reason": "Value claims must stay inside allowed claims.",
        },
        {
            "id": "argument_or_blame",
            "phrases": ["arguing with buyer", "blaming ASR or the buyer", "mirror hostility"],
            "reason": "Conversation repair should reduce friction, not debate the buyer.",
        },
        {
            "id": "model_or_internal_terms",
            "phrases": ["as an AI language model", "using internal implementation terms", "internal route", "semantic classifier"],
            "reason": "Customer-facing speech should not reveal implementation wording.",
        },
        {
            "id": "looping_apology_or_diagnostic",
            "phrases": ["over-apologizing in a loop", "asking the same diagnostic after direct answer", "repeat same non-answer"],
            "reason": "Repair must acknowledge prior context and move forward or close.",
        },
        {
            "id": "pressure_after_no",
            "phrases": ["pushing appointment after explicit no", "continue selling after stop"],
            "reason": "Explicit refusal must close or stop pressure.",
        },
        {
            "id": "sensitive_data_collection",
            "phrases": ["collecting unnecessary sensitive data", "request sensitive personal data", "repeat sensitive data"],
            "reason": "Appointment setting must avoid unnecessary sensitive data collection.",
        },
    ]
)

_append_unique(
    VALIDATOR_MATRIX["buyer_move_test_cases"],
    [
        "who are you?",
        "are you a robot?",
        "how did you get my number?",
        "is this recorded?",
        "what do you do with my data?",
        "we already have a provider",
        "how much does it cost?",
        "send me proof",
        "I need to ask my manager",
        "call me next week",
        "can you send available times?",
        "what makes you different?",
        "why should I care?",
        "not interested",
        "slow down",
        "say that again",
        "I don't speak English well",
        "that's not how you say my name",
        "you keep asking the same thing",
    ],
)


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
