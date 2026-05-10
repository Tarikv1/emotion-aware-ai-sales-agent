#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-038-local-demo-surface-review"
SOURCE_CHECKPOINT_ID = "PROD-037-local-interactive-trace-demo-surface"
NEXT_CHECKPOINT_ID = "PROD-039-customer-realism-simulator-hardening"
DEFAULT_OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
DEFAULT_RESULT = DEFAULT_OUT_DIR / "result.json"
DEFAULT_REPORT = DEFAULT_OUT_DIR / "report.md"
DEFAULT_REVIEW_PACKET = DEFAULT_OUT_DIR / "local_demo_surface_review_packet.json"
DEFAULT_SOURCE_SURFACE_DATA = ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "local_interactive_trace_demo_surface_data.json"


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
        "customer_data_allowed": False,
        "payment_collection_enabled": False,
        "runtime_behavior_changed_by_this_checkpoint": False,
        "runtime_retrieval_default_enabled": False,
        "composer_hook_flag_default_enabled": False,
        "live_provider_default_enabled": False,
        "server_started": False,
        "production_runtime_promotion_allowed": False,
    }


def count_turns(surface_data: dict[str, Any]) -> int:
    return sum(len(call.get("turns", [])) for call in surface_data.get("calls", []))


def build_customer_response_issues() -> list[dict[str, str]]:
    return [
        {
            "issue_id": "over-cooperative-acceptance",
            "severity": "blocker",
            "finding": "Some customers accept too cleanly after one or two answers, which makes the sale path feel scripted instead of earned.",
            "required_change": "Acceptance should usually be conditional, partial, delayed, or require a realistic next step unless the persona is strongly warm.",
        },
        {
            "issue_id": "evaluator-like-wording",
            "severity": "blocker",
            "finding": "Customer lines describe benchmark states such as accepting a non-binding review or rejecting the deal in language no buyer would normally use.",
            "required_change": "Customer dialogue should use plain spoken buyer phrasing and keep evaluation labels in metadata only.",
        },
        {
            "issue_id": "too-clean-state-transition",
            "severity": "blocker",
            "finding": "Replies move neatly from one objection category to the next instead of mixing confusion, skepticism, interruptions, and partial understanding.",
            "required_change": "The simulator needs messier transitions with hedging, side concerns, repeated friction, and incomplete acceptance.",
        },
        {
            "issue_id": "low-friction-follow-up",
            "severity": "major",
            "finding": "Follow-up questions are too helpful and sales-ready, so customers sound like cooperative test fixtures.",
            "required_change": "Follow-ups should include reluctance, vague language, time pressure, incomplete information, and occasional misunderstanding.",
        },
        {
            "issue_id": "artificial-boundary-language",
            "severity": "major",
            "finding": "Customers mention safety boundaries such as billing handling in unnatural ways.",
            "required_change": "Safety boundaries should remain in flags and expected outcomes; buyer speech should sound natural while still avoiding payment collection.",
        },
    ]


def build_review_packet(surface_data: dict[str, Any]) -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "review_decision": "revise-customer-simulator-before-demo-expansion",
        "review_basis": "Human review of the PROD-037 local trace surface found the customer responses too artificial for a convincing sales-agent demo.",
        "customer_response_issues": build_customer_response_issues(),
        "accepted_scope": {
            "static_surface_structure": True,
            "call_selection": True,
            "turn_selection": True,
            "decision_trace_visibility": True,
            "state_transition_visibility": True,
            "safety_visibility": True,
        },
        "blocked_scope": {
            "voice_playback": True,
            "scenario_branching": True,
            "more_call_seeds": True,
            "public_demo_polish": True,
            "production_runtime_promotion": True,
        },
        "next_customer_realism_requirements": [
            "customer dialogue must not use evaluation labels",
            "acceptance must be less immediate and more conditional",
            "rejections must sound like real buyer pushback, not status declarations",
            "follow-up questions must include realistic vagueness, friction, and incomplete understanding",
            "safety boundaries stay in metadata instead of buyer wording",
            "the same fixed calls must be rerun before claiming improvement",
        ],
        "source_counts": {
            "reviewed_call_count": len(surface_data.get("calls", [])),
            "reviewed_turn_count": count_turns(surface_data),
        },
    }


def build_summary(surface_data: dict[str, Any], packet: dict[str, Any]) -> dict[str, Any]:
    source_counts = packet["source_counts"]
    return {
        "reviewed_call_count": source_counts["reviewed_call_count"],
        "reviewed_turn_count": source_counts["reviewed_turn_count"],
        "demo_surface_ui_accepted": True,
        "customer_response_realism_accepted": False,
        "conversation_quality_gate_passed": False,
        "customer_response_issue_count": len(packet["customer_response_issues"]),
        "voice_playback_unblocked": False,
        "scenario_branching_unblocked": False,
        "more_call_seeds_unblocked": False,
        "public_demo_polish_unblocked": False,
        "provider_calls_made": False,
        "llm_used": False,
        "runtime_behavior_changed": False,
        "next_build_recommendation": "customer_realism_simulator_hardening",
    }


def build_payload(
    *,
    source_surface_data_path: Path = DEFAULT_SOURCE_SURFACE_DATA,
    result_path: Path = DEFAULT_RESULT,
    report_path: Path = DEFAULT_REPORT,
    review_packet_path: Path = DEFAULT_REVIEW_PACKET,
) -> tuple[dict[str, Any], dict[str, Any]]:
    surface_data = read_json(source_surface_data_path)
    packet = build_review_packet(surface_data)
    payload = {
        "checkpoint_id": CHECKPOINT_ID,
        "title": "PROD-038 local demo surface review",
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "next_checkpoint_recommended": NEXT_CHECKPOINT_ID,
        "outputs": {
            "result_path": rel_path(result_path),
            "report_path": rel_path(report_path),
            "review_packet_path": rel_path(review_packet_path),
        },
        "source_inputs": {
            "source_surface_data_path": rel_path(source_surface_data_path),
        },
        "boundaries": build_boundaries(),
        "summary": build_summary(surface_data, packet),
        "decision": {
            "surface_review": "ui-useful-content-not-accepted",
            "next_step": NEXT_CHECKPOINT_ID,
        },
    }
    return payload, packet


def render_report(payload: dict[str, Any], packet: dict[str, Any]) -> str:
    summary = payload["summary"]
    issue_lines = [
        f"- `{issue['issue_id']}` ({issue['severity']}): {issue['finding']}"
        for issue in packet["customer_response_issues"]
    ]
    requirement_lines = [f"- {item}" for item in packet["next_customer_realism_requirements"]]
    lines = [
        "# PROD-038 Local Demo Surface Review",
        "",
        "PROD-038 records the review outcome for the PROD-037 local trace demo surface. The surface structure is useful, but the customer responses are not realistic enough for the next demo expansion.",
        "",
        "## Result",
        "",
        f"- Checkpoint id: `{payload['checkpoint_id']}`",
        f"- Source checkpoint: `{payload['source_checkpoint_id']}`",
        f"- Reviewed calls: `{summary['reviewed_call_count']}`",
        f"- Reviewed turns: `{summary['reviewed_turn_count']}`",
        f"- Demo surface UI accepted: `{str(summary['demo_surface_ui_accepted']).lower()}`",
        f"- Customer response realism accepted: `{str(summary['customer_response_realism_accepted']).lower()}`",
        f"- Conversation quality gate passed: `{str(summary['conversation_quality_gate_passed']).lower()}`",
        f"- Customer response issue count: `{summary['customer_response_issue_count']}`",
        f"- Voice playback unblocked: `{str(summary['voice_playback_unblocked']).lower()}`",
        f"- Scenario branching unblocked: `{str(summary['scenario_branching_unblocked']).lower()}`",
        f"- More call seeds unblocked: `{str(summary['more_call_seeds_unblocked']).lower()}`",
        f"- Public demo polish unblocked: `{str(summary['public_demo_polish_unblocked']).lower()}`",
        f"- Next build recommendation: `{summary['next_build_recommendation']}`",
        f"- Next checkpoint: `{payload['next_checkpoint_recommended']}`",
        "",
        "## Customer Response Issues",
        "",
        *issue_lines,
        "",
        "## Next Customer-Realism Requirements",
        "",
        *requirement_lines,
        "",
        "## Boundary",
        "",
        "PROD-038 does not call providers, call an LLM, read private data, download datasets, start a server, collect payment, enable retrieval by default, enable composer hooks by default, change runtime behavior, unblock voice playback, unblock public demo polish, or allow production runtime promotion.",
    ]
    return "\n".join(lines) + "\n"
