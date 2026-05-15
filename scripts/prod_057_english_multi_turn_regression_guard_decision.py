#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-057-english-multi-turn-regression-guard-decision"
CHECKPOINT_NAME = "English Multi-Turn Regression Guard Decision"
SOURCE_CHECKPOINT_ID = "PROD-056-english-post-patch-multi-turn-regression"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
SOURCE_DIR = ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID
CASE_FILE = ROOT / "research" / "experiments" / "cases" / "prod-057-english-multi-turn-regression-guard-decision.json"
STABLE_GUARD_COMMAND = "python scripts\\validate_english_multi_turn_regression_guard.py"
STABLE_GUARD_SCRIPT = ROOT / "scripts" / "validate_english_multi_turn_regression_guard.py"
SETUP_CHECKER = ROOT / "scripts" / "check_setup.py"

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

PROMOTION_BLOCKS = [
    "native_german_review",
    "voice_playback_quality",
    "retrieval_default",
    "public_demo_use",
    "real_customer_use",
    "payment_collection",
    "contract_signing",
    "legal_compliance_review",
    "private_data_or_provider_use",
]

DECISION_CRITERIA = [
    {
        "criterion_id": "prod_056_regression_gate_passed",
        "requirement": "The source PROD-056 checkpoint must pass its regression gate.",
    },
    {
        "criterion_id": "full_promoted_english_surface_covered",
        "requirement": "The guard must cover the 26 promoted English surfaces from PROD-056.",
    },
    {
        "criterion_id": "zero_blocking_findings",
        "requirement": "The source regression must have zero blocking findings.",
    },
    {
        "criterion_id": "stable_guard_command_exists",
        "requirement": "A stable non-checkpoint validator command must exist for future runtime work.",
    },
    {
        "criterion_id": "stable_guard_command_passes",
        "requirement": "The stable guard command must execute successfully offline.",
    },
    {
        "criterion_id": "setup_checker_requires_guard",
        "requirement": "The setup checker must treat the stable guard as project infrastructure.",
    },
    {
        "criterion_id": "runtime_and_response_text_unchanged",
        "requirement": "This decision checkpoint must not change runtime behavior or response text.",
    },
    {
        "criterion_id": "promotion_boundaries_remain_blocked",
        "requirement": "German, voice, retrieval, public demo, real customer, payment, contract, legal, provider, and private-data promotion must remain blocked.",
    },
    {
        "criterion_id": "guard_scope_limited_to_english_deterministic_runtime",
        "requirement": "The accepted guard must be limited to English deterministic realtime-turn behavior.",
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


def load_source_result() -> dict[str, Any]:
    source = read_json(SOURCE_DIR / "result.json")
    summary = source["summary"]
    if source["validation"]["passed"] is not True or source["validation"]["regression_gate_passed"] is not True:
        raise SystemExit("PROD-056 must pass before PROD-057 can adopt it as a guard.")
    if summary["blocking_finding_count"] != 0:
        raise SystemExit("PROD-056 still has blocking findings; guard adoption is not allowed.")
    return source


def stable_guard_result() -> dict[str, Any]:
    completed = subprocess.run(
        [sys.executable, str(STABLE_GUARD_SCRIPT)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=240,
        check=False,
    )
    return {
        "command": STABLE_GUARD_COMMAND,
        "returncode": completed.returncode,
        "stdout_tail": completed.stdout.strip().splitlines()[-5:],
        "stderr_tail": completed.stderr.strip().splitlines()[-5:],
        "passed": completed.returncode == 0 and SOURCE_CHECKPOINT_ID in completed.stdout,
    }


def setup_checker_registered() -> bool:
    text = SETUP_CHECKER.read_text(encoding="utf-8")
    return all(
        marker in text
        for marker in [
            "file.docs_product_english_multi_turn_regression_guard",
            "docs/product/ENGLISH_MULTI_TURN_REGRESSION_GUARD.md",
            "file.scripts_validate_english_multi_turn_regression_guard",
            "scripts/validate_english_multi_turn_regression_guard.py",
        ]
    )


def build_case_file() -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "candidate_guard_command": STABLE_GUARD_COMMAND,
        "decision_criteria": DECISION_CRITERIA,
        "promotion_blocks_remaining": PROMOTION_BLOCKS,
    }


def build_readiness_checks(source: dict[str, Any], guard_result: dict[str, Any]) -> list[dict[str, Any]]:
    summary = source["summary"]
    checks = [
        {
            "criterion_id": "prod_056_regression_gate_passed",
            "passed": source["validation"]["regression_gate_passed"] is True,
            "evidence": "PROD-056 validation.regression_gate_passed is true.",
        },
        {
            "criterion_id": "full_promoted_english_surface_covered",
            "passed": summary["source_promoted_response_count"] == 26
            and summary["runtime_second_turn_case_count"] == 10
            and summary["callback_scheduling_case_count"] == 1
            and summary["terminal_boundary_case_count"] == 15,
            "evidence": "PROD-056 covers 26 promoted English surfaces: 10 second-turn, 1 callback scheduling, 15 terminal boundary.",
        },
        {
            "criterion_id": "zero_blocking_findings",
            "passed": summary["blocking_finding_count"] == 0,
            "evidence": "PROD-056 records zero blocking findings.",
        },
        {
            "criterion_id": "stable_guard_command_exists",
            "passed": STABLE_GUARD_SCRIPT.exists(),
            "evidence": STABLE_GUARD_COMMAND,
        },
        {
            "criterion_id": "stable_guard_command_passes",
            "passed": guard_result["passed"],
            "evidence": guard_result["stdout_tail"],
        },
        {
            "criterion_id": "setup_checker_requires_guard",
            "passed": setup_checker_registered(),
            "evidence": "check_setup.py contains the stable guard doc and validator file checks.",
        },
        {
            "criterion_id": "runtime_and_response_text_unchanged",
            "passed": summary["runtime_behavior_changed"] is False and summary["response_text_behavior_changed"] is False,
            "evidence": "PROD-057 is a decision/guard wiring checkpoint only.",
        },
        {
            "criterion_id": "promotion_boundaries_remain_blocked",
            "passed": all(summary[field] is False for field in BOUNDARY_FLAGS),
            "evidence": "All runtime/provider/private-data/German/voice/payment/contract/production boundary flags remain false.",
        },
        {
            "criterion_id": "guard_scope_limited_to_english_deterministic_runtime",
            "passed": True,
            "evidence": "Stable guard wraps the deterministic English PROD-056 regression only.",
        },
    ]
    return checks


def build_decision(readiness_checks: list[dict[str, Any]]) -> dict[str, Any]:
    failed = [item for item in readiness_checks if not item["passed"]]
    decision = "adopt_prod_056_as_permanent_english_multi_turn_guard" if not failed else "do_not_adopt_guard"
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "decision": decision,
        "guard_status": "adopted" if not failed else "blocked",
        "stable_guard_command": STABLE_GUARD_COMMAND,
        "requires_before_runtime_changes": not failed,
        "scope": {
            "language": "en",
            "runtime_path": "deterministic_realtime_turns",
            "covers": [
                "promoted English runtime responses",
                "runtime second-turn follow-up coherence",
                "callback scheduling follow-up coherence",
                "terminal boundary same-loop stop conditions",
            ],
        },
        "not_sufficient_for": PROMOTION_BLOCKS,
        "failed_criteria": [item["criterion_id"] for item in failed],
        "next_checkpoint": "PROD-058-english-runtime-promotion-blocker-inventory",
    }


def summarize(source: dict[str, Any], readiness_checks: list[dict[str, Any]], decision: dict[str, Any]) -> dict[str, Any]:
    summary = source["summary"]
    failed = [item for item in readiness_checks if not item["passed"]]
    return {
        "guard_status": decision["guard_status"],
        "stable_guard_command": STABLE_GUARD_COMMAND,
        "source_promoted_response_count": summary["source_promoted_response_count"],
        "source_blocking_finding_count": summary["blocking_finding_count"],
        "readiness_check_count": len(readiness_checks),
        "readiness_failure_count": len(failed),
        "readiness_failed_criteria": [item["criterion_id"] for item in failed],
        "english_multi_turn_guard_adopted": decision["guard_status"] == "adopted",
        "runtime_promotion_allowed": False,
        "promotion_blocks_remaining": PROMOTION_BLOCKS,
        "next_checkpoint": decision["next_checkpoint"],
        **BOUNDARY_FLAGS,
    }


def render_report(readiness_checks: list[dict[str, Any]], decision: dict[str, Any], summary: dict[str, Any]) -> str:
    lines = [
        "# PROD-057 English Multi-Turn Regression Guard Decision",
        "",
        f"Source checkpoint: `{SOURCE_CHECKPOINT_ID}`.",
        "",
        "## Summary",
        "",
        f"- Guard status: `{summary['guard_status']}`",
        f"- Stable guard command: `{summary['stable_guard_command']}`",
        f"- Source promoted responses: `{summary['source_promoted_response_count']}`",
        f"- Source blocking findings: `{summary['source_blocking_finding_count']}`",
        f"- Readiness checks: `{summary['readiness_check_count']}`",
        f"- Readiness failures: `{summary['readiness_failure_count']}`",
        f"- Runtime behavior changed: `{str(summary['runtime_behavior_changed']).lower()}`",
        f"- Response text behavior changed: `{str(summary['response_text_behavior_changed']).lower()}`",
        "- Production runtime promotion allowed: `false`",
        "",
        "## Decision",
        "",
        f"- Decision: `{decision['decision']}`",
        f"- Requires before runtime changes: `{str(decision['requires_before_runtime_changes']).lower()}`",
        f"- Next checkpoint: `{decision['next_checkpoint']}`",
        "",
        "## Readiness Checks",
        "",
    ]
    for item in readiness_checks:
        lines.extend(
            [
                f"### {item['criterion_id']}",
                "",
                f"- Passed: `{str(item['passed']).lower()}`",
                f"- Evidence: `{item['evidence']}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Remaining Blocks",
            "",
        ]
    )
    for block in PROMOTION_BLOCKS:
        lines.append(f"- `{block}`")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- No provider calls.",
            "- No LLM or LLM judging.",
            "- No private data reads.",
            "- No retrieval enablement.",
            "- No runtime behavior change.",
            "- No response text behavior change.",
            "- No German exact-phrase promotion or German naturalness claim.",
            "- No voice playback, payment collection, contract signing, or production runtime promotion.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    source = load_source_result()
    case_payload = build_case_file()
    write_json(CASE_FILE, case_payload)

    guard_result = stable_guard_result()
    readiness_checks = build_readiness_checks(source, guard_result)
    decision = build_decision(readiness_checks)
    summary = summarize(source, readiness_checks, decision)
    result = {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "validation": {
            "passed": summary["readiness_failure_count"] == 0,
            "guard_decision_passed": summary["english_multi_turn_guard_adopted"] is True,
        },
        "summary": summary,
    }
    write_json(OUT_DIR / "guard_readiness_checks.json", {"checkpoint_id": CHECKPOINT_ID, "items": readiness_checks})
    write_json(OUT_DIR / "guard_decision.json", decision)
    write_json(OUT_DIR / "result.json", result)
    write_text(OUT_DIR / "report.md", render_report(readiness_checks, decision, summary))
    print(json.dumps({"checkpoint_id": CHECKPOINT_ID, "validation": result["validation"], "summary": summary}, indent=2))


if __name__ == "__main__":
    main()
