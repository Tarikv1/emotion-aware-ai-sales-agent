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


CHECKPOINT_ID = "PROD-081-english-unknown-runtime-signal-subtype-inventory"
CHECKPOINT_NAME = "English Unknown Runtime Signal Subtype Inventory"
SOURCE_CHECKPOINT_ID = "PROD-080-english-customer-move-remaining-slice-selection"
NEXT_CHECKPOINT_ID = "PROD-082-english-guided-option-selection-review"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
CASE_FILE = ROOT / "research" / "experiments" / "cases" / "prod-081-english-unknown-runtime-signal-subtype-inventory.json"
SOURCE_DIR = ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID
SOURCE_VALIDATOR = ROOT / "scripts" / "validate_prod_080_english_customer_move_remaining_slice_selection.py"

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

UNKNOWN_CASES = [
    {
        "case_id": "prod-081-guided-option-01",
        "subtype_id": "guided_option_selection_candidate",
        "customer_turn": "So do I choose the 29 option or the 59 option?",
        "why_inventory": "Customer is asking to choose between two real offer options without using a currently routed price or plan-detail phrase.",
    },
    {
        "case_id": "prod-081-guided-option-02",
        "subtype_id": "guided_option_selection_candidate",
        "customer_turn": "Should I start small or go with the fuller option?",
        "why_inventory": "Customer has a binary choice frame, but the current runtime only has a generic clarification fallback.",
    },
    {
        "case_id": "prod-081-guided-option-03",
        "subtype_id": "guided_option_selection_candidate",
        "customer_turn": "I can see both paths, I am just not sure which one fits me.",
        "why_inventory": "This is the exact risk area for guided option selection: the agent must preserve customer agency instead of pushing.",
    },
    {
        "case_id": "prod-081-plan-difference-01",
        "subtype_id": "plan_option_difference",
        "customer_turn": "What is the real difference between the 29 option and the 59 option?",
        "why_inventory": "Customer asks for option difference without a current-provider comparison target.",
    },
    {
        "case_id": "prod-081-plan-difference-02",
        "subtype_id": "plan_option_difference",
        "customer_turn": "Can you show me both options side by side?",
        "why_inventory": "Option-comparison intent exists, but current provider-comparison guard intentionally does not cover this.",
    },
    {
        "case_id": "prod-081-recommendation-01",
        "subtype_id": "recommendation_request",
        "customer_turn": "Which route would you suggest for someone like me?",
        "why_inventory": "Recommendation language can create advice pressure and should not be folded into a sale branch without review.",
    },
    {
        "case_id": "prod-081-recommendation-02",
        "subtype_id": "recommendation_request",
        "customer_turn": "What would you do in my position?",
        "why_inventory": "The current runtime has no reviewed boundary for role-playing a customer's decision.",
    },
    {
        "case_id": "prod-081-next-step-01",
        "subtype_id": "next_step_clarity",
        "customer_turn": "What happens after I say yes?",
        "why_inventory": "The customer asks about process after agreement, not payment or contract signing.",
    },
    {
        "case_id": "prod-081-deferral-01",
        "subtype_id": "deferral_or_choose_later",
        "customer_turn": "Can I choose later instead of deciding on this call?",
        "why_inventory": "The customer asks for deferral, but the exact phrase is outside the existing autonomy-check trigger.",
    },
    {
        "case_id": "prod-081-unclear-interest-01",
        "subtype_id": "unclear_interest_probe",
        "customer_turn": "I am listening, but I do not know what I am supposed to decide yet.",
        "why_inventory": "The runtime should probably clarify the decision frame, but no reviewed subtype exists.",
    },
]

PROTECTED_CONTROLS = [
    {
        "case_id": "prod-081-control-do-not-call",
        "customer_turn": "Do not call me again.",
        "expected_sales_difficulty": "do-not-call",
    },
    {
        "case_id": "prod-081-control-human-request",
        "customer_turn": "I want to speak to a human specialist.",
        "expected_sales_difficulty": "human-request",
    },
    {
        "case_id": "prod-081-control-payment",
        "customer_turn": "I will not give card details over the phone.",
        "expected_sales_difficulty": "payment-safety-boundary",
    },
    {
        "case_id": "prod-081-control-coverage",
        "customer_turn": "Is this covered by insurance?",
        "expected_sales_difficulty": "coverage-boundary-route",
    },
    {
        "case_id": "prod-081-control-healthcare",
        "customer_turn": "Is this medical treatment right for me?",
        "expected_sales_difficulty": "healthcare-boundary-route",
    },
    {
        "case_id": "prod-081-control-support",
        "customer_turn": "I need support with my account.",
        "expected_sales_difficulty": "support-route",
    },
    {
        "case_id": "prod-081-control-email-only",
        "customer_turn": "Just email me.",
        "expected_sales_difficulty": "email-only-boundary",
    },
    {
        "case_id": "prod-081-control-voicemail",
        "customer_turn": "",
        "input_type": "voicemail-detected",
        "expected_sales_difficulty": "voicemail",
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
        "command": f"python {rel(SOURCE_VALIDATOR)}",
        "returncode": completed.returncode,
        "stdout_tail": completed.stdout.strip().splitlines()[-8:],
        "stderr_tail": completed.stderr.strip().splitlines()[-8:],
        "passed": completed.returncode == 0,
    }


def load_source() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    source_result = read_json(SOURCE_DIR / "result.json")
    source_selection = read_json(SOURCE_DIR / "remaining_slice_selection.json")
    source_snapshot = read_json(SOURCE_DIR / "current_classifier_reachability_snapshot.json")
    if source_result["validation"]["passed"] is not True:
        raise RuntimeError("PROD-080 must pass before PROD-081.")
    if source_result["summary"]["recommended_next_checkpoint"] != CHECKPOINT_ID:
        raise RuntimeError("PROD-080 must recommend PROD-081.")
    if source_selection["selected_next_slice"] != "unknown_runtime_signal_subtypes":
        raise RuntimeError("PROD-080 must select unknown_runtime_signal_subtypes.")
    return source_result, source_selection, source_snapshot


def build_case_file() -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "scope": "english_unknown_runtime_signal_subtype_inventory_only",
        "inventory_only": True,
        "selected_source_slice": "unknown_runtime_signal_subtypes",
        "runtime_change_requested": False,
        "response_text_change_requested": False,
        "classifier_change_requested": False,
        "retrieval_change_requested": False,
        "review_html_created": False,
        "recommended_next_checkpoint": NEXT_CHECKPOINT_ID,
        "recommended_next_checkpoint_requires_human_review": True,
        "inventory_targets": [
            "current unknown-runtime-signal turns",
            "guided option selection candidate",
            "plan option difference candidate",
            "recommendation request candidate",
            "next-step clarity candidate",
            "deferral candidate",
            "protected boundary controls",
        ],
    }


def runtime_decision_for(item: dict[str, Any]) -> dict[str, Any]:
    decision = build_runtime_decision(
        {
            "case_id": item["case_id"],
            "customer_input": {
                "input_type": item.get("input_type", "speech"),
                "transcript": item.get("customer_turn", ""),
                "stage": item.get("stage", "objection-handling"),
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


def build_unknown_probe_results() -> dict[str, Any]:
    observed = []
    for item in UNKNOWN_CASES:
        runtime = runtime_decision_for(item)
        observed.append(
            {
                **item,
                "observed_sales_difficulty": runtime["sales_difficulty"],
                "observed_runtime": runtime,
                "stays_unknown_runtime_signal": runtime["sales_difficulty"] == "unknown-runtime-signal",
            }
        )
    unknown_cases = [item for item in observed if item["stays_unknown_runtime_signal"]]
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "case_count": len(observed),
        "unknown_runtime_signal_case_count": len(unknown_cases),
        "unknown_cases": unknown_cases,
        "non_unknown_cases": [item for item in observed if not item["stays_unknown_runtime_signal"]],
    }


def build_subtype_inventory(probes: dict[str, Any]) -> dict[str, Any]:
    counts: dict[str, int] = {}
    examples: dict[str, list[str]] = {}
    for item in probes["unknown_cases"]:
        subtype_id = item["subtype_id"]
        counts[subtype_id] = counts.get(subtype_id, 0) + 1
        examples.setdefault(subtype_id, []).append(item["customer_turn"])

    subtypes = [
        {
            "subtype_id": "guided_option_selection_candidate",
            "unknown_case_count": counts.get("guided_option_selection_candidate", 0),
            "example_turns": examples.get("guided_option_selection_candidate", []),
            "status": "selected_for_human_review_before_probe",
            "why_selected": "Tarik explicitly raised this persuasion tactic, and it changes choice architecture rather than only wording.",
            "required_review_guardrails": [
                "two real options",
                "fair presentation",
                "neither",
                "not now",
                "explain the difference",
                "no fake urgency",
                "no pretend agreement",
                "no payment collection",
                "no contract signing",
            ],
            "requires_human_review_before_probe": True,
            "runtime_patch_allowed": False,
        },
        {
            "subtype_id": "plan_option_difference",
            "unknown_case_count": counts.get("plan_option_difference", 0),
            "example_turns": examples.get("plan_option_difference", []),
            "status": "candidate_after_guided_option_review",
            "why_deferred": "Plan differences require product-specific comparison content and should not be invented by the runtime.",
            "requires_human_review_before_probe": True,
            "runtime_patch_allowed": False,
        },
        {
            "subtype_id": "recommendation_request",
            "unknown_case_count": counts.get("recommendation_request", 0),
            "example_turns": examples.get("recommendation_request", []),
            "status": "defer_until_advice_boundary_defined",
            "why_deferred": "A direct recommendation can turn into advice or authority pressure if it is not framed as fit clarification.",
            "requires_human_review_before_probe": True,
            "runtime_patch_allowed": False,
        },
        {
            "subtype_id": "next_step_clarity",
            "unknown_case_count": counts.get("next_step_clarity", 0),
            "example_turns": examples.get("next_step_clarity", []),
            "status": "candidate_for_later_process_clarity_probe",
            "why_deferred": "This likely needs a process-clarity response, but it is less urgent than the explicitly requested persuasion-tactic review.",
            "requires_human_review_before_probe": False,
            "runtime_patch_allowed": False,
        },
        {
            "subtype_id": "deferral_or_choose_later",
            "unknown_case_count": counts.get("deferral_or_choose_later", 0),
            "example_turns": examples.get("deferral_or_choose_later", []),
            "status": "candidate_for_autonomy_route_review",
            "why_deferred": "This overlaps with autonomy-check but does not currently hit the exact trigger; broadening should wait until option-choice guardrails are reviewed.",
            "requires_human_review_before_probe": False,
            "runtime_patch_allowed": False,
        },
        {
            "subtype_id": "unclear_interest_probe",
            "unknown_case_count": counts.get("unclear_interest_probe", 0),
            "example_turns": examples.get("unclear_interest_probe", []),
            "status": "keep_unknown_for_now",
            "why_deferred": "Generic confusion is currently safer as a clarification fallback.",
            "requires_human_review_before_probe": False,
            "runtime_patch_allowed": False,
        },
    ]
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "subtypes": subtypes,
        "subtype_count": len(subtypes),
    }


def build_protected_boundary_results() -> dict[str, Any]:
    items = []
    for item in PROTECTED_CONTROLS:
        runtime = runtime_decision_for(item)
        passed = runtime["sales_difficulty"] == item["expected_sales_difficulty"]
        items.append(
            {
                **item,
                "input_type": item.get("input_type", "speech"),
                "observed_sales_difficulty": runtime["sales_difficulty"],
                "observed_runtime": runtime,
                "passed": passed,
                "issue_codes": [] if passed else ["sales_difficulty_mismatch"],
            }
        )
    failed = [item for item in items if not item["passed"]]
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "items": items,
        "control_count": len(items),
        "failed_control_count": len(failed),
        "failed_control_case_ids": [item["case_id"] for item in failed],
    }


def build_slice_decision(inventory: dict[str, Any], controls: dict[str, Any]) -> dict[str, Any]:
    selected = [item for item in inventory["subtypes"] if item["subtype_id"] == "guided_option_selection_candidate"][0]
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "decision": "select_guided_option_selection_review_next",
        "selected_next_subtype": selected["subtype_id"],
        "why": "This is the smallest concrete unknown subtype that matches Tarik's explicit future persuasion-tactic request, but it needs owner review before any probe because it shapes the customer's choice frame.",
        "required_guardrails": selected["required_review_guardrails"],
        "protected_boundary_controls_passed": controls["failed_control_count"] == 0,
        "runtime_patch_allowed": False,
        "response_text_change_allowed": False,
        "classifier_change_allowed": False,
        "review_html_created": False,
        "recommended_next_checkpoint": NEXT_CHECKPOINT_ID,
        "recommended_next_checkpoint_requires_human_review": True,
    }


def build_evidence_summary(
    source_result: dict[str, Any],
    source_selection: dict[str, Any],
    source_snapshot: dict[str, Any],
    source_validator: dict[str, Any],
) -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "source_validation": source_result["validation"],
        "source_selection": {
            "selected_next_slice": source_selection["selected_next_slice"],
            "protected_boundary_controls_required": source_selection["protected_boundary_controls_required"],
            "recommended_next_checkpoint": source_selection["recommended_next_checkpoint"],
        },
        "source_snapshot": {
            "reachable_sales_difficulty_count": source_snapshot["reachable_sales_difficulty_count"],
            "unreachable_localized_response_types": source_snapshot["unreachable_localized_response_types"],
            "unknown_runtime_signal_reachable": "unknown-runtime-signal" in source_snapshot["reachable_sales_difficulties"],
        },
        "source_validator_run": source_validator,
    }


def summarize(
    probes: dict[str, Any],
    inventory: dict[str, Any],
    controls: dict[str, Any],
    decision: dict[str, Any],
    source_validator: dict[str, Any],
) -> dict[str, Any]:
    return {
        "inventory_only": True,
        "source_validator_passed": source_validator["passed"],
        "selected_source_slice": "unknown_runtime_signal_subtypes",
        "unknown_subtype_count": inventory["subtype_count"],
        "unknown_runtime_signal_case_count": probes["unknown_runtime_signal_case_count"],
        "protected_boundary_control_count": controls["control_count"],
        "failed_protected_boundary_control_count": controls["failed_control_count"],
        "selected_next_subtype": decision["selected_next_subtype"],
        "requires_human_review_before_next_checkpoint": False,
        "recommended_next_checkpoint_requires_human_review": True,
        "review_html_created": False,
        "recommended_next_checkpoint": NEXT_CHECKPOINT_ID,
        **BOUNDARY_FLAGS,
    }


def render_report(
    summary: dict[str, Any],
    probes: dict[str, Any],
    inventory: dict[str, Any],
    controls: dict[str, Any],
    decision: dict[str, Any],
) -> str:
    lines = [
        "# PROD-081 English Unknown Runtime Signal Subtype Inventory",
        "",
        "`PROD-081` inventories English turns that still fall through to `unknown-runtime-signal` before any further customer-move classifier patch.",
        "",
        "This checkpoint is inventory-only. It creates no review HTML because the inventory itself does not need review; it selects a review-gated next checkpoint.",
        "",
        "## Summary",
        "",
        f"- Inventory only: `{str(summary['inventory_only']).lower()}`",
        f"- Selected source slice: `{summary['selected_source_slice']}`",
        f"- Unknown runtime-signal case count: `{summary['unknown_runtime_signal_case_count']}`",
        f"- Unknown subtype count: `{summary['unknown_subtype_count']}`",
        f"- Protected boundary controls: `{summary['protected_boundary_control_count']}`",
        f"- Failed protected boundary controls: `{summary['failed_protected_boundary_control_count']}`",
        f"- Selected next subtype: `{summary['selected_next_subtype']}`",
        f"- Recommended next checkpoint requires human review: `{str(summary['recommended_next_checkpoint_requires_human_review']).lower()}`",
        f"- Review HTML created: `{str(summary['review_html_created']).lower()}`",
        f"- Recommended next checkpoint: `{summary['recommended_next_checkpoint']}`",
        "- Runtime behavior changed: `false`",
        "- Response text behavior changed: `false`",
        "- Classifier behavior changed: `false`",
        "- Retrieval enabled: `false`",
        "- Production runtime promotion allowed: `false`",
        "",
        "## Subtypes",
        "",
    ]
    for item in inventory["subtypes"]:
        lines.extend(
            [
                f"### {item['subtype_id']}",
                "",
                f"- Unknown cases: `{item['unknown_case_count']}`",
                f"- Status: `{item['status']}`",
                f"- Requires human review before probe: `{str(item['requires_human_review_before_probe']).lower()}`",
                f"- Runtime patch allowed: `{str(item['runtime_patch_allowed']).lower()}`",
            ]
        )
        if "why_selected" in item:
            lines.append(f"- Why selected: {item['why_selected']}")
        if "why_deferred" in item:
            lines.append(f"- Why deferred: {item['why_deferred']}")
        if item["subtype_id"] == "guided_option_selection_candidate":
            lines.extend(
                [
                    "- Guardrails: two real options; fair presentation; `neither`; `not now`; `explain the difference`; no fake urgency; no pretend agreement.",
                    "",
                ]
            )
        else:
            lines.append("")
    lines.extend(
        [
            "## Unknown Probe Cases",
            "",
        ]
    )
    for item in probes["unknown_cases"]:
        lines.extend(
            [
                f"- `{item['case_id']}` / `{item['subtype_id']}` -> `{item['observed_sales_difficulty']}`: {item['customer_turn']}",
            ]
        )
    lines.extend(
        [
            "",
            "## Protected Boundary Controls",
            "",
        ]
    )
    for item in controls["items"]:
        lines.append(
            f"- `{item['case_id']}` expected `{item['expected_sales_difficulty']}`, observed `{item['observed_sales_difficulty']}`, passed `{str(item['passed']).lower()}`"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Decision: `{decision['decision']}`",
            f"- Selected next subtype: `{decision['selected_next_subtype']}`",
            f"- Runtime patch allowed: `{str(decision['runtime_patch_allowed']).lower()}`",
            f"- Classifier change allowed: `{str(decision['classifier_change_allowed']).lower()}`",
            f"- Recommended next checkpoint: `{decision['recommended_next_checkpoint']}`",
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
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    source_result, source_selection, source_snapshot = load_source()
    source_validator = run_source_validator()
    probes = build_unknown_probe_results()
    inventory = build_subtype_inventory(probes)
    controls = build_protected_boundary_results()
    decision = build_slice_decision(inventory, controls)
    evidence = build_evidence_summary(source_result, source_selection, source_snapshot, source_validator)
    summary = summarize(probes, inventory, controls, decision, source_validator)
    result = {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "validation": {
            "passed": (
                source_validator["passed"]
                and probes["unknown_runtime_signal_case_count"] >= 8
                and controls["failed_control_count"] == 0
                and decision["selected_next_subtype"] == "guided_option_selection_candidate"
            ),
            "inventory_passed": probes["unknown_runtime_signal_case_count"] >= 8 and controls["failed_control_count"] == 0,
        },
        "summary": summary,
    }
    write_json(CASE_FILE, build_case_file())
    write_json(OUT_DIR / "unknown_signal_probe_results.json", probes)
    write_json(OUT_DIR / "unknown_runtime_signal_subtype_inventory.json", inventory)
    write_json(OUT_DIR / "protected_boundary_control_results.json", controls)
    write_json(OUT_DIR / "slice_decision.json", decision)
    write_json(OUT_DIR / "evidence_summary.json", evidence)
    write_text(OUT_DIR / "report.md", render_report(summary, probes, inventory, controls, decision))
    write_json(OUT_DIR / "result.json", result)
    print(json.dumps({"checkpoint_id": CHECKPOINT_ID, "validation": result["validation"], "summary": summary}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
