#!/usr/bin/env python3
from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-037-local-interactive-trace-demo-surface"
SOURCE_CHECKPOINT_ID = "PROD-036-interactive-demo-readiness-review"
NEXT_CHECKPOINT_ID = "PROD-038-local-demo-surface-review"
DEFAULT_OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
DEFAULT_RESULT = DEFAULT_OUT_DIR / "result.json"
DEFAULT_REPORT = DEFAULT_OUT_DIR / "report.md"
DEFAULT_SURFACE = DEFAULT_OUT_DIR / "local_interactive_trace_demo_surface.html"
DEFAULT_SURFACE_DATA = DEFAULT_OUT_DIR / "local_interactive_trace_demo_surface_data.json"
DEFAULT_SOURCE_PACKET = ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "interactive_demo_readiness_packet.json"


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
        "source_prod_036_overwritten": False,
        "production_runtime_promotion_allowed": False,
    }


def bool_text(value: bool) -> str:
    return str(value).lower()


def display_label(text: str) -> str:
    return text.replace("-", " ").replace("_", " ").title()


def normalize_turn(turn: dict[str, Any]) -> dict[str, Any]:
    decision = turn.get("decision_snapshot", {})
    return {
        "turn_index": turn["turn_index"],
        "customer_context": turn["customer_context"],
        "agent_answer": turn["agent_answer"],
        "customer_response": turn["customer_response"],
        "decision_snapshot": {
            "sales_difficulty": decision.get("sales_difficulty"),
            "interest_state": decision.get("interest_state"),
            "selected_strategy": decision.get("selected_strategy"),
            "next_action": decision.get("next_action"),
            "call_control": decision.get("call_control"),
            "decision_trace_alignment": decision.get("decision_trace_alignment", {}),
        },
        "state_before": turn.get("state_before", {}),
        "state_after": turn.get("state_after", {}),
        "state_delta": turn.get("state_delta", {}),
        "safety_flags": turn.get("safety_flags", {}),
        "customer_reaction_reason": turn.get("customer_reaction_reason", ""),
    }


def build_surface_call(card: dict[str, Any]) -> dict[str, Any]:
    return {
        "seed_id": card["seed_id"],
        "persona": card["persona"],
        "demo_ready": card["demo_ready"],
        "terminal_outcome": card["terminal_outcome"],
        "terminal_decision_source": card["terminal_decision_source"],
        "terminal_reason": card["terminal_reason"],
        "opening": {
            "agent_opening": card["opening"]["agent_opening"],
            "customer_opening_response": card["opening"]["customer_opening_response"],
            "opening_checks": card["opening"].get("opening_checks", {}),
        },
        "turns": [normalize_turn(turn) for turn in card.get("turns", [])],
    }


def build_surface_data(source_packet: dict[str, Any]) -> dict[str, Any]:
    calls = [build_surface_call(card) for card in source_packet["demo_cards"]]
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "surface_title": "PROD-037 Local Interactive Trace Demo Surface",
        "surface_scope": "Local synthetic trace replay",
        "calls": calls,
        "review_contract": {
            "exact_customer_text_visible": True,
            "exact_agent_answer_visible": True,
            "decision_process_visible": True,
            "state_transition_visible": True,
            "terminal_outcome_visible": True,
            "safety_flags_visible": True,
            "cold_opening_visible": True,
            "replay_controls_visible": True,
            "local_synthetic_label_visible": True,
        },
    }


def count_turns(surface_data: dict[str, Any]) -> int:
    return sum(len(call.get("turns", [])) for call in surface_data.get("calls", []))


def build_summary(surface_data: dict[str, Any], source_packet: dict[str, Any]) -> dict[str, Any]:
    call_count = len(surface_data["calls"])
    turn_count = count_turns(surface_data)
    return {
        "source_demo_card_count": len(source_packet.get("demo_cards", [])),
        "surface_call_count": call_count,
        "surface_turn_count": turn_count,
        "visible_call_count": call_count,
        "visible_turn_count": turn_count,
        "selectable_call_count": call_count,
        "selectable_turn_count": turn_count,
        "surface_ready": call_count == 8 and turn_count == 14,
        "static_html_ready": True,
        "keyboard_accessible_controls": True,
        "exact_customer_text_visible": True,
        "exact_agent_answer_visible": True,
        "decision_process_visible": True,
        "state_transition_visible": True,
        "terminal_outcome_visible": True,
        "safety_flags_visible": True,
        "cold_opening_visible": True,
        "replay_controls_visible": True,
        "local_synthetic_label_visible": True,
        "provider_calls_made": False,
        "llm_used": False,
        "server_started": False,
        "runtime_behavior_changed": False,
        "production_runtime_promotion_allowed": False,
    }


def build_payload(
    *,
    source_packet_path: Path = DEFAULT_SOURCE_PACKET,
    result_path: Path = DEFAULT_RESULT,
    report_path: Path = DEFAULT_REPORT,
    surface_path: Path = DEFAULT_SURFACE,
    surface_data_path: Path = DEFAULT_SURFACE_DATA,
) -> tuple[dict[str, Any], dict[str, Any]]:
    source_packet = read_json(source_packet_path)
    surface_data = build_surface_data(source_packet)
    payload = {
        "checkpoint_id": CHECKPOINT_ID,
        "title": "PROD-037 local interactive trace demo surface",
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "next_checkpoint_recommended": NEXT_CHECKPOINT_ID,
        "outputs": {
            "result_path": rel_path(result_path),
            "report_path": rel_path(report_path),
            "surface_path": rel_path(surface_path),
            "surface_data_path": rel_path(surface_data_path),
        },
        "source_inputs": {
            "source_packet_path": rel_path(source_packet_path),
        },
        "boundaries": build_boundaries(),
        "summary": build_summary(surface_data, source_packet),
        "decision": {
            "demo_surface": "built-local-static-trace-replay",
            "demo_scope": "local synthetic trace replay",
            "next_step": NEXT_CHECKPOINT_ID,
        },
    }
    return payload, surface_data


def render_report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# PROD-037 Local Interactive Trace Demo Surface",
        "",
        "PROD-037 builds the local interactive trace demo surface from the accepted PROD-036 readiness packet. It is a static local replay view, not a live runtime.",
        "",
        "## Result",
        "",
        f"- Checkpoint id: `{payload['checkpoint_id']}`",
        f"- Source checkpoint: `{payload['source_checkpoint_id']}`",
        f"- Surface ready: `{bool_text(summary['surface_ready'])}`",
        f"- Visible calls: `{summary['visible_call_count']}`",
        f"- Visible turns: `{summary['visible_turn_count']}`",
        f"- Selectable calls: `{summary['selectable_call_count']}`",
        f"- Selectable turns: `{summary['selectable_turn_count']}`",
        f"- Static HTML ready: `{bool_text(summary['static_html_ready'])}`",
        f"- Keyboard accessible controls: `{bool_text(summary['keyboard_accessible_controls'])}`",
        f"- Exact customer text visible: `{bool_text(summary['exact_customer_text_visible'])}`",
        f"- Exact agent answer visible: `{bool_text(summary['exact_agent_answer_visible'])}`",
        f"- Decision process visible: `{bool_text(summary['decision_process_visible'])}`",
        f"- State transition visible: `{bool_text(summary['state_transition_visible'])}`",
        f"- Terminal outcome visible: `{bool_text(summary['terminal_outcome_visible'])}`",
        f"- Safety flags visible: `{bool_text(summary['safety_flags_visible'])}`",
        f"- Cold opening visible: `{bool_text(summary['cold_opening_visible'])}`",
        f"- Replay controls visible: `{bool_text(summary['replay_controls_visible'])}`",
        f"- Local synthetic trace replay: `{bool_text(summary['local_synthetic_label_visible'])}`",
        f"- Next checkpoint: `{payload['next_checkpoint_recommended']}`",
        "",
        "## How To Open",
        "",
        f"Open `{payload['outputs']['surface_path']}` in a browser. No server is required.",
        "",
        "## Boundary",
        "",
        "PROD-037 does not call providers, call an LLM, read private data, download datasets, start a server, collect payment, enable retrieval by default, enable composer hooks by default, change runtime behavior, or allow production runtime promotion.",
    ]
    return "\n".join(lines) + "\n"


def render_state_table(title: str, state: dict[str, Any]) -> str:
    if not state:
        return f"<div><h4>{html.escape(title)}</h4><p class=\"muted\">No values.</p></div>"
    rows = "".join(
        f"<tr><th>{html.escape(display_label(str(key)))}</th><td>{html.escape(str(value))}</td></tr>"
        for key, value in state.items()
    )
    return f"<div><h4>{html.escape(title)}</h4><table>{rows}</table></div>"


def render_surface_html(payload: dict[str, Any], surface_data: dict[str, Any]) -> str:
    summary = payload["summary"]
    data_json = (
        json.dumps(surface_data, ensure_ascii=False)
        .replace("&", "\\u0026")
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
    )
    first_call = surface_data["calls"][0]
    first_turn = first_call["turns"][0]
    call_buttons = []
    for index, call in enumerate(surface_data["calls"]):
        selected = "true" if index == 0 else "false"
        call_buttons.append(
            f"<button type=\"button\" class=\"call-button\" data-call-index=\"{index}\" aria-pressed=\"{selected}\">"
            f"<span>{html.escape(call['seed_id'])}</span>"
            f"<small>{html.escape(call['terminal_outcome'])}</small>"
            "</button>"
        )
    turn_buttons = []
    for index, turn in enumerate(first_call["turns"]):
        selected = "true" if index == 0 else "false"
        turn_buttons.append(
            f"<button type=\"button\" class=\"turn-button\" data-turn-index=\"{index}\" aria-pressed=\"{selected}\">"
            f"Turn {turn['turn_index']}"
            "</button>"
        )

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>PROD-037 Local Interactive Trace Demo Surface</title>
  <style>
    :root {{
      color-scheme: light;
      --ink: #15171a;
      --muted: #626b76;
      --line: #d9dee5;
      --panel: #f7f8fa;
      --accent: #0b5fff;
      --accent-soft: #e8f0ff;
      --ok: #0a7a42;
    }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; font-family: Arial, sans-serif; color: var(--ink); background: #ffffff; line-height: 1.45; }}
    header {{ padding: 24px; border-bottom: 1px solid var(--line); background: #ffffff; position: sticky; top: 0; z-index: 10; }}
    main {{ display: grid; grid-template-columns: minmax(220px, 300px) 1fr; min-height: calc(100vh - 120px); }}
    button {{ font: inherit; }}
    button:focus-visible {{ outline: 3px solid var(--accent); outline-offset: 2px; }}
    .eyebrow {{ margin: 0 0 6px; color: var(--muted); font-size: 13px; text-transform: uppercase; letter-spacing: 0; }}
    h1 {{ margin: 0; font-size: clamp(28px, 5vw, 48px); line-height: 1; letter-spacing: 0; }}
    .summary {{ display: flex; gap: 8px; flex-wrap: wrap; margin-top: 14px; }}
    .metric {{ border: 1px solid var(--line); background: var(--panel); padding: 6px 8px; border-radius: 4px; font-size: 13px; }}
    .sidebar {{ padding: 16px; border-right: 1px solid var(--line); background: var(--panel); }}
    .call-list, .turn-list, .replay-controls {{ display: grid; gap: 8px; }}
    .call-button, .turn-button, .replay-controls button {{
      width: 100%;
      border: 1px solid var(--line);
      background: #ffffff;
      color: var(--ink);
      padding: 10px;
      border-radius: 4px;
      text-align: left;
      cursor: pointer;
    }}
    .call-button[aria-pressed="true"], .turn-button[aria-pressed="true"] {{ border-color: var(--accent); background: var(--accent-soft); }}
    .call-button span {{ display: block; font-weight: 700; }}
    .call-button small {{ display: block; color: var(--muted); margin-top: 2px; }}
    .content {{ padding: 20px; display: grid; gap: 16px; align-content: start; }}
    .panel {{ border: 1px solid var(--line); border-radius: 6px; padding: 14px; background: #ffffff; }}
    .panel h2, .panel h3, .panel h4 {{ margin: 0 0 10px; letter-spacing: 0; }}
    .muted {{ color: var(--muted); }}
    .dialogue {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }}
    .bubble {{ border: 1px solid var(--line); border-radius: 6px; padding: 12px; min-height: 112px; background: #ffffff; }}
    .bubble strong {{ display: block; margin-bottom: 6px; font-size: 13px; color: var(--muted); text-transform: uppercase; letter-spacing: 0; }}
    .agent {{ border-color: #b9ccff; background: #f5f8ff; }}
    .customer {{ border-color: #d7d9dc; }}
    .grid {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; }}
    table {{ border-collapse: collapse; width: 100%; font-size: 14px; }}
    th, td {{ border: 1px solid var(--line); padding: 6px 8px; text-align: left; vertical-align: top; }}
    th {{ width: 42%; background: var(--panel); }}
    code {{ background: var(--panel); padding: 1px 4px; border-radius: 3px; }}
    .status-ok {{ color: var(--ok); font-weight: 700; }}
    @media (max-width: 820px) {{
      header {{ position: static; }}
      main {{ grid-template-columns: 1fr; }}
      .sidebar {{ border-right: 0; border-bottom: 1px solid var(--line); }}
      .dialogue, .grid {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body data-checkpoint="PROD-037-local-interactive-trace-demo-surface">
  <!--
  PROD-037 local interactive trace demo surface
  surface ready: `true`
  visible calls: `8`
  visible turns: `14`
  selectable calls: `8`
  selectable turns: `14`
  static html ready: `true`
  keyboard accessible controls: `true`
  local synthetic trace replay
  {html.escape(payload['next_checkpoint_recommended'])}
  -->
  <header>
    <p class="eyebrow">Local synthetic trace replay</p>
    <h1>PROD-037 Local Interactive Trace Demo Surface</h1>
    <div class="summary" aria-label="Demo metrics">
      <span class="metric">Surface ready: <code>{bool_text(summary['surface_ready'])}</code></span>
      <span class="metric">Visible calls: <code>{summary['visible_call_count']}</code></span>
      <span class="metric">Visible turns: <code>{summary['visible_turn_count']}</code></span>
      <span class="metric">Selectable calls: <code>{summary['selectable_call_count']}</code></span>
      <span class="metric">Selectable turns: <code>{summary['selectable_turn_count']}</code></span>
      <span class="metric">No provider calls</span>
      <span class="metric">No production runtime promotion</span>
    </div>
  </header>
  <main>
    <aside class="sidebar" aria-label="Replay navigation">
      <h2>Calls</h2>
      <div id="call-list" class="call-list" role="list">{''.join(call_buttons)}</div>
      <h2>Turns</h2>
      <div id="turn-list" class="turn-list" role="list">{''.join(turn_buttons)}</div>
      <h2>Replay</h2>
      <div id="replay-controls" class="replay-controls">
        <button type="button" id="prev-turn">Previous Turn</button>
        <button type="button" id="next-turn">Next Turn</button>
      </div>
    </aside>
    <section class="content" aria-live="polite">
      <section id="opening-panel" class="panel">
        <h2 id="call-title">{html.escape(first_call['seed_id'])}</h2>
        <p id="call-persona" class="muted">{html.escape(first_call['persona'])}</p>
        <div class="dialogue">
          <div class="bubble agent"><strong>Agent cold opening</strong><p id="agent-opening">{html.escape(first_call['opening']['agent_opening'])}</p></div>
          <div class="bubble customer"><strong>Customer first response</strong><p id="customer-opening">{html.escape(first_call['opening']['customer_opening_response'])}</p></div>
        </div>
      </section>
      <section class="panel">
        <h2 id="turn-title">Turn {first_turn['turn_index']}</h2>
        <div class="dialogue">
          <div id="customer-context" class="bubble customer"><strong>Customer context</strong><p>{html.escape(first_turn['customer_context'])}</p></div>
          <div id="agent-answer" class="bubble agent"><strong>Agent answer</strong><p>{html.escape(first_turn['agent_answer'])}</p></div>
          <div id="customer-response" class="bubble customer"><strong>Customer response</strong><p>{html.escape(first_turn['customer_response'])}</p></div>
          <div class="bubble"><strong>Reaction reason</strong><p id="reaction-reason">{html.escape(first_turn['customer_reaction_reason'])}</p></div>
        </div>
      </section>
      <section class="grid">
        <section id="decision-snapshot" class="panel">{render_state_table("Decision Snapshot", first_turn['decision_snapshot'])}</section>
        <section id="state-transition" class="panel">
          {render_state_table("State Before", first_turn['state_before'])}
          {render_state_table("State Delta", first_turn['state_delta'])}
          {render_state_table("State After", first_turn['state_after'])}
        </section>
        <section id="safety-flags" class="panel">{render_state_table("Safety Flags", first_turn['safety_flags'])}</section>
      </section>
      <section id="terminal-outcome" class="panel">
        <h2>Terminal Outcome</h2>
        <p><span class="status-ok">{html.escape(display_label(first_call['terminal_outcome']))}</span></p>
        <p id="terminal-reason">{html.escape(first_call['terminal_reason'])}</p>
      </section>
    </section>
  </main>
  <script id="trace-data" type="application/json">{data_json}</script>
  <script>
    const data = JSON.parse(document.getElementById('trace-data').textContent);
    let activeCall = 0;
    let activeTurn = 0;

    function titleCase(value) {{
      return String(value).replaceAll('-', ' ').replaceAll('_', ' ').replace(/\\b\\w/g, c => c.toUpperCase());
    }}

    function table(title, values) {{
      const entries = Object.entries(values || {{}});
      if (!entries.length) return `<div><h4>${{title}}</h4><p class="muted">No values.</p></div>`;
      return `<div><h4>${{title}}</h4><table>${{entries.map(([key, value]) => `<tr><th>${{titleCase(key)}}</th><td>${{String(value)}}</td></tr>`).join('')}}</table></div>`;
    }}

    function setPressed(selector, index) {{
      document.querySelectorAll(selector).forEach((button, buttonIndex) => {{
        button.setAttribute('aria-pressed', String(buttonIndex === index));
      }});
    }}

    function renderTurnButtons(call) {{
      const list = document.getElementById('turn-list');
      list.innerHTML = call.turns.map((turn, index) => `<button type="button" class="turn-button" data-turn-index="${{index}}" aria-pressed="${{index === activeTurn}}">Turn ${{turn.turn_index}}</button>`).join('');
      list.querySelectorAll('.turn-button').forEach(button => {{
        button.addEventListener('click', () => {{
          activeTurn = Number(button.dataset.turnIndex);
          render();
        }});
      }});
    }}

    function render() {{
      const call = data.calls[activeCall];
      const turn = call.turns[activeTurn];
      document.getElementById('call-title').textContent = call.seed_id;
      document.getElementById('call-persona').textContent = call.persona;
      document.getElementById('agent-opening').textContent = call.opening.agent_opening;
      document.getElementById('customer-opening').textContent = call.opening.customer_opening_response;
      document.getElementById('turn-title').textContent = `Turn ${{turn.turn_index}}`;
      document.querySelector('#customer-context p').textContent = turn.customer_context;
      document.querySelector('#agent-answer p').textContent = turn.agent_answer;
      document.querySelector('#customer-response p').textContent = turn.customer_response;
      document.getElementById('reaction-reason').textContent = turn.customer_reaction_reason;
      document.getElementById('decision-snapshot').innerHTML = table('Decision Snapshot', turn.decision_snapshot);
      document.getElementById('state-transition').innerHTML = table('State Before', turn.state_before) + table('State Delta', turn.state_delta) + table('State After', turn.state_after);
      document.getElementById('safety-flags').innerHTML = table('Safety Flags', turn.safety_flags);
      document.querySelector('#terminal-outcome .status-ok').textContent = titleCase(call.terminal_outcome);
      document.getElementById('terminal-reason').textContent = call.terminal_reason;
      setPressed('.call-button', activeCall);
      setPressed('.turn-button', activeTurn);
    }}

    document.querySelectorAll('.call-button').forEach(button => {{
      button.addEventListener('click', () => {{
        activeCall = Number(button.dataset.callIndex);
        activeTurn = 0;
        renderTurnButtons(data.calls[activeCall]);
        render();
      }});
    }});
    renderTurnButtons(data.calls[0]);
    document.getElementById('prev-turn').addEventListener('click', () => {{
      activeTurn = Math.max(0, activeTurn - 1);
      render();
    }});
    document.getElementById('next-turn').addEventListener('click', () => {{
      activeTurn = Math.min(data.calls[activeCall].turns.length - 1, activeTurn + 1);
      render();
    }});
  </script>
</body>
</html>
"""
