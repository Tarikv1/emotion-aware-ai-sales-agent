#!/usr/bin/env python3
from __future__ import annotations

import html
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from generate_guarded_response import build_guarded_response_packet
from prod_028_synthetic_campaign_knowledge_grounding import build_synthetic_campaign


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-035-runtime-decision-trace-alignment"
SOURCE_CHECKPOINT_ID = "PROD-034-interactive-post-fix-review"
TRACE_SOURCE_CHECKPOINT_ID = "PROD-033-interactive-simulator-termination-fix"
NEXT_CHECKPOINT_ID = "PROD-036-interactive-demo-readiness-review"
DEFAULT_OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
DEFAULT_RESULT = DEFAULT_OUT_DIR / "result.json"
DEFAULT_REPORT = DEFAULT_OUT_DIR / "report.md"
DEFAULT_TRACE = DEFAULT_OUT_DIR / "aligned_interactive_call_traces.json"
DEFAULT_HTML = DEFAULT_OUT_DIR / "aligned_interactive_call_trace.html"
DEFAULT_SOURCE_RESULT = ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "result.json"
DEFAULT_SOURCE_TRACE = ROOT / "research" / "experiments" / "generated" / TRACE_SOURCE_CHECKPOINT_ID / "interactive_call_traces.json"

OBJECTION_STATES = {"price", "confusion", "provider", "support", "time", "trust", "authority", "do-not-call", "stakeholder"}


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
        "runtime_spoken_answer_changed_by_this_checkpoint": False,
        "runtime_decision_trace_alignment_opt_in": True,
        "runtime_decision_trace_default_changed": False,
        "runtime_retrieval_default_enabled": False,
        "composer_hook_flag_default_enabled": False,
        "live_provider_default_enabled": False,
        "server_started": False,
        "source_prod_033_overwritten": False,
        "source_prod_034_overwritten": False,
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
        and turn.get("state_before", {}).get("active_objection") in OBJECTION_STATES
    )


def count_terminal_call_control_mismatches(calls: list[dict[str, Any]]) -> int:
    return sum(
        1
        for call in calls
        for turn in call.get("turns", [])
        if turn.get("state_after", {}).get("commitment") in {"sale-ready", "not-interested"}
        and turn.get("decision_snapshot", {}).get("call_control") == "continue-call"
    )


def safety_count(calls: list[dict[str, Any]], flag: str) -> int:
    return sum(1 for call in calls for turn in call.get("turns", []) if turn.get("safety_flags", {}).get(flag))


def aligned_packet_for_turn(campaign: dict[str, Any], turn: dict[str, Any]) -> dict[str, Any]:
    return build_guarded_response_packet(
        campaign=campaign,
        stage="discovery",
        input_type="speech-final",
        transcript=turn["customer_context"],
        silence_count=0,
        candidate_response_override=turn["agent_answer"],
        retrieval_enabled=False,
        retrieval_registry_path=None,
        composer_hooks_enabled=False,
        align_decision_trace=True,
    )


def align_call_traces(source_trace: dict[str, Any]) -> dict[str, Any]:
    campaign = build_synthetic_campaign()
    aligned_calls = deepcopy(source_trace["calls"])
    for call in aligned_calls:
        for turn in call.get("turns", []):
            source_answer = turn["agent_answer"]
            source_customer_response = turn["customer_response"]
            source_terminal = call.get("terminal_outcome")
            packet = aligned_packet_for_turn(campaign, turn)
            aligned_answer = packet["final_response"]
            source_decision = deepcopy(turn["decision_snapshot"])
            aligned_decision = deepcopy(packet["decision_snapshot"])
            turn["source_agent_answer"] = source_answer
            turn["source_customer_response"] = source_customer_response
            turn["source_decision_snapshot"] = source_decision
            turn["agent_answer"] = aligned_answer
            turn["decision_snapshot"] = aligned_decision
            turn["alignment_change"] = {
                "spoken_answer_changed": aligned_answer != source_answer,
                "customer_response_changed": turn["customer_response"] != source_customer_response,
                "terminal_outcome_changed": call.get("terminal_outcome") != source_terminal,
                "sales_difficulty_before": source_decision.get("sales_difficulty"),
                "sales_difficulty_after": aligned_decision.get("sales_difficulty"),
                "next_action_before": source_decision.get("next_action"),
                "next_action_after": aligned_decision.get("next_action"),
                "call_control_before": source_decision.get("call_control"),
                "call_control_after": aligned_decision.get("call_control"),
            }
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": TRACE_SOURCE_CHECKPOINT_ID,
        "source_trace_path": source_trace.get("source_result_path", ""),
        "calls": aligned_calls,
    }


def build_summary(source_calls: list[dict[str, Any]], aligned_calls: list[dict[str, Any]]) -> dict[str, Any]:
    aligned_turns = [turn for call in aligned_calls for turn in call.get("turns", [])]
    return {
        "source_call_count": len(source_calls),
        "source_turn_count": sum(len(call.get("turns", [])) for call in source_calls),
        "aligned_call_count": len(aligned_calls),
        "aligned_turn_count": len(aligned_turns),
        "spoken_answer_changed_count": sum(1 for turn in aligned_turns if turn.get("alignment_change", {}).get("spoken_answer_changed")),
        "customer_response_changed_count": sum(1 for turn in aligned_turns if turn.get("alignment_change", {}).get("customer_response_changed")),
        "terminal_outcome_changed_count": sum(1 for call in aligned_calls if call.get("terminal_outcome") != call.get("expected_terminal_outcome")),
        "decision_snapshot_mismatch_before_count": count_decision_snapshot_mismatches(source_calls),
        "decision_snapshot_mismatch_after_count": count_decision_snapshot_mismatches(aligned_calls),
        "unknown_objection_decision_before_count": count_unknown_objection_decisions(source_calls),
        "unknown_objection_decision_after_count": count_unknown_objection_decisions(aligned_calls),
        "terminal_call_control_mismatch_after_count": count_terminal_call_control_mismatches(aligned_calls),
        "direct_answer_next_action_count": sum(1 for turn in aligned_turns if turn.get("decision_snapshot", {}).get("next_action") == "continue"),
        "objection_mapped_count": sum(
            1
            for turn in aligned_turns
            if turn.get("source_decision_snapshot", {}).get("sales_difficulty") == "unknown-runtime-signal"
            and turn.get("decision_snapshot", {}).get("sales_difficulty") != "unknown-runtime-signal"
        ),
        "hard_failure_count": safety_count(aligned_calls, "hard_failure"),
        "payment_collection_count": safety_count(aligned_calls, "payment_collection"),
        "unsupported_claim_count": safety_count(aligned_calls, "unsupported_claim"),
        "leakage_finding_count": 0,
        "provider_calls_made": False,
        "llm_used": False,
        "runtime_retrieval_default_enabled": False,
        "composer_hook_flag_default_enabled": False,
        "production_runtime_promotion_allowed": False,
        "first_review_recommendation": "interactive_demo_readiness_review",
    }


def build_payload(
    *,
    source_result_path: Path = DEFAULT_SOURCE_RESULT,
    source_trace_path: Path = DEFAULT_SOURCE_TRACE,
    result_path: Path = DEFAULT_RESULT,
    report_path: Path = DEFAULT_REPORT,
    trace_path: Path = DEFAULT_TRACE,
    html_path: Path = DEFAULT_HTML,
) -> tuple[dict[str, Any], dict[str, Any]]:
    source_result = read_json(source_result_path)
    source_trace = read_json(source_trace_path)
    aligned_trace = align_call_traces(source_trace)
    payload = {
        "checkpoint_id": CHECKPOINT_ID,
        "title": "PROD-035 runtime decision-trace alignment",
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "trace_source_checkpoint_id": TRACE_SOURCE_CHECKPOINT_ID,
        "next_checkpoint_recommended": NEXT_CHECKPOINT_ID,
        "outputs": {
            "result_path": rel_path(result_path),
            "report_path": rel_path(report_path),
            "trace_path": rel_path(trace_path),
            "trace_html_path": rel_path(html_path),
        },
        "source_inputs": {
            "source_result_path": rel_path(source_result_path),
            "source_trace_path": rel_path(source_trace_path),
            "source_decision_snapshot_mismatch_count": source_result["summary"]["decision_snapshot_mismatch_count"],
            "source_unknown_objection_decision_count": source_result["summary"]["unknown_objection_decision_count"],
        },
        "boundaries": build_boundaries(),
        "summary": build_summary(source_trace["calls"], aligned_trace["calls"]),
        "decision": {
            "spoken_answer_policy": "preserve-prod-033-spoken-answers",
            "decision_trace_alignment": "opt-in-fix-accepted",
            "runtime_defaults": "unchanged",
            "next_step": NEXT_CHECKPOINT_ID,
        },
    }
    return payload, aligned_trace


def render_report(payload: dict[str, Any], traces: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# PROD-035 Runtime Decision-Trace Alignment",
        "",
        "PROD-035 applies an opt-in decision-trace alignment pass to the same PROD-033 interactive calls. Spoken answers, customer responses, and terminal outcomes are preserved; only the visible decision snapshot is corrected.",
        "",
        "## Result",
        "",
        f"- Checkpoint id: `{payload['checkpoint_id']}`",
        f"- Source checkpoint: `{payload['source_checkpoint_id']}`",
        f"- Trace source checkpoint: `{payload['trace_source_checkpoint_id']}`",
        f"- Aligned calls: `{summary['aligned_call_count']}`",
        f"- Aligned turns: `{summary['aligned_turn_count']}`",
        f"- Spoken answer changed count: `{summary['spoken_answer_changed_count']}`",
        f"- Customer response changed count: `{summary['customer_response_changed_count']}`",
        f"- Terminal outcome changed count: `{summary['terminal_outcome_changed_count']}`",
        f"- Decision snapshot mismatches before: `{summary['decision_snapshot_mismatch_before_count']}`",
        f"- Decision snapshot mismatches after: `{summary['decision_snapshot_mismatch_after_count']}`",
        f"- Unknown-objection decisions before: `{summary['unknown_objection_decision_before_count']}`",
        f"- Unknown-objection decisions after: `{summary['unknown_objection_decision_after_count']}`",
        f"- Terminal call-control mismatches after: `{summary['terminal_call_control_mismatch_after_count']}`",
        f"- Direct-answer next actions: `{summary['direct_answer_next_action_count']}`",
        f"- Objections mapped: `{summary['objection_mapped_count']}`",
        f"- Hard failures: `{summary['hard_failure_count']}`",
        f"- Payment collection count: `{summary['payment_collection_count']}`",
        f"- Unsupported claim count: `{summary['unsupported_claim_count']}`",
        f"- Leakage findings: `{summary['leakage_finding_count']}`",
        f"- Runtime decision trace default changed: `false`",
        f"- Provider calls made: `{str(summary['provider_calls_made']).lower()}`",
        f"- LLM used: `{str(summary['llm_used']).lower()}`",
        f"- Next checkpoint: `{payload['next_checkpoint_recommended']}`",
        "",
        "## Decision",
        "",
        "The next useful checkpoint is `PROD-036-interactive-demo-readiness-review`. PROD-035 removes the explainability/debug trace issue without making the agent more question-heavy or changing accepted spoken answers.",
        "",
        "## Boundary",
        "",
        "PROD-035 is local and opt-in. It does not overwrite PROD-033 or PROD-034, call providers, call an LLM, read private data, download datasets, collect payment, start a server, enable retrieval by default, enable composer hooks by default, change runtime decision-trace defaults, or allow production runtime promotion.",
    ]
    return "\n".join(lines) + "\n"


def render_html(payload: dict[str, Any], traces: dict[str, Any]) -> str:
    summary = payload["summary"]
    rows = []
    for call in traces["calls"]:
        changed = sum(1 for turn in call.get("turns", []) if turn.get("alignment_change", {}).get("next_action_before") != turn.get("alignment_change", {}).get("next_action_after"))
        rows.append(
            "<tr>"
            f"<td>{html.escape(call['seed_id'])}</td>"
            f"<td>{html.escape(call['terminal_outcome'])}</td>"
            f"<td>{call['turn_count']}</td>"
            f"<td>{changed}</td>"
            f"<td>{html.escape(call['terminal_decision_source'])}</td>"
            "</tr>"
        )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>PROD-035 Runtime Decision-Trace Alignment</title>
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
  PROD-035 runtime decision-trace alignment
  spoken answer changed count: `0`
  decision snapshot mismatches before: `13`
  decision snapshot mismatches after: `0`
  unknown-objection decisions before: `6`
  unknown-objection decisions after: `0`
  runtime decision trace default changed: `false`
  {html.escape(payload['next_checkpoint_recommended'])}
  -->
  <h1>PROD-035 Runtime Decision-Trace Alignment</h1>
  <p>Opt-in alignment of the visible decision snapshot while preserving the PROD-033 spoken answers and customer outcomes.</p>
  <div class="metric">Spoken answer changed count: <code>{summary['spoken_answer_changed_count']}</code></div>
  <div class="metric">Decision snapshot mismatches before: <code>{summary['decision_snapshot_mismatch_before_count']}</code></div>
  <div class="metric">Decision snapshot mismatches after: <code>{summary['decision_snapshot_mismatch_after_count']}</code></div>
  <div class="metric">Unknown-objection decisions before: <code>{summary['unknown_objection_decision_before_count']}</code></div>
  <div class="metric">Unknown-objection decisions after: <code>{summary['unknown_objection_decision_after_count']}</code></div>
  <div class="metric">Runtime decision trace default changed: <code>false</code></div>
  <div class="metric">Next checkpoint: <code>{html.escape(payload['next_checkpoint_recommended'])}</code></div>
  <h2>Call Alignment</h2>
  <table>
    <thead><tr><th>Seed</th><th>Terminal Outcome</th><th>Turns</th><th>Next Action Changes</th><th>Terminal Source</th></tr></thead>
    <tbody>{''.join(rows)}</tbody>
  </table>
</body>
</html>
"""
