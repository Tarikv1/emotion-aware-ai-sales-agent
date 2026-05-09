from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-011-dialogue-policy-hardening"
SOURCE_CHECKPOINT = "PROD-010-long-call-universal-objections"
POLICY_ID = "brain_002_dialogue_policy_hardening_v1"

CASE_PATH = ROOT / "research" / "experiments" / "cases" / "prod-011-dialogue-policy-hardening.json"
RESULT_PATH = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID / "result.json"
REPORT_PATH = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID / "report.md"
DOC_PATH = ROOT / "docs" / "brain" / "PROD_011_DIALOGUE_POLICY_HARDENING.md"

REQUIRED_FILES = [
    ROOT / "scripts" / "dialogue_policy_hardening.py",
    ROOT / "scripts" / "run_prod_011_dialogue_policy_hardening.py",
    Path(__file__),
    CASE_PATH,
    RESULT_PATH,
    REPORT_PATH,
    DOC_PATH,
]

REQUIRED_CASE_LABELS = {
    "telecom_multi_objection_sale",
    "b2b_procurement_authority_delay",
    "insurance_privacy_claim_boundary",
    "medical_technical_safety_escalation",
    "membership_angry_refusal",
    "home_service_support_upsell_trap",
    "retail_multi_objection_sale",
}

REQUIRED_MARKERS = [
    "PROD-011",
    "dialogue-policy hardening",
    "BRAIN-002",
    "policy action correctness",
    "objection stack preservation",
    "blocked action avoidance",
    "retrieval disabled by default",
    "fixture candidate packets used: false",
]

BLOCKED_REPORT_STRINGS = [
    "credit card",
    "customer phone",
    "raw private audio",
    "raw private transcript",
    "api key",
    "provider call made",
    '"download_performed": true',
    '"provider_calls_made": true',
    '"private_data_read": true',
    '"candidate":',
]


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    sys.exit(1)


def read_json(path: Path) -> dict:
    if not path.exists():
        fail(f"missing required file: {path.relative_to(ROOT)}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"invalid json in {path.relative_to(ROOT)}: {exc}")


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def rate_is_one(metrics: dict, key: str) -> None:
    require(metrics.get(key) == 1.0, f"{key} must be 1.0, got {metrics.get(key)!r}")


def rate_is_zero(metrics: dict, key: str) -> None:
    require(metrics.get(key) == 0.0, f"{key} must be 0.0, got {metrics.get(key)!r}")


def validate_command_docs() -> None:
    commands = ROOT / "docs" / "product" / "COMMANDS.md"
    text = commands.read_text(encoding="utf-8") if commands.exists() else ""
    require(
        "python scripts\\run_prod_011_dialogue_policy_hardening.py" in text,
        "docs/product/COMMANDS.md must list the PROD-011 runner",
    )
    require(
        "python scripts\\validate_prod_011_dialogue_policy_hardening.py" in text,
        "docs/product/COMMANDS.md must list the PROD-011 validator",
    )


def validate_docs() -> None:
    for path in [DOC_PATH, REPORT_PATH]:
        text = path.read_text(encoding="utf-8")
        lowered = text.lower()
        for marker in REQUIRED_MARKERS:
            require(marker.lower() in lowered, f"{path.relative_to(ROOT)} missing marker: {marker}")
        for blocked in BLOCKED_REPORT_STRINGS:
            require(blocked.lower() not in lowered, f"{path.relative_to(ROOT)} includes blocked text: {blocked}")


def validate_payload(payload: dict) -> None:
    require(payload.get("prod_011_id") == CHECKPOINT_ID, "payload prod_011_id mismatch")
    require(payload.get("source_checkpoint") == SOURCE_CHECKPOINT, "payload source_checkpoint mismatch")
    require(payload.get("policy_id") == POLICY_ID, "payload policy_id mismatch")
    require(payload.get("runtime_behavior_changed") is False, "PROD-011 must not change runtime behavior")
    require(payload.get("retrieval_default") == "disabled", "retrieval must remain disabled by default")
    require(payload.get("fixture_candidate_packets_used") is False, "fixture candidate packets must not be used")
    require(payload.get("editable_surface") == "dialogue_policy_rules", "editable surface must be dialogue_policy_rules")

    protocol = payload.get("protocol", {})
    require(protocol.get("fixed_cases") is True, "protocol.fixed_cases must be true")
    require(protocol.get("dialogue_policy_hardening") is True, "protocol.dialogue_policy_hardening must be true")
    require(protocol.get("uses_prod_010_packet_evidence") is True, "protocol must use PROD-010 packet evidence")
    require(protocol.get("runtime_promotion") is False, "protocol.runtime_promotion must be false")
    require(protocol.get("dataset_download") is False, "protocol.dataset_download must be false")
    require(protocol.get("provider_calls") is False, "protocol.provider_calls must be false")
    require(protocol.get("private_data") is False, "protocol.private_data must be false")
    require(protocol.get("commercial_runtime_prompt_contamination") is False, "runtime prompt contamination must be false")

    boundaries = payload.get("boundaries", {})
    for key in [
        "provider_calls_made",
        "private_data_read",
        "dataset_download_performed",
        "commercial_runtime_prompt_contamination",
        "runtime_behavior_changed",
    ]:
        require(boundaries.get(key) is False, f"boundary {key} must be false")

    summary = payload.get("summary", {})
    require(summary.get("call_count", 0) >= 7, "call_count must be at least 7")
    require(summary.get("turn_count", 0) >= 49, "turn_count must be at least 49")
    require(summary.get("policy_decision_count") == summary.get("turn_count"), "one policy decision required per turn")
    require(summary.get("universal_objection_count", 0) >= 12, "must preserve at least 12 objection labels")
    require(summary.get("retrieval_enabled_count") == 0, "retrieval must remain disabled on every decision")
    require(summary.get("provider_calls_made") is False, "summary provider_calls_made must be false")
    require(summary.get("private_data_read") is False, "summary private_data_read must be false")
    require(summary.get("max_latency_ms", 9999) <= summary.get("acceptable_latency_ms", 0), "latency exceeds threshold")

    baseline = summary.get("baseline", {})
    hardened = summary.get("hardened", {})
    rate_is_zero(hardened, "hard_failure_rate")
    rate_is_one(hardened, "safe_close_rate")
    rate_is_one(hardened, "non_sale_correctness")
    rate_is_one(hardened, "policy_action_correctness")
    rate_is_one(hardened, "blocked_action_avoidance")
    rate_is_one(hardened, "objection_stack_preservation")
    rate_is_one(hardened, "state_reference_completeness")
    rate_is_one(hardened, "call_control_correctness")
    require(
        baseline.get("hard_failure_rate", 0.0) > hardened["hard_failure_rate"],
        "hardened policy must reduce hard failure rate",
    )
    require(
        baseline.get("policy_action_correctness", 1.0) < hardened["policy_action_correctness"],
        "hardened policy must improve policy action correctness",
    )
    require(
        baseline.get("non_sale_correctness", 1.0) < hardened["non_sale_correctness"],
        "hardened policy must improve non-sale correctness",
    )
    require(
        str(summary.get("decision", "")).startswith("keep_dialogue_policy"),
        "decision must keep dialogue-policy hardening as evidence, not runtime promotion",
    )


def validate_cases(case_data: dict, payload: dict) -> None:
    require(case_data.get("prod_011_id") == CHECKPOINT_ID, "case prod_011_id mismatch")
    require(case_data.get("source_checkpoint") == SOURCE_CHECKPOINT, "case source_checkpoint mismatch")
    require(case_data.get("fixture_candidate_packets_used") is False, "case file must not use fixture candidate packets")
    calls = case_data.get("calls", [])
    require(len(calls) >= 7, "case file must contain at least 7 calls")

    labels = {call.get("scenario_label") for call in calls}
    missing = REQUIRED_CASE_LABELS - labels
    require(not missing, f"case file missing labels: {sorted(missing)}")

    results_by_call = {call["call_id"]: call for call in payload.get("calls", [])}
    require(len(results_by_call) == len(calls), "result call count must match case call count")

    total_turns = 0
    for call in calls:
        call_id = call.get("call_id")
        result_call = results_by_call.get(call_id)
        require(result_call is not None, f"missing result call for {call_id}")
        require(call.get("source_checkpoint") == SOURCE_CHECKPOINT, f"{call_id} source checkpoint mismatch")
        objections = call.get("universal_objections", [])
        require(len(objections) >= 3, f"{call_id} must have at least three universal objections")
        turns = call.get("turns", [])
        decisions = result_call.get("policy_decisions", [])
        require(len(turns) >= 7, f"{call_id} must have at least 7 turns")
        require(len(decisions) == len(turns), f"{call_id} decision count must equal turn count")
        total_turns += len(turns)

        for index, (turn, decision) in enumerate(zip(turns, decisions), start=1):
            turn_id = turn.get("turn_id")
            require(decision.get("turn_id") == turn_id, f"{call_id}/{turn_id} decision turn_id mismatch")
            require(decision.get("policy_action") == turn.get("expected_policy_action"), f"{call_id}/{turn_id} policy action mismatch")
            require(decision.get("call_control") == turn.get("expected_call_control"), f"{call_id}/{turn_id} call control mismatch")
            require(decision.get("hard_failure") is False, f"{call_id}/{turn_id} has hard failure")
            require(decision.get("retrieval_enabled") is False, f"{call_id}/{turn_id} enabled retrieval")
            require(decision.get("provider_calls_made") is False, f"{call_id}/{turn_id} made provider call")
            require(decision.get("private_data_read") is False, f"{call_id}/{turn_id} read private data")
            require(decision.get("blocked_actions_avoided") is True, f"{call_id}/{turn_id} did not avoid blocked actions")
            require(decision.get("universal_objections_seen") == objections, f"{call_id}/{turn_id} objection stack mismatch")
            ref = decision.get("source_packet_reference", {})
            require(ref.get("source_checkpoint") == SOURCE_CHECKPOINT, f"{call_id}/{turn_id} source reference checkpoint mismatch")
            require(ref.get("call_id") == call_id, f"{call_id}/{turn_id} source reference call_id mismatch")
            require(ref.get("turn_id") == turn_id, f"{call_id}/{turn_id} source reference turn_id mismatch")
            require(ref.get("turn_position") == index, f"{call_id}/{turn_id} source reference position mismatch")

        expected = call.get("expected_final", {})
        final = result_call.get("final_policy", {})
        require(final.get("policy_action") == expected.get("policy_action"), f"{call_id} final policy action mismatch")
        require(final.get("call_control") == expected.get("call_control"), f"{call_id} final call control mismatch")
        require(final.get("sale_ready") == expected.get("sale_ready"), f"{call_id} final sale_ready mismatch")
        require(final.get("non_sale_correct") == expected.get("non_sale_correct"), f"{call_id} final non_sale_correct mismatch")

    require(total_turns >= 49, "total turns must be at least 49")


def main() -> None:
    missing = [path.relative_to(ROOT) for path in REQUIRED_FILES if not path.exists()]
    if missing:
        fail(f"missing required files: {missing}")

    validate_command_docs()
    case_data = read_json(CASE_PATH)
    payload = read_json(RESULT_PATH)
    validate_payload(payload)
    validate_cases(case_data, payload)
    validate_docs()
    print("PASS: PROD-011 dialogue-policy hardening artifacts are valid")


if __name__ == "__main__":
    main()
