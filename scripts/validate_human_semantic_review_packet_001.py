#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "HUMAN-SEMANTIC-REVIEW-PACKET-001"
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
REQUIRED_EDGE_BUCKETS = {
    "permission_acknowledgement",
    "no_pain_current_issue_clear",
    "pain_confirmed",
    "possible_pain_ambiguity",
    "confusion",
    "not_relevant_no_need",
    "send_info",
    "callback_timing",
    "right_person_authority",
    "stop_refusal",
    "regulated_caution",
    "fallback_repair",
    "long_conversation_state_drift",
    "routesignal_preservation",
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
    re.compile(r"(?i)\b(api[_-]?key|secret|token|password)\s*[:=]\s*['\"]?[A-Za-z0-9._-]{8,}"),
]
SIDE_EFFECT_KEYS = [
    "provider_calls_made",
    "local_llm_calls_made",
    "sends_email",
    "creates_calendar_event",
    "writes_crm",
    "opens_prod_102",
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


def text_blob() -> str:
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
    if len(conversations) < 80:
        justification = str(packet.get("lower_count_justification") or "")
        if not justification:
            fail(f"expected at least 80 conversations or justification, found {len(conversations)}")

    jsonl_records = load_jsonl(GENERATED_DIR / "review_packet.jsonl")
    if len(jsonl_records) < 80:
        fail(f"expected at least 80 JSONL review records, found {len(jsonl_records)}")

    verticals = {str(item.get("vertical_id") or "") for item in conversations}
    missing_verticals = sorted(REQUIRED_VERTICALS - verticals)
    if missing_verticals:
        fail(f"missing required vertical/campaign sections: {missing_verticals}")

    edge_buckets: set[str] = set()
    hard_cases = 0
    routesignal_count = 0
    for conversation in conversations:
        edge_buckets.update(str(item) for item in conversation.get("edge_buckets") or [])
        risk_tags = set(str(item) for item in conversation.get("risk_tags") or [])
        if "hard_case" in risk_tags or "edge_case" in risk_tags:
            hard_cases += 1
        if conversation.get("vertical_id") == "routesignal_live_demo":
            routesignal_count += 1
        for turn in conversation.get("turns") or []:
            flags = turn.get("safety_flags") or {}
            for key in SIDE_EFFECT_KEYS:
                if flags.get(key) is not False:
                    fail(f"{conversation.get('conversation_id')} turn {turn.get('turn_index')} side effect flag {key} was not false")
    missing_buckets = sorted(REQUIRED_EDGE_BUCKETS - edge_buckets)
    if missing_buckets:
        fail(f"missing edge-case buckets: {missing_buckets}")
    if hard_cases < 20:
        fail(f"expected at least 20 hard/edge cases, found {hard_cases}")
    if routesignal_count < 15:
        fail(f"expected at least 15 RouteSignal conversations, found {routesignal_count}")

    redaction = load_json(GENERATED_DIR / "redaction_report.json")
    if redaction.get("raw_synthetic_emails_found"):
        fail(f"redaction report found raw synthetic emails: {redaction.get('raw_synthetic_emails_found')}")
    for key in SIDE_EFFECT_KEYS:
        if redaction.get("side_effect_summary", {}).get(key) is not False:
            fail(f"redaction side effect summary {key} was not false")
    if redaction.get("generated_audio_required") is not False:
        fail("redaction report must prove generated audio is not required")

    assert_no_private_or_raw_data(text_blob())

    result = load_json(GENERATED_DIR / "result.json")
    if result.get("status") != "pass":
        fail("result.json status must be pass")
    if result.get("runtime_behavior_changed") is not False:
        fail("packet phase must not change runtime behavior")

    print(
        json.dumps(
            {
                "status": "pass",
                "checkpoint_id": CHECKPOINT_ID,
                "conversation_count": len(conversations),
                "jsonl_record_count": len(jsonl_records),
                "verticals": sorted(verticals),
                "edge_buckets": sorted(edge_buckets),
                "hard_case_count": hard_cases,
                "routesignal_conversation_count": routesignal_count,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
