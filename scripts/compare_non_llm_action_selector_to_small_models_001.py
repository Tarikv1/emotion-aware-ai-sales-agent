from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
GENERATED_DIR = ROOT / "research" / "experiments" / "generated"
EVAL_RESULT_PATH = GENERATED_DIR / "NON-LLM-ACTION-SELECTOR-EVAL-001" / "result.json"
SMALL_BENCHMARK_PATH = GENERATED_DIR / "LOCAL-OLLAMA-SMALL-LIVE-ACTION-MODEL-BENCHMARK-001" / "result.json"
SMALL_DECISION_PATH = GENERATED_DIR / "LOCAL-OLLAMA-SMALL-LIVE-ACTION-MODEL-DECISION-001" / "result.json"
COMPARISON_ID = "NON-LLM-ACTION-SELECTOR-COMPARISON-001"
DECISION_ID = "NON-LLM-ACTION-SELECTOR-DECISION-001"
COMPARISON_DIR = GENERATED_DIR / COMPARISON_ID
DECISION_DIR = GENERATED_DIR / DECISION_ID


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def best_non_llm(eval_result: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    metrics = eval_result.get("baseline_metrics") if isinstance(eval_result.get("baseline_metrics"), dict) else {}
    ranked = sorted(
        metrics.items(),
        key=lambda item: (
            float((item[1].get("test") or {}).get("accuracy") or 0.0),
            -float((item[1].get("latency_ms") or {}).get("p99") or 10**9),
        ),
        reverse=True,
    )
    if not ranked:
        return "none", {}
    return ranked[0]


def build_comparison() -> dict[str, Any]:
    eval_result = read_json(EVAL_RESULT_PATH)
    small_benchmark = read_json(SMALL_BENCHMARK_PATH)
    small_decision = read_json(SMALL_DECISION_PATH)
    baseline_name, non_llm = best_non_llm(eval_result)
    non_llm_latency = non_llm.get("latency_ms") if isinstance(non_llm.get("latency_ms"), dict) else {}
    non_llm_test = non_llm.get("test") if isinstance(non_llm.get("test"), dict) else {}
    small_best = small_decision.get("best_model_mode") if isinstance(small_decision.get("best_model_mode"), dict) else {}

    small_p50_ms = float(small_best.get("p50") or 0.0) * 1000.0
    non_llm_p50_ms = float(non_llm_latency.get("p50") or 0.0)
    speedup = small_p50_ms / non_llm_p50_ms if non_llm_p50_ms > 0 else None
    case_count = int(small_benchmark.get("case_count") or 0)
    verifier_pass_count = int(small_best.get("verifier_pass_count") or 0)
    malformed_count = int(small_best.get("malformed_output_count") or 0)

    return {
        "experiment_id": COMPARISON_ID,
        "generated_at": utc_now(),
        "status": "pass",
        "inputs": {
            "non_llm_eval": "research/experiments/generated/NON-LLM-ACTION-SELECTOR-EVAL-001/result.json",
            "small_model_benchmark": "research/experiments/generated/LOCAL-OLLAMA-SMALL-LIVE-ACTION-MODEL-BENCHMARK-001/result.json",
            "small_model_decision": "research/experiments/generated/LOCAL-OLLAMA-SMALL-LIVE-ACTION-MODEL-DECISION-001/result.json",
        },
        "reran_ollama": False,
        "non_llm_baseline_compared": baseline_name,
        "latency": {
            "non_llm_p50_ms": non_llm_latency.get("p50"),
            "non_llm_p90_ms": non_llm_latency.get("p90"),
            "non_llm_p99_ms": non_llm_latency.get("p99"),
            "small_model_name": small_best.get("model_name"),
            "small_model_mode": small_best.get("mode"),
            "small_model_p50_ms": small_p50_ms,
            "small_model_p90_ms": float(small_best.get("p90") or 0.0) * 1000.0,
            "small_model_p99_ms": float(small_best.get("p99") or 0.0) * 1000.0,
            "p50_speedup_vs_small_model": speedup,
        },
        "action_id_validity": {
            "non_llm_test_accuracy": non_llm_test.get("accuracy"),
            "small_model_verifier_pass_rate": verifier_pass_count / case_count if case_count else None,
            "small_model_verifier_pass_count": verifier_pass_count,
            "small_model_case_count": case_count,
        },
        "malformed_rate": {
            "non_llm_malformed_rate": 0.0,
            "small_model_malformed_rate": malformed_count / case_count if case_count else None,
            "small_model_malformed_output_count": malformed_count,
        },
        "verifier_pass": {
            "non_llm_contract_valid": True,
            "small_model_verifier_pass_count": verifier_pass_count,
        },
        "portability": "non-LLM selector uses Python standard library rules plus optional already-installed scikit-learn; no model server, weights, or provider account required.",
        "interpretability": "rule baseline emits matched_features and reasons; sklearn baseline is less transparent but still bounded to controlled labels.",
        "data_training_cost": "non-LLM baseline trains only a classical classifier on committed sanitized/synthetic rows when scikit-learn exists; no neural training or model downloads.",
        "live_safety_risk": "lower than small local LLM for this phase because output is action_id metadata only, no buyer-facing text and no side effects.",
        "project_owned_selector_candidate": True,
        "non_llm_selector_role": "fast proposal layer only, not a full conversation brain",
        "response_renderer_and_verifier_remain_separate": True,
        "live_runtime_wiring_allowed": False,
        "provider_calls_made": False,
        "openai_api_calls_made": False,
        "ultravox_calls_made": False,
        "elevenlabs_calls_made": False,
        "local_llm_calls_made": False,
        "ollama_calls_made": False,
        "runtime_behavior_changed": False,
        "response_text_changed": False,
    }


def build_decision(comparison: dict[str, Any]) -> dict[str, Any]:
    non_llm_accuracy = comparison["action_id_validity"].get("non_llm_test_accuracy") or 0.0
    non_llm_p99 = comparison["latency"].get("non_llm_p99_ms") or 10**9
    speedup = comparison["latency"].get("p50_speedup_vs_small_model") or 0.0

    if non_llm_accuracy >= 0.75 and non_llm_p99 <= 50:
        recommendation_id = "shadow_mode_integration_design_next"
        recommendation = "Recommend a shadow-mode integration design next; keep live wiring false until verifier and renderer boundaries are reviewed."
    elif non_llm_p99 <= 50:
        recommendation_id = "hybrid_rule_ml_cleanup_next"
        recommendation = "Latency is strong but accuracy needs cleanup; improve labels/rules or use a hybrid rule plus ML selector before any runtime design."
    else:
        recommendation_id = "fallback_routing_layer_only"
        recommendation = "Keep non-LLM selector as fallback/routing evidence only; latency or accuracy is not sufficient for a proposal layer."

    preferred_candidate = speedup >= 10 and non_llm_p99 <= 50
    evidence = {
        "non_llm_test_accuracy": non_llm_accuracy,
        "non_llm_p99_ms": non_llm_p99,
        "small_model_p50_ms": comparison["latency"].get("small_model_p50_ms"),
        "non_llm_p50_ms": comparison["latency"].get("non_llm_p50_ms"),
        "p50_speedup_vs_small_model": speedup,
        "preferred_live_action_selector_candidate": preferred_candidate,
    }
    return {
        "experiment_id": DECISION_ID,
        "generated_at": utc_now(),
        "status": "pass",
        "recommendation_id": recommendation_id,
        "recommendation": recommendation,
        "non_llm_selector_role": "fast action-id proposal layer only",
        "evidence_summary": evidence,
        "non_llm_selector_is_full_conversation_brain": False,
        "response_renderer_and_verifier_remain_separate": True,
        "project_owned_selector_candidate": preferred_candidate,
        "claims_live_readiness": False,
        "live_wiring_allowed": False,
        "response_text_changed": False,
        "runtime_behavior_changed": False,
        "provider_calls_made": False,
        "openai_api_calls_made": False,
        "ultravox_calls_made": False,
        "elevenlabs_calls_made": False,
        "local_llm_calls_made": False,
        "ollama_calls_made": False,
        "model_training_performed": False,
    }


def comparison_report(result: dict[str, Any]) -> str:
    latency = result["latency"]
    validity = result["action_id_validity"]
    return "\n".join(
        [
            f"# {COMPARISON_ID}",
            "",
            f"- Status: {result['status']}",
            f"- Non-LLM baseline: {result['non_llm_baseline_compared']}",
            f"- Non-LLM p50/p90/p99 ms: {latency['non_llm_p50_ms']:.4f}/{latency['non_llm_p90_ms']:.4f}/{latency['non_llm_p99_ms']:.4f}",
            f"- Small-model p50/p90/p99 ms: {latency['small_model_p50_ms']:.1f}/{latency['small_model_p90_ms']:.1f}/{latency['small_model_p99_ms']:.1f}",
            f"- P50 speedup vs small model: {latency['p50_speedup_vs_small_model']:.1f}x",
            f"- Non-LLM test accuracy: {validity['non_llm_test_accuracy']:.4f}",
            f"- Small-model verifier pass rate: {validity['small_model_verifier_pass_rate']:.4f}",
            "- Reran Ollama: false",
            "- Provider/OpenAI/Ultravox/ElevenLabs/local LLM/Ollama calls: false",
            "- Live runtime wiring allowed: false",
            "",
            "## Framing",
            "",
            "- Non-LLM selector is not a full conversation brain.",
            "- Non-LLM selector may become a fast proposal layer.",
            "- Response renderer and verifier remain separate.",
        ]
    )


def decision_report(result: dict[str, Any]) -> str:
    evidence = result["evidence_summary"]
    return "\n".join(
        [
            f"# {DECISION_ID}",
            "",
            f"- Status: {result['status']}",
            f"- Recommendation: {result['recommendation_id']}",
            f"- Detail: {result['recommendation']}",
            f"- Non-LLM test accuracy: {evidence['non_llm_test_accuracy']:.4f}",
            f"- Non-LLM p99 ms: {evidence['non_llm_p99_ms']:.4f}",
            f"- P50 speedup vs small model: {evidence['p50_speedup_vs_small_model']:.1f}x",
            f"- Preferred live-action selector candidate: {str(evidence['preferred_live_action_selector_candidate']).lower()}",
            "- Live wiring allowed: false",
            "- Response text changed: false",
            "- Runtime behavior changed: false",
            "- Provider/OpenAI/Ultravox/ElevenLabs/local LLM/Ollama calls: false",
        ]
    )


def main() -> int:
    comparison = build_comparison()
    decision = build_decision(comparison)
    write_json(COMPARISON_DIR / "result.json", comparison)
    write_text(COMPARISON_DIR / "report.md", comparison_report(comparison))
    write_json(DECISION_DIR / "result.json", decision)
    write_text(DECISION_DIR / "report.md", decision_report(decision))
    print(
        json.dumps(
            {
                "status": comparison["status"],
                "decision": decision["recommendation_id"],
                "non_llm_test_accuracy": comparison["action_id_validity"]["non_llm_test_accuracy"],
                "non_llm_p99_ms": comparison["latency"]["non_llm_p99_ms"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
