#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-059-final-english-only-runtime-readiness-review"
CHECKPOINT_NAME = "Final English-Only Runtime Readiness Review"
SOURCE_CHECKPOINT_ID = "PROD-058-english-runtime-promotion-blocker-inventory"
SOURCE_GUARD_ID = "PROD-057-english-multi-turn-regression-guard-decision"
SOURCE_REGRESSION_ID = "PROD-056-english-post-patch-multi-turn-regression"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
REVIEW_HTML = OUT_DIR / "prod_059_review.html"
CASE_FILE = ROOT / "research" / "experiments" / "cases" / "prod-059-final-english-only-runtime-readiness-review.json"
SOURCE_DIR = ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID
SOURCE_GUARD_DIR = ROOT / "research" / "experiments" / "generated" / SOURCE_GUARD_ID
SOURCE_REGRESSION_DIR = ROOT / "research" / "experiments" / "generated" / SOURCE_REGRESSION_ID
STABLE_GUARD_SCRIPT = ROOT / "scripts" / "validate_english_multi_turn_regression_guard.py"
STABLE_GUARD_COMMAND = "python scripts\\validate_english_multi_turn_regression_guard.py"
RUNTIME_REVIEWS = SOURCE_REGRESSION_DIR / "runtime_regression_reviews.json"
CALLBACK_REVIEWS = SOURCE_REGRESSION_DIR / "callback_scheduling_reviews.json"
TERMINAL_REVIEWS = SOURCE_REGRESSION_DIR / "terminal_boundary_reviews.json"

RESOLVED_BLOCKERS = [
    "final_english_only_readiness_review_not_run",
    "english_guard_scope_limited_to_promoted_multi_turn_surface",
]

EXCLUDED_BLOCKERS = [
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


def load_sources() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    inventory_result = read_json(SOURCE_DIR / "result.json")
    inventory_recommendation = read_json(SOURCE_DIR / "recommendation.json")
    inventory_blockers = read_json(SOURCE_DIR / "blocker_inventory.json")
    guard = read_json(SOURCE_GUARD_DIR / "result.json")
    regression = read_json(SOURCE_REGRESSION_DIR / "result.json")

    if inventory_result["validation"]["inventory_gate_passed"] is not True:
        raise SystemExit("PROD-058 inventory must pass before PROD-059.")
    if inventory_recommendation["recommended_next_checkpoint"] != CHECKPOINT_ID:
        raise SystemExit("PROD-058 must recommend PROD-059 before this review.")
    if guard["summary"]["guard_status"] != "adopted":
        raise SystemExit("PROD-057 stable guard must remain adopted before PROD-059.")
    if regression["summary"]["blocking_finding_count"] != 0:
        raise SystemExit("PROD-056 regression must still have zero blocking findings before PROD-059.")
    return inventory_result, inventory_recommendation, inventory_blockers, guard, regression


def load_example_reviews() -> dict[str, Any]:
    runtime_items = read_json(RUNTIME_REVIEWS)["items"]
    callback_items = read_json(CALLBACK_REVIEWS)["items"]
    terminal_items = read_json(TERMINAL_REVIEWS)["items"]
    do_not_call = next(item for item in terminal_items if item["source_sales_difficulty"] == "do-not-call")
    product_detail = next(item for item in runtime_items if item["source_sales_difficulty"] == "product-detail-lookup")
    return {
        "manager_followup": runtime_items[0],
        "product_detail": product_detail,
        "callback_flow": callback_items[0],
        "do_not_call_boundary": do_not_call,
    }


def stable_guard_result() -> dict[str, Any]:
    completed = subprocess.run(
        [sys.executable, str(STABLE_GUARD_SCRIPT)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=240,
        check=False,
    )
    return {
        "command": STABLE_GUARD_COMMAND,
        "returncode": completed.returncode,
        "stdout_tail": completed.stdout.strip().splitlines()[-5:],
        "stderr_tail": completed.stderr.strip().splitlines()[-5:],
        "passed": completed.returncode == 0 and SOURCE_REGRESSION_ID in completed.stdout,
    }


def build_case_file() -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "source_guard_id": SOURCE_GUARD_ID,
        "source_regression_id": SOURCE_REGRESSION_ID,
        "scope": "final_english_only_readiness_review",
        "human_review_decision": "accepted_to_proceed",
        "human_review_source": "Tarik accepted the PROD-058 blocker inventory in the current review thread.",
        "stable_guard_command": STABLE_GUARD_COMMAND,
        "not_a_production_promotion": True,
        "runtime_change_requested": False,
        "allowed_readiness_statuses": ["ready_with_exclusions", "not_ready"],
    }


def build_evidence_summary(
    inventory_result: dict[str, Any],
    guard: dict[str, Any],
    regression: dict[str, Any],
    guard_run: dict[str, Any],
) -> dict[str, Any]:
    return {
        "source_inventory": {
            "checkpoint_id": inventory_result["checkpoint_id"],
            "blocker_count": inventory_result["summary"]["blocker_count"],
            "english_evidence_gap_count": inventory_result["summary"]["english_evidence_gap_count"],
            "product_policy_gate_count": inventory_result["summary"]["product_policy_gate_count"],
            "separate_gate_count": inventory_result["summary"]["separate_gate_count"],
            "recommended_next_checkpoint": inventory_result["summary"]["recommended_next_checkpoint"],
        },
        "source_guard": {
            "checkpoint_id": guard["checkpoint_id"],
            "guard_status": guard["summary"]["guard_status"],
            "stable_guard_command": guard["summary"]["stable_guard_command"],
        },
        "source_regression": {
            "checkpoint_id": regression["checkpoint_id"],
            "promoted_response_count": regression["summary"]["source_promoted_response_count"],
            "runtime_second_turn_case_count": regression["summary"]["runtime_second_turn_case_count"],
            "callback_scheduling_case_count": regression["summary"]["callback_scheduling_case_count"],
            "terminal_boundary_case_count": regression["summary"]["terminal_boundary_case_count"],
            "blocking_finding_count": regression["summary"]["blocking_finding_count"],
        },
        "stable_guard_run": guard_run,
    }


def build_scope_exclusions(inventory_blockers: dict[str, Any]) -> dict[str, Any]:
    blocker_by_id = {item["blocker_id"]: item for item in inventory_blockers["blockers"]}
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "resolved_blockers": RESOLVED_BLOCKERS,
        "excluded_blockers": EXCLUDED_BLOCKERS,
        "resolved_details": [blocker_by_id[item] for item in RESOLVED_BLOCKERS],
        "excluded_details": [blocker_by_id[item] for item in EXCLUDED_BLOCKERS],
        "excluded_policy_gates_remain_blocked": True,
        "separate_track_gates_remain_blocked": True,
    }


def build_readiness_decision() -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "decision": "english_only_runtime_ready_with_exclusions",
        "bounded_scope": {
            "language": "en",
            "runtime_path": "runtime/core/realtime_turns.py",
            "surface": "PROD-053E promoted English deterministic runtime surface guarded by PROD-056/PROD-057",
            "guard_command": STABLE_GUARD_COMMAND,
        },
        "resolved_blockers": RESOLVED_BLOCKERS,
        "excluded_blockers": EXCLUDED_BLOCKERS,
        "not_production_ready": True,
        "requires_human_decision_before_runtime_promotion_path": True,
        "recommended_next_checkpoint": "PROD-060-runtime-promotion-path-decision",
    }


def summarize(readiness_decision: dict[str, Any], guard_run: dict[str, Any]) -> dict[str, Any]:
    return {
        "human_review_acceptance_recorded": True,
        "english_only_runtime_readiness_status": "ready_with_exclusions",
        "bounded_english_surface_ready": True,
        "stable_guard_command": STABLE_GUARD_COMMAND,
        "stable_guard_passed": guard_run["passed"],
        "review_html_path": rel_path(REVIEW_HTML),
        "resolved_blocker_count": len(RESOLVED_BLOCKERS),
        "excluded_blocker_count": len(EXCLUDED_BLOCKERS),
        "resolved_blockers": RESOLVED_BLOCKERS,
        "excluded_blockers": EXCLUDED_BLOCKERS,
        "recommended_next_checkpoint": readiness_decision["recommended_next_checkpoint"],
        **BOUNDARY_FLAGS,
    }


def build_review_examples(examples: dict[str, Any], exclusions: dict[str, Any]) -> list[dict[str, Any]]:
    manager = examples["manager_followup"]
    product = examples["product_detail"]
    callback = examples["callback_flow"]
    do_not_call = examples["do_not_call_boundary"]
    policy_blockers = [
        item
        for item in exclusions["excluded_details"]
        if item["blocker_id"]
        in {
            "voicemail_action_only_behavior",
            "coverage_knowledge_policy_behavior",
            "context_sensitive_autonomy_behavior",
        }
    ]
    return [
        {
            "example_id": "bounded-manager-followup",
            "category": "ready_example",
            "title": "Manager follow-up stays inside the guarded English surface",
            "review_question": "Does this support ready_with_exclusions for the bounded English runtime surface?",
            "source_case_id": manager["case_id"],
            "customer_turn": manager["follow_up_customer_utterance"],
            "agent_turn": manager["runtime_second_turn"]["agent_response"],
            "evidence": "PROD-056 second-turn regression gates passed with no repeated first-turn response.",
            "decision_hint": "Accept if this is enough as bounded English evidence, not as production readiness.",
        },
        {
            "example_id": "bounded-product-detail",
            "category": "ready_example",
            "title": "Product detail lookup avoids invented plan details",
            "review_question": "Does this remain safe enough for the bounded English surface?",
            "source_case_id": product["case_id"],
            "customer_turn": product["follow_up_customer_utterance"],
            "agent_turn": product["runtime_second_turn"]["agent_response"],
            "evidence": "PROD-056 confirms the response stays in English, does not repeat the bridge phrase, and avoids forbidden coverage/advice markers.",
            "decision_hint": "Accept if the non-invention behavior is sufficient for the final English-only review.",
        },
        {
            "example_id": "callback-scheduling-flow",
            "category": "ready_example",
            "title": "Callback request remains coherent through scheduling",
            "review_question": "Does this callback flow support English-only readiness with exclusions?",
            "source_case_id": callback["case_id"],
            "customer_turn": callback["initial_customer_input"]["transcript"],
            "agent_turn": callback["first_turn"]["agent_response"],
            "follow_up_customer_turn": callback["follow_up_customer_utterance"],
            "follow_up_agent_turn": callback["follow_up_turn"]["agent_response"],
            "evidence": "PROD-056 keeps the first turn open for scheduling and ends only after the supplied callback time.",
            "decision_hint": "Accept if this resolves the callback multi-turn issue inside the guarded English surface.",
        },
        {
            "example_id": "do-not-call-boundary",
            "category": "boundary_example",
            "title": "Do-not-call remains terminal",
            "review_question": "Does this terminal boundary stay outside same-loop sales continuation?",
            "source_case_id": do_not_call["case_id"],
            "customer_turn": do_not_call["source_sales_difficulty"],
            "agent_turn": do_not_call["source_agent_response"],
            "evidence": "PROD-056 terminal boundary passed: no second automated sales turn expected.",
            "decision_hint": "Accept if the boundary remains blocked from further same-loop selling.",
        },
        {
            "example_id": "excluded-policy-gates",
            "category": "exclusion_example",
            "title": "Policy gates are explicitly not accepted by PROD-059",
            "review_question": "Should these remain excluded from English-only readiness?",
            "source_case_id": "PROD-058 policy blocker group",
            "customer_turn": "Voicemail, coverage knowledge, and context-sensitive autonomy cases",
            "agent_turn": "No new runtime answer is accepted in PROD-059.",
            "evidence": "; ".join(f"{item['label']}: {item['recommended_next_action']}" for item in policy_blockers),
            "decision_hint": "Request revision if any excluded policy gate should be moved into the ready surface.",
        },
    ]


def render_review_html(
    readiness_decision: dict[str, Any],
    exclusions: dict[str, Any],
    evidence: dict[str, Any],
    summary: dict[str, Any],
    review_examples: list[dict[str, Any]],
) -> str:
    data_json = json.dumps(
        {
            "checkpoint_id": CHECKPOINT_ID,
            "decision": readiness_decision,
            "summary": summary,
            "evidence": evidence,
            "examples": review_examples,
            "resolved_blockers": exclusions["resolved_blockers"],
            "excluded_blockers": exclusions["excluded_blockers"],
        },
        ensure_ascii=False,
    )
    cards = []
    for index, item in enumerate(review_examples, start=1):
        follow_up = ""
        if item.get("follow_up_customer_turn") or item.get("follow_up_agent_turn"):
            follow_up = f"""
            <div class="turn-row">
              <span>Customer follow-up</span>
              <p>{html.escape(item.get('follow_up_customer_turn', ''))}</p>
            </div>
            <div class="turn-row agent">
              <span>Agent follow-up</span>
              <p>{html.escape(item.get('follow_up_agent_turn', ''))}</p>
            </div>
            """
        cards.append(
            f"""
      <article class="example-card" data-example="{html.escape(item['example_id'])}" data-category="{html.escape(item['category'])}">
        <div class="card-top">
          <span class="eyebrow">Example {index}</span>
          <span class="tag">{html.escape(item['category'].replace('_', ' '))}</span>
        </div>
        <h2>{html.escape(item['title'])}</h2>
        <p class="question">{html.escape(item['review_question'])}</p>
        <div class="turn-row">
          <span>Customer</span>
          <p>{html.escape(item['customer_turn'])}</p>
        </div>
        <div class="turn-row agent">
          <span>Agent</span>
          <p>{html.escape(item['agent_turn'])}</p>
        </div>
        {follow_up}
        <dl>
          <dt>Source</dt><dd>{html.escape(item['source_case_id'])}</dd>
          <dt>Evidence</dt><dd>{html.escape(item['evidence'])}</dd>
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
  <title>PROD-059 Review</title>
  <style>
    :root {{
      --ink:#17212b;
      --muted:#5d6875;
      --paper:#f7f6f2;
      --panel:#ffffff;
      --line:#d7d2c8;
      --accent:#176c5f;
      --warn:#9b4b20;
      --soft:#ebe8df;
    }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; font-family:Georgia, 'Times New Roman', serif; color:var(--ink); background:var(--paper); }}
    header {{ padding:28px clamp(18px,4vw,48px); border-bottom:1px solid var(--line); background:#fffcf5; }}
    main {{ max-width:1120px; margin:0 auto; padding:24px clamp(16px,3vw,32px) 48px; }}
    h1 {{ margin:0 0 10px; font-size:clamp(28px,4vw,48px); line-height:1.05; letter-spacing:0; }}
    h2 {{ margin:8px 0 10px; font-size:24px; letter-spacing:0; }}
    p {{ line-height:1.55; }}
    .summary, .toolbar, .reviewer {{ background:var(--panel); border:1px solid var(--line); border-radius:8px; padding:16px; margin:18px 0; }}
    .metrics {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:10px; }}
    .metric {{ background:var(--soft); border:1px solid var(--line); border-radius:6px; padding:12px; }}
    .metric strong {{ display:block; font-size:20px; }}
    .toolbar {{ display:flex; flex-wrap:wrap; gap:8px; align-items:center; }}
    button, .file-label {{ border:1px solid var(--line); border-radius:6px; background:#fff; color:var(--ink); padding:10px 12px; font:inherit; cursor:pointer; }}
    button.primary {{ background:var(--accent); color:#fff; border-color:var(--accent); }}
    button.warn {{ background:var(--warn); color:#fff; border-color:var(--warn); }}
    .reviewer-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:12px; }}
    input[type="text"], input[type="date"], textarea {{ width:100%; margin-top:6px; padding:10px; border:1px solid var(--line); border-radius:6px; font:inherit; background:#fff; }}
    textarea {{ min-height:72px; resize:vertical; }}
    .example-card {{ background:var(--panel); border:1px solid var(--line); border-radius:8px; padding:18px; margin:16px 0; }}
    .card-top {{ display:flex; justify-content:space-between; gap:12px; flex-wrap:wrap; }}
    .eyebrow {{ color:var(--muted); font-size:14px; text-transform:uppercase; }}
    .tag {{ border:1px solid var(--line); border-radius:999px; padding:4px 9px; color:var(--accent); }}
    .question {{ font-weight:700; }}
    .turn-row {{ border-left:4px solid var(--line); padding:8px 12px; margin:10px 0; background:#fbfaf6; }}
    .turn-row.agent {{ border-left-color:var(--accent); }}
    .turn-row span, dt {{ color:var(--muted); font-size:14px; text-transform:uppercase; }}
    dl {{ display:grid; grid-template-columns:minmax(110px,160px) 1fr; gap:8px 12px; }}
    dd {{ margin:0; }}
    fieldset {{ border:1px solid var(--line); border-radius:6px; margin:14px 0; padding:10px; }}
    fieldset label {{ display:inline-block; margin:6px 14px 6px 0; }}
    .hidden {{ display:none; }}
    @media print {{ .toolbar, .reviewer, fieldset, .notes {{ display:none; }} body {{ background:white; }} .example-card {{ break-inside:avoid; }} }}
  </style>
</head>
<body>
  <header>
    <h1>PROD-059 Review</h1>
    <p>Final English-only runtime readiness review for the bounded deterministic surface. Not production, legal, German, voice, retrieval, provider, private-data, payment, contract, public-demo, or real-customer readiness.</p>
  </header>
  <main>
    <section class="summary">
      <div class="metrics">
        <div class="metric"><span>Status</span><strong>{html.escape(summary['english_only_runtime_readiness_status'])}</strong></div>
        <div class="metric"><span>Resolved blockers</span><strong>{summary['resolved_blocker_count']}</strong></div>
        <div class="metric"><span>Still blocked</span><strong>{summary['excluded_blocker_count']}</strong></div>
        <div class="metric"><span>Stable guard</span><strong>{str(summary['stable_guard_passed']).lower()}</strong></div>
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
    const storageKey = 'prod059FinalEnglishOnlyReview';

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
        schema_name: 'prod_059_review_export',
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
      link.download = 'prod-059-review-export.json';
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


def render_report(
    readiness_decision: dict[str, Any],
    exclusions: dict[str, Any],
    evidence: dict[str, Any],
    summary: dict[str, Any],
) -> str:
    lines = [
        "# PROD-059 Final English-Only Runtime Readiness Review",
        "",
        "`PROD-059` records human review acceptance of the `PROD-058` inventory and makes a bounded English-only readiness decision.",
        "",
        "This is not production promotion. It changes no runtime behavior or response text.",
        "",
        "## Decision",
        "",
        f"- Decision: `{readiness_decision['decision']}`",
        f"- English-only runtime readiness status: `{summary['english_only_runtime_readiness_status']}`",
        f"- Bounded English surface ready: `{str(summary['bounded_english_surface_ready']).lower()}`",
        f"- Stable guard command: `{summary['stable_guard_command']}`",
        f"- Stable guard passed: `{str(summary['stable_guard_passed']).lower()}`",
        f"- Review HTML: `{summary['review_html_path']}`",
        f"- Recommended next checkpoint: `{summary['recommended_next_checkpoint']}`",
        "- Production runtime promotion allowed: `false`",
        "",
        "## Bounded Scope",
        "",
        f"- Language: `{readiness_decision['bounded_scope']['language']}`",
        f"- Runtime path: `{readiness_decision['bounded_scope']['runtime_path']}`",
        f"- Surface: {readiness_decision['bounded_scope']['surface']}",
        "",
        "## Evidence Base",
        "",
        f"- Source inventory: `{evidence['source_inventory']['checkpoint_id']}`",
        f"- Source guard: `{evidence['source_guard']['checkpoint_id']}`",
        f"- Source regression: `{evidence['source_regression']['checkpoint_id']}`",
        f"- Promoted English response count: `{evidence['source_regression']['promoted_response_count']}`",
        f"- Regression blocking findings: `{evidence['source_regression']['blocking_finding_count']}`",
        "",
        "## Resolved For This English-Only Review",
        "",
    ]
    for blocker_id in exclusions["resolved_blockers"]:
        lines.append(f"- `{blocker_id}`")
    lines.extend(
        [
            "",
            "## Explicitly Excluded And Still Blocked",
            "",
        ]
    )
    for blocker_id in exclusions["excluded_blockers"]:
        lines.append(f"- `{blocker_id}`")
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
            "- Retrieval default remains blocked.",
            "- German exact-phrase promotion remains blocked.",
            "- Voice playback remains blocked.",
            "- Public demo use, real customer use, payment collection, contract signing, legal readiness, and production runtime promotion remain blocked.",
            "",
            "## Next Decision",
            "",
            "`PROD-060` should decide the runtime-promotion path. That decision can still choose not to promote anything. It must not turn this English-only review into production, public demo, legal, provider, retrieval, voice, or German readiness.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    inventory_result, _recommendation, inventory_blockers, guard, regression = load_sources()
    example_reviews = load_example_reviews()
    case_payload = build_case_file()
    write_json(CASE_FILE, case_payload)
    guard_run = stable_guard_result()
    evidence = build_evidence_summary(inventory_result, guard, regression, guard_run)
    exclusions = build_scope_exclusions(inventory_blockers)
    review_examples = build_review_examples(example_reviews, exclusions)
    readiness_decision = build_readiness_decision()
    summary = summarize(readiness_decision, guard_run)
    result = {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "validation": {
            "passed": guard_run["passed"],
            "readiness_review_passed": guard_run["passed"],
        },
        "summary": summary,
    }
    write_json(OUT_DIR / "evidence_summary.json", evidence)
    write_json(OUT_DIR / "scope_exclusions.json", exclusions)
    write_json(OUT_DIR / "readiness_decision.json", readiness_decision)
    write_json(OUT_DIR / "result.json", result)
    write_text(OUT_DIR / "prod_059_review.html", render_review_html(readiness_decision, exclusions, evidence, summary, review_examples))
    write_text(OUT_DIR / "report.md", render_report(readiness_decision, exclusions, evidence, summary))
    print(json.dumps({"checkpoint_id": CHECKPOINT_ID, "validation": result["validation"], "summary": summary}, indent=2))


if __name__ == "__main__":
    main()
