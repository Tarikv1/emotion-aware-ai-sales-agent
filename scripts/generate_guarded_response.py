#!/usr/bin/env python3
import argparse
import json
import time
from pathlib import Path

from core_sales_delivery_playbook import build_core_sales_delivery_pack
from product_agent_output_contract import call_control_for_next_action
from rag_guarded_retrieval_policy import (
    BLOCKING_CONTEXT_FLAGS,
    load_json as load_retrieval_json,
    retrieve_for_case,
    validate_registry_payload,
)
from realtime_turn_cli import build_turn_case, find_campaign, run_turn_decision
from run_realtime_turn_simulation import load_realtime_cases, normalize_response_language
from runtime_composer_hooks import apply_runtime_composer_hooks


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CASES_PATH = ROOT / "research" / "experiments" / "cases" / "prod-005-realtime-latency-call-control.json"
RESPONSE_GENERATION_ID = "RESP-001-local-guarded"
PROVIDER = "local-guarded-composer"
DEFAULT_RETRIEVAL_REGISTRY = ROOT / "research" / "experiments" / "generated" / "RAG-017-runtime-knowledge-registry" / "result.json"
DEFAULT_RETRIEVAL_TARGET_MS = 150
DEFAULT_RETRIEVAL_ACCEPTABLE_MS = 300
DEFAULT_RETRIEVAL_MIN_SCORE = 1

UNIVERSAL_FORBIDDEN_CLAIMS = [
    "guarantee",
    "guaranteed",
    "guaranteed savings",
    "save you money",
    "always be stable",
    "no risk",
    "covered for sure",
    "payout",
    "legal advice",
    "medical advice",
]


def resolve_project_path(path_text: str | None) -> Path | None:
    if path_text is None:
        return None
    path = Path(path_text)
    if path.is_absolute():
        return path
    return ROOT / path


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def unique_preserving_order(values: list[str]) -> list[str]:
    seen = set()
    unique = []
    for value in values:
        normalized = value.strip()
        key = normalized.lower()
        if not normalized or key in seen:
            continue
        seen.add(key)
        unique.append(normalized)
    return unique


def build_guardrails(campaign: dict) -> dict:
    campaign_forbidden_claims = campaign.get("forbidden_claims", [])
    return {
        "guardrail_source": "SalesCampaign plus universal response-safety rules",
        "allowed_claims": campaign.get("allowed_claims", []),
        "forbidden_claims": unique_preserving_order(UNIVERSAL_FORBIDDEN_CLAIMS + campaign_forbidden_claims),
        "required_disclosures": campaign.get("required_disclosures", []),
        "escalation_triggers": campaign.get("escalation_triggers", []),
        "human_handoff_role": campaign.get("human_handoff_role"),
        "compliance_notes": campaign.get("compliance_notes"),
    }


def build_campaign_fact_grounding(campaign: dict) -> dict:
    return {
        "campaign_facts_override_rag": True,
        "campaign_id": campaign.get("campaign_id"),
        "product_name": campaign.get("product_name"),
        "allowed_claims": campaign.get("allowed_claims", []),
        "forbidden_claims": campaign.get("forbidden_claims", []),
        "required_disclosures": campaign.get("required_disclosures", []),
        "discount_terms": campaign.get("discount_terms", []),
        "deadline_terms": campaign.get("deadline_terms", []),
        "conflict_rule": "If RAG advice conflicts with campaign facts, ignore the RAG hint.",
    }


def campaign_summary(campaign: dict) -> dict:
    return {
        "campaign_id": campaign.get("campaign_id"),
        "client_name": campaign.get("client_name"),
        "product_name": campaign.get("product_name"),
        "product_category": campaign.get("product_category"),
        "customer_type": campaign.get("customer_type"),
        "country_or_region": campaign.get("country_or_region"),
        "language": campaign.get("language"),
    }


def signal_reference(decision: dict) -> str:
    difficulty = decision.get("sales_difficulty")
    references = {
        "claim-boundary": "the certainty concern",
        "price-objection": "the price or effort concern",
        "product-detail-lookup": "the product-detail question",
        "human-request": "the request for a human specialist",
        "do-not-call": "the do-not-call request",
        "timing-delay": "the timing concern",
        "autonomy-check": "the timing or pressure concern",
        "provider-comparison": "the comparison concern",
        "stakeholder-review": "the stakeholder review concern",
        "procurement-review": "the procurement review concern",
        "trust-gap": "the trust or verification concern",
        "sale-ready-commitment": "the sale-ready next-step agreement",
        "scheduling-confirmation": "the appointment time",
        "voicemail": "the voicemail signal",
        "repeated-silence": "the repeated silence",
    }
    return references.get(difficulty, "the concern")


def hint_mentions(hints: list[dict] | None, *needles: str) -> bool:
    text = json.dumps(hints or [], ensure_ascii=False).lower()
    return any(needle.lower() in text for needle in needles)


def compose_german_candidate_response(
    decision: dict,
    campaign: dict,
    transcript: str,
    core_pack: dict | None = None,
    advisory_hints: list[dict] | None = None,
) -> str:
    difficulty = decision.get("sales_difficulty")
    next_action = decision.get("next_action")
    handoff_role = "Spezialisten"

    if difficulty == "claim-boundary":
        return (
            "Ich verstehe die Sicherheitsfrage. Ich moechte nichts versprechen, was von Details abhaengt, "
            f"deshalb leite ich das lieber an einen {handoff_role} weiter."
        )

    if difficulty == "price-objection":
        if hint_mentions(advisory_hints, "freedom", "pause", "compare", "objection", "diagnose"):
            return (
                "Das verstehe ich. Damit ich nicht am Punkt vorbeirede: Geht es Ihnen eher um den Preis, die Bedingungen "
                "oder darum, ob sich der Aufwand lohnt?"
            )
        return (
            "Das verstehe ich. Geht es Ihnen vor allem um den Preis, die Bedingungen "
            "oder darum, ob sich der Aufwand lohnt?"
        )

    if difficulty == "product-detail-lookup":
        return (
            "Gute Frage. Ich pruefe lieber zuerst die freigegebenen Produktinformationen, "
            "damit ich bei Details nicht rate."
        )

    if difficulty == "human-request":
        return f"Natuerlich. Ich leite das an einen {handoff_role} weiter, statt automatisch fortzufahren."

    if difficulty == "do-not-call":
        return "Verstanden. Ich markiere den Kontakt so, dass Sie nicht mehr angerufen werden. Auf Wiederhoeren."

    if difficulty == "timing-delay":
        return "Danke, ich verstehe, dass der Zeitpunkt noch nicht fest ist. Ich dokumentiere einen Rueckruf statt zu draengen."

    if difficulty == "autonomy-check":
        return "Das verstehe ich. Soll ich einen kurzen Rueckruf spaeter notieren oder zuerst klaeren, was Sie noch wissen muessen?"

    if difficulty == "provider-comparison":
        return "Das ist fair. Sollen wir zuerst Preis, Bedingungen oder Passung sachlich vergleichen?"

    if difficulty == "stakeholder-review":
        return "Das verstehe ich. Soll ich eine kurze Zusammenfassung fuer die pruefende Person vorbereiten?"

    if difficulty == "procurement-review":
        return "Verstanden. Welche schriftliche Information waere fuer die Pruefung am hilfreichsten?"

    if difficulty == "trust-gap":
        return "Faire Frage. Soll ich zuerst erklaeren, wie Sie das Unternehmen oder den naechsten Schritt verifizieren koennen?"

    if difficulty == "sale-ready-commitment":
        return "Bestaetigt. Ich markiere das als sale-ready fuer den naechsten Schritt, ohne Zahlung in diesem Anruf."

    if difficulty == "scheduling-confirmation":
        return "Bestaetigt. Ich notiere den Rueckruftermin fuer den Spezialisten. Auf Wiederhoeren."

    if difficulty == "voicemail":
        return "Ich habe die Mailbox erreicht und dokumentiere einen Follow-up nach den Kampagnenregeln."

    if difficulty == "repeated-silence":
        return "Ich beende den Anruf fuer jetzt. Auf Wiederhoeren."

    if next_action == "ask-follow-up":
        return compose_german_unknown_follow_up(transcript)

    return decision["agent_response"]


def compose_german_unknown_follow_up(transcript: str) -> str:
    lowered = transcript.lower()
    if any(phrase in lowered for phrase in ["make sense", "fit", "apartment", "situation", "for me"]):
        return (
            "Danke. Damit wir die Passung schnell klaeren: Geht es eher darum, ob das fuer Ihre Situation passt, "
            "um den Preis oder um den Zeitpunkt?"
        )
    if any(phrase in lowered for phrase in ["why", "take this call", "call today", "this call"]):
        return (
            "Faire Frage. Ich halte den Anruf kurz: Soll ich zuerst den konkreten Grund erklaeren, "
            "warum ich Sie kontaktiere?"
        )
    return "Danke. Damit es hilfreich bleibt: Geht es eher um Preis, Passung, Zeitpunkt oder genaue Details?"


def compose_unknown_follow_up(transcript: str) -> str:
    lowered = transcript.lower()
    if any(phrase in lowered for phrase in ["make sense", "fit", "apartment", "situation", "for me"]):
        return (
            "Thanks. To check fit without wasting time, is your main concern whether this is relevant "
            "for your situation, the price, or the timing?"
        )
    if any(phrase in lowered for phrase in ["why", "take this call", "call today", "this call"]):
        return (
            "Fair question. I can keep this call short: would it help if I first explain the concrete "
            "reason for reaching out?"
        )
    return "Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?"


def is_send_info_request(transcript: str) -> bool:
    lowered = transcript.lower()
    return "send" in lowered and any(token in lowered for token in ["info", "information", "details", "summary"])


def is_authority_request(transcript: str) -> bool:
    lowered = transcript.lower()
    return any(token in lowered for token in ["boss", "manager", "partner", "decision maker", "deciding"])


def is_trust_request(transcript: str) -> bool:
    lowered = transcript.lower()
    return "trust" in lowered or any(phrase in lowered for phrase in ["do not know your company", "don't know your company"])


def compose_candidate_response(
    decision: dict,
    campaign: dict,
    transcript: str,
    core_pack: dict | None = None,
    advisory_hints: list[dict] | None = None,
) -> str:
    if normalize_response_language(campaign.get("language")) == "de":
        return compose_german_candidate_response(
            decision,
            campaign,
            transcript,
            core_pack=core_pack,
            advisory_hints=advisory_hints,
        )

    difficulty = decision.get("sales_difficulty")
    next_action = decision.get("next_action")
    handoff_role = campaign.get("human_handoff_role") or "specialist"

    if difficulty == "claim-boundary":
        return (
            f"I hear {signal_reference(decision)}. I do not want to make a claim that depends on details we have "
            f"not checked, so the safest next step is to route this to a {handoff_role}."
        )

    if difficulty == "price-objection":
        if hint_mentions(advisory_hints, "freedom", "pause", "compare", "objection"):
            return (
                "That makes sense. Is your bigger concern the monthly price, the contract terms, "
                "or whether reviewing options is worth your time?"
            )
        return (
            "That makes sense. Is your bigger concern the monthly price, the contract terms, "
            "or whether reviewing options is worth your time?"
        )

    if difficulty == "product-detail-lookup":
        return (
            "Good question. I want to check the approved product information before answering, "
            "so I do not guess on plan details."
        )

    if difficulty == "human-request":
        return f"Of course. I will route this to a {handoff_role} instead of continuing automatically."

    if difficulty == "do-not-call":
        return "Understood. I will mark this contact so you are not called again. Goodbye."

    if difficulty == "timing-delay":
        return "Thanks, I understand the timing is not firm. I will log a follow-up instead of forcing an appointment now."

    if difficulty == "autonomy-check":
        return "That makes sense. Would a brief callback later help, or should we first clarify what you need before any next step?"

    if difficulty == "provider-comparison":
        return "That is fair. Should we compare price, terms, or fit first without pressure?"

    if difficulty == "stakeholder-review":
        return "That makes sense. Should I send a short summary you can share, or is there one concern I should address first?"

    if difficulty == "procurement-review":
        return "Understood. What written information would help procurement review this without asking you for anything firm today?"

    if difficulty == "trust-gap":
        return "Fair question. Should I first give you a verification path before we discuss any next step?"

    if difficulty == "sale-ready-commitment":
        return "Confirmed. I will mark this as sale-ready for the next step, with no payment handled on this call."

    if difficulty == "scheduling-confirmation":
        return "Confirmed. I will record that callback time for the specialist. Goodbye."

    if difficulty == "voicemail":
        return "I reached voicemail, so I will log this for follow-up according to the campaign rules."

    if difficulty == "repeated-silence":
        return "I will end the call for now. Goodbye."

    if next_action == "ask-follow-up":
        if is_send_info_request(transcript) and hint_mentions(advisory_hints, "send", "information", "qualify", "relevant"):
            return (
                "I can send information. To make it relevant, should I send details about fit, pricing, "
                "or how a specialist would review this with you?"
            )
        if is_authority_request(transcript) and hint_mentions(advisory_hints, "objection", "decision", "constraint", "commitment"):
            return (
                "That makes sense. Should I send a short summary you can share with your boss, "
                "or is there one concern I should address first?"
            )
        if is_trust_request(transcript) and hint_mentions(advisory_hints, "objection", "trust", "proof", "evidence"):
            return (
                "Fair. Trust matters on a cold call. To make this useful, should I send company context, "
                "security details, or a specialist review path first?"
            )
        return compose_unknown_follow_up(transcript)

    return decision["agent_response"]


def find_forbidden_claim_matches(text: str, forbidden_claims: list[str]) -> list[str]:
    lowered = text.lower()
    matches = []
    for claim in forbidden_claims:
        if claim.lower() in lowered:
            matches.append(claim)
    return matches


def validate_candidate_response(candidate_response: str, guardrails: dict) -> dict:
    matches = find_forbidden_claim_matches(candidate_response, guardrails["forbidden_claims"])
    passed = len(matches) == 0
    return {
        "validator": "RESP-001 substring forbidden-claim check",
        "checked_text_source": "candidate_response",
        "passed": passed,
        "forbidden_claim_matches": matches,
        "required_repair": not passed,
        "fallback_used": not passed,
        "notes": (
            "Candidate passed local guardrail validation."
            if passed
            else "Candidate failed local guardrail validation and was replaced by the policy response."
        ),
    }


def disabled_retrieval_packet() -> dict:
    return {
        "enabled": False,
        "status": "disabled",
        "blocked_reason": "retrieval_not_enabled",
        "retrieval_decision": "disabled",
        "retrieval_position": "not_run",
        "retrieval_used_in_runtime": False,
        "influenced_response": False,
        "retrieved_item_ids": [],
        "citation_trace": [],
        "advisory_hints": [],
        "rejected_items": [],
        "relevance_gate": {"min_score": DEFAULT_RETRIEVAL_MIN_SCORE},
        "campaign_fact_grounding": {"campaign_facts_override_rag": True},
        "used_hint_count": 0,
        "max_results": 0,
        "registry_path": "",
        "context_flags": [],
        "latency": {
            "target_ms": DEFAULT_RETRIEVAL_TARGET_MS,
            "acceptable_ms": DEFAULT_RETRIEVAL_ACCEPTABLE_MS,
            "elapsed_ms": 0,
        },
    }


def transcript_context_flags(transcript: str) -> list[str]:
    lowered = transcript.lower()
    flags: list[str] = []
    if any(phrase in lowered for phrase in ("do not call", "don't call", "stop calling", "nicht mehr an", "rufen sie mich nicht")):
        flags.extend(["do_not_call", "customer_refusal"])
    if any(phrase in lowered for phrase in ("human", "person", "manager", "menschen", "mensch", "mitarbeiter")):
        flags.append("human_escalation")
    return flags


def retrieval_context_flags(decision: dict, transcript: str) -> list[str]:
    flags = transcript_context_flags(transcript)
    difficulty = str(decision.get("sales_difficulty", ""))
    next_action = str(decision.get("next_action", ""))
    call_control = str(decision.get("call_control", ""))
    if difficulty == "do-not-call":
        flags.extend(["do_not_call", "customer_refusal"])
    if difficulty == "human-request" or next_action in {"transfer-or-escalate", "escalate"}:
        flags.append("human_escalation")
    if difficulty in {"voicemail", "repeated-silence", "scheduling-confirmation", "sale-ready-commitment"} or call_control in {
        "hang-up",
        "end-call",
        "close-and-log-sale-ready",
    }:
        flags.append("protected_script")
    return unique_preserving_order(flags)


def retrieval_query(decision: dict, transcript: str, candidate_response: str) -> str:
    parts = [
        transcript,
        str(decision.get("sales_difficulty", "")),
        str(decision.get("selected_strategy", "")),
        str(decision.get("next_action", "")),
        candidate_response,
        "low pressure customer freedom no pause compare no next step",
    ]
    return " ".join(part for part in parts if part)


def direct_answer_difficulty_from_text(transcript: str, final_response: str) -> dict:
    lowered = f"{transcript} {final_response}".lower()
    if any(phrase in lowered for phrase in ["stop calling", "do not call", "don't call", "take me off", "not called again"]):
        return {
            "sales_difficulty": "do-not-call",
            "interest_state": "do-not-call",
            "selected_strategy": "rapport",
            "next_action": "suppress-contact",
        }
    if any(phrase in lowered for phrase in ["account issue", "route me to support", "support, not a sales conversation", "account help"]):
        return {
            "sales_difficulty": "human-request",
            "interest_state": "needs-human",
            "selected_strategy": "rapport",
            "next_action": "escalate",
        }
    if any(phrase in lowered for phrase in ["busy", "not a good time", "not push while you are busy"]):
        return {
            "sales_difficulty": "timing-delay",
            "interest_state": "not-interested",
            "selected_strategy": "rapport",
            "next_action": "close-politely",
        }
    if any(phrase in lowered for phrase in ["skeptical", "vague software promises", "cannot promise", "proof in writing"]):
        return {
            "sales_difficulty": "trust-gap",
            "interest_state": "maybe-interested",
            "selected_strategy": "rapport",
            "next_action": "continue",
        }
    if any(phrase in lowered for phrase in ["already have a crm", "replace a crm", "alongside our crm"]):
        return {
            "sales_difficulty": "provider-comparison",
            "interest_state": "maybe-interested",
            "selected_strategy": "evidence-or-benefit",
            "next_action": "continue",
        }
    if any(phrase in lowered for phrase in ["manager version", "manager summary", "tell my manager"]):
        return {
            "sales_difficulty": "stakeholder-review",
            "interest_state": "maybe-interested",
            "selected_strategy": "evidence-or-benefit",
            "next_action": "continue",
        }
    if any(phrase in lowered for phrase in ["what is this actually about", "do not know routesignal", "not a full crm replacement"]):
        return {
            "sales_difficulty": "product-fit-question",
            "interest_state": "maybe-interested",
            "selected_strategy": "evidence-or-benefit",
            "next_action": "continue",
        }
    if any(phrase in lowered for phrase in ["what is it going to cost", "what would it cost", "pricing is", "growth is $59", "starter at $29"]):
        return {
            "sales_difficulty": "price-objection",
            "interest_state": "maybe-interested",
            "selected_strategy": "evidence-or-benefit",
            "next_action": "continue",
        }
    return {
        "sales_difficulty": "general-product-question",
        "interest_state": "maybe-interested",
        "selected_strategy": "evidence-or-benefit",
        "next_action": "continue",
    }


def align_decision_snapshot_for_response(decision: dict, transcript: str, final_response: str, *, enabled: bool = False) -> dict:
    aligned = dict(decision)
    aligned["decision_trace_alignment"] = {
        "enabled": enabled,
        "changed": False,
        "reason": "alignment disabled",
    }
    if not enabled:
        return aligned

    has_spoken_question = "?" in final_response
    if aligned.get("next_action") == "ask-follow-up" and not has_spoken_question:
        update = direct_answer_difficulty_from_text(transcript, final_response)
        aligned.update(update)
        aligned["call_control"] = call_control_for_next_action(aligned.get("next_action"), aligned.get("interest_state"))
        aligned["decision_trace_alignment"] = {
            "enabled": True,
            "changed": True,
            "reason": "direct answer spoken, so trace uses direct-answer-compatible next_action",
        }
        return aligned

    if aligned.get("sales_difficulty") == "unknown-runtime-signal":
        update = direct_answer_difficulty_from_text(transcript, final_response)
        aligned.update({key: value for key, value in update.items() if key != "next_action"})
        aligned["call_control"] = call_control_for_next_action(aligned.get("next_action"), aligned.get("interest_state"))
        aligned["decision_trace_alignment"] = {
            "enabled": True,
            "changed": True,
            "reason": "unknown runtime signal mapped from transcript and response wording",
        }
        return aligned

    aligned["decision_trace_alignment"] = {
        "enabled": True,
        "changed": False,
        "reason": "decision snapshot already matched response shape",
    }
    return aligned


def summarize_retrieval_items(items: list[dict]) -> list[dict]:
    hints = []
    for item in items:
        hints.append(
            {
                "item_id": item["knowledge_id"],
                "lane": item["lane"],
                "hint": item.get("project_rule", ""),
                "guardrail": item.get("guardrail_notes", ""),
                "match_score": item.get("match_score", 0),
                "voice_delivery_advisory_only": item.get("voice_delivery_advisory_only", False),
            }
        )
    return hints


def build_retrieval_packet(
    *,
    enabled: bool,
    registry_path: Path | None,
    max_results: int,
    min_score: int,
    target_ms: int,
    acceptable_ms: int,
    decision: dict,
    transcript: str,
    query_text: str,
    campaign_fact_grounding: dict,
) -> dict:
    if not enabled:
        return disabled_retrieval_packet()
    if registry_path is None:
        packet = disabled_retrieval_packet()
        packet.update({"enabled": True, "status": "blocked", "blocked_reason": "missing_registry_path"})
        return packet

    retrieval_start = time.perf_counter()
    flags = retrieval_context_flags(decision, transcript)
    case = {
        "case_id": "guarded-response-runtime",
        "query": retrieval_query(decision, transcript, query_text),
        "lane_filter": "any",
        "context_flags": flags,
        "min_score": min_score,
        "allowed_lanes": ["response_wording", "ethical_persuasion", "voice_delivery"],
    }
    registry_payload = load_retrieval_json(registry_path)
    registry_items = validate_registry_payload(registry_payload)
    result = retrieve_for_case(case, registry_items, max_results)
    elapsed_ms = int((time.perf_counter() - retrieval_start) * 1000)
    if elapsed_ms > acceptable_ms and result["retrieval_decision"] != "blocked":
        result = {**result, "retrieval_decision": "latency_fallback", "retrieved_items": []}
    retrieved_items = result["retrieved_items"]
    retrieved_item_ids = [item["knowledge_id"] for item in retrieved_items]
    citation_trace = [
        trace
        for item in retrieved_items
        for trace in item.get("citation_trace", [])
    ]

    if result["retrieval_decision"] == "blocked":
        status = "blocked"
    elif result["retrieval_decision"] == "latency_fallback":
        status = "latency_fallback"
    elif not retrieved_items:
        status = "no_match"
    else:
        status = "retrieved"

    return {
        "enabled": True,
        "status": status,
        "blocked_reason": result.get("block_reason", ""),
        "retrieval_decision": result["retrieval_decision"],
        "retrieval_position": "before_candidate_composition",
        "retrieval_used_in_runtime": False,
        "influenced_response": False,
        "retrieved_item_ids": retrieved_item_ids if status != "blocked" else [],
        "citation_trace": citation_trace if status != "blocked" else [],
        "advisory_hints": summarize_retrieval_items(retrieved_items) if status == "retrieved" else [],
        "rejected_items": result.get("rejected_items", []),
        "relevance_gate": result.get("relevance_gate", {"min_score": min_score}),
        "campaign_fact_grounding": campaign_fact_grounding,
        "used_hint_count": 0,
        "max_results": max_results,
        "registry_path": str(registry_path),
        "context_flags": flags,
        "latency": {"target_ms": target_ms, "acceptable_ms": acceptable_ms, "elapsed_ms": elapsed_ms},
    }


def finalize_retrieval_packet(
    retrieval: dict,
    validation: dict,
    candidate_response: str,
    policy_response: str,
    baseline_candidate_response: str,
) -> dict:
    finalized = dict(retrieval)
    used = (
        finalized.get("enabled") is True
        and finalized.get("status") == "retrieved"
        and validation["fallback_used"] is False
        and bool(finalized.get("advisory_hints"))
        and candidate_response != baseline_candidate_response
    )
    finalized["retrieval_used_in_runtime"] = used
    finalized["influenced_response"] = used
    finalized["used_hint_count"] = len(finalized.get("advisory_hints", [])) if used else 0
    finalized["influence_basis"] = "candidate_diff_from_no_retrieval_baseline"
    if used:
        finalized["status"] = "influenced"
    elif finalized.get("status") == "retrieved":
        finalized["status"] = "retrieved_not_used"
    return finalized


def build_guarded_response_packet(
    campaign: dict,
    stage: str,
    input_type: str,
    transcript: str,
    silence_count: int,
    candidate_response_override: str | None = None,
    retrieval_enabled: bool = False,
    retrieval_registry_path: Path | None = None,
    retrieval_max_results: int = 3,
    retrieval_min_score: int = DEFAULT_RETRIEVAL_MIN_SCORE,
    retrieval_target_latency_ms: int = DEFAULT_RETRIEVAL_TARGET_MS,
    retrieval_acceptable_latency_ms: int = DEFAULT_RETRIEVAL_ACCEPTABLE_MS,
    composer_hooks_enabled: bool = False,
    align_decision_trace: bool = False,
) -> dict:
    case = build_turn_case(campaign["campaign_id"], stage, transcript, input_type, silence_count)
    decision = run_turn_decision(case, campaign)
    return apply_guarded_response_to_decision(
        campaign=campaign,
        stage=stage,
        input_type=input_type,
        transcript=transcript,
        silence_count=silence_count,
        decision=decision,
        candidate_response_override=candidate_response_override,
        retrieval_enabled=retrieval_enabled,
        retrieval_registry_path=retrieval_registry_path,
        retrieval_max_results=retrieval_max_results,
        retrieval_min_score=retrieval_min_score,
        retrieval_target_latency_ms=retrieval_target_latency_ms,
        retrieval_acceptable_latency_ms=retrieval_acceptable_latency_ms,
        composer_hooks_enabled=composer_hooks_enabled,
        align_decision_trace=align_decision_trace,
    )


def apply_guarded_response_to_decision(
    campaign: dict,
    stage: str,
    input_type: str,
    transcript: str,
    silence_count: int,
    decision: dict,
    candidate_response_override: str | None = None,
    retrieval_enabled: bool = False,
    retrieval_registry_path: Path | None = None,
    retrieval_max_results: int = 3,
    retrieval_min_score: int = DEFAULT_RETRIEVAL_MIN_SCORE,
    retrieval_target_latency_ms: int = DEFAULT_RETRIEVAL_TARGET_MS,
    retrieval_acceptable_latency_ms: int = DEFAULT_RETRIEVAL_ACCEPTABLE_MS,
    composer_hooks_enabled: bool = False,
    align_decision_trace: bool = False,
) -> dict:
    policy_response = decision["agent_response"]
    guardrails = build_guardrails(campaign)

    generation_start = time.perf_counter()
    core_pack = build_core_sales_delivery_pack()
    campaign_fact_grounding = build_campaign_fact_grounding(campaign)
    retrieval = build_retrieval_packet(
        enabled=retrieval_enabled,
        registry_path=retrieval_registry_path,
        max_results=retrieval_max_results,
        min_score=retrieval_min_score,
        target_ms=retrieval_target_latency_ms,
        acceptable_ms=retrieval_acceptable_latency_ms,
        decision=decision,
        transcript=transcript,
        query_text=policy_response,
        campaign_fact_grounding=campaign_fact_grounding,
    )
    baseline_candidate_response = compose_candidate_response(
        decision,
        campaign,
        transcript,
        core_pack=core_pack,
        advisory_hints=[],
    )
    candidate_response = candidate_response_override or compose_candidate_response(
        decision,
        campaign,
        transcript,
        core_pack=core_pack,
        advisory_hints=retrieval.get("advisory_hints", []),
    )
    if candidate_response_override:
        composer_hooks = {
            "enabled": composer_hooks_enabled,
            "status": "blocked" if composer_hooks_enabled else "disabled",
            "applied": False,
            "hook_id": "",
            "hook_name": "",
            "hook_basis": [],
            "blocked_reason": "candidate_response_override",
            "protected_context_preserved": False,
            "no_evaluation_labels_used": True,
            "allowed_runtime_surface": "candidate_response_wording_only",
            "original_candidate_response": candidate_response,
            "final_candidate_response": candidate_response,
        }
    else:
        candidate_response, composer_hooks = apply_runtime_composer_hooks(
            candidate_response,
            enabled=composer_hooks_enabled,
            decision=decision,
            transcript=transcript,
            retrieval=retrieval,
        )
    validation = validate_candidate_response(candidate_response, guardrails)
    final_response = policy_response if validation["fallback_used"] else candidate_response
    decision_snapshot = align_decision_snapshot_for_response(
        decision,
        transcript,
        final_response,
        enabled=align_decision_trace,
    )
    retrieval = finalize_retrieval_packet(
        retrieval,
        validation,
        candidate_response,
        policy_response,
        baseline_candidate_response,
    )
    generation_latency_ms = int((time.perf_counter() - generation_start) * 1000)

    return {
        "response_generation_id": RESPONSE_GENERATION_ID,
        "provider": PROVIDER,
        "llm_used": False,
        "requires_api_key": False,
        "api_calls_made": False,
        "generation_mode": "local deterministic composer with guardrail validation",
        "campaign": campaign_summary(campaign),
        "stage": stage,
        "input_type": input_type,
        "transcript": transcript,
        "policy_response": policy_response,
        "candidate_response": candidate_response,
        "final_response": final_response,
        "validation": validation,
        "retrieval": retrieval,
        "composer_hooks": composer_hooks,
        "core_pack": {
            "core_pack_id": core_pack["core_pack_id"],
            "campaign_facts_override_rag": core_pack["campaign_facts_override_rag"],
            "ethical_persuasion_allowed": core_pack["persuasion_boundary"]["ethical_persuasion_allowed"],
            "hidden_state_certainty_allowed": core_pack["emotion_boundary"]["hidden_state_certainty_allowed"],
        },
        "guardrails": guardrails,
        "decision_snapshot": {
            "response_mode": decision_snapshot.get("response_mode"),
            "campaign_language": decision_snapshot.get("campaign_language"),
            "response_language": decision_snapshot.get("response_language"),
            "detected_emotion": decision_snapshot.get("detected_emotion"),
            "sales_difficulty": decision_snapshot.get("sales_difficulty"),
            "interest_state": decision_snapshot.get("interest_state"),
            "selected_strategy": decision_snapshot.get("selected_strategy"),
            "next_action": decision_snapshot.get("next_action"),
            "call_control": decision_snapshot.get("call_control"),
            "background_modules": decision_snapshot.get("background_modules", []),
            "first_response_latency_budget_ms": decision_snapshot.get("first_response_latency_budget_ms"),
            "first_response_latency_ms": decision_snapshot.get("first_response_latency_ms"),
            "decision_trace_alignment": decision_snapshot.get("decision_trace_alignment"),
        },
        "response_constraints": {
            "changes_allowed": "wording only; state, strategy, next_action, and call_control remain policy-owned",
            "max_sentences": 2,
            "must_not_invent_product_claims": True,
            "fallback_rule": "If validation fails, speak the policy_response instead of the candidate_response.",
            "retrieval_rule": "Retrieval is opt-in, advisory-only, and cannot alter protected text or override guardrail fallback.",
            "composer_hook_rule": "Composer hooks are explicit opt-in candidate wording hooks and remain off by default.",
        },
        "latency": {
            "generation_latency_ms": generation_latency_ms,
            "source_decision_latency_ms": decision.get("first_response_latency_ms"),
            "target": "keep generation fast enough for the live response path",
        },
    }


def render_report(packet: dict) -> str:
    validation = packet["validation"]
    decision = packet["decision_snapshot"]
    retrieval = packet["retrieval"]
    lines = [
        "# RESP-001 Guarded Response Generation Report",
        "",
        "This report was generated by `scripts/generate_guarded_response.py`.",
        "",
        "No LLM/API call was made. The provider is a local deterministic composer used to prove the response contract before any external model is added.",
        "",
        "## Result",
        "",
        f"- Provider: `{packet['provider']}`",
        f"- LLM used: `{packet['llm_used']}`",
        f"- Requires API key: `{packet['requires_api_key']}`",
        f"- Campaign: `{packet['campaign']['campaign_id']}`",
        f"- Sales difficulty: `{decision['sales_difficulty']}`",
        f"- Strategy: `{decision['selected_strategy']}`",
        f"- Next action: `{decision['next_action']}`",
        f"- Call control: `{decision['call_control']}`",
        f"- Validation passed: `{validation['passed']}`",
        f"- Fallback used: `{validation['fallback_used']}`",
        f"- Retrieval status: `{retrieval['status']}`",
        f"- Retrieval used in runtime: `{retrieval['retrieval_used_in_runtime']}`",
        f"- Composer hooks enabled: `{packet['composer_hooks']['enabled']}`",
        f"- Composer hook applied: `{packet['composer_hooks']['applied']}`",
        "",
        "## Responses",
        "",
        f"- Policy response: {packet['policy_response']}",
        f"- Candidate response: {packet['candidate_response']}",
        f"- Final response: {packet['final_response']}",
        "",
        "## Guardrail Validation",
        "",
        f"- Forbidden-claim matches: `{', '.join(validation['forbidden_claim_matches']) or 'none'}`",
        f"- Notes: {validation['notes']}",
        f"- Retrieved item IDs: `{', '.join(retrieval['retrieved_item_ids']) or 'none'}`",
        f"- Retrieval block reason: `{retrieval['blocked_reason'] or 'none'}`",
        "",
        "## Fallback Rule",
        "",
        "If a candidate response contains a forbidden claim, RESP-001 does not repair it creatively in the live path. It falls back to the policy response selected by the deterministic realtime core.",
    ]
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a guarded response from a realtime sales-agent decision.")
    parser.add_argument("--campaign", required=True, help="Campaign ID to use.")
    parser.add_argument("--stage", required=True, help="Current call stage.")
    parser.add_argument("--transcript", default="", help="Customer transcript for this turn.")
    parser.add_argument(
        "--input-type",
        default="speech-final",
        choices=["speech-final", "voicemail-detected", "silence-timeout"],
        help="Runtime input type.",
    )
    parser.add_argument("--silence-count", type=int, default=0, help="Silence retry count for silence-timeout input.")
    parser.add_argument("--cases", default=str(DEFAULT_CASES_PATH), help="Campaign wrapper case file to load.")
    parser.add_argument("--candidate-response", help="Optional candidate response override for guardrail testing.")
    parser.add_argument("--retrieval-enabled", action="store_true", help="Enable local guarded retrieval for this run.")
    parser.add_argument(
        "--composer-hooks-enabled",
        action="store_true",
        help="Enable explicit opt-in runtime composer hooks after guarded retrieval creates advisory hints.",
    )
    parser.add_argument(
        "--retrieval-registry",
        default=str(DEFAULT_RETRIEVAL_REGISTRY),
        help="RAG-017 runtime knowledge registry JSON path.",
    )
    parser.add_argument("--retrieval-max-results", type=int, default=3, help="Maximum advisory retrieval items.")
    parser.add_argument("--retrieval-min-score", type=int, default=DEFAULT_RETRIEVAL_MIN_SCORE, help="Minimum deterministic retrieval match score.")
    parser.add_argument(
        "--retrieval-target-latency-ms",
        type=int,
        default=DEFAULT_RETRIEVAL_TARGET_MS,
        help="Target live retrieval latency budget.",
    )
    parser.add_argument(
        "--retrieval-acceptable-latency-ms",
        type=int,
        default=DEFAULT_RETRIEVAL_ACCEPTABLE_MS,
        help="Acceptable live retrieval latency ceiling before fallback.",
    )
    parser.add_argument("--out", help="Optional path to write JSON output.")
    parser.add_argument("--report-out", help="Optional path to write a Markdown report.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cases_path = resolve_project_path(args.cases)
    campaigns, _cases = load_realtime_cases(cases_path)
    campaign = find_campaign(campaigns, args.campaign)
    retrieval_registry = resolve_project_path(args.retrieval_registry) if args.retrieval_enabled else None

    packet = build_guarded_response_packet(
        campaign=campaign,
        stage=args.stage,
        input_type=args.input_type,
        transcript=args.transcript,
        silence_count=args.silence_count,
        candidate_response_override=args.candidate_response,
        retrieval_enabled=args.retrieval_enabled,
        retrieval_registry_path=retrieval_registry,
        retrieval_max_results=args.retrieval_max_results,
        retrieval_min_score=args.retrieval_min_score,
        retrieval_target_latency_ms=args.retrieval_target_latency_ms,
        retrieval_acceptable_latency_ms=args.retrieval_acceptable_latency_ms,
        composer_hooks_enabled=args.composer_hooks_enabled,
    )

    out_path = resolve_project_path(args.out)
    if out_path is not None:
        write_json(out_path, packet)

    report_path = resolve_project_path(args.report_out)
    if report_path is not None:
        write_text(report_path, render_report(packet))

    print(json.dumps(packet, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
