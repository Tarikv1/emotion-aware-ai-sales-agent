#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from prosody_quality_common import assert_common_no_side_effects, load_json


ROOT = Path(__file__).resolve().parents[1]
AUDIT_RESULT = ROOT / "research" / "experiments" / "generated" / "ELEVENLABS-PROSODY-MAPPING-QUALITY-AUDIT-001" / "result.json"
DECISION_DIR = ROOT / "research" / "experiments" / "generated" / "ELEVENLABS-PROSODY-MAPPING-DECISION-001"
DECISION_RESULT = DECISION_DIR / "result.json"
DECISION_REPORT = DECISION_DIR / "report.md"


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def main() -> int:
    failures: list[str] = []
    for path in (AUDIT_RESULT, DECISION_RESULT, DECISION_REPORT):
        if not path.is_file():
            failures.append(f"missing file: {rel(path)}")
    audit = load_json(AUDIT_RESULT) if AUDIT_RESULT.is_file() else {}
    decision = load_json(DECISION_RESULT) if DECISION_RESULT.is_file() else {}

    if decision:
        recommendation = str(decision.get("recommendation") or "")
        recommendation_lower = recommendation.lower()
        for key in (
            "live_wiring_allowed",
            "provider_calls_made",
            "elevenlabs_calls_made",
            "response_text_changed",
            "runtime_behavior_changed",
        ):
            if decision.get(key) is not False:
                failures.append(f"decision.{key} must be false")
        if decision.get("does_not_claim_live_readiness") is not True:
            failures.append("decision must explicitly avoid live readiness claim")
        if "provider" in recommendation_lower or "elevenlabs" in recommendation_lower:
            if "future" not in recommendation_lower or "approval" not in recommendation_lower:
                failures.append("provider-test recommendation must be future-only and approval-gated")
        if "live" in recommendation_lower and "not live" not in recommendation_lower and "live_wiring_allowed false" not in recommendation_lower:
            failures.append("decision recommendation must not claim live readiness")
        if audit:
            blocking_failures = int(audit.get("blocking_failure_count") or 0)
            warning_count = int(audit.get("warning_count") or 0)
            if blocking_failures and "cleanup" not in recommendation_lower:
                failures.append("blocking failures require mapping cleanup before any provider test")
            if not blocking_failures and warning_count and "human review" not in recommendation_lower:
                failures.append("warnings require no-provider human review recommendation")
            if not blocking_failures and not warning_count:
                if "future" not in recommendation_lower or "provider-call approval" not in recommendation_lower:
                    failures.append("clean decision must recommend only future approval-gated sample generation")
        failures.extend(assert_common_no_side_effects(decision))

    output = {
        "status": "pass" if not failures else "fail",
        "decision_result": rel(DECISION_RESULT),
        "recommendation": decision.get("recommendation") if decision else None,
        "provider_calls_made": False,
        "elevenlabs_calls_made": False,
        "live_wiring_allowed": False,
        "runtime_behavior_changed": False,
        "response_text_changed": False,
        "failures": failures,
    }
    print(json.dumps(output, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
