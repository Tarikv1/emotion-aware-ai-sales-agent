#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from benchmark_local_qwen_live_action_latency_001 import (  # noqa: E402
    FACT_IDS,
    FACT_SUMMARIES,
    live_action_prompt,
    summarize_mode,
)
from local_ollama_qwen_utils_001 import (  # noqa: E402
    GENERATED_DIR,
    OLLAMA_PULL_ENV_VAR,
    TARGETS_SECONDS,
    approx_token_count,
    audit_side_effects,
    env_flag,
    env_gate_report,
    http_json,
    mode_target_met,
    ollama_benchmark_enabled,
    ollama_model_names,
    utc_now,
    write_json,
    write_text,
)
from runtime.llm_brain.live_action_prompt import default_available_action_ids  # noqa: E402
from runtime.llm_brain.live_action_verifier import (  # noqa: E402
    parse_live_action_json,
    signature,
    verify_live_action_output,
)


BENCHMARK_ID = "LOCAL-OLLAMA-SMALL-LIVE-ACTION-MODEL-BENCHMARK-001"
DECISION_ID = "LOCAL-OLLAMA-SMALL-LIVE-ACTION-MODEL-DECISION-001"
REGISTRY_PATH = ROOT / "runtime" / "llm_brain" / "training" / "ollama_small_live_action_model_registry.json"
BENCHMARK_OUT_DIR = GENERATED_DIR / BENCHMARK_ID
BENCHMARK_RESULT_PATH = BENCHMARK_OUT_DIR / "result.json"
BENCHMARK_REPORT_PATH = BENCHMARK_OUT_DIR / "report.md"
DECISION_OUT_DIR = GENERATED_DIR / DECISION_ID
DECISION_RESULT_PATH = DECISION_OUT_DIR / "result.json"
DECISION_REPORT_PATH = DECISION_OUT_DIR / "report.md"

PRIMARY_MODELS = [
    "qwen2.5:0.5b",
    "qwen2.5:1.5b",
    "gemma3:270m",
    "gemma3:1b",
    "smollm2:1.7b",
    "llama3.2:1b",
]
REFERENCE_MODEL = "qwen2.5:7b"
MODE_NAMES = [
    "constrained_action_selector_prompt",
    "ultra_minimal_action_id_only",
    "minimal_live_action_prompt",
]
MODE_NUM_PREDICT = {
    "constrained_action_selector_prompt": 48,
    "ultra_minimal_action_id_only": 16,
    "minimal_live_action_prompt": 64,
}

ACTION_DESCRIPTIONS = {
    "orient_plan_options": "orient the buyer to plan options",
    "ask_adoption_state": "ask whether this is individual or team use",
    "ask_use_case_gap": "ask what the buyer wants to use it for",
    "ask_usage_intensity": "ask how often or how deeply they will use it",
    "answer_price": "answer a direct price or cost question with caution",
    "answer_plan_fit": "recommend or explain plan fit",
    "compare_plus_vs_pro": "compare Plus and Pro",
    "handle_price_objection": "handle price or value objection",
    "handle_competitor_context": "handle another AI tool or competitor context",
    "answer_signup_path": "explain signup or upgrade path",
    "answer_plan_change": "answer whether plan can change later",
    "answer_source_or_affiliation": "answer affiliation or source question",
    "respect_boundary": "respect privacy, wrong-product, or unsupported side-effect boundaries",
    "terminal_close": "close after buyer acceptance or thanks",
    "disqualify_no_fit": "acknowledge no fit without pushing",
    "clarify_unclear_tool": "clarify cloud versus Claude or unclear tool words",
    "clarify_question_scope": "clarify a vague or confused buyer question",
    "replan_after_repeat": "move forward after repeated question risk",
}


def benchmark_cases() -> list[dict[str, Any]]:
    base_memory = {
        "last_action_id": "",
        "last_action_slot_signature": "",
        "last_agent_question": "",
        "last_response_signature": "",
        "answered_topics": [],
        "asked_topic_counts": {},
        "known_slots": {},
    }

    def case(case_id: str, category: str, buyer: str, **overrides: Any) -> dict[str, Any]:
        memory = {**base_memory, **overrides.pop("memory", {})}
        memory["current_buyer_utterance"] = buyer
        return {"case_id": case_id, "category": category, "buyer": buyer, "memory": memory, **overrides}

    return [
        case("direct_price_001", "direct price", "How much is Plus?"),
        case("terminal_thanks_001", "terminal thanks", "Ok, I will check that, thanks.", memory={"terminal_acceptance_seen": True}),
        case("current_tool_and_001", "current tool AND", "I use ChatGPT and Claude."),
        case("current_tool_or_001", "current tool OR", "I use ChatGPT or maybe Claude."),
        case("not_team_001", "not team", "I am by myself, not a team.", memory={"known_slots": {"team_state": False}}),
        case("coding_voice_001", "coding and voice", "I use it for coding workflow and voice."),
        case("plan_explanation_001", "plan explanation", "What are the plans actually?"),
        case("price_objection_001", "price objection", "Plus sounds expensive for what it is."),
        case("competitor_objection_001", "competitor objection", "Why not just use Claude instead?"),
        case("unsupported_side_effect_001", "unsupported side-effect request", "Can you just buy Plus for me?"),
        case(
            "repeated_question_risk_001",
            "repeated question risk",
            "You just asked that.",
            memory={
                "last_action_id": "ask_use_case_gap",
                "last_action_slot_signature": signature({}),
                "last_agent_question": "What would you mainly use it for?",
                "last_response_signature": "What would you mainly use it for?",
                "new_buyer_info_since_last_action": False,
            },
        ),
        case(
            "buyer_already_told_you_001",
            "buyer says already told you",
            "I already told you, coding and voice.",
            memory={
                "last_action_id": "ask_use_case_gap",
                "last_action_slot_signature": signature({}),
                "last_agent_question": "What would you mainly use it for?",
                "last_response_signature": "What would you mainly use it for?",
                "known_slots": {"use_case": ["coding", "voice"]},
                "buyer_said_already_told_you": True,
                "new_buyer_info_since_last_action": False,
            },
        ),
        case("asr_ambiguity_cloud_claude_001", "ASR ambiguity cloud/Claude", "I use cloud for this maybe, or Claude, not sure."),
        case("no_fit_001", "no-fit", "I barely use AI and the free plan is enough."),
        case("signup_path_001", "signup path", "Where do I sign up?"),
        case("plan_change_001", "plan change", "Can I start lower and upgrade later?"),
        case("source_affiliation_001", "source/affiliation", "Are you from OpenAI or just recommending this?"),
        case("privacy_data_question_001", "privacy/data question", "Do you store what I say in this call?"),
        case("wrong_product_001", "wrong product", "I need help with Gmail, not ChatGPT."),
        case("unclear_confused_buyer_001", "unclear/confused buyer", "I am confused. What are you actually asking me?"),
    ]


def compact_context(case: dict[str, Any]) -> dict[str, Any]:
    return {
        "buyer": case["buyer"],
        "memory": case.get("memory") or {},
        "action_ids": default_available_action_ids(),
        "action_id_meanings": ACTION_DESCRIPTIONS,
        "approved_fact_ids": FACT_IDS,
        "approved_fact_summaries": FACT_SUMMARIES,
    }


def constrained_action_selector_prompt(case: dict[str, Any]) -> str:
    return "\n".join(
        [
            "You are a local sales-call action selector.",
            "Return exactly one JSON object. No markdown. No reasoning.",
            'Required JSON shape: {"action_id":"...","say":"..."}',
            'Optional keys: "slots" as an object, "uncertainty" as a string, "confidence" as a number.',
            "Use one provided action_id. Keep say short, natural, buyer-facing, and safe.",
            "Do not claim email, calendar, CRM, purchase, ticket, TTS, or other side effects happened.",
            "Do not mention schemas, routes, verifier, policy, confidence, or internal classification.",
            "Preserve AND versus OR, voice versus writing, and not-team corrections.",
            "Context:",
            json.dumps(compact_context(case), ensure_ascii=False, separators=(",", ":")),
        ]
    )


def ultra_minimal_action_id_only_prompt(case: dict[str, Any]) -> str:
    context = compact_context(case)
    context.pop("approved_fact_summaries", None)
    return "\n".join(
        [
            "Choose the next sales-call action_id only.",
            "Return exactly one JSON object and no other text.",
            'Required JSON shape: {"action_id":"..."}',
            "Do not include say, slots, memory_updates, reasoning, or confidence.",
            "Use one provided action_id.",
            "Context:",
            json.dumps(context, ensure_ascii=False, separators=(",", ":")),
        ]
    )


def modes_for_case(case: dict[str, Any]) -> dict[str, str]:
    return {
        "constrained_action_selector_prompt": constrained_action_selector_prompt(case),
        "ultra_minimal_action_id_only": ultra_minimal_action_id_only_prompt(case),
        "minimal_live_action_prompt": live_action_prompt(case),
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--include-7b-reference", action="store_true")
    return parser.parse_args(argv)


def model_list(include_reference: bool) -> list[str]:
    models = list(PRIMARY_MODELS)
    if include_reference:
        models.append(REFERENCE_MODEL)
    return models


def base_result(limit: int | None, include_reference: bool) -> dict[str, Any]:
    cases = benchmark_cases()
    if limit is not None:
        cases = cases[: max(0, limit)]
    return {
        "experiment_id": BENCHMARK_ID,
        "generated_at": utc_now(),
        "status": "not_run",
        "benchmark_run": False,
        "not_run_reason": "",
        "backend": "ollama_local",
        "localhost_api_base": "http://localhost:11434",
        "localhost_only": True,
        "provider_api": False,
        "registry": str(REGISTRY_PATH.relative_to(ROOT)).replace("\\", "/"),
        "env_gates": env_gate_report(),
        "include_7b_reference": include_reference,
        "models_requested": model_list(include_reference),
        "primary_models": PRIMARY_MODELS,
        "reference_model": REFERENCE_MODEL,
        "mode_names": MODE_NAMES,
        "case_count": len(cases),
        "case_ids": [case["case_id"] for case in cases],
        "case_categories": [case["category"] for case in cases],
        "latency_targets_seconds": TARGETS_SECONDS,
        "target_met": False,
        "quality_acceptable": False,
        "best_model_mode": None,
        "best_latency_model_mode": None,
        "fastest_valid_model_mode": None,
        "metrics_by_model_mode": {},
        "all_metrics_by_model_mode": {},
        "model_summaries": {},
        "cold_requests_by_model": {},
        "rows": [],
        "model_present_by_model": {},
        "model_loaded_by_model": {},
        "pull_attempted_by_model": {},
        "pull_allowed": env_flag(OLLAMA_PULL_ENV_VAR),
        "ollama_pull_attempted": False,
        "local_model_calls_made": False,
        "ollama_localhost_api_attempted": False,
        "ollama_localhost_calls_made": False,
        "ollama_localhost_api_call_count": 0,
        "ollama_local_model_call_count": 0,
        "provider_calls_made": False,
        "openai_api_calls_made": False,
        "live_tts_calls_made": False,
        "provider_side_effects_made": False,
        "training_rerun": False,
        "actual_pruning_performed": False,
        "runtime_behavior_changed": False,
        "response_text_changed": False,
        "adapter_live_ready": False,
        "live_wiring_allowed": False,
        "model_weights_committed": False,
        "adapter_weights_committed": False,
        "raw_private_transcript_included": False,
        "raw_private_transcript_copied_to_public_evidence": False,
        "side_effects": audit_side_effects(),
    }


def maybe_pull_model(model_name: str) -> tuple[bool, dict[str, Any] | None, str]:
    if not env_flag(OLLAMA_PULL_ENV_VAR):
        return False, None, "pull_not_allowed"
    payload, error = http_json(
        "/api/pull",
        method="POST",
        payload={"name": model_name, "stream": False},
        timeout_s=900.0,
    )
    return True, payload, error


def generate_ollama(model_name: str, prompt: str, *, mode: str) -> tuple[str, dict[str, Any], float]:
    payload = {
        "model": model_name,
        "prompt": prompt + "\n\nReturn exactly the requested JSON object and no markdown.",
        "stream": False,
        "format": "json",
        "keep_alive": "20m",
        "options": {
            "temperature": 0,
            "num_predict": MODE_NUM_PREDICT[mode],
        },
    }
    started = time.perf_counter()
    response, error = http_json("/api/generate", method="POST", payload=payload, timeout_s=180.0)
    wall_s = round(time.perf_counter() - started, 3)
    if response is None:
        raise RuntimeError(error or "ollama generate failed")
    return str(response.get("response") or ""), response, wall_s


def verifier_dict(status: str, *, errors: list[str] | None = None, replan_reasons: list[str] | None = None, hard_block_reasons: list[str] | None = None, warnings: list[str] | None = None) -> dict[str, Any]:
    resolved_errors = sorted(set(errors or []))
    resolved_replans = sorted(set(replan_reasons or []))
    resolved_hard_blocks = sorted(set(hard_block_reasons or []))
    if resolved_errors:
        status = "invalid"
    elif resolved_hard_blocks:
        status = "hard_block"
    elif resolved_replans:
        status = "replan_required"
    return {
        "status": status,
        "valid": status == "pass",
        "replan_required": status == "replan_required",
        "hard_block": status == "hard_block",
        "errors": resolved_errors,
        "replan_reasons": resolved_replans,
        "hard_block_reasons": resolved_hard_blocks,
        "warnings": sorted(set(warnings or [])),
    }


def verify_action_only(payload: dict[str, Any] | None, parse_errors: list[str]) -> dict[str, Any]:
    if payload is None:
        return {"status": "not_applicable"}
    allowed = set(default_available_action_ids())
    errors: list[str] = []
    action_id = payload.get("action_id")
    if not isinstance(action_id, str) or not action_id.strip():
        errors.append("action_id_must_be_non_empty_string")
    elif action_id not in allowed:
        errors.append(f"action_id_not_allowed:{action_id}")
    extra = sorted(set(payload) - {"action_id"})
    if "say" in payload:
        errors.append("say_forbidden_in_action_only")
    if extra:
        errors.append(f"unsupported_fields:{extra}")
    if parse_errors:
        errors.extend(parse_errors)
    return verifier_dict("pass", errors=errors, warnings=["action_only_no_say_quality_limited"])


def verify_constrained_selector(payload: dict[str, Any] | None, parse_errors: list[str], case: dict[str, Any]) -> dict[str, Any]:
    if payload is None:
        return {"status": "not_applicable"}
    allowed = set(default_available_action_ids())
    errors: list[str] = []
    action_id = payload.get("action_id")
    say = payload.get("say")
    if not isinstance(action_id, str) or not action_id.strip():
        errors.append("action_id_must_be_non_empty_string")
    elif action_id not in allowed:
        errors.append(f"action_id_not_allowed:{action_id}")
    if not isinstance(say, str) or not say.strip():
        errors.append("say_must_be_non_empty_string")
    if "slots" in payload and not isinstance(payload.get("slots"), dict):
        errors.append("slots_must_be_object_when_present")
    if "uncertainty" in payload and not isinstance(payload.get("uncertainty"), str):
        errors.append("uncertainty_must_be_string_when_present")
    confidence = payload.get("confidence")
    if confidence is not None and (not isinstance(confidence, (int, float)) or isinstance(confidence, bool)):
        errors.append("confidence_must_be_number_when_present")
    extra = sorted(set(payload) - {"action_id", "say", "slots", "uncertainty", "confidence"})
    if extra:
        errors.append(f"unsupported_fields:{extra}")
    if parse_errors:
        errors.extend(parse_errors)

    adapted = {
        "action_id": action_id,
        "slots": payload.get("slots") if isinstance(payload.get("slots"), dict) else {},
        "memory_updates": {},
        "uncertainty": payload.get("uncertainty") if isinstance(payload.get("uncertainty"), str) else "",
        "say": say if isinstance(say, str) else "",
    }
    if confidence is not None:
        adapted["confidence"] = confidence
    semantic = verify_live_action_output(
        adapted,
        memory=case.get("memory") or {},
        approved_fact_ids=FACT_IDS,
        approved_fact_summaries=FACT_SUMMARIES,
    ).to_dict()
    return verifier_dict(
        semantic.get("status") or "pass",
        errors=errors + list(semantic.get("errors") or []),
        replan_reasons=list(semantic.get("replan_reasons") or []),
        hard_block_reasons=list(semantic.get("hard_block_reasons") or []),
        warnings=list(semantic.get("warnings") or []),
    )


def verify_minimal_live_action(payload: dict[str, Any] | None, parse_errors: list[str], case: dict[str, Any]) -> dict[str, Any]:
    if payload is None:
        return {"status": "not_applicable"}
    semantic = verify_live_action_output(
        payload,
        memory=case.get("memory") or {},
        approved_fact_ids=FACT_IDS,
        approved_fact_summaries=FACT_SUMMARIES,
    ).to_dict()
    if parse_errors:
        return verifier_dict(
            semantic.get("status") or "invalid",
            errors=list(semantic.get("errors") or []) + parse_errors,
            replan_reasons=list(semantic.get("replan_reasons") or []),
            hard_block_reasons=list(semantic.get("hard_block_reasons") or []),
            warnings=list(semantic.get("warnings") or []),
        )
    return semantic


def verify_output(mode: str, raw_output: str, case: dict[str, Any]) -> tuple[dict[str, Any] | None, list[str], dict[str, Any]]:
    payload, parse_errors = parse_live_action_json(raw_output)
    if mode == "ultra_minimal_action_id_only":
        verifier = verify_action_only(payload, parse_errors)
    elif mode == "constrained_action_selector_prompt":
        verifier = verify_constrained_selector(payload, parse_errors, case)
    else:
        verifier = verify_minimal_live_action(payload, parse_errors, case)
    return payload, parse_errors, verifier


def latency_values(metrics: dict[str, Any]) -> tuple[float, float, float]:
    p50 = metrics.get("total_generation_latency_p50_s")
    p90 = metrics.get("total_generation_latency_p90_s")
    p99 = metrics.get("total_generation_latency_p99_s")
    return (
        float(p50) if isinstance(p50, (int, float)) else math.inf,
        float(p90) if isinstance(p90, (int, float)) else math.inf,
        float(p99) if isinstance(p99, (int, float)) else math.inf,
    )


def augment_summary(summary: dict[str, Any], rows: list[dict[str, Any]], *, model_name: str, mode: str, model_present: bool, model_loaded: bool, pull_attempted: bool, cold_latency_s: float | None) -> dict[str, Any]:
    verifier_results = [row.get("verifier") or {} for row in rows]
    hard_block_count = sum(1 for item in verifier_results if item.get("hard_block") is True)
    fake_side_effect_count = sum(1 for item in verifier_results if "fake_side_effect_claim" in (item.get("hard_block_reasons") or []))
    and_or_drift_count = sum(1 for item in verifier_results if any(reason in {"and_or_drift", "or_and_drift"} for reason in (item.get("replan_reasons") or [])))
    voice_writing_drift_count = sum(1 for item in verifier_results if "voice_writing_drift" in (item.get("replan_reasons") or []))
    not_team_team_drift_count = sum(1 for item in verifier_results if "not_team_team_drift" in (item.get("replan_reasons") or []))
    summary.update(
        {
            "model_name": model_name,
            "mode": mode,
            "model_present": model_present,
            "model_loaded": model_loaded,
            "pull_attempted": pull_attempted,
            "cold_latency_s": cold_latency_s,
            "warm_case_count": len(rows),
            "hard_block_count": hard_block_count,
            "fake_side_effect_count": fake_side_effect_count,
            "and_or_drift_count": and_or_drift_count,
            "voice_writing_drift_count": voice_writing_drift_count,
            "not_team_team_drift_count": not_team_team_drift_count,
            "target_met": mode_target_met(summary),
        }
    )
    summary["quality_acceptable"] = quality_acceptable(summary, mode)
    summary["fastest_valid_mode"] = False
    return summary


def quality_acceptable(metrics: dict[str, Any], mode: str) -> bool:
    case_count = int(metrics.get("case_count") or metrics.get("warm_case_count") or 0)
    if case_count <= 0:
        return False
    malformed = int(metrics.get("malformed_output_count") or 0)
    verifier_pass = int(metrics.get("verifier_pass_count") or 0)
    hard_blocks = int(metrics.get("hard_block_count") or 0)
    internal = int(metrics.get("internal_language_count") or 0)
    loop_risk = int(metrics.get("loop_risk_count") or 0)
    drift = int(metrics.get("and_or_drift_count") or 0) + int(metrics.get("voice_writing_drift_count") or 0) + int(metrics.get("not_team_team_drift_count") or 0)
    fake_side_effects = int(metrics.get("fake_side_effect_count") or 0)
    if mode == "ultra_minimal_action_id_only":
        return malformed <= 1 and verifier_pass >= max(1, math.ceil(case_count * 0.90)) and hard_blocks == 0
    return (
        malformed <= 2
        and verifier_pass >= max(1, math.ceil(case_count * 0.60))
        and hard_blocks == 0
        and internal == 0
        and loop_risk == 0
        and drift == 0
        and fake_side_effects == 0
    )


def metric_candidates(result: dict[str, Any]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    metrics_by_model = result.get("metrics_by_model_mode") if isinstance(result.get("metrics_by_model_mode"), dict) else {}
    for model_name, by_mode in metrics_by_model.items():
        if not isinstance(by_mode, dict):
            continue
        for mode, metrics in by_mode.items():
            if not isinstance(metrics, dict):
                continue
            p50, p90, p99 = latency_values(metrics)
            if math.isinf(p50):
                continue
            candidates.append(
                {
                    "model_name": model_name,
                    "mode": mode,
                    "p50": p50,
                    "p90": p90,
                    "p99": p99,
                    "target_met": metrics.get("target_met") is True,
                    "quality_acceptable": metrics.get("quality_acceptable") is True,
                    "verifier_pass_count": metrics.get("verifier_pass_count") or 0,
                    "malformed_output_count": metrics.get("malformed_output_count") or 0,
                }
            )
    return candidates


def select_best_candidates(result: dict[str, Any]) -> None:
    candidates = metric_candidates(result)
    latency_sorted = sorted(candidates, key=lambda item: (item["p50"], item["p90"], item["p99"], item["model_name"], item["mode"]))
    valid_sorted = [item for item in latency_sorted if item["target_met"] and item["quality_acceptable"]]
    quality_sorted = sorted(candidates, key=lambda item: (-int(item["verifier_pass_count"]), int(item["malformed_output_count"]), item["p50"]))
    result["best_latency_model_mode"] = latency_sorted[0] if latency_sorted else None
    result["fastest_valid_model_mode"] = valid_sorted[0] if valid_sorted else None
    result["best_model_mode"] = valid_sorted[0] if valid_sorted else (quality_sorted[0] if quality_sorted else None)
    if valid_sorted:
        model_name = valid_sorted[0]["model_name"]
        mode = valid_sorted[0]["mode"]
        result["metrics_by_model_mode"][model_name][mode]["fastest_valid_mode"] = True
    result["target_met"] = bool(any(item["target_met"] for item in candidates))
    result["quality_acceptable"] = bool(any(item["quality_acceptable"] for item in candidates))


def summarize_model(model_name: str, rows: list[dict[str, Any]], model_present: bool, model_loaded: bool, pull_attempted: bool, pull_result: dict[str, Any] | None) -> dict[str, Any]:
    model_metrics = [row for row in rows if row.get("model_name") == model_name]
    return {
        "model_name": model_name,
        "model_present": model_present,
        "model_loaded": model_loaded,
        "pull_attempted": pull_attempted,
        "pull_status": pull_result.get("status") if isinstance(pull_result, dict) else None,
        "mode_count": len({row.get("mode") for row in model_metrics}),
        "generation_call_count": len(model_metrics),
    }


def run_benchmark(limit: int | None, include_reference: bool) -> dict[str, Any]:
    result = base_result(limit, include_reference)
    if not ollama_benchmark_enabled():
        result["not_run_reason"] = "ENABLE_LOCAL_LLM_BRAIN_EXPERIMENT=1, LOCAL_LLM_ENABLED=true, and LOCAL_OLLAMA_BENCHMARK_ENABLED=1 are required before localhost Ollama generation."
        return result

    cases = benchmark_cases()
    if limit is not None:
        cases = cases[: max(0, limit)]
    tags_payload, tags_error = http_json("/api/tags", timeout_s=10.0)
    result["ollama_localhost_api_attempted"] = True
    result["ollama_localhost_api_call_count"] += 1
    result["ollama_localhost_calls_made"] = tags_payload is not None
    if not tags_payload:
        result["status"] = "not_run_ollama_unreachable"
        result["not_run_reason"] = f"localhost Ollama API is not reachable: {tags_error}"
        result["side_effects"] = audit_side_effects()
        return result

    available_models = set(ollama_model_names(tags_payload))
    result["available_ollama_models"] = sorted(available_models)
    all_rows: list[dict[str, Any]] = []
    for model_name in model_list(include_reference):
        model_present = model_name in available_models
        pull_attempted = False
        pull_result: dict[str, Any] | None = None
        pull_error = ""
        if not model_present:
            pull_attempted, pull_result, pull_error = maybe_pull_model(model_name)
            if pull_attempted:
                result["ollama_pull_attempted"] = True
                result["ollama_localhost_api_call_count"] += 1
                tags_payload, _tags_error = http_json("/api/tags", timeout_s=10.0)
                result["ollama_localhost_api_call_count"] += 1
                available_models = set(ollama_model_names(tags_payload))
                model_present = model_name in available_models
        result["model_present_by_model"][model_name] = model_present
        result["pull_attempted_by_model"][model_name] = pull_attempted
        model_rows: list[dict[str, Any]] = []
        model_loaded = False
        if not model_present:
            result["model_loaded_by_model"][model_name] = False
            result["model_summaries"][model_name] = {
                "model_name": model_name,
                "model_present": False,
                "model_loaded": False,
                "pull_attempted": pull_attempted,
                "pull_error": pull_error,
                "not_run_reason": "model_missing_and_pull_not_allowed" if not pull_attempted else "model_missing_after_pull_attempt",
            }
            continue

        request_index = 0
        for case in cases:
            for mode, prompt in modes_for_case(case).items():
                raw_output, response, wall_s = generate_ollama(model_name, prompt, mode=mode)
                result["ollama_localhost_api_call_count"] += 1
                result["ollama_local_model_call_count"] += 1
                result["local_model_calls_made"] = True
                model_loaded = True
                request_phase = "cold" if request_index == 0 else "warm"
                prompt_tokens = response.get("prompt_eval_count")
                generated_tokens = response.get("eval_count")
                if not isinstance(prompt_tokens, int):
                    prompt_tokens = approx_token_count(prompt)
                if not isinstance(generated_tokens, int):
                    generated_tokens = approx_token_count(raw_output)
                _payload, parse_errors, verifier = verify_output(mode, raw_output, case)
                row = {
                    "case_id": case["case_id"],
                    "category": case["category"],
                    "mode": mode,
                    "backend": "ollama_local",
                    "model_name": model_name,
                    "request_phase": request_phase,
                    "prompt_token_count": prompt_tokens,
                    "generated_token_count": generated_tokens,
                    "first_output_latency_s": None,
                    "first_output_latency_note": "stream=false small-model benchmark; first output latency unavailable",
                    "total_generation_latency_s": wall_s,
                    "ollama_total_duration_s": round(float(response.get("total_duration") or 0) / 1_000_000_000, 3) if response.get("total_duration") else None,
                    "ollama_load_duration_s": round(float(response.get("load_duration") or 0) / 1_000_000_000, 3) if response.get("load_duration") else None,
                    "ollama_prompt_eval_duration_s": round(float(response.get("prompt_eval_duration") or 0) / 1_000_000_000, 3) if response.get("prompt_eval_duration") else None,
                    "ollama_eval_duration_s": round(float(response.get("eval_duration") or 0) / 1_000_000_000, 3) if response.get("eval_duration") else None,
                    "malformed_output": bool(parse_errors) or _payload is None,
                    "parse_errors": parse_errors,
                    "verifier": verifier,
                }
                model_rows.append(row)
                all_rows.append(row)
                request_index += 1
        result["model_loaded_by_model"][model_name] = model_loaded
        result["cold_requests_by_model"][model_name] = model_rows[0] if model_rows else {}

        by_mode: dict[str, list[dict[str, Any]]] = {}
        warm_by_mode: dict[str, list[dict[str, Any]]] = {}
        for row in model_rows:
            by_mode.setdefault(str(row["mode"]), []).append(row)
            if row.get("request_phase") == "warm":
                warm_by_mode.setdefault(str(row["mode"]), []).append(row)
        result["all_metrics_by_model_mode"][model_name] = {}
        result["metrics_by_model_mode"][model_name] = {}
        for mode in MODE_NAMES:
            rows_for_mode = by_mode.get(mode, [])
            warm_rows = warm_by_mode.get(mode, [])
            cold_latency_s = next((row.get("total_generation_latency_s") for row in rows_for_mode if row.get("request_phase") == "cold"), None)
            result["all_metrics_by_model_mode"][model_name][mode] = augment_summary(
                summarize_mode(rows_for_mode),
                rows_for_mode,
                model_name=model_name,
                mode=mode,
                model_present=model_present,
                model_loaded=model_loaded,
                pull_attempted=pull_attempted,
                cold_latency_s=cold_latency_s if isinstance(cold_latency_s, (int, float)) else None,
            )
            summary_rows = warm_rows or rows_for_mode
            result["metrics_by_model_mode"][model_name][mode] = augment_summary(
                summarize_mode(summary_rows),
                summary_rows,
                model_name=model_name,
                mode=mode,
                model_present=model_present,
                model_loaded=model_loaded,
                pull_attempted=pull_attempted,
                cold_latency_s=cold_latency_s if isinstance(cold_latency_s, (int, float)) else None,
            )
        result["model_summaries"][model_name] = summarize_model(model_name, model_rows, model_present, model_loaded, pull_attempted, pull_result)

    result["rows"] = all_rows
    result["benchmark_run"] = bool(all_rows)
    result["status"] = "pass" if all_rows else "not_run_no_models_benchmarked"
    if not all_rows:
        result["not_run_reason"] = "No requested model was present locally, and no model was pulled."
    select_best_candidates(result)
    result["side_effects"] = audit_side_effects(
        local_model_calls_made=result["local_model_calls_made"],
        ollama_localhost_calls_made=result["ollama_localhost_calls_made"],
        ollama_pull_attempted=result["ollama_pull_attempted"],
    )
    return result


def close_to_latency_target(metrics: dict[str, Any]) -> bool:
    p50, p90, _p99 = latency_values(metrics)
    return p50 <= 3.0 and p90 <= 3.5


def build_decision(benchmark: dict[str, Any]) -> dict[str, Any]:
    candidates = metric_candidates(benchmark)
    valid_candidates = [item for item in candidates if item["target_met"] and item["quality_acceptable"]]
    latency_only = [item for item in candidates if item["target_met"] and not item["quality_acceptable"]]
    ultra_latency = [item for item in candidates if item["mode"] == "ultra_minimal_action_id_only" and item["target_met"]]
    say_valid = [
        item
        for item in candidates
        if item["mode"] in {"constrained_action_selector_prompt", "minimal_live_action_prompt"} and item["target_met"] and item["quality_acceptable"]
    ]
    no_model_meets_latency = not any(item["target_met"] for item in candidates)
    qwen15_close = False
    qwen15_metrics = ((benchmark.get("metrics_by_model_mode") or {}).get("qwen2.5:1.5b") or {})
    if isinstance(qwen15_metrics, dict):
        qwen15_close = any(close_to_latency_target(metrics) for metrics in qwen15_metrics.values() if isinstance(metrics, dict))
    fastest = benchmark.get("best_latency_model_mode") if isinstance(benchmark.get("best_latency_model_mode"), dict) else None
    fastest_model = str((fastest or {}).get("model_name") or "")
    fastest_weak_gemma = fastest_model in {"gemma3:270m", "gemma3:1b"} and not bool((fastest or {}).get("quality_acceptable"))
    strongest = benchmark.get("best_model_mode") if isinstance(benchmark.get("best_model_mode"), dict) else None
    strongest_model = str((strongest or {}).get("model_name") or "")
    strongest_smollm_or_llama = strongest_model.startswith("smollm2") or strongest_model.startswith("llama3.2")

    if valid_candidates:
        recommendation_id = "offline_quality_benchmark_next"
        recommendation = "At least one small Ollama model/mode met warm latency and benchmark verifier quality. Run an offline quality benchmark next; live wiring stays false."
    elif ultra_latency and not say_valid:
        recommendation_id = "two_head_split_action_id_selector"
        recommendation = "Ultra-minimal action_id-only output met latency while say modes did not prove quality. Test a two-head split: small local model selects action_id, deterministic renderer or separate wording model creates speech."
    elif latency_only:
        recommendation_id = "latency_met_quality_weak_finetune_or_action_only"
        recommendation = "At least one model/mode met latency but quality is weak. Prefer constrained action-only output or task-specific fine-tuning/distillation before any live use."
    elif no_model_meets_latency:
        recommendation_id = "non_llm_classifier_or_backend_optimization"
        recommendation = "No tested small model/mode met the live latency target. Move to a non-LLM classifier/action selector or further backend optimization."
    else:
        recommendation_id = "rerun_after_blocker"
        recommendation = "Benchmark evidence is incomplete. Fix the local blocker and rerun before choosing a model path."

    recommended_actions: list[str] = [recommendation]
    if qwen15_close:
        recommended_actions.append("qwen2.5:1.5b is close enough to justify Qwen 7B teacher -> Qwen 1.5B distillation as a follow-up.")
    if fastest_weak_gemma:
        recommended_actions.append("Gemma was fastest but weak; only consider a task-specific fine-tune if the JSON output format appears learnable.")
    if strongest_smollm_or_llama:
        recommended_actions.append("smollm2 or llama3.2 was the strongest observed model family; run a follow-up quality benchmark on that model.")
    if no_model_meets_latency:
        recommended_actions.append("Add a deterministic or classical action selector baseline because the live 2-3 second budget remains unproven for local LLMs.")

    return {
        "experiment_id": DECISION_ID,
        "generated_at": utc_now(),
        "status": "pass" if benchmark.get("benchmark_run") is True else "not_run",
        "inputs": {
            "benchmark_result": str(BENCHMARK_RESULT_PATH.relative_to(ROOT)).replace("\\", "/"),
            "registry": str(REGISTRY_PATH.relative_to(ROOT)).replace("\\", "/"),
            "baseline_reference": "research/experiments/generated/LOCAL-QWEN-OLLAMA-LIVE-ACTION-BENCHMARK-001/result.json",
        },
        "benchmark_run": benchmark.get("benchmark_run") is True,
        "benchmark_status": benchmark.get("status"),
        "target_met": benchmark.get("target_met") is True,
        "quality_acceptable": benchmark.get("quality_acceptable") is True,
        "best_model_mode": benchmark.get("best_model_mode"),
        "best_latency_model_mode": benchmark.get("best_latency_model_mode"),
        "fastest_valid_model_mode": benchmark.get("fastest_valid_model_mode"),
        "recommendation_id": recommendation_id,
        "recommendation": recommendation,
        "recommended_actions": recommended_actions,
        "smaller_model_path_remains_viable": bool(valid_candidates or latency_only or qwen15_close or ultra_latency),
        "distillation_or_finetuning_recommended": bool(latency_only or qwen15_close or fastest_weak_gemma),
        "non_llm_classifier_recommended": bool(no_model_meets_latency),
        "two_head_split_recommended": bool(ultra_latency and not say_valid),
        "qwen2_5_1_5b_close": qwen15_close,
        "gemma_fastest_but_weak": fastest_weak_gemma,
        "smollm2_or_llama3_2_strongest": strongest_smollm_or_llama,
        "quality_benchmark_required_before_live_wiring": True,
        "live_wiring_allowed": False,
        "adapter_live_ready": False,
        "runtime_behavior_changed": False,
        "response_text_changed": False,
        "training_rerun": False,
        "provider_calls_made": False,
        "openai_api_calls_made": False,
        "live_tts_calls_made": False,
        "provider_side_effects_made": False,
        "actual_pruning_performed": False,
        "benchmark_local_model_calls_made": benchmark.get("local_model_calls_made") is True,
        "decision_local_model_calls_made": False,
        "ollama_localhost_calls_made": benchmark.get("ollama_localhost_calls_made") is True,
        "ollama_localhost_api_call_count": benchmark.get("ollama_localhost_api_call_count"),
        "ollama_pull_attempted": benchmark.get("ollama_pull_attempted") is True,
        "side_effects": audit_side_effects(ollama_localhost_calls_made=False),
    }


def write_benchmark_report(result: dict[str, Any]) -> None:
    lines = [
        f"# {BENCHMARK_ID}",
        "",
        f"- status: {result['status']}",
        f"- benchmark_run: {str(result['benchmark_run']).lower()}",
        f"- not_run_reason: {result.get('not_run_reason') or 'none'}",
        f"- models_requested: {', '.join(result.get('models_requested') or [])}",
        f"- local_model_calls_made: {str(result['local_model_calls_made']).lower()}",
        f"- ollama_localhost_calls_made: {str(result['ollama_localhost_calls_made']).lower()}",
        f"- ollama_local_model_call_count: {result['ollama_local_model_call_count']}",
        f"- ollama_pull_attempted: {str(result['ollama_pull_attempted']).lower()}",
        f"- target_met: {str(result['target_met']).lower()}",
        f"- quality_acceptable: {str(result['quality_acceptable']).lower()}",
        f"- best_model_mode: `{json.dumps(result.get('best_model_mode'), ensure_ascii=False)}`",
        f"- provider_calls_made: {str(result['provider_calls_made']).lower()}",
        f"- openai_api_calls_made: {str(result['openai_api_calls_made']).lower()}",
        f"- live_tts_calls_made: {str(result['live_tts_calls_made']).lower()}",
        "",
        "## Model Presence",
        "",
        json.dumps(result.get("model_present_by_model") or {}, indent=2, ensure_ascii=False),
        "",
        "## Warm Metrics By Model And Mode",
        "",
        json.dumps(result.get("metrics_by_model_mode") or {}, indent=2, ensure_ascii=False),
        "",
        "## Cold Requests By Model",
        "",
        json.dumps(result.get("cold_requests_by_model") or {}, indent=2, ensure_ascii=False),
    ]
    write_text(BENCHMARK_REPORT_PATH, "\n".join(lines))


def write_decision_report(decision: dict[str, Any]) -> None:
    lines = [
        f"# {DECISION_ID}",
        "",
        f"- status: {decision['status']}",
        f"- benchmark_run: {str(decision['benchmark_run']).lower()}",
        f"- target_met: {str(decision['target_met']).lower()}",
        f"- quality_acceptable: {str(decision['quality_acceptable']).lower()}",
        f"- recommendation_id: `{decision['recommendation_id']}`",
        f"- recommendation: {decision['recommendation']}",
        f"- smaller_model_path_remains_viable: {str(decision['smaller_model_path_remains_viable']).lower()}",
        f"- distillation_or_finetuning_recommended: {str(decision['distillation_or_finetuning_recommended']).lower()}",
        f"- non_llm_classifier_recommended: {str(decision['non_llm_classifier_recommended']).lower()}",
        f"- two_head_split_recommended: {str(decision['two_head_split_recommended']).lower()}",
        f"- live_wiring_allowed: {str(decision['live_wiring_allowed']).lower()}",
        f"- adapter_live_ready: {str(decision['adapter_live_ready']).lower()}",
        "",
        "## Best Model Mode",
        "",
        json.dumps(decision.get("best_model_mode"), indent=2, ensure_ascii=False),
        "",
        "## Recommended Actions",
        "",
        json.dumps(decision.get("recommended_actions") or [], indent=2, ensure_ascii=False),
    ]
    write_text(DECISION_REPORT_PATH, "\n".join(lines))


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    result = run_benchmark(args.limit, args.include_7b_reference)
    write_json(BENCHMARK_RESULT_PATH, result)
    write_benchmark_report(result)
    decision = build_decision(result)
    write_json(DECISION_RESULT_PATH, decision)
    write_decision_report(decision)
    print(
        json.dumps(
            {
                "status": result["status"],
                "benchmark_run": result["benchmark_run"],
                "models_tested": [model for model, loaded in result.get("model_loaded_by_model", {}).items() if loaded],
                "best_model_mode": result.get("best_model_mode"),
                "recommendation_id": decision.get("recommendation_id"),
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
