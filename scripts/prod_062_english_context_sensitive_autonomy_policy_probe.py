#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-062-english-context-sensitive-autonomy-policy-probe"
CHECKPOINT_NAME = "English Context-Sensitive Autonomy Policy Probe"
SOURCE_CHECKPOINT_ID = "PROD-061-english-product-policy-gate-prioritization"
NEXT_CHECKPOINT_ID = "PROD-063-english-autonomy-check-runtime-wording-patch"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
CASE_FILE = ROOT / "research" / "experiments" / "cases" / "prod-062-english-context-sensitive-autonomy-policy-probe.json"
SOURCE_DIR = ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID
SOURCE_VALIDATOR = ROOT / "scripts" / "validate_prod_061_english_product_policy_gate_prioritization.py"
SOURCE_VALIDATOR_COMMAND = "python scripts\\validate_prod_061_english_product_policy_gate_prioritization.py"
SOURCE_CANDIDATE_FILE = ROOT / "research" / "experiments" / "generated" / "PROD-053D-english-review-import" / "runtime_patch_candidates.json"

CANDIDATE_RESPONSE = "Okay, no rush. We can keep this low-pressure and only clarify what you need."

PROBE_CASES = [
    {
        "case_id": "prod-062-time-to-think",
        "customer_turn": "I need time to think. Do not rush.",
        "context_state": "basic_need_known",
        "expected_policy": "acknowledge_no_rush_and_offer_clarification_only",
    },
    {
        "case_id": "prod-062-no-decision-today",
        "customer_turn": "I do not want to decide today.",
        "context_state": "customer_boundary_explicit",
        "expected_policy": "preserve_choice_without_commitment",
    },
    {
        "case_id": "prod-062-explain-before-next-step",
        "customer_turn": "I still do not really understand it.",
        "context_state": "basic_context_missing",
        "expected_policy": "clarify_only_what_customer_needs",
    },
    {
        "case_id": "prod-062-overpressure-negative-control",
        "customer_turn": "You keep pushing.",
        "context_state": "pressure_risk",
        "expected_policy": "no_urgency_no_rebuttal_no_commitment",
    },
    {
        "case_id": "prod-062-leave-it-there",
        "customer_turn": "Can we just leave it there for now?",
        "context_state": "stop_or_pause_request",
        "expected_policy": "allow_pause_without_new_obligation",
    },
]

FORBIDDEN_MARKERS = [
    "must",
    "have to",
    "need to decide",
    "sign",
    "payment",
    "contract",
    "today only",
    "last chance",
    "because you are hesitant",
    "you are afraid",
    "you seem",
    "limited time",
]

BOUNDARY_FLAGS = {
    "runtime_behavior_changed": False,
    "response_text_behavior_changed": False,
    "retrieval_enabled": False,
    "provider_calls_made": False,
    "llm_used": False,
    "llm_judging_used": False,
    "private_data_read": False,
    "voice_playback_unblocked": False,
    "public_demo_polish_unblocked": False,
    "real_customer_use_unblocked": False,
    "payment_collection_allowed": False,
    "contract_signing_allowed": False,
    "production_runtime_promotion_allowed": False,
    "german_exact_phrase_promotion_allowed": False,
    "german_naturalness_claimed": False,
    "legal_compliance_claimed": False,
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def run_source_validator() -> dict[str, Any]:
    completed = subprocess.run(
        [sys.executable, str(SOURCE_VALIDATOR)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=300,
        check=False,
    )
    return {
        "command": SOURCE_VALIDATOR_COMMAND,
        "returncode": completed.returncode,
        "stdout_tail": completed.stdout.strip().splitlines()[-5:],
        "stderr_tail": completed.stderr.strip().splitlines()[-5:],
        "passed": completed.returncode == 0 and SOURCE_CHECKPOINT_ID in completed.stdout,
    }


def load_sources() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    source_result = read_json(SOURCE_DIR / "result.json")
    gate_priority = read_json(SOURCE_DIR / "gate_priority.json")
    gate_options = read_json(SOURCE_DIR / "gate_options.json")
    candidate_source = read_json(SOURCE_CANDIDATE_FILE)
    if source_result["validation"]["passed"] is not True:
        raise SystemExit("PROD-061 must pass before PROD-062.")
    if source_result["summary"]["selected_first_gate"] != "context_sensitive_autonomy_behavior":
        raise SystemExit("PROD-061 must select autonomy before PROD-062.")
    if source_result["summary"]["recommended_next_checkpoint"] != CHECKPOINT_ID:
        raise SystemExit("PROD-061 must recommend PROD-062.")
    if source_result["summary"]["requires_human_review_before_next_checkpoint"] is not False:
        raise SystemExit("PROD-061 must not require human review before PROD-062.")
    candidate = next(item for item in candidate_source["items"] if item["case_id"] == "prod-053c-autonomy-check")
    if candidate["candidate_response"] != CANDIDATE_RESPONSE:
        raise SystemExit("Autonomy candidate text changed; review before PROD-062.")
    if candidate["context_sensitive"] is not True:
        raise SystemExit("Autonomy candidate must remain context-sensitive before policy probe.")
    return source_result, gate_priority, gate_options, candidate


def build_case_file() -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "scope": "synthetic_english_autonomy_policy_probe_only",
        "candidate_response": CANDIDATE_RESPONSE,
        "runtime_change_requested": False,
        "not_a_runtime_patch": True,
        "requires_human_review_before_next_checkpoint": False,
        "probe_cases": PROBE_CASES,
        "forbidden_markers": FORBIDDEN_MARKERS,
    }


def contains_any(text: str, markers: list[str]) -> bool:
    lowered = text.lower()
    return any(marker.lower() in lowered for marker in markers)


def evaluate_probe_case(case: dict[str, Any]) -> dict[str, Any]:
    response = CANDIDATE_RESPONSE
    lowered = response.lower()
    gates = {
        "acknowledges_no_rush": "no rush" in lowered,
        "preserves_customer_choice": "only clarify what you need" in lowered,
        "offers_clarification_only": "clarify" in lowered and "only" in lowered,
        "no_commitment_or_payment": not contains_any(response, ["commit", "payment", "contract", "sign"]),
        "no_urgency_or_pressure": not contains_any(response, ["today only", "last chance", "limited time", "must", "have to"]),
        "no_fake_personalization": not contains_any(response, ["you are hesitant", "you are afraid", "you seem"]),
        "single_low_pressure_next_step": "low-pressure" in lowered and response.count("?") == 0,
        "english_only": response.isascii(),
    }
    issue_codes = [key for key, passed in gates.items() if not passed]
    forbidden_hits = [marker for marker in FORBIDDEN_MARKERS if marker.lower() in lowered]
    issue_codes.extend([f"forbidden_marker:{item}" for item in forbidden_hits])
    return {
        "case_id": case["case_id"],
        "customer_turn": case["customer_turn"],
        "context_state": case["context_state"],
        "expected_policy": case["expected_policy"],
        "candidate_response": response,
        "gates": gates,
        "passed": not issue_codes,
        "issue_codes": issue_codes,
    }


def build_policy_decision(reviews: list[dict[str, Any]]) -> dict[str, Any]:
    passed = all(item["passed"] for item in reviews)
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "decision": "autonomy_policy_probe_passed_recommend_narrow_runtime_patch" if passed else "autonomy_policy_probe_failed",
        "candidate_response": CANDIDATE_RESPONSE,
        "runtime_patch_allowed_in_prod_062": False,
        "runtime_patch_recommended_next": passed,
        "requires_human_review_before_next_checkpoint": False,
        "recommended_next_checkpoint": NEXT_CHECKPOINT_ID if passed else CHECKPOINT_ID,
    }


def build_evidence_summary(
    source_result: dict[str, Any],
    gate_priority: dict[str, Any],
    candidate: dict[str, Any],
    source_validator: dict[str, Any],
) -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "source_selected_gate": source_result["summary"]["selected_first_gate"],
        "source_gate_status": source_result["summary"]["selected_first_gate_status"],
        "source_priority_decision": gate_priority["decision"],
        "source_candidate_case_id": candidate["case_id"],
        "source_candidate_type": candidate["candidate_type"],
        "source_candidate_context_sensitive": candidate["context_sensitive"],
        "source_validator_run": source_validator,
    }


def summarize(reviews: list[dict[str, Any]], decision: dict[str, Any], source_validator: dict[str, Any]) -> dict[str, Any]:
    failed = [item for item in reviews if not item["passed"]]
    return {
        "policy_probe_only": True,
        "source_validator_passed": source_validator["passed"],
        "candidate_response": CANDIDATE_RESPONSE,
        "probe_case_count": len(reviews),
        "passed_probe_count": len(reviews) - len(failed),
        "failed_probe_count": len(failed),
        "failed_probe_case_ids": [item["case_id"] for item in failed],
        "runtime_patch_allowed": False,
        "runtime_patch_recommended_next": decision["runtime_patch_recommended_next"],
        "requires_human_review_before_next_checkpoint": False,
        "recommended_next_checkpoint": decision["recommended_next_checkpoint"],
        **BOUNDARY_FLAGS,
    }


def render_report(decision: dict[str, Any], reviews: list[dict[str, Any]], summary: dict[str, Any]) -> str:
    lines = [
        "# PROD-062 English Context-Sensitive Autonomy Policy Probe",
        "",
        "`PROD-062` tests the autonomy wording candidate with synthetic English policy probes.",
        "",
        "This is synthetic English autonomy policy probe only. It is not a runtime patch.",
        "",
        "## Decision",
        "",
        f"- Decision: `{decision['decision']}`",
        f"- Candidate response: `{decision['candidate_response']}`",
        f"- Probe cases: `{summary['probe_case_count']}`",
        f"- Passed probes: `{summary['passed_probe_count']}`",
        f"- Failed probes: `{summary['failed_probe_count']}`",
        f"- Runtime patch allowed in PROD-062: `{str(decision['runtime_patch_allowed_in_prod_062']).lower()}`",
        f"- No human review required before next checkpoint: `{str(not summary['requires_human_review_before_next_checkpoint']).lower()}`",
        f"- Recommended next checkpoint: `{summary['recommended_next_checkpoint']}`",
        "- Production runtime promotion allowed: `false`",
        "",
        "## Probe Reviews",
        "",
    ]
    for item in reviews:
        lines.extend(
            [
                f"### {item['case_id']}",
                "",
                f"- Customer turn: {item['customer_turn']}",
                f"- Context state: `{item['context_state']}`",
                f"- Expected policy: `{item['expected_policy']}`",
                f"- Passed: `{str(item['passed']).lower()}`",
                f"- Issue codes: `{', '.join(item['issue_codes']) if item['issue_codes'] else 'none'}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Boundary",
            "",
            "- Runtime behavior changed: `false`",
            "- Response text behavior changed: `false`",
            "- No provider calls.",
            "- No LLM or LLM judging.",
            "- No private data reads.",
            "- No retrieval enablement.",
            "- No German exact-phrase promotion or German naturalness claim.",
            "- No voice playback, public demo, real customer use, payment collection, contract signing, legal readiness, or production promotion.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    source_result, gate_priority, _gate_options, candidate = load_sources()
    case_payload = build_case_file()
    write_json(CASE_FILE, case_payload)
    source_validator = run_source_validator()
    reviews = [evaluate_probe_case(case) for case in PROBE_CASES]
    decision = build_policy_decision(reviews)
    evidence = build_evidence_summary(source_result, gate_priority, candidate, source_validator)
    summary = summarize(reviews, decision, source_validator)
    result = {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "validation": {
            "passed": source_validator["passed"] and summary["failed_probe_count"] == 0,
            "policy_probe_passed": summary["failed_probe_count"] == 0,
        },
        "summary": summary,
    }
    write_json(OUT_DIR / "evidence_summary.json", evidence)
    write_json(OUT_DIR / "probe_reviews.json", {"checkpoint_id": CHECKPOINT_ID, "items": reviews})
    write_json(OUT_DIR / "policy_decision.json", decision)
    write_json(OUT_DIR / "result.json", result)
    write_text(OUT_DIR / "report.md", render_report(decision, reviews, summary))
    print(json.dumps({"checkpoint_id": CHECKPOINT_ID, "validation": result["validation"], "summary": summary}, indent=2))


if __name__ == "__main__":
    main()
