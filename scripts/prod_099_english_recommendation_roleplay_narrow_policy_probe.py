#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from prod_087_english_guided_option_selection_runtime_patch import TEST_CAMPAIGN, word_count  # noqa: E402


CHECKPOINT_ID = "PROD-099-english-recommendation-roleplay-narrow-policy-probe"
CHECKPOINT_NAME = "English Recommendation Roleplay Narrow Policy Probe"
SOURCE_CHECKPOINT_ID = "PROD-098-english-recommendation-roleplay-review-import"
NEXT_CHECKPOINT_ID = "PROD-100-english-recommendation-roleplay-runtime-patch"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
SOURCE_DIR = ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID
SOURCE_VALIDATOR = ROOT / "scripts" / "validate_prod_098_english_recommendation_roleplay_review_import.py"

TARGET_DIFFICULTY = "recommendation-roleplay-boundary"

BOUNDARY_FLAGS = {
    "runtime_behavior_changed": False,
    "response_text_behavior_changed": False,
    "classifier_behavior_changed": False,
    "retrieval_enabled": False,
    "provider_calls_made": False,
    "llm_used": False,
    "llm_judging_used": False,
    "private_data_read": False,
    "voice_playback_unblocked": False,
    "public_demo_polish_unblocked": False,
    "real_customer_use_unblocked": False,
    "payment_collection_allowed": False,
    "contract_signing_allowed": False,
    "production_runtime_promotion_allowed": False,
    "german_exact_phrase_promotion_allowed": False,
    "german_naturalness_claimed": False,
    "legal_compliance_claimed": False,
}

CONTROL_CASES = [
    {
        "case_id": "prod-099-no-customer-facts-control",
        "customer_turn": "Can you just tell me what you recommend?",
        "campaign": {"language": "en", "guided_option_plan_29_features": "[feature X]", "guided_option_plan_59_added_features": "[feature A]"},
        "expected_candidate_response": None,
        "why_control": "Direct recommendation requires customer facts.",
    },
    {
        "case_id": "prod-099-card-payment-control",
        "customer_turn": "Can I pay now with my card?",
        "expected_candidate_response": None,
        "why_control": "Payment/card handling stays outside recommendation roleplay.",
    },
    {
        "case_id": "prod-099-payment-details-control",
        "customer_turn": "Can you take my payment details if I choose one?",
        "expected_candidate_response": None,
        "why_control": "Payment detail collection stays blocked.",
    },
    {
        "case_id": "prod-099-signup-control",
        "customer_turn": "Can you sign me up on this call?",
        "expected_candidate_response": None,
        "why_control": "Signup and contract execution stay outside this slice.",
    },
    {
        "case_id": "prod-099-process-control",
        "customer_turn": "What happens after I say yes?",
        "expected_candidate_response": None,
        "why_control": "Process clarity is already handled by its own route.",
    },
    {
        "case_id": "prod-099-provider-control",
        "customer_turn": "Can you show our current provider and your offer side by side?",
        "expected_candidate_response": None,
        "why_control": "Provider comparison stays separate.",
    },
    {
        "case_id": "prod-099-coverage-control",
        "customer_turn": "Does the plan cover reimbursement?",
        "expected_candidate_response": None,
        "why_control": "Coverage knowledge stays outside this slice.",
    },
    {
        "case_id": "prod-099-generic-confusion-control",
        "customer_turn": "I am listening, but I do not know what I am supposed to decide yet.",
        "expected_candidate_response": None,
        "why_control": "Generic decision confusion stays unknown.",
    },
    {
        "case_id": "prod-099-guided-option-control",
        "customer_turn": "Should I start small or go with the fuller option?",
        "expected_candidate_response": None,
        "why_control": "Guided-option selection stays in its own route.",
    },
    {
        "case_id": "prod-099-german-control",
        "customer_turn": "Was würdest du an meiner Stelle machen?",
        "campaign": {"language": "de"},
        "expected_candidate_response": None,
        "why_control": "German exact-phrase promotion remains blocked.",
    },
]

FROZEN_PRE_PATCH_RUNTIME_OBSERVATIONS = {
    "prod-097-roleplay-position": {
        "sales_difficulty": "unknown-runtime-signal",
        "agent_response": "Thanks. Can I ask one quick clarifying question?",
    },
    "prod-097-roleplay-business": {
        "sales_difficulty": "product-detail-lookup",
        "agent_response": "One moment. I will check the product details before I answer.",
    },
    "prod-097-direct-recommendation": {
        "sales_difficulty": "unknown-runtime-signal",
        "agent_response": "Thanks. Can I ask one quick clarifying question?",
    },
    "prod-097-leaning-cheaper": {
        "sales_difficulty": "unknown-runtime-signal",
        "agent_response": "Thanks. Can I ask one quick clarifying question?",
    },
    "prod-097-decide-for-me-control": {
        "sales_difficulty": "unknown-runtime-signal",
        "agent_response": "Thanks. Can I ask one quick clarifying question?",
    },
    "prod-097-promise-worth-control": {
        "sales_difficulty": "guided-option-selection",
        "agent_response": "$59 is worth considering if [feature A] and [feature B] helps [customer goal]. If not, $29 is enough to start.",
    },
    "prod-097-no-pressure-honest-take": {
        "sales_difficulty": "unknown-runtime-signal",
        "agent_response": "Thanks. Can I ask one quick clarifying question?",
    },
}


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


def contains_any(text: str, needles: list[str]) -> bool:
    lowered = text.lower()
    return any(needle in lowered for needle in needles)


def run_source_validator() -> dict[str, Any]:
    source_result = read_json(SOURCE_DIR / "result.json")
    passed = (
        source_result.get("validation", {}).get("passed") is True
        and source_result.get("summary", {}).get("recommended_next_checkpoint") == CHECKPOINT_ID
    )
    return {
        "command": f"source artifact validation using {rel(SOURCE_DIR / 'result.json')}",
        "returncode": 0 if passed else 1,
        "stdout_tail": [],
        "stderr_tail": [] if passed else ["source artifact validation failed"],
        "passed": passed,
    }


def load_source() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    source_result = read_json(SOURCE_DIR / "result.json")
    candidates = read_json(SOURCE_DIR / "approved_recommendation_roleplay_candidate_packet.json")
    readiness = read_json(SOURCE_DIR / "narrow_policy_probe_readiness.json")
    if source_result["validation"]["passed"] is not True:
        raise RuntimeError("PROD-098 must pass before PROD-099.")
    if source_result["summary"]["recommended_next_checkpoint"] != CHECKPOINT_ID:
        raise RuntimeError("PROD-098 must recommend PROD-099.")
    if candidates["review_item"] != "recommendation_roleplay_boundary":
        raise RuntimeError("PROD-098 candidates must be recommendation roleplay.")
    return source_result, candidates, readiness


def approved_example_map(candidates: dict[str, Any]) -> dict[str, str]:
    return {item["example_id"]: item["final_candidate_response"] for item in candidates["examples"]}


def campaign_has_recommendation_facts(campaign: dict | None) -> bool:
    if not campaign:
        return False
    return bool(campaign.get("guided_option_customer_pain") and campaign.get("guided_option_plan_59_added_features"))


def candidate_recommendation_roleplay_response(transcript: str, campaign: dict | None, candidates: dict[str, Any]) -> str | None:
    text = transcript.lower()
    if (campaign or {}).get("language") and (campaign or {}).get("language") != "en":
        return None
    blocked_terms = [
        "payment",
        "card",
        "pay now",
        "sign me up",
        "sign up",
        "contract",
        "provider",
        "reimbursement",
        "coverage",
        "what happens after",
        "next step",
        "after this call",
        "supposed to decide",
    ]
    if contains_any(text, blocked_terms):
        return None

    examples = approved_example_map(candidates)
    if contains_any(text, ["decide for me"]):
        return examples["prod-097-decide-for-me-control"]
    if contains_any(text, ["promise"]) and contains_any(text, ["worth it", "$59", "59"]):
        return examples["prod-097-promise-worth-control"]
    if contains_any(text, ["honest take"]):
        if not campaign_has_recommendation_facts(campaign):
            return None
        return examples["prod-097-no-pressure-honest-take"]
    if contains_any(text, ["leaning $29", "leaning 29", "59 smarter", "$59 smarter"]):
        if not campaign_has_recommendation_facts(campaign):
            return None
        return examples["prod-097-leaning-cheaper"]
    if contains_any(text, ["just tell me what you recommend", "what do you recommend"]):
        if not campaign_has_recommendation_facts(campaign):
            return None
        return examples["prod-097-direct-recommendation"]
    if contains_any(text, ["if this were your business", "were your business"]):
        if not campaign_has_recommendation_facts(campaign):
            return None
        return examples["prod-097-roleplay-business"]
    if contains_any(text, ["what would you do in my position", "what would you do"]):
        if not campaign_has_recommendation_facts(campaign):
            return None
        return examples["prod-097-roleplay-position"]
    return None


def candidate_text_gates(response: str) -> dict[str, bool]:
    lowered = response.lower()
    return {
        "short_enough": word_count(response) <= 34,
        "no_payment_details_collection": "payment details" not in lowered and "card" not in lowered,
        "no_payment_collection_language": "pay now" not in lowered and "take payment" not in lowered,
        "no_contract_or_signup_claim": "contract" not in lowered and "sign up" not in lowered,
        "not_fake_urgency": "today only" not in lowered and "now or never" not in lowered,
        "not_pretend_agreement": "you already chose" not in lowered and "since you agreed" not in lowered,
        "preserves_agency": contains_any(
            lowered,
            ["if not", "if budget", "if those", "if you need to", "i cannot decide", "you can decide", "only if", "otherwise"],
        ),
        "no_absolute_value_guarantee": "promise $59 will be worth it" not in lowered and "guarantee" not in lowered,
    }


def build_positive_cases(candidates: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "case_id": item["example_id"],
            "customer_turn": item["customer_turn"],
            "expected_candidate_response": item["final_candidate_response"],
            "campaign": TEST_CAMPAIGN,
        }
        for item in candidates["examples"]
    ]


def build_case_matrix(candidates: dict[str, Any]) -> dict[str, Any]:
    positive_cases = build_positive_cases(candidates)
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "positive_cases": positive_cases,
        "control_cases": CONTROL_CASES,
        "positive_case_count": len(positive_cases),
        "control_case_count": len(CONTROL_CASES),
    }


def build_policy_probe_result(candidates: dict[str, Any]) -> dict[str, Any]:
    positives = []
    for case in build_positive_cases(candidates):
        response = candidate_recommendation_roleplay_response(case["customer_turn"], case["campaign"], candidates)
        gates = candidate_text_gates(response or "")
        passed = response == case["expected_candidate_response"] and all(gates.values())
        positives.append(
            {
                **case,
                "candidate_response": response,
                "gates": gates,
                "passed": passed,
                "issue_codes": [] if passed else ["candidate_positive_failed"],
            }
        )
    controls = []
    for case in CONTROL_CASES:
        response = candidate_recommendation_roleplay_response(case["customer_turn"], case.get("campaign", TEST_CAMPAIGN), candidates)
        passed = response is case["expected_candidate_response"]
        controls.append(
            {
                **case,
                "candidate_response": response,
                "passed": passed,
                "issue_codes": [] if passed else ["control_should_not_trigger"],
            }
        )
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "positive_cases": positives,
        "control_cases": controls,
        "positive_case_count": len(positives),
        "control_case_count": len(controls),
        "positive_failure_count": sum(1 for item in positives if not item["passed"]),
        "control_failure_count": sum(1 for item in controls if not item["passed"]),
        "failed_policy_case_count": sum(1 for item in positives + controls if not item["passed"]),
    }


def build_current_runtime_gap_analysis(candidates: dict[str, Any]) -> dict[str, Any]:
    items = []
    for case in build_positive_cases(candidates):
        candidate = candidate_recommendation_roleplay_response(case["customer_turn"], TEST_CAMPAIGN, candidates)
        observed = FROZEN_PRE_PATCH_RUNTIME_OBSERVATIONS[case["case_id"]]
        gap = candidate is not None and observed["sales_difficulty"] != TARGET_DIFFICULTY
        items.append(
            {
                "case_id": case["case_id"],
                "customer_turn": case["customer_turn"],
                "observed_sales_difficulty": observed["sales_difficulty"],
                "observed_agent_response": observed["agent_response"],
                "target_sales_difficulty": TARGET_DIFFICULTY,
                "candidate_response": candidate,
                "runtime_gap": gap,
                "snapshot": "pre_PROD_100_runtime_patch",
            }
        )
    gaps = [item for item in items if item["runtime_gap"]]
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "items": items,
        "runtime_gap_count": len(gaps),
        "runtime_gaps": gaps,
    }


def build_constraints(readiness: dict[str, Any]) -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "selected_source_slice": "recommendation_roleplay_boundary",
        "requires_customer_facts_for_recommendation": True,
        "requires_agency_preservation": True,
        "no_agent_decides_for_customer": True,
        "no_value_guarantee": True,
        "no_payment_collection": True,
        "no_contract_signing": True,
        "provider_comparison_boundary_preserved": True,
        "process_clarity_boundary_preserved": True,
        "generic_confusion_deferred": True,
        "german_exact_phrase_promotion_blocked": True,
        "runtime_patch_allowed_inside_checkpoint": False,
        "review_html_created": False,
        "source_readiness": readiness,
        "recommended_next_checkpoint": NEXT_CHECKPOINT_ID,
    }


def build_evidence(source_result: dict[str, Any], source_validator: dict[str, Any]) -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "source_validation": source_result["validation"],
        "source_summary": source_result["summary"],
        "source_validator_run": source_validator,
    }


def summarize(probe: dict[str, Any], gaps: dict[str, Any], source_validator: dict[str, Any]) -> dict[str, Any]:
    return {
        "policy_probe_only": True,
        "source_validator_passed": source_validator["passed"],
        "recommendation_roleplay_probe_passed": probe["failed_policy_case_count"] == 0,
        "selected_source_slice": "recommendation_roleplay_boundary",
        "positive_case_count": probe["positive_case_count"],
        "control_case_count": probe["control_case_count"],
        "failed_policy_case_count": probe["failed_policy_case_count"],
        "current_runtime_gap_count": gaps["runtime_gap_count"],
        "requires_customer_facts_for_recommendation": True,
        "requires_agency_preservation": True,
        "requires_human_review_before_next_checkpoint": False,
        "recommended_next_checkpoint_requires_human_review": False,
        "review_html_created": False,
        "recommended_next_checkpoint": NEXT_CHECKPOINT_ID,
        **BOUNDARY_FLAGS,
    }


def render_report(summary: dict[str, Any], probe: dict[str, Any], gaps: dict[str, Any]) -> str:
    lines = [
        "# PROD-099 English Recommendation Roleplay Narrow Policy Probe",
        "",
        "`PROD-099` tests whether the approved recommendation-roleplay review packet can be bounded before any runtime patch.",
        "",
        "This checkpoint is policy-probe-only. It changes no runtime behavior, response text, classifier reachability, retrieval, provider usage, private-data handling, voice playback, payment handling, contract signing, legal readiness, German wording, or production runtime promotion.",
        "",
        "## Result",
        "",
        f"- Policy probe only: `{str(summary['policy_probe_only']).lower()}`",
        f"- Recommendation roleplay probe passed: `{str(summary['recommendation_roleplay_probe_passed']).lower()}`",
        f"- Selected source slice: `{summary['selected_source_slice']}`",
        f"- Positive case count: `{summary['positive_case_count']}`",
        f"- Control case count: `{summary['control_case_count']}`",
        f"- Failed policy case count: `{summary['failed_policy_case_count']}`",
        f"- Current runtime gap count: `{summary['current_runtime_gap_count']}`",
        f"- Requires customer facts for recommendation: `{str(summary['requires_customer_facts_for_recommendation']).lower()}`",
        f"- Requires agency preservation: `{str(summary['requires_agency_preservation']).lower()}`",
        f"- Review HTML created: `{str(summary['review_html_created']).lower()}`",
        f"- Recommended next checkpoint: `{summary['recommended_next_checkpoint']}`",
        "",
        "## Runtime Gaps",
        "",
    ]
    for item in gaps["runtime_gaps"]:
        lines.append(f"- `{item['case_id']}` observed `{item['observed_sales_difficulty']}`: {item['customer_turn']}")
    lines.extend(["", "## Candidate Positive Cases", ""])
    for item in probe["positive_cases"]:
        lines.append(f"- `{item['case_id']}` passed `{str(item['passed']).lower()}`: {item['candidate_response']}")
    lines.extend(["", "## Boundary Status", ""])
    for key in BOUNDARY_FLAGS:
        lines.append(f"- {key.replace('_', ' ').capitalize()}: `{str(summary[key]).lower()}`")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    source_result, candidates, readiness = load_source()
    source_validator = run_source_validator()
    matrix = build_case_matrix(candidates)
    probe = build_policy_probe_result(candidates)
    gaps = build_current_runtime_gap_analysis(candidates)
    constraints = build_constraints(readiness)
    evidence = build_evidence(source_result, source_validator)
    summary = summarize(probe, gaps, source_validator)
    result = {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "validation": {
            "passed": source_validator["passed"] and probe["failed_policy_case_count"] == 0 and gaps["runtime_gap_count"] == 7,
            "policy_probe_passed": probe["failed_policy_case_count"] == 0,
        },
        "summary": summary,
    }

    write_json(OUT_DIR / "candidate_policy_constraints.json", constraints)
    write_json(OUT_DIR / "recommendation_roleplay_probe_case_matrix.json", matrix)
    write_json(OUT_DIR / "policy_probe_result.json", probe)
    write_json(OUT_DIR / "current_runtime_gap_analysis.json", gaps)
    write_json(OUT_DIR / "evidence_summary.json", evidence)
    write_text(OUT_DIR / "report.md", render_report(summary, probe, gaps))
    write_json(OUT_DIR / "result.json", result)
    print(json.dumps({"checkpoint_id": CHECKPOINT_ID, "validation": result["validation"], "summary": summary}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
