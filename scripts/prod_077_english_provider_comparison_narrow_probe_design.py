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

from runtime.core.realtime_turns import build_runtime_decision

CHECKPOINT_ID = "PROD-077-english-provider-comparison-narrow-probe-design"
CHECKPOINT_NAME = "English Provider-Comparison Narrow Probe Design"
SOURCE_CHECKPOINT_ID = "PROD-076-english-provider-comparison-review-import"
NEXT_CHECKPOINT_ID = "PROD-078-english-provider-comparison-runtime-patch"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
SOURCE_DIR = ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID
SOURCE_VALIDATOR = ROOT / "scripts" / "validate_prod_076_english_provider_comparison_review_import.py"
SOURCE_VALIDATOR_COMMAND = "python scripts\\validate_prod_076_english_provider_comparison_review_import.py"
SOURCE_RESPONSE = "That is fair. We can compare fit and terms without pressure before you decide whether this is worth reviewing."
CANDIDATE_RESPONSE = "Fair. We can compare fit against what you use now before you decide."

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

POSITIVE_CASES = [
    {
        "case_id": "prod-077-current-provider-difference",
        "customer_turn": "How is this different from our current provider?",
        "expected_sales_difficulty": "provider-comparison",
        "why": "Contains a difference signal plus a current-provider comparison target.",
    },
    {
        "case_id": "prod-077-compare-current-use",
        "customer_turn": "Can you compare this with what we already use?",
        "expected_sales_difficulty": "provider-comparison",
        "why": "Contains a compare signal plus an existing-use comparison target.",
    },
    {
        "case_id": "prod-077-versus-current-setup",
        "customer_turn": "What would be different versus our current setup?",
        "expected_sales_difficulty": "provider-comparison",
        "why": "Contains a difference/versus signal plus current setup target.",
    },
    {
        "case_id": "prod-077-current-terms-comparison",
        "customer_turn": "How does this compare with our current terms?",
        "expected_sales_difficulty": "provider-comparison",
        "why": "Contains compare signal plus a current-terms target, without asking for invented terms.",
    },
]

NEGATIVE_CASES = [
    {
        "case_id": "prod-077-existing-provider-no-comparison",
        "customer_turn": "We already have a provider and I do not want to switch.",
        "expected_sales_difficulty": "existing-provider-gap",
        "why": "Has a provider target but no compare/difference request.",
    },
    {
        "case_id": "prod-077-generic-offer",
        "customer_turn": "What do you offer?",
        "expected_sales_difficulty": "unknown-runtime-signal",
        "why": "Generic product question without comparison target.",
    },
    {
        "case_id": "prod-077-better-generic",
        "customer_turn": "Is it better?",
        "expected_sales_difficulty": "unknown-runtime-signal",
        "why": "Comparative wording without a known comparison target.",
    },
    {
        "case_id": "prod-077-price-only",
        "customer_turn": "What does this cost?",
        "expected_sales_difficulty": "price-first-direct",
        "why": "Price question should stay in the price route.",
    },
    {
        "case_id": "prod-077-written-info",
        "customer_turn": "Just send me the details in writing.",
        "expected_sales_difficulty": "written-info-request",
        "why": "Written-info/email request is not a provider comparison.",
    },
]

PROTECTED_CASES = [
    {
        "case_id": "prod-077-payment-details",
        "customer_turn": "Can you take payment or card details if it is better?",
        "expected_sales_difficulty": "payment-safety-boundary",
        "why": "Payment safety outranks comparison language.",
    },
    {
        "case_id": "prod-077-sign-up",
        "customer_turn": "Can you sign me up if this is better?",
        "expected_sales_difficulty": "unknown-runtime-signal",
        "why": "Sign-up wording must not become provider-comparison or contract handling.",
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
    return len([part for part in text.replace(".", " ").split() if part])


def run_source_validator() -> dict[str, Any]:
    completed = subprocess.run(
        [sys.executable, str(SOURCE_VALIDATOR)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=300,
        check=False,
    )
    return {
        "command": SOURCE_VALIDATOR_COMMAND,
        "returncode": completed.returncode,
        "stdout_tail": completed.stdout.strip().splitlines()[-5:],
        "stderr_tail": completed.stderr.strip().splitlines()[-5:],
        "passed": completed.returncode == 0 and SOURCE_CHECKPOINT_ID in completed.stdout,
    }


def load_source() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    result = read_json(SOURCE_DIR / "result.json")
    requirements = read_json(SOURCE_DIR / "narrow_probe_requirements.json")
    constraints = read_json(SOURCE_DIR / "candidate_response_constraints.json")
    if result["validation"]["passed"] is not True:
        raise RuntimeError("PROD-076 must pass before PROD-077.")
    if result["summary"]["narrow_probe_approved"] is not True:
        raise RuntimeError("PROD-076 must approve a narrow probe.")
    if requirements["requirements"]["comparison_target_required"] is not True:
        raise RuntimeError("PROD-076 must require a comparison target.")
    if constraints["brevity_required"] is not True:
        raise RuntimeError("PROD-076 must require brevity.")
    return result, requirements, constraints


def runtime_case(case: dict[str, Any]) -> dict[str, Any]:
    return {
        "case_id": case["case_id"],
        "customer_input": {
            "input_type": "speech",
            "transcript": case["customer_turn"],
            "stage": "objection-handling",
        },
    }


def current_runtime(case: dict[str, Any]) -> dict[str, Any]:
    campaign = {"language": "en"}
    decision = build_runtime_decision(runtime_case(case), campaign=campaign)
    return {
        "case_id": case["case_id"],
        "customer_turn": case["customer_turn"],
        "expected_sales_difficulty": case["expected_sales_difficulty"],
        "current_sales_difficulty": decision["sales_difficulty"],
        "current_agent_response": decision["agent_response"],
        "currently_matches_expected": decision["sales_difficulty"] == case["expected_sales_difficulty"],
    }


def build_probe_design() -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "route_name": "provider-comparison",
        "design_status": "ready_for_narrow_runtime_patch_checkpoint",
        "required_signal_groups": [
            "compare_or_difference_signal",
            "known_comparison_target_signal",
        ],
        "compare_or_difference_signal": [
            "compare",
            "comparison",
            "different",
            "difference",
            "versus",
            "vs",
        ],
        "known_comparison_target_signal": [
            "current provider",
            "current setup",
            "what we already use",
            "current terms",
            "existing provider",
        ],
        "excluded_signal_groups": [
            "payment_or_card_details",
            "contract_or_signup",
            "price_only",
            "generic_product_question",
            "provider_exists_without_comparison_request",
        ],
        "branch_order": {
            "insert_before": "existing-provider-gap",
            "reason": "Current provider phrases are already consumed by existing-provider-gap before provider-comparison can be reached.",
        },
        "runtime_patch_allowed_inside_checkpoint": False,
        "broad_customer_move_classifier_patch_allowed": False,
    }


def build_candidate_response() -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "route_name": "provider-comparison",
        "source_response": SOURCE_RESPONSE,
        "candidate_response": CANDIDATE_RESPONSE,
        "source_response_word_count": word_count(SOURCE_RESPONSE),
        "candidate_response_word_count": word_count(CANDIDATE_RESPONSE),
        "approved_as_exact_response_text": False,
        "candidate_selected_for_probe": True,
        "why_this_candidate": "It removes generic terms comparison, stays grounded in what the customer already uses, and is shorter.",
        "runtime_response_changed": False,
    }


def build_case_matrix() -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "positive_probe_cases": POSITIVE_CASES,
        "negative_control_cases": NEGATIVE_CASES,
        "protected_control_cases": PROTECTED_CASES,
    }


def build_gap_analysis() -> dict[str, Any]:
    positive_results = [current_runtime(case) for case in POSITIVE_CASES]
    negative_results = [current_runtime(case) for case in NEGATIVE_CASES]
    protected_results = [current_runtime(case) for case in PROTECTED_CASES]
    positive_gaps = [item for item in positive_results if item["current_sales_difficulty"] != "provider-comparison"]
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "current_runtime_positive_gap_count": len(positive_gaps),
        "positive_results": positive_results,
        "negative_results": negative_results,
        "protected_results": protected_results,
        "runtime_behavior_changed": False,
        "classifier_behavior_changed": False,
    }


def build_evidence(source_result: dict[str, Any], source_validator: dict[str, Any]) -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "source_validation": source_result["validation"],
        "source_summary": {
            "narrow_probe_approved": source_result["summary"]["narrow_probe_approved"],
            "exact_as_written_approval": source_result["summary"]["exact_as_written_approval"],
            "comparison_grounding_required": source_result["summary"]["comparison_grounding_required"],
            "brevity_constraint_required": source_result["summary"]["brevity_constraint_required"],
        },
        "source_validator_run": source_validator,
    }


def build_summary(source_validator: dict[str, Any], response: dict[str, Any], matrix: dict[str, Any], gaps: dict[str, Any]) -> dict[str, Any]:
    return {
        "probe_design_only": True,
        "source_validator_passed": source_validator["passed"],
        "selected_review_item": "provider-comparison",
        "comparison_target_required": True,
        "generic_provider_or_terms_comparison_allowed": False,
        "candidate_response": response["candidate_response"],
        "source_response_word_count": response["source_response_word_count"],
        "candidate_response_word_count": response["candidate_response_word_count"],
        "positive_probe_case_count": len(matrix["positive_probe_cases"]),
        "negative_control_case_count": len(matrix["negative_control_cases"]),
        "protected_control_case_count": len(matrix["protected_control_cases"]),
        "current_runtime_positive_gap_count": gaps["current_runtime_positive_gap_count"],
        "review_html_created": False,
        "recommended_next_checkpoint": NEXT_CHECKPOINT_ID,
        "recommended_next_checkpoint_requires_human_review": False,
        **BOUNDARY_FLAGS,
    }


def render_report(summary: dict[str, Any], design: dict[str, Any], response: dict[str, Any], gaps: dict[str, Any]) -> str:
    lines = [
        "# PROD-077 English Provider-Comparison Narrow Probe Design",
        "",
        "`PROD-077` designs the smallest safe English `provider-comparison` probe after Tarik's constrained approval.",
        "",
        "This is design-only. It does not patch runtime behavior, response text, classifier reachability, or retrieval.",
        "",
        "## Design",
        "",
        "- Route: `provider-comparison`",
        "- Required signal group: `compare_or_difference_signal`",
        "- Required signal group: `known_comparison_target_signal`",
        "- Comparison target required: `true`",
        "- Generic provider or terms comparison allowed: `false`",
        "- Insert before `existing-provider-gap` if a later runtime patch is opened",
        f"- Candidate response: {response['candidate_response']}",
        f"- Source response word count: `{response['source_response_word_count']}`",
        f"- Candidate response word count: `{response['candidate_response_word_count']}`",
        "",
        "## Current Runtime Gap",
        "",
        f"- Positive probe cases: `{summary['positive_probe_case_count']}`",
        f"- Current runtime positive gap count: `{gaps['current_runtime_positive_gap_count']}`",
        f"- Recommended next checkpoint: `{summary['recommended_next_checkpoint']}`",
        "",
        "## Exclusions",
        "",
    ]
    for item in design["excluded_signal_groups"]:
        lines.append(f"- `{item}`")
    lines.extend(
        [
            "",
            "## Boundary Status",
            "",
            "- Runtime behavior changed: `false`",
            "- Response text behavior changed: `false`",
            "- Classifier behavior changed: `false`",
            "- Retrieval enabled: `false`",
            "- Provider calls made: `false`",
            "- LLM used: `false`",
            "- LLM judging used: `false`",
            "- Private data read: `false`",
            "- Voice playback unblocked: `false`",
            "- Public demo polish unblocked: `false`",
            "- Real customer use unblocked: `false`",
            "- Payment collection allowed: `false`",
            "- Contract signing allowed: `false`",
            "- Production runtime promotion allowed: `false`",
            "- German exact-phrase promotion allowed: `false`",
            "- German naturalness claimed: `false`",
            "- Legal compliance claimed: `false`",
            "- Review HTML created: `false`",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    source_result, _requirements, _constraints = load_source()
    source_validator = run_source_validator()
    design = build_probe_design()
    response = build_candidate_response()
    matrix = build_case_matrix()
    gaps = build_gap_analysis()
    evidence = build_evidence(source_result, source_validator)
    summary = build_summary(source_validator, response, matrix, gaps)
    result = {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "validation": {
            "passed": source_validator["passed"] and gaps["current_runtime_positive_gap_count"] >= 1,
            "probe_design_created": True,
        },
        "summary": summary,
        "outputs": {
            "result": rel(OUT_DIR / "result.json"),
            "report": rel(OUT_DIR / "report.md"),
            "narrow_probe_design": rel(OUT_DIR / "narrow_probe_design.json"),
            "candidate_response_design": rel(OUT_DIR / "candidate_response_design.json"),
            "probe_case_matrix": rel(OUT_DIR / "probe_case_matrix.json"),
            "current_runtime_gap_analysis": rel(OUT_DIR / "current_runtime_gap_analysis.json"),
            "evidence_summary": rel(OUT_DIR / "evidence_summary.json"),
        },
    }
    write_json(OUT_DIR / "narrow_probe_design.json", design)
    write_json(OUT_DIR / "candidate_response_design.json", response)
    write_json(OUT_DIR / "probe_case_matrix.json", matrix)
    write_json(OUT_DIR / "current_runtime_gap_analysis.json", gaps)
    write_json(OUT_DIR / "evidence_summary.json", evidence)
    write_text(OUT_DIR / "report.md", render_report(summary, design, response, gaps))
    write_json(OUT_DIR / "result.json", result)
    print(json.dumps({"checkpoint_id": CHECKPOINT_ID, "validation": result["validation"], "summary": summary}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
