#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-060-runtime-promotion-path-decision"
CHECKPOINT_NAME = "Runtime Promotion Path Decision"
SOURCE_CHECKPOINT_ID = "PROD-059-final-english-only-runtime-readiness-review"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
REVIEW_HTML = OUT_DIR / "prod_060_review.html"
CASE_FILE = ROOT / "research" / "experiments" / "cases" / "prod-060-runtime-promotion-path-decision.json"
SOURCE_DIR = ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID
SOURCE_VALIDATOR = ROOT / "scripts" / "validate_prod_059_final_english_only_runtime_readiness_review.py"
SOURCE_VALIDATOR_COMMAND = "python scripts\\validate_prod_059_final_english_only_runtime_readiness_review.py"
NEXT_CHECKPOINT_ID = "PROD-061-english-product-policy-gate-prioritization"

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
    readiness_decision = read_json(SOURCE_DIR / "readiness_decision.json")
    scope_exclusions = read_json(SOURCE_DIR / "scope_exclusions.json")
    evidence_summary = read_json(SOURCE_DIR / "evidence_summary.json")

    if source_result["validation"]["passed"] is not True:
        raise SystemExit("PROD-059 must pass before PROD-060.")
    if source_result["summary"]["english_only_runtime_readiness_status"] != "ready_with_exclusions":
        raise SystemExit("PROD-059 must be ready_with_exclusions before PROD-060.")
    if source_result["summary"]["recommended_next_checkpoint"] != CHECKPOINT_ID:
        raise SystemExit("PROD-059 must recommend PROD-060 before this decision.")
    if readiness_decision["requires_human_decision_before_runtime_promotion_path"] is not True:
        raise SystemExit("PROD-059 must require a human path decision before PROD-060.")
    if set(scope_exclusions["excluded_blockers"]) != set(STILL_BLOCKED):
        raise SystemExit("PROD-059 excluded blocker set changed; review before PROD-060.")
    if evidence_summary["stable_guard_run"]["passed"] is not True:
        raise SystemExit("PROD-059 stable guard evidence must pass before PROD-060.")
    return source_result, readiness_decision, scope_exclusions, evidence_summary


def build_case_file() -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "scope": "path_decision_only",
        "human_review_decision": "accepted_to_proceed",
        "human_review_source": "Tarik accepted the PROD-059 review artifact in the current review thread.",
        "selected_path": "internal_guarded_english_baseline_only",
        "not_a_production_promotion": True,
        "runtime_change_requested": False,
        "requires_human_review_before_next_checkpoint": True,
        "non_goals": [
            "runtime behavior change",
            "response text change",
            "public demo approval",
            "real customer use",
            "provider call",
            "LLM call",
            "private data read",
            "retrieval default change",
            "voice playback promotion",
            "German exact phrase promotion",
            "legal compliance approval",
            "payment collection",
            "contract signing",
            "production runtime promotion",
        ],
    }


def build_path_options() -> dict[str, Any]:
    options = [
        {
            "path_id": "internal_guarded_english_baseline_only",
            "label": "Internal guarded English baseline only",
            "status": "selected",
            "selected": True,
            "allowed_scope": "local_offline_synthetic_internal_regression_reference",
            "why": "PROD-059 makes the bounded English deterministic surface ready_with_exclusions, and this path does not cross any still-blocked legal, provider, voice, retrieval, public-demo, real-customer, payment, contract, German, or production boundary.",
            "blocked_by": [],
            "review_question": "Should this bounded English surface become only an internal, local/offline synthetic regression reference while broader gates stay blocked?",
        },
        {
            "path_id": "public_demo_path",
            "label": "Public demo path",
            "status": "blocked",
            "selected": False,
            "allowed_scope": "none",
            "why": "Public demo use remains explicitly excluded by PROD-059 and needs its own public-demo, polish, safety, and legal review.",
            "blocked_by": ["public_demo_use", "legal_compliance_review"],
            "review_question": "Is there any evidence that public demo use is ready now? PROD-060 records no such evidence.",
        },
        {
            "path_id": "real_customer_path",
            "label": "Real customer path",
            "status": "blocked",
            "selected": False,
            "allowed_scope": "none",
            "why": "Real customer use remains blocked; the current evidence is synthetic and local.",
            "blocked_by": ["real_customer_use", "legal_compliance_review", "provider_or_private_data_use"],
            "review_question": "Should real customer calls stay blocked until a separate customer-use gate exists?",
        },
        {
            "path_id": "provider_or_private_data_path",
            "label": "Provider or private-data path",
            "status": "blocked",
            "selected": False,
            "allowed_scope": "none",
            "why": "PROD-059 did not approve provider calls, LLM use, or private-data reads.",
            "blocked_by": ["provider_or_private_data_use"],
            "review_question": "Should provider/private-data work remain a separate explicit opt-in gate?",
        },
        {
            "path_id": "retrieval_default_path",
            "label": "Retrieval default path",
            "status": "blocked",
            "selected": False,
            "allowed_scope": "none",
            "why": "Runtime retrieval remains disabled by default and must reopen through RAG gates.",
            "blocked_by": ["retrieval_default"],
            "review_question": "Should retrieval stay default-off for this path decision?",
        },
        {
            "path_id": "voice_playback_path",
            "label": "Voice playback path",
            "status": "blocked",
            "selected": False,
            "allowed_scope": "none",
            "why": "Voice playback quality remains a separate listening gate and is not proven by English text readiness.",
            "blocked_by": ["voice_playback_quality"],
            "review_question": "Should voice playback stay outside the English runtime path?",
        },
        {
            "path_id": "german_language_path",
            "label": "German language path",
            "status": "blocked",
            "selected": False,
            "allowed_scope": "none",
            "why": "Native German review remains parked until the corrected reviewer export exists.",
            "blocked_by": ["native_german_review"],
            "review_question": "Should German exact-phrase promotion remain parked instead of folded into English readiness?",
        },
        {
            "path_id": "payment_or_contract_path",
            "label": "Payment or contract path",
            "status": "blocked",
            "selected": False,
            "allowed_scope": "none",
            "why": "Payment collection and contract signing are legal/deployment actions, not runtime wording readiness.",
            "blocked_by": ["payment_collection", "contract_signing", "legal_compliance_review"],
            "review_question": "Should payment and contract activity remain blocked until separate legal/deployment gates?",
        },
        {
            "path_id": "production_runtime_path",
            "label": "Production runtime path",
            "status": "blocked",
            "selected": False,
            "allowed_scope": "none",
            "why": "Production runtime promotion remains explicitly blocked by PROD-059 exclusions.",
            "blocked_by": ["production_runtime_promotion", "legal_compliance_review", "real_customer_use"],
            "review_question": "Should PROD-060 reject production promotion until product-policy and deployment gates are resolved?",
        },
    ]
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "path_options": options,
        "blocked_path_count": sum(1 for item in options if item["status"] == "blocked"),
        "selected_path_id": "internal_guarded_english_baseline_only",
    }


def build_path_decision(path_options: dict[str, Any]) -> dict[str, Any]:
    selected_path = next(item for item in path_options["path_options"] if item["selected"])
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "decision": "select_internal_guarded_english_baseline_only",
        "selected_path": {
            "path_id": selected_path["path_id"],
            "allowed_scope": selected_path["allowed_scope"],
            "plain_language_scope": "local offline synthetic internal regression reference",
            "runtime_change": False,
            "response_text_change": False,
            "production_promotion": False,
            "public_demo": False,
            "real_customer_use": False,
            "provider_or_private_data_use": False,
        },
        "blocked_paths": [
            item["path_id"] for item in path_options["path_options"] if item["status"] == "blocked"
        ],
        "still_blocked": STILL_BLOCKED,
        "requires_human_review_before_next_checkpoint": True,
        "recommended_next_checkpoint": NEXT_CHECKPOINT_ID,
    }


def build_evidence_summary(
    source_result: dict[str, Any],
    readiness_decision: dict[str, Any],
    scope_exclusions: dict[str, Any],
    evidence_summary: dict[str, Any],
    source_validator: dict[str, Any],
) -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "source_readiness_status": source_result["summary"]["english_only_runtime_readiness_status"],
        "source_readiness_decision": readiness_decision["decision"],
        "source_bounded_scope": readiness_decision["bounded_scope"],
        "source_stable_guard_command": source_result["summary"]["stable_guard_command"],
        "source_stable_guard_passed": source_result["summary"]["stable_guard_passed"],
        "source_review_html_path": source_result["summary"]["review_html_path"],
        "source_resolved_blockers": scope_exclusions["resolved_blockers"],
        "source_excluded_blockers": scope_exclusions["excluded_blockers"],
        "source_regression": evidence_summary["source_regression"],
        "source_validator_run": source_validator,
    }


def summarize(
    source_result: dict[str, Any],
    path_options: dict[str, Any],
    path_decision: dict[str, Any],
    source_validator: dict[str, Any],
) -> dict[str, Any]:
    return {
        "path_decision_only": True,
        "human_review_acceptance_recorded": True,
        "source_readiness_status": source_result["summary"]["english_only_runtime_readiness_status"],
        "source_validator_passed": source_validator["passed"],
        "selected_path": path_decision["selected_path"]["path_id"],
        "selected_path_allowed": True,
        "allowed_scope": path_decision["selected_path"]["allowed_scope"],
        "plain_language_scope": path_decision["selected_path"]["plain_language_scope"],
        "blocked_path_count": path_options["blocked_path_count"],
        "still_blocked_count": len(path_decision["still_blocked"]),
        "still_blocked": path_decision["still_blocked"],
        "review_html_path": rel_path(REVIEW_HTML),
        "requires_human_review_before_next_checkpoint": True,
        "recommended_next_checkpoint": NEXT_CHECKPOINT_ID,
        **BOUNDARY_FLAGS,
    }


def build_review_examples(path_options: dict[str, Any], path_decision: dict[str, Any]) -> list[dict[str, Any]]:
    options_by_id = {item["path_id"]: item for item in path_options["path_options"]}
    return [
        {
            "example_id": "selected-internal-baseline",
            "category": "selected_path",
            "title": "Selected path: internal guarded English baseline only",
            "path": options_by_id["internal_guarded_english_baseline_only"],
            "example_use": "Run local/offline synthetic regression checks against the bounded English deterministic surface and use it as an internal reference for future runtime QA.",
            "decision_hint": "Accept if this is the only safe path that preserves PROD-059 exclusions.",
        },
        {
            "example_id": "blocked-public-demo",
            "category": "blocked_path",
            "title": "Blocked path: public demo",
            "path": options_by_id["public_demo_path"],
            "example_use": "Showing the agent as a public product demo, even with synthetic prompts.",
            "decision_hint": "Request revision only if a separate public-demo review already exists. PROD-060 records none.",
        },
        {
            "example_id": "blocked-real-customer-provider",
            "category": "blocked_path",
            "title": "Blocked path: real customer or provider run",
            "path": options_by_id["real_customer_path"],
            "secondary_path": options_by_id["provider_or_private_data_path"],
            "example_use": "Connecting the runtime to a live call, external TTS/LLM provider, or private customer data.",
            "decision_hint": "Accept the block unless provider, consent, retention, legal, and customer-use gates are explicitly reviewed.",
        },
        {
            "example_id": "blocked-production-runtime",
            "category": "blocked_path",
            "title": "Blocked path: production runtime promotion",
            "path": options_by_id["production_runtime_path"],
            "example_use": "Treating PROD-059 readiness as permission to ship the runtime for production use.",
            "decision_hint": "Accept the block; PROD-059 explicitly says not production ready.",
        },
        {
            "example_id": "next-product-policy-gates",
            "category": "next_checkpoint",
            "title": "Next checkpoint: prioritize English product-policy gates",
            "path": {
                "path_id": NEXT_CHECKPOINT_ID,
                "label": "English product-policy gate prioritization",
                "why": "The selected path is stable enough as an internal baseline, but broad English runtime promotion is blocked by customer-move classification, voicemail action-only behavior, coverage knowledge-policy behavior, and context-sensitive autonomy behavior.",
                "review_question": "Should PROD-061 prioritize those four product-policy gates before any broader runtime promotion?",
                "blocked_by": [
                    "customer_move_classification_outside_selected_non_refusal_groups",
                    "voicemail_action_only_behavior",
                    "coverage_knowledge_policy_behavior",
                    "context_sensitive_autonomy_behavior",
                ],
            },
            "example_use": "Deciding which English policy gate to unblock first instead of moving to production, provider, voice, retrieval, German, payment, or contract work.",
            "decision_hint": "Accept if this is the right next bottleneck after the path decision.",
        },
    ]


def render_review_html(
    path_decision: dict[str, Any],
    path_options: dict[str, Any],
    evidence: dict[str, Any],
    summary: dict[str, Any],
    review_examples: list[dict[str, Any]],
) -> str:
    data_json = json.dumps(
        {
            "checkpoint_id": CHECKPOINT_ID,
            "decision": path_decision,
            "options": path_options,
            "summary": summary,
            "evidence": evidence,
            "examples": review_examples,
        },
        ensure_ascii=False,
    )
    cards: list[str] = []
    for index, item in enumerate(review_examples, start=1):
        primary_path = item["path"]
        secondary = item.get("secondary_path")
        secondary_text = ""
        if secondary:
            secondary_text = f"""
          <dt>Related path</dt><dd>{html.escape(secondary['label'])}: {html.escape(secondary['why'])}</dd>
            """
        blocked_by = ", ".join(primary_path.get("blocked_by", [])) or "none"
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
          <dt>Path</dt><dd>{html.escape(primary_path['path_id'])}</dd>
          <dt>Status</dt><dd>{html.escape(primary_path.get('status', 'next'))}</dd>
          <dt>Allowed scope</dt><dd>{html.escape(primary_path.get('allowed_scope', 'review-only'))}</dd>
          <dt>Blocked by</dt><dd>{html.escape(blocked_by)}</dd>
          <dt>Why</dt><dd>{html.escape(primary_path['why'])}</dd>
          {secondary_text}
          <dt>Review question</dt><dd>{html.escape(primary_path['review_question'])}</dd>
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
  <title>PROD-060 Review</title>
  <style>
    :root {{
      --ink:#15202b;
      --muted:#5a6672;
      --paper:#f6f4ef;
      --panel:#ffffff;
      --line:#d4cec3;
      --accent:#245e55;
      --danger:#914121;
      --soft:#e9e5dc;
    }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; font-family:Georgia, 'Times New Roman', serif; color:var(--ink); background:var(--paper); }}
    header {{ padding:28px clamp(18px,4vw,48px); border-bottom:1px solid var(--line); background:#fffcf5; }}
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
    dl {{ display:grid; grid-template-columns:minmax(110px,170px) 1fr; gap:8px 12px; }}
    dd {{ margin:0; }}
    dt {{ color:var(--muted); font-size:14px; text-transform:uppercase; }}
    fieldset {{ border:1px solid var(--line); border-radius:6px; margin:14px 0; padding:10px; }}
    fieldset label {{ display:inline-block; margin:6px 14px 6px 0; }}
    @media print {{ .toolbar, .reviewer, fieldset, .notes {{ display:none; }} body {{ background:white; }} .example-card {{ break-inside:avoid; }} }}
  </style>
</head>
<body>
  <header>
    <h1>PROD-060 Review</h1>
    <p>Runtime promotion path decision. Selected path: internal_guarded_english_baseline_only. Plain-language scope: local offline synthetic internal regression reference. This is not production promotion.</p>
  </header>
  <main>
    <section class="summary">
      <div class="metrics">
        <div class="metric"><span>Source status</span><strong>{html.escape(summary['source_readiness_status'])}</strong></div>
        <div class="metric"><span>Selected path</span><strong>{html.escape(summary['selected_path'])}</strong></div>
        <div class="metric"><span>Blocked paths</span><strong>{summary['blocked_path_count']}</strong></div>
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
    const storageKey = 'prod060RuntimePromotionPathReview';

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
        schema_name: 'prod_060_review_export',
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
        source_decision: reviewPayload.decision,
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
      link.download = 'prod-060-review-export.json';
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


def render_report(path_decision: dict[str, Any], path_options: dict[str, Any], evidence: dict[str, Any], summary: dict[str, Any]) -> str:
    lines = [
        "# PROD-060 Runtime Promotion Path Decision",
        "",
        "`PROD-060` records the path decision after human acceptance of `PROD-059`.",
        "",
        "This is a path decision only. It changes no runtime behavior or response text.",
        "",
        "## Decision",
        "",
        f"- Decision: `{path_decision['decision']}`",
        f"- Selected path: `{summary['selected_path']}`",
        f"- Allowed scope: `{summary['allowed_scope']}`",
        "- Plain-language scope: local offline synthetic internal regression reference",
        f"- Source readiness status: `{summary['source_readiness_status']}`",
        f"- Blocked path count: `{summary['blocked_path_count']}`",
        f"- Still-blocked blocker count: `{summary['still_blocked_count']}`",
        f"- Review HTML: `{summary['review_html_path']}`",
        f"- Recommended next checkpoint: `{summary['recommended_next_checkpoint']}`",
        "- Production runtime promotion allowed: `false`",
        "",
        "## Selected Path",
        "",
        "The selected path is not production and not public demo use. It only allows the bounded English deterministic surface to be used as a local offline synthetic internal regression reference.",
        "",
        "## Rejected Paths",
        "",
    ]
    for option in path_options["path_options"]:
        if option["selected"]:
            continue
        lines.extend(
            [
                f"### {option['path_id']}",
                "",
                f"- Label: {option['label']}",
                f"- Status: `{option['status']}`",
                f"- Why: {option['why']}",
                f"- Blocked by: `{', '.join(option['blocked_by'])}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Source Evidence",
            "",
            f"- Source checkpoint: `{evidence['source_checkpoint_id']}`",
            f"- Source readiness decision: `{evidence['source_readiness_decision']}`",
            f"- Source stable guard command: `{evidence['source_stable_guard_command']}`",
            f"- Source stable guard passed: `{str(evidence['source_stable_guard_passed']).lower()}`",
            f"- Source review HTML: `{evidence['source_review_html_path']}`",
            "",
            "## Still Blocked",
            "",
        ]
    )
    for blocker in path_decision["still_blocked"]:
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
            f"`{NEXT_CHECKPOINT_ID}` should prioritize the four English product-policy gates that still block broader English runtime promotion: customer-move classification, voicemail action-only behavior, coverage knowledge-policy behavior, and context-sensitive autonomy behavior.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    source_result, readiness_decision, scope_exclusions, source_evidence = load_sources()
    case_payload = build_case_file()
    write_json(CASE_FILE, case_payload)
    source_validator = run_source_validator()
    path_options = build_path_options()
    path_decision = build_path_decision(path_options)
    evidence = build_evidence_summary(source_result, readiness_decision, scope_exclusions, source_evidence, source_validator)
    summary = summarize(source_result, path_options, path_decision, source_validator)
    review_examples = build_review_examples(path_options, path_decision)
    result = {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "validation": {
            "passed": source_validator["passed"],
            "path_decision_gate_passed": source_validator["passed"],
        },
        "summary": summary,
    }

    write_json(OUT_DIR / "evidence_summary.json", evidence)
    write_json(OUT_DIR / "path_options.json", path_options)
    write_json(OUT_DIR / "path_decision.json", path_decision)
    write_json(OUT_DIR / "result.json", result)
    write_text(OUT_DIR / "prod_060_review.html", render_review_html(path_decision, path_options, evidence, summary, review_examples))
    write_text(OUT_DIR / "report.md", render_report(path_decision, path_options, evidence, summary))
    print(json.dumps({"checkpoint_id": CHECKPOINT_ID, "validation": result["validation"], "summary": summary}, indent=2))


if __name__ == "__main__":
    main()
