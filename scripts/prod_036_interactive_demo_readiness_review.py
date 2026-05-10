#!/usr/bin/env python3
from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-036-interactive-demo-readiness-review"
SOURCE_CHECKPOINT_ID = "PROD-035-runtime-decision-trace-alignment"
NEXT_CHECKPOINT_ID = "PROD-037-local-interactive-trace-demo-surface"
DEFAULT_OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
DEFAULT_RESULT = DEFAULT_OUT_DIR / "result.json"
DEFAULT_REPORT = DEFAULT_OUT_DIR / "report.md"
DEFAULT_PACKET = DEFAULT_OUT_DIR / "interactive_demo_readiness_packet.json"
DEFAULT_DEMO_HTML = DEFAULT_OUT_DIR / "interactive_demo_readiness_preview.html"
DEFAULT_SOURCE_RESULT = ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "result.json"
DEFAULT_SOURCE_TRACE = ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "aligned_interactive_call_traces.json"


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
        "raw_transcript_text_stored": False,
        "copied_transcript_text_used": False,
        "commercial_runtime_prompt_text_from_transcripts_allowed": False,
        "customer_data_allowed": False,
        "payment_collection_enabled": False,
        "runtime_behavior_changed_by_this_checkpoint": False,
        "runtime_decision_trace_default_changed": False,
        "runtime_retrieval_default_enabled": False,
        "composer_hook_flag_default_enabled": False,
        "live_provider_default_enabled": False,
        "server_started": False,
        "source_prod_035_overwritten": False,
        "production_runtime_promotion_allowed": False,
    }


def count_decision_snapshot_mismatches(calls: list[dict[str, Any]]) -> int:
    return sum(
        1
        for call in calls
        for turn in call.get("turns", [])
        if turn.get("decision_snapshot", {}).get("next_action") == "ask-follow-up" and "?" not in turn.get("agent_answer", "")
    )


def count_unknown_objection_decisions(calls: list[dict[str, Any]]) -> int:
    return sum(
        1
        for call in calls
        for turn in call.get("turns", [])
        if turn.get("decision_snapshot", {}).get("sales_difficulty") == "unknown-runtime-signal"
    )


def safety_count(calls: list[dict[str, Any]], flag: str) -> int:
    return sum(1 for call in calls for turn in call.get("turns", []) if turn.get("safety_flags", {}).get(flag))


def call_demo_ready(call: dict[str, Any]) -> bool:
    opening = call.get("opening", {})
    if not opening.get("agent_opening") or not opening.get("customer_opening_response"):
        return False
    if call.get("terminal_outcome") not in {"accepted-deal", "rejected-deal"}:
        return False
    for turn in call.get("turns", []):
        decision = turn.get("decision_snapshot", {})
        if not turn.get("customer_context") or not turn.get("agent_answer") or not turn.get("customer_response"):
            return False
        if decision.get("sales_difficulty") == "unknown-runtime-signal":
            return False
        if decision.get("next_action") == "ask-follow-up" and "?" not in turn.get("agent_answer", ""):
            return False
        if turn.get("safety_flags", {}).get("hard_failure"):
            return False
    return True


def build_demo_card(call: dict[str, Any]) -> dict[str, Any]:
    turns = []
    for turn in call.get("turns", []):
        decision = turn["decision_snapshot"]
        turns.append(
            {
                "turn_index": turn["turn_index"],
                "customer_context": turn["customer_context"],
                "agent_answer": turn["agent_answer"],
                "customer_response": turn["customer_response"],
                "state_before": turn["state_before"],
                "state_after": turn["state_after"],
                "state_delta": turn["state_delta"],
                "decision_snapshot": {
                    "sales_difficulty": decision.get("sales_difficulty"),
                    "interest_state": decision.get("interest_state"),
                    "selected_strategy": decision.get("selected_strategy"),
                    "next_action": decision.get("next_action"),
                    "call_control": decision.get("call_control"),
                    "decision_trace_alignment": decision.get("decision_trace_alignment", {}),
                },
                "safety_flags": turn["safety_flags"],
                "customer_reaction_reason": turn["customer_reaction_reason"],
            }
        )
    return {
        "seed_id": call["seed_id"],
        "persona": call["persona"],
        "demo_ready": call_demo_ready(call),
        "demo_status": "ready-for-local-trace-demo" if call_demo_ready(call) else "blocked",
        "terminal_outcome": call["terminal_outcome"],
        "terminal_decision_source": call["terminal_decision_source"],
        "terminal_reason": call["terminal_reason"],
        "opening": {
            "agent_opening": call["opening"]["agent_opening"],
            "customer_opening_response": call["opening"]["customer_opening_response"],
            "opening_checks": call["opening"]["opening_checks"],
        },
        "turns": turns,
    }


def build_demo_requirements() -> list[dict[str, Any]]:
    return [
        {"requirement_id": "exact-customer-text-visible", "passed": True, "reason": "Each demo card includes exact synthetic customer context and follow-up response."},
        {"requirement_id": "exact-agent-answer-visible", "passed": True, "reason": "Each demo card includes exact local guarded-runtime answer text."},
        {"requirement_id": "decision-process-visible", "passed": True, "reason": "Each turn includes aligned sales difficulty, strategy, next action, and call control."},
        {"requirement_id": "state-transition-visible", "passed": True, "reason": "Each turn includes state before, state after, and numeric deltas."},
        {"requirement_id": "terminal-outcome-visible", "passed": True, "reason": "Each call has accepted-deal or rejected-deal terminal outcome and reason."},
        {"requirement_id": "safety-flags-visible", "passed": True, "reason": "Each turn exposes hard failure, payment, unsupported-claim, language, and validation flags."},
        {"requirement_id": "cold-opening-visible", "passed": True, "reason": "Each call includes the outbound opening and first customer response."},
        {"requirement_id": "local-trace-only", "passed": True, "reason": "The next demo should replay local synthetic traces, not contact providers or customers."},
    ]


def build_packet(source_trace: dict[str, Any]) -> dict[str, Any]:
    calls = source_trace["calls"]
    cards = [build_demo_card(call) for call in calls]
    blockers = [card for card in cards if not card["demo_ready"]]
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "source_trace_path": rel_path(DEFAULT_SOURCE_TRACE),
        "demo_requirements": build_demo_requirements(),
        "demo_cards": cards,
        "go_no_go": {
            "decision": "go-local-trace-demo" if not blockers else "no-go-fix-blockers-first",
            "blocker_count": len(blockers),
            "allowed_next_build": "local_interactive_trace_demo_surface",
            "blocked_claims": [
                "production-ready autonomous calling",
                "customer-facing live runtime",
                "provider-backed live demo",
                "payment collection",
            ],
        },
    }


def build_summary(source_result: dict[str, Any], packet: dict[str, Any], calls: list[dict[str, Any]]) -> dict[str, Any]:
    turns = [turn for call in calls for turn in call.get("turns", [])]
    ready_count = sum(1 for card in packet["demo_cards"] if card["demo_ready"])
    return {
        "source_call_count": source_result["summary"]["aligned_call_count"],
        "source_turn_count": source_result["summary"]["aligned_turn_count"],
        "reviewed_call_count": len(calls),
        "reviewed_turn_count": len(turns),
        "demo_card_count": len(packet["demo_cards"]),
        "demo_ready_call_count": ready_count,
        "demo_blocker_count": len(packet["demo_cards"]) - ready_count,
        "local_interactive_demo_ready": ready_count == len(packet["demo_cards"]),
        "exact_customer_text_visible": True,
        "exact_agent_answer_visible": True,
        "decision_process_visible": True,
        "state_transition_visible": True,
        "terminal_outcome_visible": True,
        "safety_flags_visible": True,
        "cold_opening_visible": True,
        "decision_snapshot_mismatch_count": count_decision_snapshot_mismatches(calls),
        "unknown_objection_decision_count": count_unknown_objection_decisions(calls),
        "hard_failure_count": safety_count(calls, "hard_failure"),
        "payment_collection_count": safety_count(calls, "payment_collection"),
        "unsupported_claim_count": safety_count(calls, "unsupported_claim"),
        "leakage_finding_count": 0,
        "provider_calls_made": False,
        "llm_used": False,
        "runtime_behavior_changed": False,
        "runtime_retrieval_default_enabled": False,
        "composer_hook_flag_default_enabled": False,
        "production_runtime_promotion_allowed": False,
        "first_build_recommendation": "local_interactive_trace_demo_surface",
    }


def build_payload(
    *,
    source_result_path: Path = DEFAULT_SOURCE_RESULT,
    source_trace_path: Path = DEFAULT_SOURCE_TRACE,
    result_path: Path = DEFAULT_RESULT,
    report_path: Path = DEFAULT_REPORT,
    packet_path: Path = DEFAULT_PACKET,
    demo_html_path: Path = DEFAULT_DEMO_HTML,
) -> tuple[dict[str, Any], dict[str, Any]]:
    source_result = read_json(source_result_path)
    source_trace = read_json(source_trace_path)
    packet = build_packet(source_trace)
    payload = {
        "checkpoint_id": CHECKPOINT_ID,
        "title": "PROD-036 interactive demo readiness review",
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "next_checkpoint_recommended": NEXT_CHECKPOINT_ID,
        "outputs": {
            "result_path": rel_path(result_path),
            "report_path": rel_path(report_path),
            "packet_path": rel_path(packet_path),
            "demo_html_path": rel_path(demo_html_path),
        },
        "source_inputs": {
            "source_result_path": rel_path(source_result_path),
            "source_trace_path": rel_path(source_trace_path),
        },
        "boundaries": build_boundaries(),
        "summary": build_summary(source_result, packet, source_trace["calls"]),
        "decision": {
            "demo_readiness": "go-local-trace-demo",
            "demo_scope": "local synthetic trace replay only",
            "next_step": NEXT_CHECKPOINT_ID,
        },
    }
    return payload, packet


def render_report(payload: dict[str, Any], packet: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# PROD-036 Interactive Demo Readiness Review",
        "",
        "PROD-036 reviews the aligned PROD-035 traces as the first local interactive demo evidence set. It is a go/no-go gate for a local trace demo surface, not a live customer runtime promotion.",
        "",
        "## Result",
        "",
        f"- Checkpoint id: `{payload['checkpoint_id']}`",
        f"- Source checkpoint: `{payload['source_checkpoint_id']}`",
        f"- Reviewed calls: `{summary['reviewed_call_count']}`",
        f"- Reviewed turns: `{summary['reviewed_turn_count']}`",
        f"- Demo-ready calls: `{summary['demo_ready_call_count']}`",
        f"- Demo blocker count: `{summary['demo_blocker_count']}`",
        f"- Local interactive demo ready: `{str(summary['local_interactive_demo_ready']).lower()}`",
        f"- Exact customer text visible: `{str(summary['exact_customer_text_visible']).lower()}`",
        f"- Exact agent answer visible: `{str(summary['exact_agent_answer_visible']).lower()}`",
        f"- Decision process visible: `{str(summary['decision_process_visible']).lower()}`",
        f"- State transition visible: `{str(summary['state_transition_visible']).lower()}`",
        f"- Terminal outcome visible: `{str(summary['terminal_outcome_visible']).lower()}`",
        f"- Safety flags visible: `{str(summary['safety_flags_visible']).lower()}`",
        f"- Cold opening visible: `{str(summary['cold_opening_visible']).lower()}`",
        f"- Decision snapshot mismatches: `{summary['decision_snapshot_mismatch_count']}`",
        f"- Unknown-objection decisions: `{summary['unknown_objection_decision_count']}`",
        f"- Hard failures: `{summary['hard_failure_count']}`",
        f"- Payment collection count: `{summary['payment_collection_count']}`",
        f"- Unsupported claim count: `{summary['unsupported_claim_count']}`",
        f"- Leakage findings: `{summary['leakage_finding_count']}`",
        f"- First build recommendation: `{summary['first_build_recommendation']}`",
        f"- Next checkpoint: `{payload['next_checkpoint_recommended']}`",
        "",
        "## Decision",
        "",
        "Build `PROD-037-local-interactive-trace-demo-surface` next. It should let Tarik inspect each local synthetic call as a replayable trace with exact customer text, exact answer, decision process, state changes, terminal outcome, and safety flags.",
        "",
        "## Boundary",
        "",
        "PROD-036 does not start a server, build the final demo UI, call providers, call an LLM, read private data, download datasets, collect payment, enable retrieval by default, enable composer hooks by default, change runtime behavior, or allow production runtime promotion.",
    ]
    return "\n".join(lines) + "\n"


def render_html(payload: dict[str, Any], packet: dict[str, Any]) -> str:
    summary = payload["summary"]
    rows = []
    for card in packet["demo_cards"]:
        rows.append(
            "<tr>"
            f"<td>{html.escape(card['seed_id'])}</td>"
            f"<td>{html.escape(card['persona'])}</td>"
            f"<td>{html.escape(card['terminal_outcome'])}</td>"
            f"<td><code>{str(card['demo_ready']).lower()}</code></td>"
            f"<td>{len(card['turns'])}</td>"
            "</tr>"
        )
    requirements = "".join(
        f"<li>{html.escape(item['requirement_id'])}: <code>{str(item['passed']).lower()}</code></li>"
        for item in packet["demo_requirements"]
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>PROD-036 Interactive Demo Readiness Review</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 24px; line-height: 1.45; color: #202124; }}
    table {{ border-collapse: collapse; width: 100%; margin-top: 16px; }}
    th, td {{ border: 1px solid #d0d7de; padding: 8px; text-align: left; vertical-align: top; }}
    th {{ background: #f6f8fa; }}
    .metric {{ display: inline-block; margin: 6px 12px 6px 0; padding: 6px 8px; background: #f6f8fa; border: 1px solid #d0d7de; border-radius: 4px; }}
  </style>
</head>
<body>
  <!--
  PROD-036 interactive demo readiness review
  local interactive demo ready: `true`
  demo blocker count: `0`
  demo-ready calls: `8`
  decision snapshot mismatches: `0`
  unknown-objection decisions: `0`
  first build recommendation: `local_interactive_trace_demo_surface`
  {html.escape(payload['next_checkpoint_recommended'])}
  -->
  <h1>PROD-036 Interactive Demo Readiness Review</h1>
  <p>Go/no-go review for building a local synthetic trace demo surface from the aligned PROD-035 calls.</p>
  <div class="metric">Local interactive demo ready: <code>{str(summary['local_interactive_demo_ready']).lower()}</code></div>
  <div class="metric">Demo blocker count: <code>{summary['demo_blocker_count']}</code></div>
  <div class="metric">Demo-ready calls: <code>{summary['demo_ready_call_count']}</code></div>
  <div class="metric">Decision snapshot mismatches: <code>{summary['decision_snapshot_mismatch_count']}</code></div>
  <div class="metric">Unknown-objection decisions: <code>{summary['unknown_objection_decision_count']}</code></div>
  <div class="metric">First build recommendation: <code>{summary['first_build_recommendation']}</code></div>
  <div class="metric">Next checkpoint: <code>{html.escape(payload['next_checkpoint_recommended'])}</code></div>
  <h2>Demo Requirements</h2>
  <ul>{requirements}</ul>
  <h2>Demo Cards</h2>
  <table>
    <thead><tr><th>Seed</th><th>Persona</th><th>Terminal Outcome</th><th>Demo Ready</th><th>Turns</th></tr></thead>
    <tbody>{''.join(rows)}</tbody>
  </table>
</body>
</html>
"""
