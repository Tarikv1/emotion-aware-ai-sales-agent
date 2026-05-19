#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

if str(ROOT := Path(__file__).resolve().parents[1]) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.core.dialogue_reasoner import build_reasoning_context, reason_about_turn  # noqa: E402
from runtime.core.dialogue_reasoner_async_enrichment import (  # noqa: E402
    ASYNC_ENRICHMENT_REASONER_ID,
    async_enrichment_boundary_packet,
    build_async_enrichment_request,
    complete_async_enrichment,
    render_async_enrichment_prompt,
)
from runtime.providers.dialogue_reasoner_llm_client import (  # noqa: E402
    DEFAULT_REASONER_TEMPERATURE,
    OpenAICompatibleReasonerConfig,
    call_openai_compatible_reasoner,
    missing_provider_config,
    redacted_provider_config,
)
from scripts.run_dialogue_reasoner_001_baseline import prior_turns_to_session_state  # noqa: E402
from scripts.run_dialogue_reasoner_002_provider_evaluation import (  # noqa: E402
    DEFAULT_ENV_FILE,
    config_value,
    load_env_file,
    resolve_path,
)
from scripts.run_dialogue_reasoner_003_hybrid_gate import (  # noqa: E402
    CASES_PATH,
    GUARD_CASES_PATH,
    baseline_reference,
    load_campaign_for_cases,
    read_json,
    run_guard_cases,
    run_invocation_cases,
    summarize_boolean_results,
    write_json,
    write_text,
)
from scripts.run_live_demo_001_agent_voice_call import (  # noqa: E402
    DEFAULT_CASES_PATH,
    build_turn_packet,
)


EXPERIMENT_ID = "DIALOGUE-REASONER-004"
OUTPUT_DIR = ROOT / "research" / "experiments" / "generated" / EXPERIMENT_ID
DEFAULT_DRY_RESULT = OUTPUT_DIR / "dry_run_result.json"
DEFAULT_DRY_REPORT = OUTPUT_DIR / "dry_run_report.md"
PRIVATE_OUT = ROOT / ".tmp" / EXPERIMENT_ID / "live-demo-response-snapshots"


def latency_summary(results: list[dict[str, Any]]) -> dict[str, float | None]:
    latencies = [float(result["latency_ms"]) for result in results if isinstance(result.get("latency_ms"), (int, float))]
    return {
        "min": min(latencies) if latencies else None,
        "median": statistics.median(latencies) if latencies else None,
        "max": max(latencies) if latencies else None,
    }


def deterministic_response_text(case: dict[str, Any], campaign_id: str) -> str:
    turn_packet = build_turn_packet(
        transcript=str(case["transcript"]),
        campaign_id=campaign_id,
        stage="discovery",
        input_type="speech",
        silence_count=0,
        cases_path=DEFAULT_CASES_PATH,
        private_out=PRIVATE_OUT,
        live_tts=False,
        force_key_missing=True,
        timeout_seconds=8.0,
        session_id=f"{EXPERIMENT_ID}-{case['case_id']}",
        session_state=prior_turns_to_session_state(case.get("prior_turns") or []),
        asr_confidence=0.95,
        voice_turn_state="agent_thinking",
    )
    return str((turn_packet.get("summary") or {}).get("final_response") or "")


def planned_async_case(case: dict[str, Any], campaign: dict[str, Any], campaign_id: str) -> dict[str, Any]:
    session_state = prior_turns_to_session_state(case.get("prior_turns") or [])
    context = build_reasoning_context(str(case["transcript"]), session_state, campaign)
    deterministic_reasoning = reason_about_turn(str(case["transcript"]), session_state, campaign, mode="baseline")
    response_text = deterministic_response_text(case, campaign_id)
    return {
        "case_id": case["case_id"],
        "transcript_length": len(str(case["transcript"])),
        "prior_turn_count": len(case.get("prior_turns") or []),
        **build_async_enrichment_request(
            transcript=str(case["transcript"]),
            context=context,
            deterministic_reasoning=deterministic_reasoning,
            case_goal=str(case.get("case_goal") or ""),
            customer_response_text=response_text,
            response_packet_id=f"{EXPERIMENT_ID}-{case['case_id']}",
        ),
    }


def run_live_async_case(
    case: dict[str, Any],
    campaign: dict[str, Any],
    campaign_id: str,
    config: OpenAICompatibleReasonerConfig,
) -> dict[str, Any]:
    session_state = prior_turns_to_session_state(case.get("prior_turns") or [])
    context = build_reasoning_context(str(case["transcript"]), session_state, campaign)
    deterministic_reasoning = reason_about_turn(str(case["transcript"]), session_state, campaign, mode="baseline")
    response_text = deterministic_response_text(case, campaign_id)
    request = build_async_enrichment_request(
        transcript=str(case["transcript"]),
        context=context,
        deterministic_reasoning=deterministic_reasoning,
        case_goal=str(case.get("case_goal") or ""),
        customer_response_text=response_text,
        response_packet_id=f"{EXPERIMENT_ID}-{case['case_id']}",
    )
    if not request["provider_call_allowed"]:
        return {"case_id": case["case_id"], **request}
    prompt = render_async_enrichment_prompt(
        transcript=str(case["transcript"]),
        context=context,
        deterministic_reasoning=deterministic_reasoning,
        case_goal=str(case.get("case_goal") or ""),
    )
    provider_call = call_openai_compatible_reasoner(config, prompt)
    return {
        "case_id": case["case_id"],
        **complete_async_enrichment(
            request,
            provider_call,
            case=case,
            customer_response_text_after_provider=response_text,
        ),
    }


def summarize_async_enrichment(results: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "planned_case_count": len(results),
        "queued_count": sum(1 for result in results if result.get("queued_before_provider") is True),
        "not_eligible_count": sum(1 for result in results if result.get("status") == "not_eligible"),
        "provider_case_count": sum(1 for result in results if result.get("provider_call_made") is True),
        "completed_count": sum(1 for result in results if result.get("status") == "completed"),
        "failed_count": sum(1 for result in results if result.get("status") == "failed"),
        "ignored_count": sum(1 for result in results if result.get("status") == "ignored"),
        "failed_cases": [result["case_id"] for result in results if result.get("status") == "failed"],
        "deterministic_customer_response_available_before_provider_count": sum(
            1
            for result in results
            if (result.get("customer_response_snapshot") or {}).get("available_before_provider") is True
        ),
        "customer_response_blocked_count": sum(
            1 for result in results if result.get("customer_response_blocked_on_provider") is True
        ),
        "provider_result_applied_after_response_count": sum(
            1 for result in results if result.get("provider_result_applied_after_response") is True
        ),
        "final_response_changed_by_provider_count": sum(
            1 for result in results if result.get("final_response_changed_by_provider") is True
        ),
        "latency_ms": latency_summary(results),
    }


def empty_async_results(reasoning_cases: list[dict[str, Any]], campaign: dict[str, Any], campaign_id: str) -> list[dict[str, Any]]:
    return [planned_async_case(case, campaign, campaign_id) for case in reasoning_cases]


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    case_payload = read_json(CASES_PATH)
    campaign_id = str(case_payload["default_campaign_id"])
    campaign = load_campaign_for_cases(case_payload)
    reasoning_cases = list(case_payload["reasoning_quality_cases"])
    if args.max_reasoning_cases and args.max_reasoning_cases > 0:
        reasoning_cases = reasoning_cases[: args.max_reasoning_cases]

    guard_results = run_guard_cases(campaign)
    invocation_results = run_invocation_cases(case_payload["invocation_gate_cases"], campaign)
    planned_async = empty_async_results(reasoning_cases, campaign, campaign_id)

    env_file = resolve_path(args.env_file, DEFAULT_ENV_FILE)
    env_file_values = load_env_file(env_file)
    config = OpenAICompatibleReasonerConfig(
        base_url=config_value("DIALOGUE_REASONER_BASE_URL", args.base_url, env_file_values),
        model=config_value("DIALOGUE_REASONER_MODEL", args.model, env_file_values),
        api_key=config_value(args.api_key_env, None, env_file_values),
        timeout_seconds=float(args.timeout_seconds),
        temperature=float(args.temperature),
        use_json_response_format=not args.disable_json_response_format,
    )
    missing = missing_provider_config(config)
    boundary = async_enrichment_boundary_packet()
    base = {
        "experiment_id": EXPERIMENT_ID,
        "async_enrichment_reasoner_id": ASYNC_ENRICHMENT_REASONER_ID,
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "case_source": str(CASES_PATH.relative_to(ROOT)).replace("\\", "/"),
        "guard_case_source": str(GUARD_CASES_PATH.relative_to(ROOT)).replace("\\", "/"),
        "case_count": len(guard_results) + len(invocation_results) + len(reasoning_cases),
        "full_case_count": 100,
        "max_reasoning_cases": args.max_reasoning_cases if args.max_reasoning_cases and args.max_reasoning_cases > 0 else None,
        "default_live_enabled": False,
        "live_demo_response_behavior_changed": False,
        "runtime_route_override_allowed": boundary["runtime_route_override_allowed"],
        "customer_response_blocked_on_provider": boundary["customer_response_blocked_on_provider"],
        "mutates_final_response": boundary["mutates_final_response"],
        "opens_prod_102": False,
        "api_key_env": args.api_key_env,
        "api_key_value_logged": False,
        "env_file": {
            "path": str(env_file.relative_to(ROOT)).replace("\\", "/") if env_file.is_relative_to(ROOT) else str(env_file),
            "exists": env_file.exists(),
            "loaded_keys": sorted(key for key, value in env_file_values.items() if value),
            "values_logged": False,
        },
        "provider_config": redacted_provider_config(config),
        "baseline_reference": baseline_reference(),
        "guard_results": guard_results,
        "guard_summary": summarize_boolean_results(guard_results),
        "invocation_gate_results": invocation_results,
        "invocation_gate_summary": summarize_boolean_results(invocation_results),
        "planned_async_enrichment": planned_async,
    }
    if not args.live:
        return {
            **base,
            "mode": "dry-run",
            "blocked_reason": "dry-run-mode",
            "provider_calls_made": False,
            "text_sent_to_provider": False,
            "missing_config": missing,
            "async_enrichment_results": [],
            "async_enrichment_summary": summarize_async_enrichment(planned_async),
        }
    if not args.consent_confirmed:
        return {
            **base,
            "mode": "live-blocked",
            "blocked_reason": "missing-consent-confirmed",
            "provider_calls_made": False,
            "text_sent_to_provider": False,
            "missing_config": missing,
            "async_enrichment_results": [],
            "async_enrichment_summary": summarize_async_enrichment(planned_async),
        }
    if missing:
        return {
            **base,
            "mode": "live-blocked",
            "blocked_reason": "missing-provider-config",
            "provider_calls_made": False,
            "text_sent_to_provider": False,
            "missing_config": missing,
            "async_enrichment_results": [],
            "async_enrichment_summary": summarize_async_enrichment(planned_async),
        }

    async_results = [run_live_async_case(case, campaign, campaign_id, config) for case in reasoning_cases]
    return {
        **base,
        "mode": "live",
        "blocked_reason": None,
        "provider_calls_made": any(result.get("provider_call_made") is True for result in async_results),
        "text_sent_to_provider": any(result.get("text_sent_to_provider") is True for result in async_results),
        "missing_config": [],
        "async_enrichment_results": async_results,
        "async_enrichment_summary": summarize_async_enrichment(async_results),
    }


def render_report(payload: dict[str, Any]) -> str:
    summary = payload["async_enrichment_summary"]
    lines = [
        "# DIALOGUE-REASONER-004 Async Enrichment",
        "",
        f"- Mode: `{payload['mode']}`",
        f"- Blocked reason: `{payload['blocked_reason']}`",
        f"- Cases: `{payload['case_count']}`",
        f"- Guard batch: `{payload['guard_summary']['passed_count']}/{payload['guard_summary']['case_count']}`",
        f"- Invocation gate batch: `{payload['invocation_gate_summary']['passed_count']}/{payload['invocation_gate_summary']['case_count']}`",
        f"- Async queued before provider: `{summary['queued_count']}/{summary['planned_case_count']}`",
        f"- Deterministic response available before provider: `{summary['deterministic_customer_response_available_before_provider_count']}/{summary['planned_case_count']}`",
        f"- Provider cases completed: `{summary['completed_count']}/{summary['planned_case_count']}`",
        f"- Provider calls made: `{str(payload['provider_calls_made']).lower()}`",
        f"- Text sent to provider: `{str(payload['text_sent_to_provider']).lower()}`",
        f"- API key value logged: `{str(payload['api_key_value_logged']).lower()}`",
        f"- Runtime route override allowed: `{str(payload['runtime_route_override_allowed']).lower()}`",
        f"- Customer response blocked on provider: `{str(payload['customer_response_blocked_on_provider']).lower()}`",
        f"- Opens PROD-102: `{str(payload['opens_prod_102']).lower()}`",
        "",
        "## Boundary",
        "",
        "- Deterministic response generation finishes before any provider enrichment result is needed.",
        "- The provider may only enrich eligible reasoning cases with the DIALOGUE-REASONER-003 schema.",
        "- The enrichment packet stores response fingerprints and counts, not customer-facing response text.",
        "- Route labels and final response mutation stay blocked.",
        "",
    ]
    if payload["mode"] == "live":
        lines.extend(["## Live Async Results", ""])
        for result in payload["async_enrichment_results"]:
            lines.append(
                f"- `{result['case_id']}`: `{result['status']}`, "
                f"latency `{result.get('latency_ms')}` ms, response changed `{str(result.get('final_response_changed_by_provider')).lower()}`"
            )
    else:
        lines.extend(["## Planned Async Enrichment", ""])
        for result in payload["planned_async_enrichment"]:
            snapshot = result["customer_response_snapshot"]
            lines.append(
                f"- `{result['case_id']}`: `{result['status']}`, prompt chars `{result['prompt_char_count']}`, "
                f"response chars `{snapshot['char_count']}`"
            )
    lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate optional async LLM enrichment behind deterministic dialogue routing.")
    parser.add_argument("--live", action="store_true", help="Actually call the configured provider for async enrichment cases.")
    parser.add_argument("--consent-confirmed", action="store_true", help="Confirm synthetic transcript upload is approved.")
    parser.add_argument("--api-key-env", default="DIALOGUE_REASONER_API_KEY")
    parser.add_argument("--env-file", default=None, help="Local ignored env file. Defaults to runtime/config/local/dialogue_reasoner.env.")
    parser.add_argument("--base-url", default=None, help="OpenAI-compatible chat/completions URL. Can also use DIALOGUE_REASONER_BASE_URL.")
    parser.add_argument("--model", default=None, help="Model id. Can also use DIALOGUE_REASONER_MODEL.")
    parser.add_argument("--timeout-seconds", type=float, default=12.0)
    parser.add_argument("--temperature", type=float, default=DEFAULT_REASONER_TEMPERATURE)
    parser.add_argument("--disable-json-response-format", action="store_true")
    parser.add_argument("--max-reasoning-cases", type=int, default=0, help="Optional smoke limit for reasoning-quality provider calls.")
    parser.add_argument("--out", default=None)
    parser.add_argument("--report-out", default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    out = resolve_path(args.out, DEFAULT_DRY_RESULT)
    report_out = resolve_path(args.report_out, DEFAULT_DRY_REPORT if out == DEFAULT_DRY_RESULT else out.with_suffix(".md"))
    payload = build_payload(args)
    write_json(out, payload)
    write_text(report_out, render_report(payload))
    print(
        json.dumps(
            {
                "experiment_id": payload["experiment_id"],
                "mode": payload["mode"],
                "case_count": payload["case_count"],
                "guard": payload["guard_summary"],
                "invocation_gate": payload["invocation_gate_summary"],
                "async_enrichment": payload["async_enrichment_summary"],
                "provider_calls_made": payload["provider_calls_made"],
                "text_sent_to_provider": payload["text_sent_to_provider"],
                "blocked_reason": payload["blocked_reason"],
                "out": str(out),
            },
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
