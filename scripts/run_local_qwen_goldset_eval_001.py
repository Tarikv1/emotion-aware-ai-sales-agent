#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import replace
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.llm_brain.conversation_brain_schema import (  # noqa: E402
    COMPACT_PLANNER_MAX_OUTPUT_TOKENS,
    COMPACT_PLANNER_SCHEMA_MODE,
    PRIMARY_MODEL_ID,
    validate_conversation_brain_output,
)
from runtime.llm_brain.conversation_brain_verifier import (  # noqa: E402
    verify_conversation_brain_output,
)
from runtime.llm_brain.local_conversation_brain import (  # noqa: E402
    EXPERIMENT_ENV_VAR,
    LOCAL_LLM_ENABLED_ENV_VAR,
    LOCAL_LLM_MAX_OUTPUT_TOKENS_ENV_VAR,
    local_conversation_brain_config_from_env,
    local_llm_enabled,
    local_llm_experiment_enabled,
)
from runtime.llm_brain.local_transformers_runner import (  # noqa: E402
    dependency_status,
    ensure_model_available,
    hardware_summary,
    load_local_transformers_model,
    run_single_conversation_brain_case,
)


EXPERIMENT_ID = "LOCAL-QWEN-GOLDSET-EVAL-001"
SOURCE_EXPERIMENT_ID = "LOCAL-LLM-CONVERSATION-BRAIN-FEASIBILITY-001"
SOURCE_DIR = ROOT / "research" / "experiments" / "generated" / SOURCE_EXPERIMENT_ID
GOLD_CASES_PATH = SOURCE_DIR / "gold_cases.jsonl"
MOCK_OUTPUTS_PATH = SOURCE_DIR / "mock_planner_outputs.jsonl"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / EXPERIMENT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"
DOWNLOAD_ENV_VAR = "LOCAL_LLM_ALLOW_MODEL_DOWNLOAD"

APPROVED_CAMPAIGN_FACT_SUMMARIES = {
    "public_plan_names": (
        "ChatGPT public plan categories include Free, Plus, Pro, Business, and Enterprise; "
        "the official source remains authoritative."
    ),
    "current_public_plan_prices": (
        "The public price fixture may contain current plan prices, but the planner must avoid "
        "inventing price claims unless that fact ID is approved for the case."
    ),
}

REPRESENTATIVE_CASE_IDS = [
    "live_voice_not_writing_001",
    "live_current_tools_002",
    "live_current_tools_003",
    "live_asr_chachu_004",
    "live_asr_chacha_005",
    "live_asr_check_gpt_006",
    "live_cloud_claude_007",
    "live_what_is_this_008",
    "paraphrase_and_relation_001",
    "paraphrase_or_relation_002",
    "paraphrase_chatgpt_plus_claude_003",
    "paraphrase_another_ai_004",
    "live_not_team_011",
    "live_by_myself_012",
    "live_personal_use_013",
    "paraphrase_no_team_013",
    "live_plans_009",
    "live_model_subscription_010",
    "paraphrase_plan_list_010",
    "paraphrase_subscription_011",
    "live_competitor_objection_018",
    "live_signup_question_019",
    "live_price_objection_017",
    "live_terminal_acceptance_016",
]

EXPECTED_SECTIONS = (
    ("semantic_frame", "expected_semantic_frame"),
    ("state_update", "expected_state_update"),
    ("sales_strategy", "expected_sales_strategy"),
    ("response_plan", "expected_response_plan"),
)

SALES_ACTION_FIELDS = (
    "next_action",
    "one_next_step",
    "should_answer_directly",
    "should_ask_question",
    "should_recommend",
    "should_reframe_objection",
    "should_close",
    "should_disqualify",
)

STATE_UPDATE_BOOLEAN_FIELDS = (
    "should_update_adoption_state",
    "should_update_use_case",
    "should_update_usage_intensity",
    "should_update_team_state",
    "should_update_recommendation",
    "should_update_close_readiness",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def env_flag(name: str) -> bool:
    return str(os.getenv(name) or "").strip().lower() in {"1", "true", "yes", "on"}


def in_expected_llm_env() -> bool:
    executable = str(Path(sys.executable).resolve()).replace("\\", "/").lower()
    return "/.venv-llm/" in executable or executable.endswith("/.venv-llm/scripts/python.exe")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        payload = json.loads(stripped)
        if not isinstance(payload, dict):
            raise ValueError(f"{path} line {line_number} must be a JSON object")
        records.append(payload)
    return records


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def goldset_config_from_env():
    config = local_conversation_brain_config_from_env()
    max_output_tokens = config.max_output_tokens
    if not os.getenv(LOCAL_LLM_MAX_OUTPUT_TOKENS_ENV_VAR):
        max_output_tokens = COMPACT_PLANNER_MAX_OUTPUT_TOKENS
    return replace(
        config,
        planner_schema_mode=COMPACT_PLANNER_SCHEMA_MODE,
        max_output_tokens=max_output_tokens,
        enabled=True,
    )


def git_model_weights_committed() -> bool:
    try:
        completed = subprocess.run(
            ["git", "ls-files", "local_artifacts"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except Exception:
        return False
    if completed.returncode != 0:
        return False
    weight_suffixes = (".safetensors", ".bin", ".gguf", ".pt", ".pth")
    return any(line.strip().lower().endswith(weight_suffixes) for line in completed.stdout.splitlines())


def build_request_context(case: dict[str, Any]) -> dict[str, Any]:
    approved_fact_ids = [str(item) for item in case.get("approved_campaign_fact_ids") or []]
    summaries = {
        fact_id: APPROVED_CAMPAIGN_FACT_SUMMARIES[fact_id]
        for fact_id in approved_fact_ids
        if fact_id in APPROVED_CAMPAIGN_FACT_SUMMARIES
    }
    prior_state = case.get("prior_state") if isinstance(case.get("prior_state"), dict) else {}
    return {
        "normalized_transcript": str(case.get("sanitized_buyer_text") or ""),
        "prior_state": prior_state,
        "approved_campaign_fact_ids": approved_fact_ids,
        "approved_campaign_fact_summaries": summaries,
        "smoke_contract": {},
        "last_agent_question": str(case.get("last_agent_question") or ""),
        "campaign_id": str(prior_state.get("campaign_id") or ""),
    }


def case_for_verifier(case: dict[str, Any]) -> dict[str, Any]:
    context = build_request_context(case)
    return {
        **case,
        "approved_campaign_fact_summaries": context["approved_campaign_fact_summaries"],
    }


def normalize_text(value: Any) -> str:
    return " ".join(str(value or "").lower().split())


def semantic_equal(expected: Any, actual: Any) -> bool:
    if isinstance(expected, bool) or isinstance(actual, bool):
        return expected is actual
    if isinstance(expected, (int, float)) or isinstance(actual, (int, float)):
        return expected == actual
    if isinstance(expected, list) or isinstance(actual, list):
        expected_items = expected if isinstance(expected, list) else [expected]
        actual_items = actual if isinstance(actual, list) else [actual]
        return sorted(normalize_text(item) for item in expected_items) == sorted(
            normalize_text(item) for item in actual_items
        )
    return normalize_text(expected) == normalize_text(actual)


def compare_expected_sections(
    payload: dict[str, Any] | None,
    case: dict[str, Any],
    *,
    exact: bool,
) -> list[str]:
    if not isinstance(payload, dict):
        return ["planner_output_missing"]
    mismatches: list[str] = []
    for actual_section_name, expected_section_name in EXPECTED_SECTIONS:
        expected_section = case.get(expected_section_name)
        actual_section = payload.get(actual_section_name)
        if not isinstance(expected_section, dict):
            continue
        if not isinstance(actual_section, dict):
            mismatches.append(actual_section_name)
            continue
        for field_name, expected_value in expected_section.items():
            actual_value = actual_section.get(field_name)
            matches = expected_value == actual_value if exact else semantic_equal(expected_value, actual_value)
            if not matches:
                mismatches.append(f"{actual_section_name}.{field_name}")
    return sorted(mismatches)


def compact_failure_classes(errors: list[str], mismatches: list[str]) -> list[str]:
    classes: set[str] = set()
    for error in errors:
        text = str(error)
        if ":" in text:
            classes.add(text.split(":", 1)[0])
        elif text:
            classes.add(text)
    for mismatch in mismatches:
        if mismatch == "planner_output_missing":
            classes.add("planner_output_missing")
        elif mismatch.startswith("semantic_frame."):
            classes.add("gold_semantic_mismatch")
        elif mismatch.startswith("state_update."):
            classes.add("gold_state_mismatch")
        elif mismatch.startswith("sales_strategy."):
            classes.add("gold_sales_mismatch")
        elif mismatch.startswith("response_plan."):
            classes.add("gold_response_plan_mismatch")
        else:
            classes.add("gold_mismatch")
    return sorted(classes)


def expected_section(case: dict[str, Any], name: str) -> dict[str, Any]:
    value = case.get(name)
    return value if isinstance(value, dict) else {}


def actual_section(payload: dict[str, Any] | None, name: str) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {}
    value = payload.get(name)
    return value if isinstance(value, dict) else {}


def draft_response(payload: dict[str, Any] | None) -> str:
    if not isinstance(payload, dict):
        return ""
    return str(payload.get("draft_response") or "")


def buyer_wording_pass(payload: dict[str, Any] | None, case: dict[str, Any]) -> bool:
    expected_plan = expected_section(case, "expected_response_plan")
    phrases = [str(item) for item in expected_plan.get("buyer_words_to_preserve") or []]
    if not phrases:
        return True
    normalized_draft = normalize_text(draft_response(payload))
    return all(normalize_text(phrase) in normalized_draft for phrase in phrases)


def and_or_applicable(case: dict[str, Any]) -> bool:
    expected = expected_section(case, "expected_semantic_frame").get("conjunction_relation")
    return expected in {"and", "or"}


def and_or_pass(payload: dict[str, Any] | None, case: dict[str, Any]) -> bool:
    if not and_or_applicable(case):
        return True
    expected = expected_section(case, "expected_semantic_frame").get("conjunction_relation")
    actual = actual_section(payload, "semantic_frame").get("conjunction_relation")
    return actual == expected


def negation_applicable(case: dict[str, Any]) -> bool:
    expected_semantic = expected_section(case, "expected_semantic_frame")
    case_id = str(case.get("case_id") or "").lower()
    return expected_semantic.get("negation_scope") not in {None, "", "none"} or any(
        marker in case_id for marker in ("not_team", "no_team", "by_myself", "self_use", "individual")
    )


def negation_pass(payload: dict[str, Any] | None, case: dict[str, Any]) -> bool:
    if not negation_applicable(case):
        return True
    expected_semantic = expected_section(case, "expected_semantic_frame")
    expected_state = expected_section(case, "expected_state_update")
    actual_semantic = actual_section(payload, "semantic_frame")
    actual_state = actual_section(payload, "state_update")
    expected_negation = expected_semantic.get("negation_scope")
    if expected_negation not in {None, "", "none"} and actual_semantic.get("negation_scope") != expected_negation:
        return False
    return actual_state.get("should_update_team_state") == expected_state.get("should_update_team_state")


def state_poisoning_applicable(case: dict[str, Any]) -> bool:
    expected_state = expected_section(case, "expected_state_update")
    if case.get("source_type") == "negative_control":
        return True
    return all(expected_state.get(field) is False for field in STATE_UPDATE_BOOLEAN_FIELDS)


def state_poisoning_pass(payload: dict[str, Any] | None, case: dict[str, Any]) -> bool:
    if not state_poisoning_applicable(case):
        return True
    expected_state = expected_section(case, "expected_state_update")
    actual_state = actual_section(payload, "state_update")
    return all(actual_state.get(field) == expected_state.get(field) for field in STATE_UPDATE_BOOLEAN_FIELDS)


def sales_action_pass(payload: dict[str, Any] | None, case: dict[str, Any]) -> bool:
    expected_sales = expected_section(case, "expected_sales_strategy")
    actual_sales = actual_section(payload, "sales_strategy")
    return all(actual_sales.get(field) == expected_sales.get(field) for field in SALES_ACTION_FIELDS)


def voice_not_writing_applicable(case: dict[str, Any]) -> bool:
    expected_plan = expected_section(case, "expected_response_plan")
    forbidden = [normalize_text(item) for item in case.get("forbidden_response_markers") or []]
    must_not = [normalize_text(item) for item in expected_plan.get("must_not_include") or []]
    return "writing" in forbidden or "writing" in must_not


def voice_not_writing_pass(payload: dict[str, Any] | None, case: dict[str, Any]) -> bool:
    if not voice_not_writing_applicable(case):
        return True
    return "writing" not in normalize_text(draft_response(payload))


def verifier_error_has(verifier_errors: list[str], *markers: str) -> bool:
    joined = "\n".join(str(item).lower() for item in verifier_errors)
    return any(marker.lower() in joined for marker in markers)


def flag_is_set(payload: dict[str, Any] | None, flag_name: str) -> bool:
    safety = actual_section(payload, "safety_flags")
    return safety.get(flag_name) is True


def quality_flags(
    payload: dict[str, Any] | None,
    case: dict[str, Any],
    verifier_errors: list[str],
) -> dict[str, dict[str, bool]]:
    return {
        "current_utterance_fidelity": {
            "applicable": True,
            "pass": buyer_wording_pass(payload, case),
        },
        "and_or_fidelity": {
            "applicable": and_or_applicable(case),
            "pass": and_or_pass(payload, case),
        },
        "negation_fidelity": {
            "applicable": negation_applicable(case),
            "pass": negation_pass(payload, case),
        },
        "voice_not_writing": {
            "applicable": voice_not_writing_applicable(case),
            "pass": voice_not_writing_pass(payload, case),
        },
        "team_state_poisoning": {
            "applicable": state_poisoning_applicable(case),
            "pass": state_poisoning_pass(payload, case),
        },
        "internal_policy_leak": {
            "applicable": True,
            "pass": not verifier_error_has(verifier_errors, "internal_policy_language", "campaign_leakage")
            and not flag_is_set(payload, "internal_policy_language_risk")
            and not flag_is_set(payload, "campaign_leakage_risk"),
        },
        "fake_side_effect": {
            "applicable": True,
            "pass": not verifier_error_has(verifier_errors, "side_effect")
            and not flag_is_set(payload, "side_effect_claim_risk"),
        },
        "unsupported_claim": {
            "applicable": True,
            "pass": not verifier_error_has(verifier_errors, "unsupported_product_claim", "campaign_fact_not_approved")
            and not flag_is_set(payload, "unsupported_product_claim_risk"),
        },
        "sales_action": {
            "applicable": True,
            "pass": sales_action_pass(payload, case),
        },
    }


def evaluate_payload(
    *,
    payload: dict[str, Any] | None,
    case: dict[str, Any],
    verifier_case: dict[str, Any],
) -> dict[str, Any]:
    schema_errors = validate_conversation_brain_output(payload) if isinstance(payload, dict) else ["planner_output_missing"]
    verifier_errors = verify_conversation_brain_output(payload, verifier_case) if isinstance(payload, dict) else []
    exact_mismatches = compare_expected_sections(payload, case, exact=True)
    semantic_mismatches = compare_expected_sections(payload, case, exact=False)
    semantic_match = not schema_errors and not verifier_errors
    failure_classes = compact_failure_classes([*schema_errors, *verifier_errors], semantic_mismatches)
    flags = quality_flags(payload, case, verifier_errors)
    return {
        "schema_errors": schema_errors,
        "verifier_errors": verifier_errors,
        "exact_mismatches": exact_mismatches,
        "semantic_mismatches": semantic_mismatches,
        "exact_match": not exact_mismatches,
        "semantic_match": semantic_match,
        "failure_classes": failure_classes,
        "quality_flags": flags,
        "score": len(schema_errors) * 5 + len(verifier_errors) * 3 + len(semantic_mismatches),
    }


def deterministic_output_by_case(mock_records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    outputs: dict[str, dict[str, Any]] = {}
    for record in mock_records:
        case_id = str(record.get("case_id") or "")
        planner_output = record.get("planner_output")
        if case_id and isinstance(planner_output, dict):
            outputs[case_id] = planner_output
    return outputs


def comparison_outcome(qwen_eval: dict[str, Any], deterministic_eval: dict[str, Any]) -> str:
    qwen_pass = bool(qwen_eval.get("semantic_match"))
    deterministic_pass = bool(deterministic_eval.get("semantic_match"))
    if qwen_pass and deterministic_pass:
        return "both_pass"
    if qwen_pass and not deterministic_pass:
        return "qwen_better"
    if deterministic_pass and not qwen_pass:
        return "deterministic_better"
    return "both_fail"


def property_comparison(
    qwen_flags: dict[str, dict[str, bool]],
    deterministic_flags: dict[str, dict[str, bool]],
) -> dict[str, str]:
    outcomes: dict[str, str] = {}
    for name, qwen_item in qwen_flags.items():
        deterministic_item = deterministic_flags.get(name, {})
        if not qwen_item.get("applicable") and not deterministic_item.get("applicable"):
            outcomes[name] = "not_applicable"
            continue
        qwen_pass = bool(qwen_item.get("pass"))
        deterministic_pass = bool(deterministic_item.get("pass"))
        if qwen_pass and deterministic_pass:
            outcomes[name] = "both_pass"
        elif qwen_pass:
            outcomes[name] = "qwen_better"
        elif deterministic_pass:
            outcomes[name] = "deterministic_better"
        else:
            outcomes[name] = "both_fail"
    return outcomes


def percentile(values: list[float], pct: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return round(ordered[0], 3)
    rank = (len(ordered) - 1) * pct
    low = math.floor(rank)
    high = math.ceil(rank)
    if low == high:
        return round(ordered[low], 3)
    fraction = rank - low
    return round(ordered[low] + (ordered[high] - ordered[low]) * fraction, 3)


def pearson(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) != len(ys) or len(xs) < 2:
        return None
    mean_x = sum(xs) / len(xs)
    mean_y = sum(ys) / len(ys)
    numerator = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    denominator_x = math.sqrt(sum((x - mean_x) ** 2 for x in xs))
    denominator_y = math.sqrt(sum((y - mean_y) ** 2 for y in ys))
    if denominator_x == 0 or denominator_y == 0:
        return None
    return round(numerator / (denominator_x * denominator_y), 4)


def aggregate_latency(case_results: list[dict[str, Any]], model_load_time_ms: float | None) -> dict[str, Any]:
    generation_latencies: list[float] = []
    first_latencies: list[float] = []
    prompt_counts: list[int] = []
    generated_counts: list[int] = []
    prompt_for_corr: list[float] = []
    generated_for_corr: list[float] = []
    latency_for_corr: list[float] = []
    peak_memory: list[int] = []
    output_truncated_count = 0
    timed_out_count = 0
    completed_json_count = 0
    slow_candidates: list[dict[str, Any]] = []
    for item in case_results:
        metrics = item.get("latency_metrics") or {}
        total = metrics.get("total_generation_latency_ms")
        first = metrics.get("first_output_latency_ms")
        prompt_tokens = metrics.get("prompt_token_count")
        generated_tokens = metrics.get("tokens_generated")
        peak = metrics.get("peak_gpu_memory_bytes")
        if isinstance(total, (int, float)):
            total_float = float(total)
            generation_latencies.append(total_float)
            slow_candidates.append(
                {
                    "case_id": item.get("case_id"),
                    "total_generation_latency_ms": round(total_float, 3),
                    "prompt_token_count": prompt_tokens,
                    "tokens_generated": generated_tokens,
                }
            )
        if isinstance(first, (int, float)):
            first_latencies.append(float(first))
        if isinstance(prompt_tokens, int):
            prompt_counts.append(prompt_tokens)
        if isinstance(generated_tokens, int):
            generated_counts.append(generated_tokens)
        if isinstance(total, (int, float)) and isinstance(prompt_tokens, int):
            prompt_for_corr.append(float(prompt_tokens))
            latency_for_corr.append(float(total))
        if isinstance(total, (int, float)) and isinstance(generated_tokens, int):
            generated_for_corr.append(float(generated_tokens))
        if isinstance(peak, int):
            peak_memory.append(peak)
        if metrics.get("output_truncated") is True:
            output_truncated_count += 1
        if metrics.get("timed_out") is True:
            timed_out_count += 1
        if metrics.get("completed_json_object") is True:
            completed_json_count += 1
    slowest_cases = sorted(
        slow_candidates,
        key=lambda item: float(item.get("total_generation_latency_ms") or 0),
        reverse=True,
    )[:8]
    total_latency = round(sum(generation_latencies), 3) if generation_latencies else None
    return {
        "model_load_time_ms": model_load_time_ms,
        "first_output_latency_ms": first_latencies[0] if first_latencies else None,
        "average_first_output_latency_ms": (
            round(sum(first_latencies) / len(first_latencies), 3) if first_latencies else None
        ),
        "total_generation_latency_ms": total_latency,
        "average_generation_latency_ms": (
            round(sum(generation_latencies) / len(generation_latencies), 3) if generation_latencies else None
        ),
        "p50_generation_latency_ms": percentile(generation_latencies, 0.50),
        "p90_generation_latency_ms": percentile(generation_latencies, 0.90),
        "slowest_cases": slowest_cases,
        "tokens_generated": sum(generated_counts) if generated_counts else None,
        "generated_tokens_total": sum(generated_counts) if generated_counts else None,
        "prompt_tokens_total": sum(prompt_counts) if prompt_counts else None,
        "prompt_tokens_max": max(prompt_counts) if prompt_counts else None,
        "generated_tokens_max": max(generated_counts) if generated_counts else None,
        "completed_json_object_count": completed_json_count,
        "output_truncated_count": output_truncated_count,
        "timed_out_count": timed_out_count,
        "peak_gpu_memory_bytes": max(peak_memory) if peak_memory else None,
        "correlation": {
            "prompt_tokens_vs_latency": pearson(prompt_for_corr, latency_for_corr),
            "generated_tokens_vs_latency": pearson(generated_for_corr, generation_latencies),
        },
    }


def summarize_counts(case_results: list[dict[str, Any]]) -> dict[str, Any]:
    qwen_vs_deterministic = Counter(
        str(item.get("qwen_vs_deterministic", {}).get("outcome") or "unknown") for item in case_results
    )
    failure_classes = Counter(
        failure_class
        for item in case_results
        for failure_class in (item.get("qwen_gold_comparison", {}).get("failure_classes") or [])
    )
    property_summaries: dict[str, Counter[str]] = {}
    for item in case_results:
        property_outcomes = item.get("qwen_vs_deterministic", {}).get("property_outcomes") or {}
        for property_name, outcome in property_outcomes.items():
            property_summaries.setdefault(property_name, Counter())[str(outcome)] += 1
    return {
        "qwen_vs_deterministic_summary": dict(sorted(qwen_vs_deterministic.items())),
        "failure_class_counts": dict(sorted(failure_classes.items())),
        "quality_property_summary": {
            name: dict(sorted(counter.items())) for name, counter in sorted(property_summaries.items())
        },
    }


def parse_case_ids(values: list[str] | None) -> list[str]:
    case_ids: list[str] = []
    for value in values or []:
        for item in str(value).split(","):
            stripped = item.strip()
            if stripped:
                case_ids.append(stripped)
    return case_ids


def select_cases(
    gold_cases: list[dict[str, Any]],
    *,
    requested_case_ids: list[str],
    limit: int | None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    by_case_id = {str(case.get("case_id")): case for case in gold_cases}
    if requested_case_ids:
        missing = [case_id for case_id in requested_case_ids if case_id not in by_case_id]
        if missing:
            raise ValueError(f"unknown case id(s): {missing}")
        selected = [by_case_id[case_id] for case_id in requested_case_ids]
        if limit is not None:
            selected = selected[:limit]
        return selected, {
            "mode": "case_id",
            "requested_case_ids": requested_case_ids,
            "missing_case_ids": [],
            "limit": limit,
        }
    if limit is not None and limit >= 20:
        priority = [case_id for case_id in REPRESENTATIVE_CASE_IDS if case_id in by_case_id]
        remaining = [str(case.get("case_id")) for case in gold_cases if str(case.get("case_id")) not in set(priority)]
        ordered_ids = [*priority, *remaining]
        return [by_case_id[case_id] for case_id in ordered_ids[:limit]], {
            "mode": "representative_first_limit",
            "representative_case_ids_available": priority,
            "limit": limit,
        }
    selected = gold_cases if limit is None else gold_cases[:limit]
    return selected, {
        "mode": "gold_order",
        "limit": limit,
    }


def load_existing_case_results(selected_case_ids: set[str]) -> dict[str, dict[str, Any]]:
    if not RESULT_PATH.is_file():
        return {}
    try:
        existing = json.loads(RESULT_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}
    if not isinstance(existing, dict):
        return {}
    cases = existing.get("cases")
    if not isinstance(cases, list):
        return {}
    completed: dict[str, dict[str, Any]] = {}
    for item in cases:
        if not isinstance(item, dict):
            continue
        case_id = str(item.get("case_id") or "")
        if case_id in selected_case_ids:
            completed[case_id] = item
    return completed


def base_result(args: argparse.Namespace, config: Any, deps: dict[str, Any], hardware: dict[str, Any]) -> dict[str, Any]:
    return {
        "experiment_id": EXPERIMENT_ID,
        "generated_at": utc_now(),
        "status": "not_run",
        "quality_status": "not_run",
        "runner_implemented": True,
        "source_experiment_id": SOURCE_EXPERIMENT_ID,
        "gold_cases_path": str(GOLD_CASES_PATH.relative_to(ROOT)),
        "mock_outputs_path": str(MOCK_OUTPUTS_PATH.relative_to(ROOT)),
        "primary_model": PRIMARY_MODEL_ID,
        "local_model_path": config.model_path,
        "cache_path": config.cache_dir,
        "python_executable": sys.executable,
        "expected_python_environment": ".venv-llm",
        "expected_python_environment_active": in_expected_llm_env(),
        "dependencies_available": bool(deps.get("ready")),
        "dependency_status": deps,
        "dependency_versions": deps.get("versions") or {},
        "dependency_install_attempted": False,
        "dependency_install_succeeded": False,
        "hardware_summary": hardware,
        "cuda_available": bool(hardware.get("cuda_available")),
        "gpu_name": hardware.get("gpu_name"),
        "vram_total_bytes": hardware.get("vram_total_bytes"),
        "model_availability": None,
        "model_artifact_found": False,
        "model_download_attempted": False,
        "model_redownloaded": False,
        "inference_attempted": False,
        "model_loaded": False,
        "quantization_mode": config.quantization_mode,
        "quantization_mode_requested": config.quantization_mode,
        "quantization_mode_actually_used": None,
        "fallback_used": False,
        "fallback_attempts": [],
        "planner_schema_mode": COMPACT_PLANNER_SCHEMA_MODE,
        "planner_schema_mode_source": "explicit_goldset_eval_runner",
        "compact_adapter_status": "enabled",
        "generation_settings": {
            "max_input_tokens": config.max_input_tokens,
            "max_output_tokens": config.max_output_tokens,
            "timeout_ms": config.timeout_ms,
            "do_sample": False,
        },
        "selection": {
            "limit": args.limit,
            "case_ids": parse_case_ids(args.case_id),
            "resume": bool(args.resume),
            "skip_completed": bool(args.skip_completed),
        },
        "gold_case_count_total": 0,
        "case_count_attempted": 0,
        "case_count_completed": 0,
        "schema_valid_count": 0,
        "verifier_pass_count": 0,
        "compact_schema_valid_count": 0,
        "compact_expanded_schema_valid_count": 0,
        "compact_adapter_error_count": 0,
        "gold_match_count": 0,
        "exact_match_count": 0,
        "semantic_match_count": 0,
        "deterministic_semantic_match_count": 0,
        "deterministic_exact_match_count": 0,
        "repair_applied_count": 0,
        "truncation_count": 0,
        "failed_case_count": 0,
        "failed_cases": [],
        "failure_class_counts": {},
        "qwen_vs_deterministic_summary": {},
        "quality_property_summary": {},
        "current_utterance_fidelity_result": {},
        "and_or_fidelity_result": {},
        "negation_fidelity_result": {},
        "voice_not_writing_result": {},
        "team_state_poisoning_result": {},
        "internal_policy_leak_result": {},
        "fake_side_effect_result": {},
        "unsupported_claim_result": {},
        "sales_action_result": {},
        "latency_metrics": {
            "model_load_time_ms": None,
            "total_generation_latency_ms": None,
            "average_generation_latency_ms": None,
            "p50_generation_latency_ms": None,
            "p90_generation_latency_ms": None,
            "slowest_cases": [],
            "tokens_generated": None,
            "prompt_tokens_total": None,
            "peak_gpu_memory_bytes": None,
        },
        "local_model_calls_made": False,
        "local_model_call_count": 0,
        "provider_calls_made": False,
        "openai_api_calls_made": False,
        "live_tts_calls_made": False,
        "provider_side_effects_made": False,
        "model_weights_committed": git_model_weights_committed(),
        "runtime_behavior_changed": False,
        "response_text_changed": False,
        "raw_private_transcript_copied_to_public_evidence": False,
        "case_text_stored_in_evidence": False,
        "live_dialogue_replacement_changed": False,
        "local_llm_enabled_env": local_llm_enabled(),
        "experiment_enabled_env": local_llm_experiment_enabled(),
        "inference_gate": "explicit_offline_goldset_eval_script",
        "download_allowed_env_ignored": env_flag(DOWNLOAD_ENV_VAR),
        "notes": [
            f"{EXPERIMENT_ENV_VAR}/{LOCAL_LLM_ENABLED_ENV_VAR} are recorded but not required by this explicit offline eval.",
            "Model download is always disabled in this runner.",
            "Evidence stores case IDs and model outputs, not raw private transcripts.",
        ],
        "cases": [],
    }


def write_report(result: dict[str, Any]) -> None:
    latency = result.get("latency_metrics") or {}
    lines = [
        f"# {EXPERIMENT_ID}",
        "",
        "## Run Summary",
        "",
        f"- status: {result.get('status')}",
        f"- quality_status: {result.get('quality_status')}",
        f"- model_id: {result.get('primary_model')}",
        f"- planner_schema_mode: {result.get('planner_schema_mode')}",
        f"- case_count_attempted: {result.get('case_count_attempted')}",
        f"- case_count_completed: {result.get('case_count_completed')}",
        f"- schema_valid_count: {result.get('schema_valid_count')}",
        f"- verifier_pass_count: {result.get('verifier_pass_count')}",
        f"- gold_match_count: {result.get('gold_match_count')}",
        f"- exact_match_count: {result.get('exact_match_count')}",
        f"- semantic_match_count: {result.get('semantic_match_count')}",
        f"- deterministic_exact_match_count: {result.get('deterministic_exact_match_count')}",
        f"- deterministic_semantic_match_count: {result.get('deterministic_semantic_match_count')}",
        f"- failed_case_count: {result.get('failed_case_count')}",
        "",
        "## Qwen Versus Deterministic",
        "",
        f"- summary: {json.dumps(result.get('qwen_vs_deterministic_summary') or {}, ensure_ascii=False)}",
        f"- failure_classes: {json.dumps(result.get('failure_class_counts') or {}, ensure_ascii=False)}",
        "",
        "## Fidelity And Safety",
        "",
        f"- current_utterance_fidelity_result: {json.dumps(result.get('current_utterance_fidelity_result') or {}, ensure_ascii=False)}",
        f"- and_or_fidelity_result: {json.dumps(result.get('and_or_fidelity_result') or {}, ensure_ascii=False)}",
        f"- negation_fidelity_result: {json.dumps(result.get('negation_fidelity_result') or {}, ensure_ascii=False)}",
        f"- voice_not_writing_result: {json.dumps(result.get('voice_not_writing_result') or {}, ensure_ascii=False)}",
        f"- team_state_poisoning_result: {json.dumps(result.get('team_state_poisoning_result') or {}, ensure_ascii=False)}",
        f"- internal_policy_leak_result: {json.dumps(result.get('internal_policy_leak_result') or {}, ensure_ascii=False)}",
        f"- fake_side_effect_result: {json.dumps(result.get('fake_side_effect_result') or {}, ensure_ascii=False)}",
        f"- unsupported_claim_result: {json.dumps(result.get('unsupported_claim_result') or {}, ensure_ascii=False)}",
        f"- sales_action_result: {json.dumps(result.get('sales_action_result') or {}, ensure_ascii=False)}",
        "",
        "## Latency",
        "",
        f"- model_load_time_ms: {latency.get('model_load_time_ms')}",
        f"- total_generation_latency_ms: {latency.get('total_generation_latency_ms')}",
        f"- average_generation_latency_ms: {latency.get('average_generation_latency_ms')}",
        f"- p50_generation_latency_ms: {latency.get('p50_generation_latency_ms')}",
        f"- p90_generation_latency_ms: {latency.get('p90_generation_latency_ms')}",
        f"- slowest_cases: {json.dumps(latency.get('slowest_cases') or [], ensure_ascii=False)}",
        f"- tokens_generated: {latency.get('tokens_generated')}",
        f"- prompt_tokens_total: {latency.get('prompt_tokens_total')}",
        f"- peak_gpu_memory_bytes: {latency.get('peak_gpu_memory_bytes')}",
        f"- correlation: {json.dumps(latency.get('correlation') or {}, ensure_ascii=False)}",
        "",
        "## Side Effects",
        "",
        f"- local_model_calls_made: {str(result.get('local_model_calls_made')).lower()}",
        f"- local_model_call_count: {result.get('local_model_call_count')}",
        f"- provider_calls_made: {str(result.get('provider_calls_made')).lower()}",
        f"- openai_api_calls_made: {str(result.get('openai_api_calls_made')).lower()}",
        f"- live_tts_calls_made: {str(result.get('live_tts_calls_made')).lower()}",
        f"- provider_side_effects_made: {str(result.get('provider_side_effects_made')).lower()}",
        f"- model_download_attempted: {str(result.get('model_download_attempted')).lower()}",
        f"- model_redownloaded: {str(result.get('model_redownloaded')).lower()}",
        f"- model_weights_committed: {str(result.get('model_weights_committed')).lower()}",
        f"- runtime_behavior_changed: {str(result.get('runtime_behavior_changed')).lower()}",
        f"- response_text_changed: {str(result.get('response_text_changed')).lower()}",
        f"- raw_private_transcript_copied_to_public_evidence: {str(result.get('raw_private_transcript_copied_to_public_evidence')).lower()}",
        "",
        "## Failed Cases",
        "",
    ]
    failed_cases = result.get("failed_cases") or []
    if failed_cases:
        for item in failed_cases:
            lines.append(f"- {json.dumps(item, ensure_ascii=False)}")
    else:
        lines.append("- none")
    lines.extend(["", "## Notes", ""])
    lines.extend(f"- {item}" for item in (result.get("notes") or []))
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def persist(result: dict[str, Any]) -> None:
    write_json(RESULT_PATH, result)
    write_report(result)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run compact local Qwen on the 80-case conversation-brain gold set.")
    parser.add_argument("--limit", type=int, default=None, help="Run at most N selected cases.")
    parser.add_argument("--case-id", action="append", default=[], help="Run one case ID, or comma-separated case IDs.")
    parser.add_argument("--resume", action="store_true", help="Reuse previously completed case evidence when present.")
    parser.add_argument("--skip-completed", action="store_true", help="Do not rerun selected cases already present in evidence.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.limit is not None and args.limit < 0:
        raise SystemExit("--limit must be non-negative")

    config = goldset_config_from_env()
    deps = dependency_status(config.quantization_mode)
    hardware = hardware_summary()
    result = base_result(args, config, deps, hardware)

    if not in_expected_llm_env() or not deps.get("ready"):
        result["status"] = "wrong_python_environment"
        result["quality_status"] = "not_run"
        missing = deps.get("missing_required") or []
        result["failed_cases"] = []
        result["notes"].append(
            "Run with .venv-llm\\Scripts\\python.exe; plain python is expected to miss Torch/Transformers."
        )
        if missing:
            result["notes"].append(f"Missing local inference dependencies in this interpreter: {', '.join(missing)}")
        persist(result)
        print(json.dumps({"status": result["status"], "missing_dependencies": missing}, indent=2))
        return 1

    gold_cases = read_jsonl(GOLD_CASES_PATH)
    mock_records = read_jsonl(MOCK_OUTPUTS_PATH)
    deterministic_by_case = deterministic_output_by_case(mock_records)
    selected_cases, selection_details = select_cases(
        gold_cases,
        requested_case_ids=parse_case_ids(args.case_id),
        limit=args.limit,
    )
    result["gold_case_count_total"] = len(gold_cases)
    result["selection"].update(selection_details)
    result["case_count_attempted"] = len(selected_cases)

    selected_case_ids = {str(case.get("case_id")) for case in selected_cases}
    existing_case_results = load_existing_case_results(selected_case_ids) if (args.resume or args.skip_completed) else {}

    allow_download = False
    result["model_availability"] = ensure_model_available(config, allow_model_download=allow_download)
    result["model_artifact_found"] = bool(result["model_availability"].get("available"))
    result["model_download_attempted"] = bool(result["model_availability"].get("download_attempted"))
    if not result["model_availability"].get("available"):
        result["status"] = "model_missing_download_not_allowed"
        result["quality_status"] = "not_run"
        result["notes"].append(f"Model is not available at {config.model_path}; download is disabled for this phase.")
        persist(result)
        print(f"{EXPERIMENT_ID}: {result['status']}")
        return 1

    model = None
    tokenizer = None
    model_load_time_ms: float | None = None
    load_configs = [config]
    if config.quantization_mode == "4bit":
        load_configs.append(replace(config, quantization_mode="8bit"))
    for load_config in load_configs:
        started = time.perf_counter()
        try:
            model, tokenizer, _model_status = load_local_transformers_model(
                load_config,
                allow_model_download=allow_download,
            )
            config = load_config
            result["model_loaded"] = True
            result["quantization_mode_actually_used"] = config.quantization_mode
            result["fallback_used"] = config.quantization_mode != result["quantization_mode_requested"]
            model_load_time_ms = round((time.perf_counter() - started) * 1000, 3)
            result["fallback_attempts"].append(
                {
                    "quantization_mode": load_config.quantization_mode,
                    "status": "loaded",
                    "error": None,
                    "load_time_ms": model_load_time_ms,
                }
            )
            break
        except Exception as exc:
            result["fallback_attempts"].append(
                {
                    "quantization_mode": load_config.quantization_mode,
                    "status": "failed",
                    "error": str(exc),
                    "load_time_ms": round((time.perf_counter() - started) * 1000, 3),
                }
            )
    if model is None or tokenizer is None:
        result["status"] = "model_load_failed"
        result["quality_status"] = "not_run"
        result["notes"].append("Model load failed; no provider fallback was attempted.")
        persist(result)
        print(f"{EXPERIMENT_ID}: model_load_failed")
        return 1

    case_results: list[dict[str, Any]] = []
    result["inference_attempted"] = True
    for index, case in enumerate(selected_cases, start=1):
        case_id = str(case.get("case_id") or f"case_{index}")
        if (args.resume or args.skip_completed) and case_id in existing_case_results:
            reused = {**existing_case_results[case_id], "resume_reused": True}
            case_results.append(reused)
            print(json.dumps({"event": "case_reused", "index": index, "case_id": case_id}), flush=True)
            continue

        request_context = build_request_context(case)
        verifier_case = case_for_verifier(case)
        run_result = run_single_conversation_brain_case(
            config=config,
            request_context=request_context,
            case=verifier_case,
            allow_model_download=allow_download,
            model=model,
            tokenizer=tokenizer,
        ).to_dict()

        qwen_eval = evaluate_payload(
            payload=run_result.get("planner_output"),
            case=case,
            verifier_case=verifier_case,
        )
        deterministic_payload = deterministic_by_case.get(case_id)
        deterministic_eval = evaluate_payload(
            payload=deterministic_payload,
            case=case,
            verifier_case=verifier_case,
        )
        property_outcomes = property_comparison(
            qwen_eval["quality_flags"],
            deterministic_eval["quality_flags"],
        )
        outcome = comparison_outcome(qwen_eval, deterministic_eval)
        qwen_score = int(qwen_eval.get("score") or 0)
        deterministic_score = int(deterministic_eval.get("score") or 0)

        enriched = {
            **run_result,
            "source_type": case.get("source_type"),
            "qwen_gold_comparison": qwen_eval,
            "deterministic_gold_comparison": {
                "schema_errors": deterministic_eval["schema_errors"],
                "verifier_errors": deterministic_eval["verifier_errors"],
                "exact_mismatches": deterministic_eval["exact_mismatches"],
                "semantic_mismatches": deterministic_eval["semantic_mismatches"],
                "exact_match": deterministic_eval["exact_match"],
                "semantic_match": deterministic_eval["semantic_match"],
                "failure_classes": deterministic_eval["failure_classes"],
                "score": deterministic_score,
            },
            "qwen_vs_deterministic": {
                "outcome": outcome,
                "qwen_score": qwen_score,
                "deterministic_score": deterministic_score,
                "relative_winner": (
                    "qwen"
                    if qwen_score < deterministic_score
                    else "deterministic"
                    if deterministic_score < qwen_score
                    else "tie"
                ),
                "property_outcomes": property_outcomes,
            },
        }
        case_results.append(enriched)
        metrics = enriched.get("latency_metrics") or {}
        print(
            json.dumps(
                {
                    "event": "case_complete",
                    "index": index,
                    "total": len(selected_cases),
                    "case_id": case_id,
                    "status": enriched.get("status"),
                    "semantic_match": qwen_eval.get("semantic_match"),
                    "latency_ms": metrics.get("total_generation_latency_ms"),
                    "tokens_generated": metrics.get("tokens_generated"),
                },
                ensure_ascii=False,
            ),
            flush=True,
        )

    result["cases"] = case_results
    result["case_count_completed"] = len(case_results)
    result["local_model_call_count"] = sum(1 for item in case_results if item.get("resume_reused") is not True)
    result["local_model_calls_made"] = result["local_model_call_count"] > 0
    result["schema_valid_count"] = sum(
        1 for item in case_results if item.get("planner_output") is not None and not item.get("schema_errors")
    )
    result["verifier_pass_count"] = sum(
        1
        for item in case_results
        if item.get("planner_output") is not None
        and not item.get("schema_errors")
        and not item.get("verifier_errors")
        and not item.get("errors")
    )
    result["compact_schema_valid_count"] = sum(
        1
        for item in case_results
        if item.get("compact_planner_output") is not None and not item.get("compact_schema_errors")
    )
    result["compact_expanded_schema_valid_count"] = sum(
        1
        for item in case_results
        if item.get("planner_output") is not None and not item.get("schema_errors")
    )
    result["compact_adapter_error_count"] = sum(len(item.get("compact_adapter_errors") or []) for item in case_results)
    result["gold_match_count"] = sum(1 for item in case_results if item.get("qwen_gold_comparison", {}).get("exact_match"))
    result["exact_match_count"] = result["gold_match_count"]
    result["semantic_match_count"] = sum(
        1 for item in case_results if item.get("qwen_gold_comparison", {}).get("semantic_match")
    )
    result["deterministic_semantic_match_count"] = sum(
        1 for item in case_results if item.get("deterministic_gold_comparison", {}).get("semantic_match")
    )
    result["deterministic_exact_match_count"] = sum(
        1 for item in case_results if item.get("deterministic_gold_comparison", {}).get("exact_match")
    )
    result["repair_applied_count"] = sum(1 for item in case_results if item.get("repair_applied"))
    result["latency_metrics"] = aggregate_latency(case_results, model_load_time_ms)
    result["truncation_count"] = int(result["latency_metrics"].get("output_truncated_count") or 0)

    failed_cases: list[dict[str, Any]] = []
    for item in case_results:
        failure_classes = item.get("qwen_gold_comparison", {}).get("failure_classes") or []
        semantic_match = bool(item.get("qwen_gold_comparison", {}).get("semantic_match"))
        if item.get("status") != "pass" or not semantic_match:
            failed_cases.append(
                {
                    "case_id": item.get("case_id"),
                    "runner_status": item.get("status"),
                    "semantic_match": semantic_match,
                    "failure_classes": failure_classes,
                    "schema_errors": item.get("schema_errors") or [],
                    "verifier_errors": item.get("verifier_errors") or [],
                    "semantic_mismatches": item.get("qwen_gold_comparison", {}).get("semantic_mismatches") or [],
                }
            )
    result["failed_cases"] = failed_cases
    result["failed_case_count"] = len(failed_cases)
    count_summaries = summarize_counts(case_results)
    result.update(count_summaries)
    quality_summary = result.get("quality_property_summary") or {}
    result["current_utterance_fidelity_result"] = quality_summary.get("current_utterance_fidelity", {})
    result["and_or_fidelity_result"] = quality_summary.get("and_or_fidelity", {})
    result["negation_fidelity_result"] = quality_summary.get("negation_fidelity", {})
    result["voice_not_writing_result"] = quality_summary.get("voice_not_writing", {})
    result["team_state_poisoning_result"] = quality_summary.get("team_state_poisoning", {})
    result["internal_policy_leak_result"] = quality_summary.get("internal_policy_leak", {})
    result["fake_side_effect_result"] = quality_summary.get("fake_side_effect", {})
    result["unsupported_claim_result"] = quality_summary.get("unsupported_claim", {})
    result["sales_action_result"] = quality_summary.get("sales_action", {})
    result["quality_status"] = "pass" if result["failed_case_count"] == 0 else "fail"
    result["status"] = "completed" if result["case_count_completed"] == result["case_count_attempted"] else "partial"
    persist(result)
    print(f"{EXPERIMENT_ID}: {result['status']} quality={result['quality_status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
