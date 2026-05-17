#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-058-english-runtime-promotion-blocker-inventory"
CHECKPOINT_NAME = "English Runtime Promotion Blocker Inventory"
SOURCE_CHECKPOINT_ID = "PROD-057-english-multi-turn-regression-guard-decision"
SOURCE_REGRESSION_ID = "PROD-056-english-post-patch-multi-turn-regression"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
CASE_FILE = ROOT / "research" / "experiments" / "cases" / "prod-058-english-runtime-promotion-blocker-inventory.json"
SOURCE_DIR = ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID
SOURCE_REGRESSION_DIR = ROOT / "research" / "experiments" / "generated" / SOURCE_REGRESSION_ID
STABLE_GUARD_SCRIPT = ROOT / "scripts" / "validate_english_multi_turn_regression_guard.py"
STABLE_GUARD_COMMAND = "python scripts\\validate_english_multi_turn_regression_guard.py"

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
    "real_customer_use_unblocked": False,
    "payment_collection_allowed": False,
    "contract_signing_allowed": False,
    "production_runtime_promotion_allowed": False,
    "german_exact_phrase_promotion_allowed": False,
    "german_naturalness_claimed": False,
}

POSSIBLE_NEXT_DECISIONS = [
    "final_english_only_readiness_review",
    "return_to_native_german_review_import",
    "reopen_voice_or_retrieval_only_through_separate_gates",
]

BLOCKERS = [
    {
        "blocker_id": "final_english_only_readiness_review_not_run",
        "category": "english_evidence_gap",
        "label": "Final English-only runtime readiness review not run",
        "evidence": "PROD-056 and PROD-057 establish a stable English multi-turn guard, but no final English-only readiness review has inventoried the remaining promotion boundary.",
        "recommended_next_action": "Run a final English-only runtime readiness review only after this inventory is human-accepted.",
        "blocks_english_runtime_promotion": True,
    },
    {
        "blocker_id": "english_guard_scope_limited_to_promoted_multi_turn_surface",
        "category": "english_evidence_gap",
        "label": "English guard scope is limited to the promoted multi-turn surface",
        "evidence": "PROD-057 adopts the PROD-056 guard for 26 promoted English surfaces; it is not proof that every deterministic English runtime branch is ready.",
        "recommended_next_action": "Keep the stable guard as a prerequisite, then use the final English review to state the exact English surface being promoted.",
        "blocks_english_runtime_promotion": True,
    },
    {
        "blocker_id": "customer_move_classification_outside_selected_non_refusal_groups",
        "category": "product_policy_gate",
        "label": "Customer-move classification outside selected non-refusal groups",
        "evidence": "The checkpoint index still blocks classification changes outside the selected non-refusal groups.",
        "recommended_next_action": "Do not broaden classification behavior inside PROD-058; decide the policy in a separate runtime checkpoint if needed.",
        "blocks_english_runtime_promotion": True,
    },
    {
        "blocker_id": "voicemail_action_only_behavior",
        "category": "product_policy_gate",
        "label": "Voicemail action-only behavior",
        "evidence": "PROD-053D/PROD-053E explicitly kept voicemail action-only behavior out of the wording patch.",
        "recommended_next_action": "Keep voicemail behavior excluded from English promotion unless a separate policy checkpoint accepts it.",
        "blocks_english_runtime_promotion": True,
    },
    {
        "blocker_id": "coverage_knowledge_policy_behavior",
        "category": "product_policy_gate",
        "label": "Coverage knowledge-policy behavior",
        "evidence": "PROD-053D/PROD-053E left coverage knowledge-policy behavior as a separate design question, not a wording-only change.",
        "recommended_next_action": "Review knowledge-policy behavior separately before claiming broad English runtime readiness.",
        "blocks_english_runtime_promotion": True,
    },
    {
        "blocker_id": "context_sensitive_autonomy_behavior",
        "category": "product_policy_gate",
        "label": "Context-sensitive autonomy behavior",
        "evidence": "PROD-053D/PROD-053E left context-sensitive autonomy wording and behavior out of the accepted wording patch.",
        "recommended_next_action": "Separate autonomy-policy behavior from phrase naturalness before any promotion claim.",
        "blocks_english_runtime_promotion": True,
    },
    {
        "blocker_id": "native_german_review",
        "category": "separate_language_gate",
        "label": "Native German review",
        "evidence": "PROD-048D remains parked until corrected native German reviewer export exists.",
        "recommended_next_action": "Return to PROD-048D only when the corrected German reviewer export is available.",
        "blocks_english_runtime_promotion": False,
    },
    {
        "blocker_id": "voice_playback_quality",
        "category": "separate_voice_gate",
        "label": "Voice playback quality",
        "evidence": "RESP-007 German pacing-stability listening decision is still pending, and voice playback quality is a separate subjective gate.",
        "recommended_next_action": "Do not reopen voice through PROD-058; use RESP/VOICE gates after human listening review.",
        "blocks_english_runtime_promotion": False,
    },
    {
        "blocker_id": "retrieval_default",
        "category": "separate_retrieval_gate",
        "label": "Retrieval default",
        "evidence": "Runtime retrieval remains disabled by default unless a separate RAG gate promotes it.",
        "recommended_next_action": "Keep retrieval default-off for English readiness review; reopen only through RAG gates.",
        "blocks_english_runtime_promotion": False,
    },
    {
        "blocker_id": "provider_or_private_data_use",
        "category": "provider_or_private_data_gate",
        "label": "Provider or private-data use",
        "evidence": "PROD-057 and the command map keep providers, LLM calls, and private-data reads blocked by default.",
        "recommended_next_action": "Keep the final English review offline and synthetic unless a separate provider/private-data boundary review is approved.",
        "blocks_english_runtime_promotion": False,
    },
    {
        "blocker_id": "legal_compliance_review",
        "category": "legal_or_deployment_gate",
        "label": "Legal compliance review",
        "evidence": "Legal readiness is explicitly still blocked in the checkpoint index and PROD-057.",
        "recommended_next_action": "Do not treat English runtime readiness as legal readiness.",
        "blocks_english_runtime_promotion": False,
    },
    {
        "blocker_id": "public_demo_use",
        "category": "legal_or_deployment_gate",
        "label": "Public demo use",
        "evidence": "PROD-057 keeps public demo use blocked.",
        "recommended_next_action": "Require a separate public-demo gate before showing this as a public product demo.",
        "blocks_english_runtime_promotion": False,
    },
    {
        "blocker_id": "real_customer_use",
        "category": "legal_or_deployment_gate",
        "label": "Real customer use",
        "evidence": "PROD-057 keeps real customer use blocked.",
        "recommended_next_action": "Do not use English readiness evidence as permission for real customer calls.",
        "blocks_english_runtime_promotion": False,
    },
    {
        "blocker_id": "payment_collection",
        "category": "legal_or_deployment_gate",
        "label": "Payment collection",
        "evidence": "Payment collection remains blocked in the checkpoint index and PROD-057.",
        "recommended_next_action": "Keep payment collection outside English runtime promotion evidence.",
        "blocks_english_runtime_promotion": False,
    },
    {
        "blocker_id": "contract_signing",
        "category": "legal_or_deployment_gate",
        "label": "Contract signing",
        "evidence": "Contract signing remains blocked in the checkpoint index and PROD-057.",
        "recommended_next_action": "Keep contract signing outside English runtime promotion evidence.",
        "blocks_english_runtime_promotion": False,
    },
    {
        "blocker_id": "production_runtime_promotion",
        "category": "legal_or_deployment_gate",
        "label": "Production runtime promotion",
        "evidence": "PROD-057 explicitly keeps production runtime promotion blocked.",
        "recommended_next_action": "Treat PROD-059, if accepted, as a final English-only readiness review, not production promotion.",
        "blocks_english_runtime_promotion": False,
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


def load_sources() -> tuple[dict[str, Any], dict[str, Any]]:
    guard = read_json(SOURCE_DIR / "result.json")
    regression = read_json(SOURCE_REGRESSION_DIR / "result.json")
    if guard["validation"]["passed"] is not True or guard["validation"]["guard_decision_passed"] is not True:
        raise SystemExit("PROD-057 guard decision must pass before PROD-058.")
    if guard["summary"]["guard_status"] != "adopted":
        raise SystemExit("PROD-057 must adopt the English guard before PROD-058.")
    if regression["validation"]["regression_gate_passed"] is not True:
        raise SystemExit("PROD-056 regression gate must pass before PROD-058.")
    return guard, regression


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
        "passed": completed.returncode == 0 and SOURCE_REGRESSION_ID in completed.stdout,
    }


def build_case_file() -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "source_regression_id": SOURCE_REGRESSION_ID,
        "scope": "inventory_only",
        "stable_guard_command": STABLE_GUARD_COMMAND,
        "possible_next_decisions": POSSIBLE_NEXT_DECISIONS,
        "requires_human_review_before_next_checkpoint": True,
        "non_goals": [
            "runtime behavior change",
            "response text change",
            "German exact phrase promotion",
            "voice playback promotion",
            "retrieval default change",
            "provider call",
            "LLM call",
            "private data read",
            "public demo approval",
            "real customer use",
            "payment collection",
            "contract signing",
            "production runtime promotion",
        ],
    }


def build_evidence_summary(
    guard: dict[str, Any],
    regression: dict[str, Any],
    guard_run: dict[str, Any],
) -> dict[str, Any]:
    guard_summary = guard["summary"]
    regression_summary = regression["summary"]
    return {
        "source_guard": {
            "checkpoint_id": guard["checkpoint_id"],
            "guard_status": guard_summary["guard_status"],
            "stable_guard_command": guard_summary["stable_guard_command"],
            "readiness_failure_count": guard_summary["readiness_failure_count"],
            "next_checkpoint": guard_summary["next_checkpoint"],
        },
        "source_regression": {
            "checkpoint_id": regression["checkpoint_id"],
            "promoted_response_count": regression_summary["source_promoted_response_count"],
            "runtime_second_turn_case_count": regression_summary["runtime_second_turn_case_count"],
            "callback_scheduling_case_count": regression_summary["callback_scheduling_case_count"],
            "terminal_boundary_case_count": regression_summary["terminal_boundary_case_count"],
            "blocking_finding_count": regression_summary["blocking_finding_count"],
            "regression_gate_passed": regression_summary["regression_gate_passed"],
        },
        "stable_guard_run": guard_run,
        "positive_evidence_chain": [
            "PROD-053E promoted accepted English wording into deterministic runtime.",
            "PROD-054 found multi-turn naturalness failures instead of overclaiming single-turn acceptance.",
            "PROD-055 patched the six blocking English follow-up findings.",
            "PROD-056 passed the post-patch regression with zero blocking findings.",
            "PROD-057 adopted the regression as a stable English guard.",
        ],
    }


def build_inventory() -> dict[str, Any]:
    categories: dict[str, int] = {}
    for item in BLOCKERS:
        categories[item["category"]] = categories.get(item["category"], 0) + 1
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "blockers": [{**item, "status": "blocked"} for item in BLOCKERS],
        "category_counts": categories,
    }


def build_recommendation(inventory: dict[str, Any]) -> dict[str, Any]:
    english_blockers = [
        item["blocker_id"]
        for item in inventory["blockers"]
        if item["category"] in {"english_evidence_gap", "product_policy_gate"}
    ]
    separate_gate_blockers = [
        item["blocker_id"]
        for item in inventory["blockers"]
        if item["category"] not in {"english_evidence_gap", "product_policy_gate"}
    ]
    return {
        "decision": "run_final_english_only_readiness_review_after_human_acceptance",
        "recommended_next_checkpoint": "PROD-059-final-english-only-runtime-readiness-review",
        "why": "The English evidence chain is now strong enough for a final English-only readiness review, but not for production promotion.",
        "english_blockers_to_address_or_explicitly_exclude": english_blockers,
        "separate_gate_blockers_not_in_scope_for_english_only_review": separate_gate_blockers,
        "not_a_production_promotion": True,
        "requires_human_review_before_next_checkpoint": True,
        "human_review_request": "Review the PROD-058 inventory and accept or revise the blocker classification before creating PROD-059.",
    }


def summarize(
    inventory: dict[str, Any],
    recommendation: dict[str, Any],
    guard_run: dict[str, Any],
) -> dict[str, Any]:
    blockers = inventory["blockers"]
    english_evidence_gap_count = sum(1 for item in blockers if item["category"] == "english_evidence_gap")
    product_policy_gate_count = sum(1 for item in blockers if item["category"] == "product_policy_gate")
    separate_gate_count = len(blockers) - english_evidence_gap_count - product_policy_gate_count
    return {
        "inventory_only": True,
        "source_guard_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "source_regression_checkpoint_id": SOURCE_REGRESSION_ID,
        "stable_guard_command": STABLE_GUARD_COMMAND,
        "stable_guard_passed": guard_run["passed"],
        "blocker_count": len(blockers),
        "english_evidence_gap_count": english_evidence_gap_count,
        "product_policy_gate_count": product_policy_gate_count,
        "separate_gate_count": separate_gate_count,
        "final_english_only_readiness_review_justified": True,
        "recommended_next_checkpoint": recommendation["recommended_next_checkpoint"],
        "requires_human_review_before_next_checkpoint": True,
        **BOUNDARY_FLAGS,
    }


def render_report(
    inventory: dict[str, Any],
    recommendation: dict[str, Any],
    evidence: dict[str, Any],
    summary: dict[str, Any],
) -> str:
    lines = [
        "# PROD-058 English Runtime Promotion Blocker Inventory",
        "",
        "This is an inventory-only checkpoint. It does not change runtime behavior or response text.",
        "",
        "## Evidence Base",
        "",
        f"- Source guard: `{SOURCE_CHECKPOINT_ID}`",
        f"- Source regression: `{SOURCE_REGRESSION_ID}`",
        f"- Stable guard command: `{STABLE_GUARD_COMMAND}`",
        f"- Stable guard passed: `{str(summary['stable_guard_passed']).lower()}`",
        "- Positive evidence chain:",
    ]
    for item in evidence["positive_evidence_chain"]:
        lines.append(f"  - {item}")
    lines.extend(
        [
            "",
            "## Inventory Summary",
            "",
            f"- Blocker count: `{summary['blocker_count']}`",
            f"- English evidence gap count: `{summary['english_evidence_gap_count']}`",
            f"- Product-policy gate count: `{summary['product_policy_gate_count']}`",
            f"- Separate gate count: `{summary['separate_gate_count']}`",
            f"- Final English-only runtime readiness review justified: `{str(summary['final_english_only_readiness_review_justified']).lower()}`",
            f"- Requires human review before next checkpoint: `{str(summary['requires_human_review_before_next_checkpoint']).lower()}`",
            f"- Production runtime promotion allowed: `{str(summary['production_runtime_promotion_allowed']).lower()}`",
            "",
            "## Blockers",
            "",
        ]
    )
    for item in inventory["blockers"]:
        category_label = item["category"].replace("_", "-")
        lines.extend(
            [
                f"### {item['blocker_id']}",
                "",
                f"- Category: `{category_label}`",
                f"- Status: `{item['status']}`",
                f"- Label: {item['label']}",
                f"- Evidence: {item['evidence']}",
                f"- Blocks English runtime promotion: `{str(item['blocks_english_runtime_promotion']).lower()}`",
                f"- Recommended next action: {item['recommended_next_action']}",
                "",
            ]
        )
    lines.extend(
        [
            "## Recommendation",
            "",
            f"- Decision: `{recommendation['decision']}`",
            f"- Recommended next checkpoint: `{recommendation['recommended_next_checkpoint']}`",
            f"- Why: {recommendation['why']}",
            f"- Requires human review: `{str(recommendation['requires_human_review_before_next_checkpoint']).lower()}`",
            f"- Human review request: {recommendation['human_review_request']}",
            "",
            "## Boundary",
            "",
            f"- Runtime behavior changed: `{str(summary['runtime_behavior_changed']).lower()}`",
            f"- Response text behavior changed: `{str(summary['response_text_behavior_changed']).lower()}`",
            "- No provider calls.",
            "- No LLM or LLM judging.",
            "- No private data reads.",
            "- No retrieval enablement.",
            "- No German exact-phrase promotion or German naturalness claim.",
            "- No voice playback, public demo, real customer use, payment collection, contract signing, or production runtime promotion.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    guard, regression = load_sources()
    case_payload = build_case_file()
    write_json(CASE_FILE, case_payload)
    guard_run = stable_guard_result()
    inventory = build_inventory()
    recommendation = build_recommendation(inventory)
    evidence = build_evidence_summary(guard, regression, guard_run)
    summary = summarize(inventory, recommendation, guard_run)
    result = {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "validation": {
            "passed": guard_run["passed"],
            "inventory_gate_passed": guard_run["passed"],
        },
        "summary": summary,
    }

    write_json(CASE_FILE, case_payload)
    write_json(OUT_DIR / "evidence_summary.json", evidence)
    write_json(OUT_DIR / "blocker_inventory.json", inventory)
    write_json(OUT_DIR / "recommendation.json", recommendation)
    write_json(OUT_DIR / "result.json", result)
    write_text(OUT_DIR / "report.md", render_report(inventory, recommendation, evidence, summary))
    print(json.dumps({"checkpoint_id": CHECKPOINT_ID, "validation": result["validation"], "summary": summary}, indent=2))


if __name__ == "__main__":
    main()
