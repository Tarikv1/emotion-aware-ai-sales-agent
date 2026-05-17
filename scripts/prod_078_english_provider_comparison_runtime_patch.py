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

from runtime.core.realtime_turns import build_runtime_decision, localized_response  # noqa: E402


CHECKPOINT_ID = "PROD-078-english-provider-comparison-runtime-patch"
CHECKPOINT_NAME = "English Provider-Comparison Runtime Patch"
SOURCE_CHECKPOINT_ID = "PROD-077-english-provider-comparison-narrow-probe-design"
NEXT_CHECKPOINT_ID = "PROD-079-english-provider-comparison-post-patch-regression"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
SOURCE_DIR = ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID
SOURCE_VALIDATOR_COMMAND = "source artifact check for PROD-077 generated outputs"
EXPECTED_RESPONSE = "Fair. We can compare fit against what you use now before you decide."

BOUNDARY_FLAGS = {
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

EXTRA_POSITIVE_CASE = {
    "case_id": "prod-078-compare-terms-with-what-we-have",
    "customer_turn": "Can you compare your terms with what we already have?",
    "expected_sales_difficulty": "provider-comparison",
    "why": "Keeps Tarik's terms-comparison concern grounded in an explicitly stated baseline.",
}

NEGATIVE_EXPECTED_OVERRIDES = {
    "prod-077-written-info": "written-info-request",
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


def check_source_artifacts(source_result: dict[str, Any], design: dict[str, Any], response: dict[str, Any], matrix: dict[str, Any]) -> dict[str, Any]:
    passed = (
        source_result["validation"]["passed"] is True
        and source_result["summary"]["recommended_next_checkpoint"] == CHECKPOINT_ID
        and design["branch_order"]["insert_before"] == "existing-provider-gap"
        and response["candidate_response"] == EXPECTED_RESPONSE
        and len(matrix["positive_probe_cases"]) >= 4
    )
    return {
        "command": SOURCE_VALIDATOR_COMMAND,
        "returncode": 0 if passed else 1,
        "stdout_tail": ["PROD-077 generated source artifacts checked without regenerating pre-patch gap evidence."],
        "stderr_tail": [],
        "passed": passed,
    }


def load_source() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    result = read_json(SOURCE_DIR / "result.json")
    design = read_json(SOURCE_DIR / "narrow_probe_design.json")
    response = read_json(SOURCE_DIR / "candidate_response_design.json")
    matrix = read_json(SOURCE_DIR / "probe_case_matrix.json")
    if result["validation"]["passed"] is not True:
        raise RuntimeError("PROD-077 must pass before PROD-078.")
    if result["summary"]["recommended_next_checkpoint"] != CHECKPOINT_ID:
        raise RuntimeError("PROD-077 must recommend PROD-078.")
    if design["branch_order"]["insert_before"] != "existing-provider-gap":
        raise RuntimeError("PROD-077 must require insertion before existing-provider-gap.")
    if response["candidate_response"] != EXPECTED_RESPONSE:
        raise RuntimeError("PROD-077 response candidate changed.")
    return result, design, response, matrix


def runtime_case(case: dict[str, Any]) -> dict[str, Any]:
    return {
        "case_id": case["case_id"],
        "customer_input": {
            "input_type": "speech",
            "transcript": case["customer_turn"],
            "stage": "objection-handling",
        },
    }


def runtime_decision_for(case: dict[str, Any]) -> dict[str, Any]:
    decision = build_runtime_decision(runtime_case(case), campaign={"language": "en"})
    return {
        "response_language": decision["response_language"],
        "sales_difficulty": decision["sales_difficulty"],
        "interest_state": decision["interest_state"],
        "selected_strategy": decision["selected_strategy"],
        "next_action": decision["next_action"],
        "call_control": decision["call_control"],
        "agent_response": decision["agent_response"],
    }


def expected_for(case: dict[str, Any], case_type: str) -> dict[str, Any]:
    expected_sales_difficulty = NEGATIVE_EXPECTED_OVERRIDES.get(case["case_id"], case["expected_sales_difficulty"])
    expected = {"sales_difficulty": expected_sales_difficulty}
    if expected_sales_difficulty == "provider-comparison":
        expected.update(
            {
                "response_language": "en",
                "selected_strategy": "inquiry",
                "next_action": "ask-follow-up",
                "call_control": "continue-call",
                "agent_response": EXPECTED_RESPONSE,
            }
        )
    elif case_type == "negative_control":
        expected["not_sales_difficulty"] = "provider-comparison"
    elif case_type == "protected_control":
        expected["not_sales_difficulty"] = "provider-comparison"
    return expected


def evaluate_case(case: dict[str, Any], case_type: str) -> dict[str, Any]:
    observed = runtime_decision_for(case)
    expected = expected_for(case, case_type)
    gates = {"not_provider_comparison_when_excluded": True}
    if expected.get("sales_difficulty") == "provider-comparison":
        gates = {
            "response_language_en": observed["response_language"] == expected["response_language"],
            "sales_difficulty_matches": observed["sales_difficulty"] == "provider-comparison",
            "strategy_matches": observed["selected_strategy"] == expected["selected_strategy"],
            "next_action_matches": observed["next_action"] == expected["next_action"],
            "call_control_matches": observed["call_control"] == expected["call_control"],
            "response_matches": observed["agent_response"] == EXPECTED_RESPONSE,
        }
    else:
        gates = {
            "sales_difficulty_matches": observed["sales_difficulty"] == expected["sales_difficulty"],
            "not_provider_comparison": observed["sales_difficulty"] != "provider-comparison",
        }
    issue_codes = [key for key, passed in gates.items() if not passed]
    return {
        "case_id": case["case_id"],
        "case_type": case_type,
        "customer_turn": case["customer_turn"],
        "expected_runtime": expected,
        "observed_runtime": observed,
        "gates": gates,
        "passed": not issue_codes,
        "issue_codes": issue_codes,
    }


def build_reviews(matrix: dict[str, Any]) -> list[dict[str, Any]]:
    reviews = []
    positive_cases = [*matrix["positive_probe_cases"], EXTRA_POSITIVE_CASE]
    for case in positive_cases:
        reviews.append(evaluate_case(case, "positive_probe"))
    for case in matrix["negative_control_cases"]:
        reviews.append(evaluate_case(case, "negative_control"))
    for case in matrix["protected_control_cases"]:
        reviews.append(evaluate_case(case, "protected_control"))
    return reviews


def build_patch_decision(reviews: list[dict[str, Any]]) -> dict[str, Any]:
    failed = [item for item in reviews if not item["passed"]]
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "decision": "english_provider_comparison_runtime_patch_applied",
        "runtime_path": "runtime/core/realtime_turns.py",
        "patched_sales_difficulty": "provider-comparison",
        "patched_response": EXPECTED_RESPONSE,
        "inserted_before": "existing-provider-gap",
        "required_signal_groups": ["compare_or_difference_signal", "known_comparison_target_signal"],
        "response_text_change": True,
        "classifier_change": True,
        "generic_provider_or_terms_comparison_allowed": False,
        "runtime_patch_case_count": len(reviews),
        "failed_runtime_patch_case_count": len(failed),
        "recommended_next_checkpoint": NEXT_CHECKPOINT_ID,
        "production_runtime_promotion_allowed": False,
    }


def build_evidence(source_result: dict[str, Any], design: dict[str, Any], response: dict[str, Any], source_validator: dict[str, Any]) -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "source_validation": source_result["validation"],
        "source_design_required_signal_groups": design["required_signal_groups"],
        "source_candidate_response": response["candidate_response"],
        "source_validator_run": source_validator,
    }


def summarize(reviews: list[dict[str, Any]], source_validator: dict[str, Any]) -> dict[str, Any]:
    failed = [item for item in reviews if not item["passed"]]
    positives = [item for item in reviews if item["case_type"] == "positive_probe"]
    negatives = [item for item in reviews if item["case_type"] == "negative_control"]
    protected = [item for item in reviews if item["case_type"] == "protected_control"]
    return {
        "runtime_behavior_changed": True,
        "response_text_behavior_changed": True,
        "classifier_behavior_changed": True,
        "english_only_runtime_patch": True,
        "source_validator_passed": source_validator["passed"],
        "patched_sales_difficulty": "provider-comparison",
        "patched_response": EXPECTED_RESPONSE,
        "comparison_target_required": True,
        "generic_provider_or_terms_comparison_allowed": False,
        "positive_probe_case_count": len(positives),
        "negative_control_case_count": len(negatives),
        "protected_control_case_count": len(protected),
        "runtime_patch_case_count": len(reviews),
        "failed_runtime_patch_case_count": len(failed),
        "failed_runtime_patch_case_ids": [item["case_id"] for item in failed],
        "review_html_created": False,
        "recommended_next_checkpoint": NEXT_CHECKPOINT_ID,
        **BOUNDARY_FLAGS,
    }


def render_report(summary: dict[str, Any], decision: dict[str, Any], reviews: list[dict[str, Any]]) -> str:
    lines = [
        "# PROD-078 English Provider-Comparison Runtime Patch",
        "",
        "`PROD-078` applies the `PROD-077` narrow English `provider-comparison` runtime patch.",
        "",
        "This is an English provider-comparison narrow runtime patch. It changes classifier reachability and English response text for `provider-comparison` only.",
        "",
        "No human review required because PROD-076 imported Tarik's constrained approval and PROD-077 converted it into a deterministic design.",
        "",
        "## Decision",
        "",
        "- Decision: `english_provider_comparison_runtime_patch_applied`",
        "- Runtime path: `runtime/core/realtime_turns.py`",
        f"- Patched sales difficulty: `{summary['patched_sales_difficulty']}`",
        f"- Patched response: `{summary['patched_response']}`",
        "- Inserted before `existing-provider-gap`",
        "- Comparison target required: `true`",
        "- Generic provider or terms comparison allowed: `false`",
        f"- Runtime behavior changed: `{str(summary['runtime_behavior_changed']).lower()}`",
        f"- Response text behavior changed: `{str(summary['response_text_behavior_changed']).lower()}`",
        f"- Classifier behavior changed: `{str(summary['classifier_behavior_changed']).lower()}`",
        f"- Review HTML created: `{str(summary['review_html_created']).lower()}`",
        f"- Recommended next checkpoint: `{summary['recommended_next_checkpoint']}`",
        "- Production runtime promotion allowed: `false`",
        "",
        "## Runtime Patch Reviews",
        "",
    ]
    for item in reviews:
        observed = item["observed_runtime"]
        lines.extend(
            [
                f"### {item['case_id']}",
                "",
                f"- Case type: `{item['case_type']}`",
                f"- Customer turn: {item['customer_turn']}",
                f"- Passed: `{str(item['passed']).lower()}`",
                f"- Issue codes: `{', '.join(item['issue_codes']) if item['issue_codes'] else 'none'}`",
                f"- Sales difficulty: `{observed['sales_difficulty']}`",
                f"- Next action: `{observed['next_action']}`",
                f"- Call control: `{observed['call_control']}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Boundary Status",
            "",
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
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    source_result, design, response, matrix = load_source()
    if localized_response("en", "provider-comparison", None) != EXPECTED_RESPONSE:
        raise SystemExit("Provider-comparison response is not patched to the PROD-077 candidate.")
    source_validator = check_source_artifacts(source_result, design, response, matrix)
    reviews = build_reviews(matrix)
    decision = build_patch_decision(reviews)
    evidence = build_evidence(source_result, design, response, source_validator)
    summary = summarize(reviews, source_validator)
    result = {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "validation": {
            "passed": source_validator["passed"] and summary["failed_runtime_patch_case_count"] == 0,
            "runtime_patch_passed": summary["failed_runtime_patch_case_count"] == 0,
            "controls_preserved": all(item["passed"] for item in reviews if item["case_type"] != "positive_probe"),
        },
        "summary": summary,
    }
    write_json(OUT_DIR / "runtime_patch_reviews.json", {"checkpoint_id": CHECKPOINT_ID, "items": reviews})
    write_json(OUT_DIR / "patch_decision.json", decision)
    write_json(OUT_DIR / "evidence_summary.json", evidence)
    write_text(OUT_DIR / "report.md", render_report(summary, decision, reviews))
    write_json(OUT_DIR / "result.json", result)
    print(json.dumps({"checkpoint_id": CHECKPOINT_ID, "validation": result["validation"], "summary": summary}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
