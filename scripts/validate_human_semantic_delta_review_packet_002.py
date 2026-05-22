#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "HUMAN-SEMANTIC-DELTA-REVIEW-PACKET-002"
GENERATED_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID

REQUIRED_FILES = [
    "review_packet.md",
    "review_packet.json",
    "review_packet.jsonl",
    "review_index.md",
    "redaction_report.json",
    "report.md",
    "result.json",
]
REQUIRED_VERTICALS = {
    "b2b_saas",
    "insurance",
    "telecom",
    "home_services",
    "healthcare_admin_or_medical_equipment",
    "automotive_service",
    "membership_or_subscription",
    "retail_or_ecommerce_support_sales",
    "routesignal_live_demo",
}
REQUIRED_FOCUS_AREAS = {
    "5a1_replayed_fixes",
    "appointment_pressure_calibration",
    "support_out_of_scope_boundaries",
    "confusion_explanation_quality",
    "long_state_drift",
    "routesignal_preservation",
    "regulated_caution",
}
RAW_SYNTHETIC_EMAILS = [
    "alex@example.com",
    "ops@example.com",
    "manager@example.com",
    "policy@example.com",
    "support@example.com",
]
PRIVATE_OR_SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_-]{12,}"),
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"(?i)\b(api[_-]?key|secret|token)\s*[:=]\s*['\"]?[A-Za-z0-9._-]{8,}"),
]
SIDE_EFFECT_KEYS = [
    "provider_calls_made",
    "local_llm_calls_made",
    "sends_email",
    "creates_calendar_event",
    "writes_crm",
    "opens_prod_102",
]
TURN_REQUIRED_FIELDS = [
    "turn_index",
    "buyer_transcript",
    "agent_final_response",
    "tts_input_text",
    "provider_rendered_text",
    "semantic",
    "target_gap",
    "primary_gap",
    "cleared_gaps",
    "confirmed_gaps",
    "selected_action",
    "selected_action_source",
    "call_control",
    "send_info_state",
    "lead_followup_state",
    "handoff_target_state",
    "safety_flags",
    "reviewer_questions",
]


def fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        fail(f"{path} did not parse as JSON: {exc}")


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except Exception as exc:
            fail(f"{path}:{line_no} did not parse as JSONL: {exc}")
        if not isinstance(value, dict):
            fail(f"{path}:{line_no} must be a JSON object")
        records.append(value)
    return records


def generated_text_blob() -> str:
    parts: list[str] = []
    for name in REQUIRED_FILES:
        path = GENERATED_DIR / name
        if path.exists():
            parts.append(path.read_text(encoding="utf-8", errors="replace"))
    return "\n".join(parts)


def assert_no_private_or_raw_data(blob: str) -> None:
    lowered = blob.lower()
    for raw in RAW_SYNTHETIC_EMAILS:
        if raw.lower() in lowered:
            fail(f"raw synthetic email leaked: {raw}")
    for pattern in PRIVATE_OR_SECRET_PATTERNS:
        match = pattern.search(blob)
        if match:
            fail(f"private-looking secret pattern leaked: {match.group(0)[:40]}")


def assert_side_effects_false(turn: dict[str, Any], label: str) -> None:
    flags = turn.get("safety_flags")
    if not isinstance(flags, dict):
        fail(f"{label}: safety_flags must be an object")
    for key in SIDE_EFFECT_KEYS:
        if flags.get(key) is not False:
            fail(f"{label}: side-effect flag {key} was not false")


def main() -> int:
    missing = [name for name in REQUIRED_FILES if not (GENERATED_DIR / name).exists()]
    if missing:
        fail(f"missing required packet files: {missing}")

    packet = load_json(GENERATED_DIR / "review_packet.json")
    if not isinstance(packet, dict):
        fail("review_packet.json root must be an object")
    conversations = packet.get("conversations")
    if not isinstance(conversations, list):
        fail("review_packet.json must contain conversations list")
    if len(conversations) < 40:
        fail(f"expected at least 40 conversations, found {len(conversations)}")
    if len(conversations) > 70:
        fail(f"expected no more than 70 conversations for delta packet, found {len(conversations)}")

    records = load_jsonl(GENERATED_DIR / "review_packet.jsonl")
    if len(records) < 200:
        fail(f"expected at least 200 turn-level JSONL records, found {len(records)}")
    if len(records) > 350:
        fail(f"expected no more than 350 turn-level JSONL records, found {len(records)}")

    verticals: set[str] = set()
    focus_areas: set[str] = set()
    hard_cases = 0
    routesignal_count = 0
    turn_count = 0
    for conversation in conversations:
        vertical = str(conversation.get("vertical_id") or "")
        verticals.add(vertical)
        focus_areas.update(str(item) for item in conversation.get("focus_areas") or [])
        risk_tags = set(str(item) for item in conversation.get("risk_tags") or [])
        if "hard_case" in risk_tags or "edge_case" in risk_tags:
            hard_cases += 1
        if vertical == "routesignal_live_demo":
            routesignal_count += 1
        if "source" not in conversation:
            fail(f"{conversation.get('conversation_id')}: missing source field")
        turns = conversation.get("turns")
        if not isinstance(turns, list) or not turns:
            fail(f"{conversation.get('conversation_id')}: turns must be a non-empty list")
        for turn in turns:
            turn_count += 1
            missing_turn_fields = [field for field in TURN_REQUIRED_FIELDS if field not in turn]
            if missing_turn_fields:
                fail(
                    f"{conversation.get('conversation_id')} turn {turn.get('turn_index')}: "
                    f"missing required fields {missing_turn_fields}"
                )
            assert_side_effects_false(turn, f"{conversation.get('conversation_id')} turn {turn.get('turn_index')}")

    missing_verticals = sorted(REQUIRED_VERTICALS - verticals)
    if missing_verticals:
        fail(f"missing required verticals: {missing_verticals}")
    missing_focus = sorted(REQUIRED_FOCUS_AREAS - focus_areas)
    if missing_focus:
        fail(f"missing required focus areas: {missing_focus}")
    if routesignal_count < 10:
        fail(f"expected at least 10 RouteSignal conversations, found {routesignal_count}")
    if hard_cases < 30:
        fail(f"expected at least 30 hard/edge conversations, found {hard_cases}")
    if turn_count != len(records):
        fail(f"turn count mismatch: packet has {turn_count}, JSONL has {len(records)}")

    redaction = load_json(GENERATED_DIR / "redaction_report.json")
    if redaction.get("raw_synthetic_emails_found"):
        fail(f"redaction report found raw synthetic emails: {redaction.get('raw_synthetic_emails_found')}")
    if redaction.get("private_or_secret_pattern_matches"):
        fail(f"redaction report found private-looking data: {redaction.get('private_or_secret_pattern_matches')}")
    if redaction.get("generated_audio_required") is not False:
        fail("redaction report must prove generated audio is not required")
    for key in SIDE_EFFECT_KEYS:
        if redaction.get("side_effect_summary", {}).get(key) is not False:
            fail(f"redaction side effect summary {key} was not false")

    assert_no_private_or_raw_data(generated_text_blob())

    result = load_json(GENERATED_DIR / "result.json")
    if result.get("status") != "pass":
        fail("result.json status must be pass")
    if result.get("runtime_behavior_changed") is not False:
        fail("delta packet generation must not change runtime behavior")
    if result.get("phase_1_2_3_backpatch_required") is not False:
        fail("Phase 1/2/3 backpatch must be false for this packet phase")

    print(
        json.dumps(
            {
                "status": "pass",
                "checkpoint_id": CHECKPOINT_ID,
                "conversation_count": len(conversations),
                "turn_record_count": len(records),
                "hard_edge_conversation_count": hard_cases,
                "routesignal_conversation_count": routesignal_count,
                "verticals": sorted(verticals),
                "focus_areas": sorted(focus_areas),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
