from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
EXPANSION_ID = "NON-LLM-ACTION-SELECTOR-RUNTIME-SHADOW-EXPANSION-001"
NATURALNESS_ID = "SPOKEN-HUMAN-NATURALNESS-AUDIT-001"
GENERATED = ROOT / "research" / "experiments" / "generated"
EXPANSION_DIR = GENERATED / EXPANSION_ID
NATURALNESS_DIR = GENERATED / NATURALNESS_ID
EXPANSION_RESULT_PATH = EXPANSION_DIR / "result.json"
EXPANSION_REPORT_PATH = EXPANSION_DIR / "report.md"
DECISION_REPORT_PATH = EXPANSION_DIR / "decision_report.md"
EXPANSION_JSONL_PATH = EXPANSION_DIR / "shadow_expansion_records.jsonl"
NATURALNESS_RESULT_PATH = NATURALNESS_DIR / "result.json"
NATURALNESS_REPORT_PATH = NATURALNESS_DIR / "report.md"

RUNNER_PATH = ROOT / "scripts" / "run_non_llm_action_selector_runtime_shadow_expansion_001.py"
VALIDATOR_PATH = ROOT / "scripts" / "validate_non_llm_action_selector_runtime_shadow_expansion_001.py"
AUDIT_PATH = ROOT / "scripts" / "audit_spoken_human_naturalness_001.py"

REQUIRED_COVERAGE = {
    "public_openai_plan",
    "generic_insurance",
    "generic_telecom",
    "home_services",
    "b2b_saas",
    "routesignal_preservation",
}

REQUIRED_ROW_KEYS = {
    "shadow_record_id",
    "case_id",
    "campaign_coverage",
    "campaign_id",
    "vertical_id",
    "buyer_utterance_text_sanitized",
    "runtime_metadata",
    "selector_action_id",
    "agreement_disagreement_type",
    "reason_for_disagreement",
    "disagreement_review_classification",
    "evidence_actionable",
    "safety_flags",
    "candidate_response_hash",
}

FORBIDDEN_ROW_KEYS = {
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

FALSE_KEYS = {
    "raw_private_data",
    "audio_data_used",
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
    "buyer_facing_text_generated",
    "selector_control_allowed",
    "live_runtime_wiring_allowed",
    "side_effects_allowed",
    "memory_mutation_allowed",
    "response_text_changed",
    "runtime_behavior_changed",
}

AUDIT_CATEGORIES = {
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

FORBIDDEN_IMPORT_ROOTS = {"elevenlabs", "httpx", "openai", "requests", "ultravox", "urllib"}


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


def contains_private_source(value: Any) -> bool:
    text = json.dumps(value, sort_keys=True).replace("\\", "/").casefold()
    return "data/private" in text or "private-restricted" in text


def validate_required_files(failures: list[str]) -> None:
    for path in [
        RUNNER_PATH,
        VALIDATOR_PATH,
        AUDIT_PATH,
        EXPANSION_RESULT_PATH,
        EXPANSION_REPORT_PATH,
        DECISION_REPORT_PATH,
        EXPANSION_JSONL_PATH,
        NATURALNESS_RESULT_PATH,
        NATURALNESS_REPORT_PATH,
    ]:
        if not path.is_file():
            failures.append(f"missing required artifact: {path.relative_to(ROOT)}")


def validate_no_forbidden_imports(failures: list[str]) -> None:
    for path in [RUNNER_PATH, AUDIT_PATH, VALIDATOR_PATH]:
        if not path.is_file():
            continue
        found = sorted(imported_roots(path) & FORBIDDEN_IMPORT_ROOTS)
        if found:
            failures.append(f"{path.relative_to(ROOT)} imports forbidden provider/network module(s): {found}")


def validate_expansion_result(failures: list[str], result: dict[str, Any], rows: list[dict[str, Any]]) -> None:
    if not result:
        return
    if result.get("experiment_id") != EXPANSION_ID:
        failures.append("expansion experiment_id mismatch")
    if result.get("status") != "pass":
        failures.append(f"expansion status must be pass: {result.get('status')}")
    if result.get("case_count") != len(rows):
        failures.append("expansion case_count must match JSONL row count")
    if result.get("case_count", 0) < 18:
        failures.append(f"expansion case_count too low: {result.get('case_count')}")
    coverage = set(result.get("campaign_coverage") or [])
    missing = sorted(REQUIRED_COVERAGE - coverage)
    if missing:
        failures.append(f"missing campaign coverage: {missing}")
    if result.get("coverage_count") != len(REQUIRED_COVERAGE):
        failures.append("coverage_count must equal required campaign coverage count")
    if result.get("candidate_response_hash_recorded_count") != result.get("case_count"):
        failures.append("candidate response hashes must be recorded for every expansion case")
    if result.get("raw_candidate_response_recorded_count") != 0:
        failures.append("raw candidate responses must not be recorded in shadow expansion records")
    if result.get("safety_blockers_count") != 0:
        failures.append(f"safety_blockers_count must be 0: {result.get('safety_blockers_count')}")
    for key in [
        "genuine_selector_runtime_disagreement_count",
        "selector_possible_improvement_count",
        "selector_possible_regression_count",
        "runtime_action_unmapped_count",
        "metadata_extraction_failure_count",
        "evidence_not_actionable_yet_count",
        "false_asr_mapping_count",
    ]:
        if not isinstance(result.get(key), int):
            failures.append(f"expansion {key} must be int")
    if result.get("false_asr_mapping_count") != 0:
        failures.append(f"false_asr_mapping_count must be 0: {result.get('false_asr_mapping_count')}")
    if not isinstance(result.get("disagreement_review_by_classification"), dict):
        failures.append("disagreement_review_by_classification must be object")
    if result.get("decision_recommendation_id") != "limited_offline_sanitized_shadow_logging_and_spoken_naturalness_review_next":
        failures.append(f"unexpected recommendation: {result.get('decision_recommendation_id')}")
    if result.get("live_selector_control_recommended") is not False:
        failures.append("live_selector_control_recommended must be false")
    for key in FALSE_KEYS:
        if result.get(key) is not False:
            failures.append(f"expansion {key} must be false")


def validate_expansion_rows(failures: list[str], rows: list[dict[str, Any]]) -> None:
    seen_coverage: set[str] = set()
    for index, row in enumerate(rows, start=1):
        label = f"row[{index}]"
        missing = sorted(REQUIRED_ROW_KEYS - set(row))
        if missing:
            failures.append(f"{label} missing keys: {missing}")
        forbidden = sorted(FORBIDDEN_ROW_KEYS & set(row))
        if forbidden:
            failures.append(f"{label} contains forbidden raw response/audio keys: {forbidden}")
        seen_coverage.add(str(row.get("campaign_coverage") or ""))
        if not str(row.get("campaign_id") or "").strip():
            failures.append(f"{label}.campaign_id missing")
        if not str(row.get("vertical_id") or "").strip():
            failures.append(f"{label}.vertical_id missing")
        if not str(row.get("buyer_utterance_text_sanitized") or "").strip():
            failures.append(f"{label}.buyer_utterance_text_sanitized missing")
        if "RAW TRANSCRIPT" in str(row.get("buyer_utterance_text_sanitized") or ""):
            failures.append(f"{label} contains raw transcript marker")
        candidate_hash = str(row.get("candidate_response_hash") or "")
        if not candidate_hash.startswith("sha256:") or len(candidate_hash) != 71:
            failures.append(f"{label}.candidate_response_hash must be sha256")
        runtime_metadata = row.get("runtime_metadata")
        if not isinstance(runtime_metadata, dict):
            failures.append(f"{label}.runtime_metadata must be an object")
        elif not isinstance(runtime_metadata.get("runtime_extraction_warnings"), list):
            failures.append(f"{label}.runtime_metadata.runtime_extraction_warnings must be list")
        if not str(row.get("disagreement_review_classification") or "").strip():
            failures.append(f"{label}.disagreement_review_classification missing")
        if not str(row.get("reason_for_disagreement") or "").strip():
            failures.append(f"{label}.reason_for_disagreement missing")
        if not isinstance(row.get("evidence_actionable"), bool):
            failures.append(f"{label}.evidence_actionable must be bool")
        if contains_private_source(row):
            failures.append(f"{label} references private source")
        safety_flags = row.get("safety_flags")
        if not isinstance(safety_flags, dict):
            failures.append(f"{label}.safety_flags must be an object")
            continue
        for key in FALSE_KEYS:
            if safety_flags.get(key) is not False:
                failures.append(f"{label}.safety_flags.{key} must be false")
    missing_coverage = sorted(REQUIRED_COVERAGE - seen_coverage)
    if missing_coverage:
        failures.append(f"JSONL rows missing coverage: {missing_coverage}")


def validate_naturalness(failures: list[str], result: dict[str, Any]) -> None:
    if not result:
        return
    if result.get("experiment_id") != NATURALNESS_ID:
        failures.append("naturalness experiment_id mismatch")
    if result.get("status") != "pass":
        failures.append(f"naturalness status must be pass: {result.get('status')}")
    if result.get("private_live_transcripts_inspected") is not False:
        failures.append("naturalness audit must not inspect private live transcripts")
    for key in [
        "provider_calls_made",
        "model_calls_made",
        "local_llm_calls_made",
        "tts_calls_made",
        "crm_calls_made",
        "email_calls_made",
        "calendar_calls_made",
    ]:
        if result.get(key) is not False:
            failures.append(f"naturalness {key} must be false")
    if result.get("automatic_runtime_rewrite_performed") is not False:
        failures.append("naturalness audit must not rewrite runtime responses")
    if result.get("case_count", 0) < 18:
        failures.append(f"naturalness case_count too low: {result.get('case_count')}")
    categories = result.get("categories")
    if not isinstance(categories, dict):
        failures.append("naturalness categories must be an object")
        return
    missing_categories = sorted(AUDIT_CATEGORIES - set(categories))
    if missing_categories:
        failures.append(f"naturalness missing categories: {missing_categories}")
    for category in AUDIT_CATEGORIES:
        payload = categories.get(category) or {}
        if not isinstance(payload, dict):
            failures.append(f"naturalness category {category} must be an object")
            continue
        if not isinstance(payload.get("count"), int):
            failures.append(f"naturalness category {category}.count must be int")
        if not isinstance(payload.get("examples"), list):
            failures.append(f"naturalness category {category}.examples must be list")
    if result.get("recommendation_id") != "limited_offline_sanitized_shadow_logging_and_spoken_naturalness_review_next":
        failures.append(f"naturalness recommendation mismatch: {result.get('recommendation_id')}")
    if result.get("live_selector_control_recommended") is not False:
        failures.append("naturalness live_selector_control_recommended must be false")


def validate_decision_report(failures: list[str]) -> None:
    if not DECISION_REPORT_PATH.is_file():
        return
    text = DECISION_REPORT_PATH.read_text(encoding="utf-8").casefold()
    required_phrases = [
        "is the shadow selector still safe offline",
        "which campaigns show selector/runtime disagreement",
        "which spoken responses sound robotic",
        "which responses risk turning the sales agent into a scheduling bot",
        "what should be fixed before any live selector control",
        "autonomous emotion-aware sales closing",
        "limited_offline_sanitized_shadow_logging_and_spoken_naturalness_review_next",
        "do not enable live selector control",
    ]
    for phrase in required_phrases:
        if phrase not in text:
            failures.append(f"decision report missing phrase: {phrase}")


def main() -> int:
    failures: list[str] = []
    validate_required_files(failures)
    validate_no_forbidden_imports(failures)
    expansion_result = read_json(EXPANSION_RESULT_PATH)
    naturalness_result = read_json(NATURALNESS_RESULT_PATH)
    rows = read_jsonl(EXPANSION_JSONL_PATH)
    validate_expansion_result(failures, expansion_result, rows)
    validate_expansion_rows(failures, rows)
    validate_naturalness(failures, naturalness_result)
    validate_decision_report(failures)
    print(
        json.dumps(
            {
                "validator": "validate_non_llm_action_selector_runtime_shadow_expansion_001",
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
