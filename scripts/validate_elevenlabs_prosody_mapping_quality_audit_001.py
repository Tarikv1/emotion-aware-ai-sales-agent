#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from prosody_quality_common import assert_common_no_side_effects, load_json


ROOT = Path(__file__).resolve().parents[1]
PROTOTYPE_DIR = ROOT / "research" / "experiments" / "generated" / "ELEVENLABS-PROSODY-MAPPING-PROTOTYPE-001"
AUDIT_DIR = ROOT / "research" / "experiments" / "generated" / "ELEVENLABS-PROSODY-MAPPING-QUALITY-AUDIT-001"
PROTOTYPE_RESULT = PROTOTYPE_DIR / "result.json"
AUDIT_RESULT = AUDIT_DIR / "result.json"
AUDIT_REPORT = AUDIT_DIR / "report.md"

REQUIRED_COUNT_FIELDS = {
    "example_count",
    "shaped_text_contains_raw_fish_tags_count",
    "shaped_text_contains_internal_labels_count",
    "style_prompt_contains_unsafe_instruction_count",
    "voice_settings_hint_missing_count",
    "provider_call_required_count",
    "live_wiring_allowed_count",
    "terminal_close_asks_new_question_count",
    "boundary_response_continues_pressure_count",
    "already_told_you_repeats_question_count",
    "asr_uncertainty_uses_internal_confidence_language_count",
    "source_affiliation_overclaims_count",
    "fake_side_effect_count",
    "raw_url_speech_count",
    "overexcited_sales_voice_count",
    "manipulative_urgency_count",
    "too_long_for_phone_count",
    "too_many_questions_count",
    "unnatural_text_shape_count",
}
BLOCKING_COUNT_FIELDS = {
    "shaped_text_contains_raw_fish_tags_count",
    "shaped_text_contains_internal_labels_count",
    "style_prompt_contains_unsafe_instruction_count",
    "provider_call_required_count",
    "live_wiring_allowed_count",
    "fake_side_effect_count",
    "raw_url_speech_count",
    "manipulative_urgency_count",
}


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def main() -> int:
    failures: list[str] = []
    for path in (PROTOTYPE_RESULT, AUDIT_RESULT, AUDIT_REPORT):
        if not path.is_file():
            failures.append(f"missing file: {rel(path)}")
    prototype = load_json(PROTOTYPE_RESULT) if PROTOTYPE_RESULT.is_file() else {}
    audit = load_json(AUDIT_RESULT) if AUDIT_RESULT.is_file() else {}
    examples = prototype.get("examples", []) if isinstance(prototype.get("examples"), list) else []
    classifications = audit.get("example_classifications", []) if isinstance(audit.get("example_classifications"), list) else []

    if audit:
        missing_counts = sorted(REQUIRED_COUNT_FIELDS - set(audit))
        if missing_counts:
            failures.append(f"audit missing count fields: {missing_counts}")
        if audit.get("example_count") != len(examples):
            failures.append("audit.example_count must match prototype example count")
        if audit.get("example_count", 0) < 60:
            failures.append(f"audit.example_count must be >= 60, got {audit.get('example_count')}")
        if len(classifications) != audit.get("example_count"):
            failures.append("audit.example_classifications length must match example_count")
        status_counts = audit.get("status_counts")
        if not isinstance(status_counts, dict):
            failures.append("audit.status_counts must be an object")
        else:
            total = sum(int(status_counts.get(key, 0)) for key in ("pass", "warning", "fail", "needs_human_review"))
            if total != audit.get("example_count"):
                failures.append("audit.status_counts must sum to example_count")
        for field in BLOCKING_COUNT_FIELDS:
            if int(audit.get(field) or 0) != 0:
                failures.append(f"audit.{field} must be 0")
        for key in (
            "provider_calls_made",
            "elevenlabs_calls_made",
            "live_tts_calls_made",
            "runtime_behavior_changed",
            "response_text_changed",
        ):
            if audit.get(key) is not False:
                failures.append(f"audit.{key} must be false")
        for item in classifications:
            if not isinstance(item, dict):
                failures.append("audit.example_classifications entries must be objects")
                continue
            if item.get("status") not in {"pass", "warning", "fail", "needs_human_review"}:
                failures.append(f"{item.get('example_id')}: invalid status {item.get('status')}")
            if item.get("provider_call_required") is not False:
                failures.append(f"{item.get('example_id')}: provider_call_required must be false")
            if item.get("live_wiring_allowed") is not False:
                failures.append(f"{item.get('example_id')}: live_wiring_allowed must be false")
        failures.extend(assert_common_no_side_effects(audit))

    output = {
        "status": "pass" if not failures else "fail",
        "audit_result": rel(AUDIT_RESULT),
        "example_count": audit.get("example_count", 0) if audit else 0,
        "status_counts": audit.get("status_counts", {}) if audit else {},
        "provider_calls_made": False,
        "elevenlabs_calls_made": False,
        "runtime_behavior_changed": False,
        "response_text_changed": False,
        "failures": failures,
    }
    print(json.dumps(output, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
