from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any


sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.audit_spoken_human_naturalness_001 import audit_cases  # noqa: E402


REQUIRED_CATEGORIES = {
    "robotic_internal_wording",
    "overly_formal_or_policy_like",
    "empty_candidate_response",
    "missing_human_acknowledgment",
    "missing_sales_progression",
    "premature_scheduling_or_callback_push",
    "weak_value_framing",
    "repetitive_review_language",
    "too_long_for_spoken_call",
    "good_human_spoken_examples",
}


def case(case_id: str, response: str, sequence_index: int = 1) -> dict[str, Any]:
    return {
        "case_id": case_id,
        "campaign_coverage": "phase_4k9_naturalness_guard",
        "campaign_id": "phase-4k9-naturalness-guard",
        "vertical_id": "b2b_saas",
        "conversation_id": "phase_4k9_naturalness_guard",
        "sequence_index": sequence_index,
        "candidate_response": response,
    }


def main() -> int:
    categories = audit_cases(
        [
            case("phase_4k9_empty_response", ""),
            case("phase_4k9_robotic_phrase", "I should still tie that to your setup before I claim it."),
            case("phase_4k9_policy_phrase", "I cannot verify that claim here; exact setup fit needs verified material."),
            case(
                "phase_4k9_review_repetition",
                "A qualified human review is safer, with human review by a specialist before any recommendation.",
            ),
            case("phase_4k9_premature_time_question", "The next step is a short workflow review. What time works?"),
            case("phase_4k9_factual_no_ack", "It costs 20 dollars."),
            case("phase_4k9_good_spoken", "Got it. If manual work is slowing the team down, the useful check is whether that workflow is worth fixing first.", 2),
        ]
    )
    failures: list[str] = []
    missing = sorted(REQUIRED_CATEGORIES - set(categories))
    if missing:
        failures.append(f"missing categories: {missing}")
    required_hits = {
        "empty_candidate_response": "phase_4k9_empty_response",
        "robotic_internal_wording": "phase_4k9_robotic_phrase",
        "overly_formal_or_policy_like": "phase_4k9_policy_phrase",
        "repetitive_review_language": "phase_4k9_review_repetition",
        "premature_scheduling_or_callback_push": "phase_4k9_premature_time_question",
        "missing_human_acknowledgment": "phase_4k9_factual_no_ack",
        "missing_sales_progression": "phase_4k9_factual_no_ack",
        "good_human_spoken_examples": "phase_4k9_good_spoken",
    }
    for category, case_id in required_hits.items():
        payload = categories.get(category) if isinstance(categories.get(category), dict) else {}
        examples = payload.get("examples") if isinstance(payload.get("examples"), list) else []
        if not any(example.get("case_id") == case_id for example in examples if isinstance(example, dict)):
            failures.append(f"{category} did not include {case_id}")
    print(
        json.dumps(
            {
                "validator": "validate_phase_4k9_spoken_naturalness_audit_001",
                "status": "pass" if not failures else "fail",
                "failure_count": len(failures),
                "failures": failures,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
