#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-HOSTED-SANDBOX-QUALITY-001" / "result.json"
REPORT_PATH = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-HOSTED-SANDBOX-QUALITY-001" / "report.md"
HOSTED_RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-HOSTED-SANDBOX-001" / "result.json"

SECRET_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9_-]{20,}|u[a-z]?v[A-Za-z0-9_-]{20,}|ULTRAVOX_API_KEY\s*=\s*[^\s]+|Authorization:\s*Bearer\s+[A-Za-z0-9]|X-API-Key:\s*[A-Za-z0-9])"
)


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def fail(message: str) -> None:
    raise AssertionError(message)


def load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        fail(f"missing file: {rel(path)}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        fail(f"{rel(path)} must be a JSON object")
    return payload


def assert_no_secret_patterns(text: str) -> None:
    match = SECRET_PATTERN.search(text)
    if match:
        fail(f"secret-like token found: {match.group(0)!r}")


def main() -> None:
    result = load_json(RESULT_PATH)
    hosted = load_json(HOSTED_RESULT_PATH)
    report_text = REPORT_PATH.read_text(encoding="utf-8") if REPORT_PATH.is_file() else ""
    if not report_text:
        fail(f"missing file: {rel(REPORT_PATH)}")
    assert_no_secret_patterns(json.dumps(result) + json.dumps(hosted) + report_text)

    if result.get("evaluation_id") != "ULTRAVOX-HOSTED-SANDBOX-QUALITY-001":
        fail("unexpected quality evaluation_id")
    if result.get("sandbox_run") != hosted.get("sandbox_run"):
        fail("quality sandbox_run must match hosted evidence")
    if result.get("provider_call_made") != hosted.get("provider_call_made"):
        fail("quality provider_call_made must match hosted evidence")
    if result.get("synthetic_case_count") not in {0, 1, 2, 3}:
        fail("hosted synthetic_case_count must stay within 0..3")

    zero_count_fields = (
        "product_truth_drift_count",
        "unsupported_claim_count",
        "fake_side_effect_count",
        "crm_email_calendar_claim_count",
        "internal_label_leak_count",
        "source_boundary_violation_count",
        "memory_conflict_count",
    )
    for field in zero_count_fields:
        if result.get(field) != 0:
            fail(f"{field} must be 0 for this safe smoke")
    for field in ("raw_audio_stored", "audio_committed", "live_wiring_allowed", "production_call_allowed", "runtime_behavior_changed", "response_text_changed"):
        if result.get(field) is not False:
            fail(f"{field} must be false")
    if result.get("outbound_phone_call_made") is not False:
        fail("quality evidence must record no outbound phone call")
    if "user reported about 30 minutes free use; phase intentionally minimal" not in result.get("provider_minutes_budget_note", ""):
        fail("quality evidence must preserve provider minutes budget note")
    if "Quality decision" not in report_text:
        fail("quality report missing decision section")
    print("ULTRAVOX hosted sandbox quality validation passed.")


if __name__ == "__main__":
    main()
