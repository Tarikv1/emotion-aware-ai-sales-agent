#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
import json
import os
import sys
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.llm_brain.conversation_brain_prompts import render_conversation_brain_prompt  # noqa: E402
from runtime.llm_brain.conversation_brain_schema import COMPACT_PLANNER_SCHEMA_MODE  # noqa: E402
from runtime.llm_brain.live_action_prompt import (  # noqa: E402
    default_available_action_ids,
    render_live_action_prompt,
)
from runtime.llm_brain.live_action_verifier import (  # noqa: E402
    parse_live_action_json,
    signature,
    verify_live_action_output,
)
from runtime.llm_brain.local_conversation_brain import (  # noqa: E402
    EXPERIMENT_ENV_VAR,
    LOCAL_LLM_ENABLED_ENV_VAR,
    local_conversation_brain_config_from_env,
    local_llm_enabled,
    local_llm_experiment_enabled,
)
from runtime.llm_brain.local_transformers_runner import (  # noqa: E402
    dependency_status,
    ensure_model_available,
    generate_text,
    load_local_transformers_model,
)
from scripts.local_qwen_audit_utils_001 import (  # noqa: E402
    GENERATED_DIR,
    audit_side_effects,
    tracked_model_or_adapter_files,
)


EXPERIMENT_ID = "LOCAL-QWEN-LIVE-ACTION-LATENCY-BENCHMARK-001"
OUT_DIR = GENERATED_DIR / EXPERIMENT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"
DECISION_ID = "LOCAL-QWEN-LIVE-ACTION-LATENCY-DECISION-001"
DECISION_OUT_DIR = GENERATED_DIR / DECISION_ID
DECISION_RESULT_PATH = DECISION_OUT_DIR / "result.json"
DECISION_REPORT_PATH = DECISION_OUT_DIR / "report.md"
TARGETS_SECONDS = {"p50": 2.0, "p90": 3.0, "p99": 4.0}
ENV_DETAIL_VARS = (
    EXPERIMENT_ENV_VAR,
    LOCAL_LLM_ENABLED_ENV_VAR,
    "LOCAL_LLM_MODEL_ID",
    "LOCAL_LLM_MODEL_PATH",
    "LOCAL_LLM_CACHE_DIR",
    "LOCAL_LLM_QUANTIZATION",
    "LOCAL_LLM_DEVICE",
    "LOCAL_LLM_ALLOW_MODEL_DOWNLOAD",
)
FACT_SUMMARIES = {
    "public_plan_names": "ChatGPT public plan categories include Free, Plus, Pro, Business, and Enterprise.",
    "individual_plans": "Free, Plus, and Pro are individual ChatGPT plan categories.",
    "team_plans": "Business is the self-serve team workspace plan; Enterprise is for larger organizations.",
    "self_serve_path": "Individual plan changes start from the official ChatGPT plans page or profile upgrade flow.",
    "price_caution": "Current prices can change, so the official ChatGPT plans page is authoritative.",
}
FACT_IDS = list(FACT_SUMMARIES)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def env_enabled() -> bool:
    return local_llm_experiment_enabled() and local_llm_enabled()


def env_gate_report() -> dict[str, Any]:
    report: dict[str, Any] = {
        EXPERIMENT_ENV_VAR: local_llm_experiment_enabled(),
        LOCAL_LLM_ENABLED_ENV_VAR: local_llm_enabled(),
    }
    for name in ENV_DETAIL_VARS:
        if name not in report:
            report[name] = os.getenv(name, "")
    return report


def benchmark_cases() -> list[dict[str, Any]]:
    base_memory = {
        "last_action_id": "",
        "last_action_slot_signature": "",
        "last_agent_question": "",
        "last_response_signature": "",
        "answered_topics": [],
        "asked_topic_counts": {},
        "known_slots": {},
        "buyer_corrections": [],
        "buyer_said_already_told_you": False,
        "terminal_acceptance_seen": False,
        "price_answered": False,
        "recommendation_given": "",
        "current_decision_frame": "",
        "last_objection_handled": "",
        "new_buyer_info_since_last_action": True,
    }

    def case(case_id: str, buyer: str, **overrides: Any) -> dict[str, Any]:
        memory = {**base_memory, **overrides.pop("memory", {})}
        memory["current_buyer_utterance"] = buyer
        return {"case_id": case_id, "buyer": buyer, "memory": memory, **overrides}

    return [
        case("direct_price_001", "How much is Plus?"),
        case("direct_price_002", "What does Pro cost now?"),
        case("terminal_thanks_001", "Ok, I will check that, thanks.", memory={"terminal_acceptance_seen": True}),
        case("terminal_thanks_002", "Sounds good, thanks."),
        case("current_tool_and_001", "I use ChatGPT and Claude."),
        case("current_tool_or_001", "I use ChatGPT or maybe Claude."),
        case("not_team_001", "I am by myself, not a team.", memory={"known_slots": {"team_state": False}}),
        case("not_team_002", "This is personal use, no team.", memory={"known_slots": {"team_state": False}}),
        case("coding_voice_001", "I use it for coding workflow and voice."),
        case("coding_voice_002", "Mostly coding, but I also want voice."),
        case("plan_explanation_001", "What are the plans actually?"),
        case("plan_explanation_002", "Is this about models or subscriptions?"),
        case("price_objection_001", "Plus sounds expensive for what it is."),
        case("price_objection_002", "I do not want to overpay if I barely use it."),
        case("competitor_objection_001", "Why not just use Claude instead?"),
        case("competitor_objection_002", "I already pay for another AI tool."),
        case("unsupported_side_effect_001", "Can you just buy Plus for me?"),
        case("unsupported_side_effect_002", "Send the upgrade link to my email and schedule a reminder."),
        case(
            "repeated_question_risk_001",
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
        case(
            "repeated_question_risk_002",
            "I said it is just for me.",
            memory={
                "last_action_id": "ask_adoption_state",
                "known_slots": {"team_state": False},
                "buyer_corrections": ["just for me"],
                "buyer_said_already_told_you": True,
                "new_buyer_info_since_last_action": False,
            },
        ),
        case("asr_claude_cloud_001", "I use cloud for this maybe, or Claude, not sure."),
        case("asr_claude_cloud_002", "Did you say cloud or Claude?"),
        case("plan_change_001", "Can I start lower and upgrade later?"),
        case("signup_path_001", "Where do I sign up?"),
    ]


def build_context(case: dict[str, Any]) -> dict[str, Any]:
    return {
        "normalized_transcript": case["buyer"].casefold(),
        "prior_state": case.get("memory") or {},
        "approved_campaign_fact_ids": FACT_IDS,
        "approved_campaign_fact_summaries": FACT_SUMMARIES,
        "last_agent_question": (case.get("memory") or {}).get("last_agent_question") or "",
        "campaign_id": "synthetic_public_plan_fit",
    }


def compact_planner_prompt(case: dict[str, Any]) -> str:
    return render_conversation_brain_prompt(build_context(case), schema_mode=COMPACT_PLANNER_SCHEMA_MODE)


def live_action_prompt(case: dict[str, Any], *, with_replan_context: bool = False) -> str:
    replan_instruction = None
    if with_replan_context:
        replan_instruction = "The last response already asked this. Use the known answer and move forward."
    return render_live_action_prompt(
        sanitized_buyer_utterance=case["buyer"],
        last_agent_response=(case.get("memory") or {}).get("last_response_signature") or "",
        memory_ledger_summary=case.get("memory") or {},
        available_action_ids=default_available_action_ids(),
        approved_campaign_fact_ids=FACT_IDS,
        approved_campaign_fact_summaries=FACT_SUMMARIES,
        replan_instruction=replan_instruction,
    )


def modes_for_case(case: dict[str, Any]) -> dict[str, str]:
    return {
        "current_compact_planner_prompt": compact_planner_prompt(case),
        "minimal_live_action_prompt": live_action_prompt(case),
        "minimal_live_action_prompt_with_replan_context": live_action_prompt(case, with_replan_context=True),
    }


def qwen_chat_prompt(tokenizer: Any, prompt: str) -> str:
    messages = [{"role": "user", "content": prompt + "\n\nReturn exactly one JSON object and no markdown."}]
    if hasattr(tokenizer, "apply_chat_template"):
        try:
            return str(tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True))
        except Exception:
            return prompt
    return prompt


def percentile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, round((len(ordered) - 1) * q)))
    return round(ordered[index], 3)


def avg(values: list[float]) -> float | None:
    if not values:
        return None
    return round(sum(values) / len(values), 3)


def summarize_mode(rows: list[dict[str, Any]]) -> dict[str, Any]:
    totals = [float(row["total_generation_latency_s"]) for row in rows if isinstance(row.get("total_generation_latency_s"), (int, float))]
    firsts = [float(row["first_output_latency_s"]) for row in rows if isinstance(row.get("first_output_latency_s"), (int, float))]
    generated_tokens = [int(row["generated_token_count"]) for row in rows if isinstance(row.get("generated_token_count"), int)]
    prompt_tokens = [int(row["prompt_token_count"]) for row in rows if isinstance(row.get("prompt_token_count"), int)]
    verifier_results = [row.get("verifier") or {} for row in rows]
    return {
        "case_count": len(rows),
        "prompt_token_count_total": sum(prompt_tokens) if prompt_tokens else None,
        "prompt_token_count_avg": round(sum(prompt_tokens) / len(prompt_tokens), 2) if prompt_tokens else None,
        "generated_token_count_total": sum(generated_tokens) if generated_tokens else None,
        "generated_token_count_avg": round(sum(generated_tokens) / len(generated_tokens), 2) if generated_tokens else None,
        "first_output_latency_avg_s": avg(firsts),
        "first_output_latency_p50_s": percentile(firsts, 0.50),
        "first_output_latency_p90_s": percentile(firsts, 0.90),
        "first_output_latency_p99_s": percentile(firsts, 0.99),
        "total_generation_latency_avg_s": avg(totals),
        "total_generation_latency_p50_s": percentile(totals, 0.50),
        "total_generation_latency_p90_s": percentile(totals, 0.90),
        "total_generation_latency_p99_s": percentile(totals, 0.99),
        "malformed_output_count": sum(1 for row in rows if row.get("malformed_output") is True),
        "verifier_pass_count": sum(1 for item in verifier_results if item.get("status") == "pass"),
        "replan_required_count": sum(1 for item in verifier_results if item.get("replan_required") is True),
        "internal_language_count": sum(1 for item in verifier_results if "internal_language_in_say" in (item.get("replan_reasons") or [])),
        "loop_risk_count": sum(
            1
            for item in verifier_results
            if any(
                "repeat" in str(reason) or "already" in str(reason) or "known" in str(reason)
                for reason in (item.get("replan_reasons") or [])
            )
        ),
    }


def fastest_mode(metrics_by_mode: dict[str, Any]) -> str:
    candidates: list[tuple[float, str]] = []
    for mode, metrics in metrics_by_mode.items():
        if not isinstance(metrics, dict):
            continue
        value = metrics.get("total_generation_latency_p50_s")
        if isinstance(value, (int, float)):
            candidates.append((float(value), str(mode)))
    if not candidates:
        return ""
    return sorted(candidates)[0][1]


def latency_classification(result: dict[str, Any]) -> str:
    metrics_by_mode = result.get("metrics_by_mode") if isinstance(result.get("metrics_by_mode"), dict) else {}
    live_metrics = metrics_by_mode.get("minimal_live_action_prompt") if isinstance(metrics_by_mode.get("minimal_live_action_prompt"), dict) else {}
    p50 = live_metrics.get("total_generation_latency_p50_s")
    p90 = live_metrics.get("total_generation_latency_p90_s")
    if result.get("target_met") is True:
        return "target_met"
    if isinstance(p50, (int, float)) and isinstance(p90, (int, float)) and p50 <= 4.0 and p90 <= 6.0:
        return "close_but_misses_target"
    if isinstance(p50, (int, float)) and isinstance(p90, (int, float)):
        return "far_above_target"
    return "not_measured"


def bottleneck_notes(result: dict[str, Any]) -> list[str]:
    metrics_by_mode = result.get("metrics_by_mode") if isinstance(result.get("metrics_by_mode"), dict) else {}
    live_metrics = metrics_by_mode.get("minimal_live_action_prompt") if isinstance(metrics_by_mode.get("minimal_live_action_prompt"), dict) else {}
    notes: list[str] = []
    first_p50 = live_metrics.get("first_output_latency_p50_s")
    first_p90 = live_metrics.get("first_output_latency_p90_s")
    total_p50 = live_metrics.get("total_generation_latency_p50_s")
    total_p90 = live_metrics.get("total_generation_latency_p90_s")
    if isinstance(first_p50, (int, float)) and first_p50 > TARGETS_SECONDS["p50"]:
        notes.append("minimal live-action first-token p50 is already above the 2s target")
    if isinstance(first_p90, (int, float)) and first_p90 > TARGETS_SECONDS["p90"]:
        notes.append("minimal live-action first-token p90 is above the 3s target")
    if isinstance(total_p50, (int, float)) and total_p50 > TARGETS_SECONDS["p50"]:
        notes.append("minimal live-action total-generation p50 misses the 2s target")
    if isinstance(total_p90, (int, float)) and total_p90 > TARGETS_SECONDS["p90"]:
        notes.append("minimal live-action total-generation p90 misses the 3s target")
    if live_metrics.get("malformed_output_count"):
        notes.append("minimal live-action still has malformed output cases")
    if live_metrics.get("verifier_pass_count") == 0:
        notes.append("minimal live-action verifier pass count is zero, so latency alone cannot justify live wiring")
    return notes or ["no measured bottleneck; benchmark did not produce latency rows"]


def base_result(limit: int | None) -> dict[str, Any]:
    cases = benchmark_cases()
    if limit is not None:
        cases = cases[:limit]
    return {
        "experiment_id": EXPERIMENT_ID,
        "generated_at": utc_now(),
        "status": "not_run",
        "benchmark_run": False,
        "not_run_reason": "",
        "env_gates": env_gate_report(),
        "case_count": len(cases),
        "mode_names": [
            "current_compact_planner_prompt",
            "minimal_live_action_prompt",
            "minimal_live_action_prompt_with_replan_context",
        ],
        "latency_targets_seconds": TARGETS_SECONDS,
        "target_met": None,
        "metrics_by_mode": {},
        "rows": [],
        "local_model_calls_made": False,
        "local_model_call_count": 0,
        "model_loaded": False,
        "adapter_loaded": False,
        "adapter_source": "none",
        "model_load_status": {},
        "model_download_attempted": False,
        "model_redownloaded": False,
        "model_weights_committed": bool(tracked_model_or_adapter_files()),
        "adapter_weights_committed": False,
        "training_rerun": False,
        "provider_calls_made": False,
        "openai_api_calls_made": False,
        "live_tts_calls_made": False,
        "provider_side_effects_made": False,
        "runtime_behavior_changed": False,
        "response_text_changed": False,
        "adapter_live_ready": False,
        "live_wiring_allowed": False,
        "quality_gate_passed": False,
        "model_or_adapter_weights_committed": bool(tracked_model_or_adapter_files()),
        "fastest_mode": "",
        "latency_classification": "not_measured",
        "bottleneck_notes": [],
        "side_effects": audit_side_effects(),
    }


def write_evidence(result: dict[str, Any]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    lines = [
        f"# {EXPERIMENT_ID}",
        "",
        f"- status: {result.get('status')}",
        f"- benchmark_run: {str(result.get('benchmark_run')).lower()}",
        f"- not_run_reason: {result.get('not_run_reason') or 'none'}",
        f"- model_loaded: {str(result.get('model_loaded')).lower()}",
        f"- adapter_loaded: {str(result.get('adapter_loaded')).lower()}",
        f"- local_model_calls_made: {str(result.get('local_model_calls_made')).lower()}",
        f"- local_model_call_count: {result.get('local_model_call_count')}",
        f"- provider_calls_made: {str(result.get('provider_calls_made')).lower()}",
        f"- openai_api_calls_made: {str(result.get('openai_api_calls_made')).lower()}",
        f"- live_tts_calls_made: {str(result.get('live_tts_calls_made')).lower()}",
        f"- model_redownloaded: {str(result.get('model_redownloaded')).lower()}",
        f"- model_weights_committed: {str(result.get('model_weights_committed')).lower()}",
        f"- runtime_behavior_changed: {str(result.get('runtime_behavior_changed')).lower()}",
        f"- response_text_changed: {str(result.get('response_text_changed')).lower()}",
        f"- target_met: {result.get('target_met')}",
        f"- fastest_mode: {result.get('fastest_mode') or 'none'}",
        "",
        "## Env Gates",
        "",
        json.dumps(result.get("env_gates") or {}, indent=2, ensure_ascii=False),
        "",
        "## Metrics By Mode",
        "",
        json.dumps(result.get("metrics_by_mode") or {}, indent=2, ensure_ascii=False),
        "",
        "## Bottleneck Notes",
        "",
        json.dumps(result.get("bottleneck_notes") or [], indent=2, ensure_ascii=False),
    ]
    REPORT_PATH.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def build_latency_decision(benchmark: dict[str, Any]) -> dict[str, Any]:
    metrics_by_mode = benchmark.get("metrics_by_mode") if isinstance(benchmark.get("metrics_by_mode"), dict) else {}
    live_metrics = metrics_by_mode.get("minimal_live_action_prompt") if isinstance(metrics_by_mode.get("minimal_live_action_prompt"), dict) else {}
    classification = latency_classification(benchmark)
    if classification == "target_met":
        recommendation_id = "next_offline_quality_benchmark_for_live_action_contract"
        recommendation = "Run the next offline quality benchmark for the live-action contract before any live runtime wiring."
        recommended_actions = [
            "Run a separate offline quality benchmark against the live-action contract.",
            "Keep live wiring disabled until latency and quality both pass.",
        ]
    elif classification == "close_but_misses_target":
        recommendation_id = "backend_optimization_before_quality_benchmark"
        recommendation = "Do backend optimization before quality benchmarking or live wiring."
        recommended_actions = [
            "Test a persistent local inference process.",
            "Test llama.cpp/GGUF or another faster backend.",
            "Lower max output tokens.",
            "Use a stricter stop after the first JSON object.",
            "Reduce static prompt/context tokens and evaluate prompt caching.",
        ]
    elif classification == "far_above_target":
        recommendation_id = "smaller_model_or_constrained_selector_before_live_use"
        recommendation = "Treat Qwen 7B as an offline teacher, not the live model; test a smaller/distilled model or constrained action selector."
        recommended_actions = [
            "Test a smaller model or distillation path.",
            "Prototype a constrained classifier/action selector for live use.",
            "Keep Qwen 7B for offline teacher/evaluation work unless a faster backend changes the latency result.",
        ]
    else:
        recommendation_id = "rerun_benchmark_after_blocker"
        recommendation = "Resolve the benchmark blocker and rerun before making a live-action latency decision."
        recommended_actions = ["Rerun the benchmark with the required env gates and local model path."]

    return {
        "experiment_id": DECISION_ID,
        "generated_at": utc_now(),
        "status": "pass" if benchmark.get("benchmark_run") is True else "blocked",
        "inputs": {"benchmark_result": str(RESULT_PATH.relative_to(ROOT)).replace("\\", "/")},
        "benchmark_run": benchmark.get("benchmark_run"),
        "benchmark_status": benchmark.get("status"),
        "not_run_reason": benchmark.get("not_run_reason") or "",
        "target_met": benchmark.get("target_met"),
        "latency_targets_seconds": benchmark.get("latency_targets_seconds"),
        "minimal_live_action_metrics": live_metrics,
        "fastest_mode": benchmark.get("fastest_mode") or fastest_mode(metrics_by_mode),
        "latency_classification": classification,
        "recommendation_id": recommendation_id,
        "recommendation": recommendation,
        "recommended_actions": recommended_actions,
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
        "model_redownloaded": benchmark.get("model_redownloaded") is True,
        "model_or_adapter_weights_committed": benchmark.get("model_or_adapter_weights_committed") is True,
        "benchmark_local_model_calls_made": benchmark.get("local_model_calls_made"),
        "decision_local_model_calls_made": False,
        "bottleneck_notes": benchmark.get("bottleneck_notes") or bottleneck_notes(benchmark),
        "side_effects": audit_side_effects(),
    }


def write_decision_evidence(result: dict[str, Any]) -> None:
    DECISION_OUT_DIR.mkdir(parents=True, exist_ok=True)
    DECISION_RESULT_PATH.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    lines = [
        f"# {DECISION_ID}",
        "",
        "## Recommendation",
        "",
        f"- status: {result.get('status')}",
        f"- benchmark_run: {str(result.get('benchmark_run')).lower()}",
        f"- target_met: {result.get('target_met')}",
        f"- fastest_mode: {result.get('fastest_mode') or 'none'}",
        f"- latency_classification: {result.get('latency_classification')}",
        f"- recommendation_id: `{result.get('recommendation_id')}`",
        f"- recommendation: {result.get('recommendation')}",
        f"- live_wiring_allowed: {str(result.get('live_wiring_allowed')).lower()}",
        f"- adapter_live_ready: {str(result.get('adapter_live_ready')).lower()}",
        "",
        "## Minimal Live-Action Metrics",
        "",
        json.dumps(result.get("minimal_live_action_metrics") or {}, indent=2, ensure_ascii=False),
        "",
        "## Recommended Actions",
        "",
        json.dumps(result.get("recommended_actions") or [], indent=2, ensure_ascii=False),
        "",
        "## Bottleneck Notes",
        "",
        json.dumps(result.get("bottleneck_notes") or [], indent=2, ensure_ascii=False),
    ]
    DECISION_REPORT_PATH.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def run_benchmark(limit: int | None) -> dict[str, Any]:
    result = base_result(limit)
    cases = benchmark_cases()
    if limit is not None:
        cases = cases[:limit]
    if not env_enabled():
        result["not_run_reason"] = f"{EXPERIMENT_ENV_VAR}=1 and {LOCAL_LLM_ENABLED_ENV_VAR}=true are required before local Qwen inference."
        return result

    config = local_conversation_brain_config_from_env()
    config = replace(config, max_output_tokens=min(config.max_output_tokens, 120), timeout_ms=min(config.timeout_ms, 20000))
    result["config"] = config.redacted_dict()
    deps = dependency_status(config.quantization_mode)
    result["dependency_status"] = deps
    if not deps["ready"]:
        result["status"] = "not_run_dependency_missing"
        result["not_run_reason"] = f"missing local inference dependencies: {', '.join(deps['missing_required'])}"
        return result
    model_status = ensure_model_available(config, allow_model_download=False)
    result["model_load_status"] = model_status
    result["model_download_attempted"] = bool(model_status.get("download_attempted"))
    result["model_redownloaded"] = bool(model_status.get("download_attempted"))
    if not model_status.get("available"):
        result["status"] = "not_run_model_missing"
        result["not_run_reason"] = f"local model files not found under {config.model_path}; download is not allowed in this benchmark."
        return result

    model, tokenizer, _status = load_local_transformers_model(config, allow_model_download=False)
    result["model_loaded"] = True
    result["model_load_status"] = _status
    result["model_download_attempted"] = bool(_status.get("download_attempted"))
    result["model_redownloaded"] = bool(_status.get("download_attempted"))
    rows: list[dict[str, Any]] = []
    for case in cases:
        for mode_name, prompt in modes_for_case(case).items():
            qwen_prompt = qwen_chat_prompt(tokenizer, prompt)
            started = time.perf_counter()
            raw_output, metrics = generate_text(model, tokenizer, qwen_prompt, config)
            total_s = round(float(metrics.get("total_generation_latency_ms") or 0.0) / 1000.0, 3)
            first_ms = metrics.get("first_output_latency_ms")
            first_s = round(float(first_ms) / 1000.0, 3) if isinstance(first_ms, (int, float)) else None
            payload, parse_errors = parse_live_action_json(raw_output)
            verifier = {"status": "not_applicable"}
            malformed = bool(parse_errors) or payload is None
            if payload is not None and mode_name != "current_compact_planner_prompt":
                verifier = verify_live_action_output(
                    payload,
                    memory=case.get("memory") or {},
                    approved_fact_ids=FACT_IDS,
                    approved_fact_summaries=FACT_SUMMARIES,
                ).to_dict()
            rows.append(
                {
                    "case_id": case["case_id"],
                    "mode": mode_name,
                    "prompt_token_count": metrics.get("prompt_token_count"),
                    "generated_token_count": metrics.get("tokens_generated"),
                    "first_output_latency_s": first_s,
                    "total_generation_latency_s": total_s,
                    "wall_clock_latency_s": round(time.perf_counter() - started, 3),
                    "malformed_output": malformed,
                    "parse_errors": parse_errors,
                    "verifier": verifier,
                }
            )
    by_mode: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        by_mode.setdefault(str(row["mode"]), []).append(row)
    result["status"] = "pass"
    result["benchmark_run"] = True
    result["local_model_calls_made"] = True
    result["local_model_call_count"] = len(rows)
    result["rows"] = rows
    result["metrics_by_mode"] = {mode: summarize_mode(mode_rows) for mode, mode_rows in sorted(by_mode.items())}
    live_metrics = result["metrics_by_mode"].get("minimal_live_action_prompt") or {}
    p50 = live_metrics.get("total_generation_latency_p50_s")
    p90 = live_metrics.get("total_generation_latency_p90_s")
    p99 = live_metrics.get("total_generation_latency_p99_s")
    target_met = (
        isinstance(p50, (int, float))
        and isinstance(p90, (int, float))
        and isinstance(p99, (int, float))
        and p50 <= TARGETS_SECONDS["p50"]
        and p90 <= TARGETS_SECONDS["p90"]
        and p99 <= TARGETS_SECONDS["p99"]
    )
    result["target_met"] = target_met
    result["quality_gate_passed"] = bool(
        target_met
        and live_metrics.get("malformed_output_count") == 0
        and live_metrics.get("internal_language_count") == 0
    )
    result["adapter_live_ready"] = False
    result["live_wiring_allowed"] = False
    result["fastest_mode"] = fastest_mode(result["metrics_by_mode"])
    result["latency_classification"] = latency_classification(result)
    result["bottleneck_notes"] = bottleneck_notes(result)
    return result


def parse_args(argv: list[str]) -> int | None:
    if "--limit" not in argv:
        return None
    index = argv.index("--limit")
    try:
        value = int(argv[index + 1])
    except (IndexError, ValueError):
        raise SystemExit("--limit requires a positive integer")
    return value if value > 0 else None


def main(argv: list[str]) -> int:
    limit = parse_args(argv)
    result = run_benchmark(limit)
    write_evidence(result)
    decision = build_latency_decision(result)
    write_decision_evidence(decision)
    print(
        json.dumps(
            {
                "status": result["status"],
                "benchmark_run": result["benchmark_run"],
                "target_met": result["target_met"],
                "decision": decision["recommendation_id"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
