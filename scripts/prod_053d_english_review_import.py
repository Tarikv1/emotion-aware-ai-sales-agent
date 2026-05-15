#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-053D-english-review-import"
CHECKPOINT_NAME = "English Review Import"
SOURCE_CHECKPOINT_ID = "PROD-053C-english-spoken-response-expansion-review"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
IMPORT_DIR = ROOT / "research" / "experiments" / "imports" / SOURCE_CHECKPOINT_ID
SOURCE_DIR = ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID

SOURCE_ITEMS_PATH = SOURCE_DIR / "english_spoken_response_review_items.json"
SOURCE_RESULT_PATH = SOURCE_DIR / "result.json"

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

REWORK_CATEGORY_BY_CASE_ID = {
    "prod-053c-voicemail": "action_or_behavior_change",
    "prod-053c-identity-repair": "wording_only",
    "prod-053c-support-route": "wording_only",
    "prod-053c-cancellation-route": "wording_only",
    "prod-053c-security-review-route": "wording_only",
    "prod-053c-coverage-boundary-route": "policy_knowledge_decision",
    "prod-053c-healthcare-boundary-route": "wording_only",
    "prod-053c-claim-boundary": "wording_only",
    "prod-053c-scheduling-confirmation": "wording_only",
    "prod-053c-sale-ready-commitment": "wording_only",
    "prod-053c-procurement-review": "wording_only",
    "prod-053c-callback-request": "wording_only",
    "prod-053c-autonomy-check": "context_sensitive_wording",
}

PATCH_CANDIDATES = {
    "prod-053c-voicemail": {
        "candidate_type": "action_only_no_spoken_response",
        "candidate_response": "",
        "candidate_action": "Do not speak to voicemail. Log follow-up and try again later according to campaign rules.",
        "requires_design_decision": True,
        "context_sensitive": False,
    },
    "prod-053c-identity-repair": {
        "candidate_type": "wording",
        "candidate_response": "This is Maya from RouteSignal. I'm calling because we're checking whether missed callbacks and follow-up work are still an issue.",
        "candidate_action": "",
        "requires_design_decision": False,
        "context_sensitive": False,
    },
    "prod-053c-support-route": {
        "candidate_type": "wording",
        "candidate_response": "Of course. I'll send this to support right away. Have a good day.",
        "candidate_action": "",
        "requires_design_decision": False,
        "context_sensitive": False,
    },
    "prod-053c-cancellation-route": {
        "candidate_type": "wording",
        "candidate_response": "Sure, I'll stop and connect you to the cancellation team.",
        "candidate_action": "",
        "requires_design_decision": False,
        "context_sensitive": False,
    },
    "prod-053c-security-review-route": {
        "candidate_type": "wording",
        "candidate_response": "Security review needs verified material or a specialist. I should not make broad compliance claims here.",
        "candidate_action": "",
        "requires_design_decision": False,
        "context_sensitive": False,
    },
    "prod-053c-coverage-boundary-route": {
        "candidate_type": "design_decision",
        "candidate_response": "If approved coverage facts exist, answer from the policy document. If not, send it to a qualified reviewer.",
        "candidate_action": "Split coverage facts from regulated advice before changing runtime behavior.",
        "requires_design_decision": True,
        "context_sensitive": True,
    },
    "prod-053c-healthcare-boundary-route": {
        "candidate_type": "wording",
        "candidate_response": "I can't give medical advice, but I can send you to someone qualified.",
        "candidate_action": "",
        "requires_design_decision": False,
        "context_sensitive": False,
    },
    "prod-053c-claim-boundary": {
        "candidate_type": "wording",
        "candidate_response": "I can't guarantee something that depends on the details. A specialist can check that.",
        "candidate_action": "",
        "requires_design_decision": False,
        "context_sensitive": False,
    },
    "prod-053c-scheduling-confirmation": {
        "candidate_type": "wording",
        "candidate_response": "All right. I'll note that time for the specialist callback. Goodbye.",
        "candidate_action": "",
        "requires_design_decision": False,
        "context_sensitive": False,
    },
    "prod-053c-sale-ready-commitment": {
        "candidate_type": "wording",
        "candidate_response": "All right. I'll mark that you want the next step. No payment is handled on this call.",
        "candidate_action": "",
        "requires_design_decision": False,
        "context_sensitive": False,
    },
    "prod-053c-procurement-review": {
        "candidate_type": "wording",
        "candidate_response": "Sure. I can keep this to written review information. Nothing firm today.",
        "candidate_action": "",
        "requires_design_decision": False,
        "context_sensitive": False,
    },
    "prod-053c-existing-provider-gap": {
        "candidate_type": "approved_with_edit_note",
        "candidate_response": "I won't claim this replaces your provider. The useful check is whether there is a gap it does not cover.",
        "candidate_action": "",
        "requires_design_decision": False,
        "context_sensitive": False,
    },
    "prod-053c-callback-request": {
        "candidate_type": "wording",
        "candidate_response": "Of course. Do you have a time in mind?",
        "candidate_action": "",
        "requires_design_decision": False,
        "context_sensitive": False,
    },
    "prod-053c-autonomy-check": {
        "candidate_type": "context_sensitive_wording",
        "candidate_response": "Okay, no rush. We can keep this low-pressure and only clarify what you need.",
        "candidate_action": "Use a shorter version if the product was already explained; use a slightly longer version if the customer still lacks basic context.",
        "requires_design_decision": False,
        "context_sensitive": True,
    },
}

OWNER_FEEDBACK_THEMES = [
    {
        "theme_id": "contractions_over_formal_expansions",
        "summary": "Prefer spoken contractions such as I'll, don't, can't, and won't over I will, I do not, cannot, and will not when the boundary remains clear.",
        "source_case_ids": ["prod-053c-cancellation-route", "prod-053c-claim-boundary", "prod-053c-existing-provider-gap"],
    },
    {
        "theme_id": "less_formal_acknowledgements",
        "summary": "Use Sure, Of course, All right, or Okay instead of Confirmed and Understood when the customer-facing moment is not formal.",
        "source_case_ids": ["prod-053c-scheduling-confirmation", "prod-053c-sale-ready-commitment", "prod-053c-procurement-review"],
    },
    {
        "theme_id": "voicemail_action_only",
        "summary": "Voicemail should usually trigger logging and retry behavior, not spoken content to the mailbox.",
        "source_case_ids": ["prod-053c-voicemail"],
    },
    {
        "theme_id": "short_transfer_responses",
        "summary": "Support and cancellation routes should be short because the customer is no longer in a sales conversation.",
        "source_case_ids": ["prod-053c-support-route", "prod-053c-cancellation-route"],
    },
    {
        "theme_id": "modal_precision_matters",
        "summary": "Small modal words change meaning. Use can't for medical advice inability, and avoid too much certainty in security/compliance routes.",
        "source_case_ids": ["prod-053c-security-review-route", "prod-053c-healthcare-boundary-route"],
    },
    {
        "theme_id": "policy_knowledge_is_not_advice",
        "summary": "Coverage facts from an approved policy document may be answerable knowledge, while recommendations or advice still need a qualified reviewer.",
        "source_case_ids": ["prod-053c-coverage-boundary-route"],
    },
    {
        "theme_id": "callback_brevity",
        "summary": "When the customer asks for a callback, answer briefly and ask for a time instead of giving a reassurance paragraph.",
        "source_case_ids": ["prod-053c-callback-request"],
    },
    {
        "theme_id": "use_small_mirror_when_it_helps",
        "summary": "For autonomy concerns, a small mirror such as no rush can make the answer sound more human when it does useful work.",
        "source_case_ids": ["prod-053c-autonomy-check"],
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


def find_import_path() -> Path:
    canonical = IMPORT_DIR / "prod_053c_review_export.json"
    if canonical.exists():
        return canonical
    candidates = sorted([path for path in IMPORT_DIR.glob("*.json*") if path.is_file()])
    if len(candidates) != 1:
        raise FileNotFoundError(f"Expected exactly one import JSON in {rel(IMPORT_DIR)}; found {[path.name for path in candidates]}")
    return candidates[0]


def material_edit_note(status: str, notes: str) -> bool:
    lowered = notes.lower()
    if status != "approved" or not lowered.strip():
        return False
    if "current runtime response is fine" in lowered:
        return False
    return any(marker in lowered for marker in ["instead", "use ", "should ", "could ", "won't", "can't", "i'll"])


def source_items_by_id() -> dict[str, dict[str, Any]]:
    source_payload = read_json(SOURCE_ITEMS_PATH)
    return {item["case_id"]: item for item in source_payload["items"]}


def import_items(import_payload: dict[str, Any], source_by_id: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    items = []
    seen: set[str] = set()
    for raw in import_payload["items"]:
        case_id = raw["case_id"]
        if case_id in seen:
            raise ValueError(f"Duplicate import case_id: {case_id}")
        seen.add(case_id)
        if case_id not in source_by_id:
            raise KeyError(f"Import case_id does not exist in source review packet: {case_id}")
        source = source_by_id[case_id]
        status = raw.get("status", "pending")
        notes = raw.get("notes", "")
        if status == "needs_rework":
            bucket = "needs_rework"
        elif material_edit_note(status, notes):
            bucket = "approved_with_edit_note"
        elif status == "approved":
            bucket = "approved_as_written"
        else:
            bucket = "pending"
        items.append(
            {
                "case_id": case_id,
                "language": "en",
                "sales_difficulty": source["sales_difficulty"],
                "source_scope": source["source_scope"],
                "owner_status": status,
                "owner_notes": notes,
                "final_review_bucket": bucket,
                "current_agent_response": source["current_agent_response"],
                "proposed_review_response": source["proposed_review_response"],
                "applied_policy_rule_ids": source["applied_policy_rule_ids"],
                "runtime_response_changed": False,
                "response_text_behavior_changed": False,
                "runtime_promoted": False,
            }
        )
    if set(seen) != set(source_by_id):
        missing = sorted(set(source_by_id) - seen)
        raise ValueError(f"Import is missing source case ids: {missing}")
    return items


def enrich_rework_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    enriched = []
    for item in items:
        category = REWORK_CATEGORY_BY_CASE_ID[item["case_id"]]
        candidate = PATCH_CANDIDATES[item["case_id"]]
        enriched.append(
            {
                **item,
                "rework_category": category,
                "candidate_type": candidate["candidate_type"],
                "candidate_response": candidate["candidate_response"],
                "candidate_action": candidate["candidate_action"],
                "requires_design_decision": candidate["requires_design_decision"],
                "context_sensitive": candidate["context_sensitive"],
                "candidate_runtime_promoted": False,
            }
        )
    return enriched


def build_patch_candidates(needs_rework: list[dict[str, Any]], approved_with_note: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates = []
    for item in [*needs_rework, *approved_with_note]:
        candidate = PATCH_CANDIDATES[item["case_id"]]
        candidates.append(
            {
                "case_id": item["case_id"],
                "sales_difficulty": item["sales_difficulty"],
                "owner_status": item["owner_status"],
                "owner_notes": item["owner_notes"],
                "source_current_response": item["current_agent_response"],
                "source_proposed_review_response": item["proposed_review_response"],
                "candidate_type": candidate["candidate_type"],
                "candidate_response": candidate["candidate_response"],
                "candidate_action": candidate["candidate_action"],
                "requires_design_decision": candidate["requires_design_decision"],
                "context_sensitive": candidate["context_sensitive"],
                "runtime_response_changed": False,
                "candidate_runtime_promoted": False,
            }
        )
    return candidates


def count_by(items: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        counts[item[key]] = counts.get(item[key], 0) + 1
    return counts


def build_summary(import_path: Path, items: list[dict[str, Any]], patch_candidates: list[dict[str, Any]]) -> dict[str, Any]:
    bucket_counts = count_by(items, "final_review_bucket")
    rework_categories = count_by([item for item in items if item["final_review_bucket"] == "needs_rework"], "case_id")
    return {
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "import_path": rel(import_path),
        "import_item_count": len(items),
        "approved_count": sum(1 for item in items if item["owner_status"] == "approved"),
        "needs_rework_count": sum(1 for item in items if item["owner_status"] == "needs_rework"),
        "pending_count": sum(1 for item in items if item["owner_status"] == "pending"),
        "approved_as_written_count": bucket_counts.get("approved_as_written", 0),
        "approved_with_edit_note_count": bucket_counts.get("approved_with_edit_note", 0),
        "runtime_patch_candidate_count": len(patch_candidates),
        "owner_feedback_theme_count": len(OWNER_FEEDBACK_THEMES),
        "rework_case_ids": sorted(item["case_id"] for item in items if item["final_review_bucket"] == "needs_rework"),
        "approved_with_edit_note_case_ids": sorted(item["case_id"] for item in items if item["final_review_bucket"] == "approved_with_edit_note"),
        "rework_category_counts": {
            "wording_only": sum(1 for item in patch_candidates if item["candidate_type"] in {"wording", "approved_with_edit_note"}),
            "action_or_behavior_change": sum(1 for item in patch_candidates if item["candidate_type"] == "action_only_no_spoken_response"),
            "policy_knowledge_decision": sum(1 for item in patch_candidates if item["case_id"] == "prod-053c-coverage-boundary-route"),
            "context_sensitive_wording": sum(1 for item in patch_candidates if item["candidate_type"] == "context_sensitive_wording"),
        },
        "voicemail_requires_action_only_change": any(item["case_id"] == "prod-053c-voicemail" for item in patch_candidates),
        "coverage_requires_policy_knowledge_decision": any(item["case_id"] == "prod-053c-coverage-boundary-route" for item in patch_candidates),
        "autonomy_requires_context_sensitive_response": any(item["case_id"] == "prod-053c-autonomy-check" for item in patch_candidates),
        **BOUNDARY_FLAGS,
        "unused_rework_categories_internal": rework_categories,
    }


def build_import_summary(import_payload: dict[str, Any], summary: dict[str, Any], items: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "source_review_export_checkpoint_id": import_payload["checkpoint_id"],
        "summary": summary,
        "status_counts": count_by(items, "owner_status"),
        "bucket_counts": count_by(items, "final_review_bucket"),
        "no_runtime_changes_applied": True,
    }


def render_report(summary: dict[str, Any], patch_candidates: list[dict[str, Any]]) -> str:
    lines = [
        f"# {CHECKPOINT_NAME}",
        "",
        "`PROD-053D` imports Tarik's `PROD-053C` English review export and turns it into a decision summary plus rework plan.",
        "",
        "It does not change runtime behavior or response text.",
        "",
        "## Summary",
        "",
        f"- Import items: `{summary['import_item_count']}`",
        f"- Approved statuses: `{summary['approved_count']}`",
        f"- Needs rework statuses: `{summary['needs_rework_count']}`",
        f"- Pending statuses: `{summary['pending_count']}`",
        f"- Approved as-written: `{summary['approved_as_written_count']}`",
        f"- Approved with edit note: `{summary['approved_with_edit_note_count']}`",
        f"- Runtime patch candidates: `{summary['runtime_patch_candidate_count']}`",
        f"- Runtime behavior changed: `{str(summary['runtime_behavior_changed']).lower()}`",
        f"- Response text behavior changed: `{str(summary['response_text_behavior_changed']).lower()}`",
        "",
        "## Key Corrections",
        "",
        "- Do not speak to voicemail; log follow-up and retry later.",
        "- Prefer contractions and less formal acknowledgement words where safe.",
        "- Keep support, cancellation, and callback routes shorter.",
        "- Treat coverage facts from an approved policy document differently from advice.",
        "- Use context-sensitive autonomy wording around `no rush`.",
        "",
        "## Patch Candidates",
        "",
    ]
    for item in patch_candidates:
        response = item["candidate_response"] or item["candidate_action"]
        owner_note = " ".join(item["owner_notes"].split())
        lines.extend(
            [
                f"### {item['case_id']} - {item['sales_difficulty']}",
                "",
                f"- Candidate type: `{item['candidate_type']}`",
                f"- Owner note: {owner_note}",
                f"- Candidate: {response}",
                f"- Requires design decision: `{str(item['requires_design_decision']).lower()}`",
                f"- Context sensitive: `{str(item['context_sensitive']).lower()}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Boundaries",
            "",
            "- No runtime behavior change.",
            "- No response text behavior change.",
            "- No German exact phrase promotion.",
            "- No LLM calls, LLM judging, provider calls, retrieval enablement, private data reads, voice playback, public demo use, payment collection, contract signing, or production promotion.",
            "",
            "## Next Gate",
            "",
            "Create a narrow English runtime patch checkpoint only for accepted as-written items and owner-corrected rework candidates. Do not bundle voicemail action-only behavior or coverage knowledge-policy design without separate targeted checks.",
            "",
        ]
    )
    return "\n".join(lines)


def build_payload() -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    import_path = find_import_path()
    import_payload = read_json(import_path)
    source_result = read_json(SOURCE_RESULT_PATH)
    if source_result["validation"]["passed"] is not True:
        raise RuntimeError("PROD-053C source validation must pass before import")
    items = import_items(import_payload, source_items_by_id())
    accepted_as_written = [item for item in items if item["final_review_bucket"] == "approved_as_written"]
    approved_with_note = [item for item in items if item["final_review_bucket"] == "approved_with_edit_note"]
    needs_rework = enrich_rework_items([item for item in items if item["final_review_bucket"] == "needs_rework"])
    patch_candidates = build_patch_candidates(needs_rework, approved_with_note)
    summary = build_summary(import_path, items, patch_candidates)
    import_summary = build_import_summary(import_payload, summary, items)
    result = {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "summary": {key: value for key, value in summary.items() if key != "unused_rework_categories_internal"},
        "outputs": {
            "result": rel(OUT_DIR / "result.json"),
            "report": rel(OUT_DIR / "report.md"),
            "import_summary": rel(OUT_DIR / "imported_review_summary.json"),
            "accepted_as_written": rel(OUT_DIR / "accepted_as_written_items.json"),
            "approved_with_edit_note": rel(OUT_DIR / "approved_with_edit_note_items.json"),
            "needs_rework": rel(OUT_DIR / "needs_rework_items.json"),
            "owner_feedback_themes": rel(OUT_DIR / "owner_feedback_themes.json"),
            "runtime_patch_candidates": rel(OUT_DIR / "runtime_patch_candidates.json"),
        },
        "validation": {
            "passed": True,
            "notes": [
                "Review import only; no runtime behavior or response text was changed.",
                "Approved items with material notes are separated from exact as-written approvals.",
                "Voicemail and coverage feedback require separate behavior/design checks before runtime changes.",
            ],
        },
    }
    return result, import_summary, accepted_as_written, approved_with_note, needs_rework, OWNER_FEEDBACK_THEMES, patch_candidates


def main() -> None:
    result, import_summary, accepted_as_written, approved_with_note, needs_rework, themes, patch_candidates = build_payload()
    write_json(OUT_DIR / "imported_review_summary.json", import_summary)
    write_json(OUT_DIR / "accepted_as_written_items.json", {"items": accepted_as_written})
    write_json(OUT_DIR / "approved_with_edit_note_items.json", {"items": approved_with_note})
    write_json(OUT_DIR / "needs_rework_items.json", {"items": needs_rework})
    write_json(OUT_DIR / "owner_feedback_themes.json", {"items": themes})
    write_json(OUT_DIR / "runtime_patch_candidates.json", {"items": patch_candidates})
    write_text(OUT_DIR / "report.md", render_report(result["summary"], patch_candidates))
    write_json(OUT_DIR / "result.json", result)
    print(json.dumps({"checkpoint_id": CHECKPOINT_ID, "validation": result["validation"], "summary": result["summary"]}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
