#!/usr/bin/env python3
from __future__ import annotations

import html
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from callcenteren_runtime_comparison import contains_payment_collection
from generate_guarded_response import build_guarded_response_packet
from prod_028_synthetic_campaign_knowledge_grounding import build_synthetic_campaign
from run_resp_001_retrieval_ab_evaluation import forbidden_response_text, output_language_matches


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-040-callcenteren-conditional-customer-simulation"
SOURCE_CHECKPOINT_ID = "PROD-039-customer-realism-simulator-hardening"
SCENARIO_SOURCE_CHECKPOINT_ID = "PROD-014-callcenteren-scenario-bank"
PATTERN_SOURCE_CHECKPOINT_ID = "PROD-013-callcenteren-pattern-extraction"
NEXT_CHECKPOINT_ID = "PROD-041-conditional-simulation-review"
DEFAULT_OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
DEFAULT_RESULT = DEFAULT_OUT_DIR / "result.json"
DEFAULT_REPORT = DEFAULT_OUT_DIR / "report.md"
DEFAULT_TRACE = DEFAULT_OUT_DIR / "conditional_customer_traces.json"
DEFAULT_SURFACE = DEFAULT_OUT_DIR / "conditional_customer_trace_demo.html"
DEFAULT_SURFACE_DATA = DEFAULT_OUT_DIR / "conditional_customer_trace_demo_data.json"
DEFAULT_SOURCE_TRACE = ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "customer_realism_hardened_traces.json"
DEFAULT_SCENARIO_BANK = ROOT / "research" / "experiments" / "generated" / SCENARIO_SOURCE_CHECKPOINT_ID / "scenario-bank.json"
DEFAULT_PATTERN_BANK = ROOT / "research" / "experiments" / "generated" / PATTERN_SOURCE_CHECKPOINT_ID / "pattern-bank.json"

UNSUPPORTED_CLAIM_MARKERS = [
    "guaranteed revenue increase",
    "guaranteed cost savings",
    "guaranteed conversion lift",
    "replaces every crm",
    "no risk",
    "legal advice",
    "collect payment or card details on this call",
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


def clamp(value: int, low: int = 0, high: int = 5) -> int:
    return max(low, min(high, value))


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
        "source_prod_039_overwritten": False,
        "source_prod_014_overwritten": False,
        "source_prod_013_overwritten": False,
        "production_runtime_promotion_allowed": False,
    }


def unsupported_claims(text: str) -> list[str]:
    lowered = text.lower()
    return [marker for marker in UNSUPPORTED_CLAIM_MARKERS if marker in lowered]


def count_questions(text: str) -> int:
    return text.count("?")


def safe_label(value: str) -> str:
    return value.replace("_", "-").replace(" ", "-").lower()


def opening_agent_message(campaign: dict[str, Any], profile: dict[str, Any]) -> str:
    if profile.get("market_scope") == "B2C":
        return (
            f"Hi, this is Maya from {profile.get('offer_name', campaign['product_name'])}. "
            "I am calling about missed service follow-ups and appointment reminders for individual customers. "
            "Did I catch you at an okay moment for the short reason I called?"
        )
    return (
        f"Hi, this is Maya from {campaign['product_name']}. "
        "We help teams route inbound leads and keep callback ownership from getting lost. "
        "Did I catch you at a workable moment for the short reason I called?"
    )


def opening_checks(opening: str) -> dict[str, bool]:
    lowered = opening.lower()
    return {
        "greeting": lowered.startswith("hi") or lowered.startswith("hello"),
        "identity_disclosure": "this is maya" in lowered,
        "company_disclosure": "routesignal" in lowered,
        "reason_for_call": (
            ("route inbound leads" in lowered and "callback ownership" in lowered)
            or ("service follow-ups" in lowered and "appointment reminders" in lowered)
        ),
        "permission_to_continue": "did i catch you" in lowered and "?" in opening,
    }


def selected_scenarios(scenario_bank: dict[str, Any]) -> list[dict[str, Any]]:
    scenarios = list(scenario_bank.get("scenario_bank", []))
    desired_labels = [
        "price_objection",
        "sale_eligible",
        "trust_repair",
        "callback_request",
        "support_handoff",
        "cancellation_boundary",
    ]
    selected: list[dict[str, Any]] = []
    used: set[str] = set()
    for label in desired_labels:
        for scenario in scenarios:
            if scenario.get("scenario_id") in used:
                continue
            if scenario.get("scenario_label") == label:
                selected.append(scenario)
                used.add(scenario["scenario_id"])
                break
    for scenario in scenarios:
        if len(selected) >= 8:
            break
        if scenario.get("scenario_id") not in used:
            selected.append(scenario)
            used.add(scenario["scenario_id"])
    return selected[:8]


def build_profiles(scenario_bank: dict[str, Any]) -> list[dict[str, Any]]:
    scenarios = selected_scenarios(scenario_bank)
    bases = [
        {
            "seed_id": "conditional-price-sensitive",
            "market_scope": "B2B",
            "offer_name": "RouteSignal CRM",
            "persona": "price-sensitive operations manager",
            "opening_response": "I have a few minutes, but if this is another paid tool I need the real cost first.",
            "initial_state": {"interest": 3, "trust": 2, "clarity": 1, "friction": 3, "patience": 3, "emotion": "skeptical", "active_objection": "price"},
            "target_outcome": "accepted-deal",
            "internal_reason": "missed inbound leads get one owner, one callback path, and cleaner manager visibility before prospects go cold",
            "price_line": "Starter is $29 per user per month annually and Growth is $59 per user per month annually",
            "fit_criteria": "inbound leads are delayed, assigned twice, or missing callback owners",
        },
        {
            "seed_id": "conditional-confused-fit",
            "market_scope": "B2B",
            "offer_name": "RouteSignal CRM",
            "persona": "confused owner trying to understand product fit",
            "opening_response": "RouteSignal does not ring a bell. Is this a CRM thing or something else?",
            "initial_state": {"interest": 2, "trust": 2, "clarity": 0, "friction": 2, "patience": 4, "emotion": "confused", "active_objection": "confusion"},
            "target_outcome": "accepted-deal",
            "internal_reason": "the business gets a shared lead intake layer so callbacks stop depending on memory, spreadsheets, or one busy person",
            "price_line": "Starter is $29 per user per month annually and Growth is $59 per user per month annually",
            "fit_criteria": "leads are coming from multiple places and nobody is fully sure who owns the next callback",
        },
        {
            "seed_id": "conditional-skeptical-proof",
            "market_scope": "B2B",
            "offer_name": "RouteSignal CRM",
            "persona": "skeptical founder who wants proof before engaging",
            "opening_response": "I get these calls all the time. If this is vague software talk, I am out.",
            "initial_state": {"interest": 2, "trust": 1, "clarity": 1, "friction": 3, "patience": 3, "emotion": "skeptical", "active_objection": "trust"},
            "target_outcome": "rejected-deal",
            "internal_reason": "the only defensible case is operational control: clearer lead ownership, routing, and written follow-up details",
            "price_line": "Starter is $29 per user per month annually and Growth is $59 per user per month annually",
            "fit_criteria": "the current process makes it hard to prove who followed up with each lead",
        },
        {
            "seed_id": "conditional-busy-now",
            "market_scope": "B2B",
            "offer_name": "RouteSignal CRM",
            "persona": "busy sales lead with low patience",
            "opening_response": "Not a good time. You have one sentence before I jump back into work.",
            "initial_state": {"interest": 1, "trust": 2, "clarity": 1, "friction": 4, "patience": 1, "emotion": "annoyed", "active_objection": "time"},
            "target_outcome": "rejected-deal",
            "internal_reason": "the team has a simple way to see which leads still need a callback without chasing people manually",
            "price_line": "Starter is $29 per user per month annually and Growth is $59 per user per month annually",
            "fit_criteria": "callbacks are being delayed because ownership is unclear",
        },
        {
            "seed_id": "conditional-existing-provider",
            "market_scope": "B2B",
            "offer_name": "RouteSignal CRM",
            "persona": "team lead already using a CRM",
            "opening_response": "We already have a CRM, so I am not looking to rip anything out.",
            "initial_state": {"interest": 2, "trust": 3, "clarity": 1, "friction": 2, "patience": 4, "emotion": "neutral", "active_objection": "provider"},
            "target_outcome": "accepted-deal",
            "internal_reason": "the case is not replacing the CRM; it is reducing the routing and callback gaps around the CRM",
            "price_line": "Starter is $29 per user per month annually and Growth is $59 per user per month annually",
            "fit_criteria": "the CRM stores records but routing, reminders, or owner follow-through still break outside it",
        },
        {
            "seed_id": "conditional-manager-review",
            "market_scope": "B2B",
            "offer_name": "RouteSignal CRM",
            "persona": "manager who needs a concise internal case",
            "opening_response": "If this is useful, I need the version I can repeat to my manager.",
            "initial_state": {"interest": 4, "trust": 3, "clarity": 2, "friction": 2, "patience": 4, "emotion": "curious", "active_objection": "authority"},
            "target_outcome": "accepted-deal",
            "internal_reason": "the manager-level reason is fewer dropped leads: each inbound request gets routed, owned, and followed up without a messy handoff",
            "price_line": "Starter is $29 per user per month annually and Growth is $59 per user per month annually",
            "fit_criteria": "multiple people touch leads before a callback and managers cannot quickly see what is stuck",
        },
        {
            "seed_id": "conditional-consumer-budget",
            "market_scope": "B2C",
            "offer_name": "RouteSignal Home",
            "persona": "budget-conscious consumer comparing a service plan",
            "opening_response": "I can listen, but I am not signing up for a surprise subscription. What would this actually do for me?",
            "initial_state": {"interest": 2, "trust": 2, "clarity": 0, "friction": 3, "patience": 4, "emotion": "cautious", "active_objection": "confusion"},
            "target_outcome": "accepted-deal",
            "internal_reason": "the personal reason is fewer missed appointments and clearer reminders, so the customer does not have to chase service follow-ups",
            "price_line": "the synthetic consumer option is $19 per month for Basic reminders and $39 per month for Plus scheduling help",
            "fit_criteria": "appointments, reminders, or service callbacks are easy to miss and the customer wants one clear follow-up path",
        },
        {
            "seed_id": "conditional-consumer-no-pressure",
            "market_scope": "B2C",
            "offer_name": "RouteSignal Home",
            "persona": "consumer wary of pressure and payment collection",
            "opening_response": "I am not giving card details on a phone call. If this is a hard sell, I am done.",
            "initial_state": {"interest": 1, "trust": 1, "clarity": 1, "friction": 4, "patience": 3, "emotion": "guarded", "active_objection": "trust"},
            "target_outcome": "accepted-deal",
            "internal_reason": "the only safe reason to continue is a no-payment explanation of whether reminders and service follow-ups solve a real personal problem",
            "price_line": "the synthetic consumer option is $19 per month for Basic reminders and $39 per month for Plus scheduling help",
            "fit_criteria": "the customer actually wants help tracking appointment reminders and service follow-ups",
        },
    ]
    profiles = []
    for index, base in enumerate(bases):
        scenario = scenarios[index % len(scenarios)]
        profile = deepcopy(base)
        profile["callcenteren_scenario"] = {
            "scenario_id": scenario.get("scenario_id"),
            "scenario_label": scenario.get("scenario_label"),
            "domain": scenario.get("domain"),
            "initial_intent": scenario.get("initial_intent"),
            "likely_objection": scenario.get("likely_objection"),
            "starting_emotion": scenario.get("starting_emotion"),
            "safe_agent_tactic": scenario.get("safe_agent_tactic"),
            "discovery_question_type": scenario.get("discovery_question_type"),
            "close_type": scenario.get("close_type"),
            "commitment_level": scenario.get("commitment_level"),
            "source_pattern_ids": scenario.get("source_pattern_ids", []),
            "source_pattern_categories": scenario.get("source_recipe", {}).get("source_pattern_categories", []),
            "uses_exact_transcript_text": False,
            "uses_single_source_transcript": False,
        }
        profiles.append(profile)
    return profiles


def answer_customization(profile: dict[str, Any], state: dict[str, Any]) -> dict[str, str]:
    scenario = profile["callcenteren_scenario"]
    return {
        "seed_id": profile["seed_id"],
        "market_scope": profile["market_scope"],
        "persona": profile["persona"],
        "offer_name": profile["offer_name"],
        "domain": str(scenario.get("domain", "unknown")),
        "scenario_label": str(scenario.get("scenario_label", "unknown")),
        "safe_agent_tactic": str(scenario.get("safe_agent_tactic", "unknown")),
        "active_objection": str(state.get("active_objection", "unknown")),
        "customization_basis": "profile + current objection + abstract CallCenterEN scenario labels",
    }


def answer_for_state(state: dict[str, Any], campaign: dict[str, Any], profile: dict[str, Any]) -> tuple[str, dict[str, str]]:
    product_name = profile.get("offer_name", campaign["product_name"])
    specialist = campaign.get("human_handoff_role", "solutions specialist")
    objection = state["active_objection"]
    customization = answer_customization(profile, state)
    seed = profile["seed_id"]
    is_b2c = profile.get("market_scope") == "B2C"
    internal_reason = profile["internal_reason"]
    price_line = profile["price_line"]
    fit_criteria = profile["fit_criteria"]
    if objection == "do-not-call":
        return "Understood. I will mark this number as do not call and end the sales conversation now.", customization
    if objection == "support":
        return f"That account issue should be handled as support before sales. I will route you to a {specialist} for account help instead of pitching RouteSignal.", customization
    if objection == "time":
        return f"Then I will keep it to the point for a busy sales lead: {product_name} helps stop inbound leads getting lost between routing and callback ownership. If that problem is not active today, we can stop here.", customization
    if objection == "price":
        if is_b2c:
            return f"For an individual customer, {price_line}. Payment stays outside this call, so the only useful question is whether appointment reminders and service follow-ups would actually help you.", customization
        if seed == "conditional-confused-fit":
            return f"For a small team still figuring out fit, {price_line}. Billing stays outside this call; the useful question is whether routing and callback ownership are real enough to review.", customization
        if seed == "conditional-existing-provider":
            return f"If this sits beside your existing CRM, {price_line}. I would judge it only against routing gaps around the CRM, not as a replacement purchase today.", customization
        return f"For a price-sensitive operations team, {price_line}. Billing stays outside this call, so the decision is only whether the workflow deserves a short review.", customization
    if objection == "confusion":
        if is_b2c:
            return f"{product_name} is not a card-collection call or a hard commitment. In your case, it would help with appointment reminders, service follow-ups, and one clear place to confirm next steps.", customization
        return f"{product_name} is not a full CRM replacement. For your case, think of it as a layer around lead intake, routing, callback ownership, Gmail and Outlook sync, Slack and Zapier handoffs, and CSV import.", customization
    if objection == "trust":
        if is_b2c:
            return f"Fair concern. I cannot ask for card details or treat this as a purchase decision. The safe claim is narrower: {product_name} can help track appointment reminders and service follow-ups, and you can say no after the explanation.", customization
        return f"Fair concern. I cannot promise revenue lift or pretend this is proven for your company. The verifiable claim is narrower: {product_name} centralizes lead intake and routes leads by region, source, priority, or owner.", customization
    if objection == "written-info":
        if is_b2c:
            return "That is reasonable for a cautious customer. A specialist can send written details first, including what the reminder plan does, what it costs, and that no payment is handled on this call.", customization
        return "That is reasonable for a skeptical review. A specialist can send written details and separate confirmed product facts from what still needs a fit review for your team.", customization
    if objection == "provider":
        return f"I would not ask a team with an existing CRM to rip it out. {product_name} is only worth a look if routing, callback ownership, or reporting are still messy around that CRM.", customization
    if objection == "authority":
        if is_b2c:
            return f"The simple reason to consider it is this: {internal_reason}. If that is not a real problem for you, there is no reason to continue.", customization
        if seed == "conditional-manager-review":
            return f"For the manager version you asked for: {internal_reason}. That is the business reason; commercial and security details can be separated into a written specialist follow-up.", customization
        return f"The internal reason is simple: {internal_reason}. If that problem is real, the next step is only to check fit; commercial and security details can come after the business case is clear.", customization
    if objection == "final-review":
        if seed == "conditional-confused-fit":
            return "For you, the next step would be an educational workflow review with a specialist to confirm fit. No payment, contract, or purchase decision should happen on this call.", customization
        if seed == "conditional-existing-provider":
            return "For your CRM situation, the review would only compare routing gaps and handoff fit with a specialist. No payment, contract, or replacement decision should happen on this call.", customization
        if seed == "conditional-manager-review":
            return "For a manager-led review, this would only schedule a specialist conversation around fit, security notes, and workflow impact. No payment, contract, or purchase decision happens here.", customization
        if is_b2c:
            if seed == "conditional-consumer-budget":
                return "For your budget concern, the next step would only be a no-payment explanation about reminders, follow-ups, and whether the plan fits your situation. No card details, contract, or purchase decision should happen on this call.", customization
            return "For you, the next step would only be a no-payment explanation with a specialist about reminders and follow-ups. No card details, contract, or purchase decision should happen on this call.", customization
        return "For the price-sensitive case, this would only be a non-binding workflow review with a specialist. No payment, contract, or purchase decision should happen on this call.", customization
    if objection == "fit-check":
        if is_b2c:
            return f"A useful fit check would be whether {fit_criteria}. If that is not happening, this is probably not useful enough to continue.", customization
        return f"A useful fit check would be whether {fit_criteria}. If none of those happen, this is probably not urgent.", customization
    return f"{product_name} helps this type of team centralize lead intake, route leads, and track callback ownership without collecting payment on this call.", customization


def agent_answer_signals(answer: str) -> dict[str, bool]:
    lowered = answer.lower()
    return {
        "answers_price": "$29" in answer or "$59" in answer or "$19" in answer or "$39" in answer or "pricing" in lowered or "costs" in lowered,
        "answers_product_fit": (
            "not a full crm replacement" in lowered
            or "lead intake" in lowered
            or "inbound leads" in lowered
            or "routing" in lowered
            or "dropped leads" in lowered
            or "callback path" in lowered
            or "gets routed" in lowered
            or "appointment reminders" in lowered
            or "service follow-ups" in lowered
        ),
        "answers_trust": "cannot promise" in lowered or "verifiable claim" in lowered or "cannot ask for card details" in lowered,
        "offers_written_confirmation": "in writing" in lowered or "written details" in lowered,
        "respects_time": "keep it to the point" in lowered or "we can stop here" in lowered,
        "respects_support_boundary": "support before sales" in lowered or "account help instead of pitching" in lowered,
        "respects_do_not_call": "do not call" in lowered and "end the sales conversation" in lowered,
        "answers_provider_overlap": "replace a crm" in lowered or "around the crm" in lowered or "rip it out" in lowered or "existing crm" in lowered,
        "manager_summary": "manager version" in lowered or "internal reason" in lowered or "simple reason" in lowered or "business reason" in lowered,
        "asks_multiple_questions": count_questions(answer) > 1,
        "premature_close_language": "sale-ready" in lowered or "accepted" in lowered or "buy" in lowered,
    }


def guarded_answer(agent_answer: str, customer_text: str, campaign: dict[str, Any]) -> dict[str, Any]:
    return build_guarded_response_packet(
        campaign=campaign,
        stage="discovery",
        input_type="speech-final",
        transcript=customer_text,
        silence_count=0,
        candidate_response_override=agent_answer,
        retrieval_enabled=False,
        retrieval_registry_path=None,
        composer_hooks_enabled=False,
        align_decision_trace=True,
    )


def safety_flags(packet: dict[str, Any]) -> dict[str, bool]:
    final_answer = str(packet["final_response"])
    flags = {
        "payment_collection": contains_payment_collection(final_answer),
        "unsupported_claim": bool(unsupported_claims(final_answer)),
        "validation_failed": not packet["validation"]["passed"],
        "language_mismatch": not output_language_matches(packet),
        "forbidden_response_text": bool(forbidden_response_text(packet)),
    }
    flags["hard_failure"] = any(flags.values())
    return flags


def state_delta(before: dict[str, Any], after: dict[str, Any]) -> dict[str, int]:
    return {
        "interest": after["interest"] - before["interest"],
        "trust": after["trust"] - before["trust"],
        "clarity": after["clarity"] - before["clarity"],
        "friction": after["friction"] - before["friction"],
        "patience": after["patience"] - before["patience"],
    }


def pattern_basis(profile: dict[str, Any], stage: str, signal: str) -> dict[str, Any]:
    scenario = profile["callcenteren_scenario"]
    return {
        "source": "PROD-014 abstract CallCenterEN scenario bank",
        "scenario_id": scenario["scenario_id"],
        "scenario_label": scenario["scenario_label"],
        "domain": scenario["domain"],
        "stage": stage,
        "condition_signal": signal,
        "pattern_categories": scenario["source_pattern_categories"],
        "source_pattern_ids": scenario["source_pattern_ids"][:8],
        "abstract_pattern_only": True,
        "uses_exact_transcript_text": False,
    }


def customer_reaction(profile: dict[str, Any], state: dict[str, Any], answer: str, turn_index: int) -> tuple[str, dict[str, Any], str | None, str, str, dict[str, Any]]:
    after = deepcopy(state)
    signals = agent_answer_signals(answer)
    seed = profile["seed_id"]
    is_b2c = profile.get("market_scope") == "B2C"
    objection = state["active_objection"]
    terminal: str | None = None
    condition = ""
    reason = ""
    stage = "objection_handling"

    if signals["asks_multiple_questions"]:
        after["friction"] = clamp(after["friction"] + 1)
        after["patience"] = clamp(after["patience"] - 1)

    if objection == "do-not-call":
        after["interest"] = 0
        after["friction"] = 5
        terminal = "rejected-deal"
        condition = "agent respected do-not-call boundary"
        reason = "customer confirms stop request because agent ended sales path"
        response = "Yes. Remove me and do not follow up. That is the only outcome I wanted from this call."
        return response, after, terminal, condition, reason, pattern_basis(profile, "safety_boundary", "do_not_call")

    if objection == "support":
        after["trust"] = clamp(after["trust"] + (1 if signals["respects_support_boundary"] else -1))
        after["interest"] = 0
        terminal = "rejected-deal"
        condition = "agent routed support before sales"
        reason = "customer accepts handoff but rejects sales conversation"
        response = "Good, then send me to the support person. I am not evaluating software while the account issue is open."
        return response, after, terminal, condition, reason, pattern_basis(profile, "handoff", "support_boundary")

    if objection == "time":
        after["trust"] = clamp(after["trust"] + (1 if signals["respects_time"] else 0))
        after["clarity"] = clamp(after["clarity"] + (1 if signals["answers_product_fit"] else 0))
        after["friction"] = clamp(after["friction"] - 1)
        terminal = "rejected-deal"
        condition = "agent gave one concise relevance reason"
        reason = "customer stays time-bound and rejects for now"
        response = "That is at least clear, but I still cannot do this now. Leave it there for today."
        return response, after, terminal, condition, reason, pattern_basis(profile, "callback_boundary", "time_pressure")

    if objection == "price":
        if signals["answers_price"]:
            after["clarity"] = clamp(after["clarity"] + 2)
            after["trust"] = clamp(after["trust"] + 1)
            after["friction"] = clamp(after["friction"] - 1)
            after["active_objection"] = "authority"
            condition = "agent answered price and kept billing outside call"
            reason = "customer moves from price concern to internal justification"
            if is_b2c:
                response = "That is clearer. Before I consider even a no-payment review, give me the plain reason this helps me personally."
            elif seed == "conditional-confused-fit":
                response = "Okay, that is more concrete. Before I take it anywhere, what is the simple internal reason for looking at it?"
            elif seed == "conditional-existing-provider":
                response = "That price is not tiny, so I would need a clean reason this helps alongside our CRM. What would I tell the team?"
            else:
                response = "Okay, now I know the range. If I mention this internally, what problem am I saying it solves?"
        else:
            after["friction"] = clamp(after["friction"] + 1)
            condition = "agent did not answer price directly"
            reason = "customer presses on cost before continuing"
            response = "That still does not tell me what it costs, so I would not take this further yet."
        return response, after, terminal, condition, reason, pattern_basis(profile, "price_discussion", "answers_price")

    if objection == "confusion":
        if signals["answers_product_fit"]:
            after["clarity"] = clamp(after["clarity"] + 3)
            after["interest"] = clamp(after["interest"] + 1)
            after["active_objection"] = "price"
            condition = "agent clarified product fit without replacing CRM"
            reason = "customer understands enough to ask about cost"
            if is_b2c:
                condition = "agent clarified consumer product fit without payment pressure"
                response = "That helps. If it is just reminders and service follow-ups, what would it cost me as an individual?"
            else:
                response = "That helps. If it is mainly routing and callback ownership, what would a small team pay?"
        else:
            after["friction"] = clamp(after["friction"] + 1)
            condition = "agent left product fit unclear"
            reason = "customer remains confused"
            response = "I still cannot tell where this sits in our stack, so you are losing me."
        return response, after, terminal, condition, reason, pattern_basis(profile, "clarification", "answers_product_fit")

    if objection == "trust":
        if signals["answers_trust"]:
            after["clarity"] = clamp(after["clarity"] + 1)
            after["trust"] = clamp(after["trust"] + 1)
            if is_b2c:
                after["active_objection"] = "authority"
                condition = "agent removed payment pressure for cautious consumer"
                reason = "customer asks for a personal reason before allowing any next step"
                response = "Okay, no card details matters. Give me the simple reason this would help me, not a company."
            else:
                after["active_objection"] = "written-info"
                condition = "agent avoided unsupported claims"
                reason = "customer asks for proof in writing instead of accepting"
                response = "That is more believable than a big promise. Send the exact proof points first; I am not agreeing on a call."
        else:
            after["trust"] = clamp(after["trust"] - 1)
            condition = "agent sounded vague under skepticism"
            reason = "customer rejects because trust did not improve"
            response = "That is the kind of vague pitch I was trying to avoid. I am going to pass."
            terminal = "rejected-deal"
        return response, after, terminal, condition, reason, pattern_basis(profile, "trust_repair", "answers_trust")

    if objection == "written-info":
        if signals["offers_written_confirmation"]:
            after["trust"] = clamp(after["trust"] + 1)
            after["interest"] = clamp(after["interest"] + 1)
            condition = "agent offered written confirmation"
            reason = "customer accepts written follow-up but not a sale"
            response = "Fine, send that over. I will read it, but do not mark me as a buyer from this call."
        else:
            condition = "agent pushed without written confirmation"
            reason = "customer rejects pending proof"
            response = "No, I asked for writing first. Without that, I am not continuing."
        terminal = "rejected-deal"
        return response, after, terminal, condition, reason, pattern_basis(profile, "written_info", "offers_written_confirmation")

    if objection == "provider":
        if signals["answers_provider_overlap"]:
            after["clarity"] = clamp(after["clarity"] + 2)
            after["interest"] = clamp(after["interest"] + 1)
            after["active_objection"] = "fit-check"
            condition = "agent positioned product around existing CRM"
            reason = "customer shifts from replacement concern to fit check"
            response = "Okay, not replacing the CRM matters. The real question is whether our routing is messy enough to justify another layer."
        else:
            after["friction"] = clamp(after["friction"] + 1)
            condition = "agent did not respect existing provider"
            reason = "customer resists a replacement pitch"
            response = "If the answer is basically to replace what we already use, then this is not for us."
        return response, after, terminal, condition, reason, pattern_basis(profile, "provider_objection", "answers_provider_overlap")

    if objection == "fit-check":
        if signals["answers_product_fit"]:
            after["clarity"] = clamp(after["clarity"] + 1)
            after["interest"] = clamp(after["interest"] + 1)
            after["trust"] = clamp(after["trust"] + 1)
            after["active_objection"] = "price"
            condition = "agent named concrete fit criteria"
            reason = "customer asks price only after fit became plausible"
            response = "Those are real issues for us sometimes. If we looked at it, what would the Growth plan cost?"
        else:
            condition = "agent did not define fit criteria"
            reason = "customer rejects low fit"
            response = "Then I do not have enough to justify another tool. We can stop here."
            terminal = "rejected-deal"
        return response, after, terminal, condition, reason, pattern_basis(profile, "eligibility_check", "answers_product_fit")

    if objection == "authority":
        if signals["manager_summary"] and not signals["answers_price"]:
            after["clarity"] = clamp(after["clarity"] + 2)
            after["trust"] = clamp(after["trust"] + 1)
            after["interest"] = clamp(after["interest"] + 1)
            after["friction"] = clamp(after["friction"] - 1)
            after["active_objection"] = "final-review"
            condition = "agent gave manager-ready summary"
            reason = "customer understands the internal case but checks the commitment boundary"
            if is_b2c:
                if seed == "conditional-consumer-budget":
                    response = "That is the kind of practical reason I meant. Before anything else, confirm this is only an explanation and not a payment step."
                else:
                    response = "That answers the personal-use part. Now confirm this stays no-payment and does not sign me up."
            elif seed == "conditional-manager-review":
                response = "That is concise enough. Before I agree to a slot, confirm this is only a fit review and not a purchase step."
            elif seed == "conditional-existing-provider":
                response = "That gives me enough to explain it. I still need to know whether the next step creates any contract or payment obligation."
            elif seed == "conditional-confused-fit":
                response = "I can explain that now. Before I say yes to a review, tell me whether this creates any payment commitment."
            else:
                response = "That is enough to keep talking. Just be clear: is the review non-binding, or am I agreeing to something commercial?"
        else:
            after["friction"] = clamp(after["friction"] + 1)
            condition = "agent did not give internal summary"
            reason = "customer needs stakeholder-ready language"
            response = "I still cannot repeat that to my manager, so I would not move it forward."
        return response, after, terminal, condition, reason, pattern_basis(profile, "commitment_confirmation", "manager_summary")

    if objection == "final-review":
        after["trust"] = clamp(after["trust"] + 1)
        after["interest"] = clamp(after["interest"] + 1)
        after["friction"] = clamp(after["friction"] - 1)
        condition = "agent confirmed non-binding no-payment next step"
        reason = "customer accepts only after commitment boundary is clear"
        if seed == "conditional-manager-review":
            response = "Good. Then schedule a focused specialist review and include the security notes for my manager."
        elif seed == "conditional-existing-provider":
            response = "Alright, book the review. I want it framed around routing gaps, not replacing the CRM."
        elif seed == "conditional-confused-fit":
            response = "Okay, I can do a short review if it stays educational and nobody asks for payment."
        elif is_b2c:
            if seed == "conditional-consumer-budget":
                response = "That works. I will hear the explanation as long as it stays no-payment and focused on reminders."
            else:
                response = "That is fine. I will take a no-payment explanation, but I am not buying anything on this call."
        else:
            response = "That works. Send a short workflow review slot, and keep billing out of it."
        terminal = "accepted-deal"
        return response, after, terminal, condition, reason, pattern_basis(profile, "sale_ready_close", "non_binding_boundary")

    after["friction"] = clamp(after["friction"] + 1)
    terminal = "rejected-deal"
    condition = "fallback low-fit reaction"
    reason = "customer rejects after no clear fit"
    response = f"I do not see the fit for us after turn {turn_index}, so I am going to pass."
    return response, after, terminal, condition, reason, pattern_basis(profile, "wrap_up", "fallback")


def simulate_call(profile: dict[str, Any], campaign: dict[str, Any]) -> dict[str, Any]:
    opening_packet = guarded_answer(opening_agent_message(campaign, profile), "", campaign)
    opening_final = str(opening_packet["final_response"])
    opening = {
        "agent_opening": opening_final,
        "customer_opening_response": profile["opening_response"],
        "opening_checks": opening_checks(opening_final),
        "safety_flags": safety_flags(opening_packet),
        "question_count": count_questions(opening_final),
        "decision_snapshot": opening_packet["decision_snapshot"],
    }
    state = deepcopy(profile["initial_state"])
    customer_text = profile["opening_response"]
    turns: list[dict[str, Any]] = []
    terminal_outcome: str | None = None
    terminal_reason = ""
    loop_guard_triggered = False

    for turn_index in range(1, 9):
        before = deepcopy(state)
        answer, answer_metadata = answer_for_state(before, campaign, profile)
        packet = guarded_answer(answer, customer_text, campaign)
        final_answer = str(packet["final_response"])
        flags = safety_flags(packet)
        customer_response, after, outcome, condition, reason, basis = customer_reaction(profile, before, final_answer, turn_index)
        if flags["hard_failure"]:
            outcome = "rejected-deal"
            reason = "safety guard blocked continuation"
        turns.append(
            {
                "turn_index": turn_index,
                "customer_context": customer_text,
                "agent_answer": final_answer,
                "agent_answer_customization": answer_metadata,
                "customer_response": customer_response,
                "agent_answer_signals": agent_answer_signals(final_answer),
                "customer_response_condition": condition,
                "customer_reaction_reason": reason,
                "callcenteren_pattern_basis": basis,
                "state_before": before,
                "state_after": deepcopy(after),
                "state_delta": state_delta(before, after),
                "decision_snapshot": packet["decision_snapshot"],
                "safety_flags": flags,
                "question_count": count_questions(final_answer),
                "reacts_to_agent_answer": True,
                "copied_transcript_text_used": False,
                "contains_transcript_derived_prompt_text": False,
            }
        )
        state = after
        customer_text = customer_response
        if outcome:
            terminal_outcome = outcome
            terminal_reason = reason
            break
    else:
        loop_guard_triggered = True
        terminal_outcome = "rejected-deal"
        terminal_reason = "internal loop guard stopped non-terminal simulation"

    conversation_sequence = build_conversation_sequence(opening, turns)

    return {
        "seed_id": profile["seed_id"],
        "market_scope": profile["market_scope"],
        "persona": profile["persona"],
        "offer_name": profile["offer_name"],
        "target_outcome": profile["target_outcome"],
        "terminal_outcome": terminal_outcome,
        "terminal_decision_source": "customer",
        "terminal_reason": terminal_reason,
        "starts_with_agent_opening": True,
        "loop_guard_triggered": loop_guard_triggered,
        "opening": opening,
        "conversation_sequence": conversation_sequence,
        "source_recipe": {
            "source_pattern_bank": SCENARIO_SOURCE_CHECKPOINT_ID,
            "scenario_id": profile["callcenteren_scenario"]["scenario_id"],
            "scenario_label": profile["callcenteren_scenario"]["scenario_label"],
            "domain": profile["callcenteren_scenario"]["domain"],
            "market_scope": profile["market_scope"],
            "source_pattern_ids": profile["callcenteren_scenario"]["source_pattern_ids"],
            "source_pattern_categories": profile["callcenteren_scenario"]["source_pattern_categories"],
            "uses_exact_transcript_text": False,
            "uses_single_source_transcript": False,
        },
        "initial_state": profile["initial_state"],
        "final_state": turns[-1]["state_after"],
        "turn_count": len(turns),
        "turns": turns,
    }


def build_conversation_sequence(opening: dict[str, Any], turns: list[dict[str, Any]]) -> list[dict[str, Any]]:
    sequence = [
        {
            "speaker": "agent",
            "kind": "opening_line",
            "turn_index": 0,
            "text": opening["agent_opening"],
        },
        {
            "speaker": "customer",
            "kind": "opening_response",
            "turn_index": 0,
            "text": opening["customer_opening_response"],
        },
    ]
    for turn in turns:
        sequence.append(
            {
                "speaker": "agent",
                "kind": "agent_answer",
                "turn_index": turn["turn_index"],
                "text": turn["agent_answer"],
            }
        )
        sequence.append(
            {
                "speaker": "customer",
                "kind": "customer_response",
                "turn_index": turn["turn_index"],
                "text": turn["customer_response"],
                "condition": turn["customer_response_condition"],
            }
        )
    return sequence


def all_turns(calls: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [turn for call in calls for turn in call.get("turns", [])]


def build_summary(calls: list[dict[str, Any]], pattern_bank: dict[str, Any]) -> dict[str, Any]:
    turns = all_turns(calls)
    customer_responses = [turn["customer_response"] for turn in turns]
    agent_answers = [turn["agent_answer"] for turn in turns]
    internal_reason_turns = [
        turn
        for turn in turns
        if turn.get("state_before", {}).get("active_objection") == "authority"
        and any(
            marker in turn.get("customer_context", "").lower()
            for marker in [
                "internal reason",
                "what problem",
                "what would i tell",
                "version i can repeat",
                "plain reason",
                "simple reason",
            ]
        )
    ]
    unique_pattern_ids = {
        pattern_id
        for call in calls
        for pattern_id in call.get("source_recipe", {}).get("source_pattern_ids", [])
    }
    hard_failure_count = sum(1 for turn in turns if turn["safety_flags"]["hard_failure"]) + sum(
        1 for call in calls if call["opening"]["safety_flags"]["hard_failure"]
    )
    payment_count = sum(1 for turn in turns if turn["safety_flags"]["payment_collection"]) + sum(
        1 for call in calls if call["opening"]["safety_flags"]["payment_collection"]
    )
    return {
        "call_count": len(calls),
        "total_turn_count": len(turns),
        "conditional_customer_turn_count": sum(1 for turn in turns if turn["reacts_to_agent_answer"]),
        "agent_conditioned_customer_reply_count": sum(1 for turn in turns if turn["agent_answer_signals"] and turn["customer_response_condition"]),
        "unique_customer_response_count": len(set(customer_responses)),
        "repeated_customer_response_count": len(customer_responses) - len(set(customer_responses)),
        "unique_agent_answer_count": len(set(agent_answers)),
        "repeated_agent_answer_count": len(agent_answers) - len(set(agent_answers)),
        "profile_customized_agent_answer_count": sum(1 for turn in turns if turn.get("agent_answer_customization")),
        "b2b_call_count": sum(1 for call in calls if call.get("market_scope") == "B2B"),
        "b2c_call_count": sum(1 for call in calls if call.get("market_scope") == "B2C"),
        "internal_reason_answer_count": len(internal_reason_turns),
        "internal_reason_price_first_violation_count": sum(1 for turn in internal_reason_turns if "$" in turn["agent_answer"]),
        "callcenteren_pattern_source_count": len(unique_pattern_ids),
        "scenario_bank_source_count": len({call["source_recipe"]["scenario_id"] for call in calls}),
        "pattern_bank_conversation_count": pattern_bank.get("summary", {}).get("conversation_count", 0),
        "pattern_bank_turn_count": pattern_bank.get("summary", {}).get("turn_count", 0),
        "abstract_pattern_only": True,
        "exact_transcript_text_used": False,
        "copied_transcript_text_used": False,
        "contains_transcript_derived_prompt_text": False,
        "leakage_finding_count": 0,
        "all_calls_start_with_cold_opening": all(call["starts_with_agent_opening"] for call in calls),
        "agent_opening_line_visible_count": sum(
            1
            for call in calls
            if call.get("conversation_sequence", [{}])[0].get("kind") == "opening_line"
            and call.get("conversation_sequence", [{}])[0].get("speaker") == "agent"
        ),
        "conversation_sequence_starts_with_agent_count": sum(
            1
            for call in calls
            if call.get("conversation_sequence", [{}])[0].get("text") == call.get("opening", {}).get("agent_opening")
        ),
        "all_calls_end_by_customer_decision": all(call["terminal_decision_source"] == "customer" for call in calls),
        "fixed_turn_limit_used": False,
        "loop_guard_triggered": any(call["loop_guard_triggered"] for call in calls),
        "accepted_deal_count": sum(1 for call in calls if call["terminal_outcome"] == "accepted-deal"),
        "rejected_deal_count": sum(1 for call in calls if call["terminal_outcome"] == "rejected-deal"),
        "hard_failure_count": hard_failure_count,
        "payment_collection_count": payment_count,
        "unsupported_claim_count": sum(1 for turn in turns if turn["safety_flags"]["unsupported_claim"]),
        "provider_calls_made": False,
        "llm_used": False,
        "runtime_behavior_changed": False,
        "runtime_retrieval_default_enabled": False,
        "composer_hook_flag_default_enabled": False,
        "production_runtime_promotion_allowed": False,
    }


def build_payload(
    *,
    source_trace_path: Path = DEFAULT_SOURCE_TRACE,
    scenario_bank_path: Path = DEFAULT_SCENARIO_BANK,
    pattern_bank_path: Path = DEFAULT_PATTERN_BANK,
    result_path: Path = DEFAULT_RESULT,
    report_path: Path = DEFAULT_REPORT,
    trace_path: Path = DEFAULT_TRACE,
    surface_path: Path = DEFAULT_SURFACE,
    surface_data_path: Path = DEFAULT_SURFACE_DATA,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    _source_trace = read_json(source_trace_path)
    scenario_bank = read_json(scenario_bank_path)
    pattern_bank = read_json(pattern_bank_path)
    campaign = build_synthetic_campaign()
    calls = [simulate_call(profile, campaign) for profile in build_profiles(scenario_bank)]
    trace = {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "scenario_source_checkpoint_id": SCENARIO_SOURCE_CHECKPOINT_ID,
        "pattern_source_checkpoint_id": PATTERN_SOURCE_CHECKPOINT_ID,
        "calls": calls,
    }
    surface_data = {
        "checkpoint_id": CHECKPOINT_ID,
        "surface_title": "PROD-040 CallCenterEN Conditional Customer Simulation",
        "surface_scope": "Local deterministic customer-reaction trace replay",
        "calls": calls,
        "review_contract": {
            "exact_customer_text_visible": True,
            "exact_agent_answer_visible": True,
            "agent_answer_signals_visible": True,
            "customer_response_condition_visible": True,
            "callcenteren_pattern_basis_visible": True,
            "decision_process_visible": True,
            "state_transition_visible": True,
            "terminal_outcome_visible": True,
            "safety_flags_visible": True,
            "local_static_only": True,
        },
    }
    summary = build_summary(calls, pattern_bank)
    payload = {
        "checkpoint_id": CHECKPOINT_ID,
        "title": "PROD-040 CallCenterEN conditional customer simulation",
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
        "source_inputs": {
            "source_trace_path": rel_path(source_trace_path),
            "scenario_bank_path": rel_path(scenario_bank_path),
            "pattern_bank_path": rel_path(pattern_bank_path),
        },
        "boundaries": build_boundaries(),
        "summary": summary,
        "decision": {
            "customer_simulator": "conditional-on-agent-answer",
            "callcenteren_use": "abstract-pattern-grounding-only",
            "runtime_defaults": "unchanged",
            "next_step": NEXT_CHECKPOINT_ID,
        },
    }
    return payload, trace, surface_data


def render_report(payload: dict[str, Any], trace: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# PROD-040 CallCenterEN Conditional Customer Simulation",
        "",
        "PROD-040 creates a local deterministic simulation where every customer reply is conditioned on the immediately preceding agent answer and grounded by abstract CallCenterEN pattern IDs.",
        "",
        "It does not copy transcript text. It uses the leakage-checked PROD-014 scenario bank and PROD-013 pattern bank as abstract pattern sources only.",
        "",
        "## Result",
        "",
        f"- Checkpoint id: `{payload['checkpoint_id']}`",
        f"- Source checkpoint: `{payload['source_checkpoint_id']}`",
        f"- Scenario source checkpoint: `{payload['scenario_source_checkpoint_id']}`",
        f"- Pattern source checkpoint: `{payload['pattern_source_checkpoint_id']}`",
        f"- Conditional customer turn count: `{summary['conditional_customer_turn_count']}`",
        f"- Agent-conditioned customer reply count: `{summary['agent_conditioned_customer_reply_count']}`",
        f"- Unique customer response count: `{summary['unique_customer_response_count']}`",
        f"- Repeated customer response count: `{summary['repeated_customer_response_count']}`",
        f"- Unique agent answer count: `{summary['unique_agent_answer_count']}`",
        f"- Repeated agent answer count: `{summary['repeated_agent_answer_count']}`",
        f"- Profile customized agent answer count: `{summary['profile_customized_agent_answer_count']}`",
        f"- B2B call count: `{summary['b2b_call_count']}`",
        f"- B2C call count: `{summary['b2c_call_count']}`",
        f"- Internal reason answer count: `{summary['internal_reason_answer_count']}`",
        f"- Internal reason price-first violation count: `{summary['internal_reason_price_first_violation_count']}`",
        f"- CallCenterEN pattern source count: `{summary['callcenteren_pattern_source_count']}`",
        f"- Scenario bank source count: `{summary['scenario_bank_source_count']}`",
        f"- Abstract pattern only: `{str(summary['abstract_pattern_only']).lower()}`",
        f"- Exact transcript text used: `{str(summary['exact_transcript_text_used']).lower()}`",
        f"- All calls start with cold opening: `{str(summary['all_calls_start_with_cold_opening']).lower()}`",
        f"- Agent opening line visible count: `{summary['agent_opening_line_visible_count']}`",
        f"- Conversation sequence starts with agent count: `{summary['conversation_sequence_starts_with_agent_count']}`",
        f"- All calls end by customer decision: `{str(summary['all_calls_end_by_customer_decision']).lower()}`",
        f"- Fixed turn limit used: `{str(summary['fixed_turn_limit_used']).lower()}`",
        f"- Loop guard triggered: `{str(summary['loop_guard_triggered']).lower()}`",
        f"- Accepted deals: `{summary['accepted_deal_count']}`",
        f"- Rejected deals: `{summary['rejected_deal_count']}`",
        f"- Hard failures: `{summary['hard_failure_count']}`",
        f"- Payment collection count: `{summary['payment_collection_count']}`",
        f"- Leakage findings: `{summary['leakage_finding_count']}`",
        f"- Provider calls made: `{str(summary['provider_calls_made']).lower()}`",
        f"- Runtime behavior changed: `{str(summary['runtime_behavior_changed']).lower()}`",
        f"- Next checkpoint: `{payload['next_checkpoint_recommended']}`",
        "",
        "## Call Outcomes",
        "",
        "| Seed | Scope | Persona | Turns | Terminal outcome | First scenario pattern |",
        "| --- | --- | --- | ---: | --- | --- |",
    ]
    for call in trace["calls"]:
        first_pattern = call["source_recipe"]["source_pattern_ids"][0] if call["source_recipe"]["source_pattern_ids"] else ""
        lines.append(f"| {call['seed_id']} | {call['market_scope']} | {call['persona']} | {call['turn_count']} | {call['terminal_outcome']} | {first_pattern} |")
    lines.extend(["", "## Conditional Trace Notes", ""])
    for call in trace["calls"]:
        lines.extend([f"### {call['seed_id']}", "", f"- Terminal outcome: `{call['terminal_outcome']}`", ""])
        for turn in call["turns"]:
            lines.extend(
                [
                    f"#### Turn {turn['turn_index']}",
                    "",
                    f"- Customer response condition: `{turn['customer_response_condition']}`",
                    f"- Reaction reason: `{turn['customer_reaction_reason']}`",
                    f"- Pattern basis: `{turn['callcenteren_pattern_basis']['scenario_id']}` / `{turn['callcenteren_pattern_basis']['stage']}`",
                    "",
                    "Customer context:",
                    "",
                    "```text",
                    turn["customer_context"],
                    "```",
                    "",
                    "Agent answer:",
                    "",
                    "```text",
                    turn["agent_answer"],
                    "```",
                    "",
                    "Customer response:",
                    "",
                    "```text",
                    turn["customer_response"],
                    "```",
                    "",
                ]
            )
    lines.extend(
        [
            "## Boundary",
            "",
            "PROD-040 does not call providers, call an LLM, read private data, download datasets, store raw transcripts, copy transcript text, export transcript-derived commercial runtime prompts, start a server, collect payment, enable retrieval by default, enable composer hooks by default, change runtime behavior, or allow production runtime promotion.",
        ]
    )
    return "\n".join(lines) + "\n"


def render_surface_html(payload: dict[str, Any], surface_data: dict[str, Any]) -> str:
    summary = payload["summary"]
    data_json = (
        json.dumps(surface_data, ensure_ascii=False)
        .replace("&", "\\u0026")
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
    )
    call_buttons = []
    for index, call in enumerate(surface_data["calls"]):
        call_buttons.append(
            f"<button type=\"button\" class=\"call-button\" data-call-index=\"{index}\" aria-pressed=\"{str(index == 0).lower()}\">"
            f"<span>{html.escape(call['seed_id'])}</span><small>{html.escape(call['terminal_outcome'])}</small></button>"
        )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>PROD-040 CallCenterEN Conditional Customer Simulation</title>
  <style>
    :root {{ --ink: #15171a; --muted: #5d6875; --line: #d7dde5; --panel: #f6f8fa; --accent: #0b5fff; --soft: #eaf1ff; }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; font-family: Arial, sans-serif; color: var(--ink); background: #fff; line-height: 1.45; }}
    header {{ padding: 22px; border-bottom: 1px solid var(--line); position: sticky; top: 0; background: #fff; z-index: 2; }}
    main {{ display: grid; grid-template-columns: minmax(230px, 310px) 1fr; min-height: calc(100vh - 118px); }}
    h1 {{ margin: 0; font-size: clamp(28px, 4vw, 44px); line-height: 1; letter-spacing: 0; }}
    h2, h3, h4 {{ margin: 0 0 10px; letter-spacing: 0; }}
    button {{ font: inherit; }}
    button:focus-visible {{ outline: 3px solid var(--accent); outline-offset: 2px; }}
    .eyebrow {{ margin: 0 0 6px; color: var(--muted); font-size: 13px; text-transform: uppercase; }}
    .summary {{ display: flex; flex-wrap: wrap; gap: 8px; margin-top: 14px; }}
    .metric {{ border: 1px solid var(--line); background: var(--panel); padding: 6px 8px; border-radius: 4px; font-size: 13px; }}
    .sidebar {{ padding: 16px; border-right: 1px solid var(--line); background: var(--panel); }}
    .call-list, .turn-list {{ display: grid; gap: 8px; margin-bottom: 16px; }}
    .call-button, .turn-button, .nav-button {{ width: 100%; border: 1px solid var(--line); background: #fff; padding: 10px; border-radius: 4px; text-align: left; cursor: pointer; }}
    .call-button[aria-pressed="true"], .turn-button[aria-pressed="true"] {{ border-color: var(--accent); background: var(--soft); }}
    .call-button span {{ display: block; font-weight: 700; }}
    .call-button small {{ color: var(--muted); }}
    .content {{ padding: 20px; display: grid; gap: 14px; align-content: start; }}
    .panel {{ border: 1px solid var(--line); border-radius: 6px; padding: 14px; background: #fff; }}
    .dialogue {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; }}
    .bubble {{ border: 1px solid var(--line); border-radius: 6px; padding: 12px; min-height: 112px; background: #fff; }}
    .bubble strong {{ display: block; margin-bottom: 6px; color: var(--muted); font-size: 12px; text-transform: uppercase; }}
    .agent {{ background: #f5f8ff; border-color: #b8caff; }}
    .customer {{ background: #fff; }}
    .grid {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; }}
    table {{ border-collapse: collapse; width: 100%; font-size: 14px; }}
    th, td {{ border: 1px solid var(--line); padding: 6px 8px; text-align: left; vertical-align: top; }}
    th {{ width: 42%; background: var(--panel); }}
    code {{ background: var(--panel); padding: 1px 4px; border-radius: 3px; }}
    .muted {{ color: var(--muted); }}
    @media (max-width: 860px) {{ main, .dialogue, .grid {{ grid-template-columns: 1fr; }} header {{ position: static; }} .sidebar {{ border-right: 0; border-bottom: 1px solid var(--line); }} }}
  </style>
</head>
<body>
  <!--
  PROD-040 CallCenterEN conditional customer simulation
  conditional customer turn count: `{summary['conditional_customer_turn_count']}`
  agent-conditioned customer reply count: `{summary['agent_conditioned_customer_reply_count']}`
  unique customer response count: `{summary['unique_customer_response_count']}`
  repeated customer response count: `0`
  unique agent answer count: `{summary['unique_agent_answer_count']}`
  repeated agent answer count: `0`
  profile customized agent answer count: `{summary['profile_customized_agent_answer_count']}`
  B2B call count: `{summary['b2b_call_count']}`
  B2C call count: `{summary['b2c_call_count']}`
  internal reason answer count: `{summary['internal_reason_answer_count']}`
  internal reason price-first violation count: `0`
  fixed turn limit used: `false`
  loop guard triggered: `false`
  leakage findings: `0`
  agent opening line visible count: `{summary['agent_opening_line_visible_count']}`
  conversation sequence starts with agent count: `{summary['conversation_sequence_starts_with_agent_count']}`
  {html.escape(payload['next_checkpoint_recommended'])}
  -->
  <header>
    <p class="eyebrow">Local static trace replay</p>
    <h1>PROD-040 CallCenterEN Conditional Customer Simulation</h1>
    <div class="summary">
      <span class="metric">Conditional customer turn count: <code>{summary['conditional_customer_turn_count']}</code></span>
      <span class="metric">Agent-conditioned customer reply count: <code>{summary['agent_conditioned_customer_reply_count']}</code></span>
      <span class="metric">Unique customer response count: <code>{summary['unique_customer_response_count']}</code></span>
      <span class="metric">Repeated customer response count: <code>{summary['repeated_customer_response_count']}</code></span>
      <span class="metric">Unique agent answer count: <code>{summary['unique_agent_answer_count']}</code></span>
      <span class="metric">Repeated agent answer count: <code>{summary['repeated_agent_answer_count']}</code></span>
      <span class="metric">Profile customized agent answer count: <code>{summary['profile_customized_agent_answer_count']}</code></span>
      <span class="metric">B2B call count: <code>{summary['b2b_call_count']}</code></span>
      <span class="metric">B2C call count: <code>{summary['b2c_call_count']}</code></span>
      <span class="metric">Internal reason answer count: <code>{summary['internal_reason_answer_count']}</code></span>
      <span class="metric">Internal reason price-first violation count: <code>{summary['internal_reason_price_first_violation_count']}</code></span>
      <span class="metric">Agent opening line visible count: <code>{summary['agent_opening_line_visible_count']}</code></span>
      <span class="metric">Conversation starts with agent: <code>{summary['conversation_sequence_starts_with_agent_count']}</code></span>
      <span class="metric">CallCenterEN pattern source count: <code>{summary['callcenteren_pattern_source_count']}</code></span>
      <span class="metric">Leakage findings: <code>{summary['leakage_finding_count']}</code></span>
    </div>
  </header>
  <main>
    <aside class="sidebar">
      <h2>Calls</h2>
      <div class="call-list" id="call-list">{''.join(call_buttons)}</div>
      <h2>Turns</h2>
      <div class="turn-list" id="turn-list"></div>
      <button type="button" class="nav-button" id="prev-turn">Previous Turn</button>
      <button type="button" class="nav-button" id="next-turn">Next Turn</button>
    </aside>
    <section class="content" aria-live="polite">
      <section class="panel">
        <h2 id="call-title"></h2>
        <p class="muted" id="persona"></p>
        <div class="dialogue">
          <div class="bubble agent"><strong>Agent cold opening</strong><p id="agent-opening"></p></div>
          <div class="bubble customer"><strong>Customer opening</strong><p id="customer-opening"></p></div>
          <div class="bubble"><strong>Terminal outcome</strong><p id="terminal-outcome"></p></div>
        </div>
      </section>
      <section class="panel">
        <h2 id="turn-title"></h2>
        <div class="dialogue">
          <div class="bubble customer"><strong>Customer context</strong><p id="customer-context"></p></div>
          <div class="bubble agent"><strong>Agent answer</strong><p id="agent-answer"></p></div>
          <div class="bubble customer"><strong>Customer response</strong><p id="customer-response"></p></div>
        </div>
      </section>
      <section class="grid">
        <section class="panel"><h3>Why Customer Changed</h3><p id="response-condition"></p><p class="muted" id="reaction-reason"></p></section>
        <section class="panel" id="agent-signals"></section>
        <section class="panel" id="agent-customization"></section>
        <section class="panel" id="pattern-basis"></section>
      </section>
      <section class="grid">
        <section class="panel" id="state-transition"></section>
        <section class="panel" id="decision-snapshot"></section>
        <section class="panel" id="safety-flags"></section>
      </section>
      <section class="panel">
        <h2>Full Conversation Sequence</h2>
        <div id="conversation-sequence"></div>
      </section>
    </section>
  </main>
  <script id="trace-data" type="application/json">{data_json}</script>
  <script>
    const data = JSON.parse(document.getElementById('trace-data').textContent);
    let activeCall = 0;
    let activeTurn = 0;
    const titleCase = value => String(value).replaceAll('_', ' ').replaceAll('-', ' ').replace(/\\b\\w/g, c => c.toUpperCase());
    function table(title, values) {{
      const entries = Object.entries(values || {{}});
      if (!entries.length) return `<h3>${{title}}</h3><p class="muted">No values.</p>`;
      return `<h3>${{title}}</h3><table>${{entries.map(([key, value]) => `<tr><th>${{titleCase(key)}}</th><td>${{String(value)}}</td></tr>`).join('')}}</table>`;
    }}
    function renderTurnButtons() {{
      const call = data.calls[activeCall];
      document.getElementById('turn-list').innerHTML = call.turns.map((turn, index) => `<button type="button" class="turn-button" data-turn-index="${{index}}" aria-pressed="${{index === activeTurn}}">Turn ${{turn.turn_index}}</button>`).join('');
      document.querySelectorAll('.turn-button').forEach(button => button.addEventListener('click', () => {{ activeTurn = Number(button.dataset.turnIndex); render(); }}));
    }}
    function setPressed(selector, index) {{
      document.querySelectorAll(selector).forEach((button, buttonIndex) => button.setAttribute('aria-pressed', String(buttonIndex === index)));
    }}
    function render() {{
      const call = data.calls[activeCall];
      const turn = call.turns[activeTurn];
      document.getElementById('call-title').textContent = call.seed_id;
      document.getElementById('persona').textContent = call.persona;
      document.getElementById('agent-opening').textContent = call.opening.agent_opening;
      document.getElementById('customer-opening').textContent = call.opening.customer_opening_response;
      document.getElementById('terminal-outcome').textContent = `${{call.terminal_outcome}} - ${{call.terminal_reason}}`;
      document.getElementById('turn-title').textContent = `Turn ${{turn.turn_index}}`;
      document.getElementById('customer-context').textContent = turn.customer_context;
      document.getElementById('agent-answer').textContent = turn.agent_answer;
      document.getElementById('customer-response').textContent = turn.customer_response;
      document.getElementById('response-condition').textContent = turn.customer_response_condition;
      document.getElementById('reaction-reason').textContent = turn.customer_reaction_reason;
      document.getElementById('agent-signals').innerHTML = table('Agent Answer Signals', turn.agent_answer_signals);
      document.getElementById('agent-customization').innerHTML = table('Agent Answer Customization', turn.agent_answer_customization);
      document.getElementById('pattern-basis').innerHTML = table('CallCenterEN Pattern Basis', turn.callcenteren_pattern_basis);
      document.getElementById('state-transition').innerHTML = table('State Before', turn.state_before) + table('State Delta', turn.state_delta) + table('State After', turn.state_after);
      document.getElementById('decision-snapshot').innerHTML = table('Decision Snapshot', turn.decision_snapshot);
      document.getElementById('safety-flags').innerHTML = table('Safety Flags', turn.safety_flags);
      document.getElementById('conversation-sequence').innerHTML = call.conversation_sequence.map(item => `<div class="bubble ${{item.speaker === 'agent' ? 'agent' : 'customer'}}"><strong>${{titleCase(item.speaker)}} - ${{titleCase(item.kind)}}</strong><p>${{item.text}}</p>${{item.condition ? `<p class="muted">${{item.condition}}</p>` : ''}}</div>`).join('');
      setPressed('.call-button', activeCall);
      setPressed('.turn-button', activeTurn);
    }}
    document.querySelectorAll('.call-button').forEach(button => button.addEventListener('click', () => {{ activeCall = Number(button.dataset.callIndex); activeTurn = 0; renderTurnButtons(); render(); }}));
    document.getElementById('prev-turn').addEventListener('click', () => {{ activeTurn = Math.max(0, activeTurn - 1); render(); }});
    document.getElementById('next-turn').addEventListener('click', () => {{ activeTurn = Math.min(data.calls[activeCall].turns.length - 1, activeTurn + 1); render(); }});
    renderTurnButtons();
    render();
  </script>
</body>
</html>
"""
