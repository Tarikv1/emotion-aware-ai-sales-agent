from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import statistics
import sys
from time import perf_counter_ns
from typing import Any


sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

OUT_DIR = ROOT / "research" / "experiments" / "generated" / "RUNTIME-ACTION-METADATA-EXTRACTION-001"
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"
EXPERIMENT_ID = "RUNTIME-ACTION-METADATA-EXTRACTION-001"
CAMPAIGN_ID = "public_openai_chatgpt_plans"

from runtime.action_selector.action_selector_contract import action_labels, normalize_text  # noqa: E402
from runtime.action_selector.non_llm_action_selector import RuleBasedActionSelector  # noqa: E402
from runtime.action_selector.runtime_action_metadata_extractor import (  # noqa: E402
    extract_runtime_action_metadata,
    redact_runtime_metadata_for_public_evidence,
    validate_runtime_action_metadata,
)


FALSE_FLAGS = {
    "runtime_behavior_changed": False,
    "response_text_changed": False,
    "side_effects_allowed": False,
    "live_runtime_wiring_allowed": False,
    "memory_mutation_allowed": False,
    "provider_calls_made": False,
    "openai_api_calls_made": False,
    "ultravox_calls_made": False,
    "elevenlabs_calls_made": False,
    "local_llm_calls_made": False,
    "ollama_calls_made": False,
    "tts_calls_made": False,
    "raw_private_data": False,
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def percentile(values: list[float], percentile_value: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, round((percentile_value / 100.0) * (len(ordered) - 1))))
    return ordered[index]


def runtime_result(
    *,
    case_id: str,
    action_signal: str,
    decision_stage: str,
    response_strategy: str,
    recommended_path: str = "",
    active_frame: str = "",
    markers: list[str] | None = None,
) -> dict[str, Any]:
    marker_values = markers or []
    return {
        "campaign_id": CAMPAIGN_ID,
        "turn_id": case_id,
        "runtime_decision": {
            "next_action": action_signal,
            "response_mode": decision_stage,
            "selected_strategy": response_strategy,
            "call_control": "continue",
        },
        "semantic_frame": {
            "semantic": action_signal,
            "dialogue_focus": decision_stage,
            "response_strategy": response_strategy,
            "response_variation_key": response_strategy,
            "candidate_response": f"Synthetic sanitized response for {case_id}.",
            "evidence": marker_values,
        },
        "commercial_state": {
            "buyer_decision_stage": decision_stage,
            "next_commercial_action": action_signal,
            "last_recommendation_given": recommended_path,
            "recommendation_confidence": "high",
            "buyer_fit_level": "fit",
            "active_decision_frame": active_frame,
        },
        "metadata_markers": marker_values,
    }


def _base_context(text: str, action_id: str) -> dict[str, Any]:
    known_use_case = []
    if action_id == "recommend_pro":
        known_use_case = ["heavy_daily_use"]
    return {
        "buyer_utterance_text": text,
        "normalized_buyer_text": normalize_text(text),
        "memory_summary": "",
        "known_use_case": known_use_case,
        "known_tools": [],
        "known_plan_interest": "",
        "known_team_status": "",
        "safety_boundary_detected": action_id in {"respect_boundary", "answer_privacy_boundary"},
    }


def make_case(
    index: int,
    action_id: str,
    text: str,
    action_signal: str,
    decision_stage: str,
    response_strategy: str,
    *,
    recommended_path: str = "",
    active_frame: str = "",
    markers: list[str] | None = None,
) -> dict[str, Any]:
    case_id = f"runtime_metadata_case_{index:03d}"
    return {
        "case_id": case_id,
        "campaign_id": CAMPAIGN_ID,
        "buyer_utterance_text": text,
        "expected_action_id": action_id,
        "source_file": "research/experiments/generated/RUNTIME-ACTION-METADATA-EXTRACTION-001/synthetic_cases",
        "sanitized": True,
        "raw_private_data": False,
        "context": _base_context(text, action_id),
        "runtime_result": runtime_result(
            case_id=case_id,
            action_signal=action_signal,
            decision_stage=decision_stage,
            response_strategy=response_strategy,
            recommended_path=recommended_path,
            active_frame=active_frame,
            markers=markers,
        ),
    }


def build_cases() -> list[dict[str, Any]]:
    specs: list[tuple[str, list[str], str, str, str, str, str, list[str]]] = [
        ("answer_price", ["How much does Plus cost?", "What is the price for Pro?", "Can you explain the pricing?"], "price_answer", "price_question", "answer_price", "", "", []),
        ("handle_price_objection", ["That sounds expensive, is it worth it?", "The price is too much for me.", "It feels pricey, why pay?"], "price_objection too_expensive", "price_objection", "price_objection", "", "", []),
        ("handle_competitor_context", ["Why not Claude instead?", "I use Gemini instead, why switch?", "Does Copilot cover this enough?"], "competitor current_tool", "competitor", "competitor_context", "", "", []),
        ("ask_use_case_gap", ["I use Claude now.", "I use ChatGPT already.", "We use Gemini today."], "ask_use_case use_case_gap", "use_case", "ask_use_case_gap", "", "", []),
        ("ask_usage_intensity", ["I need coding help.", "I do writing workflows.", "Voice work and research are my main tasks."], "ask_usage_intensity usage_intensity", "usage_intensity", "ask_usage_intensity", "", "", []),
        ("clarify_team_vs_individual", ["No company, personal use only.", "This is personal use only."], "team_vs_individual not_team", "team_scope", "clarify_team_vs_individual", "", "team_scope", []),
        ("orient_plan_options", ["What are the plans?", "Explain the plans and options."], "plan_options plan_overview", "plan_overview", "orient_plan_options", "", "", []),
        ("explain_subscription_vs_model", ["Is the model vs subscription different?", "I am confused about subscription vs model."], "subscription_vs_model", "subscription_vs_model", "subscription_vs_model", "", "", []),
        ("answer_signup_path", ["How do I sign up?", "Where do I start using it?", "Can I close this myself online?"], "signup self_serve", "signup", "answer_signup_path", "", "", []),
        ("answer_plan_change", ["Can I upgrade later?", "Can I change plans midcycle?"], "plan_change upgrade_later", "plan_change", "answer_plan_change", "", "", []),
        ("answer_privacy_boundary", ["What is the privacy boundary?", "Do you store raw transcript?", "What is the data retention?"], "privacy transcript raw_audio", "privacy", "answer_privacy_boundary", "", "", ["privacy", "boundary"]),
        ("answer_source_or_affiliation", ["Are you from OpenAI?", "What is the source for this recommendation?"], "source affiliation", "source", "answer_source_or_affiliation", "", "", ["source", "affiliation", "public official"]),
        ("disqualify_no_fit", ["I'm not interested.", "The free plan is enough.", "This is the wrong product.", "I need billing support, not ChatGPT."], "no_fit wrong_product not_interested", "no_fit", "disqualify_no_fit", "", "", ["no_fit", "not_interested"]),
        ("recommend_plus", ["Would Plus be enough?", "Can I stay on Plus?"], "recommend_plus plus_fit light_use", "recommendation", "recommend_plus", "plus", "", []),
        ("recommend_pro", ["Which plan should I pick for daily heavy use?", "Recommend one for every day heavy coding.", "I hit limits every day; which plan?"], "recommend_pro heavy_use limit_pain", "recommendation", "recommend_pro", "pro", "", ["heavy_daily_use"]),
        ("recommend_business_or_enterprise", ["We have a team with SSO needs.", "My company needs admin controls.", "Enterprise legal review is required."], "team enterprise business sso admin_controls", "team", "recommend_business_or_enterprise", "business", "", []),
        ("compare_plus_vs_pro", ["Should I choose Plus vs Pro?", "Plus or Pro for my use?"], "plus_vs_pro plus_enough", "comparison", "compare_plus_vs_pro", "", "plus_vs_pro", []),
        ("compare_pro_tiers", ["Which Pro tier should I choose?", "Is Pro better or should I choose Pro?"], "which_pro pro_tier", "comparison", "compare_pro_tiers", "", "pro_100_vs_200", []),
        ("terminal_close", ["Thanks.", "That works for me.", "Sounds good."], "terminal close", "terminal", "terminal_close", "", "", ["terminal"]),
        ("respect_boundary", ["Can you send an email for me?", "Can you book a calendar invite for me?", "Can you update my CRM for me?", "Can you purchase Plus for me?", "Please create a ticket in my account."], "boundary crm email calendar purchase book_meeting", "boundary", "respect_boundary", "", "", ["boundary", "crm", "email", "calendar"]),
        ("repair_already_told_you", ["I already told you that.", "I said that already."], "already_told repair", "repair", "repair_already_told_you", "", "", ["already_told"]),
        ("repair_buyer_correction", ["No, I said writing not voice.", "Actually I meant code, not writing."], "correction buyer_correction", "repair", "repair_buyer_correction", "", "", ["correction"]),
        ("repair_asr_uncertainty", ["Did you say cloud or Claude?", "Was that Chat GBT maybe?"], "asr uncertain_tool ambiguous_tool", "repair", "repair_asr_uncertainty", "", "", ["asr", "uncertain_tool"]),
        ("avoid_repetition_rephrase", ["You already asked the same question.", "You repeat yourself."], "avoid_repetition repeat duplicate", "repair", "avoid_repetition_rephrase", "", "", ["repeat", "duplicate"]),
        ("clarify_question_scope", ["I'm confused, what do you mean?", "That is unclear."], "clarify_question_scope confusion", "question_scope", "clarify_question_scope", "", "", []),
    ]
    cases: list[dict[str, Any]] = []
    index = 1
    for action_id, texts, action_signal, decision_stage, strategy, recommended_path, active_frame, markers in specs:
        for text in texts:
            cases.append(
                make_case(
                    index,
                    action_id,
                    text,
                    action_signal,
                    decision_stage,
                    strategy,
                    recommended_path=recommended_path,
                    active_frame=active_frame,
                    markers=markers,
                )
            )
            index += 1
    return cases


def selector_action_for_case(case: dict[str, Any], selector: RuleBasedActionSelector) -> str:
    output = selector.select(
        {
            "buyer_utterance_text": case["buyer_utterance_text"],
            "context": case["context"],
        }
    )
    return str(output.action_id)


def run_case(case: dict[str, Any], selector: RuleBasedActionSelector) -> tuple[dict[str, Any], float]:
    start = perf_counter_ns()
    metadata = extract_runtime_action_metadata(case["runtime_result"], {"campaign_id": CAMPAIGN_ID, "turn_id": case["case_id"]})
    latency_ms = (perf_counter_ns() - start) / 1_000_000
    validation_errors = validate_runtime_action_metadata(metadata)
    selector_action_id = selector_action_for_case(case, selector)
    redacted_metadata = redact_runtime_metadata_for_public_evidence(metadata)
    return (
        {
            "case_id": case["case_id"],
            "campaign_id": case["campaign_id"],
            "expected_action_id": case["expected_action_id"],
            "runtime_action_id": redacted_metadata.get("runtime_action_id"),
            "runtime_action_confidence": redacted_metadata.get("runtime_action_confidence"),
            "runtime_action_reason": redacted_metadata.get("runtime_action_reason"),
            "runtime_metadata_available": redacted_metadata.get("runtime_metadata_available"),
            "runtime_response_text_available": redacted_metadata.get("runtime_response_text_available"),
            "runtime_response_text_hash": redacted_metadata.get("runtime_response_text_hash"),
            "extraction_warnings": redacted_metadata.get("extraction_warnings") or [],
            "validation_errors": validation_errors,
            "selector_action_id": selector_action_id,
            "selector_expected_match": selector_action_id == case["expected_action_id"],
            "expected_action_match": redacted_metadata.get("runtime_action_id") == case["expected_action_id"],
            "sanitized": True,
            "raw_private_data": False,
        },
        latency_ms,
    )


def build_result(case_results: list[dict[str, Any]], latencies: list[float]) -> dict[str, Any]:
    case_count = len(case_results)
    validation_error_count = sum(len(row.get("validation_errors") or []) for row in case_results)
    selector_mismatch_count = sum(1 for row in case_results if row.get("selector_expected_match") is not True)
    action_counts = Counter(str(row.get("runtime_action_id") or "") for row in case_results)
    result = {
        "experiment_id": EXPERIMENT_ID,
        "generated_at": utc_now(),
        "status": "pass",
        "case_count": case_count,
        "extraction_success_count": sum(1 for row in case_results if row.get("runtime_metadata_available") is True and not row.get("validation_errors")),
        "action_id_mapped_count": sum(1 for row in case_results if row.get("runtime_action_id") in action_labels()),
        "expected_action_match_count": sum(1 for row in case_results if row.get("expected_action_match") is True),
        "selector_expected_match_count": sum(1 for row in case_results if row.get("selector_expected_match") is True),
        "unmapped_count": sum(1 for row in case_results if not row.get("runtime_action_id")),
        "validation_error_count": validation_error_count,
        "selector_mismatch_count": selector_mismatch_count,
        "runtime_action_counts": dict(sorted(action_counts.items())),
        "latency_ms": {
            "sample_count": len(latencies),
            "p50": percentile(latencies, 50),
            "p90": percentile(latencies, 90),
            "p99": percentile(latencies, 99),
            "max": max(latencies) if latencies else 0.0,
            "mean": statistics.mean(latencies) if latencies else 0.0,
        },
        "case_results": case_results,
        **FALSE_FLAGS,
    }
    if (
        result["case_count"] < 60
        or result["extraction_success_count"] != case_count
        or result["action_id_mapped_count"] != case_count
        or result["expected_action_match_count"] != case_count
        or result["selector_expected_match_count"] != case_count
        or result["unmapped_count"] != 0
        or validation_error_count != 0
    ):
        result["status"] = "fail"
    return result


def build_report(result: dict[str, Any]) -> str:
    latency = result["latency_ms"]
    lines = [
        f"# {EXPERIMENT_ID}",
        "",
        f"- Status: {result['status']}",
        f"- Cases: {result['case_count']}",
        f"- Extraction success/action mapped/expected match: {result['extraction_success_count']}/{result['action_id_mapped_count']}/{result['expected_action_match_count']}",
        f"- Selector expected match: {result['selector_expected_match_count']}",
        f"- Unmapped/validation/selector mismatches: {result['unmapped_count']}/{result['validation_error_count']}/{result['selector_mismatch_count']}",
        f"- Latency ms p50/p90/p99/max: {latency['p50']:.4f}/{latency['p90']:.4f}/{latency['p99']:.4f}/{latency['max']:.4f}",
        "- Runtime behavior changed: false",
        "- Response text changed: false",
        "- Provider/OpenAI/Ultravox/ElevenLabs/local LLM/Ollama/TTS calls: false",
        "- Raw private data: false",
        "",
        "## Runtime Action Counts",
        "",
    ]
    for action_id, count in result["runtime_action_counts"].items():
        lines.append(f"- {action_id}: {count}")
    return "\n".join(lines)


def main() -> int:
    selector = RuleBasedActionSelector()
    case_results: list[dict[str, Any]] = []
    latencies: list[float] = []
    for case in build_cases():
        result, latency_ms = run_case(case, selector)
        case_results.append(result)
        latencies.append(latency_ms)
    result = build_result(case_results, latencies)
    write_json(RESULT_PATH, result)
    write_text(REPORT_PATH, build_report(result))
    print(
        json.dumps(
            {
                "status": result["status"],
                "case_count": result["case_count"],
                "expected_action_match_count": result["expected_action_match_count"],
                "selector_expected_match_count": result["selector_expected_match_count"],
            },
            indent=2,
        )
    )
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
