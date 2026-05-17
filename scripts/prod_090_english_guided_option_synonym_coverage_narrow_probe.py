#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.core.realtime_turns import build_runtime_decision  # noqa: E402
from prod_087_english_guided_option_selection_runtime_patch import TEST_CAMPAIGN, runtime_case, word_count  # noqa: E402


CHECKPOINT_ID = "PROD-090-english-guided-option-synonym-coverage-narrow-probe"
CHECKPOINT_NAME = "English Guided Option Synonym Coverage Narrow Probe"
SOURCE_CHECKPOINT_ID = "PROD-089-english-customer-move-remaining-slice-selection-after-guided-option"
NEXT_CHECKPOINT_ID = "PROD-091-english-guided-option-synonym-coverage-runtime-patch"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
SOURCE_DIR = ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID
SOURCE_VALIDATOR = ROOT / "scripts" / "validate_prod_089_english_customer_move_remaining_slice_selection_after_guided_option.py"

STARTER_FEATURES = TEST_CAMPAIGN["guided_option_plan_29_features"]
EXPANDED_FEATURES = TEST_CAMPAIGN["guided_option_plan_59_added_features"]
CUSTOMER_GOAL = TEST_CAMPAIGN["guided_option_customer_goal"]

POSITIVE_CASES = [
    {
        "case_id": "prod-090-start-small-fuller",
        "customer_turn": "Should I start small or go with the fuller option?",
        "expected_contains": ["$29", "$59", STARTER_FEATURES, EXPANDED_FEATURES],
    },
    {
        "case_id": "prod-090-side-by-side",
        "customer_turn": "Can you show me both options side by side?",
        "expected_contains": ["$29", "$59", STARTER_FEATURES, EXPANDED_FEATURES],
    },
    {
        "case_id": "prod-090-safer-start-small",
        "customer_turn": "Would it be safer to start small first?",
        "expected_contains": ["$29", "$59", STARTER_FEATURES, EXPANDED_FEATURES],
    },
    {
        "case_id": "prod-090-fuller-worth-it",
        "customer_turn": "Is the fuller option worth it for what I need?",
        "expected_contains": ["$29", "$59", EXPANDED_FEATURES, CUSTOMER_GOAL],
    },
]

CONTROL_CASES = [
    {
        "case_id": "prod-090-advice-roleplay-control",
        "customer_turn": "What would you do in my position?",
        "expected_candidate_response": None,
        "why_control": "Advice-roleplay boundary stays deferred.",
    },
    {
        "case_id": "prod-090-process-after-yes-control",
        "customer_turn": "What happens after I say yes?",
        "expected_candidate_response": None,
        "why_control": "Post-yes process clarity stays deferred.",
    },
    {
        "case_id": "prod-090-generic-confusion-control",
        "customer_turn": "I am listening, but I do not know what I am supposed to decide yet.",
        "expected_candidate_response": None,
        "why_control": "Generic confusion stays a clarification fallback.",
    },
    {
        "case_id": "prod-090-card-payment-control",
        "customer_turn": "Can I pay now with my card?",
        "expected_candidate_response": None,
        "why_control": "Payment/card boundary must stay outside guided option synonyms.",
    },
    {
        "case_id": "prod-090-payment-details-control",
        "customer_turn": "Can you take my payment details if I choose one?",
        "expected_candidate_response": None,
        "why_control": "Payment-detail collection stays blocked.",
    },
    {
        "case_id": "prod-090-coverage-control",
        "customer_turn": "Does the plan cover reimbursement?",
        "expected_candidate_response": None,
        "why_control": "Coverage boundary stays outside guided option synonyms.",
    },
    {
        "case_id": "prod-090-provider-side-by-side-control",
        "customer_turn": "Can you show our current provider and your offer side by side?",
        "expected_candidate_response": None,
        "why_control": "Provider comparison requires a known comparison target and different route.",
    },
    {
        "case_id": "prod-090-autonomy-control",
        "customer_turn": "I need time to think. Do not rush.",
        "expected_candidate_response": None,
        "why_control": "Autonomy stays outside guided option synonyms.",
    },
    {
        "case_id": "prod-090-german-control",
        "customer_turn": "Soll ich klein anfangen oder die vollere Option nehmen?",
        "expected_candidate_response": None,
        "why_control": "German exact-phrase promotion remains blocked.",
    },
]

SELECTED_RUNTIME_GAP_CASES = [
    {
        "case_id": "prod-081-guided-option-02",
        "customer_turn": "Should I start small or go with the fuller option?",
    },
    {
        "case_id": "prod-081-plan-difference-02",
        "customer_turn": "Can you show me both options side by side?",
    },
]

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


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def contains_any(text: str, needles: list[str]) -> bool:
    lowered = text.lower()
    return any(needle in lowered for needle in needles)


def run_source_validator() -> dict[str, Any]:
    completed = subprocess.run(
        [sys.executable, str(SOURCE_VALIDATOR)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=360,
        check=False,
    )
    return {
        "command": f"python {rel(SOURCE_VALIDATOR)}",
        "returncode": completed.returncode,
        "stdout_tail": completed.stdout.strip().splitlines()[-8:],
        "stderr_tail": completed.stderr.strip().splitlines()[-8:],
        "passed": completed.returncode == 0,
    }


def load_source() -> dict[str, Any]:
    source_result = read_json(SOURCE_DIR / "result.json")
    if source_result["validation"]["passed"] is not True:
        raise RuntimeError("PROD-089 must pass before PROD-090.")
    if source_result["summary"]["recommended_next_checkpoint"] != CHECKPOINT_ID:
        raise RuntimeError("PROD-089 must recommend PROD-090.")
    return source_result


def build_case_file() -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "scope": "english_guided_option_synonym_coverage_narrow_policy_probe",
        "policy_probe_only": True,
        "selected_source_slice": "guided_option_synonym_coverage",
        "runtime_patch_allowed_inside_checkpoint": False,
        "review_html_created": False,
        "recommended_next_checkpoint": NEXT_CHECKPOINT_ID,
        "recommended_next_checkpoint_requires_human_review": False,
    }


def candidate_synonym_response(transcript: str) -> str | None:
    if contains_any(transcript, ["payment", "card", "provider", "reimbursement", "yes", "my position", "supposed to decide"]):
        return None
    if contains_any(transcript, ["worth it"]):
        return f"$59 is worth considering if {EXPANDED_FEATURES} helps {CUSTOMER_GOAL}. If not, $29 is enough to start."
    if contains_any(transcript, ["start small", "safer to start small", "fuller option"]):
        return f"I mean, start with $29 if {STARTER_FEATURES} is enough. If you want {EXPANDED_FEATURES} included, $59 fits better."
    if contains_any(transcript, ["side by side", "both options"]):
        return f"$29 covers {STARTER_FEATURES}. $59 includes that plus {EXPANDED_FEATURES}."
    return None


def candidate_text_gates(response: str, expected_contains: list[str]) -> dict[str, bool]:
    lowered = response.lower()
    return {
        "has_expected_content": all(part in response for part in expected_contains),
        "short_enough": word_count(response) <= 34,
        "no_company_domain_placeholder": "companyname.com" not in lowered,
        "no_payment_details_collection": "payment details" not in lowered and "card" not in lowered,
        "no_contract_or_signup_claim": "contract" not in lowered and "sign up" not in lowered,
        "not_fake_urgency": "today only" not in lowered and "now or never" not in lowered,
        "not_pretend_agreement": "you already chose" not in lowered and "since you agreed" not in lowered,
    }


def build_case_matrix() -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "positive_cases": POSITIVE_CASES,
        "control_cases": CONTROL_CASES,
        "positive_case_count": len(POSITIVE_CASES),
        "control_case_count": len(CONTROL_CASES),
    }


def build_policy_probe_result() -> dict[str, Any]:
    positives = []
    for case in POSITIVE_CASES:
        response = candidate_synonym_response(case["customer_turn"])
        gates = candidate_text_gates(response or "", case["expected_contains"])
        passed = response is not None and all(gates.values())
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
        response = candidate_synonym_response(case["customer_turn"])
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


def build_current_runtime_gap_analysis() -> dict[str, Any]:
    source_probe_results = read_json(SOURCE_DIR / "post_guided_option_probe_results.json")
    source_selected_gaps = {
        item["case_id"]: item
        for item in source_probe_results["selected_gaps"]
    }
    items = []
    for case in SELECTED_RUNTIME_GAP_CASES:
        source_gap = source_selected_gaps[case["case_id"]]
        candidate = candidate_synonym_response(case["customer_turn"])
        gap = source_gap["observed_sales_difficulty"] != "guided-option-selection" and candidate is not None
        items.append(
            {
                **case,
                "observed_sales_difficulty": source_gap["observed_sales_difficulty"],
                "observed_agent_response": source_gap["observed_agent_response"],
                "candidate_response": candidate,
                "runtime_gap": gap,
                "gap_source_checkpoint": SOURCE_CHECKPOINT_ID,
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


def build_constraints() -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "selected_source_slice": "guided_option_synonym_coverage",
        "plan_feature_matrix_required": True,
        "uses_existing_review_guardrails": True,
        "positive_synonym_targets": ["start small", "fuller option", "side by side"],
        "advice_roleplay_boundary_deferred": True,
        "process_clarity_deferred": True,
        "generic_confusion_deferred": True,
        "no_new_payment_path": True,
        "no_payment_collection": True,
        "no_contract_signing": True,
        "runtime_patch_allowed_inside_checkpoint": False,
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
        "policy_probe_passed": probe["failed_policy_case_count"] == 0,
        "selected_gap_count": 2,
        "positive_case_count": probe["positive_case_count"],
        "control_case_count": probe["control_case_count"],
        "failed_policy_case_count": probe["failed_policy_case_count"],
        "current_runtime_gap_count": gaps["runtime_gap_count"],
        "uses_existing_review_guardrails": True,
        "requires_human_review_before_next_checkpoint": False,
        "recommended_next_checkpoint_requires_human_review": False,
        "review_html_created": False,
        "recommended_next_checkpoint": NEXT_CHECKPOINT_ID,
        **BOUNDARY_FLAGS,
    }


def render_report(summary: dict[str, Any], probe: dict[str, Any], gaps: dict[str, Any]) -> str:
    lines = [
        "# PROD-090 English Guided Option Synonym Coverage Narrow Probe",
        "",
        "`PROD-090` probes whether two near-synonym guided-option gaps can use the existing reviewed guardrails before any runtime trigger expansion.",
        "",
        "This checkpoint is policy-probe-only. It changes no runtime behavior, response text, classifier reachability, retrieval, provider usage, private-data handling, voice playback, payment handling, contract signing, legal readiness, German wording, or production runtime promotion.",
        "",
        "## Result",
        "",
        f"- Policy probe only: `{str(summary['policy_probe_only']).lower()}`",
        f"- Policy probe passed: `{str(summary['policy_probe_passed']).lower()}`",
        f"- Selected gap count: `{summary['selected_gap_count']}`",
        f"- Positive case count: `{summary['positive_case_count']}`",
        f"- Control case count: `{summary['control_case_count']}`",
        f"- Failed policy case count: `{summary['failed_policy_case_count']}`",
        f"- Current runtime gap count: `{summary['current_runtime_gap_count']}`",
        f"- Requires human review before next checkpoint: `{str(summary['requires_human_review_before_next_checkpoint']).lower()}`",
        f"- Recommended next checkpoint requires human review: `{str(summary['recommended_next_checkpoint_requires_human_review']).lower()}`",
        f"- Review HTML created: `{str(summary['review_html_created']).lower()}`",
        f"- Recommended next checkpoint: `{summary['recommended_next_checkpoint']}`",
        "",
        "## Runtime Gaps",
        "",
    ]
    for item in gaps["runtime_gaps"]:
        lines.append(f"- `{item['case_id']}` -> `{item['observed_sales_difficulty']}`: {item['customer_turn']}")
    lines.extend(["", "## Candidate Positive Cases", ""])
    for item in probe["positive_cases"]:
        lines.append(f"- `{item['case_id']}` passed `{str(item['passed']).lower()}`: {item['candidate_response']}")
    lines.extend(["", "## Boundary Status", ""])
    for key in BOUNDARY_FLAGS:
        lines.append(f"- {key.replace('_', ' ').capitalize()}: `{str(summary[key]).lower()}`")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    source_result = load_source()
    source_validator = run_source_validator()
    matrix = build_case_matrix()
    probe = build_policy_probe_result()
    gaps = build_current_runtime_gap_analysis()
    constraints = build_constraints()
    evidence = build_evidence(source_result, source_validator)
    summary = summarize(probe, gaps, source_validator)
    result = {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "validation": {
            "passed": source_validator["passed"] and probe["failed_policy_case_count"] == 0 and gaps["runtime_gap_count"] == 2,
            "policy_probe_passed": probe["failed_policy_case_count"] == 0,
        },
        "summary": summary,
    }

    write_json(OUT_DIR / "candidate_policy_constraints.json", constraints)
    write_json(OUT_DIR / "synonym_probe_case_matrix.json", matrix)
    write_json(OUT_DIR / "policy_probe_result.json", probe)
    write_json(OUT_DIR / "current_runtime_gap_analysis.json", gaps)
    write_json(OUT_DIR / "evidence_summary.json", evidence)
    write_text(OUT_DIR / "report.md", render_report(summary, probe, gaps))
    write_json(OUT_DIR / "result.json", result)
    print(json.dumps({"checkpoint_id": CHECKPOINT_ID, "validation": result["validation"], "summary": summary}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
