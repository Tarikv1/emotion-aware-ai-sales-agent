#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-082-english-guided-option-selection-review"
CHECKPOINT_NAME = "English Guided Option Selection Review"
SOURCE_CHECKPOINT_ID = "PROD-081-english-unknown-runtime-signal-subtype-inventory"
NEXT_CHECKPOINT_ID = "PROD-083-english-guided-option-selection-review-import"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
CASE_FILE = ROOT / "research" / "experiments" / "cases" / "prod-082-english-guided-option-selection-review.json"
SOURCE_DIR = ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID
SOURCE_VALIDATOR = ROOT / "scripts" / "validate_prod_081_english_unknown_runtime_signal_subtype_inventory.py"
REVIEW_HTML = OUT_DIR / "prod_082_review.html"

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

REVIEW_OPTIONS = [
    "keep_deferred",
    "approve_for_narrow_policy_probe_with_guardrails",
    "needs_rewrite_before_probe",
]

GUARDRAILS = [
    "two real options",
    "fair presentation",
    "neither",
    "not now",
    "explain the difference",
    "no fake urgency",
    "no pretend agreement",
    "no payment collection",
    "no contract signing",
]

EXAMPLES = [
    {
        "example_id": "guided-option-binary-choice",
        "title": "Two-option choice",
        "customer_turn": "So do I choose the $29 option or the $59 option?",
        "current_runtime_route": "unknown-runtime-signal",
        "review_target": "guided_option_selection_candidate",
        "proposed_response": "There are two fair paths: $29 for the basics, or $59 for more included. Which feels closer to what you'd actually use? Neither is fine too.",
        "review_question": "Does this let the customer choose without making one option feel mandatory?",
        "risk": "The agent could sound like it is steering toward a plan while pretending the customer created the idea.",
    },
    {
        "example_id": "guided-option-fit-unclear",
        "title": "Fit is unclear",
        "customer_turn": "I can see both paths, I am just not sure which one fits me.",
        "current_runtime_route": "unknown-runtime-signal",
        "review_target": "guided_option_selection_candidate",
        "proposed_response": "Start with use, not pressure: $29 if basics are enough, $59 if you want more included. Which side fits better, or should we pause?",
        "review_question": "Is this low-pressure enough, or does it still push the customer toward choosing today?",
        "risk": "A choice frame can collapse uncertainty into a sale attempt too early.",
    },
    {
        "example_id": "guided-option-recommendation-request",
        "title": "Recommendation request",
        "customer_turn": "Which route would you suggest for someone like me?",
        "current_runtime_route": "unknown-runtime-signal",
        "review_target": "guided_option_selection_candidate",
        "proposed_response": "I shouldn't choose for you. I can make the tradeoff clear: $29 is the lighter start, $59 has more included. Which sounds closer?",
        "review_question": "Should the agent refuse to choose for the customer before offering the two-option frame?",
        "risk": "Direct recommendation language can become advice or authority pressure.",
    },
    {
        "example_id": "guided-option-explain-difference",
        "title": "Difference first",
        "customer_turn": "What is the real difference between the $29 option and the $59 option?",
        "current_runtime_route": "unknown-runtime-signal",
        "review_target": "guided_option_selection_candidate",
        "proposed_response": "I can explain the difference first. $29 is the lower starting point; $59 includes more. No payment details needed.",
        "review_question": "Is this an acceptable bridge when the customer wants explanation before choosing?",
        "risk": "The runtime must not invent exact feature differences beyond approved product facts.",
    },
    {
        "example_id": "guided-option-not-now",
        "title": "Not now",
        "customer_turn": "Can I choose later instead of deciding on this call?",
        "current_runtime_route": "unknown-runtime-signal",
        "review_target": "guided_option_selection_candidate",
        "proposed_response": "Yes. Not now is a valid answer. I can leave both options open and send the $29/$59 difference in writing.",
        "review_question": "Does this preserve autonomy clearly enough?",
        "risk": "The agent must not treat deferral as hidden consent to continue selling.",
    },
    {
        "example_id": "guided-option-neither",
        "title": "Neither option",
        "customer_turn": "I'm not sure either is right.",
        "current_runtime_route": "unknown-runtime-signal",
        "review_target": "guided_option_selection_candidate",
        "proposed_response": "Then neither may be the right answer today. We can pause, or just compare what each option includes.",
        "review_question": "Should this be the default fallback when neither option feels right?",
        "risk": "A guided option tactic must keep a real non-sale path available.",
    },
    {
        "example_id": "guided-option-payment-boundary",
        "title": "Payment boundary",
        "customer_turn": "If I pick one, can I pay now?",
        "current_runtime_route": "unknown-runtime-signal",
        "review_target": "payment_boundary_control",
        "proposed_response": "No payment details needed. This review is only about whether either option is worth considering.",
        "review_question": "Should payment stay blocked even when a customer chooses an option?",
        "risk": "Option selection must not become checkout, card collection, or contract signing.",
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
        timeout=300,
        check=False,
    )
    return {
        "command": f"python {rel(SOURCE_VALIDATOR)}",
        "returncode": completed.returncode,
        "stdout_tail": completed.stdout.strip().splitlines()[-8:],
        "stderr_tail": completed.stderr.strip().splitlines()[-8:],
        "passed": completed.returncode == 0,
    }


def load_source() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    source_result = read_json(SOURCE_DIR / "result.json")
    source_decision = read_json(SOURCE_DIR / "slice_decision.json")
    source_inventory = read_json(SOURCE_DIR / "unknown_runtime_signal_subtype_inventory.json")
    if source_result["validation"]["passed"] is not True:
        raise RuntimeError("PROD-081 must pass before PROD-082.")
    if source_result["summary"]["recommended_next_checkpoint"] != CHECKPOINT_ID:
        raise RuntimeError("PROD-081 must recommend PROD-082.")
    if source_decision["selected_next_subtype"] != "guided_option_selection_candidate":
        raise RuntimeError("PROD-081 must select guided_option_selection_candidate.")
    return source_result, source_decision, source_inventory


def build_case_file() -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "scope": "english_guided_option_selection_review_only",
        "review_item": "guided_option_selection_candidate",
        "requires_human_review_before_next_checkpoint": True,
        "review_html_created": True,
        "review_html_path": rel(REVIEW_HTML),
        "runtime_change_requested": False,
        "response_text_change_requested": False,
        "classifier_change_requested": False,
        "retrieval_change_requested": False,
        "recommended_next_checkpoint": NEXT_CHECKPOINT_ID,
    }


def build_review_packet() -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "review_item": "guided_option_selection_candidate",
        "review_options": REVIEW_OPTIONS,
        "guardrails": GUARDRAILS,
        "recommended_default": "keep_deferred_until_review_import",
        "question": "Should guided option selection become eligible for a narrow English policy probe with these guardrails, or stay deferred/rewrite first?",
        "example_context": "Example product only: a $29 subscription and a $59 subscription. These examples are review candidates, not approved runtime copy.",
        "examples": EXAMPLES,
        "boundaries": {
            "runtime_patch_allowed": False,
            "response_text_change_allowed": False,
            "classifier_change_allowed": False,
            "retrieval_allowed": False,
            "payment_collection_allowed": False,
            "contract_signing_allowed": False,
            "production_runtime_promotion_allowed": False,
        },
    }


def build_review_state_template(packet: dict[str, Any]) -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "review_status": "pending_tarik_review",
        "review_item": packet["review_item"],
        "reviewer": "",
        "review_date": "",
        "overall_decision": "",
        "overall_notes": "",
        "example_decisions": {
            item["example_id"]: {"decision": "", "notes": ""}
            for item in packet["examples"]
        },
        "valid_decisions": REVIEW_OPTIONS,
        "exported_from": rel(REVIEW_HTML),
    }


def build_evidence_summary(source_result: dict[str, Any], source_decision: dict[str, Any], source_validator: dict[str, Any]) -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "source_validation": source_result["validation"],
        "source_summary": {
            "selected_next_subtype": source_result["summary"]["selected_next_subtype"],
            "recommended_next_checkpoint_requires_human_review": source_result["summary"]["recommended_next_checkpoint_requires_human_review"],
            "recommended_next_checkpoint": source_result["summary"]["recommended_next_checkpoint"],
        },
        "source_decision": {
            "decision": source_decision["decision"],
            "required_guardrails": source_decision["required_guardrails"],
            "runtime_patch_allowed": source_decision["runtime_patch_allowed"],
        },
        "source_validator_run": source_validator,
    }


def summarize(packet: dict[str, Any], source_validator: dict[str, Any]) -> dict[str, Any]:
    return {
        "review_packet_only": True,
        "source_validator_passed": source_validator["passed"],
        "selected_review_item": packet["review_item"],
        "review_example_count": len(packet["examples"]),
        "review_options": packet["review_options"],
        "requires_human_review_before_next_checkpoint": True,
        "review_html_created": True,
        "review_html_path": rel(REVIEW_HTML),
        "recommended_next_checkpoint": NEXT_CHECKPOINT_ID,
        **BOUNDARY_FLAGS,
    }


def render_report(summary: dict[str, Any], packet: dict[str, Any]) -> str:
    lines = [
        "# PROD-082 English Guided Option Selection Review",
        "",
        "`PROD-082` creates the human review packet for the English `guided_option_selection_candidate` subtype selected by `PROD-081`.",
        "",
        "This checkpoint does not patch runtime behavior, response text, classifier reachability, or retrieval.",
        "",
        "## Summary",
        "",
        f"- Review packet only: `{str(summary['review_packet_only']).lower()}`",
        f"- Selected review item: `{summary['selected_review_item']}`",
        f"- Review example count: `{summary['review_example_count']}`",
        f"- Requires human review before next checkpoint: `{str(summary['requires_human_review_before_next_checkpoint']).lower()}`",
        f"- Review HTML created: `{str(summary['review_html_created']).lower()}`",
        f"- Review HTML path: `{summary['review_html_path']}`",
        f"- Recommended next checkpoint: `{summary['recommended_next_checkpoint']}`",
        "- Runtime behavior changed: `false`",
        "- Response text behavior changed: `false`",
        "- Classifier behavior changed: `false`",
        "- Retrieval enabled: `false`",
        "- Production runtime promotion allowed: `false`",
        "",
        "## Guardrails",
        "",
    ]
    for guardrail in packet["guardrails"]:
        lines.append(f"- {guardrail}")
    lines.extend(["", "## Review Options", ""])
    for option in packet["review_options"]:
        lines.append(f"- `{option}`")
    lines.extend(["", "## Examples", ""])
    for item in packet["examples"]:
        lines.extend(
            [
                f"### {item['title']}",
                "",
                f"- Customer turn: {item['customer_turn']}",
                f"- Current runtime route: `{item['current_runtime_route']}`",
                f"- Review target: `{item['review_target']}`",
                f"- Risk: {item['risk']}",
                "",
                "```text",
                item["proposed_response"],
                "```",
                "",
            ]
        )
    lines.extend(
        [
            "## Boundary",
            "",
            "- Runtime behavior changed: `false`",
            "- Response text behavior changed: `false`",
            "- Classifier behavior changed: `false`",
            "- Retrieval enabled: `false`",
            "- Provider calls made: `false`",
            "- LLM used: `false`",
            "- LLM judging used: `false`",
            "- Private data read: `false`",
            "- Voice playback unblocked: `false`",
            "- Public demo polish unblocked: `false`",
            "- Real customer use unblocked: `false`",
            "- Payment collection allowed: `false`",
            "- Contract signing allowed: `false`",
            "- Production runtime promotion allowed: `false`",
            "- German exact-phrase promotion allowed: `false`",
            "- German naturalness claimed: `false`",
            "- Legal compliance claimed: `false`",
            "",
        ]
    )
    return "\n".join(lines)


def render_review_html(packet: dict[str, Any], template: dict[str, Any], summary: dict[str, Any]) -> str:
    packet_json = json.dumps(packet, ensure_ascii=False)
    template_json = json.dumps(template, ensure_ascii=False)
    example_cards = "\n".join(render_example_card(index + 1, item) for index, item in enumerate(packet["examples"]))
    guardrails = "\n".join(f"<li>{html.escape(item)}</li>" for item in packet["guardrails"])
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>PROD-082 Guided Option Selection Review</title>
  <style>
    :root {{
      --ink:#101417;
      --muted:#52616a;
      --paper:#f2efe8;
      --panel:#fffdf6;
      --line:#c9c1b3;
      --accent:#1e5c63;
      --accent-2:#9a5a22;
      --danger:#8a382f;
      --soft:#e5ded1;
      --focus:#f8d16c;
    }}
    * {{ box-sizing:border-box; }}
    body {{
      margin:0;
      color:var(--ink);
      background:var(--paper);
      font-family:Cambria, Georgia, 'Times New Roman', serif;
    }}
    header {{
      padding:28px clamp(18px,4vw,54px) 20px;
      border-bottom:1px solid var(--line);
      background:var(--panel);
    }}
    main {{
      max-width:1220px;
      margin:0 auto;
      padding:18px clamp(16px,3vw,32px) 44px;
    }}
    h1 {{ margin:0 0 8px; font-size:clamp(30px,4vw,48px); line-height:1.06; letter-spacing:0; }}
    h2 {{ margin:0 0 10px; font-size:23px; letter-spacing:0; }}
    h3 {{ margin:0 0 8px; font-size:18px; letter-spacing:0; }}
    p {{ line-height:1.48; }}
    .subhead {{ max-width:920px; color:var(--muted); font-size:18px; }}
    .grid {{
      display:grid;
      grid-template-columns:minmax(0,1fr) 330px;
      gap:16px;
      align-items:start;
    }}
    .panel, .toolbar, .reviewer, .example-card {{
      background:var(--panel);
      border:1px solid var(--line);
      border-radius:8px;
    }}
    .panel, .reviewer, .toolbar {{ padding:16px; margin:0 0 16px; }}
    .metrics {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(160px,1fr)); gap:10px; }}
    .metric {{ background:var(--soft); border:1px solid var(--line); border-radius:6px; padding:11px; min-height:78px; }}
    .metric span {{ display:block; color:var(--muted); font-size:12px; text-transform:uppercase; }}
    .metric strong {{ display:block; margin-top:6px; font-size:18px; overflow-wrap:anywhere; }}
    .guardrail-list {{ margin:8px 0 0; padding-left:18px; line-height:1.5; }}
    .sidebar {{ position:sticky; top:12px; }}
    .toolbar {{ display:flex; gap:8px; align-items:center; flex-wrap:wrap; }}
    button, .file-label, select {{
      border:1px solid var(--line);
      border-radius:6px;
      background:#fff;
      color:var(--ink);
      padding:9px 11px;
      font:inherit;
      cursor:pointer;
    }}
    button.primary {{ background:var(--accent); color:white; border-color:var(--accent); }}
    button.warn {{ background:var(--danger); color:white; border-color:var(--danger); }}
    button:focus-visible, input:focus-visible, textarea:focus-visible, select:focus-visible {{
      outline:3px solid var(--focus);
      outline-offset:2px;
    }}
    .reviewer-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(190px,1fr)); gap:12px; }}
    input[type="text"], input[type="date"], textarea {{
      width:100%;
      margin-top:6px;
      padding:9px;
      border:1px solid var(--line);
      border-radius:6px;
      font:inherit;
      background:#fff;
    }}
    textarea {{ min-height:76px; resize:vertical; }}
    .examples {{ display:grid; grid-template-columns:1fr; gap:14px; }}
    .example-card {{ padding:17px; }}
    .card-top {{ display:flex; justify-content:space-between; gap:12px; flex-wrap:wrap; color:var(--muted); margin-bottom:8px; }}
    .tag {{ border:1px solid var(--line); border-radius:999px; padding:4px 9px; color:var(--accent); background:#fff; }}
    dl {{ display:grid; grid-template-columns:minmax(118px,178px) 1fr; gap:8px 12px; }}
    dt {{ color:var(--muted); font-size:12px; text-transform:uppercase; }}
    dd {{ margin:0; }}
    blockquote {{ margin:10px 0; padding:12px 14px; border-left:4px solid var(--accent); background:#f8f4ec; line-height:1.5; }}
    fieldset {{ border:1px solid var(--line); border-radius:6px; margin:14px 0; padding:10px; }}
    fieldset label {{ display:block; margin:7px 0; }}
    .blocked {{ color:var(--danger); font-weight:700; }}
    .note {{ color:var(--muted); font-size:14px; }}
    @media (max-width:900px) {{
      .grid {{ grid-template-columns:1fr; }}
      .sidebar {{ position:static; }}
      dl {{ grid-template-columns:1fr; }}
    }}
    @media print {{
      .toolbar, .reviewer, fieldset, .notes {{ display:none; }}
      body {{ background:white; }}
      .grid {{ display:block; }}
      .example-card {{ break-inside:avoid; margin-bottom:12px; }}
      .sidebar {{ position:static; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>PROD-082 Guided Option Selection Review</h1>
    <p class="subhead">Review whether the agent may place the $29 and $59 options in front of the customer and let them choose, while preserving neither, not now, and explain the difference paths.</p>
  </header>
  <main>
    <section class="panel">
      <div class="metrics">
        <div class="metric"><span>Review item</span><strong>guided option selection</strong></div>
        <div class="metric"><span>Runtime patch</span><strong class="blocked">blocked</strong></div>
        <div class="metric"><span>Examples</span><strong>{summary['review_example_count']}</strong></div>
        <div class="metric"><span>Next</span><strong>review import</strong></div>
      </div>
    </section>
    <div class="grid">
      <section>
        <section class="reviewer">
          <h2>Decision</h2>
          <p class="note">This is not approval for runtime behavior. Approval here only allows a later narrow policy probe with the accepted guardrails.</p>
          <div class="reviewer-grid">
            <label>Name or initials<input id="reviewerName" type="text"></label>
            <label>Date<input id="reviewDate" type="date"></label>
            <label>Overall decision
              <select id="overallDecision">
                <option value="">Select</option>
                <option value="keep_deferred">Keep deferred</option>
                <option value="approve_for_narrow_policy_probe_with_guardrails">Approve for narrow policy probe</option>
                <option value="needs_rewrite_before_probe">Needs rewrite</option>
              </select>
            </label>
          </div>
          <label>Overall notes<textarea id="overallNotes"></textarea></label>
        </section>
        <section class="toolbar">
          <button class="primary" onclick="setAll('approve_for_narrow_policy_probe_with_guardrails')">Approve for narrow policy probe</button>
          <button onclick="setAll('keep_deferred')">Keep deferred</button>
          <button class="warn" onclick="setAll('needs_rewrite_before_probe')">Needs rewrite</button>
          <button onclick="saveProgress()">Save in browser</button>
          <button onclick="loadProgress()">Load saved</button>
          <button onclick="exportJson()">Export JSON</button>
          <label class="file-label">Import JSON<input id="jsonImportFile" type="file" accept="application/json" onchange="importJsonFile(event)" hidden></label>
          <button onclick="clearEntries()">Clear</button>
        </section>
        <section class="examples">
          {example_cards}
        </section>
      </section>
      <aside class="sidebar">
        <section class="panel">
          <h2>Guardrails</h2>
          <ul class="guardrail-list">
            {guardrails}
          </ul>
        </section>
        <section class="panel">
          <h2>Blocked</h2>
          <p>Production runtime promotion allowed: false.</p>
          <p>No payment collection, contract signing, provider call, retrieval default, private data, voice playback, public demo, real customer use, or German wording promotion is approved here.</p>
        </section>
      </aside>
    </div>
  </main>
  <script>
    const reviewPayload = {packet_json};
    const reviewTemplate = {template_json};
    const storageKey = 'prod082GuidedOptionSelectionReview';

    function decisionName(id) {{ return id + '-decision'; }}
    function notesSelector(id) {{ return '[data-notes-for="' + id + '"]'; }}
    function setAll(value) {{
      document.getElementById('overallDecision').value = value;
      reviewPayload.examples.forEach((item) => {{
        const radio = document.querySelector('input[name="' + decisionName(item.example_id) + '"][value="' + value + '"]');
        if (radio) radio.checked = true;
      }});
      saveProgress();
    }}
    function collectState() {{
      const state = JSON.parse(JSON.stringify(reviewTemplate));
      state.reviewer = document.getElementById('reviewerName').value;
      state.review_date = document.getElementById('reviewDate').value;
      state.overall_decision = document.getElementById('overallDecision').value;
      state.overall_notes = document.getElementById('overallNotes').value;
      reviewPayload.examples.forEach((item) => {{
        const checked = document.querySelector('input[name="' + decisionName(item.example_id) + '"]:checked');
        const notes = document.querySelector(notesSelector(item.example_id));
        state.example_decisions[item.example_id] = {{
          decision: checked ? checked.value : '',
          notes: notes ? notes.value : ''
        }};
      }});
      return state;
    }}
    function applyState(state) {{
      document.getElementById('reviewerName').value = state.reviewer || '';
      document.getElementById('reviewDate').value = state.review_date || '';
      document.getElementById('overallDecision').value = state.overall_decision || '';
      document.getElementById('overallNotes').value = state.overall_notes || '';
      Object.entries(state.example_decisions || {{}}).forEach(([id, value]) => {{
        const radio = document.querySelector('input[name="' + decisionName(id) + '"][value="' + (value.decision || '') + '"]');
        if (radio) radio.checked = true;
        const notes = document.querySelector(notesSelector(id));
        if (notes) notes.value = value.notes || '';
      }});
    }}
    function saveProgress() {{ localStorage.setItem(storageKey, JSON.stringify(collectState())); }}
    function loadProgress() {{
      const raw = localStorage.getItem(storageKey);
      if (raw) applyState(JSON.parse(raw));
    }}
    function clearEntries() {{
      localStorage.removeItem(storageKey);
      applyState(reviewTemplate);
    }}
    function exportJson() {{
      const blob = new Blob([JSON.stringify(collectState(), null, 2)], {{ type: 'application/json' }});
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'prod_082_guided_option_selection_review.json';
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    }}
    function importJsonFile(event) {{
      const file = event.target.files[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = () => {{
        const state = JSON.parse(reader.result);
        applyState(state);
        saveProgress();
      }};
      reader.readAsText(file);
    }}
    document.addEventListener('change', saveProgress);
    document.addEventListener('input', saveProgress);
    loadProgress();
  </script>
</body>
</html>
"""


def render_example_card(index: int, item: dict[str, Any]) -> str:
    choices = "\n".join(
        f'<label><input type="radio" name="{html.escape(item["example_id"])}-decision" value="{html.escape(option)}"> {option.replace("_", " ")}</label>'
        for option in REVIEW_OPTIONS
    )
    return f"""
      <article class="example-card" data-example="{html.escape(item['example_id'])}">
        <div class="card-top">
          <span>Example {index}</span>
          <span class="tag">{html.escape(item['review_target'])}</span>
        </div>
        <h2>{html.escape(item['title'])}</h2>
        <dl>
          <dt>Customer turn</dt><dd>{html.escape(item['customer_turn'])}</dd>
          <dt>Current route</dt><dd>{html.escape(item['current_runtime_route'])}</dd>
          <dt>Review target</dt><dd>{html.escape(item['review_target'])}</dd>
          <dt>Risk</dt><dd>{html.escape(item['risk'])}</dd>
          <dt>Question</dt><dd>{html.escape(item['review_question'])}</dd>
        </dl>
        <blockquote>{html.escape(item['proposed_response'])}</blockquote>
        <fieldset>
          <legend>Decision</legend>
          {choices}
        </fieldset>
        <label class="notes">Notes<textarea data-notes-for="{html.escape(item['example_id'])}"></textarea></label>
      </article>
"""


def main() -> None:
    source_result, source_decision, _source_inventory = load_source()
    source_validator = run_source_validator()
    packet = build_review_packet()
    template = build_review_state_template(packet)
    evidence = build_evidence_summary(source_result, source_decision, source_validator)
    summary = summarize(packet, source_validator)
    result = {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "validation": {
            "passed": source_validator["passed"] and summary["review_html_created"],
            "review_packet_created": summary["review_html_created"],
        },
        "summary": summary,
    }
    write_json(CASE_FILE, build_case_file())
    write_json(OUT_DIR / "guided_option_selection_review_packet.json", packet)
    write_json(OUT_DIR / "review_state_template.json", template)
    write_json(OUT_DIR / "evidence_summary.json", evidence)
    write_text(OUT_DIR / "report.md", render_report(summary, packet))
    write_text(REVIEW_HTML, render_review_html(packet, template, summary))
    write_json(OUT_DIR / "result.json", result)
    print(json.dumps({"checkpoint_id": CHECKPOINT_ID, "validation": result["validation"], "summary": summary}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
