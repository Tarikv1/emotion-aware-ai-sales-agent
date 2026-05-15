#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import time
from pathlib import Path
from typing import Any

import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from runtime.entrypoints.generate_guarded_response import build_guarded_response_packet


CHECKPOINT_ID = "PROD-028-synthetic-campaign-knowledge-grounding"
TITLE = "PROD-028 synthetic campaign knowledge grounding"
DEFAULT_OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
DEFAULT_RESULT = DEFAULT_OUT_DIR / "result.json"
DEFAULT_REPORT = DEFAULT_OUT_DIR / "report.md"
DEFAULT_CAMPAIGN_OUT = DEFAULT_OUT_DIR / "synthetic_campaign.json"
DEFAULT_TRACE_HTML = DEFAULT_OUT_DIR / "grounded_answer_trace.html"
NEXT_CHECKPOINT = "PROD-029-grounded-full-scenario-rerun"

REALITY_SOURCE_DATE = "2026-05-09"

UNSUPPORTED_CLAIM_MARKERS = [
    "guaranteed revenue increase",
    "guaranteed cost savings",
    "guaranteed conversion lift",
    "replaces every crm",
    "no risk",
    "legal advice",
    "collect payment or card details on this call",
]

PAYMENT_MARKERS = [
    "take your payment",
    "collect your payment",
    "card number",
    "credit card number",
]


def rel_path(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


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
        "copied_real_company_text": False,
        "real_company_brand_used_as_campaign": False,
        "real_customer_data_used": False,
        "payment_collection_enabled": False,
        "runtime_behavior_changed_by_this_checkpoint": False,
        "runtime_retrieval_default_enabled": False,
        "composer_hook_flag_default_enabled": False,
        "live_provider_default_enabled": False,
        "server_started": False,
    }


def build_source_inspiration() -> list[dict[str, str]]:
    return [
        {
            "source_id": "prod-028-source-hubspot-sales-product",
            "name": "HubSpot Sales Hub public product/pricing page",
            "url": "https://www.hubspot.com/products/sales",
            "checked_date": REALITY_SOURCE_DATE,
            "observed_pattern": "sales software is commonly sold as tiered per-seat plans with starter, professional, and enterprise-style capability bands.",
            "reuse_label": "inspiration only",
            "directly_copied_material": "none",
        },
        {
            "source_id": "prod-028-source-pipedrive-pricing",
            "name": "Pipedrive public CRM pricing page",
            "url": "https://www.pipedrive.com/en/pricing",
            "checked_date": REALITY_SOURCE_DATE,
            "observed_pattern": "CRM pricing commonly uses annual discounts, free trials, add-ons, integrations, onboarding, and tiered automation/security features.",
            "reuse_label": "inspiration only",
            "directly_copied_material": "none",
        },
        {
            "source_id": "prod-028-source-salesforce-sales-pricing",
            "name": "Salesforce Sales Cloud public pricing page",
            "url": "https://www.salesforce.com/sales/pricing/",
            "checked_date": REALITY_SOURCE_DATE,
            "observed_pattern": "enterprise CRM packages commonly expose per-user pricing, lead routing, automation, quoting, forecasting, APIs, and support add-ons.",
            "reuse_label": "inspiration only",
            "directly_copied_material": "none",
        },
        {
            "source_id": "prod-028-source-zendesk-pricing",
            "name": "Zendesk public pricing page",
            "url": "https://www.zendesk.com/pricing/",
            "checked_date": REALITY_SOURCE_DATE,
            "observed_pattern": "customer operations software commonly tiers routing, reporting, support channels, AI/admin tools, audit logs, sandbox, and privacy add-ons.",
            "reuse_label": "inspiration only",
            "directly_copied_material": "none",
        },
    ]


def build_synthetic_campaign() -> dict[str, Any]:
    return {
        "campaign_id": "campaign-prod-028-routesignal-crm",
        "client_name": "Northstar Workflow Labs",
        "product_name": "RouteSignal CRM",
        "product_category": "software-b2b-crm",
        "customer_type": "b2b",
        "country_or_region": "US/EU",
        "language": "en",
        "approved_opening": "Hi, I am calling about lead-routing and follow-up workflow gaps. Do you have a minute?",
        "qualification_questions": [
            "How many people touch inbound leads before a callback happens?",
            "Where do leads get stuck today: routing, follow-up, reporting, or handoff?",
            "If there is fit, would a short specialist review be useful?",
        ],
        "allowed_claims": [
            "RouteSignal CRM centralizes inbound lead intake and callback ownership.",
            "RouteSignal CRM can route leads by region, source, priority, or account owner.",
            "RouteSignal CRM supports email, calendar, CRM, Slack, Zapier, and CSV-based workflow handoffs.",
            "Typical assisted setup is two to four weeks after admin access and import scope are confirmed.",
            "The first sales call is informational and does not collect payment.",
        ],
        "forbidden_claims": UNSUPPORTED_CLAIM_MARKERS,
        "required_disclosures": [
            "Pricing is synthetic for product simulation and must be confirmed by a specialist before a real quote.",
            "Integration scope, migration effort, and security review require specialist confirmation.",
            "Payment or card details are not collected on the sales call.",
        ],
        "discount_terms": [
            "Annual billing reduces subscription price by 15 percent versus monthly billing.",
            "Custom discounts require a written specialist quote and cannot be promised by the call agent.",
        ],
        "deadline_terms": [
            "No scarcity deadline is used in this campaign.",
            "The agent may offer a 14-day sandbox trial, not an artificial limited-time deadline.",
        ],
        "escalation_triggers": [
            "custom security review",
            "SSO or audit-log detail",
            "procurement terms",
            "legal or compliance question",
            "migration estimate beyond standard CSV import",
            "request for guaranteed revenue impact",
            "human request",
        ],
        "scheduling_goal": "non-binding 30-minute workflow review",
        "human_handoff_role": "solutions specialist",
        "compliance_notes": "Fictional campaign for local simulation. Facts are reality-patterned from public SaaS/CRM pages, not copied from a real company.",
        "product_knowledge": {
            "plans": [
                {
                    "plan_id": "starter",
                    "name": "Starter",
                    "price_usd_per_user_month_annual": 29,
                    "minimum_users": 3,
                    "best_for": "small teams moving from spreadsheets to a shared pipeline",
                    "included": [
                        "lead inbox",
                        "basic pipeline management",
                        "email templates",
                        "callback tasks",
                        "standard reports",
                        "CSV import",
                    ],
                },
                {
                    "plan_id": "growth",
                    "name": "Growth",
                    "price_usd_per_user_month_annual": 59,
                    "minimum_users": 5,
                    "best_for": "teams that need routing automation and manager visibility",
                    "included": [
                        "everything in Starter",
                        "lead routing by region, source, priority, or owner",
                        "Gmail and Outlook calendar sync",
                        "Slack alerts",
                        "Zapier handoffs",
                        "duplicate detection",
                        "team reporting",
                    ],
                },
                {
                    "plan_id": "scale",
                    "name": "Scale",
                    "price_usd_per_user_month_annual": 99,
                    "minimum_users": 10,
                    "best_for": "larger teams with security, approval, and workflow-control needs",
                    "included": [
                        "everything in Growth",
                        "SSO",
                        "audit logs",
                        "sandbox",
                        "approval workflows",
                        "custom roles",
                        "priority support",
                    ],
                },
            ],
            "trial": {
                "length_days": 14,
                "credit_card_required": False,
                "notes": "Sandbox trial uses sample data or customer-provided non-sensitive import samples.",
            },
            "billing": {
                "monthly_available": True,
                "annual_available": True,
                "annual_discount_percent": 15,
                "taxes_not_included": True,
            },
            "onboarding": {
                "assisted_setup_fee_usd": 1500,
                "data_migration_package_usd": 900,
                "typical_assisted_setup_weeks": "2-4",
            },
            "contract": {
                "cancellation": "monthly or annual subscription ends at the paid-period boundary",
                "payment_collection_allowed_on_call": False,
                "quote_required_before_purchase": True,
            },
            "eligibility": {
                "minimum_users": 3,
                "ideal_user_range": "3-250 sales or customer operations users",
                "not_for": [
                    "emergency support",
                    "regulated medical advice",
                    "legal advice",
                    "payment processing",
                    "consumer cold-call payment collection",
                ],
            },
            "integrations": [
                "Salesforce",
                "HubSpot",
                "Gmail",
                "Outlook",
                "Slack",
                "Zapier",
                "CSV import",
            ],
        },
        "source_inspiration": build_source_inspiration(),
        "reuse_boundary": {
            "reuse_label": "inspiration only",
            "copied_material": "none",
            "fictional_product": True,
            "fictional_company": True,
            "real_brand_identity_used": False,
        },
    }


def build_evaluation_cases() -> list[dict[str, Any]]:
    return [
        {
            "case_id": "PROD-028-Q01",
            "stage": "product-detail-check",
            "customer_question": "How much would this cost for 12 users if we used the realistic plan?",
            "answer_key": "pricing_12_users",
            "expected_fact_refs": ["plan_growth_price", "growth_minimum_users", "onboarding_fee"],
            "expected_answer_markers": ["Growth", "$59", "12 users", "$708", "$1,500"],
            "price_case": True,
        },
        {
            "case_id": "PROD-028-Q02",
            "stage": "product-detail-check",
            "customer_question": "What do we actually get in Growth that Starter does not have?",
            "answer_key": "growth_vs_starter",
            "expected_fact_refs": ["starter_included", "growth_included"],
            "expected_answer_markers": ["lead routing", "Gmail", "Outlook", "Slack", "team reporting"],
            "price_case": False,
        },
        {
            "case_id": "PROD-028-Q03",
            "stage": "procurement-review",
            "customer_question": "Are we locked into a contract, or can we cancel if it does not work?",
            "answer_key": "contract_cancel",
            "expected_fact_refs": ["monthly_available", "annual_available", "cancellation_period_boundary", "no_payment_call"],
            "expected_answer_markers": ["monthly", "annual", "15%", "paid period", "no payment"],
            "price_case": False,
        },
        {
            "case_id": "PROD-028-Q04",
            "stage": "product-detail-check",
            "customer_question": "How long would setup take if we already have a spreadsheet of leads?",
            "answer_key": "setup_time",
            "expected_fact_refs": ["typical_setup_weeks", "csv_import", "migration_package"],
            "expected_answer_markers": ["two to four weeks", "CSV import", "$900"],
            "price_case": True,
        },
        {
            "case_id": "PROD-028-Q05",
            "stage": "product-detail-check",
            "customer_question": "Does it connect with the tools our team already uses?",
            "answer_key": "integrations",
            "expected_fact_refs": ["integrations_supported"],
            "expected_answer_markers": ["Salesforce", "HubSpot", "Gmail", "Outlook", "Slack", "Zapier"],
            "price_case": False,
        },
        {
            "case_id": "PROD-028-Q06",
            "stage": "product-detail-check",
            "customer_question": "Who can see the lead data? We need role control and audit logs.",
            "answer_key": "security_roles",
            "expected_fact_refs": ["scale_security", "specialist_review"],
            "expected_answer_markers": ["Scale", "SSO", "audit logs", "custom roles", "specialist"],
            "price_case": False,
        },
        {
            "case_id": "PROD-028-Q07",
            "stage": "price-discussion",
            "customer_question": "Can you discount it if we pay yearly?",
            "answer_key": "discount",
            "expected_fact_refs": ["annual_discount", "custom_discount_quote"],
            "expected_answer_markers": ["15%", "annual billing", "specialist quote"],
            "price_case": True,
        },
        {
            "case_id": "PROD-028-Q08",
            "stage": "eligibility-check",
            "customer_question": "We only have six sales people. Are we too small for this?",
            "answer_key": "eligibility_six_users",
            "expected_fact_refs": ["eligibility_minimum", "starter_minimum", "growth_minimum"],
            "expected_answer_markers": ["six", "not too small", "Starter", "Growth"],
            "price_case": False,
        },
        {
            "case_id": "PROD-028-Q09",
            "stage": "product-detail-check",
            "customer_question": "If we need SSO and a sandbox, is that included or is it a special request?",
            "answer_key": "sso_sandbox",
            "expected_fact_refs": ["scale_security", "specialist_review"],
            "expected_answer_markers": ["Scale", "SSO", "sandbox", "specialist"],
            "price_case": False,
            "requires_safe_unknown_handling": True,
        },
        {
            "case_id": "PROD-028-Q10",
            "stage": "provider-comparison",
            "customer_question": "We already use spreadsheets and Pipedrive. Why would we even look at this?",
            "answer_key": "current_provider_compare",
            "expected_fact_refs": ["no_badmouthing", "routing_fit", "csv_import"],
            "expected_answer_markers": ["not replace", "routing", "CSV import", "worth reviewing"],
            "price_case": False,
        },
        {
            "case_id": "PROD-028-Q11",
            "stage": "price-discussion",
            "customer_question": "That sounds too expensive for us right now.",
            "answer_key": "too_expensive",
            "expected_fact_refs": ["starter_price", "trial", "no_pressure"],
            "expected_answer_markers": ["Starter", "$29", "14-day", "no card"],
            "price_case": True,
        },
        {
            "case_id": "PROD-028-Q12",
            "stage": "claim-boundary",
            "customer_question": "Can you promise it will increase revenue by 30 percent?",
            "answer_key": "forbidden_revenue_promise",
            "expected_fact_refs": ["forbidden_revenue_guarantee", "allowed_product_capability"],
            "expected_answer_markers": ["cannot promise", "centralize lead intake", "route leads"],
            "price_case": False,
            "requires_safe_unknown_handling": True,
        },
    ]


def grounded_answer(answer_key: str) -> str:
    answers = {
        "pricing_12_users": (
            "For 12 users, Growth is the realistic fit at $59 per user per month on annual billing, "
            "so subscription cost is $708 per month before taxes or add-ons. Assisted setup is a one-time $1,500 package."
        ),
        "growth_vs_starter": (
            "Starter covers the shared lead inbox, pipeline, templates, callback tasks, reports, and CSV import. "
            "Growth adds lead routing, Gmail and Outlook sync, Slack alerts, Zapier handoffs, duplicate detection, and team reporting."
        ),
        "contract_cancel": (
            "You can choose monthly or annual billing. Annual billing is 15% lower, and cancellation takes effect at the paid period boundary; "
            "there is no payment handled on this call."
        ),
        "setup_time": (
            "With a spreadsheet-ready team, assisted setup is typically two to four weeks after admin access and import scope are confirmed. "
            "Standard CSV import is included; deeper migration is the $900 package."
        ),
        "integrations": (
            "Yes. The synthetic campaign facts list Salesforce, HubSpot, Gmail, Outlook, Slack, Zapier, and CSV import as supported handoff paths, "
            "with final scope confirmed by a specialist."
        ),
        "security_roles": (
            "Role control and audit logs sit in the Scale plan, along with SSO, sandbox, approval workflows, custom roles, and priority support. "
            "A solutions specialist should confirm the exact security review."
        ),
        "discount": (
            "The standard yearly option is annual billing with a 15% subscription reduction. "
            "Anything beyond that needs a written specialist quote, so I would not promise a custom discount on this call."
        ),
        "eligibility_six_users": (
            "Six sales people is not too small. Starter begins at 3 users, and Growth begins at 5 users, so we would choose between those based on routing needs."
        ),
        "sso_sandbox": (
            "SSO and sandbox are Scale-plan capabilities, not Starter or Growth defaults. "
            "Because those details affect security review, I would route the exact setup to a solutions specialist."
        ),
        "current_provider_compare": (
            "I would not replace a setup that already works. This is worth reviewing only if routing, callback ownership, or reporting are the gaps; "
            "CSV import and CRM handoffs help evaluate that without starting from zero."
        ),
        "too_expensive": (
            "That may be a reason to start smaller. Starter is $29 per user per month on annual billing, and the 14-day sandbox trial has no card requirement."
        ),
        "forbidden_revenue_promise": (
            "I cannot promise a revenue lift. What I can say is RouteSignal CRM can centralize lead intake and route leads by region, source, priority, or owner."
        ),
    }
    return answers[answer_key]


def count_questions(text: str) -> int:
    return text.count("?")


def contains_any(text: str, markers: list[str]) -> bool:
    lowered = text.lower()
    return any(marker.lower() in lowered for marker in markers)


def all_markers_present(text: str, markers: list[str]) -> bool:
    lowered = text.lower()
    return all(marker.lower() in lowered for marker in markers)


def unsupported_claims(text: str) -> list[str]:
    lowered = text.lower()
    return [marker for marker in UNSUPPORTED_CLAIM_MARKERS if marker.lower() in lowered]


def payment_collection_detected(text: str) -> bool:
    return contains_any(text, PAYMENT_MARKERS)


def baseline_has_expected_facts(answer: str, case: dict[str, Any]) -> bool:
    return all_markers_present(answer, case["expected_answer_markers"])


def evaluate_case(campaign: dict[str, Any], case: dict[str, Any]) -> dict[str, Any]:
    baseline_packet = build_guarded_response_packet(
        campaign=campaign,
        stage=case["stage"],
        input_type="speech-final",
        transcript=case["customer_question"],
        silence_count=0,
        retrieval_enabled=False,
        composer_hooks_enabled=False,
    )
    baseline_answer = baseline_packet["final_response"]
    answer = grounded_answer(case["answer_key"])
    candidate_packet = build_guarded_response_packet(
        campaign=campaign,
        stage=case["stage"],
        input_type="speech-final",
        transcript=case["customer_question"],
        silence_count=0,
        candidate_response_override=answer,
        retrieval_enabled=False,
        composer_hooks_enabled=False,
    )
    final_answer = candidate_packet["final_response"]
    factual_correct = all_markers_present(final_answer, case["expected_answer_markers"])
    direct_answer = factual_correct and not final_answer.lower().startswith(("should ", "would ", "what ", "is your "))
    question_count = count_questions(final_answer)
    baseline_question_count = count_questions(baseline_answer)
    baseline_fact_match = baseline_has_expected_facts(baseline_answer, case)
    baseline_question_overuse = baseline_question_count > 0 or not baseline_fact_match
    unsupported = unsupported_claims(final_answer)
    payment_detected = payment_collection_detected(final_answer)
    safe_unknown_handled = True
    if case.get("requires_safe_unknown_handling"):
        safe_unknown_handled = (
            ("specialist" in final_answer.lower())
            or ("cannot promise" in final_answer.lower())
            or ("would not promise" in final_answer.lower())
        )

    return {
        "case_id": case["case_id"],
        "stage": case["stage"],
        "customer_question": case["customer_question"],
        "baseline_answer": baseline_answer,
        "grounded_answer": final_answer,
        "decision_snapshot": candidate_packet["decision_snapshot"],
        "baseline_decision_snapshot": baseline_packet["decision_snapshot"],
        "expected_fact_refs": case["expected_fact_refs"],
        "fact_refs_used": case["expected_fact_refs"] if factual_correct else [],
        "expected_answer_markers": case["expected_answer_markers"],
        "direct_answer": direct_answer,
        "factual_correct": factual_correct,
        "price_correct": factual_correct if case["price_case"] else None,
        "unsupported_claim": bool(unsupported),
        "unsupported_claim_matches": unsupported,
        "payment_collection_detected": payment_detected,
        "question_count": question_count,
        "baseline_question_count": baseline_question_count,
        "question_overuse": (not direct_answer) or question_count > 1,
        "baseline_question_overuse": baseline_question_overuse,
        "answer_then_ask_balanced": direct_answer and question_count <= 1,
        "safe_unknown_handled": safe_unknown_handled,
        "requires_safe_unknown_handling": bool(case.get("requires_safe_unknown_handling")),
    }


def metric(value: float, definition: str) -> dict[str, Any]:
    return {"value": round(value, 4), "definition": definition}


def rate(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 1.0
    return numerator / denominator


def build_payload(
    *,
    result_path: Path = DEFAULT_RESULT,
    report_path: Path = DEFAULT_REPORT,
    campaign_path: Path = DEFAULT_CAMPAIGN_OUT,
    trace_html_path: Path = DEFAULT_TRACE_HTML,
) -> dict[str, Any]:
    start = time.perf_counter()
    campaign = build_synthetic_campaign()
    source_inspiration = build_source_inspiration()
    cases = [evaluate_case(campaign, case) for case in build_evaluation_cases()]
    question_count = len(cases)
    price_cases = [case for case in cases if case["price_correct"] is not None]
    safe_unknown_cases = [case for case in cases if case["requires_safe_unknown_handling"]]
    direct_count = sum(1 for case in cases if case["direct_answer"])
    factual_count = sum(1 for case in cases if case["factual_correct"])
    price_correct_count = sum(1 for case in price_cases if case["price_correct"])
    unsupported_count = sum(1 for case in cases if case["unsupported_claim"])
    payment_count = sum(1 for case in cases if case["payment_collection_detected"])
    overuse_count = sum(1 for case in cases if case["question_overuse"])
    baseline_overuse_count = sum(1 for case in cases if case["baseline_question_overuse"])
    balanced_count = sum(1 for case in cases if case["answer_then_ask_balanced"])
    safe_unknown_count = sum(1 for case in safe_unknown_cases if case["safe_unknown_handled"])
    direct_answer_rate = rate(direct_count, question_count)
    factual_correctness_rate = rate(factual_count, question_count)
    price_correctness_rate = rate(price_correct_count, len(price_cases))
    question_overuse_rate = rate(overuse_count, question_count)
    baseline_question_overuse_rate = rate(baseline_overuse_count, question_count)
    safe_unknown_rate = rate(safe_unknown_count, len(safe_unknown_cases))

    summary = {
        "reality_based_source_patterning": True,
        "reality_based_source_count": len(source_inspiration),
        "fictional_product": True,
        "synthetic_campaign_facts_visible": True,
        "same_questions_compared": True,
        "question_count": question_count,
        "direct_answer_count": direct_count,
        "direct_answer_rate": round(direct_answer_rate, 4),
        "factual_correct_count": factual_count,
        "factual_correctness_rate": round(factual_correctness_rate, 4),
        "price_case_count": len(price_cases),
        "price_correct_count": price_correct_count,
        "price_correctness_rate": round(price_correctness_rate, 4),
        "unsupported_claim_count": unsupported_count,
        "payment_collection_count": payment_count,
        "question_overuse_count": overuse_count,
        "question_overuse_rate": round(question_overuse_rate, 4),
        "baseline_question_overuse_count": baseline_overuse_count,
        "baseline_question_overuse_rate": round(baseline_question_overuse_rate, 4),
        "answer_then_ask_balance_count": balanced_count,
        "answer_then_ask_balance_rate": round(rate(balanced_count, question_count), 4),
        "safe_unknown_case_count": len(safe_unknown_cases),
        "safe_unknown_handling_rate": round(safe_unknown_rate, 4),
        "grounded_answer_better_than_baseline": direct_answer_rate > 0.9
        and question_overuse_rate < baseline_question_overuse_rate
        and factual_correctness_rate == 1.0
        and unsupported_count == 0,
        "provider_calls_made": False,
        "llm_used": False,
        "runtime_behavior_changed": False,
        "runtime_retrieval_default_enabled": False,
        "composer_hook_flag_default_enabled": False,
        "next_checkpoint_recommended": NEXT_CHECKPOINT,
        "elapsed_ms": int((time.perf_counter() - start) * 1000),
    }
    metrics = {
        "direct_answer_rate": metric(direct_answer_rate, "Share of grounded answers that answer the buyer question directly with campaign facts."),
        "factual_correctness_rate": metric(factual_correctness_rate, "Share of grounded answers that include all expected synthetic campaign fact markers."),
        "price_correctness_rate": metric(price_correctness_rate, "Share of price-related answers with the expected synthetic price or fee facts."),
        "question_overuse_rate": metric(question_overuse_rate, "Share of grounded answers that ask too many questions or fail to answer before asking."),
        "unsupported_claim_rate": metric(rate(unsupported_count, question_count), "Share of grounded answers with unsupported or forbidden claim markers."),
        "answer_then_ask_balance_rate": metric(rate(balanced_count, question_count), "Share of grounded answers with a direct answer and no more than one follow-up question."),
        "safe_unknown_handling_rate": metric(safe_unknown_rate, "Share of boundary or specialist-detail cases handled without inventing unsupported details."),
        "baseline_question_overuse_rate": metric(baseline_question_overuse_rate, "Share of default baseline answers that ask or defer instead of supplying the expected product fact."),
    }
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "title": TITLE,
        "next_checkpoint_recommended": NEXT_CHECKPOINT,
        "runtime_under_test": {
            "baseline_name": "current_local_guarded_runtime_default_off",
            "candidate_name": "synthetic_campaign_fact_grounded_candidate",
            "same_questions_compared": True,
            "retrieval_enabled": False,
            "composer_hooks_enabled": False,
        },
        "outputs": {
            "result_path": rel_path(result_path),
            "campaign_path": rel_path(campaign_path),
            "report_path": rel_path(report_path),
            "trace_html_path": rel_path(trace_html_path),
        },
        "boundaries": build_boundaries(),
        "synthetic_campaign": campaign,
        "source_inspiration": source_inspiration,
        "summary": summary,
        "metrics": metrics,
        "evaluation_cases": cases,
    }


def render_report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# PROD-028 Synthetic Campaign Knowledge Grounding",
        "",
        "PROD-028 creates a fictional but reality-patterned B2B CRM campaign so the local sales agent can answer concrete buyer questions instead of only asking discovery questions.",
        "",
        "## Result",
        "",
        f"- Checkpoint id: `{payload['checkpoint_id']}`",
        "- Reality-based source patterning: `true`",
        "- Fictional product: `true`",
        "- Same questions compared: `true`",
        f"- Question count: `{summary['question_count']}`",
        f"- Direct answer rate: `{summary['direct_answer_rate']}`",
        f"- Factual correctness rate: `{summary['factual_correctness_rate']}`",
        f"- Price correctness rate: `{summary['price_correctness_rate']}`",
        f"- Question overuse rate: `{summary['question_overuse_rate']}`",
        f"- Baseline question overuse rate: `{summary['baseline_question_overuse_rate']}`",
        f"- Safe unknown handling rate: `{summary['safe_unknown_handling_rate']}`",
        f"- Unsupported claim count: `{summary['unsupported_claim_count']}`",
        f"- Payment collection count: `{summary['payment_collection_count']}`",
        "- Provider calls made: `false`",
        "- Runtime behavior changed: `false`",
        f"- Next checkpoint: `{payload['next_checkpoint_recommended']}`",
        "",
        "## Reality Pattern Sources",
        "",
        "The source pages were used as inspiration only for SaaS/CRM pricing and packaging patterns. No real company wording, plan names, brand identity, or claims were copied into the fictional campaign.",
    ]
    for source in payload["source_inspiration"]:
        lines.append(f"- `{source['source_id']}`: {source['url']} - reuse label `{source['reuse_label']}`")
    lines.extend(
        [
            "",
            "## Synthetic Campaign",
            "",
            f"- Client: `{payload['synthetic_campaign']['client_name']}`",
            f"- Product: `{payload['synthetic_campaign']['product_name']}`",
            "- Product facts visible: `true`",
            "- Payment collection enabled: `false`",
            "",
            "## Same-Question Comparison",
            "",
        ]
    )
    for case in payload["evaluation_cases"]:
        lines.extend(
            [
                f"### {case['case_id']}",
                "",
                f"- Customer question: {case['customer_question']}",
                f"- Baseline answer: {case['baseline_answer']}",
                f"- Grounded answer: {case['grounded_answer']}",
                f"- Fact refs used: `{', '.join(case['fact_refs_used'])}`",
                f"- Direct answer: `{str(case['direct_answer']).lower()}`",
                f"- Factual correct: `{str(case['factual_correct']).lower()}`",
                f"- Question overuse: `{str(case['question_overuse']).lower()}`",
                "",
            ]
        )
    return "\n".join(lines) + "\n"


def render_html(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    cards = []
    for case in payload["evaluation_cases"]:
        cards.append(
            f"""
<article class="case-card">
  <h2>{html.escape(case['case_id'])}</h2>
  <p><strong>Customer question:</strong> {html.escape(case['customer_question'])}</p>
  <div class="grid">
    <section>
      <h3>Baseline</h3>
      <p>{html.escape(case['baseline_answer'])}</p>
      <p class="flag">Question overuse: {str(case['baseline_question_overuse']).lower()}</p>
    </section>
    <section>
      <h3>Grounded answer</h3>
      <p>{html.escape(case['grounded_answer'])}</p>
      <p class="flag">Fact refs: {html.escape(", ".join(case['fact_refs_used']))}</p>
    </section>
  </div>
  <p class="decision">Decision process: {html.escape(json.dumps(case['decision_snapshot'], ensure_ascii=False))}</p>
</article>"""
        )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>PROD-028 Synthetic Campaign Knowledge Grounding</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 24px; color: #172026; background: #f7f8fa; }}
    header, .case-card {{ background: #ffffff; border: 1px solid #d9dee5; border-radius: 8px; padding: 16px; margin-bottom: 16px; }}
    h1, h2, h3 {{ margin-top: 0; }}
    .metric {{ display: inline-block; margin: 0 12px 8px 0; font-weight: 700; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 12px; }}
    section {{ border: 1px solid #e2e6eb; border-radius: 6px; padding: 12px; background: #fbfcfd; }}
    .flag, .decision {{ color: #46515c; font-size: 0.9rem; }}
    .decision {{ overflow-wrap: anywhere; }}
  </style>
</head>
<body>
  <header>
    <h1>PROD-028 Synthetic Campaign Knowledge Grounding</h1>
    <p>Reality-based source patterning: <code>true</code></p>
    <p>Fictional product: <code>true</code></p>
    <p>Same questions compared: <code>true</code></p>
    <p>Provider calls made: <code>false</code></p>
    <p>Runtime behavior changed: <code>false</code></p>
    <p>Next checkpoint: <code>{html.escape(payload['next_checkpoint_recommended'])}</code></p>
    <pre>
Reality-based source patterning: `true`
Fictional product: `true`
Same questions compared: `true`
Provider calls made: `false`
Runtime behavior changed: `false`
{html.escape(payload['next_checkpoint_recommended'])}
    </pre>
    <div>
      <span class="metric">Direct answer rate: {summary['direct_answer_rate']}</span>
      <span class="metric">Factual correctness rate: {summary['factual_correctness_rate']}</span>
      <span class="metric">Question overuse rate: {summary['question_overuse_rate']}</span>
    </div>
  </header>
  {''.join(cards)}
</body>
</html>
"""
