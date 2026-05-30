from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any


sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.action_selector.runtime_action_metadata_extractor import extract_runtime_action_metadata  # noqa: E402


def normal_continuation_runtime_result() -> dict[str, Any]:
    return {
        "campaign_id": "phase-4k9-test-generic",
        "turn_id": "phase_4k9_no_asr_negative_signal",
        "selected_action": {"action_id": "continue_with_session_policy", "call_control": "continue-call"},
        "state_before": {
            "contextual_buyer_semantics": {"semantic": "continue_with_session_policy"},
            "universal_policy_frame": {"enforcement_reason": "no_asr_repair_required"},
        },
        "continuity": {"universal_policy_frame": {"enforcement_reason": "no_asr_repair_required"}},
        "candidate_response": "Sure, what is the main workflow issue you want checked?",
    }


def explicit_asr_runtime_result() -> dict[str, Any]:
    return {
        "campaign_id": "phase-4k9-test-generic",
        "turn_id": "phase_4k9_positive_asr_signal",
        "runtime_decision": {
            "next_action": "asr_uncertainty uncertain_tool ambiguous_tool",
            "response_mode": "repair",
            "selected_strategy": "repair_asr_uncertainty",
            "call_control": "continue-call",
        },
        "semantic_frame": {
            "semantic": "asr_uncertainty",
            "dialogue_focus": "repair",
            "response_strategy": "repair_asr_uncertainty",
            "candidate_response": "Sorry, did you mean Claude or cloud?",
        },
    }


def main() -> int:
    cases = [
        (
            "normal_continuation_with_negative_asr_marker_stays_unmapped",
            normal_continuation_runtime_result(),
            "",
        ),
        (
            "explicit_asr_tool_ambiguity_still_maps_to_repair",
            explicit_asr_runtime_result(),
            "repair_asr_uncertainty",
        ),
    ]
    failures: list[str] = []
    observations: list[dict[str, Any]] = []
    for case_id, runtime_result, expected_action_id in cases:
        metadata = extract_runtime_action_metadata(
            runtime_result,
            {
                "campaign_id": runtime_result["campaign_id"],
                "turn_id": runtime_result["turn_id"],
            },
        )
        actual = str(metadata.get("runtime_action_id") or "")
        observations.append(
            {
                "case_id": case_id,
                "expected_runtime_action_id": expected_action_id,
                "actual_runtime_action_id": actual,
                "runtime_repair_state": str(metadata.get("runtime_repair_state") or ""),
                "runtime_action_reason": str(metadata.get("runtime_action_reason") or ""),
            }
        )
        if actual != expected_action_id:
            failures.append(f"{case_id}: expected {expected_action_id!r}, got {actual!r}")

    print(
        json.dumps(
            {
                "validator": "validate_phase_4k9_runtime_metadata_asr_mapping_001",
                "status": "pass" if not failures else "fail",
                "failure_count": len(failures),
                "failures": failures,
                "observations": observations,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
