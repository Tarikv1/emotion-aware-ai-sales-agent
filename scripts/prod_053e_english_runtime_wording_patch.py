#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-053E-english-runtime-wording-patch"
CHECKPOINT_NAME = "English Runtime Wording Patch"
SOURCE_CHECKPOINT_ID = "PROD-053D-english-review-import"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
SOURCE_DIR = ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID
SOURCE_REVIEW_DIR = ROOT / "research" / "experiments" / "generated" / "PROD-053C-english-spoken-response-expansion-review"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from runtime.core.realtime_turns import build_runtime_decision  # noqa: E402
from prod_053c_english_spoken_response_expansion_review import BASE_CAMPAIGN, RUNTIME_PROBES  # noqa: E402


SAFE_CANDIDATE_TYPES = {"wording", "approved_with_edit_note"}
BOUNDARY_FLAGS = {
    "runtime_behavior_changed": True,
    "response_text_behavior_changed": True,
    "english_only_runtime_patch": True,
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


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def runtime_probe_by_id() -> dict[str, dict[str, Any]]:
    probes = {item["case_id"]: item for item in RUNTIME_PROBES}
    source_items = read_json(SOURCE_REVIEW_DIR / "english_spoken_response_review_items.json")["items"]
    for item in source_items:
        if item["case_id"] not in probes:
            probes[item["case_id"]] = {
                "case_id": item["case_id"],
                "case_title": item["case_title"],
                "sales_difficulty": item["sales_difficulty"],
                "customer_utterance": item["customer_utterance"],
                "customer_input": {
                    "input_type": "speech",
                    "transcript": item["customer_utterance"],
                    "stage": "opening",
                },
            }
    return probes


def runtime_decision_for(case_id: str) -> dict[str, Any]:
    probe = runtime_probe_by_id()[case_id]
    campaign = probe.get("campaign", BASE_CAMPAIGN)
    return build_runtime_decision(probe, campaign=campaign)


def accepted_promotions() -> list[dict[str, Any]]:
    payload = read_json(SOURCE_DIR / "accepted_as_written_items.json")
    return [
        {
            "case_id": item["case_id"],
            "language": "en",
            "sales_difficulty": item["sales_difficulty"],
            "source_bucket": "approved_as_written",
            "previous_response": item["current_agent_response"],
            "promoted_response": item["proposed_review_response"],
        }
        for item in payload["items"]
    ]


def candidate_promotions_and_skips() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    payload = read_json(SOURCE_DIR / "runtime_patch_candidates.json")
    promoted = []
    skipped = []
    for item in payload["items"]:
        safe_candidate = (
            item["candidate_type"] in SAFE_CANDIDATE_TYPES
            and item["requires_design_decision"] is False
            and item["context_sensitive"] is False
        )
        if safe_candidate:
            promoted.append(
                {
                    "case_id": item["case_id"],
                    "language": "en",
                    "sales_difficulty": item["sales_difficulty"],
                    "source_bucket": item["candidate_type"],
                    "previous_response": item["source_current_response"],
                    "promoted_response": item["candidate_response"],
                }
            )
        else:
            skipped.append(
                {
                    "case_id": item["case_id"],
                    "language": "en",
                    "sales_difficulty": item["sales_difficulty"],
                    "candidate_type": item["candidate_type"],
                    "candidate_response": item["candidate_response"],
                    "requires_design_decision": item["requires_design_decision"],
                    "context_sensitive": item["context_sensitive"],
                    "runtime_promoted": False,
                    "skip_reason": skip_reason(item),
                }
            )
    return promoted, skipped


def skip_reason(item: dict[str, Any]) -> str:
    if item["candidate_type"] == "action_only_no_spoken_response":
        return "Voicemail action-only behavior needs a separate call-control checkpoint."
    if item["requires_design_decision"]:
        return "Coverage policy knowledge behavior needs a separate design/runtime checkpoint."
    if item["context_sensitive"]:
        return "Context-sensitive autonomy wording needs a separate multi-turn check."
    return "Candidate is outside the safe wording-only promotion set."


def promoted_items() -> list[dict[str, Any]]:
    candidate_promoted, _ = candidate_promotions_and_skips()
    items = accepted_promotions() + candidate_promoted
    seen: set[str] = set()
    deduped = []
    for item in items:
        if item["case_id"] in seen:
            continue
        seen.add(item["case_id"])
        decision = runtime_decision_for(item["case_id"])
        deduped.append(
            {
                **item,
                "runtime_response": decision["agent_response"],
                "runtime_sales_difficulty": decision["sales_difficulty"],
                "runtime_next_action": decision["next_action"],
                "runtime_call_control": decision["call_control"],
                "response_text_changed": item["previous_response"] != item["promoted_response"],
                "runtime_promoted": decision["agent_response"] == item["promoted_response"],
            }
        )
    return deduped


def skipped_items() -> list[dict[str, Any]]:
    _, skipped = candidate_promotions_and_skips()
    output = []
    for item in skipped:
        decision = runtime_decision_for(item["case_id"])
        output.append(
            {
                **item,
                "runtime_response": decision["agent_response"],
                "runtime_response_matches_candidate": decision["agent_response"] == item["candidate_response"],
            }
        )
    return output


def render_report(promoted: list[dict[str, Any]], skipped: list[dict[str, Any]], summary: dict[str, Any]) -> str:
    lines = [
        "# PROD-053E English Runtime Wording Patch",
        "",
        f"Source checkpoint: `{SOURCE_CHECKPOINT_ID}`.",
        "",
        "## Summary",
        "",
        f"- Promoted runtime responses: `{summary['promoted_response_count']}`",
        f"- Accepted-as-written promoted: `{summary['accepted_as_written_promoted_count']}`",
        f"- Safe wording rework promoted: `{summary['safe_rework_promoted_count']}`",
        f"- Approved-with-edit-note promoted: `{summary['approved_with_edit_note_promoted_count']}`",
        f"- Skipped runtime candidates: `{summary['skipped_runtime_candidate_count']}`",
        f"- Runtime behavior changed: `{str(summary['runtime_behavior_changed']).lower()}`",
        f"- Response text behavior changed: `{str(summary['response_text_behavior_changed']).lower()}`",
        "",
        "## Promoted Responses",
        "",
    ]
    for item in promoted:
        lines.extend(
            [
                f"### {item['case_id']}",
                "",
                f"- Sales difficulty: `{item['sales_difficulty']}`",
                f"- Source bucket: `{item['source_bucket']}`",
                f"- Runtime promoted: `{str(item['runtime_promoted']).lower()}`",
                "",
                "```text",
                item["runtime_response"],
                "```",
                "",
            ]
        )
    lines.extend(["## Skipped Candidates", ""])
    for item in skipped:
        lines.extend(
            [
                f"### {item['case_id']}",
                "",
                f"- Candidate type: `{item['candidate_type']}`",
                f"- Reason: {item['skip_reason']}",
                f"- Runtime promoted: `{str(item['runtime_promoted']).lower()}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Boundary",
            "",
            "- No provider calls.",
            "- No LLM or LLM judging.",
            "- No private data reads.",
            "- No German exact-phrase promotion or German naturalness claim.",
            "- `PROD-054` remains blocked until the promoted single-turn English wording is validated.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    source_result = read_json(SOURCE_DIR / "result.json")
    if source_result["validation"]["passed"] is not True:
        raise SystemExit("PROD-053D must pass before PROD-053E.")

    promoted = promoted_items()
    skipped = skipped_items()
    promoted_ids = {item["case_id"] for item in promoted}
    skipped_ids = {item["case_id"] for item in skipped}
    validation_passed = (
        len(promoted) == 26
        and len(skipped) == 3
        and all(item["runtime_promoted"] for item in promoted)
        and all(not item["runtime_response_matches_candidate"] for item in skipped)
    )
    safe_rework_count = sum(1 for item in promoted if item["source_bucket"] == "wording")
    approved_with_edit_count = sum(1 for item in promoted if item["source_bucket"] == "approved_with_edit_note")
    accepted_count = sum(1 for item in promoted if item["source_bucket"] == "approved_as_written")
    summary = {
        "promoted_response_count": len(promoted),
        "accepted_as_written_promoted_count": accepted_count,
        "safe_rework_promoted_count": safe_rework_count,
        "approved_with_edit_note_promoted_count": approved_with_edit_count,
        "skipped_runtime_candidate_count": len(skipped),
        "changed_response_count": sum(1 for item in promoted if item["response_text_changed"]),
        "promoted_case_ids": sorted(promoted_ids),
        "skipped_case_ids": sorted(skipped_ids),
        **BOUNDARY_FLAGS,
    }

    result = {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "validation": {"passed": validation_passed},
        "summary": summary,
    }

    write_json(OUT_DIR / "promoted_runtime_responses.json", {"checkpoint_id": CHECKPOINT_ID, "items": promoted})
    write_json(OUT_DIR / "skipped_runtime_candidates.json", {"checkpoint_id": CHECKPOINT_ID, "items": skipped})
    write_json(OUT_DIR / "result.json", result)
    write_text(OUT_DIR / "report.md", render_report(promoted, skipped, summary))
    print(json.dumps({"checkpoint_id": CHECKPOINT_ID, "validation": result["validation"], "summary": summary}, indent=2))


if __name__ == "__main__":
    main()
