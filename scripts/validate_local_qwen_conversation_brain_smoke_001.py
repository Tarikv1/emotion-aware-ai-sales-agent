#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.llm_brain.conversation_brain_schema import (  # noqa: E402
    PRIMARY_MODEL_ID,
    validate_conversation_brain_output,
)
from runtime.llm_brain.local_conversation_brain import (  # noqa: E402
    default_local_conversation_brain_config,
)
try:
    from runtime.llm_brain.local_transformers_runner import parse_and_repair_planner_output  # noqa: E402
except ImportError:  # pragma: no cover - reported by validator
    parse_and_repair_planner_output = None  # type: ignore[assignment]


EXPERIMENT_ID = "LOCAL-QWEN-CONVERSATION-BRAIN-SMOKE-001"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / EXPERIMENT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"
SMOKE_SCRIPT = ROOT / "scripts" / "run_local_qwen_conversation_brain_smoke_001.py"

REQUIRED_GITIGNORE_PATTERNS = {
    ".venv-llm/",
    "local_artifacts/",
    "models/",
    "hf-cache/",
    "llm-checkpoints/",
    "*.gguf",
    "*.safetensors",
    "*.pt",
    "*.pth",
    "*.bin",
}

EXPECTED_DEFAULTS = {
    "enabled": False,
    "provider": "local_transformers",
    "model_id": "Qwen/Qwen2.5-7B-Instruct",
    "model_path": "local_artifacts/models/qwen2.5-7b-instruct",
    "cache_dir": "local_artifacts/cache/huggingface",
    "quantization_mode": "4bit",
    "device": "cuda",
}

FILES_WITH_NO_PROVIDER_CALLS = [
    ROOT / "runtime" / "llm_brain" / "local_conversation_brain.py",
    ROOT / "runtime" / "llm_brain" / "conversation_brain_schema.py",
    ROOT / "runtime" / "llm_brain" / "conversation_brain_prompts.py",
    ROOT / "runtime" / "llm_brain" / "local_transformers_runner.py",
    SMOKE_SCRIPT,
]

BLOCKED_PROVIDER_PATTERNS = {
    "openai import": re.compile(r"(^|\n)\s*(from\s+openai\b|import\s+openai\b)", re.I),
    "anthropic import": re.compile(r"(^|\n)\s*(from\s+anthropic\b|import\s+anthropic\b)", re.I),
    "elevenlabs import": re.compile(r"(^|\n)\s*(from\s+elevenlabs\b|import\s+elevenlabs\b)", re.I),
    "cartesia import": re.compile(r"(^|\n)\s*(from\s+cartesia\b|import\s+cartesia\b)", re.I),
    "requests call": re.compile(r"\brequests\.(get|post|put|patch|delete)\s*\(", re.I),
    "httpx call": re.compile(r"\bhttpx\.(get|post|put|patch|delete|Client|AsyncClient)\s*\(", re.I),
    "urllib urlopen": re.compile(r"\burllib\.request\.urlopen\s*\(", re.I),
    "email smtp": re.compile(r"\bsmtplib\b", re.I),
    "calendar api": re.compile(r"\bgoogleapiclient\b|\bgoogle\.oauth\b", re.I),
}

LIVE_RUNTIME_WIRING_PATTERNS = (
    "local_transformers_runner",
    "run_local_qwen_conversation_brain_smoke_001",
    "ENABLE_LOCAL_LLM_BRAIN_EXPERIMENT",
    "LOCAL_LLM_ENABLED",
)


def repair_probe_payload() -> dict[str, Any]:
    return {
        "semantic_frame": {
            "semantic_family": "use_case_scope",
            "speech_act": "use_case_statement",
            "sub_intent": "workflow_need",
            "object_type": "use_case",
            "object_mentions": "voice",
            "conjunction_relation": "and",
            "negation_scope": "none",
            "buyer_state": "evaluating",
            "buyer_emotion_hint": "neutral",
            "commercial_intent": "medium",
            "current_utterance_fidelity_notes": "preserve current buyer words exactly",
        },
        "state_update": {
            "should_update_adoption_state": "false",
            "should_update_use_case": "true",
            "use_case_values": "voice",
            "should_update_usage_intensity": "false",
            "usage_intensity": "unknown",
            "should_update_team_state": "false",
            "should_update_recommendation": "false",
            "should_update_close_readiness": "false",
            "blocked_updates": [],
            "reason": "buyer named use case scope",
        },
        "sales_strategy": {
            "next_action": "ask_usage_intensity",
            "should_answer_directly": "true",
            "should_ask_question": "true",
            "should_recommend": "false",
            "should_reframe_objction": "false",
            "should_close": "false",
            "should_disqualify": "false",
            "persuasion_strategy": "diagnose before recommending",
            "one_next_step": "ask_usage_intensity",
        },
        "response_plan": {
            "must_include": "usage intensity",
            "must_not_include": "writing",
            "campaign_facts_needed": "public_plan_names",
            "buyer_words_to_preserve": "voice",
            "response_tone": "plain spoken sales; direct_price_question 1-2 sentences; explanation_request 2-4",
            "max_sentence_count": 2,
        },
        "draft_response": "I hear voice. The next useful step is usage intensity.",
        "safety_flags": {
            "needs_fact_check": "false",
            "unsupported_product_claim_risk": "false",
            "side_effect_claim_risk": "false",
            "affiliation_claim_risk": "false",
            "internal_policy_language_risk": "false",
            "raw_url_risk": "false",
            "campaign_leakage_risk": "false",
        },
        "confidence": "0.75",
        "reasons": "current utterance wording is preserved",
    }


def validate_repair_layer(failures: list[str]) -> None:
    if parse_and_repair_planner_output is None:
        failures.append("missing repair API: runtime.llm_brain.local_transformers_runner.parse_and_repair_planner_output")
        return
    raw = "```json\n" + json.dumps(repair_probe_payload(), ensure_ascii=False) + "\n```\ntrailing text"
    repaired, diagnostics = parse_and_repair_planner_output(raw)
    if repaired is None:
        failures.append(f"repair probe returned no payload: {diagnostics.to_dict()!r}")
        return
    schema_errors = validate_conversation_brain_output(repaired)
    if schema_errors:
        failures.append(f"repair probe schema errors after repair: {schema_errors!r}")
    expected_repair_types = {
        "markdown_code_fence_removed",
        "first_json_object_extracted",
        "known_key_typo:sales_strategy.should_reframe_objction->should_reframe_objection",
        "list_coercion:semantic_frame.object_mentions",
        "list_coercion:state_update.use_case_values",
        "list_coercion:response_plan.must_include",
        "list_coercion:response_plan.must_not_include",
        "list_coercion:response_plan.campaign_facts_needed",
        "list_coercion:response_plan.buyer_words_to_preserve",
        "list_coercion:reasons",
        "boolean_string_coercion:sales_strategy.should_reframe_objection",
        "confidence_number_string_coercion",
    }
    actual_repair_types = set(diagnostics.repair_types)
    missing = sorted(expected_repair_types - actual_repair_types)
    if missing:
        failures.append(f"repair probe missing repair type(s): {missing}")
    if repaired["draft_response"] != repair_probe_payload()["draft_response"]:
        failures.append("repair probe must not rewrite draft_response semantics")
    if repaired["semantic_frame"]["conjunction_relation"] != "and":
        failures.append("repair probe must not flip conjunction_relation")
    if repaired["response_plan"]["buyer_words_to_preserve"] != ["voice"]:
        failures.append("repair probe must not add missing buyer words")
    incomplete_outer = '{"semantic_frame":{"semantic_family":"partial"}'
    nested_payload, nested_diagnostics = parse_and_repair_planner_output(incomplete_outer)
    if nested_payload is not None:
        failures.append(
            "repair parser must not extract a nested object from an incomplete top-level JSON object: "
            f"{nested_payload!r}; diagnostics={nested_diagnostics.to_dict()!r}"
        )


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def read_gitignore_patterns() -> set[str]:
    gitignore = ROOT / ".gitignore"
    if not gitignore.is_file():
        return set()
    patterns: set[str] = set()
    for raw in gitignore.read_text(encoding="utf-8").splitlines():
        stripped = raw.strip()
        if stripped and not stripped.startswith("#"):
            patterns.add(stripped.replace("\\", "/"))
    return patterns


def is_project_local_relative(path_text: str) -> bool:
    path = Path(path_text)
    if path.is_absolute():
        return False
    return ".." not in path.parts


def validate_static_contract(failures: list[str]) -> None:
    if not SMOKE_SCRIPT.is_file():
        failures.append(f"missing smoke script: {rel(SMOKE_SCRIPT)}")

    config = default_local_conversation_brain_config()
    for key, expected in EXPECTED_DEFAULTS.items():
        actual = getattr(config, key, None)
        if actual != expected:
            failures.append(f"default config {key} expected {expected!r}, got {actual!r}")

    model_path = getattr(config, "model_path", "")
    cache_dir = getattr(config, "cache_dir", "")
    if not is_project_local_relative(str(model_path)):
        failures.append(f"model_path must be project-local relative, got {model_path!r}")
    if not str(model_path).replace("\\", "/").startswith("local_artifacts/models/"):
        failures.append(f"model_path must live under local_artifacts/models/, got {model_path!r}")
    if not is_project_local_relative(str(cache_dir)):
        failures.append(f"cache_dir must be project-local relative, got {cache_dir!r}")
    if not str(cache_dir).replace("\\", "/").startswith("local_artifacts/cache/"):
        failures.append(f"cache_dir must live under local_artifacts/cache/, got {cache_dir!r}")

    gitignore_patterns = read_gitignore_patterns()
    missing = sorted(REQUIRED_GITIGNORE_PATTERNS - gitignore_patterns)
    if missing:
        failures.append(f".gitignore missing local model artifact pattern(s): {missing}")


def validate_no_provider_calls(failures: list[str]) -> None:
    for path in FILES_WITH_NO_PROVIDER_CALLS:
        if not path.is_file():
            failures.append(f"missing local LLM file for provider-call scan: {rel(path)}")
            continue
        text = path.read_text(encoding="utf-8")
        for label, pattern in BLOCKED_PROVIDER_PATTERNS.items():
            if pattern.search(text):
                failures.append(f"{rel(path)} contains blocked provider/network pattern: {label}")


def validate_no_live_runtime_wiring(failures: list[str]) -> None:
    live_dirs = [
        ROOT / "runtime" / "core",
        ROOT / "runtime" / "entrypoints",
        ROOT / "runtime" / "voice",
        ROOT / "runtime" / "providers",
    ]
    for live_dir in live_dirs:
        if not live_dir.is_dir():
            continue
        for path in live_dir.rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            for pattern in LIVE_RUNTIME_WIRING_PATTERNS:
                if pattern in text:
                    failures.append(f"live runtime file references local Qwen smoke wiring: {rel(path)} -> {pattern}")


def validate_evidence(failures: list[str]) -> str:
    if not RESULT_PATH.exists() and not REPORT_PATH.exists():
        return "not_run"
    if not RESULT_PATH.is_file():
        failures.append(f"missing result evidence: {rel(RESULT_PATH)}")
        return "invalid"
    if not REPORT_PATH.is_file():
        failures.append(f"missing report evidence: {rel(REPORT_PATH)}")
    try:
        result = json.loads(RESULT_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        failures.append(f"result.json invalid JSON: {exc}")
        return "invalid"
    if not isinstance(result, dict):
        failures.append("result.json must be a JSON object")
        return "invalid"

    required_fields = {
        "experiment_id",
        "runner_implemented",
        "primary_model",
        "local_model_path",
        "cache_path",
        "dependencies_available",
        "model_artifact_found",
        "model_download_attempted",
        "inference_attempted",
        "model_loaded",
        "dependency_status",
        "dependency_install_attempted",
        "dependency_install_succeeded",
        "dependency_versions",
        "cuda_available",
        "gpu_name",
        "quantization_mode",
        "quantization_mode_requested",
        "quantization_mode_actually_used",
        "fallback_used",
        "smoke_case_count",
        "schema_valid_count",
        "verifier_pass_count",
        "schema_valid_before_repair_count",
        "schema_valid_after_repair_count",
        "repair_applied_count",
        "repair_types",
        "needs_fact_check_before_repair_count",
        "needs_fact_check_after_repair_count",
        "buyer_word_preservation_errors_before_repair",
        "buyer_word_preservation_errors_after_repair",
        "failed_cases",
        "latency_metrics",
        "local_model_calls_made",
        "provider_calls_made",
        "runtime_behavior_changed",
        "response_text_changed",
        "wsl_required",
        "wsl_optional_for_future_training",
    }
    missing = sorted(required_fields - set(result))
    if missing:
        failures.append(f"result.json missing field(s): {missing}")
    if result.get("experiment_id") != EXPERIMENT_ID:
        failures.append(f"result.json experiment_id mismatch: {result.get('experiment_id')!r}")
    if result.get("primary_model") != PRIMARY_MODEL_ID:
        failures.append(f"primary_model must be {PRIMARY_MODEL_ID!r}")
    if result.get("runner_implemented") is not True:
        failures.append("runner_implemented must be true once evidence exists")
    for key, expected in {
        "provider_calls_made": False,
        "runtime_behavior_changed": False,
        "response_text_changed": False,
        "wsl_required": False,
        "wsl_optional_for_future_training": True,
    }.items():
        if result.get(key) is not expected:
            failures.append(f"result.json {key} must be {expected!r}")
    if not result.get("inference_attempted"):
        if result.get("model_loaded") is not False:
            failures.append("model_loaded must stay false when inference_attempted is false")
        if result.get("local_model_calls_made") is not False:
            failures.append("local_model_calls_made must stay false when inference_attempted is false")
    if result.get("status") == "model_missing_download_not_allowed":
        if result.get("model_artifact_found") is not False:
            failures.append("model_missing_download_not_allowed requires model_artifact_found=false")
        if result.get("model_download_attempted") is not False:
            failures.append("model_missing_download_not_allowed requires model_download_attempted=false")

    cases = result.get("cases", [])
    if cases is None:
        cases = []
    if not isinstance(cases, list):
        failures.append("result.json cases must be a list when present")
        return "invalid"
    for index, case_result in enumerate(cases, start=1):
        if not isinstance(case_result, dict):
            failures.append(f"cases[{index}] must be an object")
            continue
        planner_output = case_result.get("planner_output")
        schema_errors = case_result.get("schema_errors", [])
        raw_schema_errors = case_result.get("raw_schema_errors_before_repair", [])
        schema_errors_after_repair = case_result.get("schema_errors_after_repair", schema_errors)
        if not isinstance(raw_schema_errors, list):
            failures.append(f"cases[{index}].raw_schema_errors_before_repair must be a list")
        if schema_errors_after_repair != schema_errors:
            failures.append(f"cases[{index}].schema_errors_after_repair must match schema_errors")
        if "repair_applied" not in case_result:
            failures.append(f"cases[{index}].repair_applied is required")
        if not isinstance(case_result.get("repair_types", []), list):
            failures.append(f"cases[{index}].repair_types must be a list")
        if "verifier_errors_after_repair" not in case_result:
            failures.append(f"cases[{index}].verifier_errors_after_repair is required")
        if planner_output is not None:
            if not isinstance(planner_output, dict):
                failures.append(f"cases[{index}].planner_output must be an object or null")
            else:
                actual_schema_errors = validate_conversation_brain_output(planner_output)
                if actual_schema_errors != schema_errors:
                    failures.append(
                        f"cases[{index}] schema_errors mismatch: expected {actual_schema_errors!r}, got {schema_errors!r}"
                    )

    return str(result.get("status") or "present")


def main() -> int:
    failures: list[str] = []
    validate_repair_layer(failures)
    validate_static_contract(failures)
    validate_no_provider_calls(failures)
    validate_no_live_runtime_wiring(failures)
    evidence_status = validate_evidence(failures)

    summary: dict[str, Any] = {
        "validator": "validate_local_qwen_conversation_brain_smoke_001",
        "status": "pass" if not failures else "fail",
        "evidence_status": evidence_status,
        "failures": failures,
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
