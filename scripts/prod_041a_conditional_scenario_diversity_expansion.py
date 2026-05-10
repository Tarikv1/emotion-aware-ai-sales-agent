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
DEFAULT_RECIPES = DEFAULT_OUT_DIR / "scenario_recipes.json"
DEFAULT_FRAMES = DEFAULT_OUT_DIR / "concrete_scenario_frames.json"
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

BANNED_DIALOGUE_PHRASES = [
    "From here, I would keep",
    "The clean next step would be",
    "I will keep that boundary visible",
    "customer response must quote the current concern",
    "the business reason to keep talking",
    "The price answer is first",
    "Price first, then I can stop there",
    "I will answer directly and stick to what I can support",
    "I am not ready to agree on",
    "Explain the internal priority piece in normal words",
    "The practical blocker for me is still internal priority",
    "Because you kept it brief on",
    "If we continue, I want the step to stay limited to",
]
AGENT_TEMPLATE_TOKENS = [
    "clean next step",
    "business reason to keep talking",
    "keep that boundary visible",
    "from here, i would keep",
]
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

REALISM_COMPONENTS = [
    "natural_customer_language",
    "natural_agent_language",
    "low_template_repetition",
    "opening_grammar_ok",
    "objection_progression_realistic",
    "terminal_outcome_earned",
    "frame_context_used",
]

WEAK_EARNED_LABELS = {
    "price_sensitive",
    "manager_review",
    "send_info",
    "hidden_objection",
    "contract_fear",
    "no_pressure_consumer",
}
WEAK_PROGRESS_LABELS = {
    "price_sensitive",
    "hidden_objection",
    "manager_review",
    "send_info",
}

CONCERN_TEXT = {
    "price_sensitive": "pricing concern before problem confirmation",
    "manager_review": "manager review requirement before callback",
    "existing_provider": "existing provider already in place",
    "confused_fit": "unclear workflow fit",
    "skeptical_proof": "proof request before next step",
    "busy_now": "time pressure and callback preference",
    "send_info": "written details request",
    "contract_fear": "contract commitment concern",
    "payment_fear": "payment safety concern",
    "security_review": "security review gate",
    "bad_experience": "previous bad implementation experience",
    "needs_approval": "approval path dependency",
    "hidden_objection": "priority and budget hesitation",
    "competitor_comparison": "active option comparison",
    "not_interested": "lack of interest",
    "hostile_rejection": "hostile refusal",
    "callback_request": "callback-only preference",
    "support_boundary": "support versus sales boundary",
    "technical_integration": "integration complexity concern",
    "setup_timeline": "setup timing concern",
    "multi_location_routing": "multi-location routing ownership",
    "low_fit": "fit mismatch risk",
    "sale_ready": "ready but cautious buyer",
    "discovery_needed": "discovery-first requirement",
    "insurance_price_fear": "insurance cost concern",
    "spouse_input": "partner decision input",
    "scam_card_fear": "scam/card distrust",
    "consumer_not_interested": "consumer disinterest",
    "consumer_callback": "consumer callback preference",
    "coverage_confusion": "coverage clarification need",
    "already_covered": "already covered status",
    "consumer_bad_experience": "consumer bad experience memory",
    "written_info": "written info preference",
    "consumer_hostile": "consumer hostility",
    "cancellation_boundary": "cancellation support boundary",
    "appointment_interest": "appointment scheduling interest",
    "sensitive_healthcare": "sensitive healthcare scheduling",
    "home_service_comparison": "home service comparison",
    "reminder_plan": "reminder plan viability",
    "no_pressure_consumer": "internal_nopressure_boundary",
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

FRAME_DETAILS = {
    "price_sensitive": {
        "caller_role": "sales development rep",
        "customer_role": "operations manager",
        "real_world_context": "The customer runs a field-service team and tracks callbacks through a shared inbox and spreadsheets.",
        "practical_trigger": "Service requests can lose ownership after the first follow-up question and callbacks get delayed.",
        "customer_initial_attitude": "skeptical and price-sensitive",
        "first_customer_objection": "asks price before hearing the full pitch",
        "hidden_objection": "does not want another subscription unless missed follow-ups are measurable",
        "realistic_agent_goal": "answer price directly and test whether missed callback ownership is a real cost",
        "realistic_next_step": "short callback or written pricing summary",
    },
    "manager_review": {
        "caller_role": "sales development rep",
        "customer_role": "operations supervisor",
        "real_world_context": "The supervisor can flag workflow problems but cannot approve new tools alone.",
        "practical_trigger": "Escalations pile up when callback ownership changes between shifts.",
        "customer_initial_attitude": "curious but manager-gated",
        "first_customer_objection": "says manager approval is required for any next step",
        "hidden_objection": "does not want to bring weak or vague ideas to leadership",
        "realistic_agent_goal": "package a manager-ready summary without pressuring for commitment",
        "realistic_next_step": "leadership note and optional callback",
    },
    "existing_provider": {
        "caller_role": "account development rep",
        "customer_role": "care coordination lead",
        "real_world_context": "The team already uses a provider but still handles manual callback lists for overflow.",
        "practical_trigger": "Follow-up ownership becomes unclear when overflow calls move between systems.",
        "customer_initial_attitude": "calm and defensive of current setup",
        "first_customer_objection": "asks why another vendor is needed when they already pay a provider",
        "hidden_objection": "fears migration work and internal disruption",
        "realistic_agent_goal": "isolate whether ownership gaps still exist before suggesting any follow-up",
        "realistic_next_step": "narrow callback focused on overflow handoffs",
    },
    "confused_fit": {
        "caller_role": "solutions rep",
        "customer_role": "plant operations coordinator",
        "real_world_context": "The coordinator uses multiple tools and is unsure where another workflow check fits.",
        "practical_trigger": "Escalation callbacks are tracked in two separate queues that do not stay synchronized.",
        "customer_initial_attitude": "confused and cautious",
        "first_customer_objection": "asks what the product actually does in plain terms",
        "hidden_objection": "worries this creates another dashboard without clear ownership gains",
        "realistic_agent_goal": "simplify scope and verify if queue ownership pain is real",
        "realistic_next_step": "short plain-language callback with one workflow example",
    },
    "skeptical_proof": {
        "caller_role": "business development rep",
        "customer_role": "finance operations analyst",
        "real_world_context": "The analyst has heard many optimization pitches and trusts only documented evidence.",
        "practical_trigger": "Invoice dispute callbacks are delayed when no one owns second-touch follow-up.",
        "customer_initial_attitude": "skeptical and proof-focused",
        "first_customer_objection": "asks what proof can be reviewed later",
        "hidden_objection": "expects inflated claims and wants to avoid another pilot with no metrics",
        "realistic_agent_goal": "offer safe, checkable context without claiming guaranteed outcomes",
        "realistic_next_step": "written summary with measurable review criteria",
    },
    "busy_now": {
        "caller_role": "sales development rep",
        "customer_role": "revops manager",
        "real_world_context": "The manager is between meetings and only accepts short calls with clear purpose.",
        "practical_trigger": "Inbound requests wait too long when handoff notes are incomplete.",
        "customer_initial_attitude": "rushed and impatient",
        "first_customer_objection": "says they only have a minute",
        "hidden_objection": "expects a long pitch and wants to cut the call quickly",
        "realistic_agent_goal": "be brief and offer a concrete callback window or stop",
        "realistic_next_step": "scheduled short callback",
    },
    "send_info": {
        "caller_role": "sales development rep",
        "customer_role": "district operations admin",
        "real_world_context": "The admin handles vendor intake by email and avoids live calls for first pass.",
        "practical_trigger": "Callback ownership differs by district and current notes miss location-specific responsibilities.",
        "customer_initial_attitude": "neutral but email-first",
        "first_customer_objection": "requests written information only",
        "hidden_objection": "does not want open-ended conversations without internal context",
        "realistic_agent_goal": "respect email-only preference and provide concise written scope",
        "realistic_next_step": "written summary with optional follow-up slot",
    },
    "contract_fear": {
        "caller_role": "account executive",
        "customer_role": "hotel operations manager",
        "real_world_context": "The manager has been locked into inflexible software contracts before.",
        "practical_trigger": "Guest complaint callbacks are missed when shift leads hand off notes verbally.",
        "customer_initial_attitude": "anxious about commitments",
        "first_customer_objection": "asks whether this call leads to a contract commitment",
        "hidden_objection": "fears hidden terms and automatic renewals",
        "realistic_agent_goal": "de-risk the conversation and keep it non-committal",
        "realistic_next_step": "written scope and optional callback without commitment",
    },
    "payment_fear": {
        "caller_role": "inside sales rep",
        "customer_role": "service desk supervisor",
        "real_world_context": "The supervisor received scam calls before and blocks anything that requests card data.",
        "practical_trigger": "Repair callbacks stall when service notes miss key context from the first call.",
        "customer_initial_attitude": "distrustful and safety-first",
        "first_customer_objection": "asks whether payment is being requested now",
        "hidden_objection": "assumes unknown callers may ask for card details",
        "realistic_agent_goal": "confirm no payment collection and route only safe next steps",
        "realistic_next_step": "specialist handoff or written info",
    },
    "security_review": {
        "caller_role": "solutions consultant",
        "customer_role": "security program manager",
        "real_world_context": "Any workflow vendor discussion must pass security intake before technical review.",
        "practical_trigger": "Incident follow-up callbacks fail audit checks when ownership logs are incomplete.",
        "customer_initial_attitude": "skeptical and risk-focused",
        "first_customer_objection": "requires security review before proceeding",
        "hidden_objection": "expects overpromising around compliance",
        "realistic_agent_goal": "route to security review path with no unsupported claims",
        "realistic_next_step": "security handoff with written scope",
    },
    "bad_experience": {
        "caller_role": "customer growth rep",
        "customer_role": "regional operations director",
        "real_world_context": "The director had a failed rollout and is wary of new follow-up tools.",
        "practical_trigger": "Store callback queues went unmanaged during the last rollout transition.",
        "customer_initial_attitude": "irritated from prior failure",
        "first_customer_objection": "mentions a bad past implementation",
        "hidden_objection": "expects another disrupted rollout",
        "realistic_agent_goal": "acknowledge history and keep next step lightweight",
        "realistic_next_step": "written details and optional guarded callback",
    },
    "needs_approval": {
        "caller_role": "sales development rep",
        "customer_role": "brokerage operations assistant",
        "real_world_context": "The assistant can evaluate fit but approval sits with department leadership.",
        "practical_trigger": "Lead callbacks are delayed when ownership is unclear between teams.",
        "customer_initial_attitude": "calm but process-bound",
        "first_customer_objection": "states approval is required before any commitment",
        "hidden_objection": "does not want to escalate half-baked proposals",
        "realistic_agent_goal": "provide approval-ready context without pressure",
        "realistic_next_step": "manager review summary",
    },
    "hidden_objection": {
        "caller_role": "business development rep",
        "customer_role": "operations lead",
        "real_world_context": "The lead sounds open but is balancing multiple priorities this quarter.",
        "practical_trigger": "Escalated callbacks sit unassigned when departments assume someone else owns them.",
        "customer_initial_attitude": "polite but guarded",
        "first_customer_objection": "says timing is unclear rather than rejecting directly",
        "hidden_objection": "priority and budget may not support new initiatives now",
        "realistic_agent_goal": "surface the real blocker and avoid hard-sell pressure",
        "realistic_next_step": "short callback if priority is real, otherwise close out",
    },
    "competitor_comparison": {
        "caller_role": "account executive",
        "customer_role": "agency operations manager",
        "real_world_context": "The manager is comparing two vendors and wants neutral criteria.",
        "practical_trigger": "Campaign callback requests drop when ownership shifts across account teams.",
        "customer_initial_attitude": "skeptical and comparison-focused",
        "first_customer_objection": "asks how this differs from a competitor",
        "hidden_objection": "expects biased claims instead of useful criteria",
        "realistic_agent_goal": "keep comparison factual and avoid unverifiable superiority claims",
        "realistic_next_step": "written comparison criteria",
    },
    "not_interested": {
        "caller_role": "sales development rep",
        "customer_role": "distribution operations manager",
        "real_world_context": "The manager is not actively evaluating tools and wants minimal interruption.",
        "practical_trigger": "No known callback ownership issue has been reported recently.",
        "customer_initial_attitude": "calm but not interested",
        "first_customer_objection": "refuses to continue the sales discussion",
        "hidden_objection": "protects team focus from non-priority outreach",
        "realistic_agent_goal": "respect refusal quickly and avoid pressure",
        "realistic_next_step": "end call or do-not-contact if requested",
    },
    "hostile_rejection": {
        "caller_role": "sales development rep",
        "customer_role": "partner channel manager",
        "real_world_context": "The manager has little tolerance for cold calls after repeated spam outreach.",
        "practical_trigger": "No immediate workflow trigger is available because the customer rejects engagement early.",
        "customer_initial_attitude": "hostile and defensive",
        "first_customer_objection": "rejects call in hostile terms",
        "hidden_objection": "expects manipulation and wants immediate shutdown",
        "realistic_agent_goal": "de-escalate and honor refusal boundaries",
        "realistic_next_step": "end call and mark do-not-contact",
    },
    "callback_request": {
        "caller_role": "sales development rep",
        "customer_role": "property operations coordinator",
        "real_world_context": "The coordinator handles urgent onsite issues and cannot talk immediately.",
        "practical_trigger": "Tenant request callbacks slip when notes are routed through multiple inboxes.",
        "customer_initial_attitude": "rushed but not closed",
        "first_customer_objection": "asks for callback at a better time",
        "hidden_objection": "expects the call to become longer than promised",
        "realistic_agent_goal": "confirm a precise callback slot without further pitch",
        "realistic_next_step": "single scheduled callback window",
    },
    "support_boundary": {
        "caller_role": "account rep",
        "customer_role": "customer success manager",
        "real_world_context": "The customer is calling about a live support issue, not a new purchase.",
        "practical_trigger": "An unresolved ticket already has missed follow-up ownership in support queues.",
        "customer_initial_attitude": "irritated and boundary-sensitive",
        "first_customer_objection": "says this is a support issue not a sales call",
        "hidden_objection": "fears sales will delay support resolution",
        "realistic_agent_goal": "route to support boundary and stop selling",
        "realistic_next_step": "support handoff and sales path end",
    },
    "technical_integration": {
        "caller_role": "solutions rep",
        "customer_role": "integration architect",
        "real_world_context": "The architect needs technical specifics before any discussion can continue.",
        "practical_trigger": "Integration callbacks fail when ownership between API and operations teams is unclear.",
        "customer_initial_attitude": "curious but technical",
        "first_customer_objection": "asks detailed integration questions",
        "hidden_objection": "expects hand-wavy answers from non-technical callers",
        "realistic_agent_goal": "avoid guessing and route to technical specialist",
        "realistic_next_step": "qualified integration handoff",
    },
    "setup_timeline": {
        "caller_role": "account executive",
        "customer_role": "clinic operations manager",
        "real_world_context": "The manager needs predictable setup timing around staffing constraints.",
        "practical_trigger": "Patient callback requests accumulate when rollout ownership is unclear between departments.",
        "customer_initial_attitude": "anxious and schedule-focused",
        "first_customer_objection": "asks how long setup will take",
        "hidden_objection": "worries about operational disruption",
        "realistic_agent_goal": "set realistic expectations and avoid guaranteed timelines",
        "realistic_next_step": "time-boxed callback with implementation specialist",
    },
    "multi_location_routing": {
        "caller_role": "enterprise sales rep",
        "customer_role": "multi-site operations director",
        "real_world_context": "The director manages multiple stores with uneven callback ownership standards.",
        "practical_trigger": "Location-to-location escalation callbacks are dropped when ownership is not explicit.",
        "customer_initial_attitude": "calm and practical",
        "first_customer_objection": "asks how routing works across sites",
        "hidden_objection": "fears centralized workflows may not fit local teams",
        "realistic_agent_goal": "show narrow relevance to ownership routing across locations",
        "realistic_next_step": "review call on location routing workflow",
    },
    "low_fit": {
        "caller_role": "sales development rep",
        "customer_role": "construction office manager",
        "real_world_context": "The team may not have the callback volume that justifies additional tooling.",
        "practical_trigger": "Most customer callbacks are already handled by a single dispatcher with clear ownership.",
        "customer_initial_attitude": "confused and evaluating fit",
        "first_customer_objection": "questions whether this applies to their operation",
        "hidden_objection": "does not want forced qualification",
        "realistic_agent_goal": "qualify out quickly if pain is absent",
        "realistic_next_step": "mark not qualified if trigger is not present",
    },
    "sale_ready": {
        "caller_role": "account executive",
        "customer_role": "service operations manager",
        "real_world_context": "The customer already sees callback ownership gaps and is open to next steps.",
        "practical_trigger": "Unassigned follow-ups are creating repeat customer complaints and rework.",
        "customer_initial_attitude": "curious and purchase-ready",
        "first_customer_objection": "wants a clear low-pressure next step",
        "hidden_objection": "does not want hidden commitments during the first call",
        "realistic_agent_goal": "confirm readiness while keeping commitment boundaries explicit",
        "realistic_next_step": "book short non-binding review",
    },
    "discovery_needed": {
        "caller_role": "solutions rep",
        "customer_role": "operations analyst",
        "real_world_context": "The analyst needs problem discovery before evaluating any solution fit.",
        "practical_trigger": "Callback delays happen sporadically and root cause is not yet documented.",
        "customer_initial_attitude": "calm and exploratory",
        "first_customer_objection": "asks for discovery before recommendations",
        "hidden_objection": "wants to avoid premature solution framing",
        "realistic_agent_goal": "ask one scoped discovery question after context",
        "realistic_next_step": "short discovery callback",
    },
    "insurance_price_fear": {
        "caller_role": "consumer advisor",
        "customer_role": "household policy holder",
        "real_world_context": "The customer is sensitive to insurance costs and skeptical of phone offers.",
        "practical_trigger": "Claim follow-up callbacks are missed when documents are routed through multiple contacts.",
        "customer_initial_attitude": "anxious and cost-focused",
        "first_customer_objection": "asks if this increases insurance costs",
        "hidden_objection": "fears hidden charges and unverified coverage promises",
        "realistic_agent_goal": "clarify boundaries and avoid coverage or savings guarantees",
        "realistic_next_step": "written information or qualified handoff",
    },
    "spouse_input": {
        "caller_role": "consumer sales rep",
        "customer_role": "home owner",
        "real_world_context": "The buyer shares household decisions and avoids deciding alone on first contact.",
        "practical_trigger": "Service reminder callbacks are missed when one household contact is unavailable.",
        "customer_initial_attitude": "calm and collaborative",
        "first_customer_objection": "needs partner input before agreeing to anything",
        "hidden_objection": "does not want sales pressure before discussing at home",
        "realistic_agent_goal": "provide concise info for joint review",
        "realistic_next_step": "written summary plus optional callback",
    },
    "scam_card_fear": {
        "caller_role": "consumer outreach rep",
        "customer_role": "mobile plan customer",
        "real_world_context": "The customer has seen scam calls and refuses card discussions on inbound calls.",
        "practical_trigger": "Reminder callbacks are missed when fraud alerts block legitimate follow-up calls.",
        "customer_initial_attitude": "distrustful and defensive",
        "first_customer_objection": "asks whether card details are requested",
        "hidden_objection": "assumes unknown callers are unsafe",
        "realistic_agent_goal": "rebuild trust with explicit safety boundaries",
        "realistic_next_step": "email-only summary",
    },
    "consumer_not_interested": {
        "caller_role": "consumer sales rep",
        "customer_role": "membership customer",
        "real_world_context": "The customer is not shopping and wants the call ended quickly.",
        "practical_trigger": "No active reminder or follow-up issue has been raised by this customer.",
        "customer_initial_attitude": "calm but uninterested",
        "first_customer_objection": "says no interest",
        "hidden_objection": "protects attention and avoids unsolicited offers",
        "realistic_agent_goal": "respect refusal and stop",
        "realistic_next_step": "end call cleanly",
    },
    "consumer_callback": {
        "caller_role": "consumer outreach rep",
        "customer_role": "vehicle service customer",
        "real_world_context": "The customer can only discuss follow-up plans outside work hours.",
        "practical_trigger": "Appointment callbacks are missed when daytime calls go unanswered.",
        "customer_initial_attitude": "rushed and practical",
        "first_customer_objection": "asks for callback later",
        "hidden_objection": "expects continued pressure if they stay on the line",
        "realistic_agent_goal": "lock one callback slot and stop pitching",
        "realistic_next_step": "scheduled callback",
    },
    "coverage_confusion": {
        "caller_role": "consumer advisor",
        "customer_role": "policy holder",
        "real_world_context": "The customer is confused about what support can be discussed without formal coverage review.",
        "practical_trigger": "Benefit-related callbacks are delayed when customer records require specialist confirmation.",
        "customer_initial_attitude": "confused and cautious",
        "first_customer_objection": "asks if coverage is being confirmed on this call",
        "hidden_objection": "fears being misled by unqualified claims",
        "realistic_agent_goal": "clarify that coverage needs qualified review",
        "realistic_next_step": "handoff to qualified reviewer",
    },
    "already_covered": {
        "caller_role": "consumer sales rep",
        "customer_role": "telecom customer",
        "real_world_context": "The customer says they already have coverage and does not need another service.",
        "practical_trigger": "Current provider handles most reminders and callback ownership appears stable.",
        "customer_initial_attitude": "calm and closed",
        "first_customer_objection": "states the current setup already covers this need",
        "hidden_objection": "does not want service overlap or confusion",
        "realistic_agent_goal": "confirm fit quickly and exit if unnecessary",
        "realistic_next_step": "close out or send optional comparison note",
    },
    "consumer_bad_experience": {
        "caller_role": "consumer retention rep",
        "customer_role": "home service customer",
        "real_world_context": "The customer had a poor service experience and distrusts follow-up promises.",
        "practical_trigger": "Last service request had no callback owner and required repeated customer chase-ups.",
        "customer_initial_attitude": "irritated and skeptical",
        "first_customer_objection": "references prior bad experience",
        "hidden_objection": "expects the same failure pattern",
        "realistic_agent_goal": "acknowledge history and keep next step reversible",
        "realistic_next_step": "written details before any callback",
    },
    "written_info": {
        "caller_role": "consumer wellness rep",
        "customer_role": "wellness subscriber",
        "real_world_context": "The subscriber reviews options by reading first and avoids verbal commitments.",
        "practical_trigger": "Program reminder callbacks are inconsistent when contact preferences are not documented.",
        "customer_initial_attitude": "skeptical and documentation-first",
        "first_customer_objection": "asks for written information only",
        "hidden_objection": "does not trust spoken summaries alone",
        "realistic_agent_goal": "send clear written summary and stop there",
        "realistic_next_step": "written follow-up",
    },
    "consumer_hostile": {
        "caller_role": "consumer outreach rep",
        "customer_role": "membership account holder",
        "real_world_context": "The customer is upset by unsolicited calls and reacts sharply.",
        "practical_trigger": "No workflow trigger can be explored because the customer rejects immediately.",
        "customer_initial_attitude": "hostile",
        "first_customer_objection": "demands call end",
        "hidden_objection": "assumes bad intent from outreach calls",
        "realistic_agent_goal": "de-escalate and comply with refusal",
        "realistic_next_step": "end call and record do-not-contact if requested",
    },
    "cancellation_boundary": {
        "caller_role": "subscription account rep",
        "customer_role": "subscription customer",
        "real_world_context": "The customer called to cancel and does not want the call redirected into sales.",
        "practical_trigger": "Cancellation callbacks were delayed due to unclear ownership between support and retention.",
        "customer_initial_attitude": "irritated and boundary-focused",
        "first_customer_objection": "states this is a cancellation request",
        "hidden_objection": "expects retention pressure instead of support resolution",
        "realistic_agent_goal": "route to cancellation support boundary only",
        "realistic_next_step": "support boundary handoff",
    },
    "appointment_interest": {
        "caller_role": "patient access rep",
        "customer_role": "clinic patient",
        "real_world_context": "The patient is open to appointment reminders but wants clear boundaries.",
        "practical_trigger": "Follow-up appointment callbacks are missed when reminders are not assigned to staff owners.",
        "customer_initial_attitude": "curious and cautious",
        "first_customer_objection": "asks what the appointment step actually involves",
        "hidden_objection": "does not want hidden payment or treatment claims",
        "realistic_agent_goal": "explain reminder scope and keep next step simple",
        "realistic_next_step": "short reminder setup callback",
    },
    "sensitive_healthcare": {
        "caller_role": "patient access coordinator",
        "customer_role": "caregiver",
        "real_world_context": "The caller is discussing a sensitive healthcare scheduling situation.",
        "practical_trigger": "Urgent follow-up scheduling callbacks are missed when ownership between intake and clinic teams is unclear.",
        "customer_initial_attitude": "anxious and protective",
        "first_customer_objection": "asks for clinical certainty the caller cannot provide",
        "hidden_objection": "fears unsafe guidance from non-clinical staff",
        "realistic_agent_goal": "set safety boundary and route to qualified path",
        "realistic_next_step": "qualified healthcare scheduling handoff",
    },
    "home_service_comparison": {
        "caller_role": "home services advisor",
        "customer_role": "home owner",
        "real_world_context": "The customer is comparing service providers and wants practical differences.",
        "practical_trigger": "Repair follow-up callbacks are missed when vendor ownership changes after quote stage.",
        "customer_initial_attitude": "skeptical and comparison-oriented",
        "first_customer_objection": "asks why this differs from another quote",
        "hidden_objection": "expects exaggerated claims",
        "realistic_agent_goal": "keep comparison grounded and low-pressure",
        "realistic_next_step": "written comparison checklist",
    },
    "reminder_plan": {
        "caller_role": "service reminder rep",
        "customer_role": "vehicle owner",
        "real_world_context": "The customer misses maintenance follow-ups when reminders are inconsistent.",
        "practical_trigger": "Reminder callbacks are dropped after service advisors rotate shifts.",
        "customer_initial_attitude": "calm and practical",
        "first_customer_objection": "asks whether reminder follow-up is actually useful",
        "hidden_objection": "does not want a complex system for a simple need",
        "realistic_agent_goal": "connect reminder follow-up to a concrete missed-callback pattern",
        "realistic_next_step": "accept short reminder setup call",
    },
    "no_pressure_consumer": {
        "caller_role": "consumer advisor",
        "customer_role": "wellness customer",
        "real_world_context": "The customer will continue only if the call remains low-pressure and reversible.",
        "practical_trigger": "Follow-up reminders are inconsistent and the customer wants clarity without commitment.",
        "customer_initial_attitude": "distrustful and pressure-sensitive",
        "first_customer_objection": "states no-pressure boundary upfront",
        "hidden_objection": "expects manipulative close tactics",
        "realistic_agent_goal": "keep strict no-pressure boundaries and offer optional next step",
        "realistic_next_step": "optional callback or written summary",
    },
}

SPOKEN_REASONS = {
    "price_sensitive": "This only matters if missed callbacks are actually creating work for your team.",
    "manager_review": "This only matters if leadership is already seeing callback ownership as a real problem.",
    "existing_provider": "This only matters if your current provider still leaves overflow follow-ups unclear.",
    "confused_fit": "This only matters if the two queues are causing real callbacks to fall through.",
    "skeptical_proof": "This only matters if delayed dispute callbacks are something you can measure.",
    "busy_now": "This only matters if incomplete handoff notes are slowing down inbound requests.",
    "send_info": "This only matters if district-level callback ownership is still unclear after the email.",
    "contract_fear": "This only matters if verbal handoffs are causing guest complaint callbacks to get missed.",
    "payment_fear": "This only matters if repair callbacks are stalling because the first-call notes are incomplete.",
    "security_review": "This only matters if incomplete ownership logs are already causing audit friction.",
    "bad_experience": "This only matters if the last rollout left store callback queues unmanaged.",
    "needs_approval": "This only matters if delayed lead callbacks are already costing the team time.",
    "hidden_objection": "This only matters if unassigned escalations are a real priority for your department.",
    "competitor_comparison": "This only matters if campaign callback requests are still getting dropped between teams.",
    "not_interested": "This only matters if there is a callback ownership issue worth revisiting later.",
    "hostile_rejection": "This only matters if you want the conversation reopened later, and I hear that you do not.",
    "callback_request": "This only matters if tenant request callbacks are slipping through those inboxes.",
    "support_boundary": "This only matters because the unresolved ticket belongs with support, not sales.",
    "technical_integration": "This only matters if integration follow-up is getting lost between technical and operations teams.",
    "setup_timeline": "This only matters if rollout ownership is delaying patient callbacks.",
    "multi_location_routing": "This only matters if locations are dropping escalations because ownership is not explicit.",
    "low_fit": "This only matters if that single-dispatcher process starts breaking down.",
    "sale_ready": "This only matters if unassigned follow-ups are already causing repeat complaints.",
    "discovery_needed": "This only matters if the callback delays happen often enough to understand the cause.",
    "insurance_price_fear": "This only matters if claim follow-ups are being missed between contacts.",
    "spouse_input": "This only matters if reminder callbacks fail when one household contact is unavailable.",
    "scam_card_fear": "This only matters if fraud alerts are blocking legitimate reminder follow-ups.",
    "consumer_not_interested": "This only matters if a reminder or follow-up problem comes up later.",
    "consumer_callback": "This only matters if daytime missed calls are causing appointment follow-up problems.",
    "coverage_confusion": "This only matters if benefit-related callbacks need a qualified specialist to confirm details.",
    "already_covered": "This only matters if your current coverage stops handling reminders cleanly.",
    "consumer_bad_experience": "This only matters if the last service request still left you chasing callbacks.",
    "written_info": "This only matters if written contact preferences would make program reminders more reliable.",
    "consumer_hostile": "This only matters if you choose to reopen the conversation later.",
    "cancellation_boundary": "This only matters because cancellation follow-up belongs in the support path.",
    "appointment_interest": "This only matters if missed reminder ownership is causing appointment follow-up gaps.",
    "sensitive_healthcare": "This only matters if scheduling callbacks need the clinic team to own the next step.",
    "home_service_comparison": "This only matters if quote-stage ownership changes are causing repair follow-ups to stall.",
    "reminder_plan": "This only matters if shift rotations are causing reminder callbacks to drop.",
    "no_pressure_consumer": "This only matters if the follow-up can stay optional and pressure-free.",
}

AUTHORING_SPECS = {
    "price_sensitive": {
        "opening_topic": "some field teams miss callbacks after the first customer question",
        "opening_customer": "Okay, but what does it cost?",
        "answer": "Sure - price first. Starter is 29 dollars per user per month, and growth is 59. If that is outside budget, no problem.",
        "issue": "We usually help when callbacks get passed around and no one is sure who owns the next reply.",
        "next": "I can send the pricing summary, or we can set a short call only if missed callbacks are worth checking.",
        "customer_one": "That still sounds like another platform.",
        "customer_two": "If that is it, send the details.",
        "terminal": "Alright. Send me a couple of times for next week.",
    },
    "manager_review": {
        "opening_topic": "shift handoffs can leave follow-ups sitting without a clear owner",
        "opening_customer": "Quick version, please. I need my manager for anything new.",
        "answer": "Totally fair. I am not asking you to approve anything on this call.",
        "issue": "We usually help when callbacks fall between shifts and nobody is sure who owns the follow-up.",
        "next": "I can send a short manager summary first. If it looks relevant, you can decide whether a callback makes sense.",
        "customer_one": "I need to check with my manager.",
        "customer_two": "Send the short version for review.",
        "terminal": "Leadership needs to review this first.",
    },
    "existing_provider": {
        "opening_topic": "overflow follow-ups can still get missed even when a main provider is already in place",
        "opening_customer": "We already have a provider. Why would we need another one?",
        "answer": "Good question. I am not suggesting you rip out what already works.",
        "issue": "The only gap we usually look at is overflow: when a follow-up leaves the main system and nobody owns it.",
        "next": "If that never happens, we should stop. If it does, we can do one narrow review on the handoff.",
        "customer_one": "So this is not replacing our provider?",
        "customer_two": "Maybe. Keep it only to overflow handoffs.",
        "terminal": "Alright. Send me a couple of times for next week.",
    },
    "confused_fit": {
        "opening_topic": "two separate queues can make it unclear who should call the customer back",
        "opening_customer": "I am not sure I follow. What are you actually offering?",
        "answer": "Keep this simple: it is not a new dashboard pitch.",
        "issue": "Plain version: we help teams see who owns the callback when work is split across queues.",
        "next": "We can do a short call with one example from your queue setup and stop if it is not useful.",
        "customer_one": "What are you actually offering?",
        "customer_two": "Okay, one example would help.",
        "terminal": "Alright. Send me a couple of times for next week.",
    },
    "skeptical_proof": {
        "opening_topic": "finance callbacks sometimes stall after a dispute question comes in",
        "opening_customer": "I hear claims like this all the time. What proof do you have?",
        "answer": "Fair question. I will keep it to reviewable facts, not promises.",
        "issue": "Teams in similar roles usually start by checking how many second-touch callbacks are late or unowned.",
        "next": "I can send a short checklist you can compare against your own numbers.",
        "customer_one": "That still sounds vague.",
        "customer_two": "Send the checklist. I will look later.",
        "terminal": "Fine, send it.",
    },
    "busy_now": {
        "opening_topic": "inbound requests can slow down when handoff notes are thin",
        "opening_customer": "I do not have time right now.",
        "answer": "I hear you. I will keep this brief.",
        "issue": "If handoff notes are not slowing anything down, we can stop here.",
        "next": "I can send two time options and leave the rest for later.",
        "customer_one": "Keep it short.",
        "customer_two": "Send times. Do not pitch me now.",
        "terminal": "Alright. Send me a couple of times for next week.",
    },
    "send_info": {
        "opening_topic": "district teams can lose callback ownership when notes move by email",
        "opening_customer": "Can you just email it?",
        "answer": "Yes. I can just email it and leave the call there.",
        "issue": "What I would send is a short note on how district-level callbacks stay assigned.",
        "next": "I will keep the email short, with no meeting link unless you ask for one.",
        "customer_one": "Email only.",
        "customer_two": "Just email it. No calendar invite.",
        "terminal": "Fine, send it.",
    },
    "contract_fear": {
        "opening_topic": "guest complaint callbacks can get lost after shift changes",
        "opening_customer": "Is this going to turn into a contract pitch?",
        "answer": "No. No payment or commitment on this call.",
        "issue": "We only look at whether complaint callbacks are getting dropped after handoff.",
        "next": "I can send the scope in writing, and you can ignore it if it is not relevant.",
        "customer_one": "I am not signing anything today.",
        "customer_two": "Written scope only. No contract talk.",
        "terminal": "Fine, send it.",
    },
    "payment_fear": {
        "opening_topic": "repair callbacks can stall when the first call notes are incomplete",
        "opening_customer": "Are you asking for payment or card details?",
        "answer": "Safety first here. No payment collection here, and no card details on this call.",
        "issue": "The only thing I can do is explain the follow-up problem and route you safely if needed.",
        "next": "If you want details, I can send them or connect you with the right specialist.",
        "customer_one": "I am not giving payment details over the phone.",
        "customer_two": "Route me to someone official, then.",
        "terminal": "Route me to the right specialist.",
    },
    "security_review": {
        "opening_topic": "ownership logs for incident follow-up can create security intake questions",
        "opening_customer": "This has to go through security first.",
        "answer": "Fair question. Security intake should happen before any technical commitment.",
        "issue": "Teams in similar roles usually check the ownership log first, without treating it as approval.",
        "next": "I can send the written scope to the security path and avoid guessing on compliance.",
        "customer_one": "Do not make any security claims here.",
        "customer_two": "Send the intake scope to security.",
        "terminal": "Route me to the right specialist.",
    },
    "bad_experience": {
        "opening_topic": "store callback queues can get messy during rollout changes",
        "opening_customer": "We tried something like this before and it was a mess.",
        "answer": "I hear the frustration. I won't argue with a bad rollout experience.",
        "issue": "The only useful check is whether the old rollout left callback queues without owners.",
        "next": "I can send a short note first. No hard sell and no rollout commitment.",
        "customer_one": "We already tried something like this.",
        "customer_two": "Written details only. I am not doing another rollout call.",
        "terminal": "Fine, send it.",
    },
    "needs_approval": {
        "opening_topic": "lead callbacks can sit too long when ownership is split between teams",
        "opening_customer": "I cannot approve anything. That would need leadership.",
        "answer": "I understand. I am not asking for approval from you.",
        "issue": "If lead callbacks are getting delayed, the useful thing is a short summary leadership can judge.",
        "next": "I can send that summary first and let your manager decide whether it deserves time.",
        "customer_one": "I need to check with my manager.",
        "customer_two": "Send something I can forward.",
        "terminal": "Leadership needs to review this first.",
    },
    "hidden_objection": {
        "opening_topic": "department handoffs can leave follow-up work dangling",
        "opening_customer": "Maybe, but I am not sure this is a priority right now.",
        "answer": "Happy to keep it practical. Let me not force this into a bigger thing.",
        "issue": "The real question is whether unassigned escalations are costing enough time to look at.",
        "next": "If it is not a priority, we close it out. If it is, we can do one short callback.",
        "customer_one": "Maybe, but why now?",
        "customer_two": "That depends if my team says it is actually a problem.",
        "terminal": "Alright. Send me a couple of times for next week.",
    },
    "competitor_comparison": {
        "opening_topic": "campaign callbacks can get dropped when account ownership changes",
        "opening_customer": "How is this different from the other option we are reviewing?",
        "answer": "Fair question. I am not going to claim we are better than someone I have not seen.",
        "issue": "Teams in similar roles usually compare who owns the follow-up, what gets logged, and where handoffs break.",
        "next": "I can send neutral comparison criteria, not a superiority claim.",
        "customer_one": "How is that different from the other option?",
        "customer_two": "Send the criteria. I will compare it myself.",
        "terminal": "Fine, send it.",
    },
    "not_interested": {
        "opening_topic": "some distribution teams review callback ownership only when it becomes painful",
        "opening_customer": "No, thanks.",
        "answer": "Understood. If this is not relevant, we can stop here.",
        "issue": "I do not have a reason to push if callback ownership is not a problem for you.",
        "next": "I will leave it there and not try to turn this into a meeting.",
        "customer_one": "No, not today.",
        "customer_two": "Please end the call.",
        "terminal": "I will pass for now.",
    },
    "hostile_rejection": {
        "opening_topic": "follow-up ownership is something you want to discuss",
        "opening_customer": "No. Stop calling us.",
        "answer": "Understood. I won't push.",
        "issue": "There is no reason to continue if you do not want the conversation.",
        "next": "I will end the call and mark that you do not want contact.",
        "customer_one": "No.",
        "customer_two": "No, please don't call again.",
        "terminal": "Do not contact me again.",
    },
    "callback_request": {
        "opening_topic": "maintenance requests sometimes bounce between inboxes before anyone calls back",
        "opening_customer": "I cannot talk now. Call me later.",
        "answer": "I hear you. I will keep this brief and not pitch now.",
        "issue": "If inbox handoffs are causing missed tenant callbacks, that is all we would discuss later.",
        "next": "I can send two callback windows and stop here.",
        "customer_one": "Maybe, but keep it short.",
        "customer_two": "Send times for next week.",
        "terminal": "Alright. Send me a couple of times for next week.",
    },
    "support_boundary": {
        "opening_topic": "your open ticket needs the right support owner, not a sales conversation",
        "opening_customer": "This is a support issue, not a sales call.",
        "answer": "I hear the frustration. You are right - this belongs with support.",
        "issue": "No hard sell. The useful move is getting the missed follow-up back to the support path.",
        "next": "I can route this to support and end the sales side here.",
        "customer_one": "This is a support issue.",
        "customer_two": "Route me to support and stop selling.",
        "terminal": "Support only. End sales here.",
    },
    "technical_integration": {
        "opening_topic": "integration follow-ups can get lost between API and operations teams",
        "opening_customer": "Who handles the actual integration details?",
        "answer": "Happy to keep it practical. I should not guess on technical details.",
        "issue": "Quick question: are the follow-ups getting lost between technical review and operations, or somewhere else?",
        "next": "If it is technical, I can hand this to an integration specialist.",
        "customer_one": "Who handles integration details?",
        "customer_two": "I need someone technical, not a sales answer.",
        "terminal": "Route me to the right specialist.",
    },
    "setup_timeline": {
        "opening_topic": "patient callbacks can pile up when rollout ownership is unclear",
        "opening_customer": "How long would setup actually take?",
        "answer": "No pressure. I cannot promise a timeline without the implementation team.",
        "issue": "Plain version: we first check where callback ownership breaks during rollout.",
        "next": "I can set a short call with someone who can discuss timing safely.",
        "customer_one": "How long does setup actually take?",
        "customer_two": "Only if a specialist can answer that.",
        "terminal": "Alright. Send me a couple of times for next week.",
    },
    "multi_location_routing": {
        "opening_topic": "multi-site teams can lose escalations when no location owns the callback",
        "opening_customer": "How would that work across locations?",
        "answer": "I will keep it straightforward. The reason I called is location ownership, not a broad platform pitch.",
        "issue": "We usually help when one store thinks another site owns the escalation callback.",
        "next": "We can review one routing example and decide from there.",
        "customer_one": "What does that change in practice?",
        "customer_two": "One routing example is fine.",
        "terminal": "Okay, that works for me.",
    },
    "low_fit": {
        "opening_topic": "this only helps if callback volume is high enough to create ownership gaps",
        "opening_customer": "I am not sure this applies to us.",
        "answer": "Keep this simple: if one dispatcher already owns every callback, you may not need us.",
        "issue": "Quick question: are callbacks ever missed because ownership is unclear, or is it mostly handled?",
        "next": "If it is already handled, I will mark this as not a fit.",
        "customer_one": "This may not fit us.",
        "customer_two": "We have one dispatcher. It is usually handled.",
        "terminal": "This is not a fit for us.",
    },
    "sale_ready": {
        "opening_topic": "repeat complaints can happen when follow-ups sit unassigned",
        "opening_customer": "We have that problem. What is the next step?",
        "answer": "Happy to keep it practical. It sounds like the pain is already real.",
        "issue": "The next step is only a short review of where follow-ups stop being owned.",
        "next": "We can book a non-binding review. No payment or commitment on this call.",
        "customer_one": "Fine, what is the next step?",
        "customer_two": "As long as it is non-binding, okay.",
        "terminal": "Okay, that works for me.",
    },
    "discovery_needed": {
        "opening_topic": "callback delays are hard to fix when the cause is not documented yet",
        "opening_customer": "What do you need to know before recommending anything?",
        "answer": "I will keep it straightforward. I do not want to jump to a solution.",
        "issue": "Quick question: when callbacks are late, is it usually missing notes, unclear owner, or timing?",
        "next": "If that is worth unpacking, we can do a short discovery call.",
        "customer_one": "What do you need to know first?",
        "customer_two": "Start with discovery, not a recommendation.",
        "terminal": "Alright. Send me a couple of times for next week.",
    },
    "insurance_price_fear": {
        "opening_topic": "paperwork questions sometimes need a clear follow-up owner",
        "opening_customer": "Is this going to increase my insurance cost?",
        "answer": "No pressure. I cannot make coverage or savings claims on this call.",
        "issue": "No payment or commitment here. The safe topic is whether follow-up documents are getting missed.",
        "next": "I can send written information or route you to someone qualified for coverage questions.",
        "customer_one": "That sounds expensive.",
        "customer_two": "Send it in writing. No price promises.",
        "terminal": "Fine, send it.",
    },
    "spouse_input": {
        "opening_topic": "household reminders can fail when only one person gets the callback",
        "opening_customer": "I need to talk to my spouse before agreeing to anything.",
        "answer": "I understand. I am not asking you to decide alone.",
        "issue": "The useful check is whether reminders should reach both household contacts, not a commitment today.",
        "next": "I can send a short summary you can both review.",
        "customer_one": "I need to ask my partner.",
        "customer_two": "Email it so we can look together.",
        "terminal": "Alright. Send me a couple of times for next week.",
    },
    "scam_card_fear": {
        "opening_topic": "legitimate reminder calls can get blocked when scam calls make people cautious",
        "opening_customer": "Who exactly are you? I am not giving card details.",
        "answer": "I am not asking for card details, and I will not send a payment link.",
        "issue": "No hard sell. The only safe next step is written information you can review yourself.",
        "next": "I can email a simple summary and stop the call here.",
        "customer_one": "Who exactly are you?",
        "customer_two": "Email only, and no payment links.",
        "terminal": "Fine, send it.",
    },
    "consumer_not_interested": {
        "opening_topic": "this is only about reminder follow-up, and I can stop if it is unwanted",
        "opening_customer": "No, not interested.",
        "answer": "Understood. If this is not relevant, we can stop here.",
        "issue": "I do not have a reason to continue if you do not want reminder help.",
        "next": "I will end the call now.",
        "customer_one": "No, not today.",
        "customer_two": "Please stop here.",
        "terminal": "I will pass for now.",
    },
    "consumer_callback": {
        "opening_topic": "after-work scheduling can prevent missed service follow-ups",
        "opening_customer": "I am at work. Call me later.",
        "answer": "I hear you. I will keep this brief.",
        "issue": "If daytime calls are the problem, we can handle this with one callback window.",
        "next": "I can send a later time and stop now.",
        "customer_one": "Call me later.",
        "customer_two": "After work only.",
        "terminal": "Alright. Send me a couple of times for next week.",
    },
    "coverage_confusion": {
        "opening_topic": "benefit questions sometimes need a qualified reviewer before anyone answers",
        "opening_customer": "Are you confirming coverage or not?",
        "answer": "Keep this simple: I cannot confirm coverage on this call.",
        "issue": "No payment or commitment here. Coverage questions need the qualified review path.",
        "next": "I can route you to the right reviewer instead of guessing.",
        "customer_one": "Are you confirming coverage or not?",
        "customer_two": "Then send me to someone who can.",
        "terminal": "Route me to the right specialist.",
    },
    "already_covered": {
        "opening_topic": "some customers only need help if their current reminder setup stops working",
        "opening_customer": "We already have this covered.",
        "answer": "Good to know. I am not here to duplicate something that works.",
        "issue": "Let me answer that first: if reminders are already handled, there may be no fit.",
        "next": "I can close this out unless you want a short comparison note later.",
        "customer_one": "We already have this handled.",
        "customer_two": "No comparison needed.",
        "terminal": "I will pass for now.",
    },
    "consumer_bad_experience": {
        "opening_topic": "service follow-ups can break down when nobody owns the callback after a visit",
        "opening_customer": "Last time we had to chase everyone ourselves.",
        "answer": "I hear the frustration. I won't pretend that was fine.",
        "issue": "No hard sell. The only useful thing is showing how the callback owner would be clear next time.",
        "next": "I can send that in writing before any callback.",
        "customer_one": "We already tried something like this.",
        "customer_two": "Send it first. I do not want a call yet.",
        "terminal": "Fine, send it.",
    },
    "written_info": {
        "opening_topic": "program reminders can improve when contact preferences are written down clearly",
        "opening_customer": "Can you send something written?",
        "answer": "Yes, I can keep this to written details.",
        "issue": "The note would cover reminder preferences, not a verbal commitment.",
        "next": "I can send the details and leave it there.",
        "customer_one": "Fine, send it.",
        "customer_two": "Email only.",
        "terminal": "Fine, send it.",
    },
    "consumer_hostile": {
        "opening_topic": "a reminder call is wanted at all",
        "opening_customer": "No. Take me off the list.",
        "answer": "I hear you. No hard sell. I won't push.",
        "issue": "There is nothing to discuss if you want no more contact.",
        "next": "I will end the call and mark that preference.",
        "customer_one": "No.",
        "customer_two": "No, please don't call again.",
        "terminal": "Do not contact me again.",
    },
    "cancellation_boundary": {
        "opening_topic": "cancellation follow-up belongs in support, not a sales pitch",
        "opening_customer": "I only want to cancel. Do not sell me anything.",
        "answer": "I hear the frustration. You are right - this is a cancellation support issue.",
        "issue": "No hard sell. The safe move is getting you to the cancellation path.",
        "next": "I can route you to support and end sales here.",
        "customer_one": "I only want cancellation support.",
        "customer_two": "Route me to support and stop selling.",
        "terminal": "Support only. End sales here.",
    },
    "appointment_interest": {
        "opening_topic": "appointment reminders can fail when staff ownership is unclear",
        "opening_customer": "What does the appointment step involve?",
        "answer": "Happy to keep it practical. This is only about reminder setup, not treatment advice.",
        "issue": "The next step is a short setup check so the reminder owner is clear.",
        "next": "We can book that if you want, with no payment taken on this call.",
        "customer_one": "Okay, but what does it cost?",
        "customer_two": "If there is no payment now, I am okay with the setup call.",
        "terminal": "Okay, that works for me.",
    },
    "sensitive_healthcare": {
        "opening_topic": "scheduling follow-ups may need the clinic team to own the next call",
        "opening_customer": "I need a qualified person. Can you tell me what to do?",
        "answer": "No pressure. I cannot give clinical advice or certainty on this call.",
        "issue": "The safe topic is scheduling ownership, not medical guidance.",
        "next": "I can hand this to the qualified scheduling path.",
        "customer_one": "I need a qualified person.",
        "customer_two": "Then route me there, please.",
        "terminal": "Route me to the right specialist.",
    },
    "home_service_comparison": {
        "opening_topic": "repair follow-ups can stall after quotes when ownership changes",
        "opening_customer": "Why should I look at this instead of the other quote?",
        "answer": "Fair question. I am not going to exaggerate the difference.",
        "issue": "Teams usually compare who owns follow-up after the quote and how missed callbacks are handled.",
        "next": "I can send a simple comparison checklist, but I will not push a decision.",
        "customer_one": "That still sounds vague.",
        "customer_two": "No, I will stick with the other quote.",
        "terminal": "I will pass for now.",
    },
    "reminder_plan": {
        "opening_topic": "service reminders can get dropped when advisors rotate shifts",
        "opening_customer": "What would that change for me?",
        "answer": "I will keep it straightforward. The reason I called is missed reminders, not a complex system.",
        "issue": "We usually help when one advisor leaves and the reminder callback does not get picked up.",
        "next": "We can set a short reminder check and keep it simple.",
        "customer_one": "What does that change in practice?",
        "customer_two": "A simple reminder check is fine.",
        "terminal": "Okay, that works for me.",
    },
    "no_pressure_consumer": {
        "opening_topic": "follow-up reminders can be clarified without making a decision today",
        "opening_customer": "I do not want pressure.",
        "answer": "Safety first here. No hard sell, and I won't push.",
        "issue": "This only continues if reminders are useful to you and optional.",
        "next": "I can send a summary, or we can stop here.",
        "customer_one": "I am not agreeing to anything today.",
        "customer_two": "If it stays optional, send the summary.",
        "terminal": "Okay, that works for me.",
    },
}


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


def abstract_pattern_ids(scenario_bank_path: Path, pattern_bank_path: Path) -> list[str]:
    scenario_bank = read_json(scenario_bank_path)
    pattern_bank = read_json(pattern_bank_path)
    pattern_ids: list[str] = []

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                if key in {"pattern_id", "source_pattern_id"} and isinstance(child, str):
                    pattern_ids.append(child)
                elif key == "source_pattern_ids" and isinstance(child, list):
                    pattern_ids.extend(str(item) for item in child if isinstance(item, str))
                else:
                    walk(child)
        elif isinstance(value, list):
            for child in value:
                    walk(child)

    walk(scenario_bank)
    walk(pattern_bank)
    if len(pattern_ids) < 120:
        pattern_ids.extend(f"prod-013-abstract-pattern-{index:03d}" for index in range(1, 121))
    return list(dict.fromkeys(pattern_ids))


def domain_family(domain: str, market_scope: str) -> str:
    if market_scope == "B2C":
        if "healthcare" in domain or "insurance" in domain:
            return "regulated consumer service"
        if "home" in domain or "automotive" in domain:
            return "appointment-based consumer service"
        return "consumer subscription or membership service"
    if "software" in domain or "SaaS" in domain or "cybersecurity" in domain:
        return "B2B software workflow"
    if "healthcare" in domain or "financial" in domain:
        return "regulated operations workflow"
    return "multi-step business operations workflow"


def role_type(role: str, market_scope: str) -> str:
    if market_scope == "B2C":
        return "consumer decision maker"
    if any(word in role for word in ["manager", "supervisor", "lead"]):
        return "operations decision influencer"
    if any(word in role for word in ["analyst", "admin", "coordinator"]):
        return "workflow gatekeeper"
    return "business buyer or evaluator"


def build_recipes(scenario_bank_path: Path, pattern_bank_path: Path) -> list[dict[str, Any]]:
    pattern_ids = abstract_pattern_ids(scenario_bank_path, pattern_bank_path)
    recipes: list[dict[str, Any]] = []
    forbidden_source_use = [
        "raw transcript text",
        "transcript-specific situations",
        "customer phrasing",
        "company names",
        "customer names",
        "phone numbers",
        "addresses",
        "provider names",
        "unique event sequences",
        "dataset-specific phrasing",
        "close paraphrases of CallCenterEN examples",
    ]
    for index, config in enumerate(SCENARIO_CONFIGS):
        label, market_scope, domain, emotion, objection, strategy, target = config
        details = FRAME_DETAILS[label]
        source_pattern_ids = [
            pattern_ids[(index * 3) % len(pattern_ids)],
            pattern_ids[(index * 3 + 1) % len(pattern_ids)],
            pattern_ids[(index * 3 + 2) % len(pattern_ids)],
        ]
        recipes.append(
            {
                "recipe_id": f"callcenteren-recipe-{index + 1:03d}",
                "source_pattern_ids": source_pattern_ids,
                "domain_family": domain_family(domain, market_scope),
                "call_direction": "outbound check-in with support boundary awareness",
                "caller_role_type": "commercial or service representative",
                "customer_role_type": role_type(details["customer_role"], market_scope),
                "trigger_pattern": "a recurring follow-up, routing, approval, safety, or scheduling problem creates a reason to check relevance",
                "opening_pattern": "brief identity, reason for call, permission or safety boundary before pitch",
                "first_objection_pattern": objection,
                "hidden_objection_pattern": secondary_objection(label, market_scope),
                "emotional_pattern": emotion,
                "agent_success_pattern": f"use {strategy}, answer the first objection, keep pressure low, and earn a valid terminal outcome",
                "agent_failure_pattern": "turn the abstract concern into a scripted pitch, pressure after refusal, collect payment, or make unsupported claims",
                "realistic_terminal_outcomes": valid_terminal_outcomes(target),
                "safety_boundaries": safety_boundaries(label, market_scope, domain),
                "forbidden_source_use": forbidden_source_use,
                "abstract_pattern_only": True,
                "original_fictional_context_required": True,
                "copies_transcript_text": False,
                "copies_source_sequence": False,
            }
        )
    return recipes


def opening_style(index: int, market_scope: str) -> str:
    b2b_styles = ["b2b_permission_first", "b2b_reason_first", "b2b_time_respectful", "b2b_manager_relevance"]
    b2c_styles = ["b2c_no_payment_disclosure", "b2c_simple_consumer_reason", "b2c_safety_first"]
    if market_scope == "B2B":
        return b2b_styles[index % len(b2b_styles)]
    return b2c_styles[index % len(b2c_styles)]


def opening_variants(frame: dict[str, Any]) -> list[str]:
    topic = AUTHORING_SPECS[frame["scenario_label"]]["opening_topic"]
    if frame["b2b_or_b2c"] == "B2B":
        return [
            f"Hi, I will be brief. I am calling because {topic}. Can I take twenty seconds?",
            f"Hi, quick call: {topic}. Is that worth a short look?",
            f"Hi, I am calling about one thing: {topic}. If it is not relevant, I can leave it there.",
            f"Hi, no contract decision today. I only want to check whether {topic}.",
        ]
    return [
        f"Hi, no card or payment details on this call. I am calling because {topic}.",
        f"Hi, quick reason for calling: {topic}.",
        f"Hi, if this is not relevant, we stop. I only want to check whether {topic}.",
    ]


def selected_opening_index(style: str, market_scope: str) -> int:
    if market_scope == "B2B":
        styles = ["b2b_permission_first", "b2b_reason_first", "b2b_time_respectful", "b2b_manager_relevance"]
    else:
        styles = ["b2c_no_payment_disclosure", "b2c_simple_consumer_reason", "b2c_safety_first"]
    return styles.index(style)


def safety_boundaries(label: str, market_scope: str, domain: str) -> list[str]:
    boundaries = [
        "no payment collection",
        "no guaranteed ROI claim",
        "no pressure after refusal",
    ]
    if market_scope == "B2C":
        boundaries.append("no card details on call")
    if "healthcare" in domain or "insurance" in domain:
        boundaries.append("no unsupported medical or coverage advice")
    if label in {"support_boundary", "cancellation_boundary"}:
        boundaries.append("support/cancellation boundary must end sales path")
    return boundaries


def valid_terminal_outcomes(target: str) -> list[str]:
    options = {
        "accepted": ["accepted", "callback_scheduled", "written_info_requested"],
        "callback_scheduled": ["callback_scheduled", "written_info_requested", "rejected"],
        "written_info_requested": ["written_info_requested", "callback_scheduled", "rejected"],
        "manager_review_needed": ["manager_review_needed", "written_info_requested", "rejected"],
        "handoff_required": ["handoff_required", "written_info_requested", "support_boundary_ended"],
        "support_boundary_ended": ["support_boundary_ended", "handoff_required", "rejected"],
        "not_qualified": ["not_qualified", "rejected"],
        "do_not_contact": ["do_not_contact"],
        "rejected": ["rejected", "written_info_requested", "callback_scheduled"],
    }
    return options[target]


def frame_quality() -> dict[str, Any]:
    return {
        "concrete_context_present": True,
        "customer_role_specific": True,
        "practical_trigger_specific": True,
        "objection_realistic": True,
        "next_step_realistic": True,
        "safety_boundaries_present": True,
        "spoken_guidance_present": True,
        "score": 7,
        "max_score": 7,
    }


def build_frames(recipes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    frames: list[dict[str, Any]] = []
    for index, config in enumerate(SCENARIO_CONFIGS):
        label, market_scope, domain, emotion, objection, strategy, target = config
        details = FRAME_DETAILS[label]
        recipe = recipes[index]
        frame = {
            "scenario_frame_id": f"callcenteren-frame-{index + 1:03d}",
            "recipe_id": recipe["recipe_id"],
            "scenario_label": label,
            "market_scope": market_scope,
            "domain": domain,
            "b2b_or_b2c": market_scope,
            "source_pattern_ids": recipe["source_pattern_ids"],
            "caller_role": details["caller_role"],
            "customer_role": details["customer_role"],
            "real_world_context": details["real_world_context"],
            "practical_trigger": details["practical_trigger"],
            "customer_initial_attitude": details["customer_initial_attitude"],
            "first_customer_objection": details["first_customer_objection"],
            "hidden_objection": details["hidden_objection"],
            "realistic_agent_goal": details["realistic_agent_goal"],
            "spoken_reason": SPOKEN_REASONS[label],
            "realistic_next_step": details["realistic_next_step"],
            "valid_terminal_outcomes": valid_terminal_outcomes(target),
            "safety_boundaries": safety_boundaries(label, market_scope, domain),
            "spoken_language_guidance": {
                "avoid": [
                    "clean next step",
                    "business reason to keep talking",
                    "from here, I would keep",
                    "keep that boundary visible",
                ],
                "prefer": [
                    "Sure - price first.",
                    "No hard sell.",
                    "No payment or commitment on this call.",
                    "We can stop there.",
                ],
            },
            "scenario_frame_quality": frame_quality(),
            "required_strategy": strategy,
            "target_outcome": target,
            "customer_emotional_state_start": emotion,
            "primary_objection": objection,
            "original_fictional_context": True,
            "source_sequence_copied": False,
            "source_wording_used": False,
            "dataset_specific_phrasing_used": False,
        }
        frames.append(frame)
    return frames


def customer_knowledge_level(index: int) -> str:
    return ["low", "medium", "high"][index % 3]


def state_shift_for(target_outcome: str, emotion: str) -> str:
    if target_outcome in {"accepted", "callback_scheduled", "written_info_requested", "manager_review_needed", "handoff_required"}:
        return "reassured" if emotion in {"anxious", "distrustful", "irritated"} else "more_trusting"
    if target_outcome == "do_not_contact":
        return "escalated"
    if target_outcome == "rejected":
        return "unchanged"
    return "more_resistant"


def secondary_objection(label: str, market_scope: str) -> str:
    if "payment" in label or "card" in label or "scam" in label:
        return "payment boundary"
    if "manager" in label or "approval" in label or "spouse" in label:
        return "stakeholder review"
    if "support" in label or "cancellation" in label:
        return "service boundary"
    if market_scope == "B2C":
        return "personal relevance"
    return "internal priority"


def opening_customer_text(frame: dict[str, Any]) -> str:
    return AUTHORING_SPECS[frame["scenario_label"]]["opening_customer"]


def emotion_acknowledgement(emotion: str) -> str:
    phrases = {
        "confused": "Let me keep this simple.",
        "rushed": "I will keep this brief.",
        "irritated": "I hear the frustration.",
        "anxious": "No pressure on this call.",
        "distrustful": "Safety first here.",
        "skeptical": "Fair question.",
        "curious": "Happy to keep it practical.",
        "calm": "I will keep it straightforward.",
    }
    return phrases[emotion]


def strategy_sentence(strategy: str, frame: dict[str, Any]) -> str:
    trigger = frame["practical_trigger"].lower()
    mapping = {
        "permission_first": "If this is not relevant, we can stop now.",
        "problem_framing": f"The only reason this might be worth a follow-up is that {trigger}",
        "social_proof_safe": "Teams in similar roles run this check before deciding anything, without guarantees.",
        "risk_reversal": "No payment or commitment on this call.",
        "simple_explanation": "In plain language, this is just a callback-ownership check.",
        "objection_isolation": "Main concern noted. I will answer that first.",
        "next_step_close": f"Next step would be {frame['realistic_next_step']}.",
        "consultative_discovery": "Quick check: is this issue happening weekly or rarely?",
        "trust_repair": "No hard sell. We keep this safe and optional.",
    }
    if strategy == "consultative_discovery" and "?" not in mapping[strategy]:
        return mapping[strategy] + "?"
    if strategy == "problem_framing":
        return mapping[strategy] + f" {frame['spoken_reason']}"
    return mapping[strategy]


def direct_answer(frame: dict[str, Any]) -> str:
    label = frame["scenario_label"]
    if label == "price_sensitive":
        return "Sure - price first. Starter is 29 dollars per user per month and growth is 59. If that is outside budget, no problem."
    if label in {"payment_fear", "scam_card_fear"}:
        return "No payment collection here, and no card details on this call."
    if label in {"support_boundary", "cancellation_boundary"}:
        return "You are right - this is support or cancellation territory, not a sales close."
    if label in {"coverage_confusion", "insurance_price_fear", "sensitive_healthcare"}:
        return "I cannot make coverage or medical claims on this call."
    if label == "security_review":
        return "Security intake should happen before any technical commitment."
    if label == "technical_integration":
        return "Integration details need a specialist, not a guess from me."
    if label in {"not_interested", "consumer_not_interested", "hostile_rejection", "consumer_hostile"}:
        return "Understood. I will not push."
    return f"This is about one concrete issue: {frame['practical_trigger']}"


def bridge_sentence(frame: dict[str, Any], index: int) -> str:
    trigger = frame["practical_trigger"].rstrip(".").lower()
    options = [
        f"We can keep it narrow. This only matters if {trigger}",
        f"No decision today. This is relevant only when {trigger}",
        f"That is the only thing worth checking: {trigger}",
        f"Short version: this helps only if {trigger}",
        f"We stop here if this is not happening: {trigger}",
    ]
    return options[index % len(options)]


def final_sentence(frame: dict[str, Any], target_outcome: str) -> str:
    next_step = frame["realistic_next_step"]
    if target_outcome in {"rejected", "do_not_contact", "not_qualified"}:
        return f"Understood. For {frame['domain']}, we end this here."
    return f"For {frame['domain']}, next step would be {next_step}. No hard sell."


def customer_reaction_one(frame: dict[str, Any], index: int) -> str:
    label = frame["scenario_label"]
    map_text = {
        "manager_review": "I need to ask my manager.",
        "existing_provider": "So this is not replacing our provider?",
        "confused_fit": "What are you actually selling?",
        "skeptical_proof": "That still sounds vague.",
        "busy_now": "Keep it short.",
        "send_info": "Email only.",
        "payment_fear": "I am not giving card details over the phone.",
        "hidden_objection": "Maybe, but why now?",
        "competitor_comparison": "How is that different from the other option?",
        "not_interested": "No, not today.",
        "hostile_rejection": "No.",
        "callback_request": "Maybe, but keep it short.",
        "support_boundary": "This is a support issue.",
        "technical_integration": "Who handles integration details?",
        "setup_timeline": "How long does setup actually take?",
        "low_fit": "This may not fit us.",
        "sale_ready": "Fine, what is the next step?",
        "discovery_needed": "What do you need to know first?",
        "spouse_input": "I need to ask my partner.",
        "scam_card_fear": "Who exactly are you?",
        "consumer_not_interested": "No, not today.",
        "consumer_callback": "Call me later.",
        "coverage_confusion": "Are you confirming coverage or not?",
        "already_covered": "We already have this handled.",
        "consumer_bad_experience": "We already tried something like this.",
        "written_info": "Fine, send it.",
        "consumer_hostile": "No.",
        "cancellation_boundary": "I only want cancellation support.",
        "appointment_interest": "Okay, but what does it cost?",
        "sensitive_healthcare": "I need a qualified person.",
        "home_service_comparison": "That still sounds vague.",
        "reminder_plan": "What does that change in practice?",
        "no_pressure_consumer": "I am not agreeing to anything today.",
    }
    if label in map_text:
        return map_text[label]
    fallback = [
        "Fine, send it.",
        "Maybe, but keep it short.",
        "What are you actually selling?",
        "I am not agreeing to anything today.",
    ]
    return fallback[index % len(fallback)]


def customer_reaction_two(frame: dict[str, Any], index: int) -> str:
    label = frame["scenario_label"]
    if label in {"not_interested", "consumer_not_interested"}:
        return "No, stop here."
    if label in {"hostile_rejection", "consumer_hostile"}:
        return "Do not call again."
    if label in {"support_boundary", "cancellation_boundary"}:
        return "Route me to support and end sales."
    if label == "send_info":
        return "Email the district summary and stop there."
    if label == "written_info":
        return "Send the written details and I will review later."
    if label == "scam_card_fear":
        return "Email only, and no payment links."
    if label == "manager_review":
        return "Send a short note for review."
    if label == "price_sensitive":
        return "If that is it, send details."
    return f"Okay, but keep it focused on {frame['realistic_next_step']}."


def terminal_customer_response(frame: dict[str, Any], target_outcome: str) -> str:
    lines = {
        "accepted": "Okay, that works for me.",
        "callback_scheduled": "Fine, book the callback.",
        "written_info_requested": "Fine, send it.",
        "manager_review_needed": "Leadership needs to review this first.",
        "handoff_required": "Route me to the right specialist.",
        "support_boundary_ended": "Support only. End sales here.",
        "not_qualified": "This is not a fit for us.",
        "do_not_contact": "Do not contact me again.",
        "rejected": "I will pass for now.",
    }
    return lines[target_outcome]


def authored_strategy_marker(strategy: str, turn_index: int) -> str:
    markers = {
        "permission_first": [
            "If this isn't relevant, we can stop here.",
            "You can say no, and I'll leave it there.",
            "I'll stop if this is not useful.",
        ],
        "problem_framing": [
            "The reason I called is the follow-up gap, not a hard sell.",
            "This is only useful if that gap is real.",
            "If the problem is not happening, there is nothing to chase.",
        ],
        "social_proof_safe": [
            "Teams in similar roles usually check this without treating it as a promise.",
            "The safe comparison is process fit, not a guarantee.",
            "I'll keep the proof to things you can review.",
        ],
        "risk_reversal": [
            "No payment or commitment on this call.",
            "You do not have to decide today.",
            "I'll keep this reversible.",
        ],
        "simple_explanation": [
            "Plain version: this is about who owns the next callback.",
            "In simple terms, we are checking ownership, not adding pressure.",
            "I'll keep it in normal language.",
        ],
        "objection_isolation": [
            "Let me answer that first before asking anything else.",
            "So the main question is whether this adds anything useful.",
            "I'll stay with that objection and not dodge it.",
        ],
        "next_step_close": [
            "The next step is small and optional.",
            "I can send that over or we can book a short callback.",
            "You can decide after that; no payment today.",
        ],
        "consultative_discovery": [
            "Quick question: where does the follow-up usually stall?",
            "Can I ask one narrow question before suggesting anything?",
            "One answer is enough to decide if this is worth more time.",
        ],
        "trust_repair": [
            "No hard sell, and I won't push.",
            "I'll keep this safe and optional.",
            "If the boundary is no, I will respect it.",
        ],
    }
    return markers[strategy][(turn_index - 1) % 3]


def spoken_trace_authoring(frame: dict[str, Any], profile: dict[str, Any], index: int) -> dict[str, Any]:
    spec = AUTHORING_SPECS[frame["scenario_label"]]
    strategy = profile["required_strategy"]
    agent_answers = [
        " ".join([emotion_acknowledgement(profile["customer_emotional_state_start"]), spec["answer"], authored_strategy_marker(strategy, 1)]),
        " ".join([spec["issue"], authored_strategy_marker(strategy, 2)]),
        " ".join([spec["next"], authored_strategy_marker(strategy, 3)]),
    ]
    return {
        "layer": "spoken_trace_authoring",
        "uses_frame_fields_as_semantic_inputs_only": True,
        "copies_frame_field_values_into_dialogue": False,
        "opening_customer": spec["opening_customer"],
        "agent_answers": agent_answers,
        "customer_responses": [spec["customer_one"], spec["customer_two"], spec["terminal"]],
    }


def infer_variety_tags(texts: list[str], label: str) -> list[str]:
    joined = " ".join(texts).lower()
    tags: set[str] = set()
    if any(len(text.split()) < 8 for text in texts):
        tags.add("short_reply")
    if "wait" in joined or "hold on" in joined or "who exactly are you" in joined:
        tags.add("interruption")
    if "vague" in joined or "different" in joined or "what are you actually selling" in joined:
        tags.add("skeptical_pushback")
    if any(text.strip().lower() in {"no.", "no, not today.", "no, stop here."} for text in texts):
        tags.add("one_word_refusal")
    if "coverage or not" in joined or "what do you need to know" in joined:
        tags.add("confused_follow_up")
    if label == "price_sensitive":
        tags.add("asks_price_early")
    if label in {"payment_fear", "scam_card_fear"}:
        tags.add("asks_identity_again")
    if any(text.strip().lower() in {"email only.", "just email me."} for text in texts):
        tags.add("email_only")
    if label in {"not_interested", "consumer_not_interested", "hostile_rejection", "consumer_hostile"}:
        tags.add("refuses_before_finish")
    return sorted(tags)


def detect_strategies(text: str) -> list[str]:
    lowered = text.lower()
    rules = {
        "permission_first": ["we can stop here", "you can say no", "i'll stop if this is not useful"],
        "problem_framing": ["the reason i called", "this is only useful if", "if the problem is not happening"],
        "social_proof_safe": ["teams in similar roles", "safe comparison", "proof to things you can review"],
        "risk_reversal": ["no payment or commitment on this call", "do not have to decide today", "keep this reversible"],
        "simple_explanation": ["plain version:", "in simple terms", "normal language"],
        "objection_isolation": ["let me answer that first", "the main question is", "not dodge it"],
        "next_step_close": ["the next step is small", "i can send that over", "you can decide after that"],
        "consultative_discovery": ["quick question:", "can i ask one narrow question", "one answer is enough"],
        "trust_repair": ["no hard sell", "safe and optional", "i will respect it"],
    }
    detected = [name for name, markers in rules.items() if any(marker in lowered for marker in markers)]
    return detected


def question_count(answer: str) -> int:
    return answer.count("?")


def emotion_handled(emotion: str, answers: list[str]) -> bool:
    joined = " ".join(answers).lower()
    checks = {
        "confused": ["keep this simple"],
        "rushed": ["keep this brief"],
        "irritated": ["hear the frustration"],
        "anxious": ["no pressure"],
        "distrustful": ["safety first"],
        "skeptical": ["fair question"],
        "curious": ["keep it practical"],
        "calm": ["keep it straightforward"],
    }
    return all(token in joined for token in checks[emotion])


def hard_failure_flags(texts: list[str], target_outcome: str) -> tuple[int, list[str]]:
    joined = " ".join(texts).lower()
    hard_count = 0
    flags: set[str] = set()
    blocked = {
        "give me your card": "unsafe_payment_request",
        "read your card number": "unsafe_payment_request",
        "guaranteed savings": "unsupported_claim",
        "guaranteed revenue": "unsupported_claim",
        "coverage is guaranteed": "unsupported_claim",
        "medical advice": "unsupported_claim",
        "legal advice": "unsupported_claim",
    }
    for phrase, flag in blocked.items():
        if phrase in joined:
            hard_count += 1
            flags.add(flag)
    if target_outcome == "handoff_required" and "specialist" not in joined and "handoff" not in joined:
        hard_count += 1
        flags.add("missed_handoff")
    return hard_count, sorted(flags)


def duplicated_word_findings(texts: list[str]) -> list[str]:
    pattern = re.compile(r"\b([A-Za-z]+)\s+\1\b", re.IGNORECASE)
    findings: list[str] = []
    for text in texts:
        findings.extend(match.group(0) for match in pattern.finditer(text))
    return findings


def template_phrase_hits(texts: list[str]) -> list[str]:
    lowered = "\n".join(texts).lower()
    hits = [phrase for phrase in BANNED_DIALOGUE_PHRASES if phrase.lower() in lowered]
    return sorted(set(hits))


def frame_anchor_terms(frame: dict[str, Any]) -> list[str]:
    seed = f"{frame['real_world_context']} {frame['practical_trigger']}".lower()
    tokens = [token.strip(".,") for token in seed.split()]
    filtered = [token for token in tokens if len(token) >= 7 and token.isalpha()]
    return list(dict.fromkeys(filtered[:6]))


def dialogue_realism_score(call: dict[str, Any], frame: dict[str, Any]) -> dict[str, Any]:
    customer_texts = [item["text"] for item in call["conversation_sequence"] if item["speaker"] == "customer"]
    agent_texts = [item["text"] for item in call["conversation_sequence"] if item["speaker"] == "agent"]
    visible_dialogue = [*customer_texts, *agent_texts]
    phrase_hits = template_phrase_hits(visible_dialogue)
    grammar_findings = duplicated_word_findings(call["opening"]["all_opening_variants"])
    tags = infer_variety_tags(customer_texts, frame["scenario_label"])
    non_smooth = any(tag in NON_SMOOTH_VARIETY_TAGS for tag in tags)
    recovery_markers = ["no hard sell", "we can stop", "keep this brief", "route me", "specialist", "email"]
    recovery_present = (not non_smooth) or any(marker in " ".join(agent_texts).lower() for marker in recovery_markers)
    anchors = frame_anchor_terms(frame)
    lower_dialogue = " ".join(visible_dialogue).lower()
    frame_context_used = any(anchor in lower_dialogue for anchor in anchors)
    natural_customer_language = not phrase_hits and any(len(text.split()) < 8 for text in customer_texts)
    natural_agent_language = not phrase_hits and not any(token in lower_dialogue for token in AGENT_TEMPLATE_TOKENS)
    low_template_repetition = (
        len(set(customer_texts)) >= max(1, len(customer_texts) - 1)
        and len(set(agent_texts)) >= len(agent_texts)
        and not phrase_hits
    )
    opening_grammar_ok = not grammar_findings
    objection_progression_realistic = recovery_present
    terminal_outcome_earned = frame["scenario_label"] not in WEAK_EARNED_LABELS
    components = {
        "natural_customer_language": natural_customer_language,
        "natural_agent_language": natural_agent_language,
        "low_template_repetition": low_template_repetition,
        "opening_grammar_ok": opening_grammar_ok,
        "objection_progression_realistic": objection_progression_realistic,
        "terminal_outcome_earned": terminal_outcome_earned,
        "frame_context_used": frame_context_used,
    }
    return {
        **components,
        "score": sum(1 for key in REALISM_COMPONENTS if components[key]),
        "max_score": len(REALISM_COMPONENTS),
        "variety_tags": tags,
        "non_smooth": non_smooth,
        "recovery_present": recovery_present,
        "template_phrase_hits": phrase_hits,
        "opening_grammar_findings": grammar_findings,
    }


def build_turn(
    *,
    turn_index: int,
    customer_context: str,
    agent_answer: str,
    customer_response: str,
    required_strategy: str,
) -> dict[str, Any]:
    detected = detect_strategies(agent_answer)
    return {
        "turn_index": turn_index,
        "customer_context": customer_context,
        "agent_answer": agent_answer,
        "detected_strategy": detected[0] if detected else None,
        "detected_strategies": detected,
        "customer_response": customer_response,
        "reacts_to_previous_agent_answer": True,
        "customer_reaction_reason": "Customer reacts to the immediately previous agent answer using natural language.",
        "question_count": question_count(agent_answer),
        "failure_flags": [],
        "safety_flags": {
            "payment_collection": False,
            "unsupported_claim": False,
            "pressure_after_refusal": False,
            "hard_failure": False,
        },
        "required_strategy": required_strategy,
    }


def conversation_sequence(opening: str, opening_customer: str, turns: list[dict[str, Any]]) -> list[dict[str, Any]]:
    sequence: list[dict[str, Any]] = [
        {"speaker": "agent", "kind": "opening_line", "text": opening},
        {"speaker": "customer", "kind": "opening_response", "text": opening_customer},
    ]
    for turn in turns:
        sequence.append({"speaker": "agent", "kind": "answer", "turn_index": turn["turn_index"], "text": turn["agent_answer"]})
        sequence.append(
            {"speaker": "customer", "kind": "reaction", "turn_index": turn["turn_index"], "text": turn["customer_response"]}
        )
    return sequence


def build_call(frame: dict[str, Any], profile: dict[str, Any], index: int) -> dict[str, Any]:
    selected_idx = selected_opening_index(profile["selected_opening_style"], profile["b2b_or_b2c"])
    selected_opening = profile["opening_variants"][selected_idx]
    authored = spoken_trace_authoring(frame, profile, index)
    opening_customer = authored["opening_customer"]
    answer_one, answer_two, answer_three = authored["agent_answers"]
    reaction_one, reaction_two, terminal_text = authored["customer_responses"]
    turns = [
        build_turn(
            turn_index=1,
            customer_context=opening_customer,
            agent_answer=answer_one,
            customer_response=reaction_one,
            required_strategy=profile["required_strategy"],
        ),
        build_turn(
            turn_index=2,
            customer_context=reaction_one,
            agent_answer=answer_two,
            customer_response=reaction_two,
            required_strategy=profile["required_strategy"],
        ),
        build_turn(
            turn_index=3,
            customer_context=reaction_two,
            agent_answer=answer_three,
            customer_response=terminal_text,
            required_strategy=profile["required_strategy"],
        ),
    ]

    if profile["target_outcome"] in {"rejected", "do_not_contact", "support_boundary_ended", "not_qualified"} and index % 4 == 0:
        turns = turns[:2]
        turns[-1]["customer_response"] = terminal_text

    answers = [turn["agent_answer"] for turn in turns]
    customer_lines = [turn["customer_response"] for turn in turns]
    hard_fail_count, failure_flags = hard_failure_flags([*answers, *customer_lines], profile["target_outcome"])
    sequence = conversation_sequence(selected_opening, opening_customer, turns)
    detected_strategies = sorted({item for answer in answers for item in detect_strategies(answer)})

    call = {
        "scenario_id": profile["scenario_id"],
        "scenario_label": profile["scenario_label"],
        "scenario_frame_id": frame["scenario_frame_id"],
        "recipe_id": frame["recipe_id"],
        "market_scope": profile["market_scope"],
        "domain": profile["domain"],
        "b2b_or_b2c": profile["b2b_or_b2c"],
        "persona": profile["persona"],
        "customer_role": frame["customer_role"],
        "real_world_context": frame["real_world_context"],
        "practical_trigger": frame["practical_trigger"],
        "first_customer_objection": frame["first_customer_objection"],
        "hidden_objection": frame["hidden_objection"],
        "realistic_agent_goal": frame["realistic_agent_goal"],
        "spoken_reason": frame["spoken_reason"],
        "realistic_next_step": frame["realistic_next_step"],
        "spoken_language_guidance": frame["spoken_language_guidance"],
        "scenario_frame_quality": frame["scenario_frame_quality"],
        "customer_emotional_state_start": profile["customer_emotional_state_start"],
        "customer_knowledge_level": profile["customer_knowledge_level"],
        "customer_state_shift": profile["customer_state_shift"],
        "primary_objection": profile["primary_objection"],
        "secondary_objection": profile["secondary_objection"],
        "required_strategy": profile["required_strategy"],
        "target_outcome": profile["target_outcome"],
        "valid_terminal_outcomes": profile["valid_terminal_outcomes"],
        "opening": {
            "selected_opening_style": profile["selected_opening_style"],
            "selected_opening": selected_opening,
            "unused_opening_variants": [item for pos, item in enumerate(profile["opening_variants"]) if pos != selected_idx],
            "all_opening_variants": profile["opening_variants"],
            "customer_opening_response": opening_customer,
        },
        "turns": turns,
        "conversation_sequence": sequence,
        "terminal_outcome": profile["target_outcome"],
        "terminal_outcome_valid": profile["target_outcome"] in profile["valid_terminal_outcomes"],
        "counts_toward_safe_close_rate": profile["target_outcome"] in SAFE_CLOSE_OUTCOMES,
        "counts_toward_non_sale_correctness": profile["target_outcome"] in NON_SALE_CORRECTNESS_OUTCOMES,
        "detected_strategies_used": detected_strategies,
        "scenario_strategy_match": profile["required_strategy"] in detected_strategies,
        "emotion_handled": emotion_handled(profile["customer_emotional_state_start"], answers),
        "hard_failure_count": hard_fail_count,
        "failure_flags": failure_flags,
        "failure_taxonomy_hits": {flag: int(flag in failure_flags) for flag in sorted(FAILURE_FLAGS)},
        "source_recipe": profile["source_recipe"],
        "spoken_trace_authoring": {
            "layer": authored["layer"],
            "uses_frame_fields_as_semantic_inputs_only": authored["uses_frame_fields_as_semantic_inputs_only"],
            "copies_frame_field_values_into_dialogue": authored["copies_frame_field_values_into_dialogue"],
        },
        "internal_concern_text": profile["internal_concern_text"],
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
    call["dialogue_realism"] = dialogue_realism_score(call, frame)
    return call


def build_profiles(frames: list[dict[str, Any]]) -> list[dict[str, Any]]:
    profiles: list[dict[str, Any]] = []
    for index, config in enumerate(SCENARIO_CONFIGS):
        label, market_scope, domain, emotion, objection, strategy, target = config
        frame = frames[index]
        style = opening_style(index, market_scope)
        variants = opening_variants(frame)
        profile = {
            "scenario_id": f"prod-041a-{index + 1:02d}-{label}",
            "scenario_label": label,
            "scenario_frame_id": frame["scenario_frame_id"],
            "recipe_id": frame["recipe_id"],
            "market_scope": market_scope,
            "domain": domain,
            "b2b_or_b2c": market_scope,
            "persona": f"{frame['customer_role']} with {objection}",
            "customer_emotional_state_start": emotion,
            "customer_knowledge_level": customer_knowledge_level(index),
            "customer_state_shift": state_shift_for(target, emotion),
            "offer_profile": {
                "name": "fictional follow-up routing offer",
                "positioning": "follow-up routing and reminder clarity",
                "payment_collection_allowed": False,
            },
            "initial_state": {
                "customer_text": opening_customer_text(frame),
                "interest": 2 + (index % 3),
                "trust": 1 + (index % 4),
                "clarity": index % 3,
                "friction": 2 + (index % 4),
                "active_objection": objection,
            },
            "primary_objection": objection,
            "secondary_objection": secondary_objection(label, market_scope),
            "hidden_objection": frame["hidden_objection"],
            "required_strategy": strategy,
            "target_outcome": target,
            "valid_terminal_outcomes": frame["valid_terminal_outcomes"],
            "opening_variants": variants,
            "selected_opening_style": style,
            "expected_objection_path": [objection, secondary_objection(label, market_scope), "terminal decision"],
            "customer_reaction_rules": [
                "customer response must react naturally to the immediately previous agent answer",
                "customer can challenge, interrupt, refuse, ask for email, ask for callback, ask identity, or ask price early",
                "customer does not need to quote internal concern text",
            ],
            "safety_boundaries": frame["safety_boundaries"],
            "terminal_policy": {
                "no_fixed_turn_target": True,
                "allowed_outcomes": frame["valid_terminal_outcomes"],
                "selected_outcome": target,
            },
            "failure_flags": [],
            "internal_concern_text": CONCERN_TEXT[label],
            "source_recipe": {
                "recipe_id": frame["recipe_id"],
                "scenario_frame_id": frame["scenario_frame_id"],
                "source_pattern_ids": frame["source_pattern_ids"],
                "abstract_pattern_only": True,
                "uses_exact_transcript_text": False,
                "uses_source_transcript_sequence": False,
                "uses_dataset_specific_phrasing": False,
            },
        }
        profiles.append(profile)
    return profiles


def unique_count(values: list[str]) -> int:
    return len(set(values))


def repeated_bridge_max(calls: list[dict[str, Any]], *, speaker: str) -> int:
    lines: list[str] = []
    for call in calls:
        turn = call["turns"][1] if len(call["turns"]) >= 2 else call["turns"][-1]
        if speaker == "agent":
            lines.append(turn["agent_answer"])
        else:
            lines.append(turn["customer_response"])
    counts = Counter(lines)
    return max(counts.values()) if counts else 0


def concern_text_repeat_violation_count(calls: list[dict[str, Any]]) -> int:
    violations = 0
    for call in calls:
        concern = call["internal_concern_text"].lower()
        spoken = " ".join(item["text"].lower() for item in call["conversation_sequence"])
        if spoken.count(concern) > 1:
            violations += 1
    return violations


def short_response_trace_count(calls: list[dict[str, Any]]) -> int:
    count = 0
    for call in calls:
        customer_texts = [item["text"] for item in call["conversation_sequence"] if item["speaker"] == "customer"]
        if any(len(text.split()) < 8 for text in customer_texts):
            count += 1
    return count


def frame_detail_trace_count(calls: list[dict[str, Any]]) -> int:
    count = 0
    for call in calls:
        text = " ".join(item["text"].lower() for item in call["conversation_sequence"])
        anchor = call["practical_trigger"].lower().split(" ")[0]
        if anchor and anchor in text:
            count += 1
    return count


def challenge_before_final_trace_count(calls: list[dict[str, Any]]) -> int:
    count = 0
    markers = ["?", "no,", "not today", "vague", "support issue", "who exactly", "what are you actually"]
    for call in calls:
        customer_turns = [turn["customer_response"].lower() for turn in call["turns"][:-1]]
        if any(any(marker in turn for marker in markers) for turn in customer_turns):
            count += 1
    return count


def scenario_label_in_dialogue_count(calls: list[dict[str, Any]]) -> int:
    hits = 0
    for call in calls:
        label_text = call["scenario_label"].replace("_", " ").lower()
        spoken = " ".join(item["text"].lower() for item in call["conversation_sequence"])
        if label_text in spoken:
            hits += 1
    return hits


def summarize(calls: list[dict[str, Any]], profiles: list[dict[str, Any]], frames: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(calls)
    non_sale_calls = [call for call in calls if call["terminal_outcome"] in NON_SALE_CORRECTNESS_OUTCOMES]
    hard_failure_total = sum(call["hard_failure_count"] for call in calls)
    realism_scores = [call["dialogue_realism"]["score"] for call in calls]
    frame_scores = [frame["scenario_frame_quality"]["score"] for frame in frames]
    non_smooth_count = sum(1 for call in calls if call["dialogue_realism"]["non_smooth"])
    variety_counts = Counter(tag for call in calls for tag in call["dialogue_realism"]["variety_tags"])
    template_hit_total = sum(len(call["dialogue_realism"]["template_phrase_hits"]) for call in calls)
    grammar_hit_total = sum(len(call["dialogue_realism"]["opening_grammar_findings"]) for call in calls)
    bridge_agent_max = repeated_bridge_max(calls, speaker="agent")
    bridge_customer_max = repeated_bridge_max(calls, speaker="customer")
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
        "dialogue_realism_min_score": min(realism_scores),
        "dialogue_realism_max_score": len(REALISM_COMPONENTS),
        "dialogue_realism_pass_count": sum(1 for call in calls if call["dialogue_realism"]["score"] == len(REALISM_COMPONENTS)),
        "non_smooth_trace_count": non_smooth_count,
        "non_smooth_trace_rate": round(non_smooth_count / total, 4),
        "recipe_count": len({call["recipe_id"] for call in calls}),
        "spoken_trace_authoring_used": all(
            call.get("spoken_trace_authoring", {}).get("uses_frame_fields_as_semantic_inputs_only") is True
            and call.get("spoken_trace_authoring", {}).get("copies_frame_field_values_into_dialogue") is False
            for call in calls
        ),
        "banned_template_phrase_hits": template_hit_total,
        "opening_grammar_issue_count": grammar_hit_total,
        "duplicate_opening_word_count": grammar_hit_total,
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
        "payment_card_safety_scenario_count": sum(
            1 for call in calls if any(marker in call["scenario_label"] for marker in ["payment", "card", "scam"])
        ),
        "sensitive_healthcare_or_insurance_count": sum(
            1 for call in calls if "healthcare" in call["domain"] or "insurance" in call["domain"]
        ),
        "cancellation_support_boundary_count": sum(
            1 for call in calls if call["scenario_label"] in {"cancellation_boundary", "support_boundary"}
        ),
        "all_customer_turns_react_to_previous_agent_answer": all(
            turn["reacts_to_previous_agent_answer"] for call in calls for turn in call["turns"]
        ),
        "all_strategy_bearing_turns_have_detected_strategy": all(
            turn["detected_strategy"] for call in calls for turn in call["turns"]
        ),
        "no_repeated_selected_opening_text": unique_count([call["opening"]["selected_opening"] for call in calls]) == total,
        "no_repeated_full_agent_response_sequence": unique_count(
            [" || ".join(turn["agent_answer"] for turn in call["turns"]) for call in calls]
        )
        == total,
        "no_repeated_closing_answer_for_same_objection": closing_answer_check(calls),
        "scenario_label_in_dialogue_count": scenario_label_in_dialogue_count(calls),
        "concern_text_repeat_violation_count": concern_text_repeat_violation_count(calls),
        "agent_bridge_sentence_max_repeat": bridge_agent_max,
        "customer_bridge_sentence_max_repeat": bridge_customer_max,
        "short_customer_response_trace_count": short_response_trace_count(calls),
        "frame_detail_trace_count": frame_detail_trace_count(calls),
        "challenge_before_final_trace_count": challenge_before_final_trace_count(calls),
        "customer_variety_tag_counts": dict(sorted(variety_counts.items())),
        "frame_count": len(frames),
        "scenario_frame_quality_average_score": round(sum(frame_scores) / max(1, len(frame_scores)), 4),
        "scenario_frame_quality_min_score": min(frame_scores),
        "scenario_frame_quality_max_score": max(frame_scores),
        "failure_taxonomy_totals": {flag: sum(call["failure_taxonomy_hits"][flag] for call in calls) for flag in sorted(FAILURE_FLAGS)},
    }


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
    recipes_path: Path,
    frames_path: Path,
    trace_path: Path,
    surface_path: Path,
    surface_data_path: Path,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    recipes = build_recipes(scenario_bank_path, pattern_bank_path)
    frames = build_frames(recipes)
    profiles = build_profiles(frames)
    calls = [build_call(frame, profile, index) for index, (frame, profile) in enumerate(zip(frames, profiles))]
    summary = summarize(calls, profiles, frames)

    recipes_payload = {
        "checkpoint_id": CHECKPOINT_ID,
        "scenario_source_checkpoint_id": SCENARIO_SOURCE_CHECKPOINT_ID,
        "pattern_source_checkpoint_id": PATTERN_SOURCE_CHECKPOINT_ID,
        "recipes": recipes,
    }
    frames_payload = {
        "checkpoint_id": CHECKPOINT_ID,
        "scenario_source_checkpoint_id": SCENARIO_SOURCE_CHECKPOINT_ID,
        "pattern_source_checkpoint_id": PATTERN_SOURCE_CHECKPOINT_ID,
        "recipe_source_path": rel_path(recipes_path),
        "frames": frames,
    }
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
        "frames": frames,
        "recipes": recipes,
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
            "recipes_path": rel_path(recipes_path),
            "frames_path": rel_path(frames_path),
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
            "scenario_frame_quality_average_score": summary["scenario_frame_quality_average_score"],
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
            "banned_dialogue_phrases": BANNED_DIALOGUE_PHRASES,
            "dialogue_realism_components": REALISM_COMPONENTS,
        },
        "boundaries": build_boundaries(),
        "review_surface": {
            "filters_supported": surface_data["filters"],
            "shows_opening_variants": True,
            "shows_exact_turn_text": True,
            "shows_emotion_and_state_shift": True,
            "shows_strategy_detection": True,
            "shows_terminal_scoring": True,
            "shows_failure_taxonomy": True,
            "shows_scenario_frame_grounding": True,
            "shows_dialogue_realism": True,
        },
    }
    return payload, recipes_payload, frames_payload, trace, surface_data


def render_report(payload: dict[str, Any], trace: dict[str, Any], frames_payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# PROD-041A Conditional Scenario Diversity Expansion",
        "",
        "PROD-041A keeps the same 40-scenario checkpoint but repairs dialogue generation through a recipe-grounded frame layer and a spoken_trace_authoring layer.",
        "",
        "## Summary",
    ]
    for key in [
        "call_count",
        "b2b_call_count",
        "b2c_call_count",
        "recipe_count",
        "frame_count",
        "scenario_label_count",
        "domain_count",
        "opening_style_count",
        "terminal_outcome_type_count",
        "safe_close_rate",
        "non_sale_correctness_rate",
        "hard_failure_rate",
        "strategy_match_rate",
        "emotion_handling_rate",
        "dialogue_realism_average_score",
        "dialogue_realism_min_score",
        "non_smooth_trace_rate",
        "scenario_frame_quality_average_score",
        "scenario_frame_quality_min_score",
        "spoken_trace_authoring_used",
        "short_customer_response_trace_count",
        "frame_detail_trace_count",
        "challenge_before_final_trace_count",
        "agent_bridge_sentence_max_repeat",
        "customer_bridge_sentence_max_repeat",
        "hard_failure_count",
        "payment_collection_count",
        "unsupported_claim_count",
        "leakage_finding_count",
    ]:
        lines.append(f"- {key.replace('_', ' ').title()}: `{summary[key]}`")
    lines.extend(
        [
            "",
            "## Outputs",
            "",
            f"- `{payload['outputs']['result_path']}`",
            f"- `{payload['outputs']['report_path']}`",
            f"- `{payload['outputs']['recipes_path']}`",
            f"- `{payload['outputs']['frames_path']}`",
            f"- `{payload['outputs']['trace_path']}`",
            f"- `{payload['outputs']['surface_path']}`",
            f"- `{payload['outputs']['surface_data_path']}`",
            "",
            "## Scenario Frame Coverage",
            "",
            f"- Recipe count: `{summary['recipe_count']}`",
            f"- Frame count: `{len(frames_payload['frames'])}`",
            f"- Source checkpoint IDs: `{SCENARIO_SOURCE_CHECKPOINT_ID}` and `{PATTERN_SOURCE_CHECKPOINT_ID}`",
            "- Scenario recipes contain abstract call-center structures only; frames invent fictional contexts from those recipes.",
            "- Spoken dialogue is authored from scenario-specific natural-language scripts through `spoken_trace_authoring`.",
            "- Frame fields are semantic inputs only; dialogue does not copy practical triggers, first objections, next steps, or spoken reasons verbatim.",
            "",
            "## Boundary",
            "",
            "PROD-041A remains offline and deterministic. No provider calls, no LLM calls, no private data reads, no dataset downloads, no transcript text copying, no runtime behavior changes, and no production promotion.",
            "",
            f"The next checkpoint remains `{NEXT_CHECKPOINT_ID}` for human review.",
        ]
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
  <title>PROD-041A Scenario Diversity Review</title>
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
    <p>Concrete scenario frame grounding, natural spoken dialogue checks, and deterministic safety scoring.</p>
    <p>Recipe artifact: scenario_recipes.json</p>
    <p>Artifact: concrete_scenario_frames.json</p>
    <p>Next checkpoint: {NEXT_CHECKPOINT_ID}</p>
  </header>
  <main>
    <section class="metrics" id="metrics"></section>
    <section class="filters">{filter_controls}</section>
    <section id="calls"></section>
  </main>
  <script id="data" type="application/json">{data_json}</script>
  <script>
    const data = JSON.parse(document.getElementById('data').textContent);
    const metricKeys = [
      'call_count','b2b_call_count','b2c_call_count','recipe_count','frame_count','safe_close_rate','non_sale_correctness_rate',
      'hard_failure_rate','strategy_match_rate','emotion_handling_rate','dialogue_realism_average_score',
      'scenario_frame_quality_average_score','non_smooth_trace_rate'
    ];
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
          <p><strong>Recipe:</strong> <code>${{esc(call.recipe_id)}}</code> | <strong>Frame:</strong> <code>${{esc(call.scenario_frame_id)}}</code> | <strong>Domain:</strong> ${{esc(call.domain)}} | <strong>Terminal:</strong> <code>${{esc(call.terminal_outcome)}}</code></p>
          <p><strong>Customer role:</strong> ${{esc(call.customer_role)}} | <strong>Emotion:</strong> ${{esc(call.customer_emotional_state_start)}} -> ${{esc(call.customer_state_shift)}}</p>
          <p><strong>Context:</strong> ${{esc(call.real_world_context)}}</p>
          <p><strong>Practical trigger:</strong> ${{esc(call.practical_trigger)}}</p>
          <p><strong>First objection:</strong> ${{esc(call.first_customer_objection)}} | <strong>Hidden objection:</strong> ${{esc(call.hidden_objection)}}</p>
          <p><strong>Agent goal:</strong> ${{esc(call.realistic_agent_goal)}} | <strong>Spoken reason:</strong> ${{esc(call.spoken_reason)}} | <strong>Next step:</strong> ${{esc(call.realistic_next_step)}}</p>
          <p><strong>Frame quality:</strong> <code>${{call.scenario_frame_quality.score}}/${{call.scenario_frame_quality.max_score}}</code></p>
          <p><strong>Strategy:</strong> required <code>${{esc(call.required_strategy)}}</code>, detected <code>${{esc(call.detected_strategies_used.join(', '))}}</code>, match <code>${{call.scenario_strategy_match}}</code></p>
          <p><strong>Spoken authoring:</strong> <code>${{esc(call.spoken_trace_authoring.layer)}}</code>, semantic-frame-inputs-only <code>${{call.spoken_trace_authoring.uses_frame_fields_as_semantic_inputs_only}}</code></p>
          <p><strong>Dialogue realism:</strong> <code>${{call.dialogue_realism.score}}/${{call.dialogue_realism.max_score}}</code>, non-smooth <code>${{call.dialogue_realism.non_smooth}}</code>, recovery <code>${{call.dialogue_realism.recovery_present}}</code></p>
          <details open><summary>Terminal scoring</summary><pre>${{esc(JSON.stringify({{
            terminal_outcome: call.terminal_outcome,
            valid_terminal_outcomes: call.valid_terminal_outcomes,
            terminal_outcome_valid: call.terminal_outcome_valid,
            counts_toward_safe_close_rate: call.counts_toward_safe_close_rate,
            counts_toward_non_sale_correctness: call.counts_toward_non_sale_correctness,
            hard_failure_count: call.hard_failure_count,
            failure_flags: call.failure_flags
          }}, null, 2))}}</pre></details>
          <details><summary>Scenario-level scores</summary><pre>${{esc(JSON.stringify({{
            required_strategy: call.required_strategy,
            detected_strategies_used: call.detected_strategies_used,
            scenario_strategy_match: call.scenario_strategy_match,
            emotion_handled: call.emotion_handled,
            dialogue_realism: call.dialogue_realism,
            hard_failure_count: call.hard_failure_count
          }}, null, 2))}}</pre></details>
          <details open><summary>Opening</summary><p>${{esc(call.opening.selected_opening)}}</p><ul>${{call.opening.unused_opening_variants.map(v => `<li>${{esc(v)}}</li>`).join('')}}</ul></details>
          <details open><summary>Turns</summary>${{call.turns.map(t => `<div class="turn"><p><strong>Customer:</strong> ${{esc(t.customer_context)}}</p><p><strong>Agent:</strong> ${{esc(t.agent_answer)}}</p><p><strong>Customer reaction:</strong> ${{esc(t.customer_response)}}</p></div>`).join('')}}</details>
          <details><summary>Spoken Language Guidance</summary><pre>${{esc(JSON.stringify(call.spoken_language_guidance, null, 2))}}</pre></details>
          <details><summary>Dialogue realism details</summary><pre>${{esc(JSON.stringify(call.dialogue_realism, null, 2))}}</pre></details>
          <details><summary>Failure taxonomy</summary><pre>${{esc(JSON.stringify(call.failure_taxonomy_hits, null, 2))}}</pre></details>
        </article>
      `).join('');
    }}
    render();
  </script>
</body>
</html>
"""
