#!/usr/bin/env python3
from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-053B-compact-english-psychology-layer-review"
CHECKPOINT_NAME = "Compact English Psychology Layer Review"
SOURCE_CHECKPOINT_ID = "PROD-053A-english-sales-psychology-deep-dive"
LANGUAGE_LANE_CHECKPOINT_ID = "PROD-052-language-lane-review-separation"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
SOURCE_DIR = ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID
LANGUAGE_LANE_DIR = ROOT / "research" / "experiments" / "generated" / LANGUAGE_LANE_CHECKPOINT_ID

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
    "payment_collection_allowed": False,
    "contract_signing_allowed": False,
    "production_runtime_promotion_allowed": False,
    "german_exact_phrase_promotion_allowed": False,
    "german_naturalness_claimed": False,
}

COMPACT_POLICY_RULES = [
    {
        "policy_rule_id": "en_response_001_answer_then_continue",
        "source_candidate_rule_ids": ["english_psych_001_listen_answer_then_continue"],
        "name": "Answer, then continue.",
        "language": "en",
        "runtime_instruction": "Use a tiny acknowledgement, answer the customer move, then offer one low-friction next step.",
        "blocked_shape": "Do not open a menu of facts, explanations, and options before answering the customer.",
        "deterministic": True,
        "runtime_cost": "low",
        "review_status": "accepted_for_prod_053c",
        "runtime_promoted": False,
    },
    {
        "policy_rule_id": "en_response_002_plain_relief",
        "source_candidate_rule_ids": ["english_psych_002_relief_without_policy_dump"],
        "name": "Keep relief plain.",
        "language": "en",
        "runtime_instruction": "When relief matters, say it briefly: no commitment today, take a look, let me know.",
        "blocked_shape": "Do not list every legal or commercial non-commitment as a policy dump.",
        "deterministic": True,
        "runtime_cost": "low",
        "review_status": "accepted_for_prod_053c",
        "runtime_promoted": False,
    },
    {
        "policy_rule_id": "en_response_003_mirror_only_for_repair",
        "source_candidate_rule_ids": ["english_psych_003_mirror_only_for_repair_or_discovery"],
        "name": "Mirror only for repair.",
        "language": "en",
        "runtime_instruction": "Use a short partial repeat only when it repairs ambiguity or invites useful detail.",
        "blocked_shape": "Do not repeat the customer's full category such as manager, spouse, boss, or partner in every answer.",
        "deterministic": True,
        "runtime_cost": "low",
        "review_status": "accepted_with_constraint_for_prod_053c",
        "runtime_promoted": False,
    },
    {
        "policy_rule_id": "en_response_004_one_small_decision",
        "source_candidate_rule_ids": ["english_psych_004_one_small_decision"],
        "name": "One small decision.",
        "language": "en",
        "runtime_instruction": "Offer or ask for one small next step per turn.",
        "blocked_shape": "Do not ask the buyer to process summary, pricing, terms, booking, and contract details in one turn.",
        "deterministic": True,
        "runtime_cost": "low",
        "review_status": "accepted_for_prod_053c",
        "runtime_promoted": False,
    },
    {
        "policy_rule_id": "en_response_005_friction_not_personality",
        "source_candidate_rule_ids": ["english_psych_005_diagnose_friction_not_personality"],
        "name": "Diagnose friction, not personality.",
        "language": "en",
        "runtime_instruction": "If hesitation is unclear, ask one small friction question about price, timing, authority, risk, or usefulness.",
        "blocked_shape": "Do not label hidden emotions or personality traits.",
        "deterministic": True,
        "runtime_cost": "low",
        "review_status": "accepted_with_constraint_for_prod_053c",
        "runtime_promoted": False,
    },
    {
        "policy_rule_id": "en_response_006_autonomy_visible",
        "source_candidate_rule_ids": ["english_psych_006_autonomy_visible"],
        "name": "Make autonomy visible.",
        "language": "en",
        "runtime_instruction": "Keep pause, review, decline, compare, or human handoff visible when the next step could feel like pressure.",
        "blocked_shape": "Do not turn a review step into a forced booking, hidden obligation, or scarcity close.",
        "deterministic": True,
        "runtime_cost": "low",
        "review_status": "accepted_with_constraint_for_prod_053c",
        "runtime_promoted": False,
    },
    {
        "policy_rule_id": "en_response_007_trust_gap_specific",
        "source_candidate_rule_ids": ["english_psych_007_trust_gap_specific"],
        "name": "Answer the specific trust gap.",
        "language": "en",
        "runtime_instruction": "For trust concerns, answer ability, interest, or honesty gaps with only the relevant verified path.",
        "blocked_shape": "Do not use generic reassurance, testimonials, or confidence as a universal trust answer.",
        "deterministic": True,
        "runtime_cost": "low",
        "review_status": "accepted_for_prod_053c",
        "runtime_promoted": False,
    },
    {
        "policy_rule_id": "en_response_008_stop_after_question",
        "source_candidate_rule_ids": ["english_psych_008_stop_after_question"],
        "name": "Ask, then stop.",
        "language": "en",
        "runtime_instruction": "If the turn asks a question, stop after the question.",
        "blocked_shape": "Do not ask a question and then continue explaining the answer options.",
        "deterministic": True,
        "runtime_cost": "low",
        "review_status": "accepted_for_prod_053c",
        "runtime_promoted": False,
    },
]

CANDIDATE_DECISION_OVERRIDES = {
    "english_psych_003_mirror_only_for_repair_or_discovery": {
        "decision": "accept_with_constraint",
        "constraint": "Use mirroring only for ambiguity repair or discovery. Do not echo stakeholder categories in normal answer turns.",
    },
    "english_psych_005_diagnose_friction_not_personality": {
        "decision": "accept_with_constraint",
        "constraint": "Use one narrow friction question only when the customer has not already given enough detail.",
    },
    "english_psych_006_autonomy_visible": {
        "decision": "accept_with_constraint",
        "constraint": "Autonomy language must not become terminal hang-up wording unless the customer is actually ending the call.",
    },
}

POLICY_SUGGESTIONS = {
    "price-first-direct": "The starter plan is 29 per user per month. I can send the exact terms in writing. No payment or commitment on this call.",
    "written-info-request": "Of course. I can tailor it to your main point, then send it over.",
    "stakeholder-review": "Of course. I can send it over. No commitment today. Take a look and let me know.",
    "partner-review": "Of course. I can send it over. No commitment today. Take a look and let me know.",
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def source_candidate_rules() -> list[dict[str, Any]]:
    return read_json(SOURCE_DIR / "compact_candidate_rules.json")["items"]


def source_deferred_tactics() -> list[dict[str, Any]]:
    return read_json(SOURCE_DIR / "rejected_or_deferred_tactics.json")["items"]


def source_english_items() -> list[dict[str, Any]]:
    return read_json(LANGUAGE_LANE_DIR / "english_spoken_review_items.json")["items"]


def build_candidate_review(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    items = []
    for candidate in candidates:
        override = CANDIDATE_DECISION_OVERRIDES.get(candidate["rule_id"], {})
        decision = override.get("decision", "accept")
        items.append(
            {
                "source_rule_id": candidate["rule_id"],
                "source_name": candidate["name"],
                "decision": decision,
                "constraint": override.get("constraint", ""),
                "prod_053c_use": "Use as a deterministic English response-shape rule, not as exact customer-facing wording.",
                "source_finding_ids": candidate["source_finding_ids"],
                "runtime_promoted": False,
                "exact_phrase_change_allowed": False,
            }
        )
    return items


def sentence_count(text: str) -> int:
    return sum(1 for chunk in text.replace("?", ".").replace("!", ".").split(".") if chunk.strip())


def audit_case(item: dict[str, Any]) -> dict[str, Any]:
    response = item["agent_response"]
    response_lower = response.lower()
    issues: list[str] = []
    if item["sales_difficulty"] in {"stakeholder-review", "partner-review"}:
        if any(token in response_lower for token in ["manager", "spouse", "boss", "partner"]):
            issues.append("customer_category_echo")
        if "commitment" not in response_lower:
            issues.append("relief_needs_commitment_wording")
    if sentence_count(response) > 3:
        issues.append("live_turn_too_long")
    if "?" in response and response.rstrip().endswith("?") is False:
        issues.append("continues_after_question")
    if "no decision or commitment required" in response_lower or "binding agreement" in response_lower:
        issues.append("policy_dump_relief")
    return {
        "case_id": item["case_id"],
        "language": "en",
        "sales_difficulty": item["sales_difficulty"],
        "customer_utterance": item["customer_utterance"],
        "current_agent_response": response,
        "policy_issues": issues,
        "policy_shape_suggestion": POLICY_SUGGESTIONS[item["sales_difficulty"]],
        "prod_053c_rewrite_decision": "rewrite_candidate" if issues else "carry_forward",
        "runtime_response_changed": False,
    }


def build_current_case_audit(english_items: list[dict[str, Any]]) -> dict[str, Any]:
    items = [audit_case(item) for item in english_items]
    return {
        "language": "en",
        "scope": "PROD-052 English items only; not the broader English response surface.",
        "items": items,
        "rewrite_candidate_count": sum(1 for item in items if item["prod_053c_rewrite_decision"] == "rewrite_candidate"),
        "runtime_behavior_changed": False,
        "response_text_behavior_changed": False,
    }


def build_deferred_tactics_review(tactics: list[dict[str, Any]]) -> list[dict[str, Any]]:
    items = []
    for tactic in tactics:
        items.append(
            {
                "source_tactic_id": tactic["tactic_id"],
                "name": tactic["name"],
                "source_decision": tactic["decision"],
                "prod_053b_decision": "keep_deferred" if tactic["decision"] == "defer" else "keep_rejected",
                "allowed_in_compact_policy": False,
                "reason": tactic["reason"],
            }
        )
    return items


def build_summary(
    candidates: list[dict[str, Any]],
    candidate_review: list[dict[str, Any]],
    case_audit: dict[str, Any],
    deferred_review: list[dict[str, Any]],
) -> dict[str, Any]:
    accepted = [item for item in candidate_review if item["decision"] in {"accept", "accept_with_constraint"}]
    return {
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "language_lane_checkpoint_id": LANGUAGE_LANE_CHECKPOINT_ID,
        "source_candidate_rule_count": len(candidates),
        "accepted_rule_count": len(accepted),
        "accepted_with_constraint_count": sum(1 for item in accepted if item["decision"] == "accept_with_constraint"),
        "compact_policy_rule_count": len(COMPACT_POLICY_RULES),
        "current_english_case_count": len(case_audit["items"]),
        "current_english_cases_requiring_prod_053c_rewrite": case_audit["rewrite_candidate_count"],
        "rejected_or_deferred_tactic_count": len(deferred_review),
        "rejected_or_deferred_tactic_kept_blocked_count": sum(
            1 for item in deferred_review if item["allowed_in_compact_policy"] is False
        ),
        "english_only_review": True,
        "prod_053c_ready": True,
        "prod_053c_scope": "Broader English spoken-response expansion, excluding already-approved items unless this audit flags them for rewrite.",
        **BOUNDARY_FLAGS,
    }


def render_report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        f"# {CHECKPOINT_NAME}",
        "",
        "`PROD-053B` reviews the `PROD-053A` candidate rules and compresses them into an English-only deterministic response-shape policy for `PROD-053C`.",
        "",
        "It makes no runtime behavior or response text change.",
        "",
        "## Summary",
        "",
        f"- Source candidate rules: `{summary['source_candidate_rule_count']}`",
        f"- Accepted rules: `{summary['accepted_rule_count']}`",
        f"- Accepted with constraints: `{summary['accepted_with_constraint_count']}`",
        f"- Compact policy rules: `{summary['compact_policy_rule_count']}`",
        f"- Current English cases audited: `{summary['current_english_case_count']}`",
        f"- Current English cases requiring PROD-053C rewrite: `{summary['current_english_cases_requiring_prod_053c_rewrite']}`",
        f"- Runtime behavior changed: `{summary['runtime_behavior_changed']}`",
        f"- Response text behavior changed: `{summary['response_text_behavior_changed']}`",
        f"- LLM used: `{summary['llm_used']}`",
        f"- Provider calls made: `{summary['provider_calls_made']}`",
        "",
        "## Compact English Policy",
        "",
    ]
    for rule in payload["compact_policy_rules"]:
        lines.extend(
            [
                f"### {rule['policy_rule_id']} - {rule['name']}",
                "",
                f"- Instruction: {rule['runtime_instruction']}",
                f"- Blocked shape: {rule['blocked_shape']}",
                f"- Review status: `{rule['review_status']}`",
                "",
            ]
        )
    lines.extend(["## Current English Case Audit", ""])
    for item in payload["current_english_case_policy_audit"]["items"]:
        lines.extend(
            [
                f"### {item['case_id']}",
                "",
                f"- Current response: {item['current_agent_response']}",
                f"- Policy issues: `{', '.join(item['policy_issues']) or 'none'}`",
                f"- PROD-053C decision: `{item['prod_053c_rewrite_decision']}`",
                f"- Policy-shape suggestion: {item['policy_shape_suggestion']}",
                "",
            ]
        )
    lines.extend(
        [
            "## Boundaries",
            "",
            "- English-only review.",
            "- No German exact phrase promotion.",
            "- No runtime behavior or response text changed.",
            "- No LLM judging, no LLM calls, no provider calls, no retrieval enablement, and no private data reads.",
            "- Rejected or deferred PROD-053A tactics remain blocked.",
            "",
        ]
    )
    return "\n".join(lines)


def render_html(payload: dict[str, Any]) -> str:
    rows = []
    for item in payload["current_english_case_policy_audit"]["items"]:
        rows.append(
            "<tr>"
            f"<td>{html.escape(item['case_id'])}</td>"
            f"<td>{html.escape(item['sales_difficulty'])}</td>"
            f"<td>{html.escape(item['current_agent_response'])}</td>"
            f"<td>{html.escape(', '.join(item['policy_issues']) or 'none')}</td>"
            f"<td>{html.escape(item['policy_shape_suggestion'])}</td>"
            f"<td>{html.escape(item['prod_053c_rewrite_decision'])}</td>"
            "</tr>"
        )
    rule_cards = []
    for rule in payload["compact_policy_rules"]:
        rule_cards.append(
            "<section class='rule'>"
            f"<h2>{html.escape(rule['policy_rule_id'])}</h2>"
            f"<p><strong>{html.escape(rule['name'])}</strong></p>"
            f"<p>{html.escape(rule['runtime_instruction'])}</p>"
            f"<p class='blocked'>Blocked: {html.escape(rule['blocked_shape'])}</p>"
            "</section>"
        )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>PROD-053B Compact English Policy Review</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 24px; color: #1f2933; background: #f7f8fa; }}
    h1 {{ margin-bottom: 4px; }}
    .meta {{ color: #52606d; margin-top: 0; }}
    .rules {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 12px; }}
    .rule {{ background: #fff; border: 1px solid #d9e2ec; border-radius: 8px; padding: 14px; }}
    .blocked {{ color: #7b341e; }}
    table {{ width: 100%; border-collapse: collapse; background: #fff; margin-top: 16px; }}
    th, td {{ border: 1px solid #d9e2ec; padding: 10px; vertical-align: top; }}
    th {{ background: #eef2f7; text-align: left; }}
  </style>
</head>
<body>
  <h1>PROD-053B Compact English Policy Review</h1>
  <p class="meta">English-only deterministic response-shape review. No runtime behavior, no German exact phrase promotion, no LLM, no provider call.</p>
  <div class="rules">{''.join(rule_cards)}</div>
  <h2>Current English Case Audit</h2>
  <table>
    <thead>
      <tr><th>Case</th><th>Difficulty</th><th>Current response</th><th>Policy issues</th><th>Policy-shape suggestion</th><th>Decision</th></tr>
    </thead>
    <tbody>{''.join(rows)}</tbody>
  </table>
</body>
</html>
"""


def build_payload() -> dict[str, Any]:
    candidates = source_candidate_rules()
    candidate_review = build_candidate_review(candidates)
    deferred_review = build_deferred_tactics_review(source_deferred_tactics())
    case_audit = build_current_case_audit(source_english_items())
    summary = build_summary(candidates, candidate_review, case_audit, deferred_review)
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "language_lane_checkpoint_id": LANGUAGE_LANE_CHECKPOINT_ID,
        "summary": summary,
        "candidate_rule_review": candidate_review,
        "compact_policy_rules": COMPACT_POLICY_RULES,
        "current_english_case_policy_audit": case_audit,
        "rejected_or_deferred_tactics_review": deferred_review,
        "validation": {
            "passed": True,
            "notes": [
                "Compact rules are accepted for PROD-053C review use only.",
                "No runtime policy import or response text change is made in PROD-053B.",
            ],
        },
    }


def main() -> None:
    payload = build_payload()
    write_json(OUT_DIR / "result.json", payload)
    write_json(OUT_DIR / "compact_english_policy_rules.json", {"items": payload["compact_policy_rules"]})
    write_json(OUT_DIR / "candidate_rule_review.json", {"items": payload["candidate_rule_review"]})
    write_json(OUT_DIR / "current_english_case_policy_audit.json", payload["current_english_case_policy_audit"])
    write_json(OUT_DIR / "rejected_or_deferred_tactics_review.json", {"items": payload["rejected_or_deferred_tactics_review"]})
    write_text(OUT_DIR / "report.md", render_report(payload))
    write_text(OUT_DIR / "prod_053b_compact_english_policy_review.html", render_html(payload))
    print(json.dumps(payload["summary"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
