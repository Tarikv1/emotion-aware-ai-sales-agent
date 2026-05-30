from __future__ import annotations

import ast
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.action_selector.non_llm_action_selector import RuleBasedActionSelector

CHECKPOINT_ID = "PHASE-4K11-BOUNDARY-SENSITIVE-SELECTOR-GENERALIZATION-001"
GENERATED = ROOT / "research" / "experiments" / "generated"
OUT_DIR = GENERATED / CHECKPOINT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"
REVIEW_SCRIPT = ROOT / "scripts" / "review_phase_4k11_boundary_sensitive_selector_generalization_001.py"
VALIDATOR_SCRIPT = ROOT / "scripts" / "validate_phase_4k11_boundary_sensitive_selector_generalization_001.py"

RECONCILIATION_4K10A_ID = "PHASE-4K10A-SELECTOR-RUNTIME-RECONCILIATION-001"
REPAIR_4K10_ID = "PHASE-4K10-SPOKEN-RESPONSE-REPAIR-001"
EXPANSION_ID = "NON-LLM-ACTION-SELECTOR-RUNTIME-SHADOW-EXPANSION-001"
RECONCILIATION_4K10A_RESULT = GENERATED / RECONCILIATION_4K10A_ID / "result.json"
REPAIR_4K10_RESULT = GENERATED / REPAIR_4K10_ID / "result.json"
EXPANSION_RESULT = GENERATED / EXPANSION_ID / "result.json"
EXPANSION_JSONL = GENERATED / EXPANSION_ID / "shadow_expansion_records.jsonl"

TARGET_CASE_ID = "phase_4k8_b2b_saas_003"
TARGET_UTTERANCE = "Does it integrate securely with Salesforce?"
REQUIRED_DEFERRED_LIVE_DEMOS = ["LIVE-DEMO-002", "LIVE-DEMO-009", "LIVE-DEMO-014"]

POSITIVE_CASES = [
    "Does it integrate securely with Salesforce?",
    "Can you guarantee Salesforce integration works?",
    "Is it compliant with our security requirements?",
    "Can you prove HubSpot integration is secure?",
    "Can you guarantee the CRM setup?",
]

NEGATIVE_CASES = [
    "What CRM does this work with at a high level?",
    "How does the workflow routing work?",
    "What does the integration review check?",
    "Is this about CRM follow-up reminders?",
    "What kind of security details would a reviewer need?",
    "Can you explain the setup process at a high level?",
]

FALSE_FLAG_KEYS = [
    "provider_calls_made",
    "model_calls_made",
    "openai_api_calls_made",
    "ultravox_calls_made",
    "elevenlabs_calls_made",
    "local_llm_calls_made",
    "ollama_calls_made",
    "tts_calls_made",
    "crm_calls_made",
    "email_calls_made",
    "calendar_calls_made",
    "selector_control_allowed",
    "live_selector_control_recommended",
    "response_replacement_performed",
    "side_effects_allowed",
    "response_text_changed",
    "runtime_behavior_changed",
    "raw_private_data",
]

FORBIDDEN_IMPORT_ROOTS = {"elevenlabs", "httpx", "openai", "requests", "ultravox", "urllib"}
FORBIDDEN_PUBLIC_SHADOW_KEYS = {
    "candidate_response",
    "response_text",
    "agent_response",
    "final_response",
    "audio",
    "audio_path",
    "audio_file",
    "wav_path",
    "mp3_path",
    "raw_url",
}


def read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        payload = json.loads(stripped)
        if not isinstance(payload, dict):
            raise ValueError(f"{path}:{line_number} is not a JSON object")
        rows.append(payload)
    return rows


def imported_roots(path: Path) -> set[str]:
    if not path.is_file():
        return set()
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                roots.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".")[0])
    return roots


def selector_matrix() -> list[dict[str, Any]]:
    selector = RuleBasedActionSelector()
    rows: list[dict[str, Any]] = []
    for expected_group, utterances in [("positive", POSITIVE_CASES), ("negative", NEGATIVE_CASES)]:
        for index, utterance in enumerate(utterances, start=1):
            output = selector.select({"buyer_utterance_text": utterance})
            expected_action_id = "respect_boundary" if expected_group == "positive" else "not_respect_boundary"
            passed = output.action_id == "respect_boundary" if expected_group == "positive" else output.action_id != "respect_boundary"
            rows.append(
                {
                    "case_id": f"4k11_{expected_group}_{index:03d}",
                    "utterance": utterance,
                    "expected_group": expected_group,
                    "expected_action_id": expected_action_id,
                    "selector_action_id": output.action_id,
                    "selector_confidence": output.confidence,
                    "selector_reasons": output.reasons,
                    "selector_matched_features": output.matched_features,
                    "passed": passed,
                }
            )
    return rows


def nested_key_hits(value: Any, forbidden: set[str]) -> list[str]:
    hits: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key) in forbidden:
                hits.append(str(key))
            hits.extend(nested_key_hits(child, forbidden))
    elif isinstance(value, list):
        for child in value:
            hits.extend(nested_key_hits(child, forbidden))
    return hits


def validate_result_shape(failures: list[str], result: dict[str, Any]) -> None:
    if result.get("checkpoint_id") != CHECKPOINT_ID:
        failures.append("checkpoint_id mismatch")
    if result.get("status") != "pass":
        failures.append(f"status must be pass: {result.get('status')}")
    if not REPORT_PATH.is_file():
        failures.append("report.md missing")
    matrix = result.get("selector_matrix")
    validate_live_selector_matrix(failures)
    if not isinstance(matrix, list):
        failures.append("selector_matrix must be a list")
        return
    if len(matrix) != len(POSITIVE_CASES) + len(NEGATIVE_CASES):
        failures.append(f"selector_matrix row count mismatch: {len(matrix)}")
    by_utterance = {str(row.get("utterance")): row for row in matrix if isinstance(row, dict)}
    for expected in POSITIVE_CASES + NEGATIVE_CASES:
        if expected not in by_utterance:
            failures.append(f"selector_matrix missing utterance: {expected}")
    direct_rows = selector_matrix()
    for direct in direct_rows:
        recorded = by_utterance.get(direct["utterance"])
        if not isinstance(recorded, dict):
            continue
        if recorded.get("selector_action_id") != direct["selector_action_id"]:
            failures.append(
                f"{direct['case_id']} recorded selector_action_id does not match live selector: "
                f"{recorded.get('selector_action_id')} != {direct['selector_action_id']}"
            )
        if recorded.get("passed") is not direct["passed"]:
            failures.append(f"{direct['case_id']} recorded pass flag does not match live selector")
    summary = result.get("selector_matrix_summary") if isinstance(result.get("selector_matrix_summary"), dict) else {}
    if summary.get("positive_pass_count") != len(POSITIVE_CASES):
        failures.append(f"positive_pass_count mismatch: {summary.get('positive_pass_count')}")
    if summary.get("negative_pass_count") != len(NEGATIVE_CASES):
        failures.append(f"negative_pass_count mismatch: {summary.get('negative_pass_count')}")


def validate_live_selector_matrix(failures: list[str]) -> None:
    direct_rows = selector_matrix()
    positives = [row for row in direct_rows if row["expected_group"] == "positive"]
    negatives = [row for row in direct_rows if row["expected_group"] == "negative"]
    for row in positives:
        if row["selector_action_id"] != "respect_boundary":
            failures.append(f"positive case must select respect_boundary: {row['utterance']} -> {row['selector_action_id']}")
    for row in negatives:
        if row["selector_action_id"] == "respect_boundary":
            failures.append(f"negative case must not select respect_boundary: {row['utterance']}")


def validate_prior_evidence(failures: list[str], result: dict[str, Any]) -> None:
    reconciliation = read_json(RECONCILIATION_4K10A_RESULT)
    repair = read_json(REPAIR_4K10_RESULT)
    expansion = read_json(EXPANSION_RESULT)
    target = reconciliation.get("target_case") if isinstance(reconciliation.get("target_case"), dict) else {}
    if target.get("case_id") != TARGET_CASE_ID or target.get("utterance") != TARGET_UTTERANCE:
        failures.append("4K10A target Salesforce case missing or changed")
    for key, expected in [
        ("runtime_action_id", "respect_boundary"),
        ("selector_action_id", "respect_boundary"),
        ("disagreement_review_classification", "same_action"),
        ("agreement_disagreement_type", "same_action"),
    ]:
        if target.get(key) != expected:
            failures.append(f"4K10A target {key} must be {expected}: {target.get(key)}")
    after = reconciliation.get("after") if isinstance(reconciliation.get("after"), dict) else {}
    if after.get("false_asr_mapping_count") != 0:
        failures.append(f"false_asr_mapping_count must remain 0: {after.get('false_asr_mapping_count')}")
    if after.get("genuine_selector_runtime_disagreement_count") not in {0, None}:
        failures.append(
            "genuine_selector_runtime_disagreement_count must remain 0 or documented non-actionable: "
            f"{after.get('genuine_selector_runtime_disagreement_count')}"
        )
    naturalness_count = repair.get("after_naturalness_issue_count")
    if int(naturalness_count or 999) > 14:
        failures.append(f"4K10 naturalness count must stay at or below 14: {naturalness_count}")
    route_signal = result.get("routesignal_deferred_status") if isinstance(result.get("routesignal_deferred_status"), dict) else {}
    for checkpoint in REQUIRED_DEFERRED_LIVE_DEMOS:
        payload = route_signal.get(checkpoint)
        if not isinstance(payload, dict):
            failures.append(f"{checkpoint} deferred status missing from 4K11 result")
            continue
        if payload.get("status") != "deferred_or_fail":
            failures.append(f"{checkpoint} must remain deferred_or_fail: {payload.get('status')}")
        if payload.get("intentionally_untouched_in_4k11") is not True:
            failures.append(f"{checkpoint} must be explicitly untouched in 4K11")
    for key in FALSE_FLAG_KEYS:
        expected = False
        value = result.get(key)
        if value is not expected:
            failures.append(f"4K11 result {key} must be false: {value}")
    if result.get("raw_candidate_responses_absent_from_public_shadow_records") is not True:
        failures.append("raw candidate responses must remain absent from public shadow records")
    if expansion.get("raw_candidate_response_recorded_count") != 0:
        failures.append("shadow expansion raw_candidate_response_recorded_count must remain 0")
    for key in ["provider_calls_made", "model_calls_made", "tts_calls_made", "crm_calls_made", "email_calls_made", "calendar_calls_made"]:
        if expansion.get(key) is not False:
            failures.append(f"shadow expansion {key} must remain false")


def validate_public_shadow_records(failures: list[str]) -> None:
    rows = read_jsonl(EXPANSION_JSONL)
    if not rows:
        failures.append("shadow expansion JSONL missing or empty")
        return
    for index, row in enumerate(rows, start=1):
        forbidden = sorted(FORBIDDEN_PUBLIC_SHADOW_KEYS & set(row))
        if forbidden:
            failures.append(f"shadow row[{index}] contains forbidden raw key(s): {forbidden}")
        if row.get("candidate_response_text_recorded") is not False:
            failures.append(f"shadow row[{index}] candidate_response_text_recorded must be false")


def validate_no_forbidden_imports(failures: list[str]) -> None:
    for path in [REVIEW_SCRIPT, VALIDATOR_SCRIPT]:
        found = sorted(imported_roots(path) & FORBIDDEN_IMPORT_ROOTS)
        if found:
            failures.append(f"{path.relative_to(ROOT)} imports forbidden provider/network modules: {found}")


def main() -> int:
    failures: list[str] = []
    result = read_json(RESULT_PATH)
    validate_no_forbidden_imports(failures)
    validate_result_shape(failures, result)
    validate_prior_evidence(failures, result)
    validate_public_shadow_records(failures)
    forbidden_result_keys = sorted(set(nested_key_hits(result, FORBIDDEN_PUBLIC_SHADOW_KEYS)))
    if forbidden_result_keys:
        failures.append(f"4K11 result contains forbidden raw response/audio key(s): {forbidden_result_keys}")
    print(
        json.dumps(
            {
                "validator": "validate_phase_4k11_boundary_sensitive_selector_generalization_001",
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
