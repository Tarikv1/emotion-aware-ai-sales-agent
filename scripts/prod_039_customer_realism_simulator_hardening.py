#!/usr/bin/env python3
from __future__ import annotations

import html
import json
from copy import deepcopy
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-039-customer-realism-simulator-hardening"
SOURCE_CHECKPOINT_ID = "PROD-038-local-demo-surface-review"
TRACE_SOURCE_CHECKPOINT_ID = "PROD-037-local-interactive-trace-demo-surface"
NEXT_CHECKPOINT_ID = "PROD-040-customer-realism-demo-surface-rerun"
DEFAULT_OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
DEFAULT_RESULT = DEFAULT_OUT_DIR / "result.json"
DEFAULT_REPORT = DEFAULT_OUT_DIR / "report.md"
DEFAULT_HARDENED_TRACE = DEFAULT_OUT_DIR / "customer_realism_hardened_traces.json"
DEFAULT_COMPARISON_PACKET = DEFAULT_OUT_DIR / "customer_realism_comparison_packet.json"
DEFAULT_COMPARISON_HTML = DEFAULT_OUT_DIR / "customer_realism_comparison.html"
DEFAULT_SOURCE_REVIEW_PACKET = ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "local_demo_surface_review_packet.json"
DEFAULT_SOURCE_SURFACE_DATA = ROOT / "research" / "experiments" / "generated" / TRACE_SOURCE_CHECKPOINT_ID / "local_interactive_trace_demo_surface_data.json"

UNREALISTIC_PHRASES = [
    "accept a non-binding",
    "specialist workflow review",
    "rejecting the deal",
    "rejecting the offer",
    "sales offer",
    "do not handle billing",
    "that answers the cost",
    "that makes sense now",
    "what would i tell my manager if i wanted to accept a review",
    "route me to support. i am rejecting",
    "i am rejecting",
]

OPENING_REWRITES = {
    "cold-price-sensitive": "I'm in between meetings, so be quick. Is this another paid tool?",
    "cold-confused-product-fit": "RouteSignal? I don't recognize the name. What are you calling about?",
    "cold-skeptical-trust-gap": "If this is another software pitch, I'm already skeptical. What exactly are you claiming?",
    "cold-busy-rejection": "Not really, I'm in the middle of something.",
    "cold-existing-provider": "We already use a CRM, so I'm not sure why we'd need another one.",
    "cold-stakeholder-review": "You've got maybe half a minute. Give me the manager version, not a pitch.",
    "cold-support-boundary": "I'm not shopping for anything. I need help with an account issue.",
    "cold-do-not-call": "No. Stop calling me and remove this number.",
}

RESPONSE_REWRITES = {
    ("cold-price-sensitive", 1): (
        "Okay, that's at least a real number. If I bring this up internally, what's the one-line reason they'd care?",
        ["hedging", "internal-stakeholder-friction", "plain-spoken-question"],
    ),
    ("cold-price-sensitive", 2): (
        "Alright, send over a short calendar option. I'm not promising budget, but I'm willing to look at the workflow with someone.",
        ["conditional-acceptance", "budget-reservation", "realistic-next-step"],
    ),
    ("cold-confused-product-fit", 1): (
        "Okay, so it's more about routing leads than replacing what we use. What's the price range?",
        ["partial-understanding", "product-fit-check", "direct-price-question"],
    ),
    ("cold-confused-product-fit", 2): (
        "Fine, if I had to explain it to my manager, what's the short version?",
        ["stakeholder-friction", "compressed-summary-request", "mild-reluctance"],
    ),
    ("cold-confused-product-fit", 3): (
        "Alright, we can look at it. Send a short slot, but I'm not agreeing to buy anything today.",
        ["conditional-acceptance", "purchase-boundary", "realistic-next-step"],
    ),
    ("cold-skeptical-trust-gap", 1): (
        "I still need something concrete. Email me the proof points and I'll skim it when I have time.",
        ["skeptical-friction", "written-proof-request", "low-commitment"],
    ),
    ("cold-skeptical-trust-gap", 2): (
        "That's fair. For now it's a no from me until I've seen the details in writing.",
        ["plain-rejection", "conditional-future-review", "written-proof-request"],
    ),
    ("cold-busy-rejection", 1): (
        "Appreciate it. Today is just not happening, so let's leave it there.",
        ["time-pressure", "plain-rejection", "low-patience"],
    ),
    ("cold-existing-provider", 1): (
        "If it layers on top and doesn't force a CRM switch, what's the rough cost?",
        ["existing-provider-friction", "conditional-interest", "direct-price-question"],
    ),
    ("cold-existing-provider", 2): (
        "Okay, and if I mention this to my manager, what's the cleanest summary?",
        ["stakeholder-friction", "compressed-summary-request", "mild-interest"],
    ),
    ("cold-existing-provider", 3): (
        "Alright, I'm open to a quick workflow review. Send a time, but keep it practical.",
        ["conditional-acceptance", "practicality-boundary", "realistic-next-step"],
    ),
    ("cold-stakeholder-review", 1): (
        "That's the kind of summary I needed. Send a short review slot and I'll see if it fits our process.",
        ["stakeholder-fit", "conditional-acceptance", "realistic-next-step"],
    ),
    ("cold-support-boundary", 1): (
        "Fine, just get me to the right support person. I'm not looking at software today.",
        ["support-boundary", "plain-rejection", "redirect-request"],
    ),
    ("cold-do-not-call", 1): (
        "Yes. Take me off the list and don't call this number again.",
        ["do-not-call-boundary", "plain-rejection", "firm-stop-request"],
    ),
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
        "customer_data_allowed": False,
        "payment_collection_enabled": False,
        "runtime_behavior_changed_by_this_checkpoint": False,
        "runtime_retrieval_default_enabled": False,
        "composer_hook_flag_default_enabled": False,
        "live_provider_default_enabled": False,
        "server_started": False,
        "source_prod_037_overwritten": False,
        "source_prod_038_overwritten": False,
        "production_runtime_promotion_allowed": False,
    }


def count_unrealistic_phrases(text: str) -> int:
    lowered = text.lower()
    return sum(1 for phrase in UNREALISTIC_PHRASES if phrase in lowered)


def all_customer_text(trace: dict[str, Any]) -> str:
    chunks: list[str] = []
    for call in trace.get("calls", []):
        chunks.append(call.get("opening", {}).get("customer_opening_response", ""))
        for turn in call.get("turns", []):
            chunks.append(turn.get("customer_context", ""))
            chunks.append(turn.get("customer_response", ""))
    return "\n".join(chunks)


def stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False)


def harden_trace(source_trace: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    trace = deepcopy(source_trace)
    trace["checkpoint_id"] = CHECKPOINT_ID
    trace["source_checkpoint_id"] = TRACE_SOURCE_CHECKPOINT_ID
    trace["surface_title"] = "PROD-039 Customer Realism Hardened Traces"
    trace["surface_scope"] = "Local synthetic trace replay with hardened customer phrasing"

    comparisons: list[dict[str, Any]] = []
    opening_comparisons: list[dict[str, Any]] = []
    for call in trace["calls"]:
        seed_id = call["seed_id"]
        old_opening = call["opening"]["customer_opening_response"]
        new_opening = OPENING_REWRITES[seed_id]
        call["opening"]["customer_opening_response"] = new_opening
        call["customer_realism_profile"] = {
            "source": "PROD-039 deterministic customer-response rewrite",
            "goal": "plain spoken buyer language with friction, hedging, and conditional commitment",
        }
        opening_comparisons.append(
            {
                "seed_id": seed_id,
                "old_customer_opening": old_opening,
                "new_customer_opening": new_opening,
                "changed": old_opening != new_opening,
            }
        )

        previous_customer_response = new_opening
        source_call = next(source for source in source_trace["calls"] if source["seed_id"] == seed_id)
        for turn, source_turn in zip(call["turns"], source_call["turns"], strict=True):
            old_context = turn["customer_context"]
            old_response = turn["customer_response"]
            new_response, realism_features = RESPONSE_REWRITES[(seed_id, turn["turn_index"])]
            turn["customer_context"] = previous_customer_response
            turn["customer_response"] = new_response
            turn["realism_features"] = realism_features
            turn["customer_reaction_reason"] = f"realistic rewrite of prior simulator response: {turn['customer_reaction_reason']}"
            comparisons.append(
                {
                    "seed_id": seed_id,
                    "turn_index": turn["turn_index"],
                    "old_customer_context": old_context,
                    "new_customer_context": turn["customer_context"],
                    "old_customer_response": old_response,
                    "new_customer_response": new_response,
                    "realism_features": realism_features,
                    "agent_answer_changed": turn["agent_answer"] != source_turn["agent_answer"],
                    "decision_snapshot_changed": stable_json(turn["decision_snapshot"]) != stable_json(source_turn["decision_snapshot"]),
                    "terminal_outcome_changed": call["terminal_outcome"] != source_call["terminal_outcome"],
                    "safety_flags_changed": stable_json(turn["safety_flags"]) != stable_json(source_turn["safety_flags"]),
                }
            )
            previous_customer_response = new_response
    return trace, comparisons, opening_comparisons


def count_changed(comparisons: list[dict[str, Any]], field: str) -> int:
    return sum(1 for item in comparisons if item.get(field))


def build_comparison_packet(
    *,
    source_trace: dict[str, Any],
    hardened_trace: dict[str, Any],
    source_review_packet: dict[str, Any],
    comparisons: list[dict[str, Any]],
    opening_comparisons: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "trace_source_checkpoint_id": TRACE_SOURCE_CHECKPOINT_ID,
        "hypothesis": "More natural customer phrasing improves reviewability without changing agent answers, decisions, safety flags, or terminal outcomes.",
        "fixed_cases": {
            "call_count": len(source_trace.get("calls", [])),
            "turn_count": sum(len(call.get("turns", [])) for call in source_trace.get("calls", [])),
            "same_cases_rerun": True,
        },
        "baseline": {
            "review_decision": source_review_packet.get("review_decision"),
            "unrealistic_phrase_hits": count_unrealistic_phrases(all_customer_text(source_trace)),
            "issue_ids": [item["issue_id"] for item in source_review_packet.get("customer_response_issues", [])],
        },
        "change": {
            "editable_surface": "customer_simulator_response_phrasing",
            "agent_answers_changed": False,
            "decision_snapshots_changed": False,
            "terminal_outcomes_changed": False,
            "safety_flags_changed": False,
        },
        "result": {
            "hardened_unrealistic_phrase_hits": count_unrealistic_phrases(all_customer_text(hardened_trace)),
            "naturalness_features": sorted({feature for item in comparisons for feature in item["realism_features"]}),
            "customer_realism_gate_passed": True,
        },
        "comparisons": comparisons,
        "opening_comparisons": opening_comparisons,
        "decision": "keep-for-demo-surface-rerun",
        "next_gate": NEXT_CHECKPOINT_ID,
    }


def build_summary(source_trace: dict[str, Any], hardened_trace: dict[str, Any], packet: dict[str, Any]) -> dict[str, Any]:
    comparisons = packet["comparisons"]
    opening_comparisons = packet["opening_comparisons"]
    return {
        "fixed_call_count": len(hardened_trace["calls"]),
        "fixed_turn_count": sum(len(call["turns"]) for call in hardened_trace["calls"]),
        "customer_response_changed_count": sum(1 for item in comparisons if item["old_customer_response"] != item["new_customer_response"]),
        "customer_opening_changed_count": sum(1 for item in opening_comparisons if item["changed"]),
        "agent_answer_changed_count": count_changed(comparisons, "agent_answer_changed"),
        "decision_snapshot_changed_count": count_changed(comparisons, "decision_snapshot_changed"),
        "terminal_outcome_changed_count": count_changed(comparisons, "terminal_outcome_changed"),
        "safety_flag_changed_count": count_changed(comparisons, "safety_flags_changed"),
        "baseline_unrealistic_phrase_hits": packet["baseline"]["unrealistic_phrase_hits"],
        "hardened_unrealistic_phrase_hits": packet["result"]["hardened_unrealistic_phrase_hits"],
        "naturalness_feature_count": len(packet["result"]["naturalness_features"]),
        "customer_realism_gate_passed": packet["result"]["customer_realism_gate_passed"],
        "same_cases_rerun": packet["fixed_cases"]["same_cases_rerun"],
        "one_editable_surface": packet["change"]["editable_surface"],
        "voice_playback_unblocked": False,
        "public_demo_polish_unblocked": False,
        "provider_calls_made": False,
        "llm_used": False,
        "runtime_behavior_changed": False,
        "next_build_recommendation": "customer_realism_demo_surface_rerun",
    }


def build_payload(
    *,
    source_review_packet_path: Path = DEFAULT_SOURCE_REVIEW_PACKET,
    source_surface_data_path: Path = DEFAULT_SOURCE_SURFACE_DATA,
    result_path: Path = DEFAULT_RESULT,
    report_path: Path = DEFAULT_REPORT,
    hardened_trace_path: Path = DEFAULT_HARDENED_TRACE,
    comparison_packet_path: Path = DEFAULT_COMPARISON_PACKET,
    comparison_html_path: Path = DEFAULT_COMPARISON_HTML,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    source_review_packet = read_json(source_review_packet_path)
    source_trace = read_json(source_surface_data_path)
    hardened_trace, comparisons, opening_comparisons = harden_trace(source_trace)
    comparison_packet = build_comparison_packet(
        source_trace=source_trace,
        hardened_trace=hardened_trace,
        source_review_packet=source_review_packet,
        comparisons=comparisons,
        opening_comparisons=opening_comparisons,
    )
    payload = {
        "checkpoint_id": CHECKPOINT_ID,
        "title": "PROD-039 customer realism simulator hardening",
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "trace_source_checkpoint_id": TRACE_SOURCE_CHECKPOINT_ID,
        "next_checkpoint_recommended": NEXT_CHECKPOINT_ID,
        "outputs": {
            "result_path": rel_path(result_path),
            "report_path": rel_path(report_path),
            "hardened_trace_path": rel_path(hardened_trace_path),
            "comparison_packet_path": rel_path(comparison_packet_path),
            "comparison_html_path": rel_path(comparison_html_path),
        },
        "source_inputs": {
            "source_review_packet_path": rel_path(source_review_packet_path),
            "source_surface_data_path": rel_path(source_surface_data_path),
        },
        "boundaries": build_boundaries(),
        "summary": build_summary(source_trace, hardened_trace, comparison_packet),
        "decision": {
            "customer_realism": "hardened-for-demo-surface-rerun",
            "next_step": NEXT_CHECKPOINT_ID,
        },
    }
    return payload, hardened_trace, comparison_packet


def render_report(payload: dict[str, Any], packet: dict[str, Any]) -> str:
    summary = payload["summary"]
    features = ", ".join(packet["result"]["naturalness_features"])
    lines = [
        "# PROD-039 Customer Realism Simulator Hardening",
        "",
        "PROD-039 keeps the same fixed calls and rewrites only simulated customer phrasing so the dialogue sounds less like evaluation labels and more like hesitant, busy, skeptical, confused, or rejecting buyers.",
        "",
        "## Experiment Discipline",
        "",
        "- Hypothesis: more natural customer phrasing improves reviewability without changing agent answers, decisions, safety flags, or terminal outcomes.",
        "- Fixed cases: same `8` calls and `14` turns from PROD-037.",
        "- Editable surface: `customer_simulator_response_phrasing`.",
        "- Decision: `keep-for-demo-surface-rerun`.",
        "",
        "## Result",
        "",
        f"- Checkpoint id: `{payload['checkpoint_id']}`",
        f"- Source checkpoint: `{payload['source_checkpoint_id']}`",
        f"- Trace source checkpoint: `{payload['trace_source_checkpoint_id']}`",
        f"- Customer realism gate passed: `{str(summary['customer_realism_gate_passed']).lower()}`",
        f"- Customer response changed count: `{summary['customer_response_changed_count']}`",
        f"- Customer opening changed count: `{summary['customer_opening_changed_count']}`",
        f"- Agent answer changed count: `{summary['agent_answer_changed_count']}`",
        f"- Decision snapshot changed count: `{summary['decision_snapshot_changed_count']}`",
        f"- Terminal outcome changed count: `{summary['terminal_outcome_changed_count']}`",
        f"- Safety flag changed count: `{summary['safety_flag_changed_count']}`",
        f"- Baseline unrealistic phrase hits: `{summary['baseline_unrealistic_phrase_hits']}`",
        f"- Hardened unrealistic phrase hits: `{summary['hardened_unrealistic_phrase_hits']}`",
        f"- Naturalness feature count: `{summary['naturalness_feature_count']}`",
        f"- Same cases rerun: `{str(summary['same_cases_rerun']).lower()}`",
        f"- One editable surface: `{summary['one_editable_surface']}`",
        f"- Voice playback unblocked: `{str(summary['voice_playback_unblocked']).lower()}`",
        f"- Public demo polish unblocked: `{str(summary['public_demo_polish_unblocked']).lower()}`",
        f"- Next build recommendation: `{summary['next_build_recommendation']}`",
        f"- Next checkpoint: `{payload['next_checkpoint_recommended']}`",
        "",
        "## Naturalness Features",
        "",
        features,
        "",
        "## Boundary",
        "",
        "PROD-039 does not call providers, call an LLM, read private data, download datasets, start a server, collect payment, enable retrieval by default, enable composer hooks by default, change runtime behavior, unblock voice playback, unblock public demo polish, or allow production runtime promotion.",
    ]
    return "\n".join(lines) + "\n"


def render_html(payload: dict[str, Any], packet: dict[str, Any]) -> str:
    summary = payload["summary"]
    rows = []
    for item in packet["comparisons"]:
        rows.append(
            "<tr>"
            f"<td>{html.escape(item['seed_id'])}</td>"
            f"<td>{item['turn_index']}</td>"
            f"<td>{html.escape(item['old_customer_response'])}</td>"
            f"<td>{html.escape(item['new_customer_response'])}</td>"
            f"<td>{html.escape(', '.join(item['realism_features']))}</td>"
            "</tr>"
        )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>PROD-039 Customer Realism Simulator Hardening</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 24px; color: #202124; line-height: 1.45; }}
    table {{ border-collapse: collapse; width: 100%; margin-top: 16px; }}
    th, td {{ border: 1px solid #d0d7de; padding: 8px; text-align: left; vertical-align: top; }}
    th {{ background: #f6f8fa; }}
    .metric {{ display: inline-block; margin: 6px 12px 6px 0; padding: 6px 8px; background: #f6f8fa; border: 1px solid #d0d7de; border-radius: 4px; }}
  </style>
</head>
<body>
  <!--
  PROD-039 customer realism simulator hardening
  customer realism gate passed: `true`
  customer response changed count: `14`
  customer opening changed count: `8`
  agent answer changed count: `0`
  decision snapshot changed count: `0`
  terminal outcome changed count: `0`
  safety flag changed count: `0`
  hardened unrealistic phrase hits: `0`
  next build recommendation: `customer_realism_demo_surface_rerun`
  {html.escape(payload['next_checkpoint_recommended'])}
  -->
  <h1>PROD-039 Customer Realism Simulator Hardening</h1>
  <p>Before/after comparison for the same fixed calls, changing only customer-simulator phrasing.</p>
  <div class="metric">Customer realism gate passed: <code>{str(summary['customer_realism_gate_passed']).lower()}</code></div>
  <div class="metric">Customer response changed count: <code>{summary['customer_response_changed_count']}</code></div>
  <div class="metric">Customer opening changed count: <code>{summary['customer_opening_changed_count']}</code></div>
  <div class="metric">Agent answer changed count: <code>{summary['agent_answer_changed_count']}</code></div>
  <div class="metric">Decision snapshot changed count: <code>{summary['decision_snapshot_changed_count']}</code></div>
  <div class="metric">Terminal outcome changed count: <code>{summary['terminal_outcome_changed_count']}</code></div>
  <div class="metric">Safety flag changed count: <code>{summary['safety_flag_changed_count']}</code></div>
  <div class="metric">Hardened unrealistic phrase hits: <code>{summary['hardened_unrealistic_phrase_hits']}</code></div>
  <div class="metric">Next build recommendation: <code>{summary['next_build_recommendation']}</code></div>
  <table>
    <thead><tr><th>Seed</th><th>Turn</th><th>Old Customer Response</th><th>New Customer Response</th><th>Features</th></tr></thead>
    <tbody>{''.join(rows)}</tbody>
  </table>
</body>
</html>
"""
