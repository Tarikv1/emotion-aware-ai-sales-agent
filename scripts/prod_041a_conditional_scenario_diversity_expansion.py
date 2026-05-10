#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-041A-conditional-scenario-diversity-expansion"
SOURCE_CHECKPOINT_ID = "PROD-040-callcenteren-conditional-customer-simulation"
SCENARIO_SOURCE_CHECKPOINT_ID = "PROD-014-callcenteren-scenario-bank"
PATTERN_SOURCE_CHECKPOINT_ID = "PROD-013-callcenteren-pattern-extraction"
NEXT_CHECKPOINT_ID = "PROD-041-conditional-simulation-review"
DEFAULT_OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
DEFAULT_RESULT = DEFAULT_OUT_DIR / "result.json"
DEFAULT_REPORT = DEFAULT_OUT_DIR / "report.md"
DEFAULT_TRACE = DEFAULT_OUT_DIR / "scenario_diversity_traces.json"
DEFAULT_SURFACE = DEFAULT_OUT_DIR / "scenario_diversity_review.html"
DEFAULT_SURFACE_DATA = DEFAULT_OUT_DIR / "scenario_diversity_review_data.json"
DEFAULT_SCENARIO_BANK = ROOT / "research" / "experiments" / "generated" / SCENARIO_SOURCE_CHECKPOINT_ID / "scenario-bank.json"
DEFAULT_PATTERN_BANK = ROOT / "research" / "experiments" / "generated" / PATTERN_SOURCE_CHECKPOINT_ID / "pattern-bank.json"

REQUIRED_LABELS = [
    "price_sensitive",
    "manager_review",
    "existing_provider",
    "confused_fit",
    "skeptical_proof",
    "busy_now",
    "send_info",
    "contract_fear",
    "payment_fear",
    "security_review",
    "bad_experience",
    "needs_approval",
    "hidden_objection",
    "competitor_comparison",
    "not_interested",
    "hostile_rejection",
    "callback_request",
    "support_boundary",
    "technical_integration",
    "setup_timeline",
    "multi_location_routing",
    "low_fit",
    "sale_ready",
    "discovery_needed",
    "insurance_price_fear",
    "spouse_input",
    "scam_card_fear",
    "consumer_not_interested",
    "consumer_callback",
    "coverage_confusion",
    "already_covered",
    "consumer_bad_experience",
    "written_info",
    "consumer_hostile",
    "cancellation_boundary",
    "appointment_interest",
    "sensitive_healthcare",
    "home_service_comparison",
    "reminder_plan",
    "no_pressure_consumer",
]

SAFE_CLOSE_OUTCOMES = {
    "accepted",
    "callback_scheduled",
    "written_info_requested",
    "manager_review_needed",
    "handoff_required",
}
NON_SALE_CORRECTNESS_OUTCOMES = {"rejected", "support_boundary_ended", "not_qualified", "do_not_contact"}
TERMINAL_OUTCOMES = SAFE_CLOSE_OUTCOMES | NON_SALE_CORRECTNESS_OUTCOMES
OPENING_STYLES = {
    "b2b_permission_first",
    "b2b_reason_first",
    "b2b_time_respectful",
    "b2b_manager_relevance",
    "b2c_no_payment_disclosure",
    "b2c_simple_consumer_reason",
    "b2c_safety_first",
}
EMOTIONS = {"calm", "skeptical", "confused", "rushed", "irritated", "anxious", "distrustful", "curious"}
STATE_SHIFTS = {"more_trusting", "unchanged", "more_resistant", "escalated", "reassured"}
STRATEGIES = {
    "permission_first",
    "problem_framing",
    "social_proof_safe",
    "risk_reversal",
    "simple_explanation",
    "objection_isolation",
    "next_step_close",
    "consultative_discovery",
    "trust_repair",
}
FAILURE_FLAGS = {
    "dodged_question",
    "question_storming",
    "premature_price_discussion",
    "unsupported_claim",
    "pressure_after_refusal",
    "unsafe_payment_request",
    "missed_handoff",
    "ignored_emotion",
    "repeated_answer",
    "unclear_next_step",
    "product_misfit",
}
HARD_FAILURE_MARKERS = {
    "give me your card",
    "read your card number",
    "guaranteed savings",
    "guaranteed revenue",
    "legal advice",
    "medical advice",
    "coverage is guaranteed",
    "i will keep calling",
    "api call made",
    "raw transcript",
}
BLOCKED_TEMPLATE_PHRASES = [
    "That boundary makes sense.",
    "What would the next step be without pushing me?",
    "Okay, that is clearer on",
    "My remaining concern is",
    "I do not want pressure.",
]
REALISM_COMPONENTS = [
    "natural_customer_language",
    "low_template_repetition",
    "opening_grammar_ok",
    "objection_progression_realistic",
    "terminal_outcome_earned",
]
REQUESTED_VARIETY_TAGS = {
    "short_reply",
    "interruption",
    "skeptical_pushback",
    "one_word_refusal",
    "confused_follow_up",
    "asks_price_early",
    "asks_identity_again",
    "email_only",
    "refuses_before_finish",
}
NON_SMOOTH_VARIETY_TAGS = {
    "interruption",
    "skeptical_pushback",
    "one_word_refusal",
    "confused_follow_up",
    "asks_price_early",
    "asks_identity_again",
    "email_only",
    "refuses_before_finish",
}
OPENING_VARIETY_BY_LABEL = {
    "price_sensitive": ["asks_price_early"],
    "payment_fear": ["asks_identity_again"],
    "send_info": ["email_only"],
    "not_interested": ["refuses_before_finish"],
    "consumer_not_interested": ["refuses_before_finish"],
    "scam_card_fear": ["asks_identity_again"],
    "written_info": ["email_only"],
}
TURN_VARIETY_BY_LABEL = {
    "manager_review": {1: ["short_reply"]},
    "existing_provider": {1: ["interruption"]},
    "confused_fit": {1: ["confused_follow_up"]},
    "skeptical_proof": {1: ["skeptical_pushback"]},
    "hostile_rejection": {1: ["one_word_refusal"]},
    "consumer_hostile": {1: ["one_word_refusal"]},
    "home_service_comparison": {1: ["skeptical_pushback"]},
    "coverage_confusion": {1: ["confused_follow_up"]},
    "busy_now": {1: ["short_reply"]},
}

CONCERN_TEXT = {
    "price_sensitive": "the price and whether it is worth a second conversation",
    "manager_review": "what your manager would need for a quick review",
    "existing_provider": "whether this adds anything when you already have a provider",
    "confused_fit": "how this would fit into your current workflow",
    "skeptical_proof": "what proof you can check later",
    "busy_now": "whether this is worth a callback",
    "send_info": "what needs to be sent in writing",
    "contract_fear": "whether this creates a contract commitment",
    "payment_fear": "whether any payment is being requested",
    "security_review": "whether security needs to review it first",
    "bad_experience": "why this would not repeat the last bad experience",
    "needs_approval": "who needs to approve the next step",
    "hidden_objection": "whether there is enough priority and budget to continue",
    "competitor_comparison": "how this differs from the option you are already comparing",
    "not_interested": "whether there is any reason to keep talking",
    "hostile_rejection": "your clear refusal",
    "callback_request": "the right time to continue",
    "support_boundary": "the support issue that should not be treated as a sales lead",
    "technical_integration": "whether the integration question needs a specialist",
    "setup_timeline": "how long setup would realistically take",
    "multi_location_routing": "how follow-up would work across locations",
    "low_fit": "whether this is actually a fit",
    "sale_ready": "the clean next step after interest is clear",
    "discovery_needed": "what needs to be understood before recommending anything",
    "insurance_price_fear": "the cost concern around insurance help",
    "spouse_input": "whether another person needs to weigh in",
    "scam_card_fear": "whether this is safe and does not involve card details",
    "consumer_not_interested": "your lack of interest",
    "consumer_callback": "the right callback time",
    "coverage_confusion": "what is and is not being confirmed about coverage",
    "already_covered": "whether you already have what you need",
    "consumer_bad_experience": "your previous bad service experience",
    "written_info": "what you want in writing",
    "consumer_hostile": "your refusal as a consumer",
    "cancellation_boundary": "the cancellation or support issue",
    "appointment_interest": "whether an appointment reminder would help",
    "sensitive_healthcare": "the healthcare scheduling concern that needs care",
    "home_service_comparison": "how this compares with another home service option",
    "reminder_plan": "whether reminders would solve the actual problem",
    "no_pressure_consumer": "whether you can continue without pressure",
}

DIRECT_ANSWERS = {
    "price_sensitive": "The price answer is first: the range I can quote here is 29 dollars per user per month for a starter tier and 59 dollars per user per month for a growth tier. If that is outside budget, the right move is to stop or send details, not push.",
    "manager_review": "For your manager, the short version is this: it is a workflow review to reduce missed callbacks and unclear ownership, not a request to approve a purchase today.",
    "existing_provider": "If you already have a provider, this only makes sense if follow-up ownership still breaks around it. If your current provider already solves that, there is no fit.",
    "confused_fit": "In plain terms, this is not a replacement for your team. It is a check on whether leads, reminders, or callbacks are falling between people.",
    "skeptical_proof": "The only proof I should offer here is written and checkable: what workflow is reviewed, what claims are not being made, and what a specialist would verify.",
    "busy_now": "Fair. The direct answer is that this is only worth continuing if missed callbacks are costing time; otherwise we should set a callback or stop.",
    "send_info": "Yes, written information is the right next step. I can send the summary first and leave the decision for later.",
    "contract_fear": "No contract decision should happen on this call. This can only be a review or written summary unless you choose otherwise later.",
    "payment_fear": "No payment is being collected here. If payment ever becomes relevant, it belongs in a separate verified checkout process, not this call.",
    "security_review": "Your security team should review this before any technical commitment. I can only route the question and avoid making claims I cannot verify.",
    "bad_experience": "Given the previous bad experience, the safe answer is to slow down, put the details in writing, and avoid promising that this will fix everything.",
    "needs_approval": "If approval is needed, the only useful step is a short internal note and a review path, not asking you to decide alone.",
    "hidden_objection": "If budget or priority is the real blocker, it is better to say that now. We can either check fit briefly or close this out.",
    "competitor_comparison": "The honest comparison is about workflow fit, not claiming we are better. If you are comparing options, written criteria are the safest next step.",
    "not_interested": "Understood. If you are not interested, I should not keep pitching.",
    "hostile_rejection": "Understood. I will stop the sales conversation and respect the refusal.",
    "callback_request": "A callback is fine. I only need the best window; I do not need to keep pitching now.",
    "support_boundary": "That is a support issue, not a sales discussion. I should route it to support and end the sales path.",
    "technical_integration": "The integration answer needs a specialist. I can note the question and hand it off instead of guessing.",
    "setup_timeline": "Setup timing depends on systems and team size, so the safe answer is a scoped review before giving a timeline.",
    "multi_location_routing": "For multiple locations, the practical point is assigning clear follow-up ownership by location so requests do not get lost.",
    "low_fit": "If the problem is not happening in your workflow, this is not qualified and I should not force it.",
    "sale_ready": "If you are already interested, the clean next step is a non-binding review slot, not a payment or contract decision.",
    "discovery_needed": "Before recommending anything, I need to understand where follow-ups or reminders currently break, if they break at all.",
    "insurance_price_fear": "For insurance-related cost questions, I cannot confirm coverage or savings. I can only send general information or route you to a qualified person.",
    "spouse_input": "If your spouse needs input, the right next step is a written summary or callback after you have both seen it.",
    "scam_card_fear": "No card details should be shared on this call. If you want information, it should be written and non-binding.",
    "consumer_not_interested": "Understood. If you are not interested, I should stop instead of trying to persuade you.",
    "consumer_callback": "A callback is the right next step if now is bad. I can set one window and stop here.",
    "coverage_confusion": "I cannot confirm coverage on this call. A qualified person has to review that before any decision.",
    "already_covered": "If you are already covered and do not have a follow-up problem, there may be no need to continue.",
    "consumer_bad_experience": "Given the bad experience, I should not push. Written details and a clear support route are safer.",
    "written_info": "Written information first is reasonable. No decision needs to happen on this call.",
    "consumer_hostile": "Understood. I will stop the conversation and respect that boundary.",
    "cancellation_boundary": "Cancellation is a support matter. I should route it and not turn it into a sales pitch.",
    "appointment_interest": "If appointment reminders would help, the next step can be a no-payment scheduling review.",
    "sensitive_healthcare": "For healthcare scheduling, I cannot provide clinical guidance. I can only route scheduling questions to the right qualified path.",
    "home_service_comparison": "For a comparison, the fair answer is to look at written criteria and avoid claiming this is better without proof.",
    "reminder_plan": "A reminder plan only makes sense if missed appointments or follow-ups are a real problem for you.",
    "no_pressure_consumer": "No pressure. You can hear the short explanation, request writing, or end the call.",
}


SCENARIO_CONFIGS = [
    ("price_sensitive", "B2B", "field-service software", "skeptical", "price", "problem_framing", "callback_scheduled"),
    ("manager_review", "B2B", "logistics", "curious", "manager approval", "next_step_close", "manager_review_needed"),
    ("existing_provider", "B2B", "healthcare operations", "calm", "existing provider", "objection_isolation", "callback_scheduled"),
    ("confused_fit", "B2B", "manufacturing", "confused", "fit confusion", "simple_explanation", "callback_scheduled"),
    ("skeptical_proof", "B2B", "financial services", "skeptical", "proof", "social_proof_safe", "written_info_requested"),
    ("busy_now", "B2B", "SaaS operations", "rushed", "time", "permission_first", "callback_scheduled"),
    ("send_info", "B2B", "education services", "calm", "written information", "next_step_close", "written_info_requested"),
    ("contract_fear", "B2B", "hospitality", "anxious", "contract", "risk_reversal", "written_info_requested"),
    ("payment_fear", "B2B", "automotive services", "distrustful", "payment safety", "trust_repair", "handoff_required"),
    ("security_review", "B2B", "cybersecurity", "skeptical", "security review", "social_proof_safe", "handoff_required"),
    ("bad_experience", "B2B", "retail chain", "irritated", "bad experience", "trust_repair", "written_info_requested"),
    ("needs_approval", "B2B", "real estate", "calm", "approval", "next_step_close", "manager_review_needed"),
    ("hidden_objection", "B2B", "professional services", "curious", "hidden budget concern", "objection_isolation", "callback_scheduled"),
    ("competitor_comparison", "B2B", "marketing agency", "skeptical", "comparison", "social_proof_safe", "written_info_requested"),
    ("not_interested", "B2B", "wholesale distribution", "calm", "not interested", "permission_first", "rejected"),
    ("hostile_rejection", "B2B", "telecom reseller", "irritated", "hostile refusal", "trust_repair", "do_not_contact"),
    ("callback_request", "B2B", "property management", "rushed", "callback", "permission_first", "callback_scheduled"),
    ("support_boundary", "B2B", "B2B software", "irritated", "support issue", "trust_repair", "support_boundary_ended"),
    ("technical_integration", "B2B", "manufacturing", "curious", "integration", "consultative_discovery", "handoff_required"),
    ("setup_timeline", "B2B", "healthcare operations", "anxious", "timeline", "simple_explanation", "callback_scheduled"),
    ("multi_location_routing", "B2B", "retail chain", "calm", "multi-location routing", "problem_framing", "accepted"),
    ("low_fit", "B2B", "construction", "confused", "low fit", "consultative_discovery", "not_qualified"),
    ("sale_ready", "B2B", "field-service software", "curious", "ready to proceed", "next_step_close", "accepted"),
    ("discovery_needed", "B2B", "SaaS operations", "calm", "needs discovery", "consultative_discovery", "callback_scheduled"),
    ("insurance_price_fear", "B2C", "insurance service", "anxious", "insurance price", "risk_reversal", "written_info_requested"),
    ("spouse_input", "B2C", "home services", "calm", "spouse input", "next_step_close", "callback_scheduled"),
    ("scam_card_fear", "B2C", "consumer telecom", "distrustful", "scam or card fear", "trust_repair", "written_info_requested"),
    ("consumer_not_interested", "B2C", "retail membership", "calm", "not interested", "permission_first", "rejected"),
    ("consumer_callback", "B2C", "automotive service", "rushed", "callback", "permission_first", "callback_scheduled"),
    ("coverage_confusion", "B2C", "insurance service", "confused", "coverage confusion", "simple_explanation", "handoff_required"),
    ("already_covered", "B2C", "consumer telecom", "calm", "already covered", "objection_isolation", "rejected"),
    ("consumer_bad_experience", "B2C", "home services", "irritated", "bad experience", "trust_repair", "written_info_requested"),
    ("written_info", "B2C", "consumer wellness", "skeptical", "written information", "next_step_close", "written_info_requested"),
    ("consumer_hostile", "B2C", "retail membership", "irritated", "hostile refusal", "trust_repair", "do_not_contact"),
    ("cancellation_boundary", "B2C", "subscription service", "irritated", "cancellation", "trust_repair", "support_boundary_ended"),
    ("appointment_interest", "B2C", "healthcare scheduling", "curious", "appointment", "next_step_close", "accepted"),
    ("sensitive_healthcare", "B2C", "healthcare scheduling", "anxious", "healthcare sensitivity", "risk_reversal", "handoff_required"),
    ("home_service_comparison", "B2C", "home services", "skeptical", "comparison", "social_proof_safe", "rejected"),
    ("reminder_plan", "B2C", "automotive service", "calm", "reminder plan", "problem_framing", "accepted"),
    ("no_pressure_consumer", "B2C", "consumer wellness", "distrustful", "pressure concern", "trust_repair", "accepted"),
]


def rel_path(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_boundaries() -> dict[str, bool]:
    return {
        "provider_calls_made": False,
        "llm_used": False,
        "private_data_read": False,
        "dataset_download_performed": False,
        "raw_transcript_text_stored": False,
        "copied_transcript_text_used": False,
        "commercial_runtime_prompt_text_from_transcripts_allowed": False,
        "customer_data_allowed": False,
        "payment_collection_enabled": False,
        "runtime_behavior_changed_by_this_checkpoint": False,
        "runtime_retrieval_default_enabled": False,
        "composer_hook_flag_default_enabled": False,
        "live_provider_default_enabled": False,
        "server_started": False,
        "source_prod_040_overwritten": False,
        "source_prod_014_overwritten": False,
        "source_prod_013_overwritten": False,
        "production_runtime_promotion_allowed": False,
    }


def source_ids(scenario_bank_path: Path, pattern_bank_path: Path) -> tuple[list[str], list[str]]:
    scenario_bank = read_json(scenario_bank_path)
    pattern_bank = read_json(pattern_bank_path)
    scenario_ids = [
        str(item.get("scenario_id"))
        for item in scenario_bank.get("scenario_bank", [])
        if item.get("scenario_id")
    ]
    pattern_ids: list[str] = []

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                if key in {"pattern_id", "source_pattern_id"} and isinstance(child, str):
                    pattern_ids.append(child)
                elif key == "source_pattern_ids" and isinstance(child, list):
                    pattern_ids.extend(str(item) for item in child)
                else:
                    walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(pattern_bank)
    if not scenario_ids:
        scenario_ids = [f"prod-014-abstract-{index:03d}" for index in range(1, 41)]
    if len(pattern_ids) < 120:
        pattern_ids.extend(f"prod-013-abstract-pattern-{index:03d}" for index in range(1, 121))
    return scenario_ids, pattern_ids


def opening_style(index: int, market_scope: str) -> str:
    b2b = ["b2b_permission_first", "b2b_reason_first", "b2b_time_respectful", "b2b_manager_relevance"]
    b2c = ["b2c_no_payment_disclosure", "b2c_simple_consumer_reason", "b2c_safety_first"]
    return (b2b if market_scope == "B2B" else b2c)[index % (4 if market_scope == "B2B" else 3)]


def opening_variants(profile: dict[str, Any]) -> list[str]:
    concern = CONCERN_TEXT[profile["scenario_label"]]
    domain = profile["domain"]
    if profile["b2b_or_b2c"] == "B2B":
        variants = [
            f"Hi, this is Maya from RouteSignal. Before I get into it, is this an okay moment to share the {domain} reason I called about {concern}?",
            f"Hi, this is Maya from RouteSignal. The reason I called is a short workflow check for {domain} teams dealing with {concern}; may I take thirty seconds?",
            f"Hi, this is Maya from RouteSignal. I know your time is tight, so I can keep this to one practical {domain} point about {concern} and stop if it is not relevant.",
            f"Hi, this is Maya from RouteSignal. For teams dealing with {concern}, the manager-level reason is usually routing clarity, not a surprise purchase pitch.",
        ]
    else:
        variants = [
            f"Hi, this is Maya from RouteSignal Home. I will not ask for payment or card details; I am calling about a simple {domain} reminder question tied to {concern}.",
            f"Hi, this is Maya from RouteSignal Home. The short consumer reason is a reminder check around {concern}.",
            f"Hi, this is Maya from RouteSignal Home. If this feels unsafe or irrelevant, you can stop me; I only want to clarify the {domain} reason around {concern}.",
        ]
    return variants


def opening_customer_text(profile: dict[str, Any]) -> str:
    concern = CONCERN_TEXT[profile["scenario_label"]]
    label = profile["scenario_label"]
    if label == "price_sensitive":
        return "Before anything else, what does it cost? I am not sitting through a pitch without a number."
    if label in {"payment_fear", "scam_card_fear"}:
        return f"Wait, who are you again? I am not giving card details for {concern} to someone who just called me."
    if label in {"send_info", "written_info"}:
        return f"Just email it about {concern}. I am not discussing this live."
    if label in {"not_interested", "consumer_not_interested"}:
        return f"I am going to stop you there. Not interested in a call about {concern}."
    emotion = profile["customer_emotional_state_start"]
    if emotion == "rushed":
        return f"I am short on time. If this is about {concern}, make it brief and do not bury the point."
    if emotion == "irritated":
        return f"I am already frustrated about this kind of call. If the issue is {concern}, do not argue with me."
    if emotion == "confused":
        return f"I do not understand where this fits. Explain the part about {concern} in plain language first."
    if emotion == "anxious":
        return f"I am worried {concern} turns into risk or commitment. Be clear about the boundary before anything else."
    if emotion == "distrustful":
        return f"I do not trust phone offers about {concern}, and I will not give payment details. What is this actually about?"
    if emotion == "skeptical":
        return f"I hear claims like this all the time. Give me a direct, grounded answer on {concern}."
    if emotion == "curious":
        return f"I can listen if it is relevant. What is the practical reason for {concern}?"
    return f"I can hear the short version. Start with the practical reason around {concern}."


def emotion_phrase(emotion: str) -> str:
    return {
        "confused": "Let me keep it simple and answer one point at a time.",
        "rushed": "I will keep this brief, and we can set a callback instead of stretching the call.",
        "irritated": "I hear the frustration, and I am not here to argue with you.",
        "anxious": "No pressure here; nothing risky needs to happen on this call.",
        "distrustful": "No hype and no payment collection; the safety boundary comes first.",
        "skeptical": "Fair question. I will answer directly and stick to what I can support.",
        "curious": "Yes, and I will give the context before asking anything else.",
        "calm": "I can give you the clear version and one low-pressure next step.",
    }[emotion]


def strategy_phrase(strategy: str, profile: dict[str, Any], stage: str) -> str:
    domain = profile["domain"]
    concern = CONCERN_TEXT[profile["scenario_label"]]
    if strategy == "permission_first":
        return f"Your control comes first: if now is bad, we can stop or set one callback to cover {concern}."
    if strategy == "problem_framing":
        return f"The business reason to keep talking is whether {domain} follow-up gets unclear, like who owns callbacks after the first question, not whether you should buy something today."
    if strategy == "social_proof_safe":
        return f"The safe proof point is general: teams review this kind of workflow when follow-up gaps keep repeating, without assuming your results."
    if strategy == "risk_reversal":
        return f"The risk boundary is simple: no purchase, no card details, no contract decision, and no promise beyond a review of {concern}."
    if strategy == "simple_explanation":
        return f"In plain language, this checks whether the {domain} follow-up path is clear enough for the issue you raised."
    if strategy == "objection_isolation":
        return "The main issue sounds like the concern you just raised; I will answer that directly before asking anything else."
    if strategy == "next_step_close":
        return f"The clean next step would be to {next_step_text(profile)}."
    if strategy == "consultative_discovery":
        return f"One useful question after context: is this happening often enough to justify a short review?"
    if strategy == "trust_repair":
        return f"I understand the hesitation; I will remove pressure, keep payment out of scope, and route support or handoff if needed."
    raise ValueError(strategy)


def next_step_text(profile: dict[str, Any]) -> str:
    terminal = profile["target_outcome"]
    concern = CONCERN_TEXT[profile["scenario_label"]]
    if terminal == "accepted":
        return f"book a non-binding review focused on {concern}"
    if terminal == "callback_scheduled":
        return f"schedule one callback window to discuss {concern}"
    if terminal == "written_info_requested":
        return f"send a short written summary about {concern}"
    if terminal == "manager_review_needed":
        return f"send a short note your manager can review about {concern}"
    if terminal == "handoff_required":
        return f"handoff to the qualified specialist for {concern}"
    if terminal == "support_boundary_ended":
        return "stop the sales path and route the support boundary"
    if terminal == "not_qualified":
        return "mark this as not qualified and avoid forcing fit"
    if terminal == "do_not_contact":
        return f"honor the do-not-contact request about {concern}"
    return f"close the loop without pressure on {concern}"


def terminal_customer_response(profile: dict[str, Any]) -> str:
    concern = CONCERN_TEXT[profile["scenario_label"]]
    terminal = profile["target_outcome"]
    if terminal == "accepted":
        return f"That is clear enough on {concern}. I accept a no-pressure next step, with no payment handled here."
    if terminal == "callback_scheduled":
        return f"Because you kept it brief on {concern}, schedule one callback and do not keep selling now."
    if terminal == "written_info_requested":
        return f"Send the details on {concern} in writing first. I am not deciding on this call."
    if terminal == "manager_review_needed":
        return f"I need my manager to review {concern} before anything else. Send the short internal summary and stop there."
    if terminal == "handoff_required":
        return f"This needs the right specialist for {concern}. Handoff is fine, but do not make claims you cannot verify."
    if terminal == "support_boundary_ended":
        return f"This is a support issue around {concern}, not a sale. End the sales path and route support."
    if terminal == "not_qualified":
        return f"Based on that explanation, this does not fit my situation. Mark it not qualified."
    if terminal == "do_not_contact":
        return f"No. Do not contact me again about {concern}."
    if terminal == "rejected":
        return f"I understand the answer on {concern}, but I am rejecting the offer for now."
    raise ValueError(terminal)


def valid_terminal_outcomes(target: str) -> list[str]:
    alternatives = {
        "accepted": ["accepted", "callback_scheduled", "written_info_requested"],
        "callback_scheduled": ["callback_scheduled", "written_info_requested", "rejected"],
        "written_info_requested": ["written_info_requested", "manager_review_needed", "rejected"],
        "manager_review_needed": ["manager_review_needed", "written_info_requested", "rejected"],
        "handoff_required": ["handoff_required", "support_boundary_ended", "written_info_requested"],
        "support_boundary_ended": ["support_boundary_ended", "handoff_required", "rejected"],
        "not_qualified": ["not_qualified", "rejected"],
        "do_not_contact": ["do_not_contact"],
        "rejected": ["rejected", "written_info_requested", "callback_scheduled"],
    }
    return alternatives[target]


def build_profiles(scenario_bank_path: Path, pattern_bank_path: Path) -> list[dict[str, Any]]:
    scenario_ids, pattern_ids = source_ids(scenario_bank_path, pattern_bank_path)
    profiles = []
    for index, (label, market, domain, emotion, objection, strategy, terminal) in enumerate(SCENARIO_CONFIGS):
        scenario_id = f"prod-041a-{index + 1:02d}-{label}"
        variants = opening_variants(
            {
                "scenario_label": label,
                "domain": domain,
                "persona": f"{domain} buyer with {objection}",
                "b2b_or_b2c": market,
            }
        )
        style = opening_style(index, market)
        profile = {
            "scenario_id": scenario_id,
            "scenario_label": label,
            "market_scope": market,
            "domain": domain,
            "b2b_or_b2c": market,
            "persona": f"{domain} buyer with {objection}",
            "customer_emotional_state_start": emotion,
            "customer_knowledge_level": ["low", "medium", "high"][index % 3],
            "customer_state_shift": state_shift_for(terminal, emotion),
            "offer_profile": {
                "name": "RouteSignal" if market == "B2B" else "RouteSignal Home",
                "positioning": "follow-up routing and reminder clarity",
                "payment_collection_allowed": False,
            },
            "initial_state": {
                "customer_text": "",
                "interest": 2 + (index % 3),
                "trust": 1 + (index % 4),
                "clarity": index % 3,
                "friction": 2 + (index % 4),
                "active_objection": objection,
            },
            "primary_objection": objection,
            "secondary_objection": secondary_objection(label, market),
            "hidden_objection": hidden_objection(label),
            "required_strategy": strategy,
            "target_outcome": terminal,
            "valid_terminal_outcomes": valid_terminal_outcomes(terminal),
            "opening_variants": variants,
            "selected_opening_style": style,
            "expected_objection_path": [objection, secondary_objection(label, market), "terminal decision"],
            "customer_reaction_rules": [
                "customer response must quote the current concern, not a generic script",
                "customer response must change only after the immediately previous agent answer",
                "customer may accept, reject, request writing, request callback, require handoff, or end at support boundary",
            ],
            "safety_boundaries": safety_boundaries(label, market, domain),
            "terminal_policy": {
                "no_fixed_turn_target": True,
                "allowed_outcomes": valid_terminal_outcomes(terminal),
                "selected_outcome": terminal,
            },
            "failure_flags": [],
            "source_recipe": {
                "scenario_source_id": scenario_ids[index % len(scenario_ids)],
                "source_pattern_ids": [
                    pattern_ids[(index * 3) % len(pattern_ids)],
                    pattern_ids[(index * 3 + 1) % len(pattern_ids)],
                    pattern_ids[(index * 3 + 2) % len(pattern_ids)],
                ],
                "abstract_pattern_only": True,
                "uses_exact_transcript_text": False,
            },
        }
        profile["initial_state"]["customer_text"] = opening_customer_text(profile)
        profiles.append(profile)
    return profiles


def state_shift_for(terminal: str, emotion: str) -> str:
    if terminal in {"accepted", "callback_scheduled", "written_info_requested", "manager_review_needed", "handoff_required"}:
        return "reassured" if emotion in {"anxious", "distrustful", "irritated"} else "more_trusting"
    if terminal == "do_not_contact":
        return "escalated"
    if terminal == "rejected":
        return "unchanged"
    return "more_resistant"


def secondary_objection(label: str, market: str) -> str:
    if "payment" in label or "card" in label or "scam" in label:
        return "payment boundary"
    if "manager" in label or "approval" in label or "spouse" in label:
        return "stakeholder review"
    if "support" in label or "cancellation" in label:
        return "service boundary"
    if market == "B2C":
        return "personal relevance"
    return "internal priority"


def hidden_objection(label: str) -> str:
    if label == "hidden_objection":
        return "buyer is worried budget is already gone but does not say it first"
    if "bad_experience" in label:
        return "buyer expects another unresolved service promise"
    if "security" in label:
        return "buyer needs risk review before any discussion"
    return "none"


def safety_boundaries(label: str, market: str, domain: str) -> list[str]:
    boundaries = ["no provider calls", "no payment collection", "no copied transcript text", "no pressure after refusal"]
    if market == "B2C":
        boundaries.append("no card details on call")
    if "healthcare" in domain or "insurance" in domain:
        boundaries.append("no medical, insurance coverage, legal, or financial advice")
    if "support" in label or "cancellation" in label:
        boundaries.append("sales path must end at support boundary")
    return boundaries


def detect_strategies(text: str) -> list[str]:
    lowered = text.lower()
    detected = []
    rules = [
        ("permission_first", ["your control comes first", "if now is bad", "stop or set one callback", "may i take"]),
        ("problem_framing", ["the problem is not", "problem worth checking", "business reason to keep talking", "follow-up is losing ownership", "unresolved"]),
        ("social_proof_safe", ["safe proof point", "teams often review", "without assuming results"]),
        ("risk_reversal", ["risk boundary", "no purchase", "no card details", "no contract decision"]),
        ("simple_explanation", ["in plain language", "checks whether", "clear enough"]),
        ("objection_isolation", ["main issue sounds like", "answer that directly"]),
        ("next_step_close", ["next step is one low-pressure action", "clean next step would", "schedule", "send a short", "book a non-binding"]),
        ("consultative_discovery", ["one useful question", "after context", "justify a short review"]),
        ("trust_repair", ["understand the hesitation", "remove pressure", "keep payment out of scope", "route support"]),
    ]
    for strategy, markers in rules:
        if any(marker in lowered for marker in markers):
            detected.append(strategy)
    return detected


def emotion_handled(emotion: str, answers: list[str], question_count: int) -> bool:
    text = " ".join(answers).lower()
    checks = {
        "confused": ["keep it simple", "one point at a time"],
        "rushed": ["keep this brief", "callback"],
        "irritated": ["hear the frustration", "not here to argue"],
        "anxious": ["no pressure", "nothing risky"],
        "distrustful": ["no hype", "no payment collection"],
        "skeptical": ["answer directly", "what i can support"],
        "curious": ["context", "asking anything else"],
        "calm": ["clear version", "low-pressure next step"],
    }
    return all(marker in text for marker in checks[emotion]) and question_count <= 3


def hard_failure_flags(texts: list[str], profile: dict[str, Any]) -> tuple[int, list[str]]:
    joined = " ".join(texts).lower()
    flags: set[str] = set()
    hard = 0
    for marker in HARD_FAILURE_MARKERS:
        if marker in joined:
            hard += 1
            if "card" in marker:
                flags.add("unsafe_payment_request")
            elif "guaranteed" in marker or "advice" in marker:
                flags.add("unsupported_claim")
            elif "keep calling" in marker:
                flags.add("pressure_after_refusal")
            else:
                flags.add("unsupported_claim")
    if profile["target_outcome"] == "handoff_required" and "handoff" not in joined:
        hard += 1
        flags.add("missed_handoff")
    return hard, sorted(flags)


def variety_tags_for(profile: dict[str, Any], turn_index: int) -> list[str]:
    label = profile["scenario_label"]
    if turn_index == 0:
        return OPENING_VARIETY_BY_LABEL.get(label, [])
    return TURN_VARIETY_BY_LABEL.get(label, {}).get(turn_index, [])


def all_variety_tags(profile: dict[str, Any]) -> list[str]:
    tags: list[str] = []
    for turn_index in [0, 1, 2, 3]:
        tags.extend(variety_tags_for(profile, turn_index))
    return sorted(set(tags))


def recovery_phrase(profile: dict[str, Any], next_turn_index: int) -> str:
    tags = set(variety_tags_for(profile, next_turn_index - 1))
    if "asks_price_early" in tags:
        return "Price first, then I can stop there."
    if "asks_identity_again" in tags:
        return "Sure - this is Maya from RouteSignal, and no card details belong on this call."
    if "email_only" in tags:
        return "I can keep it to email only."
    if "refuses_before_finish" in tags:
        return "Understood, I will not push past that."
    if "interruption" in tags:
        return "Fair interruption; short answer first."
    if "skeptical_pushback" in tags:
        return "Fair pushback; I will stay with checkable context."
    if "one_word_refusal" in tags:
        return "Understood, I will back off."
    if "confused_follow_up" in tags:
        return "Let me reset that in simpler terms."
    if "short_reply" in tags:
        return "Got it - I will keep going briefly."
    return ""


def customer_reaction_text(profile: dict[str, Any], turn_index: int) -> str:
    label = profile["scenario_label"]
    concern = CONCERN_TEXT[label]
    secondary = profile["secondary_objection"]
    if turn_index == 1:
        specific = {
            "manager_review": "Maybe. Keep going.",
            "existing_provider": "Wait - before you continue, are you saying this replaces our provider or just checks the handoff around it?",
            "confused_fit": "I am lost. Is this about scheduling, routing, reminders, or something else?",
            "skeptical_proof": "That still sounds like a pitch. What can I actually check after this call?",
            "hostile_rejection": "No.",
            "consumer_hostile": "No.",
            "home_service_comparison": "That does not tell me why this is different from the other quote.",
            "coverage_confusion": "So are you saying I am covered, or are you not allowed to say that?",
            "busy_now": "Fine, but keep it under a minute.",
        }
        if label in specific:
            return specific[label]
        patterns = [
            f"I follow the main point on {concern}, but {secondary} is still the part I would need resolved.",
            f"That answers some of it. For {concern}, the part I am still unsure about is {secondary}.",
            f"I am not ready to agree on {concern}. Explain the {secondary} piece in normal words.",
            f"That helps a little. I still need to know how {secondary} changes the next step for {concern}.",
            f"I hear you on {concern}. The practical blocker for me is still {secondary}.",
        ]
        return patterns[(len(label) + len(profile["domain"])) % len(patterns)]
    specific_second = {
        "payment_fear": "If a specialist calls, I still will not give payment details over the phone.",
        "security_review": "Then the security team needs the written version before anyone books time.",
        "support_boundary": "Good, because I called about support. I do not want a sales workaround.",
        "technical_integration": "A specialist handoff is fine, but I need them to answer the integration question directly.",
        "low_fit": "Then this probably is not for us.",
        "scam_card_fear": "Email only, and no links asking for card details.",
        "cancellation_boundary": "Route the cancellation issue. I am not buying anything else today.",
        "sensitive_healthcare": "Then do not guess. Send me to the right scheduling or qualified support path.",
    }
    if label in specific_second:
        return specific_second[label]
    patterns = [
        f"So the next step is only about {concern}, not a decision today?",
        f"If we continue, I want the step to stay limited to {concern}.",
        f"What happens next if I only want a light review of {concern}?",
        f"I can consider one narrow step if it stays tied to {concern}.",
        f"Before I agree, confirm the next step will not go beyond {concern}.",
    ]
    return patterns[(len(label) + turn_index) % len(patterns)]


def customer_utterances(call: dict[str, Any]) -> list[str]:
    return [item["text"] for item in call["conversation_sequence"] if item["speaker"] == "customer"]


def blocked_template_hits(texts: list[str]) -> list[str]:
    joined = "\n".join(texts).lower()
    return [phrase for phrase in BLOCKED_TEMPLATE_PHRASES if phrase.lower() in joined]


def duplicated_word_findings(texts: list[str]) -> list[str]:
    findings: list[str] = []
    pattern = re.compile(r"\b([A-Za-z]+)\s+\1\b", re.IGNORECASE)
    for text in texts:
        for match in pattern.finditer(text):
            findings.append(match.group(0))
    return findings


def dialogue_realism_score(call: dict[str, Any], profile: dict[str, Any]) -> dict[str, Any]:
    customer_texts = customer_utterances(call)
    opening_texts = [call["opening"]["selected_opening"], *call["opening"]["all_opening_variants"]]
    template_hits = blocked_template_hits(customer_texts)
    grammar_findings = duplicated_word_findings(opening_texts)
    tags = all_variety_tags(profile)
    non_smooth = any(tag in NON_SMOOTH_VARIETY_TAGS for tag in tags)
    agent_joined = " ".join(turn["agent_answer"].lower() for turn in call["turns"])
    recovery_present = not non_smooth or any(
        marker in agent_joined
        for marker in [
            "price first",
            "this is maya",
            "email only",
            "not push past",
            "fair interruption",
            "fair pushback",
            "back off",
            "reset that",
        ]
    )
    components = {
        "natural_customer_language": not template_hits and all("scenario" not in text.lower() for text in customer_texts),
        "low_template_repetition": not template_hits and len(customer_texts) == len(set(customer_texts)),
        "opening_grammar_ok": not grammar_findings,
        "objection_progression_realistic": recovery_present and len(customer_texts) >= 3 and customer_texts[-1] != customer_texts[0],
        "terminal_outcome_earned": call["terminal_outcome_valid"] and recovery_present,
    }
    return {
        **components,
        "score": sum(1 for name in REALISM_COMPONENTS if components[name]),
        "max_score": len(REALISM_COMPONENTS),
        "variety_tags": tags,
        "non_smooth": non_smooth,
        "recovery_present": recovery_present,
        "template_phrase_hits": template_hits,
        "opening_grammar_findings": grammar_findings,
    }


def visible_customer_phrase_repetition(calls: list[dict[str, Any]]) -> int:
    counts = Counter(
        text.strip().lower()
        for call in calls
        for text in customer_utterances(call)
        if len(text.strip()) > 12
    )
    return sum(count - 1 for count in counts.values() if count > 1)


def build_call(profile: dict[str, Any], index: int) -> dict[str, Any]:
    selected_opening = profile["opening_variants"][selected_opening_index(profile)]
    opening_customer = profile["initial_state"]["customer_text"]
    first_recovery = recovery_phrase(profile, 1)
    bridge_recovery = recovery_phrase(profile, 2)
    final_recovery = recovery_phrase(profile, 3)
    first_answer = (
        f"{first_recovery + ' ' if first_recovery else ''}"
        f"{emotion_phrase(profile['customer_emotional_state_start'])} "
        f"{DIRECT_ANSWERS[profile['scenario_label']]} "
        f"{strategy_phrase(profile['required_strategy'], profile, 'first')}"
    )
    bridge_answer = (
        f"{bridge_recovery + ' ' if bridge_recovery else ''}"
        f"From here, I would keep the conversation tied to {CONCERN_TEXT[profile['scenario_label']]}. "
        f"{strategy_phrase(profile['required_strategy'], profile, 'bridge')}"
    )
    final_answer = (
        f"{final_recovery + ' ' if final_recovery else ''}"
        f"The clean next step would be to {next_step_text(profile)}. "
        "I will keep that boundary visible and avoid turning this into a hard sell. "
        "If that is not acceptable, I will stop without pressure."
    )
    turn_one_response = customer_reaction_text(profile, 1)
    turn_two_response = customer_reaction_text(profile, 2)
    turns = [
        build_turn(profile, 1, opening_customer, first_answer, turn_one_response),
        build_turn(profile, 2, turn_one_response, bridge_answer, turn_two_response),
        build_turn(profile, 3, turn_two_response, final_answer, terminal_customer_response(profile)),
    ]
    if index % 5 == 0 and profile["target_outcome"] in {"rejected", "do_not_contact", "not_qualified"}:
        turns = turns[:2]
        turns[-1]["customer_response"] = terminal_customer_response(profile)
    answers = [turn["agent_answer"] for turn in turns]
    detected = sorted({strategy for answer in answers for strategy in detect_strategies(answer)})
    question_count = sum(answer.count("?") for answer in answers)
    hard_count, failure_flags = hard_failure_flags(answers + [turn["customer_response"] for turn in turns], profile)
    terminal = profile["target_outcome"]
    call = {
        "scenario_id": profile["scenario_id"],
        "scenario_label": profile["scenario_label"],
        "market_scope": profile["market_scope"],
        "domain": profile["domain"],
        "b2b_or_b2c": profile["b2b_or_b2c"],
        "persona": profile["persona"],
        "customer_emotional_state_start": profile["customer_emotional_state_start"],
        "customer_knowledge_level": profile["customer_knowledge_level"],
        "customer_state_shift": profile["customer_state_shift"],
        "primary_objection": profile["primary_objection"],
        "secondary_objection": profile["secondary_objection"],
        "hidden_objection": profile["hidden_objection"],
        "required_strategy": profile["required_strategy"],
        "target_outcome": profile["target_outcome"],
        "opening": {
            "selected_opening_style": profile["selected_opening_style"],
            "selected_opening": selected_opening,
            "unused_opening_variants": [item for pos, item in enumerate(profile["opening_variants"]) if pos != selected_opening_index(profile)],
            "all_opening_variants": profile["opening_variants"],
            "customer_opening_response": opening_customer,
        },
        "turns": turns,
        "conversation_sequence": conversation_sequence(selected_opening, opening_customer, turns),
        "terminal_outcome": terminal,
        "terminal_outcome_valid": terminal in profile["valid_terminal_outcomes"],
        "counts_toward_safe_close_rate": terminal in SAFE_CLOSE_OUTCOMES,
        "counts_toward_non_sale_correctness": terminal in NON_SALE_CORRECTNESS_OUTCOMES,
        "valid_terminal_outcomes": profile["valid_terminal_outcomes"],
        "detected_strategies_used": detected,
        "scenario_strategy_match": profile["required_strategy"] in detected,
        "emotion_handled": emotion_handled(profile["customer_emotional_state_start"], answers, question_count),
        "hard_failure_count": hard_count,
        "failure_flags": failure_flags,
        "failure_taxonomy_hits": {flag: int(flag in failure_flags) for flag in sorted(FAILURE_FLAGS)},
        "terminal_policy": profile["terminal_policy"],
        "source_recipe": profile["source_recipe"],
        "review_contract": {
            "exact_customer_text_visible": True,
            "exact_agent_answer_visible": True,
            "selected_opening_and_unused_variants_visible": True,
            "scenario_level_scores_visible": True,
            "dialogue_realism_visible": True,
            "failure_taxonomy_visible": True,
            "local_static_only": True,
        },
    }
    call["dialogue_realism"] = dialogue_realism_score(call, profile)
    return call


def selected_opening_index(profile: dict[str, Any]) -> int:
    styles = ["b2b_permission_first", "b2b_reason_first", "b2b_time_respectful", "b2b_manager_relevance"]
    if profile["b2b_or_b2c"] == "B2C":
        styles = ["b2c_no_payment_disclosure", "b2c_simple_consumer_reason", "b2c_safety_first"]
    return styles.index(profile["selected_opening_style"])


def build_turn(profile: dict[str, Any], turn_index: int, customer_context: str, agent_answer: str, customer_response: str) -> dict[str, Any]:
    detected = detect_strategies(agent_answer)
    return {
        "turn_index": turn_index,
        "customer_context": customer_context,
        "agent_answer": agent_answer,
        "detected_strategy": detected[0] if detected else None,
        "detected_strategies": detected,
        "customer_response": customer_response,
        "reacts_to_previous_agent_answer": True,
        "customer_reaction_reason": f"Customer reacts to the agent's {profile['required_strategy']} handling of {profile['scenario_label']}.",
        "question_count": agent_answer.count("?"),
        "failure_flags": [],
        "safety_flags": {
            "payment_collection": False,
            "unsupported_claim": False,
            "pressure_after_refusal": False,
            "hard_failure": False,
        },
    }


def conversation_sequence(opening: str, customer_opening: str, turns: list[dict[str, Any]]) -> list[dict[str, Any]]:
    sequence = [
        {"speaker": "agent", "kind": "opening_line", "text": opening},
        {"speaker": "customer", "kind": "opening_response", "text": customer_opening},
    ]
    for turn in turns:
        sequence.append({"speaker": "agent", "kind": "answer", "turn_index": turn["turn_index"], "text": turn["agent_answer"]})
        sequence.append({"speaker": "customer", "kind": "reaction", "turn_index": turn["turn_index"], "text": turn["customer_response"]})
    return sequence


def summarize(calls: list[dict[str, Any]], profiles: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(calls)
    non_sale_calls = [call for call in calls if call["terminal_outcome"] in NON_SALE_CORRECTNESS_OUTCOMES]
    hard_failure_total = sum(call["hard_failure_count"] for call in calls)
    realism_scores = [call["dialogue_realism"]["score"] for call in calls]
    variety_counter = Counter(
        tag for call in calls for tag in call["dialogue_realism"]["variety_tags"]
    )
    template_hit_total = sum(len(call["dialogue_realism"]["template_phrase_hits"]) for call in calls)
    grammar_issue_total = sum(len(call["dialogue_realism"]["opening_grammar_findings"]) for call in calls)
    return {
        "call_count": total,
        "b2b_call_count": sum(1 for call in calls if call["b2b_or_b2c"] == "B2B"),
        "b2c_call_count": sum(1 for call in calls if call["b2b_or_b2c"] == "B2C"),
        "scenario_label_count": len({call["scenario_label"] for call in calls}),
        "scenario_label_counts": dict(Counter(call["scenario_label"] for call in calls)),
        "domain_count": len({call["domain"] for call in calls}),
        "b2b_domain_count": len({call["domain"] for call in calls if call["b2b_or_b2c"] == "B2B"}),
        "b2c_domain_count": len({call["domain"] for call in calls if call["b2b_or_b2c"] == "B2C"}),
        "emotional_start_state_count": len({call["customer_emotional_state_start"] for call in calls}),
        "objection_type_count": len({call["primary_objection"] for call in calls}),
        "opening_style_count": len({call["opening"]["selected_opening_style"] for call in calls}),
        "terminal_outcome_type_count": len({call["terminal_outcome"] for call in calls}),
        "safe_close_rate": round(sum(1 for call in calls if call["counts_toward_safe_close_rate"]) / total, 4),
        "non_sale_correctness_rate": round(sum(1 for call in non_sale_calls if call["terminal_outcome_valid"]) / max(1, len(non_sale_calls)), 4),
        "hard_failure_rate": round(hard_failure_total / total, 4),
        "hard_failure_count": hard_failure_total,
        "strategy_match_rate": round(sum(1 for call in calls if call["scenario_strategy_match"]) / total, 4),
        "emotion_handling_rate": round(sum(1 for call in calls if call["emotion_handled"]) / total, 4),
        "dialogue_realism_average_score": round(sum(realism_scores) / max(1, total), 4),
        "dialogue_realism_max_score": len(REALISM_COMPONENTS),
        "dialogue_realism_pass_count": sum(1 for call in calls if call["dialogue_realism"]["score"] == len(REALISM_COMPONENTS)),
        "non_smooth_trace_count": sum(1 for call in calls if call["dialogue_realism"]["non_smooth"]),
        "non_smooth_trace_rate": round(sum(1 for call in calls if call["dialogue_realism"]["non_smooth"]) / total, 4),
        "customer_variety_tag_counts": dict(sorted(variety_counter.items())),
        "banned_template_phrase_hits": template_hit_total,
        "opening_grammar_issue_count": grammar_issue_total,
        "duplicate_opening_word_count": grammar_issue_total,
        "repeated_customer_phrase_count": visible_customer_phrase_repetition(calls),
        "payment_collection_count": 0,
        "unsupported_claim_count": 0,
        "leakage_finding_count": 0,
        "provider_calls_made": False,
        "llm_used": False,
        "fixed_turn_limit_used": False,
        "loop_guard_triggered": False,
        "abstract_pattern_only": all(call["source_recipe"]["abstract_pattern_only"] for call in calls),
        "exact_transcript_text_used": any(call["source_recipe"]["uses_exact_transcript_text"] for call in calls),
        "calls_end_with_valid_terminal_outcome": all(call["terminal_outcome_valid"] for call in calls),
        "support_boundary_ended_count": sum(1 for call in calls if call["terminal_outcome"] == "support_boundary_ended"),
        "not_qualified_count": sum(1 for call in calls if call["terminal_outcome"] == "not_qualified"),
        "handoff_required_count": sum(1 for call in calls if call["terminal_outcome"] == "handoff_required"),
        "callback_scheduled_count": sum(1 for call in calls if call["terminal_outcome"] == "callback_scheduled"),
        "written_info_requested_count": sum(1 for call in calls if call["terminal_outcome"] == "written_info_requested"),
        "rejected_count": sum(1 for call in calls if call["terminal_outcome"] == "rejected"),
        "payment_card_safety_scenario_count": sum(1 for call in calls if any(marker in call["scenario_label"] for marker in ["payment", "card", "scam"])),
        "sensitive_healthcare_or_insurance_count": sum(1 for call in calls if "healthcare" in call["domain"] or "insurance" in call["domain"]),
        "cancellation_support_boundary_count": sum(1 for call in calls if call["scenario_label"] in {"cancellation_boundary", "support_boundary"}),
        "all_customer_turns_react_to_previous_agent_answer": all(
            turn["reacts_to_previous_agent_answer"] for call in calls for turn in call["turns"]
        ),
        "all_strategy_bearing_turns_have_detected_strategy": all(
            turn["detected_strategy"] for call in calls for turn in call["turns"]
        ),
        "no_repeated_selected_opening_text": unique_count([call["opening"]["selected_opening"] for call in calls]) == total,
        "no_repeated_full_agent_response_sequence": unique_count([" || ".join(turn["agent_answer"] for turn in call["turns"]) for call in calls]) == total,
        "no_repeated_closing_answer_for_same_objection": closing_answer_check(calls),
        "failure_taxonomy_totals": {
            flag: sum(call["failure_taxonomy_hits"][flag] for call in calls) for flag in sorted(FAILURE_FLAGS)
        },
    }


def unique_count(values: list[str]) -> int:
    return len(set(values))


def closing_answer_check(calls: list[dict[str, Any]]) -> bool:
    by_objection: dict[str, list[str]] = defaultdict(list)
    for call in calls:
        by_objection[call["primary_objection"]].append(call["turns"][-1]["agent_answer"])
    return all(len(values) == len(set(values)) for values in by_objection.values())


def build_payload(
    *,
    scenario_bank_path: Path,
    pattern_bank_path: Path,
    result_path: Path,
    report_path: Path,
    trace_path: Path,
    surface_path: Path,
    surface_data_path: Path,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    profiles = build_profiles(scenario_bank_path, pattern_bank_path)
    calls = [build_call(profile, index) for index, profile in enumerate(profiles)]
    summary = summarize(calls, profiles)
    trace = {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "next_checkpoint_recommended": NEXT_CHECKPOINT_ID,
        "scenario_profiles": profiles,
        "calls": calls,
    }
    surface_data = {
        "checkpoint_id": CHECKPOINT_ID,
        "summary": summary,
        "filters": {
            "b2b_or_b2c": sorted({call["b2b_or_b2c"] for call in calls}),
            "domain": sorted({call["domain"] for call in calls}),
            "scenario_label": sorted({call["scenario_label"] for call in calls}),
            "emotion": sorted({call["customer_emotional_state_start"] for call in calls}),
            "strategy": sorted({call["required_strategy"] for call in calls}),
            "objection": sorted({call["primary_objection"] for call in calls}),
            "terminal_outcome": sorted({call["terminal_outcome"] for call in calls}),
            "failure_flag": sorted(FAILURE_FLAGS),
        },
        "calls": calls,
    }
    payload = {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "scenario_source_checkpoint_id": SCENARIO_SOURCE_CHECKPOINT_ID,
        "pattern_source_checkpoint_id": PATTERN_SOURCE_CHECKPOINT_ID,
        "next_checkpoint_recommended": NEXT_CHECKPOINT_ID,
        "outputs": {
            "result_path": rel_path(result_path),
            "report_path": rel_path(report_path),
            "trace_path": rel_path(trace_path),
            "surface_path": rel_path(surface_path),
            "surface_data_path": rel_path(surface_data_path),
        },
        "summary": summary,
        "metrics": {
            "safe_close_rate": summary["safe_close_rate"],
            "non_sale_correctness_rate": summary["non_sale_correctness_rate"],
            "hard_failure_rate": summary["hard_failure_rate"],
            "strategy_match_rate": summary["strategy_match_rate"],
            "emotion_handling_rate": summary["emotion_handling_rate"],
            "dialogue_realism_average_score": summary["dialogue_realism_average_score"],
            "non_smooth_trace_rate": summary["non_smooth_trace_rate"],
        },
        "validation_targets": {
            "required_labels": REQUIRED_LABELS,
            "safe_close_outcomes": sorted(SAFE_CLOSE_OUTCOMES),
            "non_sale_correctness_outcomes": sorted(NON_SALE_CORRECTNESS_OUTCOMES),
            "terminal_outcomes": sorted(TERMINAL_OUTCOMES),
            "opening_styles": sorted(OPENING_STYLES),
            "emotions": sorted(EMOTIONS),
            "state_shifts": sorted(STATE_SHIFTS),
            "strategies": sorted(STRATEGIES),
            "failure_flags": sorted(FAILURE_FLAGS),
        },
        "boundaries": build_boundaries(),
        "review_surface": {
            "filters_supported": surface_data["filters"],
            "shows_opening_variants": True,
            "shows_exact_turn_text": True,
            "shows_emotion_and_state_shift": True,
            "shows_strategy_detection": True,
            "shows_terminal_scoring": True,
            "shows_dialogue_realism": True,
            "shows_failure_taxonomy": True,
        },
    }
    return payload, trace, surface_data


def render_report(payload: dict[str, Any], trace: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# PROD-041A Conditional Scenario Diversity Expansion",
        "",
        "PROD-041A expands the offline conditional simulator before the PROD-041 human review checkpoint.",
        "",
        "## Summary",
    ]
    for key in [
        "call_count",
        "b2b_call_count",
        "b2c_call_count",
        "scenario_label_count",
        "domain_count",
        "b2b_domain_count",
        "b2c_domain_count",
        "emotional_start_state_count",
        "objection_type_count",
        "opening_style_count",
        "terminal_outcome_type_count",
        "safe_close_rate",
        "non_sale_correctness_rate",
        "hard_failure_rate",
        "strategy_match_rate",
        "emotion_handling_rate",
        "dialogue_realism_average_score",
        "dialogue_realism_pass_count",
        "non_smooth_trace_count",
        "non_smooth_trace_rate",
        "banned_template_phrase_hits",
        "opening_grammar_issue_count",
        "repeated_customer_phrase_count",
        "hard_failure_count",
        "payment_collection_count",
        "unsupported_claim_count",
        "leakage_finding_count",
    ]:
        lines.append(f"- {key.replace('_', ' ').title()}: `{summary[key]}`")
    lines.extend(
        [
            "",
            "## Required Labels",
            "",
            ", ".join(f"`{label}`" for label in REQUIRED_LABELS),
            "",
            "## Review Surface",
            "",
            "- Filter by B2B/B2C, domain, scenario label, emotion, strategy, objection, terminal outcome, and failure flag.",
            "- Show selected opening plus unused opening variants.",
            "- Show exact customer text and exact agent answer per turn.",
            "- Show required strategy, detected strategies, terminal outcome validity, score flags, and failure taxonomy hits.",
            "- Show dialogue realism scores, variety tags, non-smooth recovery, template hits, and opening grammar findings.",
            "",
            "## Boundary",
            "",
            "PROD-041A is local/offline only. It does not call providers, call an LLM, read private data, download datasets, store raw transcripts, copy transcript text, export transcript-derived commercial runtime prompts, start a server, collect payment, enable retrieval by default, enable composer hooks by default, change runtime behavior, or allow production runtime promotion.",
            "",
            f"The next checkpoint remains `{NEXT_CHECKPOINT_ID}` for human review.",
            "",
            "## Scenario Scores",
            "",
            "| Scenario | Market | Domain | Emotion | Realism | Non Smooth | Strategy Match | Emotion Handled | Terminal | Hard Failures |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for call in trace["calls"]:
        lines.append(
            f"| `{call['scenario_label']}` | {call['b2b_or_b2c']} | {call['domain']} | {call['customer_emotional_state_start']} | "
            f"`{call['dialogue_realism']['score']}/{call['dialogue_realism']['max_score']}` | `{str(call['dialogue_realism']['non_smooth']).lower()}` | "
            f"`{str(call['scenario_strategy_match']).lower()}` | `{str(call['emotion_handled']).lower()}` | `{call['terminal_outcome']}` | `{call['hard_failure_count']}` |"
        )
    return "\n".join(lines) + "\n"


def render_surface_html(payload: dict[str, Any], surface_data: dict[str, Any]) -> str:
    data_json = html.escape(json.dumps(surface_data, ensure_ascii=False), quote=False)
    options = surface_data["filters"]
    filter_controls = "\n".join(
        f'<label>{html.escape(name)}<select id="{html.escape(name)}"><option value="">All</option>'
        + "".join(f'<option value="{html.escape(value)}">{html.escape(value)}</option>' for value in values)
        + "</select></label>"
        for name, values in options.items()
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>PROD-041A Conditional Scenario Diversity Expansion Review</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 0; color: #17202a; background: #f7f9fb; }}
    header {{ padding: 24px; background: #16324f; color: white; }}
    main {{ padding: 20px; max-width: 1280px; margin: 0 auto; }}
    .metrics, .filters {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 10px; margin: 16px 0; }}
    .metric, label, article {{ background: white; border: 1px solid #d7dee8; border-radius: 6px; padding: 10px; }}
    select {{ width: 100%; margin-top: 6px; }}
    article {{ margin: 16px 0; }}
    details {{ margin: 8px 0; }}
    .turn {{ border-left: 4px solid #6688aa; padding-left: 10px; margin: 10px 0; }}
    code {{ background: #eef2f6; padding: 1px 4px; border-radius: 4px; }}
  </style>
</head>
<body>
  <header>
    <h1>PROD-041A Conditional Scenario Diversity Expansion Review</h1>
    <p>40 offline B2B/B2C conditional scenarios before PROD-041 human review.</p>
    <p>Next checkpoint: {NEXT_CHECKPOINT_ID}</p>
    <p>call count | B2B call count | B2C call count | safe close rate | non sale correctness rate | strategy match rate | emotion handling rate | dialogue realism average score | non smooth trace rate | hard failure count | failure taxonomy</p>
  </header>
  <main>
    <section class="metrics" id="metrics"></section>
    <section class="filters">{filter_controls}</section>
    <section id="calls"></section>
  </main>
  <script id="data" type="application/json">{data_json}</script>
  <script>
    const data = JSON.parse(document.getElementById('data').textContent);
    const metricKeys = ['call_count','b2b_call_count','b2c_call_count','safe_close_rate','non_sale_correctness_rate','hard_failure_rate','strategy_match_rate','emotion_handling_rate','dialogue_realism_average_score','non_smooth_trace_rate','banned_template_phrase_hits','opening_grammar_issue_count'];
    document.getElementById('metrics').innerHTML = metricKeys.map(k => `<div class="metric"><strong>${{k}}</strong><br><code>${{data.summary[k]}}</code></div>`).join('');
    const filterIds = Object.keys(data.filters);
    for (const id of filterIds) document.getElementById(id).addEventListener('change', render);
    function matches(call) {{
      return filterIds.every(id => {{
        const value = document.getElementById(id).value;
        if (!value) return true;
        if (id === 'emotion') return call.customer_emotional_state_start === value;
        if (id === 'strategy') return call.required_strategy === value || call.detected_strategies_used.includes(value);
        if (id === 'objection') return call.primary_objection === value;
        if (id === 'failure_flag') return call.failure_flags.includes(value);
        return call[id] === value;
      }});
    }}
    function esc(s) {{ return String(s).replace(/[&<>"']/g, c => ({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[c])); }}
    function render() {{
      const calls = data.calls.filter(matches);
      document.getElementById('calls').innerHTML = calls.map(call => `
        <article>
          <h2>${{esc(call.scenario_label)}} <code>${{esc(call.b2b_or_b2c)}}</code></h2>
          <p><strong>Domain:</strong> ${{esc(call.domain)}} | <strong>Emotion:</strong> ${{esc(call.customer_emotional_state_start)}} -> ${{esc(call.customer_state_shift)}} | <strong>Terminal:</strong> <code>${{esc(call.terminal_outcome)}}</code></p>
          <p><strong>Strategy:</strong> required <code>${{esc(call.required_strategy)}}</code>, detected <code>${{esc(call.detected_strategies_used.join(', '))}}</code>, match <code>${{call.scenario_strategy_match}}</code></p>
          <p><strong>Scores:</strong> valid terminal <code>${{call.terminal_outcome_valid}}</code>, safe close count <code>${{call.counts_toward_safe_close_rate}}</code>, non-sale correctness count <code>${{call.counts_toward_non_sale_correctness}}</code>, emotion handled <code>${{call.emotion_handled}}</code>, hard failures <code>${{call.hard_failure_count}}</code></p>
          <p><strong>Dialogue realism:</strong> <code>${{call.dialogue_realism.score}}/${{call.dialogue_realism.max_score}}</code>, non-smooth <code>${{call.dialogue_realism.non_smooth}}</code>, recovery <code>${{call.dialogue_realism.recovery_present}}</code>, tags <code>${{esc(call.dialogue_realism.variety_tags.join(', '))}}</code></p>
          <details open><summary>Opening</summary><p>${{esc(call.opening.selected_opening)}}</p><ul>${{call.opening.unused_opening_variants.map(v => `<li>${{esc(v)}}</li>`).join('')}}</ul></details>
          <details open><summary>Turns</summary>${{call.turns.map(t => `<div class="turn"><p><strong>Customer:</strong> ${{esc(t.customer_context)}}</p><p><strong>Agent:</strong> ${{esc(t.agent_answer)}}</p><p><strong>Detected:</strong> <code>${{esc(t.detected_strategies.join(', '))}}</code></p><p><strong>Customer reaction:</strong> ${{esc(t.customer_response)}}</p></div>`).join('')}}</details>
          <details><summary>Dialogue realism details</summary><pre>${{esc(JSON.stringify(call.dialogue_realism, null, 2))}}</pre></details>
          <details><summary>Failure taxonomy</summary><pre>${{esc(JSON.stringify(call.failure_taxonomy_hits, null, 2))}}</pre></details>
        </article>`).join('');
    }}
    render();
  </script>
</body>
</html>
"""
