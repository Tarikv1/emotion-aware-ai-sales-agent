#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-061-english-product-policy-gate-prioritization"
CHECKPOINT_NAME = "English Product-Policy Gate Prioritization"
SOURCE_CHECKPOINT_ID = "PROD-060-runtime-promotion-path-decision"
NEXT_CHECKPOINT_ID = "PROD-062-english-context-sensitive-autonomy-policy-probe"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
CASE_FILE = ROOT / "research" / "experiments" / "cases" / "prod-061-english-product-policy-gate-prioritization.json"
SOURCE_DIR = ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID
SOURCE_VALIDATOR = ROOT / "scripts" / "validate_prod_060_runtime_promotion_path_decision.py"
SOURCE_VALIDATOR_COMMAND = "python scripts\\validate_prod_060_runtime_promotion_path_decision.py"

STILL_BLOCKED = [
    "customer_move_classification_outside_selected_non_refusal_groups",
    "voicemail_action_only_behavior",
    "coverage_knowledge_policy_behavior",
    "context_sensitive_autonomy_behavior",
    "native_german_review",
    "voice_playback_quality",
    "retrieval_default",
    "provider_or_private_data_use",
    "legal_compliance_review",
    "public_demo_use",
    "real_customer_use",
    "payment_collection",
    "contract_signing",
    "production_runtime_promotion",
]

BOUNDARY_FLAGS = {
    "runtime_behavior_changed": False,
    "response_text_behavior_changed": False,
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


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def rel_path(path: Path) -> str:
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


def load_sources() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    source_result = read_json(SOURCE_DIR / "result.json")
    path_decision = read_json(SOURCE_DIR / "path_decision.json")
    path_options = read_json(SOURCE_DIR / "path_options.json")
    evidence_summary = read_json(SOURCE_DIR / "evidence_summary.json")

    if source_result["validation"]["passed"] is not True:
        raise SystemExit("PROD-060 must pass before PROD-061.")
    if source_result["summary"]["selected_path"] != "internal_guarded_english_baseline_only":
        raise SystemExit("PROD-060 must select the internal guarded English baseline before PROD-061.")
    if source_result["summary"]["recommended_next_checkpoint"] != CHECKPOINT_ID:
        raise SystemExit("PROD-060 must recommend PROD-061 before this prioritization.")
    if path_decision["requires_human_review_before_next_checkpoint"] is not True:
        raise SystemExit("PROD-060 must require human review before PROD-061.")
    if set(path_decision["still_blocked"]) != set(STILL_BLOCKED):
        raise SystemExit("PROD-060 still-blocked blocker set changed; review before PROD-061.")
    if path_options["selected_path_id"] != "internal_guarded_english_baseline_only":
        raise SystemExit("PROD-060 path options changed; review before PROD-061.")
    if evidence_summary["source_stable_guard_passed"] is not True:
        raise SystemExit("PROD-060 source guard evidence must pass before PROD-061.")
    return source_result, path_decision, path_options, evidence_summary


def build_case_file() -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "scope": "english_product_policy_prioritization_only",
        "human_review_decision": "accepted_to_proceed",
        "human_review_source": "Tarik accepted the PROD-060 path decision and wants to move forward with the English version for now.",
        "selected_first_gate": "context_sensitive_autonomy_behavior",
        "not_a_runtime_patch": True,
        "runtime_change_requested": False,
        "requires_human_review_before_next_checkpoint": False,
        "non_goals": [
            "runtime behavior change",
            "response text change",
            "classifier change",
            "voicemail action behavior",
            "coverage knowledge-policy behavior",
            "provider call",
            "LLM call",
            "private data read",
            "retrieval default change",
            "voice playback promotion",
            "German exact phrase promotion",
            "legal compliance approval",
            "public demo approval",
            "real customer use",
            "payment collection",
            "contract signing",
            "production runtime promotion",
        ],
    }


def build_gate_options() -> dict[str, Any]:
    ranked_gates = [
        {
            "rank": 1,
            "gate_id": "context_sensitive_autonomy_behavior",
            "label": "Context-sensitive autonomy behavior",
            "status": "selected_for_next_probe_still_blocked",
            "selected_for_next_probe": True,
            "runtime_patch_allowed": False,
            "why": "It is the best first English-only policy probe because it can be tested with synthetic multi-turn examples, does not require regulated product facts, and does not alter call-control or broad classifier reachability.",
            "risk": "Can still become manipulative or over-personalized if autonomy language adapts too aggressively to customer hesitation.",
            "next_action": "Open a targeted policy probe that defines allowed and forbidden autonomy-preserving follow-up patterns before any runtime patch.",
            "review_question": "Should context-sensitive autonomy be the first English product-policy gate to probe while still blocked from runtime promotion?",
        },
        {
            "rank": 2,
            "gate_id": "voicemail_action_only_behavior",
            "label": "Voicemail action-only behavior",
            "status": "deferred_still_blocked",
            "selected_for_next_probe": False,
            "runtime_patch_allowed": False,
            "why": "It is important for English call quality, but it is call-control/action behavior rather than phrase quality, so it should follow a smaller policy probe.",
            "risk": "Could make the runtime take inappropriate same-loop actions after voicemail detection or blur message-taking versus selling behavior.",
            "next_action": "Keep blocked until a call-control-specific checkpoint defines action-only voicemail behavior.",
            "review_question": "Should voicemail behavior remain deferred behind the autonomy probe?",
        },
        {
            "rank": 3,
            "gate_id": "coverage_knowledge_policy_behavior",
            "label": "Coverage knowledge-policy behavior",
            "status": "deferred_still_blocked",
            "selected_for_next_probe": False,
            "runtime_patch_allowed": False,
            "why": "Coverage and policy-knowledge responses risk unsupported regulated advice and need product/legal boundaries before runtime use.",
            "risk": "Could imply insurance coverage, eligibility, or legal/financial advice without a reviewed knowledge policy.",
            "next_action": "Keep blocked until a separate knowledge-policy checkpoint defines allowed facts, uncertainty handling, and escalation.",
            "review_question": "Should coverage knowledge-policy stay behind a separate legal/product-knowledge gate?",
        },
        {
            "rank": 4,
            "gate_id": "customer_move_classification_outside_selected_non_refusal_groups",
            "label": "Customer-move classification outside selected non-refusal groups",
            "status": "deferred_still_blocked",
            "selected_for_next_probe": False,
            "runtime_patch_allowed": False,
            "why": "Broadening customer-move classification has the largest blast radius because it changes reachability across many runtime branches.",
            "risk": "Could route customer turns into newly promoted behavior without enough evidence for each branch.",
            "next_action": "Keep blocked until smaller policy gates provide clearer acceptance criteria for broader classifier reachability.",
            "review_question": "Should broad classifier expansion remain last among the current English product-policy gates?",
        },
    ]
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "ranked_gates": ranked_gates,
        "selected_first_gate_id": "context_sensitive_autonomy_behavior",
        "product_policy_gate_count": len(ranked_gates),
        "all_runtime_patch_allowed": False,
    }


def build_gate_priority(gate_options: dict[str, Any]) -> dict[str, Any]:
    selected = next(item for item in gate_options["ranked_gates"] if item["selected_for_next_probe"])
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "decision": "prioritize_context_sensitive_autonomy_first",
        "selected_first_gate": {
            "gate_id": selected["gate_id"],
            "label": selected["label"],
            "status": selected["status"],
            "next_action": "open_targeted_policy_probe",
            "runtime_patch_allowed": False,
            "still_blocked_until_probe_passes": True,
            "recommended_probe_scope": "synthetic English multi-turn policy examples only",
        },
        "deferred_gates": [
            item["gate_id"] for item in gate_options["ranked_gates"] if not item["selected_for_next_probe"]
        ],
        "still_blocked": STILL_BLOCKED,
        "requires_human_review_before_next_checkpoint": False,
        "recommended_next_checkpoint": NEXT_CHECKPOINT_ID,
    }


def build_evidence_summary(
    source_result: dict[str, Any],
    path_decision: dict[str, Any],
    source_evidence: dict[str, Any],
    source_validator: dict[str, Any],
) -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "source_selected_path": source_result["summary"]["selected_path"],
        "source_allowed_scope": source_result["summary"]["allowed_scope"],
        "source_still_blocked": source_result["summary"]["still_blocked"],
        "source_path_decision": path_decision["decision"],
        "source_stable_guard_passed": source_evidence["source_stable_guard_passed"],
        "source_review_html_path": source_result["summary"]["review_html_path"],
        "english_direction_accepted": True,
        "english_direction_note": "Tarik wants to move forward with the English version for now, while keeping non-English and deployment paths blocked.",
        "source_validator_run": source_validator,
    }


def summarize(
    gate_options: dict[str, Any],
    gate_priority: dict[str, Any],
    source_validator: dict[str, Any],
) -> dict[str, Any]:
    return {
        "prioritization_only": True,
        "human_review_acceptance_recorded": True,
        "source_validator_passed": source_validator["passed"],
        "selected_first_gate": gate_priority["selected_first_gate"]["gate_id"],
        "selected_first_gate_status": gate_priority["selected_first_gate"]["status"],
        "product_policy_gate_count": gate_options["product_policy_gate_count"],
        "still_blocked_count": len(gate_priority["still_blocked"]),
        "still_blocked": gate_priority["still_blocked"],
        "requires_human_review_before_next_checkpoint": False,
        "recommended_next_checkpoint": NEXT_CHECKPOINT_ID,
        **BOUNDARY_FLAGS,
    }


def build_review_examples(gate_options: dict[str, Any], gate_priority: dict[str, Any]) -> list[dict[str, Any]]:
    gates_by_id = {item["gate_id"]: item for item in gate_options["ranked_gates"]}
    return [
        {
            "example_id": "selected-autonomy-probe",
            "category": "selected_gate",
            "title": "Selected first probe: context-sensitive autonomy",
            "gate": gates_by_id["context_sensitive_autonomy_behavior"],
            "example_use": "A hesitant customer says they do not want to decide today; the policy probe should test whether the English response preserves autonomy while still offering a low-pressure next step.",
            "decision_hint": "Accept if this is the best first English-only product-policy probe and still not a runtime patch.",
        },
        {
            "example_id": "defer-voicemail-action",
            "category": "deferred_gate",
            "title": "Deferred: voicemail action-only behavior",
            "gate": gates_by_id["voicemail_action_only_behavior"],
            "example_use": "A voicemail-like turn should not trigger a normal sales continuation until call-control/action policy is reviewed.",
            "decision_hint": "Accept the defer if voicemail requires a separate call-control checkpoint.",
        },
        {
            "example_id": "defer-coverage-knowledge",
            "category": "deferred_gate",
            "title": "Deferred: coverage knowledge-policy behavior",
            "gate": gates_by_id["coverage_knowledge_policy_behavior"],
            "example_use": "A customer asks whether a specific medical/insurance situation is covered; the current English baseline should not invent coverage or advice.",
            "decision_hint": "Accept the defer if coverage needs product/legal/knowledge boundaries before runtime use.",
        },
        {
            "example_id": "defer-broad-classification",
            "category": "deferred_gate",
            "title": "Deferred: broad customer-move classification",
            "gate": gates_by_id["customer_move_classification_outside_selected_non_refusal_groups"],
            "example_use": "A new customer-move type becomes reachable through classifier expansion; this is too broad before smaller policy gates are tested.",
            "decision_hint": "Accept the defer if classifier expansion should wait until narrower gates define acceptance criteria.",
        },
        {
            "example_id": "next-probe-boundary",
            "category": "next_checkpoint",
            "title": "Next checkpoint boundary",
            "gate": {
                "gate_id": NEXT_CHECKPOINT_ID,
                "label": "English context-sensitive autonomy policy probe",
                "status": "recommended_next_checkpoint",
                "why": "The next checkpoint should define allowed and forbidden English autonomy-preserving patterns with synthetic multi-turn examples only.",
                "risk": "If it becomes a runtime patch too early, it can create manipulative or over-personalized behavior.",
                "review_question": "Should PROD-062 remain a policy probe rather than a runtime patch?",
                "runtime_patch_allowed": False,
            },
            "example_use": "Create a review packet for autonomy-preserving English follow-ups; do not change runtime behavior.",
            "decision_hint": "Accept if the next step should gather targeted policy evidence before implementation.",
        },
    ]


def render_review_html(
    gate_priority: dict[str, Any],
    gate_options: dict[str, Any],
    evidence: dict[str, Any],
    summary: dict[str, Any],
    review_examples: list[dict[str, Any]],
) -> str:
    data_json = json.dumps(
        {
            "checkpoint_id": CHECKPOINT_ID,
            "priority": gate_priority,
            "options": gate_options,
            "summary": summary,
            "evidence": evidence,
            "examples": review_examples,
        },
        ensure_ascii=False,
    )
    cards: list[str] = []
    for index, item in enumerate(review_examples, start=1):
        gate = item["gate"]
        cards.append(
            f"""
      <article class="example-card" data-example="{html.escape(item['example_id'])}" data-category="{html.escape(item['category'])}">
        <div class="card-top">
          <span class="eyebrow">Example {index}</span>
          <span class="tag">{html.escape(item['category'].replace('_', ' '))}</span>
        </div>
        <h2>{html.escape(item['title'])}</h2>
        <p class="example-use">{html.escape(item['example_use'])}</p>
        <dl>
          <dt>Gate</dt><dd>{html.escape(gate['gate_id'])}</dd>
          <dt>Status</dt><dd>{html.escape(gate['status'])}</dd>
          <dt>Runtime patch allowed</dt><dd>{str(gate['runtime_patch_allowed']).lower()}</dd>
          <dt>Why</dt><dd>{html.escape(gate['why'])}</dd>
          <dt>Risk</dt><dd>{html.escape(gate['risk'])}</dd>
          <dt>Review question</dt><dd>{html.escape(gate['review_question'])}</dd>
          <dt>Decision hint</dt><dd>{html.escape(item['decision_hint'])}</dd>
        </dl>
        <fieldset>
          <legend>Review decision</legend>
          <label><input type="radio" name="{html.escape(item['example_id'])}-decision" value="accept"> Accept current decision</label>
          <label><input type="radio" name="{html.escape(item['example_id'])}-decision" value="revise"> Request revision</label>
          <label><input type="radio" name="{html.escape(item['example_id'])}-decision" value="defer"> Defer</label>
        </fieldset>
        <label class="notes">Notes<textarea data-notes-for="{html.escape(item['example_id'])}"></textarea></label>
      </article>
            """
        )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>PROD-061 Review</title>
  <style>
    :root {{
      --ink:#151f2a;
      --muted:#5c6670;
      --paper:#f5f2ea;
      --panel:#ffffff;
      --line:#d3cabc;
      --accent:#225f57;
      --danger:#8d4024;
      --soft:#e8e2d6;
    }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; font-family:Georgia, 'Times New Roman', serif; color:var(--ink); background:var(--paper); }}
    header {{ padding:28px clamp(18px,4vw,48px); border-bottom:1px solid var(--line); background:#fffaf0; }}
    main {{ max-width:1120px; margin:0 auto; padding:24px clamp(16px,3vw,32px) 48px; }}
    h1 {{ margin:0 0 10px; font-size:clamp(28px,4vw,48px); line-height:1.05; letter-spacing:0; }}
    h2 {{ margin:8px 0 10px; font-size:24px; letter-spacing:0; }}
    p {{ line-height:1.55; }}
    .summary, .toolbar, .reviewer {{ background:var(--panel); border:1px solid var(--line); border-radius:8px; padding:16px; margin:18px 0; }}
    .metrics {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(190px,1fr)); gap:10px; }}
    .metric {{ background:var(--soft); border:1px solid var(--line); border-radius:6px; padding:12px; }}
    .metric strong {{ display:block; font-size:20px; overflow-wrap:anywhere; }}
    .toolbar {{ display:flex; flex-wrap:wrap; gap:8px; align-items:center; }}
    button, .file-label {{ border:1px solid var(--line); border-radius:6px; background:#fff; color:var(--ink); padding:10px 12px; font:inherit; cursor:pointer; }}
    button.primary {{ background:var(--accent); color:#fff; border-color:var(--accent); }}
    button.warn {{ background:var(--danger); color:#fff; border-color:var(--danger); }}
    .reviewer-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:12px; }}
    input[type="text"], input[type="date"], textarea {{ width:100%; margin-top:6px; padding:10px; border:1px solid var(--line); border-radius:6px; font:inherit; background:#fff; }}
    textarea {{ min-height:72px; resize:vertical; }}
    .example-card {{ background:var(--panel); border:1px solid var(--line); border-radius:8px; padding:18px; margin:16px 0; }}
    .card-top {{ display:flex; justify-content:space-between; gap:12px; flex-wrap:wrap; }}
    .eyebrow {{ color:var(--muted); font-size:14px; text-transform:uppercase; }}
    .tag {{ border:1px solid var(--line); border-radius:999px; padding:4px 9px; color:var(--accent); }}
    .example-use {{ font-weight:700; }}
    dl {{ display:grid; grid-template-columns:minmax(120px,180px) 1fr; gap:8px 12px; }}
    dd {{ margin:0; }}
    dt {{ color:var(--muted); font-size:14px; text-transform:uppercase; }}
    fieldset {{ border:1px solid var(--line); border-radius:6px; margin:14px 0; padding:10px; }}
    fieldset label {{ display:inline-block; margin:6px 14px 6px 0; }}
    @media print {{ .toolbar, .reviewer, fieldset, .notes {{ display:none; }} body {{ background:white; }} .example-card {{ break-inside:avoid; }} }}
  </style>
</head>
<body>
  <header>
    <h1>PROD-061 Review</h1>
    <p>English product-policy gate prioritization. Selected first gate: context_sensitive_autonomy_behavior. Status: selected_for_next_probe_still_blocked. This is not a runtime patch.</p>
  </header>
  <main>
    <section class="summary">
      <div class="metrics">
        <div class="metric"><span>Selected first gate</span><strong>{html.escape(summary['selected_first_gate'])}</strong></div>
        <div class="metric"><span>Status</span><strong>{html.escape(summary['selected_first_gate_status'])}</strong></div>
        <div class="metric"><span>Policy gates</span><strong>{summary['product_policy_gate_count']}</strong></div>
        <div class="metric"><span>Still blocked</span><strong>{summary['still_blocked_count']}</strong></div>
      </div>
      <p>Runtime behavior changed: false. Response text behavior changed: false. Production runtime promotion allowed: false.</p>
    </section>
    <section class="reviewer">
      <div class="reviewer-grid">
        <label>Name or initials<input id="reviewerName" type="text"></label>
        <label>Date<input id="reviewDate" type="date"></label>
      </div>
      <label>Overall notes<textarea id="overallNotes"></textarea></label>
    </section>
    <section class="toolbar">
      <button class="primary" onclick="setAll('accept')">Accept current decision</button>
      <button class="warn" onclick="setAll('revise')">Request revision</button>
      <button onclick="saveProgress()">Save in browser</button>
      <button onclick="loadProgress()">Load saved</button>
      <button onclick="exportJson()">Export JSON</button>
      <label class="file-label">Import JSON<input id="jsonImportFile" type="file" accept="application/json" onchange="importJsonFile(event)" hidden></label>
      <button onclick="clearEntries()">Clear</button>
    </section>
    <section>
      <h2>Review examples</h2>
      {''.join(cards)}
    </section>
  </main>
  <script>
    const reviewPayload = {data_json};
    const storageKey = 'prod061EnglishPolicyGateReview';

    function decisionValue(exampleId) {{
      const selected = document.querySelector(`input[name="${{exampleId}}-decision"]:checked`);
      return selected ? selected.value : '';
    }}

    function collectReview() {{
      const items = reviewPayload.examples.map(example => ({{
        example_id: example.example_id,
        category: example.category,
        decision: decisionValue(example.example_id),
        notes: document.querySelector(`[data-notes-for="${{example.example_id}}"]`).value
      }}));
      return {{
        schema_name: 'prod_061_review_export',
        checkpoint_id: reviewPayload.checkpoint_id,
        reviewer: {{
          name_or_initials: document.getElementById('reviewerName').value,
          date: document.getElementById('reviewDate').value,
          overall_notes: document.getElementById('overallNotes').value
        }},
        items,
        summary: {{
          accept_count: items.filter(item => item.decision === 'accept').length,
          revise_count: items.filter(item => item.decision === 'revise').length,
          defer_count: items.filter(item => item.decision === 'defer').length,
          blank_count: items.filter(item => !item.decision).length
        }},
        source_priority: reviewPayload.priority,
        source_summary: reviewPayload.summary
      }};
    }}

    function setAll(value) {{
      reviewPayload.examples.forEach(example => {{
        const input = document.querySelector(`input[name="${{example.example_id}}-decision"][value="${{value}}"]`);
        if (input) input.checked = true;
      }});
      saveProgress();
    }}

    function saveProgress() {{
      localStorage.setItem(storageKey, JSON.stringify(collectReview()));
    }}

    function applyReviewPayload(payload) {{
      if (!payload) return false;
      const reviewer = payload.reviewer || {{}};
      document.getElementById('reviewerName').value = reviewer.name_or_initials || '';
      document.getElementById('reviewDate').value = reviewer.date || '';
      document.getElementById('overallNotes').value = reviewer.overall_notes || '';
      (payload.items || []).forEach(item => {{
        const input = document.querySelector(`input[name="${{item.example_id}}-decision"][value="${{item.decision}}"]`);
        if (input) input.checked = true;
        const notes = document.querySelector(`[data-notes-for="${{item.example_id}}"]`);
        if (notes) notes.value = item.notes || '';
      }});
      return true;
    }}

    function loadProgress() {{
      applyReviewPayload(JSON.parse(localStorage.getItem(storageKey) || 'null'));
    }}

    function exportJson() {{
      const blob = new Blob([JSON.stringify(collectReview(), null, 2)], {{type:'application/json'}});
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = 'prod-061-review-export.json';
      link.click();
      URL.revokeObjectURL(url);
    }}

    function importJsonFile(event) {{
      const file = event.target.files && event.target.files[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = () => {{
        try {{
          const payload = JSON.parse(String(reader.result || '{{}}'));
          if (!applyReviewPayload(payload)) throw new Error('empty');
          localStorage.setItem(storageKey, JSON.stringify(collectReview()));
        }} catch (error) {{
          alert('JSON import failed.');
        }} finally {{
          event.target.value = '';
        }}
      }};
      reader.readAsText(file);
    }}

    function clearEntries() {{
      document.querySelectorAll('input[type="radio"]').forEach(input => input.checked = false);
      document.querySelectorAll('textarea').forEach(input => input.value = '');
      localStorage.removeItem(storageKey);
    }}

    loadProgress();
  </script>
</body>
</html>
"""


def render_report(gate_priority: dict[str, Any], gate_options: dict[str, Any], evidence: dict[str, Any], summary: dict[str, Any]) -> str:
    lines = [
        "# PROD-061 English Product-Policy Gate Prioritization",
        "",
        "`PROD-061` records the English-only product-policy gate order after Tarik accepted the `PROD-060` path decision.",
        "",
        "This is prioritization only and not a runtime patch.",
        "",
        "## Decision",
        "",
        f"- Decision: `{gate_priority['decision']}`",
        f"- Selected first gate: `{summary['selected_first_gate']}`",
        f"- Selected first gate status: `{summary['selected_first_gate_status']}`",
        f"- Product-policy gate count: `{summary['product_policy_gate_count']}`",
        f"- Still-blocked blocker count: `{summary['still_blocked_count']}`",
        "- Review HTML: not generated; no human review required for this prioritization checkpoint.",
        f"- Recommended next checkpoint: `{summary['recommended_next_checkpoint']}`",
        "- Production runtime promotion allowed: `false`",
        "",
        "## Ranked Gates",
        "",
    ]
    for item in gate_options["ranked_gates"]:
        lines.extend(
            [
                f"### Rank {item['rank']} - {item['gate_id']}",
                "",
                f"- Status: `{item['status']}`",
                f"- Runtime patch allowed: `{str(item['runtime_patch_allowed']).lower()}`",
                f"- Why: {item['why']}",
                f"- Risk: {item['risk']}",
                f"- Next action: {item['next_action']}",
                "",
            ]
        )
    lines.extend(
        [
            "## Source Evidence",
            "",
            f"- Source checkpoint: `{evidence['source_checkpoint_id']}`",
            f"- Source selected path: `{evidence['source_selected_path']}`",
            f"- Source allowed scope: `{evidence['source_allowed_scope']}`",
            f"- Source validator passed: `{str(evidence['source_validator_run']['passed']).lower()}`",
            f"- English direction accepted: `{str(evidence['english_direction_accepted']).lower()}`",
            "",
            "## Still Blocked",
            "",
        ]
    )
    for blocker in gate_priority["still_blocked"]:
        lines.append(f"- `{blocker}`")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            f"- Runtime behavior changed: `{str(summary['runtime_behavior_changed']).lower()}`",
            f"- Response text behavior changed: `{str(summary['response_text_behavior_changed']).lower()}`",
            "- No provider calls.",
            "- No LLM or LLM judging.",
            "- No private data reads.",
            "- Retrieval remains default-off.",
            "- Voice playback remains blocked.",
            "- German exact-phrase promotion remains blocked.",
            "- Public demo use remains blocked.",
            "- Real customer use remains blocked.",
            "- Payment collection remains blocked.",
            "- Contract signing remains blocked.",
            "- Production runtime promotion allowed: `false`",
            "",
            "## Next Checkpoint",
            "",
            f"`{NEXT_CHECKPOINT_ID}` should be a synthetic English policy probe for context-sensitive autonomy. It should define allowed and forbidden autonomy-preserving follow-up patterns before any runtime patch.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    source_result, path_decision, _path_options, source_evidence = load_sources()
    case_payload = build_case_file()
    write_json(CASE_FILE, case_payload)
    source_validator = run_source_validator()
    gate_options = build_gate_options()
    gate_priority = build_gate_priority(gate_options)
    evidence = build_evidence_summary(source_result, path_decision, source_evidence, source_validator)
    summary = summarize(gate_options, gate_priority, source_validator)
    result = {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "validation": {
            "passed": source_validator["passed"],
            "priority_gate_passed": source_validator["passed"],
        },
        "summary": summary,
    }

    write_json(OUT_DIR / "evidence_summary.json", evidence)
    write_json(OUT_DIR / "gate_options.json", gate_options)
    write_json(OUT_DIR / "gate_priority.json", gate_priority)
    write_json(OUT_DIR / "result.json", result)
    write_text(OUT_DIR / "report.md", render_report(gate_priority, gate_options, evidence, summary))
    print(json.dumps({"checkpoint_id": CHECKPOINT_ID, "validation": result["validation"], "summary": summary}, indent=2))


if __name__ == "__main__":
    main()
