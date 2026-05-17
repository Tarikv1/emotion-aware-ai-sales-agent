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


CHECKPOINT_ID = "PROD-101-english-recommendation-roleplay-post-patch-regression"
CHECKPOINT_NAME = "English Recommendation Roleplay Post-Patch Regression"
SOURCE_CHECKPOINT_ID = "PROD-100-english-recommendation-roleplay-runtime-patch"
NEXT_CHECKPOINT_ID = "PROD-102-english-customer-move-remaining-slice-selection-after-recommendation-roleplay"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
SOURCE_DIR = ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID
SOURCE_VALIDATOR = ROOT / "scripts" / "validate_prod_100_english_recommendation_roleplay_runtime_patch.py"
STABLE_ENGLISH_GUARD = ROOT / "scripts" / "validate_english_multi_turn_regression_guard.py"
TARGET_DIFFICULTY = "recommendation-roleplay-boundary"

ADDITIONAL_ADJACENT_CONTROLS = [
    {
        "case_id": "prod-101-product-detail-control",
        "customer_turn": "Which exact plan is included?",
        "campaign": TEST_CAMPAIGN,
        "expected_sales_difficulty": "product-detail-lookup",
    },
    {
        "case_id": "prod-101-provider-comparison-control",
        "customer_turn": "How is this different from our current provider?",
        "campaign": TEST_CAMPAIGN,
        "expected_sales_difficulty": "provider-comparison",
    },
    {
        "case_id": "prod-101-autonomy-control",
        "customer_turn": "I need time to think. Do not rush me into a plan.",
        "campaign": TEST_CAMPAIGN,
        "expected_sales_difficulty": "autonomy-check",
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


def run_validator(path: Path) -> dict[str, Any]:
    completed = subprocess.run(
        [sys.executable, str(path)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=360,
        check=False,
    )
    return {
        "command": f"python {rel(path)}",
        "returncode": completed.returncode,
        "stdout_tail": completed.stdout.strip().splitlines()[-8:],
        "stderr_tail": completed.stderr.strip().splitlines()[-8:],
        "passed": completed.returncode == 0,
    }


def load_source() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    result = read_json(SOURCE_DIR / "result.json")
    patch = read_json(SOURCE_DIR / "runtime_patch_summary.json")
    positives = read_json(SOURCE_DIR / "positive_runtime_cases.json")
    controls = read_json(SOURCE_DIR / "control_runtime_cases.json")
    if result["validation"]["passed"] is not True:
        raise RuntimeError("PROD-100 must pass before PROD-101.")
    if result["summary"]["recommended_next_checkpoint"] != CHECKPOINT_ID:
        raise RuntimeError("PROD-100 must recommend PROD-101.")
    if patch["runtime_patch_applied"] is not True:
        raise RuntimeError("PROD-100 runtime patch summary must show an applied patch.")
    return result, patch, positives, controls


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


def run_recommendation_roleplay_cases(source_positives: dict[str, Any]) -> dict[str, Any]:
    cases = []
    for case in source_positives["cases"]:
        decision = build_runtime_decision(runtime_case(case["case_id"], case["customer_turn"]), campaign=TEST_CAMPAIGN)
        response = decision["agent_response"]
        gates = {
            "sales_difficulty": decision["sales_difficulty"] == TARGET_DIFFICULTY,
            "selected_strategy": decision["selected_strategy"] == "guided-recommendation",
            "next_action": decision["next_action"] == "answer-and-continue",
            "exact_source_response": response == case["expected_agent_response"],
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
                "expected_agent_response": case["expected_agent_response"],
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


def campaign_for_source_control(case: dict[str, Any]) -> dict[str, Any]:
    if case["case_id"] == "prod-099-no-customer-facts-control":
        return {}
    if case["case_id"] == "prod-099-german-control":
        return {"language": "de"}
    return TEST_CAMPAIGN


def run_adjacent_control_cases(source_controls: dict[str, Any]) -> dict[str, Any]:
    cases = []
    for case in source_controls["cases"]:
        decision = build_runtime_decision(runtime_case(case["case_id"], case["customer_turn"]), campaign=campaign_for_source_control(case))
        gates = {
            "not_recommendation_roleplay": decision["sales_difficulty"] != TARGET_DIFFICULTY,
            "exact_source_sales_difficulty": decision["sales_difficulty"] == case["sales_difficulty"],
            "exact_source_response": decision["agent_response"] == case["agent_response"],
        }
        cases.append(
            {
                "case_id": case["case_id"],
                "customer_turn": case["customer_turn"],
                "expected": case["sales_difficulty"],
                "sales_difficulty": decision["sales_difficulty"],
                "agent_response": decision["agent_response"],
                "gates": gates,
                "passed": all(gates.values()),
            }
        )

    for case in ADDITIONAL_ADJACENT_CONTROLS:
        decision = build_runtime_decision(runtime_case(case["case_id"], case["customer_turn"]), campaign=case["campaign"])
        gates = {
            "expected_sales_difficulty": decision["sales_difficulty"] == case["expected_sales_difficulty"],
            "not_recommendation_roleplay": decision["sales_difficulty"] != TARGET_DIFFICULTY,
        }
        cases.append(
            {
                "case_id": case["case_id"],
                "customer_turn": case["customer_turn"],
                "expected": case["expected_sales_difficulty"],
                "sales_difficulty": decision["sales_difficulty"],
                "agent_response": decision["agent_response"],
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


def build_evidence(source_result: dict[str, Any], patch: dict[str, Any], source_validator: dict[str, Any], stable_guard: dict[str, Any]) -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "source_validation": source_result["validation"],
        "source_summary": source_result["summary"],
        "source_runtime_patch_summary": patch,
        "source_validator_run": source_validator,
        "stable_english_guard_run": stable_guard,
    }


def summarize(recommendation: dict[str, Any], controls: dict[str, Any], source_validator: dict[str, Any], stable_guard: dict[str, Any]) -> dict[str, Any]:
    return {
        "post_patch_regression_only": True,
        "source_validator_passed": source_validator["passed"],
        "recommendation_roleplay_positive_failures": recommendation["failure_count"],
        "adjacent_control_failures": controls["failure_count"],
        "stable_english_guard_passed": stable_guard["passed"],
        "requires_customer_facts_for_recommendation": True,
        "requires_agency_preservation": True,
        "no_agent_decides_for_customer": True,
        "no_value_guarantee": True,
        "review_html_created": False,
        "recommended_next_checkpoint": NEXT_CHECKPOINT_ID,
        "do_not_open_next_checkpoint_in_this_run": True,
        **BOUNDARY_FLAGS,
    }


def render_report(summary: dict[str, Any], recommendation: dict[str, Any], controls: dict[str, Any]) -> str:
    lines = [
        "# PROD-101 English Recommendation Roleplay Post-Patch Regression",
        "",
        "`PROD-101` verifies the `PROD-100` English recommendation-roleplay runtime patch after application.",
        "",
        "This checkpoint is post-patch regression only. It changes no runtime behavior, response text, classifier reachability, retrieval, provider usage, private-data handling, voice playback, payment handling, contract signing, legal readiness, German wording, or production runtime promotion.",
        "",
        "## Result",
        "",
        f"- Recommendation roleplay positive failures: `{summary['recommendation_roleplay_positive_failures']}`",
        f"- Adjacent control failures: `{summary['adjacent_control_failures']}`",
        f"- Stable English guard passed: `{str(summary['stable_english_guard_passed']).lower()}`",
        f"- Requires customer facts for recommendation: `{str(summary['requires_customer_facts_for_recommendation']).lower()}`",
        f"- Requires agency preservation: `{str(summary['requires_agency_preservation']).lower()}`",
        f"- No agent decides for customer: `{str(summary['no_agent_decides_for_customer']).lower()}`",
        f"- No value guarantee: `{str(summary['no_value_guarantee']).lower()}`",
        f"- Review HTML created: `{str(summary['review_html_created']).lower()}`",
        f"- Recommended next checkpoint: `{summary['recommended_next_checkpoint']}`",
        f"- Do not open the next checkpoint in this run: `{str(summary['do_not_open_next_checkpoint_in_this_run']).lower()}`",
        "",
        "## Recommendation Roleplay Cases",
        "",
    ]
    for item in recommendation["cases"]:
        lines.append(f"- `{item['case_id']}` -> `{item['sales_difficulty']}`, passed `{str(item['passed']).lower()}`")
    lines.extend(["", "## Adjacent Controls", ""])
    for item in controls["cases"]:
        lines.append(f"- `{item['case_id']}` expected `{item['expected']}`, observed `{item['sales_difficulty']}`, passed `{str(item['passed']).lower()}`")
    lines.extend(["", "## Boundary Status", ""])
    for key in BOUNDARY_FLAGS:
        lines.append(f"- {key.replace('_', ' ').capitalize()}: `{str(summary[key]).lower()}`")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    source_result, patch, source_positives, source_controls = load_source()
    source_validator = run_validator(SOURCE_VALIDATOR)
    if not source_validator["passed"]:
        raise RuntimeError("Source validator failed; refusing PROD-101 regression.")
    stable_guard = run_validator(STABLE_ENGLISH_GUARD)
    recommendation = run_recommendation_roleplay_cases(source_positives)
    controls = run_adjacent_control_cases(source_controls)
    evidence = build_evidence(source_result, patch, source_validator, stable_guard)
    summary = summarize(recommendation, controls, source_validator, stable_guard)
    result = {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "validation": {
            "passed": recommendation["failure_count"] == 0 and controls["failure_count"] == 0 and stable_guard["passed"],
            "post_patch_regression_completed": True,
        },
        "summary": summary,
    }

    write_json(OUT_DIR / "recommendation_roleplay_regression_cases.json", recommendation)
    write_json(OUT_DIR / "adjacent_control_cases.json", controls)
    write_json(OUT_DIR / "stable_english_guard_summary.json", stable_guard)
    write_json(OUT_DIR / "evidence_summary.json", evidence)
    write_text(OUT_DIR / "report.md", render_report(summary, recommendation, controls))
    write_json(OUT_DIR / "result.json", result)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
