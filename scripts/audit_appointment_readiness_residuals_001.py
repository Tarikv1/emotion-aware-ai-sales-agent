"""Audit residual appointment-readiness warnings in the commercial review packet.

This script is evidence-only. It reads the generated commercial review packet,
classifies appointment-readiness warning candidates, and writes an audit report.
It does not call providers, send email, write calendars, write CRM records, or
mutate runtime behavior.
"""

from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "APPOINTMENT-READINESS-RESIDUAL-AUDIT-001"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
PACKET_PATH = (
    ROOT
    / "research"
    / "experiments"
    / "generated"
    / "COMMERCIAL-SALES-CONVERSATION-REVIEW-001"
    / "review_packet.json"
)

WARNING_ID = "appointment_not_asked_when_ready"

APPOINTMENT_ASK_PATTERNS = [
    "what time works",
    "what callback window",
    "callback window works",
    "time window",
    "note a time",
    "schedule",
    "book",
    "tomorrow at",
]

NEXT_STEP_PATTERNS = [
    *APPOINTMENT_ASK_PATTERNS,
    "what email",
    "email should",
    "email or callback",
    "what works",
    "which day",
    "preferred window",
    "what day or time",
]

WEAK_CLOSE_PATTERNS = [
    "probably the right next step",
    "would a review be useful",
    "should i stop here",
    "we can leave it there",
    "if not, i can stop here",
]

INTENTIONAL_NO_ASK_MOVES = {
    "implication_weak_or_denied",
    "permission_to_continue_denied",
    "stop_request",
    "language_mismatch",
    "emotional_frustration",
    "abusive_or_hostile_buyer",
    "privacy_data_use_question",
}


def load_packet() -> dict[str, Any]:
    return json.loads(PACKET_PATH.read_text(encoding="utf-8"))


def contains_any(text: str, patterns: list[str]) -> bool:
    lowered = text.lower()
    return any(pattern in lowered for pattern in patterns)


def turn_records(packet: dict[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for conversation in packet.get("conversations") or []:
        for turn in conversation.get("turns") or []:
            records.append(
                {
                    "conversation_id": conversation.get("conversation_id"),
                    "campaign_id": conversation.get("campaign_id"),
                    "arc_type": conversation.get("arc_type"),
                    "turn_index": turn.get("turn_index"),
                    "buyer_utterance": turn.get("buyer_utterance"),
                    "final_response": turn.get("final_response") or "",
                    "call_control": turn.get("call_control"),
                    "mechanical_warning_flags": turn.get("mechanical_warning_flags") or [],
                    "appointment_readiness": turn.get("appointment_readiness"),
                    "next_best_sales_action": turn.get("next_best_sales_action"),
                    "confirmed_gaps": turn.get("confirmed_gaps") or [],
                    "target_gap": turn.get("target_gap"),
                    "selected_action_source": (turn.get("selected_action") or {}).get("source"),
                    "universal_policy_frame": turn.get("universal_policy_frame") or {},
                }
            )
    return records


def legacy_warning_candidate(record: dict[str, Any]) -> bool:
    response = str(record.get("final_response") or "")
    return record.get("appointment_readiness") == "high" and not contains_any(response, APPOINTMENT_ASK_PATTERNS)


def response_has_next_step(record: dict[str, Any]) -> bool:
    return contains_any(str(record.get("final_response") or ""), NEXT_STEP_PATTERNS)


def response_confirms_callback_time(record: dict[str, Any]) -> bool:
    frame = record.get("universal_policy_frame") or {}
    response = str(record.get("final_response") or "").lower()
    return (
        frame.get("buyer_move_id") == "callback_time_provided"
        or record.get("next_best_sales_action") == "confirm_callback_time"
        or ("note that time" in response and "follow up" in response)
    )


def classify(record: dict[str, Any]) -> tuple[str, str]:
    frame = record.get("universal_policy_frame") or {}
    buyer_move = str(frame.get("buyer_move_id") or "")
    response = str(record.get("final_response") or "")
    confirmed = [gap for gap in record.get("confirmed_gaps") or [] if gap]

    if response_confirms_callback_time(record):
        return (
            "review_packet_warning_bug",
            "Concrete callback time was already captured; the old warning only checked for a new appointment ask.",
        )
    if buyer_move in INTENTIONAL_NO_ASK_MOVES or record.get("appointment_readiness") == "low":
        return ("intentional_no_ask", "No appointment pressure is correct for this buyer move or low readiness.")
    if not confirmed and record.get("appointment_readiness") in {"medium", "high"}:
        return ("state_preservation_bug", "Readiness exists but the confirmed gap was not preserved.")
    if response_has_next_step(record):
        if contains_any(response, WEAK_CLOSE_PATTERNS):
            return ("weak_close_language", "A next step exists, but the close language is hesitant or stop-heavy.")
        return ("false_positive_warning", "The response already asks for a next step.")
    if contains_any(response, WEAK_CLOSE_PATTERNS):
        return ("weak_close_language", "High-readiness response used weak close language instead of a concrete next step.")
    if record.get("appointment_readiness") in {"medium", "high"} and confirmed:
        return ("true_missed_next_step", "Readiness and confirmed gap exist, but no callback/contact/time ask was present.")
    return ("needs_human_sales_review", "The case is ambiguous under deterministic audit rules.")


def build_audit(packet: dict[str, Any]) -> dict[str, Any]:
    all_records = turn_records(packet)
    current_flagged = [record for record in all_records if WARNING_ID in record.get("mechanical_warning_flags", [])]
    legacy_candidates = [record for record in all_records if legacy_warning_candidate(record)]

    # Before the packet warning fix, this warning was counted once at the turn
    # level and once at the conversation aggregate level. Keep both counts so
    # the audit can explain the reported "30" while classifying unique turns.
    current_packet_count = int((packet.get("mechanical_warning_counts") or {}).get(WARNING_ID) or 0)
    current_conversation_count = sum(
        1 for conversation in packet.get("conversations") or [] if WARNING_ID in (conversation.get("mechanical_warning_flags") or [])
    )
    current_turn_count = len(current_flagged)
    legacy_conversation_count = len({record["conversation_id"] for record in legacy_candidates})
    legacy_turn_count = len(legacy_candidates)
    legacy_reported_count = legacy_conversation_count + legacy_turn_count

    audit_subject = current_flagged if current_flagged else legacy_candidates
    classified: list[dict[str, Any]] = []
    counts: Counter[str] = Counter()
    for record in audit_subject:
        classification, reason = classify(record)
        counts[classification] += 1
        frame = record.get("universal_policy_frame") or {}
        classified.append(
            {
                "classification": classification,
                "reason": reason,
                "conversation_id": record.get("conversation_id"),
                "campaign_id": record.get("campaign_id"),
                "arc_type": record.get("arc_type"),
                "turn_index": record.get("turn_index"),
                "buyer_utterance": record.get("buyer_utterance"),
                "buyer_move_id": frame.get("buyer_move_id"),
                "appointment_readiness": record.get("appointment_readiness"),
                "next_best_sales_action": record.get("next_best_sales_action"),
                "confirmed_gaps": record.get("confirmed_gaps"),
                "call_control": record.get("call_control"),
                "selected_action_source": record.get("selected_action_source"),
                "final_response": record.get("final_response"),
            }
        )

    side_effects = {
        "provider_calls_made": False,
        "local_llm_calls_made": False,
        "live_tts_used": False,
        "sends_email": False,
        "creates_calendar_event": False,
        "writes_crm": False,
        "opens_prod_102": False,
        "customer_audio_uploaded_to_python_server": False,
        "customer_audio_uploaded_to_tts_provider": False,
    }
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "source_packet": str(PACKET_PATH.relative_to(ROOT)),
        "current_packet_warning_occurrences": current_packet_count,
        "current_flagged_turn_count": current_turn_count,
        "current_flagged_conversation_count": current_conversation_count,
        "legacy_residual_warning_occurrences": legacy_reported_count,
        "legacy_residual_turn_count": legacy_turn_count,
        "legacy_residual_conversation_count": legacy_conversation_count,
        "classification_basis": "current_flags" if current_flagged else "legacy_residual_heuristic",
        "classification_counts": dict(sorted(counts.items())),
        "classified_records": classified,
        "true_missed_next_step_count": counts.get("true_missed_next_step", 0),
        "weak_close_language_count": counts.get("weak_close_language", 0),
        "false_positive_count": counts.get("false_positive_warning", 0),
        "review_packet_warning_bug_count": counts.get("review_packet_warning_bug", 0),
        "intentional_no_ask_count": counts.get("intentional_no_ask", 0),
        "state_preservation_bug_count": counts.get("state_preservation_bug", 0),
        "needs_human_sales_review_count": counts.get("needs_human_sales_review", 0),
        "recommended_patch_scope": (
            "Fix review-packet warning logic for callback_time_provided turns; no runtime behavior patch is justified."
            if counts and set(counts) == {"review_packet_warning_bug"}
            else "Patch only categories with true runtime defects."
        ),
        "runtime_behavior_changed": False,
        "side_effects": side_effects,
        **side_effects,
    }


def write_report(payload: dict[str, Any]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "result.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    records = payload["classified_records"]

    def examples_for(classification: str, limit: int = 5) -> list[dict[str, Any]]:
        return [record for record in records if record["classification"] == classification][:limit]

    lines = [
        f"# {CHECKPOINT_ID}",
        "",
        "## 1. Summary",
        f"- Classification basis: `{payload['classification_basis']}`",
        f"- Recommended patch scope: {payload['recommended_patch_scope']}",
        f"- Runtime behavior changed: `{str(payload['runtime_behavior_changed']).lower()}`",
        "",
        "## 2. Total appointment_not_asked_when_ready warnings",
        f"- Current packet warning occurrences: `{payload['current_packet_warning_occurrences']}`",
        f"- Current flagged turns: `{payload['current_flagged_turn_count']}`",
        f"- Current flagged conversations: `{payload['current_flagged_conversation_count']}`",
        f"- Legacy residual reported occurrences: `{payload['legacy_residual_warning_occurrences']}`",
        f"- Legacy residual turns: `{payload['legacy_residual_turn_count']}`",
        "",
        "## 3. Count by classification",
    ]
    for key, value in payload["classification_counts"].items():
        lines.append(f"- `{key}`: `{value}`")
    if not payload["classification_counts"]:
        lines.append("- None")
    lines.extend(["", "## 4. Top true missed-next-step examples"])
    for item in examples_for("true_missed_next_step"):
        lines.append(f"- `{item['conversation_id']}` turn `{item['turn_index']}`: {item['final_response']}")
    if not examples_for("true_missed_next_step"):
        lines.append("- None")
    lines.extend(["", "## 5. Top weak-close examples"])
    for item in examples_for("weak_close_language"):
        lines.append(f"- `{item['conversation_id']}` turn `{item['turn_index']}`: {item['final_response']}")
    if not examples_for("weak_close_language"):
        lines.append("- None")
    lines.extend(["", "## 6. False-positive examples"])
    for item in examples_for("false_positive_warning") + examples_for("review_packet_warning_bug"):
        lines.append(
            f"- `{item['conversation_id']}` turn `{item['turn_index']}` `{item['buyer_move_id']}`: {item['final_response']}"
        )
    if not (examples_for("false_positive_warning") + examples_for("review_packet_warning_bug")):
        lines.append("- None")
    lines.extend(
        [
            "",
            "## 7. Warning-logic defects",
            f"- Review-packet warning bug count: `{payload['review_packet_warning_bug_count']}`",
            "- The old warning treated callback-time confirmation as a missed appointment ask.",
            "",
            "## 8. Runtime defects",
            f"- True missed-next-step count: `{payload['true_missed_next_step_count']}`",
            f"- State preservation bug count: `{payload['state_preservation_bug_count']}`",
            "",
            "## 9. Recommended patch scope",
            f"- {payload['recommended_patch_scope']}",
            "",
            "## 10. Whether runtime behavior changed",
            f"- `{str(payload['runtime_behavior_changed']).lower()}`",
        ]
    )
    (OUT_DIR / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    payload = build_audit(load_packet())
    write_report(payload)
    print(
        json.dumps(
            {
                "checkpoint_id": payload["checkpoint_id"],
                "current_packet_warning_occurrences": payload["current_packet_warning_occurrences"],
                "legacy_residual_warning_occurrences": payload["legacy_residual_warning_occurrences"],
                "classification_basis": payload["classification_basis"],
                "classification_counts": payload["classification_counts"],
                "recommended_patch_scope": payload["recommended_patch_scope"],
                "runtime_behavior_changed": payload["runtime_behavior_changed"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
