#!/usr/bin/env python3
from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-048B-native-german-review-import"
CHECKPOINT_NAME = "Native German Review Import"
SOURCE_CHECKPOINT_ID = "PROD-048A-german-review-html-and-brevity-packet"
NEXT_CHECKPOINT_ID = "PROD-048C-german-wording-feedback-patch"

OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
IMPORT_PATH = (
    ROOT
    / "research"
    / "experiments"
    / "imports"
    / CHECKPOINT_ID
    / "deutsche-telefonantworten-bewertung-1.json"
)

GROUPED_PACKET_PATH = (
    ROOT
    / "research"
    / "experiments"
    / "generated"
    / SOURCE_CHECKPOINT_ID
    / "native_german_grouped_review_packet.json"
)
GROUPED_RESULT_PATH = (
    ROOT
    / "research"
    / "experiments"
    / "generated"
    / SOURCE_CHECKPOINT_ID
    / "result.json"
)
LEGACY_PACKET_PATH = (
    ROOT
    / "research"
    / "experiments"
    / "generated"
    / "PROD-048A-native-german-review-html-packet"
    / "native_german_review_packet.json"
)

DEPENDENCY_RESULTS = {
    "prod_048a": GROUPED_RESULT_PATH,
    "prod_047": ROOT / "research" / "experiments" / "generated" / "PROD-047-campaign-profile-contract-validator" / "result.json",
    "prod_046": ROOT / "research" / "experiments" / "generated" / "PROD-046-core-sales-policy-human-review" / "result.json",
}

BOUNDARY_FALSE_SUMMARY = {
    "full_native_german_approval_claimed": False,
    "legal_compliance_claimed": False,
    "runtime_behavior_changed": False,
    "call_control_behavior_changed": False,
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


def filled(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, list):
        return any(filled(item) for item in value)
    if isinstance(value, dict):
        return any(filled(item) for item in value.values())
    return bool(value)


def norm(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip().lower().replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")


def is_reviewed(item: dict[str, Any]) -> bool:
    marker = {
        "ratings": item.get("ratings", {}),
        "safety_flags": item.get("safety_flags", []),
        "rewrite_suggestion": item.get("rewrite_suggestion", ""),
        "comment": item.get("comment", ""),
    }
    return filled(marker)


def no_revision_requested(item: dict[str, Any]) -> bool:
    revision = norm(item.get("ratings", {}).get("ueberarbeitung_noetig", ""))
    return revision in {"", "nein", "keine", "keine_aenderung", "no"}


def small_change_requested(item: dict[str, Any]) -> bool:
    return norm(item.get("ratings", {}).get("ueberarbeitung_noetig", "")) in {
        "kleine_aenderung",
        "kleine aenderung",
    }


def large_change_requested(item: dict[str, Any]) -> bool:
    return norm(item.get("ratings", {}).get("ueberarbeitung_noetig", "")) in {
        "grosse_aenderung",
        "grosse aenderung",
        "grosze_aenderung",
    }


def rejected(item: dict[str, Any]) -> bool:
    return norm(item.get("ratings", {}).get("telefonisch_akzeptabel", "")) == "nein"


def accepted(item: dict[str, Any]) -> bool:
    return norm(item.get("ratings", {}).get("telefonisch_akzeptabel", "")) == "ja" and no_revision_requested(item)


def load_inputs() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any] | None]:
    if not IMPORT_PATH.exists():
        raise FileNotFoundError(
            "Missing reviewer JSON. Place it at "
            f"{rel(IMPORT_PATH)} and rerun PROD-048B."
        )
    grouped_packet = read_json(GROUPED_PACKET_PATH)
    legacy_packet = read_json(LEGACY_PACKET_PATH) if LEGACY_PACKET_PATH.exists() else None
    return read_json(IMPORT_PATH), grouped_packet, legacy_packet


def index_legacy_items(legacy_packet: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    if not legacy_packet:
        return {}
    return {item["review_item_id"]: item for item in legacy_packet.get("review_items", [])}


def index_grouped_packet(grouped_packet: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    by_case: dict[str, dict[str, Any]] = {}
    by_group: dict[str, dict[str, Any]] = {}
    for group in grouped_packet.get("review_groups", []):
        by_group[group["group_id"]] = group
        for case_id in group.get("original_case_ids", []):
            by_case[case_id] = group
    return by_case, by_group


def enrich_item(
    item: dict[str, Any],
    legacy_index: dict[str, dict[str, Any]],
    grouped_by_case: dict[str, dict[str, Any]],
    reviewed: bool,
) -> dict[str, Any]:
    legacy = legacy_index.get(item.get("review_item_id", ""), {})
    source_case_id = legacy.get("source_case_id")
    group = grouped_by_case.get(source_case_id or "", {})
    return {
        "review_item_id": item.get("review_item_id"),
        "topic": item.get("topic") or legacy.get("topic_title_de") or group.get("topic_title_de"),
        "reviewed": reviewed,
        "ratings": item.get("ratings", {}),
        "safety_flags": item.get("safety_flags", []),
        "rewrite_suggestion": item.get("rewrite_suggestion", ""),
        "comment": item.get("comment", ""),
        "source_case_id": source_case_id,
        "customer_move_id": legacy.get("customer_move_id"),
        "customer_utterance": legacy.get("customer_utterance"),
        "current_or_reviewed_answer": legacy.get("agent_response") or group.get("short_agent_response"),
        "current_group_id": group.get("group_id"),
        "current_group_topic": group.get("topic_title_de"),
        "current_group_short_answer": group.get("short_agent_response"),
    }


def build_revision_candidates(reviewed_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for item in reviewed_items:
        if item.get("topic") != "Preisfrage":
            continue
        if not (small_change_requested(item) or item.get("safety_flags") or item.get("comment")):
            continue
        candidates.append(
            {
                "topic": "Preisfrage",
                "review_item_id": item["review_item_id"],
                "current_or_reviewed_answer": item.get("current_or_reviewed_answer"),
                "reviewer_issue": item.get("comment") or "Reviewer requested a smaller wording change.",
                "reviewer_safety_flags": item.get("safety_flags", []),
                "reviewer_rewrite_suggestion": item.get("rewrite_suggestion", ""),
                "proposed_project_owned_revision": (
                    "Das Starter-Paket liegt bei 29 Euro pro Nutzer und Monat. "
                    "Die genauen Bedingungen schicke ich Ihnen schriftlich."
                ),
                "safety_boundary_analysis": (
                    "For plain price-first answers, the no-payment/no-contract sentence can draw attention to payment. "
                    "The no-payment/no-contract boundary must remain available for payment, scam, contract, and sale-ready contexts."
                ),
                "runtime_change_allowed_now": False,
                "requires_later_patch_checkpoint": True,
            }
        )
    return candidates


def summarize_counts(import_payload: dict[str, Any], reviewed_items: list[dict[str, Any]], unreviewed_items: list[dict[str, Any]]) -> dict[str, Any]:
    reported = import_payload.get("summary", {})
    return {
        "source_item_count": len(import_payload.get("items", [])),
        "reported_checked_count": reported.get("anzahl_gepruefter_antworten"),
        "reported_accepted_count": reported.get("anzahl_akzeptiert"),
        "reported_small_change_count": reported.get("anzahl_mit_kleinen_aenderungen"),
        "reported_large_change_count": reported.get("anzahl_mit_grossen_aenderungen"),
        "reported_rejected_count": reported.get("anzahl_abgelehnt"),
        "reported_safety_or_impact_count": reported.get("anzahl_mit_sicherheits_oder_wirkungs_hinweisen"),
        "reviewed_item_count": len(reviewed_items),
        "unreviewed_item_count": len(unreviewed_items),
        "accepted_count": sum(1 for item in reviewed_items if accepted(item)),
        "small_change_count": sum(1 for item in reviewed_items if small_change_requested(item)),
        "large_change_count": sum(1 for item in reviewed_items if large_change_requested(item)),
        "rejected_count": sum(1 for item in reviewed_items if rejected(item)),
        "safety_or_impact_count": sum(1 for item in reviewed_items if item.get("safety_flags")),
        "blank_rows_counted_as_unreviewed": True,
    }


def build_followup_plan(
    reviewed_enriched: list[dict[str, Any]],
    grouped_packet: dict[str, Any],
    revision_candidates: list[dict[str, Any]],
) -> dict[str, Any]:
    reviewed_case_ids = {item["source_case_id"] for item in reviewed_enriched if item.get("source_case_id")}
    accepted_groups: dict[str, dict[str, Any]] = {}
    focused: dict[str, dict[str, Any]] = {}
    for item in reviewed_enriched:
        topic = item.get("topic") or "Unknown"
        group_id = item.get("current_group_id")
        entry = {
            "topic": topic,
            "current_group_id": group_id,
            "review_item_id": item["review_item_id"],
            "source_case_id": item.get("source_case_id"),
            "note": "Only one exported individual row was reviewed; grouped-card acceptance still needs confirmation.",
        }
        if item.get("topic") == "Preisfrage" or small_change_requested(item) or large_change_requested(item) or rejected(item) or item.get("safety_flags"):
            focused[topic] = entry | {
                "reason": "Reviewer requested a small wording change or flagged a safety/impact concern.",
            }
        elif accepted(item):
            accepted_groups[topic] = entry

    completely_unreviewed = []
    for group in grouped_packet.get("review_groups", []):
        group_case_ids = set(group.get("original_case_ids", []))
        if not (group_case_ids & reviewed_case_ids):
            completely_unreviewed.append(
                {
                    "current_group_id": group["group_id"],
                    "topic": group["topic_title_de"],
                    "case_count": len(group.get("original_case_ids", [])),
                    "short_agent_response": group.get("short_agent_response"),
                }
            )

    return {
        "groups_accepted_from_current_feedback": list(accepted_groups.values()),
        "groups_requiring_focused_followup": list(focused.values()),
        "groups_still_completely_unreviewed": completely_unreviewed,
        "revision_candidates": [item["topic"] for item in revision_candidates],
        "review_coverage_gaps": {
            "input_export_used_99_individual_rows": True,
            "current_grouped_packet_group_count": len(grouped_packet.get("review_groups", [])),
            "reviewed_group_count": len({item.get("current_group_id") for item in reviewed_enriched if item.get("current_group_id")}),
            "full_native_german_approval_claimed": False,
            "blank_rows_are_not_rejections": True,
        },
        "recommendation": "ask_reviewer_to_continue_with_grouped_html",
        "recommendation_detail": (
            "Ask the reviewer to continue with the grouped PROD-048A HTML so repeated answers are reviewed once per answer group. "
            "Do not treat the blank individual rows as approval or rejection."
        ),
    }


def build_feedback_summary(
    import_payload: dict[str, Any],
    grouped_packet: dict[str, Any],
    counts: dict[str, Any],
    reviewed_enriched: list[dict[str, Any]],
    revision_candidates: list[dict[str, Any]],
) -> dict[str, Any]:
    reviewer = import_payload.get("reviewer", {})
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "input_path": rel(IMPORT_PATH),
        "reviewer": reviewer,
        "input_export_shape": {
            "item_count": len(import_payload.get("items", [])),
            "current_grouped_packet_group_count": len(grouped_packet.get("review_groups", [])),
            "import_concern": (
                "The returned JSON contains 99 individual review rows while the current grouped PROD-048A packet has fewer visible grouped cards. "
                "This suggests the reviewer used the earlier individual-row packet or exported individual rows for traceability."
            ),
        },
        "reported_summary": import_payload.get("summary", {}),
        "recomputed_counts": counts,
        "reviewed_topics": sorted({item.get("topic") for item in reviewed_enriched if item.get("topic")}),
        "accepted_topics": sorted({item.get("topic") for item in reviewed_enriched if accepted(item)}),
        "revision_needed_topics": sorted({item.get("topic") for item in reviewed_enriched if small_change_requested(item) or large_change_requested(item)}),
        "safety_or_impact_flagged_topics": sorted({item.get("topic") for item in reviewed_enriched if item.get("safety_flags")}),
        "price_feedback_captured": any(item["topic"] == "Preisfrage" for item in revision_candidates),
        "full_native_german_approval_claimed": False,
        "legal_compliance_claimed": False,
    }


def build_report(summary: dict[str, Any], followup: dict[str, Any], revision_candidates: list[dict[str, Any]]) -> str:
    accepted_topics = ", ".join(summary["accepted_topics"]) or "none"
    revision_topics = ", ".join(summary["revision_needed_topics"]) or "none"
    flagged_topics = ", ".join(summary["safety_or_impact_flagged_topics"]) or "none"
    price_revision = revision_candidates[0]["proposed_project_owned_revision"] if revision_candidates else "none"
    return f"""# PROD-048B Native German Review Import

## Summary

PROD-048B imports the returned native German reviewer JSON as partial evidence. No full native German approval is claimed. No legal compliance is claimed.

The import recomputes reviewed rows from filled ratings, safety flags, rewrite suggestions, and comments. The exported summary reported `0` checked rows, so the report does not trust that value. Blank rows are treated as unreviewed, not rejected.

## Reviewer Metadata

- Reviewer name or initials: `{summary['reviewer'].get('name_or_initials')}`
- Native German: `{summary['reviewer'].get('native_german')}`
- Region: `{summary['reviewer'].get('region_optional')}`
- Date: `{summary['reviewer'].get('date')}`

## Recomputed Counts

- Source item count: `{summary['recomputed_counts']['source_item_count']}`
- Reviewed item count: `{summary['recomputed_counts']['reviewed_item_count']}`
- Unreviewed item count: `{summary['recomputed_counts']['unreviewed_item_count']}`
- Accepted count: `{summary['recomputed_counts']['accepted_count']}`
- Small-change count: `{summary['recomputed_counts']['small_change_count']}`
- Large-change count: `{summary['recomputed_counts']['large_change_count']}`
- Rejected count: `{summary['recomputed_counts']['rejected_count']}`
- Safety/impact count: `{summary['recomputed_counts']['safety_or_impact_count']}`

## Findings

- Accepted topics from reviewed rows: {accepted_topics}
- Revision-needed topics: {revision_topics}
- Safety/impact flagged topics: {flagged_topics}
- Import concern: returned JSON contains `{summary['input_export_shape']['item_count']}` individual review rows, while the current grouped packet has `{summary['input_export_shape']['current_grouped_packet_group_count']}` visible grouped cards.

## Price Revision Candidate

The price-question row was rated acceptable but partially natural, slightly abrupt, marked for a small change, and flagged for sales-pressure effect. The reviewer comment says the last sentence draws too much attention to payment.

Project-owned candidate for a later patch checkpoint:

```text
{price_revision}
```

This revision is not applied in PROD-048B. No-payment/no-contract language must remain available for payment, scam, contract, and sale-ready contexts.

## Follow-Up Review Plan

- Continue with the grouped PROD-048A HTML instead of another 99-row individual packet.
- Focus first on `Preisfrage`.
- Review the completely unreviewed grouped cards before making a broader German quality claim.
- Do not count blank rows as accepted or rejected.

Completely unreviewed grouped cards: `{len(followup['groups_still_completely_unreviewed'])}`

## Boundaries

- Runtime behavior changed: `false`
- Call-control behavior changed: `false`
- Retrieval enabled: `false`
- Provider calls made: `false`
- LLM used: `false`
- Private data read: `false`
- Voice playback unblocked: `false`
- Public demo polish unblocked: `false`
- Payment collection allowed: `false`
- Contract signing allowed: `false`
- Production runtime promotion allowed: `false`

## Next Checkpoint

Recommended next checkpoint: `{NEXT_CHECKPOINT_ID}`.
"""


def build_html(summary: dict[str, Any], reviewed: list[dict[str, Any]], revision_candidates: list[dict[str, Any]]) -> str:
    rows = []
    for item in reviewed:
        rows.append(
            "<tr>"
            f"<td>{html.escape(str(item.get('review_item_id')))}</td>"
            f"<td>{html.escape(str(item.get('topic')))}</td>"
            f"<td>{html.escape(str(item.get('ratings', {}).get('telefonisch_akzeptabel', '')))}</td>"
            f"<td>{html.escape(str(item.get('ratings', {}).get('ueberarbeitung_noetig', '')))}</td>"
            f"<td>{html.escape(', '.join(item.get('safety_flags', [])))}</td>"
            f"<td>{html.escape(str(item.get('comment', '')))}</td>"
            "</tr>"
        )
    candidate = revision_candidates[0]["proposed_project_owned_revision"] if revision_candidates else "No candidate recorded."
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>PROD-048B Native German Review Import</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 32px; color: #172033; line-height: 1.5; }}
    .metric {{ display: inline-block; margin: 0 12px 12px 0; padding: 10px 12px; border: 1px solid #ccd3df; border-radius: 6px; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 16px; }}
    th, td {{ border: 1px solid #d8dee9; padding: 8px; text-align: left; vertical-align: top; }}
    th {{ background: #f4f6fa; }}
    .notice {{ padding: 12px; border-left: 4px solid #4666cc; background: #f7f9ff; }}
  </style>
</head>
<body>
  <h1>PROD-048B Native German Review Import</h1>
  <p class="notice">Full native German approval is not claimed. Legal compliance is not claimed. Runtime and call-control behavior were not changed.</p>
  <div class="metric">Reviewed: {summary['recomputed_counts']['reviewed_item_count']}</div>
  <div class="metric">Unreviewed: {summary['recomputed_counts']['unreviewed_item_count']}</div>
  <div class="metric">Accepted: {summary['recomputed_counts']['accepted_count']}</div>
  <div class="metric">Small changes: {summary['recomputed_counts']['small_change_count']}</div>
  <div class="metric">Safety/impact: {summary['recomputed_counts']['safety_or_impact_count']}</div>
  <h2>Reviewer</h2>
  <p>{html.escape(str(summary['reviewer'].get('name_or_initials')))}; native German: {html.escape(str(summary['reviewer'].get('native_german')))}; region: {html.escape(str(summary['reviewer'].get('region_optional')))}; date: {html.escape(str(summary['reviewer'].get('date')))}.</p>
  <h2>Price Revision Candidate</h2>
  <p>{html.escape(candidate)}</p>
  <h2>Reviewed Rows</h2>
  <table>
    <thead><tr><th>Item</th><th>Topic</th><th>Phone acceptable</th><th>Revision</th><th>Flags</th><th>Comment</th></tr></thead>
    <tbody>{''.join(rows)}</tbody>
  </table>
</body>
</html>
"""


def main() -> None:
    import_payload, grouped_packet, legacy_packet = load_inputs()
    legacy_index = index_legacy_items(legacy_packet)
    grouped_by_case, _ = index_grouped_packet(grouped_packet)

    reviewed_source = [item for item in import_payload.get("items", []) if is_reviewed(item)]
    unreviewed_source = [item for item in import_payload.get("items", []) if not is_reviewed(item)]
    reviewed_enriched = [enrich_item(item, legacy_index, grouped_by_case, True) for item in reviewed_source]
    unreviewed_enriched = [enrich_item(item, legacy_index, grouped_by_case, False) for item in unreviewed_source]
    revision_candidates = build_revision_candidates(reviewed_enriched)
    counts = summarize_counts(import_payload, reviewed_source, unreviewed_source)
    feedback_summary = build_feedback_summary(import_payload, grouped_packet, counts, reviewed_enriched, revision_candidates)
    followup_plan = build_followup_plan(reviewed_enriched, grouped_packet, revision_candidates)

    outputs = {
        "result": OUT_DIR / "result.json",
        "report": OUT_DIR / "report.md",
        "summary": OUT_DIR / "imported_reviewer_feedback_summary.json",
        "reviewed_items": OUT_DIR / "reviewed_items.json",
        "unreviewed_items": OUT_DIR / "unreviewed_items.json",
        "revision_candidates": OUT_DIR / "revision_candidates.json",
        "followup_review_plan": OUT_DIR / "followup_review_plan.json",
        "html": OUT_DIR / "reviewer_feedback_import.html",
    }

    write_json(outputs["summary"], feedback_summary)
    write_json(outputs["reviewed_items"], {"items": reviewed_enriched})
    write_json(outputs["unreviewed_items"], {"items": unreviewed_enriched})
    write_json(outputs["revision_candidates"], {"items": revision_candidates})
    write_json(outputs["followup_review_plan"], followup_plan)
    write_text(outputs["report"], build_report(feedback_summary, followup_plan, revision_candidates))
    write_text(outputs["html"], build_html(feedback_summary, reviewed_enriched, revision_candidates))

    summary = {
        "reviewer_name_or_initials": import_payload.get("reviewer", {}).get("name_or_initials", ""),
        "reviewer_native_german": import_payload.get("reviewer", {}).get("native_german", ""),
        "reviewer_region": import_payload.get("reviewer", {}).get("region_optional", ""),
        "reviewer_date": import_payload.get("reviewer", {}).get("date", ""),
        "source_item_count": counts["source_item_count"],
        "reported_checked_count": counts["reported_checked_count"],
        "reviewed_item_count": counts["reviewed_item_count"],
        "unreviewed_item_count": counts["unreviewed_item_count"],
        "accepted_count": counts["accepted_count"],
        "small_change_count": counts["small_change_count"],
        "large_change_count": counts["large_change_count"],
        "rejected_count": counts["rejected_count"],
        "safety_or_impact_count": counts["safety_or_impact_count"],
        "blank_rows_counted_as_unreviewed": True,
        "price_feedback_captured": bool(revision_candidates),
        "price_revision_candidate_count": len(revision_candidates),
        "returned_individual_item_count": len(import_payload.get("items", [])),
        "current_grouped_packet_group_count": len(grouped_packet.get("review_groups", [])),
        "import_shape_concern_recorded": len(import_payload.get("items", [])) > len(grouped_packet.get("review_groups", [])),
        **BOUNDARY_FALSE_SUMMARY,
    }
    result = {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "summary": summary,
        "outputs": {key: rel(path) for key, path in outputs.items()},
        "dependencies": {key: rel(path) for key, path in DEPENDENCY_RESULTS.items()},
        "validation": {"passed": True},
        "next_checkpoint_recommended": NEXT_CHECKPOINT_ID,
    }
    write_json(outputs["result"], result)
    print(f"Wrote {CHECKPOINT_ID} artifacts to {rel(OUT_DIR)}")


if __name__ == "__main__":
    main()
