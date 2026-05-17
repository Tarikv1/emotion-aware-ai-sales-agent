#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-075-english-provider-comparison-reachability-review"
CHECKPOINT_NAME = "English Provider-Comparison Reachability Review"
SOURCE_CHECKPOINT_ID = "PROD-074-english-customer-move-classification-slice-inventory"
NEXT_CHECKPOINT_ID = "PROD-076-english-provider-comparison-review-import"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
CASE_FILE = ROOT / "research" / "experiments" / "cases" / "prod-075-english-provider-comparison-reachability-review.json"
SOURCE_DIR = ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID
SOURCE_VALIDATOR = ROOT / "scripts" / "validate_prod_074_english_customer_move_classification_slice_inventory.py"
SOURCE_VALIDATOR_COMMAND = "python scripts\\validate_prod_074_english_customer_move_classification_slice_inventory.py"
REVIEW_HTML = OUT_DIR / "prod_075_review.html"
CURRENT_RESPONSE = "That is fair. We can compare fit and terms without pressure before you decide whether this is worth reviewing."

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
    "keep_blocked",
    "approve_for_narrow_probe_as_written",
    "needs_rewrite_before_probe",
]

EXAMPLES = [
    {
        "example_id": "provider-comparison-current-provider",
        "title": "Current provider comparison",
        "customer_turn": "How is this different from our current provider?",
        "current_runtime_route": "unknown-runtime-signal",
        "proposed_review_route": "provider-comparison",
        "proposed_response": CURRENT_RESPONSE,
        "review_question": "Is this response acceptable if the customer asks for a provider comparison?",
        "risk": "The wording must not claim replacement, superiority, savings, or specific terms without approved evidence.",
    },
    {
        "example_id": "provider-comparison-terms",
        "title": "Terms comparison",
        "customer_turn": "Can you compare your terms with what we already have?",
        "current_runtime_route": "unknown-runtime-signal",
        "proposed_review_route": "provider-comparison",
        "proposed_response": CURRENT_RESPONSE,
        "review_question": "Should the agent use this as a low-pressure bridge or stay blocked until product-specific comparison facts exist?",
        "risk": "Comparing terms can sound factual. The response must keep the comparison to fit and review process, not invented terms.",
    },
    {
        "example_id": "provider-comparison-no-replacement-claim",
        "title": "No replacement claim",
        "customer_turn": "We already have someone handling this.",
        "current_runtime_route": "existing-provider-gap",
        "proposed_review_route": "existing-provider-gap",
        "proposed_response": "I won't claim this replaces your provider. The useful check is whether there is a gap it does not cover.",
        "review_question": "Does provider-comparison need the same no-replacement discipline as this already reachable route?",
        "risk": "A provider-comparison branch must not weaken the existing no-replacement boundary.",
    },
    {
        "example_id": "provider-comparison-protected-boundary",
        "title": "Protected-boundary control",
        "customer_turn": "Can you take payment or sign me up if it is better?",
        "current_runtime_route": "payment-safety-boundary",
        "proposed_review_route": "payment-safety-boundary",
        "proposed_response": "No card or payment details are needed here. I can keep the next step to safe written information only.",
        "review_question": "Should any future provider-comparison probe keep payment and contract language blocked?",
        "risk": "Provider comparison must not become payment collection, contract signing, or production promotion.",
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
        "command": SOURCE_VALIDATOR_COMMAND,
        "returncode": completed.returncode,
        "stdout_tail": completed.stdout.strip().splitlines()[-5:],
        "stderr_tail": completed.stderr.strip().splitlines()[-5:],
        "passed": completed.returncode == 0 and SOURCE_CHECKPOINT_ID in completed.stdout,
    }


def load_source() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    result = read_json(SOURCE_DIR / "result.json")
    decision = read_json(SOURCE_DIR / "slice_inventory_decision.json")
    unreachable = read_json(SOURCE_DIR / "unreachable_response_inventory.json")
    if result["validation"]["passed"] is not True:
        raise SystemExit("PROD-074 must pass before PROD-075.")
    if result["summary"]["selected_next_review_item"] != "provider-comparison":
        raise SystemExit("PROD-074 must select provider-comparison for review.")
    if result["summary"]["recommended_next_checkpoint"] != CHECKPOINT_ID:
        raise SystemExit("PROD-074 must recommend PROD-075.")
    if decision["runtime_patch_allowed"] is not False:
        raise SystemExit("PROD-074 must not allow a runtime patch.")
    if unreachable["items"][0]["requires_human_review_before_reachability"] is not True:
        raise SystemExit("PROD-074 must require review before provider-comparison reachability.")
    return result, decision, unreachable


def build_case_file() -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "scope": "english_provider_comparison_reachability_review_only",
        "review_item": "provider-comparison",
        "runtime_change_requested": False,
        "response_text_change_requested": False,
        "classifier_change_requested": False,
        "retrieval_change_requested": False,
        "requires_human_review_before_next_checkpoint": True,
        "review_html_created": True,
        "review_html_path": rel(REVIEW_HTML),
        "recommended_next_checkpoint": NEXT_CHECKPOINT_ID,
    }


def build_review_packet() -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "review_item": "provider-comparison",
        "current_response": CURRENT_RESPONSE,
        "review_options": REVIEW_OPTIONS,
        "recommended_default": "keep_blocked_until_review_import",
        "question": "Should provider-comparison remain blocked, be rewritten before reachability, or become eligible for a narrow classifier probe as written?",
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


def build_evidence_summary(source_result: dict[str, Any], source_validator: dict[str, Any]) -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "source_validation": source_result["validation"],
        "source_summary": {
            "unreachable_localized_response_types": source_result["summary"]["unreachable_localized_response_types"],
            "selected_next_review_item": source_result["summary"]["selected_next_review_item"],
            "recommended_next_checkpoint_requires_human_review": source_result["summary"]["recommended_next_checkpoint_requires_human_review"],
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
        "# PROD-075 English Provider-Comparison Reachability Review",
        "",
        "`PROD-075` creates the human review packet for the unreachable English `provider-comparison` response.",
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
        "## Review Options",
        "",
    ]
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
                f"- Proposed review route: `{item['proposed_review_route']}`",
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
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>PROD-075 Provider Comparison Review</title>
  <style>
    :root {{
      --ink:#17211f;
      --muted:#5d6b66;
      --paper:#f4f1ea;
      --panel:#fffdf8;
      --line:#cfc7ba;
      --accent:#245b4f;
      --accent-2:#8d5a2b;
      --danger:#8b3d2d;
      --soft:#e8e1d5;
    }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; color:var(--ink); background:var(--paper); font-family:Georgia, 'Times New Roman', serif; }}
    header {{ padding:26px clamp(18px,4vw,48px); border-bottom:1px solid var(--line); background:#fff9ee; }}
    main {{ max-width:1180px; margin:0 auto; padding:22px clamp(16px,3vw,32px) 46px; }}
    h1 {{ margin:0 0 8px; font-size:clamp(28px,4vw,46px); line-height:1.08; letter-spacing:0; }}
    h2 {{ margin:0 0 10px; font-size:24px; letter-spacing:0; }}
    h3 {{ margin:0 0 8px; font-size:19px; letter-spacing:0; }}
    p {{ line-height:1.55; }}
    .summary, .toolbar, .reviewer, .example-card, .decision-strip {{ background:var(--panel); border:1px solid var(--line); border-radius:8px; }}
    .summary, .reviewer, .toolbar, .decision-strip {{ padding:16px; margin:16px 0; }}
    .metrics {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(190px,1fr)); gap:10px; }}
    .metric {{ background:var(--soft); border:1px solid var(--line); border-radius:6px; padding:12px; min-height:84px; }}
    .metric span {{ display:block; color:var(--muted); font-size:13px; text-transform:uppercase; }}
    .metric strong {{ display:block; margin-top:6px; font-size:20px; overflow-wrap:anywhere; }}
    .decision-strip {{ display:grid; grid-template-columns:1fr; gap:10px; border-left:5px solid var(--accent-2); }}
    .toolbar {{ display:flex; gap:8px; align-items:center; flex-wrap:wrap; }}
    button, .file-label {{ border:1px solid var(--line); border-radius:6px; background:#fff; color:var(--ink); padding:10px 12px; font:inherit; cursor:pointer; }}
    button.primary {{ background:var(--accent); color:white; border-color:var(--accent); }}
    button.warn {{ background:var(--danger); color:white; border-color:var(--danger); }}
    .reviewer-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:12px; }}
    input[type="text"], input[type="date"], textarea {{ width:100%; margin-top:6px; padding:10px; border:1px solid var(--line); border-radius:6px; font:inherit; background:#fff; }}
    textarea {{ min-height:74px; resize:vertical; }}
    .examples {{ display:grid; grid-template-columns:1fr; gap:14px; }}
    .example-card {{ padding:18px; }}
    .card-top {{ display:flex; justify-content:space-between; gap:12px; flex-wrap:wrap; color:var(--muted); }}
    .tag {{ border:1px solid var(--line); border-radius:999px; padding:4px 9px; color:var(--accent); background:#fff; }}
    dl {{ display:grid; grid-template-columns:minmax(120px,180px) 1fr; gap:8px 12px; }}
    dt {{ color:var(--muted); font-size:13px; text-transform:uppercase; }}
    dd {{ margin:0; }}
    blockquote {{ margin:10px 0; padding:12px 14px; border-left:4px solid var(--accent); background:#f8f4ec; }}
    fieldset {{ border:1px solid var(--line); border-radius:6px; margin:14px 0; padding:10px; }}
    fieldset label {{ display:inline-block; margin:6px 16px 6px 0; }}
    .blocked {{ color:var(--danger); font-weight:700; }}
    @media print {{ .toolbar, .reviewer, fieldset, .notes {{ display:none; }} body {{ background:white; }} .example-card {{ break-inside:avoid; }} }}
  </style>
</head>
<body>
  <header>
    <h1>PROD-075 Provider Comparison Review</h1>
    <p>Review whether the unreachable English <strong>provider-comparison</strong> response should remain blocked, be rewritten, or become eligible for a later narrow classifier probe.</p>
  </header>
  <main>
    <section class="summary">
      <div class="metrics">
        <div class="metric"><span>Review item</span><strong>provider-comparison</strong></div>
        <div class="metric"><span>Runtime patch</span><strong class="blocked">blocked</strong></div>
        <div class="metric"><span>Examples</span><strong>{summary['review_example_count']}</strong></div>
        <div class="metric"><span>Next step</span><strong>review import</strong></div>
      </div>
    </section>
    <section class="decision-strip">
      <h2>Decision Needed</h2>
      <p>Choose one: keep this branch blocked, approve the current wording for a later narrow probe, or require a rewrite before reachability. Production runtime promotion allowed: false. No payment, contract signing, provider calls, retrieval, private data, voice playback, or real customer use is approved here.</p>
    </section>
    <section class="reviewer">
      <div class="reviewer-grid">
        <label>Name or initials<input id="reviewerName" type="text"></label>
        <label>Date<input id="reviewDate" type="date"></label>
        <label>Overall decision
          <select id="overallDecision">
            <option value="">Select</option>
            <option value="keep_blocked">Keep blocked</option>
            <option value="approve_for_narrow_probe_as_written">Approve for narrow probe as written</option>
            <option value="needs_rewrite_before_probe">Needs rewrite before probe</option>
          </select>
        </label>
      </div>
      <label>Overall notes<textarea id="overallNotes"></textarea></label>
    </section>
    <section class="toolbar">
      <button class="primary" onclick="setAll('approve_for_narrow_probe_as_written')">Approve for narrow probe</button>
      <button onclick="setAll('keep_blocked')">Keep blocked</button>
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
  </main>
  <script>
    const reviewPayload = {packet_json};
    const reviewTemplate = {template_json};
    const storageKey = 'prod075ProviderComparisonReview';

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
      a.download = 'prod_075_provider_comparison_review.json';
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
          <span class="tag">{html.escape(item['proposed_review_route'])}</span>
        </div>
        <h2>{html.escape(item['title'])}</h2>
        <dl>
          <dt>Customer turn</dt><dd>{html.escape(item['customer_turn'])}</dd>
          <dt>Current route</dt><dd>{html.escape(item['current_runtime_route'])}</dd>
          <dt>Review route</dt><dd>{html.escape(item['proposed_review_route'])}</dd>
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
    source_result, _source_decision, _unreachable = load_source()
    source_validator = run_source_validator()
    packet = build_review_packet()
    template = build_review_state_template(packet)
    evidence = build_evidence_summary(source_result, source_validator)
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
    write_json(OUT_DIR / "provider_comparison_review_packet.json", packet)
    write_json(OUT_DIR / "review_state_template.json", template)
    write_json(OUT_DIR / "evidence_summary.json", evidence)
    write_json(OUT_DIR / "result.json", result)
    write_text(OUT_DIR / "report.md", render_report(summary, packet))
    write_text(REVIEW_HTML, render_review_html(packet, template, summary))
    print(json.dumps({"checkpoint_id": CHECKPOINT_ID, "validation": result["validation"], "summary": summary}, indent=2))


if __name__ == "__main__":
    main()
