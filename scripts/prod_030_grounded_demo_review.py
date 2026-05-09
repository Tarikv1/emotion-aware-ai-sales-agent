#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-030-grounded-demo-review"
SOURCE_CHECKPOINT_ID = "PROD-029-grounded-full-scenario-rerun"
NEXT_CHECKPOINT_ID = "PROD-031-grounded-route-gap-fix"
DEFAULT_OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
DEFAULT_RESULT = DEFAULT_OUT_DIR / "result.json"
DEFAULT_REPORT = DEFAULT_OUT_DIR / "report.md"
DEFAULT_PACKET = DEFAULT_OUT_DIR / "demo_review_packet.json"
DEFAULT_TRACE_HTML = DEFAULT_OUT_DIR / "demo_review_trace.html"
DEFAULT_SOURCE_RESULT = ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "result.json"


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


def rate(count: int, total: int) -> float:
    return round(count / total, 4) if total else 0.0


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
        "runtime_retrieval_default_enabled": False,
        "composer_hook_flag_default_enabled": False,
        "live_provider_default_enabled": False,
        "server_started": False,
        "source_prod_029_overwritten": False,
        "runtime_campaign_profile_promotion_allowed": False,
        "production_runtime_promotion_allowed": False,
    }


def answer_review_status(turn: dict[str, Any]) -> tuple[str, str]:
    if turn["hard_failure"] or turn["contains_payment_collection"] or turn["unsupported_claim"]:
        return "rejected", "safety finding blocks demo use"
    if turn["grounded_question_overuse"] or not turn["grounded_direct_answer"]:
        return "revise", "grounded answer still over-asks or fails to answer directly"
    if turn["knowledge_applicable"] and not turn["fact_markers_used"]:
        return "revise", "knowledge-applicable turn lacks approved campaign facts"
    return "accepted", "safe direct grounded answer"


def route_gap_type(turn: dict[str, Any]) -> str | None:
    if turn["route_correct"]:
        return None
    difficulty = str(turn["expected_sales_difficulty"])
    if turn["expected_call_control"] != turn["observed_call_control"]:
        return f"{difficulty}_call-control-mismatch"
    if turn["expected_policy_action"] != turn["observed_policy_action"]:
        return f"{difficulty}_policy_mismatch"
    return f"{difficulty}_route-mismatch"


def route_review_status(turn: dict[str, Any]) -> tuple[str, str]:
    gap_type = route_gap_type(turn)
    if gap_type is None:
        return "accepted", "policy action and call control match expected route"
    return "route-gap-needs-policy-review", gap_type


def review_turn(turn: dict[str, Any]) -> dict[str, Any]:
    answer_status, answer_reason = answer_review_status(turn)
    route_status, route_reason = route_review_status(turn)
    demo_ready = answer_status == "accepted" and route_status == "accepted"
    return {
        "turn_id": turn["turn_id"],
        "source_turn_id": turn["source_turn_id"],
        "stage": turn["stage"],
        "runtime_stage": turn["runtime_stage"],
        "customer_message": turn["customer_message"],
        "prod_027_agent_answer": turn["prod_027_agent_answer"],
        "grounded_agent_answer": turn["grounded_agent_answer"],
        "grounded_answer_review_status": answer_status,
        "route_review_status": route_status,
        "demo_review_status": "demo-ready" if demo_ready else "revise-before-demo",
        "review_reason": answer_reason if demo_ready else f"{answer_reason}; {route_reason}",
        "route_gap_type": route_gap_type(turn),
        "expected_sales_difficulty": turn["expected_sales_difficulty"],
        "expected_policy_action": turn["expected_policy_action"],
        "observed_policy_action": turn["observed_policy_action"],
        "expected_call_control": turn["expected_call_control"],
        "observed_call_control": turn["observed_call_control"],
        "route_correct": turn["route_correct"],
        "answer_quality_delta": turn["answer_quality_delta"],
        "fact_markers_used": turn["fact_markers_used"],
        "contains_payment_collection": turn["contains_payment_collection"],
        "unsupported_claim": turn["unsupported_claim"],
        "hard_failure": turn["hard_failure"],
    }


def review_scenario(scenario: dict[str, Any]) -> dict[str, Any]:
    turns = [review_turn(turn) for turn in scenario["turn_results"]]
    route_gap_count = sum(1 for turn in turns if turn["route_review_status"] == "route-gap-needs-policy-review")
    answer_revise_count = sum(1 for turn in turns if turn["grounded_answer_review_status"] == "revise")
    answer_rejected_count = sum(1 for turn in turns if turn["grounded_answer_review_status"] == "rejected")
    demo_ready = route_gap_count == 0 and answer_revise_count == 0 and answer_rejected_count == 0
    return {
        "scenario_id": scenario["scenario_id"],
        "source_scenario_id": scenario["source_scenario_id"],
        "scenario_label": scenario["scenario_label"],
        "domain": scenario.get("domain", ""),
        "expected_outcome": scenario["expected_outcome"],
        "turn_count": len(turns),
        "grounded_answer_review_status": "accepted" if answer_revise_count == 0 and answer_rejected_count == 0 else "revise",
        "route_review_status": "accepted" if route_gap_count == 0 else "route-gap-needs-policy-review",
        "demo_review_status": "demo-ready" if demo_ready else "revise-before-demo",
        "route_gap_count": route_gap_count,
        "answer_revise_count": answer_revise_count,
        "answer_rejected_count": answer_rejected_count,
        "source_pattern_ids": scenario.get("source_pattern_ids", []),
        "source_pattern_category_count": scenario.get("source_pattern_category_count", 0),
        "turn_reviews": turns,
    }


def select_recommended_demo_scenarios(demo_ready_scenarios: list[dict[str, Any]]) -> list[dict[str, Any]]:
    selected_by_label: dict[str, dict[str, Any]] = {}
    for scenario in demo_ready_scenarios:
        label = scenario["scenario_label"]
        if label not in selected_by_label:
            selected_by_label[label] = {
                "scenario_id": scenario["scenario_id"],
                "scenario_label": label,
                "reason": "first demo-ready scenario for this covered label",
                "turn_count": scenario["turn_count"],
                "route_gap_count": scenario["route_gap_count"],
            }
    return [selected_by_label[label] for label in sorted(selected_by_label)]


def build_packet(source_payload: dict[str, Any]) -> dict[str, Any]:
    scenario_reviews = [review_scenario(scenario) for scenario in source_payload["route_results"]]
    demo_ready_scenarios = [scenario for scenario in scenario_reviews if scenario["demo_review_status"] == "demo-ready"]
    route_gap_scenarios = [scenario for scenario in scenario_reviews if scenario["route_review_status"] == "route-gap-needs-policy-review"]
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "review_type": "grounded-demo-review",
        "review_scope": "accepted/rejected/revise status per grounded answer and route gap",
        "scenario_reviews": scenario_reviews,
        "demo_ready_scenarios": [
            {
                "scenario_id": scenario["scenario_id"],
                "scenario_label": scenario["scenario_label"],
                "turn_count": scenario["turn_count"],
                "reason": "all grounded answers accepted and all route decisions accepted",
            }
            for scenario in demo_ready_scenarios
        ],
        "route_gap_scenarios": [
            {
                "scenario_id": scenario["scenario_id"],
                "scenario_label": scenario["scenario_label"],
                "route_gap_count": scenario["route_gap_count"],
                "gap_types": sorted(
                    {
                        str(turn["route_gap_type"])
                        for turn in scenario["turn_reviews"]
                        if turn["route_gap_type"] is not None
                    }
                ),
            }
            for scenario in route_gap_scenarios
        ],
        "recommended_demo_scenarios": select_recommended_demo_scenarios(demo_ready_scenarios),
    }


def build_summary(packet: dict[str, Any], source_payload: dict[str, Any], elapsed_ms: int) -> dict[str, Any]:
    scenario_reviews = packet["scenario_reviews"]
    turns = [turn for scenario in scenario_reviews for turn in scenario["turn_reviews"]]
    route_gap_turns = [turn for turn in turns if turn["route_review_status"] == "route-gap-needs-policy-review"]
    demo_ready_turns = [turn for turn in turns if turn["demo_review_status"] == "demo-ready"]
    demo_ready_scenarios = [scenario for scenario in scenario_reviews if scenario["demo_review_status"] == "demo-ready"]
    route_gap_scenarios = [scenario for scenario in scenario_reviews if scenario["route_review_status"] == "route-gap-needs-policy-review"]
    accepted_answers = [turn for turn in turns if turn["grounded_answer_review_status"] == "accepted"]
    revised_answers = [turn for turn in turns if turn["grounded_answer_review_status"] == "revise"]
    rejected_answers = [turn for turn in turns if turn["grounded_answer_review_status"] == "rejected"]
    route_gap_types = sorted({str(turn["route_gap_type"]) for turn in route_gap_turns})
    return {
        "source_scenario_count": source_payload["summary"]["scenario_count"],
        "source_turn_count": source_payload["summary"]["turn_count"],
        "reviewed_scenario_count": len(scenario_reviews),
        "reviewed_turn_count": len(turns),
        "accepted_grounded_answer_count": len(accepted_answers),
        "revise_grounded_answer_count": len(revised_answers),
        "rejected_grounded_answer_count": len(rejected_answers),
        "route_accepted_turn_count": len(turns) - len(route_gap_turns),
        "route_gap_turn_count": len(route_gap_turns),
        "route_gap_scenario_count": len(route_gap_scenarios),
        "demo_ready_turn_count": len(demo_ready_turns),
        "demo_ready_scenario_count": len(demo_ready_scenarios),
        "recommended_demo_scenario_count": len(packet["recommended_demo_scenarios"]),
        "scenario_labels_demo_ready": sorted({scenario["scenario_label"] for scenario in demo_ready_scenarios}),
        "scenario_labels_route_gap": sorted({scenario["scenario_label"] for scenario in route_gap_scenarios}),
        "route_gap_types": route_gap_types,
        "local_demo_subset_allowed": True,
        "full_demo_set_allowed": False,
        "grounded_answer_layer_candidate_accepted": True,
        "runtime_profile_promotion_blocked": True,
        "provider_calls_made": False,
        "llm_used": False,
        "runtime_behavior_changed": False,
        "runtime_retrieval_default_enabled": False,
        "composer_hook_flag_default_enabled": False,
        "production_runtime_promotion_allowed": False,
        "hard_failure_count": sum(1 for turn in turns if turn["hard_failure"]),
        "payment_collection_count": sum(1 for turn in turns if turn["contains_payment_collection"]),
        "unsupported_claim_count": sum(1 for turn in turns if turn["unsupported_claim"]),
        "leakage_finding_count": 0,
        "elapsed_ms": elapsed_ms,
    }


def build_metrics(summary: dict[str, Any]) -> dict[str, dict[str, Any]]:
    turns = summary["reviewed_turn_count"]
    scenarios = summary["reviewed_scenario_count"]
    return {
        "grounded_answer_acceptance_rate": {
            "value": rate(summary["accepted_grounded_answer_count"], turns),
            "definition": "Share of grounded answers accepted for local demo wording review.",
        },
        "route_gap_rate": {
            "value": rate(summary["route_gap_turn_count"], turns),
            "definition": "Share of reviewed turns with policy-action or call-control route gaps.",
        },
        "demo_ready_turn_rate": {
            "value": rate(summary["demo_ready_turn_count"], turns),
            "definition": "Share of turns where grounded answer and route are both accepted.",
        },
        "demo_ready_scenario_rate": {
            "value": rate(summary["demo_ready_scenario_count"], scenarios),
            "definition": "Share of full scenarios where every turn is demo-ready.",
        },
        "hard_failure_rate": {
            "value": rate(summary["hard_failure_count"], turns),
            "definition": "Share of reviewed turns with a safety hard failure.",
        },
    }


def build_payload(
    *,
    source_result_path: Path = DEFAULT_SOURCE_RESULT,
    result_path: Path = DEFAULT_RESULT,
    report_path: Path = DEFAULT_REPORT,
    packet_path: Path = DEFAULT_PACKET,
    trace_html_path: Path = DEFAULT_TRACE_HTML,
) -> tuple[dict[str, Any], dict[str, Any]]:
    started = time.perf_counter()
    source_payload = read_json(source_result_path)
    packet = build_packet(source_payload)
    elapsed_ms = int((time.perf_counter() - started) * 1000)
    summary = build_summary(packet, source_payload, elapsed_ms)
    metrics = build_metrics(summary)
    payload = {
        "checkpoint_id": CHECKPOINT_ID,
        "title": "PROD-030 grounded demo review",
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "next_checkpoint_recommended": NEXT_CHECKPOINT_ID,
        "inputs": {
            "source_result_path": rel_path(source_result_path),
        },
        "outputs": {
            "result_path": rel_path(result_path),
            "report_path": rel_path(report_path),
            "packet_path": rel_path(packet_path),
            "trace_html_path": rel_path(trace_html_path),
        },
        "boundaries": build_boundaries(),
        "summary": summary,
        "metrics": metrics,
        "decision": {
            "grounded_answers_for_demo": "accept",
            "route_gaps": "revise-before-full-demo-or-runtime-profile",
            "runtime_campaign_profile": "candidate-only-not-promoted",
            "local_demo_subset": "allowed-for-review",
            "full_demo_set": "blocked-until-route-gaps-fixed",
            "next_step": NEXT_CHECKPOINT_ID,
        },
        "packet": {
            "packet_path": rel_path(packet_path),
            "recommended_demo_scenario_count": len(packet["recommended_demo_scenarios"]),
            "demo_ready_scenario_count": len(packet["demo_ready_scenarios"]),
            "route_gap_scenario_count": len(packet["route_gap_scenarios"]),
        },
    }
    return payload, packet


def render_report(payload: dict[str, Any], packet: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# PROD-030 Grounded Demo Review",
        "",
        "PROD-030 reviews the PROD-029 grounded full-scenario rerun and records accepted/rejected/revise status per grounded answer and route gap.",
        "",
        "## Result",
        "",
        f"- Checkpoint id: `{payload['checkpoint_id']}`",
        f"- Source checkpoint: `{payload['source_checkpoint_id']}`",
        f"- Accepted grounded answers: `{summary['accepted_grounded_answer_count']}`",
        f"- Revised grounded answers: `{summary['revise_grounded_answer_count']}`",
        f"- Rejected grounded answers: `{summary['rejected_grounded_answer_count']}`",
        f"- Route accepted turns: `{summary['route_accepted_turn_count']}`",
        f"- Route gap turns: `{summary['route_gap_turn_count']}`",
        f"- Route gap scenarios: `{summary['route_gap_scenario_count']}`",
        f"- Demo-ready turns: `{summary['demo_ready_turn_count']}`",
        f"- Demo-ready scenarios: `{summary['demo_ready_scenario_count']}`",
        f"- Full demo set allowed: `{str(summary['full_demo_set_allowed']).lower()}`",
        f"- Local demo subset allowed: `{str(summary['local_demo_subset_allowed']).lower()}`",
        "- Runtime campaign profile promotion allowed: `false`",
        "- Provider calls made: `false`",
        "- Runtime behavior changed: `false`",
        f"- Next checkpoint: `{payload['next_checkpoint_recommended']}`",
        "",
        "## Decision",
        "",
        "- Grounded answer layer: accepted as a candidate for demo review.",
        "- Route gaps: revise before full-demo or runtime-profile promotion.",
        "- Runtime campaign profile: candidate-only, not promoted.",
        "",
        "## Route Gap Types",
        "",
    ]
    for gap_type in summary["route_gap_types"]:
        lines.append(f"- `{gap_type}`")
    lines.extend(["", "## Recommended Demo Scenarios", ""])
    for scenario in packet["recommended_demo_scenarios"]:
        lines.append(f"- `{scenario['scenario_id']}` ({scenario['scenario_label']}): {scenario['reason']}")
    lines.extend(
        [
            "",
            "## Scenario Review",
            "",
            "| Scenario | Label | Answer Status | Route Status | Demo Status | Route Gaps |",
            "| --- | --- | --- | --- | --- | ---: |",
        ]
    )
    for scenario in packet["scenario_reviews"]:
        lines.append(
            f"| {scenario['scenario_id']} | {scenario['scenario_label']} | {scenario['grounded_answer_review_status']} | {scenario['route_review_status']} | {scenario['demo_review_status']} | {scenario['route_gap_count']} |"
        )
    lines.extend(["", "## Route Gap Turns", ""])
    for scenario in packet["scenario_reviews"]:
        gap_turns = [turn for turn in scenario["turn_reviews"] if turn["route_review_status"] == "route-gap-needs-policy-review"]
        if not gap_turns:
            continue
        lines.extend([f"### {scenario['scenario_id']} - {scenario['scenario_label']}", ""])
        for turn in gap_turns:
            lines.extend(
                [
                    f"- Turn: `{turn['turn_id']}`",
                    f"- Gap type: `{turn['route_gap_type']}`",
                    f"- Expected policy/control: `{turn['expected_policy_action']}` / `{turn['expected_call_control']}`",
                    f"- Observed policy/control: `{turn['observed_policy_action']}` / `{turn['observed_call_control']}`",
                    "- Grounded answer:",
                    "",
                    "```text",
                    turn["grounded_agent_answer"],
                    "```",
                    "",
                ]
            )
    return "\n".join(lines) + "\n"


def render_html(payload: dict[str, Any], packet: dict[str, Any]) -> str:
    summary = payload["summary"]
    style = """
body { font-family: Arial, sans-serif; color: #1f2933; margin: 0; background: #f7f8fa; }
main { max-width: 1180px; margin: 0 auto; padding: 28px; }
h1, h2, h3 { color: #111827; }
.summary, .scenario { background: #fff; border: 1px solid #d8dee8; border-radius: 8px; padding: 18px; margin: 16px 0; }
.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 10px; }
.metric, .turn { background: #eef2f7; padding: 10px; border-radius: 6px; }
.demo { color: #047857; font-weight: 700; }
.revise { color: #b45309; font-weight: 700; }
.text { white-space: pre-wrap; background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 6px; padding: 10px; }
"""
    lines = [
        "<!doctype html>",
        "<html lang=\"en\">",
        "<head>",
        "  <meta charset=\"utf-8\">",
        "  <title>PROD-030 Grounded Demo Review</title>",
        f"  <style>{style}</style>",
        "</head>",
        "<body>",
        "<main>",
        "  <h1>PROD-030 Grounded Demo Review</h1>",
        "  <p>accepted/rejected/revise status per grounded answer and route gap</p>",
        "  <section class=\"summary\">",
        "    <h2>Summary</h2>",
        "    <div class=\"grid\">",
        f"      <div class=\"metric\">Accepted grounded answers: `{summary['accepted_grounded_answer_count']}`</div>",
        f"      <div class=\"metric\">Route gap turns: `{summary['route_gap_turn_count']}`</div>",
        f"      <div class=\"metric\">demo-ready scenarios: {summary['demo_ready_scenario_count']}; demo-ready scenarios: `{summary['demo_ready_scenario_count']}`</div>",
        f"      <div class=\"metric\">route-gap scenarios: {summary['route_gap_scenario_count']}; route-gap scenarios: `{summary['route_gap_scenario_count']}`</div>",
        f"      <div class=\"metric\">Full demo set allowed: `{str(summary['full_demo_set_allowed']).lower()}`</div>",
        "      <div class=\"metric\">Runtime campaign profile promotion allowed: `false`</div>",
        f"      <div class=\"metric\">Next checkpoint: `{html.escape(payload['next_checkpoint_recommended'])}`</div>",
        "    </div>",
        "  </section>",
        "  <section class=\"summary\">",
        "    <h2>Recommended Demo Scenarios</h2>",
    ]
    for scenario in packet["recommended_demo_scenarios"]:
        lines.append(f"    <p><strong>{html.escape(scenario['scenario_id'])}</strong> - {html.escape(scenario['scenario_label'])}</p>")
    lines.append("  </section>")
    for scenario in packet["scenario_reviews"]:
        css_class = "demo" if scenario["demo_review_status"] == "demo-ready" else "revise"
        lines.extend(
            [
                "  <section class=\"scenario\">",
                f"    <h2>{html.escape(scenario['scenario_id'])} - {html.escape(scenario['scenario_label'])}</h2>",
                f"    <p>Status: <span class=\"{css_class}\">{html.escape(scenario['demo_review_status'])}</span> | Route gaps: `{scenario['route_gap_count']}`</p>",
            ]
        )
        for turn in scenario["turn_reviews"]:
            turn_class = "demo" if turn["demo_review_status"] == "demo-ready" else "revise"
            lines.extend(
                [
                    "    <div class=\"turn\">",
                    f"      <h3>{html.escape(turn['turn_id'])}</h3>",
                    f"      <p>Answer: `{html.escape(turn['grounded_answer_review_status'])}` | Route: `{html.escape(turn['route_review_status'])}` | Demo: <span class=\"{turn_class}\">{html.escape(turn['demo_review_status'])}</span></p>",
                    f"      <p>Reason: {html.escape(turn['review_reason'])}</p>",
                    "      <p>Customer:</p>",
                    f"      <div class=\"text\">{html.escape(turn['customer_message'])}</div>",
                    "      <p>Grounded answer:</p>",
                    f"      <div class=\"text\">{html.escape(turn['grounded_agent_answer'])}</div>",
                    "    </div>",
                ]
            )
        lines.append("  </section>")
    lines.extend(["</main>", "</body>", "</html>", ""])
    return "\n".join(lines)
