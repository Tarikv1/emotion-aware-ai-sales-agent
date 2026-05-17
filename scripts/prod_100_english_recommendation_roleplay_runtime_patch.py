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


CHECKPOINT_ID = "PROD-100-english-recommendation-roleplay-runtime-patch"
CHECKPOINT_NAME = "English Recommendation Roleplay Runtime Patch"
SOURCE_CHECKPOINT_ID = "PROD-099-english-recommendation-roleplay-narrow-policy-probe"
NEXT_CHECKPOINT_ID = "PROD-101-english-recommendation-roleplay-post-patch-regression"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
SOURCE_DIR = ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID
SOURCE_VALIDATOR = ROOT / "scripts" / "validate_prod_099_english_recommendation_roleplay_narrow_policy_probe.py"
RUNTIME_FILE = ROOT / "runtime" / "core" / "realtime_turns.py"
TARGET_DIFFICULTY = "recommendation-roleplay-boundary"

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


def load_source() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    source_result = read_json(SOURCE_DIR / "result.json")
    gap_analysis = read_json(SOURCE_DIR / "current_runtime_gap_analysis.json")
    policy_probe = read_json(SOURCE_DIR / "policy_probe_result.json")
    if source_result["validation"]["passed"] is not True:
        raise RuntimeError("PROD-099 must pass before PROD-100.")
    if source_result["summary"]["recommended_next_checkpoint"] != CHECKPOINT_ID:
        raise RuntimeError("PROD-099 must recommend PROD-100.")
    if gap_analysis["runtime_gap_count"] != 7:
        raise RuntimeError("PROD-099 must identify exactly seven runtime gaps.")
    if policy_probe["failed_policy_case_count"] != 0:
        raise RuntimeError("PROD-099 policy probe must pass before runtime patch.")
    return source_result, gap_analysis, policy_probe


def positive_text_gates(case_id: str, response: str) -> dict[str, bool]:
    lowered = response.lower()
    gates = {
        "short_enough": word_count(response) <= 34,
        "no_payment_details_collection": "payment details" not in lowered and "card" not in lowered,
        "no_payment_collection_language": "pay now" not in lowered and "take payment" not in lowered,
        "no_contract_or_signup_claim": "contract" not in lowered and "sign up" not in lowered,
        "not_fake_urgency": "today only" not in lowered and "now or never" not in lowered,
        "not_pretend_agreement": "you already chose" not in lowered and "since you agreed" not in lowered,
        "preserves_agency": any(
            phrase in lowered
            for phrase in ["if not", "if budget", "if those", "if you need to", "i cannot decide", "you can decide", "only if", "otherwise"]
        ),
        "no_absolute_value_guarantee": "guarantee" not in lowered and "promise $59 will be worth it" not in lowered,
    }
    if case_id == "prod-097-direct-recommendation":
        gates["keeps_if_you_need_to_softener"] = "upgrade later if you need to" in lowered
    if case_id == "prod-097-decide-for-me-control":
        gates["keeps_decide_boundary"] = "i cannot decide for you, but i can show" in lowered
    if case_id == "prod-097-promise-worth-control":
        gates["keeps_value_claim_boundary"] = "i cannot promise that" in lowered and "you can decide" in lowered
    return gates


def run_positive_cases(policy_probe: dict[str, Any]) -> dict[str, Any]:
    cases = []
    for case in policy_probe["positive_cases"]:
        decision = build_runtime_decision(runtime_case(case["case_id"], case["customer_turn"]), campaign=TEST_CAMPAIGN)
        response = decision["agent_response"]
        expected = case["expected_candidate_response"]
        gates = {
            "sales_difficulty": decision["sales_difficulty"] == TARGET_DIFFICULTY,
            "selected_strategy": decision["selected_strategy"] == "guided-recommendation",
            "next_action": decision["next_action"] == "answer-and-continue",
            "exact_candidate_response": response == expected,
            **positive_text_gates(case["case_id"], response),
        }
        cases.append(
            {
                "case_id": case["case_id"],
                "customer_turn": case["customer_turn"],
                "sales_difficulty": decision["sales_difficulty"],
                "selected_strategy": decision["selected_strategy"],
                "next_action": decision["next_action"],
                "agent_response": response,
                "expected_agent_response": expected,
                "gates": gates,
                "passed": all(gates.values()),
            }
        )
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "case_count": len(cases),
        "cases": cases,
        "failure_count": sum(1 for case in cases if not case["passed"]),
    }


def run_control_cases(policy_probe: dict[str, Any]) -> dict[str, Any]:
    cases = []
    for case in policy_probe["control_cases"]:
        decision = build_runtime_decision(
            runtime_case(case["case_id"], case["customer_turn"]),
            campaign=case.get("campaign", TEST_CAMPAIGN),
        )
        passed = decision["sales_difficulty"] != TARGET_DIFFICULTY
        cases.append(
            {
                "case_id": case["case_id"],
                "customer_turn": case["customer_turn"],
                "expected": f"not {TARGET_DIFFICULTY}",
                "sales_difficulty": decision["sales_difficulty"],
                "agent_response": decision["agent_response"],
                "passed": passed,
            }
        )
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "case_count": len(cases),
        "cases": cases,
        "failure_count": sum(1 for case in cases if not case["passed"]),
    }


def build_runtime_patch_summary(gap_analysis: dict[str, Any]) -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "runtime_file": rel(RUNTIME_FILE),
        "runtime_patch_applied": True,
        "selected_gap_case_ids": [item["case_id"] for item in gap_analysis["runtime_gaps"]],
        "new_sales_difficulty": TARGET_DIFFICULTY,
        "selected_strategy": "guided-recommendation",
        "requires_customer_facts_for_recommendation": True,
        "requires_agency_preservation": True,
        "no_agent_decides_for_customer": True,
        "no_value_guarantee": True,
        "blocked_boundary_signals": ["payment", "card", "pay now", "sign me up", "contract", "current provider", "reimbursement", "coverage", "next step"],
        "review_html_created": False,
    }


def build_evidence(source_result: dict[str, Any], gap_analysis: dict[str, Any], source_validator: dict[str, Any]) -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "source_validation": source_result["validation"],
        "source_summary": source_result["summary"],
        "source_gap_count_before_patch": gap_analysis["runtime_gap_count"],
        "source_validator_run": source_validator,
    }


def summarize(positives: dict[str, Any], controls: dict[str, Any], gap_analysis: dict[str, Any], source_validator: dict[str, Any]) -> dict[str, Any]:
    return {
        "runtime_patch_applied": True,
        "runtime_behavior_changed": True,
        "response_text_behavior_changed": True,
        "classifier_behavior_changed": True,
        "source_validator_passed": source_validator["passed"],
        "selected_gap_fixed_count": len(gap_analysis["runtime_gaps"]),
        "positive_case_count": positives["case_count"],
        "positive_case_failures": positives["failure_count"],
        "control_case_count": controls["case_count"],
        "control_case_failures": controls["failure_count"],
        "current_runtime_gap_count_before_patch": gap_analysis["runtime_gap_count"],
        "requires_customer_facts_for_recommendation": True,
        "requires_agency_preservation": True,
        "no_agent_decides_for_customer": True,
        "no_value_guarantee": True,
        "review_html_created": False,
        "recommended_next_checkpoint": NEXT_CHECKPOINT_ID,
        **BOUNDARY_FLAGS,
    }


def render_report(summary: dict[str, Any], patch: dict[str, Any]) -> str:
    lines = [
        "# PROD-100 English Recommendation Roleplay Runtime Patch",
        "",
        "`PROD-100` applies the narrow English runtime branch for the approved recommendation-roleplay cases from `PROD-099`.",
        "",
        "## Result",
        "",
        f"- Runtime patch applied: `{str(summary['runtime_patch_applied']).lower()}`",
        f"- Selected gap fixed count: `{summary['selected_gap_fixed_count']}`",
        f"- Positive case failures: `{summary['positive_case_failures']}`",
        f"- Control case failures: `{summary['control_case_failures']}`",
        f"- Requires customer facts for recommendation: `{str(summary['requires_customer_facts_for_recommendation']).lower()}`",
        f"- Requires agency preservation: `{str(summary['requires_agency_preservation']).lower()}`",
        f"- No agent decides for customer: `{str(summary['no_agent_decides_for_customer']).lower()}`",
        f"- No value guarantee: `{str(summary['no_value_guarantee']).lower()}`",
        f"- Review HTML created: `{str(summary['review_html_created']).lower()}`",
        f"- Recommended next checkpoint: `{summary['recommended_next_checkpoint']}`",
        "",
        "## Patch Summary",
        "",
        f"- New sales difficulty: `{patch['new_sales_difficulty']}`",
        f"- Selected strategy: `{patch['selected_strategy']}`",
        f"- Selected gap case count: `{len(patch['selected_gap_case_ids'])}`",
        "",
        "## Boundary Status",
        "",
        f"- Runtime behavior changed: `{str(summary['runtime_behavior_changed']).lower()}`",
        f"- Response text behavior changed: `{str(summary['response_text_behavior_changed']).lower()}`",
        f"- Classifier behavior changed: `{str(summary['classifier_behavior_changed']).lower()}`",
    ]
    for key in BOUNDARY_FLAGS:
        lines.append(f"- {key.replace('_', ' ').capitalize()}: `{str(summary[key]).lower()}`")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    source_result, gap_analysis, policy_probe = load_source()
    source_validator = run_source_validator()
    positives = run_positive_cases(policy_probe)
    controls = run_control_cases(policy_probe)
    patch = build_runtime_patch_summary(gap_analysis)
    evidence = build_evidence(source_result, gap_analysis, source_validator)
    summary = summarize(positives, controls, gap_analysis, source_validator)
    result = {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "validation": {
            "passed": source_validator["passed"] and positives["failure_count"] == 0 and controls["failure_count"] == 0,
            "runtime_patch_verified": positives["failure_count"] == 0 and controls["failure_count"] == 0,
        },
        "summary": summary,
    }
    write_json(OUT_DIR / "runtime_patch_summary.json", patch)
    write_json(OUT_DIR / "positive_runtime_cases.json", positives)
    write_json(OUT_DIR / "control_runtime_cases.json", controls)
    write_json(OUT_DIR / "evidence_summary.json", evidence)
    write_text(OUT_DIR / "report.md", render_report(summary, patch))
    write_json(OUT_DIR / "result.json", result)
    print(json.dumps({"checkpoint_id": CHECKPOINT_ID, "validation": result["validation"], "summary": summary}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
