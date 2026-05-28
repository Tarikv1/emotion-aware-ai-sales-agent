#!/usr/bin/env python3
from __future__ import annotations

import json

from prosody_quality_common import (
    ELEVENLABS_READINESS_DIR,
    ELEVENLABS_READINESS_PATH,
    assert_common_no_side_effects,
    load_json,
)


def main() -> int:
    failures: list[str] = []
    result_path = ELEVENLABS_READINESS_DIR / "result.json"
    report_path = ELEVENLABS_READINESS_DIR / "report.md"
    for path in (ELEVENLABS_READINESS_PATH, result_path, report_path):
        if not path.is_file():
            failures.append(f"missing file: {path}")
    plan = load_json(ELEVENLABS_READINESS_PATH) if ELEVENLABS_READINESS_PATH.is_file() else {}
    result = load_json(result_path) if result_path.is_file() else {}
    for payload, name in ((plan, "plan"), (result, "result")):
        if payload.get("current_voice_path") != "ElevenLabs":
            failures.append(f"{name}: current_voice_path must be ElevenLabs")
        if payload.get("fish_tags_in_elevenlabs_text_allowed") is not False:
            failures.append(f"{name}: Fish tags must not be allowed in ElevenLabs text")
        if payload.get("current_integration_status") != "not_wired":
            failures.append(f"{name}: integration status must be not_wired")
        if payload.get("elevenlabs_calls_made") is not False:
            failures.append(f"{name}: elevenlabs calls must be false")
        if payload.get("runtime_behavior_changed") is not False:
            failures.append(f"{name}: runtime behavior changed must be false")
        if payload.get("response_text_changed") is not False:
            failures.append(f"{name}: response text changed must be false")
    disallowed = set(plan.get("disallowed", []))
    for required in ("raw bracket tags", "fake laughter", "manipulative urgency", "internal policy language", "unsupported claims"):
        if required not in disallowed:
            failures.append(f"readiness plan missing disallowed item: {required}")
    gates = set(plan.get("required_future_gate_before_live", []))
    for required_gate in ("sample generation", "listening review", "no raw tag leakage"):
        if required_gate not in gates:
            failures.append(f"readiness plan missing gate: {required_gate}")
    failures.extend(assert_common_no_side_effects(result))
    output = {
        "status": "pass" if not failures else "fail",
        "plan": str(ELEVENLABS_READINESS_PATH),
        "current_integration_status": plan.get("current_integration_status"),
        "failures": failures,
    }
    print(json.dumps(output, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
