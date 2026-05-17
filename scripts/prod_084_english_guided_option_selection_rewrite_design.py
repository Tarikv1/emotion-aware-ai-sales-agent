#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-084-english-guided-option-selection-rewrite-design"
CHECKPOINT_NAME = "English Guided Option Selection Rewrite Design"
SOURCE_CHECKPOINT_ID = "PROD-083-english-guided-option-selection-review-import"
NEXT_CHECKPOINT_ID = "PROD-085-english-guided-option-selection-rewrite-review-import"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
CASE_FILE = ROOT / "research" / "experiments" / "cases" / "prod-084-english-guided-option-selection-rewrite-design.json"
SOURCE_DIR = ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID
SOURCE_VALIDATOR = ROOT / "scripts" / "validate_prod_083_english_guided_option_selection_review_import.py"
REVIEW_HTML = OUT_DIR / "prod_084_review.html"

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
    "approve_rewrite_for_policy_probe",
    "needs_rewrite",
    "keep_deferred",
]

PLAN_FIXTURE = {
    "checkpoint_id": CHECKPOINT_ID,
    "review_only_fixture": True,
    "invent_plan_features_allowed_in_runtime": False,
    "plans": {
        "29": {
            "label": "$29 starter placeholder",
            "features": ["[feature X]", "[feature Y]", "[feature Z]"],
            "fit_when": "customer only needs the basic feature set",
        },
        "59": {
            "label": "$59 expanded placeholder",
            "features": ["[feature X]", "[feature Y]", "[feature Z]", "[feature A]", "[feature B]", "[feature C]"],
            "fit_when": "customer benefits from the added features or wants fewer gaps later",
        },
    },
    "upgrade_path_placeholder": "$29 can be used as a starter path if the campaign allows later upgrade to $59.",
}

EXAMPLES = [
    {
        "example_id": "rewrite-binary-choice",
        "title": "Direct choice",
        "customer_turn": "So do I choose the $29 option or the $59 option?",
        "proposed_response": "I mean, if you only need [feature X] and [feature Y], start with $29. If [feature A] matters too, $59 fits better.",
        "uses_discourse_marker": True,
        "marker": "I mean",
        "review_focus": "Answer fit directly without repeating that one option is cheaper.",
    },
    {
        "example_id": "rewrite-fit-unclear",
        "title": "Fit is unclear",
        "customer_turn": "I can see both paths, I am just not sure which one fits me.",
        "proposed_response": "Based on what you said, $59 sounds stronger if [feature A] saves you time. If not, $29 is the safer start and you can upgrade later.",
        "uses_discourse_marker": False,
        "marker": "",
        "review_focus": "Steer from customer facts while preserving the upgrade path.",
    },
    {
        "example_id": "rewrite-recommendation",
        "title": "Recommendation request",
        "customer_turn": "Which route would you suggest for someone like me?",
        "proposed_response": "Honestly, like, if your main issue is [customer pain], I would lean $59 because it adds [feature A] and [feature B]. If budget matters more, start $29.",
        "uses_discourse_marker": True,
        "marker": "like",
        "review_focus": "Allow a recommendation without pretending to choose for the customer.",
    },
    {
        "example_id": "rewrite-difference",
        "title": "Explain the difference",
        "customer_turn": "What is the real difference between the $29 option and the $59 option?",
        "proposed_response": "$29 covers [feature X], [feature Y], and [feature Z]. $59 adds [feature A] and [feature B], so it fits better if you need [customer goal].",
        "uses_discourse_marker": False,
        "marker": "",
        "review_focus": "Answer the real difference using approved plan facts.",
    },
    {
        "example_id": "rewrite-decide-later",
        "title": "Decide later",
        "customer_turn": "Can I choose later instead of deciding on this call?",
        "proposed_response": "Yes. I can send the differences in writing and keep both options open for the follow-up.",
        "uses_discourse_marker": False,
        "marker": "",
        "review_focus": "Keep deferral short and avoid saying the same thing twice.",
    },
    {
        "example_id": "rewrite-neither-uncertain",
        "title": "Neither feels right",
        "customer_turn": "I'm not sure either is right.",
        "proposed_response": "I get that, you know, it may just mean we should match the plan to [customer goal] first, then see whether $29 or $59 makes sense.",
        "uses_discourse_marker": True,
        "marker": "you know",
        "review_focus": "Use acknowledgement plus light persuasion instead of ending the opportunity.",
    },
    {
        "example_id": "rewrite-payment-path",
        "title": "Payment path",
        "customer_turn": "If I pick one, can I pay now?",
        "proposed_response": "No payment on this call. I'll send the companyname.com email with the link, and you can review the plan and finish registration there.",
        "uses_discourse_marker": False,
        "marker": "",
        "sensitive_boundary": "payment",
        "review_focus": "Explain the approved campaign payment path without collecting payment.",
    },
    {
        "example_id": "rewrite-upgrade-path",
        "title": "Start cheaper, upgrade later",
        "customer_turn": "Could I start smaller and change later if it works?",
        "proposed_response": "You can start with $29 if [feature X] covers enough. If you later need [feature A] or [feature B], we can move you to $59.",
        "uses_discourse_marker": False,
        "marker": "",
        "review_focus": "Use the upgrade path as a selling bridge when campaign rules allow it.",
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


def load_source() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    source_result = read_json(SOURCE_DIR / "result.json")
    rewrite = read_json(SOURCE_DIR / "rewrite_requirements.json")
    plan_facts = read_json(SOURCE_DIR / "plan_fact_requirements.json")
    payment = read_json(SOURCE_DIR / "payment_workflow_requirements.json")
    naturalness = read_json(SOURCE_DIR / "spoken_naturalness_constraints.json")
    if source_result["validation"]["passed"] is not True:
        raise RuntimeError("PROD-083 must pass before PROD-084.")
    if source_result["summary"]["recommended_next_checkpoint"] != CHECKPOINT_ID:
        raise RuntimeError("PROD-083 must recommend PROD-084.")
    if rewrite["rewrite_required"] is not True:
        raise RuntimeError("PROD-083 must require rewrite.")
    return source_result, rewrite, plan_facts, payment, naturalness


def word_count(text: str) -> int:
    return len(text.replace("/", " ").replace("-", " ").split())


def build_case_file() -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "scope": "english_guided_option_selection_rewrite_review_only",
        "review_item": "guided_option_selection_rewritten_examples",
        "requires_human_review_before_next_checkpoint": True,
        "review_html_created": True,
        "review_html_path": rel(REVIEW_HTML),
        "runtime_change_requested": False,
        "response_text_change_requested": False,
        "classifier_change_requested": False,
        "retrieval_change_requested": False,
        "recommended_next_checkpoint": NEXT_CHECKPOINT_ID,
    }


def build_review_packet(rewrite: dict[str, Any], payment: dict[str, Any], naturalness: dict[str, Any]) -> dict[str, Any]:
    examples = []
    for item in EXAMPLES:
        examples.append(
            {
                **item,
                "word_count": word_count(item["proposed_response"]),
                "current_runtime_route": "unknown-runtime-signal",
                "review_target": "guided_option_selection_rewritten_examples",
            }
        )
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "review_item": "guided_option_selection_rewritten_examples",
        "review_options": REVIEW_OPTIONS,
        "examples_are_review_only": True,
        "runtime_candidate_promoted": False,
        "question": "Do these rewritten guided option examples sound like usable live-call wording, including sparse discourse markers, or do they still need rewriting?",
        "source_rules": rewrite["rules"],
        "payment_rule": payment["runtime_requirement"],
        "naturalness_rule": naturalness["runtime_requirement"],
        "examples": examples,
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


def build_naturalness_audit(packet: dict[str, Any]) -> dict[str, Any]:
    examples_with_markers = [item for item in packet["examples"] if item["uses_discourse_marker"]]
    sensitive_violations = [
        item["example_id"]
        for item in packet["examples"]
        if item.get("sensitive_boundary") and item["uses_discourse_marker"]
    ]
    marker_counts: dict[str, int] = {}
    for item in examples_with_markers:
        marker_counts[item["marker"]] = marker_counts.get(item["marker"], 0) + 1
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "random_fillers_allowed": False,
        "sparse_discourse_markers_required_for_review": True,
        "examples_with_discourse_markers": len(examples_with_markers),
        "marker_counts": marker_counts,
        "sensitive_boundary_marker_violations": sensitive_violations,
        "max_word_count": max(item["word_count"] for item in packet["examples"]),
    }


def build_evidence(
    source_result: dict[str, Any],
    rewrite: dict[str, Any],
    plan_facts: dict[str, Any],
    payment: dict[str, Any],
    naturalness: dict[str, Any],
    source_validator: dict[str, Any],
) -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "source_validation": source_result["validation"],
        "source_summary": {
            "imported_review_decision": source_result["summary"]["imported_review_decision"],
            "rewrite_required": source_result["summary"]["rewrite_required"],
            "recommended_next_checkpoint": source_result["summary"]["recommended_next_checkpoint"],
        },
        "source_rewrite_rules": rewrite["rules"],
        "source_plan_fact_requirement": {
            "plan_feature_matrix_required": plan_facts["plan_feature_matrix_required"],
            "invent_plan_features_allowed": plan_facts["invent_plan_features_allowed"],
        },
        "source_payment_requirement": {
            "no_payment_on_call_default": payment["no_payment_on_call_default"],
            "approved_campaign_payment_path_can_be_explained": payment["approved_campaign_payment_path_can_be_explained"],
        },
        "source_naturalness_requirement": {
            "sparse_contextual_discourse_markers_candidate": naturalness["sparse_contextual_discourse_markers_candidate"],
            "random_fillers_allowed": naturalness["random_fillers_allowed"],
        },
        "source_validator_run": source_validator,
    }


def summarize(packet: dict[str, Any], naturalness_audit: dict[str, Any], source_validator: dict[str, Any]) -> dict[str, Any]:
    return {
        "review_packet_only": True,
        "source_validator_passed": source_validator["passed"],
        "selected_review_item": packet["review_item"],
        "review_example_count": len(packet["examples"]),
        "requires_human_review_before_next_checkpoint": True,
        "review_html_created": True,
        "review_html_path": rel(REVIEW_HTML),
        "narrow_policy_probe_approved": False,
        "runtime_candidate_promoted": False,
        "examples_with_discourse_markers": naturalness_audit["examples_with_discourse_markers"],
        "random_fillers_allowed": False,
        "recommended_next_checkpoint": NEXT_CHECKPOINT_ID,
        **BOUNDARY_FLAGS,
    }


def render_report(summary: dict[str, Any], packet: dict[str, Any], plan_fixture: dict[str, Any], naturalness_audit: dict[str, Any]) -> str:
    lines = [
        "# PROD-084 English Guided Option Selection Rewrite Design",
        "",
        "`PROD-084` creates rewritten guided option selection examples for human review.",
        "",
        "This checkpoint does not patch runtime behavior, response text, classifier reachability, retrieval, payment handling, or spoken naturalness behavior.",
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
        "- Narrow policy probe approved: `false`",
        "- Runtime candidate promoted: `false`",
        "- Random fillers allowed: `false`",
        "- Runtime behavior changed: `false`",
        "- Response text behavior changed: `false`",
        "- Classifier behavior changed: `false`",
        "- Retrieval enabled: `false`",
        "- Production runtime promotion allowed: `false`",
        "",
        "## Review-Only Plan Feature Matrix",
        "",
    ]
    for plan_id, plan in plan_fixture["plans"].items():
        lines.append(f"- `${plan_id}`: {', '.join(plan['features'])}")
    lines.extend(
        [
            "",
            "## Sparse Discourse Markers",
            "",
            f"- Examples with discourse markers: `{naturalness_audit['examples_with_discourse_markers']}`",
            f"- Sensitive boundary marker violations: `{', '.join(naturalness_audit['sensitive_boundary_marker_violations']) or 'none'}`",
            "",
            "## Examples",
            "",
        ]
    )
    for item in packet["examples"]:
        lines.extend(
            [
                f"### {item['title']}",
                "",
                f"- Customer turn: {item['customer_turn']}",
                f"- Uses discourse marker: `{str(item['uses_discourse_marker']).lower()}`",
                f"- Word count: `{item['word_count']}`",
                f"- Review focus: {item['review_focus']}",
                "",
                "```text",
                item["proposed_response"],
                "```",
                "",
            ]
        )
    lines.extend(
        [
            "## Boundary Status",
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


def render_review_html(packet: dict[str, Any], template: dict[str, Any], plan_fixture: dict[str, Any], summary: dict[str, Any]) -> str:
    packet_json = json.dumps(packet, ensure_ascii=False)
    template_json = json.dumps(template, ensure_ascii=False)
    cards = "\n".join(render_example_card(index + 1, item) for index, item in enumerate(packet["examples"]))
    plan_rows = "\n".join(
        f"<tr><th>${html.escape(plan_id)}</th><td>{html.escape(', '.join(plan['features']))}</td><td>{html.escape(plan['fit_when'])}</td></tr>"
        for plan_id, plan in plan_fixture["plans"].items()
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>PROD-084 Guided Option Selection Rewrite</title>
  <style>
    :root {{
      --ink:#111416;
      --muted:#58636b;
      --paper:#f0ece4;
      --panel:#fffdf6;
      --line:#c8bfb0;
      --accent:#245f5a;
      --accent-2:#a5632a;
      --danger:#87372f;
      --soft:#e7ded0;
      --focus:#f5c84b;
    }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; color:var(--ink); background:var(--paper); font-family:Cambria, Georgia, 'Times New Roman', serif; }}
    header {{ padding:28px clamp(18px,4vw,54px); border-bottom:1px solid var(--line); background:var(--panel); }}
    main {{ max-width:1240px; margin:0 auto; padding:18px clamp(16px,3vw,32px) 44px; }}
    h1 {{ margin:0 0 8px; font-size:clamp(30px,4vw,48px); line-height:1.06; letter-spacing:0; }}
    h2 {{ margin:0 0 10px; font-size:23px; letter-spacing:0; }}
    h3 {{ margin:0 0 8px; font-size:18px; letter-spacing:0; }}
    p {{ line-height:1.5; }}
    .subhead {{ max-width:960px; color:var(--muted); font-size:18px; }}
    .grid {{ display:grid; grid-template-columns:minmax(0,1fr) 350px; gap:16px; align-items:start; }}
    .panel, .toolbar, .reviewer, .example-card {{ background:var(--panel); border:1px solid var(--line); border-radius:8px; }}
    .panel, .reviewer, .toolbar {{ padding:16px; margin:0 0 16px; }}
    .metrics {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(160px,1fr)); gap:10px; }}
    .metric {{ background:var(--soft); border:1px solid var(--line); border-radius:6px; padding:11px; min-height:76px; }}
    .metric span {{ display:block; color:var(--muted); font-size:12px; text-transform:uppercase; }}
    .metric strong {{ display:block; margin-top:6px; font-size:18px; overflow-wrap:anywhere; }}
    .sidebar {{ position:sticky; top:12px; }}
    table {{ width:100%; border-collapse:collapse; font-size:14px; }}
    th, td {{ border:1px solid var(--line); padding:8px; text-align:left; vertical-align:top; }}
    th {{ background:var(--soft); width:74px; }}
    .toolbar {{ display:flex; gap:8px; align-items:center; flex-wrap:wrap; }}
    button, .file-label, select {{ border:1px solid var(--line); border-radius:6px; background:#fff; color:var(--ink); padding:9px 11px; font:inherit; cursor:pointer; }}
    button.primary {{ background:var(--accent); color:white; border-color:var(--accent); }}
    button.warn {{ background:var(--danger); color:white; border-color:var(--danger); }}
    button:focus-visible, input:focus-visible, textarea:focus-visible, select:focus-visible {{ outline:3px solid var(--focus); outline-offset:2px; }}
    .reviewer-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(190px,1fr)); gap:12px; }}
    input[type="text"], input[type="date"], textarea {{ width:100%; margin-top:6px; padding:9px; border:1px solid var(--line); border-radius:6px; font:inherit; background:#fff; }}
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
    @media (max-width:920px) {{ .grid {{ grid-template-columns:1fr; }} .sidebar {{ position:static; }} dl {{ grid-template-columns:1fr; }} }}
    @media print {{ .toolbar, .reviewer, fieldset, .notes {{ display:none; }} body {{ background:white; }} .grid {{ display:block; }} .example-card {{ break-inside:avoid; margin-bottom:12px; }} .sidebar {{ position:static; }} }}
  </style>
</head>
<body>
  <header>
    <h1>PROD-084 Guided Option Selection Rewrite</h1>
    <p class="subhead">Review rewritten live-call examples. These use placeholder plan facts and sparse discourse markers so you can judge whether the agent sounds human or still scripted.</p>
  </header>
  <main>
    <section class="panel">
      <div class="metrics">
        <div class="metric"><span>Review item</span><strong>rewritten examples</strong></div>
        <div class="metric"><span>Runtime patch</span><strong class="blocked">blocked</strong></div>
        <div class="metric"><span>Examples</span><strong>{summary['review_example_count']}</strong></div>
        <div class="metric"><span>Next</span><strong>review import</strong></div>
      </div>
    </section>
    <div class="grid">
      <section>
        <section class="reviewer">
          <h2>Decision</h2>
          <p class="note">Approval here only allows a later policy probe. It does not promote runtime wording.</p>
          <div class="reviewer-grid">
            <label>Name or initials<input id="reviewerName" type="text"></label>
            <label>Date<input id="reviewDate" type="date"></label>
            <label>Overall decision
              <select id="overallDecision">
                <option value="">Select</option>
                <option value="approve_rewrite_for_policy_probe">Approve rewrite for policy probe</option>
                <option value="needs_rewrite">Needs rewrite</option>
                <option value="keep_deferred">Keep deferred</option>
              </select>
            </label>
          </div>
          <label>Overall notes<textarea id="overallNotes"></textarea></label>
        </section>
        <section class="toolbar">
          <button class="primary" onclick="setAll('approve_rewrite_for_policy_probe')">Approve rewrite for policy probe</button>
          <button class="warn" onclick="setAll('needs_rewrite')">Needs rewrite</button>
          <button onclick="setAll('keep_deferred')">Keep deferred</button>
          <button onclick="saveProgress()">Save in browser</button>
          <button onclick="loadProgress()">Load saved</button>
          <button onclick="exportJson()">Export JSON</button>
          <label class="file-label">Import JSON<input id="jsonImportFile" type="file" accept="application/json" onchange="importJsonFile(event)" hidden></label>
          <button onclick="clearEntries()">Clear</button>
        </section>
        <section class="examples">
          {cards}
        </section>
      </section>
      <aside class="sidebar">
        <section class="panel">
          <h2>Review-Only Plan Fixture</h2>
          <table>
            <thead><tr><th>Plan</th><th>Features</th><th>Fit</th></tr></thead>
            <tbody>{plan_rows}</tbody>
          </table>
        </section>
        <section class="panel">
          <h2>Boundaries</h2>
          <p>Production runtime promotion allowed: false.</p>
          <p>No runtime patch, classifier change, retrieval, provider call, private data, voice playback, payment collection, or contract signing is approved here.</p>
        </section>
      </aside>
    </div>
  </main>
  <script>
    const reviewPayload = {packet_json};
    const reviewTemplate = {template_json};
    const storageKey = 'prod084GuidedOptionRewriteReview';

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
      a.download = 'prod_084_guided_option_rewrite_review.json';
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
    marker = item["marker"] if item["uses_discourse_marker"] else "none"
    return f"""
      <article class="example-card" data-example="{html.escape(item['example_id'])}">
        <div class="card-top">
          <span>Example {index}</span>
          <span class="tag">marker: {html.escape(marker)}</span>
        </div>
        <h2>{html.escape(item['title'])}</h2>
        <dl>
          <dt>Customer turn</dt><dd>{html.escape(item['customer_turn'])}</dd>
          <dt>Review focus</dt><dd>{html.escape(item['review_focus'])}</dd>
          <dt>Word count</dt><dd>{item['word_count']}</dd>
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
    source_result, rewrite, plan_facts, payment, naturalness = load_source()
    source_validator = run_source_validator()
    packet = build_review_packet(rewrite, payment, naturalness)
    template = build_review_state_template(packet)
    naturalness_audit = build_naturalness_audit(packet)
    evidence = build_evidence(source_result, rewrite, plan_facts, payment, naturalness, source_validator)
    summary = summarize(packet, naturalness_audit, source_validator)
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
    write_json(OUT_DIR / "rewritten_guided_option_review_packet.json", packet)
    write_json(OUT_DIR / "review_state_template.json", template)
    write_json(OUT_DIR / "review_only_plan_feature_fixture.json", PLAN_FIXTURE)
    write_json(OUT_DIR / "spoken_naturalness_audit.json", naturalness_audit)
    write_json(OUT_DIR / "evidence_summary.json", evidence)
    write_text(OUT_DIR / "report.md", render_report(summary, packet, PLAN_FIXTURE, naturalness_audit))
    write_text(REVIEW_HTML, render_review_html(packet, template, PLAN_FIXTURE, summary))
    write_json(OUT_DIR / "result.json", result)
    print(json.dumps({"checkpoint_id": CHECKPOINT_ID, "validation": result["validation"], "summary": summary}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
