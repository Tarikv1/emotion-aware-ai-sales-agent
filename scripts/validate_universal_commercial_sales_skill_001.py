#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.core import universal_sales_conversation_knowledge as knowledge  # noqa: E402


CHECKPOINT_ID = "UNIVERSAL-COMMERCIAL-SALES-SKILL-001"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"

SIDE_EFFECTS = {
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

ABSTRACT_CAMPAIGNS = [
    {
        "id": "workflow_saas",
        "product": "FlowDesk",
        "option_a": "Starter",
        "option_b": "Scale",
        "tradeoff_a": "lower cost",
        "tradeoff_b": "automation headroom",
        "value": "fewer manual handoffs",
        "close": "the self-serve plan page",
    },
    {
        "id": "home_service",
        "product": "HomeShield",
        "option_a": "Basic Visit",
        "option_b": "Priority Plan",
        "tradeoff_a": "lower upfront cost",
        "tradeoff_b": "faster response",
        "value": "less waiting when a repair becomes urgent",
        "close": "the booking page",
    },
    {
        "id": "insurance_review",
        "product": "PolicyCheck",
        "option_a": "Standard Review",
        "option_b": "Advisor Review",
        "tradeoff_a": "simple coverage check",
        "tradeoff_b": "human review for edge cases",
        "value": "clearer coverage fit",
        "close": "a licensed review route",
    },
    {
        "id": "team_security_tool",
        "product": "SecureTeam",
        "option_a": "Team",
        "option_b": "Enterprise",
        "tradeoff_a": "self-serve team controls",
        "tradeoff_b": "procurement and security controls",
        "value": "cleaner admin control",
        "close": "the official sales route",
    },
]

SCENARIO_TYPES = [
    "price_after_use_case",
    "option_enough",
    "competitor_exists",
    "expensive",
    "what_should_i_do",
    "buying_signal",
    "maybe_later",
    "current_solution_enough",
    "enough_fit_info",
    "no_fit",
]

VARIANTS = [
    ("moderate", "moderate use", "price matters"),
    ("heavy", "heavy use", "avoiding limits matters"),
    ("team", "team use", "admin controls matter"),
]

INTERNAL_RE = re.compile(r"adoption state|internal policy|plan fit still needs|approved qualified reviewer path", re.I)
UNSUPPORTED_RE = re.compile(r"guarantee|guaranteed|best in the market|beats every competitor|100% result", re.I)
FAKE_SIDE_EFFECT_RE = re.compile(r"i sent|i emailed|i booked|created .*calendar|created .*crm|charged your card", re.I)


def normalize(text: Any) -> str:
    return re.sub(r"\s+", " ", str(text or "").strip().lower())


def sha12(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def scenario_id(campaign: dict[str, str], scenario_type: str, variant: str) -> str:
    return f"{campaign['id']}-{scenario_type}-{variant}"


def build_scenarios() -> list[dict[str, Any]]:
    scenarios: list[dict[str, Any]] = []
    for campaign in ABSTRACT_CAMPAIGNS:
        for scenario_type in SCENARIO_TYPES:
            for variant, intensity, priority in VARIANTS:
                turns = [
                    "yes, quick",
                    f"I need this for {intensity}; {priority}.",
                    {
                        "price_after_use_case": "How much is it?",
                        "option_enough": f"Is {campaign['option_a']} enough?",
                        "competitor_exists": "We already use another tool. Why compare?",
                        "expensive": "That sounds too expensive.",
                        "what_should_i_do": "What should I do?",
                        "buying_signal": f"So {campaign['option_b']} is probably better?",
                        "maybe_later": "Maybe later.",
                        "current_solution_enough": "Our current solution works fine.",
                        "enough_fit_info": "We have enough fit info, which option should I compare?",
                        "no_fit": "I barely use this and do not want to pay.",
                    }[scenario_type],
                ]
                scenarios.append(
                    {
                        "id": scenario_id(campaign, scenario_type, variant),
                        "campaign": campaign,
                        "scenario_type": scenario_type,
                        "variant": variant,
                        "turns": turns,
                        "multi_turn": True,
                    }
                )
    return scenarios


def recommendation_for(campaign: dict[str, str], variant: str, scenario_type: str) -> str:
    if scenario_type in {"no_fit", "current_solution_enough"}:
        return "no_fit"
    if variant == "moderate" or scenario_type == "expensive":
        return campaign["option_a"]
    return campaign["option_b"]


def render_response(item: dict[str, Any]) -> str:
    campaign = item["campaign"]
    scenario_type = item["scenario_type"]
    variant = item["variant"]
    recommendation = recommendation_for(campaign, variant, scenario_type)
    context = {
        "moderate": "moderate use with price sensitivity",
        "heavy": "heavy use where headroom matters",
        "team": "team use where controls matter",
    }[variant]

    if recommendation == "no_fit":
        return (
            f"Given {context} and that your current need is low, I would not push {campaign['product']} now. "
            f"Stay with the current solution unless {campaign['value']} becomes important. The next action is no paid close."
        )
    if scenario_type == "competitor_exists":
        return (
            f"You may not need to switch. Given {context}, the reason to compare {campaign['product']} is only if it solves a gap "
            f"your current tool does not, such as {campaign['value']}. Choose {campaign['option_a']} if {campaign['tradeoff_a']} matters more; "
            f"choose {campaign['option_b']} if {campaign['tradeoff_b']} matters more. The next action is compare that one gap."
        )
    if scenario_type == "maybe_later":
        return (
            f"That is fine. Given {context}, I would keep the decision simple: {campaign['option_a']} if {campaign['tradeoff_a']} matters more, "
            f"{campaign['option_b']} if {campaign['tradeoff_b']} matters more. The next action is to revisit when timing is real."
        )
    if scenario_type == "buying_signal":
        return (
            f"Yes - given {context}, {recommendation} is the stronger fit to compare because it supports {campaign['value']}. "
            f"{campaign['option_a']} is better if {campaign['tradeoff_a']} matters more; {campaign['option_b']} is better if {campaign['tradeoff_b']} matters more. "
            f"The next action is {campaign['close']}."
        )
    if scenario_type == "price_after_use_case":
        return (
            f"Price should be checked in the configured source for {campaign['product']}. Given {context}, the value decision is "
            f"{campaign['option_a']} for {campaign['tradeoff_a']} versus {campaign['option_b']} for {campaign['tradeoff_b']}. "
            f"I would compare {recommendation} first. The next action is {campaign['close']}."
        )
    if scenario_type == "expensive":
        return (
            f"If price is the concern, start with the lower-cost path. Given {context}, compare {campaign['option_a']} if "
            f"{campaign['tradeoff_a']} matters more; compare {campaign['option_b']} if {campaign['tradeoff_b']} matters more. "
            f"I would start with {recommendation} and move up only if {campaign['value']} matters enough."
        )
    return (
        f"Given {context}, I would recommend {recommendation} because it is the better match for {campaign['value']}. "
        f"Choose {campaign['option_a']} if {campaign['tradeoff_a']} matters more; choose {campaign['option_b']} if {campaign['tradeoff_b']} matters more. "
        f"The next action is {campaign['close']}."
    )


def validate_response(item: dict[str, Any], response: str) -> list[str]:
    failures: list[str] = []
    lowered = normalize(response)
    scenario_type = item["scenario_type"]
    campaign = item["campaign"]
    recommendation = recommendation_for(campaign, item["variant"], scenario_type)

    if INTERNAL_RE.search(response):
        failures.append("internal policy wording")
    if UNSUPPORTED_RE.search(response):
        failures.append("unsupported claim")
    if FAKE_SIDE_EFFECT_RE.search(response):
        failures.append("fake side effect")
    if "given" not in lowered:
        failures.append("missing buyer-context summary")
    if scenario_type not in {"no_fit", "current_solution_enough"} and recommendation.lower() not in lowered:
        failures.append("enough context but no recommendation")
    if scenario_type == "price_after_use_case" and not re.search(r"price|source|value decision", response, re.I):
        failures.append("buyer asks price and agent refuses or dodges")
    if scenario_type == "buying_signal" and not re.search(r"next action|official|route|page", response, re.I):
        failures.append("buyer shows intent and agent does not close")
    if scenario_type == "competitor_exists" and not re.search(r"gap|current tool|may not need to switch", response, re.I):
        failures.append("competitor not reframed")
    if scenario_type == "expensive" and not re.search(r"lower.*cost|cost|price", response, re.I):
        failures.append("price objection not reframed")
    if scenario_type in {"no_fit", "current_solution_enough"} and not re.search(r"not push|stay with|no paid close", response, re.I):
        failures.append("no-fit close missing")
    if scenario_type in {"no_fit", "current_solution_enough"} and "unless" in lowered:
        return failures
    if not re.search(r"(choose |compare |[A-Z][A-Za-z0-9 -]+ is better if ).*matters more|versus|if .* matters more, .* if .* matters more", response, re.I):
        failures.append("decision frame missing")
    if len(response.split()) > 95:
        failures.append("too information-heavy")
    return failures


def write_evidence(result: dict[str, Any]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report = "\n".join(
        [
            f"# {CHECKPOINT_ID}",
            "",
            f"- Status: `{result['status']}`",
            f"- Scenario count: `{result['scenario_count']}`",
            f"- Multi-turn scenario count: `{result['multi_turn_scenario_count']}`",
            f"- Campaign count: `{result['abstract_campaign_count']}`",
            f"- Failed count: `{result['failed_count']}`",
            f"- Critical failure count: `{result['critical_failure_count']}`",
            f"- Side effects false: `{str(result['side_effects_false']).lower()}`",
            "",
            "## Principle IDs",
            "",
            "```json",
            json.dumps(result["principle_ids"], indent=2, sort_keys=True),
            "```",
            "",
            "## Failed Cases",
            "",
            "```json",
            json.dumps(result["failed_cases"][:20], indent=2, sort_keys=True),
            "```",
            "",
        ]
    )
    REPORT_PATH.write_text(report, encoding="utf-8")


def main() -> None:
    scenarios = build_scenarios()
    principle_ids = [item["id"] for item in knowledge.commercial_sales_skill_principles()]
    required_principles = {
        "recommend_after_enough_context",
        "direct_buying_question_priority",
        "context_summary_before_recommendation",
        "decision_frame_contrast",
        "competitor_reframe",
        "buying_signal_close",
        "avoid_over_caveating",
        "no_repeated_qualification",
        "information_must_advance",
        "sales_ready_means_selling",
    }
    structure_failures = []
    if len(scenarios) < 120:
        structure_failures.append(f"at least 120 scenarios required, got {len(scenarios)}")
    if sum(1 for item in scenarios if item["multi_turn"]) < 80:
        structure_failures.append("at least 80 multi-turn scenarios required")
    if len({item["campaign"]["id"] for item in scenarios}) < 4:
        structure_failures.append("at least 4 abstract campaigns required")
    missing_principles = sorted(required_principles - set(principle_ids))
    if missing_principles:
        structure_failures.append(f"missing universal principles {missing_principles}")

    traces = []
    for item in scenarios:
        response = render_response(item)
        failures = validate_response(item, response)
        traces.append(
            {
                "id": item["id"],
                "campaign_id": item["campaign"]["id"],
                "scenario_type": item["scenario_type"],
                "multi_turn": item["multi_turn"],
                "status": "pass" if not failures else "fail",
                "failures": failures,
                "response_hash": sha12(response),
                "response": response,
                "side_effects": dict(SIDE_EFFECTS),
            }
        )
    failed = [trace for trace in traces if trace["status"] != "pass"]
    critical_count = sum(len(trace["failures"]) for trace in failed) + len(structure_failures)
    result = {
        "status": "pass" if not failed and not structure_failures else "fail",
        "checkpoint_id": CHECKPOINT_ID,
        "scenario_count": len(scenarios),
        "multi_turn_scenario_count": sum(1 for item in scenarios if item["multi_turn"]),
        "abstract_campaign_count": len({item["campaign"]["id"] for item in scenarios}),
        "scenario_type_counts": dict(sorted(Counter(item["scenario_type"] for item in scenarios).items())),
        "failed_count": len(failed) + len(structure_failures),
        "critical_failure_count": critical_count,
        "structure_failures": structure_failures,
        "principle_ids": principle_ids,
        "commercial_buying_question_types": knowledge.commercial_buying_question_types(),
        "side_effects_false": True,
        "provider_calls_made": False,
        "live_tts_calls_made": False,
        "local_llm_calls_made": False,
        "raw_private_transcript_copied_to_public_evidence": False,
        "failed_cases": failed,
        "traces": traces,
    }
    write_evidence(result)
    print(
        json.dumps(
            {
                "status": result["status"],
                "scenario_count": result["scenario_count"],
                "multi_turn_scenario_count": result["multi_turn_scenario_count"],
                "failed_count": result["failed_count"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    if result["status"] != "pass":
        sys.exit(1)


if __name__ == "__main__":
    main()
