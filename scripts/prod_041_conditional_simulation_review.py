#!/usr/bin/env python3
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-041-conditional-simulation-review"
SOURCE_CHECKPOINT_ID = "PROD-041A-conditional-scenario-diversity-expansion"
DEFAULT_OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
DEFAULT_RESULT = DEFAULT_OUT_DIR / "result.json"
DEFAULT_REPORT = DEFAULT_OUT_DIR / "report.md"
DEFAULT_REVIEW_PACKET = DEFAULT_OUT_DIR / "conditional_simulation_review_packet.json"
DEFAULT_SOURCE_RESULT = ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "result.json"
DEFAULT_SOURCE_TRACE = ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "scenario_diversity_traces.json"

SAFE_CLOSE_OUTCOMES = {
    "accepted",
    "callback_scheduled",
    "written_info_requested",
    "manager_review_needed",
    "handoff_required",
}

TEMPLATE_LIKE_MARKERS = [
    "what happens next if i only want a light review",
    "so the next step is only about",
    "i can consider one narrow step",
    "that is clear enough on",
    "fine, keep it to that one point",
    "do not keep selling right now",
    "not sales wording",
    "send the short version and stop there",
    "no-pressure next step",
]

WEAK_SAFE_CLOSE_LABELS = {
    "price_sensitive": "Customer accepts callback after a still-formulaic light-review question.",
    "manager_review": "Manager path is plausible, but the repeated manager-review wording is too neat for voice.",
    "send_info": "Email-only request is realistic, but the final written-info close is still too orderly.",
    "hidden_objection": "Callback close is not fully earned because the budget/priority concern remains abstract.",
    "contract_fear": "Written-info close is safe, but the customer does not show enough real contract-friction resolution.",
    "no_pressure_consumer": "Acceptance is safe, but the final no-pressure wording still sounds review-oriented.",
}


def rel_path(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_boundaries() -> dict[str, bool]:
    return {
        "provider_calls_made": False,
        "llm_used": False,
        "private_data_read": False,
        "dataset_download_performed": False,
        "source_prod_041a_modified": False,
        "runtime_behavior_changed_by_this_checkpoint": False,
        "runtime_retrieval_default_enabled": False,
        "composer_hook_flag_default_enabled": False,
        "live_provider_default_enabled": False,
        "server_started": False,
        "payment_collection_enabled": False,
        "production_runtime_promotion_allowed": False,
    }


def customer_texts(call: dict[str, Any]) -> list[str]:
    return [item["text"] for item in call.get("conversation_sequence", []) if item.get("speaker") == "customer"]


def template_like_turns(calls: list[dict[str, Any]]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for call in calls:
        for text in customer_texts(call):
            lowered = text.lower()
            marker = next((item for item in TEMPLATE_LIKE_MARKERS if item in lowered), None)
            if marker:
                findings.append(
                    {
                        "scenario_label": call["scenario_label"],
                        "terminal_outcome": call["terminal_outcome"],
                        "marker": marker,
                        "customer_text": text,
                    }
                )
    return findings


def rewrite_candidates(calls: list[dict[str, Any]], template_findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_label = {finding["scenario_label"]: finding for finding in template_findings}
    candidates: list[dict[str, Any]] = []
    for label, reason in WEAK_SAFE_CLOSE_LABELS.items():
        finding = by_label.get(label)
        candidates.append(
            {
                "scenario_label": label,
                "reason": reason,
                "example_customer_text": finding["customer_text"] if finding else "",
                "required_rewrite_direction": "Rewrite the customer turn only; keep terminal outcome, safety counters, source checkpoint, and PROD-041A structure locked.",
            }
        )
    for call in calls:
        if call["dialogue_realism"]["score"] < 5 and call["scenario_label"] not in WEAK_SAFE_CLOSE_LABELS:
            candidates.append(
                {
                    "scenario_label": call["scenario_label"],
                    "reason": "Realism score is below perfect and the deterministic phrasing is still audible.",
                    "example_customer_text": customer_texts(call)[-1],
                    "required_rewrite_direction": "Use a targeted human rewrite before voice playback; do not add scenarios or change the safety outcome.",
                }
            )
    return candidates[:14]


def build_manual_findings(template_findings: list[dict[str, Any]], candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "finding_id": "deterministic-phrasing-still-audible",
            "severity": "major",
            "assessment": "The remaining deterministic phrasing is acceptable for an offline review artifact, but not for voice playback or demo use without targeted rewriting.",
        },
        {
            "finding_id": "template-like-customer-turns-remain",
            "severity": "major",
            "assessment": f"{len(template_findings)} customer turns still contain recognizable deterministic patterns such as light-review, one-point, next-step, or no-pressure phrasing.",
        },
        {
            "finding_id": "safe-close-outcomes-only-partly-earned",
            "severity": "major",
            "assessment": "The safe-close outcomes remain safety-correct, but several closes are too orderly: the customer often agrees to callback, written info, or review before enough natural friction has been resolved.",
        },
        {
            "finding_id": "targeted-rewrites-required-before-voice",
            "severity": "blocker",
            "assessment": f"{len(candidates)} traces should receive targeted customer-turn rewrites before voice playback or public demo use. PROD-041A should not be expanded or regenerated for this.",
        },
    ]


def build_review_packet(source_result: dict[str, Any], source_trace: dict[str, Any]) -> dict[str, Any]:
    calls = source_trace["calls"]
    template_findings = template_like_turns(calls)
    candidates = rewrite_candidates(calls, template_findings)
    terminal_counts = dict(Counter(call["terminal_outcome"] for call in calls))
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "review_basis": "Manual review pass over the locked PROD-041A expanded traces and review surface data.",
        "review_decision": {
            "prod_041a_locked": True,
            "do_not_expand_prod_041a": True,
            "remaining_deterministic_phrasing_acceptable": "offline-review-only",
            "safe_close_outcomes_earned": "partially",
            "targeted_rewrite_required_before_voice_or_demo": True,
            "voice_playback_unblocked": False,
            "scenario_branching_unblocked": False,
            "public_demo_polish_unblocked": False,
        },
        "source_metrics_locked": source_result["summary"],
        "terminal_outcome_counts": terminal_counts,
        "manual_review_findings": build_manual_findings(template_findings, candidates),
        "template_like_customer_turns": template_findings,
        "rewrite_candidates": candidates,
        "before_voice_or_demo_requirements": [
            "Do not expand or regenerate PROD-041A.",
            "Rewrite only the identified customer turns in a future targeted voice/demo readiness checkpoint.",
            "Keep terminal outcomes and safety counters unchanged unless a separate review explicitly changes them.",
            "Re-check whether safe closes feel earned after the targeted rewrites.",
        ],
    }


def build_summary(packet: dict[str, Any], calls: list[dict[str, Any]]) -> dict[str, Any]:
    source = packet["source_metrics_locked"]
    decision = packet["review_decision"]
    return {
        "reviewed_call_count": len(calls),
        "reviewed_b2b_call_count": sum(1 for call in calls if call["b2b_or_b2c"] == "B2B"),
        "reviewed_b2c_call_count": sum(1 for call in calls if call["b2b_or_b2c"] == "B2C"),
        "prod_041a_locked": decision["prod_041a_locked"],
        "remaining_deterministic_phrasing_acceptable": decision["remaining_deterministic_phrasing_acceptable"],
        "safe_close_outcomes_earned": decision["safe_close_outcomes_earned"],
        "targeted_rewrite_required_before_voice_or_demo": decision["targeted_rewrite_required_before_voice_or_demo"],
        "template_like_turn_count": len(packet["template_like_customer_turns"]),
        "rewrite_candidate_count": len(packet["rewrite_candidates"]),
        "voice_playback_unblocked": decision["voice_playback_unblocked"],
        "scenario_branching_unblocked": decision["scenario_branching_unblocked"],
        "public_demo_polish_unblocked": decision["public_demo_polish_unblocked"],
        "source_safe_close_rate": source["safe_close_rate"],
        "source_non_sale_correctness_rate": source["non_sale_correctness_rate"],
        "source_hard_failure_count": source["hard_failure_count"],
        "source_dialogue_realism_average_score": source["dialogue_realism_average_score"],
        "provider_calls_made": False,
        "llm_used": False,
        "runtime_behavior_changed": False,
    }


def build_payload(
    *,
    source_result_path: Path = DEFAULT_SOURCE_RESULT,
    source_trace_path: Path = DEFAULT_SOURCE_TRACE,
    result_path: Path = DEFAULT_RESULT,
    report_path: Path = DEFAULT_REPORT,
    review_packet_path: Path = DEFAULT_REVIEW_PACKET,
) -> tuple[dict[str, Any], dict[str, Any]]:
    source_result = read_json(source_result_path)
    source_trace = read_json(source_trace_path)
    packet = build_review_packet(source_result, source_trace)
    payload = {
        "checkpoint_id": CHECKPOINT_ID,
        "title": "PROD-041 conditional simulation review",
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "outputs": {
            "result_path": rel_path(result_path),
            "report_path": rel_path(report_path),
            "review_packet_path": rel_path(review_packet_path),
        },
        "source_inputs": {
            "source_result_path": rel_path(source_result_path),
            "source_trace_path": rel_path(source_trace_path),
        },
        "boundaries": build_boundaries(),
        "source_metrics_locked": source_result["summary"],
        "summary": build_summary(packet, source_trace["calls"]),
        "decision": packet["review_decision"],
    }
    return payload, packet


def render_report(payload: dict[str, Any], packet: dict[str, Any]) -> str:
    summary = payload["summary"]
    finding_lines = [
        f"- `{finding['finding_id']}` ({finding['severity']}): {finding['assessment']}"
        for finding in packet["manual_review_findings"]
    ]
    candidate_lines = [
        f"- `{candidate['scenario_label']}`: {candidate['reason']}"
        for candidate in packet["rewrite_candidates"]
    ]
    lines = [
        "# PROD-041 Conditional Simulation Review",
        "",
        "PROD-041 records the human review outcome for the locked PROD-041A expanded traces. It does not expand or regenerate the scenario diversity checkpoint.",
        "",
        "## Result",
        "",
        f"- Checkpoint id: `{payload['checkpoint_id']}`",
        f"- Source checkpoint: `{payload['source_checkpoint_id']}`",
        f"- Reviewed calls: `{summary['reviewed_call_count']}`",
        f"- Reviewed B2B calls: `{summary['reviewed_b2b_call_count']}`",
        f"- Reviewed B2C calls: `{summary['reviewed_b2c_call_count']}`",
        f"- PROD-041A locked: `{str(summary['prod_041a_locked']).lower()}`",
        f"- Remaining deterministic phrasing acceptable: `{summary['remaining_deterministic_phrasing_acceptable']}`",
        f"- Safe close outcomes earned: `{summary['safe_close_outcomes_earned']}`",
        f"- Targeted rewrite required before voice or demo: `{str(summary['targeted_rewrite_required_before_voice_or_demo']).lower()}`",
        f"- Template-like customer turn count: `{summary['template_like_turn_count']}`",
        f"- Rewrite candidate count: `{summary['rewrite_candidate_count']}`",
        f"- Voice playback unblocked: `{str(summary['voice_playback_unblocked']).lower()}`",
        f"- Scenario branching unblocked: `{str(summary['scenario_branching_unblocked']).lower()}`",
        f"- Public demo polish unblocked: `{str(summary['public_demo_polish_unblocked']).lower()}`",
        f"- Source safe close rate: `{summary['source_safe_close_rate']}`",
        f"- Source non sale correctness rate: `{summary['source_non_sale_correctness_rate']}`",
        f"- Source hard failure count: `{summary['source_hard_failure_count']}`",
        f"- Source dialogue realism average score: `{summary['source_dialogue_realism_average_score']}`",
        "",
        "## Manual Review Findings",
        "",
        *finding_lines,
        "",
        "## Rewrite Candidates Before Voice Or Demo",
        "",
        *candidate_lines,
        "",
        "## Decision",
        "",
        "Keep `PROD-041A-conditional-scenario-diversity-expansion` offline, deterministic, and locked as the scenario diversity checkpoint. Do not keep expanding PROD-041A. Use a future targeted readiness checkpoint for customer-turn rewrites before voice playback or demo use.",
        "",
        "## Boundary",
        "",
        "PROD-041 does not call providers, call an LLM, read private data, download datasets, modify PROD-041A, start a server, collect payment, enable retrieval by default, enable composer hooks by default, change runtime behavior, unblock voice playback, unblock public demo polish, or allow production runtime promotion.",
    ]
    return "\n".join(lines) + "\n"
