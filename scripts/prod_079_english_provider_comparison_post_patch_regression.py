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


CHECKPOINT_ID = "PROD-079-english-provider-comparison-post-patch-regression"
CHECKPOINT_NAME = "English Provider-Comparison Post-Patch Regression"
SOURCE_CHECKPOINT_ID = "PROD-078-english-provider-comparison-runtime-patch"
NEXT_CHECKPOINT_ID = "PROD-080-english-customer-move-remaining-slice-selection"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
SOURCE_DIR = ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID
SOURCE_VALIDATOR = ROOT / "scripts" / "validate_prod_078_english_provider_comparison_runtime_patch.py"
STABLE_GUARD_VALIDATOR = ROOT / "scripts" / "validate_prod_056_english_post_patch_multi_turn_regression.py"
EXPECTED_RESPONSE = "Fair. We can compare fit against what you use now before you decide."

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

REGRESSION_CASES = [
    ("provider_comparison_positive", "How is this different from our current provider?", "provider-comparison"),
    ("provider_comparison_positive", "Can you compare this with what we already use?", "provider-comparison"),
    ("provider_comparison_positive", "What would be different versus our current setup?", "provider-comparison"),
    ("provider_comparison_positive", "How does this compare with our current terms?", "provider-comparison"),
    ("provider_comparison_positive", "Can you compare your terms with what we already have?", "provider-comparison"),
    ("existing_provider_control", "We already have a provider and I do not want to switch.", "existing-provider-gap"),
    ("existing_provider_control", "We have another provider.", "existing-provider-gap"),
    ("existing_provider_control", "We already use another provider.", "existing-provider-gap"),
    ("adjacent_control", "What does this cost?", "price-first-direct"),
    ("adjacent_control", "What do you offer?", "unknown-runtime-signal"),
    ("adjacent_control", "Just send me the details in writing.", "written-info-request"),
    ("protected_control", "Can you take payment or card details if it is better?", "payment-safety-boundary"),
    ("protected_control", "Can you sign me up if this is better?", "unknown-runtime-signal"),
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


def run_command(command: list[str]) -> dict[str, Any]:
    completed = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=300,
        check=False,
    )
    return {
        "command": " ".join(command),
        "returncode": completed.returncode,
        "stdout_tail": completed.stdout.strip().splitlines()[-8:],
        "stderr_tail": completed.stderr.strip().splitlines()[-8:],
        "passed": completed.returncode == 0,
    }


def load_source() -> tuple[dict[str, Any], dict[str, Any]]:
    result = read_json(SOURCE_DIR / "result.json")
    decision = read_json(SOURCE_DIR / "patch_decision.json")
    if result["validation"]["passed"] is not True:
        raise RuntimeError("PROD-078 must pass before PROD-079.")
    if result["summary"]["patched_response"] != EXPECTED_RESPONSE:
        raise RuntimeError("PROD-078 patched response changed.")
    return result, decision


def runtime_decision_for(transcript: str) -> dict[str, Any]:
    decision = build_runtime_decision(
        {
            "case_id": "prod-079-post-patch",
            "customer_input": {
                "input_type": "speech",
                "transcript": transcript,
                "stage": "objection-handling",
            },
        },
        campaign={"language": "en"},
    )
    return {
        "response_language": decision["response_language"],
        "sales_difficulty": decision["sales_difficulty"],
        "interest_state": decision["interest_state"],
        "selected_strategy": decision["selected_strategy"],
        "next_action": decision["next_action"],
        "call_control": decision["call_control"],
        "agent_response": decision["agent_response"],
    }


def evaluate_case(index: int, case_type: str, transcript: str, expected_sales_difficulty: str) -> dict[str, Any]:
    observed = runtime_decision_for(transcript)
    gates = {
        "sales_difficulty_matches": observed["sales_difficulty"] == expected_sales_difficulty,
        "provider_response_matches_when_expected": expected_sales_difficulty != "provider-comparison" or observed["agent_response"] == EXPECTED_RESPONSE,
        "non_provider_controls_stay_out": expected_sales_difficulty == "provider-comparison" or observed["sales_difficulty"] != "provider-comparison",
    }
    issue_codes = [key for key, passed in gates.items() if not passed]
    return {
        "case_id": f"prod-079-{index:02d}",
        "case_type": case_type,
        "customer_turn": transcript,
        "expected_sales_difficulty": expected_sales_difficulty,
        "observed_runtime": observed,
        "gates": gates,
        "passed": not issue_codes,
        "issue_codes": issue_codes,
    }


def build_reviews() -> list[dict[str, Any]]:
    return [
        evaluate_case(index + 1, case_type, transcript, expected)
        for index, (case_type, transcript, expected) in enumerate(REGRESSION_CASES)
    ]


def build_stable_guard_summary() -> dict[str, Any]:
    return run_command([sys.executable, str(STABLE_GUARD_VALIDATOR)])


def build_evidence(source_result: dict[str, Any], source_decision: dict[str, Any], source_validator: dict[str, Any], stable_guard: dict[str, Any]) -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "source_validation": source_result["validation"],
        "source_patch_decision": source_decision["decision"],
        "source_validator_run": source_validator,
        "stable_guard_run": stable_guard,
    }


def summarize(reviews: list[dict[str, Any]], source_validator: dict[str, Any], stable_guard: dict[str, Any]) -> dict[str, Any]:
    failed = [item for item in reviews if not item["passed"]]
    return {
        "post_patch_regression_only": True,
        "source_validator_passed": source_validator["passed"],
        "stable_english_guard_passed": stable_guard["passed"],
        "provider_comparison_positive_case_count": sum(1 for item in reviews if item["case_type"] == "provider_comparison_positive"),
        "existing_provider_control_count": sum(1 for item in reviews if item["case_type"] == "existing_provider_control"),
        "adjacent_control_count": sum(1 for item in reviews if item["case_type"] in {"adjacent_control", "protected_control"}),
        "regression_case_count": len(reviews),
        "failed_regression_case_count": len(failed),
        "failed_regression_case_ids": [item["case_id"] for item in failed],
        "review_html_created": False,
        "recommended_next_checkpoint": NEXT_CHECKPOINT_ID,
        **BOUNDARY_FLAGS,
    }


def render_report(summary: dict[str, Any], reviews: list[dict[str, Any]]) -> str:
    lines = [
        "# PROD-079 English Provider-Comparison Post-Patch Regression",
        "",
        "`PROD-079` verifies the `PROD-078` English provider-comparison runtime patch after application.",
        "",
        "This is regression only. It changes no runtime behavior, response text, classifier reachability, or retrieval.",
        "",
        "## Summary",
        "",
        f"- Provider-comparison positive cases: `{summary['provider_comparison_positive_case_count']}`",
        f"- Existing-provider-gap controls: `{summary['existing_provider_control_count']}`",
        f"- Adjacent/protected controls: `{summary['adjacent_control_count']}`",
        f"- Failed regression case count: `{summary['failed_regression_case_count']}`",
        f"- Stable English guard passed: `{str(summary['stable_english_guard_passed']).lower()}`",
        f"- Review HTML created: `{str(summary['review_html_created']).lower()}`",
        f"- Recommended next checkpoint: `{summary['recommended_next_checkpoint']}`",
        "",
        "## Regression Cases",
        "",
    ]
    for item in reviews:
        lines.extend(
            [
                f"### {item['case_id']}",
                "",
                f"- Case type: `{item['case_type']}`",
                f"- Customer turn: {item['customer_turn']}",
                f"- Expected sales difficulty: `{item['expected_sales_difficulty']}`",
                f"- Observed sales difficulty: `{item['observed_runtime']['sales_difficulty']}`",
                f"- Passed: `{str(item['passed']).lower()}`",
                "",
            ]
        )
    lines.extend(
        [
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
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    source_result, source_decision = load_source()
    if localized_response("en", "provider-comparison", None) != EXPECTED_RESPONSE:
        raise SystemExit("Provider-comparison response changed before PROD-079.")
    source_validator = run_command([sys.executable, str(SOURCE_VALIDATOR)])
    stable_guard = build_stable_guard_summary()
    reviews = build_reviews()
    evidence = build_evidence(source_result, source_decision, source_validator, stable_guard)
    summary = summarize(reviews, source_validator, stable_guard)
    result = {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "validation": {
            "passed": source_validator["passed"] and stable_guard["passed"] and summary["failed_regression_case_count"] == 0,
            "post_patch_regression_passed": summary["failed_regression_case_count"] == 0,
            "stable_guard_passed": stable_guard["passed"],
        },
        "summary": summary,
    }
    write_json(OUT_DIR / "post_patch_regression_reviews.json", {"checkpoint_id": CHECKPOINT_ID, "items": reviews})
    write_json(OUT_DIR / "stable_guard_summary.json", stable_guard)
    write_json(OUT_DIR / "evidence_summary.json", evidence)
    write_text(OUT_DIR / "report.md", render_report(summary, reviews))
    write_json(OUT_DIR / "result.json", result)
    print(json.dumps({"checkpoint_id": CHECKPOINT_ID, "validation": result["validation"], "summary": summary}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
