#!/usr/bin/env python3
from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-026-local-demo-trace-harness"
SOURCE_CHECKPOINT_ID = "PROD-025-bounded-demo-readiness-packet"
DEFAULT_SOURCE_PROD_025_RESULT = (
    ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "result.json"
)
DEFAULT_OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
DEFAULT_RESULT = DEFAULT_OUT_DIR / "result.json"
DEFAULT_REPORT = DEFAULT_OUT_DIR / "report.md"
DEFAULT_TRACE_PACKET = DEFAULT_OUT_DIR / "trace_packet.json"
DEFAULT_TRACE_HTML = DEFAULT_OUT_DIR / "trace_harness.html"
NEXT_CHECKPOINT = "PROD-027-manual-demo-trace-review"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def relpath(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def build_boundaries() -> dict[str, bool]:
    return {
        "provider_calls_made": False,
        "llm_used": False,
        "private_data_read": False,
        "dataset_download_performed": False,
        "runtime_behavior_changed_by_this_checkpoint": False,
        "runtime_retrieval_default_enabled": False,
        "composer_hook_flag_default_enabled": False,
        "live_provider_default_enabled": False,
        "customer_data_allowed": False,
        "payment_collection_enabled": False,
        "customer_facing_claim_allowed": False,
        "server_started": False,
    }


def build_trace_cards(source_payload: dict[str, Any]) -> list[dict[str, Any]]:
    trace_cards = []
    for index, source_card in enumerate(source_payload["demo_trace_cards"], start=1):
        trace_cards.append(
            {
                "card_id": f"demo-trace-{index:03d}",
                "source_turn_id": source_card["turn_id"],
                "scenario_label": source_card["scenario_label"],
                "customer_question": source_card["customer_question"],
                "agent_answer": source_card["agent_answer"],
                "decision_process": {
                    "policy_action": source_card["policy_action"],
                    "call_control": source_card["call_control"],
                    "expected_outcome": source_card["expected_outcome"],
                    "source_checkpoint": source_card["source_checkpoint"],
                },
                "safety_flags": source_card["safety_flags"],
                "review_status": "pending-manual-review",
            }
        )
    return trace_cards


def build_harness_summary(source_payload: dict[str, Any], trace_cards: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "source_trace_card_count": len(source_payload["demo_trace_cards"]),
        "trace_card_count": len(trace_cards),
        "exact_question_and_answer_visible": True,
        "decision_process_visible": True,
        "safety_flags_visible": True,
        "local_trace_only": True,
        "manual_review_required": True,
        "local_demo_trace_harness_ready": len(trace_cards) == len(source_payload["demo_trace_cards"]) == 3,
        "production_runtime_promotion_allowed": False,
        "live_provider_demo_allowed": False,
        "next_checkpoint_recommended": NEXT_CHECKPOINT,
    }


def build_review_checklist() -> list[dict[str, str]]:
    return [
        {
            "check_id": "exact-question-answer-visible",
            "status": "pending-manual-review",
            "question": "Can Tarik see the exact synthetic customer question and exact agent answer for each card?",
        },
        {
            "check_id": "decision-process-understandable",
            "status": "pending-manual-review",
            "question": "Are policy action, call control, expected outcome, and source checkpoint clear enough to inspect?",
        },
        {
            "check_id": "safety-boundary-visible",
            "status": "pending-manual-review",
            "question": "Are payment, hard failure, and protected-context flags visible on each trace card?",
        },
        {
            "check_id": "demo-claim-contained",
            "status": "pending-manual-review",
            "question": "Does the harness avoid production, live-provider, customer-data, and default-retrieval claims?",
        },
    ]


def build_trace_packet(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "title": "PROD-026 local demo trace packet",
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "boundaries": payload["boundaries"],
        "harness_summary": payload["harness_summary"],
        "trace_cards": payload["trace_cards"],
        "review_checklist": payload["manual_review_checklist"],
    }


def build_payload(
    source_prod_025_result_path: Path = DEFAULT_SOURCE_PROD_025_RESULT,
    *,
    report_path: Path = DEFAULT_REPORT,
    trace_packet_path: Path = DEFAULT_TRACE_PACKET,
    trace_html_path: Path = DEFAULT_TRACE_HTML,
) -> dict[str, Any]:
    source_payload = read_json(source_prod_025_result_path)
    trace_cards = build_trace_cards(source_payload)
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "title": "PROD-026 local demo trace harness",
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "source_prod_025_result_path": relpath(source_prod_025_result_path),
        "purpose": "Build a local trace-only demo harness from the accepted PROD-025 readiness packet without starting a server or enabling live behavior.",
        "boundaries": build_boundaries(),
        "source_prod_025_readiness_summary": source_payload["readiness_summary"],
        "harness_summary": build_harness_summary(source_payload, trace_cards),
        "harness_outputs": {
            "trace_packet_path": relpath(trace_packet_path),
            "static_html_path": relpath(trace_html_path),
            "report_path": relpath(report_path),
        },
        "trace_cards": trace_cards,
        "manual_review_checklist": build_review_checklist(),
        "decision": "local_trace_harness_ready_pending_manual_review",
    }


def render_trace_card_markdown(card: dict[str, Any]) -> list[str]:
    decision = card["decision_process"]
    return [
        f"### {card['card_id']} - {card['source_turn_id']}",
        "",
        f"- Scenario label: `{card['scenario_label']}`",
        f"- Policy action: `{decision['policy_action']}`",
        f"- Call control: `{decision['call_control']}`",
        f"- Expected outcome: `{decision['expected_outcome']}`",
        f"- Source checkpoint: `{decision['source_checkpoint']}`",
        f"- Safety flags: `{json.dumps(card['safety_flags'], sort_keys=True)}`",
        f"- Review status: `{card['review_status']}`",
        "",
        "Customer question:",
        "",
        "```text",
        card["customer_question"],
        "```",
        "",
        "Agent answer:",
        "",
        "```text",
        card["agent_answer"],
        "```",
        "",
    ]


def render_report(payload: dict[str, Any]) -> str:
    summary = payload["harness_summary"]
    boundaries = payload["boundaries"]
    lines = [
        "# PROD-026 Local Demo Trace Harness",
        "",
        "PROD-026 builds the local demo trace harness from PROD-025. It is a static trace artifact only; it does not start a server, call providers, use customer data, or promote production runtime behavior.",
        "",
        "## Summary",
        "",
        f"- Source checkpoint: `{payload['source_checkpoint_id']}`",
        f"- Source PROD-025 result: `{payload['source_prod_025_result_path']}`",
        f"- Trace cards: `{summary['trace_card_count']}`",
        f"- Exact question and answer visible: `{str(summary['exact_question_and_answer_visible']).lower()}`",
        f"- Decision process visible: `{str(summary['decision_process_visible']).lower()}`",
        f"- Safety flags visible: `{str(summary['safety_flags_visible']).lower()}`",
        f"- Local trace only: `{str(summary['local_trace_only']).lower()}`",
        f"- Manual review required: `{str(summary['manual_review_required']).lower()}`",
        f"- Provider calls made: `{str(boundaries['provider_calls_made']).lower()}`",
        f"- Customer data allowed: `{str(boundaries['customer_data_allowed']).lower()}`",
        f"- Retrieval default enabled: `{str(boundaries['runtime_retrieval_default_enabled']).lower()}`",
        f"- Composer hook default enabled: `{str(boundaries['composer_hook_flag_default_enabled']).lower()}`",
        f"- Live provider demo allowed: `{str(summary['live_provider_demo_allowed']).lower()}`",
        f"- Production runtime promotion allowed: `{str(summary['production_runtime_promotion_allowed']).lower()}`",
        f"- Next checkpoint recommended: `{summary['next_checkpoint_recommended']}`",
        "",
        "## Harness Outputs",
        "",
        f"- Trace packet: `{payload['harness_outputs']['trace_packet_path']}`",
        f"- Static HTML: `{payload['harness_outputs']['static_html_path']}`",
        f"- Report: `{payload['harness_outputs']['report_path']}`",
        "",
        "## Trace Cards",
        "",
    ]
    for card in payload["trace_cards"]:
        lines.extend(render_trace_card_markdown(card))

    lines.extend(["## Manual Review Checklist", ""])
    for item in payload["manual_review_checklist"]:
        lines.append(f"- `{item['check_id']}`: {item['question']} Status: `{item['status']}`")

    lines.extend(
        [
            "",
            "## Decision",
            "",
            "Keep PROD-026 as a local trace harness pending manual review. Build `PROD-027-manual-demo-trace-review` next before any provider-backed, voice, telephony, or client-facing demo step.",
            "",
        ]
    )
    return "\n".join(lines)


def html_escape(value: Any) -> str:
    return html.escape(str(value), quote=True)


def render_html(payload: dict[str, Any]) -> str:
    summary = payload["harness_summary"]
    boundaries = payload["boundaries"]
    cards = []
    for card in payload["trace_cards"]:
        decision = card["decision_process"]
        cards.append(
            f"""
      <article class="trace-card">
        <h2>{html_escape(card['card_id'])} / {html_escape(card['source_turn_id'])}</h2>
        <dl>
          <dt>Scenario</dt><dd>{html_escape(card['scenario_label'])}</dd>
          <dt>Policy action</dt><dd>{html_escape(decision['policy_action'])}</dd>
          <dt>Call control</dt><dd>{html_escape(decision['call_control'])}</dd>
          <dt>Expected outcome</dt><dd>{html_escape(decision['expected_outcome'])}</dd>
          <dt>Source checkpoint</dt><dd>{html_escape(decision['source_checkpoint'])}</dd>
          <dt>Review status</dt><dd>{html_escape(card['review_status'])}</dd>
        </dl>
        <section>
          <h3>Customer Question</h3>
          <p>{html_escape(card['customer_question'])}</p>
        </section>
        <section>
          <h3>Agent Answer</h3>
          <p>{html_escape(card['agent_answer'])}</p>
        </section>
        <section>
          <h3>Safety Flags</h3>
          <pre>{html_escape(json.dumps(card['safety_flags'], indent=2, sort_keys=True))}</pre>
        </section>
      </article>
            """.strip()
        )

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>PROD-026 Local Demo Trace Harness</title>
  <style>
    body {{
      font-family: Arial, sans-serif;
      margin: 0;
      background: #f6f7f9;
      color: #1f2933;
    }}
    main {{
      max-width: 980px;
      margin: 0 auto;
      padding: 32px 20px;
    }}
    h1 {{
      margin: 0 0 12px;
      font-size: 30px;
    }}
    .summary, .trace-card {{
      background: #ffffff;
      border: 1px solid #d6dbe1;
      border-radius: 6px;
      padding: 18px;
      margin: 16px 0;
    }}
    dl {{
      display: grid;
      grid-template-columns: 180px 1fr;
      gap: 8px 12px;
    }}
    dt {{
      font-weight: 700;
    }}
    dd {{
      margin: 0;
    }}
    p, pre {{
      line-height: 1.45;
    }}
    pre {{
      white-space: pre-wrap;
      background: #eef2f6;
      padding: 12px;
      border-radius: 4px;
    }}
  </style>
</head>
<body>
  <main>
    <h1>PROD-026 Local Demo Trace Harness</h1>
    <p>Local demo trace harness built from PROD-025. This is a static trace artifact only.</p>
    <section class="summary">
      <h2>Boundary Summary</h2>
      <p>Exact question and answer visible: `true`</p>
      <p>Decision process visible: `true`</p>
      <p>Local trace only: `true`</p>
      <p>Manual review required: `true`</p>
      <p>Provider calls made: `false`</p>
      <p>Customer data allowed: `false`</p>
      <p>Retrieval default enabled: `false`</p>
      <p>Composer hook default enabled: `false`</p>
      <p>Next checkpoint recommended: `{html_escape(summary['next_checkpoint_recommended'])}`</p>
    </section>
    <section class="summary">
      <h2>Harness Outputs</h2>
      <p>Trace packet: `{html_escape(payload['harness_outputs']['trace_packet_path'])}`</p>
      <p>Report: `{html_escape(payload['harness_outputs']['report_path'])}`</p>
      <p>Server started: `{str(boundaries['server_started']).lower()}`</p>
    </section>
    {''.join(cards)}
  </main>
</body>
</html>
"""
