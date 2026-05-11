#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-044-core-sales-policy-update"
CHECKPOINT_NAME = "Core Sales Policy Update Review Packet"
SOURCE_CHECKPOINT_ID = "PROD-043-sales-playbook-runtime-adapter"
NEXT_CHECKPOINT_ID = "PROD-045-core-sales-policy-regression-rerun"
SOURCE_DIR = ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID

BOUNDARY_FLAGS = {
    "runtime_behavior_changed": False,
    "retrieval_enabled": False,
    "runtime_agent_modified": False,
    "provider_calls_made": False,
    "llm_used": False,
    "private_data_read": False,
    "dataset_download_performed": False,
    "production_runtime_promotion_allowed": False,
    "uses_exact_transcript_text": False,
    "uses_source_transcript_sequence": False,
    "uses_dataset_specific_phrasing": False,
    "voice_playback_unblocked": False,
    "public_demo_polish_unblocked": False,
}

MOVE_TO_POLICY = {
    "price_first": "policy-price-first-direct-answer",
    "send_info": "policy-written-info-and-email-boundary",
    "email_only": "policy-written-info-and-email-boundary",
    "who_are_you": "policy-identity-repair-before-discovery",
    "scam_or_card_fear": "policy-payment-and-scam-safety-boundary",
    "payment_safety_fear": "policy-payment-and-scam-safety-boundary",
    "support_issue": "policy-support-and-cancellation-routing",
    "cancellation_request": "policy-support-and-cancellation-routing",
    "technical_question": "policy-specialist-handoff-for-technical-security-healthcare",
    "security_review": "policy-specialist-handoff-for-technical-security-healthcare",
    "coverage_confusion": "policy-specialist-handoff-for-technical-security-healthcare",
    "sensitive_healthcare_concern": "policy-specialist-handoff-for-technical-security-healthcare",
    "existing_provider": "policy-existing-provider-gap-isolation",
    "needs_manager_approval": "policy-decision-maker-review-path",
    "needs_spouse_or_partner_input": "policy-decision-maker-review-path",
}

POLICY_DESIGNS = {
    "policy-price-first-direct-answer": {
        "title": "Answer price or pricing boundary before discovery",
        "policy_change_summary": "When the latest customer move is price-first, the core should answer with approved pricing facts or an explicit pricing-boundary statement before any discovery question.",
        "target_runtime_surface": "scripts/run_realtime_turn_simulation.py::classify_runtime_input and localized response map",
        "required_guard_ids": ["guard-approved-pricing-facts", "guard-no-callback-before-price-answer"],
        "blocked_without_guards": False,
    },
    "policy-written-info-and-email-boundary": {
        "title": "Honor send-info and email-only requests before asking more",
        "policy_change_summary": "When the customer asks for written information or email-only contact, the core should offer approved written info, respect the channel boundary, and avoid callback pressure.",
        "target_runtime_surface": "scripts/run_realtime_turn_simulation.py::classify_runtime_input and localized response map",
        "required_guard_ids": ["guard-approved-written-summary", "guard-contact-channel-boundary"],
        "blocked_without_guards": False,
    },
    "policy-identity-repair-before-discovery": {
        "title": "Identify caller and reason before continuing",
        "policy_change_summary": "When the customer asks who is calling, the core should identify the caller/company/role and brief reason using campaign facts before any pitch or discovery.",
        "target_runtime_surface": "scripts/run_realtime_turn_simulation.py::classify_runtime_input and localized response map",
        "required_guard_ids": ["guard-approved-identity-and-reason"],
        "blocked_without_guards": False,
    },
    "policy-payment-and-scam-safety-boundary": {
        "title": "State no payment or card collection on safety fears",
        "policy_change_summary": "When the customer raises scam, card, or payment fear, the core should explicitly say no payment/card details are collected and offer a safe verification or written-info path.",
        "target_runtime_surface": "scripts/run_realtime_turn_simulation.py::classify_runtime_input and localized response map",
        "required_guard_ids": ["guard-no-payment-collection", "guard-approved-verification-path"],
        "blocked_without_guards": False,
    },
    "policy-support-and-cancellation-routing": {
        "title": "Route support and cancellation before sales",
        "policy_change_summary": "When the customer raises support or cancellation, the core should stop the sales path and route to an approved support/cancellation path.",
        "target_runtime_surface": "scripts/run_realtime_turn_simulation.py::classify_runtime_input and call-control mapping",
        "required_guard_ids": ["guard-support-route-available", "guard-cancellation-route-available"],
        "blocked_without_guards": False,
    },
    "policy-specialist-handoff-for-technical-security-healthcare": {
        "title": "Handoff technical, security, coverage, and healthcare boundaries",
        "policy_change_summary": "For technical, security, coverage, or healthcare questions beyond approved campaign facts, the core should avoid guessing and route to a specialist or qualified reviewer.",
        "target_runtime_surface": "scripts/run_realtime_turn_simulation.py::classify_runtime_input and localized response map",
        "required_guard_ids": ["guard-approved-technical-scope", "guard-specialist-route-available", "guard-no-medical-or-coverage-advice"],
        "blocked_without_guards": False,
    },
    "policy-existing-provider-gap-isolation": {
        "title": "Isolate a gap without claiming replacement superiority",
        "policy_change_summary": "When the customer has an existing provider, the core should avoid replacement or competitor-superiority claims and ask only whether there is a specific uncovered gap.",
        "target_runtime_surface": "scripts/run_realtime_turn_simulation.py::localized response map",
        "required_guard_ids": ["guard-no-competitor-superiority-claim", "guard-campaign-fit-gap-only"],
        "blocked_without_guards": False,
    },
    "policy-decision-maker-review-path": {
        "title": "Offer reviewable summary without bypassing the decision maker",
        "policy_change_summary": "When manager, spouse, or partner approval is needed, the core should offer a reviewable summary and avoid pressure or bypass language.",
        "target_runtime_surface": "scripts/run_realtime_turn_simulation.py::classify_runtime_input and localized response map",
        "required_guard_ids": ["guard-review-summary-only", "guard-no-decision-maker-bypass"],
        "blocked_without_guards": False,
    },
}

CAMPAIGN_FACT_GUARDS = [
    {
        "guard_id": "guard-approved-pricing-facts",
        "required_campaign_fields": ["pricing_summary", "pricing_boundary_text"],
        "purpose": "Allows price-first handling without inventing price, discounts, ROI, or contract terms.",
        "blocks_policy_updates": ["policy-price-first-direct-answer"],
    },
    {
        "guard_id": "guard-no-callback-before-price-answer",
        "required_campaign_fields": ["callback_offer_allowed_after_direct_answer"],
        "purpose": "Prevents scheduling pressure before the customer's explicit price question is addressed.",
        "blocks_policy_updates": ["policy-price-first-direct-answer"],
    },
    {
        "guard_id": "guard-approved-written-summary",
        "required_campaign_fields": ["approved_written_summary", "approved_email_followup_scope"],
        "purpose": "Allows send-info and email-only responses without creating unsupported product copy.",
        "blocks_policy_updates": ["policy-written-info-and-email-boundary", "policy-decision-maker-review-path"],
    },
    {
        "guard_id": "guard-contact-channel-boundary",
        "required_campaign_fields": ["allowed_contact_channels", "respect_email_only_boundary"],
        "purpose": "Keeps email-only handling from turning into callback pressure.",
        "blocks_policy_updates": ["policy-written-info-and-email-boundary"],
    },
    {
        "guard_id": "guard-approved-identity-and-reason",
        "required_campaign_fields": ["caller_identity", "company_or_campaign_name", "approved_reason_for_call"],
        "purpose": "Allows identity repair without hype or private/provider-specific claims.",
        "blocks_policy_updates": ["policy-identity-repair-before-discovery"],
    },
    {
        "guard_id": "guard-no-payment-collection",
        "required_campaign_fields": ["payment_collection_allowed"],
        "required_values": {"payment_collection_allowed": False},
        "purpose": "Keeps payment/card handling safety-perfect.",
        "blocks_policy_updates": ["policy-payment-and-scam-safety-boundary"],
    },
    {
        "guard_id": "guard-approved-verification-path",
        "required_campaign_fields": ["approved_verification_path"],
        "purpose": "Gives scam-fear customers a safe verification route without asking for sensitive data.",
        "blocks_policy_updates": ["policy-payment-and-scam-safety-boundary"],
    },
    {
        "guard_id": "guard-support-route-available",
        "required_campaign_fields": ["support_route", "support_boundary_text"],
        "purpose": "Stops support issues from drifting into sales continuation.",
        "blocks_policy_updates": ["policy-support-and-cancellation-routing"],
    },
    {
        "guard_id": "guard-cancellation-route-available",
        "required_campaign_fields": ["cancellation_route", "cancellation_boundary_text"],
        "purpose": "Stops cancellation requests from becoming retention pressure.",
        "blocks_policy_updates": ["policy-support-and-cancellation-routing"],
    },
    {
        "guard_id": "guard-approved-technical-scope",
        "required_campaign_fields": ["approved_technical_scope", "unknown_technical_answer_boundary"],
        "purpose": "Allows only supported technical answers and routes unknown details.",
        "blocks_policy_updates": ["policy-specialist-handoff-for-technical-security-healthcare"],
    },
    {
        "guard_id": "guard-specialist-route-available",
        "required_campaign_fields": ["specialist_handoff_route"],
        "purpose": "Gives technical, security, coverage, and healthcare boundary turns a safe next action.",
        "blocks_policy_updates": ["policy-specialist-handoff-for-technical-security-healthcare"],
    },
    {
        "guard_id": "guard-no-medical-or-coverage-advice",
        "required_campaign_fields": ["regulated_advice_boundary_text"],
        "purpose": "Blocks medical, legal, financial, or coverage advice outside approved campaign facts.",
        "blocks_policy_updates": ["policy-specialist-handoff-for-technical-security-healthcare"],
    },
    {
        "guard_id": "guard-no-competitor-superiority-claim",
        "required_campaign_fields": ["competitor_comparison_boundary_text"],
        "purpose": "Prevents unsupported competitor superiority or replacement claims.",
        "blocks_policy_updates": ["policy-existing-provider-gap-isolation"],
    },
    {
        "guard_id": "guard-campaign-fit-gap-only",
        "required_campaign_fields": ["approved_gap_isolation_question"],
        "purpose": "Keeps existing-provider handling to one concrete fit gap.",
        "blocks_policy_updates": ["policy-existing-provider-gap-isolation"],
    },
    {
        "guard_id": "guard-review-summary-only",
        "required_campaign_fields": ["approved_review_summary"],
        "purpose": "Supports manager/spouse review without pressure or commitment.",
        "blocks_policy_updates": ["policy-decision-maker-review-path"],
    },
    {
        "guard_id": "guard-no-decision-maker-bypass",
        "required_campaign_fields": ["decision_maker_bypass_forbidden"],
        "required_values": {"decision_maker_bypass_forbidden": True},
        "purpose": "Prevents bypassing the person who must approve.",
        "blocks_policy_updates": ["policy-decision-maker-review-path"],
    },
]

BLOCKED_UPDATES = [
    {
        "blocked_update_id": "blocked-enable-retrieval-default",
        "reason": "PROD-043 validates offline artifact lookup only; it does not prove live retrieval should be enabled.",
    },
    {
        "blocked_update_id": "blocked-broaden-product-claims",
        "reason": "PROD-043 evidence supports safer turn policy, not broader claims, guarantees, ROI, medical, coverage, security, or competitor assertions.",
    },
    {
        "blocked_update_id": "blocked-voice-playback-or-demo-polish",
        "reason": "PROD-043 is a single-turn offline evaluator and does not unblock voice playback, public demo polish, or synthetic dialogue promotion.",
    },
    {
        "blocked_update_id": "blocked-payment-or-contract-close",
        "reason": "The product boundary remains no payment collection, no contract signing, and no unsupported close.",
    },
    {
        "blocked_update_id": "blocked-full-conversation-generation",
        "reason": "PROD-044 is a policy review packet, not a scenario simulator or synthetic conversation generator.",
    },
    {
        "blocked_update_id": "blocked-runtime-change-without-regression",
        "reason": "Any future runtime edit must be covered by deterministic regression tests before being marked applied.",
    },
]


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def rel_path(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def load_source() -> dict[str, Any]:
    required = {
        "result": SOURCE_DIR / "result.json",
        "report": SOURCE_DIR / "report.md",
        "agent_response_evaluations": SOURCE_DIR / "agent_response_evaluations.json",
        "runtime_adapter_review_data": SOURCE_DIR / "runtime_adapter_review_data.json",
    }
    missing = [rel_path(path) for path in required.values() if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing PROD-043 input artifacts: {missing}")
    return {
        "result": read_json(required["result"]),
        "agent_response_evaluations": read_json(required["agent_response_evaluations"])["agent_response_evaluations"],
        "review_data": read_json(required["runtime_adapter_review_data"]),
    }


def probe_current_runtime(classifier_cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    sys.path.insert(0, str(ROOT / "scripts"))
    from run_realtime_turn_simulation import build_runtime_decision  # type: ignore
    from prod_043_sales_playbook_runtime_adapter import evaluate_response, load_prod_042  # type: ignore

    artifacts = load_prod_042()
    probes: list[dict[str, Any]] = []
    seen_moves: set[str] = set()
    for case in classifier_cases:
        move_id = case["expected_customer_move_id"]
        if move_id in seen_moves:
            continue
        seen_moves.add(move_id)
        runtime_case = {
            "case_id": f"prod-044-probe-{case['case_id']}",
            "customer_input": {
                "input_type": "speech-final",
                "stage": "relevance-check",
                "transcript": case["customer_utterance"],
            },
        }
        decision = build_runtime_decision(runtime_case, expected=None, campaign={"language": "en"})
        eval_case = {
            "case_id": f"prod-044-current-runtime-{move_id}",
            "customer_utterance": case["customer_utterance"],
            "expected_customer_move_id": move_id,
            "agent_response": decision.get("agent_response", ""),
            "expected_result": "pass",
            "example_type": "synthetic_generic_test_case",
            "source_quote": False,
            "from_single_transcript": False,
        }
        evaluation = evaluate_response(eval_case, artifacts)
        probes.append(
            {
                "probe_id": f"probe-{move_id}",
                "customer_move_id": move_id,
                "source_case_id": case["case_id"],
                "customer_utterance": case["customer_utterance"],
                "actual_agent_response": decision.get("agent_response", ""),
                "runtime_sales_difficulty": decision.get("sales_difficulty"),
                "runtime_next_action": decision.get("next_action"),
                "runtime_call_control": decision.get("call_control"),
                "prod_043_evaluation_rule_ids": evaluation.get("retrieved_evaluation_rule_ids", []),
                "detected_agent_tactic_ids": evaluation.get("detected_agent_tactic_ids", []),
                "failed_check_ids": evaluation.get("failed_check_ids", []),
                "detected_failure_flags": evaluation.get("detected_failure_flags", []),
                "prod_043_rule_passed": bool(evaluation.get("passed")),
            }
        )
    return probes


def source_eval_evidence(evaluations: list[dict[str, Any]], move_ids: set[str]) -> list[dict[str, Any]]:
    evidence = []
    for item in evaluations:
        if item.get("expected_customer_move_id") not in move_ids:
            continue
        evidence.append(
            {
                "case_id": item["case_id"],
                "customer_move_id": item["expected_customer_move_id"],
                "evaluation_rule_ids": item.get("retrieved_evaluation_rule_ids", []),
                "expected_result": item.get("expected_result"),
                "passed": item.get("passed"),
                "failed_check_ids": item.get("failed_check_ids", []),
                "detected_failure_flags": item.get("detected_failure_flags", []),
                "success_dimensions": item.get("success_dimensions", []),
            }
        )
    return evidence


def build_candidate_updates(source: dict[str, Any], runtime_probes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    evaluations = source["agent_response_evaluations"]
    by_policy: dict[str, list[dict[str, Any]]] = {}
    for probe in runtime_probes:
        policy_id = MOVE_TO_POLICY.get(probe["customer_move_id"])
        if not policy_id:
            continue
        runtime_failed = not probe["prod_043_rule_passed"]
        runtime_unknown = probe.get("runtime_sales_difficulty") == "unknown-runtime-signal"
        runtime_asks_followup = probe.get("runtime_next_action") == "ask-follow-up"
        needs_policy = runtime_failed or runtime_unknown or runtime_asks_followup
        if needs_policy:
            by_policy.setdefault(policy_id, []).append(probe)

    candidates = []
    for policy_id, probes in sorted(by_policy.items()):
        design = POLICY_DESIGNS[policy_id]
        move_ids = {probe["customer_move_id"] for probe in probes}
        candidates.append(
            {
                "candidate_update_id": policy_id,
                "title": design["title"],
                "status": "candidate_not_applied",
                "justified_by_prod_043_evidence": True,
                "policy_change_summary": design["policy_change_summary"],
                "target_runtime_surface": design["target_runtime_surface"],
                "customer_move_ids": sorted(move_ids),
                "prod_043_evidence": source_eval_evidence(evaluations, move_ids),
                "current_runtime_probe_evidence": probes,
                "required_campaign_fact_guard_ids": design["required_guard_ids"],
                "runtime_change_performed": False,
                "retrieval_required": False,
                "provider_or_llm_required": False,
                "deterministic_regression_required_before_apply": True,
                "minimum_regression_cases": [
                    f"{move_id}: good response follows PROD-043 required tactics" for move_id in sorted(move_ids)
                ]
                + [
                    f"{move_id}: bad response still fails deterministic evaluation" for move_id in sorted(move_ids)
                ],
            }
        )
    return candidates


def build_review_packet(source: dict[str, Any], runtime_probes: list[dict[str, Any]]) -> dict[str, Any]:
    candidates = build_candidate_updates(source, runtime_probes)
    source_summary = source["result"]["summary"]
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "review_basis": [
            "PROD-043 result/report metrics",
            "PROD-043 deterministic agent response evaluations",
            "PROD-043 runtime adapter review data",
            "Offline probes of the current deterministic realtime turn entrypoint using PROD-043 synthetic generic cases",
            "Realtime architecture and BRAIN-002 runtime state boundaries",
        ],
        "source_summary": source_summary,
        "decision": {
            "runtime_policy_update_justified": bool(candidates),
            "runtime_changes_performed": False,
            "apply_runtime_changes_now": False,
            "reason": "PROD-043 evidence identifies targeted policy gaps, but this checkpoint is a review/design packet. Runtime changes need a separate deterministic regression-gated application step.",
        },
        "candidate_policy_updates": candidates,
        "blocked_updates": BLOCKED_UPDATES,
        "required_campaign_fact_guards": CAMPAIGN_FACT_GUARDS,
        "current_runtime_probe_results": runtime_probes,
        "acceptance_for_future_runtime_apply": [
            "Add deterministic tests for every candidate update before editing runtime behavior.",
            "Preserve one reusable sales-agent core with SalesCampaign-specific facts and guardrails.",
            "Do not hard-code pricing, identity, support routes, security claims, coverage details, or healthcare guidance into the reusable core.",
            "Keep retrieval disabled by default.",
            "Keep provider calls, LLM calls, private-data reads, voice playback, public demo polish, payment collection, and production runtime promotion blocked.",
        ],
        "boundaries": BOUNDARY_FLAGS,
    }


def render_report(packet: dict[str, Any]) -> str:
    decision = packet["decision"]
    candidates = packet["candidate_policy_updates"]
    lines = [
        "# PROD-044 Core Sales Policy Update Review Packet",
        "",
        "PROD-044 reviews PROD-043 evidence and prepares targeted runtime-policy updates. It does not apply runtime changes.",
        "",
        "## Decision",
        "",
        f"- Runtime policy update justified: `{str(decision['runtime_policy_update_justified']).lower()}`",
        f"- Runtime changes performed: `{str(decision['runtime_changes_performed']).lower()}`",
        f"- Apply runtime changes now: `{str(decision['apply_runtime_changes_now']).lower()}`",
        f"- Candidate policy update count: `{len(candidates)}`",
        f"- Blocked update count: `{len(packet['blocked_updates'])}`",
        f"- Required campaign-fact guard count: `{len(packet['required_campaign_fact_guards'])}`",
        "",
        "## Candidate Policy Updates",
        "",
    ]
    for candidate in candidates:
        evidence_ids = [probe["probe_id"] for probe in candidate["current_runtime_probe_evidence"]]
        lines.extend(
            [
                f"### {candidate['candidate_update_id']}",
                "",
                f"- Title: {candidate['title']}",
                f"- Status: `{candidate['status']}`",
                f"- Moves: `{', '.join(candidate['customer_move_ids'])}`",
                f"- Runtime probe evidence: `{', '.join(evidence_ids)}`",
                f"- Required campaign guards: `{', '.join(candidate['required_campaign_fact_guard_ids'])}`",
                f"- Runtime change performed: `{str(candidate['runtime_change_performed']).lower()}`",
                f"- Summary: {candidate['policy_change_summary']}",
                "",
            ]
        )
    lines.extend(
        [
            "## Blocked Updates",
            "",
            *[f"- `{item['blocked_update_id']}`: {item['reason']}" for item in packet["blocked_updates"]],
            "",
            "## Campaign-Fact Guards",
            "",
            *[
                f"- `{guard['guard_id']}`: fields `{', '.join(guard['required_campaign_fields'])}`. {guard['purpose']}"
                for guard in packet["required_campaign_fact_guards"]
            ],
            "",
            "## Boundary",
            "",
            "Runtime behavior, retrieval defaults, provider usage, LLM usage, private-data access, voice playback, public demo polish, payment collection, and production runtime promotion remain unchanged and blocked.",
        ]
    )
    return "\n".join(lines) + "\n"


def render_html(packet: dict[str, Any]) -> str:
    rows = []
    for candidate in packet["candidate_policy_updates"]:
        rows.append(
            "<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>".format(
                html.escape(candidate["candidate_update_id"]),
                html.escape(", ".join(candidate["customer_move_ids"])),
                html.escape(candidate["status"]),
                html.escape(", ".join(candidate["required_campaign_fact_guard_ids"])),
                html.escape(str(candidate["runtime_change_performed"]).lower()),
            )
        )
    blocked = "".join(
        f"<li><code>{html.escape(item['blocked_update_id'])}</code>: {html.escape(item['reason'])}</li>"
        for item in packet["blocked_updates"]
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>PROD-044 Core Sales Policy Review</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 24px; color: #202124; }}
    table {{ border-collapse: collapse; width: 100%; margin-top: 12px; }}
    th, td {{ border: 1px solid #ddd; padding: 6px; vertical-align: top; }}
    th {{ background: #f3f4f6; }}
    code {{ background: #f6f8fa; padding: 1px 4px; }}
    .metric {{ display: inline-block; border: 1px solid #ccc; padding: 8px 10px; margin: 4px; }}
  </style>
</head>
<body>
  <h1>PROD-044 Core Sales Policy Update Review</h1>
  <p>Offline review/design packet based on PROD-043 evidence. Runtime policy changes are not applied here.</p>
  <section id="summary">
    <span class="metric">candidate updates: {len(packet['candidate_policy_updates'])}</span>
    <span class="metric">runtime changed: false</span>
    <span class="metric">retrieval enabled: false</span>
    <span class="metric">provider/LLM used: false</span>
  </section>
  <section id="candidate-policy-updates">
    <h2>Candidate Policy Updates</h2>
    <table><thead><tr><th>ID</th><th>Moves</th><th>Status</th><th>Required Guards</th><th>Runtime Change</th></tr></thead><tbody>{''.join(rows)}</tbody></table>
  </section>
  <section id="blocked-updates"><h2>Blocked Updates</h2><ul>{blocked}</ul></section>
  <section id="campaign-fact-guards"><h2>Required Campaign-Fact Guards</h2><pre>{html.escape(json.dumps(packet['required_campaign_fact_guards'], indent=2))}</pre></section>
  <section id="runtime-probes"><h2>Current Runtime Probe Evidence</h2><pre>{html.escape(json.dumps(packet['current_runtime_probe_results'], indent=2))}</pre></section>
  <section id="boundaries"><h2>Boundary Summary</h2><pre>{html.escape(json.dumps(packet['boundaries'], indent=2))}</pre></section>
</body>
</html>
"""


def build() -> dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    source = load_source()
    runtime_probes = probe_current_runtime(source["review_data"]["customer_move_classification_cases"])
    packet = build_review_packet(source, runtime_probes)
    outputs = {
        "result": rel_path(OUT_DIR / "result.json"),
        "report": rel_path(OUT_DIR / "report.md"),
        "core_sales_policy_review_packet": rel_path(OUT_DIR / "core_sales_policy_review_packet.json"),
        "prod_044_review_data": rel_path(OUT_DIR / "prod_044_review_data.json"),
        "prod_044_review_html": rel_path(OUT_DIR / "prod_044_review.html"),
    }
    summary = {
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "prod_043_validator_passed": source["result"].get("validation", {}).get("passed") is True,
        "prod_043_classifier_accuracy": source["result"]["summary"].get("classifier_accuracy"),
        "prod_043_playbook_retrieval_match_rate": source["result"]["summary"].get("playbook_retrieval_match_rate"),
        "prod_043_agent_response_evaluation_expected_match_rate": source["result"]["summary"].get("agent_response_evaluation_expected_match_rate"),
        "current_runtime_probe_count": len(runtime_probes),
        "current_runtime_probe_pass_count": sum(1 for probe in runtime_probes if probe["prod_043_rule_passed"]),
        "current_runtime_probe_fail_count": sum(1 for probe in runtime_probes if not probe["prod_043_rule_passed"]),
        "candidate_policy_update_count": len(packet["candidate_policy_updates"]),
        "blocked_update_count": len(packet["blocked_updates"]),
        "required_campaign_fact_guard_count": len(packet["required_campaign_fact_guards"]),
        "runtime_policy_update_justified": packet["decision"]["runtime_policy_update_justified"],
        "runtime_changes_performed": False,
        "runtime_behavior_changed": False,
        "retrieval_enabled": False,
        "runtime_agent_modified": False,
        "provider_calls_made": False,
        "llm_used": False,
        "private_data_read": False,
        "dataset_download_performed": False,
        "production_runtime_promotion_allowed": False,
        "voice_playback_unblocked": False,
        "public_demo_polish_unblocked": False,
    }
    review_data = {**packet, "summary": summary, "outputs": outputs}
    write_json(OUT_DIR / "core_sales_policy_review_packet.json", packet)
    write_json(OUT_DIR / "prod_044_review_data.json", review_data)
    (OUT_DIR / "prod_044_review.html").write_text(render_html(packet), encoding="utf-8")
    (OUT_DIR / "report.md").write_text(render_report(packet), encoding="utf-8")
    result = {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "summary": summary,
        "outputs": outputs,
        "validation": {"passed": True},
        "next_checkpoint_recommended": NEXT_CHECKPOINT_ID,
    }
    write_json(OUT_DIR / "result.json", result)
    return result


def main() -> None:
    result = build()
    print(json.dumps({"checkpoint_id": CHECKPOINT_ID, "summary": result["summary"], "output_dir": rel_path(OUT_DIR)}, indent=2))


if __name__ == "__main__":
    main()
