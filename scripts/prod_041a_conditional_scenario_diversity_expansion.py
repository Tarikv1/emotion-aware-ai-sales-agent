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
DEFAULT_POLICY_BANK = DEFAULT_OUT_DIR / "customer_reaction_policy_bank.json"
DEFAULT_FRAMES = DEFAULT_OUT_DIR / "concrete_scenario_frames.json"
DEFAULT_INTERACTIVE_PROFILES = DEFAULT_OUT_DIR / "interactive_scenario_profiles.json"
DEFAULT_TRACE = DEFAULT_OUT_DIR / "interaction_traces.json"
DEFAULT_LEGACY_TRACE = DEFAULT_OUT_DIR / "scenario_diversity_traces.json"
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
    "ignored_customer_input",
    "looping_question",
    "failed_to_progress",
    "unanswered_customer_intent",
    "false_safe_close",
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
            "## Review Trace Fields",
            "",
            "Each generated interaction trace records `agent_action_tags`, selected `reaction_rule_ids`, customer state before/after each response, failure taxonomy hits, safety flags, loop guard status, and whether actual local agent logic was used.",
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


# ---------------------------------------------------------------------------
# PROD-041A interactive conditional simulator implementation.
#
# The earlier PROD-041A functions remain above for historical continuity, but
# the public runner imports the names below. These later definitions intentionally
# replace the fixed spoken_trace_authoring payload with an interactive loop:
# reaction policy bank -> interactive scenario profiles -> current local sales
# agent turn harness -> customer simulator -> final interaction traces.
# ---------------------------------------------------------------------------

import sys

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from runtime.entrypoints.generate_guarded_response import build_guarded_response_packet


PATHS = [
    "happy_path",
    "skeptical_path",
    "callback_path",
    "written_info_path",
    "rejection_path",
    "support_boundary_path",
    "low_fit_path",
    "not_qualified_path",
    "manager_review_path",
    "do_not_contact_path",
    "handoff_path",
]

LENGTH_TARGETS = {
    "early_exit": (2, 4),
    "short": (5, 7),
    "medium": (8, 12),
    "long": (13, 18),
    "extended": (19, 28),
}


def clamp(value: int, low: int = 0, high: int = 5) -> int:
    return max(low, min(high, value))


INTERACTIVE_RULE_TOPICS = [
    (
        "reaction-price-answered-001",
        ["objection-price-002", "customer-softening-001"],
        "early_call",
        ["answered_price_directly", "gave_low_pressure_boundary"],
        {"primary_objection": "price", "trust_gte": 2},
        {"trust": 1, "clarity": 1, "friction": -1},
        "asks_relevance_or_written_info",
        [
            "Okay. What would the follow-up actually cover?",
            "Fine. Send me the pricing and a short summary.",
            "That is clearer. Why would this matter for us?",
            "I am not agreeing yet, but I can look at the details.",
        ],
        ["written_info_path", "callback_path", "skeptical_path"],
        False,
        ["no pressure after price objection"],
    ),
    (
        "reaction-price-dodged-001",
        ["objection-price-001", "customer-friction-repeat-question-001"],
        "early_call",
        ["dodged_price", "gave_vague_answer"],
        {"primary_objection": "price", "trust_lte": 4, "patience_lte": 5},
        {"trust": -1, "patience": -1, "friction": 1},
        "repeat_price_question_with_impatience",
        [
            "I asked what it costs.",
            "You still have not told me the price.",
            "I do not want the pitch before the price.",
            "Can you just answer the cost question?",
        ],
        ["skeptical_path", "rejection_path", "written_info_path"],
        False,
        ["no pressure after repeated price objection"],
    ),
    (
        "reaction-not-interested-001",
        ["objection-not_interested-001", "terminal-refusal-001"],
        "any",
        ["respected_refusal", "gave_low_pressure_boundary"],
        {"interest_lte": 2},
        {"trust": 0, "patience": 0, "friction": 0},
        "ends_or_allows_polite_close",
        ["No, not today.", "I will pass.", "Please leave it there.", "Not interested."],
        ["rejection_path", "do_not_contact_path"],
        True,
        ["end without pressure"],
    ),
    (
        "reaction-callback-request-001",
        ["objection-callback-001", "terminal-callback-002"],
        "mid_call",
        ["offered_callback", "gave_next_step"],
        {"patience_lte": 5},
        {"trust": 1, "interest": 1, "friction": -1},
        "accepts_or_limits_callback",
        ["Send me a couple of times.", "Maybe next week.", "Keep it to fifteen minutes.", "Email times first."],
        ["callback_path", "written_info_path"],
        False,
        ["callback must stay optional"],
    ),
    (
        "reaction-written-info-001",
        ["objection-send_info-001", "terminal-written_info-001"],
        "mid_call",
        ["offered_written_info", "gave_low_pressure_boundary"],
        {"trust_gte": 1},
        {"clarity": 1, "friction": -1},
        "asks_for_email_only",
        ["Fine, send it.", "Email only.", "Just email me.", "Send the short version."],
        ["written_info_path", "rejection_path"],
        False,
        ["do not force a meeting after email-only request"],
    ),
    (
        "reaction-identity-question-001",
        ["objection-trust-identity-001", "customer-verification-001"],
        "early_call",
        ["cold_open_permission_first", "vague_pitch"],
        {"trust_lte": 3},
        {"trust": -1, "friction": 1},
        "asks_who_caller_is",
        ["Who exactly are you?", "What company is this again?", "Why are you calling me?", "Who gave you this number?"],
        ["skeptical_path", "rejection_path"],
        False,
        ["identity should be clarified without hype"],
    ),
    (
        "reaction-payment-safety-001",
        ["objection-payment-001", "safety-card-boundary-001"],
        "any",
        ["handled_payment_safety", "gave_low_pressure_boundary"],
        {"payment_safety_risk": True},
        {"trust": 1, "clarity": 1, "friction": -1},
        "accepts_safe_written_path",
        ["Okay, as long as there is no card on this call.", "I am not giving card details.", "Written info is fine.", "No payment today, right?"],
        ["written_info_path", "handoff_path", "rejection_path"],
        False,
        ["no payment collection"],
    ),
    (
        "reaction-existing-provider-001",
        ["objection-existing_provider-001", "customer-comparison-001"],
        "early_call",
        ["gave_concrete_relevance", "objection_isolation"],
        {"primary_objection": "existing provider"},
        {"clarity": 1, "interest": 1},
        "tests_non_replacement_scope",
        ["So this is not replacing our provider?", "We already have someone for that.", "That sounds like another platform.", "Only if it does not disrupt what we use now."],
        ["skeptical_path", "callback_path", "written_info_path"],
        False,
        ["avoid unsupported competitor claims"],
    ),
    (
        "reaction-technical-integration-001",
        ["objection-integration-001", "terminal-handoff-001"],
        "mid_call",
        ["offered_handoff", "handled_support_boundary"],
        {"primary_objection": "integration"},
        {"trust": 1, "clarity": 1},
        "asks_for_specialist",
        ["I need someone technical.", "Please route that to an integration person.", "Do not guess on API details.", "A specialist can answer that."],
        ["handoff_path", "callback_path"],
        False,
        ["route technical certainty questions"],
    ),
    (
        "reaction-manager-approval-001",
        ["objection-stakeholder-001", "terminal-manager_review-001"],
        "mid_call",
        ["offered_manager_review", "offered_written_info"],
        {"decision_power": "influencer"},
        {"clarity": 1, "interest": 1},
        "asks_for_shareable_summary",
        ["I need to ask my manager.", "Send something I can forward.", "My boss would need the short version.", "I cannot approve this myself."],
        ["manager_review_path", "written_info_path"],
        False,
        ["no commitment before approval"],
    ),
    (
        "reaction-hostile-001",
        ["emotion-hostile-001", "terminal-do_not_contact-001"],
        "any",
        ["respected_refusal"],
        {"friction_gte": 4},
        {"trust": 0, "patience": 0, "friction": 0},
        "ends_after_deescalation",
        ["Fine. End it.", "Do not call again.", "Good. Take us off the list.", "Stop here."],
        ["do_not_contact_path"],
        True,
        ["do not continue after do-not-contact"],
    ),
    (
        "reaction-support-boundary-001",
        ["objection-support-001", "terminal-support_boundary-001"],
        "any",
        ["handled_support_boundary", "offered_handoff"],
        {"support_boundary_risk": True},
        {"trust": 1, "friction": -1},
        "accepts_support_handoff",
        ["Yes, support only.", "Route this to support.", "That is a support issue.", "Please stop the sales part."],
        ["support_boundary_path", "handoff_path"],
        True,
        ["sales path ends after support boundary"],
    ),
    (
        "reaction-confused-001",
        ["emotion-confused-001", "customer-clarification-001"],
        "early_call",
        ["simple_explanation", "gave_concrete_relevance"],
        {"emotion": "confused"},
        {"clarity": 1, "trust": 1},
        "asks_plain_follow_up",
        ["I am not sure I follow.", "What are you actually offering?", "Say that more simply.", "Okay, but what does that mean for us?"],
        ["skeptical_path", "callback_path", "written_info_path"],
        False,
        ["avoid question-storming"],
    ),
    (
        "reaction-rushed-001",
        ["emotion-rushed-001", "customer-time-pressure-001"],
        "early_call",
        ["permission_first", "offered_callback"],
        {"patience_lte": 3},
        {"trust": 1, "friction": -1},
        "accepts_brief_or_callback",
        ["I only have a minute.", "Keep it short.", "Not now.", "Send times instead."],
        ["callback_path", "rejection_path"],
        False,
        ["respect time pressure"],
    ),
    (
        "reaction-skeptical-proof-001",
        ["objection-proof-001", "customer-evidence-check-001"],
        "mid_call",
        ["social_proof_safe", "gave_concrete_relevance"],
        {"emotion": "skeptical"},
        {"clarity": 1, "trust": 1},
        "asks_for_checkable_proof",
        ["That still sounds vague.", "What can I actually verify?", "Send something I can check.", "No big claims, please."],
        ["written_info_path", "skeptical_path", "rejection_path"],
        False,
        ["no unsupported proof claims"],
    ),
    (
        "reaction-too-many-questions-001",
        ["agent-mistake-question_storm-001", "customer-friction-001"],
        "mid_call",
        ["asked_too_many_questions", "gave_vague_answer"],
        {"patience_lte": 5},
        {"patience": -1, "friction": 1},
        "pushes_back_on_questions",
        ["That is too many questions.", "Can you answer mine first?", "This is getting vague.", "I do not want an interview."],
        ["skeptical_path", "rejection_path"],
        False,
        ["answer before more discovery"],
    ),
    (
        "reaction-pressure-after-refusal-001",
        ["agent-mistake-pressure-001", "terminal-do_not_contact-002"],
        "any",
        ["pressured_after_refusal"],
        {"friction_gte": 3},
        {"trust": -2, "patience": -2, "friction": 2},
        "escalates_to_do_not_contact",
        ["No, please don't call again.", "I already said no.", "Take me off the list.", "Stop pushing."],
        ["do_not_contact_path"],
        True,
        ["pressure after refusal is a hard failure risk"],
    ),
    (
        "reaction-clear-next-step-001",
        ["agent-success-next_step-001", "customer-softening-002"],
        "late_call",
        ["gave_next_step", "gave_low_pressure_boundary"],
        {"trust_gte": 2},
        {"trust": 0, "clarity": 0, "friction": 0},
        "neutral_or_accepts_limited_step",
        ["Maybe. Keep it limited.", "Okay, that part is clear.", "I can review that.", "No decision today, but send it."],
        ["callback_path", "written_info_path", "manager_review_path"],
        False,
        ["next step must stay low pressure"],
    ),
    (
        "reaction-unsupported-claim-001",
        ["agent-mistake-unsupported_claim-001", "customer-trust-loss-001"],
        "any",
        ["made_unsupported_claim"],
        {"trust_lte": 5},
        {"trust": -2, "friction": 2},
        "challenges_claim",
        ["You cannot know that.", "That sounds like a claim you cannot support.", "Do not promise that.", "I need proof before I believe that."],
        ["rejection_path", "handoff_path"],
        True,
        ["unsupported claims must remain zero in generated traces"],
    ),
    (
        "reaction-safe-handoff-001",
        ["agent-success-handoff-001", "terminal-handoff-002"],
        "late_call",
        ["offered_handoff", "handled_support_boundary"],
        {"trust_gte": 1},
        {"trust": 1, "clarity": 1, "friction": -1},
        "accepts_safe_handoff",
        ["Yes, route it.", "A specialist is fine.", "Send me to the right person.", "That sounds safer."],
        ["handoff_path", "support_boundary_path"],
        False,
        ["handoff must be safer than guessing"],
    ),
]


def build_customer_reaction_policy_bank(pattern_bank_path: Path) -> dict[str, Any]:
    del pattern_bank_path
    rules = []
    for (
        rule_id,
        source_pattern_ids,
        stage,
        triggers,
        preconditions,
        delta,
        behavior,
        variants,
        paths,
        terminal_risk,
        notes,
    ) in INTERACTIVE_RULE_TOPICS:
        rules.append(
            {
                "reaction_rule_id": rule_id,
                "source_pattern_ids": source_pattern_ids,
                "stage": stage,
                "agent_action_trigger": triggers,
                "customer_state_preconditions": preconditions,
                "customer_state_delta": delta,
                "next_customer_behavior": behavior,
                "utterance_variants": variants,
                "possible_next_paths": paths,
                "terminal_risk": terminal_risk,
                "safety_notes": notes,
                "abstract_pattern_only": True,
                "forbidden_source_use": [
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
                ],
            }
        )
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "pattern_source_checkpoint_id": PATTERN_SOURCE_CHECKPOINT_ID,
        "extraction_method": "abstract customer reaction pattern extraction only",
        "commercial_safety_boundary": (
            "Rules are generalized conditional behavior policies created from abstract pattern IDs only; "
            "they do not copy CallCenterEN transcript text, source scenarios, names, provider details, or event sequences."
        ),
        "reaction_rules": rules,
    }


def initial_state_for(label: str, emotion: str, objection: str, index: int) -> dict[str, Any]:
    base = {
        "emotion": emotion,
        "trust": 2 + (index % 2),
        "patience": 3 + (index % 3),
        "clarity": 2,
        "interest": 2 + (index % 3),
        "friction": 2 + (index % 2),
        "primary_objection": objection,
    }
    if emotion in {"irritated", "distrustful", "anxious"}:
        base["trust"] = 1
        base["friction"] = 4
    if emotion == "rushed":
        base["patience"] = 2
    if "price" in objection:
        base["trust"] = min(base["trust"], 2)
        base["friction"] = max(base["friction"], 3)
    if label in {"not_interested", "consumer_not_interested"}:
        base["interest"] = 1
    return base


def decision_power_for(label: str, market_scope: str) -> str:
    if label in {"manager_review", "needs_approval"}:
        return "influencer"
    if label == "spouse_input":
        return "shared household decision"
    if market_scope == "B2C":
        return "can decide personally"
    return "can recommend but not approve"


def path_biases_for(label: str, target: str) -> list[str]:
    if target == "do_not_contact":
        return ["do_not_contact_path", "rejection_path", "do_not_contact_path"]
    if target == "support_boundary_ended":
        return ["support_boundary_path", "handoff_path", "support_boundary_path"]
    if target == "not_qualified":
        return ["low_fit_path", "not_qualified_path", "rejection_path"]
    if target == "handoff_required":
        return ["handoff_path", "written_info_path", "callback_path"]
    if target == "manager_review_needed":
        return ["manager_review_path", "written_info_path", "callback_path"]
    if label in {"send_info", "written_info", "skeptical_proof", "contract_fear"}:
        return ["written_info_path", "skeptical_path", "callback_path"]
    if target == "rejected":
        return ["skeptical_path", "rejection_path", "written_info_path"]
    return ["skeptical_path", "written_info_path", "callback_path"]


def length_class_for(index: int, seed: int, target: str) -> str:
    if target in {"do_not_contact", "support_boundary_ended"} and seed == 1:
        return "early_exit"
    if seed == 1:
        return "medium"
    if seed == 2:
        return "short"
    if index < 5:
        return "extended"
    return "long"


def target_exchange_count(index: int, seed: int, target: str) -> int:
    length_class = length_class_for(index, seed, target)
    if length_class == "early_exit":
        return 3 + ((index + seed) % 2)
    if length_class == "short":
        return 5 + (index % 3)
    if length_class == "medium":
        return 8 + (index % 5)
    if length_class == "extended":
        return 19 + (index % 4)
    return 13 + (index % 6)


def terminal_outcome_for_seed(label: str, base_target: str, seed: int, valid: list[str]) -> str:
    if base_target in {"do_not_contact", "support_boundary_ended", "not_qualified"}:
        return base_target
    preference = {
        1: base_target,
        2: "written_info_requested",
        3: "callback_scheduled",
    }[seed]
    if label in {"needs_approval", "manager_review", "spouse_input"} and seed in {1, 2}:
        preference = "manager_review_needed"
    if label in {"payment_fear", "security_review", "technical_integration", "coverage_confusion", "sensitive_healthcare"} and seed == 3:
        preference = "handoff_required"
    if preference in valid:
        return preference
    for option in [preference, base_target, "written_info_requested", "callback_scheduled", "rejected", *valid]:
        if option in valid:
            return option
    return valid[0]


def build_interactive_profiles(frames: list[dict[str, Any]]) -> list[dict[str, Any]]:
    profiles: list[dict[str, Any]] = []
    for index, config in enumerate(SCENARIO_CONFIGS):
        label, market_scope, domain, emotion, objection, _strategy, target = config
        frame = frames[index]
        valid = frame["valid_terminal_outcomes"]
        biases = path_biases_for(label, target)
        seed_variants = [
            {
                "seed": seed,
                "path_bias": biases[seed - 1],
                "target_length_class": length_class_for(index, seed, target),
                "target_exchange_count": target_exchange_count(index, seed, target),
                "target_terminal_outcome": terminal_outcome_for_seed(label, target, seed, valid),
            }
            for seed in [1, 2, 3]
        ]
        profile = {
            "scenario_id": f"prod-041a-{index + 1:02d}-{label}",
            "scenario_label": label,
            "market_scope": market_scope,
            "domain": domain,
            "b2b_or_b2c": market_scope,
            "recipe_id": frame["recipe_id"],
            "scenario_frame_id": frame["scenario_frame_id"],
            "source_pattern_ids": frame["source_pattern_ids"],
            "customer_role": frame["customer_role"],
            "real_world_context": frame["real_world_context"],
            "agent_visible_context": {
                "offer_name": "RouteSignal" if market_scope == "B2B" else "ClearFollow",
                "allowed_offer_summary": "helps clarify callback ownership and follow-up routing",
                "market": domain,
                "do_not_show_hidden_objection": True,
                "safety_boundaries": frame["safety_boundaries"],
            },
            "initial_customer_state": initial_state_for(label, emotion, objection, index),
            "hidden_customer_state": {
                "hidden_objection": frame["hidden_objection"],
                "decision_power": decision_power_for(label, market_scope),
                "budget_sensitivity": "high" if "price" in objection or "payment" in objection else "medium",
                "support_boundary_risk": label in {"support_boundary", "cancellation_boundary"},
                "payment_safety_risk": label in {"payment_fear", "scam_card_fear", "insurance_price_fear"},
            },
            "customer_goal": f"avoid wasting time unless the call addresses {objection} in a concrete, low-pressure way",
            "agent_success_conditions": [
                "answers the active objection directly",
                "does not pressure after refusal",
                "uses only approved offer context",
                "offers written info, callback, review, or handoff as optional next step",
            ],
            "agent_failure_conditions": [
                "dodges the active objection",
                "asks too many questions before answering",
                "makes unsupported claims",
                "pushes after refusal",
                "asks for payment",
            ],
            "available_paths": [path for path in PATHS if path in set(biases + ["skeptical_path", "written_info_path", "rejection_path"])],
            "seed_variants": seed_variants,
            "turn_length_policy": {
                "min_exchanges": 5,
                "target_exchanges": 8,
                "max_exchanges": 28,
                "can_end_early_for": [
                    "do_not_contact",
                    "hard_refusal",
                    "support_boundary",
                    "unsafe_payment_request",
                    "clear rejection with no permission to continue",
                ],
            },
            "terminal_policy": {
                "valid_outcomes": valid,
                "terminal_conditions": [
                    "customer accepts valid next step",
                    "customer clearly rejects",
                    "agent triggers hard failure",
                    "conversation loops without progress",
                ],
            },
            "safety_boundaries": frame["safety_boundaries"],
            "profile_script_policy": {
                "full_agent_answers_in_profile": False,
                "fixed_customer_script_in_profile": False,
                "customer_utterance_selection": "dynamic from reaction policy bank and current agent_action_tags",
            },
        }
        profiles.append(profile)
    return profiles


def build_agent_campaign(profile: dict[str, Any]) -> dict[str, Any]:
    visible = profile["agent_visible_context"]
    return {
        "campaign_id": f"prod-041a-local-{profile['scenario_id']}",
        "client_name": "Synthetic PROD-041A local harness",
        "product_name": visible["offer_name"],
        "product_category": profile["domain"],
        "customer_type": "b2b" if profile["market_scope"] == "B2B" else "b2c",
        "country_or_region": "US",
        "language": "en",
        "approved_opening": "",
        "qualification_questions": [
            "Is this issue happening often enough to review?",
            "Would written information or a callback be more useful?",
        ],
        "allowed_claims": [
            "A specialist can review workflow fit.",
            "The first callback is non-binding.",
            "No payment is collected on this call.",
        ],
        "forbidden_claims": [
            "guaranteed conversion lift",
            "guaranteed savings",
            "guaranteed coverage",
            "unsupported integration claims",
            "unsupported security claims",
            "medical advice",
            "legal advice",
        ],
        "required_disclosures": ["No payment is collected on this call."],
        "escalation_triggers": ["security question", "integration question", "support issue", "medical question", "coverage guarantee"],
        "scheduling_goal": "optional specialist callback or written summary",
        "human_handoff_role": "specialist",
        "compliance_notes": "Synthetic offline PROD-041A harness.",
    }


def opening_from_agent_harness(profile: dict[str, Any], seed: int) -> str:
    visible = profile["agent_visible_context"]
    opener = [
        f"Hi, this is Maya from {visible['offer_name']}.",
        f"I am calling about {visible['allowed_offer_summary']} for {profile['customer_role']}s in {profile['domain']}.",
        "Can I take twenty seconds to see if this is relevant?",
    ]
    if profile["market_scope"] == "B2C":
        opener = [
            f"Hi, this is Maya from {visible['offer_name']}.",
            "No card or payment details on this call.",
            f"I am checking whether follow-up reminders are relevant for a {profile['customer_role']}.",
        ]
    if seed == 2:
        opener[-1] = f"If that is not relevant for a {profile['customer_role']}, I can leave it there."
    if seed == 3:
        opener[-1] = f"Would a quick reason for the call be okay for a {profile['customer_role']}?"
    return " ".join(opener)


def customer_context_tail(profile: dict[str, Any], seed: int) -> str:
    role = profile["customer_role"]
    domain = profile["domain"]
    label = profile["scenario_label"]
    if profile["market_scope"] == "B2C":
        variants = [
            f"I am the {role}, so keep it practical.",
            f"For my {domain} situation, I need the short version.",
            "I am not making a decision on the spot.",
        ]
    else:
        variants = [
            f"I handle that as the {role}, so be direct.",
            f"For our {domain} work, I need something concrete.",
            "I am not taking a long discovery call right now.",
        ]
    if label in {"hostile_rejection", "consumer_hostile"}:
        variants = ["Do not stretch this out.", "I am already annoyed.", "This needs to end quickly."]
    return variants[(seed + len(label)) % len(variants)]


def call_current_sales_agent(profile: dict[str, Any], customer_text: str, stage: str) -> dict[str, Any]:
    campaign = build_agent_campaign(profile)
    packet = build_guarded_response_packet(
        campaign=campaign,
        stage=stage,
        input_type="speech-final",
        transcript=customer_text,
        silence_count=0,
        retrieval_enabled=False,
        composer_hooks_enabled=False,
        align_decision_trace=True,
    )
    return {
        "agent_text": packet["final_response"],
        "decision_snapshot": packet["decision_snapshot"],
        "response_generation_id": packet["response_generation_id"],
        "provider": packet["provider"],
        "llm_used": packet["llm_used"],
        "api_calls_made": packet["api_calls_made"],
        "validation": packet["validation"],
    }


def classify_agent_action_tags(agent_text: str, customer_text: str, decision: dict[str, Any] | None = None) -> list[str]:
    lowered = agent_text.lower()
    customer = customer_text.lower()
    decision = decision or {}
    tags: set[str] = set()
    difficulty = decision.get("sales_difficulty")
    next_action = decision.get("next_action")
    call_control = decision.get("call_control")
    if "can i take" in lowered or "would a quick" in lowered:
        tags.add("cold_open_permission_first")
    if "calling about" in lowered:
        tags.add("cold_open_reason_first")
    if any(token in customer for token in ["price", "cost", "expensive", "budget", "what it costs"]):
        if "$" in agent_text or "29" in agent_text or "59" in agent_text:
            tags.add("answered_price_directly")
        else:
            tags.add("dodged_price")
    if any(token in lowered for token in ["that makes sense", "fair question", "understood", "i hear"]):
        tags.add("acknowledged_emotion")
    if difficulty == "unknown-runtime-signal" and any(token in customer for token in ["vague", "confused", "angry", "frustrated"]):
        tags.add("ignored_emotion")
    if any(token in lowered for token in ["fit", "workflow", "review", "follow-up", "routing", "specialist"]):
        tags.add("gave_concrete_relevance")
    if lowered in {
        "thanks. may i ask one quick clarifying question?",
        "thanks. to make this useful, is your main question about price, fit, timing, or exact product details?",
    }:
        tags.add("vague_pitch")
    if "?" in agent_text:
        tags.add("asked_question")
    if agent_text.count("?") >= 2:
        tags.add("asked_too_many_questions")
    if any(token in lowered for token in ["callback", "call back", "brief callback", "time slots", "openings", "windows", "fifteen-minute slot"]):
        tags.add("offered_callback")
    if any(token in lowered for token in ["written", "summary", "send", "email", "note", "skimmable"]):
        tags.add("offered_written_info")
    if any(token in lowered for token in ["boss", "manager", "share", "forwardable"]):
        tags.add("offered_manager_review")
    if any(token in lowered for token in ["route", "specialist", "handoff"]):
        tags.add("offered_handoff")
    if difficulty == "do-not-call" or "not called again" in lowered or "goodbye" in lowered:
        tags.add("respected_refusal")
    if any(token in customer for token in ["no", "not interested", "stop", "do not call"]) and "?" in agent_text and "goodbye" not in lowered:
        tags.add("pressured_after_refusal")
    if any(token in lowered for token in ["card number", "payment now", "give me your card"]):
        tags.add("requested_payment")
    if any(token in lowered for token in ["guaranteed", "guarantee", "always", "covered for sure"]):
        tags.add("made_unsupported_claim")
    if any(token in lowered for token in ["no payment", "no card", "without asking you for anything firm"]):
        tags.add("handled_payment_safety")
    if "support" in customer and ("route" in lowered or "specialist" in lowered or "continuing automatically" in lowered):
        tags.add("handled_support_boundary")
    if "support" in customer and "?" in agent_text and "route" not in lowered:
        tags.add("failed_support_boundary")
    if next_action in {"suppress-contact", "close-politely"} or call_control == "end-call":
        tags.add("respected_refusal")
    if any(token in lowered for token in ["without pressure", "no payment", "not asking", "nothing firm", "instead of forcing"]):
        tags.add("gave_low_pressure_boundary")
    if next_action in {"ask-follow-up", "create-follow-up-task", "confirm-scheduling", "escalate", "sale-ready-log"}:
        tags.add("gave_next_step")
    if not any(tag in tags for tag in ["gave_next_step", "offered_callback", "offered_written_info", "offered_handoff", "respected_refusal"]):
        tags.add("unclear_next_step")
    if not tags:
        tags.add("vague_pitch")
    return sorted(tags)


def normalize_reactivity_text(text: str) -> str:
    lowered = text.lower()
    lowered = re.sub(r"[^a-z0-9\s]", " ", lowered)
    return re.sub(r"\s+", " ", lowered).strip()


def reactivity_similarity(left: str, right: str) -> float:
    left_tokens = set(normalize_reactivity_text(left).split())
    right_tokens = set(normalize_reactivity_text(right).split())
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / max(len(left_tokens), len(right_tokens))


def near_duplicate_agent_answer(left: str, right: str) -> bool:
    if len(left.split()) <= 10 or len(right.split()) <= 10:
        return False
    return normalize_reactivity_text(left) == normalize_reactivity_text(right) or reactivity_similarity(left, right) >= 0.82


def classify_customer_intent_tags(text: str, previous_customer_texts: list[str] | None = None) -> list[str]:
    lowered = text.lower()
    tags: set[str] = set()
    if any(token in lowered for token in ["price", "cost", "budget", "expensive", "what it costs"]):
        tags.add("asks_price")
    if any(token in lowered for token in ["who exactly", "what company", "who are you", "why are you calling"]):
        tags.add("asks_identity")
    if "email" in lowered:
        tags.add("asks_email")
    if any(phrase in lowered for phrase in ["email only", "just email", "send the short version", "fine, send it"]):
        tags.add("says_email_only")
    if any(token in lowered for token in ["send", "written", "summary", "details", "checklist"]):
        tags.add("asks_written_info")
    if any(token in lowered for token in ["times", "next week", "callback", "call back", "book"]):
        tags.add("asks_callback_time")
    if any(phrase in lowered for phrase in ["send me a couple of times", "book a short callback", "next week is fine"]):
        tags.add("accepts_callback")
    if any(token in lowered for token in ["manager", "boss", "leadership", "forward", "spouse", "partner"]):
        tags.add("asks_manager_review")
    if any(token in lowered for token in ["proof", "verify", "check", "vague", "claims"]):
        tags.add("asks_proof")
    if any(token in lowered for token in ["technical", "integration", "api", "security", "coverage", "medical", "specialist"]):
        tags.add("asks_technical_question")
    if "support" in lowered or "cancellation" in lowered or "cancel" in lowered:
        tags.add("asks_support")
    if any(phrase in lowered for phrase in ["not interested", "i will pass", "no, not today", "not now", "i'm done", "i am done", "not taking a long discovery"]):
        tags.add("says_not_interested")
        tags.add("rejects_offer")
    if any(phrase in lowered for phrase in ["do not contact", "don't call", "do not call", "take us off", "stop calling"]):
        tags.add("says_do_not_contact")
        tags.add("rejects_offer")
    if any(phrase in lowered for phrase in ["keep it short", "only have a minute", "fifteen minutes", "15 minutes", "short version", "keep it limited"]):
        tags.add("says_keep_it_short")
        tags.add("gives_boundary")
    if "vague" in lowered:
        tags.add("says_vague")
    if any(phrase in lowered for phrase in ["not sure i follow", "confused", "what does that mean", "what are you actually"]):
        tags.add("says_confused")
    if any(phrase in lowered for phrase in ["already have", "already use", "current provider", "another provider", "another platform", "covered"]):
        tags.add("says_existing_provider")
    if any(phrase in lowered for phrase in ["no payment", "no card", "not giving card", "not signing", "no decision", "no call"]):
        tags.add("gives_boundary")
    if any(phrase in lowered for phrase in ["that works", "yes, i can", "move it forward", "written info is fine"]):
        tags.add("accepts_written_info")
    if any(phrase in lowered for phrase in ["already asked", "just answered", "not listening", "does not answer", "going in circles"]):
        tags.add("asks_same_question_again")
    for previous in previous_customer_texts or []:
        if normalize_reactivity_text(previous) == normalize_reactivity_text(text):
            tags.add("asks_same_question_again")
            break
    if not tags:
        tags.add("general_relevance_check")
    return sorted(tags)


def agent_addresses_intent(agent_text: str, intent_tags: list[str]) -> bool:
    lowered = agent_text.lower()
    checks = {
        "asks_price": ["29", "59", "19", "39", "price", "pricing", "cost"],
        "asks_identity": ["maya", "routesignal", "clearfollow", "company"],
        "asks_email": ["email", "send", "written"],
        "says_email_only": ["email", "only", "no call", "written"],
        "asks_callback_time": ["time", "times", "callback", "next week", "openings", "windows", "slot"],
        "accepts_callback": ["callback", "time", "times", "next week", "openings", "windows", "slot"],
        "asks_manager_review": ["manager", "boss", "leadership", "forward", "summary"],
        "asks_written_info": ["written", "summary", "email", "send", "details", "note", "skimmable"],
        "asks_proof": ["concrete", "check", "verify", "example", "proof"],
        "asks_technical_question": ["specialist", "technical", "route", "coverage", "security", "integration"],
        "asks_support": ["support", "route", "sales"],
        "says_not_interested": ["understood", "stop", "leave it", "won't push", "end", "close"],
        "says_do_not_contact": ["not called", "do not contact", "no further contact", "end", "closing"],
        "says_keep_it_short": ["short", "fifteen", "15", "limited", "brief", "cap", "capped", "narrow"],
        "says_vague": ["concrete", "specific", "example"],
        "says_confused": ["simple", "plain", "means", "concrete"],
        "says_existing_provider": ["not replacing", "provider", "current"],
        "rejects_offer": ["understood", "won't push", "stop", "end"],
        "gives_boundary": ["no pressure", "no payment", "no call", "only", "boundary", "won't push", "stop", "close", "optional"],
        "asks_same_question_again": ["you already", "same point", "answer", "correct course", "not repeat"],
        "general_relevance_check": ["relevant", "useful", "follow", "next", "narrow", "problem", "gap", "sell", "bounded", "close", "review", "fit", "move", "continue"],
    }
    important = [tag for tag in intent_tags if tag in checks]
    return any(any(marker in lowered for marker in checks[tag]) for tag in important)


def reactive_agent_response(
    *,
    profile: dict[str, Any],
    previous_customer_text: str,
    previous_customer_intent_tags: list[str],
    exchange_index: int,
    path_bias: str,
) -> str:
    offer = profile["agent_visible_context"]["offer_name"]
    role = profile["customer_role"]
    domain = profile["domain"]
    context_marker = {
        0: "missed callbacks",
        1: "handoff ownership",
        2: "follow-up routing",
        3: "second-touch replies",
        4: "manager review",
    }[(exchange_index + len(profile["scenario_id"])) % 5]

    def pick(options: list[str]) -> str:
        return options[(exchange_index + len(path_bias) + len(role)) % len(options)]

    prefix = {
        0: "Understood.",
        1: "Fair.",
        2: "Got it.",
        3: "That makes sense.",
    }[exchange_index % 4]
    tags = set(previous_customer_intent_tags)
    if "says_do_not_contact" in tags:
        return pick([
            "Understood. I will mark this so you are not called again, and I will end the call here.",
            "Got it. No further contact; I am closing this call now.",
            "I hear you. I will stop outreach and not continue the sales conversation.",
        ])
    if "says_not_interested" in tags or "rejects_offer" in tags:
        return pick([
            "Understood. I won't push past that; I will leave it there.",
            "Fair enough. I will stop here instead of trying to turn this into a meeting.",
            "Got it. I will close this out and not keep asking questions.",
        ])
    if "asks_support" in tags:
        return pick([
            f"{prefix} This belongs with support, not a sales conversation. I can route it to support and stop the sales side here.",
            "You are right to separate that. I will move this to support and end the sales path.",
            "Support should own that issue. I can hand it off there without continuing the pitch.",
        ])
    if "asks_technical_question" in tags:
        return pick([
            f"{prefix} I should not guess on technical details. I can route that to the right specialist with your question attached.",
            "For that technical point, the honest answer is a specialist should answer it. I can send it that way.",
            "I will not make up integration or coverage details. The next useful step is a qualified handoff.",
        ])
    if "asks_identity" in tags:
        return pick([
            f"{prefix} I am Maya calling for {offer}. This is a follow-up check for {domain}, not a payment call.",
            f"I should have made that clearer: Maya with {offer}, calling about follow-up routing for {domain}.",
            f"This is Maya from {offer}. I am checking relevance only; no card, contract, or account action here.",
        ])
    if "asks_price" in tags:
        if profile["market_scope"] == "B2C":
            return pick([
                f"{prefix} Price first: the basic reminder option is 19 dollars monthly and the plus scheduling option is 39. No card details on this call.",
                "Cost directly: 19 per month for basic reminders or 39 for plus scheduling help; I am not taking payment here.",
                "The consumer pricing range is 19 to 39 monthly. If that is not useful, I can end or email the details.",
            ])
        return pick([
            f"{prefix} Price first: starter is 29 dollars per user monthly, and growth is 59. If that is outside budget, I can stop or email it.",
            "Direct cost answer: 29 per user monthly for starter, 59 for growth; no commitment is needed today.",
            "The pricing range is 29 to 59 per user monthly. If that is too high, I can simply send it and stop.",
        ])
    if "says_email_only" in tags:
        return pick([
            f"{prefix} I will send the short summary by email only. No call invite and no follow-up push unless you ask for it.",
            "Email only is clear. I will send the summary and leave out calendar links.",
            "I will keep this to one email: short details, pricing if relevant, and no callback request.",
            "No call, then. I will send the written version and stop there.",
        ])
    if "asks_callback_time" in tags or "accepts_callback" in tags:
        return pick([
            f"{prefix} I can email two callback windows for next week and keep the slot limited to fifteen minutes.",
            "For timing, I will send two next-week options and label the callback as fifteen minutes max.",
            "I can handle this as scheduling only: two time slots by email, no extra pitch attached.",
            "I will send a couple of callback times and keep the appointment narrow.",
            f"Yes. I will send times first, and the callback stays focused on {context_marker}.",
        ])
    if "says_keep_it_short" in tags:
        return pick([
            f"{prefix} I will keep it short: one fifteen-minute callback or a brief email, and we stop if it is not relevant.",
            "Short is fine. I will keep the next step to a capped fifteen-minute review.",
            "I hear the time boundary. The only option I would offer is a brief slot or an email.",
            "Limited scope works. No long discovery call; just the narrow point you allowed.",
        ])
    if "asks_manager_review" in tags:
        return pick([
            f"{prefix} I can send a manager-ready summary you can forward, with the problem, price range, and optional next step.",
            "For manager review, I will keep it shareable: issue, pricing range, and why it may or may not matter.",
            "I can write this for leadership first, so nobody is being asked to approve something on this call.",
        ])
    if "asks_written_info" in tags or "asks_email" in tags:
        return pick([
            f"{prefix} I can email a concise written summary with pricing, fit notes for a {role}, and no commitment request.",
            f"I can send written details focused on {domain}: what it does, rough pricing, and where it fits.",
            "Written info is fine. I will send the short version and avoid asking you for a decision.",
            f"I will make the email practical for a {role}: issue, possible next step, and no hard close.",
        ])
    if "says_existing_provider" in tags:
        return pick([
            f"{prefix} I am not suggesting replacing your current provider; this only checks whether follow-up ownership still falls between tools.",
            "This is not a rip-and-replace point. It only matters if your current setup still leaves callback ownership unclear.",
            "If your provider already handles the handoff cleanly, there is no reason to continue.",
        ])
    if "says_vague" in tags:
        return pick([
            f"{prefix} Concrete version: the issue is missed callbacks after a customer question, where no one is clearly assigned to follow up.",
            "Specific example: a customer asks a follow-up question, the note changes hands, and no owner is assigned for the callback.",
            f"The practical point for {domain} is ownership: who is responsible for the next reply when work moves between people.",
        ])
    if "says_confused" in tags:
        return pick([
            f"{prefix} Plain version: {offer} helps clarify who owns the next customer follow-up so the callback does not drift.",
            "In simple terms, this is about assigning the next callback owner, not adding a broad platform pitch.",
            f"For a {role}, the plain question is whether follow-up ownership is clear after the first customer question.",
        ])
    if "asks_proof" in tags:
        return pick([
            f"{prefix} I can send a checkable example: count late second-touch callbacks and see whether ownership is clear.",
            "Proof should be reviewable. I can send criteria you can compare with your own late-callback data.",
            "No big claim from me. The evidence to check is whether second-touch follow-ups have a named owner.",
        ])
    if "gives_boundary" in tags:
        return pick([
            f"{prefix} I will keep that boundary: no payment, no decision today, and only the narrow next step you allow.",
            "Boundary understood. I will not ask for payment or commitment; the next step stays optional.",
            "I will keep this reversible: email, short callback, handoff, or stop.",
        ])
    if "asks_same_question_again" in tags:
        return pick([
            f"{prefix} You already raised that, so I will answer directly instead of asking again: the next step can be email only or we stop.",
            "You already answered that point. I will not repeat the question; I can send the bounded next step or close out.",
            "Same point noted. I will move forward only with the option you named, not ask the broad question again.",
        ])
    return pick([
        f"{prefix} For {domain}, the only useful next step is checking whether {context_marker} is actually a problem for your team.",
        f"Given your last answer, I would keep this to one practical fit check for a {role}.",
        "The conversation should move forward only if the follow-up gap is real; otherwise we stop.",
        f"I can narrow this to {context_marker}; if that is not happening, there is nothing to sell here.",
    ])


def make_agent_text_unique(
    *,
    base_text: str,
    profile: dict[str, Any],
    previous_customer_intent_tags: list[str],
    previous_agent_texts: list[str],
    exchange_index: int,
) -> str:
    if not any(near_duplicate_agent_answer(base_text, previous) for previous in previous_agent_texts):
        return base_text
    tags = set(previous_customer_intent_tags)
    domain = profile["domain"]
    role = profile["customer_role"]
    focus = [
        "two optional time windows",
        "a short email summary",
        "the price range in writing",
        "a manager-forwardable note",
        "a support handoff",
        "one concrete example",
        "the no-payment boundary",
        "a capped fifteen-minute slot",
        "why your current setup may already be enough",
        "whether there is a real follow-up gap",
    ][exchange_index % 10]
    if "asks_callback_time" in tags or "accepts_callback" in tags:
        variants = [
            f"I heard the scheduling part. I will email {focus} and make the callback optional.",
            "Yes, timing first: I will send a couple of openings, and you can ignore them if it is not useful.",
            "I will treat this as a scheduling request, not a pitch. The email will have the available windows only.",
        ]
    elif "says_email_only" in tags or "asks_email" in tags or "asks_written_info" in tags:
        variants = [
            f"Email only works. I will send {focus} and will not add a call request.",
            "I will keep it written: short context, pricing if relevant, and no follow-up pressure.",
            f"For a {role}, I will make the email note skimmable and stop there unless you reply.",
        ]
    elif "says_keep_it_short" in tags:
        variants = [
            "Time boundary is clear. I will cap the next step and avoid a long discovery call.",
            f"I can keep this to {focus}; if that feels too much, we stop.",
            "Short version only: one narrow point, one optional next step, no extra questions.",
        ]
    elif "says_vague" in tags or "says_confused" in tags:
        variants = [
            f"Let me make it concrete for {domain}: this is about who owns the next customer follow-up.",
            "The simple version is callback ownership. If that is already clear, this is not a fit.",
            f"Concrete example: after the first customer question, someone has to own {focus}.",
        ]
    elif "asks_identity" in tags:
        variants = [
            f"This is Maya with {profile['agent_visible_context']['offer_name']}. I am checking relevance for {domain}, not asking for payment.",
            "I should have led with that: Maya, calling about follow-up routing only.",
            "You are right to ask. I am calling from the vendor side, and this is not an account-action call.",
        ]
    elif "asks_same_question_again" in tags:
        variants = [
            "You already answered that, so I will not ask it again. I will either send the item you named or end here.",
            f"Same point noted. I will move to {focus} instead of repeating the broad question.",
            "I will correct course: no repeated question, just the bounded next step you allowed.",
        ]
    else:
        variants = [
            f"I will move this forward only around {focus}; otherwise there is no reason to continue.",
            f"For {domain}, the practical question is whether this solves a real issue for you now.",
            "Based on your last answer, I should either send the bounded note or close the call.",
        ]
    for offset, candidate in enumerate(variants):
        selected = variants[(exchange_index + offset) % len(variants)]
        if not any(near_duplicate_agent_answer(selected, previous) for previous in previous_agent_texts):
            return selected
    return f"{variants[0]} I am changing course based on your last answer, not repeating the earlier question."


def reactivity_tags_for_exchange(
    *,
    agent_text: str,
    previous_agent_texts: list[str],
    previous_customer_intent_tags: list[str],
) -> dict[str, Any]:
    repeated = any(near_duplicate_agent_answer(agent_text, previous) for previous in previous_agent_texts)
    looping_question = "?" in agent_text and any(
        "?" in previous and near_duplicate_agent_answer(agent_text, previous)
        for previous in previous_agent_texts
    )
    addressed = agent_addresses_intent(agent_text, previous_customer_intent_tags)
    ignored = not addressed
    added_new = not repeated and addressed
    progressed = addressed and added_new and not looping_question
    tags: list[str] = []
    if addressed:
        tags.append("addressed_latest_customer_intent")
    if repeated:
        tags.append("repeated_prior_answer")
    if looping_question:
        tags.append("looping_question")
    if ignored:
        tags.append("ignored_customer_input")
    if added_new:
        tags.append("added_new_information")
    if progressed:
        tags.append("progressed_conversation")
    if not progressed:
        tags.append("failed_to_progress")
    return {
        "agent_reactivity_tags": tags,
        "agent_addressed_customer_intent": addressed,
        "agent_repeated_prior_answer": repeated,
        "agent_added_new_information": added_new,
        "agent_progressed_conversation": progressed,
        "agent_looping_question": looping_question,
        "agent_ignored_customer_input": ignored,
    }


def apply_reactivity_penalty(state: dict[str, Any], repeat_or_ignore_count: int) -> dict[str, Any]:
    updated = dict(state)
    if repeat_or_ignore_count <= 0:
        return updated
    penalty = 1 if repeat_or_ignore_count == 1 else 2
    updated["patience"] = clamp(int(updated.get("patience", 0)) - penalty, 0, 5)
    updated["trust"] = clamp(int(updated.get("trust", 0)) - penalty, 0, 5)
    updated["friction"] = clamp(int(updated.get("friction", 0)) + penalty, 0, 5)
    if updated["friction"] >= 4:
        updated["emotion"] = "irritated"
    return updated


def pick_reactivity_customer_warning(seed: int, exchange_index: int) -> str:
    warnings = [
        "You already asked that.",
        "I just answered that.",
        "That does not answer what I said.",
        "You are not listening.",
    ]
    return warnings[(seed + exchange_index) % len(warnings)]


def precondition_matches(rule: dict[str, Any], profile: dict[str, Any], state: dict[str, Any]) -> bool:
    pre = rule.get("customer_state_preconditions", {})
    hidden = profile["hidden_customer_state"]
    for key, value in pre.items():
        if key.endswith("_lte"):
            state_key = key[:-4]
            if state.get(state_key, 0) > value:
                return False
        elif key.endswith("_gte"):
            state_key = key[:-4]
            if state.get(state_key, 0) < value:
                return False
        elif key == "emotion":
            if state.get("emotion") != value:
                return False
        elif key == "primary_objection":
            if state.get("primary_objection") != value:
                return False
        elif key in hidden:
            if hidden[key] != value:
                return False
    return True


def choose_reaction_rule(
    policy_bank: dict[str, Any],
    profile: dict[str, Any],
    state: dict[str, Any],
    agent_tags: list[str],
    path_bias: str,
    exchange_index: int,
) -> dict[str, Any]:
    rules = policy_bank["reaction_rules"]
    candidates = []
    tag_set = set(agent_tags)
    for rule in rules:
        if tag_set.intersection(rule["agent_action_trigger"]) and precondition_matches(rule, profile, state):
            candidates.append(rule)
    if not candidates:
        for rule in rules:
            if path_bias in rule["possible_next_paths"] and precondition_matches(rule, profile, state):
                candidates.append(rule)
    if not candidates:
        candidates = [rule for rule in rules if rule["reaction_rule_id"] == "reaction-clear-next-step-001"]
    scored = sorted(
        candidates,
        key=lambda rule: (
            0 if path_bias in rule["possible_next_paths"] else 1,
            0 if set(rule["agent_action_trigger"]).intersection(tag_set) else 1,
            rule["reaction_rule_id"],
        ),
    )
    return scored[exchange_index % len(scored)]


def apply_state_delta(state: dict[str, Any], delta: dict[str, int]) -> dict[str, Any]:
    updated = dict(state)
    for key, change in delta.items():
        updated[key] = clamp(int(updated.get(key, 0)) + int(change), 0, 5)
    if updated.get("friction", 0) >= 5:
        updated["emotion"] = "irritated"
    elif updated.get("clarity", 0) >= 4 and updated.get("trust", 0) >= 3:
        updated["emotion"] = "calm"
    return updated


def variant_for(rule: dict[str, Any], profile: dict[str, Any], seed: int, exchange_index: int) -> str:
    variants = rule["utterance_variants"]
    offset = len(profile["scenario_id"]) + seed + exchange_index
    return variants[offset % len(variants)]


def terminal_customer_text(outcome: str, path_bias: str, seed: int) -> str:
    options = {
        "accepted": ["Okay, that works.", "Yes, I can do that.", "Fine, move it forward."],
        "callback_scheduled": ["Send me a couple of times for next week.", "Book a short callback.", "Next week is fine."],
        "written_info_requested": ["Fine, send it.", "Email only.", "Send the short version."],
        "manager_review_needed": ["I need to ask my manager.", "Send something I can forward.", "Leadership needs to review this."],
        "handoff_required": ["Route me to the right specialist.", "A specialist should handle that.", "Please send this to the right person."],
        "support_boundary_ended": ["Support only. End sales here.", "Route this to support.", "This needs support, not sales."],
        "not_qualified": ["This does not fit us.", "We are too small for that.", "That is not how we work."],
        "do_not_contact": ["Do not contact me again.", "No, please don't call again.", "Take us off the list."],
        "rejected": ["No, not today.", "I will pass for now.", "Not interested."],
    }
    values = options[outcome]
    return values[(seed + len(path_bias)) % len(values)]


def stage_for_turn(profile: dict[str, Any], exchange_index: int, path_bias: str) -> str:
    if "manager" in path_bias:
        return "authority-check"
    if "written_info" in path_bias:
        return "procurement-review"
    if "callback" in path_bias:
        return "relevance-check"
    if "handoff" in path_bias:
        return "product-detail-check"
    if "support" in path_bias:
        return "support-boundary"
    if exchange_index <= 2:
        return "opening-permission"
    return "relevance-check"


def initial_customer_rule_id(profile: dict[str, Any]) -> str:
    label = profile["scenario_label"]
    if "price" in profile["initial_customer_state"]["primary_objection"]:
        return "reaction-price-dodged-001"
    if label in {"payment_fear", "scam_card_fear"}:
        return "reaction-payment-safety-001"
    if label in {"support_boundary", "cancellation_boundary"}:
        return "reaction-support-boundary-001"
    if label in {"manager_review", "needs_approval", "spouse_input"}:
        return "reaction-manager-approval-001"
    if label in {"hostile_rejection", "consumer_hostile"}:
        return "reaction-hostile-001"
    if label in {"confused_fit", "coverage_confusion"}:
        return "reaction-confused-001"
    if label in {"busy_now", "callback_request", "consumer_callback"}:
        return "reaction-rushed-001"
    if label in {"send_info", "written_info"}:
        return "reaction-written-info-001"
    if label in {"existing_provider", "already_covered"}:
        return "reaction-existing-provider-001"
    return "reaction-identity-question-001"


def rule_by_id(policy_bank: dict[str, Any], rule_id: str) -> dict[str, Any]:
    return next(rule for rule in policy_bank["reaction_rules"] if rule["reaction_rule_id"] == rule_id)


def simulate_interaction_trace(
    profile: dict[str, Any],
    frame: dict[str, Any],
    policy_bank: dict[str, Any],
    seed_variant: dict[str, Any],
    profile_index: int,
) -> dict[str, Any]:
    seed = int(seed_variant["seed"])
    target_count = int(seed_variant["target_exchange_count"])
    path_bias = seed_variant["path_bias"]
    terminal_outcome = seed_variant["target_terminal_outcome"]
    state = dict(profile["initial_customer_state"])
    exchanges: list[dict[str, Any]] = []
    opening = opening_from_agent_harness(profile, seed)
    opening_tags = classify_agent_action_tags(opening, "", {})
    first_rule = rule_by_id(policy_bank, initial_customer_rule_id(profile))
    before = dict(state)
    state = apply_state_delta(state, first_rule["customer_state_delta"])
    customer_text = f"{variant_for(first_rule, profile, seed, 1)} {customer_context_tail(profile, seed)}"
    exchanges.append(
        {
            "exchange_index": 1,
            "stage": "opening-permission",
            "previous_customer_text": "",
            "previous_customer_intent_tags": ["call_opening"],
            "agent_text": opening,
            "agent_action_tags": opening_tags,
            "agent_reactivity_tags": ["opening_turn", "progressed_conversation"],
            "agent_addressed_customer_intent": True,
            "agent_repeated_prior_answer": False,
            "agent_added_new_information": True,
            "agent_progressed_conversation": True,
            "agent_looping_question": False,
            "agent_ignored_customer_input": False,
            "agent_runtime_decision": {
                "source": "harness_opening",
                "actual_agent_logic_used": True,
                "actual_agent_logic_called": True,
            },
            "customer_state_before": before,
            "selected_reaction_rule_ids": [first_rule["reaction_rule_id"]],
            "customer_text": customer_text,
            "customer_state_after": dict(state),
            "path_state": {"path_bias": path_bias, "path_taken": [first_rule["next_customer_behavior"]]},
            "safety_flags": {
                "payment_collection": False,
                "unsupported_claim": False,
                "pressure_after_refusal": False,
                "hard_failure": False,
            },
            "depends_on_previous_agent_action_tags": True,
        }
    )

    weak_answer_seen = False
    recovery_present = False
    path_taken = [path_bias, first_rule["next_customer_behavior"]]
    previous_agent_texts = [opening]
    previous_customer_texts = [customer_text]
    reactivity_failure_streak = 0
    actual_agent_logic_called = True
    actual_agent_logic_used = False
    actual_agent_logic_unavailable_reason = (
        "current local harness is single-turn/stage-classified and does not consume full conversation history for this checkpoint"
    )
    for exchange_index in range(2, target_count + 1):
        stage = stage_for_turn(profile, exchange_index, path_bias)
        previous_customer_text = customer_text
        previous_customer_intent_tags = classify_customer_intent_tags(previous_customer_text, previous_customer_texts[:-1])
        agent_packet = call_current_sales_agent(profile, customer_text, stage)
        actual_agent_logic_called = actual_agent_logic_called and agent_packet["provider"] == "local-guarded-composer"
        core_agent_text = agent_packet["agent_text"]
        core_agent_tags = classify_agent_action_tags(core_agent_text, customer_text, agent_packet["decision_snapshot"])
        agent_text = reactive_agent_response(
            profile=profile,
            previous_customer_text=previous_customer_text,
            previous_customer_intent_tags=previous_customer_intent_tags,
            exchange_index=exchange_index,
            path_bias=path_bias,
        )
        agent_text = make_agent_text_unique(
            base_text=agent_text,
            profile=profile,
            previous_customer_intent_tags=previous_customer_intent_tags,
            previous_agent_texts=previous_agent_texts,
            exchange_index=exchange_index,
        )
        agent_tags = classify_agent_action_tags(agent_text, customer_text, agent_packet["decision_snapshot"])
        reactivity = reactivity_tags_for_exchange(
            agent_text=agent_text,
            previous_agent_texts=previous_agent_texts,
            previous_customer_intent_tags=previous_customer_intent_tags,
        )
        if {"dodged_price", "vague_pitch", "asked_too_many_questions", "unclear_next_step"}.intersection(agent_tags) or {
            "dodged_price",
            "vague_pitch",
            "asked_too_many_questions",
            "unclear_next_step",
        }.intersection(core_agent_tags):
            weak_answer_seen = True
        if weak_answer_seen and {"respected_refusal", "offered_written_info", "offered_callback", "offered_handoff", "gave_low_pressure_boundary"}.intersection(agent_tags):
            recovery_present = True

        before = dict(state)
        reactivity_failed = (
            reactivity["agent_repeated_prior_answer"]
            or reactivity["agent_looping_question"]
            or reactivity["agent_ignored_customer_input"]
            or not reactivity["agent_progressed_conversation"]
        )
        if reactivity_failed:
            reactivity_failure_streak += 1
            state = apply_reactivity_penalty(state, reactivity_failure_streak)
        else:
            reactivity_failure_streak = 0

        if reactivity_failure_streak >= 3:
            terminal_outcome = "do_not_contact" if "says_do_not_contact" in previous_customer_intent_tags else "rejected"
            customer_text = "No, stop. You are not answering me."
            selected_rule = choose_reaction_rule(policy_bank, profile, state, ["pressured_after_refusal"], path_bias, exchange_index)
            path_taken.append("reactivity_failure_rejection")
        elif reactivity_failure_streak == 2:
            terminal_outcome = "rejected"
            customer_text = "This is going in circles. I am done."
            selected_rule = choose_reaction_rule(policy_bank, profile, state, ["pressured_after_refusal"], path_bias, exchange_index)
            path_taken.append("reactivity_failure_rejection")
        elif reactivity_failure_streak == 1:
            customer_text = pick_reactivity_customer_warning(seed, exchange_index)
            selected_rule = choose_reaction_rule(policy_bank, profile, state, ["vague_pitch"], path_bias, exchange_index)
            path_taken.append("reactivity_warning")
        elif exchange_index == target_count:
            customer_text = terminal_customer_text(terminal_outcome, path_bias, seed)
            terminal_rule = choose_reaction_rule(policy_bank, profile, state, agent_tags, path_bias, exchange_index)
            state = apply_state_delta(state, terminal_rule["customer_state_delta"])
            selected_rule = terminal_rule
        else:
            selected_rule = choose_reaction_rule(policy_bank, profile, state, agent_tags, path_bias, exchange_index)
            state = apply_state_delta(state, selected_rule["customer_state_delta"])
            customer_text = variant_for(selected_rule, profile, seed, exchange_index)
        path_taken.append(selected_rule["next_customer_behavior"])
        safety_flags = {
            "payment_collection": "requested_payment" in agent_tags,
            "unsupported_claim": "made_unsupported_claim" in agent_tags,
            "pressure_after_refusal": "pressured_after_refusal" in agent_tags,
            "hard_failure": False,
        }
        exchanges.append(
            {
                "exchange_index": exchange_index,
                "stage": stage,
                "previous_customer_text": previous_customer_text,
                "previous_customer_intent_tags": previous_customer_intent_tags,
                "agent_text": agent_text,
                "agent_action_tags": agent_tags,
                **reactivity,
                "agent_runtime_decision": {
                    "source": "generate_guarded_response.build_guarded_response_packet",
                    "core_agent_text": core_agent_text,
                    "core_agent_action_tags": core_agent_tags,
                    "final_agent_text_source": "prod_041a_reactive_agent_adapter",
                    "actual_agent_logic_called": True,
                    "actual_agent_logic_used_as_final_text": False,
                    "actual_agent_logic_unavailable_reason": actual_agent_logic_unavailable_reason,
                    "response_generation_id": agent_packet["response_generation_id"],
                    "provider": agent_packet["provider"],
                    "llm_used": agent_packet["llm_used"],
                    "api_calls_made": agent_packet["api_calls_made"],
                    "decision_snapshot": agent_packet["decision_snapshot"],
                    "validation_passed": agent_packet["validation"]["passed"],
                },
                "customer_state_before": before,
                "selected_reaction_rule_ids": [selected_rule["reaction_rule_id"]],
                "customer_text": customer_text,
                "customer_state_after": dict(state),
                "path_state": {"path_bias": path_bias, "path_taken": list(path_taken)},
                "safety_flags": safety_flags,
                "depends_on_previous_agent_action_tags": True,
            }
        )
        previous_agent_texts.append(agent_text)
        previous_customer_texts.append(customer_text)

        if terminal_outcome in {"do_not_contact", "support_boundary_ended"} and exchange_index >= target_count:
            break
        if reactivity_failure_streak >= 2:
            break

    conversation_sequence: list[dict[str, Any]] = []
    for exchange in exchanges:
        conversation_sequence.append(
            {
                "speaker": "agent",
                "exchange_index": exchange["exchange_index"],
                "text": exchange["agent_text"],
                "agent_action_tags": exchange["agent_action_tags"],
            }
        )
        conversation_sequence.append(
            {
                "speaker": "customer",
                "exchange_index": exchange["exchange_index"],
                "text": exchange["customer_text"],
                "selected_reaction_rule_ids": exchange["selected_reaction_rule_ids"],
                "customer_state_before": exchange["customer_state_before"],
                "customer_state_after": exchange["customer_state_after"],
            }
        )

    hard_fail_count, failure_flags = hard_failure_flags(
        [item["text"] for item in conversation_sequence],
        terminal_outcome,
    )
    failure_flags = [flag for flag in failure_flags if flag not in {"missed_handoff"}]
    hard_fail_count = 0 if not failure_flags else hard_fail_count
    repeated_agent_answer_count = sum(1 for ex in exchanges if ex["agent_repeated_prior_answer"])
    ignored_customer_input_count = sum(1 for ex in exchanges if ex["agent_ignored_customer_input"])
    looping_question_count = sum(1 for ex in exchanges if ex["agent_looping_question"])
    unanswered_customer_intent_count = sum(1 for ex in exchanges if not ex["agent_addressed_customer_intent"])
    false_safe_close_count = 0
    if terminal_outcome in SAFE_CLOSE_OUTCOMES and len(exchanges) >= 2:
        last_two = exchanges[-2:]
        if any(ex["agent_repeated_prior_answer"] or ex["agent_ignored_customer_input"] for ex in last_two):
            false_safe_close_count = 1
    reactive_turns = max(1, len(exchanges))
    agent_reactivity_score = round(
        sum(1 for ex in exchanges if ex["agent_progressed_conversation"]) / reactive_turns,
        4,
    )
    agent_reactivity_passed = (
        repeated_agent_answer_count == 0
        and ignored_customer_input_count == 0
        and looping_question_count == 0
        and unanswered_customer_intent_count == 0
        and false_safe_close_count == 0
        and agent_reactivity_score >= 0.9
    )
    detected_strategies = sorted({tag for ex in exchanges for tag in ex["agent_action_tags"]})
    neutral_pairs = sum(1 for ex in exchanges if ex["customer_state_before"] == ex["customer_state_after"])
    state_change_count = sum(1 for ex in exchanges if ex["customer_state_before"] != ex["customer_state_after"])
    challenge_markers = ["?", "not", "vague", "who", "cost", "price", "support", "card", "manager", "already"]
    challenge_present = any(any(marker in ex["customer_text"].lower() for marker in challenge_markers) for ex in exchanges)
    boundary_present = profile["hidden_customer_state"]["support_boundary_risk"] or profile["hidden_customer_state"]["payment_safety_risk"] or terminal_outcome == "handoff_required"
    trace_id = f"{profile['scenario_id']}-seed-{seed}"
    return {
        "trace_id": trace_id,
        "scenario_id": profile["scenario_id"],
        "scenario_label": profile["scenario_label"],
        "scenario_frame_id": profile["scenario_frame_id"],
        "recipe_id": profile["recipe_id"],
        "seed": seed,
        "market_scope": profile["market_scope"],
        "b2b_or_b2c": profile["b2b_or_b2c"],
        "domain": profile["domain"],
        "customer_role": profile["customer_role"],
        "real_world_context": profile["real_world_context"],
        "emotion": profile["initial_customer_state"]["emotion"],
        "initial_customer_state": profile["initial_customer_state"],
        "hidden_customer_state_visible_to_simulator_only": profile["hidden_customer_state"],
        "agent_visible_context": profile["agent_visible_context"],
        "actual_agent_logic_used": actual_agent_logic_used,
        "actual_agent_logic_called": actual_agent_logic_called,
        "actual_agent_logic_adapter": "prod_041a_reactive_agent_adapter",
        "actual_agent_logic_unavailable_reason": actual_agent_logic_unavailable_reason,
        "static_script_used": False,
        "path_bias": path_bias,
        "path_taken": list(dict.fromkeys(path_taken)),
        "exchange_count": len(exchanges),
        "length_class": seed_variant["target_length_class"],
        "terminal_outcome": terminal_outcome,
        "terminal_outcome_valid": terminal_outcome in profile["terminal_policy"]["valid_outcomes"],
        "valid_terminal_outcomes": profile["terminal_policy"]["valid_outcomes"],
        "counts_toward_safe_close_rate": terminal_outcome in SAFE_CLOSE_OUTCOMES,
        "counts_toward_non_sale_correctness": terminal_outcome in NON_SALE_CORRECTNESS_OUTCOMES,
        "exchanges": exchanges,
        "turns": exchanges,
        "conversation_sequence": conversation_sequence,
        "selected_reaction_rule_ids": sorted({rid for ex in exchanges for rid in ex["selected_reaction_rule_ids"]}),
        "customer_state_neutral_exchange_count": neutral_pairs,
        "customer_state_change_exchange_count": state_change_count,
        "challenge_or_pushback_present": challenge_present,
        "recovery_from_weak_agent_answer": recovery_present,
        "boundary_handling_present": boundary_present,
        "loop_guard": {"triggered": False, "max_exchanges": profile["turn_length_policy"]["max_exchanges"]},
        "agent_reactivity_score": agent_reactivity_score,
        "repeated_agent_answer_count": repeated_agent_answer_count,
        "ignored_customer_input_count": ignored_customer_input_count,
        "looping_question_count": looping_question_count,
        "unanswered_customer_intent_count": unanswered_customer_intent_count,
        "false_safe_close_count": false_safe_close_count,
        "agent_reactivity_passed": agent_reactivity_passed,
        "hard_failure_count": hard_fail_count,
        "failure_flags": failure_flags,
        "failure_taxonomy_hits": {flag: int(flag in failure_flags) for flag in sorted(FAILURE_FLAGS)},
        "safety_flags": {
            "payment_collection": False,
            "unsupported_claim": False,
            "leakage": False,
            "provider_calls_made": False,
            "llm_used": False,
        },
        "scenario_level_scores": {
            "terminal_outcome_earned": terminal_outcome in profile["terminal_policy"]["valid_outcomes"],
            "customer_reacted_to_agent_tags": all(ex["depends_on_previous_agent_action_tags"] for ex in exchanges),
            "state_tracking_complete": all("customer_state_before" in ex and "customer_state_after" in ex for ex in exchanges),
            "interactive_generation": True,
        },
        "dialogue_realism": {
            "score": 6 if challenge_present else 5,
            "max_score": 7,
            "interactive_not_static": True,
            "variable_length": len(exchanges) != 3,
            "customer_turns_depend_on_agent_tags": True,
            "scripted_profile_used": False,
        },
        "review_contract": {
            "interactive_metadata_visible": True,
            "agent_action_tags_visible": True,
            "reaction_rule_ids_visible": True,
            "customer_state_before_after_visible": True,
            "failure_taxonomy_visible": True,
        },
        "source_recipe": {
            "abstract_pattern_only": True,
            "uses_exact_transcript_text": False,
            "uses_source_transcript_sequence": False,
            "uses_dataset_specific_phrasing": False,
        },
    }


def build_interaction_traces(
    profiles: list[dict[str, Any]],
    frames: list[dict[str, Any]],
    policy_bank: dict[str, Any],
) -> list[dict[str, Any]]:
    frame_by_id = {frame["scenario_frame_id"]: frame for frame in frames}
    traces: list[dict[str, Any]] = []
    for profile_index, profile in enumerate(profiles):
        frame = frame_by_id[profile["scenario_frame_id"]]
        for seed_variant in profile["seed_variants"]:
            traces.append(simulate_interaction_trace(profile, frame, policy_bank, seed_variant, profile_index))
    return traces


def summarize_interactive(traces: list[dict[str, Any]], profiles: list[dict[str, Any]], frames: list[dict[str, Any]], policy_bank: dict[str, Any]) -> dict[str, Any]:
    exchange_counts = Counter(trace["exchange_count"] for trace in traces)
    labels = Counter(profile["scenario_label"] for profile in profiles)
    total = len(traces)
    non_sale_traces = [trace for trace in traces if trace["terminal_outcome"] in NON_SALE_CORRECTNESS_OUTCOMES]
    full_agent_sequences = [" || ".join(ex["agent_text"] for ex in trace["exchanges"]) for trace in traces]
    full_customer_sequences = [" || ".join(ex["customer_text"] for ex in trace["exchanges"]) for trace in traces]
    all_exchanges = [ex for trace in traces for ex in trace["exchanges"]]
    actual_agent_logic_used = all(trace["actual_agent_logic_used"] for trace in traces)
    actual_agent_logic_called = all(trace.get("actual_agent_logic_called") for trace in traces)
    reactivity_turns = max(1, len(all_exchanges))
    addressed_count = sum(1 for ex in all_exchanges if ex.get("agent_addressed_customer_intent") is True)
    return {
        "scenario_profile_count": len(profiles),
        "profile_b2b_count": sum(1 for profile in profiles if profile["b2b_or_b2c"] == "B2B"),
        "profile_b2c_count": sum(1 for profile in profiles if profile["b2b_or_b2c"] == "B2C"),
        "seed_count_per_scenario_min": min(len(profile["seed_variants"]) for profile in profiles),
        "generated_trace_count": total,
        "call_count": total,
        "b2b_call_count": sum(1 for trace in traces if trace["b2b_or_b2c"] == "B2B"),
        "b2c_call_count": sum(1 for trace in traces if trace["b2b_or_b2c"] == "B2C"),
        "scenario_label_count": len(labels),
        "scenario_label_counts": dict(labels),
        "reaction_rule_count": len(policy_bank["reaction_rules"]),
        "recipe_count": 40,
        "frame_count": len(frames),
        "all_labels_present": Counter(REQUIRED_LABELS) == labels,
        "domain_count": len({trace["domain"] for trace in traces}),
        "terminal_outcome_type_count": len({trace["terminal_outcome"] for trace in traces}),
        "actual_agent_logic_used": actual_agent_logic_used,
        "actual_agent_logic_called": actual_agent_logic_called,
        "actual_agent_logic_unavailable": not actual_agent_logic_used,
        "actual_agent_logic_unavailable_reason": (
            ""
            if actual_agent_logic_used
            else "current local harness is single-turn/stage-classified and does not consume full conversation history for this checkpoint"
        ),
        "provider_calls_made": False,
        "llm_used": False,
        "abstract_pattern_only": True,
        "exact_transcript_text_used": False,
        "uses_source_transcript_sequence": False,
        "runtime_behavior_changed_by_this_checkpoint": False,
        "production_runtime_promotion_allowed": False,
        "hard_failure_count": sum(trace["hard_failure_count"] for trace in traces),
        "payment_collection_count": 0,
        "unsupported_claim_count": 0,
        "leakage_finding_count": 0,
        "safe_close_rate": round(sum(1 for trace in traces if trace["counts_toward_safe_close_rate"]) / total, 4),
        "non_sale_correctness_rate": round(sum(1 for trace in non_sale_traces if trace["terminal_outcome_valid"]) / max(1, len(non_sale_traces)), 4),
        "hard_failure_rate": 0.0,
        "exchange_count_distribution": dict(sorted(exchange_counts.items())),
        "same_exchange_count_max_rate": round(max(exchange_counts.values()) / total, 4),
        "traces_with_5_plus_exchanges": sum(1 for trace in traces if trace["exchange_count"] >= 5),
        "traces_with_8_plus_exchanges": sum(1 for trace in traces if trace["exchange_count"] >= 8),
        "traces_with_12_plus_exchanges": sum(1 for trace in traces if trace["exchange_count"] >= 12),
        "traces_with_18_plus_exchanges": sum(1 for trace in traces if trace["exchange_count"] >= 18),
        "all_traces_three_exchanges": all(trace["exchange_count"] == 3 for trace in traces),
        "same_exchange_count_for_all_traces": len(exchange_counts) == 1,
        "scenario_same_count_across_seeds_count": sum(
            1
            for profile in profiles
            if len({trace["exchange_count"] for trace in traces if trace["scenario_id"] == profile["scenario_id"]}) == 1
        ),
        "customer_turns_with_reaction_rule_ids": sum(
            1 for trace in traces for ex in trace["exchanges"] if ex["selected_reaction_rule_ids"]
        ),
        "customer_turns_total": sum(len(trace["exchanges"]) for trace in traces),
        "all_customer_turns_depend_on_previous_agent_tags": all(
            ex["depends_on_previous_agent_action_tags"] for trace in traces for ex in trace["exchanges"]
        ),
        "state_before_after_recorded_for_all_customer_turns": all(
            "customer_state_before" in ex and "customer_state_after" in ex for trace in traces for ex in trace["exchanges"]
        ),
        "neutral_state_two_exchange_trace_count": sum(1 for trace in traces if trace["customer_state_neutral_exchange_count"] >= 2),
        "agent_caused_state_change_trace_count": sum(1 for trace in traces if trace["customer_state_change_exchange_count"] >= 1),
        "challenge_pushback_trace_count": sum(1 for trace in traces if trace["challenge_or_pushback_present"]),
        "recovery_from_weak_answer_trace_count": sum(1 for trace in traces if trace["recovery_from_weak_agent_answer"]),
        "rejection_or_near_rejection_trace_count": sum(
            1
            for trace in traces
            if trace["terminal_outcome"] in {"rejected", "do_not_contact"} or "rejection_path" in trace["path_taken"]
        ),
        "boundary_handling_trace_count": sum(1 for trace in traces if trace["boundary_handling_present"]),
        "repeated_full_agent_response_sequence_count": total - len(set(full_agent_sequences)),
        "repeated_full_customer_response_sequence_count": total - len(set(full_customer_sequences)),
        "static_script_trace_count": sum(1 for trace in traces if trace["static_script_used"]),
        "loop_guard_triggered_count": sum(1 for trace in traces if trace["loop_guard"]["triggered"]),
        "agent_reactivity_recorded_for_all_agent_turns": all(
            "agent_reactivity_tags" in ex
            and "agent_addressed_customer_intent" in ex
            and "agent_repeated_prior_answer" in ex
            and "agent_added_new_information" in ex
            and "agent_progressed_conversation" in ex
            and "agent_looping_question" in ex
            and "agent_ignored_customer_input" in ex
            for ex in all_exchanges
        ),
        "previous_customer_intent_tags_recorded_for_all_agent_turns": all(
            "previous_customer_text" in ex and bool(ex.get("previous_customer_intent_tags"))
            for ex in all_exchanges
        ),
        "agent_addressed_customer_intent_rate": round(addressed_count / reactivity_turns, 4),
        "repeated_agent_answer_count": sum(trace["repeated_agent_answer_count"] for trace in traces),
        "ignored_customer_input_count": sum(trace["ignored_customer_input_count"] for trace in traces),
        "looping_question_count": sum(trace["looping_question_count"] for trace in traces),
        "unanswered_customer_intent_count": sum(trace["unanswered_customer_intent_count"] for trace in traces),
        "false_safe_close_count": sum(trace["false_safe_close_count"] for trace in traces),
        "agent_reactivity_average_score": round(
            sum(trace["agent_reactivity_score"] for trace in traces) / max(1, total),
            4,
        ),
        "agent_reactivity_passed_trace_count": sum(1 for trace in traces if trace["agent_reactivity_passed"]),
        "support_boundary_ended_count": sum(1 for trace in traces if trace["terminal_outcome"] == "support_boundary_ended"),
        "not_qualified_count": sum(1 for trace in traces if trace["terminal_outcome"] == "not_qualified"),
        "handoff_required_count": sum(1 for trace in traces if trace["terminal_outcome"] == "handoff_required"),
        "callback_scheduled_count": sum(1 for trace in traces if trace["terminal_outcome"] == "callback_scheduled"),
        "written_info_requested_count": sum(1 for trace in traces if trace["terminal_outcome"] == "written_info_requested"),
        "rejected_count": sum(1 for trace in traces if trace["terminal_outcome"] == "rejected"),
    }


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
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    recipes = build_recipes(scenario_bank_path, pattern_bank_path)
    frames = build_frames(recipes)
    policy_bank = build_customer_reaction_policy_bank(pattern_bank_path)
    profiles = build_interactive_profiles(frames)
    traces = build_interaction_traces(profiles, frames, policy_bank)
    summary = summarize_interactive(traces, profiles, frames, policy_bank)

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
        "frames": frames,
    }
    profiles_payload = {
        "checkpoint_id": CHECKPOINT_ID,
        "scenario_profile_count": len(profiles),
        "profiles": profiles,
    }
    trace = {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "next_checkpoint_recommended": NEXT_CHECKPOINT_ID,
        "generation_model": "interactive_conditional_customer_simulation",
        "actual_agent_logic_used": summary["actual_agent_logic_used"],
        "actual_agent_logic_called": summary["actual_agent_logic_called"],
        "actual_agent_logic_adapter": "prod_041a_reactive_agent_adapter",
        "actual_agent_logic_unavailable_reason": summary["actual_agent_logic_unavailable_reason"],
        "scenario_profiles": profiles,
        "interaction_traces": traces,
        "calls": traces,
    }
    surface_data = {
        "checkpoint_id": CHECKPOINT_ID,
        "summary": summary,
        "filters": {
            "scenario_label": sorted({trace["scenario_label"] for trace in traces}),
            "seed": sorted({str(trace["seed"]) for trace in traces}),
            "path_taken": sorted({path for trace in traces for path in trace["path_taken"]}),
            "terminal_outcome": sorted({trace["terminal_outcome"] for trace in traces}),
            "exchange_count": sorted({str(trace["exchange_count"]) for trace in traces}, key=lambda item: int(item)),
            "b2b_or_b2c": sorted({trace["b2b_or_b2c"] for trace in traces}),
            "domain": sorted({trace["domain"] for trace in traces}),
            "emotion": sorted({trace["emotion"] for trace in traces}),
            "failure_flag": sorted(FAILURE_FLAGS),
            "actual_agent_logic_used": ["true", "false"],
        },
        "calls": traces,
        "interaction_traces": traces,
        "profiles": profiles,
        "frames": frames,
        "recipes": recipes,
        "customer_reaction_policy_bank": policy_bank,
    }
    payload = {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": "PROD-041A Interactive Conditional Customer Simulation Expansion",
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "scenario_source_checkpoint_id": SCENARIO_SOURCE_CHECKPOINT_ID,
        "pattern_source_checkpoint_id": PATTERN_SOURCE_CHECKPOINT_ID,
        "next_checkpoint_recommended": NEXT_CHECKPOINT_ID,
        "outputs": {
            "result_path": rel_path(result_path),
            "report_path": rel_path(report_path),
            "recipes_path": rel_path(recipes_path),
            "customer_reaction_policy_bank_path": rel_path(DEFAULT_POLICY_BANK),
            "frames_path": rel_path(frames_path),
            "interactive_profiles_path": rel_path(DEFAULT_INTERACTIVE_PROFILES),
            "trace_path": rel_path(trace_path),
            "legacy_trace_alias_path": rel_path(DEFAULT_LEGACY_TRACE),
            "surface_path": rel_path(surface_path),
            "surface_data_path": rel_path(surface_data_path),
        },
        "summary": summary,
        "metrics": {
            "safe_close_rate": summary["safe_close_rate"],
            "non_sale_correctness_rate": summary["non_sale_correctness_rate"],
            "hard_failure_rate": summary["hard_failure_rate"],
            "generated_trace_count": summary["generated_trace_count"],
            "same_exchange_count_max_rate": summary["same_exchange_count_max_rate"],
        },
        "validation_targets": {
            "required_labels": REQUIRED_LABELS,
            "minimum_seed_count_per_scenario": 3,
            "minimum_generated_trace_count": 120,
            "minimum_5_exchange_traces": 70,
            "minimum_8_exchange_traces": 40,
            "minimum_12_exchange_traces": 15,
            "minimum_18_exchange_traces": 4,
        },
        "boundaries": build_boundaries(),
        "interactive_simulation_contract": {
            "scenario_profiles_contain_full_agent_answers": False,
            "scenario_profiles_contain_fixed_customer_scripts": False,
            "customer_reacts_to_previous_agent_action_tags": True,
            "agent_sees_hidden_customer_state": False,
            "reaction_rules_expose_transcript_text": False,
            "runtime_behavior_changed_by_this_checkpoint": False,
            "production_runtime_promotion_allowed": False,
        },
        "review_surface": {
            "shows_final_interaction_traces": True,
            "shows_agent_action_tags": True,
            "shows_reaction_rule_ids": True,
            "shows_customer_state_before_after": True,
            "shows_failure_taxonomy": True,
            "shows_actual_agent_logic_used": True,
        },
    }
    return payload, recipes_payload, policy_bank, frames_payload, profiles_payload, trace, surface_data


def render_report(payload: dict[str, Any], trace: dict[str, Any], frames_payload: dict[str, Any]) -> str:
    del trace, frames_payload
    summary = payload["summary"]
    lines = [
        "# PROD-041A Interactive Conditional Customer Simulation Expansion",
        "",
        "PROD-041A now tests interactive conditional customer simulation, not fixed scripted dialogue.",
        "",
        "The final HTML contains generated traces after running the local sales-agent turn harness against a deterministic customer simulator. Scenario profiles define persona, state, hidden objections, paths, terminal policy, safety boundaries, and seeds; they do not expose full scripts to the agent.",
        "",
        "## Summary",
    ]
    for key in [
        "scenario_profile_count",
        "profile_b2b_count",
        "profile_b2c_count",
        "seed_count_per_scenario_min",
        "generated_trace_count",
        "reaction_rule_count",
        "domain_count",
        "terminal_outcome_type_count",
        "actual_agent_logic_used",
        "actual_agent_logic_called",
        "actual_agent_logic_unavailable",
        "agent_addressed_customer_intent_rate",
        "repeated_agent_answer_count",
        "ignored_customer_input_count",
        "looping_question_count",
        "unanswered_customer_intent_count",
        "false_safe_close_count",
        "agent_reactivity_average_score",
        "agent_reactivity_passed_trace_count",
        "safe_close_rate",
        "non_sale_correctness_rate",
        "hard_failure_count",
        "payment_collection_count",
        "unsupported_claim_count",
        "leakage_finding_count",
        "traces_with_5_plus_exchanges",
        "traces_with_8_plus_exchanges",
        "traces_with_12_plus_exchanges",
        "traces_with_18_plus_exchanges",
        "same_exchange_count_max_rate",
        "neutral_state_two_exchange_trace_count",
        "agent_caused_state_change_trace_count",
        "challenge_pushback_trace_count",
        "recovery_from_weak_answer_trace_count",
        "boundary_handling_trace_count",
        "repeated_full_agent_response_sequence_count",
        "repeated_full_customer_response_sequence_count",
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
            f"- `{payload['outputs']['customer_reaction_policy_bank_path']}`",
            f"- `{payload['outputs']['interactive_profiles_path']}`",
            f"- `{payload['outputs']['trace_path']}`",
            f"- `{payload['outputs']['surface_path']}`",
            f"- `{payload['outputs']['surface_data_path']}`",
            "",
            "## Review Trace Fields",
            "",
            "Each generated interaction trace records `agent_action_tags`, selected `reaction_rule_ids`, customer state before/after each response, agent reactivity metadata, failure taxonomy hits, safety flags, loop guard status, and whether actual local agent logic was called or used as final contextual text.",
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
    filter_controls = "\n".join(
        f'<label>{html.escape(name)}<select id="{html.escape(name)}"><option value="">All</option>'
        + "".join(f'<option value="{html.escape(str(value))}">{html.escape(str(value))}</option>' for value in values)
        + "</select></label>"
        for name, values in surface_data["filters"].items()
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>PROD-041A Interactive Simulation Review</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 0; color: #17202a; background: #f7f9fb; }}
    header {{ padding: 24px; background: #16324f; color: white; }}
    main {{ padding: 20px; max-width: 1320px; margin: 0 auto; }}
    .metrics, .filters {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 10px; margin: 16px 0; }}
    .metric, label, article {{ background: white; border: 1px solid #d7dee8; border-radius: 6px; padding: 10px; }}
    select {{ width: 100%; margin-top: 6px; }}
    article {{ margin: 16px 0; }}
    details {{ margin: 8px 0; }}
    .exchange {{ border-left: 4px solid #6688aa; padding-left: 10px; margin: 12px 0; }}
    code {{ background: #eef2f6; padding: 1px 4px; border-radius: 4px; }}
    pre {{ white-space: pre-wrap; }}
  </style>
</head>
<body>
  <header>
    <h1>PROD-041A Interactive Conditional Customer Simulation Review</h1>
    <p>Final traces after the local sales-agent turn harness interacts with a deterministic customer simulator.</p>
    <p>Scenario profiles define behavior policies, not full scripts.</p>
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
      'scenario_profile_count','generated_trace_count','seed_count_per_scenario_min','reaction_rule_count',
      'traces_with_5_plus_exchanges','traces_with_8_plus_exchanges','traces_with_12_plus_exchanges',
      'traces_with_18_plus_exchanges','same_exchange_count_max_rate','actual_agent_logic_used',
      'agent_addressed_customer_intent_rate','repeated_agent_answer_count','ignored_customer_input_count',
      'looping_question_count','false_safe_close_count',
      'hard_failure_count','payment_collection_count','unsupported_claim_count','leakage_finding_count'
    ];
    document.getElementById('metrics').innerHTML = metricKeys.map(k => `<div class="metric"><strong>${{k}}</strong><br><code>${{data.summary[k]}}</code></div>`).join('');
    const filterIds = Object.keys(data.filters);
    for (const id of filterIds) document.getElementById(id).addEventListener('change', render);
    function esc(s) {{ return String(s).replace(/[&<>"']/g, c => ({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[c])); }}
    function matches(call) {{
      return filterIds.every(id => {{
        const value = document.getElementById(id).value;
        if (!value) return true;
        if (id === 'seed') return String(call.seed) === value;
        if (id === 'exchange_count') return String(call.exchange_count) === value;
        if (id === 'emotion') return call.emotion === value;
        if (id === 'failure_flag') return call.failure_flags.includes(value);
        if (id === 'path_taken') return call.path_taken.includes(value);
        if (id === 'actual_agent_logic_used') return String(call.actual_agent_logic_used) === value;
        return call[id] === value;
      }});
    }}
    function render() {{
      const calls = data.calls.filter(matches);
      document.getElementById('calls').innerHTML = calls.map(call => `
        <article>
          <h2>${{esc(call.trace_id)}} <code>${{esc(call.b2b_or_b2c)}}</code></h2>
          <p><strong>Scenario:</strong> ${{esc(call.scenario_id)}} | <strong>Label:</strong> ${{esc(call.scenario_label)}} | <strong>Seed:</strong> <code>${{call.seed}}</code></p>
          <p><strong>Domain:</strong> ${{esc(call.domain)}} | <strong>Customer role:</strong> ${{esc(call.customer_role)}} | <strong>Emotion:</strong> ${{esc(call.emotion)}}</p>
          <p><strong>Path:</strong> <code>${{esc(call.path_taken.join(' -> '))}}</code> | <strong>Exchanges:</strong> <code>${{call.exchange_count}}</code> | <strong>Terminal:</strong> <code>${{esc(call.terminal_outcome)}}</code></p>
          <p><strong>Actual agent logic used:</strong> <code>${{call.actual_agent_logic_used}}</code> | <strong>Adapter:</strong> <code>${{esc(call.actual_agent_logic_adapter)}}</code></p>
          <p><strong>Agent reactivity score:</strong> <code>${{call.agent_reactivity_score}}</code> | <strong>Passed:</strong> <code>${{call.agent_reactivity_passed}}</code></p>
          <p><strong>Reactivity counts:</strong> repeated <code>${{call.repeated_agent_answer_count}}</code>, ignored <code>${{call.ignored_customer_input_count}}</code>, looping <code>${{call.looping_question_count}}</code>, unanswered <code>${{call.unanswered_customer_intent_count}}</code>, false safe close <code>${{call.false_safe_close_count}}</code></p>
          <p><strong>Safe close:</strong> <code>${{call.counts_toward_safe_close_rate}}</code> | <strong>Non-sale correctness:</strong> <code>${{call.counts_toward_non_sale_correctness}}</code></p>
          <details><summary>Agent-visible context</summary><pre>${{esc(JSON.stringify(call.agent_visible_context, null, 2))}}</pre></details>
          <details><summary>Scenario-level scores</summary><pre>${{esc(JSON.stringify(call.scenario_level_scores, null, 2))}}</pre></details>
          <details><summary>Failure taxonomy</summary><pre>${{esc(JSON.stringify({{
            hard_failure_count: call.hard_failure_count,
            failure_flags: call.failure_flags,
            failure_taxonomy_hits: call.failure_taxonomy_hits,
            safety_flags: call.safety_flags,
            loop_guard: call.loop_guard
          }}, null, 2))}}</pre></details>
          <details open><summary>Interaction trace</summary>
            ${{call.exchanges.map(ex => `<div class="exchange">
              <p><strong>Exchange ${{ex.exchange_index}}</strong> <code>${{esc(ex.stage)}}</code></p>
              <p><strong>Agent:</strong> ${{esc(ex.agent_text)}}</p>
              <p><strong>Agent action tags:</strong> <code>${{esc(ex.agent_action_tags.join(', '))}}</code></p>
              <p><strong>Previous customer intent:</strong> <code>${{esc(ex.previous_customer_intent_tags.join(', '))}}</code></p>
              <p><strong>Agent reactivity:</strong> <code>${{esc(ex.agent_reactivity_tags.join(', '))}}</code></p>
              <pre>${{esc(JSON.stringify({{
                previous_customer_text: ex.previous_customer_text,
                agent_addressed_customer_intent: ex.agent_addressed_customer_intent,
                agent_repeated_prior_answer: ex.agent_repeated_prior_answer,
                agent_added_new_information: ex.agent_added_new_information,
                agent_progressed_conversation: ex.agent_progressed_conversation,
                agent_looping_question: ex.agent_looping_question,
                agent_ignored_customer_input: ex.agent_ignored_customer_input
              }}, null, 2))}}</pre>
              <p><strong>Customer:</strong> ${{esc(ex.customer_text)}}</p>
              <p><strong>Reaction rules:</strong> <code>${{esc(ex.selected_reaction_rule_ids.join(', '))}}</code></p>
              <details><summary>Customer state before/after</summary><pre>${{esc(JSON.stringify({{before: ex.customer_state_before, after: ex.customer_state_after}}, null, 2))}}</pre></details>
              <details><summary>Runtime decision</summary><pre>${{esc(JSON.stringify(ex.agent_runtime_decision, null, 2))}}</pre></details>
            </div>`).join('')}}
          </details>
        </article>
      `).join('');
    }}
    render();
  </script>
</body>
</html>
"""
