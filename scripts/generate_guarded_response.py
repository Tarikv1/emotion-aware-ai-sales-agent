#!/usr/bin/env python3
import argparse
import json
import time
from pathlib import Path

from realtime_turn_cli import build_turn_case, find_campaign, run_turn_decision
from run_realtime_turn_simulation import load_realtime_cases


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CASES_PATH = ROOT / "research" / "experiments" / "cases" / "prod-005-realtime-latency-call-control.json"
RESPONSE_GENERATION_ID = "RESP-001-local-guarded"
PROVIDER = "local-guarded-composer"

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
        "claim-boundary": "the certainty or guarantee concern",
        "price-objection": "the price or effort concern",
        "product-detail-lookup": "the product-detail question",
        "human-request": "the request for a human specialist",
        "do-not-call": "the do-not-call request",
        "timing-delay": "the timing concern",
        "scheduling-confirmation": "the appointment time",
        "voicemail": "the voicemail signal",
        "repeated-silence": "the repeated silence",
    }
    return references.get(difficulty, "the concern")


def compose_candidate_response(decision: dict, campaign: dict) -> str:
    difficulty = decision.get("sales_difficulty")
    next_action = decision.get("next_action")
    handoff_role = campaign.get("human_handoff_role") or "specialist"

    if difficulty == "claim-boundary":
        return (
            f"I hear {signal_reference(decision)}. I do not want to make a claim that depends on details we have "
            f"not checked, so the safest next step is to route this to a {handoff_role}."
        )

    if difficulty == "price-objection":
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

    if difficulty == "scheduling-confirmation":
        return "Confirmed. I will record that callback time for the specialist. Goodbye."

    if difficulty == "voicemail":
        return "I reached voicemail, so I will log this for follow-up according to the campaign rules."

    if difficulty == "repeated-silence":
        return "I will end the call for now. Goodbye."

    if next_action == "ask-follow-up":
        return "Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?"

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


def build_guarded_response_packet(
    campaign: dict,
    stage: str,
    input_type: str,
    transcript: str,
    silence_count: int,
    candidate_response_override: str | None = None,
) -> dict:
    case = build_turn_case(campaign["campaign_id"], stage, transcript, input_type, silence_count)
    decision = run_turn_decision(case)
    policy_response = decision["agent_response"]
    guardrails = build_guardrails(campaign)

    generation_start = time.perf_counter()
    candidate_response = candidate_response_override or compose_candidate_response(decision, campaign)
    validation = validate_candidate_response(candidate_response, guardrails)
    final_response = policy_response if validation["fallback_used"] else candidate_response
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
        "guardrails": guardrails,
        "decision_snapshot": {
            "response_mode": decision.get("response_mode"),
            "detected_emotion": decision.get("detected_emotion"),
            "sales_difficulty": decision.get("sales_difficulty"),
            "interest_state": decision.get("interest_state"),
            "selected_strategy": decision.get("selected_strategy"),
            "next_action": decision.get("next_action"),
            "call_control": decision.get("call_control"),
            "background_modules": decision.get("background_modules", []),
            "first_response_latency_budget_ms": decision.get("first_response_latency_budget_ms"),
            "first_response_latency_ms": decision.get("first_response_latency_ms"),
        },
        "response_constraints": {
            "changes_allowed": "wording only; state, strategy, next_action, and call_control remain policy-owned",
            "max_sentences": 2,
            "must_not_invent_product_claims": True,
            "fallback_rule": "If validation fails, speak the policy_response instead of the candidate_response.",
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
    parser.add_argument("--out", help="Optional path to write JSON output.")
    parser.add_argument("--report-out", help="Optional path to write a Markdown report.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cases_path = resolve_project_path(args.cases)
    campaigns, _cases = load_realtime_cases(cases_path)
    campaign = find_campaign(campaigns, args.campaign)

    packet = build_guarded_response_packet(
        campaign=campaign,
        stage=args.stage,
        input_type=args.input_type,
        transcript=args.transcript,
        silence_count=args.silence_count,
        candidate_response_override=args.candidate_response,
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
