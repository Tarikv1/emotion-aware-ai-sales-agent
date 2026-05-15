#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.core.realtime_turns import build_runtime_decision  # noqa: E402


CHECKPOINT_ID = "PROD-053C-english-spoken-response-expansion-review"
CHECKPOINT_NAME = "English Spoken Response Expansion Review"
SOURCE_CHECKPOINT_ID = "PROD-053B-compact-english-psychology-layer-review"
LANGUAGE_LANE_CHECKPOINT_ID = "PROD-052-language-lane-review-separation"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
SOURCE_DIR = ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID

SOURCE_FILES = {
    "source_result": SOURCE_DIR / "result.json",
    "compact_policy": SOURCE_DIR / "compact_english_policy_rules.json",
    "case_audit": SOURCE_DIR / "current_english_case_policy_audit.json",
}

BOUNDARY_FLAGS = {
    "runtime_behavior_changed": False,
    "response_text_behavior_changed": False,
    "retrieval_enabled": False,
    "provider_calls_made": False,
    "llm_used": False,
    "llm_judging_used": False,
    "private_data_read": False,
    "voice_playback_unblocked": False,
    "public_demo_polish_unblocked": False,
    "payment_collection_allowed": False,
    "contract_signing_allowed": False,
    "production_runtime_promotion_allowed": False,
    "german_exact_phrase_promotion_allowed": False,
    "german_naturalness_claimed": False,
}

BASE_CAMPAIGN = {
    "campaign_id": "prod-053c-english-review-campaign",
    "language": "en",
    "locale": "en-US",
    "product_category": "sales follow-up automation",
    "customer_type": "business",
    "pricing_summary": "The starter plan is 29 per user per month",
    "approved_written_summary": "a short written summary",
    "approved_email_followup_scope": "a short written summary",
    "approved_review_summary": "a short review summary",
    "caller_identity": "Maya from RouteSignal",
    "company_or_campaign_name": "RouteSignal",
    "approved_reason_for_call": "to see whether missed callbacks and follow-up work are still an issue",
    "approved_verification_path": "the official verification path",
    "support_route": "support",
    "cancellation_route": "the cancellation team",
    "specialist_handoff_route": "a specialist",
    "approved_technical_scope": "standard API integration is available through the documented endpoint",
    "regulated_advice_boundary_text": "I should not give coverage or medical advice.",
    "approved_gap_isolation_question": "The useful check is whether there is a gap they do not cover.",
    "approved_sale_ready_next_step": "the specialist follow-up",
    "close_criteria_satisfied": False,
    "sale_ready_close_allowed": False,
}

SALE_READY_CAMPAIGN = {
    **BASE_CAMPAIGN,
    "close_criteria_satisfied": True,
    "sale_ready_close_allowed": True,
}

POLICY_RULE_NAMES = {
    "en_response_001_answer_then_continue": "Answer, then continue.",
    "en_response_002_plain_relief": "Keep relief plain.",
    "en_response_003_mirror_only_for_repair": "Mirror only for repair.",
    "en_response_004_one_small_decision": "One small decision.",
    "en_response_005_friction_not_personality": "Diagnose friction, not personality.",
    "en_response_006_autonomy_visible": "Make autonomy visible.",
    "en_response_007_trust_gap_specific": "Answer the specific trust gap.",
    "en_response_008_stop_after_question": "Ask, then stop.",
}

PROPOSED_RESPONSES = {
    "voicemail": "I reached voicemail, so I will note it for follow-up.",
    "repeated-silence": "I will end the call for now. Goodbye.",
    "do-not-call": "Understood. I will mark this so you are not called again. Goodbye.",
    "human-request": "Of course. I will pass this to a human specialist.",
    "identity-repair": "Of course. I can confirm who I am and why I am calling before we continue.",
    "scam-safety-boundary": "No payment, card, or sensitive details are collected on this call. I can send the verification path instead.",
    "payment-safety-boundary": "No card or payment details are needed here. I can keep this to written information.",
    "support-route": "That sounds like support. I will stop here and send this to support.",
    "cancellation-route": "Understood. I will stop here and send this to the cancellation team.",
    "email-only-boundary": "Understood. I will keep this to email and will not push for a call.",
    "technical-specialist-route": "I should not guess on technical details. I can send this to a specialist.",
    "security-review-route": "Security review needs verified material or a specialist. I will not make broad compliance claims here.",
    "coverage-boundary-route": "I should not give coverage advice. I can send this to a qualified reviewer.",
    "healthcare-boundary-route": "I should not give health or medical advice. I can send this to a qualified reviewer.",
    "claim-boundary": "I do not want to guarantee something that depends on the details. A specialist can check that.",
    "product-detail-lookup": "One moment. I will check the product details before I answer.",
    "scheduling-confirmation": "Confirmed. I will note that time for the specialist callback. Goodbye.",
    "sale-ready-missing-criteria": "Before I mark this as ready, I need one more check. No payment or contract signing happens on this call.",
    "sale-ready-commitment": "Confirmed. I will mark that you want the next step. No payment is handled on this call.",
    "procurement-review": "Understood. I can keep this to written review information. Nothing firm today.",
    "stakeholder-review": "Of course. I can send it over. No commitment today. Take a look and let me know.",
    "partner-review": "Of course. I can send it over. No commitment today. Take a look and let me know.",
    "existing-provider-gap": "I will not claim this replaces your provider. The useful check is whether there is a gap it does not cover.",
    "callback-request": "I can set a callback as optional. No forced appointment or commitment today.",
    "autonomy-check": "That makes sense. We can keep this low-pressure and only clarify what you need.",
    "trust-gap": "Fair question. I can send the verification path before we discuss any next step.",
    "timing-delay": "No problem. I will leave it open for now instead of forcing a time today.",
    "price-objection": "That makes sense. Is the main concern price, or whether it is worth the effort?",
    "unknown-runtime-signal": "Thanks. Can I ask one quick clarifying question?",
}

RUNTIME_PROBES = [
    {
        "case_id": "prod-053c-voicemail",
        "case_title": "Voicemail detected",
        "sales_difficulty": "voicemail",
        "customer_utterance": "[voicemail detected]",
        "customer_input": {"input_type": "voicemail-detected", "transcript": "", "stage": "opening"},
    },
    {
        "case_id": "prod-053c-repeated-silence",
        "case_title": "Repeated silence",
        "sales_difficulty": "repeated-silence",
        "customer_utterance": "[customer silent twice]",
        "customer_input": {"input_type": "silence-timeout", "silence_count": 2, "transcript": "", "stage": "opening"},
    },
    {
        "case_id": "prod-053c-do-not-call",
        "case_title": "Do not call",
        "sales_difficulty": "do-not-call",
        "customer_utterance": "Do not call me again.",
        "customer_input": {"input_type": "speech", "transcript": "Do not call me again.", "stage": "opening"},
    },
    {
        "case_id": "prod-053c-human-request",
        "case_title": "Human request",
        "sales_difficulty": "human-request",
        "customer_utterance": "I want to speak with a human.",
        "customer_input": {"input_type": "speech", "transcript": "I want to speak with a human.", "stage": "opening"},
    },
    {
        "case_id": "prod-053c-identity-repair",
        "case_title": "Identity repair",
        "sales_difficulty": "identity-repair",
        "customer_utterance": "Who are you?",
        "customer_input": {"input_type": "speech", "transcript": "Who are you?", "stage": "opening"},
    },
    {
        "case_id": "prod-053c-scam-safety-boundary",
        "case_title": "Scam safety boundary",
        "sales_difficulty": "scam-safety-boundary",
        "customer_utterance": "Is this a scam?",
        "customer_input": {"input_type": "speech", "transcript": "Is this a scam?", "stage": "opening"},
    },
    {
        "case_id": "prod-053c-payment-safety-boundary",
        "case_title": "Payment safety boundary",
        "sales_difficulty": "payment-safety-boundary",
        "customer_utterance": "I am not giving card details.",
        "customer_input": {"input_type": "speech", "transcript": "I am not giving card details.", "stage": "objection"},
    },
    {
        "case_id": "prod-053c-support-route",
        "case_title": "Support route",
        "sales_difficulty": "support-route",
        "customer_utterance": "I need support with my account.",
        "customer_input": {"input_type": "speech", "transcript": "I need support with my account.", "stage": "objection"},
    },
    {
        "case_id": "prod-053c-cancellation-route",
        "case_title": "Cancellation route",
        "sales_difficulty": "cancellation-route",
        "customer_utterance": "I want to cancel.",
        "customer_input": {"input_type": "speech", "transcript": "I want to cancel.", "stage": "objection"},
    },
    {
        "case_id": "prod-053c-email-only-boundary",
        "case_title": "Email-only boundary",
        "sales_difficulty": "email-only-boundary",
        "customer_utterance": "Just email me.",
        "customer_input": {"input_type": "speech", "transcript": "Just email me.", "stage": "objection"},
    },
    {
        "case_id": "prod-053c-technical-specialist-route",
        "case_title": "Technical specialist route",
        "sales_difficulty": "technical-specialist-route",
        "customer_utterance": "I have a technical question about the API.",
        "customer_input": {"input_type": "speech", "transcript": "I have a technical question about the API.", "stage": "objection"},
    },
    {
        "case_id": "prod-053c-security-review-route",
        "case_title": "Security review route",
        "sales_difficulty": "security-review-route",
        "customer_utterance": "Our security team needs SOC 2.",
        "customer_input": {"input_type": "speech", "transcript": "Our security team needs SOC 2.", "stage": "objection"},
    },
    {
        "case_id": "prod-053c-coverage-boundary-route",
        "case_title": "Coverage boundary route",
        "sales_difficulty": "coverage-boundary-route",
        "customer_utterance": "Is this covered?",
        "customer_input": {"input_type": "speech", "transcript": "Is this covered?", "stage": "objection"},
    },
    {
        "case_id": "prod-053c-healthcare-boundary-route",
        "case_title": "Healthcare boundary route",
        "sales_difficulty": "healthcare-boundary-route",
        "customer_utterance": "Can you give medical advice?",
        "customer_input": {"input_type": "speech", "transcript": "Can you give medical advice?", "stage": "objection"},
    },
    {
        "case_id": "prod-053c-claim-boundary",
        "case_title": "Claim boundary",
        "sales_difficulty": "claim-boundary",
        "customer_utterance": "Can you guarantee this works?",
        "customer_input": {"input_type": "speech", "transcript": "Can you guarantee this works?", "stage": "objection"},
    },
    {
        "case_id": "prod-053c-product-detail-lookup",
        "case_title": "Product detail lookup",
        "sales_difficulty": "product-detail-lookup",
        "customer_utterance": "Which exact plan is included?",
        "customer_input": {"input_type": "speech", "transcript": "Which exact plan is included?", "stage": "objection"},
    },
    {
        "case_id": "prod-053c-scheduling-confirmation",
        "case_title": "Scheduling confirmation",
        "sales_difficulty": "scheduling-confirmation",
        "customer_utterance": "Wednesday at 10 works.",
        "customer_input": {"input_type": "speech", "transcript": "Wednesday at 10 works.", "stage": "scheduling"},
    },
    {
        "case_id": "prod-053c-sale-ready-missing-criteria",
        "case_title": "Sale-ready missing criteria",
        "sales_difficulty": "sale-ready-missing-criteria",
        "customer_utterance": "I am ready to move forward.",
        "customer_input": {"input_type": "speech", "transcript": "I am ready to move forward.", "stage": "close"},
    },
    {
        "case_id": "prod-053c-sale-ready-commitment",
        "case_title": "Sale-ready commitment",
        "sales_difficulty": "sale-ready-commitment",
        "customer_utterance": "I am ready to move forward.",
        "customer_input": {"input_type": "speech", "transcript": "I am ready to move forward.", "stage": "close"},
        "campaign": SALE_READY_CAMPAIGN,
    },
    {
        "case_id": "prod-053c-procurement-review",
        "case_title": "Procurement review",
        "sales_difficulty": "procurement-review",
        "customer_utterance": "We need written information for procurement.",
        "customer_input": {"input_type": "speech", "transcript": "We need written information for procurement.", "stage": "procurement-review"},
    },
    {
        "case_id": "prod-053c-existing-provider-gap",
        "case_title": "Existing provider gap",
        "sales_difficulty": "existing-provider-gap",
        "customer_utterance": "We already use another provider.",
        "customer_input": {"input_type": "speech", "transcript": "We already use another provider.", "stage": "objection"},
    },
    {
        "case_id": "prod-053c-callback-request",
        "case_title": "Callback request",
        "sales_difficulty": "callback-request",
        "customer_utterance": "Can you call back later?",
        "customer_input": {"input_type": "speech", "transcript": "Can you call back later?", "stage": "objection"},
    },
    {
        "case_id": "prod-053c-autonomy-check",
        "case_title": "Autonomy check",
        "sales_difficulty": "autonomy-check",
        "customer_utterance": "I need time to think. Do not rush.",
        "customer_input": {"input_type": "speech", "transcript": "I need time to think. Do not rush.", "stage": "objection"},
    },
    {
        "case_id": "prod-053c-trust-gap",
        "case_title": "Trust gap",
        "sales_difficulty": "trust-gap",
        "customer_utterance": "I do not know your company.",
        "customer_input": {"input_type": "speech", "transcript": "I do not know your company.", "stage": "objection"},
    },
    {
        "case_id": "prod-053c-timing-delay",
        "case_title": "Timing delay",
        "sales_difficulty": "timing-delay",
        "customer_utterance": "Nothing firm. Maybe next week.",
        "customer_input": {"input_type": "speech", "transcript": "Nothing firm. Maybe next week.", "stage": "objection"},
    },
    {
        "case_id": "prod-053c-price-objection",
        "case_title": "Price objection",
        "sales_difficulty": "price-objection",
        "customer_utterance": "This is too expensive.",
        "customer_input": {"input_type": "speech", "transcript": "This is too expensive.", "stage": "objection"},
    },
    {
        "case_id": "prod-053c-unknown-runtime-signal",
        "case_title": "Unknown runtime signal",
        "sales_difficulty": "unknown-runtime-signal",
        "customer_utterance": "I am not sure yet.",
        "customer_input": {"input_type": "speech", "transcript": "I am not sure yet.", "stage": "objection"},
    },
]


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def word_count(text: str) -> int:
    return len([chunk for chunk in text.replace("/", " ").split() if chunk.strip()])


def sentence_count(text: str) -> int:
    return sum(1 for chunk in text.replace("?", ".").replace("!", ".").split(".") if chunk.strip())


def compact_policy_rules() -> list[dict[str, Any]]:
    return read_json(SOURCE_FILES["compact_policy"])["items"]


def source_case_audit() -> dict[str, Any]:
    return read_json(SOURCE_FILES["case_audit"])


def sanitized_runtime_decision(decision: dict[str, Any]) -> dict[str, Any]:
    return {
        "response_language": decision["response_language"],
        "response_mode": decision["response_mode"],
        "sales_difficulty": decision["sales_difficulty"],
        "interest_state": decision["interest_state"],
        "selected_strategy": decision["selected_strategy"],
        "next_action": decision["next_action"],
        "call_control": decision["call_control"],
        "agent_response": decision["agent_response"],
    }


def runtime_decision_for(spec: dict[str, Any]) -> dict[str, Any]:
    case = {"case_id": spec["case_id"], "customer_input": spec["customer_input"]}
    decision = build_runtime_decision(case, campaign=spec.get("campaign", BASE_CAMPAIGN))
    if decision["response_language"] != "en" or decision["sales_difficulty"] != spec["sales_difficulty"]:
        raise RuntimeError(
            f"probe {spec['case_id']} expected {spec['sales_difficulty']} / en "
            f"but got {decision['sales_difficulty']} / {decision['response_language']}"
        )
    return decision


def policy_ids_for(sales_difficulty: str, proposed_response: str) -> list[str]:
    ids = ["en_response_001_answer_then_continue", "en_response_004_one_small_decision"]
    if sales_difficulty in {
        "stakeholder-review",
        "partner-review",
        "procurement-review",
        "callback-request",
        "timing-delay",
        "sale-ready-commitment",
        "sale-ready-missing-criteria",
        "email-only-boundary",
        "do-not-call",
        "payment-safety-boundary",
        "scam-safety-boundary",
    }:
        ids.append("en_response_002_plain_relief")
    if sales_difficulty in {"stakeholder-review", "partner-review"}:
        ids.append("en_response_003_mirror_only_for_repair")
    if sales_difficulty in {"price-objection", "unknown-runtime-signal", "existing-provider-gap", "autonomy-check"}:
        ids.append("en_response_005_friction_not_personality")
    if sales_difficulty in {
        "do-not-call",
        "human-request",
        "email-only-boundary",
        "callback-request",
        "timing-delay",
        "autonomy-check",
        "procurement-review",
        "stakeholder-review",
        "partner-review",
    }:
        ids.append("en_response_006_autonomy_visible")
    if sales_difficulty in {"trust-gap", "scam-safety-boundary", "identity-repair", "security-review-route"}:
        ids.append("en_response_007_trust_gap_specific")
    if proposed_response.rstrip().endswith("?"):
        ids.append("en_response_008_stop_after_question")
    return list(dict.fromkeys(ids))


def audit_current_response(sales_difficulty: str, response: str) -> list[str]:
    lowered = response.lower()
    issues: list[str] = []
    internal_terms = [
        "according to campaign rules",
        "approved",
        "sale-ready",
        "close criteria",
        "sales path",
        "automatically",
        "log",
        "route",
    ]
    if any(term in lowered for term in internal_terms):
        issues.append("internal_runtime_jargon")
    if word_count(response) > 24 or sentence_count(response) > 2:
        issues.append("live_turn_too_long")
    if "?" in response and not response.rstrip().endswith("?"):
        issues.append("continues_after_question")
    if sales_difficulty in {"stakeholder-review", "partner-review"}:
        if any(token in lowered for token in ["manager", "boss", "spouse", "partner"]):
            issues.append("customer_category_echo")
        if "commitment" not in lowered:
            issues.append("relief_needs_commitment_wording")
    if "no decision or commitment from you today" in lowered:
        issues.append("policy_dump_relief")
    return list(dict.fromkeys(issues))


def policy_rule_results(applied_rule_ids: list[str], issues: list[str]) -> list[dict[str, Any]]:
    results = []
    for rule_id in applied_rule_ids:
        results.append(
            {
                "policy_rule_id": rule_id,
                "name": POLICY_RULE_NAMES[rule_id],
                "applied": True,
                "current_response_needs_review": bool(issues),
                "runtime_promoted": False,
            }
        )
    return results


def build_flagged_rewrite_items(source_audit: dict[str, Any]) -> list[dict[str, Any]]:
    items = []
    for source_item in source_audit["items"]:
        if source_item["prod_053c_rewrite_decision"] != "rewrite_candidate":
            continue
        spec = {
            "case_id": source_item["case_id"],
            "case_title": "PROD-053B flagged rewrite",
            "sales_difficulty": source_item["sales_difficulty"],
            "customer_utterance": source_item["customer_utterance"],
            "customer_input": {
                "input_type": "speech",
                "transcript": source_item["customer_utterance"],
                "stage": "authority-check" if source_item["sales_difficulty"] == "stakeholder-review" else "objection",
            },
        }
        decision = runtime_decision_for(spec)
        current_response = source_item["current_agent_response"]
        issues = list(dict.fromkeys([*source_item["policy_issues"], *audit_current_response(source_item["sales_difficulty"], current_response)]))
        proposed = PROPOSED_RESPONSES[source_item["sales_difficulty"]]
        applied = policy_ids_for(source_item["sales_difficulty"], proposed)
        items.append(
            {
                "case_id": source_item["case_id"],
                "case_title": spec["case_title"],
                "language": "en",
                "source_scope": "flagged_prod_053b_rewrite",
                "sales_difficulty": source_item["sales_difficulty"],
                "customer_utterance": source_item["customer_utterance"],
                "current_agent_response": current_response,
                "current_runtime_decision": sanitized_runtime_decision(decision),
                "proposed_review_response": proposed,
                "applied_policy_rule_ids": applied,
                "policy_issues": issues,
                "policy_note": "Included because PROD-053B flagged the already-visible English response for rewrite review.",
                "review_status": "ready_for_tarik_english_review",
                "requires_tarik_review": True,
                "exact_phrase_review_allowed": True,
                "german_exact_phrase_review_allowed": False,
                "runtime_response_changed": False,
                "runtime_promoted": False,
            }
        )
    return items


def build_unreviewed_runtime_items() -> list[dict[str, Any]]:
    items = []
    for spec in RUNTIME_PROBES:
        decision = runtime_decision_for(spec)
        proposed = PROPOSED_RESPONSES[spec["sales_difficulty"]]
        issues = audit_current_response(spec["sales_difficulty"], decision["agent_response"])
        applied = policy_ids_for(spec["sales_difficulty"], proposed)
        items.append(
            {
                "case_id": spec["case_id"],
                "case_title": spec["case_title"],
                "language": "en",
                "source_scope": "unreviewed_runtime_response_surface",
                "sales_difficulty": spec["sales_difficulty"],
                "customer_utterance": spec["customer_utterance"],
                "current_agent_response": decision["agent_response"],
                "current_runtime_decision": sanitized_runtime_decision(decision),
                "proposed_review_response": proposed,
                "applied_policy_rule_ids": applied,
                "policy_issues": issues,
                "policy_note": "Included because this English deterministic runtime response was not part of the PROD-052 exact phrase review lane.",
                "review_status": "ready_for_tarik_english_review",
                "requires_tarik_review": True,
                "exact_phrase_review_allowed": True,
                "german_exact_phrase_review_allowed": False,
                "runtime_response_changed": False,
                "runtime_promoted": False,
            }
        )
    return items


def build_scope_decisions(source_audit: dict[str, Any]) -> dict[str, Any]:
    excluded = []
    included = []
    for item in source_audit["items"]:
        if item["prod_053c_rewrite_decision"] == "carry_forward":
            excluded.append(
                {
                    "case_id": item["case_id"],
                    "sales_difficulty": item["sales_difficulty"],
                    "reason": "Already reviewed and carried forward by PROD-053B; excluding avoids duplicate owner review.",
                    "runtime_response_changed": False,
                }
            )
        elif item["prod_053c_rewrite_decision"] == "rewrite_candidate":
            included.append(
                {
                    "case_id": item["case_id"],
                    "sales_difficulty": item["sales_difficulty"],
                    "reason": "PROD-053B flagged this response for English rewrite review.",
                    "policy_issues": item["policy_issues"],
                    "runtime_response_changed": False,
                }
            )
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "language_lane_checkpoint_id": LANGUAGE_LANE_CHECKPOINT_ID,
        "english_only_review": True,
        "german_exact_phrase_review_allowed": False,
        "runtime_behavior_changed": False,
        "response_text_behavior_changed": False,
        "excluded_already_approved_items": excluded,
        "included_flagged_rewrite_items": included,
        "excluded_unreachable_or_deferred_items": [
            {
                "sales_difficulty": "provider-comparison",
                "reason": "Localized response text exists, but the current deterministic classifier has no distinct reachable English provider-comparison branch. Keep out of exact phrase review until runtime reachability is clarified.",
            }
        ],
    }


def build_policy_application_audit(review_items: list[dict[str, Any]]) -> dict[str, Any]:
    items = []
    for item in review_items:
        items.append(
            {
                "case_id": item["case_id"],
                "language": "en",
                "sales_difficulty": item["sales_difficulty"],
                "source_scope": item["source_scope"],
                "current_word_count": word_count(item["current_agent_response"]),
                "proposed_word_count": word_count(item["proposed_review_response"]),
                "policy_issues": item["policy_issues"],
                "policy_rule_results": policy_rule_results(item["applied_policy_rule_ids"], item["policy_issues"]),
                "runtime_response_changed": False,
            }
        )
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "items": items,
        "runtime_behavior_changed": False,
        "response_text_behavior_changed": False,
    }


def build_summary(
    policy_rules: list[dict[str, Any]],
    scope_decisions: dict[str, Any],
    flagged_items: list[dict[str, Any]],
    unreviewed_items: list[dict[str, Any]],
) -> dict[str, Any]:
    review_items = [*flagged_items, *unreviewed_items]
    return {
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "language_lane_checkpoint_id": LANGUAGE_LANE_CHECKPOINT_ID,
        "english_only_review": True,
        "source_compact_policy_rule_count": len(policy_rules),
        "carry_forward_excluded_count": len(scope_decisions["excluded_already_approved_items"]),
        "flagged_rewrite_included_count": len(flagged_items),
        "unreviewed_runtime_response_count": len(unreviewed_items),
        "review_item_count": len(review_items),
        "all_review_items_ready_for_tarik": all(item["review_status"] == "ready_for_tarik_english_review" for item in review_items),
        "approved_carry_forward_case_ids": sorted(item["case_id"] for item in scope_decisions["excluded_already_approved_items"]),
        "runtime_response_source": "runtime/core/realtime_turns.py",
        "review_artifact_only": True,
        **BOUNDARY_FLAGS,
    }


def render_report(payload: dict[str, Any], review_items: list[dict[str, Any]]) -> str:
    summary = payload["summary"]
    lines = [
        f"# {CHECKPOINT_NAME}",
        "",
        "`PROD-053C` creates the broader English-only spoken-response review packet from the current deterministic runtime surface.",
        "",
        "It does not change runtime behavior or response text. The proposed review responses are review candidates only.",
        "",
        "## Summary",
        "",
        f"- Source compact policy rules: `{summary['source_compact_policy_rule_count']}`",
        f"- Already-approved English items excluded: `{summary['carry_forward_excluded_count']}`",
        f"- PROD-053B flagged rewrites included: `{summary['flagged_rewrite_included_count']}`",
        f"- Unreviewed runtime response items included: `{summary['unreviewed_runtime_response_count']}`",
        f"- Total review items: `{summary['review_item_count']}`",
        f"- Runtime behavior changed: `{str(summary['runtime_behavior_changed']).lower()}`",
        f"- Response text behavior changed: `{str(summary['response_text_behavior_changed']).lower()}`",
        f"- LLM used: `{str(summary['llm_used']).lower()}`",
        f"- Provider calls made: `{str(summary['provider_calls_made']).lower()}`",
        "",
        "## Scope Decisions",
        "",
        "- Exclude `prod-045-price-first` and `prod-045-send-info` because PROD-053B carried them forward.",
        "- Include `prod-045-manager` and `prod-045-spouse` because PROD-053B still flags them as rewrite candidates for compactness and response-shape review.",
        "- Include current reachable English runtime response types that were not in the PROD-052 exact phrase review lane.",
        "- Keep German exact phrase review blocked.",
        "- Keep the currently unreachable `provider-comparison` response out of exact phrase review until classifier reachability is clarified.",
        "",
        "## Review Items",
        "",
    ]
    for item in review_items:
        lines.extend(
            [
                f"### {item['case_id']} - {item['sales_difficulty']}",
                "",
                f"- Source scope: `{item['source_scope']}`",
                f"- Customer: {item['customer_utterance']}",
                f"- Current response: {item['current_agent_response']}",
                f"- Proposed review response: {item['proposed_review_response']}",
                f"- Policy issues: `{', '.join(item['policy_issues']) or 'none'}`",
                f"- Applied policy rules: `{', '.join(item['applied_policy_rule_ids'])}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Boundaries",
            "",
            "- English-only exact phrase review.",
            "- No German exact phrase promotion.",
            "- No runtime behavior or response text changed.",
            "- No LLM calls, LLM judging, provider calls, retrieval enablement, private data reads, voice playback, public demo use, payment collection, contract signing, or production promotion.",
            "",
        ]
    )
    return "\n".join(lines)


def render_review_html(review_items: list[dict[str, Any]], payload: dict[str, Any]) -> str:
    data_json = html.escape(json.dumps({"checkpoint_id": CHECKPOINT_ID, "items": review_items}, indent=2), quote=False)
    cards = []
    for item in review_items:
        issues = ", ".join(item["policy_issues"]) or "none"
        cards.append(
            "<section class='item' data-case-id='{case_id}'>"
            "<div class='item-head'><h2>{case_id}</h2><span>{difficulty}</span></div>"
            "<p class='scope'>{scope}</p>"
            "<p><strong>Customer</strong><br>{customer}</p>"
            "<p><strong>Current runtime response</strong><br>{current}</p>"
            "<p><strong>Proposed review response</strong><br>{proposed}</p>"
            "<p><strong>Policy issues</strong><br>{issues}</p>"
            "<label>Status<select data-field='status'>"
            "<option value='pending'>Pending</option>"
            "<option value='approved'>Approved</option>"
            "<option value='needs_rework'>Needs rework</option>"
            "</select></label>"
            "<label>Reviewer notes<textarea data-field='notes' rows='3'></textarea></label>"
            "</section>".format(
                case_id=html.escape(item["case_id"]),
                difficulty=html.escape(item["sales_difficulty"]),
                scope=html.escape(item["source_scope"]),
                customer=html.escape(item["customer_utterance"]),
                current=html.escape(item["current_agent_response"]),
                proposed=html.escape(item["proposed_review_response"]),
                issues=html.escape(issues),
            )
        )
    cards_html = "\n  ".join(cards)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>PROD-053C English Spoken Response Review</title>
  <style>
    body {{ margin: 24px; font-family: Arial, sans-serif; color: #172026; background: #f5f7fa; line-height: 1.45; }}
    header, .controls, .item {{ background: #fff; border: 1px solid #d9e2ec; border-radius: 8px; padding: 16px; margin-bottom: 14px; }}
    h1 {{ margin: 0 0 6px; font-size: 28px; }}
    .meta {{ color: #52606d; margin: 0; }}
    .stats {{ display: flex; flex-wrap: wrap; gap: 10px; margin-top: 12px; }}
    .stat {{ border: 1px solid #bcccdc; border-radius: 6px; padding: 6px 8px; background: #f8fafc; }}
    .controls {{ display: grid; gap: 10px; }}
    button {{ width: fit-content; border: 1px solid #334e68; background: #243b53; color: #fff; border-radius: 6px; padding: 8px 10px; cursor: pointer; }}
    textarea, select {{ width: 100%; box-sizing: border-box; margin-top: 4px; border: 1px solid #bcccdc; border-radius: 6px; padding: 8px; font: inherit; background: #fff; }}
    .item-head {{ display: flex; justify-content: space-between; gap: 12px; align-items: baseline; border-bottom: 1px solid #e6edf3; margin-bottom: 8px; }}
    .item h2 {{ font-size: 18px; margin: 0 0 8px; }}
    .item-head span, .scope {{ color: #52606d; }}
    label {{ display: block; margin-top: 10px; font-weight: 700; }}
    #exportBox, #importBox {{ min-height: 120px; font-family: Consolas, monospace; }}
  </style>
</head>
<body>
  <header>
    <h1>PROD-053C English Spoken Response Review</h1>
    <p class="meta">English-only exact phrase review. No runtime behavior change, no German exact phrase promotion, no LLM, no provider call.</p>
    <div class="stats">
      <span class="stat">Review items: {payload['summary']['review_item_count']}</span>
      <span class="stat">Carry-forward excluded: {payload['summary']['carry_forward_excluded_count']}</span>
      <span class="stat">Flagged rewrites: {payload['summary']['flagged_rewrite_included_count']}</span>
      <span class="stat">Unreviewed runtime items: {payload['summary']['unreviewed_runtime_response_count']}</span>
    </div>
  </header>

  <section class="controls">
    <strong>Local review state</strong>
    <span>Selections and notes save to localStorage in this browser.</span>
    <button type="button" id="exportBtn">Export JSON</button>
    <textarea id="exportBox" readonly></textarea>
    <textarea id="importBox" placeholder="Paste review JSON here to import"></textarea>
    <button type="button" id="importBtn">Import JSON</button>
  </section>

  <script id="reviewData" type="application/json">{data_json}</script>
  {cards_html}

  <script>
    const storageKey = "PROD-053C-english-spoken-response-expansion-review";
    const rows = Array.from(document.querySelectorAll("[data-case-id]"));

    function readState() {{
      const state = {{ checkpoint_id: storageKey, items: [] }};
      for (const row of rows) {{
        state.items.push({{
          case_id: row.dataset.caseId,
          status: row.querySelector("[data-field='status']").value,
          notes: row.querySelector("[data-field='notes']").value
        }});
      }}
      return state;
    }}

    function writeState(state) {{
      const byId = new Map((state.items || []).map((item) => [item.case_id, item]));
      for (const row of rows) {{
        const item = byId.get(row.dataset.caseId);
        if (!item) continue;
        row.querySelector("[data-field='status']").value = item.status || "pending";
        row.querySelector("[data-field='notes']").value = item.notes || "";
      }}
    }}

    function saveState() {{
      localStorage.setItem(storageKey, JSON.stringify(readState(), null, 2));
    }}

    const saved = localStorage.getItem(storageKey);
    if (saved) {{
      try {{ writeState(JSON.parse(saved)); }} catch (error) {{ console.warn(error); }}
    }}

    for (const row of rows) {{
      row.addEventListener("change", saveState);
      row.addEventListener("input", saveState);
    }}

    document.getElementById("exportBtn").addEventListener("click", () => {{
      const text = JSON.stringify(readState(), null, 2);
      document.getElementById("exportBox").value = text;
      localStorage.setItem(storageKey, text);
    }});

    document.getElementById("importBtn").addEventListener("click", () => {{
      const text = document.getElementById("importBox").value;
      const parsed = JSON.parse(text);
      writeState(parsed);
      saveState();
    }});
  </script>
</body>
</html>
"""


def build_payload() -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    source_result = read_json(SOURCE_FILES["source_result"])
    policy_rules = compact_policy_rules()
    source_audit = source_case_audit()
    scope_decisions = build_scope_decisions(source_audit)
    flagged_items = build_flagged_rewrite_items(source_audit)
    unreviewed_items = build_unreviewed_runtime_items()
    review_items = [*flagged_items, *unreviewed_items]
    policy_audit = build_policy_application_audit(review_items)
    summary = build_summary(policy_rules, scope_decisions, flagged_items, unreviewed_items)
    payload = {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "language_lane_checkpoint_id": LANGUAGE_LANE_CHECKPOINT_ID,
        "source_validation_passed": source_result["validation"]["passed"],
        "summary": summary,
        "outputs": {
            "result": rel(OUT_DIR / "result.json"),
            "report": rel(OUT_DIR / "report.md"),
            "review_items": rel(OUT_DIR / "english_spoken_response_review_items.json"),
            "scope_decisions": rel(OUT_DIR / "review_scope_decisions.json"),
            "policy_audit": rel(OUT_DIR / "policy_application_audit.json"),
            "review_html": rel(OUT_DIR / "prod_053c_english_spoken_response_review.html"),
        },
        "validation": {
            "passed": source_result["validation"]["passed"]
            and summary["source_compact_policy_rule_count"] == 8
            and summary["carry_forward_excluded_count"] == 2
            and summary["flagged_rewrite_included_count"] == 2
            and summary["review_item_count"] == len(review_items)
            and summary["all_review_items_ready_for_tarik"],
            "notes": [
                "Review candidates only; no runtime behavior or response text was changed.",
                "Already-approved English carry-forward items are excluded.",
                "German exact phrase review remains blocked.",
            ],
        },
    }
    return payload, review_items, scope_decisions, policy_audit


def main() -> None:
    payload, review_items, scope_decisions, policy_audit = build_payload()
    write_json(OUT_DIR / "english_spoken_response_review_items.json", {"checkpoint_id": CHECKPOINT_ID, "items": review_items})
    write_json(OUT_DIR / "review_scope_decisions.json", scope_decisions)
    write_json(OUT_DIR / "policy_application_audit.json", policy_audit)
    write_text(OUT_DIR / "report.md", render_report(payload, review_items))
    write_text(OUT_DIR / "prod_053c_english_spoken_response_review.html", render_review_html(review_items, payload))
    write_json(OUT_DIR / "result.json", payload)
    print(json.dumps({"checkpoint_id": CHECKPOINT_ID, "validation": payload["validation"], "summary": payload["summary"]}, indent=2))


if __name__ == "__main__":
    main()
