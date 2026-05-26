#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
import json
import os
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.llm_brain.conversation_brain_schema import (  # noqa: E402
    ACTIVE_MODEL_COMPARISON_THIS_PHASE,
    FALLBACK_MODEL_CANDIDATES,
    PRIMARY_MODEL_ID,
    REQUIRED_RESPONSE_PLAN_FIELDS,
    REQUIRED_SAFETY_FLAG_FIELDS,
    REQUIRED_SALES_STRATEGY_FIELDS,
    REQUIRED_SEMANTIC_FRAME_FIELDS,
    REQUIRED_STATE_UPDATE_FIELDS,
    REQUIRED_TOP_LEVEL_FIELDS,
    validate_conversation_brain_output,
)
from runtime.llm_brain.conversation_brain_verifier import (  # noqa: E402
    verify_conversation_brain_output,
)
from runtime.llm_brain.local_conversation_brain import (  # noqa: E402
    default_local_conversation_brain_config,
)


EXPERIMENT_ID = "LOCAL-LLM-CONVERSATION-BRAIN-FEASIBILITY-001"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / EXPERIMENT_ID
GOLD_PATH = OUT_DIR / "gold_cases.jsonl"
MOCK_PATH = OUT_DIR / "mock_planner_outputs.jsonl"
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"

MIN_TOTAL_CASES = 80
MIN_LIVE_DERIVED_CASES = 30
MIN_PARAPHRASE_CASES = 30
MIN_NEGATIVE_CONTROLS = 20


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def assert_condition(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    assert_condition(path.is_file(), f"Missing JSONL file: {path.relative_to(ROOT)}")
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError as exc:
            raise AssertionError(f"{path.name}:{line_number} invalid JSON: {exc}") from exc
        assert_condition(isinstance(payload, dict), f"{path.name}:{line_number} must be a JSON object")
        records.append(payload)
    return records


def normalize(text: Any) -> str:
    return " ".join(str(text or "").lower().split())


def marker_present(text: str, marker: str) -> bool:
    return normalize(marker) in normalize(text)


def compare_nested(
    case_id: str,
    section_name: str,
    expected: dict[str, Any],
    actual: dict[str, Any],
    failures: list[str],
) -> None:
    for key, expected_value in expected.items():
        actual_value = actual.get(key)
        if actual_value != expected_value:
            failures.append(
                f"{case_id}: {section_name}.{key} expected {expected_value!r}, got {actual_value!r}"
            )


def validate_gold_case_shape(case: dict[str, Any], failures: list[str]) -> None:
    case_id = case.get("case_id", "<missing-case-id>")
    required = {
        "case_id",
        "source_type",
        "prior_state",
        "approved_campaign_fact_ids",
        "expected_semantic_frame",
        "expected_state_update",
        "expected_sales_strategy",
        "expected_response_plan",
        "acceptable_response_markers",
        "forbidden_response_markers",
    }
    missing = sorted(required - set(case))
    if missing:
        failures.append(f"{case_id}: missing gold case field(s): {missing}")
    if not (case.get("sanitized_buyer_text") or case.get("raw_buyer_text")):
        failures.append(f"{case_id}: missing sanitized_buyer_text or raw_buyer_text")
    if case.get("raw_private_transcript_text"):
        failures.append(f"{case_id}: raw_private_transcript_text is forbidden in generated evidence")
    if not isinstance(case.get("approved_campaign_fact_ids"), list):
        failures.append(f"{case_id}: approved_campaign_fact_ids must be a list")
    for section_name, required_fields in {
        "expected_semantic_frame": REQUIRED_SEMANTIC_FRAME_FIELDS,
        "expected_state_update": REQUIRED_STATE_UPDATE_FIELDS,
        "expected_sales_strategy": REQUIRED_SALES_STRATEGY_FIELDS,
        "expected_response_plan": REQUIRED_RESPONSE_PLAN_FIELDS,
    }.items():
        section = case.get(section_name)
        if not isinstance(section, dict):
            failures.append(f"{case_id}: {section_name} must be an object")
            continue
        missing_section = sorted(set(required_fields) - set(section))
        if missing_section:
            failures.append(f"{case_id}: {section_name} missing field(s): {missing_section}")
    for marker_field in ("acceptable_response_markers", "forbidden_response_markers"):
        markers = case.get(marker_field)
        if not isinstance(markers, list) or not all(isinstance(item, str) for item in markers):
            failures.append(f"{case_id}: {marker_field} must be a list of strings")


def validate_mock_against_gold(
    case: dict[str, Any],
    planner_output: dict[str, Any],
    failures: list[str],
) -> None:
    case_id = case["case_id"]
    schema_errors = validate_conversation_brain_output(planner_output)
    failures.extend(f"{case_id}: schema: {message}" for message in schema_errors)
    verifier_errors = verify_conversation_brain_output(planner_output, case)
    failures.extend(f"{case_id}: verifier: {message}" for message in verifier_errors)

    compare_nested(
        case_id,
        "semantic_frame",
        case["expected_semantic_frame"],
        planner_output.get("semantic_frame") or {},
        failures,
    )
    compare_nested(
        case_id,
        "state_update",
        case["expected_state_update"],
        planner_output.get("state_update") or {},
        failures,
    )
    compare_nested(
        case_id,
        "sales_strategy",
        case["expected_sales_strategy"],
        planner_output.get("sales_strategy") or {},
        failures,
    )
    compare_nested(
        case_id,
        "response_plan",
        case["expected_response_plan"],
        planner_output.get("response_plan") or {},
        failures,
    )

    draft = planner_output.get("draft_response")
    if not isinstance(draft, str) or not draft.strip():
        failures.append(f"{case_id}: draft_response must be a non-empty string")
        return
    for marker in case["acceptable_response_markers"]:
        if not marker_present(draft, marker):
            failures.append(f"{case_id}: draft_response missing acceptable marker {marker!r}")
    for marker in case["forbidden_response_markers"]:
        if marker_present(draft, marker):
            failures.append(f"{case_id}: draft_response contains forbidden marker {marker!r}")


def mutate_case_output(
    mocks_by_case_id: dict[str, dict[str, Any]],
    case_id: str,
    mutator: Any,
) -> dict[str, Any]:
    output = deepcopy(mocks_by_case_id[case_id])
    mutator(output)
    return output


def expect_verifier_failure(
    case: dict[str, Any],
    output: dict[str, Any],
    expected_fragment: str,
    failures: list[str],
) -> bool:
    errors = verify_conversation_brain_output(output, case)
    matched = any(expected_fragment in error for error in errors)
    if not matched:
        failures.append(
            f"{case['case_id']}: verifier probe did not catch {expected_fragment!r}; errors={errors!r}"
        )
    return matched


def run_verifier_regression_probes(
    cases_by_id: dict[str, dict[str, Any]],
    mocks_by_case_id: dict[str, dict[str, Any]],
    failures: list[str],
) -> dict[str, bool]:
    probes: dict[str, bool] = {}

    voice_case = cases_by_id["live_voice_not_writing_001"]
    voice_output = mutate_case_output(
        mocks_by_case_id,
        "live_voice_not_writing_001",
        lambda output: (
            output.__setitem__(
                "draft_response",
                "Right - ChatGPT for coding and writing. Plus is usually the first paid plan to compare.",
            ),
            output["response_plan"].__setitem__("buyer_words_to_preserve", ["coding workflow"]),
        ),
    )
    probes["voice_not_writing"] = expect_verifier_failure(
        voice_case, voice_output, "voice_to_writing", failures
    )

    and_case = cases_by_id["paraphrase_and_relation_001"]
    and_output = mutate_case_output(
        mocks_by_case_id,
        "paraphrase_and_relation_001",
        lambda output: (
            output["semantic_frame"].__setitem__("conjunction_relation", "or"),
            output.__setitem__("draft_response", "So it is coding or voice. Which matters more?"),
        ),
    )
    probes["and_or_fidelity"] = expect_verifier_failure(and_case, and_output, "and_or_drift", failures)

    not_team_case = cases_by_id["negative_not_team_001"]
    not_team_output = mutate_case_output(
        mocks_by_case_id,
        "negative_not_team_001",
        lambda output: (
            output["state_update"].__setitem__("should_update_team_state", True),
            output.__setitem__("draft_response", "For your team, Business may be worth comparing."),
        ),
    )
    probes["not_team_no_team_update"] = expect_verifier_failure(
        not_team_case, not_team_output, "negated_team_state", failures
    )

    internal_case = cases_by_id["negative_internal_policy_001"]
    internal_output = mutate_case_output(
        mocks_by_case_id,
        "negative_internal_policy_001",
        lambda output: output.__setitem__(
            "draft_response", "Internal policy says I should ask one more qualification question."
        ),
    )
    probes["internal_policy_language"] = expect_verifier_failure(
        internal_case, internal_output, "internal_policy_language", failures
    )

    side_effect_case = cases_by_id["negative_side_effect_001"]
    side_effect_output = mutate_case_output(
        mocks_by_case_id,
        "negative_side_effect_001",
        lambda output: output.__setitem__(
            "draft_response", "I created the calendar invite and sent the email."
        ),
    )
    probes["side_effect_safety"] = expect_verifier_failure(
        side_effect_case, side_effect_output, "side_effect_claim", failures
    )

    unsupported_case = cases_by_id["negative_unsupported_fact_001"]
    unsupported_output = mutate_case_output(
        mocks_by_case_id,
        "negative_unsupported_fact_001",
        lambda output: output.__setitem__(
            "draft_response", "Pro guarantees unlimited access to every newest model."
        ),
    )
    probes["unsupported_claim"] = expect_verifier_failure(
        unsupported_case, unsupported_output, "unsupported_product_claim", failures
    )

    raw_url_case = cases_by_id["negative_raw_url_001"]
    raw_url_output = mutate_case_output(
        mocks_by_case_id,
        "negative_raw_url_001",
        lambda output: output.__setitem__(
            "draft_response", "Check this URL: https://example.invalid/private-plan-source"
        ),
    )
    probes["raw_url"] = expect_verifier_failure(raw_url_case, raw_url_output, "raw_url", failures)

    affiliation_case = cases_by_id["negative_affiliation_001"]
    affiliation_output = mutate_case_output(
        mocks_by_case_id,
        "negative_affiliation_001",
        lambda output: output.__setitem__(
            "draft_response", "We at OpenAI can help you pick the right plan."
        ),
    )
    probes["affiliation_claim"] = expect_verifier_failure(
        affiliation_case, affiliation_output, "affiliation_claim", failures
    )

    leakage_case = cases_by_id["negative_campaign_leakage_001"]
    leakage_output = mutate_case_output(
        mocks_by_case_id,
        "negative_campaign_leakage_001",
        lambda output: output.__setitem__(
            "draft_response", "RouteSignal routing evidence shows the next step is Pro."
        ),
    )
    probes["campaign_leakage"] = expect_verifier_failure(
        leakage_case, leakage_output, "campaign_leakage", failures
    )

    return probes


def write_result_and_report(result: dict[str, Any], failures: list[str]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    result_with_failures = {**result, "failures": failures}
    RESULT_PATH.write_text(json.dumps(result_with_failures, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    status = "PASS" if not failures else "FAIL"
    report = [
        f"# {EXPERIMENT_ID}",
        "",
        f"- status: {status}",
        f"- generated_at: {result['generated_at']}",
        f"- schema_status: {result['schema_status']}",
        f"- gold_case_count: {result['gold_case_count']}",
        f"- live_derived_sanitized_case_count: {result['source_type_counts'].get('live_sanitized', 0)}",
        f"- paraphrase_case_count: {result['source_type_counts'].get('synthetic_paraphrase', 0)}",
        f"- negative_control_count: {result['source_type_counts'].get('negative_control', 0)}",
        f"- mock_planner_output_count: {result['mock_planner_output_count']}",
        f"- verifier_passed: {str(result['verifier_passed']).lower()}",
        f"- current_utterance_fidelity_result: {result['verifier_regression_probes'].get('voice_not_writing')}",
        f"- and_or_fidelity_result: {result['verifier_regression_probes'].get('and_or_fidelity')}",
        f"- negation_fidelity_result: {result['verifier_regression_probes'].get('not_team_no_team_update')}",
        f"- voice_not_writing_result: {result['verifier_regression_probes'].get('voice_not_writing')}",
        f"- side_effect_safety_result: {result['verifier_regression_probes'].get('side_effect_safety')}",
        f"- unsupported_claim_result: {result['verifier_regression_probes'].get('unsupported_claim')}",
        f"- local_model_inference_attempted: {str(result['local_model_inference_attempted']).lower()}",
        f"- local_model_calls_made: {str(result['local_model_calls_made']).lower()}",
        f"- provider_calls_made: {str(result['provider_calls_made']).lower()}",
        f"- runtime_behavior_changed: {str(result['runtime_behavior_changed']).lower()}",
        f"- response_text_changed: {str(result['response_text_changed']).lower()}",
        f"- raw_private_transcript_copied_to_public_evidence: {str(result['raw_private_transcript_copied_to_public_evidence']).lower()}",
        f"- primary_model_id: {result['primary_model_id']}",
        f"- fallback_model_candidates: {', '.join(result['fallback_model_candidates'])}",
        f"- active_model_comparison_this_phase: {str(result['active_model_comparison_this_phase']).lower()}",
        "",
        "## Model Candidates",
        "",
        *(f"- {item}" for item in result["model_candidates"]),
        "",
        "## Failure Details",
        "",
    ]
    if failures:
        report.extend(f"- {failure}" for failure in failures)
    else:
        report.append("- none")
    REPORT_PATH.write_text("\n".join(report) + "\n", encoding="utf-8")


def main() -> int:
    failures: list[str] = []
    gold_cases = read_jsonl(GOLD_PATH)
    mock_records = read_jsonl(MOCK_PATH)
    source_counts = Counter(case.get("source_type") for case in gold_cases)

    cases_by_id = {case.get("case_id"): case for case in gold_cases}
    mocks_by_case_id = {record.get("case_id"): record.get("planner_output") for record in mock_records}

    if len(cases_by_id) != len(gold_cases):
        failures.append("case_id values must be unique")
    if len(mocks_by_case_id) != len(mock_records):
        failures.append("mock planner case_id values must be unique")

    if len(gold_cases) < MIN_TOTAL_CASES:
        failures.append(f"expected at least {MIN_TOTAL_CASES} gold cases, got {len(gold_cases)}")
    if source_counts.get("live_sanitized", 0) < MIN_LIVE_DERIVED_CASES:
        failures.append(
            f"expected at least {MIN_LIVE_DERIVED_CASES} live_sanitized cases, got {source_counts.get('live_sanitized', 0)}"
        )
    if source_counts.get("synthetic_paraphrase", 0) < MIN_PARAPHRASE_CASES:
        failures.append(
            f"expected at least {MIN_PARAPHRASE_CASES} synthetic_paraphrase cases, got {source_counts.get('synthetic_paraphrase', 0)}"
        )
    if source_counts.get("negative_control", 0) < MIN_NEGATIVE_CONTROLS:
        failures.append(
            f"expected at least {MIN_NEGATIVE_CONTROLS} negative_control cases, got {source_counts.get('negative_control', 0)}"
        )
    if len(mock_records) != len(gold_cases):
        failures.append(f"mock output count must equal gold case count: {len(mock_records)} != {len(gold_cases)}")

    missing_mock_ids = sorted(set(cases_by_id) - set(mocks_by_case_id))
    extra_mock_ids = sorted(set(mocks_by_case_id) - set(cases_by_id))
    if missing_mock_ids:
        failures.append(f"missing mock planner outputs for case(s): {missing_mock_ids[:10]}")
    if extra_mock_ids:
        failures.append(f"mock planner outputs without gold case(s): {extra_mock_ids[:10]}")

    for case in gold_cases:
        validate_gold_case_shape(case, failures)
        output = mocks_by_case_id.get(case.get("case_id"))
        if isinstance(output, dict):
            validate_mock_against_gold(case, output, failures)
        else:
            failures.append(f"{case.get('case_id')}: missing planner_output object")

    required_probe_ids = {
        "live_voice_not_writing_001",
        "paraphrase_and_relation_001",
        "negative_not_team_001",
        "negative_internal_policy_001",
        "negative_side_effect_001",
        "negative_unsupported_fact_001",
        "negative_raw_url_001",
        "negative_affiliation_001",
        "negative_campaign_leakage_001",
    }
    missing_probe_ids = sorted(required_probe_ids - set(cases_by_id))
    if missing_probe_ids:
        failures.append(f"missing required verifier probe case(s): {missing_probe_ids}")
        probes: dict[str, bool] = {}
    else:
        probes = run_verifier_regression_probes(cases_by_id, mocks_by_case_id, failures)

    config = default_local_conversation_brain_config()
    enabled_env = os.getenv("ENABLE_LOCAL_LLM_BRAIN_EXPERIMENT") == "1"
    result = {
        "experiment_id": EXPERIMENT_ID,
        "generated_at": utc_now(),
        "schema_status": "defined" if not failures else "defined_with_failures",
        "required_top_level_fields": list(REQUIRED_TOP_LEVEL_FIELDS),
        "required_semantic_frame_fields": list(REQUIRED_SEMANTIC_FRAME_FIELDS),
        "required_state_update_fields": list(REQUIRED_STATE_UPDATE_FIELDS),
        "required_sales_strategy_fields": list(REQUIRED_SALES_STRATEGY_FIELDS),
        "required_response_plan_fields": list(REQUIRED_RESPONSE_PLAN_FIELDS),
        "required_safety_flag_fields": list(REQUIRED_SAFETY_FLAG_FIELDS),
        "gold_case_count": len(gold_cases),
        "source_type_counts": dict(source_counts),
        "mock_planner_output_count": len(mock_records),
        "verifier_passed": not failures,
        "verifier_regression_probes": probes,
        "local_brain_config": config.redacted_dict(),
        "local_model_experiment_env_enabled": enabled_env,
        "local_model_inference_attempted": False,
        "local_model_calls_made": False,
        "provider_calls_made": False,
        "runtime_behavior_changed": False,
        "response_text_changed": False,
        "raw_private_transcript_copied_to_public_evidence": False,
        "model_candidates": [
            PRIMARY_MODEL_ID,
            *FALLBACK_MODEL_CANDIDATES,
        ],
        "primary_model_id": PRIMARY_MODEL_ID,
        "fallback_model_candidates": list(FALLBACK_MODEL_CANDIDATES),
        "active_model_comparison_this_phase": ACTIVE_MODEL_COMPARISON_THIS_PHASE,
    }
    write_result_and_report(result, failures)
    if failures:
        print(f"{EXPERIMENT_ID}: FAIL ({len(failures)} failure(s))")
        for failure in failures[:50]:
            print(f"- {failure}")
        return 1
    print(f"{EXPERIMENT_ID}: PASS")
    print(f"gold cases: {len(gold_cases)}")
    print(f"mock outputs: {len(mock_records)}")
    print("local model inference attempted: false")
    print("provider calls made: false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
