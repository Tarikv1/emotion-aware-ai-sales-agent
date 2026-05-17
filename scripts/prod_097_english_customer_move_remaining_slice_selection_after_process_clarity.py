#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-097-english-customer-move-remaining-slice-selection-after-process-clarity"
CHECKPOINT_NAME = "English Customer-Move Remaining Slice Selection After Process Clarity"
SOURCE_CHECKPOINT_ID = "PROD-096-english-next-step-process-clarity-post-patch-regression"
NEXT_CHECKPOINT_ID = "PROD-098-english-recommendation-roleplay-review-import"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
SOURCE_DIR = ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID
SOURCE_VALIDATOR = ROOT / "scripts" / "validate_prod_096_english_next_step_process_clarity_post_patch_regression.py"

SELECTED_SLICE = "recommendation_roleplay_boundary"
SELECTED_CASE_ID = "prod-081-recommendation-02"

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

REVIEW_EXAMPLES = [
    {
        "example_id": "prod-097-roleplay-position",
        "customer_turn": "What would you do in my position?",
        "candidate_agent_response": "I would base it on what you will actually use. If [customer pain] is the issue, $59 fits better because it includes [feature A] and [feature B]. If not, start with $29.",
        "review_question": "Is this acceptable, or is using 'I would' too strong for the agent?",
        "risk": "The customer asks for roleplay advice. The agent should guide without taking the decision away.",
    },
    {
        "example_id": "prod-097-roleplay-business",
        "customer_turn": "If this were your business, which plan would you take?",
        "candidate_agent_response": "If I were judging only from what you told me, I would lean $59 for [feature A] and [feature B]. If those do not matter yet, $29 is the cleaner start.",
        "review_question": "Is the roleplay framing okay when the agent ties it to stated needs?",
        "risk": "This is more persuasive than a neutral comparison and may need softer wording.",
    },
    {
        "example_id": "prod-097-direct-recommendation",
        "customer_turn": "Can you just tell me what you recommend?",
        "candidate_agent_response": "Based on [customer pain], I would recommend $59. If budget is the main concern, start with $29 and upgrade later.",
        "review_question": "Should direct recommendation be allowed after customer facts exist?",
        "risk": "Recommendation is useful, but it can become pushy if not grounded in the customer's facts.",
    },
    {
        "example_id": "prod-097-leaning-cheaper",
        "customer_turn": "I am leaning $29, but is $59 smarter?",
        "candidate_agent_response": "I mean, $59 is smarter only if [feature A] and [feature B] would actually save you time. Otherwise $29 is the cleaner start.",
        "review_question": "Does this steer enough without repeating obvious price facts?",
        "risk": "This uses light natural filler and fit-based steering; reject if it feels too scripted or too casual.",
    },
    {
        "example_id": "prod-097-decide-for-me-control",
        "customer_turn": "Can you decide for me?",
        "candidate_agent_response": "I cannot decide for you. I can show what each plan covers and why one may fit your needs better.",
        "review_question": "Is this the right boundary when the customer asks the agent to decide?",
        "risk": "The agent must not take over the customer's decision.",
    },
    {
        "example_id": "prod-097-promise-worth-control",
        "customer_turn": "Can you promise $59 will be worth it?",
        "candidate_agent_response": "I cannot promise that. I can explain what $59 adds and you can decide if that is worth it.",
        "review_question": "Is this enough of a claim boundary?",
        "risk": "The agent must not guarantee value or outcome.",
    },
    {
        "example_id": "prod-097-no-pressure-honest-take",
        "customer_turn": "I do not want sales pressure; just give me your honest take.",
        "candidate_agent_response": "Fair. My honest take is $59 only makes sense if [feature A] and [feature B] solve the problem you described. If not, start with $29.",
        "review_question": "Is 'honest take' acceptable, or should the agent avoid that persona?",
        "risk": "This may feel human, but it can also sound like over-personalized persuasion.",
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
        timeout=360,
        check=False,
    )
    return {
        "command": f"python {rel(SOURCE_VALIDATOR)}",
        "returncode": completed.returncode,
        "stdout_tail": completed.stdout.strip().splitlines()[-8:],
        "stderr_tail": completed.stderr.strip().splitlines()[-8:],
        "passed": completed.returncode == 0,
    }


def load_source() -> dict[str, Any]:
    source_result = read_json(SOURCE_DIR / "result.json")
    if source_result["validation"]["passed"] is not True:
        raise RuntimeError("PROD-096 must pass before PROD-097.")
    if source_result["summary"]["recommended_next_checkpoint"] != CHECKPOINT_ID:
        raise RuntimeError("PROD-096 must recommend PROD-097.")
    return source_result


def build_selection() -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "decision": "select_recommendation_roleplay_review_next",
        "selected_next_slice": SELECTED_SLICE,
        "selected_remaining_case_id": SELECTED_CASE_ID,
        "selected_customer_turn": "What would you do in my position?",
        "why": "After guided option and process clarity are closed, the next concrete remaining subtype is recommendation roleplay. It is persuasion-sensitive, so it needs human review before a probe or runtime patch.",
        "selected_requires_human_review_before_probe": True,
        "review_html_created": True,
        "recommended_next_checkpoint": NEXT_CHECKPOINT_ID,
        "recommended_next_checkpoint_requires_human_review_import": True,
    }


def build_review_packet(selection: dict[str, Any]) -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "review_required": True,
        "review_type": SELECTED_SLICE,
        "selected_remaining_case_id": SELECTED_CASE_ID,
        "what_you_are_reviewing": "Whether the English agent may answer recommendation-roleplay turns by giving a grounded recommendation while preserving customer agency.",
        "decision_needed": "Approve, reject, or edit each example before any narrow policy probe is opened.",
        "selection": selection,
    }


def build_review_examples() -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "review_type": SELECTED_SLICE,
        "example_count": len(REVIEW_EXAMPLES),
        "examples": REVIEW_EXAMPLES,
    }


def build_review_state_template() -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "review_type": SELECTED_SLICE,
        "items": [
            {
                "example_id": item["example_id"],
                "decision": "pending",
                "notes": "",
                "edited_agent_response": item["candidate_agent_response"],
            }
            for item in REVIEW_EXAMPLES
        ],
    }


def render_review_html(packet: dict[str, Any], examples: dict[str, Any], state: dict[str, Any]) -> str:
    cards = []
    for index, item in enumerate(examples["examples"], start=1):
        escaped_id = html.escape(item["example_id"])
        cards.append(
            f"""
      <section class="example" data-example="{escaped_id}">
        <div class="example-head">
          <span>Example {index}</span>
          <code>{escaped_id}</code>
        </div>
        <label>Customer</label>
        <p class="turn">{html.escape(item["customer_turn"])}</p>
        <label>Candidate agent response</label>
        <textarea data-field="edited_agent_response">{html.escape(item["candidate_agent_response"])}</textarea>
        <label>Why this needs review</label>
        <p>{html.escape(item["risk"])}</p>
        <label>Review question</label>
        <p>{html.escape(item["review_question"])}</p>
        <div class="choices">
          <label><input type="radio" name="{escaped_id}" value="approve"> Approve</label>
          <label><input type="radio" name="{escaped_id}" value="needs_edit"> Needs edit</label>
          <label><input type="radio" name="{escaped_id}" value="reject"> Reject</label>
        </div>
        <label>Reviewer notes</label>
        <textarea data-field="notes" placeholder="Write what should change, or why this is acceptable."></textarea>
      </section>
"""
        )
    state_json = html.escape(json.dumps(state, ensure_ascii=False))
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>PROD-097 Recommendation Roleplay Review</title>
  <style>
    :root {{
      color-scheme: light;
      --ink: #15181d;
      --muted: #5b6472;
      --line: #d8dde6;
      --paper: #ffffff;
      --band: #f4f6f8;
      --accent: #1f6feb;
      --danger: #9f1239;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Arial, Helvetica, sans-serif;
      color: var(--ink);
      background: var(--band);
      line-height: 1.45;
    }}
    header {{
      background: var(--paper);
      border-bottom: 1px solid var(--line);
      padding: 24px;
    }}
    main {{
      width: min(1040px, calc(100% - 32px));
      margin: 24px auto 56px;
    }}
    h1 {{
      margin: 0 0 8px;
      font-size: 26px;
      letter-spacing: 0;
    }}
    h2 {{
      font-size: 18px;
      margin: 0 0 10px;
    }}
    p {{ margin: 0 0 12px; }}
    .summary, .example, .actions {{
      background: var(--paper);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 18px;
      margin-bottom: 16px;
    }}
    .summary-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 10px;
      margin-top: 12px;
    }}
    .summary-grid div {{
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 10px;
      background: #fbfcfe;
    }}
    .example-head {{
      display: flex;
      justify-content: space-between;
      gap: 12px;
      align-items: center;
      margin-bottom: 12px;
      color: var(--muted);
      font-size: 14px;
    }}
    code {{
      font-family: Consolas, Monaco, monospace;
      font-size: 12px;
      white-space: normal;
    }}
    label {{
      display: block;
      font-weight: 700;
      margin: 12px 0 6px;
    }}
    .turn {{
      border-left: 3px solid var(--accent);
      padding-left: 10px;
    }}
    textarea {{
      width: 100%;
      min-height: 76px;
      resize: vertical;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 10px;
      font: inherit;
      line-height: 1.4;
    }}
    .choices {{
      display: flex;
      flex-wrap: wrap;
      gap: 14px;
      margin: 10px 0 4px;
    }}
    .choices label {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      font-weight: 400;
      margin: 0;
    }}
    button {{
      border: 1px solid var(--accent);
      background: var(--accent);
      color: white;
      border-radius: 6px;
      padding: 10px 14px;
      font-weight: 700;
      cursor: pointer;
    }}
    button.secondary {{
      background: white;
      color: var(--accent);
    }}
    .warning {{
      color: var(--danger);
      font-weight: 700;
    }}
    pre {{
      white-space: pre-wrap;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 12px;
      background: #f8fafc;
      max-height: 260px;
      overflow: auto;
    }}
  </style>
</head>
<body>
  <header>
    <h1>PROD-097 Recommendation Roleplay Review</h1>
    <p>{html.escape(packet["what_you_are_reviewing"])}</p>
    <p class="warning">Nothing here changes runtime behavior. This is the review gate before any probe.</p>
  </header>
  <main>
    <section class="summary">
      <h2>What You Are Reviewing</h2>
      <p>{html.escape(packet["decision_needed"])}</p>
      <div class="summary-grid">
        <div><strong>Selected slice</strong><br>{html.escape(SELECTED_SLICE)}</div>
        <div><strong>Selected case</strong><br>{html.escape(SELECTED_CASE_ID)}</div>
        <div><strong>Next checkpoint</strong><br>{html.escape(NEXT_CHECKPOINT_ID)}</div>
      </div>
    </section>
    {''.join(cards)}
    <section class="actions">
      <h2>Export Review</h2>
      <p>Use export after choosing approve, needs edit, or reject for each example. Import Review can reload a saved JSON review.</p>
      <button type="button" onclick="exportReview()">Export Review</button>
      <button type="button" class="secondary" onclick="document.getElementById('importBox').focus()">Import Review</button>
      <textarea id="importBox" placeholder="Paste a review JSON here, then click Apply Import."></textarea>
      <button type="button" class="secondary" onclick="applyImport()">Apply Import</button>
      <pre id="output" aria-live="polite"></pre>
    </section>
  </main>
  <script id="initial-state" type="application/json">{state_json}</script>
  <script>
    const checkpointId = "{CHECKPOINT_ID}";
    function collectReview() {{
      const items = [...document.querySelectorAll(".example")].map(card => {{
        const exampleId = card.dataset.example;
        const checked = card.querySelector("input[type=radio]:checked");
        return {{
          example_id: exampleId,
          decision: checked ? checked.value : "pending",
          edited_agent_response: card.querySelector('[data-field="edited_agent_response"]').value,
          notes: card.querySelector('[data-field="notes"]').value
        }};
      }});
      return {{
        checkpoint_id: checkpointId,
        review_type: "{SELECTED_SLICE}",
        reviewed_at_local: new Date().toISOString(),
        items
      }};
    }}
    function exportReview() {{
      document.getElementById("output").textContent = JSON.stringify(collectReview(), null, 2);
    }}
    function applyImport() {{
      const raw = document.getElementById("importBox").value.trim();
      if (!raw) return;
      const payload = JSON.parse(raw);
      for (const item of payload.items || []) {{
        const card = document.querySelector(`[data-example="${{item.example_id}}"]`);
        if (!card) continue;
        const radio = card.querySelector(`input[value="${{item.decision}}"]`);
        if (radio) radio.checked = true;
        card.querySelector('[data-field="edited_agent_response"]').value = item.edited_agent_response || "";
        card.querySelector('[data-field="notes"]').value = item.notes || "";
      }}
      exportReview();
    }}
  </script>
</body>
</html>
"""


def build_evidence(source_result: dict[str, Any], source_validator: dict[str, Any]) -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "source_validation": source_result["validation"],
        "source_summary": source_result["summary"],
        "source_validator_run": source_validator,
    }


def summarize(selection: dict[str, Any], source_validator: dict[str, Any]) -> dict[str, Any]:
    return {
        "selection_only": True,
        "source_validator_passed": source_validator["passed"],
        "selected_next_slice": selection["selected_next_slice"],
        "selected_remaining_case_id": selection["selected_remaining_case_id"],
        "review_html_created": True,
        "requires_human_review_before_next_checkpoint": True,
        "recommended_next_checkpoint": NEXT_CHECKPOINT_ID,
        **BOUNDARY_FLAGS,
    }


def render_report(summary: dict[str, Any], selection: dict[str, Any], examples: dict[str, Any]) -> str:
    lines = [
        "# PROD-097 English Customer-Move Remaining Slice Selection After Process Clarity",
        "",
        "`PROD-097` selects the next remaining English customer-move subtype after process-clarity regression.",
        "",
        "This checkpoint is selection and review-packet creation only. It changes no runtime behavior, response text, classifier reachability, retrieval, provider usage, private-data handling, voice playback, payment handling, contract signing, legal readiness, German wording, or production runtime promotion.",
        "",
        "## Result",
        "",
        f"- Selection only: `{str(summary['selection_only']).lower()}`",
        f"- Selected next slice: `{summary['selected_next_slice']}`",
        f"- Selected remaining case: `{summary['selected_remaining_case_id']}`",
        f"- Requires human review before next checkpoint: `{str(summary['requires_human_review_before_next_checkpoint']).lower()}`",
        f"- Review HTML created: `{str(summary['review_html_created']).lower()}`",
        f"- Recommended next checkpoint: `{summary['recommended_next_checkpoint']}`",
        "",
        "## Review Packet",
        "",
        f"- Example count: `{examples['example_count']}`",
        "- Review HTML: `review.html`",
        "",
        "## Selection Reason",
        "",
        selection["why"],
        "",
        "## Boundary Status",
        "",
    ]
    for key in BOUNDARY_FLAGS:
        lines.append(f"- {key.replace('_', ' ').capitalize()}: `{str(summary[key]).lower()}`")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    source_result = load_source()
    source_validator = run_source_validator()
    selection = build_selection()
    packet = build_review_packet(selection)
    examples = build_review_examples()
    state = build_review_state_template()
    evidence = build_evidence(source_result, source_validator)
    summary = summarize(selection, source_validator)
    result = {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "validation": {
            "passed": source_validator["passed"] and len(REVIEW_EXAMPLES) >= 6,
            "review_packet_created": True,
        },
        "summary": summary,
    }

    write_json(OUT_DIR / "remaining_subtype_selection.json", selection)
    write_json(OUT_DIR / "review_packet.json", packet)
    write_json(OUT_DIR / "review_examples.json", examples)
    write_json(OUT_DIR / "review_state_template.json", state)
    write_text(OUT_DIR / "review.html", render_review_html(packet, examples, state))
    write_json(OUT_DIR / "evidence_summary.json", evidence)
    write_text(OUT_DIR / "report.md", render_report(summary, selection, examples))
    write_json(OUT_DIR / "result.json", result)
    print(json.dumps({"checkpoint_id": CHECKPOINT_ID, "validation": result["validation"], "summary": summary}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
