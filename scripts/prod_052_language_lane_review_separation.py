#!/usr/bin/env python3
from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-052-language-lane-review-separation"
CHECKPOINT_NAME = "Language Lane Review Separation"
SOURCE_CHECKPOINT_ID = "PROD-051-safe-call-control-runtime-update"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
SOURCE_DIR = ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID

SOURCE_FILES = {
    "source_result": SOURCE_DIR / "result.json",
    "runtime_results": SOURCE_DIR / "runtime_update_results.json",
    "naturalness_audit": SOURCE_DIR / "naturalness_audit_results.json",
}

BOUNDARY_FLAGS = {
    "retrieval_enabled": False,
    "provider_calls_made": False,
    "llm_used": False,
    "private_data_read": False,
    "voice_playback_unblocked": False,
    "public_demo_polish_unblocked": False,
    "payment_collection_allowed": False,
    "contract_signing_allowed": False,
    "production_runtime_promotion_allowed": False,
}


POLICY_RULES = [
    {
        "rule_id": "answer_customer_move_first",
        "name": "Answer or acknowledge the customer move before continuing.",
    },
    {
        "rule_id": "optional_low_pressure_continuation",
        "name": "Frame continuation as optional help, not pressure.",
    },
    {
        "rule_id": "no_terminal_closing_phrase",
        "name": "Do not use hang-up wording when the call should continue.",
    },
    {
        "rule_id": "no_internal_jargon",
        "name": "Do not expose campaign, approval, routing, or logging terms to the customer.",
    },
    {
        "rule_id": "spoken_sentence_shape",
        "name": "Keep spoken turns short, sentence-bounded, and not overloaded.",
    },
    {
        "rule_id": "customer_move_fit",
        "name": "Tie the continuation to the customer's actual reason for hesitating.",
    },
    {
        "rule_id": "language_boundary",
        "name": "Keep response language consistent and do not mix English/German fragments awkwardly.",
    },
    {
        "rule_id": "no_pressure_payment_contract_or_unsupported_claim",
        "name": "Do not create naturalness through pressure, payment handling, contract signing, or unsupported claims.",
    },
]

LEGACY_MIXED_SURFACES = [
    {
        "checkpoint_id": "PROD-046-core-sales-policy-human-review",
        "path": "research/experiments/generated/PROD-046-core-sales-policy-human-review/prod_046_review.html",
        "language_mix": "english_and_german",
        "current_acceptance_surface": False,
        "separation_action": "historical_evidence_only",
        "note": "Historical internal product-review evidence; not the current exact spoken phrase acceptance page.",
    },
    {
        "checkpoint_id": "PROD-049-safe-end-call-bridge-continue-review",
        "path": "research/experiments/generated/PROD-049-safe-end-call-bridge-continue-review/prod_049_review.html",
        "language_mix": "english_and_german",
        "current_acceptance_surface": False,
        "separation_action": "historical_evidence_only",
        "note": "Historical candidate-selection evidence; not an active phrase acceptance page.",
    },
    {
        "checkpoint_id": "PROD-050-safe-call-control-softening-regression",
        "path": "research/experiments/generated/PROD-050-safe-call-control-softening-regression/prod_050_review.html",
        "language_mix": "english_and_german",
        "current_acceptance_surface": False,
        "separation_action": "historical_evidence_only",
        "note": "Historical proposed-softening evidence; exact phrase review is superseded by PROD-052.",
    },
    {
        "checkpoint_id": "PROD-051-safe-call-control-runtime-update",
        "path": "research/experiments/generated/PROD-051-safe-call-control-runtime-update/prod_051_review.html",
        "language_mix": "english_and_german",
        "current_acceptance_surface": False,
        "separation_action": "superseded_by_prod_052",
        "note": "Mixed source review surface. Use PROD-052 for separated English review and German pending lanes.",
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


def source_statuses() -> dict[str, bool]:
    return {key: path.exists() for key, path in SOURCE_FILES.items()} | {
        "source_result_passed": read_json(SOURCE_FILES["source_result"]).get("validation", {}).get("passed") is True
        if SOURCE_FILES["source_result"].exists()
        else False
    }


def runtime_items() -> list[dict[str, Any]]:
    return read_json(SOURCE_FILES["runtime_results"])["items"]


def naturalness_by_id() -> dict[str, dict[str, Any]]:
    return {item["case_id"]: item for item in read_json(SOURCE_FILES["naturalness_audit"])["items"]}


def build_english_item(item: dict[str, Any], audit: dict[str, Any]) -> dict[str, Any]:
    decision = item["live_runtime_decision"]
    return {
        "case_id": item["case_id"],
        "language": "en",
        "sales_difficulty": item["sales_difficulty"],
        "customer_utterance": item["customer_utterance"],
        "agent_response": decision["agent_response"],
        "call_control": decision["call_control"],
        "next_action": decision["next_action"],
        "spoken_phrase_review_lane": "english_owner_review",
        "review_status": "ready_for_tarik_english_review",
        "exact_phrase_acceptance_allowed": True,
        "requires_tarik_review": True,
        "requires_native_german_review": False,
        "policy_level_only": False,
        "source_policy_score": audit["score"],
        "source_policy_checks_passed": audit["passed"],
    }


def build_german_item(item: dict[str, Any], audit: dict[str, Any]) -> dict[str, Any]:
    decision = item["live_runtime_decision"]
    return {
        "case_id": item["case_id"],
        "language": "de",
        "sales_difficulty": item["sales_difficulty"],
        "customer_utterance": item["customer_utterance"],
        "agent_response": decision["agent_response"],
        "call_control": decision["call_control"],
        "next_action": decision["next_action"],
        "spoken_phrase_review_lane": "german_pending_native_or_source_backed_review",
        "review_status": "pending_native_or_source_backed_review",
        "exact_phrase_acceptance_allowed": False,
        "requires_tarik_review": False,
        "requires_native_german_review": True,
        "policy_level_only": True,
        "source_policy_score": audit["score"],
        "source_policy_checks_passed": audit["passed"],
        "acceptance_note": "Use this only as policy-shape evidence until native German or source-backed wording review exists.",
    }


def build_language_lanes(items: list[dict[str, Any]], audits: dict[str, dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    english: list[dict[str, Any]] = []
    german: list[dict[str, Any]] = []
    for item in items:
        audit = audits[item["case_id"]]
        if item["language"] == "en":
            english.append(build_english_item(item, audit))
        elif item["language"] == "de":
            german.append(build_german_item(item, audit))
    return english, german


def build_policy_rules(audits: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    check_name_by_rule = {
        "answer_customer_move_first": "direct_answer_or_acknowledgement",
        "optional_low_pressure_continuation": "optional_low_pressure_continuation",
        "no_terminal_closing_phrase": "no_terminal_closing_phrase",
        "no_internal_jargon": "no_internal_jargon",
        "spoken_sentence_shape": "spoken_sentence_shape",
        "customer_move_fit": "customer_move_fit",
        "language_boundary": "language_specific_naturalness",
        "no_pressure_payment_contract_or_unsupported_claim": "no_pressure_payment_contract_or_unsupported_claim",
    }
    rules = []
    for rule in POLICY_RULES:
        check_name = check_name_by_rule[rule["rule_id"]]
        passed = all(item["checks"][check_name]["passed"] is True for item in audits.values())
        rules.append(
            {
                **rule,
                "scope": "style_or_safety_policy",
                "applies_to_languages": ["en", "de"],
                "exact_phrase_acceptance_rule": "language_specific",
                "passed": passed,
            }
        )
    return rules


def build_summary(
    english: list[dict[str, Any]],
    german: list[dict[str, Any]],
    rules: list[dict[str, Any]],
    legacy_surfaces: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "source_result_statuses": source_statuses(),
        "source_case_count": len(english) + len(german),
        "english_spoken_review_case_count": len(english),
        "english_exact_phrase_review_allowed_count": sum(1 for item in english if item["exact_phrase_acceptance_allowed"]),
        "german_pending_review_case_count": len(german),
        "german_exact_phrase_acceptance_allowed_count": sum(1 for item in german if item["exact_phrase_acceptance_allowed"]),
        "german_pending_native_or_source_backed_review_count": sum(1 for item in german if item["requires_native_german_review"]),
        "multilingual_policy_rule_count": len(rules),
        "multilingual_policy_rule_pass_count": sum(1 for item in rules if item["passed"]),
        "legacy_mixed_surface_count": len(legacy_surfaces),
        "legacy_mixed_surface_active_acceptance_count": sum(1 for item in legacy_surfaces if item["current_acceptance_surface"]),
        "cross_language_policy_reuse_allowed": True,
        "cross_language_exact_phrase_reuse_allowed": False,
        "english_focus_next": True,
        "english_review_scope_note": "This lane covers only the four English PROD-051 call-control update cases. Broader English spoken-response review and promotion status belong to later English expansion checkpoints.",
        "native_german_approval_claimed": False,
        "german_naturalness_claimed": False,
        "llm_judging_used": False,
        "runtime_behavior_changed": False,
        "response_text_behavior_changed": False,
        **BOUNDARY_FLAGS,
    }


def build_report(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"# {CHECKPOINT_NAME}",
            "",
            f"- Checkpoint id: `{CHECKPOINT_ID}`",
            f"- Source checkpoint: `{SOURCE_CHECKPOINT_ID}`",
            f"- English spoken review cases: `{summary['english_spoken_review_case_count']}`",
            f"- German pending review cases: `{summary['german_pending_review_case_count']}`",
            f"- Multilingual policy rules passing: `{summary['multilingual_policy_rule_pass_count']} / {summary['multilingual_policy_rule_count']}`",
            f"- Legacy mixed review surfaces inventoried: `{summary['legacy_mixed_surface_count']}`",
            f"- Runtime behavior changed: `{str(summary['runtime_behavior_changed']).lower()}`",
            f"- Provider calls made: `{str(summary['provider_calls_made']).lower()}`",
            "",
            "## Result",
            "",
            "`PROD-052` separates spoken-response acceptance by language. English exact responses are owner-review lane evidence for this runtime slice. German exact wording remains pending until native German or source-backed wording review exists.",
            "",
            "Shared naturalness constraints can be reused across English and German as style or safety policy. Exact phrase acceptance cannot be reused across languages.",
            "",
            "The English lane intentionally contains only the four English cases inherited from the PROD-051 call-control update. It is not the full English policy surface, and later promotion status belongs to the English expansion checkpoints.",
            "",
            "Older mixed English/German review files remain historical evidence unless a future checkpoint explicitly reopens them. Active exact phrase promotion should use separated language-lane evidence plus the later promotion checkpoint.",
            "",
        ]
    )


def html_rows(items: list[dict[str, Any]]) -> str:
    rows = []
    for item in items:
        rows.append(
            "<tr>"
            f"<td>{html.escape(item['case_id'])}</td>"
            f"<td>{html.escape(item['sales_difficulty'])}</td>"
            f"<td>{html.escape(item['customer_utterance'])}</td>"
            f"<td>{html.escape(item['agent_response'])}</td>"
            f"<td>{html.escape(item['review_status'])}</td>"
            f"<td>{str(item['exact_phrase_acceptance_allowed']).lower()}</td>"
            "</tr>"
        )
    return "".join(rows)


def build_html(english: list[dict[str, Any]], german: list[dict[str, Any]], summary: dict[str, Any]) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>PROD-052 Language Lane Review Separation</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 32px; line-height: 1.45; color: #1f2933; }}
    .banner {{ border: 1px solid #cbd5e1; background: #f8fafc; padding: 12px; margin: 12px 0 20px; }}
    table {{ border-collapse: collapse; width: 100%; margin: 16px 0 32px; }}
    th, td {{ border: 1px solid #cbd5e1; padding: 8px; text-align: left; vertical-align: top; }}
    th {{ background: #edf2f7; }}
  </style>
</head>
<body>
  <h1>PROD-052 Language Lane Review Separation</h1>
  <div class="banner">
    Runtime behavior changed: false. Response text behavior changed: false. Provider calls made: false.
  </div>
  <p>English exact spoken phrases are ready for Tarik review. German exact wording is separated and pending native German or source-backed wording review. Shared multilingual checks remain policy-level only.</p>
  <p>This English lane covers only the four English cases inherited from the PROD-051 call-control update. A broader English review should be opened as a separate checkpoint.</p>
  <p>English review cases: {summary['english_spoken_review_case_count']}. German pending cases: {summary['german_pending_review_case_count']}.</p>
  <h2>English Spoken Review Lane</h2>
  <table>
    <thead><tr><th>Case</th><th>Sales difficulty</th><th>Customer utterance</th><th>Agent response</th><th>Status</th><th>Exact phrase acceptance allowed</th></tr></thead>
    <tbody>{html_rows(english)}</tbody>
  </table>
  <h2>German Pending Review Lane</h2>
  <table>
    <thead><tr><th>Case</th><th>Sales difficulty</th><th>Customer utterance</th><th>Agent response</th><th>Status</th><th>Exact phrase acceptance allowed</th></tr></thead>
    <tbody>{html_rows(german)}</tbody>
  </table>
</body>
</html>
"""


def build_payload() -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    items = runtime_items()
    audits = naturalness_by_id()
    english, german = build_language_lanes(items, audits)
    rules = build_policy_rules(audits)
    legacy_surfaces = LEGACY_MIXED_SURFACES
    summary = build_summary(english, german, rules, legacy_surfaces)
    payload = {
        "checkpoint_id": CHECKPOINT_ID,
        "title": CHECKPOINT_NAME,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "validation": {
            "passed": summary["source_result_statuses"]["source_result_passed"]
            and summary["source_case_count"] == 22
            and summary["english_spoken_review_case_count"] == 4
            and summary["german_pending_review_case_count"] == 18
            and summary["german_exact_phrase_acceptance_allowed_count"] == 0
            and summary["multilingual_policy_rule_pass_count"] == summary["multilingual_policy_rule_count"],
        },
        "outputs": {
            "result": rel(OUT_DIR / "result.json"),
            "report": rel(OUT_DIR / "report.md"),
            "english_review": rel(OUT_DIR / "english_spoken_review_items.json"),
            "german_pending": rel(OUT_DIR / "german_pending_review_items.json"),
            "policy_rules": rel(OUT_DIR / "multilingual_policy_rules.json"),
            "legacy_surfaces": rel(OUT_DIR / "legacy_mixed_review_surfaces.json"),
            "review_html": rel(OUT_DIR / "prod_052_language_lane_review.html"),
        },
        "summary": summary,
    }
    return payload, english, german, rules, legacy_surfaces


def main() -> None:
    payload, english, german, rules, legacy_surfaces = build_payload()
    write_json(OUT_DIR / "english_spoken_review_items.json", {"checkpoint_id": CHECKPOINT_ID, "items": english})
    write_json(OUT_DIR / "german_pending_review_items.json", {"checkpoint_id": CHECKPOINT_ID, "items": german})
    write_json(OUT_DIR / "multilingual_policy_rules.json", {"checkpoint_id": CHECKPOINT_ID, "items": rules})
    write_json(OUT_DIR / "legacy_mixed_review_surfaces.json", {"checkpoint_id": CHECKPOINT_ID, "items": legacy_surfaces})
    write_text(OUT_DIR / "report.md", build_report(payload["summary"]))
    write_text(OUT_DIR / "prod_052_language_lane_review.html", build_html(english, german, payload["summary"]))
    write_json(OUT_DIR / "result.json", payload)
    print(json.dumps({"checkpoint_id": CHECKPOINT_ID, "validation": payload["validation"], "summary": payload["summary"]}, indent=2))


if __name__ == "__main__":
    main()
